"""
Daily Challenge Component v2 for ScienceGPT.
Changes vs v1:
- Challenge questions for Grades 9-12 added
- Tips are seeded by date so they don't change on every rerun
- add_fact_generated() now called when fact is shown
- clear_fact_cache() only clears the current key, not everything
- At-home experiment button wired
"""

import streamlit as st
import random
from datetime import datetime

from backend_code.llm_handler import get_llm_handler


# ── Challenge question bank ───────────────────────────────────────────────────
CHALLENGES: dict[int, str] = {
    1:  "Can you name 3 things you see around you that are living?",
    2:  "What makes plants green? Think about it!",
    3:  "How many bones do you think are in your body?",
    4:  "What happens to water when you heat it?",
    5:  "Why do we see different shapes of the moon?",
    6:  "What is the smallest unit of life?",
    7:  "How do magnets work?",
    8:  "What causes earthquakes?",
    9:  "If you drop a feather and a stone at the same time on the Moon, what happens?",
    10: "Why does the filament in a bulb glow but the connecting wires do not?",
    11: "If temperature increases, what happens to the rate of a chemical reaction?",
    12: "What is the difference between nuclear fission and nuclear fusion?",
}

TIPS: list[str] = [
    "Ask 'why' and 'how' questions — that's how scientists think!",
    "Observe the world around you; science is happening everywhere.",
    "Try simple experiments at home with adult supervision.",
    "Keep a science journal to record interesting discoveries.",
    "Connect what you learn to real-life examples.",
    "Discuss what you learn with friends and family.",
    "Don't be afraid to make mistakes — they help you learn!",
    "Draw diagrams to visualise complex concepts.",
    "Teach someone else what you've learned; it deepens your own understanding.",
    "Break hard problems into smaller, manageable questions.",
]


def draw_daily_challenge() -> None:
    """Render the fact of the day, daily challenge, and learning tip."""
    grade = st.session_state.get("grade", 8)
    subject = st.session_state.get("subject", "Physics")
    topic = st.session_state.get("topic", "All Topics")
    handler = get_llm_handler()

    # ── Fact of the day ────────────────────────────────────────────────────────
    st.markdown("### 🌟 Fact of the Day")

    with st.spinner("Loading your personalised fact…"):
        fact_data = handler.generate_fact_of_day(grade, subject, topic)

    # Wire gamification — only increment once per unique fact (keyed by timestamp)
    fact_ts_key = f"fact_seen_{fact_data.get('timestamp', '')}"
    if fact_ts_key not in st.session_state:
        st.session_state[fact_ts_key] = True
        if "gamification" in st.session_state:
            st.session_state.gamification.add_fact_generated()

    st.markdown(
        f'<div class="fact-card">'
        f'<div class="fact-text">💡 {fact_data["fact"]}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    if fact_data.get("explanation"):
        with st.expander("📖 Learn more"):
            st.markdown(fact_data["explanation"])

    topic_text = topic if topic != "All Topics" else "General Topics"
    st.caption(f"Grade {grade} · {subject} · {topic_text}")

    if st.button("🔄 New Fact", help="Generate a new fact for current settings"):
        # Clear ONLY the current fact key — not the whole cache
        from utils.helpers import make_cache_key
        key = make_cache_key(grade, subject, topic)
        st.session_state.fact_cache.pop(key, None)
        st.rerun()

    # ── At-home experiment ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔭 Try This at Home")

    exp_key = f"experiment_{grade}_{subject}_{topic}"
    if st.button("🧪 Suggest an Experiment", key="exp_btn"):
        with st.spinner("Designing your experiment…"):
            experiment = handler.generate_experiment(grade, subject, topic)
        st.session_state[exp_key] = experiment

    if exp_key in st.session_state:
        st.markdown(st.session_state[exp_key])

    # ── Daily challenge ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🎯 Daily Challenge")

    challenge = CHALLENGES.get(grade, "What's your favourite science topic and why?")
    st.markdown(f"**For Grade {grade}:**")
    st.info(challenge)

    today_str = datetime.now().date().isoformat()
    challenge_done_key = f"challenge_done_{today_str}_{grade}"

    if challenge_done_key not in st.session_state:
        if st.button("✅ I thought about it!", key="challenge_complete"):
            st.session_state[challenge_done_key] = True
            if "gamification" in st.session_state:
                st.session_state.gamification.add_challenge_completed()
            st.success("Great thinking! You earned 5 points! 🎉")
            st.rerun()
    else:
        st.success("✅ Challenge completed for today!")

    # ── Learning tip (stable per day — doesn't change on every rerun) ─────────
    st.markdown("---")
    st.markdown("### 💡 Learning Tip")

    # Seed by date so the same tip shows all day
    day_seed = int(today_str.replace("-", ""))
    tip = TIPS[day_seed % len(TIPS)]
    st.markdown(f"💭 *{tip}*")
