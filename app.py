import streamlit as st
import tempfile
import os
from pathlib import Path
from scipy.io import wavfile

st.set_page_config(
    page_title="clone-her",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Session State ─────────────────────────────────────────
if "dark_mode"       not in st.session_state: st.session_state.dark_mode       = True
if "client"          not in st.session_state: st.session_state.client          = None
if "connected_space" not in st.session_state: st.session_state.connected_space = None
if "audio_result"    not in st.session_state: st.session_state.audio_result    = None

dark = st.session_state.dark_mode

# ─────────────────────────────────────────────────────────
# FONTS + ICONS
# ─────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://cdn.hugeicons.com/font/hgi-stroke-rounded.css" rel="stylesheet"/>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# SCOPED CSS — only Streamlit widget overrides + shell
# Tailwind handles all layout/color/typography
# ─────────────────────────────────────────────────────────
bg       = "#09090b" if dark else "#fafafa"
surface  = "#18181b" if dark else "#ffffff"
border   = "#27272a" if dark else "#e4e4e7"
txt      = "#fafafa"  if dark else "#09090b"
muted    = "#71717a"
accent   = "#e4e4e7"  if dark else "#18181b"
accent_bg= "#27272a"  if dark else "#f4f4f5"

st.markdown(f"""
<style>
  /* ── shell ── */
  .stApp                    {{
    background:
      radial-gradient(1200px 500px at 90% -20%, {'rgba(16,185,129,.08)' if dark else 'rgba(24,24,27,.05)'}, transparent 60%),
      radial-gradient(1000px 500px at -10% 0%, {'rgba(59,130,246,.08)' if dark else 'rgba(113,113,122,.05)'}, transparent 55%),
      {bg} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
  }}
  .stApp::before            {{ display: none !important; }}
  .block-container          {{ max-width: 46rem !important; padding: .75rem 1.1rem 4.5rem !important; }}
  #MainMenu, footer, header,
  .stDeployButton, .stDecoration,
  [data-testid="stToolbar"] {{ display: none !important; }}
  html, body, [class*="css"],
  p, span, div, label       {{ color: {txt} !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }}

  /* ── inputs ── */
  .stTextArea textarea,
  .stTextInput input {{
    background: {surface} !important;
    border: 1px solid {border} !important;
    border-radius: .75rem !important;
    color: {txt} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: .9rem !important;
  }}
  .stTextArea textarea:focus,
  .stTextInput input:focus {{
    border-color: {accent} !important;
    box-shadow: 0 0 0 2px {'rgba(228,228,231,.15)' if dark else 'rgba(24,24,27,.08)'} !important;
    outline: none !important;
  }}
  .stTextArea textarea::placeholder,
  .stTextInput input::placeholder {{ color: {muted} !important; }}

  /* ── file uploader ── */
  [data-testid="stFileUploader"] section {{
    background: {surface} !important;
    border: 1.5px dashed {border} !important;
    border-radius: .75rem !important;
  }}
  [data-testid="stFileUploader"] p,
  [data-testid="stFileUploader"] span {{ color: {muted} !important; }}

  /* ── audio input (recorder) ── */
  [data-testid="stAudioInput"] {{
    background: {surface} !important;
    border: 1.5px dashed {border} !important;
    border-radius: .75rem !important;
  }}

  /* ── tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
    background: {surface} !important;
    border-radius: .625rem !important;
    border: 1px solid {border} !important;
    gap: 2px !important;
    padding: 3px !important;
    margin-bottom: .55rem !important;
  }}
  .stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border-radius: .5rem !important;
    color: {muted} !important;
    font-size: .8rem !important;
    font-weight: 600 !important;
  }}
  .stTabs [aria-selected="true"] {{
    background: {accent_bg} !important;
    color: {txt} !important;
  }}
  .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}
  .stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}

  /* ── buttons ── */
  .stButton > button {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: .875rem !important;
    border-radius: .625rem !important;
    border: 1px solid {border} !important;
    background: {surface} !important;
    color: {txt} !important;
    transition: all .15s !important;
    min-height: 2.5rem !important;
  }}
  .stButton > button:hover {{
    background: {accent_bg} !important;
    border-color: {accent} !important;
  }}
  [data-testid="baseButton-primary"] {{
    background: {accent} !important;
    color: {bg} !important;
    border-color: transparent !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    border-radius: .625rem !important;
    min-height: 2.75rem !important;
  }}
  [data-testid="baseButton-primary"]:hover {{ opacity: .85 !important; }}

  /* ── download button ── */
  [data-testid="stDownloadButton"] > button {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    border-radius: .625rem !important;
    border: 1px solid {border} !important;
    background: {surface} !important;
    color: {txt} !important;
    width: 100% !important;
  }}

  /* ── selectbox ── */
  [data-baseweb="select"] > div {{
    background: {surface} !important;
    border-color: {border} !important;
    border-radius: .625rem !important;
    color: {txt} !important;
  }}

  /* ── audio player ── */
  audio {{ width: 100%; border-radius: .625rem; margin-top: .5rem; }}

  /* ── scrollbar ── */
  ::-webkit-scrollbar       {{ width: 5px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{ background: {border}; border-radius: 999px; }}

  /* ── custom utility classes (tailwind-free) ── */
  .app-nav {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 1rem;
    padding: .85rem 1rem;
    margin: .1rem 0 .75rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: .75rem;
  }}
  .app-title {{
    font-family: 'DM Serif Display', serif;
    color: {txt};
    font-size: 1.45rem;
    line-height: 1.1;
    letter-spacing: -.02em;
  }}
  .status-pill {{
    background: {surface};
    border: 1px solid {border};
    border-radius: .8rem;
    padding: .65rem .85rem;
    margin: .15rem 0 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: .75rem;
  }}
  .status-pill .left {{
    display: flex;
    align-items: center;
    gap: .45rem;
  }}
  .status-dot {{
    width: .45rem;
    height: .45rem;
    border-radius: 999px;
    display: inline-block;
  }}
  .status-main {{
    color: {txt};
    font-size: .77rem;
    font-weight: 600;
  }}
  .status-side {{
    color: {muted};
    font-size: .75rem;
  }}
  .section-card {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 1rem;
    padding: 1rem;
    margin-bottom: .9rem;
  }}
  .section-label {{
    display: flex;
    align-items: center;
    gap: .5rem;
    margin-bottom: .55rem;
  }}
  .section-label i {{ color: {muted}; font-size: .95rem; }}
  .section-label span {{
    color: {muted};
    font-size: .73rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
  }}
  .body-text {{
    color: {muted};
    font-size: .9rem;
    line-height: 1.55;
    margin: 0 0 .7rem;
  }}
  .hint-text {{
    color: {muted};
    font-size: .73rem;
    margin-top: .35rem;
  }}
  .tiny-ok {{
    color: #10b981;
    font-size: .75rem;
    margin-top: .35rem;
  }}
  .warning-line {{
    color: {muted};
    font-size: .78rem;
    display: flex;
    align-items: center;
    gap: .35rem;
    margin: .1rem 0 .65rem;
  }}
  .app-footer {{
    border-top: 1px solid {border};
    margin-top: 2.1rem;
    padding-top: .9rem;
    padding-bottom: .2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: {muted};
    font-size: .75rem;
    gap: .8rem;
  }}
  @media (max-width: 640px) {{
    .app-nav {{ padding: .85rem .9rem; }}
    .app-title {{ font-size: 1.25rem; }}
    .app-footer {{ flex-direction: column; align-items: flex-start; }}
  }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# TOP BAR
# ─────────────────────────────────────────────────────────
col_nav, col_toggle = st.columns([8, 2])
with col_nav:
    st.markdown("""
    <div class="app-nav">
      <div class="app-title">clone-her</div>
    </div>
    """, unsafe_allow_html=True)
with col_toggle:
    theme_label = "Use Light" if dark else "Use Dark"
    if st.button(theme_label, key="theme_btn", use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# ─────────────────────────────────────────────────────────
# API CONNECTION
# ─────────────────────────────────────────────────────────
SPACES = ["mrfakename/E2-F5-TTS", "abidlabs/E2-F5-TTS", "Hev832/E2-F5-TTS"]

def get_client():
    from gradio_client import Client
    for space in SPACES:
        try:
            return Client(space, verbose=False), space
        except Exception:
            continue
    return None, None

if st.session_state.client is None:
    with st.spinner("Connecting to voice engine..."):
        try:
            c, s = get_client()
            st.session_state.client, st.session_state.connected_space = c, s
        except ImportError:
            st.error("Run: pip install gradio_client scipy")
            st.stop()

# connection status pill
if st.session_state.client:
    space_short = (st.session_state.connected_space or "").split("/")[-1]
    st.markdown(f"""
    <div class="status-pill">
      <div class="left">
        <span class="status-dot" style="background:#10b981;"></span>
        <span class="status-main">Connected - {space_short}</span>
      </div>
      <span class="status-side">F5-TTS</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="status-pill">
      <div class="left">
        <span class="status-dot" style="background:#ef4444;"></span>
        <span class="status-main" style="color:#f87171;">All spaces unavailable</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Reconnect", key="reconnect"):
        st.session_state.client = None
        st.rerun()
    st.stop()

# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────
def section_label(icon, text):
    st.markdown(f"""
    <div class="section-label">
      <i class="hgi hgi-stroke hgi-{icon}"></i>
      <span>{text}</span>
    </div>
    """, unsafe_allow_html=True)

def card_open():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)

def card_close():
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# 1. VOICE INPUT
# ─────────────────────────────────────────────────────────
card_open()
section_label("microphone-01", "Reference Voice")

st.markdown('<p class="body-text">Record your voice or upload an existing clip. 6-30 seconds works best, and clean audio improves voice quality.</p>', unsafe_allow_html=True)

source = st.radio(
  "Source",
  options=["Record", "Upload"],
  horizontal=True,
  key="voice_source",
  label_visibility="collapsed"
)

recorded_audio = None
uploaded_file  = None

if source == "Record":
    recorded_audio = st.audio_input(
        "Record",
        label_visibility="collapsed",
        key="recorder"
    )
    if recorded_audio:
        st.markdown('<p class="tiny-ok"><i class="hgi hgi-stroke hgi-checkmark-circle-01"></i> Recording ready</p>', unsafe_allow_html=True)

if source == "Upload":
    uploaded_file = st.file_uploader(
        "Upload",
        type=["wav","mp3","m4a","ogg","flac","aac","webm","opus","mp4"],
        label_visibility="collapsed",
        key="uploader"
    )
    if uploaded_file:
        st.markdown(f'<p class="tiny-ok"><i class="hgi hgi-stroke hgi-music-note-01"></i> {uploaded_file.name}</p>', unsafe_allow_html=True)
        st.audio(uploaded_file)

card_close()

active_audio  = recorded_audio or uploaded_file
active_is_rec = recorded_audio is not None

# ─────────────────────────────────────────────────────────
# 2. TEXT TO SYNTHESIZE
# ─────────────────────────────────────────────────────────
card_open()
section_label("text-font", "Text to Synthesize")

gen_text = st.text_area(
    "gen_text",
    placeholder="Type anything. Use commas and periods to shape pacing.",
    height=110,
    label_visibility="collapsed",
    key="gen_text"
)

char_count = len(gen_text) if gen_text else 0
st.markdown(f'<p class="hint-text" style="text-align:right;">{char_count} chars</p>', unsafe_allow_html=True)
card_close()

# ─────────────────────────────────────────────────────────
# 3. GENERATE BUTTON + VALIDATION
# ─────────────────────────────────────────────────────────
can_generate = bool(active_audio and gen_text and gen_text.strip())

if not can_generate:
    missing = []
    if not active_audio:                      missing.append("voice reference")
    if not gen_text or not gen_text.strip():  missing.append("text")
    st.markdown(f"""
    <div class="warning-line">
      <i class="hgi hgi-stroke hgi-alert-02"></i>
      Missing: {' and '.join(missing)}
    </div>
    """, unsafe_allow_html=True)

generate_btn = st.button(
    "Generate Voice",
    disabled=not can_generate,
    type="primary",
    use_container_width=True,
    key="generate"
)

# ─────────────────────────────────────────────────────────
# GENERATION LOGIC
# ─────────────────────────────────────────────────────────
def save_to_tmp(audio_source, is_rec=False):
    suffix = ".wav" if is_rec else (Path(audio_source.name).suffix.lower() or ".wav")
    data   = audio_source.read()
    audio_source.seek(0)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data); tmp.close()
    if suffix != ".wav":
        try:
            import subprocess
            wp = tmp.name[:-len(suffix)] + ".wav"
            r  = subprocess.run(["ffmpeg","-y","-i",tmp.name,wp], capture_output=True, timeout=30)
            if r.returncode == 0:
                os.unlink(tmp.name); return wp
        except Exception:
            pass
    return tmp.name

