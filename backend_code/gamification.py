"""
Gamification Manager for ScienceGPT
Handles points, badges, and achievement system
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any

class GamificationManager:
    """Manages gamification features like points, badges, and achievements"""

    def __init__(self):
        """Initialize gamification manager"""
        self.badges = {
            "first_question": {
                "name": "Curious Mind",
                "description": "Asked your first question",
                "icon": "🤔",
                "points_required": 0
            },
            "question_master": {
                "name": "Question Master", 
                "description": "Asked 10 questions",
                "icon": "❓",
                "points_required": 100
            },
            "daily_learner": {
                "name": "Daily Learner",
                "description": "Used the app for 3 consecutive days",
                "icon": "📚",
                "points_required": 0
            },
            "science_explorer": {
                "name": "Science Explorer",
                "description": "Explored 3 different subjects",
                "icon": "🔬",
                "points_required": 0
            },
            "fact_collector": {
                "name": "Fact Collector",
                "description": "Generated 5 facts of the day",
                "icon": "💡",
                "points_required": 0
            },
            "point_milestone_50": {
                "name": "Rising Star",
                "description": "Earned 50 points",
                "icon": "⭐",
                "points_required": 50
            },
            "point_milestone_100": {
                "name": "Science Star", 
                "description": "Earned 100 points",
                "icon": "🌟",
                "points_required": 100
            },
            "point_milestone_200": {
                "name": "Knowledge Champion",
                "description": "Earned 200 points",
                "icon": "🏆", 
                "points_required": 200
            }
        }

        # Initialize session state for gamification
        if 'gamification_data' not in st.session_state:
            st.session_state.gamification_data = {
                "points": 0,
                "badges": [],
                "questions_asked": 0,
                "subjects_explored": set(),
                "facts_generated": 0,
                "streak_days": 0,
                "last_visit": datetime.now(),
                "daily_visits": []
            }

    def add_points(self, points: int):
        """Add points to user's total"""
        st.session_state.gamification_data["points"] += points
        self.check_achievements()

    def get_total_points(self) -> int:
        """Get total points earned"""
        return st.session_state.gamification_data.get("points", 0)

    def add_question(self):
        """Record that a question was asked"""
        st.session_state.gamification_data["questions_asked"] += 1
        self.add_points(10)  # 10 points per question

    def add_subject_explored(self, subject: str):
        """Record that a subject was explored"""
        st.session_state.gamification_data["subjects_explored"].add(subject)

    def add_fact_generated(self):
        """Record that a fact was generated"""
        st.session_state.gamification_data["facts_generated"] += 1
        self.add_points(5)  # 5 points per fact

    def update_streak(self):
        """Update daily learning streak"""
        today = datetime.now().date()
        last_visit = st.session_state.gamification_data.get("last_visit")

        if isinstance(last_visit, str):
            last_visit = datetime.fromisoformat(last_visit).date()
        elif isinstance(last_visit, datetime):
            last_visit = last_visit.date()
        else:
            last_visit = today

        daily_visits = st.session_state.gamification_data.get("daily_visits", [])

        # Convert string dates back to date objects if needed
        daily_visits = [
            datetime.fromisoformat(d).date() if isinstance(d, str) else d
            for d in daily_visits
        ]

        if today not in daily_visits:
            daily_visits.append(today)
            st.session_state.gamification_data["daily_visits"] = daily_visits

            # Calculate streak
            daily_visits.sort(reverse=True)
            streak = 1
            for i in range(1, len(daily_visits)):
                if daily_visits[i-1] - daily_visits[i] == timedelta(days=1):
                    streak += 1
                else:
                    break

            st.session_state.gamification_data["streak_days"] = streak
            st.session_state.gamification_data["last_visit"] = today

    def check_achievements(self):
        """Check and award new badges"""
        data = st.session_state.gamification_data
        current_badges = set(data.get("badges", []))
        new_badges = []

        # Check point-based badges
        points = data.get("points", 0)
        for badge_id, badge_info in self.badges.items():
            if badge_id not in current_badges and points >= badge_info["points_required"]:
                if badge_id.startswith("point_milestone"):
                    current_badges.add(badge_id)
                    new_badges.append(badge_id)

        # Check first question badge
        if "first_question" not in current_badges and data.get("questions_asked", 0) >= 1:
            current_badges.add("first_question")
            new_badges.append("first_question")

        # Check question master badge
        if "question_master" not in current_badges and data.get("questions_asked", 0) >= 10:
            current_badges.add("question_master")
            new_badges.append("question_master")

        # Check daily learner badge
        if "daily_learner" not in current_badges and data.get("streak_days", 0) >= 3:
            current_badges.add("daily_learner")
            new_badges.append("daily_learner")

        # Check science explorer badge
        if "science_explorer" not in current_badges and len(data.get("subjects_explored", set())) >= 3:
            current_badges.add("science_explorer")
            new_badges.append("science_explorer")

        # Check fact collector badge
        if "fact_collector" not in current_badges and data.get("facts_generated", 0) >= 5:
            current_badges.add("fact_collector")
            new_badges.append("fact_collector")

        # Update badges in session state
        st.session_state.gamification_data["badges"] = list(current_badges)

        # Show notifications for new badges
        if new_badges:
            for badge_id in new_badges:
                badge = self.badges[badge_id]
                st.toast(f"🎉 New Badge: {badge['icon']} {badge['name']}")

    def get_user_badges(self) -> List[Dict[str, Any]]:
        """Get list of user's earned badges with details"""
        earned_badge_ids = st.session_state.gamification_data.get("badges", [])
        return [
            {
                "id": badge_id,
                "name": self.badges[badge_id]["name"],
                "description": self.badges[badge_id]["description"],
                "icon": self.badges[badge_id]["icon"]
            }
            for badge_id in earned_badge_ids if badge_id in self.badges
        ]

    def get_available_badges(self) -> List[Dict[str, Any]]:
        """Get list of badges not yet earned"""
        earned_badge_ids = set(st.session_state.gamification_data.get("badges", []))
        return [
            {
                "id": badge_id,
                "name": badge_info["name"],
                "description": badge_info["description"], 
                "icon": badge_info["icon"],
                "points_required": badge_info["points_required"]
            }
            for badge_id, badge_info in self.badges.items()
            if badge_id not in earned_badge_ids
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        data = st.session_state.gamification_data
        return {
            "points": data.get("points", 0),
            "badges_count": len(data.get("badges", [])),
            "questions_asked": data.get("questions_asked", 0),
            "subjects_explored": len(data.get("subjects_explored", set())),
            "facts_generated": data.get("facts_generated", 0),
            "streak_days": data.get("streak_days", 0)
        }
