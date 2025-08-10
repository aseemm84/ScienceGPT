"""
Enhanced LLM Handler for ScienceGPT
Handles Groq API integration, YouTube video search, and dynamic content generation.
"""

import streamlit as st
import os
from groq import Groq
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class LLMHandler:
    """Enhanced LLM Handler with YouTube integration, improved caching, and dynamic content"""

    def __init__(self):
        """Initialize the LLM Handler"""
        self.groq_api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
        self.youtube_api_key = st.secrets.get("YOUTUBE_API_KEY", os.getenv("YOUTUBE_API_KEY"))

        if not self.groq_api_key:
            st.error("GROQ_API_KEY not found in secrets or environment variables!")
            st.stop()
        
        if not self.youtube_api_key:
            st.warning("YOUTUBE_API_KEY not found. Video search will be disabled.")
            self.youtube_service = None
        else:
            try:
                self.youtube_service = build('youtube', 'v3', developerKey=self.youtube_api_key)
            except Exception as e:
                st.error(f"Failed to initialize YouTube service: {e}")
                self.youtube_service = None


        self.client = Groq(api_key=self.groq_api_key)
        self.model = "llama-3.3-70b-versatile"

        # Initialize cache in session state
        if 'llm_cache' not in st.session_state:
            st.session_state.llm_cache = {}
        if 'fact_cache' not in st.session_state:
            st.session_state.fact_cache = {}

    def _create_settings_hash(self, grade: int, subject: str, language: str, topic: str) -> str:
        """Create a hash for the current settings combination"""
        settings_string = f"{grade}-{subject}-{language}-{topic}"
        return hashlib.md5(settings_string.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str, cache_duration_hours: int = 24) -> bool:
        """Check if cached content is still valid"""
        if cache_key not in st.session_state.fact_cache:
            return False

        cache_entry = st.session_state.fact_cache[cache_key]
        cache_time = cache_entry.get('timestamp', datetime.min)

        if isinstance(cache_time, str):
            cache_time = datetime.fromisoformat(cache_time)

        return datetime.now() - cache_time < timedelta(hours=cache_duration_hours)

    def search_youtube_video(self, query: str) -> Optional[str]:
        """Search for a relevant YouTube video."""
        if not self.youtube_service:
            return None
        
        try:
            search_response = self.youtube_service.search().list(
                q=query,
                part='snippet',
                maxResults=1,
                type='video',
                videoCategoryId='27',  # Category for Education
                relevanceLanguage='en' # Prioritize English content
            ).execute()

            results = search_response.get('items', [])
            if not results:
                return None

            video_id = results[0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"

        except HttpError as e:
            st.error(f"An HTTP error {e.resp.status} occurred during YouTube search: {e.content}")
            return None
        except Exception as e:
            st.error(f"An error occurred during YouTube search: {e}")
            return None

    def generate_suggestions(self, grade: int, subject: str, language: str, topic: str) -> List[str]:
        """Generate dynamic question suggestions based on current settings"""
        try:
            # Create cache key based on settings
            cache_key = self._create_settings_hash(grade, subject, language, topic)

            # Check if we need to generate new suggestions
            if (st.session_state.last_settings_hash != cache_key or 
                not st.session_state.cached_suggestions or
                st.session_state.settings_applied):

                # Reset the settings_applied flag
                st.session_state.settings_applied = False

                # Create the prompt for suggestions
                topic_text = f" focusing on {topic}" if topic != "All Topics" else ""

                prompt = f"""Generate 4 educational questions for Grade {grade} students studying {subject}{topic_text}.

                Requirements:
                - Questions must be in {language} language
                - Age-appropriate for Grade {grade} students
                - Related to {subject} curriculum
                - Encourage curiosity and learning
                - Mix different question types (factual, conceptual, analytical)

                Return only the questions, one per line, without numbering or bullets."""

                # Make API call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an educational assistant specialized in creating engaging questions for Indian students following NCERT curriculum."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )

                # Parse suggestions
                suggestions_text = response.choices[0].message.content.strip()
                suggestions = [q.strip() for q in suggestions_text.split('\n') if q.strip()]

                # Cache the results
                st.session_state.cached_suggestions = suggestions[:4]  # Ensure we have max 4
                st.session_state.last_settings_hash = cache_key

                return st.session_state.cached_suggestions
            else:
                # Return cached suggestions
                return st.session_state.cached_suggestions

        except Exception as e:
            st.error(f"Error generating suggestions: {str(e)}")
            return [
                "What is the structure of an atom?",
                "How do plants make their food?", 
                "What causes the seasons to change?",
                "Why is water important for living things?"
            ]

    def generate_fact_of_day(self, grade: int, subject: str, topic: str) -> Dict[str, Any]:
        """Generate fact of the day with priority: Grade > Subject > Topic, Language always English"""
        try:
            # Create cache key for fact (language always English for facts)
            cache_key = self._create_settings_hash(grade, subject, "English", topic)

            # Check if we need to generate a new fact
            if (not self._is_cache_valid(cache_key) or 
                st.session_state.settings_applied):

                # Create the prompt for fact generation
                topic_text = f" related to {topic}" if topic != "All Topics" else ""

                prompt = f"""Generate an interesting and educational science fact for Grade {grade} students studying {subject}{topic_text}.

                Requirements:
                - Must be in English language (always)
                - Age-appropriate for Grade {grade} students
                - Related to {subject} curriculum
                - Fascinating and memorable
                - Include a brief explanation
                - Should inspire curiosity

                Format the response as:
                Fact: [The interesting fact]
                Explanation: [Brief 2-3 sentence explanation]"""

                # Make API call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an educational assistant specialized in creating fascinating science facts for Indian students following NCERT curriculum."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=300
                )

                # Parse the fact
                fact_text = response.choices[0].message.content.strip()

                # Try to parse fact and explanation
                lines = fact_text.split('\n')
                fact = ""
                explanation = ""

                for line in lines:
                    if line.startswith("Fact:"):
                        fact = line.replace("Fact:", "").strip()
                    elif line.startswith("Explanation:"):
                        explanation = line.replace("Explanation:", "").strip()

                # Fallback if parsing fails
                if not fact:
                    fact = fact_text.split('\n')[0]
                if not explanation and len(lines) > 1:
                    explanation = ' '.join(lines[1:])

                # Create fact dictionary
                fact_data = {
                    "fact": fact,
                    "explanation": explanation,
                    "timestamp": datetime.now().isoformat()
                }

                # Cache the result
                st.session_state.fact_cache[cache_key] = fact_data

                return fact_data
            else:
                # Return cached fact
                return st.session_state.fact_cache[cache_key]

        except Exception as e:
            st.error(f"Error generating fact: {str(e)}")
            return {
                "fact": "The human brain contains approximately 86 billion neurons!",
                "explanation": "Each neuron can connect to thousands of other neurons, creating an incredibly complex network that allows us to think, learn, and remember.",
                "timestamp": datetime.now().isoformat()
            }

    def generate_response(self, question: str, grade: int, subject: str, language: str, topic: str) -> Dict[str, Optional[str]]:
        """Generate response to student question and find a relevant YouTube video."""
        response_text = ""
        video_url = None
        try:
            # 1. Generate text response
            topic_context = f" with focus on {topic}" if topic != "All Topics" else ""
            prompt = f"""You are an expert science teacher for Grade {grade} Indian students following NCERT curriculum.
            Student Question: {question}
            Context:
            - Grade: {grade}
            - Subject: {subject}
            - Language: {language}
            - Topic: {topic}
            Please provide a comprehensive, age-appropriate answer in {language} language that:
            1. Directly answers the student's question
            2. Is appropriate for Grade {grade} level understanding
            3. Relates to {subject}{topic_context}
            4. Encourages further learning
            5. Uses simple language and examples
            Keep the response educational, engaging, and encouraging."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a helpful science teacher for Grade {grade} students. Always respond in {language} language and keep explanations age-appropriate."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=1000
            )
            response_text = response.choices[0].message.content.strip()

            # 2. Search for a YouTube video
            video_search_query = f"educational video for grade {grade} {subject} {topic}: {question}"
            video_url = self.search_youtube_video(video_search_query)

        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            response_text = f"I apologize, but I'm having trouble answering your question right now. Please try again or ask a different question about {subject}."
        
        return {"text": response_text, "video_url": video_url}


    def clear_suggestion_cache(self):
        """Clear the suggestion cache to force regeneration"""
        st.session_state.cached_suggestions = []
        st.session_state.last_settings_hash = None
        st.session_state.settings_applied = True

    def clear_fact_cache(self):
        """Clear the fact cache to force regeneration"""
        st.session_state.fact_cache = {}
        st.session_state.settings_applied = True
