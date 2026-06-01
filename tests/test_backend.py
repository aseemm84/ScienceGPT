"""
Tests for ScienceGPT backend modules.
Run with: pytest tests/
"""

import pytest
from backend_code.curriculum_data import CurriculumData
from utils.helpers import make_cache_key, safe_parse_json, set_to_list, score_to_color


# ── CurriculumData ────────────────────────────────────────────────────────────

class TestCurriculumData:
    def setup_method(self):
        self.cd = CurriculumData()

    def test_all_grades_present(self):
        grades = self.cd.get_all_grades()
        assert list(range(1, 13)) == grades

    def test_grade_8_has_three_subjects(self):
        subjects = self.cd.get_subjects_for_grade(8)
        assert set(subjects) == {"Physics", "Chemistry", "Biology"}

    def test_topics_non_empty_for_valid_combo(self):
        topics = self.cd.get_topics_for_grade_subject(9, "Physics")
        assert len(topics) > 0

    def test_invalid_grade_returns_empty(self):
        assert self.cd.get_subjects_for_grade(99) == []

    def test_invalid_subject_returns_empty(self):
        assert self.cd.get_topics_for_grade_subject(8, "Music") == []

    def test_valid_combination(self):
        assert self.cd.is_valid_combination(10, "Chemistry") is True
        assert self.cd.is_valid_combination(10, "History") is False


# ── Helpers ───────────────────────────────────────────────────────────────────

class TestHelpers:
    def test_make_cache_key_deterministic(self):
        k1 = make_cache_key(8, "Physics", "Friction")
        k2 = make_cache_key(8, "Physics", "Friction")
        assert k1 == k2

    def test_make_cache_key_different_inputs(self):
        k1 = make_cache_key(8, "Physics", "Friction")
        k2 = make_cache_key(8, "Physics", "Sound")
        assert k1 != k2

    def test_safe_parse_json_valid(self):
        result = safe_parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_safe_parse_json_with_fences(self):
        result = safe_parse_json('```json\n{"key": 1}\n```')
        assert result == {"key": 1}

    def test_safe_parse_json_invalid_returns_none(self):
        result = safe_parse_json("this is not json")
        assert result is None

    def test_set_to_list_converts(self):
        data = {"subjects": {"Math", "Science"}, "count": 2}
        result = set_to_list(data)
        assert isinstance(result["subjects"], list)
        assert set(result["subjects"]) == {"Math", "Science"}

    def test_score_to_color(self):
        assert score_to_color(20) == "#e74c3c"   # red
        assert score_to_color(55) == "#f39c12"   # amber
        assert score_to_color(80) == "#27ae60"   # green


# ── Gamification ──────────────────────────────────────────────────────────────

class TestGamificationManager:
    """
    These tests require a Streamlit session context.
    Run them with streamlit's test utilities or mock st.session_state.
    Placeholder structure shown here.
    """

    def test_placeholder(self):
        """Replace with real tests using st.testing or mock session state."""
        assert True
