"""
5_🃏_Flashcards.py — AI-Generated Study Flashcards

Flow:
  1. User selects an indexed document + number of cards
  2. Page calls POST /api/flashcards
  3. Backend: broad RAG retrieval → LLM → term-definition JSON
  4. Page renders interactive 3D flip cards (CSS transform)
  5. User navigates prev/next, shuffles, marks cards as known
"""

import os
import random
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Flashcards", page_icon="🃏", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ── Theme CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color:#0C0C0C; color:#F5F5F5;
    font-family:'Inter',sans-serif;
    background-image: radial-gradient(ellipse at 60% 20%, rgba(212,175,55,0.05) 0%, transparent 55%);
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

/* Settings card */
.settings-card {
    background:linear-gradient(135deg,rgba(212,175,55,0.06),rgba(20,20,20,0.95));
    border:1px solid rgba(212,175,55,0.2);
    border-left:3px solid #D4AF37;
    border-radius:12px;
    padding:1rem 1.2rem;
    font-size:0.84rem; color:#AAA; line-height:1.75;
}

/* Progress bar */
.progress-wrap {
    background:rgba(255,255,255,0.06);
    border-radius:100px;
    height:6px;
    margin:0.6rem 0 0.4rem;
    overflow:hidden;
}
.progress-fill {
    height:100%;
    border-radius:100px;
    background:linear-gradient(90deg,#D4AF37,#F5E070);
    box-shadow:0 0 8px rgba(212,175,55,0.5);
    transition:width 0.4s ease;
}

/* Card counter badge */
.card-counter {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(212,175,55,0.1);
    border:1px solid rgba(212,175,55,0.3);
    border-radius:20px;
    padding:4px 14px;
    font-size:0.8rem; color:#D4AF37; font-weight:600;
    letter-spacing:0.03em;
}
.known-badge {
    display:inline-flex; align-items:center; gap:5px;
    background:rgba(40,160,80,0.12);
    border:1px solid rgba(40,160,80,0.35);
    border-radius:20px;
    padding:4px 14px;
    font-size:0.8rem; color:#5CBA7D; font-weight:600;
}

/* Buttons */
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
[data-testid="stSelectbox"] > div {
    background:#141414 !important; color:#F5F5F5 !important;
    border:1px solid rgba(212,175,55,0.3) !important; border-radius:8px !important;
}
[data-testid="stSlider"] .stSlider > div > div > div {
    background: #D4AF37 !important;
}

/* Page fade-in */
@keyframes pageIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
[data-testid="stAppViewContainer"] > section { animation:pageIn 0.55s ease both; }

/* Expander */
[data-testid="stExpander"] {
    border:1px solid rgba(212,175,55,0.2) !important;
    border-radius:12px !important;
    background:rgba(212,175,55,0.03) !important;
}
/* Spinner */
[data-testid="stSpinner"] > div > div { border-top-color:#D4AF37 !important; }
/* Alert */
[data-testid="stAlert"] { border-radius:12px !important; }
</style>
""", unsafe_allow_html=True)

# ── Fetch collections ─────────────────────────────────────────────────────────
try:
    resp = requests.get(f"{BACKEND_URL}/api/documents", timeout=15)
    collections: list[str] = resp.json().get("collections", []) if resp.status_code == 200 else []
except Exception:
    collections = []

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🃏 Study Flashcards")
st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)
st.markdown(
    "AI extracts the **key terms and concepts** from your notes and turns them into "
    "interactive flashcards. Click any card to flip it and reveal the definition."
)

if not collections:
    st.warning("⚠️ No documents indexed yet. Go to **📁 Upload** first.")
    st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
if "flashcards"    not in st.session_state: st.session_state["flashcards"]    = []
if "card_index"    not in st.session_state: st.session_state["card_index"]    = 0
if "known_indices" not in st.session_state: st.session_state["known_indices"] = set()
if "card_order"    not in st.session_state: st.session_state["card_order"]    = []

# ── Layout ────────────────────────────────────────────────────────────────────
col_ctrl, col_main = st.columns([1, 2], gap="large")

# ─────────────────────────────────────────────────────────────────────────────
with col_ctrl:
    st.markdown("### ⚙️ Settings")

    active      = st.session_state.get("active_collection")
    default_idx = collections.index(active) if active in collections else 0
    selected    = st.selectbox("📚 Document", options=collections, index=default_idx)

    num_cards = st.slider("Number of cards", min_value=5, max_value=30, value=10, step=5)

    gen_btn = st.button("✨ Generate Flashcards", use_container_width=True)

    st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

    # How it works
    st.markdown("""<div class="settings-card">
    <b style="color:#D4AF37">How it works</b><br><br>
    1. Top chunks retrieved from <b>ChromaDB</b><br>
    2. LLM extracts <b>key terms &amp; definitions</b><br>
    3. Returns strict <b>JSON flashcard array</b><br>
    4. Click card to <b>flip</b> · Mark as <b>Known ✓</b>
    </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

    # Controls (only shown when cards are loaded)
    if st.session_state["flashcards"]:
        cards     = st.session_state["flashcards"]
        order     = st.session_state["card_order"]
        known     = st.session_state["known_indices"]
        idx       = st.session_state["card_index"]
        remaining = [i for i in order if i not in known]

        st.markdown(f'<div class="card-counter">🃏 Card {idx + 1} of {len(order)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="known-badge" style="margin-top:6px">✓ Known: {len(known)} / {len(cards)}</div>', unsafe_allow_html=True)

        # Progress bar
        pct = int((len(known) / len(cards)) * 100) if cards else 0
        st.markdown(f"""
        <div class="progress-wrap">
          <div class="progress-fill" style="width:{pct}%"></div>
        </div>
        <div style="font-size:0.72rem;color:#555;text-align:right">{pct}% mastered</div>
        """, unsafe_allow_html=True)

        st.markdown("")

        # Navigation buttons
        nav1, nav2 = st.columns(2)
        with nav1:
            if st.button("◀ Prev", use_container_width=True):
                st.session_state["card_index"] = (idx - 1) % len(order)
                st.rerun()
        with nav2:
            if st.button("Next ▶", use_container_width=True):
                st.session_state["card_index"] = (idx + 1) % len(order)
                st.rerun()

        # Mark as known
        current_card_idx = order[idx]
        if current_card_idx not in known:
            if st.button("✓ Mark as Known", use_container_width=True):
                st.session_state["known_indices"].add(current_card_idx)
                # Auto-advance to next
                st.session_state["card_index"] = (idx + 1) % len(order)
                st.rerun()
        else:
            if st.button("↩ Unmark Known", use_container_width=True):
                st.session_state["known_indices"].discard(current_card_idx)
                st.rerun()

        # Shuffle
        if st.button("🔀 Shuffle Cards", use_container_width=True):
            shuffled = list(range(len(cards)))
            random.shuffle(shuffled)
            st.session_state["card_order"] = shuffled
            st.session_state["card_index"] = 0
            st.session_state["known_indices"] = set()
            st.rerun()

        # Reset
        if st.button("🔄 Reset Progress", use_container_width=True):
            st.session_state["known_indices"] = set()
            st.session_state["card_index"]    = 0
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
with col_main:

    # ── Generate flashcards ───────────────────────────────────────────────────
    if gen_btn:
        with st.spinner(f"Generating {num_cards} flashcards from your notes…"):
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/flashcards",
                    json={"collection_name": selected, "num_cards": num_cards},
                    timeout=90,
                )
                if r.status_code == 200:
                    data = r.json()
                    cards = data["flashcards"]
                    st.session_state["flashcards"]    = cards
                    st.session_state["card_order"]    = list(range(len(cards)))
                    st.session_state["card_index"]    = 0
                    st.session_state["known_indices"] = set()
                    st.rerun()
                else:
                    st.error(r.json().get("detail", r.text))
            except requests.exceptions.ConnectionError:
                st.error("❌ Backend unreachable.")
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. Try fewer cards.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

    # ── Render flashcards ─────────────────────────────────────────────────────
    if st.session_state["flashcards"]:
        cards  = st.session_state["flashcards"]
        order  = st.session_state["card_order"]
        known  = st.session_state["known_indices"]
        idx    = st.session_state["card_index"]

        current_card_idx = order[idx]
        card             = cards[current_card_idx]
        term             = card["term"]
        definition       = card["definition"]
        is_known         = current_card_idx in known

        known_overlay = ""
        if is_known:
            known_overlay = """
            <div style="position:absolute;top:12px;right:14px;
                        background:rgba(40,160,80,0.85);
                        color:#FFF;font-size:0.72rem;font-weight:700;
                        border-radius:12px;padding:3px 10px;z-index:10;">
              ✓ Known
            </div>"""

        # 3D flip card via embedded HTML component
        flip_card_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    background:transparent;
    display:flex; flex-direction:column; align-items:center;
    padding:8px 4px 16px;
    font-family:'Inter',system-ui,sans-serif;
  }}

  /* ── Hint text ── */
  .flip-hint {{
    color:#555; font-size:0.75rem; letter-spacing:0.04em;
    margin-bottom:14px; text-align:center;
  }}

  /* ── 3D card container ── */
  .scene {{
    width:100%; max-width:580px; height:260px;
    perspective:1100px;
    cursor:pointer;
  }}
  .card {{
    width:100%; height:100%;
    position:relative;
    transform-style:preserve-3d;
    transition:transform 0.65s cubic-bezier(0.4,0.2,0.2,1);
    border-radius:20px;
  }}
  .card.flipped {{ transform:rotateY(180deg); }}

  /* ── Front & Back shared ── */
  .face {{
    position:absolute; inset:0;
    backface-visibility:hidden;
    border-radius:20px;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    padding:2rem 2.2rem;
    text-align:center;
  }}

  /* ── Front (TERM) ── */
  .front {{
    background: linear-gradient(135deg, rgba(212,175,55,0.12) 0%, rgba(20,20,20,0.97) 100%);
    border:1px solid rgba(212,175,55,0.4);
    box-shadow:0 8px 40px rgba(0,0,0,0.6), inset 0 1px 0 rgba(212,175,55,0.15),
               0 0 60px rgba(212,175,55,0.06);
  }}
  .front-label {{
    font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;
    color:#8B6914; font-weight:700; margin-bottom:1rem;
  }}
  .term-text {{
    font-size:1.65rem; font-weight:800; line-height:1.25;
    background:linear-gradient(135deg,#D4AF37 0%,#F5E070 50%,#C0A020 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;
    letter-spacing:-0.01em;
  }}
  .front-icon {{
    font-size:1.8rem; margin-bottom:0.8rem; opacity:0.8;
  }}

  /* ── Back (DEFINITION) ── */
  .back {{
    background: linear-gradient(135deg, rgba(139,105,20,0.18) 0%, rgba(15,15,15,0.98) 100%);
    border:1px solid rgba(212,175,55,0.55);
    box-shadow:0 8px 40px rgba(0,0,0,0.6), inset 0 1px 0 rgba(212,175,55,0.2),
               0 0 60px rgba(212,175,55,0.1);
    transform:rotateY(180deg);
  }}
  .back-label {{
    font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;
    color:#8B6914; font-weight:700; margin-bottom:0.9rem;
  }}
  .back-term {{
    font-size:0.9rem; font-weight:700; color:#D4AF37; margin-bottom:0.8rem;
    letter-spacing:0.01em;
  }}
  .definition-text {{
    font-size:0.97rem; color:#DEDEDE; line-height:1.75;
    max-width:480px;
  }}

  /* ── Corner shine ── */
  .face::before {{
    content:'';
    position:absolute; top:0; left:-60%;
    width:40%; height:100%;
    background:linear-gradient(90deg,transparent,rgba(245,224,112,0.05),transparent);
    transform:skewX(-15deg);
    transition:left 0.7s ease;
    pointer-events:none; border-radius:20px;
  }}
  .card:hover .face::before {{ left:130%; }}

  /* ── Keyboard shortcut tip ── */
  .shortcut-tip {{
    margin-top:14px;
    color:#333; font-size:0.7rem; letter-spacing:0.03em; text-align:center;
  }}
</style>
</head>
<body>
  <div class="flip-hint">👆 Click the card to flip</div>
  <div class="scene" onclick="flipCard()">
    <div class="card" id="fc">
      <!-- FRONT -->
      <div class="face front">
        {known_overlay}
        <div class="front-icon">🃏</div>
        <div class="front-label">Term</div>
        <div class="term-text">{term}</div>
      </div>
      <!-- BACK -->
      <div class="face back">
        <div class="back-label">Definition</div>
        <div class="back-term">{term}</div>
        <div class="definition-text">{definition}</div>
      </div>
    </div>
  </div>
  <div class="shortcut-tip">Press <kbd style="background:#1a1a1a;border:1px solid #333;
    border-radius:4px;padding:1px 6px;font-size:0.68rem;color:#888">Space</kbd> to flip</div>

<script>
let flipped = false;
function flipCard() {{
  flipped = !flipped;
  document.getElementById('fc').classList.toggle('flipped', flipped);
}}
document.addEventListener('keydown', (e) => {{
  if (e.code === 'Space') {{ e.preventDefault(); flipCard(); }}
}});
</script>
</body>
</html>
"""
        components.html(flip_card_html, height=340)

        # ── All-cards grid (overview) ─────────────────────────────────────
        st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)
        with st.expander(f"📋 All {len(cards)} Cards — Overview", expanded=False):
            gcols = st.columns(3)
            for i, c in enumerate(cards):
                col = gcols[i % 3]
                card_idx = i
                is_k = card_idx in known
                border_color = "rgba(40,160,80,0.5)" if is_k else "rgba(212,175,55,0.2)"
                bg_color     = "rgba(40,160,80,0.06)" if is_k else "rgba(212,175,55,0.04)"
                badge        = '<span style="color:#5CBA7D;font-size:0.7rem;font-weight:700">✓ Known</span>' if is_k else ""
                col.markdown(f"""
                <div style="background:{bg_color};border:1px solid {border_color};
                            border-radius:10px;padding:0.7rem 0.9rem;margin-bottom:0.5rem;
                            cursor:pointer;"
                     onclick="">
                  <div style="font-size:0.78rem;font-weight:700;color:#D4AF37;
                              margin-bottom:3px;">{i+1}. {c['term']} {badge}</div>
                  <div style="font-size:0.72rem;color:#666;line-height:1.5;">
                    {c['definition'][:100]}{'…' if len(c['definition']) > 100 else ''}
                  </div>
                </div>""", unsafe_allow_html=True)
                if col.button("Go", key=f"goto_{i}", use_container_width=False):
                    new_pos = st.session_state["card_order"].index(card_idx) \
                              if card_idx in st.session_state["card_order"] else 0
                    st.session_state["card_index"] = new_pos
                    st.rerun()

    else:
        # Placeholder
        st.markdown("""
        <div style="background:#111;border:2px dashed #222;border-radius:16px;
                    padding:4rem 2rem;text-align:center;color:#444;">
            <div style="font-size:4rem;margin-bottom:1rem;">🃏</div>
            <div style="font-size:1.05rem;font-weight:600;color:#555;">
                Select a document and click <b style="color:#D4AF37">Generate Flashcards</b>
            </div>
            <div style="font-size:0.85rem;margin-top:0.5rem;color:#333;">
                AI will extract key terms and definitions from your notes
            </div>
        </div>
        """, unsafe_allow_html=True)
