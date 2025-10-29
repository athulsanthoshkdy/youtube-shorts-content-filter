"""
Zero-Shot Classification Engine using facebook/bart-large-mnli
Combines rule-based guardrails + NLI model scoring
"""

import torch
from transformers import pipeline
from typing import Dict, List, Tuple
import numpy as np
from config import (
    RISK_DEFINITIONS, THRESHOLDS, CRITICAL_CATEGORIES,
    MODEL_CONFIG, KEYWORD_PATTERNS
)
from rules import rule_engine
from preprocess import preprocessor
import warnings
warnings.filterwarnings("ignore")

class ModerationEngine:
    """Zero-shot classification for content moderation"""

    def __init__(self, model_name: str = "facebook/bart-large-mnli", device: str = "cpu"):
        """Initialize the NLI model"""
        print(f"🚀 Loading model: {model_name}...")
        self.device = device
        self.model_name = model_name

        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model=model_name,
                device=0 if device == "cuda" else -1  # -1 = CPU
            )
            print("✓ Model loaded successfully")
        except Exception as e:
            print(f"⚠️  Error loading model: {e}")
            self.classifier = None

    def classify_with_nli(self, text: str) -> Dict[str, float]:
        """
        Zero-shot classification using Natural Language Inference
        Returns scores for each category
        """
        if not self.classifier:
            return {cat: 0.5 for cat in RISK_DEFINITIONS.keys()}

        # Get hypotheses
        hypotheses = list(RISK_DEFINITIONS.values())
        categories = list(RISK_DEFINITIONS.keys())

        try:
            # Run zero-shot classification
            result = self.classifier(
                text[:512],  # Truncate to model max length
                hypotheses,
                multi_class=True
            )

            # Map results back to categories
            scores = {}
            for label, score in zip(result["labels"], result["scores"]):
                idx = hypotheses.index(label)
                scores[categories[idx]] = score

            return scores
        except Exception as e:
            print(f"⚠️  Classification error: {e}")
            return {cat: 0.5 for cat in RISK_DEFINITIONS.keys()}

    def apply_keyword_boost(self, scores: Dict[str, float], text: str) -> Dict[str, float]:
        """
        Boost scores based on keyword matches
        """
        boosted_scores = scores.copy()

        for category in scores.keys():
            # Get keyword boost for this category
            keyword_key = category.replace("HATE_SPEECH", "SLURS")                                    .replace("SCAM_SPAM", "SCAM_INDICATORS")                                    .replace("MISINFO_HIGH_HARM", "HEALTH_MISINFORMATION")

            # Simple keyword matching
            category_keywords = {
                "HATE_SPEECH": ["slur", "racial", "ethnic", "racist", "discrimination"],
                "HARASSMENT": ["bully", "attack", "harassment", "threaten", "doxx"],
                "VIOLENCE_INCITEMENT": ["kill", "hurt", "violence", "attack", "bomb"],
                "SEXUAL_EXPLICIT": ["sexual", "nude", "pornography", "xxx", "explicit"],
                "SELF_HARM": ["suicide", "cut", "self-harm", "eat disorder", "die"],
                "SCAM_SPAM": ["scam", "fraud", "phishing", "free money", "click here"],
                "MISINFO_HIGH_HARM": ["fake", "hoax", "false", "misinformation", "conspiracy"],
            }

            keywords = category_keywords.get(category, [])
            text_lower = text.lower()

            match_count = sum(1 for kw in keywords if kw in text_lower)
            if match_count > 0:
                boost = min(0.15, match_count * 0.05)
                boosted_scores[category] = min(1.0, boosted_scores[category] + boost)

        return boosted_scores

    def moderate(self, short_metadata: dict) -> Dict:
        """
        Full moderation pipeline:
        1. Preprocess text
        2. Check hard filters
        3. Run NLI classification
        4. Apply keyword boost
        5. Return detailed results
        """

        # Step 1: Preprocess
        processed = preprocessor.preprocess_short(short_metadata)
        context = processed["context"]

        # Step 2: Check hard filters (instant HIGH risk)
        is_violated, category, evidence = rule_engine.check_guardrails(context)

        if is_violated:
            scores = {cat: 0.0 for cat in RISK_DEFINITIONS.keys()}
            scores[category] = 1.0
            evidence_list = [evidence]
        else:
            # Step 3: NLI classification
            scores = self.classify_with_nli(context)

            # Step 4: Keyword boost
            scores = self.apply_keyword_boost(scores, context)

            evidence_list = []

        # Categorize risk levels
        risk_levels = {}
        for cat, score in scores.items():
            if score > THRESHOLDS["HIGH_RISK"]:
                risk_levels[cat] = "HIGH"
            elif score > THRESHOLDS["MEDIUM_RISK"]:
                risk_levels[cat] = "MEDIUM"
            else:
                risk_levels[cat] = "LOW"

        # Find primary violation
        primary = max(scores.items(), key=lambda x: x[1])

        return {
            "short_id": short_metadata.get("short_id"),
            "context": context,
            "scores": scores,
            "risk_levels": risk_levels,
            "primary_violation": primary[0],
            "primary_score": primary[1],
            "evidence": evidence_list,
        }

# Global instance
engine = None

def get_engine():
    """Lazy load the engine"""
    global engine
    if engine is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        engine = ModerationEngine(device=device)
    return engine

# Test
if __name__ == "__main__":
    test_input = {
        "short_id": "test_123",
        "title": "Free money method revealed! Click now!!!",
        "description": "DM for details",
        "transcript": "Hey guys, send me $50 and I'll double it",
        "top_comments": ["This looks legit", "Sent $100!"]
    }

    eng = get_engine()
    result = eng.moderate(test_input)

    print("\n📊 Moderation Result:")
    print(f"Primary Violation: {result['primary_violation']}")
    print(f"Confidence: {result['primary_score']:.2%}")
    print(f"\nScores:")
    for cat, score in result['scores'].items():
        print(f"  {cat}: {score:.2%} ({result['risk_levels'][cat]})")
