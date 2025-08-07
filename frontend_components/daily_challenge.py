"""
Daily Challenge Component for ScienceGPT
Displays daily science facts and quiz challenges
"""

import streamlit as st
from typing import Dict
from datetime import datetime
import hashlib
from backend_code.llm_handler import LLMHandler
from backend_code.curriculum_data import CurriculumData
from backend_code.gamification import GamificationSystem

class DailyChallenge:
    """Manages daily challenges and fun facts"""

    def __init__(self, llm_handler: LLMHandler, curriculum_data: CurriculumData):
        self.llm_handler = llm_handler
        self.curriculum_data = curriculum_data
        self.gamification = GamificationSystem()

    def display(self):
        """Display the daily challenge section"""
        st.markdown("### 🌟 Daily Science Challenge")

        # Get today's challenge
        challenge = self._get_daily_challenge()

        # Display challenge in a styled container
        st.markdown(f"""
        <div class="daily-challenge">
            <h4>🎯 {challenge['type'].title()} of the Day</h4>
            <p style="font-size: 1.1rem; margin: 1rem 0;"><strong>{challenge['question']}</strong></p>
            <p style="color: #666;">{challenge['explanation']}</p>
            <p style="font-style: italic; color: #4ecdc4;">{challenge.get('fun_factor', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Challenge interaction
        self._display_challenge_interaction(challenge)

    def _get_daily_challenge(self) -> Dict:
        """Get or generate today's daily challenge"""
        today = datetime.now().date().isoformat()

        # Check if we already have today's challenge
        if ('daily_challenge' in st.session_state and 
            st.session_state.get('challenge_date') == today):
            return st.session_state.daily_challenge

        # Generate new challenge for today
        # Use a simple hash of the date to ensure consistency
        date_hash = int(hashlib.md5(today.encode()).hexdigest()[:8], 16)

        # Select grade and subject based on user preference or random
        default_grade = st.session_state.get('selected_grade', 5)
        default_subject = st.session_state.get('selected_subject', 'General Science')
        default_language = st.session_state.get('selected_language', 'English')

        # Generate challenge using LLM
        challenge = self.llm_handler.generate_daily_challenge(
            grade=default_grade,
            subject=default_subject,
            language=default_language
        )

        # Store in session state
        st.session_state.daily_challenge = challenge
        st.session_state.challenge_date = today

        return challenge

    def _display_challenge_interaction(self, challenge: Dict):
        """Display interactive elements for the challenge"""
        challenge_type = challenge.get('type', 'fact')

        if challenge_type.lower() == 'quiz':
            self._display_quiz_interaction(challenge)
        else:
            self._display_fact_interaction(challenge)

    def _display_quiz_interaction(self, challenge: Dict):
        """Display quiz-style interaction"""
        col1, col2 = st.columns([2, 1])

        with col1:
            # Simple answer input for quiz
            user_answer = st.text_input(
                "Your answer:",
                placeholder="Type your answer here...",
                key="daily_quiz_answer"
            )

        with col2:
            if st.button("Submit Answer", type="primary", key="submit_daily_quiz"):
                if user_answer.strip():
                    self._handle_quiz_answer(user_answer, challenge)

    def _display_fact_interaction(self, challenge: Dict):
        """Display fact-style interaction"""
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🤔 Tell me more!", key="learn_more"):
                self._show_more_info(challenge)

        with col2:
            if st.button("✨ I learned this!", key="mark_learned"):
                self._mark_as_learned(challenge)

        with col3:
            if st.button("📚 Related Questions", key="related_q"):
                self._show_related_questions(challenge)

    def _handle_quiz_answer(self, answer: str, challenge: Dict):
        """Handle quiz answer submission"""
        # Award points for attempting
        points = self.gamification.award_points("daily_challenge")

        st.success(f"Great effort! You earned {points} points for participating in today's challenge! 🎉")

        # Provide feedback (simplified - in real implementation, you'd check the answer)
        st.info("🎓 Keep exploring science! Every question helps you learn something new.")

        # Mark challenge as completed
        st.session_state.daily_challenge_completed = True

    def _mark_as_learned(self, challenge: Dict):
        """Mark the daily fact as learned"""
        points = self.gamification.award_points("daily_challenge")

        st.success(f"Awesome! You earned {points} points for engaging with today's science fact! 🌟")
        st.balloons()

        # Update learning progress
        if 'topics_explored' not in st.session_state:
            st.session_state.topics_explored = 0
        st.session_state.topics_explored += 1

        st.session_state.daily_challenge_completed = True

    def _show_more_info(self, challenge: Dict):
        """Show more information about the daily fact"""
        with st.expander("🔍 Learn More", expanded=True):
            # Generate additional information
            more_info_prompt = f"Provide more detailed, age-appropriate information about: {challenge['question']}"

            with st.spinner("Getting more information..."):
                additional_info = self.llm_handler.generate_response(more_info_prompt)

            st.write(additional_info)

            # Award points for curiosity
            points = self.gamification.award_points("topic_exploration")
            st.success(f"Curious mind! +{points} points for wanting to learn more! 🧠")

    def _show_related_questions(self, challenge: Dict):
        """Show related questions for further exploration"""
        with st.expander("🤔 Related Questions", expanded=True):
            st.write("Here are some related questions you might find interesting:")

            # Generate related questions
            related_prompt = f"Generate 3 related science questions suitable for students based on: {challenge['question']}"

            with st.spinner("Generating related questions..."):
                related_content = self.llm_handler.generate_response(related_prompt)

            st.write(related_content)

            st.info("💡 Click any of these questions in the main chat to explore further!")

    def get_challenge_stats(self) -> Dict:
        """Get statistics about daily challenge participation"""
        return {
            'completed_today': st.session_state.get('daily_challenge_completed', False),
            'total_challenges': st.session_state.get('total_daily_challenges', 0),
            'streak': st.session_state.get('daily_challenge_streak', 0)
        }
