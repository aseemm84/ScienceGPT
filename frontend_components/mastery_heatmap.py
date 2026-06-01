"""
Mastery Heatmap Component v2 for ScienceGPT.
Feature #3: Visual grid showing topic mastery across subjects.

Colour legend:
  Grey   → never attempted
  Red    → attempted, avg score < 40%
  Amber  → avg score 40-69%
  Green  → avg score ≥ 70%
"""

import streamlit as st

try:
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

from config.constants import MASTERY_LOW, MASTERY_MEDIUM
from utils.helpers import score_to_color


def draw_mastery_heatmap() -> None:
    """Render the concept mastery heatmap for the current grade/subject."""
    grade = st.session_state.get("grade", 8)
    subject = st.session_state.get("subject", "Physics")

    st.markdown("### 🗺️ Concept Mastery Map")
    st.caption(
        f"Grade {grade} · {subject} — "
        "Complete quizzes to fill in your mastery map."
    )

    if "progress" not in st.session_state:
        st.info("Start studying and taking quizzes to see your mastery map!")
        return

    grid = st.session_state.progress.get_mastery_grid(grade, subject)

    if not grid:
        st.info("No topics found for this subject/grade combination.")
        return

    if _HAS_PLOTLY:
        _render_plotly_heatmap(grid, subject)
    else:
        _render_css_grid(grid)


# ── Plotly version (preferred) ────────────────────────────────────────────────

def _render_plotly_heatmap(grid: list[dict], subject: str) -> None:
    topics = [item["topic"] for item in grid]
    scores = []
    hover_texts = []
    colors = []

    for item in grid:
        mastery = item["mastery"]
        if mastery is None:
            scores.append(0)
            colors.append("#CBD5E1")  # grey — not attempted
            hover_texts.append(f"<b>{item['topic']}</b><br>Not yet attempted")
        else:
            scores.append(mastery)
            colors.append(score_to_color(mastery))
            label = (
                "Mastered" if mastery >= MASTERY_MEDIUM
                else "In Progress" if mastery >= MASTERY_LOW
                else "Needs Review"
            )
            hover_texts.append(
                f"<b>{item['topic']}</b><br>"
                f"Avg Quiz Score: {mastery}%<br>"
                f"Status: {label}"
            )

    # Wrap into a grid of ~3 columns
    cols = 3
    rows = (len(topics) + cols - 1) // cols
    padded = topics + [""] * (rows * cols - len(topics))
    padded_scores = scores + [None] * (rows * cols - len(scores))
    padded_colors = colors + ["#F8FAFC"] * (rows * cols - len(colors))
    padded_hover = hover_texts + [""] * (rows * cols - len(hover_texts))

    z = [padded_scores[r * cols:(r + 1) * cols] for r in range(rows)]
    text = [[padded[r * cols + c] for c in range(cols)] for r in range(rows)]
    hover = [[padded_hover[r * cols + c] for c in range(cols)] for r in range(rows)]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            text=text,
            hovertext=hover,
            hovertemplate="%{hovertext}<extra></extra>",
            texttemplate="%{text}",
            textfont={"size": 10},
            colorscale=[
                [0.0, "#EF4444"],
                [0.4, "#F59E0B"],
                [0.7, "#10B981"],
                [1.0, "#059669"],
            ],
            showscale=True,
            colorbar=dict(
                title="Score %",
                tickvals=[0, 40, 70, 100],
                ticktext=["0%", "40%", "70%", "100%"],
            ),
            zmin=0,
            zmax=100,
        )
    )

    fig.update_layout(
        height=max(250, rows * 60),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif"),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Legend
    st.markdown(
        """
        <div style="display:flex; gap:16px; font-size:0.8rem; margin-top:4px;">
            <span>⬜ Not attempted</span>
            <span>🟥 Needs review (&lt;40%)</span>
            <span>🟨 In progress (40-69%)</span>
            <span>🟩 Mastered (≥70%)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── CSS grid fallback (when plotly not installed) ─────────────────────────────

def _render_css_grid(grid: list[dict]) -> None:
    cols = st.columns(3)
    for i, item in enumerate(grid):
        mastery = item["mastery"]
        if mastery is None:
            bg, fg, label = "#E2E8F0", "#64748B", "—"
        elif mastery >= MASTERY_MEDIUM:
            bg, fg, label = "#D1FAE5", "#065F46", f"{mastery}%"
        elif mastery >= MASTERY_LOW:
            bg, fg, label = "#FEF3C7", "#92400E", f"{mastery}%"
        else:
            bg, fg, label = "#FEE2E2", "#991B1B", f"{mastery}%"

        with cols[i % 3]:
            st.markdown(
                f'<div class="mastery-cell" style="background:{bg};color:{fg};">'
                f"{item['topic'][:30]}<br>"
                f'<span style="font-size:0.7rem;">{label}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
