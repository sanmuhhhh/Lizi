#!/usr/bin/env python3
"""Embedding utilities for semantic memory search."""

import os
import re
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Lazy-loaded model
_model = None


def load_model():
    """Load SentenceTransformer model (lazy, cached)."""
    global _model
    if _model is None:
        # Set offline mode if model already cached
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def chunk_markdown(
    text: str,
    source_file: str = "unknown",
    category: str = "unknown",
    max_chars: int = 500,
) -> List[Dict]:
    """
    Split markdown text into chunks by ## headers.
    Long sections are recursively split.

    Returns list of dicts with keys:
    - text: chunk content
    - source: source filename
    - category: memory category
    - section: header hierarchy (e.g., "Work > Projects")
    - char_range: (start, end) tuple
    """
    chunks = []

    # Split by ## headers
    sections = re.split(r"\n(?=## )", text)

    current_pos = 0
    header_stack = []

    for section in sections:
        section = section.strip()
        if not section:
            current_pos += 1
            continue

        # Skip top-level # headers (file title)
        if section.startswith("# ") and not section.startswith("## "):
            current_pos += len(section) + 1
            continue

        # Extract header if present
        lines = section.split("\n", 1)
        header = ""
        content = section

        if lines[0].startswith("## "):
            header = lines[0][3:].strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            # Track header hierarchy
            header_stack = [header]  # Reset for ## level
        elif lines[0].startswith("### "):
            header = lines[0][4:].strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            if header_stack:
                header_stack = [header_stack[0], header]
            else:
                header_stack = [header]

        section_path = " > ".join(header_stack) if header_stack else "Untitled"

        # Handle long sections by splitting
        if len(section) > max_chars:
            sub_chunks = _split_long_text(section, max_chars)
            for i, sub_chunk in enumerate(sub_chunks):
                chunks.append(
                    {
                        "text": sub_chunk.strip(),
                        "source": source_file,
                        "category": category,
                        "section": f"{section_path} (part {i + 1})"
                        if len(sub_chunks) > 1
                        else section_path,
                        "char_range": (current_pos, current_pos + len(sub_chunk)),
                    }
                )
                current_pos += len(sub_chunk)
        else:
            if section.strip():
                chunks.append(
                    {
                        "text": section.strip(),
                        "source": source_file,
                        "category": category,
                        "section": section_path,
                        "char_range": (current_pos, current_pos + len(section)),
                    }
                )

        current_pos += len(section) + 1

    # Remove exact duplicates within file
    seen = set()
    unique_chunks = []
    for chunk in chunks:
        text_hash = hash(chunk["text"])
        if text_hash not in seen:
            seen.add(text_hash)
            unique_chunks.append(chunk)

    return unique_chunks


