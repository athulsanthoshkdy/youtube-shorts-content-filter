"""
Rule-based guardrails and keyword matching
Hard filters that run before the model
"""

import re
from typing import Dict, Tuple, List
from config import HARD_FILTERS, KEYWORD_PATTERNS, CRITICAL_CATEGORIES

class RuleEngine:
    """Fast, deterministic rule-based checks"""

    def __init__(self):
        # Compile regex patterns for speed
        self.slur_patterns = [re.compile(p, re.IGNORECASE) for p in HARD_FILTERS["SLURS"]]
        self.self_harm_patterns = [re.compile(p, re.IGNORECASE) for p in HARD_FILTERS["SELF_HARM_EXPLICIT"]]
        self.csam_patterns = [re.compile(p, re.IGNORECASE) for p in HARD_FILTERS["CSAM_INDICATORS"]]
        self.scam_link_patterns = [re.compile(p, re.IGNORECASE) for p in HARD_FILTERS["EXTREME_SCAM_LINKS"]]

    def check_guardrails(self, text: str) -> Tuple[bool, str, str]:
        """
        Run hard filters. Returns (is_violated, category, evidence)
        """
        text_lower = text.lower()

        # Check 1: CSAM (highest priority)
        for pattern in self.csam_patterns:
            if pattern.search(text_lower):
                return True, "SELF_HARM", "CSAM indicators detected - IMMEDIATE ESCALATION"

        # Check 2: Self-harm explicit
        for pattern in self.self_harm_patterns:
            if pattern.search(text_lower):
                return True, "SELF_HARM", "Explicit self-harm content detected"

        # Check 3: Slurs and hate speech
        for pattern in self.slur_patterns:
            match = pattern.search(text_lower)
            if match:
                return True, "HATE_SPEECH", f"Slur detected: {match.group()}"

        # Check 4: Extreme scam + link combo
        for pattern in self.scam_link_patterns:
            if pattern.search(text_lower):
                return True, "SCAM_SPAM", "Malicious link + scam keywords detected"

        return False, "", ""

    def keyword_match(self, text: str, category: str) -> Tuple[float, List[str]]:
        """
        Soft keyword matching for a category.
        Returns (score_boost, evidence_phrases)
        """
        text_lower = text.lower()
        keywords = KEYWORD_PATTERNS.get(category, [])

        matched_keywords = []
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)

        # Score: 0-1 based on keyword density
        if not matched_keywords:
            return 0.0, []

        score_boost = min(0.3, len(matched_keywords) * 0.1)  # Max +0.3 boost
        return score_boost, matched_keywords

    def check_context_safety(self, text: str, context_category: str = None) -> float:
        """
        If text contains safe context keywords, reduce risk.
        Returns multiplier (0.5 to 1.0)
        """
        text_lower = text.lower()

        safe_keywords = {
            "GAMING": ["minecraft", "roblox", "fortnite", "gamer", "stream"],
            "NEWS": ["breaking", "report", "investigation", "journalist"],
            "EDUCATION": ["tutorial", "how to", "explanation", "educational"],
        }

        for category, keywords in safe_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return 0.6  # Reduce risk by 40%

        return 1.0  # No safe context

# Global instance
rule_engine = RuleEngine()
