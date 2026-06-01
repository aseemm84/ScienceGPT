"""
ScienceGPT v2 — app.py
Main Streamlit entry point.

Upgrade summary vs frontend.py v1:
- Renamed to app.py (Streamlit convention)
- @st.cache_resource for LLMHandler and CurriculumData singletons
- StudentProgress.start_session() actually called on init
- Quiz panel and Mastery Heatmap added as tabs in main column
- Custom CSS loaded once from styles/custom.css
- All session_state keys initialised in one place
"""

import streamlit as st
from pathlib import Path

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="ScienceGPT",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load custom CSS once ──────────────────────────────────────────────────────
_css_path = Path(__file__).parent / "styles" / "custom.css"
if _css_path.exists():
    st.markdown(f"<style>{_css_path.read_text()}</style>", unsafe_allow_html=True)


# ── Session state bootstrap ───────────────────────────────────────────────────

def initialize_session_state() -> None:
    """
    Declare ALL session state keys in one place.
    Idempotent — safe to call on every rerun.
    """
    defaults = {
        # User settings
        "grade": 8,
        "language": "English",
        "subject": "Physics",
        "topic": "All Topics",
        "socratic_mode": False,

        # Chat
        "messages": [],
        "user_input": None,

        # Suggestion cache control
        "_sugg_sig": "",
        "_suggestions": [],

        # LLM caches
        "llm_cache": {},
        "fact_cache": {},
        "suggestion_cache": {},

        # Settings flag
        "settings_applied": False,

        # Quiz
        "active_quiz": False,
        "quiz_questions": [],
        "quiz_answers": {},
        "quiz_submitted": False,
        "quiz_score": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # ── Singletons (use cache_resource under the hood) ────────────────────────
    from backend_code.llm_handler import get_llm_handler
    from backend_code.curriculum_data import get_curriculum
    from backend_code.gamification import GamificationManager
    from backend_code.student_progress import StudentProgress

    # Ensure handler is warm (triggers cache_resource if not already created)
    get_llm_handler()
    get_curriculum()

    if "gamification" not in st.session_state:
        st.session_state.gamification = GamificationManager()

    if "progress" not in st.session_state:
        st.session_state.progress = StudentProgress()
        # ⬇ This was NEVER called in v1 — now it is
        st.session_state.progress.start_session()


# ── Main layout ───────────────────────────────────────────────────────────────

def main() -> None:
    initialize_session_state()

    # Sidebar
    with st.sidebar:
        from frontend_components.sidebar import draw_sidebar
        draw_sidebar()

    # Main content: two columns (3:1)
    col_main, col_right = st.columns([3, 1])

    with col_main:
        # Three tabs: Chat | Quiz | Progress
        tab_chat, tab_quiz, tab_progress = st.tabs([
            "💬 Chat", "📝 Quiz", "📊 My Progress"
        ])

        with tab_chat:
            from frontend_components.main_interface import draw_main_interface
            draw_main_interface()

        with tab_quiz:
            from frontend_components.quiz_ui import draw_quiz_panel
            draw_quiz_panel()

        with tab_progress:
            _draw_progress_tab()

    with col_right:
        from frontend_components.daily_challenge import draw_daily_challenge
        from frontend_components.gamification_ui import draw_gamification_ui
        draw_daily_challenge()
        st.divider()
        draw_gamification_ui()


def _draw_progress_tab() -> None:
    """Render the progress tab: mastery heatmap + weekly chart."""
    from frontend_components.mastery_heatmap import draw_mastery_heatmap
    draw_mastery_heatmap()

    st.markdown("---")
    st.markdown("### 📅 Weekly Activity")

    if "progress" not in st.session_state:
        st.info("No progress data yet.")
        return

    weekly = st.session_state.progress.get_weekly_progress()
    if not any(d["questions"] > 0 for d in weekly):
        st.info("Start chatting and taking quizzes to see your weekly activity!")
        return

    try:
        import plotly.graph_objects as go
        days = [d["day_name"] for d in weekly]
        questions = [d["questions"] for d in weekly]

        fig = go.Figure(
            go.Bar(
                x=days,
                y=questions,
                marker_color="#3B82F6",
                text=questions,
                textposition="outside",
            )
        )
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis_title="Questions Asked",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans, sans-serif"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        # Fallback without plotly
        for d in weekly:
            bar = "█" * d["questions"] if d["questions"] else "·"
            st.markdown(f"`{d['day_name']}` {bar} {d['questions']}")

    # Summary stats
    summary = st.session_state.progress.get_progress_summary()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Questions", summary["total_questions"])
    c2.metric("Subjects Explored", summary["subjects_explored"])
    c3.metric("Time Spent", f"{summary['total_time_spent']} min")

    # Export
    if st.button("📥 Export Progress Data (JSON)"):
        json_data = st.session_state.progress.export_progress_data()
        st.download_button(
            label="⬇️ Download JSON",
            data=json_data,
            file_name="sciencegpt_progress.json",
            mime="application/json",
        )


if __name__ == "__main__":
    main()
