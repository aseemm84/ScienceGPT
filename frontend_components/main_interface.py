"""
Enhanced Main Interface for ScienceGPT
Handles chat interface, dynamic question suggestions, and video display.
"""

import streamlit as st
from typing import List, Dict, Optional

def draw_main_interface():
    """Draw the enhanced main interface with a simplified and robust chat handler."""
    st.title("🤖 Ask Your Science Questions")

    # Get current settings from session state
    grade = st.session_state.get('grade', 3)
    language = st.session_state.get('language', 'English')
    subject = st.session_state.get('subject', 'General Science')
    topic = st.session_state.get('topic', 'All Topics')

    # Initialize LLM handler if not already done
    if 'llm_handler' not in st.session_state:
        from backend_code.llm_handler import LLMHandler
        st.session_state.llm_handler = LLMHandler()
    llm_handler = st.session_state.llm_handler

    # Generate dynamic suggestions based on current settings
    with st.spinner("Generating personalized questions..."):
        suggestions = llm_handler.generate_suggestions(grade, subject, language, topic)

    # Display suggested questions
    st.markdown("### 💭 Suggested Questions")
    st.markdown(f"*Based on Grade {grade} {subject} in {language}*")

    col1, col2 = st.columns(2)
    # Use a session state variable to hold input from buttons
    if "user_input" not in st.session_state:
        st.session_state.user_input = None

    for i, suggestion in enumerate(suggestions):
        with col1 if i % 2 == 0 else col2:
            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                st.session_state.user_input = suggestion
                st.rerun()

    # Chat interface
    st.markdown("---")
    st.markdown("### 💬 Chat with ScienceGPT")

    # Initialize and display chat messages
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "video_url" in message and message["video_url"]:
                st.markdown("---")
                st.markdown("##### 📺 Recommended Video")
                st.video(message["video_url"])

    # Process input from either a button click or the chat input box
    prompt = st.chat_input(f"Ask your {subject} question in {language}...")
    if st.session_state.user_input:
        prompt = st.session_state.user_input
        st.session_state.user_input = None  # Reset after use

    # Main logic block to handle a new prompt
    if prompt:
        # Add user message to history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display the user's message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking and finding a relevant video..."):
                response_data = llm_handler.generate_response(
                    prompt, grade, subject, language, topic
                )
                response_text = response_data.get("text", "Sorry, I encountered an error.")
                video_url = response_data.get("video_url")

                st.markdown(response_text)
                if video_url:
                    st.markdown("---")
                    st.markdown("##### 📺 Recommended Video")
                    st.video(video_url)

        # Add assistant message to history
        assistant_message = {"role": "assistant", "content": response_text, "video_url": video_url}
        st.session_state.messages.append(assistant_message)

        # Update gamification stats
        if 'gamification' in st.session_state:
            # This single call handles points, achievements, and question count
            st.session_state.gamification.add_question()
        
        # Rerun to clear the input box and reflect the new state
        st.rerun()

