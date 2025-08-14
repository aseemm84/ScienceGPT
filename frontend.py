"""
ScienceGPT - AI-Powered Science Learning Tool
Main Streamlit application
"""

import streamlit as st
from datetime import datetime

# Import components and backend modules
from frontend_components.sidebar import draw_sidebar
from frontend_components.main_interface import draw_main_interface
from frontend_components.gamification_ui import draw_gamification_ui
from frontend_components.daily_challenge import draw_daily_challenge

from backend_code.llm_handler import LLMHandler
from backend_code.curriculum_data import CurriculumData
from backend_code.gamification import GamificationManager
from backend_code.student_progress import StudentProgress

# Set page config
st.set_page_config(
    page_title="ScienceGPT",
    page_icon="🧪",
    layout="wide"
)

def initialize_session_state():
    """Initialize all session state variables on first run."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        
        # Default settings for a new user
        st.session_state.grade = 8  # A sensible default for a wide audience
        st.session_state.language = 'English'
        st.session_state.subject = 'Physics'  # A common subject for Grade 8
        st.session_state.topic = 'All Topics'
        
        # Core application state
        st.session_state.messages = []
        
        # Caching and flags
        st.session_state.last_settings_hash = None
        st.session_state.cached_suggestions = []
        st.session_state.fact_cache = {}
        st.session_state.settings_applied = False

        # Initialize backend managers to ensure they exist from the start
        st.session_state.llm_handler = LLMHandler()
        st.session_state.curriculum_data_handler = CurriculumData()
        st.session_state.gamification = GamificationManager()
        st.session_state.progress = StudentProgress()


def main():
    """Main application function."""
    initialize_session_state()

    # Main layout with sidebar and content columns
    with st.sidebar:
        draw_sidebar()

    col1, col2 = st.columns([3, 1])

    with col1:
        draw_main_interface()

    with col2:
        draw_daily_challenge()
        st.divider()
        draw_gamification_ui()

if __name__ == "__main__":
    main()
