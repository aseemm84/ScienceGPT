"""
Sidebar Component for ScienceGPT
Handles grade, language, subject, and topic selection
"""

import streamlit as st
from typing import Dict
from backend_code.curriculum_data import CurriculumData

class Sidebar:
    """Manages the sidebar interface for user selections"""

    def __init__(self, curriculum_data: CurriculumData):
        self.curriculum_data = curriculum_data

    def display(self) -> Dict:
        """Display sidebar and return user selections"""
        st.sidebar.title("🎓 Learning Settings")

        # Grade selection
        grades = self.curriculum_data.get_grades()
        selected_grade = st.sidebar.selectbox(
            "Select Grade",
            grades,
            index=2,  # Default to grade 3
            help="Choose your grade level"
        )

        # Language selection
        languages = self.curriculum_data.get_languages()
        selected_language = st.sidebar.selectbox(
            "Select Language",
            languages,
            index=0,  # Default to English
            help="Choose your preferred language"
        )

        # Subject selection
        subjects = self.curriculum_data.get_subjects(selected_grade)
        selected_subject = st.sidebar.selectbox(
            "Select Subject",
            subjects,
            help="Choose the science subject"
        )

        # Topic selection
        topics = self.curriculum_data.get_topics(selected_grade, selected_subject)
        if topics:
            selected_topic = st.sidebar.selectbox(
                "Select Topic",
                ["All Topics"] + topics,
                help="Choose a specific topic (optional)"
            )
            if selected_topic == "All Topics":
                selected_topic = None
        else:
            selected_topic = None

        # Apply button
        st.sidebar.markdown("---")
        apply_settings = st.sidebar.button(
            "🚀 Apply Settings",
            type="primary",
            help="Apply your selections and update suggestions"
        )

        # Display current selection summary
        st.sidebar.markdown("### 📋 Current Selection")
        st.sidebar.write(f"**Grade:** {selected_grade}")
        st.sidebar.write(f"**Language:** {selected_language}")
        st.sidebar.write(f"**Subject:** {selected_subject}")
        if selected_topic:
            st.sidebar.write(f"**Topic:** {selected_topic}")

        # Learning progress section
        self._display_progress_section()

        return {
            "grade": selected_grade,
            "language": selected_language,
            "subject": selected_subject,
            "topic": selected_topic,
            "apply_pressed": apply_settings
        }

    def _display_progress_section(self):
        """Display learning progress in sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Your Progress")

        # Points display
        points = st.session_state.get('user_points', 0)
        st.sidebar.metric("Points Earned", points, delta=None)

        # Streak display
        streak = st.session_state.get('streak_count', 0)
        st.sidebar.metric("Learning Streak", f"{streak} days", delta=None)

        # Questions asked
        questions = st.session_state.get('questions_answered', 0)
        st.sidebar.metric("Questions Asked", questions, delta=None)

        # Badges count
        badges = st.session_state.get('user_badges', [])
        st.sidebar.metric("Badges Earned", len(badges), delta=None)

        # Progress bar for next level
        next_level_points = ((points // 100) + 1) * 100
        progress = (points % 100) / 100
        st.sidebar.progress(progress)
        st.sidebar.caption(f"Next level: {100 - (points % 100)} points to go!")
