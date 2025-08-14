"""
Enhanced Sidebar Component for ScienceGPT
Handles grade, language, subject, and topic selection with dynamic updates for Grades 1-12.
"""

import streamlit as st
from backend_code.curriculum_data import CurriculumData

def draw_sidebar():
    """Draw the enhanced sidebar with dynamic content updates."""
    st.title("🧪 ScienceGPT")
    st.markdown("*AI-Powered Science Learning*")

    # Instantiate the curriculum data handler
    curriculum = CurriculumData()

    st.markdown("### 📚 Learning Settings")

    # Grade selection for Grades 1-12
    all_grades = curriculum.get_all_grades()
    # Default to Grade 8 (index 7) if not set
    grade_index = all_grades.index(st.session_state.get('grade', 8)) 
    grade = st.selectbox(
        "Select Grade:",
        options=all_grades,
        index=grade_index,
        key="grade_selector"
    )

    # Language selection
    languages = curriculum.get_languages()
    language_index = languages.index(st.session_state.get('language', 'English'))
    language = st.selectbox(
        "Select Language:",
        options=languages,
        index=language_index,
        key="language_selector"
    )

    # Subject selection - dynamically updates based on grade
    subjects = curriculum.get_subjects_for_grade(grade)
    current_subject = st.session_state.get('subject')
    # If the current subject is not valid for the new grade, default to the first one
    subject_index = subjects.index(current_subject) if current_subject in subjects else 0
    subject = st.selectbox(
        "Select Subject:",
        options=subjects,
        index=subject_index,
        key="subject_selector"
    )

    # Topic selection - dynamically updates based on grade and subject
    topics = curriculum.get_topics_for_grade_subject(grade, subject)
    topic_options = ["All Topics"] + topics
    current_topic = st.session_state.get('topic')
    topic_index = topic_options.index(current_topic) if current_topic in topic_options else 0
    topic = st.selectbox(
        "Select Topic:",
        options=topic_options,
        index=topic_index,
        key="topic_selector"
    )

    st.markdown("---")
    if st.button("🔄 Apply Settings", type="primary", use_container_width=True):
        # Check if settings have changed before applying
        if (grade != st.session_state.get('grade') or
            language != st.session_state.get('language') or
            subject != st.session_state.get('subject') or
            topic != st.session_state.get('topic')):
            
            # Update session state
            st.session_state.grade = grade
            st.session_state.language = language
            st.session_state.subject = subject
            st.session_state.topic = topic

            # Clear caches to force regeneration of dynamic content
            if 'llm_handler' in st.session_state:
                st.session_state.llm_handler.clear_suggestion_cache()
                st.session_state.llm_handler.clear_fact_cache()

            st.session_state.settings_applied = True
            st.success("✅ Settings applied!")
            st.rerun()
        else:
            st.info("Settings are already up to date!")

    # Display current settings
    st.markdown("#### 📋 Current Settings:")
    st.markdown(f"""
    - **Grade:** {st.session_state.get('grade', grade)}
    - **Language:** {st.session_state.get('language', language)}
    - **Subject:** {st.session_state.get('subject', subject)}
    - **Topic:** {st.session_state.get('topic', topic)}
    """)

    st.markdown("---")
    st.markdown("*ScienceGPT v3.0 - High School Edition*")
