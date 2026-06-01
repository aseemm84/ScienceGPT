"""
ScienceGPT v3 — app.py (simplified persistence)

Name handling strategy:
- Ask for name once at the top of the main interface (inline, not a blocking gate)
- Store in st.session_state["student_name"] for the duration of the session
- On refresh: ask again (2-second friction, zero broken behaviour)
- Onboarding flow removed — grade/subject/language selected via sidebar as before
  (they persist correctly already via st.session_state + Apply Settings)

Why this is better than query_params:
- Streamlit Cloud has been observed stripping or not propagating custom query
  params written via st.query_params on certain deployments/CDN edges.
- Session state is 100% reliable within a session.
- The name input is non-blocking: the user can ask questions immediately,
  the name just won't appear in the greeting until they enter it.
"""

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="ScienceGPT",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

_css_path = Path(__file__).parent / "styles" / "custom.css"
if _css_path.exists():
    st.markdown(f"<style>{_css_path.read_text()}</style>", unsafe_allow_html=True)


def initialize_session_state() -> None:
    defaults = {
        # Identity — None = not yet entered this session
        "student_name": None,

        # Learning settings
        "grade":    8,
        "language": "English",
        "subject":  "Physics",
        "topic":    "All Topics",

        # AI modes
        "socratic_mode": False,
        "difficulty":    "Standard",

        # Chat
        "messages":   [],
        "user_input": None,

        # Suggestion cache
        "_sugg_sig":    "",
        "_suggestions": [],

        # LLM caches
        "llm_cache":        {},
        "fact_cache":       {},
        "suggestion_cache": {},

        "settings_applied": False,

        # Quiz
        "active_quiz":    False,
        "quiz_questions": [],
        "quiz_answers":   {},
        "quiz_submitted": False,
        "quiz_score":     0,
        "jump_to_quiz":   False,

        # Bookmarks
        "bookmarks": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    from backend_code.llm_handler import get_llm_handler
    from backend_code.curriculum_data import get_curriculum
    from backend_code.gamification import GamificationManager
    from backend_code.student_progress import StudentProgress

    get_llm_handler()
    get_curriculum()

    if "gamification" not in st.session_state:
        st.session_state.gamification = GamificationManager()

    if "progress" not in st.session_state:
        st.session_state.progress = StudentProgress()
        st.session_state.progress.start_session()


def main() -> None:
    initialize_session_state()

    with st.sidebar:
        from frontend_components.sidebar import draw_sidebar
        draw_sidebar()

    col_main, col_right = st.columns([3, 1])

    with col_main:
        tab_chat, tab_quiz, tab_progress = st.tabs(
            ["💬 Chat", "📝 Quiz", "📊 My Progress"]
        )

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
        fig = go.Figure(go.Bar(
            x=[d["day_name"]  for d in weekly],
            y=[d["questions"] for d in weekly],
            marker_color="#1e40af",
            text=[d["questions"] for d in weekly],
            textposition="outside",
        ))
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis_title="Questions Asked",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Nunito, sans-serif"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        for d in weekly:
            bar = "█" * d["questions"] if d["questions"] else "·"
            st.markdown(f"`{d['day_name']}` {bar} {d['questions']}")

    summary = st.session_state.progress.get_progress_summary()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Questions", summary["total_questions"])
    c2.metric("Subjects Explored", summary["subjects_explored"])
    c3.metric("Time Spent", f"{summary['total_time_spent']} min")

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
