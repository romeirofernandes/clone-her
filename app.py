import streamlit as st
import tempfile
import os
import shutil
from pathlib import Path
from scipy.io import wavfile
import numpy as np

st.set_page_config(
    page_title="clone-her — voice cloning studio",
    page_icon="https://cdn.hugeicons.com/favicon.ico",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Theme State ───────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "client" not in st.session_state:
    st.session_state.client = None
if "connected_space" not in st.session_state:
    st.session_state.connected_space = None
if "audio_result" not in st.session_state:
    st.session_state.audio_result = None

dark = st.session_state.dark_mode

# ── CSS + Hugeicons CDN ───────────────────────────────────
st.markdown(f"""
<link rel="stylesheet" href="https://cdn.hugeicons.com/font/hgi-stroke-rounded.css" />
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300&family=DM+Serif+Display:ital@0;1&display=swap');

  :root {{
    --font-heading: 'DM Serif Display', Georgia, serif;
    --font-body:    'Plus Jakarta Sans', sans-serif;
    --max-w:        48rem;

    --bg-primary:       {"#000000" if dark else "#ffffff"};
    --bg-secondary:     {"rgba(255,255,255,0.04)" if dark else "rgba(59,130,246,0.04)"};
    --bg-card:          {"rgba(255,255,255,0.05)" if dark else "rgba(255,255,255,0.85)"};
    --bg-card-hover:    {"rgba(255,255,255,0.08)" if dark else "rgba(255,255,255,0.95)"};
    --border:           {"rgba(255,255,255,0.10)" if dark else "rgba(59,130,246,0.15)"};
    --border-focus:     {"rgba(255,255,255,0.30)" if dark else "rgba(59,130,246,0.50)"};
    --text-primary:     {"#f8fafc" if dark else "#0f172a"};
    --text-secondary:   {"rgba(248,250,252,0.55)" if dark else "#475569"};
    --text-muted:       {"rgba(248,250,252,0.30)" if dark else "#94a3b8"};
    --accent:           {"#60a5fa" if dark else "#2563eb"};
    --accent-glow:      {"rgba(96,165,250,0.20)" if dark else "rgba(37,99,235,0.12)"};
    --accent-bg:        {"rgba(96,165,250,0.10)" if dark else "rgba(37,99,235,0.08)"};
    --danger:           {"#f87171" if dark else "#dc2626"};
    --success:          {"#4ade80" if dark else "#16a34a"};
    --warning:          {"#fbbf24" if dark else "#d97706"};
    --shadow:           {"0 0 0 1px rgba(255,255,255,0.06), 0 4px 24px rgba(0,0,0,0.40)" if dark else "0 0 0 1px rgba(59,130,246,0.10), 0 4px 24px rgba(59,130,246,0.08)"};
    --shadow-lg:        {"0 0 0 1px rgba(255,255,255,0.08), 0 8px 48px rgba(0,0,0,0.60)" if dark else "0 0 0 1px rgba(59,130,246,0.12), 0 8px 48px rgba(59,130,246,0.12)"};
  }}

  /* ── Reset & Base ── */
  html, body, [class*="css"] {{
    font-family: var(--font-body) !important;
    color: var(--text-primary) !important;
    background: transparent !important;
  }}

  /* ── Page Background ── */
  .stApp {{
    background: var(--bg-primary) !important;
    min-height: 100vh;
  }}

  .stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    {"background: radial-gradient(125% 125% at 50% 10%, #000000 40%, #0d1a36 100%);" if dark else
     "background: #ffffff; background-image: radial-gradient(circle at top center, rgba(59,130,246,0.5), transparent 70%);"}
  }}

  /* ── Block Container ── */
  .block-container {{
    max-width: var(--max-w) !important;
    padding: 2rem 1.5rem 4rem !important;
    position: relative;
    z-index: 1;
  }}

  /* ── Hide Streamlit Cruft ── */
  #MainMenu, footer, header, .stDeployButton {{ display: none !important; }}
  .stDecoration {{ display: none !important; }}
  [data-testid="stToolbar"] {{ display: none !important; }}

  /* ── Typography ── */
  h1, h2, h3 {{
    font-family: var(--font-heading) !important;
    letter-spacing: -0.02em;
    line-height: 1.15;
  }}

  /* ── Cards ── */
  .vf-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(12px);
    box-shadow: var(--shadow);
    transition: border-color 0.2s, box-shadow 0.2s;
  }}
  .vf-card:hover {{
    border-color: var(--border-focus);
    box-shadow: var(--shadow-lg);
  }}

  /* ── Badge ── */
  .vf-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 999px;
    background: var(--accent-bg);
    color: var(--accent);
    border: 1px solid var(--accent-glow);
    margin-bottom: 1rem;
  }}
  .vf-badge i {{
    font-size: 13px;
  }}

  /* ── Hero ── */
  .vf-hero {{
    text-align: center;
    padding: 3rem 0 2rem;
  }}
  .vf-hero h1 {{
    font-size: clamp(2.4rem, 6vw, 3.6rem);
    font-family: var(--font-heading) !important;
    color: var(--text-primary) !important;
    margin-bottom: 0.75rem;
    line-height: 1.1;
  }}
  .vf-hero p {{
    font-size: 1.05rem;
    color: var(--text-secondary) !important;
    max-width: 36rem;
    margin: 0 auto;
    line-height: 1.7;
    font-weight: 400;
  }}

  /* ── Section label ── */
  .vf-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted) !important;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .vf-label i {{
    font-size: 14px;
    color: var(--accent);
  }}

  /* ── Status pills ── */
  .vf-status {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 500;
    padding: 5px 12px;
    border-radius: 999px;
    margin-top: 0.5rem;
  }}
  .vf-status i {{ font-size: 14px; }}
  .vf-status.ok   {{ background: rgba(74,222,128,0.10);  color: var(--success); border: 1px solid rgba(74,222,128,0.20);  }}
  .vf-status.err  {{ background: rgba(248,113,113,0.10); color: var(--danger);  border: 1px solid rgba(248,113,113,0.20); }}
  .vf-status.warn {{ background: rgba(251,191,36,0.10);  color: var(--warning); border: 1px solid rgba(251,191,36,0.20);  }}

  /* ── Divider ── */
  .vf-divider {{
    height: 1px;
    background: var(--border);
    margin: 1.5rem 0;
  }}

  /* ── Theme toggle ── */
  .vf-theme-row {{
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 10;
  }}

  /* ── Streamlit widget overrides ── */
  .stTextArea textarea, .stTextInput input {{
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s !important;
  }}
  .stTextArea textarea:focus, .stTextInput input:focus {{
    border-color: var(--border-focus) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
  }}
  .stTextArea textarea::placeholder, .stTextInput input::placeholder {{
    color: var(--text-muted) !important;
  }}

  .stSlider [data-baseweb="thumb"] {{
    background: var(--accent) !important;
    border-color: var(--accent) !important;
  }}
  .stSlider [data-baseweb="track-foreground"] {{
    background: var(--accent) !important;
  }}

  /* File uploader */
  [data-testid="stFileUploader"] {{
    background: var(--bg-secondary) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 12px !important;
    transition: border-color 0.2s !important;
  }}
  [data-testid="stFileUploader"]:hover {{
    border-color: var(--border-focus) !important;
  }}
  [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] p {{
    color: var(--text-secondary) !important;
  }}

  /* Buttons */
  .stButton > button {{
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    transition: all 0.2s !important;
    padding: 0.5rem 1.25rem !important;
  }}
  .stButton > button:hover {{
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
  }}

  /* Primary button */
  [data-testid="baseButton-primary"] {{
    background: var(--accent) !important;
    color: #fff !important;
    border-color: transparent !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
  }}
  [data-testid="baseButton-primary"]:hover {{
    opacity: 0.88 !important;
    color: #fff !important;
    border-color: transparent !important;
  }}

  /* Selectbox */
  [data-baseweb="select"] > div {{
    background: var(--bg-secondary) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
  }}
  [data-baseweb="popover"] {{
    background: {"#0d1a36" if dark else "#fff"} !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
  }}

  /* Audio player */
  audio {{
    width: 100%;
    border-radius: 10px;
    margin-top: 0.5rem;
  }}

  /* Labels */
  label, .stTextArea label, .stSlider label, .stSelectbox label {{
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
  }}

  /* Alert boxes */
  .stAlert {{
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
  }}

  /* Scroll */
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 999px; }}

  /* Footer */
  .vf-footer {{
    text-align: center;
    padding: 3rem 0 1rem;
    color: var(--text-muted);
    font-size: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }}
  .vf-footer i {{
    font-size: 14px;
    margin-right: 4px;
    vertical-align: middle;
  }}

  /* char count */
  .vf-char {{
    font-size: 11px;
    color: var(--text-muted);
    text-align: right;
    margin-top: 4px;
  }}
</style>
""", unsafe_allow_html=True)

# ── Theme Toggle ──────────────────────────────────────────
col_spacer, col_toggle = st.columns([10, 1])
with col_toggle:
    toggle_icon = "sun-01" if dark else "moon-02"
    toggle_label = f'<i class="hgi hgi-stroke hgi-{toggle_icon}"></i>'
    if st.button("☀" if dark else "☾", key="theme_toggle", help="Toggle theme"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# ── Hero ──────────────────────────────────────────────────
st.markdown("""
<div class="vf-hero">
  <div class="vf-badge">
    <i class="hgi hgi-stroke hgi-voice"></i>
    Zero-Shot Voice Cloning
  </div>
  <h1>clone-her</h1>
  <p>Clone any voice from a short audio sample. Upload a reference clip, type your text, and hear it spoken in that voice.</p>
</div>
""", unsafe_allow_html=True)

# ── Connect to API ────────────────────────────────────────
SPACES = [
    "mrfakename/E2-F5-TTS",
    "abidlabs/E2-F5-TTS",
    "Hev832/E2-F5-TTS",
]

def get_client():
    from gradio_client import Client
    for space in SPACES:
        try:
            c = Client(space, verbose=False)
            return c, space
        except Exception:
            continue
    return None, None

if st.session_state.client is None:
    with st.spinner("Connecting to voice cloning engine..."):
        try:
            client, space = get_client()
            if client:
                st.session_state.client = client
                st.session_state.connected_space = space
        except ImportError:
            st.error("gradio_client not installed. Run: pip install gradio_client scipy")
            st.stop()

# ── Connection Status ─────────────────────────────────────
st.markdown('<div class="vf-card">', unsafe_allow_html=True)
st.markdown('<span class="vf-label"><i class="hgi hgi-stroke hgi-wifi-connected-01"></i>Engine Status</span>', unsafe_allow_html=True)

if st.session_state.client:
    space_short = st.session_state.connected_space.split("/")[-1] if st.session_state.connected_space else "—"
    st.markdown(f'<div class="vf-status ok"><i class="hgi hgi-stroke hgi-checkmark-circle-01"></i> Connected — {space_short}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="vf-status err"><i class="hgi hgi-stroke hgi-alert-circle"></i> All spaces unavailable. Try again later.</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Reconnect", key="reconnect"):
        st.session_state.client = None
        st.session_state.connected_space = None
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.client:
    st.stop()

# ── Upload Reference Audio ────────────────────────────────
st.markdown('<div class="vf-card">', unsafe_allow_html=True)
st.markdown('<span class="vf-label"><i class="hgi hgi-stroke hgi-upload-04"></i>Reference Voice</span>', unsafe_allow_html=True)
st.markdown('<p style="color:var(--text-secondary);font-size:0.875rem;margin-bottom:1rem;line-height:1.6;">Upload a 6–30 second clip of the voice you want to clone. Cleaner audio = better results.</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop audio here",
    type=["wav", "mp3", "m4a", "ogg", "flac", "aac", "wma", "webm", "mp4", "opus"],
    label_visibility="collapsed",
)

ref_text = st.text_input(
    "Transcript of reference audio (optional — leave blank to auto-detect)",
    placeholder="What does the person say in the uploaded clip?",
    key="ref_text_input"
)

if uploaded_file:
    try:
        audio_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        st.markdown(f'<div class="vf-status ok"><i class="hgi hgi-stroke hgi-music-note-01"></i> {uploaded_file.name} — ready</div>', unsafe_allow_html=True)
    except Exception:
        pass
    st.audio(uploaded_file, format=uploaded_file.type or "audio/wav")

st.markdown('</div>', unsafe_allow_html=True)

# ── Text Input ────────────────────────────────────────────
st.markdown('<div class="vf-card">', unsafe_allow_html=True)
st.markdown('<span class="vf-label"><i class="hgi hgi-stroke hgi-text-font"></i>Text to Synthesize</span>', unsafe_allow_html=True)

gen_text = st.text_area(
    "What should the cloned voice say?",
    placeholder="Type anything here — no length cap. Use commas and periods to control pacing.",
    height=120,
    key="gen_text_input",
    label_visibility="collapsed",
)

char_count = len(gen_text) if gen_text else 0
st.markdown(f'<div class="vf-char">{char_count} characters</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── Settings ──────────────────────────────────────────────
st.markdown('<div class="vf-card">', unsafe_allow_html=True)
st.markdown('<span class="vf-label"><i class="hgi hgi-stroke hgi-settings-01"></i>Generation Settings</span>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    speed = st.slider(
        "Playback Speed",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.05,
        format="%.2fx",
        help="Adjusts playback speed without re-generating. 1.0 = normal."
    )
with col_b:
    remove_silence = st.selectbox(
        "Remove Silence",
        options=["Yes", "No"],
        index=0,
        help="Trims leading/trailing silence from the output."
    )

st.markdown('</div>', unsafe_allow_html=True)

# ── Generate ──────────────────────────────────────────────
def save_upload_to_temp(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower() or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        uploaded_file.seek(0)
        tmp_path = tmp.name

    if suffix != ".wav":
        try:
            import subprocess
            wav_path = tmp_path.replace(suffix, ".wav")
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_path, wav_path],
                capture_output=True, timeout=30
            )
            if result.returncode == 0:
                os.unlink(tmp_path)
                return wav_path
        except Exception:
            pass
    return tmp_path

can_generate = bool(uploaded_file and gen_text and gen_text.strip())

generate_btn = st.button(
    "Generate Voice",
    disabled=not can_generate,
    type="primary",
    use_container_width=True,
    key="generate_btn"
)

if not can_generate and not generate_btn:
    missing = []
    if not uploaded_file:
        missing.append("reference audio")
    if not gen_text or not gen_text.strip():
        missing.append("text to synthesize")
    if missing:
        st.markdown(f'<div class="vf-status warn"><i class="hgi hgi-stroke hgi-alert-02"></i> Missing: {" and ".join(missing)}</div>', unsafe_allow_html=True)

if generate_btn and can_generate:
    from gradio_client import handle_file

    ref_tmp = None
    out_tmp = None

    try:
        with st.spinner("Cloning voice and generating audio..."):
            ref_tmp = save_upload_to_temp(uploaded_file)

            def call_api(client):
                return client.predict(
                    ref_audio=handle_file(ref_tmp),
                    ref_text=ref_text.strip(),
                    gen_text=gen_text.strip(),
                    remove_silence=(remove_silence == "Yes"),
                    api_name="/predict"
                )

            try:
                result = call_api(st.session_state.client)
            except Exception as e:
                err_str = str(e).lower()
                if any(k in err_str for k in ["quota", "exceeded", "unauthorized", "runtime_error"]):
                    st.warning("Current space hit quota — switching to backup...")
                    new_client, new_space = get_client()
                    if new_client:
                        st.session_state.client = new_client
                        st.session_state.connected_space = new_space
                        result = call_api(new_client)
                    else:
                        raise Exception("All spaces exhausted. Try again tomorrow or switch networks.")
                else:
                    raise

            if result and os.path.exists(result):
                sr, data = wavfile.read(result)
                new_sr = int(sr * speed) if speed != 1.0 else sr
                out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                wavfile.write(out_tmp.name, new_sr, data)
                out_tmp.close()

                with open(out_tmp.name, "rb") as f:
                    st.session_state.audio_result = f.read()

                st.rerun()
            else:
                st.error("API returned an empty result. Please try again.")

    except Exception as e:
        err_msg = str(e)
        if any(k in err_msg.lower() for k in ["quota", "exceeded"]):
            st.error("GPU quota exhausted across all spaces. Wait 24h or connect via a different network.")
        elif any(k in err_msg.lower() for k in ["runtime_error", "invalid state"]):
            st.error("Space is down. Click Reconnect to try a backup space.")
        elif any(k in err_msg.lower() for k in ["connection", "timeout"]):
            st.error("Connection timeout. Check your internet and try again.")
        else:
            st.error(f"Generation failed: {err_msg}")

    finally:
        for p in [ref_tmp, (out_tmp.name if out_tmp else None)]:
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except Exception:
                    pass

# ── Output ────────────────────────────────────────────────
if st.session_state.audio_result:
    st.markdown('<div class="vf-card">', unsafe_allow_html=True)
    st.markdown('<span class="vf-label"><i class="hgi hgi-stroke hgi-headphones"></i>Output</span>', unsafe_allow_html=True)
    st.audio(st.session_state.audio_result, format="audio/wav")

    col_dl, col_clear = st.columns([3, 1])
    with col_dl:
        st.download_button(
            label="Download Audio",
            data=st.session_state.audio_result,
            file_name="clone-her-output.wav",
            mime="audio/wav",
            use_container_width=True,
        )
    with col_clear:
        if st.button("Clear", use_container_width=True, key="clear_btn"):
            st.session_state.audio_result = None
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────
st.markdown("""
<div class="vf-footer">
  <div><i class="hgi hgi-stroke hgi-github"></i>clone-her — Voice Cloning Studio</div>
  <div><i class="hgi hgi-stroke hgi-shield-01"></i>No audio is stored or retained</div>
</div>
""", unsafe_allow_html=True)