"""
LLM Handler v3 for ScienceGPT.

New vs v2:
- Model routing: llama-3.1-8b for Grades 1-9, llama-3.3-70b for Grades 10-12
- Difficulty level fed into system prompt (Simple / Standard / Deep Dive)
- generate_summary(): extracts 3 key takeaways from a streamed response
- All prompts use config/prompts.py get_system_standard() for difficulty
- youtube_transcript_api removed (was unused in v1, never added back)
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from typing import Any, Generator

import streamlit as st
from groq import Groq

try:
    from googleapiclient.discovery import build as yt_build
    _HAS_YT = True
except ImportError:
    _HAS_YT = False

try:
    from deep_translator import GoogleTranslator
    _HAS_TRANSLATOR = True
except ImportError:
    _HAS_TRANSLATOR = False

from config import prompts as P
from config.constants import (
    get_model_for_grade,
    GROQ_MODEL_FAST,
    MAX_TOKENS_ANSWER, MAX_TOKENS_QUIZ, MAX_TOKENS_GRADE,
    MAX_TOKENS_EXPLAIN, MAX_TOKENS_SUGGESTIONS, MAX_TOKENS_FACT,
    MAX_TOKENS_VIDEO, MAX_TOKENS_EXPERIMENT, MAX_TOKENS_SUMMARY,
    ANSWER_TEMPERATURE, QUIZ_TEMPERATURE, GRADE_TEMPERATURE,
    SUGGESTIONS_TEMPERATURE, FACT_TEMPERATURE, SUMMARY_TEMPERATURE,
    FACT_CACHE_HOURS,
    YOUTUBE_MAX_RESULTS, YOUTUBE_CATEGORY_EDUCATION, YOUTUBE_RELEVANCE_LANG,
    LANG_MAP,
)
from utils.helpers import get_logger, make_cache_key, safe_parse_json, now_iso

log = get_logger(__name__)


# ── Singleton ─────────────────────────────────────────────────────────────────

@st.cache_resource
def get_llm_handler() -> "LLMHandler":
    return LLMHandler()


# ── Main class ────────────────────────────────────────────────────────────────

class LLMHandler:
    """Central AI engine for ScienceGPT v3."""

    def __init__(self) -> None:
        self._groq_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
        self._yt_key   = st.secrets.get("YOUTUBE_API_KEY", os.getenv("YOUTUBE_API_KEY", ""))

        if not self._groq_key:
            st.error("❌ GROQ_API_KEY not found. Add it to .streamlit/secrets.toml.")
            st.stop()

        self._client = Groq(api_key=self._groq_key)

        self._yt_service = None
        if self._yt_key and _HAS_YT:
            try:
                self._yt_service = yt_build("youtube", "v3", developerKey=self._yt_key)
            except Exception as exc:
                log.warning("YouTube service init failed: %s", exc)

        for key in ("llm_cache", "fact_cache", "suggestion_cache"):
            if key not in st.session_state:
                st.session_state[key] = {}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _call(
        self,
        system: str,
        user: str,
        max_tokens: int = MAX_TOKENS_ANSWER,
        temperature: float = ANSWER_TEMPERATURE,
        stream: bool = False,
        model: str | None = None,
    ) -> Any:
        return self._client.chat.completions.create(
            model=model or GROQ_MODEL_FAST,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

    @staticmethod
    def _text(response: Any) -> str:
        return response.choices[0].message.content.strip()

    def _translate(self, text: str, source: str, target: str) -> str:
        if not _HAS_TRANSLATOR or source == target:
            return text
        try:
            return GoogleTranslator(source=source, target=target).translate(text)
        except Exception as exc:
            log.warning("Translation failed (%s→%s): %s", source, target, exc)
            return text

    def _cache_valid(self, key: str, cache_name: str = "fact_cache",
                     hours: int = FACT_CACHE_HOURS) -> bool:
        entry = st.session_state[cache_name].get(key)
        if not entry:
            return False
        try:
            return datetime.now() - datetime.fromisoformat(entry["timestamp"]) < timedelta(hours=hours)
        except Exception:
            return False

    # ── Streaming answer ──────────────────────────────────────────────────────

    def stream_response(
        self,
        question: str,
        grade: int,
        subject: str,
        language: str,
        topic: str,
        socratic_mode: bool = False,
        difficulty: str = "Standard",
    ) -> tuple[Generator, str]:
        lang_code  = LANG_MAP.get(language, "en")
        english_q  = self._translate(question, "auto", "en") if lang_code != "en" else question
        model      = get_model_for_grade(grade)

        if socratic_mode:
            system = P.SYSTEM_SOCRATIC.format(grade=grade, subject=subject, topic=topic)
        else:
            system = P.get_system_standard(grade, subject, topic, difficulty)

        user   = P.USER_ANSWER.format(question=english_q, subject=subject,
                                      topic=topic, grade=grade)
        stream = self._call(system, user, stream=True, model=model)

        collected: list[str] = []

        def _gen() -> Generator[str, None, None]:
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                collected.append(delta)
                yield delta
            st.session_state["_last_english_response"] = "".join(collected)
            st.session_state["_last_english_question"]  = english_q

        return _gen(), lang_code

    def finalize_response(
        self,
        english_response: str,
        english_question: str,
        lang_code: str,
        grade: int,
        subject: str,
        topic: str,
    ) -> dict[str, str | None]:
        original_english: str | None = None
        if lang_code != "en":
            original_english = english_response
            translated  = self._translate(english_response, "en", lang_code)
            final_text  = translated or english_response
        else:
            final_text = english_response

        video     = self._find_video(english_question, grade, subject, topic)
        video_url = f"https://www.youtube.com/watch?v={video['id']}" if video else None

        return {"text": final_text, "video_url": video_url,
                "original_english": original_english}

    # ── Concept Summary (Feature #4) ──────────────────────────────────────────

    def generate_summary(self, explanation: str, grade: int) -> dict[str, Any] | None:
        """
        Extract 3 key takeaways from an existing explanation.
        Returns {"takeaways": [...], "remember_this": "..."} or None on failure.
        This is a cheap call: short prompt, short response, low temperature.
        """
        # Use cache to avoid re-summarising the same response
        cache_key = make_cache_key("summary", explanation[:80], grade)
        if cache_key in st.session_state.llm_cache:
            return st.session_state.llm_cache[cache_key]

        system = P.SYSTEM_SUMMARY
        user   = P.USER_SUMMARY.format(explanation=explanation[:1200], grade=grade)

        try:
            resp   = self._call(system, user,
                                max_tokens=MAX_TOKENS_SUMMARY,
                                temperature=SUMMARY_TEMPERATURE,
                                model=GROQ_MODEL_FAST)  # always use fast model
            result = safe_parse_json(self._text(resp))
            if isinstance(result, dict) and "takeaways" in result:
                st.session_state.llm_cache[cache_key] = result
                return result
        except Exception as exc:
            log.error("generate_summary failed: %s", exc)
        return None

    # ── Non-streaming answer ──────────────────────────────────────────────────

    def generate_response(
        self,
        question: str,
        grade: int,
        subject: str,
        language: str,
        topic: str,
        socratic_mode: bool = False,
        difficulty: str = "Standard",
    ) -> dict[str, str | None]:
        lang_code = LANG_MAP.get(language, "en")
        english_q = self._translate(question, "auto", "en") if lang_code != "en" else question
        model     = get_model_for_grade(grade)

        system = (P.SYSTEM_SOCRATIC.format(grade=grade, subject=subject, topic=topic)
                  if socratic_mode
                  else P.get_system_standard(grade, subject, topic, difficulty))
        user   = P.USER_ANSWER.format(question=english_q, subject=subject,
                                      topic=topic, grade=grade)

        try:
            resp         = self._call(system, user, model=model)
            english_resp = self._text(resp)
        except Exception as exc:
            log.error("generate_response failed: %s", exc)
            return {"text": f"Error: {exc}", "video_url": None, "original_english": None}

        original_english: str | None = None
        if lang_code != "en":
            original_english = english_resp
            final_text = self._translate(english_resp, "en", lang_code)
        else:
            final_text = english_resp

        video     = self._find_video(english_q, grade, subject, topic)
        video_url = f"https://www.youtube.com/watch?v={video['id']}" if video else None

        return {"text": final_text, "video_url": video_url,
                "original_english": original_english}

    # ── Quiz ──────────────────────────────────────────────────────────────────

    def generate_quiz(self, grade: int, subject: str, topic: str) -> list[dict[str, Any]]:
        cache_key = make_cache_key("quiz", grade, subject, topic)
        if cache_key in st.session_state.llm_cache:
            return st.session_state.llm_cache[cache_key]

        system = P.SYSTEM_QUIZ.format(grade=grade, subject=subject)
        user   = P.USER_QUIZ.format(topic=topic, grade=grade, subject=subject)
        model  = get_model_for_grade(grade)

        try:
            resp      = self._call(system, user, max_tokens=MAX_TOKENS_QUIZ,
                                   temperature=QUIZ_TEMPERATURE, model=model)
            raw       = self._text(resp)
            questions = safe_parse_json(raw)
            if not isinstance(questions, list):
                log.warning("Quiz parse failed: %s", raw[:200])
                return []
            st.session_state.llm_cache[cache_key] = questions
            return questions
        except Exception as exc:
            log.error("generate_quiz failed: %s", exc)
            return []

    def grade_short_answer(self, model_answer: str, student_answer: str,
                           grade: int) -> dict[str, Any]:
        system = P.SYSTEM_GRADE_SHORT.format(grade=grade)
        user   = P.USER_GRADE_SHORT.format(model_answer=model_answer,
                                           student_answer=student_answer)
        try:
            resp   = self._call(system, user, max_tokens=MAX_TOKENS_GRADE,
                                temperature=GRADE_TEMPERATURE, model=GROQ_MODEL_FAST)
            result = safe_parse_json(self._text(resp))
            if result:
                return result
        except Exception as exc:
            log.error("grade_short_answer failed: %s", exc)
        return {"score": 0, "correct_parts": "Could not evaluate.",
                "missed_parts": "Please try again.", "encouragement": "Keep going!"}

    # ── Explain-It-Back ───────────────────────────────────────────────────────

    def grade_explain_back(self, original_explanation: str,
                           student_explanation: str, grade: int) -> dict[str, Any]:
        system = P.SYSTEM_EXPLAIN_BACK.format(grade=grade)
        user   = P.USER_EXPLAIN_BACK.format(
            original_explanation=original_explanation,
            student_explanation=student_explanation,
        )
        try:
            resp   = self._call(system, user, max_tokens=MAX_TOKENS_EXPLAIN,
                                temperature=GRADE_TEMPERATURE, model=GROQ_MODEL_FAST)
            result = safe_parse_json(self._text(resp))
            if result:
                return result
        except Exception as exc:
            log.error("grade_explain_back failed: %s", exc)
        return {"score": 5, "understanding_level": "Partial",
                "correct_parts": "You showed some understanding.",
                "missed_parts": "Some key ideas were missing.",
                "follow_up_question": "Can you think of a real-world example?",
                "encouragement": "Great effort! Keep going!"}

    # ── Suggestions ───────────────────────────────────────────────────────────

    def generate_suggestions(self, grade: int, subject: str,
                              language: str, topic: str) -> list[str]:
        cache_key = make_cache_key(grade, subject, language, topic)
        if self._cache_valid(cache_key, "suggestion_cache", hours=6):
            return st.session_state.suggestion_cache[cache_key]["suggestions"]

        topic_clause = f" focusing on {topic}" if topic != "All Topics" else ""
        system = P.SYSTEM_SUGGESTIONS.format(language=language)
        user   = P.USER_SUGGESTIONS.format(grade=grade, subject=subject,
                                           topic_clause=topic_clause)
        try:
            resp        = self._call(system, user, max_tokens=MAX_TOKENS_SUGGESTIONS,
                                     temperature=SUGGESTIONS_TEMPERATURE,
                                     model=GROQ_MODEL_FAST)
            raw         = self._text(resp)
            suggestions = [q.strip() for q in raw.split("\n") if q.strip()][:4]
            st.session_state.suggestion_cache[cache_key] = {
                "suggestions": suggestions, "timestamp": now_iso()
            }
            return suggestions
        except Exception as exc:
            log.error("generate_suggestions failed: %s", exc)
            return ["What is the structure of an atom?",
                    "How do plants make their food?",
                    "What causes the seasons to change?",
                    "Why is water important for living things?"]

    # ── Fact of the day ───────────────────────────────────────────────────────

    def generate_fact_of_day(self, grade: int, subject: str, topic: str) -> dict[str, Any]:
        cache_key = make_cache_key(grade, subject, topic)
        if self._cache_valid(cache_key, "fact_cache"):
            return st.session_state.fact_cache[cache_key]

        topic_clause = f" related to {topic}" if topic != "All Topics" else ""
        system = P.SYSTEM_FACT
        user   = P.USER_FACT.format(grade=grade, subject=subject, topic_clause=topic_clause)

        try:
            resp = self._call(system, user, max_tokens=MAX_TOKENS_FACT,
                              temperature=FACT_TEMPERATURE, model=GROQ_MODEL_FAST)
            raw  = self._text(resp)
            fact, explanation = "", ""
            for line in raw.split("\n"):
                if line.startswith("Fact:"):
                    fact = line.replace("Fact:", "").strip()
                elif line.startswith("Explanation:"):
                    explanation = line.replace("Explanation:", "").strip()
            if not fact:
                fact = raw.split("\n")[0]
            entry = {"fact": fact, "explanation": explanation, "timestamp": now_iso()}
            st.session_state.fact_cache[cache_key] = entry
            return entry
        except Exception as exc:
            log.error("generate_fact_of_day failed: %s", exc)
            return {"fact": "The human brain contains ~86 billion neurons!",
                    "explanation": "Each neuron can connect to thousands of others.",
                    "timestamp": now_iso()}

    # ── Experiments ───────────────────────────────────────────────────────────

    def generate_experiment(self, grade: int, subject: str, topic: str) -> str:
        cache_key = make_cache_key("exp", grade, subject, topic)
        if cache_key in st.session_state.llm_cache:
            return st.session_state.llm_cache[cache_key]

        system = P.SYSTEM_EXPERIMENT
        user   = P.USER_EXPERIMENT.format(grade=grade, subject=subject, topic=topic)
        try:
            resp = self._call(system, user, max_tokens=MAX_TOKENS_EXPERIMENT,
                              temperature=0.4, model=GROQ_MODEL_FAST)
            text = self._text(resp)
            st.session_state.llm_cache[cache_key] = text
            return text
        except Exception as exc:
            log.error("generate_experiment failed: %s", exc)
            return "Could not generate an experiment. Please try again."

    # ── YouTube ───────────────────────────────────────────────────────────────

    def _find_video(self, english_question: str, grade: int,
                    subject: str, topic: str) -> dict[str, str] | None:
        if not self._yt_service:
            return None

        cache_key = make_cache_key("vid", grade, subject, topic, english_question[:40])
        if cache_key in st.session_state.llm_cache:
            return st.session_state.llm_cache[cache_key]

        try:
            search_q    = f"educational grade {grade} {subject} {topic} {english_question}"
            search_resp = self._yt_service.search().list(
                q=search_q, part="snippet",
                maxResults=YOUTUBE_MAX_RESULTS, type="video",
                videoCategoryId=YOUTUBE_CATEGORY_EDUCATION,
                relevanceLanguage=YOUTUBE_RELEVANCE_LANG,
            ).execute()

            items = search_resp.get("items", [])
            if not items:
                return None

            options = {v["id"]["videoId"]: {"id": v["id"]["videoId"],
                                             "title": v["snippet"]["title"]}
                       for v in items}
            video_list = "\n".join(f"- ID: {v['id']}, Title: {v['title']}"
                                   for v in options.values())

            resp     = self._call(P.SYSTEM_VIDEO_SELECT,
                                  P.USER_VIDEO_SELECT.format(grade=grade, topic=topic,
                                      subject=subject, question=english_question,
                                      video_list=video_list),
                                  max_tokens=MAX_TOKENS_VIDEO, temperature=0.1,
                                  model=GROQ_MODEL_FAST)
            raw_id   = self._text(resp)
            match    = re.search(r"[\w-]{11}", raw_id)
            sel_id   = match.group(0) if match and match.group(0) in options \
                       else list(options.keys())[0]

            result = options[sel_id]
            st.session_state.llm_cache[cache_key] = result
            return result
        except Exception as exc:
            log.warning("Video search failed: %s", exc)
            return None

    # ── Cache management ──────────────────────────────────────────────────────

    def clear_suggestion_cache(self) -> None:
        st.session_state.suggestion_cache = {}

    def clear_fact_cache(self) -> None:
        st.session_state.fact_cache = {}

    def clear_all_caches(self) -> None:
        for key in ("llm_cache", "fact_cache", "suggestion_cache"):
            st.session_state[key] = {}
