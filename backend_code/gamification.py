"""
Gamification Manager for ScienceGPT v2.
Fixed: sets replaced with lists, subject tracking wired, badge triggers corrected.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Any

from config.constants import (
    POINTS_PER_QUESTION, POINTS_PER_FACT, POINTS_PER_CHALLENGE,
    POINTS_PER_QUIZ_CORRECT, POINTS_PER_EXPLAIN_BACK, POINTS_EXPLAIN_BACK_BASE,
)
from utils.helpers import get_logger

log = get_logger(__name__)

# ── Badge catalogue ───────────────────────────────────────────────────────────

BADGES: dict[str, dict[str, Any]] = {
    "first_question": {
        "name": "Curious Mind",
        "description": "Asked your first question",
        "icon": "🤔",
        "points_required": 0,
    },
    "question_master": {
        "name": "Question Master",
        "description": "Asked 10 questions",
        "icon": "❓",
        "points_required": 0,
    },
    "daily_learner": {
        "name": "Daily Learner",
        "description": "Learned for 3 consecutive days",
        "icon": "📚",
        "points_required": 0,
    },
    "science_explorer": {
        "name": "Science Explorer",
        "description": "Explored 3 different subjects",
        "icon": "🔬",
        "points_required": 0,
    },
    "fact_collector": {
        "name": "Fact Collector",
        "description": "Viewed 5 facts of the day",
        "icon": "💡",
        "points_required": 0,
    },
    "quiz_taker": {
        "name": "Quiz Taker",
        "description": "Completed your first quiz",
        "icon": "📝",
        "points_required": 0,
    },
    "quiz_ace": {
        "name": "Quiz Ace",
        "description": "Scored 100% on a quiz",
        "icon": "🎯",
        "points_required": 0,
    },
    "explain_it_back": {
        "name": "Teacher's Pet",
        "description": "Explained a concept back and scored ≥7/10",
        "icon": "🗣️",
        "points_required": 0,
    },
    "rising_star": {
        "name": "Rising Star",
        "description": "Earned 50 points",
        "icon": "⭐",
        "points_required": 50,
    },
    "science_star": {
        "name": "Science Star",
        "description": "Earned 100 points",
        "icon": "🌟",
        "points_required": 100,
    },
    "knowledge_champion": {
        "name": "Knowledge Champion",
        "description": "Earned 200 points",
        "icon": "🏆",
        "points_required": 200,
    },
    "socratic_scholar": {
        "name": "Socratic Scholar",
        "description": "Completed 5 Socratic conversations",
        "icon": "🦉",
        "points_required": 0,
    },
}

_EMPTY_STATE: dict[str, Any] = {
    "points": 0,
    "badges": [],              # list[str] — badge IDs
    "questions_asked": 0,
    "subjects_explored": [],   # list[str]  — was set, now list
    "facts_generated": 0,
    "streak_days": 0,
    "last_visit": None,
    "daily_visits": [],        # list[str ISO dates]
    "quizzes_completed": 0,
    "perfect_quizzes": 0,
    "explain_backs_passed": 0,
    "socratic_sessions": 0,
}


class GamificationManager:
    """Manages points, badges, streaks, and achievements."""

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def __init__(self) -> None:
        if "gamification_data" not in st.session_state:
            st.session_state.gamification_data = _EMPTY_STATE.copy()
            st.session_state.gamification_data["last_visit"] = datetime.now().isoformat()

    @property
    def _data(self) -> dict[str, Any]:
        return st.session_state.gamification_data

    # ── Points ────────────────────────────────────────────────────────────────

    def add_points(self, points: int) -> None:
        self._data["points"] += points
        self._check_achievements()

    def get_total_points(self) -> int:
        return self._data.get("points", 0)

    # ── Event recorders ───────────────────────────────────────────────────────

    def add_question(self, subject: str | None = None) -> None:
        self._data["questions_asked"] += 1
        if subject:
            self.add_subject_explored(subject)
        self.add_points(POINTS_PER_QUESTION)

    def add_subject_explored(self, subject: str) -> None:
        explored: list[str] = self._data.setdefault("subjects_explored", [])
        if subject not in explored:
            explored.append(subject)

    def add_fact_generated(self) -> None:
        self._data["facts_generated"] += 1
        self.add_points(POINTS_PER_FACT)

    def add_challenge_completed(self) -> None:
        self.add_points(POINTS_PER_CHALLENGE)

    def add_quiz_completed(self, correct: int, total: int) -> None:
        self._data["quizzes_completed"] += 1
        points = correct * POINTS_PER_QUIZ_CORRECT
        if correct == total:
            self._data["perfect_quizzes"] += 1
        self.add_points(points)

    def add_explain_back(self, score: int) -> None:
        """Record an Explain-It-Back attempt. score is 1-10."""
        if score >= 7:
            self._data["explain_backs_passed"] += 1
            self.add_points(POINTS_PER_EXPLAIN_BACK)
        else:
            self.add_points(POINTS_EXPLAIN_BACK_BASE)

    def add_socratic_session(self) -> None:
        self._data["socratic_sessions"] = self._data.get("socratic_sessions", 0) + 1
        self._check_achievements()

    # ── Streak ────────────────────────────────────────────────────────────────

    def update_streak(self) -> None:
        today = datetime.now().date()
        raw_visits: list[str] = self._data.get("daily_visits", [])

        # normalise to date objects
        visits = []
        for d in raw_visits:
            try:
                visits.append(
                    datetime.fromisoformat(d).date() if isinstance(d, str) else d
                )
            except Exception:
                pass

        if today not in visits:
            visits.append(today)
            self._data["daily_visits"] = [v.isoformat() for v in visits]
            self._data["last_visit"] = today.isoformat()

            visits_sorted = sorted(visits, reverse=True)
            streak = 1
            for i in range(1, len(visits_sorted)):
                if visits_sorted[i - 1] - visits_sorted[i] == timedelta(days=1):
                    streak += 1
                else:
                    break
            self._data["streak_days"] = streak

    # ── Achievements ──────────────────────────────────────────────────────────

    def _check_achievements(self) -> None:
        d = self._data
        earned: set[str] = set(d.get("badges", []))
        new: list[str] = []

        def _award(badge_id: str) -> None:
            if badge_id not in earned:
                earned.add(badge_id)
                new.append(badge_id)

        points = d.get("points", 0)
        for bid, binfo in BADGES.items():
            if binfo["points_required"] > 0 and points >= binfo["points_required"]:
                _award(bid)

        if d.get("questions_asked", 0) >= 1:
            _award("first_question")
        if d.get("questions_asked", 0) >= 10:
            _award("question_master")
        if d.get("streak_days", 0) >= 3:
            _award("daily_learner")
        if len(d.get("subjects_explored", [])) >= 3:
            _award("science_explorer")
        if d.get("facts_generated", 0) >= 5:
            _award("fact_collector")
        if d.get("quizzes_completed", 0) >= 1:
            _award("quiz_taker")
        if d.get("perfect_quizzes", 0) >= 1:
            _award("quiz_ace")
        if d.get("explain_backs_passed", 0) >= 1:
            _award("explain_it_back")
        if d.get("socratic_sessions", 0) >= 5:
            _award("socratic_scholar")

        d["badges"] = list(earned)

        for bid in new:
            b = BADGES[bid]
            st.toast(f"🎉 New Badge: {b['icon']} {b['name']}", icon="🏅")

    # ── Getters ───────────────────────────────────────────────────────────────

    def get_user_badges(self) -> list[dict[str, Any]]:
        earned = self._data.get("badges", [])
        return [
            {
                "id": bid,
                "name": BADGES[bid]["name"],
                "description": BADGES[bid]["description"],
                "icon": BADGES[bid]["icon"],
            }
            for bid in earned
            if bid in BADGES
        ]

    def get_available_badges(self) -> list[dict[str, Any]]:
        earned = set(self._data.get("badges", []))
        return [
            {
                "id": bid,
                "name": b["name"],
                "description": b["description"],
                "icon": b["icon"],
                "points_required": b["points_required"],
            }
            for bid, b in BADGES.items()
            if bid not in earned
        ]

    def get_stats(self) -> dict[str, Any]:
        d = self._data
        return {
            "points": d.get("points", 0),
            "badges_count": len(d.get("badges", [])),
            "questions_asked": d.get("questions_asked", 0),
            "subjects_explored": len(d.get("subjects_explored", [])),
            "facts_generated": d.get("facts_generated", 0),
            "streak_days": d.get("streak_days", 0),
            "quizzes_completed": d.get("quizzes_completed", 0),
            "perfect_quizzes": d.get("perfect_quizzes", 0),
            "explain_backs_passed": d.get("explain_backs_passed", 0),
        }

    def reset(self) -> None:
        st.session_state.gamification_data = _EMPTY_STATE.copy()
        st.session_state.gamification_data["last_visit"] = datetime.now().isoformat()
