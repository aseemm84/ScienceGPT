"""
Topic Bookmarks & Study List for ScienceGPT v3.
Feature #6.

A bookmark is created when the student clicks 📌 next to any assistant message.
Bookmarks are stored in st.session_state["bookmarks"] and persisted to localStorage.

Each bookmark:
  {
    "topic":      str,   # from current session_state topic or inferred from message
    "subject":    str,
    "grade":      int,
    "question":   str,   # the question that triggered this answer
    "summary":    str,   # first 120 chars of the answer
    "saved_at":   str,   # ISO datetime
  }

The study list panel is rendered in the sidebar under a collapsible section.
A "Quiz me on this" button for each bookmark jumps to the Quiz tab pre-loaded
with that topic.
"""

from __future__ import annotations

import streamlit as st
from datetime import datetime
from utils.local_storage import persist_now
from utils.helpers import now_iso


# ── Add / remove ──────────────────────────────────────────────────────────────

def add_bookmark(question: str, answer: str, subject: str, topic: str, grade: int) -> None:
    """Add a bookmark to session state and persist."""
    bookmarks: list[dict] = st.session_state.setdefault("bookmarks", [])

    # Deduplicate by question
    if any(b["question"] == question for b in bookmarks):
        st.toast("Already bookmarked!", icon="📌")
        return

    summary = answer[:120].strip()
    if len(answer) > 120:
        summary += "…"

    bookmarks.insert(0, {
        "topic":    topic,
        "subject":  subject,
        "grade":    grade,
        "question": question,
        "summary":  summary,
        "saved_at": now_iso(),
    })

    persist_now()
    st.toast(f"📌 Bookmarked: {question[:50]}…" if len(question) > 50 else f"📌 Bookmarked!", icon="✅")


def remove_bookmark(index: int) -> None:
    """Remove bookmark by index and persist."""
    bookmarks: list[dict] = st.session_state.get("bookmarks", [])
    if 0 <= index < len(bookmarks):
        bookmarks.pop(index)
        persist_now()


# ── Inline bookmark button (rendered next to each chat message) ───────────────

def render_bookmark_button(msg_index: int, question: str, answer: str) -> None:
    """
    Render a small 📌 button under an assistant message.
    msg_index must be unique per message in the current render pass.
    """
    subject = st.session_state.get("subject", "Physics")
    topic   = st.session_state.get("topic", "All Topics")
    grade   = st.session_state.get("grade", 8)

    bookmarks = st.session_state.get("bookmarks", [])
    already   = any(b["question"] == question for b in bookmarks)

    label = "📌 Saved" if already else "📌 Save"
    if st.button(label, key=f"bm_btn_{msg_index}", disabled=already,
                 help="Save this to your Study List"):
        add_bookmark(question, answer, subject, topic, grade)
        st.rerun()


# ── Study list panel (rendered in sidebar) ────────────────────────────────────

def draw_study_list() -> None:
    """Render the study list in the sidebar."""
    bookmarks: list[dict] = st.session_state.get("bookmarks", [])

    st.markdown('<p class="sidebar-section">📚 Study List</p>', unsafe_allow_html=True)

    if not bookmarks:
        st.caption("No bookmarks yet. Click 📌 on any answer to save it here.")
        return

    st.caption(f"{len(bookmarks)} saved topic{'s' if len(bookmarks) != 1 else ''}")

    for i, bm in enumerate(bookmarks):
        with st.expander(f"📌 {bm['question'][:45]}…" if len(bm['question']) > 45
                         else f"📌 {bm['question']}"):
            st.markdown(
                f"**Subject:** {bm['subject']} · **Grade:** {bm['grade']}"
            )
            if bm.get("topic") and bm["topic"] != "All Topics":
                st.markdown(f"**Topic:** {bm['topic']}")
            st.caption(bm["summary"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Quiz me", key=f"bm_quiz_{i}",
                             use_container_width=True):
                    # Pre-load quiz settings and jump to quiz tab
                    st.session_state["grade"]   = bm["grade"]
                    st.session_state["subject"] = bm["subject"]
                    st.session_state["topic"]   = bm["topic"]
                    st.session_state["jump_to_quiz"] = True
                    # Clear existing quiz
                    for k in ("quiz_questions", "quiz_submitted",
                              "quiz_answers", "quiz_score", "active_quiz"):
                        st.session_state.pop(k, None)
                    st.rerun()
            with col2:
                if st.button("🗑️ Remove", key=f"bm_del_{i}",
                             use_container_width=True):
                    remove_bookmark(i)
                    st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear All Bookmarks", use_container_width=True):
        st.session_state["bookmarks"] = []
        persist_now()
        st.rerun()
