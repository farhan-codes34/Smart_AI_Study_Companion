"""
streamlit_app.py — Main Streamlit entry point
Theme: Black background + #FCB800 golden yellow (Farhan Ejaz portfolio)
"""

import streamlit as st
import os
import requests

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart AI Study Companion",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — matches portfolio aesthetic ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0C0C0C;
    color: #F5F5F5;
    font-family: 'Inter', sans-serif;
    background-image:
        radial-gradient(ellipse at 15% 40%, rgba(212,175,55,0.05) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 10%, rgba(192,192,192,0.03) 0%, transparent 50%);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #141414 0%, #0C0C0C 100%) !important;
    border-right: 1px solid rgba(212,175,55,0.3) !important;
}
[data-testid="stSidebar"] * { color: #F5F5F5 !important; }

/* ── Top nav bar ── */
header[data-testid="stHeader"] {
    background: rgba(12,12,12,0.9) !important;
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(212,175,55,0.25) !important;
}

/* ── Hero title ── */
.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #D4AF37 0%, #F5E070 50%, #C0C0C0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}
.hero-sub {
    font-size: 1.4rem;
    font-weight: 600;
    color: #E8E8E8;
    margin-bottom: 1rem;
}
.hero-desc {
    font-size: 1rem;
    color: #A0A0A0;
    max-width: 620px;
    line-height: 1.75;
}

/* ── Glowing divider ── */
.yellow-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #D4AF37 40%, #C0C0C0 60%, transparent 100%);
    box-shadow: 0 0 12px rgba(212,175,55,0.4), 0 0 24px rgba(212,175,55,0.1);
    margin: 1.8rem 0;
}

