"""
Enhanced Daily Challenge Component for ScienceGPT
Generates dynamic facts based on Grade > Subject > Language (English) > Topic
"""

import streamlit as st
from datetime import datetime

def draw_daily_challenge():
    """Draw the enhanced daily challenge with dynamic fact generation"""
    st.markdown("### 🌟 Fun Fact of the Day")

    # Get current settings from session state
    grade = st.session_state.get('grade', 3)
    subject = st.session_state.get('subject', 'General Science')
    topic = st.session_state.get('topic', 'All Topics')

    # Initialize LLM handler if not already done
    if 'llm_handler' not in st.session_state:
        from backend_code.llm_handler import LLMHandler
        st.session_state.llm_handler = LLMHandler()

    llm_handler = st.session_state.llm_handler

    # Generate fact based on current settings (Language always English for facts)
    with st.spinner("Loading your personalized fact..."):
        fact_data = llm_handler.generate_fact_of_day(grade, subject, topic)

    # Display the fact
    st.markdown("#### 🔬 Today's Discovery")

    # Create an attractive container for the fact
    with st.container():
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1f77b4;">
            <h5 style="margin: 0; color: #1f77b4;">💡 {fact_data['fact']}</h5>
        </div>
        """, unsafe_allow_html=True)

        if fact_data.get('explanation'):
            st.markdown("#### 📖 Learn More:")
            st.markdown(fact_data['explanation'])

    # Show the context for the fact
    topic_text = topic if topic != "All Topics" else "General Topics"
    st.markdown(f"*Grade {grade} • {subject} • {topic_text}*")

    # Fact refresh button
    if st.button("🔄 Get New Fact", help="Generate a new fact for current settings"):
        # Clear the fact cache for current settings to force regeneration
        llm_handler.clear_fact_cache()
        st.rerun()

    # Display when the fact was generated
    if 'timestamp' in fact_data:
        try:
            if isinstance(fact_data['timestamp'], str):
                fact_time = datetime.fromisoformat(fact_data['timestamp'])
            else:
                fact_time = fact_data['timestamp']

            time_str = fact_time.strftime("%I:%M %p")
            st.caption(f"Generated at {time_str}")
        except:
            pass

    # Daily challenge section
    st.markdown("---")
    st.markdown("### 🎯 Daily Challenge")

    # Simple daily challenge based on current settings
    challenge_questions = {
        1: "Can you name 3 things you see around you that are living?",
        2: "What makes plants green? Think about it!",
        3: "How many bones do you think are in your body?",
        4: "What happens to water when you heat it?",
        5: "Why do we see different shapes of the moon?",
        6: "What is the smallest unit of life?",
        7: "How do magnets work?",
        8: "What causes earthquakes?"
    }

    challenge = challenge_questions.get(grade, "What's your favorite science topic and why?")

    st.markdown(f"**Today's Challenge for Grade {grade}:**")
    st.info(challenge)

    # Challenge completion tracking
    if f"challenge_completed_{datetime.now().date()}" not in st.session_state:
        if st.button("✅ I thought about it!", key="complete_challenge"):
            st.session_state[f"challenge_completed_{datetime.now().date()}"] = True
            if 'gamification' in st.session_state:
                st.session_state.gamification.add_points(5)  # 5 points for daily challenge
                st.session_state.points = st.session_state.gamification.get_total_points()
            st.success("Great job! You earned 5 points! 🎉")
            st.rerun()
    else:
        st.success("✅ Challenge completed for today!")

    # Learning tip
    st.markdown("---")
    st.markdown("### 💡 Learning Tip")

    tips = [
        "Ask 'why' and 'how' questions to understand science better!",
        "Observe the world around you - science is everywhere!",
        "Try simple experiments at home with adult supervision.",
        "Read science books and watch educational videos.",
        "Discuss what you learn with friends and family.",
        "Keep a science journal to record interesting discoveries.",
        "Don't be afraid to make mistakes - they help you learn!",
        "Connect what you learn in school to real life examples."
    ]

    import random
    tip = random.choice(tips)
    st.markdown(f"💭 *{tip}*")
