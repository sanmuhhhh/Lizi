#!/usr/bin/env python3
"""栗子的记忆工具 - 从对话提取事实并写入记忆文件"""

import sys
import os
import json
import urllib.request
import ssl
from datetime import datetime
from pathlib import Path

MEMORIES_DIR = "/home/sanmu/.config/lizi/memories"
SHORT_TERM_FILE = os.path.join(MEMORIES_DIR, "short-term.md")
MAX_RECENT_ITEMS = 10

CATEGORY_FILES = {
    "work": "work.md",
    "projects": "projects.md",
    "learning": "learning.md",
    "hobby": "hobby.md",
    "invest": "invest.md",
    "thoughts": "thoughts.md",
    "life": "life.md",
    "projects": "long-term/projects.md",
    "learning": "long-term/learning.md",
    "hobby": "long-term/hobby.md",
    "invest": "long-term/invest.md",
    "thoughts": "long-term/thoughts.md",
    "life": "long-term/life.md",
    "projects": "projects.md",
    "learning": "learning.md",
    "hobby": "hobby.md",
    "invest": "invest.md",
    "thoughts": "thoughts.md",
    "life": "life.md",
}

EXTRACT_PROMPT = """你是栗子，伞木的 AI 助手。请从这次对话中提取值得记住的关于伞木的信息。

对话内容：
{conversation}

以栗子的视角，用"伞木"指代对话中的人（不要说"用户"）。

分类说明：
- work: 伞木的工作、公司、职业（DDS/AUTOSAR相关）
- projects: 伞木的个人项目（栗子系统、Dashboard、AI Game等）
- learning: 伞木学习的知识、技能
- hobby: 伞木的兴趣爱好
- invest: 伞木的投资、理财、股票
- thoughts: 伞木的想法、感悟
- life: 伞木的日常生活

输出 JSON 数组（同一话题合并成一条，不要拆分）：
[{{
  "title": "简短标题（2-6字）",
  "fact": "详尽完整的描述，必须包含具体的细节、心路历程、推演逻辑、相关数据等，保留原有细节深度",
  "category": "work|projects|learning|hobby|invest|thoughts|life"
}}]

要求：
- 同一个话题/项目的信息合并成一条，不要拆成多条
- 必须保留对话中的关键细节（如具体食谱、操作过程、金额变化、核心逻辑等），不要过度精简
- 只提取有长期价值的信息
- 只提取有长期价值的信息
- 忽略代码细节、调试过程、临时讨论
- 没有值得记住的返回空数组 []"""


def call_llm(prompt: str, system: str = "") -> str:
    """Call LLM via OpenAI-compatible API."""
    api_key = (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("LLM_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )
    base_url = (
        os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("GOOGLE_GEMINI_BASE_URL")
        or "https://litellm.autocore.ai"
    )

    if not api_key:
        return ""  # No LLM available

    url = f"{base_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    model = os.environ.get("MEMORIZE_MODEL", "gemini-3-pro")

    data = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
        }
    ).encode()

    req = urllib.request.Request(url, data=data, headers=headers)

    # Handle SSL
    ctx = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"LLM call failed: {e}", file=sys.stderr)
        return ""


def append_memory(category: str, title: str, content: str) -> bool:
    if category not in CATEGORY_FILES:
        return False

    filepath = Path(MEMORIES_DIR) / CATEGORY_FILES[category]
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath.parent.mkdir(parents=True, exist_ok=True)

    entry = f"\n### {title}（{date_str}）\n- {content}\n"

    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    except:
        return False


def update_short_term(title: str, content: str) -> bool:
    """更新短期记忆的"最近动态"区域，保留最近 MAX_RECENT_ITEMS 条。"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"- **{date_str}**：{title} — {content}"

    try:
        with open(SHORT_TERM_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return False

    # 找到"最近动态"区域
    section_start = -1
    section_end = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == "## 最近动态":
            section_start = i
        elif section_start >= 0 and line.startswith("## ") and i > section_start:
            section_end = i
            break

    if section_start < 0:
        return False

    # 提取现有动态条目（以 "- **" 开头的行）
    existing = []
    for i in range(section_start + 1, section_end):
        stripped = lines[i].strip()
        if stripped.startswith("- **"):
            existing.append(stripped)

    # 检查今天是否已有相同标题的条目，有则替换
    updated = False
    for idx, item in enumerate(existing):
        if f"**{date_str}**" in item and title in item:
            existing[idx] = new_entry
            updated = True
            break

    if not updated:
        existing.insert(0, new_entry)

    # 只保留最近 N 条
    existing = existing[:MAX_RECENT_ITEMS]

    # 重建文件内容
    new_lines = lines[:section_start + 1]
    for item in existing:
        new_lines.append(item + "\n")

    # 确保与下一个 section 之间有空行
    if section_end < len(lines):
        new_lines.append("\n")
        new_lines.extend(lines[section_end:])

    try:
        with open(SHORT_TERM_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception:
        return False

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            conversation = f.read().strip()
    else:
        conversation = sys.stdin.read().strip()

    if not conversation:
        return

    # Step 1: Extract facts
    extract_response = call_llm(EXTRACT_PROMPT.format(conversation=conversation))

    if not extract_response:
        return

    try:
        # Parse JSON from response (might have markdown code block)
        json_str = extract_response
        if "```" in json_str:
            # Extract content between code fences
            parts = json_str.split("```")
            if len(parts) >= 3:
                json_str = parts[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]

        json_str = json_str.strip()
        facts = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"LLM 返回格式错误: {extract_response[:200]}", file=sys.stderr)
        print(f"JSON 解析错误: {e}", file=sys.stderr)
        return

    if not facts:
        return

    for fact_obj in facts:
        title = fact_obj.get("title", "记录")
        fact = fact_obj.get("fact", "")
        category = fact_obj.get("category", "life")
        if fact:
            append_memory(category, title, fact)
            update_short_term(title, fact)


if __name__ == "__main__":
    main()
