"""
Main Interface Component for ScienceGPT
Handles the main chat interface and question answering
"""

import streamlit as st
from typing import Dict, List
import time
from backend_code.llm_handler import LLMHandler
from backend_code.curriculum_data import CurriculumData
from backend_code.gamification import GamificationSystem
from backend_code.student_progress import StudentProgress

class MainInterface:
    """Manages the main chat interface"""

    def __init__(self, llm_handler: LLMHandler, curriculum_data: CurriculumData, gamification: GamificationSystem):
        self.llm_handler = llm_handler
        self.curriculum_data = curriculum_data
        self.gamification = gamification
        self.student_progress = StudentProgress()

    def display(self, sidebar_settings: Dict):
        """Display the main interface"""
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # Generate and display suggestions
        self._display_suggestions(sidebar_settings)

        # Chat interface
        self._display_chat_interface(sidebar_settings)

        # Display chat history
        self._display_chat_history()

    def _display_suggestions(self, settings: Dict):
        """Display dynamic question suggestions"""
        st.markdown("### 💡 Question Suggestions")
        st.markdown("Click on any suggestion below to ask ScienceGPT:")

        # Generate suggestions based on current settings
        context = {
            'grade': settings['grade'],
            'language': settings['language'],
            'subject': settings['subject'],
            'topic': settings['topic']
        }

        # Use cached suggestions or generate new ones
        cache_key = f"{settings['grade']}_{settings['subject']}_{settings['topic']}"

        if settings['apply_pressed'] or 'suggestions_cache' not in st.session_state or st.session_state.get('suggestions_key') != cache_key:
            with st.spinner("Generating personalized suggestions..."):
                suggestions = self.llm_handler.generate_suggestions(context)
            st.session_state.suggestions_cache = suggestions
            st.session_state.suggestions_key = cache_key
        else:
            suggestions = st.session_state.get('suggestions_cache', [])

        # Display suggestions as clickable buttons
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions[:4]):
            col = cols[i % 2]
            with col:
                if st.button(suggestion, key=f"suggestion_{i}", help="Click to ask this question"):
                    self._handle_question(suggestion, settings)

    def _display_chat_interface(self, settings: Dict):
        """Display the main chat input interface"""
        st.markdown("### 🤖 Ask ScienceGPT")

        # Text input for questions
        user_question = st.text_area(
            "Type your science question here:",
            height=100,
            placeholder=f"Ask anything about {settings['subject']} for Grade {settings['grade']}...",
            help="Ask any science question and get detailed explanations!"
        )

        # Ask button
        col1, col2 = st.columns([1, 4])
        with col1:
            ask_button = st.button("🔍 Ask", type="primary", disabled=not user_question.strip())

        if ask_button and user_question.strip():
            self._handle_question(user_question.strip(), settings)

    def _handle_question(self, question: str, settings: Dict):
        """Handle a user question"""
        # Add user question to chat history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': question,
            'timestamp': time.time(),
            'settings': settings.copy()
        })

        # Generate response
        with st.spinner("🤔 ScienceGPT is thinking..."):
            context = {
                'grade': settings['grade'],
                'language': settings['language'],
                'subject': settings['subject'],
                'topic': settings['topic']
            }

            response = self.llm_handler.generate_response(question, context)

        # Add AI response to chat history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': time.time()
        })

        # Update gamification and progress tracking
        self._update_progress(question, settings, response)

        # Check for new badges
        new_badges = self.gamification.check_and_award_badges()
        if new_badges:
            self._display_badge_notification(new_badges)

        # Rerun to update the display
        st.rerun()

    def _display_chat_history(self):
        """Display the chat history"""
        if not st.session_state.chat_history:
            st.info("👋 Welcome to ScienceGPT! Ask your first science question to get started.")
            return

        st.markdown("### 💬 Conversation History")

        # Display messages in reverse order (newest first)
        for i, message in enumerate(reversed(st.session_state.chat_history)):
            with st.container():
                if message['role'] == 'user':
                    st.markdown(f"**🧑‍🎓 You:** {message['content']}")
                else:
                    st.markdown(f"**🤖 ScienceGPT:** {message['content']}")

                # Add timestamp
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message['timestamp']))
                st.caption(f"⏰ {timestamp}")

                st.markdown("---")

        # Clear chat button
        if st.button("🗑️ Clear Chat History", help="Clear all conversation history"):
            st.session_state.chat_history = []
            st.rerun()

    def _update_progress(self, question: str, settings: Dict, response: str):
        """Update user progress and gamification"""
        # Award points for asking question
        points_earned = self.gamification.award_points("question_asked")

        # Update question counter
        st.session_state.questions_answered = st.session_state.get('questions_answered', 0) + 1

        # Log question in progress tracking
        self.student_progress.log_question(
            question=question,
            grade=settings['grade'],
            subject=settings['subject'],
            topic=settings['topic'] or 'General',
            response_quality=0.8  # Assume good quality response
        )

        # Update streak
        self.gamification.update_streak()

        # Show points notification
        st.success(f"🌟 You earned {points_earned} points! Total: {st.session_state.user_points}")

    def _display_badge_notification(self, new_badges: List[Dict]):
        """Display notification for new badges earned"""
        for badge in new_badges:
            st.balloons()
            st.success(f"🎉 Congratulations! You earned the **{badge['name']}** badge {badge['icon']}\n{badge['description']}")
