"""
ScienceGPT - AI-Powered Science Learning Tool
Main Streamlit application
"""

import streamlit as st
import os
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="ScienceGPT",
    page_icon="🧪",
    layout="wide"
)

# Import components
from frontend_components.sidebar import draw_sidebar
from frontend_components.main_interface import draw_main_interface
from frontend_components.gamification_ui import draw_gamification_ui
from frontend_components.daily_challenge import draw_daily_challenge

from backend_code.llm_handler import LLMHandler
from backend_code.curriculum_data import CurriculumData
from backend_code.gamification import GamificationManager
from backend_code.student_progress import StudentProgress

# Initialize session state variables
def initialize_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.grade = 3
        st.session_state.language = 'English'
        st.session_state.subject = 'General Science'
        st.session_state.topic = 'All Topics'
        st.session_state.messages = []
        st.session_state.points = 0
        st.session_state.badges = []
        st.session_state.streak = 0
        st.session_state.last_visit = datetime.now()

        # New states for dynamic content
        st.session_state.last_settings_hash = None
        st.session_state.cached_suggestions = []
        st.session_state.cached_fact = {}
        st.session_state.last_fact_time = {}
        st.session_state.settings_applied = False

def main():
    """Main application function"""
    initialize_session_state()

    # Initialize backend components
    llm_handler = LLMHandler()
    curriculum_data = CurriculumData()
    gamification = GamificationManager()
    progress = StudentProgress()

    # Store in session state for access by components
    st.session_state.llm_handler = llm_handler
    st.session_state.curriculum_data = curriculum_data
    st.session_state.gamification = gamification
    st.session_state.progress = progress

    # Main layout
    with st.sidebar:
        draw_sidebar()

    # Main content area
    col1, col2 = st.columns([3, 1])

    with col1:
        draw_main_interface()

    with col2:
        draw_daily_challenge()
        st.divider()
        draw_gamification_ui()

if __name__ == "__main__":
    main()
