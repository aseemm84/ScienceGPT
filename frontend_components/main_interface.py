"""
Enhanced Main Interface for ScienceGPT
Handles chat interface, dynamic question suggestions, and video display with summaries.
"""

import streamlit as st
from typing import List, Dict, Optional

def draw_main_interface():
    """Draw the enhanced main interface with a simplified and robust chat handler."""
    
    st.markdown("""
        <div style="text-align: center;">
            <h1 style="font-size: 3rem; font-weight: 700; display: flex; align-items: center; justify-content: center; margin-bottom: 0;">
                <span style="font-size: 3.5rem; margin-right: 10px;">🧪</span> ScienceGPT
            </h1>
            <p style="font-size: 1.25rem; color: #666; margin-top: 0;">Your Personal AI Science Tutor</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
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

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # ADDED: Logic to show an expander for the original English response
            if message["role"] == "assistant" and message.get("original_english"):
                with st.expander("See original English response"):
                    st.markdown(message["original_english"])
            
            if message["role"] == "assistant" and message.get("video_url"):
                st.markdown("---")
                st.markdown("##### 📺 Recommended Video")
                st.video(message["video_url"])

    # Process input from either a button click or the chat input box
    prompt = st.chat_input(f"Ask your {subject} question in {language}...")
    if st.session_state.user_input:
        prompt = st.session_state.user_input
        st.session_state.user_input = None

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking, finding the best video, and summarizing..."):
                response_data = llm_handler.generate_response(
                    prompt, grade, subject, language, topic
                )
                response_text = response_data.get("text", "Sorry, I encountered an error.")
                video_url = response_data.get("video_url")
                original_english = response_data.get("original_english") # ADDED

                st.markdown(response_text)
                
                # ADDED: Show expander for the new message immediately if applicable
                if original_english:
                    with st.expander("See original English response"):
                        st.markdown(original_english)

                if video_url:
                    st.markdown("---")
                    st.markdown("##### 📺 Recommended Video")
                    st.video(video_url)

        assistant_message = {
            "role": "assistant", 
            "content": response_text, 
            "video_url": video_url,
            "original_english": original_english # ADDED
        }
        st.session_state.messages.append(assistant_message)

        if 'gamification' in st.session_state:
            st.session_state.gamification.add_question()
        
        st.rerun()