if generate_btn and can_generate:
    from gradio_client import handle_file
    ref_tmp = out_tmp = None
    try:
        with st.spinner("Cloning voice..."):
            ref_tmp = save_to_tmp(active_audio, is_rec=active_is_rec)

            def call_api(cl):
                return cl.predict(
                    ref_audio=handle_file(ref_tmp),
                  ref_text="",
                    gen_text=gen_text.strip(),
                    remove_silence=True,
                    api_name="/predict"
                )

            try:
                result = call_api(st.session_state.client)
            except Exception as e:
                if any(k in str(e).lower() for k in ["quota","exceeded","unauthorized","runtime_error"]):
                    st.warning("Quota hit — switching space...")
                    nc, ns = get_client()
                    if nc:
                        st.session_state.client = nc
                        st.session_state.connected_space = ns
                        result = call_api(nc)
                    else:
                        raise Exception("All spaces exhausted.")
                else:
                    raise

            if result and os.path.exists(result):
                sr, data = wavfile.read(result)
                fd, out_tmp = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                wavfile.write(out_tmp, sr, data)
                with open(out_tmp, "rb") as f:
                    st.session_state.audio_result = f.read()
                st.rerun()
            else:
                st.error("API returned an empty result. Try again.")

    except Exception as e:
        m = str(e).lower()
        if any(k in m for k in ["quota","exceeded"]):      st.error("GPU quota exhausted. Wait 24h or switch networks.")
        elif "exhausted" in m:                             st.error("All spaces down. Try reconnecting later.")
        elif any(k in m for k in ["connection","timeout"]): st.error("Connection timeout. Check your internet.")
        else:                                              st.error(f"Failed: {e}")
    finally:
        for p in [ref_tmp, out_tmp]:
            if p and os.path.exists(p):
                try: os.unlink(p)
                except: pass

# ─────────────────────────────────────────────────────────
# OUTPUT PLAYER
# ─────────────────────────────────────────────────────────
if st.session_state.audio_result:
    card_open()
    section_label("headphones", "Output")
    st.audio(st.session_state.audio_result, format="audio/wav")
    col_dl, col_clr = st.columns([4, 1])
    with col_dl:
        st.download_button(
            "Download",
            data=st.session_state.audio_result,
            file_name="clone-her-output.wav",
            mime="audio/wav",
            use_container_width=True,
        )
    with col_clr:
        if st.button("Clear", use_container_width=True, key="clear"):
            st.session_state.audio_result = None
            st.rerun()
    card_close()

# ─────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────
st.markdown(f"""
<footer class="app-footer">
  <span>© clone-her 2026. all rights reserved.</span>
  <span>crafted by romeiro &amp; gavin</span>
</footer>
""", unsafe_allow_html=True)