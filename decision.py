"""
Decision logic: aggregates signals and maps to final decisions
"""

from typing import Dict, Tuple, Optional
from datetime import datetime
from config import THRESHOLDS, DECISION_TYPES, CRITICAL_CATEGORIES, ESCALATION_LEVELS
from schemas import ModerationResult, CategoryScore

class DecisionLogic:
    """Maps moderation engine scores to actionable decisions"""

    @staticmethod
    def compute_overall_decision(moderation_result: Dict) -> Tuple[str, str, str]:
        """
        Decision tree logic
        Returns (decision, action_recommendation, escalation_priority)
        """

        scores = moderation_result["scores"]
        risk_levels = moderation_result["risk_levels"]
        primary_violation = moderation_result["primary_violation"]
        primary_score = moderation_result["primary_score"]

        # Rule 1: If any critical category is HIGH -> ESCALATE_TO_HUMAN
        for critical_cat in CRITICAL_CATEGORIES:
            if risk_levels.get(critical_cat) == "HIGH":
                return ("ESCALATE_TO_HUMAN", "ESCALATE_FOR_HUMAN_REVIEW", "P0")

        # Rule 2: If primary violation score > 0.90 -> REMOVE
        if primary_score > 0.90 and primary_violation in ["HATE_SPEECH", "SCAM_SPAM", "VIOLENCE_INCITEMENT"]:
            return ("REMOVE", "BLOCK_AND_REPORT", "P1")

        # Rule 3: Multiple MEDIUM risks -> QUARANTINE
        medium_count = sum(1 for rl in risk_levels.values() if rl == "MEDIUM")
        if medium_count >= 2:
            return ("ESCALATE_TO_HUMAN", "HOLD_FOR_REVIEW", "P2")

        # Rule 4: SEXUAL_EXPLICIT + MEDIUM -> AGE_RESTRICT
        if risk_levels.get("SEXUAL_EXPLICIT") == "MEDIUM" and primary_score > THRESHOLDS["MEDIUM_RISK"]:
            return ("AGE_RESTRICT", "ADD_AGE_RESTRICTION", "P3")

        # Rule 5: If confidence ambiguous (0.5-0.7) -> ESCALATE
        if 0.5 < primary_score < 0.7:
            return ("ESCALATE_TO_HUMAN", "HOLD_FOR_HUMAN_REVIEW", "P3")

        # Default: APPROVED
        return ("APPROVED", "APPROVE_CONTENT", "P3")

    @staticmethod
    def generate_notes(moderation_result: Dict, decision: str) -> str:
        """Generate human-readable notes"""

        primary_violation = moderation_result["primary_violation"]
        primary_score = moderation_result["primary_score"]
        evidence = moderation_result.get("evidence", [])

        if decision == "REMOVE":
            return f"High confidence {primary_violation} detected ({primary_score:.1%}). Immediate removal recommended."

        elif decision == "AGE_RESTRICT":
            return f"Mature content detected ({primary_violation}, {primary_score:.1%}). Age restriction recommended."

        elif decision == "ESCALATE_TO_HUMAN":
            if primary_score < 0.7:
                return f"Borderline confidence ({primary_score:.1%}). {primary_violation} suspected. Requires human judgment."
            else:
                return f"High confidence {primary_violation}. Escalated due to policy sensitivity. Manual review needed."

        else:  # APPROVED
            return "Content passes all checks. No violations detected."

    @staticmethod
    def create_result(
        short_metadata: dict,
        moderation_result: dict
    ) -> ModerationResult:
        """Convert engine output to ModerationResult"""

        scores = moderation_result["scores"]
        risk_levels = moderation_result["risk_levels"]

        # Compute decision
        decision, action, escalation = DecisionLogic.compute_overall_decision(moderation_result)

        # Generate notes
        notes = DecisionLogic.generate_notes(moderation_result, decision)

        # Build category results
        category_results = {}
        for cat in scores.keys():
            category_results[cat] = CategoryScore(
                risk_level=risk_levels[cat],
                score=scores[cat],
                evidence=moderation_result.get("evidence", []) if cat == moderation_result["primary_violation"] else []
            )

        # Compute overall confidence
        overall_confidence = max(scores.values()) if scores else 0.5

        return ModerationResult(
            short_id=short_metadata.get("short_id", "unknown"),
            overall_decision=decision,
            confidence_score=overall_confidence,
            primary_violation=moderation_result["primary_violation"],
            categories=category_results,
            action_recommendation=action,
            escalation_priority=escalation,
            notes_for_human_reviewer=notes,
            processing_timestamp=datetime.now().isoformat()
        )

# Global instance
decision_logic = DecisionLogic()
