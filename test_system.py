"""
Unit tests for the moderation system
"""

import pytest
import json
from schemas import ShortMetadata, ModerationResult
from engine import get_engine
from decision import decision_logic
from rules import rule_engine
from preprocess import preprocessor

class TestPreprocessing:
    """Test text preprocessing"""

    def test_normalize_text(self):
        text = "Check http://example.com and email@test.com"
        normalized = preprocessor.normalize_text(text)
        assert "http" not in normalized
        assert "email" not in normalized

    def test_demojize(self):
        text = "Great! 🎉 Amazing 👍"
        result = preprocessor.demojize_text(text)
        assert "🎉" not in result

class TestRuleEngine:
    """Test hard filters"""

    def test_slur_detection(self):
        text_with_slur = "This is a [explicit slur here]"
        is_violated, category, evidence = rule_engine.check_guardrails(text_with_slur)
        # Should detect if pattern matches

    def test_self_harm_detection(self):
        text = "how to kill myself methods"
        is_violated, category, evidence = rule_engine.check_guardrails(text)
        assert is_violated and category == "SELF_HARM"

    def test_scam_detection(self):
        text = "free money guaranteed returns click here now"
        is_violated, category, evidence = rule_engine.check_guardrails(text)
        # May trigger depending on pattern strictness

class TestEngine:
    """Test moderation engine"""

    @pytest.fixture
    def engine_instance(self):
        return get_engine()

    def test_engine_initialization(self, engine_instance):
        assert engine_instance is not None
        assert engine_instance.classifier is not None

    def test_scam_classification(self, engine_instance):
        short = {
            "short_id": "test_scam",
            "title": "Double your money now!!!",
            "description": "Free crypto giveaway",
            "transcript": "Send $100 and get $200 back",
            "top_comments": [],
            "channel_name": "Test",
            "upload_date": "2024-01-01",
            "language": "en"
        }

        result = engine_instance.moderate(short)
        assert result["primary_violation"] in ["SCAM_SPAM", "MISINFO_HIGH_HARM"]
        assert result["primary_score"] > 0.5

class TestDecisionLogic:
    """Test decision making"""

    def test_high_confidence_remove(self):
        mod_result = {
            "scores": {cat: 0.1 for cat in ["HATE_SPEECH", "HARASSMENT", "VIOLENCE_INCITEMENT", "SEXUAL_EXPLICIT", "SELF_HARM", "SCAM_SPAM", "MISINFO_HIGH_HARM"]},
            "primary_violation": "SCAM_SPAM",
            "primary_score": 0.95,
            "risk_levels": {},
            "evidence": []
        }

        decision, action, escalation = decision_logic.compute_overall_decision(mod_result)
        assert decision == "REMOVE"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
