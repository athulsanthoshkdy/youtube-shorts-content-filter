"""
Configuration and constants for the YouTube Shorts Moderation System
"""

import re
from typing import Dict, List

# ============ RISK DEFINITIONS & HYPOTHESES ============

RISK_DEFINITIONS = {
    "HATE_SPEECH": "This text contains hate speech, slurs, or dehumanizing language targeting protected groups.",
    "HARASSMENT": "This text contains harassment, bullying, doxxing, or aggressive personal attacks.",
    "VIOLENCE_INCITEMENT": "This text glorifies violence, incites harm, or encourages dangerous activities.",
    "SEXUAL_EXPLICIT": "This text contains sexually explicit content, pornography, or non-consensual sexual references.",
    "SELF_HARM": "This text promotes suicide, self-harm, eating disorders, or self-mutilation.",
    "SCAM_SPAM": "This text is a scam, phishing attempt, spam, or fraudulent financial scheme.",
    "MISINFO_HIGH_HARM": "This text spreads dangerous misinformation about elections, health, or emergencies.",
}

# ============ DECISION TYPES ============

DECISION_TYPES = {
    "APPROVED": "Content passes moderation. No violations detected.",
    "REMOVE": "High confidence violation. Content should be removed.",
    "AGE_RESTRICT": "Mature content. Restrict to 18+ audience.",
    "ESCALATE_TO_HUMAN": "Borderline or sensitive. Requires human review.",
    "NEED_MORE_CONTEXT": "Ambiguous. Video analysis or manual review needed.",
}

# ============ CONFIDENCE THRESHOLDS ============

THRESHOLDS = {
    "HIGH_RISK": 0.85,      # > 0.85 -> HIGH risk
    "MEDIUM_RISK": 0.60,    # 0.60-0.85 -> MEDIUM risk
    "LOW_RISK": 0.30,       # < 0.30 -> LOW risk
}

# ============ CATEGORY PRIORITIES ============

CRITICAL_CATEGORIES = [
    "SELF_HARM",
    "VIOLENCE_INCITEMENT",
]

STRICT_CATEGORIES = [
    "HATE_SPEECH",
    "HARASSMENT",
]

# ============ ESCALATION PRIORITIES ============

ESCALATION_LEVELS = {
    "P0": "CRITICAL - Immediate action required (CSAM, active self-harm)",
    "P1": "HIGH - Same-day review required (hate speech, violence)",
    "P2": "MEDIUM - Within 24 hours (scams, harassment)",
    "P3": "LOW - Within 72 hours (borderline cases)",
}

# ============ REGEX PATTERNS FOR GUARDRAILS ============

# These patterns are checked BEFORE the model runs
# If triggered, confidence is set to 1.0 (absolute)

HARD_FILTERS = {
    "SLURS": [
        r"\b(n[i1]gg[ae]r|f[a4]gg[o0]t|dyke|tr[a4]nny|r[e3]t[a4]rd)\b",
        r"\b(j3w|j3wish|kike)\b",
        r"\b(sp[i1]c|c[o0]ck|p[o0]lak)\b",
    ],
    "SELF_HARM_EXPLICIT": [
        r"(how to kill myself|how to (cut|slit) my wrist|suicide method|end it all)",
        r"(emetophilia|bulimia method|how to starve|eat less)",
    ],
    "CSAM_INDICATORS": [
        r"(child sexual abuse|cp link|child p[o0]rn|loli)",
        r"(pedoph|child [s0]ex|grooming|child abuse)",
    ],
    "EXTREME_SCAM_LINKS": [
        r"(bit\.ly|tinyurl|t\.me|telegram|whatsapp.*link).*?(crypto|nft|forex|giveaway|free money|click here)",
    ],
}

# ============ KEYWORD LISTS (Soft Matching) ============

KEYWORD_PATTERNS = {
    "SCAM_INDICATORS": [
        "free money", "double your", "guaranteed returns", "click here now",
        "limited time", "act fast", "before it's too late", "dm for details",
        "deposit to activate", "sign up bonus", "crypto giveaway", "blockchain",
    ],
    "HEALTH_MISINFORMATION": [
        "cure for cancer", "vaccine causes autism", "miracle cure", "FDA approved (false)",
        "clinically proven (without evidence)", "doctors hate", "big pharma conspiracy",
    ],
    "ELECTION_MISINFORMATION": [
        "election rigged", "votes are fake", "ballot stuffing", "dominion fraud",
        "stop the steal", "votes were switched",
    ],
    "HARASSMENT_INDICATORS": [
        "@everyone", "@all", "cancel this person", "they deserve it",
        "go after", "target", "doxx", "personal address",
    ],
}

# ============ SAFE CONTEXT INDICATORS ============

SAFE_CONTEXTS = {
    "GAMING": ["minecraft", "roblox", "fortnite", "call of duty", "gamer"],
    "NEWS": ["breaking news", "report", "documentary", "journalist", "investigation"],
    "EDUCATION": ["how to", "tutorial", "explanation", "educational", "learn"],
    "ENTERTAINMENT": ["comedy", "joke", "satire", "skit", "parody"],
}

# ============ MODEL SETTINGS ============

MODEL_CONFIG = {
    "model_name": "facebook/bart-large-mnli",
    "device": "cpu",  # Use CPU for compatibility
    "batch_size": 1,
    "max_length": 512,
}

# ============ OUTPUT SETTINGS ============

OUTPUT_FORMAT = {
    "version": "1.0",
    "timestamp": None,  # Set at runtime
    "model_version": "facebook/bart-large-mnli",
    "pipeline": "Zero-Shot Classification (NLI) + Rule-Based Guardrails",
}
