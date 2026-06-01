"""
Main Interface v3 for ScienceGPT.

New vs v2:
- Feature #1: Student name in hero greeting (personalised)
- Feature #4: Concept Summary Cards after each assistant message
- Feature #5: Difficulty Level selector (Simple / Standard / Deep Dive) inline in chat header
- Feature #6: Bookmark button on every assistant message
- Difficulty is read from session_state and passed to stream_response
- Summary is generated async after streaming (one extra small LLM call)
"""

from __future__ import annotations

import streamlit as st
from backend_code.llm_handler import get_llm_handler
from frontend_components.bookmarks import render_bookmark_button
from utils.local_storage import persist_now
from config.constants import DIFFICULTY_LEVELS, DIFFICULTY_ICONS, DIFFICULTY_HELP


# ── Suggestion panel ──────────────────────────────────────────────────────────

def _render_suggestions(grade: int, subject: str, language: str, topic: str) -> None:
    handler      = get_llm_handler()
    settings_sig = f"{grade}|{subject}|{language}|{topic}"

    if (st.session_state.get("_sugg_sig") != settings_sig
            or not st.session_state.get("_suggestions")):
        with st.spinner("Generating personalised questions…"):
            suggestions = handler.generate_suggestions(grade, subject, language, topic)
        st.session_state["_suggestions"]  = suggestions
        st.session_state["_sugg_sig"]     = settings_sig
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


# ── Difficulty selector ───────────────────────────────────────────────────────

def _render_difficulty_selector() -> str:
    """
    Render three pill buttons for Simple / Standard / Deep Dive.
    Returns the currently selected difficulty string.
    """
    current = st.session_state.get("difficulty", "Standard")

    st.markdown("**🎚️ Explanation Depth**")
    cols = st.columns(3)
    for col, level in zip(cols, DIFFICULTY_LEVELS):
        with col:
            icon    = DIFFICULTY_ICONS[level]
            is_sel  = level == current
            btn_type = "primary" if is_sel else "secondary"
            if st.button(f"{icon} {level}", key=f"diff_{level}",
                         type=btn_type, use_container_width=True,
                         help=DIFFICULTY_HELP[level]):
                st.session_state["difficulty"] = level
                persist_now()
                st.rerun()

    return current


# ── Concept Summary Card (Feature #4) ────────────────────────────────────────

