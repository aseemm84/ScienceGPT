"""
Quiz UI Component v2 for ScienceGPT.
Feature #2: Auto-generated quizzes with instant grading.

MCQ and True/False are graded client-side.
Short answers are graded by the LLM.
Results feed into StudentProgress mastery tracking.
"""

import streamlit as st
from backend_code.llm_handler import get_llm_handler
from config.constants import POINTS_PER_QUIZ_CORRECT


def draw_quiz_panel() -> None:
    """Render the full quiz panel for the current grade/subject/topic."""
    grade = st.session_state.get("grade", 8)
    subject = st.session_state.get("subject", "Physics")
    topic = st.session_state.get("topic", "All Topics")

    st.markdown("### 📝 Quiz Mode")
    st.caption(f"Grade {grade} · {subject} · {topic}")

    handler = get_llm_handler()

    # ── Start / regenerate quiz ────────────────────────────────────────────────
    if not st.session_state.get("active_quiz"):
        st.markdown(
            "Test your knowledge! Claude will generate 5 questions — "
            "3 multiple choice, 1 true/false, and 1 short answer."
        )
        if st.button("🚀 Generate Quiz", type="primary", use_container_width=True):
            with st.spinner("Generating your quiz…"):
                questions = handler.generate_quiz(grade, subject, topic)
            if not questions:
                st.error("Could not generate the quiz. Please try again.")
                return
            st.session_state.quiz_questions = questions
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_score = 0
            st.session_state.active_quiz = True
            st.rerun()
        return

    questions: list[dict] = st.session_state.get("quiz_questions", [])
    if not questions:
        st.session_state.active_quiz = False
        st.rerun()
        return

    # ── Render questions ───────────────────────────────────────────────────────
    submitted: bool = st.session_state.get("quiz_submitted", False)
    answers: dict = st.session_state.get("quiz_answers", {})

    for i, q in enumerate(questions):
        qtype = q.get("type", "mcq")
        question_text = q.get("question", "")

        st.markdown(
            f'<div class="quiz-card">'
            f'<div class="q-number">Question {i+1} / {len(questions)} · {qtype.upper()}</div>'
            f'<div class="q-text">{question_text}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )

        if qtype == "mcq":
            options = q.get("options", [])
            if not submitted:
                chosen = st.radio(
                    f"q{i}_radio",
                    options=options,
                    index=None,
                    key=f"quiz_radio_{i}",
                    label_visibility="collapsed",
                )
                if chosen is not None:
                    answers[str(i)] = chosen[0]  # store just the letter A/B/C/D
            else:
                _show_mcq_result(i, q, answers)

        elif qtype == "truefalse":
            if not submitted:
                chosen = st.radio(
                    f"q{i}_tf",
                    options=["True", "False"],
                    index=None,
                    key=f"quiz_tf_{i}",
                    label_visibility="collapsed",
                )
                if chosen is not None:
                    answers[str(i)] = chosen
            else:
                _show_tf_result(i, q, answers)

        elif qtype == "shortanswer":
            if not submitted:
                student_ans = st.text_area(
                    "Your answer:",
                    key=f"quiz_sa_{i}",
                    height=80,
                    placeholder="Write your answer here…",
                )
                if student_ans:
                    answers[str(i)] = student_ans
            else:
                _show_sa_result(i, q, answers, grade)

        st.session_state.quiz_answers = answers
        st.markdown("")  # spacer

    # ── Submit button ──────────────────────────────────────────────────────────
    if not submitted:
        answered = sum(1 for k in [str(i) for i in range(len(questions))]
                       if answers.get(k))
        progress_val = answered / len(questions)
        st.progress(progress_val, text=f"Answered {answered} / {len(questions)}")

        if st.button("✅ Submit Quiz", type="primary", use_container_width=True,
                     disabled=answered < len(questions)):
            _grade_and_submit(questions, answers, grade, subject, topic)

    # ── Results summary ────────────────────────────────────────────────────────
    else:
        _show_results_summary(questions, grade, subject, topic)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Quiz", use_container_width=True):
                for k in ("quiz_questions", "quiz_submitted", "quiz_answers",
                          "quiz_score", "active_quiz", "_sa_grades"):
                    st.session_state.pop(k, None)
                st.rerun()
        with col2:
            if st.button("❌ Exit Quiz Mode", use_container_width=True):
                for k in ("quiz_questions", "quiz_submitted", "quiz_answers",
                          "quiz_score", "active_quiz", "_sa_grades"):
                    st.session_state.pop(k, None)
                st.rerun()


# ── Result renderers ──────────────────────────────────────────────────────────

def _show_mcq_result(idx: int, q: dict, answers: dict) -> None:
    correct = q.get("answer", "").strip().upper()
    student = answers.get(str(idx), "").strip().upper()
    is_correct = student == correct

    label_class = "result-correct" if is_correct else "result-incorrect"
    icon = "✅" if is_correct else "❌"
    st.markdown(
        f'<span class="result-pill {label_class}">{icon} '
        f'{"Correct" if is_correct else f"Incorrect — correct answer: {correct}"}'
        f"</span>",
        unsafe_allow_html=True,
    )
    st.caption(f"💡 {q.get('explanation', '')}")


def _show_tf_result(idx: int, q: dict, answers: dict) -> None:
    correct = q.get("answer", "True").strip()
    student = answers.get(str(idx), "").strip()
    is_correct = student.lower() == correct.lower()

    label_class = "result-correct" if is_correct else "result-incorrect"
    icon = "✅" if is_correct else "❌"
    st.markdown(
        f'<span class="result-pill {label_class}">{icon} '
        f'{"Correct" if is_correct else f"Incorrect — answer was {correct}"}'
        f"</span>",
        unsafe_allow_html=True,
    )
    st.caption(f"💡 {q.get('explanation', '')}")


def _show_sa_result(idx: int, q: dict, answers: dict, grade: int) -> None:
    """Show LLM-graded result for short answer. Grade once and cache."""
    sa_grades = st.session_state.setdefault("_sa_grades", {})

    if str(idx) not in sa_grades:
        # This branch only runs first time; grading happens in _grade_and_submit
        st.info("Grading…")
        return

    result = sa_grades[str(idx)]
    score = result.get("score", 0)
    max_score = 5

    if score >= 4:
        label_class, icon = "result-correct", "✅"
    elif score >= 2:
        label_class, icon = "result-partial", "🔶"
    else:
        label_class, icon = "result-incorrect", "❌"

    st.markdown(
        f'<span class="result-pill {label_class}">{icon} Score: {score}/{max_score}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(f"✅ {result.get('correct_parts', '')}")
    if result.get("missed_parts"):
        st.markdown(f"🔶 {result.get('missed_parts', '')}")
    st.info(result.get("encouragement", ""))
    st.caption(f"📖 Model answer: {q.get('answer', '')}")


# ── Grading logic ─────────────────────────────────────────────────────────────

def _grade_and_submit(
    questions: list[dict], answers: dict, grade: int, subject: str, topic: str
) -> None:
    """Score all questions, update gamification + progress, mark submitted."""
    handler = get_llm_handler()
    correct_count = 0
    sa_grades: dict = {}

    with st.spinner("Grading your answers…"):
        for i, q in enumerate(questions):
            qtype = q.get("type", "mcq")
            student = answers.get(str(i), "")

            if qtype == "mcq":
                if student.strip().upper() == q.get("answer", "").strip().upper():
                    correct_count += 1

            elif qtype == "truefalse":
                if student.strip().lower() == q.get("answer", "").strip().lower():
                    correct_count += 1

            elif qtype == "shortanswer":
                result = handler.grade_short_answer(
                    model_answer=q.get("answer", ""),
                    student_answer=student,
                    grade=grade,
                )
                sa_grades[str(i)] = result
                # score 0-5; count as correct if ≥ 3
                if result.get("score", 0) >= 3:
                    correct_count += 1

    st.session_state.quiz_score = correct_count
    st.session_state._sa_grades = sa_grades
    st.session_state.quiz_submitted = True

    total = len(questions)
    pct = round((correct_count / total) * 100) if total > 0 else 0

    # Update gamification
    if "gamification" in st.session_state:
        st.session_state.gamification.add_quiz_completed(
            correct=correct_count, total=total
        )

    # Update progress mastery
    if "progress" in st.session_state:
        st.session_state.progress.record_quiz_result(
            subject=subject, topic=topic, score=correct_count, total=total
        )

    st.rerun()


def _show_results_summary(
    questions: list[dict], grade: int, subject: str, topic: str
) -> None:
    score = st.session_state.get("quiz_score", 0)
    total = len(questions)
    pct = round((score / total) * 100) if total > 0 else 0

    from utils.helpers import score_to_color
    color = score_to_color(pct)

    st.markdown("---")
    st.markdown("### 🏁 Quiz Results")

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{score}/{total}")
    col2.metric("Percentage", f"{pct}%")
    col3.metric("Points Earned", score * POINTS_PER_QUIZ_CORRECT)

    if pct == 100:
        st.success("🎯 Perfect score! You've mastered this topic!")
    elif pct >= 70:
        st.success(f"⭐ Great work! You scored {pct}%.")
    elif pct >= 40:
        st.warning(f"🔶 Good effort! Review the explanations above to improve.")
    else:
        st.error("📚 Keep studying — you'll get there! Review the explanations above.")
