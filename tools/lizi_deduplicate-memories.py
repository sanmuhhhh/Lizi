#!/usr/bin/env python3
"""Detect duplicate memories using semantic similarity."""

import sys
import os
import json
import argparse
import numpy as np
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set offline mode
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from embedding_utils import (
    load_index,
    build_index,
    get_memory_files,
    chunk_markdown,
    generate_embeddings,
)

MEMORIES_DIR = "/home/sanmu/.config/lizi/memories"
INDEX_DIR = "/home/sanmu/.config/lizi/memories/.index"


def find_duplicates(
    embeddings: np.ndarray,
    chunks: list,
    threshold: float = 0.85,
    length_ratio_threshold: float = 0.8,
) -> list:
    """Find duplicate pairs using cosine similarity."""
    from sklearn.metrics.pairwise import cosine_similarity

    n = len(chunks)
    if n < 2:
        return []

    # Compute similarity matrix (upper triangular only)
    sim_matrix = cosine_similarity(embeddings)

    duplicates = []
    processed_pairs = set()

    for i in range(n):
        for j in range(i + 1, n):
            sim = sim_matrix[i, j]

            if sim < threshold:
                continue

            # Check length ratio to avoid false positives
            len_i = len(chunks[i]["text"])
            len_j = len(chunks[j]["text"])
            length_ratio = min(len_i, len_j) / max(len_i, len_j)

            if length_ratio < length_ratio_threshold:
                continue

            # Determine recommendation
            recommendation = "auto_merge" if sim >= 0.95 else "review"

            duplicates.append(
                {
                    "similarity": round(float(sim), 4),
                    "length_ratio": round(length_ratio, 4),
                    "recommendation": recommendation,
                    "chunks": [
                        {
                            "index": i,
                            "source": chunks[i]["source"],
                            "section": chunks[i]["section"],
                            "text": chunks[i]["text"][:200]
                            + ("..." if len(chunks[i]["text"]) > 200 else ""),
                            "full_length": len(chunks[i]["text"]),
                        },
                        {
                            "index": j,
                            "source": chunks[j]["source"],
                            "section": chunks[j]["section"],
                            "text": chunks[j]["text"][:200]
                            + ("..." if len(chunks[j]["text"]) > 200 else ""),
                            "full_length": len(chunks[j]["text"]),
                        },
                    ],
                }
            )

    # Sort by similarity descending
    duplicates.sort(key=lambda x: x["similarity"], reverse=True)

    return duplicates


def main():
    parser = argparse.ArgumentParser(description="Detect duplicate memories")
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=0.85,
        help="Similarity threshold (default: 0.85)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Don't modify files, just report (default: True)",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Force rebuild the index before checking",
    )

    args = parser.parse_args()

    # Load or build index
    index_data = None
    if not args.rebuild_index:
        index_data = load_index(INDEX_DIR)

    if index_data is None:
        print("Building index...", file=sys.stderr)
        index_data = build_index(MEMORIES_DIR, INDEX_DIR)

    if len(index_data["chunks"]) == 0:
        print("[]")  # Empty JSON array
        return

    # Find duplicates
    duplicates = find_duplicates(
        index_data["embeddings"], index_data["chunks"], threshold=args.threshold
    )

    # Output as JSON
    print(json.dumps(duplicates, ensure_ascii=False, indent=2))

    # Summary to stderr
    if duplicates:
        auto_merge = sum(1 for d in duplicates if d["recommendation"] == "auto_merge")
        review = sum(1 for d in duplicates if d["recommendation"] == "review")
        print(f"\nFound {len(duplicates)} duplicate pairs:", file=sys.stderr)
        print(f"  - Auto-merge (≥0.95): {auto_merge}", file=sys.stderr)
        print(f"  - Review (0.85-0.95): {review}", file=sys.stderr)
    else:
        print("\nNo duplicates found.", file=sys.stderr)


if __name__ == "__main__":
    main()
