"""
Onboarding / Quick Start flow for ScienceGPT v3.
Feature #3: Zero-config first experience.

Shows a friendly multi-step welcome screen on first visit:
  Step 1 → Enter your name
  Step 2 → Pick your grade (visual grid, not a dropdown)
  Step 3 → Pick your subject (pill buttons for the grade)

After completing, sets onboarding_done = True and persists to localStorage.
Returning visitors with a stored name skip straight to the app.
"""

from __future__ import annotations

import streamlit as st
from backend_code.curriculum_data import get_curriculum
from utils.local_storage import persist_now


# ── Public entry point ────────────────────────────────────────────────────────

def is_onboarding_needed() -> bool:
    """Return True if the user hasn't completed onboarding this session."""
    return not st.session_state.get("onboarding_done", False)


def draw_onboarding() -> None:
    """
    Render the full onboarding flow.
    Sets session_state keys and calls persist_now() on completion.
    """
    step = st.session_state.get("onboarding_step", 1)

    # ── Outer container ────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="onboarding-shell">
            <div class="onboarding-logo">🧪</div>
            <h1 class="onboarding-title">Welcome to ScienceGPT</h1>
            <p class="onboarding-sub">Your personal AI science tutor for NCERT Grades 1–12</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Progress dots
    _render_progress_dots(step, total=3)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    if step == 1:
        _step_name()
    elif step == 2:
        _step_grade()
    elif step == 3:
        _step_subject()


# ── Step renderers ────────────────────────────────────────────────────────────

def _step_name() -> None:
    st.markdown(
        '<p class="onboarding-question">👋 First, what\'s your name?</p>',
        unsafe_allow_html=True,
    )

    col = st.columns([1, 2, 1])[1]
    with col:
        name = st.text_input(
            "Your name",
            placeholder="e.g. Priya, Arjun, Riya…",
            key="ob_name_input",
            label_visibility="collapsed",
        )
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

        if st.button("Continue →", type="primary", use_container_width=True,
                     key="ob_name_btn", disabled=len(name.strip()) < 2):
            st.session_state["student_name"] = name.strip()
            st.session_state["onboarding_step"] = 2
            st.rerun()


def _step_grade() -> None:
    name = st.session_state.get("student_name", "there")
    st.markdown(
        f'<p class="onboarding-question">📚 Nice to meet you, {name}! What grade are you in?</p>',
        unsafe_allow_html=True,
    )

    # Visual 4×3 grid of grade buttons
    grades = list(range(1, 13))
    rows = [grades[i:i+4] for i in range(0, 12, 4)]

    for row in rows:
        cols = st.columns(4)
        for col, g in zip(cols, row):
            with col:
                label = f"Grade {g}"
                if st.button(label, key=f"ob_grade_{g}", use_container_width=True):
                    st.session_state["grade"] = g
                    # Reset subject when grade changes
                    curriculum = get_curriculum()
                    subjects = curriculum.get_subjects_for_grade(g)
                    if subjects:
                        st.session_state["subject"] = subjects[0]
                    st.session_state["topic"] = "All Topics"
                    st.session_state["onboarding_step"] = 3
                    st.rerun()

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    if st.button("← Back", key="ob_grade_back"):
        st.session_state["onboarding_step"] = 1
        st.rerun()


def _step_subject() -> None:
    grade = st.session_state.get("grade", 8)
    name = st.session_state.get("student_name", "there")
    curriculum = get_curriculum()
    subjects = curriculum.get_subjects_for_grade(grade)

    st.markdown(
        f'<p class="onboarding-question">🔬 Great! What would you like to study today, {name}?</p>',
        unsafe_allow_html=True,
    )
    st.caption(f"Grade {grade} subjects")

    # Subject pill buttons centred
    cols = st.columns(len(subjects))
    subject_icons = {
        "Physics": "⚡", "Chemistry": "🧪", "Biology": "🌿",
        "General Science": "🔭", "Environmental Studies": "🌍",
    }
    for col, subj in zip(cols, subjects):
        with col:
            icon = subject_icons.get(subj, "📖")
            if st.button(f"{icon}\n{subj}", key=f"ob_subj_{subj}",
                         use_container_width=True):
                st.session_state["subject"] = subj
                st.session_state["topic"] = "All Topics"
                _complete_onboarding()
                st.rerun()

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    if st.button("← Back", key="ob_subj_back"):
        st.session_state["onboarding_step"] = 2
        st.rerun()


# ── Completion ────────────────────────────────────────────────────────────────

def _complete_onboarding() -> None:
    """Mark onboarding done, set defaults, persist to localStorage."""
    st.session_state["onboarding_done"] = True
    st.session_state.pop("onboarding_step", None)

    # Ensure language has a default
    if not st.session_state.get("language"):
        st.session_state["language"] = "English"

    persist_now()


# ── UI helper ─────────────────────────────────────────────────────────────────

def _render_progress_dots(current: int, total: int) -> None:
    dots = ""
    for i in range(1, total + 1):
        cls = "dot-active" if i == current else ("dot-done" if i < current else "dot-idle")
        dots += f'<span class="ob-dot {cls}"></span>'
    st.markdown(
        f'<div class="ob-dots">{dots}</div>',
        unsafe_allow_html=True,
    )
