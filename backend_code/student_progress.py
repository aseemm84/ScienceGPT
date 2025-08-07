"""
Student Progress Tracker for ScienceGPT
Tracks learning analytics and progress metrics
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

class StudentProgress:
    """Tracks and analyzes student learning progress"""

    def __init__(self):
        """Initialize student progress tracker"""
        if 'progress_data' not in st.session_state:
            st.session_state.progress_data = {
                "sessions": [],
                "questions_by_subject": {},
                "questions_by_grade": {},
                "learning_time": {},
                "topic_coverage": {},
                "performance_metrics": {
                    "total_questions": 0,
                    "total_time_spent": 0,
                    "favorite_subjects": [],
                    "learning_patterns": {}
                }
            }

    def start_session(self):
        """Start a new learning session"""
        session_data = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "questions_asked": 0,
            "subjects_covered": set(),
            "grade": st.session_state.get('grade', 3),
            "language": st.session_state.get('language', 'English')
        }

        st.session_state.current_session = session_data

    def end_session(self):
        """End the current learning session"""
        if 'current_session' in st.session_state:
            session = st.session_state.current_session
            session['end_time'] = datetime.now().isoformat()
            session['subjects_covered'] = list(session['subjects_covered'])

            # Add to sessions history
            st.session_state.progress_data['sessions'].append(session)

            # Update metrics
            self._update_metrics(session)

            del st.session_state.current_session

    def record_question(self, question: str, subject: str, grade: int, topic: str = None):
        """Record a question asked by the student"""
        # Update current session
        if 'current_session' in st.session_state:
            st.session_state.current_session['questions_asked'] += 1
            st.session_state.current_session['subjects_covered'].add(subject)

        # Update subject tracking
        if subject not in st.session_state.progress_data['questions_by_subject']:
            st.session_state.progress_data['questions_by_subject'][subject] = 0
        st.session_state.progress_data['questions_by_subject'][subject] += 1

        # Update grade tracking
        grade_key = f"Grade {grade}"
        if grade_key not in st.session_state.progress_data['questions_by_grade']:
            st.session_state.progress_data['questions_by_grade'][grade_key] = 0
        st.session_state.progress_data['questions_by_grade'][grade_key] += 1

        # Update topic coverage
        if topic and topic != "All Topics":
            if subject not in st.session_state.progress_data['topic_coverage']:
                st.session_state.progress_data['topic_coverage'][subject] = set()
            st.session_state.progress_data['topic_coverage'][subject].add(topic)

        # Update total questions
        st.session_state.progress_data['performance_metrics']['total_questions'] += 1

    def _update_metrics(self, session: Dict):
        """Update performance metrics based on completed session"""
        # Calculate session duration
        if session['end_time'] and session['start_time']:
            start = datetime.fromisoformat(session['start_time'])
            end = datetime.fromisoformat(session['end_time'])
            duration = (end - start).total_seconds() / 60  # minutes

            st.session_state.progress_data['performance_metrics']['total_time_spent'] += duration

        # Update favorite subjects
        questions_by_subject = st.session_state.progress_data['questions_by_subject']
        if questions_by_subject:
            favorite_subjects = sorted(
                questions_by_subject.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            st.session_state.progress_data['performance_metrics']['favorite_subjects'] = [
                {"subject": subj, "count": count} for subj, count in favorite_subjects
            ]

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get comprehensive progress summary"""
        data = st.session_state.progress_data
        metrics = data['performance_metrics']

        # Calculate learning consistency
        sessions = data.get('sessions', [])
        if sessions:
            # Group sessions by date
            daily_sessions = {}
            for session in sessions:
                date = datetime.fromisoformat(session['start_time']).date()
                if date not in daily_sessions:
                    daily_sessions[date] = 0
                daily_sessions[date] += 1

            consistency_score = len(daily_sessions) * 10  # 10 points per day
        else:
            consistency_score = 0

        # Calculate subject diversity
        subjects_explored = len(data.get('questions_by_subject', {}))
        diversity_score = subjects_explored * 15  # 15 points per subject

        return {
            "total_questions": metrics.get('total_questions', 0),
            "total_time_spent": round(metrics.get('total_time_spent', 0), 1),
            "subjects_explored": subjects_explored,
            "sessions_count": len(sessions),
            "favorite_subjects": metrics.get('favorite_subjects', []),
            "consistency_score": consistency_score,
            "diversity_score": diversity_score,
            "overall_score": consistency_score + diversity_score + metrics.get('total_questions', 0),
            "questions_by_subject": data.get('questions_by_subject', {}),
            "topic_coverage": {
                subj: list(topics) for subj, topics in data.get('topic_coverage', {}).items()
            }
        }

    def get_weekly_progress(self) -> List[Dict[str, Any]]:
        """Get progress for the last 7 days"""
        sessions = st.session_state.progress_data.get('sessions', [])

        # Get last 7 days
        today = datetime.now().date()
        week_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

        daily_progress = []
        for day in week_days:
            day_sessions = [
                s for s in sessions 
                if datetime.fromisoformat(s['start_time']).date() == day
            ]

            total_questions = sum(s.get('questions_asked', 0) for s in day_sessions)
            subjects_covered = set()
            for session in day_sessions:
                subjects_covered.update(session.get('subjects_covered', []))

            daily_progress.append({
                "date": day.strftime("%Y-%m-%d"),
                "day_name": day.strftime("%a"),
                "questions": total_questions,
                "subjects": len(subjects_covered),
                "sessions": len(day_sessions)
            })

        return daily_progress

    def export_progress_data(self) -> str:
        """Export progress data as JSON string"""
        # Convert sets to lists for JSON serialization
        export_data = st.session_state.progress_data.copy()

        # Convert topic_coverage sets to lists
        if 'topic_coverage' in export_data:
            export_data['topic_coverage'] = {
                subj: list(topics) for subj, topics in export_data['topic_coverage'].items()
            }

        return json.dumps(export_data, indent=2, default=str)

    def clear_progress_data(self):
        """Clear all progress data"""
        st.session_state.progress_data = {
            "sessions": [],
            "questions_by_subject": {},
            "questions_by_grade": {},
            "learning_time": {},
            "topic_coverage": {},
            "performance_metrics": {
                "total_questions": 0,
                "total_time_spent": 0,
                "favorite_subjects": [],
                "learning_patterns": {}
            }
        }
