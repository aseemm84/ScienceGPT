"""
Gamification UI Component for ScienceGPT
Displays points, badges, streaks, and achievements
"""

import streamlit as st
from typing import List, Dict
from backend_code.gamification import GamificationSystem

class GamificationUI:
    """Handles gamification display elements"""

    def __init__(self):
        self.gamification = GamificationSystem()

    def display_top_stats(self):
        """Display top-level gamification stats"""
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            points = st.session_state.get('user_points', 0)
            st.metric(
                label="🌟 Points",
                value=points,
                delta=None,
                help="Points earned from learning activities"
            )

        with col2:
            streak = st.session_state.get('streak_count', 0)
            st.metric(
                label="🔥 Streak",
                value=f"{streak} days",
                delta=None,
                help="Consecutive days of learning"
            )

        with col3:
            badges = st.session_state.get('user_badges', [])
            st.metric(
                label="🏆 Badges",
                value=len(badges),
                delta=None,
                help="Achievement badges earned"
            )

        with col4:
            questions = st.session_state.get('questions_answered', 0)
            st.metric(
                label="❓ Questions",
                value=questions,
                delta=None,
                help="Total questions asked"
            )

        # Progress towards next level
        self._display_level_progress()

        # Badges display
        self._display_badges_section()

    def _display_level_progress(self):
        """Display progress towards next level"""
        points = st.session_state.get('user_points', 0)
        current_level = points // 100 + 1
        points_in_level = points % 100
        points_to_next = 100 - points_in_level

        st.markdown("### 📈 Level Progress")

        col1, col2 = st.columns([3, 1])
        with col1:
            progress = points_in_level / 100
            st.progress(progress)
            st.caption(f"Level {current_level} - {points_to_next} points to next level")

        with col2:
            st.markdown(f"**Level {current_level}**")

    def _display_badges_section(self):
        """Display earned badges and upcoming badges"""
        st.markdown("### 🏆 Achievements")

        # Tabs for different badge views
        tab1, tab2 = st.tabs(["🎉 Earned Badges", "🎯 Next Goals"])

        with tab1:
            self._display_earned_badges()

        with tab2:
            self._display_next_badges()

    def _display_earned_badges(self):
        """Display badges the user has earned"""
        earned_badges = self.gamification.get_user_badges()

        if not earned_badges:
            st.info("🎯 Start learning to earn your first badge!")
            return

        # Display badges in a grid
        cols = st.columns(3)
        for i, badge in enumerate(earned_badges):
            col = cols[i % 3]
            with col:
                st.markdown(f"""
                <div style="
                    text-align: center; 
                    padding: 1rem; 
                    border: 2px solid #4CAF50; 
                    border-radius: 10px; 
                    margin: 0.5rem 0;
                    background: linear-gradient(45deg, #f0f9ff, #e0f2fe);
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{badge['icon']}</div>
                    <div style="font-weight: bold; color: #1976d2;">{badge['name']}</div>
                    <div style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">{badge['description']}</div>
                </div>
                """, unsafe_allow_html=True)

    def _display_next_badges(self):
        """Display upcoming badges and progress"""
        next_badges = self.gamification.get_next_badges()

        if not next_badges:
            st.info("🌟 Great job! You're working towards more advanced achievements.")
            return

        for badge in next_badges:
            progress_percent = int(badge['progress'] * 100)

            with st.container():
                col1, col2 = st.columns([1, 3])

                with col1:
                    st.markdown(f"<div style='font-size: 2rem; text-align: center;'>{badge['icon']}</div>", unsafe_allow_html=True)

                with col2:
                    st.markdown(f"**{badge['name']}**")
                    st.progress(badge['progress'])
                    st.caption(f"{badge['description']} - {progress_percent}% complete")

                st.markdown("---")

    def display_leaderboard(self):
        """Display a simple leaderboard (placeholder for future implementation)"""
        st.markdown("### 🏅 Leaderboard")
        st.info("🚀 Leaderboard feature coming soon! Compare your progress with classmates.")

    def display_achievements_popup(self, badges: List[Dict]):
        """Display achievement popup for new badges"""
        if not badges:
            return

        for badge in badges:
            st.markdown(f"""
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
                color: white;
                padding: 1rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                animation: slideIn 0.5s ease-out;
            ">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">{badge['icon']}</div>
                    <div style="font-weight: bold; font-size: 1.2rem;">New Badge Earned!</div>
                    <div style="font-size: 1rem; margin: 0.5rem 0;">{badge['name']}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">{badge['description']}</div>
                </div>
            </div>

            <style>
            @keyframes slideIn {{
                from {{ transform: translateX(100%); }}
                to {{ transform: translateX(0); }}
            }}
            </style>
            """, unsafe_allow_html=True)
