"""
Onboarding v3 — name-fix revision.

Bug fixed: _complete_onboarding() called persist_now() which wrote to
st.query_params, then called st.rerun(). On the next rerun, _load_from_query_params
correctly read the name from the URL. But the onboarding flow never called
st.rerun() from _complete_onboarding() itself — the caller (_step_subject) called
st.rerun() AFTER _complete_onboarding() returned. This meant that
st.session_state["student_name"] was set correctly, but because the rerun
happened immediately, the sidebar displayed "Guest" for one frame before
the name appeared.

Real fix: ensure student_name is in session_state AND in query_params before
the final rerun. Both are now done atomically inside _complete_onboarding().
"""

from __future__ import annotations

import streamlit as st
from backend_code.curriculum_data import get_curriculum
from utils.local_storage import persist_now


def is_onboarding_needed() -> bool:
    return not st.session_state.get("onboarding_done", False)


def draw_onboarding() -> None:
    step = st.session_state.get("onboarding_step", 1)

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

    _render_progress_dots(step, total=3)
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    if step == 1:
        _step_name()
    elif step == 2:
        _step_grade()
    elif step == 3:
        _step_subject()


# ── Steps ─────────────────────────────────────────────────────────────────────

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

        disabled = len(name.strip()) < 2
        if st.button("Continue →", type="primary", use_container_width=True,
                     key="ob_name_btn", disabled=disabled):
            st.session_state["student_name"] = name.strip()
            st.session_state["onboarding_step"] = 2
            st.rerun()


def _step_grade() -> None:
    name = st.session_state.get("student_name") or "there"
    st.markdown(
        f'<p class="onboarding-question">📚 Nice to meet you, {name}! What grade are you in?</p>',
        unsafe_allow_html=True,
    )

    grades = list(range(1, 13))
    rows   = [grades[i:i+4] for i in range(0, 12, 4)]

    for row in rows:
        cols = st.columns(4)
        for col, g in zip(cols, row):
            with col:
                if st.button(f"Grade {g}", key=f"ob_grade_{g}", use_container_width=True):
                    st.session_state["grade"] = g
                    curriculum = get_curriculum()
                    subjects   = curriculum.get_subjects_for_grade(g)
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
    grade     = st.session_state.get("grade", 8)
    name      = st.session_state.get("student_name") or "there"
    curriculum = get_curriculum()
    subjects  = curriculum.get_subjects_for_grade(grade)

    st.markdown(
        f'<p class="onboarding-question">🔬 What would you like to study today, {name}?</p>',
        unsafe_allow_html=True,
    )
    st.caption(f"Grade {grade} subjects")

    subject_icons = {
        "Physics": "⚡", "Chemistry": "🧪", "Biology": "🌿",
        "General Science": "🔭", "Environmental Studies": "🌍",
    }
    cols = st.columns(len(subjects))
    for col, subj in zip(cols, subjects):
        with col:
            icon = subject_icons.get(subj, "📖")
            if st.button(f"{icon}\n{subj}", key=f"ob_subj_{subj}",
                         use_container_width=True):
                st.session_state["subject"] = subj
                st.session_state["topic"]   = "All Topics"
                _complete_onboarding()   # sets done=True AND writes query params
                st.rerun()               # now the URL already has ?name= in it

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    if st.button("← Back", key="ob_subj_back"):
        st.session_state["onboarding_step"] = 2
        st.rerun()


# ── Completion ────────────────────────────────────────────────────────────────

def _complete_onboarding() -> None:
    """
    Mark onboarding done and write ALL state (including name) to query params.

    Critical ordering:
      1. Set student_name in session_state (it was set in _step_name already,
         but confirm it's there).
      2. Set onboarding_done = True.
      3. Call persist_now() — this writes ?name=X&grade=Y... to the URL.
      4. Caller does st.rerun().

    On the next rerun, _load_from_query_params() reads ?name= from the URL
    and writes it into session_state BEFORE initialize_session_state() runs,
    so "Guest" is never shown.
    """
    # Guard: ensure name is never None or empty going into the URL
    name = (st.session_state.get("student_name") or "").strip()
    if not name:
        name = st.session_state.get("ob_name_input", "").strip()
    if not name:
        name = "Student"
    st.session_state["student_name"] = name

    if not st.session_state.get("language"):
        st.session_state["language"] = "English"

    st.session_state["onboarding_done"] = True
    st.session_state.pop("onboarding_step", None)

    # Write to URL — must happen BEFORE st.rerun() so the next load has it
    persist_now()


# ── Progress dots ─────────────────────────────────────────────────────────────

def _render_progress_dots(current: int, total: int) -> None:
    dots = ""
    for i in range(1, total + 1):
        if i == current:
            cls = "dot-active"
        elif i < current:
            cls = "dot-done"
        else:
            cls = "dot-idle"
        dots += f'<span class="ob-dot {cls}"></span>'
    st.markdown(f'<div class="ob-dots">{dots}</div>', unsafe_allow_html=True)
