"""
Main Interface v2 for ScienceGPT.

Key changes vs v1:
- Streaming LLM responses via st.write_stream (Feature #1)
- Socratic mode respects toggle from sidebar (Feature #4)
- Explain-It-Back panel after each assistant message (Feature #5)
- Suggestions only regenerate on settings change, not every rerun
- StudentProgress.record_question() actually called
- GamificationManager.add_question() called with subject
- At-home experiment button per answer
- LaTeX rendering note (Streamlit renders $...$ natively)
"""

import streamlit as st
from backend_code.llm_handler import get_llm_handler
from backend_code.gamification import GamificationManager


# ── Suggestion panel ──────────────────────────────────────────────────────────

def _render_suggestions(grade: int, subject: str, language: str, topic: str) -> None:
    """
    Render question suggestion chips.
    Only regenerates when settings change — no spinner on every rerun.
    """
    handler = get_llm_handler()

    # Check if we need fresh suggestions
    settings_sig = f"{grade}|{subject}|{language}|{topic}"
    if (
        st.session_state.get("_sugg_sig") != settings_sig
        or not st.session_state.get("_suggestions")
    ):
        with st.spinner("Generating personalised questions…"):
            suggestions = handler.generate_suggestions(grade, subject, language, topic)
        st.session_state["_suggestions"] = suggestions
        st.session_state["_sugg_sig"] = settings_sig
    else:
        suggestions = st.session_state["_suggestions"]

    st.markdown("### 💭 Suggested Questions")
    st.caption(f"Grade {grade} · {subject} · {language}")

    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(suggestion, key=f"sugg_{i}_{settings_sig[:8]}",
                         use_container_width=True):
                st.session_state.user_input = suggestion
                st.rerun()


# ── Explain-It-Back panel ─────────────────────────────────────────────────────

