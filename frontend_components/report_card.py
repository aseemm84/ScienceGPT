"""
Shareable HTML Report Card for ScienceGPT v3.
Feature #2.

Generates a fully self-contained, single-file HTML report card that:
- Requires no external dependencies (all CSS/SVG inline)
- Shows student name, grade, session stats, quiz scores, badges, topic coverage
- Includes a sparkline-style weekly activity bar chart (pure SVG)
- Downloads via st.download_button — no server needed
- Designed to be shared (WhatsApp, email, printed)
"""

from __future__ import annotations

import streamlit as st
from datetime import datetime
from typing import Any


# ── Public entry point ────────────────────────────────────────────────────────

def draw_report_card_section() -> None:
    """Render the 'Generate Report Card' button and download widget."""
    st.markdown("### 📄 Report Card")
    st.caption("Generate a shareable summary of your learning progress.")

    if st.button("🎓 Generate My Report Card", type="primary",
                 use_container_width=True):
        html = _build_html_report()
        name = st.session_state.get("student_name", "Student").replace(" ", "_")
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"ScienceGPT_Report_{name}_{today}.html"

        st.download_button(
            label="⬇️ Download Report Card (HTML)",
            data=html,
            file_name=filename,
            mime="text/html",
            use_container_width=True,
        )
        st.success("✅ Report ready! Open the downloaded file in any browser.")
        st.caption("Tip: You can print it or share the file directly.")


# ── HTML builder ──────────────────────────────────────────────────────────────

