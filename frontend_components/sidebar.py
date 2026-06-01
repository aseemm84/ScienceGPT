"""
Sidebar v3 — name-fix revision.

Bug fixed: student_name is now initialised as None (not ""), so the
`if name:` check correctly distinguishes "not set" from "set to empty string".
The sidebar now shows the actual name when it's been set, never "Guest"
after onboarding is complete.
"""

from __future__ import annotations

import streamlit as st
from backend_code.curriculum_data import get_curriculum
from frontend_components.bookmarks import draw_study_list
from utils.local_storage import persist_now
from config.constants import DIFFICULTY_ICONS


def draw_sidebar() -> None:
    """Render the full sidebar."""

    # ── Student name ───────────────────────────────────────────────────────────
    # student_name is None before onboarding, a string after.
    raw_name = st.session_state.get("student_name")
    name = raw_name.strip() if isinstance(raw_name, str) else ""

    if name:
        col_name, col_edit = st.columns([3, 1])
        with col_name:
            st.markdown(
                f'<p class="sidebar-section">👤 {name}</p>',
                unsafe_allow_html=True,
            )
        with col_edit:
            if st.button("✏️", key="edit_name_btn", help="Change name"):
                st.session_state["editing_name"] = True

        if st.session_state.get("editing_name"):
            new_name = st.text_input("New name:", value=name, key="new_name_input")
            if st.button("Save", key="save_name_btn"):
                stripped = new_name.strip()
                if stripped:
                    st.session_state["student_name"] = stripped
                    st.session_state.pop("editing_name", None)
                    persist_now()
                    st.rerun()
    else:
        # Should only appear if someone bypasses onboarding
        st.markdown('<p class="sidebar-section">👤 Guest</p>', unsafe_allow_html=True)

    # ── Learning Settings ──────────────────────────────────────────────────────
    st.markdown('<p class="sidebar-section">⚙️ Learning Settings</p>',
                unsafe_allow_html=True)

    curriculum = get_curriculum()

    all_grades = curriculum.get_all_grades()
    grade = st.selectbox(
        "Grade",
        options=all_grades,
        index=all_grades.index(st.session_state.get("grade", 8)),
        key="grade_selector",
    )

    languages = curriculum.get_languages()
    language  = st.selectbox(
        "Language",
        options=languages,
        index=languages.index(st.session_state.get("language", "English")),
        key="language_selector",
    )

    subjects = curriculum.get_subjects_for_grade(grade)
    cur_subj = st.session_state.get("subject")
    subj_idx = subjects.index(cur_subj) if cur_subj in subjects else 0
    subject  = st.selectbox("Subject", options=subjects, index=subj_idx,
                             key="subject_selector")

    topics        = curriculum.get_topics_for_grade_subject(grade, subject)
    topic_options = ["All Topics"] + topics
    cur_topic     = st.session_state.get("topic", "All Topics")
    topic_idx     = topic_options.index(cur_topic) if cur_topic in topic_options else 0
    topic         = st.selectbox("Topic", options=topic_options, index=topic_idx,
                                 key="topic_selector")

    st.markdown("---")
    if st.button("🔄 Apply Settings", type="primary", use_container_width=True):
        changed = (
            grade    != st.session_state.get("grade")
            or language != st.session_state.get("language")
            or subject  != st.session_state.get("subject")
            or topic    != st.session_state.get("topic")
        )
        if changed:
            st.session_state.grade    = grade
            st.session_state.language = language
            st.session_state.subject  = subject
            st.session_state.topic    = topic
            st.session_state.settings_applied = True

            if "progress" in st.session_state:
                st.session_state.progress.end_session()
                st.session_state.progress.start_session()

            from backend_code.llm_handler import get_llm_handler
            handler = get_llm_handler()
            handler.clear_suggestion_cache()
            handler.clear_fact_cache()

            for key in ("quiz_questions", "quiz_submitted", "quiz_answers",
                        "quiz_score", "active_quiz"):
                st.session_state.pop(key, None)

            # persist_now includes the name — URL will have ?name=X&grade=Y...
            persist_now()
            st.success("✅ Settings applied!")
            st.rerun()
        else:
            st.info("Settings are already up to date.")

    # ── Current settings summary ───────────────────────────────────────────────
    st.markdown('<p class="sidebar-section">📋 Current Settings</p>',
                unsafe_allow_html=True)
    diff      = st.session_state.get("difficulty", "Standard")
    diff_icon = DIFFICULTY_ICONS.get(diff, "🟡")
    st.markdown(f"""
- **Grade:** {st.session_state.get('grade', grade)}
- **Language:** {st.session_state.get('language', language)}
- **Subject:** {st.session_state.get('subject', subject)}
- **Topic:** {st.session_state.get('topic', topic)}
- **Depth:** {diff_icon} {diff}
""")

    # ── AI Mode ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="sidebar-section">🧠 AI Mode</p>', unsafe_allow_html=True)

    socratic = st.toggle(
        "Socratic Mode",
        value=st.session_state.get("socratic_mode", False),
        help="ScienceGPT asks guiding questions instead of giving direct answers.",
        key="socratic_toggle",
    )
    st.session_state.socratic_mode = socratic

    if socratic:
        st.markdown('<div class="mode-badge mode-socratic">🦉 Socratic Mode ON</div>',
                    unsafe_allow_html=True)
        st.caption("ScienceGPT will guide you to the answer with questions.")
    else:
        st.markdown('<div class="mode-badge mode-standard">🤖 Standard Mode</div>',
                    unsafe_allow_html=True)

    # ── Quick stats ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="sidebar-section">📊 Quick Stats</p>', unsafe_allow_html=True)
    if "gamification" in st.session_state:
        stats = st.session_state.gamification.get_stats()
        col1, col2 = st.columns(2)
        col1.metric("🎯 Points", stats["points"])
        col2.metric("🔥 Streak", f"{stats['streak_days']}d")

    # ── Study List ─────────────────────────────────────────────────────────────
    st.markdown("---")
    draw_study_list()

    # ── Report Card ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="sidebar-section">📄 Report Card</p>', unsafe_allow_html=True)
    from frontend_components.report_card import draw_report_card_section
    draw_report_card_section()

    # ── Branding ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center; padding:10px 0; font-size:0.82rem; color:#94a3b8;">
            Made with ❤️ by
            <a href="https://www.linkedin.com/in/aseem-mehrotra/" target="_blank"
               style="color:#3B82F6; text-decoration:none; font-weight:600;">
               Aseem Mehrotra
            </a><br>
            <span style="font-size:0.75rem;">ScienceGPT v3.0</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
