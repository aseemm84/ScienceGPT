"""
Application-wide constants for ScienceGPT v3.
"""

# ── Models — Free Groq tier ───────────────────────────────────────────────────
# Route by grade: 8b-instant for Grades 1-9 (fast, sufficient)
#                 70b-versatile for Grades 10-12 (complex topics need it)
GROQ_MODEL_FAST  = "llama-3.1-8b-instant"      # Grades 1-9, suggestions, facts
GROQ_MODEL_SMART = "llama-3.3-70b-versatile"   # Grades 10-12, quiz grading

def get_model_for_grade(grade: int) -> str:
    """Return the appropriate free-tier Groq model for the given grade."""
    return GROQ_MODEL_SMART if grade >= 10 else GROQ_MODEL_FAST

# ── Token budgets ─────────────────────────────────────────────────────────────
MAX_TOKENS_ANSWER      = 1500
MAX_TOKENS_QUIZ        = 1200
MAX_TOKENS_GRADE       = 400
MAX_TOKENS_EXPLAIN     = 500
MAX_TOKENS_SUGGESTIONS = 500
MAX_TOKENS_FACT        = 300
MAX_TOKENS_VIDEO       = 20
MAX_TOKENS_EXPERIMENT  = 400
MAX_TOKENS_SUMMARY     = 300   # NEW: concept summary cards

# ── Temperatures ──────────────────────────────────────────────────────────────
ANSWER_TEMPERATURE      = 0.2
QUIZ_TEMPERATURE        = 0.3
GRADE_TEMPERATURE       = 0.1
SUGGESTIONS_TEMPERATURE = 0.4
FACT_TEMPERATURE        = 0.3
SUMMARY_TEMPERATURE     = 0.1   # NEW: deterministic summaries

# ── Caching ───────────────────────────────────────────────────────────────────
FACT_CACHE_HOURS       = 24
SUGGESTION_CACHE_HOURS = 6

# ── Gamification ──────────────────────────────────────────────────────────────
POINTS_PER_QUESTION      = 10
POINTS_PER_FACT          = 5
POINTS_PER_CHALLENGE     = 5
POINTS_PER_QUIZ_CORRECT  = 15
POINTS_PER_EXPLAIN_BACK  = 20
POINTS_EXPLAIN_BACK_BASE = 10
POINTS_PER_BOOKMARK      = 2    # NEW: small reward for saving a bookmark

# ── Mastery thresholds ────────────────────────────────────────────────────────
MASTERY_NONE   = 0
MASTERY_LOW    = 40
MASTERY_MEDIUM = 70
MASTERY_HIGH   = 100

# ── Difficulty levels ─────────────────────────────────────────────────────────
DIFFICULTY_LEVELS = ["Simple", "Standard", "Deep Dive"]
DIFFICULTY_ICONS  = {"Simple": "🟢", "Standard": "🟡", "Deep Dive": "🔴"}
DIFFICULTY_HELP   = {
    "Simple":     "Clear, jargon-free explanations. Best when starting a new topic.",
    "Standard":   "Balanced depth with relatable examples. Good for most students.",
    "Deep Dive":  "Full detail: mechanisms, misconceptions, worked examples. For exam prep.",
}

# ── YouTube ───────────────────────────────────────────────────────────────────
YOUTUBE_MAX_RESULTS       = 5
YOUTUBE_CATEGORY_EDUCATION = "27"
YOUTUBE_RELEVANCE_LANG    = "en"

# ── UI ────────────────────────────────────────────────────────────────────────
APP_TITLE    = "ScienceGPT"
APP_ICON     = "🧪"
APP_SUBTITLE = "Your Personal AI Science Tutor"
APP_VERSION  = "3.0"
LAYOUT       = "wide"

# ── Languages ─────────────────────────────────────────────────────────────────
LANG_MAP = {
    "English":   "en",
    "Hindi":     "hi",
    "Marathi":   "mr",
    "Gujarati":  "gu",
    "Tamil":     "ta",
    "Kannada":   "kn",
    "Telugu":    "te",
    "Malayalam": "ml",
    "Bengali":   "bn",
    "Punjabi":   "pa",
}
