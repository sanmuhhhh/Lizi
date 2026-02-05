# Memory Index Cache

This directory contains cached embedding vectors for semantic memory search.

## Files

- `embeddings.npy` - NumPy array of embedding vectors (384 dimensions each)
- `chunks.json` - Metadata for each embedded text chunk (source file, section, text)

## Regeneration

These files are automatically rebuilt when:
1. Memory files (*.md) are modified
2. The `recalling` tool detects stale index via mtime comparison

To manually rebuild, delete these files and run any semantic search.

## Size

Typical size: ~1-2 MB for ~400 lines of memories.
