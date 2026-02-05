#!/usr/bin/env python3
"""Memory importance calculation module for semantic memory system."""

import math
from typing import List, Optional


def recency_factor(days_ago: float) -> float:
    """
    Calculate recency factor using exponential decay.
    Formula: 0.5^(days_ago/7) - 7-day half-life

    Args:
        days_ago: Number of days since last access (can be fractional)

    Returns:
        Float in range [0, 1], where 1.0 = today, 0.5 = 7 days ago
    """
    # Clamp negative values to 0
    days = max(0, days_ago)
    return 0.5 ** (days / 7)


def access_frequency_factor(access_count: int) -> float:
    """
    Calculate access frequency factor using logarithmic scaling.
    Formula: min(1.0, log(access_count + 1) / 5)

    Args:
        access_count: Number of times this memory has been accessed

    Returns:
        Float in range [0, 1], capped at 1.0
    """
    # Treat negative counts as 0
    count = max(0, access_count)
    return min(1.0, math.log(count + 1) / 5)


def semantic_similarity_factor(similarity: float) -> float:
    """
    Pass-through for semantic similarity score.

    Args:
        similarity: Cosine similarity score from semantic search [0, 1]

    Returns:
        Same value (pass-through)
    """
    return similarity


def explicit_priority_factor(priority: Optional[float] = None) -> float:
    """
    Return explicit user-set priority or default.

    Args:
        priority: User-set priority (0-1) or None for default

    Returns:
        Priority value, default 0.5 if not set
    """
    if priority is None:
        return 0.5
    return priority


def context_relevance_factor(chunk_text: str, recent_messages: List[str]) -> float:
    """
    Calculate relevance to current conversation context via keyword matching.

    Args:
        chunk_text: The memory chunk text
        recent_messages: Last 3 user messages for context

    Returns:
        Float in range [0, 1] based on keyword overlap
    """
    # Normalize and extract words from chunk
    chunk_words = set(chunk_text.lower().split())

    # Extract words from recent messages
    context_words = set()
    for message in recent_messages:
        context_words.update(message.lower().split())

    # Calculate overlap ratio
    if not chunk_words or not context_words:
        return 0.0

    overlap = len(chunk_words & context_words)
    total = len(chunk_words | context_words)

    if total == 0:
        return 0.0

    return overlap / total


def calculate_importance(
    recency: float, frequency: float, semantic: float, explicit: float, context: float
) -> float:
    """
    Calculate combined importance score using weighted factors.

    Weights:
    - recency: 30%
    - frequency: 20%
    - semantic: 20%
    - explicit: 20%
    - context: 10%

    Args:
        recency: Recency factor [0, 1]
        frequency: Access frequency factor [0, 1]
        semantic: Semantic similarity factor [0, 1]
        explicit: Explicit priority factor [0, 1]
        context: Context relevance factor [0, 1]

    Returns:
        Combined importance score, clamped to [0.1, 1.0]
        Minimum 0.1 ensures memories never completely decay
    """
    weighted_sum = (
        recency * 0.30
        + frequency * 0.20
        + semantic * 0.20
        + explicit * 0.20
        + context * 0.10
    )

    # Clamp to [0.1, 1.0]
    return max(0.1, min(1.0, weighted_sum))