def _render_summary_card(msg_index: int, answer_text: str, grade: int) -> None:
    """
    Show a collapsible '📌 Key Takeaways' card under an assistant message.
    Generates the summary on first view, caches it in session_state.
    """
    cache_key = f"summary_{msg_index}"

    # Check if summary already generated
    if cache_key not in st.session_state:
        # Lazy generation — only when expander is opened
        with st.expander("📌 Key Takeaways — tap to expand"):
            if st.button("✨ Generate Summary", key=f"sum_btn_{msg_index}"):
                with st.spinner("Extracting key ideas…"):
                    handler = get_llm_handler()
                    result  = handler.generate_summary(answer_text, grade)
                st.session_state[cache_key] = result
                st.rerun()
        return

    result = st.session_state[cache_key]
    if not result:
        return

    with st.expander("📌 Key Takeaways", expanded=False):
        st.markdown(
            '<div class="summary-card">',
            unsafe_allow_html=True,
        )
        takeaways = result.get("takeaways", [])
        for i, t in enumerate(takeaways):
            icon = ["1️⃣", "2️⃣", "3️⃣"][i] if i < 3 else "▪️"
            st.markdown(f"{icon} {t}")

        remember = result.get("remember_this", "")
        if remember:
            st.markdown(
                f'<div class="remember-this">💡 <strong>Remember:</strong> {remember}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


# ── Explain-It-Back ───────────────────────────────────────────────────────────

def _render_explain_back(msg_index: int, original_text: str, grade: int) -> None:
    result_key = f"eib_result_{msg_index}"

    with st.expander("🗣️ Explain It Back — test your understanding"):
        st.markdown(
            '<div class="explain-back-box">'
            "<b>Your turn!</b> Explain this concept in your own words. "
            "ScienceGPT will grade your understanding."
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
                    result  = handler.grade_explain_back(
                        original_explanation=original_text,
                        student_explanation=student_text,
                        grade=grade,
                    )
                st.session_state[result_key] = result
                if "gamification" in st.session_state:
                    st.session_state.gamification.add_explain_back(result.get("score", 5))
                persist_now()
                st.rerun()

        if result_key in st.session_state:
            r     = st.session_state[result_key]
            score = r.get("score", 0)
            level = r.get("understanding_level", "")

            from utils.helpers import score_to_color, understanding_emoji
            color = score_to_color(score, max_score=10)

            col_score, col_info = st.columns([1, 3])
            with col_score:
                st.markdown(
                    f'<div class="score-display">'
                    f'<div class="score-number" style="color:{color}">{score}/10</div>'
                    f'<div style="font-size:0.8rem;color:#64748b;">'
                    f'{understanding_emoji(level)} {level}</div>'
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

    # ── Personalised hero ──────────────────────────────────────────────────────
    name   = st.session_state.get("student_name", "")
    grade  = st.session_state.get("grade", 8)
    streak = 0
    if "gamification" in st.session_state:
        streak = st.session_state.gamification.get_stats().get("streak_days", 0)

    if name:
        streak_msg = f"🔥 {streak}-day streak — keep it going!" if streak >= 2 else "Welcome back!"
        st.markdown(
            f"""
            <div class="sgpt-hero">
                <h1>🧪 ScienceGPT</h1>
                <p class="hero-greeting">Hey {name}! {streak_msg}</p>
                <p class="hero-sub">Your Personal AI Science Tutor</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="sgpt-hero">
                <h1>🧪 ScienceGPT</h1>
                <p>Your Personal AI Science Tutor</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    language     = st.session_state.get("language", "English")
    subject      = st.session_state.get("subject", "Physics")
    topic        = st.session_state.get("topic", "All Topics")
    socratic_mode: bool = st.session_state.get("socratic_mode", False)
    handler      = get_llm_handler()

    # ── Mode indicator ─────────────────────────────────────────────────────────
    if socratic_mode:
        st.markdown(
            '<span class="mode-badge mode-socratic">🦉 Socratic Mode — '
            "ScienceGPT will guide you with questions, not direct answers</span>",
            unsafe_allow_html=True,
        )

    # ── Difficulty selector (Feature #5) ──────────────────────────────────────
    difficulty = _render_difficulty_selector()

    # ── Suggestions ────────────────────────────────────────────────────────────
    st.markdown("---")
    _render_suggestions(grade, subject, language, topic)

    # ── Chat area ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💬 Chat with ScienceGPT")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Track which message index corresponds to which user question
    # (for bookmark button — needs the question text)
    user_q_map: dict[int, str] = {}
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            # The NEXT assistant message corresponds to this question
            user_q_map[i + 1] = msg["content"]

    # Render history
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                if message.get("original_english"):
                    with st.expander("🌐 See original English response"):
                        st.markdown(message["original_english"])

                if message.get("video_url"):
                    st.markdown("---")
                    st.markdown("##### 📺 Recommended Video")
                    st.video(message["video_url"])

                if message.get("content") and not message.get("is_socratic"):
                    # Summary card (Feature #4)
                    _render_summary_card(i, message["content"], grade)
                    # Explain-It-Back
                    _render_explain_back(i, message["content"], grade)
                    # Bookmark button (Feature #6)
                    question_for_bm = user_q_map.get(i, "")
                    if question_for_bm:
                        render_bookmark_button(i, question_for_bm, message["content"])

    # ── Input handling ─────────────────────────────────────────────────────────
    prompt = st.chat_input(f"Ask a {subject} question in {language}…")

    if st.session_state.get("user_input"):
        prompt = st.session_state.pop("user_input")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # ── Streaming response ─────────────────────────────────────────────────
        with st.chat_message("assistant"):
            if socratic_mode:
                st.markdown(
                    '<span class="mode-badge mode-socratic" '
                    'style="font-size:0.7rem;margin-bottom:6px;display:inline-flex;">'
                    '🦉 Socratic</span>',
                    unsafe_allow_html=True,
                )

            gen, lang_code = handler.stream_response(
                question=prompt,
                grade=grade,
                subject=subject,
                language=language,
                topic=topic,
                socratic_mode=socratic_mode,
                difficulty=difficulty,
            )
            streamed_text = st.write_stream(gen)

        full_english = st.session_state.pop("_last_english_response", streamed_text)
        english_q    = st.session_state.pop("_last_english_question", prompt)

        # ── Post-stream finalization ───────────────────────────────────────────
        with st.spinner("Finding a relevant video…"):
            final = handler.finalize_response(
                english_response=full_english,
                english_question=english_q,
                lang_code=lang_code,
                grade=grade,
                subject=subject,
                topic=topic,
            )

        display_text = final["text"]
        if lang_code != "en" and final["text"] != full_english:
            with st.chat_message("assistant"):
                st.markdown(display_text)
                if final.get("original_english"):
                    with st.expander("🌐 See original English response"):
                        st.markdown(final["original_english"])

        if final.get("video_url"):
            with st.chat_message("assistant"):
                st.markdown("---")
                st.markdown("##### 📺 Recommended Video")
                st.video(final["video_url"])

        # ── Record progress + gamification ────────────────────────────────────
        if "progress" in st.session_state:
            st.session_state.progress.record_question(
                question=prompt, subject=subject, grade=grade, topic=topic
            )
        if "gamification" in st.session_state:
            st.session_state.gamification.add_question(subject=subject)
            if socratic_mode:
                st.session_state.gamification.add_socratic_session()
            persist_now()

        # ── Save to history ────────────────────────────────────────────────────
        st.session_state.messages.append({
            "role":             "assistant",
            "content":          display_text if lang_code != "en" else full_english,
            "video_url":        final.get("video_url"),
            "original_english": final.get("original_english"),
            "is_socratic":      socratic_mode,
            "difficulty":       difficulty,
        })

        st.rerun()

    # ── Clear chat ─────────────────────────────────────────────────────────────
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat", help="Clear conversation history"):
            st.session_state.messages = []
            keys_to_clear = [k for k in st.session_state
                             if k.startswith(("eib_", "summary_"))]
            for k in keys_to_clear:
                del st.session_state[k]
            st.rerun()
