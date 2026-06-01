"""
Persistence layer for ScienceGPT v3 — REVISED.

Replaces the broken localStorage JS-bridge approach with st.query_params,
which works reliably on all OS and browsers (Chrome, Safari, Firefox on
macOS M1, Windows, iOS, Android).

How it works:
  - On app load, read ?name=&grade=&language=&subject=&difficulty= from the URL.
  - After onboarding completes (or settings change), write those keys back into
    the URL via st.query_params.
  - The URL can be bookmarked or shared and will restore the user's settings.

What is NOT persisted across sessions this way:
  - Points / badges / streak (session-only; resets on refresh)
  - Bookmarks (session-only; resets on refresh)
  - Chat history (session-only by design)

For full cross-session persistence, use a database (Supabase free tier
recommended). See README for setup instructions.
"""

from __future__ import annotations
import streamlit as st
from utils.helpers import get_logger

log = get_logger(__name__)

# Query param keys
_QP_NAME       = "name"
_QP_GRADE      = "grade"
_QP_LANGUAGE   = "language"
_QP_SUBJECT    = "subject"
_QP_DIFFICULTY = "difficulty"


# ── Read ──────────────────────────────────────────────────────────────────────

def load_from_local_storage() -> dict | None:
    """
    Read persisted user settings from URL query params.
    Returns a dict matching the old localStorage schema, or None if no name
    is present (triggers onboarding).

    Call once at the top of app.py.
    """
    name = st.query_params.get(_QP_NAME, "").strip()
    if not name:
        return None

    grade_raw = st.query_params.get(_QP_GRADE, "8")
    try:
        grade = int(grade_raw)
    except ValueError:
        grade = 8

    return {
        "name":       name,
        "grade":      grade,
        "language":   st.query_params.get(_QP_LANGUAGE,   "English"),
        "subject":    st.query_params.get(_QP_SUBJECT,    "Physics"),
        "difficulty": st.query_params.get(_QP_DIFFICULTY, "Standard"),
        # Points/badges/bookmarks are session-only; not restored from URL
        "points":       0,
        "badges":       [],
        "streak_days":  0,
        "daily_visits": [],
        "bookmarks":    [],
    }


def hydrate_from_payload(data: dict) -> None:
    """
    Write a payload dict back into st.session_state.
    Only sets keys that aren't already set this session.
    """
    if data.get("name") and not st.session_state.get("student_name"):
        st.session_state["student_name"] = data["name"]

    if not st.session_state.get("onboarding_done"):
        for key in ("grade", "language", "subject", "difficulty"):
            if key in data:
                st.session_state[key] = data[key]

    # Bookmarks: restore if session has none
    if data.get("bookmarks") and not st.session_state.get("bookmarks"):
        st.session_state["bookmarks"] = data["bookmarks"]


# ── Write ─────────────────────────────────────────────────────────────────────

def save_to_local_storage(data: dict) -> None:
    """
    Write user settings into URL query params so they survive a page refresh.
    Silently skips any key whose value cannot be represented as a string.
    """
    updates: dict[str, str] = {}

    if data.get("name"):
        updates[_QP_NAME] = str(data["name"])
    if data.get("grade"):
        updates[_QP_GRADE] = str(data["grade"])
    if data.get("language"):
        updates[_QP_LANGUAGE] = str(data["language"])
    if data.get("subject"):
        updates[_QP_SUBJECT] = str(data["subject"])
    if data.get("difficulty"):
        updates[_QP_DIFFICULTY] = str(data["difficulty"])

    try:
        for k, v in updates.items():
            st.query_params[k] = v
    except Exception as e:
        log.warning("query_params write failed: %s", e)


# ── High-level helpers (same public API as before) ───────────────────────────

def build_persist_payload() -> dict:
    """Collect persistable state from session_state."""
    gam_data = st.session_state.get("gamification_data", {})
    return {
        "name":         st.session_state.get("student_name", ""),
        "grade":        st.session_state.get("grade", 8),
        "language":     st.session_state.get("language", "English"),
        "subject":      st.session_state.get("subject", "Physics"),
        "difficulty":   st.session_state.get("difficulty", "Standard"),
        # These are kept in payload schema for future DB upgrade compatibility
        "points":       gam_data.get("points", 0),
        "badges":       gam_data.get("badges", []),
        "streak_days":  gam_data.get("streak_days", 0),
        "daily_visits": gam_data.get("daily_visits", []),
        "bookmarks":    st.session_state.get("bookmarks", []),
    }


def persist_now() -> None:
    """Convenience: build payload and write to query params in one call."""
    save_to_local_storage(build_persist_payload())