def _render_explain_back(msg_index: int, original_text: str, grade: int) -> None:
    """
    Show the Explain-It-Back widget below an assistant message.
    msg_index is used to key widgets uniquely per message.
    """
    state_key = f"eib_{msg_index}"
    result_key = f"eib_result_{msg_index}"

    with st.expander("🗣️ Explain It Back — test your understanding"):
        st.markdown(
            '<div class="explain-back-box">'
            "<b>Your turn!</b> Explain this concept in your own words. "
            "Claude will grade your understanding."
            "</div>",
            unsafe_allow_html=True,
        )
        student_text = st.text_area(
            "Your explanation:",
            key=f"eib_input_{msg_index}",
            height=100,
            placeholder="Write what you understood in 2-4 sentences…",
        )

        if st.button("📝 Submit Explanation", key=f"eib_btn_{msg_index}"):
            if len(student_text.strip()) < 10:
                st.warning("Please write at least a sentence or two!")
            else:
                with st.spinner("Grading your explanation…"):
                    handler = get_llm_handler()
                    result = handler.grade_explain_back(
                        original_explanation=original_text,
                        student_explanation=student_text,
                        grade=grade,
                    )
                st.session_state[result_key] = result

                # Award gamification points
                if "gamification" in st.session_state:
                    st.session_state.gamification.add_explain_back(result.get("score", 5))

                st.rerun()

        # Show result if already graded
        if result_key in st.session_state:
            r = st.session_state[result_key]
            score = r.get("score", 0)
            level = r.get("understanding_level", "")

            from utils.helpers import score_to_color, understanding_emoji
            color = score_to_color(score, max_score=10)

            col_score, col_info = st.columns([1, 3])
            with col_score:
                st.markdown(
                    f'<div class="score-display">'
                    f'<div class="score-number" style="color:{color}">{score}/10</div>'
                    f'<div style="font-size:0.8rem;color:#64748b;">{understanding_emoji(level)} {level}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with col_info:
                st.markdown(f"✅ **What you got right:** {r.get('correct_parts', '')}")
                if r.get("missed_parts"):
                    st.markdown(f"🔶 **To improve:** {r.get('missed_parts', '')}")
                st.markdown(f"💬 **Follow-up:** *{r.get('follow_up_question', '')}*")
                st.info(r.get("encouragement", "Great effort!"))


# ── Main draw function ────────────────────────────────────────────────────────

def draw_main_interface() -> None:
    """Render the full main chat interface."""

    # ── Hero header ────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="sgpt-hero">
            <h1>🧪 ScienceGPT</h1>
            <p>Your Personal AI Science Tutor</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    grade = st.session_state.get("grade", 8)
    language = st.session_state.get("language", "English")
    subject = st.session_state.get("subject", "Physics")
    topic = st.session_state.get("topic", "All Topics")
    socratic_mode: bool = st.session_state.get("socratic_mode", False)

    handler = get_llm_handler()

    # ── Mode indicator ─────────────────────────────────────────────────────────
    if socratic_mode:
        st.markdown(
            '<span class="mode-badge mode-socratic">🦉 Socratic Mode — '
            "Claude will guide you with questions, not direct answers</span>",
            unsafe_allow_html=True,
        )
        st.markdown("")

    # ── Suggestions ────────────────────────────────────────────────────────────
    _render_suggestions(grade, subject, language, topic)

    # ── Chat area ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💬 Chat with ScienceGPT")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render history
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                # Original English toggle (for translated responses)
                if message.get("original_english"):
                    with st.expander("🌐 See original English response"):
                        st.markdown(message["original_english"])

                # Video
                if message.get("video_url"):
                    st.markdown("---")
                    st.markdown("##### 📺 Recommended Video")
                    st.video(message["video_url"])

                # Explain-It-Back
                if message.get("content") and not message.get("is_socratic"):
                    _render_explain_back(i, message["content"], grade)

    # ── Input handling ─────────────────────────────────────────────────────────
    prompt = st.chat_input(f"Ask a {subject} question in {language}…")

    # Pick up suggestion-button clicks
    if st.session_state.get("user_input"):
        prompt = st.session_state.pop("user_input")

    if prompt:
        # Append user message immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # ── Streaming assistant response ───────────────────────────────────────
        with st.chat_message("assistant"):
            # Socratic mode label
            if socratic_mode:
                st.markdown(
                    '<span class="mode-badge mode-socratic" '
                    'style="font-size:0.7rem;margin-bottom:6px;display:inline-flex;">🦉 Socratic</span>',
                    unsafe_allow_html=True,
                )

            gen, lang_code = handler.stream_response(
                question=prompt,
                grade=grade,
                subject=subject,
                language=language,
                topic=topic,
                socratic_mode=socratic_mode,
            )

            # Stream into the UI — this is the core Feature #1 change
            response_container = st.empty()
            full_english = ""
            streamed_text = ""

            # st.write_stream handles the generator automatically
            streamed_text = st.write_stream(gen)

            # After streaming finishes, stash English response
            full_english = st.session_state.pop("_last_english_response", streamed_text)
            english_q = st.session_state.pop("_last_english_question", prompt)

        # ── Post-stream processing (translation + video) ───────────────────────
        with st.spinner("Finding a relevant video…"):
            final = handler.finalize_response(
                english_response=full_english,
                english_question=english_q,
                lang_code=lang_code,
                grade=grade,
                subject=subject,
                topic=topic,
            )

        # If language is not English, we need to show translated text
        # The streamed text was in English; replace with translated version
        display_text = final["text"]
        if lang_code != "en" and final["text"] != full_english:
            # Re-render the assistant bubble with translated content
            with st.chat_message("assistant"):
                st.markdown(display_text)
                if final.get("original_english"):
                    with st.expander("🌐 See original English response"):
                        st.markdown(final["original_english"])

        # Show video
        if final.get("video_url"):
            with st.chat_message("assistant"):
                st.markdown("---")
                st.markdown("##### 📺 Recommended Video")
                st.video(final["video_url"])

        # ── Record progress ────────────────────────────────────────────────────
        if "progress" in st.session_state:
            st.session_state.progress.record_question(
                question=prompt, subject=subject, grade=grade, topic=topic
            )

        if "gamification" in st.session_state:
            st.session_state.gamification.add_question(subject=subject)
            if socratic_mode:
                # count socratic exchanges — award badge after 5
                st.session_state.gamification.add_socratic_session()

        # ── Save to history ────────────────────────────────────────────────────
        st.session_state.messages.append({
            "role": "assistant",
            "content": display_text if lang_code != "en" else full_english,
            "video_url": final.get("video_url"),
            "original_english": final.get("original_english"),
            "is_socratic": socratic_mode,
        })

        st.rerun()

    # ── Clear chat ─────────────────────────────────────────────────────────────
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat", help="Clear conversation history"):
            st.session_state.messages = []
            # Also clear explain-it-back states
            keys_to_clear = [k for k in st.session_state if k.startswith("eib_")]
            for k in keys_to_clear:
                del st.session_state[k]
            st.rerun()