def _build_html_report() -> str:
    """Assemble a complete, self-contained HTML report card string."""
    name      = st.session_state.get("student_name", "Student")
    grade     = st.session_state.get("grade", 8)
    subject   = st.session_state.get("subject", "Physics")
    language  = st.session_state.get("language", "English")
    generated = datetime.now().strftime("%d %B %Y, %I:%M %p")

    # Gamification stats
    gam_data = st.session_state.get("gamification_data", {})
    points       = gam_data.get("points", 0)
    streak       = gam_data.get("streak_days", 0)
    badges_ids   = gam_data.get("badges", [])
    q_asked      = gam_data.get("questions_asked", 0)
    facts_seen   = gam_data.get("facts_generated", 0)
    quizzes_done = gam_data.get("quizzes_completed", 0)
    perfect_q    = gam_data.get("perfect_quizzes", 0)

    # Progress stats
    progress_summary: dict[str, Any] = {}
    if "progress" in st.session_state:
        try:
            progress_summary = st.session_state.progress.get_progress_summary()
        except Exception:
            pass

    total_time   = progress_summary.get("total_time_spent", 0)
    topics_data  = progress_summary.get("topic_coverage", {})
    quiz_results = {}
    if "progress" in st.session_state:
        try:
            quiz_results = st.session_state.progress._data.get("quiz_results", {})
        except Exception:
            pass

    # Weekly activity
    weekly: list[dict] = []
    if "progress" in st.session_state:
        try:
            weekly = st.session_state.progress.get_weekly_progress()
        except Exception:
            pass

    # Bookmarks
    bookmarks: list[dict] = st.session_state.get("bookmarks", [])

    # Badge catalogue (just the ones earned)
    from backend_code.gamification import BADGES
    earned_badges = [
        BADGES[bid] for bid in badges_ids if bid in BADGES
    ]

    # Build topic mastery rows
    mastery_rows = _build_mastery_rows(grade, subject, quiz_results)

    # Build weekly SVG chart
    weekly_svg = _build_weekly_svg(weekly)

    # Build badge chips HTML
    badge_html = _build_badge_html(earned_badges)

    # Build bookmarks HTML
    bookmark_html = _build_bookmarks_html(bookmarks)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ScienceGPT Report Card — {name}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Space+Mono:wght@700&display=swap');
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Nunito', sans-serif;
    background: #f0f4ff;
    color: #0f172a;
    padding: 2rem 1rem;
  }}
  .card {{
    max-width: 780px;
    margin: 0 auto;
    background: #fff;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 8px 40px rgba(0,0,0,0.12);
  }}
  .header {{
    background: linear-gradient(135deg, #1e3a8a 0%, #0f766e 100%);
    padding: 2.5rem 2rem 2rem;
    color: white;
    position: relative;
  }}
  .header-logo {{ font-size: 3rem; margin-bottom: 0.5rem; }}
  .header h1 {{
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    letter-spacing: -0.02em;
  }}
  .header .student-name {{
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0.3rem 0;
  }}
  .header .meta {{
    font-size: 0.88rem;
    opacity: 0.8;
    margin-top: 0.4rem;
  }}
  .header .generated {{
    position: absolute;
    top: 1.5rem;
    right: 2rem;
    font-size: 0.75rem;
    opacity: 0.7;
    text-align: right;
  }}
  .body {{ padding: 2rem; }}
  .section {{ margin-bottom: 2rem; }}
  .section h2 {{
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b;
    margin-bottom: 1rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid #e2e8f0;
  }}
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }}
  .stat-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
  }}
  .stat-value {{
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #1e3a8a;
  }}
  .stat-label {{
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 0.2rem;
  }}
  .mastery-table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  .mastery-table th {{
    background: #f1f5f9;
    padding: 0.6rem 0.8rem;
    text-align: left;
    font-weight: 700;
    color: #475569;
  }}
  .mastery-table td {{ padding: 0.5rem 0.8rem; border-bottom: 1px solid #f1f5f9; }}
  .mastery-pill {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
  }}
  .pill-green  {{ background:#d1fae5; color:#065f46; }}
  .pill-yellow {{ background:#fef3c7; color:#92400e; }}
  .pill-red    {{ background:#fee2e2; color:#991b1b; }}
  .pill-grey   {{ background:#e2e8f0; color:#475569; }}
  .badge-grid {{ display:flex; flex-wrap:wrap; gap:0.6rem; }}
  .badge {{
    background:#f0f4ff;
    border:1px solid #c7d2fe;
    border-radius:10px;
    padding:0.5rem 0.8rem;
    font-size:0.82rem;
    display:flex;
    align-items:center;
    gap:0.4rem;
  }}
  .badge .icon {{ font-size:1.2rem; }}
  .bm-list {{ list-style:none; }}
  .bm-list li {{
    padding:0.6rem 0;
    border-bottom:1px solid #f1f5f9;
    font-size:0.88rem;
  }}
  .bm-list li .bm-subject {{
    font-size:0.75rem;
    color:#64748b;
    margin-top:0.15rem;
  }}
  .footer {{
    background:#f8fafc;
    padding:1rem 2rem;
    text-align:center;
    font-size:0.78rem;
    color:#94a3b8;
    border-top:1px solid #e2e8f0;
  }}
  .footer strong {{ color:#3b82f6; }}
  @media print {{
    body {{ background:white; padding:0; }}
    .card {{ box-shadow:none; }}
  }}
</style>
</head>
<body>
<div class="card">

  <!-- HEADER -->
  <div class="header">
    <div class="generated">Generated<br>{generated}</div>
    <div class="header-logo">🧪</div>
    <h1>ScienceGPT Report Card</h1>
    <div class="student-name">{name}</div>
    <div class="meta">Grade {grade} · {subject} · {language}</div>
  </div>

  <div class="body">

    <!-- STATS -->
    <div class="section">
      <h2>📊 Session Statistics</h2>
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-value">{points}</div>
          <div class="stat-label">Points Earned</div>
        </div>
        <div class="stat-box">
          <div class="stat-value">{q_asked}</div>
          <div class="stat-label">Questions Asked</div>
        </div>
        <div class="stat-box">
          <div class="stat-value">{streak}d</div>
          <div class="stat-label">Learning Streak</div>
        </div>
        <div class="stat-box">
          <div class="stat-value">{quizzes_done}</div>
          <div class="stat-label">Quizzes Taken</div>
        </div>
        <div class="stat-box">
          <div class="stat-value">{perfect_q}</div>
          <div class="stat-label">Perfect Scores</div>
        </div>
        <div class="stat-box">
          <div class="stat-value">{int(total_time)}m</div>
          <div class="stat-label">Time Studied</div>
        </div>
      </div>
    </div>

    <!-- WEEKLY CHART -->
    {f'''<div class="section">
      <h2>📅 Weekly Activity</h2>
      {weekly_svg}
    </div>''' if weekly_svg else ''}

    <!-- TOPIC MASTERY -->
    {f'''<div class="section">
      <h2>🗺️ Topic Mastery — {subject}</h2>
      <table class="mastery-table">
        <thead><tr><th>Topic</th><th>Avg Score</th><th>Status</th></tr></thead>
        <tbody>{mastery_rows}</tbody>
      </table>
    </div>''' if mastery_rows else ''}

    <!-- BADGES -->
    {f'''<div class="section">
      <h2>🏅 Badges Earned ({len(earned_badges)})</h2>
      <div class="badge-grid">{badge_html}</div>
    </div>''' if earned_badges else ''}

    <!-- BOOKMARKS -->
    {f'''<div class="section">
      <h2>📌 Study Bookmarks ({len(bookmarks)})</h2>
      <ul class="bm-list">{bookmark_html}</ul>
    </div>''' if bookmarks else ''}

  </div>

  <div class="footer">
    Generated by <strong>ScienceGPT v3</strong> — Your Personal AI Science Tutor<br>
    Built with ❤️ by <strong>Aseem Mehrotra</strong>
  </div>
</div>
</body>
</html>"""


# ── Sub-builders ──────────────────────────────────────────────────────────────

def _build_mastery_rows(grade: int, subject: str, quiz_results: dict) -> str:
    try:
        from backend_code.curriculum_data import get_curriculum
        from utils.helpers import make_cache_key
        topics = get_curriculum().get_topics_for_grade_subject(grade, subject)
    except Exception:
        return ""

    rows = ""
    for t in topics:
        key = make_cache_key(subject, t)
        scores = quiz_results.get(key, [])
        if scores:
            avg = round(sum(scores) / len(scores))
            if avg >= 70:
                pill = f'<span class="mastery-pill pill-green">✅ Mastered ({avg}%)</span>'
            elif avg >= 40:
                pill = f'<span class="mastery-pill pill-yellow">🔶 In Progress ({avg}%)</span>'
            else:
                pill = f'<span class="mastery-pill pill-red">🔴 Needs Review ({avg}%)</span>'
        else:
            pill = '<span class="mastery-pill pill-grey">— Not attempted</span>'
        rows += f"<tr><td>{t}</td><td>{'—' if not scores else f'{avg}%'}</td><td>{pill}</td></tr>\n"

    return rows


def _build_weekly_svg(weekly: list[dict]) -> str:
    if not weekly or not any(d["questions"] > 0 for d in weekly):
        return ""

    max_q = max(d["questions"] for d in weekly) or 1
    w, h, bar_w, gap = 660, 120, 70, 10
    bars = ""

    for i, d in enumerate(weekly):
        x = i * (bar_w + gap) + 20
        bar_h = int((d["questions"] / max_q) * 80)
        y = h - bar_h - 25
        color = "#3b82f6" if d["questions"] > 0 else "#e2e8f0"
        bars += f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" rx="6" fill="{color}"/>'
        bars += f'<text x="{x + bar_w//2}" y="{h - 8}" text-anchor="middle" font-size="11" fill="#94a3b8" font-family="Nunito,sans-serif">{d["day_name"]}</text>'
        if d["questions"] > 0:
            bars += f'<text x="{x + bar_w//2}" y="{y - 4}" text-anchor="middle" font-size="11" fill="#1e3a8a" font-weight="700" font-family="Nunito,sans-serif">{d["questions"]}</text>'

    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:{w}px">{bars}</svg>'


def _build_badge_html(badges: list[dict]) -> str:
    html = ""
    for b in badges:
        html += f'<div class="badge"><span class="icon">{b["icon"]}</span><span>{b["name"]}</span></div>'
    return html


def _build_bookmarks_html(bookmarks: list[dict]) -> str:
    html = ""
    for bm in bookmarks[:10]:  # cap at 10 in the report
        q = bm["question"][:80] + ("…" if len(bm["question"]) > 80 else "")
        html += f'<li>📌 {q}<div class="bm-subject">{bm["subject"]} · Grade {bm["grade"]}</div></li>'
    return html
