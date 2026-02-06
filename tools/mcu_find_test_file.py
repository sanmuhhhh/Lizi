#!/usr/bin/env python3
"""
MCU Find Test File Tool

根据源文件查找已有的测试文件，并推荐应该追加测试的位置。
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path("/home/sanmu/MyProject/mcu_ctest/autosar-mcu")
TESTS_DIR = PROJECT_ROOT / "tests"


def extract_module_name(source_file: str) -> str:
    """从源文件名提取模块名"""
    base = Path(source_file).stem
    base = re.sub(r"^dds_|^ddsi_|^ddsrt_", "", base)
    return base


def find_related_test_files(source_file: str) -> list[dict]:
    """查找与源文件相关的测试文件"""
    base_name = Path(source_file).stem
    module_name = extract_module_name(source_file)

    related = []

    if not TESTS_DIR.exists():
        return related

    for test_file in TESTS_DIR.glob("*.c"):
        content = test_file.read_text(encoding="utf-8", errors="ignore")

        relevance = 0
        suites = []

        if base_name in test_file.stem:
            relevance += 10

        if (
            f'#include "{source_file}"' in content
            or f'#include "../src/' in content
            and base_name in content
        ):
            relevance += 5

        suite_matches = re.findall(r"CU_Test\s*\(\s*(\w+)\s*,", content)
        unique_suites = list(set(suite_matches))

        for suite in unique_suites:
            if (
                base_name.lower() in suite.lower()
                or module_name.lower() in suite.lower()
            ):
                relevance += 3
                suites.append(suite)

        if relevance > 0:
            related.append(
                {
                    "file": test_file.name,
                    "path": str(test_file.relative_to(PROJECT_ROOT)),
                    "suites": suites if suites else unique_suites[:5],
                    "relevance": relevance,
                }
            )

    related.sort(key=lambda x: x["relevance"], reverse=True)
    return related


def analyze_multiproc_need(source_file: str) -> dict | None:
    src_path = find_source_path(source_file)
    if not src_path:
        return None

    try:
        content = src_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    MULTIPROC_PATTERNS = [
        (r"\bnew_\w+\s*\(", "new_* 函数创建实体"),
        (r"\bproxy_\w+\s*\(", "proxy_* 代理实体操作"),
        (r"\bnn_xpack_\w+\s*\(", "nn_xpack 消息打包"),
        (r"\bremote_\w+\s*\(", "remote_* 远程实体"),
        (r"\bdds_get_matched_\w+\s*\(", "dds_get_matched_* 匹配查询"),
    ]

    detected = []
    for pattern, desc in MULTIPROC_PATTERNS:
        if re.search(pattern, content):
            detected.append(desc)

    if detected:
        return {
            "needs_multiproc": True,
            "patterns_found": detected,
            "multiproc_location": "examples/multiproc_test/",
            "hint": "部分代码路径需要多进程测试才能覆盖",
        }

    return None


def find_source_path(source_file: str) -> Path | None:
    base_name = Path(source_file).name
    for src in PROJECT_ROOT.rglob(base_name):
        if src.is_file() and "/tests/" not in str(src) and "/build/" not in str(src):
            return src
    return None


def get_recommendation(source_file: str, related_files: list[dict]) -> dict:
    base_name = Path(source_file).stem

    if related_files:
        best = related_files[0]
        return {
            "action": "append",
            "file": best["file"],
            "path": best["path"],
            "reason": f"已有相关测试文件，建议追加到现有 suite",
        }

    new_file = f"{base_name}_coverage.c"
    return {
        "action": "create",
        "file": new_file,
        "path": f"tests/{new_file}",
        "reason": "未找到相关测试文件，建议创建新的覆盖率测试文件",
        "suggested_suite": f"{base_name}_coverage",
    }


def main():
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "用法: mcu_find_test_file.py <source_file>",
                    "example": "mcu_find_test_file.py rpcserver.c",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    source_file = sys.argv[1]
    related = find_related_test_files(source_file)
    recommendation = get_recommendation(source_file, related)
    multiproc = analyze_multiproc_need(source_file)

    result = {
        "source_file": source_file,
        "existing_tests": related[:5],
        "recommendation": recommendation,
    }

    if multiproc:
        result["multiproc_analysis"] = multiproc

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
