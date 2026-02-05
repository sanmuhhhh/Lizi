#!/usr/bin/env python3
"""栗子的回忆工具 - 搜索长期记忆（支持关键词和语义搜索）"""

import sys
import os
import re
import random
import argparse
import json
import hashlib
from datetime import datetime
from typing import Dict

MEMORIES_DIR = "/home/sanmu/.config/lizi/memories"
INDEX_DIR = "/home/sanmu/.config/lizi/memories/.index"

ACCESS_LOG_PATH = os.path.join(INDEX_DIR, "access_log.json")
MAX_ACCESS_LOG_ENTRIES = 10000


def load_access_log() -> Dict:
    """Load access log from JSON, return {} if missing/corrupted."""
    try:
        if os.path.exists(ACCESS_LOG_PATH):
            with open(ACCESS_LOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def save_access_log(access_log: Dict) -> None:
    """Atomic save using temp file + rename."""
    temp_path = ACCESS_LOG_PATH + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(access_log, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, ACCESS_LOG_PATH)
    except IOError:
        # Silently fail - access log is non-critical
        if os.path.exists(temp_path):
            os.remove(temp_path)


def update_access_record(chunk_hash: str, access_log: Dict) -> None:
    """Update last_access and access_count for a chunk."""
    now = datetime.now().isoformat()
    if chunk_hash in access_log:
        access_log[chunk_hash]["last_access"] = now
        access_log[chunk_hash]["access_count"] += 1
    else:
        access_log[chunk_hash] = {
            "last_access": now,
            "access_count": 1,
            "base_importance": 0.5,
            "created_at": now,
        }


def prune_access_log(access_log: Dict) -> Dict:
    """Keep only most recent MAX_ACCESS_LOG_ENTRIES, FIFO removal."""
    if len(access_log) <= MAX_ACCESS_LOG_ENTRIES:
        return access_log

    # Sort by last_access, keep newest
    sorted_items = sorted(
        access_log.items(), key=lambda x: x[1].get("last_access", ""), reverse=True
    )
    return dict(sorted_items[:MAX_ACCESS_LOG_ENTRIES])


# 长期记忆文件（不包括短期记忆）
LONG_TERM_FILES = [
    "work.md",
    "hobby.md",
    "invest.md",
    "learning.md",
    "life.md",
    "thoughts.md",
    "projects.md",
]


def get_all_sections():
    """获取所有记忆片段"""
    all_sections = []

    for filename in LONG_TERM_FILES:
        filepath = os.path.join(MEMORIES_DIR, filename)
        if not os.path.exists(filepath):
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 按段落分割（以 ## 开头的标题为分隔）
        sections = re.split(r"\n(?=## )", content)
        category = filename.replace(".md", "")

        for section in sections:
            section = section.strip()
            if section and not section.startswith("# "):  # 跳过一级标题
                all_sections.append(f"【{category}】\n{section}")

    return all_sections


def search_memories(keyword):
    """搜索包含关键词的记忆片段"""
    results = []
    keyword_lower = keyword.lower()

    for section in get_all_sections():
        if keyword_lower in section.lower():
            results.append(section)

    return results


def random_memory():
    """随机返回一段记忆"""
    all_sections = get_all_sections()
    if all_sections:
        return random.choice(all_sections)
    return None


def semantic_search_memories(query, top_k=5):
    """使用语义搜索查找相关记忆（含重要性排序）"""
    try:
        from embedding_utils import (
            load_index,
            is_index_stale,
            build_index,
            semantic_search,
            get_memory_files,
        )
    except ImportError:
        # 尝试从同目录导入
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from embedding_utils import (
            load_index,
            is_index_stale,
            build_index,
            semantic_search,
            get_memory_files,
        )

    # 检查索引是否存在且有效
    memory_files = get_memory_files(MEMORIES_DIR)

    if is_index_stale(INDEX_DIR, memory_files):
        print("索引需要更新，正在重建...", file=sys.stderr)
        index_data = build_index(MEMORIES_DIR, INDEX_DIR)
    else:
        index_data = load_index(INDEX_DIR)

    if index_data is None or len(index_data.get("chunks", [])) == 0:
        print("索引为空或无法加载，尝试重建...", file=sys.stderr)
        index_data = build_index(MEMORIES_DIR, INDEX_DIR)

    if index_data is None or len(index_data.get("chunks", [])) == 0:
        return []

    access_log = load_access_log()

    results = semantic_search(
        query,
        index_data["embeddings"],
        index_data["chunks"],
        top_k=top_k * 2,
        threshold=0.3,
    )

    from embedding_utils import calculate_chunk_importance

    ranked_results = []
    for r in results:
        chunk_hash = hashlib.sha256(r.get("text", "").encode()).hexdigest()[:16]

        importance = calculate_chunk_importance(
            {"text": r.get("text", ""), "hash": chunk_hash},
            access_log,
            semantic_score=r.get("score", 0.5),
        )

        combined_score = importance

        update_access_record(chunk_hash, access_log)

        ranked_results.append(
            {**r, "importance": importance, "combined_score": combined_score}
        )

    ranked_results.sort(key=lambda x: x["combined_score"], reverse=True)

    access_log = prune_access_log(access_log)
    save_access_log(access_log)  # Don't reassign - function returns None

    top_results = ranked_results[:top_k]

    formatted_results = []
    for r in top_results:
        category = r.get("category", "unknown")
        text = r.get("text", "")
        formatted_results.append(f"【{category}】{r.get('section', '')}\n{text}")

    return formatted_results


def main():
    parser = argparse.ArgumentParser(description="栗子的回忆工具")
    parser.add_argument("keyword", nargs="*", help="搜索关键词")
    parser.add_argument(
        "--mode",
        choices=["keyword", "semantic", "auto"],
        default="keyword",
        help="搜索模式: keyword(默认), semantic(语义), auto(智能)",
    )

    args = parser.parse_args()

    if not args.keyword:
        # 没有参数，随机回忆
        memory = random_memory()
        if memory:
            print("突然想起来...\n")
            print(memory)
        else:
            print("脑袋空空的，什么都想不起来")
        return

    keyword = " ".join(args.keyword)
    mode = args.mode

    if mode == "keyword":
        results = search_memories(keyword)
        if results:
            print(f"找到 {len(results)} 条相关记忆：\n")
            print("\n---\n".join(results))
        else:
            print(f"没有找到关于「{keyword}」的记忆")

    elif mode == "semantic":
        results = semantic_search_memories(keyword)
        if results:
            print(f"找到 {len(results)} 条语义相关记忆：\n")
            print("\n---\n".join(results))
        else:
            print(f"没有找到与「{keyword}」语义相关的记忆")

    elif mode == "auto":
        # 智能模式：先关键词搜索，结果不足时补充语义搜索
        keyword_results = search_memories(keyword)

        if len(keyword_results) >= 2:
            # 关键词结果足够
            print(f"找到 {len(keyword_results)} 条相关记忆：\n")
            print("\n---\n".join(keyword_results))
        else:
            # 需要语义搜索补充
            semantic_results = semantic_search_memories(keyword)

            # 合并去重（基于文本内容）
            seen_texts = set()
            all_results = []

            for r in keyword_results:
                text_key = r.strip()
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    all_results.append(r)

            for r in semantic_results:
                text_key = r.strip()
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    all_results.append(r)

            if all_results:
                kw_count = len(keyword_results)
                sem_count = len(all_results) - kw_count
                print(
                    f"找到 {len(all_results)} 条记忆（关键词{kw_count}条，语义{sem_count}条）：\n"
                )
                print("\n---\n".join(all_results))
            else:
                print(f"没有找到关于「{keyword}」的记忆")


if __name__ == "__main__":
    main()
