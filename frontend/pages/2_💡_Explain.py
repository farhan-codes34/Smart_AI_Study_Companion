"""
2_💡_Explain.py — Simplified Explanation page

Flow:
  1. User selects an indexed document (or uses the active one from Upload page)
  2. Optionally types a specific topic to focus on
  3. Page calls POST /api/explain
  4. Backend: RAG retrieval → LLM → JSON response
  5. Page renders: explanation paragraphs, key points, analogy, source chunks
"""

import os
import requests
import streamlit as st

st.set_page_config(page_title="Explain Notes", page_icon="💡", layout="wide")

# Deployment-ready: BACKEND_URL from environment variable, fallback to localhost
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ── Theme CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color:#0C0C0C; color:#F5F5F5;
    background-image: radial-gradient(ellipse at 80% 30%, rgba(212,175,55,0.04) 0%, transparent 55%);
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

/* Explanation card — glassmorphism */
.explain-card {
    background:linear-gradient(135deg,rgba(212,175,55,0.07),rgba(20,20,20,0.95));
    border:1px solid rgba(212,175,55,0.25);
    border-radius:16px;
    padding:1.6rem 1.9rem;
    margin-bottom:1.2rem;
    line-height:1.8;
    box-shadow:0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(212,175,55,0.1);
    backdrop-filter:blur(10px);
}
.explain-card h3 {
    background:linear-gradient(135deg,#D4AF37,#F5E070);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    background-clip:text;
    margin-bottom:0.8rem;
    font-size:1rem;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:0.08em;
}

/* Key points */
.key-point {
    display:flex; align-items:flex-start; gap:0.8rem;
    background:rgba(192,192,192,0.04);
    border-left:3px solid #C0C0C0;
    border-radius:0 10px 10px 0;
    padding:0.65rem 1rem;
    margin-bottom:0.5rem;
    font-size:0.93rem; color:#E0E0E0;
    transition:all 0.2s ease;
}
.key-point:hover { background:rgba(192,192,192,0.08); border-left-color:#D4AF37; }
.kp-dot { color:#D4AF37; font-weight:900; font-size:1rem; flex-shrink:0; margin-top:2px; }

/* Analogy card */
.analogy-card {
    background:linear-gradient(135deg,rgba(139,105,20,0.15),rgba(20,20,20,0.95));
    border:1px solid rgba(212,175,55,0.35);
    border-radius:16px;
    padding:1.3rem 1.6rem;
    margin-bottom:1.2rem;
    box-shadow:0 0 30px rgba(212,175,55,0.08), inset 0 1px 0 rgba(212,175,55,0.15);
}
.analogy-card h3 {
    background:linear-gradient(135deg,#D4AF37,#F5E070);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    background-clip:text;
    margin-bottom:0.5rem; font-size:0.95rem; font-weight:700;
}
.analogy-card p { color:#D8D8D8; font-style:italic; font-size:1.02rem; margin:0; line-height:1.7; }

/* Source chunks */
.source-chunk {
    background:rgba(255,255,255,0.02);
    border:1px solid rgba(212,175,55,0.12);
    border-radius:10px;
    padding:0.85rem 1rem;
    font-size:0.8rem; color:#666;
    margin-bottom:0.5rem;
    font-family:'Courier New',monospace;
    white-space:pre-wrap; word-break:break-word;
}

/* Inputs */
[data-testid="stSelectbox"] > div {
    background:#141414 !important; color:#F5F5F5 !important;
    border:1px solid rgba(212,175,55,0.3) !important; border-radius:8px !important;
}
[data-testid="stTextInput"] input {
    background:#141414 !important; color:#F5F5F5 !important;
    border:1px solid rgba(212,175,55,0.35) !important;
    border-radius:8px !important;
    box-shadow:0 0 0 0 rgba(212,175,55,0) !important;
    transition:border-color 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stTextInput"] input:focus {
    border-color:#D4AF37 !important;
    box-shadow:0 0 0 3px rgba(212,175,55,0.15) !important;
}

/* Buttons */
.stButton > button {
    background:linear-gradient(135deg,#D4AF37,#8B6914) !important;
    color:#0C0C0C !important; font-weight:700 !important;
    border:none !important; border-radius:8px !important;
    padding:0.5rem 2rem !important;
    box-shadow:0 4px 15px rgba(212,175,55,0.3) !important;
    transition:all 0.3s ease !important;
    position:relative !important; overflow:hidden !important;
}
.stButton > button::after {
    content:'';
    position:absolute; top:50%; left:50%;
    width:0; height:0;
    background:rgba(255,255,255,0.15);
    border-radius:50%;
    transform:translate(-50%,-50%);
    transition:width 0.5s ease, height 0.5s ease;
}
.stButton > button:hover::after { width:250px; height:250px; }
.stButton > button:hover {
    background:linear-gradient(135deg,#F0C842,#D4AF37) !important;
    box-shadow:0 6px 25px rgba(212,175,55,0.5) !important;
    transform:translateY(-2px) !important;
}


/* Page fade-in */
@keyframes pageIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
[data-testid="stAppViewContainer"] > section { animation:pageIn 0.55s ease both; }

/* Card entrance animation */
@keyframes cardIn {
    from { opacity:0; transform:translateY(16px); }
    to   { opacity:1; transform:translateY(0); }
}
.explain-card { animation:cardIn 0.45s ease both; }
.explain-card:nth-child(2) { animation-delay:0.1s; }
.explain-card:nth-child(3) { animation-delay:0.2s; }
.analogy-card { animation:cardIn 0.45s 0.25s ease both; }

/* Explain card shine */
.explain-card { position:relative; overflow:hidden; }
.explain-card::before {
    content:'';
    position:absolute; top:0; left:-70%;
    width:45%; height:100%;
    background:linear-gradient(90deg,transparent,rgba(245,224,112,0.06),transparent);
    transform:skewX(-15deg);
    transition:left 0.7s ease;
    pointer-events:none;
}
.explain-card:hover::before { left:130%; }

/* Expander */
[data-testid="stExpander"] {
    border:1px solid rgba(212,175,55,0.2) !important;
    border-radius:12px !important;
    background:rgba(212,175,55,0.03) !important;
}
[data-testid="stExpander"]:hover { border-color:rgba(212,175,55,0.4) !important; }

/* Spinner */
[data-testid="stSpinner"] > div > div { border-top-color:#D4AF37 !important; }

/* Placeholder hint text */
.stTextInput > div > div > input::placeholder { color:rgba(255,255,255,0.25) !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 💡 Simplified Explanation")
st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)
st.markdown(
    "Select a document and let the AI explain it in plain language — "
    "with **key points** and a **real-life analogy** — all grounded in YOUR notes."
)

# ── Fetch available collections ───────────────────────────────────────────────
try:
    resp = requests.get(f"{BACKEND_URL}/api/documents", timeout=15)
    collections: list[str] = resp.json().get("collections", []) if resp.status_code == 200 else []
except Exception:
    collections = []

if not collections:
    st.warning(
        "⚠️ No documents indexed yet. "
        "Go to **📁 Upload** first and upload your notes."
    )
    st.stop()

# ── Controls ──────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 3], gap="large")

with col_left:
    st.markdown("### ⚙️ Settings")

    # Pre-select the active document from the Upload page if available
    active = st.session_state.get("active_collection")
    default_idx = collections.index(active) if active in collections else 0

    selected_collection = st.selectbox(
        "📚 Select document",
        options=collections,
        index=default_idx,
        help="Choose which indexed document to explain.",
    )

    topic = st.text_input(
        "🔍 Topic to focus on (optional)",
        placeholder="e.g. photosynthesis, Newton's laws, TCP/IP...",
        help="Leave blank to get a general overview of the whole document.",
    )

    explain_btn = st.button("✨ Generate Explanation", use_container_width=True)

    st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

    # GenAI concept callout
    st.markdown("""<div style="background:#0d0d0d;border:1px solid #333;
    border-left:4px solid #D4AF37;border-radius:6px;padding:1rem;font-size:0.85rem;color:#AAA;">
    <b style="color:#D4AF37">How it works (RAG)</b><br><br>
    1. Your topic is converted to an <b>embedding vector</b><br>
    2. ChromaDB finds the <b>most relevant chunks</b> from your document<br>
    3. Those chunks are injected into the <b>LLM prompt</b> as context<br>
    4. Groq Llama-3 explains <b>only what's in your notes</b>
    </div>""", unsafe_allow_html=True)

with col_right:
    if explain_btn:
        with st.spinner("Retrieving relevant content and generating explanation…"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/explain",
                    json={
                        "collection_name": selected_collection,
                        "topic": topic.strip() if topic else None,
                    },
                    timeout=60,
                )

                if response.status_code == 200:
                    data = response.json()

                    # ── Explanation ───────────────────────────────────────────
                    st.markdown(f"""<div class="explain-card">
                        <h3>📖 Explanation</h3>
                        <p style="color:#DDD;line-height:1.8;">
                        {data['explanation'].replace(chr(10), '<br>')}
                        </p>
                    </div>""", unsafe_allow_html=True)

                    # ── Key Points ────────────────────────────────────────────
                    st.markdown('<div class="explain-card"><h3>🎯 Key Points</h3>', unsafe_allow_html=True)
                    for kp in data["key_points"]:
                        st.markdown(
                            f'<div class="key-point"><span class="kp-dot">▶</span>{kp}</div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown('</div>', unsafe_allow_html=True)

                    # ── Analogy ───────────────────────────────────────────────
                    st.markdown(f"""<div class="analogy-card">
                        <h3>💡 Real-Life Analogy</h3>
                        <p>{data['analogy']}</p>
                    </div>""", unsafe_allow_html=True)

                    # ── Source Chunks (transparency) ──────────────────────────
                    with st.expander("🔍 View source chunks used (RAG context)", expanded=False):
                        st.caption(
                            "These are the exact parts of your document the AI used. "
                            "This is RAG in action — the answer is grounded in your notes."
                        )
                        for i, chunk in enumerate(data.get("source_chunks", []), 1):
                            st.markdown(
                                f'<div class="source-chunk"><b>[Chunk {i}]</b>\n{chunk}</div>',
                                unsafe_allow_html=True,
                            )

                else:
                    detail = response.json().get("detail", response.text)
                    st.error(f"❌ {detail}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot reach the backend. Is `uvicorn` running?")
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. Try a shorter document or topic.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
    else:
        # Placeholder when nothing has been generated yet
        st.markdown("""
        <div style="background:#111;border:2px dashed #333;border-radius:12px;
                    padding:3rem;text-align:center;color:#555;margin-top:1rem;">
            <div style="font-size:3rem">💡</div>
            <div style="font-size:1rem;margin-top:0.5rem;">
                Select a document and click <b style="color:#D4AF37">Generate Explanation</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
