"""
Gamification UI Component v2 for ScienceGPT.
Changes vs v1: fixed reset, new badge types displayed, better stat grid.
"""

import streamlit as st
from backend_code.gamification import GamificationManager


def draw_gamification_ui() -> None:
    """Render the achievements and stats panel."""
    st.markdown("### 🏆 Achievements")

    if "gamification" not in st.session_state:
        st.session_state.gamification = GamificationManager()

    gm: GamificationManager = st.session_state.gamification
    gm.update_streak()
    stats = gm.get_stats()

    # ── Key metrics ────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    col1.metric("🎯 Points", stats["points"])
    col1.metric("🔥 Streak", f"{stats['streak_days']}d")
    col2.metric("🏅 Badges", stats["badges_count"])
    col2.metric("❓ Questions", stats["questions_asked"])

    # Additional stats row
    col3, col4 = st.columns(2)
    col3.metric("📝 Quizzes", stats["quizzes_completed"])
    col4.metric("🎯 Perfect", stats["perfect_quizzes"])

    # ── Earned badges ──────────────────────────────────────────────────────────
    earned = gm.get_user_badges()
    if earned:
        st.markdown("#### 🏅 Your Badges")
        n_cols = min(3, len(earned))
        cols = st.columns(n_cols)
        for i, badge in enumerate(earned):
            with cols[i % n_cols]:
                st.markdown(
                    f'<div class="badge-chip">'
                    f'<div style="font-size:24px;">{badge["icon"]}</div>'
                    f'<div style="font-size:11px;font-weight:600;">{badge["name"]}</div>'
                    f'<div style="font-size:10px;color:#94a3b8;">{badge["description"]}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ── Next goals ─────────────────────────────────────────────────────────────
    available = gm.get_available_badges()
    point_badges = sorted(
        [b for b in available if b["points_required"] > 0],
        key=lambda x: x["points_required"],
    )

    if point_badges:
        st.markdown("#### 🎯 Next Goals")
        current_pts = stats["points"]
        for badge in point_badges[:2]:
            needed = badge["points_required"] - current_pts
            if needed > 0:
                progress = min(current_pts / badge["points_required"], 1.0)
                st.markdown(f"**{badge['icon']} {badge['name']}**")
                st.progress(progress)
                st.caption(f"{needed} more points needed")

    # ── Motivation ─────────────────────────────────────────────────────────────
    pts = stats["points"]
    if pts == 0:
        st.info("🌟 Start your learning journey by asking a question!")
    elif pts < 50:
        st.info("🚀 Keep asking questions to earn more points!")
    elif pts < 100:
        st.success("⭐ Excellent progress! You're becoming a science star!")
    else:
        st.success("🏆 Amazing! You're a true science champion!")

    # ── Reset ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("🔄 Reset Progress", help="Reset all gamification data"):
        gm.reset()
        st.rerun()
