"""
ScienceGPT v3 — app.py (name-fix revision)

Bugs fixed vs previous version:
1. _ls_checked guard was preventing re-reading query params on every rerun.
   The guard was designed for the old JS bridge (which was slow). With
   st.query_params it's instant — no guard needed. Removed entirely.

2. initialize_session_state() was writing "student_name": "" into session_state
   BEFORE _load_local_storage() ran. Then hydrate_from_payload() checked
   `if not st.session_state.get("student_name")` — which returned "" (falsy),
   so it DID write. But because initialize_session_state() always ran first
   with the empty default, the check was fragile. Fixed by using a sentinel
   value (None) instead of "" so the truthiness check is unambiguous.

3. _complete_onboarding() called persist_now() then st.rerun() from the
   caller. On the rerun, initialize_session_state() ran again and reset
   student_name to "" BEFORE _load_local_storage() could restore it from
   the query params — because the query params write happens inside
   persist_now() which calls st.query_params[k] = v, but Streamlit doesn't
   guarantee the query params are readable in the same rerun they're written.
   Fixed by reading query params FIRST, then initialising defaults only for
   keys that don't yet have a value.
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


# ── Step 1: read query params BEFORE setting any defaults ─────────────────────

def _load_from_query_params() -> None:
    """
    Read ?name=&grade=&language=&subject=&difficulty= from the URL and write
    them directly into session_state.

    This runs BEFORE initialize_session_state() so that the defaults below
    never overwrite values that came from the URL.

    Guarded by _qp_loaded so it only runs once per browser session
    (query params don't change mid-session unless we write them).
    """
    if st.session_state.get("_qp_loaded"):
        return
    st.session_state["_qp_loaded"] = True

    name = st.query_params.get("name", "").strip()
    if not name:
        return  # no persisted user — onboarding will run

    # Write directly into session_state — initialize_session_state will
    # skip any key that already exists.
    st.session_state["student_name"]    = name
    st.session_state["onboarding_done"] = True

    grade_raw = st.query_params.get("grade", "8")
    try:
        st.session_state["grade"] = int(grade_raw)
    except ValueError:
        st.session_state["grade"] = 8

    for key, qp_key, default in [
        ("language",   "language",   "English"),
        ("subject",    "subject",    "Physics"),
        ("difficulty", "difficulty", "Standard"),
    ]:
        val = st.query_params.get(qp_key, "").strip()
        st.session_state[key] = val if val else default


# ── Step 2: fill in any remaining defaults ────────────────────────────────────

def initialize_session_state() -> None:
    """
    Set default values for all session_state keys.
    Only sets a key if it is NOT already present — so query-param values
    written in _load_from_query_params() are never overwritten.
    """
    defaults = {
        # Identity — use None sentinel so "no name yet" is distinguishable from ""
        "student_name":    None,
        "onboarding_done": False,

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

    # Singletons
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Order matters: query params first, then defaults
    _load_from_query_params()
    initialize_session_state()

    # Onboarding gate
    from frontend_components.onboarding import is_onboarding_needed, draw_onboarding
    if is_onboarding_needed():
        _, col, _ = st.columns([1, 2, 1])
        with col:
            draw_onboarding()
        return

    # Normal app
    with st.sidebar:
        from frontend_components.sidebar import draw_sidebar
        draw_sidebar()

    col_main, col_right = st.columns([3, 1])

    with col_main:
        tab_chat, tab_quiz, tab_progress = st.tabs(["💬 Chat", "📝 Quiz", "📊 My Progress"])

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
            st.markdown(f"`{d['day_name']}` {'█' * d['questions'] or '·'} {d['questions']}")

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
