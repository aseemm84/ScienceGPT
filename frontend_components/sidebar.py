"""
Enhanced Sidebar Component for ScienceGPT
Handles grade, language, subject, and topic selection with dynamic updates
"""

import streamlit as st
from backend_code.curriculum_data import CurriculumData

def draw_sidebar():
    """Draw the enhanced sidebar with dynamic content updates"""
    st.title("🧪 ScienceGPT")
    st.markdown("*AI-Powered Science Learning*")

    # Initialize curriculum data
    curriculum = CurriculumData()

    # Current settings display
    st.markdown("### 📚 Learning Settings")

    # Grade selection
    grade = st.selectbox(
        "Select Grade:",
        options=list(range(1, 9)),
        index=2,  # Default to grade 3
        key="grade_selector"
    )

    # Language selection
    languages = curriculum.get_languages()
    language = st.selectbox(
        "Select Language:",
        options=languages,
        index=languages.index("English") if "English" in languages else 0,
        key="language_selector"
    )

    # Subject selection
    subjects = curriculum.get_subjects_for_grade(grade)
    subject = st.selectbox(
        "Select Subject:",
        options=subjects,
        index=subjects.index("General Science") if "General Science" in subjects else 0,
        key="subject_selector"
    )

    # Topic selection
    topics = curriculum.get_topics_for_grade_subject(grade, subject)
    topic = st.selectbox(
        "Select Topic:",
        options=["All Topics"] + topics,
        index=0,
        key="topic_selector"
    )

    # Apply Settings Button - This is the key enhancement
    st.markdown("---")
    if st.button("🔄 Apply Settings", type="primary", use_container_width=True):
        # Update session state with new settings
        old_settings = (st.session_state.get('grade', 3), 
                       st.session_state.get('subject', 'General Science'),
                       st.session_state.get('language', 'English'),
                       st.session_state.get('topic', 'All Topics'))

        new_settings = (grade, subject, language, topic)

        # Update session state
        st.session_state.grade = grade
        st.session_state.language = language
        st.session_state.subject = subject
        st.session_state.topic = topic

        # Check if settings actually changed
        if old_settings != new_settings:
            # Clear caches to force regeneration of suggestions and facts
            if 'llm_handler' in st.session_state:
                st.session_state.llm_handler.clear_suggestion_cache()
                st.session_state.llm_handler.clear_fact_cache()

            # Set flag to indicate settings were applied
            st.session_state.settings_applied = True

            # Show success message
            st.success("✅ Settings applied! New suggestions and fact will be generated.")

            # Trigger rerun to update content
            st.rerun()
        else:
            st.info("Settings are already up to date!")

    # Show current settings
    st.markdown("#### 📋 Current Settings:")
    current_grade = st.session_state.get('grade', grade)
    current_language = st.session_state.get('language', language)
    current_subject = st.session_state.get('subject', subject)
    current_topic = st.session_state.get('topic', topic)

    st.markdown(f"""
    - **Grade:** {current_grade}
    - **Language:** {current_language}
    - **Subject:** {current_subject}
    - **Topic:** {current_topic}
    """)

    # Progress summary
    st.markdown("---")
    st.markdown("#### 📈 Progress Summary")

    points = st.session_state.get('points', 0)
    streak = st.session_state.get('streak', 0)
    badges_count = len(st.session_state.get('badges', []))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Points", points)
        st.metric("Streak", f"{streak} days")
    with col2:
        st.metric("Badges", badges_count)
        questions_asked = len([msg for msg in st.session_state.get('messages', []) if msg.get('role') == 'user'])
        st.metric("Questions", questions_asked)

    # Quick tips
    st.markdown("---")
    st.markdown("#### 💡 Quick Tips")
    st.markdown("""
    - Use **Apply Settings** to refresh suggestions and facts
    - Ask questions to earn points and badges
    - Visit daily to maintain your learning streak
    - Explore different topics to broaden your knowledge
    """)

    # Version info
    st.markdown("---")
    st.markdown("*ScienceGPT v2.0 - Enhanced*")
