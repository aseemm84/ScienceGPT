"""
Shared utility helpers for ScienceGPT.
Keeps formatting, logging, and JSON-safety out of business logic.
"""

import json
import logging
import re
import hashlib
from datetime import datetime
from typing import Any

# ── Logger ────────────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """Return a consistently configured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                              datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


# ── JSON helpers ──────────────────────────────────────────────────────────────

def safe_parse_json(raw: str) -> Any | None:
    """
    Strip markdown fences and parse JSON.
    Returns None on failure instead of raising.
    """
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


# ── Hashing / caching ─────────────────────────────────────────────────────────

def make_cache_key(*parts: Any) -> str:
    """Create a stable MD5 cache key from arbitrary parts."""
    joined = "-".join(str(p) for p in parts)
    return hashlib.md5(joined.encode()).hexdigest()


# ── Set serialisation (session state safety) ──────────────────────────────────

def set_to_list(obj: Any) -> Any:
    """Recursively convert sets to sorted lists for JSON-safe storage."""
    if isinstance(obj, set):
        return sorted(obj)
    if isinstance(obj, dict):
        return {k: set_to_list(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [set_to_list(i) for i in obj]
    return obj


# ── Display helpers ───────────────────────────────────────────────────────────

def grade_label(grade: int) -> str:
    return f"Grade {grade}"


def score_to_color(score: float, max_score: float = 100) -> str:
    """Return a hex colour string on a red→yellow→green scale."""
    pct = score / max_score
    if pct < 0.4:
        return "#e74c3c"   # red
    if pct < 0.7:
        return "#f39c12"   # amber
    return "#27ae60"       # green


def understanding_emoji(level: str) -> str:
    return {
        "Excellent": "🌟",
        "Good": "✅",
        "Partial": "🔶",
        "Needs Review": "🔴",
    }.get(level, "❓")


def format_duration(minutes: float) -> str:
    """Format minutes into a human-readable string."""
    if minutes < 1:
        return "< 1 min"
    if minutes < 60:
        return f"{int(minutes)} min"
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h}h {m}m"


def now_iso() -> str:
    return datetime.now().isoformat()
