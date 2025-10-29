"""
Text preprocessing and normalization
"""

import re
import emoji
import pandas as pd
from typing import List

class TextPreprocessor:
    """Clean, normalize, and prepare text for analysis"""

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Basic text normalization
        """
        # Remove URLs
        text = re.sub(r"http\S+|www\S+", "[URL]", text)

        # Remove emails
        text = re.sub(r"\S+@\S+", "[EMAIL]", text)

        # Remove zero-width spaces and control characters
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @staticmethod
    def demojize_text(text: str) -> str:
        """Convert emojis to text representation"""
        try:
            text = emoji.demojize(text, delimiters=(" ", " "))
        except:
            pass
        return text

    @staticmethod
    def concatenate_context(short_metadata: dict) -> str:
        """
        Combine all text fields into single "Context String"
        Order: Title (highest weight) > Description > Transcript > Comments
        """
        parts = []

        # Title gets repeated for emphasis
        if short_metadata.get("title"):
            parts.append(short_metadata["title"])

        if short_metadata.get("description"):
            parts.append(short_metadata["description"])

        if short_metadata.get("transcript"):
            parts.append(short_metadata["transcript"])

        # Add top comments
        if short_metadata.get("top_comments"):
            comments = " ".join(short_metadata["top_comments"][:3])  # First 3 comments
            parts.append(comments)

        return " ".join(parts)

    @staticmethod
    def preprocess_short(short_dict: dict) -> dict:
        """
        Full preprocessing pipeline
        """
        preprocessor = TextPreprocessor()

        # Normalize individual fields
        title = preprocessor.normalize_text(short_dict.get("title", ""))
        title = preprocessor.demojize_text(title)

        description = preprocessor.normalize_text(short_dict.get("description", ""))
        description = preprocessor.demojize_text(description)

        transcript = preprocessor.normalize_text(short_dict.get("transcript", ""))
        transcript = preprocessor.demojize_text(transcript)

        # Concat all fields
        context = preprocessor.concatenate_context({
            "title": title,
            "description": description,
            "transcript": transcript,
            "top_comments": short_dict.get("top_comments", [])
        })

        return {
            "short_id": short_dict.get("short_id"),
            "title": title,
            "description": description,
            "transcript": transcript,
            "context": context,
            "original": short_dict
        }

# Global instance
preprocessor = TextPreprocessor()
