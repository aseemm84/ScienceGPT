"""
Student Progress Tracking for ScienceGPT
Manages learning analytics and progress tracking
"""

import streamlit as st
from typing import Dict, List
from datetime import datetime, timedelta
import json

class StudentProgress:
    """Handles student progress tracking and analytics"""

    def __init__(self):
        self.initialize_progress_data()

    def initialize_progress_data(self):
        """Initialize progress tracking data in session state"""
        if 'progress_data' not in st.session_state:
            st.session_state.progress_data = {
                'sessions': [],
                'topics_studied': {},
                'questions_history': [],
                'performance_metrics': {
                    'total_questions': 0,
                    'correct_answers': 0,
                    'topics_explored': 0,
                    'time_spent': 0
                }
            }

    def log_question(self, question: str, grade: int, subject: str, topic: str, response_quality: float = 0.8):
        """Log a question asked by the student"""
        question_data = {
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'grade': grade,
            'subject': subject,
            'topic': topic,
            'response_quality': response_quality
        }

        st.session_state.progress_data['questions_history'].append(question_data)
        st.session_state.progress_data['performance_metrics']['total_questions'] += 1

        # Update topics studied
        topic_key = f"{subject}_{topic}"
        if topic_key not in st.session_state.progress_data['topics_studied']:
            st.session_state.progress_data['topics_studied'][topic_key] = {
                'subject': subject,
                'topic': topic,
                'questions_count': 0,
                'first_studied': datetime.now().isoformat()
            }
        st.session_state.progress_data['topics_studied'][topic_key]['questions_count'] += 1

    def log_session_start(self):
        """Log the start of a learning session"""
        session_data = {
            'start_time': datetime.now().isoformat(),
            'questions_in_session': 0,
            'topics_in_session': set()
        }

        if 'current_session' not in st.session_state:
            st.session_state.current_session = session_data

    def log_session_end(self):
        """Log the end of a learning session"""
        if 'current_session' in st.session_state:
            session = st.session_state.current_session
            session['end_time'] = datetime.now().isoformat()

            start_time = datetime.fromisoformat(session['start_time'])
            end_time = datetime.fromisoformat(session['end_time'])
            session['duration'] = (end_time - start_time).total_seconds()

            # Convert set to list for storage
            session['topics_in_session'] = list(session['topics_in_session'])

            st.session_state.progress_data['sessions'].append(session)
            st.session_state.progress_data['performance_metrics']['time_spent'] += session['duration']

            del st.session_state.current_session

    def get_learning_stats(self) -> Dict:
        """Get comprehensive learning statistics"""
        progress = st.session_state.progress_data

        stats = {
            'total_questions': progress['performance_metrics']['total_questions'],
            'topics_explored': len(progress['topics_studied']),
            'total_sessions': len(progress['sessions']),
            'total_time_minutes': progress['performance_metrics']['time_spent'] / 60,
            'average_session_time': 0,
            'most_studied_subject': None,
            'most_studied_topic': None,
            'recent_activity': []
        }

        if stats['total_sessions'] > 0:
            stats['average_session_time'] = stats['total_time_minutes'] / stats['total_sessions']

        # Find most studied subject and topic
        subject_counts = {}
        topic_counts = {}

        for topic_key, topic_data in progress['topics_studied'].items():
            subject = topic_data['subject']
            topic = topic_data['topic']
            count = topic_data['questions_count']

            subject_counts[subject] = subject_counts.get(subject, 0) + count
            topic_counts[topic] = topic_counts.get(topic, 0) + count

        if subject_counts:
            stats['most_studied_subject'] = max(subject_counts, key=subject_counts.get)
        if topic_counts:
            stats['most_studied_topic'] = max(topic_counts, key=topic_counts.get)

        # Get recent activity (last 5 questions)
        recent_questions = progress['questions_history'][-5:]
        for q in recent_questions:
            stats['recent_activity'].append({
                'question': q['question'][:50] + "..." if len(q['question']) > 50 else q['question'],
                'subject': q['subject'],
                'topic': q['topic'],
                'time': q['timestamp']
            })

        return stats

    def get_progress_by_subject(self) -> Dict:
        """Get progress breakdown by subject"""
        progress = st.session_state.progress_data
        subjects = {}

        for topic_key, topic_data in progress['topics_studied'].items():
            subject = topic_data['subject']
            if subject not in subjects:
                subjects[subject] = {
                    'topics_count': 0,
                    'questions_count': 0,
                    'topics': []
                }

            subjects[subject]['topics_count'] += 1
            subjects[subject]['questions_count'] += topic_data['questions_count']
            subjects[subject]['topics'].append(topic_data['topic'])

        return subjects

    def get_weekly_activity(self) -> Dict:
        """Get activity data for the past week"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        daily_activity = {i: 0 for i in range(7)}

        for question in st.session_state.progress_data['questions_history']:
            q_date = datetime.fromisoformat(question['timestamp'])
            if start_date <= q_date <= end_date:
                days_ago = (end_date.date() - q_date.date()).days
                if days_ago < 7:
                    daily_activity[days_ago] += 1

        return daily_activity

    def export_progress_data(self) -> str:
        """Export progress data as JSON string"""
        return json.dumps(st.session_state.progress_data, indent=2, default=str)

    def clear_progress_data(self):
        """Clear all progress data (with confirmation)"""
        st.session_state.progress_data = {
            'sessions': [],
            'topics_studied': {},
            'questions_history': [],
            'performance_metrics': {
                'total_questions': 0,
                'correct_answers': 0,
                'topics_explored': 0,
                'time_spent': 0
            }
        }
