#!/usr/bin/env python3
"""
MCU Estimate Max Coverage Tool

估算文件的最大可达覆盖率，识别无法通过单元测试覆盖的代码块。
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/sanmu/MyProject/mcu_ctest/autosar-mcu")
PUBLIC_DIR = PROJECT_ROOT / "public"


BLOCKER_PATTERNS = [
    {
        "pattern": r"\bnew_\w+\s*\(",
        "category": "multiproc_required",
        "reason": "new_* 函数需要多进程测试",
        "uncoverable_lines": 5,
    },
    {
        "pattern": r"\bproxy_\w+\s*\(",
        "category": "multiproc_required",
        "reason": "proxy_* 代理实体需要远程对端",
        "uncoverable_lines": 3,
    },
    {
        "pattern": r"\bnn_xpack_\w+\s*\(",
        "category": "multiproc_required",
        "reason": "nn_xpack 消息打包需要网络交互",
        "uncoverable_lines": 2,
    },
    {
        "pattern": r"\bassert\s*\(\s*(false|0)\s*\)",
        "category": "defensive",
        "reason": "防御性断言，不应到达",
        "uncoverable_lines": 1,
    },
    {
        "pattern": r"DDS_FATAL|abort\s*\(\s*\)",
        "category": "defensive",
        "reason": "致命错误路径",
        "uncoverable_lines": 1,
    },
    {
        "pattern": r"#ifdef\s+(_WIN32|__APPLE__|LWIP_SOCKET)",
        "category": "platform_specific",
        "reason": "非 Linux 平台代码",
        "uncoverable_lines": 10,
    },
]


def find_source_file(file_name: str) -> Path | None:
    base_name = Path(file_name).name
    for src in PROJECT_ROOT.rglob(base_name):
        if src.is_file() and "/tests/" not in str(src) and "/build/" not in str(src):
            return src
    return None


def get_current_coverage(file_name: str) -> dict | None:
    from html.parser import HTMLParser

    class CoverageParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.line_coverage = 0.0
            self.branch_coverage = 0.0
            self.function_coverage = 0.0
            self._row_type = None
            self._capture = False
            self._text = ""

        def handle_starttag(self, tag, attrs):
            attrs_d = dict(attrs)
            if tag == "th" and attrs_d.get("scope") == "row":
                self._capture = True
                self._text = ""
            class_val = attrs_d.get("class") or ""
            if tag == "td" and "coverage-" in class_val:
                self._capture = True
                self._text = ""

        def handle_endtag(self, tag):
            if tag == "th" and self._capture:
                t = self._text.strip()
                if t == "Lines:":
                    self._row_type = "Lines"
                elif t == "Branches:":
                    self._row_type = "Branches"
                elif t == "Functions:":
                    self._row_type = "Functions"
                self._capture = False
            if tag == "td" and self._row_type:
                t = self._text.strip()
                if "%" in t:
                    try:
                        val = float(t.replace("%", ""))
                        if self._row_type == "Lines":
                            self.line_coverage = val
                        elif self._row_type == "Branches":
                            self.branch_coverage = val
                        elif self._row_type == "Functions":
                            self.function_coverage = val
                    except ValueError:
                        pass
                    self._row_type = None
                self._capture = False

        def handle_data(self, data):
            if self._capture:
                self._text += data

    base_name = Path(file_name).name
    for html_file in PUBLIC_DIR.glob(f"codecov.{base_name}.*.html"):
        parser = CoverageParser()
        parser.feed(html_file.read_text(encoding="utf-8"))
        return {
            "line_coverage": parser.line_coverage,
            "branch_coverage": parser.branch_coverage,
            "function_coverage": parser.function_coverage,
        }
    return None


def estimate_max_coverage(file_name: str) -> dict:
    src_path = find_source_file(file_name)
    if not src_path:
        return {"error": f"找不到源文件: {file_name}"}

    try:
        content = src_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        total_lines = len(
            [l for l in lines if l.strip() and not l.strip().startswith("//")]
        )
    except Exception as e:
        return {"error": f"读取源文件失败: {e}"}

    current = get_current_coverage(file_name)
    if not current:
        current = {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "function_coverage": 0.0,
        }

    blockers = []
    uncoverable_estimate = 0
    categories = {}

    for bp in BLOCKER_PATTERNS:
        matches = list(re.finditer(bp["pattern"], content))
        if matches:
            count = len(matches)
            lines_blocked = count * bp["uncoverable_lines"]
            uncoverable_estimate += lines_blocked

            cat = bp["category"]
            if cat not in categories:
                categories[cat] = {"count": 0, "lines": 0}
            categories[cat]["count"] += count
            categories[cat]["lines"] += lines_blocked

            blockers.append(
                {
                    "pattern": bp["pattern"],
                    "category": cat,
                    "occurrences": count,
                    "estimated_lines": lines_blocked,
                    "reason": bp["reason"],
                }
            )

    coverable_lines = max(1, total_lines - uncoverable_estimate)
    max_line_coverage = min(100.0, round((coverable_lines / total_lines) * 100, 1))

    max_branch_coverage = max_line_coverage * 0.85
    max_function_coverage = min(100.0, max_line_coverage + 5)

    return {
        "file": file_name,
        "total_code_lines": total_lines,
        "current": current,
        "estimated_max": {
            "line_coverage": max_line_coverage,
            "branch_coverage": round(max_branch_coverage, 1),
            "function_coverage": round(max_function_coverage, 1),
        },
        "uncoverable_lines_estimate": uncoverable_estimate,
        "blockers": blockers,
        "categories_summary": categories,
        "note": "估算值基于代码模式分析，实际值可能有偏差",
    }


def main():
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "用法: mcu_estimate_max_coverage.py <file_name>",
                    "example": "mcu_estimate_max_coverage.py q_transmit.c",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    result = estimate_max_coverage(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
