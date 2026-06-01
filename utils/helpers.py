"""
Shared utility helpers for ScienceGPT.
Unchanged from v2 — included so the v3 folder is self-contained.
"""

import json
import logging
import re
import hashlib
from datetime import datetime
from typing import Any


def get_logger(name: str) -> logging.Logger:
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


def safe_parse_json(raw: str) -> Any | None:
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def make_cache_key(*parts: Any) -> str:
    joined = "-".join(str(p) for p in parts)
    return hashlib.md5(joined.encode()).hexdigest()


def set_to_list(obj: Any) -> Any:
    if isinstance(obj, set):
        return sorted(obj)
    if isinstance(obj, dict):
        return {k: set_to_list(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [set_to_list(i) for i in obj]
    return obj


def grade_label(grade: int) -> str:
    return f"Grade {grade}"


def score_to_color(score: float, max_score: float = 100) -> str:
    pct = score / max_score
    if pct < 0.4:
        return "#e74c3c"
    if pct < 0.7:
        return "#f39c12"
    return "#27ae60"


def understanding_emoji(level: str) -> str:
    return {
        "Excellent": "🌟", "Good": "✅",
        "Partial": "🔶", "Needs Review": "🔴",
    }.get(level, "❓")


def format_duration(minutes: float) -> str:
    if minutes < 1:
        return "< 1 min"
    if minutes < 60:
        return f"{int(minutes)} min"
    h, m = int(minutes // 60), int(minutes % 60)
    return f"{h}h {m}m"


def now_iso() -> str:
    return datetime.now().isoformat()
