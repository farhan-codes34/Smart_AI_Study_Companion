"""
1_📁_Upload.py — Document upload page

Flow on this page:
  1. User picks a file (PDF / TXT / image)
  2. Page sends it to POST /api/upload
  3. Backend: saves → extracts text → chunks → embeds → stores in ChromaDB
  4. Page shows success + chunk count, and stores collection name in session_state
     so other pages (Explain, Quiz, Voice) know which document is active
"""

import os
import streamlit as st
import requests
from pathlib import Path

st.set_page_config(page_title="Upload Notes", page_icon="📁", layout="wide")

# ── Theme CSS (matches portfolio: black + #FCB800) ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color:#0C0C0C; color:#F5F5F5;
    background-image: radial-gradient(ellipse at 10% 50%, rgba(212,175,55,0.04) 0%, transparent 55%);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#141414,#0C0C0C) !important;
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

/* Upload drop-zone */
[data-testid="stFileUploader"] {
    background:rgba(212,175,55,0.04) !important;
    border:2px dashed rgba(212,175,55,0.5) !important;
    border-radius:14px !important;
    padding:1.2rem !important;
    transition:all 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color:rgba(212,175,55,0.8) !important;
    background:rgba(212,175,55,0.07) !important;
}
[data-testid="stFileUploader"] * { color:#F5F5F5 !important; }

/* Result cards */
.result-card { border-radius:14px; padding:1.3rem 1.5rem; margin-top:1rem; }
.result-ok {
    background:linear-gradient(135deg,rgba(212,175,55,0.08),rgba(20,20,20,0.95));
    border:1px solid rgba(212,175,55,0.4);
    box-shadow:0 0 20px rgba(212,175,55,0.1);
}
.result-err {
    background:rgba(42,0,0,0.8);
    border:1px solid rgba(255,68,68,0.5);
    color:#ff6666;
}

/* Document chips */
.doc-chip {
    display:inline-block;
    background:linear-gradient(135deg,#D4AF37,#8B6914);
    color:#0C0C0C;
    font-weight:700;
    border-radius:20px;
    padding:5px 16px;
    margin:4px 4px 4px 0;
    font-size:0.83rem;
    box-shadow:0 2px 8px rgba(212,175,55,0.3);
}

/* Info card */
.info-card {
    background:linear-gradient(135deg,rgba(212,175,55,0.06),rgba(20,20,20,0.9));
    border:1px solid rgba(212,175,55,0.2);
    border-left:3px solid #D4AF37;
    border-radius:12px;
    padding:1.1rem 1.3rem;
    font-size:0.88rem;
    color:#A0A0A0;
    line-height:1.75;
    box-shadow:inset 0 1px 0 rgba(212,175,55,0.08);
}

/* Buttons */
.stButton > button {
    background:linear-gradient(135deg,#D4AF37,#8B6914) !important;
    color:#0C0C0C !important; font-weight:700 !important;
    border:none !important; border-radius:8px !important;
    padding:0.5rem 1.5rem !important;
    box-shadow:0 4px 15px rgba(212,175,55,0.3) !important;
    transition:all 0.3s ease !important;
}
.stButton > button:hover {
    background:linear-gradient(135deg,#F0C842,#D4AF37) !important;
    box-shadow:0 6px 25px rgba(212,175,55,0.5) !important;
    transform:translateY(-2px) !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div {
    background:#141414 !important; color:#F5F5F5 !important;
    border:1px solid rgba(212,175,55,0.3) !important;
    border-radius:8px !important;
}


/* Page fade-in */
@keyframes pageIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
[data-testid="stAppViewContainer"] > section { animation:pageIn 0.55s ease both; }

/* File uploader pulse border */
@keyframes borderPulse {
    0%,100% { border-color:rgba(212,175,55,0.4) !important; }
    50%      { border-color:rgba(212,175,55,0.8) !important; }
}
[data-testid="stFileUploader"] { animation:borderPulse 3s ease-in-out infinite; }

/* Doc chip shine */
.doc-chip { position:relative; overflow:hidden; }
.doc-chip::after {
    content:'';
    position:absolute; top:0; left:-60%;
    width:40%; height:100%;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,0.25),transparent);
    transform:skewX(-20deg);
    animation:chipShine 3s ease-in-out infinite;
}
@keyframes chipShine {
    0%  { left:-60%; }
    40%,100% { left:140%; }
}

/* Expander */
[data-testid="stExpander"] {
    border:1px solid rgba(212,175,55,0.2) !important;
    border-radius:12px !important;
    background:rgba(212,175,55,0.03) !important;
}
[data-testid="stExpander"]:hover { border-color:rgba(212,175,55,0.4) !important; }

/* Success/info/warning Streamlit boxes */
[data-testid="stAlert"] { border-radius:12px !important; }

/* Spinner */
[data-testid="stSpinner"] > div > div { border-top-color:#D4AF37 !important; }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📁 Upload Your Notes")
st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)
st.markdown(
    "Upload your lecture notes and the app will **extract text → split into chunks → "
    "generate embeddings → store in ChromaDB** so all other features can use them."
)

# ── Two-column layout: uploader left, instructions right ──────────────────────
col_upload, col_info = st.columns([3, 2], gap="large")

with col_info:
    st.markdown("""<div class="info-card">
    <b style="color:#D4AF37">What happens when you upload?</b><br><br>
    1️⃣ &nbsp;<b>Text extraction</b> — PDF pages read with pdfplumber;
    images run through Tesseract OCR; TXT files read directly.<br><br>
    2️⃣ &nbsp;<b>Chunking</b> — Text split into ~500-token pieces with
    50-token overlap so no idea is cut in half.<br><br>
    3️⃣ &nbsp;<b>Embedding</b> — Each chunk converted to a 384-dim vector
    using <code>all-MiniLM-L6-v2</code> (runs locally).<br><br>
    4️⃣ &nbsp;<b>Vector store</b> — Chunks + vectors saved to ChromaDB
    on disk for instant retrieval later.
    </div>""", unsafe_allow_html=True)

with col_upload:
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "txt", "md", "png", "jpg", "jpeg", "webp", "bmp", "tiff"],
        help="PDF, plain text, or an image of your notes",
    )

    if uploaded_file:
        # Show file info
        file_bytes = uploaded_file.getvalue()
        size_kb = len(file_bytes) / 1024
        size_mb = size_kb / 1024
        MAX_MB  = 50

        st.markdown(f"""
        <div style="background:#111;border:1px solid #333;border-radius:8px;
                    padding:0.8rem 1rem;margin:0.5rem 0;font-size:0.88rem;color:#CCC;">
            📄 <b style="color:#FFF">{uploaded_file.name}</b>
            &nbsp;·&nbsp; {size_kb:.1f} KB
            &nbsp;·&nbsp; {uploaded_file.type or 'unknown type'}
        </div>
        """, unsafe_allow_html=True)

        if size_mb > MAX_MB:
            st.error(f"❌ File is {size_mb:.1f} MB — exceeds the 50 MB limit. Please use a smaller file.")
        elif st.button("⚡ Upload & Index Document"):
            with st.spinner("Extracting text, generating embeddings, storing in ChromaDB… (first run may take ~30s while the model loads)"):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/upload",
                        files={"file": (
                            uploaded_file.name,
                            file_bytes,
                            uploaded_file.type or "application/octet-stream",
                        )},
                        timeout=300,  # 5 min — model loads on first request (~90MB download)
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # Save active collection to session so other pages can use it
                        st.session_state["active_collection"] = data["collection_name"]
                        st.session_state["active_filename"]   = data["filename"]

                        st.markdown(f"""
                        <div class="result-card result-ok">
                            ✅ <b>Indexed successfully!</b><br><br>
                            📄 File: <code>{data['filename']}</code><br>
                            🗂️ Collection: <code>{data['collection_name']}</code><br>
                            🔢 Chunks stored: <b>{data['chunks_stored']}</b><br><br>
                            <span style="color:#CCC;font-size:0.88rem">
                            You can now use <b>Explain</b>, <b>Quiz</b>, and
                            <b>Voice Q&A</b> on this document.
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                    else:
                        detail = response.json().get("detail", response.text)
                        st.markdown(f"""
                        <div class="result-card result-err">
                            ❌ <b>Upload failed</b><br>{detail}
                        </div>
                        """, unsafe_allow_html=True)

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot reach the backend. Is `uvicorn` running?")
                except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
                    st.warning(
                        "⏱️ The request is still processing in the background "
                        "(model may still be loading). "
                        "Wait 30 seconds then **refresh the page** — "
                        "your document may already be indexed."
                    )
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

# ── Currently indexed documents ───────────────────────────────────────────────
st.markdown("### 📚 Indexed Documents")
st.caption("Documents already stored in ChromaDB and ready to use.")

try:
    resp = requests.get(f"{BACKEND_URL}/api/documents", timeout=15)
    if resp.status_code == 200:
        collections: list[str] = resp.json().get("collections", [])
        if collections:
            chips_html = " ".join(
                f'<span class="doc-chip">{name}</span>' for name in collections
            )
            st.markdown(chips_html, unsafe_allow_html=True)

            # Let user set the active document from the list
            st.markdown("<br>", unsafe_allow_html=True)
            selected = st.selectbox(
                "Set active document for Explain / Quiz / Voice Q&A:",
                options=collections,
                index=collections.index(st.session_state.get("active_collection", collections[0]))
                       if st.session_state.get("active_collection") in collections else 0,
            )
            if st.button("✅ Use This Document"):
                st.session_state["active_collection"] = selected
                st.session_state["active_filename"]   = selected
                st.success(f"Active document set to **{selected}**")
        else:
            st.info("No documents indexed yet — upload one above to get started.")
    else:
        st.warning("Could not fetch document list from backend.")
except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout,
        requests.exceptions.Timeout):
    st.warning("⏳ Backend is starting up or busy — refresh in a few seconds.")

# ── Session state indicator ───────────────────────────────────────────────────
if st.session_state.get("active_collection"):
    st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)
    st.markdown(
        f"🟡 **Active document:** `{st.session_state['active_collection']}`  "
        f"— this is what Explain, Quiz, and Voice Q&A will use."
    )
