"""
Text Processing Utilities

Reusable text manipulation functions for:
- Truncation with ellipsis
- Sentence scoring and extraction
- Text cleaning and normalization
"""

import re

from app.config.settings import settings


def truncate_text(text: str, max_chars: int, add_ellipsis: bool = True) -> str:
    """
    Truncate text to specified length with optional ellipsis.

    """
    if not text or len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    return truncated + '...' if add_ellipsis else truncated


def calculate_sentence_score(position: int, length: int, total_sentences: int) -> float:
    """
    Calculate relevance score for a sentence based on position and length.
    Earlier sentences and longer sentences score higher.

    """
    # Earlier = more important
    position_weight = 1.0 / (position + 1)

    # Longer = more informative (capped at 1.0)
    length_weight = min(length / settings.TEXT_SENTENCE_WEIGHT_DENOMINATOR, 1.0)

    # Weighted combination
    score = (
        position_weight * settings.SENTENCE_SCORE_POSITION_WEIGHT
        + length_weight * settings.SENTENCE_SCORE_LENGTH_WEIGHT
    )

    return score


def extract_key_phrases(text: str, max_phrases: int = 5) -> list[str]:
    """
    Extract key phrases from text using pattern matching.

    """
    if not text:
        return []

    # Extract capitalized phrases (likely important terms/names)
    phrases = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text)

    # Deduplicate while preserving order
    seen = set()
    unique_phrases = []
    for phrase in phrases:
        phrase_lower = phrase.lower()
        if phrase_lower not in seen:
            seen.add(phrase_lower)
            unique_phrases.append(phrase)

    return unique_phrases[:max_phrases]


def split_into_sentences(text: str, min_length: int = None) -> list[str]:
    """
    Split text into sentences with optional minimum length filter.

    """
    if min_length is None:
        min_length = settings.TEXT_MIN_SENTENCE_LENGTH

    if not text:
        return []

    # Split by sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)

    # Filter and clean
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) >= min_length]

    return sentences


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text (collapse multiple spaces, normalize newlines).

    """
    if not text:
        return text

    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)

    # Replace multiple newlines with double newline
    text = re.sub(r'\n\n+', '\n\n', text)

    # Remove leading/trailing whitespace per line
    lines = [line.strip() for line in text.split('\n')]

    return '\n'.join(lines)


def create_preview(text: str, max_chars: int, context: str = '') -> str:
    """
    Create a contextual preview of text for logging.

    """
    preview = truncate_text(text, max_chars, add_ellipsis=True)

    if context:
        return f"{context}: '{preview}'"

    return preview
