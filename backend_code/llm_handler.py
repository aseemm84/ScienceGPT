"""
Enhanced LLM Handler for ScienceGPT
Handles Groq API integration, intelligent YouTube video search with summarization, and dynamic content generation.
"""

import streamlit as st
import os
from groq import Groq
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from deep_translator import GoogleTranslator

class LLMHandler:
    """Enhanced LLM Handler with intelligent YouTube search, summarization, improved caching, and dynamic content"""

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
        self.model = "llama3-8b-8192"
        
        # Language mapping for the new translator library
        self.lang_map = {
            "English": "en", "Hindi": "hi", "Marathi": "mr", "Gujarati": "gu",
            "Tamil": "ta", "Kannada": "kn", "Telugu": "te", "Malayalam": "ml",
            "Bengali": "bn", "Punjabi": "pa"
        }

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

    def search_and_select_video(self, english_question: str, grade: int, subject: str, topic: str) -> Optional[Dict[str, str]]:
        """Searches for top videos using an English question and uses an LLM to select the best one."""
        if not self.youtube_service:
            return None
        
        try:
            search_query = f"educational video for grade {grade} {subject} {topic}: {english_question}"
            search_response = self.youtube_service.search().list(
                q=search_query,
                part='snippet',
                maxResults=5,
                type='video',
                videoCategoryId='27',
                relevanceLanguage='en'
            ).execute()

            videos = search_response.get('items', [])
            if not videos:
                return None

            video_options = {
                video['id']['videoId']: {
                    "id": video['id']['videoId'],
                    "title": video['snippet']['title'],
                    "description": video['snippet']['description']
                }
                for video in videos
            }
            
            prompt_video_list = [f"- ID: {v['id']}, Title: {v['title']}" for v in video_options.values()]
            prompt_video_text = "\n".join(prompt_video_list)

            selection_prompt = f"""
            A Grade {grade} student, studying '{topic}' in '{subject}', asked: "{english_question}"
            From the following list, select the ONE most relevant video. Return ONLY its ID.
            Video Options:
            {prompt_video_text}
            Best Video ID:
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at selecting relevant educational videos. You will only return the video ID."},
                    {"role": "user", "content": selection_prompt}
                ],
                temperature=0.1,
                max_tokens=20
            )
            
            response_text = response.choices[0].message.content.strip()
            
            match = re.search(r'[\w-]{11}', response_text)
            if match:
                selected_id = match.group(0)
                if selected_id in video_options:
                    return video_options[selected_id]

            return list(video_options.values())[0]

        except Exception as e:
            st.error(f"An error occurred during video selection: {e}")
            return None

    def get_video_summary(self, video_id: str, video_description: str) -> Optional[str]:
        """Generates a summary for a video using its transcript or description."""
        content_to_summarize = ""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
            transcript_text = " ".join([item['text'] for item in transcript_list])
            content_to_summarize = transcript_text
        except (NoTranscriptFound, TranscriptsDisabled):
            content_to_summarize = video_description
        except Exception:
            content_to_summarize = video_description

        if not content_to_summarize:
            return "No summary could be generated."

        summary_prompt = f"Summarize the following for a young student in 2-3 sentences:\n\n{content_to_summarize[:2000]}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing educational content for students."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.5,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error generating video summary: {e}")
            return None

    def generate_response(self, question: str, grade: int, subject: str, language: str, topic: str) -> Dict[str, Optional[str]]:
        """Generate response with a robust, self-correcting prompt to ensure a valid answer."""
        response_text = ""
        video_url = None
        video_summary = None
        
        try:
            lang_code = self.lang_map.get(language, 'en')

            # --- Step 1: Translate the user's question to English using deep-translator ---
            english_question = question
            if lang_code != 'en':
                try:
                    english_question = GoogleTranslator(source='auto', target='en').translate(question)
                except Exception as e:
                    st.warning(f"Could not translate question for processing: {e}")
                    english_question = question

            # --- Step 2: Generate the main response in English ---
            system_prompt = f"""
            You are ScienceGPT, an expert science teacher for Indian students.
            The user is a Grade {grade} student. Your explanations must be simple and age-appropriate.
            You MUST provide a valid, relevant scientific answer.
            """

            user_prompt = f"Provide a comprehensive answer in English for the question '{english_question}'."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=1500
            )
            english_response = response.choices[0].message.content.strip()

            # --- Step 3: Translate the English response back to the user's language ---
            if lang_code != 'en':
                try:
                    response_text = GoogleTranslator(source='en', target=lang_code).translate(english_response)
                except Exception as e:
                    st.warning(f"Could not translate response back to {language}: {e}")
                    response_text = english_response # Fallback to English response
            else:
                response_text = english_response

            if not response_text:
                response_text = f"I am currently having trouble processing this request in {language}. Please try rephrasing your question."

            # --- Step 4: Search for a video using the English question ---
            selected_video = self.search_and_select_video(english_question, grade, subject, topic)
            
            if selected_video:
                video_id = selected_video['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_summary = self.get_video_summary(video_id, selected_video['description'])

        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            response_text = f"An unexpected error occurred. Please try again."
        
        return {"text": response_text, "video_url": video_url, "video_summary": video_summary}

    def generate_suggestions(self, grade: int, subject: str, language: str, topic: str) -> List[str]:
        """Generate dynamic question suggestions based on current settings"""
        try:
            cache_key = self._create_settings_hash(grade, subject, language, topic)
            if (st.session_state.last_settings_hash != cache_key or 
                not st.session_state.cached_suggestions or
                st.session_state.settings_applied):
                st.session_state.settings_applied = False
                topic_text = f" focusing on {topic}" if topic != "All Topics" else ""
                prompt = f"""Generate 4 educational questions for a Grade {grade} student studying {subject}{topic_text}.
                The questions must be in {language}.
                Return only the questions, one per line, without numbering or bullets."""

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": f"You are an educational assistant creating questions for Indian students. You must respond in {language}."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )

                suggestions_text = response.choices[0].message.content.strip()
                suggestions = [q.strip() for q in suggestions_text.split('\n') if q.strip()]
                st.session_state.cached_suggestions = suggestions[:4]
                st.session_state.last_settings_hash = cache_key
                return st.session_state.cached_suggestions
            else:
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
            cache_key = self._create_settings_hash(grade, subject, "English", topic)
            if (not self._is_cache_valid(cache_key) or 
                st.session_state.settings_applied):
                topic_text = f" related to {topic}" if topic != "All Topics" else ""
                prompt = f"""Generate an interesting and educational science fact for a Grade {grade} student studying {subject}{topic_text}.
                The fact must be in English.
                Format the response as:
                Fact: [The interesting fact]
                Explanation: [Brief 2-3 sentence explanation]"""

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an educational assistant specialized in creating fascinating science facts for Indian students."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=300
                )

                fact_text = response.choices[0].message.content.strip()
                lines = fact_text.split('\n')
                fact = ""
                explanation = ""
                for line in lines:
                    if line.startswith("Fact:"):
                        fact = line.replace("Fact:", "").strip()
                    elif line.startswith("Explanation:"):
                        explanation = line.replace("Explanation:", "").strip()
                if not fact:
                    fact = fact_text.split('\n')[0]
                if not explanation and len(lines) > 1:
                    explanation = ' '.join(lines[1:])
                fact_data = {
                    "fact": fact,
                    "explanation": explanation,
                    "timestamp": datetime.now().isoformat()
                }
                st.session_state.fact_cache[cache_key] = fact_data
                return fact_data
            else:
                return st.session_state.fact_cache[cache_key]
        except Exception as e:
            st.error(f"Error generating fact: {str(e)}")
            return {
                "fact": "The human brain contains approximately 86 billion neurons!",
                "explanation": "Each neuron can connect to thousands of other neurons, creating an incredibly complex network that allows us to think, learn, and remember.",
                "timestamp": datetime.now().isoformat()
            }

    def clear_suggestion_cache(self):
        """Clear the suggestion cache to force regeneration"""
        st.session_state.cached_suggestions = []
        st.session_state.last_settings_hash = None
        st.session_state.settings_applied = True

    def clear_fact_cache(self):
        """Clear the fact cache to force regeneration"""
        st.session_state.fact_cache = {}
        st.session_state.settings_applied = True
