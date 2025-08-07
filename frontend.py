"""
ScienceGPT - A Science Education Tool for Indian Students (Grades 1-8)
Main frontend interface built with Streamlit
"""

import streamlit as st
import os
from datetime import datetime
import json

# Import backend components
from backend_code.llm_handler import LLMHandler
from backend_code.curriculum_data import CurriculumData
from backend_code.gamification import GamificationSystem
from backend_code.student_progress import StudentProgress

# Import frontend components
from frontend_components.sidebar import Sidebar
from frontend_components.main_interface import MainInterface
from frontend_components.gamification_ui import GamificationUI
from frontend_components.daily_challenge import DailyChallenge

# Page configuration
st.set_page_config(
    page_title="ScienceGPT - Learn Science with AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .badge-container {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 1rem 0;
    }
    .badge {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .daily-challenge {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4ecdc4;
    }
    .progress-bar {
        height: 20px;
        background: #ddd;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        border-radius: 10px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""

    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user_points = 0
        st.session_state.user_badges = []
        st.session_state.streak_count = 0
        st.session_state.questions_answered = 0

    # Initialize backend systems
    try:
        llm_handler = LLMHandler()
        curriculum_data = CurriculumData()
        gamification = GamificationSystem()
        student_progress = StudentProgress()
    except Exception as e:
        st.error(f"Error initializing system: {e}")
        return

    # Header
    st.markdown('<h1 class="main-header">🔬 ScienceGPT</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your AI-Powered Science Learning Companion for Grades 1-8</p>', unsafe_allow_html=True)

    # Daily Challenge section
    daily_challenge = DailyChallenge(llm_handler, curriculum_data)
    daily_challenge.display()

    # Sidebar
    sidebar = Sidebar(curriculum_data)
    sidebar_settings = sidebar.display()

    # Gamification UI
    gamification_ui = GamificationUI()
    gamification_ui.display_top_stats()

    # Main interface
    main_interface = MainInterface(llm_handler, curriculum_data, gamification)
    main_interface.display(sidebar_settings)

    # Footer
    st.markdown("---")
    st.markdown(
        "**ScienceGPT** - Empowering young minds to explore science with AI assistance. "
        "Built for Indian students following NCERT curriculum."
    )

if __name__ == "__main__":
    main()
