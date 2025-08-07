"""
LLM Handler for ScienceGPT
Manages interactions with Groq API
"""

import streamlit as st
from groq import Groq
import json
import logging
from typing import List, Dict, Optional

class LLMHandler:
    """Handles all LLM-related operations using Groq API"""

    def __init__(self):
        self.client = None
        self.initialize_client()

    def initialize_client(self):
        """Initialize Groq client with API key from Streamlit secrets"""
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
            if not api_key:
                st.error("GROQ_API_KEY not found in secrets. Please add it to your Streamlit secrets.")
                return

            self.client = Groq(api_key=api_key)

        except Exception as e:
            st.error(f"Error initializing Groq client: {e}")

    def generate_response(self, prompt: str, context: Dict = None) -> str:
        """Generate response from LLM based on prompt and context"""
        try:
            if not self.client:
                return "Sorry, I'm having trouble connecting to the AI service. Please try again later."

            # Build system prompt based on context
            system_prompt = self._build_system_prompt(context or {})

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1024,
            )

            return chat_completion.choices[0].message.content

        except Exception as e:
            logging.error(f"Error generating LLM response: {e}")
            return f"I'm sorry, I encountered an error: {e}. Please try again."

    def generate_suggestions(self, context: Dict) -> List[str]:
        """Generate dynamic suggestions based on context"""
        try:
            grade = context.get('grade', 3)
            language = context.get('language', 'English')
            subject = context.get('subject', 'General Science')
            topic = context.get('topic', 'Basic Science')

            prompt = f"""Generate 4 engaging science question suggestions for:
- Grade: {grade}
- Language: {language}
- Subject: {subject}
- Topic: {topic}

Make the suggestions:
1. Age-appropriate for grade {grade} students
2. Engaging and curiosity-driven
3. Related to the Indian NCERT curriculum
4. Interactive and educational

Return as a JSON list of strings. Example:
["What makes plants green?", "Why do magnets stick to some metals?"]"""

            response = self.generate_response(prompt)

            try:
                # Try to parse JSON response
                suggestions = json.loads(response)
                if isinstance(suggestions, list):
                    return suggestions[:4]  # Limit to 4 suggestions
            except json.JSONDecodeError:
                pass

            # Fallback suggestions if JSON parsing fails
            return self._get_fallback_suggestions(grade, subject)

        except Exception as e:
            logging.error(f"Error generating suggestions: {e}")
            return self._get_fallback_suggestions(context.get('grade', 3), 
                                               context.get('subject', 'General Science'))

    def generate_daily_challenge(self, grade: int, subject: str, language: str) -> Dict:
        """Generate a daily challenge question"""
        try:
            prompt = f"""Create a fun daily science challenge for grade {grade} students:
- Subject: {subject}
- Language: {language}
- Make it engaging and educational
- Include the question and a brief explanation
- Make it appropriate for the Indian NCERT curriculum

Return as JSON with keys: 'question', 'type' (fact/quiz), 'explanation', 'fun_factor'"""

            response = self.generate_response(prompt)

            try:
                challenge = json.loads(response)
                return challenge
            except json.JSONDecodeError:
                return self._get_fallback_challenge(grade, subject)

        except Exception as e:
            logging.error(f"Error generating daily challenge: {e}")
            return self._get_fallback_challenge(grade, subject)

    def _build_system_prompt(self, context: Dict) -> str:
        """Build system prompt based on context"""
        grade = context.get('grade', 3)
        language = context.get('language', 'English')
        subject = context.get('subject', 'General Science')

        return f"""You are ScienceGPT, an AI science tutor for Indian students in grade {grade}.

Key guidelines:
- Respond in {language} language
- Use age-appropriate language for grade {grade} students (ages {5+grade}-{6+grade})
- Follow Indian NCERT curriculum standards
- Make learning fun and engaging
- Use simple examples from daily life
- Be encouraging and supportive
- Focus on {subject} concepts
- Include interactive elements when possible
- Promote scientific thinking and curiosity

Always be helpful, educational, and inspiring!"""

    def _get_fallback_suggestions(self, grade: int, subject: str) -> List[str]:
        """Provide fallback suggestions when LLM fails"""
        suggestions_by_grade = {
            1: ["What colors do you see in a rainbow?", "Why do birds have feathers?", 
                "What makes day and night?", "How do plants drink water?"],
            2: ["Why do leaves change colors?", "What makes thunder sound?", 
                "How do animals stay warm?", "Where does rain come from?"],
            3: ["How do magnets work?", "Why do some things float?", 
                "What makes plants green?", "How do we hear sounds?"],
            4: ["Why do we see lightning before thunder?", "How do plants make food?", 
                "What makes things hot or cold?", "How do animals breathe underwater?"],
            5: ["How does electricity work?", "Why do objects fall down?", 
                "What makes different materials?", "How do our eyes see colors?"],
            6: ["How do chemical reactions happen?", "What makes living things different?", 
                "How does light travel?", "Why do plants need sunlight?"],
            7: ["How do acids and bases work?", "What controls our body functions?", 
                "How do forces affect motion?", "How do organisms reproduce?"],
            8: ["How do cells divide?", "What causes different sounds?", 
                "How does friction affect movement?", "What makes materials conduct electricity?"]
        }

        return suggestions_by_grade.get(grade, suggestions_by_grade[3])

    def _get_fallback_challenge(self, grade: int, subject: str) -> Dict:
        """Provide fallback daily challenge"""
        challenges = {
            "question": f"Fun Science Fact: Did you know that a cloud weighs about a million tons? Despite this, clouds float because they are less dense than the air around them!",
            "type": "fact",
            "explanation": "This shows how density affects whether things sink or float - even in the sky!",
            "fun_factor": "Amazing but true! ☁️"
        }
        return challenges
