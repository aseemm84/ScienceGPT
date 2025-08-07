"""
Gamification UI Component for ScienceGPT
Displays points, badges, and achievements
"""

import streamlit as st

def draw_gamification_ui():
    """Draw the gamification interface"""
    st.markdown("### 🏆 Your Achievements")

    # Initialize gamification if not already done
    if 'gamification' not in st.session_state:
        from backend_code.gamification import GamificationManager
        st.session_state.gamification = GamificationManager()

    gamification = st.session_state.gamification

    # Update streak
    gamification.update_streak()

    # Get user stats
    stats = gamification.get_stats()

    # Display key metrics
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="🎯 Points",
            value=stats["points"],
            help="Earn points by asking questions and completing challenges"
        )

        st.metric(
            label="🔥 Streak",
            value=f"{stats['streak_days']} days",
            help="Consecutive days of learning"
        )

    with col2:
        st.metric(
            label="🏅 Badges",
            value=stats["badges_count"],
            help="Achievements unlocked"
        )

        st.metric(
            label="❓ Questions",
            value=stats["questions_asked"],
            help="Questions asked"
        )

    # Display earned badges
    earned_badges = gamification.get_user_badges()

    if earned_badges:
        st.markdown("#### 🏅 Your Badges")

        # Display badges in a grid
        cols = st.columns(min(3, len(earned_badges)))

        for i, badge in enumerate(earned_badges):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 8px; margin: 5px;">
                    <div style="font-size: 24px;">{badge['icon']}</div>
                    <div style="font-size: 12px; font-weight: bold;">{badge['name']}</div>
                    <div style="font-size: 10px; color: #666;">{badge['description']}</div>
                </div>
                """, unsafe_allow_html=True)

    # Show progress towards next badges
    available_badges = gamification.get_available_badges()

    if available_badges:
        st.markdown("#### 🎯 Next Goals")

        # Show next 2 achievable badges
        current_points = stats["points"]

        # Sort by points required and show closest ones
        point_badges = [b for b in available_badges if b["points_required"] > 0]
        point_badges.sort(key=lambda x: x["points_required"])

        for badge in point_badges[:2]:
            points_needed = badge["points_required"] - current_points
            if points_needed > 0:
                progress = current_points / badge["points_required"]
                st.markdown(f"**{badge['icon']} {badge['name']}**")
                st.progress(progress)
                st.caption(f"{points_needed} more points needed")
                st.markdown("---")

    # Learning statistics
    st.markdown("#### 📊 Learning Stats")

    stats_text = f"""
    - **Subjects Explored:** {stats['subjects_explored']}
    - **Facts Generated:** {stats['facts_generated']}
    - **Learning Streak:** {stats['streak_days']} days
    """

    st.markdown(stats_text)

    # Motivational message based on performance
    if stats["points"] == 0:
        st.info("🌟 Start your learning journey by asking a question!")
    elif stats["points"] < 50:
        st.info("🚀 You're doing great! Keep asking questions to earn more points!")
    elif stats["points"] < 100:
        st.success("⭐ Excellent progress! You're becoming a science star!")
    else:
        st.success("🏆 Amazing! You're a true science champion!")

    # Reset progress (for testing/demo purposes)
    if st.button("🔄 Reset Progress", help="Reset all progress (for demo)"):
        if 'gamification_data' in st.session_state:
            st.session_state.gamification_data = {
                "points": 0,
                "badges": [],
                "questions_asked": 0,
                "subjects_explored": set(),
                "facts_generated": 0,
                "streak_days": 0,
                "last_visit": st.session_state.gamification_data.get("last_visit"),
                "daily_visits": []
            }
        st.rerun()
