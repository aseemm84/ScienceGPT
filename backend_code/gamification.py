"""
Gamification System for ScienceGPT
Manages points, badges, streaks, and rewards
"""

import streamlit as st
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import json

class GamificationSystem:
    """Handles all gamification features"""

    def __init__(self):
        self.badge_definitions = self._define_badges()
        self.point_system = self._define_point_system()

    def _define_badges(self) -> Dict:
        """Define available badges and their criteria"""
        return {
            "first_question": {
                "name": "Curious Mind",
                "icon": "🤔",
                "description": "Asked your first question",
                "criteria": {"questions_asked": 1}
            },
            "science_explorer": {
                "name": "Science Explorer",
                "icon": "🔍",
                "description": "Asked 10 science questions",
                "criteria": {"questions_asked": 10}
            },
            "daily_learner": {
                "name": "Daily Learner",
                "icon": "📅",
                "description": "Used ScienceGPT for 3 consecutive days",
                "criteria": {"streak_days": 3}
            },
            "week_warrior": {
                "name": "Week Warrior",
                "icon": "🗓️",
                "description": "7 day learning streak",
                "criteria": {"streak_days": 7}
            },
            "quiz_master": {
                "name": "Quiz Master",
                "icon": "🧠",
                "description": "Answered 5 quiz questions correctly",
                "criteria": {"correct_answers": 5}
            },
            "points_collector": {
                "name": "Points Collector",
                "icon": "⭐",
                "description": "Earned 100 points",
                "criteria": {"total_points": 100}
            },
            "science_star": {
                "name": "Science Star",
                "icon": "🌟",
                "description": "Earned 500 points",
                "criteria": {"total_points": 500}
            },
            "topic_master": {
                "name": "Topic Master",
                "icon": "🎯",
                "description": "Explored 5 different topics",
                "criteria": {"topics_explored": 5}
            },
            "helping_hand": {
                "name": "Helping Hand",
                "icon": "🤝",
                "description": "Shared knowledge with classmates",
                "criteria": {"shares": 3}
            },
            "consistent_learner": {
                "name": "Consistent Learner",
                "icon": "📈",
                "description": "30 day learning streak",
                "criteria": {"streak_days": 30}
            }
        }

    def _define_point_system(self) -> Dict:
        """Define point rewards for different actions"""
        return {
            "question_asked": 10,
            "daily_challenge": 25,
            "correct_answer": 15,
            "topic_exploration": 5,
            "daily_login": 5,
            "sharing_knowledge": 20,
            "completing_lesson": 30
        }

    def award_points(self, action: str, multiplier: int = 1) -> int:
        """Award points for specific actions"""
        base_points = self.point_system.get(action, 0)
        points_earned = base_points * multiplier

        # Update session state
        if 'user_points' not in st.session_state:
            st.session_state.user_points = 0
        st.session_state.user_points += points_earned

        return points_earned

    def check_and_award_badges(self) -> List[Dict]:
        """Check for new badges and award them"""
        newly_earned = []

        if 'user_badges' not in st.session_state:
            st.session_state.user_badges = []

        # Get current user stats
        stats = self._get_user_stats()

        for badge_id, badge_info in self.badge_definitions.items():
            if badge_id not in st.session_state.user_badges:
                if self._check_badge_criteria(badge_info["criteria"], stats):
                    st.session_state.user_badges.append(badge_id)
                    newly_earned.append({
                        "id": badge_id,
                        "name": badge_info["name"],
                        "icon": badge_info["icon"],
                        "description": badge_info["description"]
                    })

        return newly_earned

    def _get_user_stats(self) -> Dict:
        """Get current user statistics"""
        return {
            "questions_asked": st.session_state.get('questions_answered', 0),
            "streak_days": st.session_state.get('streak_count', 0),
            "correct_answers": st.session_state.get('correct_answers', 0),
            "total_points": st.session_state.get('user_points', 0),
            "topics_explored": st.session_state.get('topics_explored', 0),
            "shares": st.session_state.get('knowledge_shares', 0)
        }

    def _check_badge_criteria(self, criteria: Dict, stats: Dict) -> bool:
        """Check if badge criteria are met"""
        for criterion, required_value in criteria.items():
            if stats.get(criterion, 0) < required_value:
                return False
        return True

    def get_user_badges(self) -> List[Dict]:
        """Get user's earned badges"""
        user_badge_ids = st.session_state.get('user_badges', [])
        badges = []

        for badge_id in user_badge_ids:
            if badge_id in self.badge_definitions:
                badge_info = self.badge_definitions[badge_id]
                badges.append({
                    "id": badge_id,
                    "name": badge_info["name"],
                    "icon": badge_info["icon"],
                    "description": badge_info["description"]
                })

        return badges

    def get_next_badges(self) -> List[Dict]:
        """Get badges that are close to being earned"""
        user_badge_ids = st.session_state.get('user_badges', [])
        stats = self._get_user_stats()
        next_badges = []

        for badge_id, badge_info in self.badge_definitions.items():
            if badge_id not in user_badge_ids:
                progress = self._calculate_badge_progress(badge_info["criteria"], stats)
                if progress > 0.3:  # Show badges that are at least 30% complete
                    next_badges.append({
                        "id": badge_id,
                        "name": badge_info["name"],
                        "icon": badge_info["icon"],
                        "description": badge_info["description"],
                        "progress": progress
                    })

        return sorted(next_badges, key=lambda x: x["progress"], reverse=True)[:3]

    def _calculate_badge_progress(self, criteria: Dict, stats: Dict) -> float:
        """Calculate progress toward earning a badge"""
        if not criteria:
            return 0.0

        total_progress = 0
        for criterion, required_value in criteria.items():
            current_value = stats.get(criterion, 0)
            progress = min(current_value / required_value, 1.0)
            total_progress += progress

        return total_progress / len(criteria)

    def update_streak(self):
        """Update daily learning streak"""
        today = datetime.now().date()
        last_visit = st.session_state.get('last_visit_date')

        if last_visit:
            last_date = datetime.strptime(last_visit, '%Y-%m-%d').date()
            if today == last_date:
                # Same day, no change
                return
            elif today == last_date + timedelta(days=1):
                # Consecutive day, increase streak
                st.session_state.streak_count = st.session_state.get('streak_count', 0) + 1
            else:
                # Break in streak, reset
                st.session_state.streak_count = 1
        else:
            # First visit
            st.session_state.streak_count = 1

        st.session_state.last_visit_date = today.strftime('%Y-%m-%d')

        # Award daily login points
        self.award_points("daily_login")