def _split_long_text(text: str, max_chars: int) -> List[str]:
    """Split long text at paragraph/sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""

    # Split by paragraphs first
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            # If single paragraph is too long, split by sentences
            if len(para) > max_chars:
                sentences = re.split(r"(?<=[.!?。！？])\s+", para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_chars:
                        current += (" " if current else "") + sent
                    else:
                        if current:
                            chunks.append(current)
                        current = sent
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


def generate_embeddings(texts: List[str], show_progress: bool = True) -> np.ndarray:
    """Generate embeddings for a list of texts."""
    model = load_model()
    embeddings = model.encode(
        texts, show_progress_bar=show_progress, convert_to_numpy=True
    )
    return embeddings.astype(np.float32)


def save_index(index_dir: str, embeddings: np.ndarray, chunks: List[Dict]) -> None:
    """Save embeddings and chunk metadata to disk."""
    index_path = Path(index_dir)
    index_path.mkdir(parents=True, exist_ok=True)

    np.save(index_path / "embeddings.npy", embeddings)

    with open(index_path / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def load_index(index_dir: str) -> Optional[Dict]:
    """Load embeddings and chunks from disk. Returns None if not found."""
    index_path = Path(index_dir)
    embeddings_file = index_path / "embeddings.npy"
    chunks_file = index_path / "chunks.json"

    if not embeddings_file.exists() or not chunks_file.exists():
        return None

    try:
        embeddings = np.load(embeddings_file)
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        return {"embeddings": embeddings, "chunks": chunks}
    except Exception as e:
        print(f"Warning: Failed to load index: {e}")
        return None


def is_index_stale(index_dir: str, memory_files: List[str]) -> bool:
    """Check if index is older than any memory file."""
    index_path = Path(index_dir)
    embeddings_file = index_path / "embeddings.npy"

    if not embeddings_file.exists():
        return True

    index_mtime = embeddings_file.stat().st_mtime

    for mem_file in memory_files:
        if Path(mem_file).exists():
            if Path(mem_file).stat().st_mtime > index_mtime:
                return True

    return False


def get_memory_files(memories_dir: str) -> List[str]:
    """Get list of long-term memory files."""
    categories = ["work", "hobby", "invest", "learning", "life", "thoughts", "projects"]
    return [str(Path(memories_dir) / f"{cat}.md") for cat in categories]


def build_index(memories_dir: str, index_dir: str) -> Dict:
    """Build complete index from all memory files."""
    memory_files = get_memory_files(memories_dir)
    all_chunks = []

    for mem_file in memory_files:
        file_path = Path(mem_file)
        if file_path.exists():
            category = file_path.stem
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            chunks = chunk_markdown(
                content, source_file=file_path.name, category=category
            )
            all_chunks.extend(chunks)

    if not all_chunks:
        return {"embeddings": np.array([]), "chunks": []}

    print(f"Generating embeddings for {len(all_chunks)} chunks...")
    texts = [c["text"] for c in all_chunks]
    embeddings = generate_embeddings(texts)

    save_index(index_dir, embeddings, all_chunks)
    print(f"Index saved: {len(all_chunks)} chunks, {embeddings.shape}")

    return {"embeddings": embeddings, "chunks": all_chunks}


def semantic_search(
    query: str,
    embeddings: np.ndarray,
    chunks: List[Dict],
    top_k: int = 5,
    threshold: float = 0.3,
) -> List[Dict]:
    """Search for similar chunks using cosine similarity."""
    from sklearn.metrics.pairwise import cosine_similarity

    model = load_model()
    query_embedding = model.encode([query], convert_to_numpy=True)

    similarities = cosine_similarity(query_embedding, embeddings)[0]

    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = float(similarities[idx])
        if score >= threshold:
            result = chunks[idx].copy()
            result["score"] = score
            results.append(result)

    return results


def calculate_chunk_importance(
    chunk: Dict,
    access_log: Dict,
    semantic_score: float = 0.5,
    recent_messages: Optional[List[str]] = None,
) -> float:
    """
    Calculate importance score for a memory chunk using access log data.

    Args:
        chunk: Chunk dict with 'text' and optionally 'hash' or computed hash
        access_log: Dict mapping chunk_hash -> access record
        semantic_score: Current semantic similarity score (from search)
        recent_messages: Last few user messages for context relevance

    Returns:
        Float importance score in range [0.1, 1.0]
    """
    from importance import (
        recency_factor,
        access_frequency_factor,
        semantic_similarity_factor,
        explicit_priority_factor,
        context_relevance_factor,
        calculate_importance,
    )

    # Get or compute chunk hash
    chunk_hash = chunk.get("hash") or str(hash(chunk.get("text", "")))

    # Get access record (default values if not found)
    access_record = access_log.get(chunk_hash, {})

    # Calculate days since last access
    last_access_str = access_record.get("last_access")
    if last_access_str:
        try:
            last_access = datetime.fromisoformat(last_access_str)
            days_ago = (datetime.now() - last_access).total_seconds() / 86400
        except (ValueError, TypeError):
            days_ago = 30  # Default if parse fails
    else:
        days_ago = 30  # Default for never-accessed chunks

    # Get other factors
    access_count = access_record.get("access_count", 0)
    base_importance = access_record.get("base_importance", 0.5)

    # Calculate all factors
    recency = recency_factor(days_ago)
    frequency = access_frequency_factor(access_count)
    semantic = semantic_similarity_factor(semantic_score)
    explicit = explicit_priority_factor(base_importance)
    context = context_relevance_factor(chunk.get("text", ""), recent_messages or [])

    return calculate_importance(recency, frequency, semantic, explicit, context)


if __name__ == "__main__":
    # Quick self-test
    print("Testing embedding_utils...")

    test_md = """# Test File
    
## Section 1
This is about semantic search implementation.

## Section 2  
Another topic about memory systems.
"""

    chunks = chunk_markdown(test_md, source_file="test.md", category="test")
    print(f"Chunks: {len(chunks)}")
    for c in chunks:
        print(f"  - {c['section']}: {c['text'][:50]}...")

    print("\nGenerating embeddings...")
    embeddings = generate_embeddings([c["text"] for c in chunks], show_progress=False)
    print(f"Embeddings shape: {embeddings.shape}")

    print("\nAll tests passed!")
