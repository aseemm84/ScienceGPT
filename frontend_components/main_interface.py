"""
Enhanced Main Interface for ScienceGPT
Handles chat interface and dynamic question suggestions
"""

import streamlit as st
from typing import List

def draw_main_interface():
    """Draw the enhanced main interface with dynamic content"""
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

    # Create columns for better layout
    col1, col2 = st.columns(2)

    for i, suggestion in enumerate(suggestions):
        with col1 if i % 2 == 0 else col2:
            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                # Add suggestion to chat and get response
                handle_question(suggestion, grade, subject, language, topic)

    # Chat interface
    st.markdown("---")
    st.markdown("### 💬 Chat with ScienceGPT")

    # Display chat messages
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Chat container
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input(f"Ask your {subject} question in {language}..."):
        handle_question(prompt, grade, subject, language, topic)

def handle_question(question: str, grade: int, subject: str, language: str, topic: str):
    """Handle a user question and generate response"""
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": question})

    # Display user message
    with st.chat_message("user"):
        st.markdown(question)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if 'llm_handler' in st.session_state:
                response = st.session_state.llm_handler.generate_response(
                    question, grade, subject, language, topic
                )
            else:
                response = "I'm sorry, I'm having trouble connecting right now. Please try again."

        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Update gamification
    if 'gamification' in st.session_state:
        st.session_state.gamification.add_points(10)  # 10 points per question
        st.session_state.gamification.check_achievements()
        # Update points in session state
        st.session_state.points = st.session_state.gamification.get_total_points()

    # Trigger rerun to update the interface
    st.rerun()

def clear_chat():
    """Clear the chat history"""
    if st.button("🗑️ Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.rerun()
