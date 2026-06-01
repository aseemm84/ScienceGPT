"""
Sidebar Component v2 for ScienceGPT.
Changes vs v1:
- Uses @st.cache_resource singleton for CurriculumData
- Socratic mode toggle
- Settings auto-apply on change (no separate button press required for grade/subject)
- Clean section headers using CSS class
"""

import streamlit as st
from backend_code.curriculum_data import get_curriculum


def draw_sidebar() -> None:
    """Render the sidebar: settings, mode toggles, quick stats."""

    st.markdown('<p class="sidebar-section">⚙️ Learning Settings</p>', unsafe_allow_html=True)

    curriculum = get_curriculum()

    # ── Grade ──────────────────────────────────────────────────────────────────
    all_grades = curriculum.get_all_grades()
    grade = st.selectbox(
        "Grade",
        options=all_grades,
        index=all_grades.index(st.session_state.get("grade", 8)),
        key="grade_selector",
    )

    # ── Language ───────────────────────────────────────────────────────────────
    languages = curriculum.get_languages()
    language = st.selectbox(
        "Language",
        options=languages,
        index=languages.index(st.session_state.get("language", "English")),
        key="language_selector",
    )

    # ── Subject (depends on grade) ─────────────────────────────────────────────
    subjects = curriculum.get_subjects_for_grade(grade)
    cur_subj = st.session_state.get("subject")
    subj_idx = subjects.index(cur_subj) if cur_subj in subjects else 0
    subject = st.selectbox(
        "Subject",
        options=subjects,
        index=subj_idx,
        key="subject_selector",
    )

    # ── Topic (depends on grade + subject) ────────────────────────────────────
    topics = curriculum.get_topics_for_grade_subject(grade, subject)
    topic_options = ["All Topics"] + topics
    cur_topic = st.session_state.get("topic", "All Topics")
    topic_idx = topic_options.index(cur_topic) if cur_topic in topic_options else 0
    topic = st.selectbox(
        "Topic",
        options=topic_options,
        index=topic_idx,
        key="topic_selector",
    )

    # ── Apply settings ─────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("🔄 Apply Settings", type="primary", use_container_width=True):
        changed = (
            grade != st.session_state.get("grade")
            or language != st.session_state.get("language")
            or subject != st.session_state.get("subject")
            or topic != st.session_state.get("topic")
        )
        if changed:
            st.session_state.grade = grade
            st.session_state.language = language
            st.session_state.subject = subject
            st.session_state.topic = topic
            st.session_state.settings_applied = True

            # End current session and start fresh
            if "progress" in st.session_state:
                st.session_state.progress.end_session()
                st.session_state.progress.start_session()

            # Clear caches so new settings take effect
            from backend_code.llm_handler import get_llm_handler
            handler = get_llm_handler()
            handler.clear_suggestion_cache()
            handler.clear_fact_cache()

            # Reset quiz state
            for key in ("quiz_questions", "quiz_submitted", "quiz_answers",
                        "quiz_score", "active_quiz"):
                st.session_state.pop(key, None)

            st.success("✅ Settings applied!")
            st.rerun()
        else:
            st.info("Settings are already up to date.")

    # ── Current settings summary ───────────────────────────────────────────────
    st.markdown('<p class="sidebar-section">📋 Current Settings</p>', unsafe_allow_html=True)
    st.markdown(f"""
- **Grade:** {st.session_state.get('grade', grade)}
- **Language:** {st.session_state.get('language', language)}
- **Subject:** {st.session_state.get('subject', subject)}
- **Topic:** {st.session_state.get('topic', topic)}
""")

    # ── AI Mode ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="sidebar-section">🧠 AI Mode</p>', unsafe_allow_html=True)

    socratic = st.toggle(
        "Socratic Mode",
        value=st.session_state.get("socratic_mode", False),
        help="Claude asks guiding questions instead of giving direct answers.",
        key="socratic_toggle",
    )
    st.session_state.socratic_mode = socratic

    if socratic:
        st.markdown(
            '<div class="mode-badge mode-socratic">🦉 Socratic Mode ON</div>',
            unsafe_allow_html=True,
        )
        st.caption("Claude will guide you to the answer with questions.")
    else:
        st.markdown(
            '<div class="mode-badge mode-standard">🤖 Standard Mode</div>',
            unsafe_allow_html=True,
        )

    # ── Quick stats ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="sidebar-section">📊 Quick Stats</p>', unsafe_allow_html=True)

    if "gamification" in st.session_state:
        stats = st.session_state.gamification.get_stats()
        col1, col2 = st.columns(2)
        col1.metric("🎯 Points", stats["points"])
        col2.metric("🔥 Streak", f"{stats['streak_days']}d")

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
            <span style="font-size:0.75rem;">ScienceGPT v2.0</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
