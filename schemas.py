"""
Pydantic data models for input validation and output serialization
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime

# ============ INPUT SCHEMA ============

class ShortMetadata(BaseModel):
    """Input schema for YouTube Shorts"""

    short_id: str = Field(..., description="Unique video ID")
    title: str = Field(..., description="Video title")
    description: str = Field(default="", description="Video description")
    transcript: str = Field(default="", description="Video transcript/captions")
    top_comments: List[str] = Field(default_factory=list, description="Top 3-5 comments")
    duration_seconds: int = Field(default=60, description="Video duration in seconds")
    view_count: int = Field(default=0, description="Total views")
    upload_date: str = Field(..., description="Upload timestamp")
    channel_name: str = Field(default="Unknown", description="Channel name")
    language: str = Field(default="en", description="Language code")

    @validator("title", "description", "transcript")
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator("duration_seconds")
    def validate_duration(cls, v):
        if v <= 0 or v > 3600:  # Max 1 hour
            raise ValueError("Duration must be between 1 and 3600 seconds")
        return v

    class Config:
        schema_extra = {
            "example": {
                "short_id": "VideoID_123",
                "title": "Unbelievable trick to get free money now!!",
                "description": "Click the link in bio. Guaranteed returns.",
                "transcript": "Hey guys, do you want to double your savings...",
                "top_comments": ["This is a scam", "Reported."],
                "duration_seconds": 59,
                "view_count": 1500,
                "upload_date": "2023-10-27T10:00:00Z",
                "channel_name": "CryptoKing_X",
                "language": "en"
            }
        }

# ============ OUTPUT SCHEMA ============

class CategoryScore(BaseModel):
    """Per-category risk assessment"""
    risk_level: str = Field(..., description="LOW/MEDIUM/HIGH")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence 0-1")
    evidence: List[str] = Field(default_factory=list, description="Supporting phrases")

class ModerationResult(BaseModel):
    """Final moderation decision"""

    short_id: str
    overall_decision: str = Field(..., description="APPROVED/REMOVE/AGE_RESTRICT/ESCALATE_TO_HUMAN/NEED_MORE_CONTEXT")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    primary_violation: Optional[str] = Field(default=None, description="Category with highest score")
    categories: Dict[str, CategoryScore]
    action_recommendation: str
    escalation_priority: str = Field(..., description="P0/P1/P2/P3")
    notes_for_human_reviewer: str
    processing_timestamp: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "short_id": "VideoID_123",
                "overall_decision": "REMOVE",
                "confidence_score": 0.92,
                "primary_violation": "SCAM_SPAM",
                "categories": {
                    "SCAM_SPAM": {
                        "risk_level": "HIGH",
                        "score": 0.92,
                        "evidence": ["free money", "guaranteed returns"]
                    }
                },
                "action_recommendation": "BLOCK_AND_REPORT",
                "escalation_priority": "P2",
                "notes_for_human_reviewer": "High confidence scam detected"
            }
        }

# ============ BATCH PROCESSING ============

class BatchInput(BaseModel):
    """Batch of Shorts for processing"""
    shorts: List[ShortMetadata]
    batch_id: Optional[str] = None

class BatchOutput(BaseModel):
    """Batch processing results"""
    batch_id: str
    processing_timestamp: str
    total_processed: int
    results: List[ModerationResult]
    summary_stats: Dict[str, int]
