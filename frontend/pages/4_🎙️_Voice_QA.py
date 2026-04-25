"""
4_🎙️_Voice_QA.py — RAG-powered Q&A: text chat + voice recording

Two input modes on the same page:
  • Text  — type a question → /api/ask → text answer
  • Voice — record audio   → /api/voice-query → transcription + text + MP3 answer
"""

import os
import requests
import streamlit as st
from audio_recorder_streamlit import audio_recorder

st.set_page_config(page_title="Voice Q&A", page_icon="🎙️", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ── Theme CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color:#0C0C0C; color:#F5F5F5;
    background-image: radial-gradient(ellipse at 70% 60%, rgba(212,175,55,0.04) 0%, transparent 55%);
}
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#141414,#0C0C0C) !important;
    border-right:1px solid rgba(212,175,55,0.25) !important;
}
[data-testid="stSidebar"] * { color:#F5F5F5 !important; }
header[data-testid="stHeader"] {
    background:rgba(12,12,12,0.9) !important;
    backdrop-filter:blur(12px);
    border-bottom:1px solid rgba(212,175,55,0.2) !important;
}
.yellow-divider {
    border:none; height:1px;
    background:linear-gradient(90deg,transparent,#D4AF37,#C0C0C0,transparent);
    box-shadow:0 0 10px rgba(212,175,55,0.35);
    margin:1.2rem 0;
}

/* Chat bubbles */
.bubble-user {
    background:linear-gradient(135deg,#D4AF37,#8B6914);
    color:#0C0C0C; font-weight:600; font-size:.93rem;
    border-radius:18px 18px 4px 18px;
    padding:.8rem 1.2rem;
    max-width:74%; width:fit-content;
    margin-left:auto; margin-bottom:.3rem;
    box-shadow:0 4px 15px rgba(212,175,55,0.3);
}
.bubble-ai {
    background:linear-gradient(135deg,rgba(212,175,55,0.06),rgba(20,20,20,0.95));
    border:1px solid rgba(192,192,192,0.2);
    border-left:3px solid #C0C0C0;
    color:#E8E8E8;
    border-radius:18px 18px 18px 4px;
    padding:.8rem 1.2rem;
    max-width:78%; width:fit-content;
    font-size:.93rem; line-height:1.75;
    margin-bottom:.3rem;
    box-shadow:0 4px 20px rgba(0,0,0,0.3);
}
.label-user { text-align:right; font-size:.72rem; color:#666; margin-bottom:3px; letter-spacing:0.02em; }
.label-ai   { font-size:.72rem; color:#666; margin-bottom:3px; letter-spacing:0.02em; }
.voice-badge {
    display:inline-block;
    background:linear-gradient(135deg,#D4AF37,#8B6914);
    color:#0C0C0C;
    font-size:.68rem; font-weight:800; border-radius:10px;
    padding:2px 8px; margin-left:6px; vertical-align:middle;
    box-shadow:0 2px 6px rgba(212,175,55,0.3);
}

/* Source chunks */
.source-box {
    background:rgba(255,255,255,0.02);
    border:1px solid rgba(212,175,55,0.12);
    border-radius:10px;
    padding:.65rem .95rem;
    font-size:.76rem; color:#555;
    font-family:'Courier New',monospace;
    white-space:pre-wrap; word-break:break-word;
    margin-bottom:5px;
}

/* Mic card */
.mic-card {
    background:linear-gradient(135deg,rgba(212,175,55,0.07),rgba(20,20,20,0.95));
    border:1px solid rgba(212,175,55,0.35);
    border-radius:18px;
    padding:1.4rem 1.6rem;
    text-align:center;
    margin-bottom:1rem;
    box-shadow:0 0 30px rgba(212,175,55,0.08), inset 0 1px 0 rgba(212,175,55,0.1);
}
.mic-card h4 {
    background:linear-gradient(135deg,#D4AF37,#F5E070);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    background-clip:text;
    margin-bottom:.5rem; font-size:1.1rem; font-weight:700;
}
.mic-card p { color:#888; font-size:.84rem; margin:0; }

/* RAG info card */
.rag-card {
    background:linear-gradient(135deg,rgba(192,192,192,0.05),rgba(20,20,20,0.9));
    border:1px solid rgba(192,192,192,0.15);
    border-left:3px solid #C0C0C0;
    border-radius:12px;
    padding:.95rem 1.1rem;
    font-size:.82rem; color:#888; line-height:1.75;
}

/* Inputs & buttons */
[data-testid="stTextInput"] input {
    background:#141414 !important; color:#F5F5F5 !important;
    border:1px solid rgba(212,175,55,0.4) !important;
    border-radius:8px !important;
    transition:border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
    border-color:#D4AF37 !important;
    box-shadow:0 0 0 3px rgba(212,175,55,0.15) !important;
}
[data-testid="stSelectbox"] > div {
    background:#141414 !important; color:#F5F5F5 !important;
    border:1px solid rgba(212,175,55,0.3) !important; border-radius:8px !important;
}
.stButton > button {
    background:linear-gradient(135deg,#D4AF37,#8B6914) !important;
    color:#0C0C0C !important; font-weight:700 !important;
    border:none !important; border-radius:8px !important;
    box-shadow:0 4px 15px rgba(212,175,55,0.3) !important;
    transition:all 0.3s ease !important;
}
.stButton > button:hover {
    background:linear-gradient(135deg,#F0C842,#D4AF37) !important;
    box-shadow:0 6px 25px rgba(212,175,55,0.5) !important;
    transform:translateY(-2px) !important;
}
.stTabs [data-baseweb="tab"] { color:#777 !important; font-weight:500 !important; }
.stTabs [aria-selected="true"] {
    color:#D4AF37 !important;
    border-bottom:2px solid #D4AF37 !important;
    font-weight:700 !important;
}


/* Page fade-in */
@keyframes pageIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
[data-testid="stAppViewContainer"] > section { animation:pageIn 0.55s ease both; }

/* Chat bubble entrance */
@keyframes bubbleIn {
    from { opacity:0; transform:translateY(8px) scale(0.97); }
    to   { opacity:1; transform:translateY(0) scale(1); }
}
.bubble-user { animation:bubbleIn 0.35s ease both; }
.bubble-ai   { animation:bubbleIn 0.35s 0.1s ease both; }

/* Mic card pulse ring */
@keyframes micPulse {
    0%   { box-shadow:0 0 0 0 rgba(212,175,55,0.4), 0 0 30px rgba(212,175,55,0.08); }
    60%  { box-shadow:0 0 0 18px rgba(212,175,55,0), 0 0 30px rgba(212,175,55,0.08); }
    100% { box-shadow:0 0 0 0 rgba(212,175,55,0),   0 0 30px rgba(212,175,55,0.08); }
}
.mic-card { animation:micPulse 2.5s ease-in-out infinite; }

/* Button ripple */
.stButton > button { position:relative !important; overflow:hidden !important; }
.stButton > button::after {
    content:''; position:absolute; top:50%; left:50%;
    width:0; height:0;
    background:rgba(255,255,255,0.12); border-radius:50%;
    transform:translate(-50%,-50%);
    transition:width 0.5s ease, height 0.5s ease;
}
.stButton > button:hover::after { width:300px; height:300px; }

/* Voice badge pulse */
@keyframes badgePop {
    0%   { transform:scale(1); }
    50%  { transform:scale(1.1); }
    100% { transform:scale(1); }
}
.voice-badge { animation:badgePop 2s ease-in-out infinite; }

/* Expander */
[data-testid="stExpander"] {
    border:1px solid rgba(212,175,55,0.2) !important;
    border-radius:12px !important;
    background:rgba(212,175,55,0.03) !important;
}
[data-testid="stExpander"]:hover { border-color:rgba(212,175,55,0.4) !important; }

/* Spinner */
[data-testid="stSpinner"] > div > div { border-top-color:#D4AF37 !important; }

/* Placeholder */
[data-testid="stTextInput"] input::placeholder { color:rgba(255,255,255,0.22) !important; }
</style>
""", unsafe_allow_html=True)

# ── Fetch collections ─────────────────────────────────────────────────────────
try:
    resp = requests.get(f"{BACKEND_URL}/api/documents", timeout=15)
    collections: list[str] = resp.json().get("collections", []) if resp.status_code == 200 else []
except Exception:
    collections = []

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🎙️ Voice & Text Q&A")
st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)
st.markdown(
    "Ask questions about your notes by **typing** or **speaking**. "
    "Every answer is grounded in your document — no hallucination."
)

if not collections:
    st.warning("⚠️ No documents indexed yet. Go to **📁 Upload** first.")
    st.stop()

# ── Layout ────────────────────────────────────────────────────────────────────
col_ctrl, col_chat = st.columns([1, 2], gap="large")

with col_ctrl:
    st.markdown("### ⚙️ Settings")
    active      = st.session_state.get("active_collection")
    default_idx = collections.index(active) if active in collections else 0
    selected_collection = st.selectbox("📚 Document", options=collections, index=default_idx)

    st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)
    st.markdown("""<div class="rag-card">
    <b style="color:#C0C0C0">Grounding mechanism</b><br><br>
    🔎 Question → <b>embedding vector</b><br>
    📦 ChromaDB → <b>top-4 closest chunks</b><br>
    📋 Chunks → <b>LLM context only</b><br>
    🚫 LLM <b>cannot use outside knowledge</b><br>
    ✅ Answer cites <b>your notes only</b>
    </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["qa_history"] = []
        st.rerun()
    st.caption(f"💬 {len(st.session_state.get('qa_history', []))} messages")

with col_chat:

    # ── Initialise history ────────────────────────────────────────────────────
    if "qa_history" not in st.session_state:
        st.session_state["qa_history"] = []
    if "last_audio_hash" not in st.session_state:
        st.session_state["last_audio_hash"] = None

    # ── Render chat history ───────────────────────────────────────────────────
    history = st.session_state["qa_history"]

    if not history:
        st.markdown("""
        <div style="text-align:center;padding:2.5rem;color:#444;
                    border:2px dashed #222;border-radius:12px;margin-bottom:1rem;">
            <div style="font-size:2.5rem">💬</div>
            <div style="margin-top:.5rem;font-size:.95rem;">
                Type or speak your first question below
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        for turn in history:
            mode_badge = '<span class="voice-badge">🎙️ Voice</span>' if turn.get("is_voice") else ""
            st.markdown(f'<div class="label-user">You {mode_badge}</div>'
                        f'<div class="bubble-user">{turn["question"]}</div>', unsafe_allow_html=True)

            answer_html = turn["answer"].replace("\\n", "<br>")
            st.markdown(f'<div class="label-ai">🤖 AI (from your notes)</div>'
                        f'<div class="bubble-ai">{answer_html}</div>', unsafe_allow_html=True)

            # Voice answer playback
            if turn.get("audio_filename"):
                audio_url = f"{BACKEND_URL}/audio/{turn['audio_filename']}"
                try:
                    audio_resp = requests.get(audio_url, timeout=10)
                    if audio_resp.status_code == 200:
                        st.audio(audio_resp.content, format="audio/mp3")
                except Exception:
                    pass

            # Source chunks
            if turn.get("source_chunks"):
                with st.expander("🔍 Source chunks (RAG context)", expanded=False):
                    for i, chunk in enumerate(turn["source_chunks"], 1):
                        preview = chunk[:400] + ("…" if len(chunk) > 400 else "")
                        st.markdown(f'<div class="source-box">[Chunk {i}] {preview}</div>',
                                    unsafe_allow_html=True)
            st.markdown("")

    st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

    # ── Input tabs: Text | Voice ──────────────────────────────────────────────
    tab_text, tab_voice = st.tabs(["⌨️  Text Question", "🎙️  Voice Question"])

    # ── TEXT TAB ──────────────────────────────────────────────────────────────
    with tab_text:
        with st.form("text_qa_form", clear_on_submit=True):
            q_col, btn_col = st.columns([5, 1])
            with q_col:
                question_text = st.text_input(
                    "question", placeholder="e.g. What is photosynthesis?",
                    label_visibility="collapsed",
                )
            with btn_col:
                text_submit = st.form_submit_button("Ask ➤", use_container_width=True)

        if text_submit and question_text.strip():
            with st.spinner("Searching your notes…"):
                try:
                    r = requests.post(
                        f"{BACKEND_URL}/api/ask",
                        json={"collection_name": selected_collection,
                              "question": question_text.strip()},
                        timeout=60,
                    )
                    if r.status_code == 200:
                        d = r.json()
                        st.session_state["qa_history"].append({
                            "question":      d["question"],
                            "answer":        d["answer"],
                            "source_chunks": d.get("source_chunks", []),
                            "is_voice":      False,
                            "audio_filename": None,
                        })
                        st.rerun()
                    else:
                        st.error(r.json().get("detail", r.text))
                except requests.exceptions.ConnectionError:
                    st.error("❌ Backend unreachable.")
                except Exception as e:
                    st.error(f"Error: {e}")
        elif text_submit:
            st.warning("Please type a question.")

    # ── VOICE TAB ─────────────────────────────────────────────────────────────
    with tab_voice:
        st.markdown("""<div class="mic-card">
            <h4>🎙️ Click the microphone to record</h4>
            <p>Speak your question clearly · Click again to stop · Auto-submits when done</p>
        </div>""", unsafe_allow_html=True)

        # audio_recorder returns bytes when recording is done, None otherwise
        audio_bytes = audio_recorder(
            text="",
            recording_color="#D4AF37",
            neutral_color="#555555",
            icon_size="3x",
            pause_threshold=2.5,   # stop after 2.5s silence
        )

        # Deduplicate: only process if this is a NEW recording
        import hashlib
        audio_hash = hashlib.md5(audio_bytes).hexdigest() if audio_bytes else None
        already_processed = audio_hash and audio_hash == st.session_state.get("last_audio_hash")

        if audio_bytes and not already_processed:
            st.session_state["last_audio_hash"] = audio_hash
            st.success("✅ Recording captured — submitting…")
            st.audio(audio_bytes, format="audio/wav")  # playback before sending

            with st.spinner("Transcribing → Retrieving → Answering → Converting to speech…"):
                try:
                    r = requests.post(
                        f"{BACKEND_URL}/api/voice-query",
                        data={"collection_name": selected_collection},
                        files={"audio": ("recording.wav", audio_bytes, "audio/wav")},
                        timeout=120,
                    )
                    if r.status_code == 200:
                        d = r.json()
                        st.session_state["qa_history"].append({
                            "question":       d["transcribed_question"],
                            "answer":         d["answer"],
                            "source_chunks":  [],
                            "is_voice":       True,
                            "audio_filename": d["audio_filename"],
                        })
                        st.rerun()
                    else:
                        st.error(r.json().get("detail", r.text))
                except requests.exceptions.ConnectionError:
                    st.error("❌ Backend unreachable.")
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out. Try a shorter question.")
                except Exception as e:
                    st.error(f"Error: {e}")
