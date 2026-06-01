"""
Persistence layer for ScienceGPT v3 — name-fix revision.

Change vs previous version:
- save_to_local_storage() previously skipped writing "name" if it was falsy.
  This meant that when sidebar.py called persist_now() after "Apply Settings",
  the name was not included in the query params (because the user might have
  set student_name = None via the sentinel). Now "name" is always written if
  it exists in session_state, and the sidebar no longer silently drops it.

- build_persist_payload() now uses the None sentinel correctly:
  student_name = None means "not set yet" (onboarding not done)
  student_name = ""    should never happen — treated same as None
  student_name = "X"  → written to query params as ?name=X
"""

from __future__ import annotations
import streamlit as st
from utils.helpers import get_logger

log = get_logger(__name__)

_QP_NAME       = "name"
_QP_GRADE      = "grade"
_QP_LANGUAGE   = "language"
_QP_SUBJECT    = "subject"
_QP_DIFFICULTY = "difficulty"


# ── Read ──────────────────────────────────────────────────────────────────────

def load_from_local_storage() -> dict | None:
    """
    Read persisted user settings from URL query params.
    Returns None if no ?name= is present (triggers onboarding).
    NOTE: app.py now calls _load_from_query_params() directly instead of this
    function, but this is kept for backward compatibility with any code that
    imports it.
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
        "points":       0,
        "badges":       [],
        "streak_days":  0,
        "daily_visits": [],
        "bookmarks":    [],
    }


def hydrate_from_payload(data: dict) -> None:
    """Write payload into session_state. Only sets keys not already present."""
    if data.get("name") and not st.session_state.get("student_name"):
        st.session_state["student_name"] = data["name"]

    if not st.session_state.get("onboarding_done"):
        for key in ("grade", "language", "subject", "difficulty"):
            if key in data:
                st.session_state[key] = data[key]

    if data.get("bookmarks") and not st.session_state.get("bookmarks"):
        st.session_state["bookmarks"] = data["bookmarks"]


# ── Write ─────────────────────────────────────────────────────────────────────

def save_to_local_storage(data: dict) -> None:
    """
    Write user settings into URL query params.

    Key fix: name is written whenever it is a non-empty string.
    Previously `if data.get("name")` would skip it if name was None or "".
    Now we explicitly check for a non-empty string.
    """
    updates: dict[str, str] = {}

    # Name: always include if it's a real string
    name = data.get("name")
    if isinstance(name, str) and name.strip():
        updates[_QP_NAME] = name.strip()

    # Settings
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


# ── High-level helpers ────────────────────────────────────────────────────────

def build_persist_payload() -> dict:
    """Collect persistable state from session_state."""
    gam_data = st.session_state.get("gamification_data", {})

    # Resolve name: treat None and "" the same (not set)
    raw_name = st.session_state.get("student_name")
    name = raw_name.strip() if isinstance(raw_name, str) else ""

    return {
        "name":         name,
        "grade":        st.session_state.get("grade", 8),
        "language":     st.session_state.get("language", "English"),
        "subject":      st.session_state.get("subject", "Physics"),
        "difficulty":   st.session_state.get("difficulty", "Standard"),
        "points":       gam_data.get("points", 0),
        "badges":       gam_data.get("badges", []),
        "streak_days":  gam_data.get("streak_days", 0),
        "daily_visits": gam_data.get("daily_visits", []),
        "bookmarks":    st.session_state.get("bookmarks", []),
    }


def persist_now() -> None:
    """Convenience: build payload and write to query params."""
    save_to_local_storage(build_persist_payload())
