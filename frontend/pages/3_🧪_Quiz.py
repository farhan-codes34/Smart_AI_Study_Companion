"""
3_🧪_Quiz.py — Interactive MCQ Quiz page

Three-step flow managed via st.session_state["quiz_step"]:
  Step 1 — Configure:  pick document, set question count, generate
  Step 2 — Take quiz:  answer each MCQ with radio buttons
  Step 3 — Results:    see score, correct/wrong per question, explanations
"""

import os
import requests
import streamlit as st

st.set_page_config(page_title="Quiz", page_icon="🧪", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ── Theme CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color:#0C0C0C; color:#F5F5F5;
    background-image: radial-gradient(ellipse at 50% 0%, rgba(212,175,55,0.05) 0%, transparent 60%);
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

/* Question card */
.q-card {
    background:linear-gradient(135deg,rgba(212,175,55,0.05),rgba(20,20,20,0.95));
    border:1px solid rgba(212,175,55,0.2);
    border-radius:16px;
    padding:1.3rem 1.6rem;
    margin-bottom:1rem;
    box-shadow:0 4px 20px rgba(0,0,0,0.4);
    transition:box-shadow 0.2s ease;
}
.q-card:hover { box-shadow:0 4px 20px rgba(212,175,55,0.1); }
.q-number {
    background:linear-gradient(135deg,#D4AF37,#C0C0C0);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    background-clip:text;
    font-size:0.78rem; font-weight:700;
    text-transform:uppercase; letter-spacing:0.1em;
    margin-bottom:0.5rem;
}
.q-text { font-size:1.05rem; font-weight:600; color:#F0F0F0; margin-bottom:0.8rem; line-height:1.55; }

/* Result cards */
.result-correct {
    background:linear-gradient(135deg,rgba(76,175,80,0.1),rgba(20,20,20,0.95));
    border:1px solid rgba(76,175,80,0.4); border-left:3px solid #4CAF50;
    border-radius:14px; padding:1rem 1.3rem; margin-bottom:0.8rem;
    box-shadow:0 0 15px rgba(76,175,80,0.08);
}
.result-wrong {
    background:linear-gradient(135deg,rgba(244,67,54,0.1),rgba(20,20,20,0.95));
    border:1px solid rgba(244,67,54,0.4); border-left:3px solid #f44336;
    border-radius:14px; padding:1rem 1.3rem; margin-bottom:0.8rem;
    box-shadow:0 0 15px rgba(244,67,54,0.08);
}
.result-label-correct { color:#4CAF50; font-weight:700; margin-bottom:0.3rem; }
.result-label-wrong   { color:#f44336; font-weight:700; margin-bottom:0.3rem; }
.explanation-text {
    color:#A0A0A0; font-size:0.87rem;
    border-top:1px solid rgba(255,255,255,0.06);
    margin-top:0.5rem; padding-top:0.5rem; line-height:1.65;
}

/* Score badge */
.score-badge {
    text-align:center; padding:2.2rem 2rem;
    border-radius:20px; margin-bottom:1.5rem;
    backdrop-filter:blur(10px);
}
.score-badge .score-num { font-size:4.5rem; font-weight:900; line-height:1; letter-spacing:-0.03em; }
.score-badge .score-label { font-size:1rem; margin-top:0.5rem; opacity:0.85; font-weight:600; }

/* Progress bar */
.stProgress > div > div {
    background:linear-gradient(90deg,#D4AF37,#F5E070) !important;
    border-radius:99px !important;
}

/* Radio buttons */
[data-testid="stRadio"] label { color:#D0D0D0 !important; }
[data-testid="stRadio"] > div { background:transparent !important; }

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

/* Selectbox / slider */
[data-testid="stSelectbox"] > div {
    background:#141414 !important; color:#F5F5F5 !important;
    border:1px solid rgba(212,175,55,0.3) !important; border-radius:8px !important;
}


/* Page fade-in */
@keyframes pageIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
[data-testid="stAppViewContainer"] > section { animation:pageIn 0.55s ease both; }

/* Question card entrance */
@keyframes cardIn { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
.q-card { animation:cardIn 0.4s ease both; }

/* Score badge pulse glow */
@keyframes pulseGold {
    0%   { box-shadow:0 0 0 0 rgba(212,175,55,0.5); }
    60%  { box-shadow:0 0 0 24px rgba(212,175,55,0); }
    100% { box-shadow:0 0 0 0 rgba(212,175,55,0); }
}
.score-badge { animation:pulseGold 1.8s ease-out 0.3s; }

/* Score number count-in */
@keyframes scoreIn {
    from { opacity:0; transform:scale(0.7); }
    to   { opacity:1; transform:scale(1); }
}
.score-badge .score-num { animation:scoreIn 0.5s cubic-bezier(0.34,1.56,0.64,1) 0.2s both; }

/* Result card entrance */
.result-correct, .result-wrong { animation:cardIn 0.4s ease both; }

/* Button ripple */
.stButton > button { position:relative !important; overflow:hidden !important; }
.stButton > button::after {
    content:''; position:absolute; top:50%; left:50%;
    width:0; height:0;
    background:rgba(255,255,255,0.15); border-radius:50%;
    transform:translate(-50%,-50%);
    transition:width 0.5s ease, height 0.5s ease;
}
.stButton > button:hover::after { width:300px; height:300px; }

/* Expander */
[data-testid="stExpander"] {
    border:1px solid rgba(212,175,55,0.2) !important;
    border-radius:12px !important;
    background:rgba(212,175,55,0.03) !important;
}

/* Spinner */
[data-testid="stSpinner"] > div > div { border-top-color:#D4AF37 !important; }

/* Slider thumb */
[data-testid="stSlider"] [role="slider"] {
    background:linear-gradient(135deg,#D4AF37,#8B6914) !important;
    box-shadow:0 0 8px rgba(212,175,55,0.5) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Initialise session state ───────────────────────────────────────────────────
if "quiz_step"      not in st.session_state: st.session_state["quiz_step"]      = 1
if "quiz_questions" not in st.session_state: st.session_state["quiz_questions"] = []
if "quiz_answers"   not in st.session_state: st.session_state["quiz_answers"]   = {}
if "quiz_results"   not in st.session_state: st.session_state["quiz_results"]   = None
if "quiz_collection" not in st.session_state: st.session_state["quiz_collection"] = ""

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🧪 Auto-Generated Quiz")
st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

# Step indicator
steps = {1: "Configure", 2: "Take Quiz", 3: "Results"}
step_cols = st.columns(3)
for i, (num, label) in enumerate(steps.items()):
    current = st.session_state["quiz_step"]
    with step_cols[i]:
        if num == current:
            st.markdown(
                f'<div style="text-align:center;background:#D4AF37;color:#FFF;'
                f'border-radius:8px;padding:0.4rem;font-weight:700;border:none;">'
                f'Step {num}: {label}</div>',
                unsafe_allow_html=True,
            )
        elif num < current:
            st.markdown(
                f'<div style="text-align:center;background:#141414;color:#D4AF37;'
                f'border-radius:8px;padding:0.4rem;border:1px solid #D4AF37;">✓ {label}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="text-align:center;background:#0d0d0d;color:#555;'
                f'border-radius:8px;padding:0.4rem;border:1px solid #222;">{label}</div>',
                unsafe_allow_html=True,
            )

st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — CONFIGURE
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state["quiz_step"] == 1:

    # Fetch collections
    try:
        resp = requests.get(f"{BACKEND_URL}/api/documents", timeout=15)
        collections: list[str] = resp.json().get("collections", []) if resp.status_code == 200 else []
    except Exception:
        collections = []

    if not collections:
        st.warning("⚠️ No documents indexed yet. Go to **📁 Upload** first.")
        st.stop()

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("### ⚙️ Quiz Settings")

        active = st.session_state.get("active_collection")
        default_idx = collections.index(active) if active in collections else 0

        selected_doc = st.selectbox(
            "📚 Select document",
            options=collections,
            index=default_idx,
        )

        num_q = st.slider(
            "🔢 Number of questions",
            min_value=3,
            max_value=15,
            value=5,
            step=1,
            help="More questions = longer generation time",
        )

        st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

        gen_btn = st.button("🚀 Generate Quiz", use_container_width=True)

        if gen_btn:
            with st.spinner(f"Generating {num_q} questions from your notes…"):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/generate-quiz",
                        json={"collection_name": selected_doc, "num_questions": num_q},
                        timeout=90,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        questions = data.get("questions", [])
                        if questions:
                            st.session_state["quiz_questions"]  = questions
                            st.session_state["quiz_answers"]    = {}
                            st.session_state["quiz_results"]    = None
                            st.session_state["quiz_collection"] = selected_doc
                            st.session_state["quiz_step"]       = 2
                            st.rerun()
                        else:
                            st.error("No questions returned — try a longer document.")
                    else:
                        st.error(response.json().get("detail", response.text))
                except requests.exceptions.Timeout:
                    st.error("⏱️ Generation timed out. Try fewer questions.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot reach the backend.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_right:
        st.markdown("""
        <div style="background:#141414;border:1px solid #2A2A2A;border-left:4px solid #D4AF37;
                    border-radius:8px;padding:1.2rem;font-size:0.88rem;color:#AAA;line-height:1.8;">
        <b style="color:#D4AF37">How quiz generation works</b><br><br>
        📄 Content from your document is retrieved as context<br>
        🤖 Groq Llama-3 generates MCQs in strict JSON format<br>
        ✅ Each question has 4 options + correct answer + explanation<br>
        📊 You get scored and see explanations for wrong answers<br><br>
        <b style="color:#D4AF37">Tips for better quizzes</b><br><br>
        • Use documents with at least 2–3 pages of content<br>
        • Start with 5 questions to test quality<br>
        • Re-generate if questions seem repetitive
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — TAKE QUIZ
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["quiz_step"] == 2:

    questions = st.session_state["quiz_questions"]
    answers   = st.session_state["quiz_answers"]

    # Progress
    answered  = len(answers)
    total     = len(questions)
    st.markdown(f"**Progress: {answered} / {total} answered**")
    st.progress(answered / total if total else 0)
    st.markdown("")

    # Render each question
    for i, q in enumerate(questions):
        q_num = i + 1
        with st.container():
            st.markdown(f"""
            <div class="q-card">
                <div class="q-number">Question {q_num} of {total}</div>
                <div class="q-text">{q['question']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Radio options
            selected = st.radio(
                label=f"q_{q_num}",
                options=q["options"],
                index=None,
                key=f"radio_{i}",
                label_visibility="collapsed",
            )

            if selected:
                # Extract just the letter (e.g. "A" from "A. Some option")
                letter = selected.strip()[0].upper()
                answers[i] = letter
                st.session_state["quiz_answers"] = answers

        st.markdown("")

    # Action buttons
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        if st.button("↩️ Start Over", use_container_width=True):
            st.session_state["quiz_step"] = 1
            st.rerun()

    with b_col2:
        all_answered = len(answers) == total
        submit_btn = st.button(
            f"✅ Submit Quiz ({answered}/{total} answered)",
            use_container_width=True,
            disabled=not all_answered,
        )

        if not all_answered:
            st.caption(f"Answer all {total} questions to submit.")

        if submit_btn and all_answered:
            with st.spinner("Evaluating your answers…"):
                try:
                    student_answers = [answers.get(i, "") for i in range(total)]
                    response = requests.post(
                        f"{BACKEND_URL}/api/evaluate-quiz",
                        json={
                            "questions": questions,
                            "answers":   student_answers,
                        },
                        timeout=30,
                    )
                    if response.status_code == 200:
                        st.session_state["quiz_results"] = response.json()
                        st.session_state["quiz_step"]    = 3
                        st.rerun()
                    else:
                        st.error(response.json().get("detail", response.text))
                except Exception as e:
                    st.error(f"Evaluation error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — RESULTS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["quiz_step"] == 3:

    results = st.session_state["quiz_results"]
    if not results:
        st.error("No results found — go back and retake the quiz.")
        st.stop()

    score      = results["score"]
    total      = results["total"]
    percentage = results["percentage"]

    # ── Score badge ────────────────────────────────────────────────────────────
    if percentage >= 80:
        badge_bg, badge_color, grade_msg = "#0a2a00", "#4CAF50", "🏆 Excellent!"
    elif percentage >= 60:
        badge_bg, badge_color, grade_msg = "#1A1200", "#C0C0C0", "👍 Good job!"
    else:
        badge_bg, badge_color, grade_msg = "#2a0000", "#f44336", "📚 Keep studying!"

    st.markdown(f"""
    <div class="score-badge" style="background:{badge_bg};border:2px solid {badge_color};">
        <div class="score-num" style="color:{badge_color};">{score}/{total}</div>
        <div class="score-label" style="color:{badge_color};">
            {percentage}% &nbsp;·&nbsp; {grade_msg}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Visual score bar
    st.progress(score / total if total else 0)
    st.markdown("")

    # ── Per-question results ───────────────────────────────────────────────────
    st.markdown("### 📋 Question Review")

    for i, r in enumerate(results["results"], 1):
        is_correct = r["is_correct"]
        css_class  = "result-correct" if is_correct else "result-wrong"
        label_cls  = "result-label-correct" if is_correct else "result-label-wrong"
        icon       = "✅" if is_correct else "❌"
        status     = "Correct!" if is_correct else f"Incorrect — correct answer: **{r['correct_answer']}**"

        # Build options display
        options_html = ""
        for opt in r.get("options", []):
            letter = opt.strip()[0].upper() if opt.strip() else ""
            is_correct_opt  = letter == r["correct_answer"]
            is_student_opt  = letter == r["student_answer"]
            opt_color = "#4CAF50" if is_correct_opt else ("#f44336" if is_student_opt and not is_correct_opt else "#666")
            opt_weight = "700" if is_correct_opt or is_student_opt else "400"
            marker = " ✓" if is_correct_opt else (" ✗" if is_student_opt and not is_correct_opt else "")
            options_html += f'<div style="color:{opt_color};font-weight:{opt_weight};padding:2px 0;">{opt}{marker}</div>'

        explanation = r.get("explanation", "").replace("\\n", "<br>")

        st.markdown(f"""
        <div class="{css_class}">
            <div class="{label_cls}">{icon} Q{i}: {status}</div>
            <div style="color:#EEE;font-weight:600;margin:0.4rem 0 0.6rem;">{r['question']}</div>
            {options_html}
            <div class="explanation-text">💡 {explanation}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="yellow-divider">', unsafe_allow_html=True)

    # ── Action buttons ─────────────────────────────────────────────────────────
    rb1, rb2 = st.columns(2)
    with rb1:
        if st.button("🔄 Retake Same Quiz", use_container_width=True):
            st.session_state["quiz_answers"] = {}
            st.session_state["quiz_results"] = None
            st.session_state["quiz_step"]    = 2
            st.rerun()
    with rb2:
        if st.button("🆕 Generate New Quiz", use_container_width=True):
            st.session_state["quiz_step"]      = 1
            st.session_state["quiz_questions"] = []
            st.session_state["quiz_answers"]   = {}
            st.session_state["quiz_results"]   = None
            st.rerun()