/* ── Feature cards — glassmorphism ── */
.feature-card {
    background: linear-gradient(135deg, rgba(212,175,55,0.07) 0%, rgba(20,20,20,0.9) 100%);
    border: 1px solid rgba(212,175,55,0.25);
    border-radius: 16px;
    padding: 1.2rem 1.1rem;
    height: 160px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(212,175,55,0.1);
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    overflow: hidden;
}
.feature-card:hover {
    transform: translateY(-5px);
    border-color: rgba(212,175,55,0.55);
    box-shadow: 0 12px 40px rgba(212,175,55,0.15), 0 4px 12px rgba(0,0,0,0.5);
}
.feature-card h4 {
    background: linear-gradient(135deg, #D4AF37, #F5E070);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 0.95rem;
    font-weight: 700;
    margin-bottom: 0.45rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.feature-card p {
    color: #A0A0A0;
    font-size: 0.82rem;
    margin: 0;
    line-height: 1.55;
}

/* ── Step rows ── */
.step-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #D4AF37, #8B6914);
    color: #0C0C0C;
    font-weight: 800;
    border-radius: 50%;
    width: 34px;
    height: 34px;
    font-size: 0.9rem;
    margin-right: 0.75rem;
    flex-shrink: 0;
    box-shadow: 0 0 10px rgba(212,175,55,0.4);
}
.step-row {
    display: flex;
    align-items: center;
    background: linear-gradient(135deg, rgba(212,175,55,0.05), rgba(20,20,20,0.8));
    border: 1px solid rgba(212,175,55,0.15);
    border-left: 3px solid #D4AF37;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    color: #E8E8E8;
    font-size: 0.95rem;
    transition: all 0.2s ease;
}
.step-row:hover {
    background: linear-gradient(135deg, rgba(212,175,55,0.1), rgba(20,20,20,0.9));
    border-color: rgba(212,175,55,0.35);
}

/* ── Status box ── */
.status-ok {
    background: linear-gradient(135deg, rgba(212,175,55,0.08), rgba(20,20,20,0.9));
    border: 1px solid rgba(212,175,55,0.4);
    border-radius: 10px;
    padding: 0.9rem 1.3rem;
    color: #D4AF37;
    font-weight: 600;
    box-shadow: 0 0 20px rgba(212,175,55,0.1);
}
.status-err {
    background: rgba(42,0,0,0.8);
    border: 1px solid rgba(255,68,68,0.5);
    border-radius: 10px;
    padding: 0.9rem 1.3rem;
    color: #ff6666;
}

/* ── Gradient buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #D4AF37 0%, #8B6914 100%) !important;
    color: #0C0C0C !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 15px rgba(212,175,55,0.3) !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #F0C842 0%, #D4AF37 100%) !important;
    box-shadow: 0 6px 25px rgba(212,175,55,0.5) !important;
    transform: translateY(-2px) !important;
}

/* ── Table ── */
thead tr th {
    background: linear-gradient(135deg, #D4AF37, #8B6914) !important;
    color: #0C0C0C !important;
    font-weight: 700 !important;
}
tbody tr:nth-child(even) { background-color: rgba(212,175,55,0.04); }
tbody tr:hover { background-color: rgba(212,175,55,0.07) !important; }


/* ── Page fade-in ── */
@keyframes pageIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
[data-testid="stAppViewContainer"] > section { animation: pageIn 0.55s ease both; }

/* ── Hero title shimmer ── */
@keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
}
.hero-title {
    background: linear-gradient(110deg, #8B6914 0%, #D4AF37 20%, #F5E070 40%, #D4AF37 60%, #C0C0C0 80%, #D4AF37 100%);
    background-size: 250% auto;
    animation: shimmer 5s linear infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ── Card shine sweep on hover ── */
.feature-card { position: relative; overflow: hidden; }
.feature-card::before {
    content: '';
    position: absolute;
    top: 0; left: -80%;
    width: 50%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(245,224,112,0.08), transparent);
    transform: skewX(-15deg);
    transition: left 0.65s ease;
    pointer-events: none;
}
.feature-card:hover::before { left: 140%; }

/* ── Streamlit alert / info / warning overrides ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    backdrop-filter: blur(8px) !important;
}
div[data-baseweb="notification"] {
    border-radius: 12px !important;
}

/* ── Spinner colour ── */
[data-testid="stSpinner"] > div > div {
    border-top-color: #D4AF37 !important;
}

/* ── Caption / small text ── */
[data-testid="stCaptionContainer"] p { color: #666 !important; }

/* ── Sidebar nav links glow on hover ── */
[data-testid="stSidebar"] a:hover { color: #D4AF37 !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid rgba(212,175,55,0.2) !important;
    border-radius: 12px !important;
    background: rgba(212,175,55,0.03) !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(212,175,55,0.4) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 AI Study Companion")
    st.markdown("<hr style='border:1px solid #D4AF37;margin:0.5rem 0 1rem'>",
                unsafe_allow_html=True)
    st.markdown("""
**Navigate:**

📁 **Upload** — Add your notes

💡 **Explain** — Simplify your notes

🧪 **Quiz** — Auto-generated MCQs

🎙️ **Voice Q&A** — Ask by voice

🃏 **Flashcards** — Study key terms
""")
    st.markdown("<hr style='border:1px solid #333;'>", unsafe_allow_html=True)
    st.caption("Powered by Groq · Llama-3 · RAG")
    st.caption("Final-Year Project · GenAI Demo")

# ── Hero section ──────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">Smart AI Study Companion</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Your personal AI tutor — powered by Generative AI</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-desc">Upload your lecture notes and let AI explain them in plain language, generate quizzes, and answer your questions by voice — all grounded in your own material.</p>', unsafe_allow_html=True)

st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

# ── Feature cards ─────────────────────────────────────────────────────────────
st.markdown("### What You Can Do")
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown("""<div class="feature-card">
        <h4>📁 Upload</h4>
        <p>PDF, TXT, or image notes chunked and stored as embeddings.</p>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown("""<div class="feature-card">
        <h4>💡 Explain</h4>
        <p>Notes rewritten in plain language with key points and analogy.</p>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown("""<div class="feature-card">
        <h4>🧪 Quiz</h4>
        <p>Auto-generated MCQs from your notes with scoring.</p>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown("""<div class="feature-card">
        <h4>🎙️ Voice Q&A</h4>
        <p>Speak a question, get an answer grounded in your notes.</p>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown("""<div class="feature-card">
        <h4>🃏 Flashcards</h4>
        <p>Flip cards with key terms and definitions from your notes.</p>
    </div>""", unsafe_allow_html=True)

st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

# ── How to get started ────────────────────────────────────────────────────────
st.markdown("### How to Get Started")

steps = [
    ("1", "Go to  📁 Upload  and upload your lecture notes (PDF, TXT, or image)"),
    ("2", "Visit  💡 Explain  to get a simplified breakdown of your notes"),
    ("3", "Try  🃏 Flashcards  to study key terms with interactive flip cards"),
    ("4", "Take  🧪 Quiz  to test yourself with auto-generated MCQs"),
    ("5", "Use  🎙️ Voice Q&A  to ask questions out loud and hear answers back"),
]
for num, text in steps:
    st.markdown(
        f'<div class="step-row"><span class="step-badge">{num}</span>{text}</div>',
        unsafe_allow_html=True
    )

st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

# ── GenAI concepts table ──────────────────────────────────────────────────────
st.markdown("### Core GenAI Concepts Used")
st.markdown("""
| Concept | Where Used |
|---|---|
| **LLM via API** | All text generation (Groq · Llama-3.3-70B) |
| **Prompt Engineering** | Custom prompts for explain, quiz, flashcards & Q&A |
| **RAG** | Voice Q&A retrieves context before answering |
| **Embeddings** | `all-MiniLM-L6-v2` encodes every text chunk |
| **Vector Database** | ChromaDB stores and searches embeddings |
| **Text Chunking** | 500-token chunks with 50-token overlap |
| **Speech-to-Text** | OpenAI Whisper transcribes voice questions |
| **Text-to-Speech** | gTTS converts answers to audio |
| **Structured Output** | LLM returns quiz & flashcards as strict JSON |
| **Grounded Generation** | Q&A and flashcard prompts forbid outside context |
""")

st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

# ── Backend status ────────────────────────────────────────────────────────────
st.markdown("### Backend Status")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

try:
    resp = requests.get(f"{BACKEND_URL}/health", timeout=3)
    if resp.status_code == 200:
        data = resp.json()
        st.markdown(
            f'<div class="status-ok">✅ API is running — v{data["version"]} &nbsp;|&nbsp; {data["message"]}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="status-err">⚠️ API responded with unexpected status.</div>',
                    unsafe_allow_html=True)
except requests.exceptions.ConnectionError:
    st.markdown("""<div class="status-err">
    ❌ Cannot reach the FastAPI backend. Start it with:<br><br>
    <code>cd backend &nbsp;&amp;&amp;&nbsp; uv run uvicorn app.main:app --reload</code>
    </div>""", unsafe_allow_html=True)
