"""
localStorage bridge for ScienceGPT.

Streamlit has no native localStorage API. This module provides a clean
read/write interface by injecting JavaScript via st.components.v1.html
and communicating back to Python through Streamlit's query_params.

Architecture:
  - On page load, JS reads localStorage and writes a compact JSON blob
    into ?ls_data=<base64> in the URL query params.
  - Python reads that query param once and hydrates session_state.
  - On write, Python encodes the payload as base64, injects JS that
    writes it to localStorage and clears the query param.

Key stored: "sciencegpt_user"
Payload schema:
  {
    "name":        str,
    "grade":       int,
    "language":    str,
    "subject":     str,
    "points":      int,
    "badges":      list[str],
    "streak_days": int,
    "daily_visits":list[str],
    "bookmarks":   list[{topic, subject, grade, saved_at}],
    "difficulty":  str   ("Simple" | "Standard" | "Deep Dive")
  }
"""

from __future__ import annotations

import base64
import json
import streamlit as st
import streamlit.components.v1 as components
from utils.helpers import get_logger

log = get_logger(__name__)

_LS_KEY = "sciencegpt_user"
_QP_KEY = "ls_data"


# ── Read ──────────────────────────────────────────────────────────────────────

def load_from_local_storage() -> dict | None:
    """
    Inject JS that reads localStorage and stuffs the value into a query param.
    Returns the parsed dict on the NEXT rerun (after JS fires), or None.

    Call this once at the top of app.py before any other rendering.
    """
    # Step 1: inject reader JS (runs in the browser)
    _inject_reader()

    # Step 2: on subsequent reruns, the query param will be populated
    raw = st.query_params.get(_QP_KEY)
    if raw:
        try:
            decoded = base64.b64decode(raw.encode()).decode()
            data = json.loads(decoded)
            # Clean the query param so it doesn't persist in the URL
            _clear_qp()
            return data
        except Exception as e:
            log.warning("localStorage decode failed: %s", e)
            _clear_qp()
    return None


def _inject_reader() -> None:
    """Inject JS that reads localStorage and fires a query-param update."""
    # Only inject once per session to avoid flickering
    if st.session_state.get("_ls_reader_injected"):
        return
    st.session_state["_ls_reader_injected"] = True

    js = f"""
    <script>
    (function() {{
        try {{
            const raw = localStorage.getItem('{_LS_KEY}');
            if (raw) {{
                const b64 = btoa(unescape(encodeURIComponent(raw)));
                const url = new URL(window.parent.location.href);
                url.searchParams.set('{_QP_KEY}', b64);
                window.parent.history.replaceState(null, '', url.toString());
                // Trigger a Streamlit rerun by dispatching a storage event
                window.parent.dispatchEvent(new Event('popstate'));
            }}
        }} catch(e) {{ console.warn('ScienceGPT localStorage read failed', e); }}
    }})();
    </script>
    """
    components.html(js, height=0, scrolling=False)


def _clear_qp() -> None:
    """Remove the ls_data query param from the URL."""
    try:
        if _QP_KEY in st.query_params:
            del st.query_params[_QP_KEY]
    except Exception:
        pass


# ── Write ─────────────────────────────────────────────────────────────────────

def save_to_local_storage(data: dict) -> None:
    """
    Inject JS that writes `data` into localStorage under _LS_KEY.
    Call this whenever persistent state changes (name set, points earned, etc.).
    """
    try:
        payload = json.dumps(data, default=str)
        b64 = base64.b64encode(payload.encode()).decode()
    except Exception as e:
        log.warning("localStorage encode failed: %s", e)
        return

    js = f"""
    <script>
    (function() {{
        try {{
            const raw = atob('{b64}');
            const decoded = decodeURIComponent(escape(raw));
            localStorage.setItem('{_LS_KEY}', decoded);
        }} catch(e) {{ console.warn('ScienceGPT localStorage write failed', e); }}
    }})();
    </script>
    """
    components.html(js, height=0, scrolling=False)


# ── High-level helpers ────────────────────────────────────────────────────────

def build_persist_payload() -> dict:
    """
    Collect all persistable state from st.session_state into a single dict.
    Called before every save.
    """
    gam_data = st.session_state.get("gamification_data", {})
    return {
        "name":         st.session_state.get("student_name", ""),
        "grade":        st.session_state.get("grade", 8),
        "language":     st.session_state.get("language", "English"),
        "subject":      st.session_state.get("subject", "Physics"),
        "points":       gam_data.get("points", 0),
        "badges":       gam_data.get("badges", []),
        "streak_days":  gam_data.get("streak_days", 0),
        "daily_visits": gam_data.get("daily_visits", []),
        "bookmarks":    st.session_state.get("bookmarks", []),
        "difficulty":   st.session_state.get("difficulty", "Standard"),
    }


def hydrate_from_payload(data: dict) -> None:
    """
    Write a localStorage payload back into st.session_state.
    Only sets keys that aren't already overridden this session.
    """
    if data.get("name") and not st.session_state.get("student_name"):
        st.session_state["student_name"] = data["name"]

    # Restore settings only on first load (onboarding_done guards this)
    if not st.session_state.get("onboarding_done"):
        for key in ("grade", "language", "subject", "difficulty"):
            if key in data:
                st.session_state[key] = data[key]

    # Restore bookmarks
    if "bookmarks" in data and not st.session_state.get("bookmarks"):
        st.session_state["bookmarks"] = data["bookmarks"]

    # Restore gamification data
    if "gamification_data" in st.session_state:
        gd = st.session_state["gamification_data"]
        if data.get("points", 0) > gd.get("points", 0):
            gd["points"] = data["points"]
        if data.get("badges"):
            existing = set(gd.get("badges", []))
            existing.update(data["badges"])
            gd["badges"] = list(existing)
        if data.get("streak_days", 0) > gd.get("streak_days", 0):
            gd["streak_days"] = data["streak_days"]
        if data.get("daily_visits"):
            existing_visits = set(gd.get("daily_visits", []))
            existing_visits.update(data["daily_visits"])
            gd["daily_visits"] = list(existing_visits)


def persist_now() -> None:
    """Convenience: build payload and write to localStorage in one call."""
    save_to_local_storage(build_persist_payload())
