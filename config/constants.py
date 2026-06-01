"""
Application-wide constants for ScienceGPT.
Change values here — never scatter magic strings through the codebase.
"""

# ── Model ─────────────────────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.1-8b-instant"
MAX_TOKENS_ANSWER = 1500
MAX_TOKENS_QUIZ = 1200
MAX_TOKENS_GRADE = 400
MAX_TOKENS_EXPLAIN = 500
MAX_TOKENS_SUGGESTIONS = 500
MAX_TOKENS_FACT = 300
MAX_TOKENS_VIDEO = 20
MAX_TOKENS_EXPERIMENT = 400

ANSWER_TEMPERATURE = 0.2
QUIZ_TEMPERATURE = 0.3
GRADE_TEMPERATURE = 0.1
SUGGESTIONS_TEMPERATURE = 0.4
FACT_TEMPERATURE = 0.3

# ── Caching ───────────────────────────────────────────────────────────────────
FACT_CACHE_HOURS = 24
SUGGESTION_CACHE_HOURS = 6

# ── Gamification ──────────────────────────────────────────────────────────────
POINTS_PER_QUESTION = 10
POINTS_PER_FACT = 5
POINTS_PER_CHALLENGE = 5
POINTS_PER_QUIZ_CORRECT = 15
POINTS_PER_EXPLAIN_BACK = 20   # bonus for scoring ≥7/10
POINTS_EXPLAIN_BACK_BASE = 10  # awarded for any attempt

# ── Mastery thresholds (quiz score 0-100) ─────────────────────────────────────
MASTERY_NONE = 0        # never attempted  → grey
MASTERY_LOW = 40        # < 40             → red
MASTERY_MEDIUM = 70     # 40-69            → yellow
MASTERY_HIGH = 100      # 70-100           → green

# ── YouTube ───────────────────────────────────────────────────────────────────
YOUTUBE_MAX_RESULTS = 5
YOUTUBE_CATEGORY_EDUCATION = "27"
YOUTUBE_RELEVANCE_LANG = "en"

# ── UI ────────────────────────────────────────────────────────────────────────
APP_TITLE = "ScienceGPT"
APP_ICON = "🧪"
APP_SUBTITLE = "Your Personal AI Science Tutor"
APP_VERSION = "2.0"
LAYOUT = "wide"

# ── Languages ─────────────────────────────────────────────────────────────────
LANG_MAP = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Tamil": "ta",
    "Kannada": "kn",
    "Telugu": "te",
    "Malayalam": "ml",
    "Bengali": "bn",
    "Punjabi": "pa",
}
