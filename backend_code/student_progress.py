"""
Student Progress Tracker for ScienceGPT v2.
Now actually called from the frontend — sessions, questions, and quiz results recorded.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Any
import json

from utils.helpers import get_logger, make_cache_key, set_to_list, now_iso

log = get_logger(__name__)

_EMPTY: dict[str, Any] = {
    "sessions": [],
    "questions_by_subject": {},
    "questions_by_grade": {},
    "topic_coverage": {},          # {subject: [topics]}  — lists, not sets
    "quiz_results": {},            # {subject/topic key: [scores]}
    "performance_metrics": {
        "total_questions": 0,
        "total_time_spent": 0.0,
        "favorite_subjects": [],
    },
}


class StudentProgress:
    """Tracks learning sessions, questions, topics, and quiz results."""

    def __init__(self) -> None:
        if "progress_data" not in st.session_state:
            st.session_state.progress_data = {
                k: (v.copy() if isinstance(v, dict) else v)
                for k, v in _EMPTY.items()
            }

    @property
    def _data(self) -> dict[str, Any]:
        return st.session_state.progress_data

    # ── Session lifecycle ─────────────────────────────────────────────────────

    def start_session(self) -> None:
        st.session_state.current_session = {
            "start_time": now_iso(),
            "end_time": None,
            "questions_asked": 0,
            "subjects_covered": [],
            "grade": st.session_state.get("grade", 8),
            "language": st.session_state.get("language", "English"),
        }

    def end_session(self) -> None:
        if "current_session" not in st.session_state:
            return
        session = st.session_state.current_session
        session["end_time"] = now_iso()
        self._data["sessions"].append(session)
        self._update_metrics(session)
        del st.session_state.current_session

    # ── Question recording ────────────────────────────────────────────────────

    def record_question(self, question: str, subject: str, grade: int, topic: str = "") -> None:
        # Current session
        if "current_session" in st.session_state:
            cs = st.session_state.current_session
            cs["questions_asked"] += 1
            if subject not in cs["subjects_covered"]:
                cs["subjects_covered"].append(subject)

        # Subject totals
        self._data["questions_by_subject"][subject] = (
            self._data["questions_by_subject"].get(subject, 0) + 1
        )

        # Grade totals
        gk = f"Grade {grade}"
        self._data["questions_by_grade"][gk] = (
            self._data["questions_by_grade"].get(gk, 0) + 1
        )

        # Topic coverage
        if topic and topic != "All Topics":
            tc = self._data.setdefault("topic_coverage", {})
            if subject not in tc:
                tc[subject] = []
            if topic not in tc[subject]:
                tc[subject].append(topic)

        self._data["performance_metrics"]["total_questions"] += 1

    # ── Quiz recording ────────────────────────────────────────────────────────

    def record_quiz_result(self, subject: str, topic: str, score: float, total: float) -> None:
        """Record a quiz result as a percentage."""
        key = make_cache_key(subject, topic)
        results: list[float] = self._data.setdefault("quiz_results", {}).get(key, [])
        pct = round((score / total) * 100) if total > 0 else 0
        results.append(pct)
        self._data["quiz_results"][key] = results

    def get_topic_mastery(self, subject: str, topic: str) -> float | None:
        """Return average quiz score (0-100) for a topic, or None if never attempted."""
        key = make_cache_key(subject, topic)
        results = self._data.get("quiz_results", {}).get(key)
        if not results:
            return None
        return round(sum(results) / len(results), 1)

    def get_mastery_grid(self, grade: int, subject: str) -> list[dict[str, Any]]:
        """
        Return mastery data for every topic in a grade/subject,
        ready to render as a heatmap.
        """
        from backend_code.curriculum_data import get_curriculum
        topics = get_curriculum().get_topics_for_grade_subject(grade, subject)
        grid = []
        for t in topics:
            mastery = self.get_topic_mastery(subject, t)
            coverage = (
                t in self._data.get("topic_coverage", {}).get(subject, [])
            )
            grid.append({
                "topic": t,
                "mastery": mastery,       # None | 0-100
                "attempted": coverage,
            })
        return grid

    # ── Summaries ─────────────────────────────────────────────────────────────

    def get_progress_summary(self) -> dict[str, Any]:
        metrics = self._data["performance_metrics"]
        sessions = self._data.get("sessions", [])
        qbs = self._data.get("questions_by_subject", {})

        daily_sessions: dict = {}
        for s in sessions:
            d = datetime.fromisoformat(s["start_time"]).date()
            daily_sessions[d] = daily_sessions.get(d, 0) + 1

        return {
            "total_questions": metrics.get("total_questions", 0),
            "total_time_spent": round(metrics.get("total_time_spent", 0.0), 1),
            "subjects_explored": len(qbs),
            "sessions_count": len(sessions),
            "favorite_subjects": metrics.get("favorite_subjects", []),
            "consistency_score": len(daily_sessions) * 10,
            "questions_by_subject": qbs,
            "topic_coverage": self._data.get("topic_coverage", {}),
        }

    def get_weekly_progress(self) -> list[dict[str, Any]]:
        sessions = self._data.get("sessions", [])
        today = datetime.now().date()
        week = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

        result = []
        for day in week:
            day_sessions = [
                s for s in sessions
                if datetime.fromisoformat(s["start_time"]).date() == day
            ]
            subjects: set[str] = set()
            for s in day_sessions:
                subjects.update(s.get("subjects_covered", []))
            result.append({
                "date": day.strftime("%Y-%m-%d"),
                "day_name": day.strftime("%a"),
                "questions": sum(s.get("questions_asked", 0) for s in day_sessions),
                "subjects": len(subjects),
                "sessions": len(day_sessions),
            })
        return result

    def export_progress_data(self) -> str:
        return json.dumps(set_to_list(self._data), indent=2, default=str)

    def clear(self) -> None:
        st.session_state.progress_data = {
            k: (v.copy() if isinstance(v, dict) else v)
            for k, v in _EMPTY.items()
        }

    # ── Private ───────────────────────────────────────────────────────────────

    def _update_metrics(self, session: dict) -> None:
        if session.get("end_time") and session.get("start_time"):
            start = datetime.fromisoformat(session["start_time"])
            end = datetime.fromisoformat(session["end_time"])
            duration = (end - start).total_seconds() / 60
            self._data["performance_metrics"]["total_time_spent"] += duration

        qbs = self._data["questions_by_subject"]
        if qbs:
            top3 = sorted(qbs.items(), key=lambda x: x[1], reverse=True)[:3]
            self._data["performance_metrics"]["favorite_subjects"] = [
                {"subject": s, "count": c} for s, c in top3
            ]
