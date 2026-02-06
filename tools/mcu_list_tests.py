#!/usr/bin/env python3
"""
MCU List Tests Tool

列出 CUnit 测试中的所有 suite 和 test。

支持两种解析模式：
1. 源码解析（默认）：直接从测试源文件解析 CU_Test(suite, test) 宏，最准确
2. 符号解析（备用）：从二进制符号表推断，可能不准确

用法:
    mcu_list_tests()                    # 列出所有测试
    mcu_list_tests(suite_filter="dds")  # 过滤包含 "dds" 的 suite
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path("/home/sanmu/MyProject/mcu_ctest/autosar-mcu")
TESTS_DIR = PROJECT_ROOT / "tests"
BINARY_PATH = PROJECT_ROOT / "build" / "bin" / "cunit_Ddscp"


def extract_tests_from_source() -> dict:
    """从测试源文件直接解析 CU_Test(suite, test) 宏"""
    if not TESTS_DIR.exists():
        return {"error": f"测试目录不存在: {TESTS_DIR}"}

    suites: dict[str, dict] = {}
    cu_test_pattern = re.compile(r"CU_Test\s*\(\s*(\w+)\s*,\s*(\w+)\s*[,)]")

    for test_file in TESTS_DIR.glob("*.c"):
        try:
            content = test_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for match in cu_test_pattern.finditer(content):
            suite_name = match.group(1)
            test_name = match.group(2)

            if suite_name not in suites:
                suites[suite_name] = {"tests": [], "source_file": test_file.name}

            if test_name not in suites[suite_name]["tests"]:
                suites[suite_name]["tests"].append(test_name)

    result_list = []
    for suite_name in sorted(suites.keys()):
        suite_data = suites[suite_name]
        result_list.append(
            {
                "name": suite_name,
                "tests": sorted(suite_data["tests"]),
                "test_count": len(suite_data["tests"]),
                "source_file": suite_data["source_file"],
                "run_example": f'./bin/cunit_Ddscp -s "{suite_name}"',
            }
        )

    return {
        "source": "tests/*.c",
        "method": "source_parsing",
        "total_suites": len(result_list),
        "total_tests": sum(s["test_count"] for s in result_list),
        "suites": result_list,
    }


def extract_tests_from_binary(binary_path: Path) -> dict:
    """
    从二进制文件的符号表中提取测试信息。
    备用方法，不如源码解析准确。
    """
    if not binary_path.exists():
        return {
            "error": f"二进制文件不存在: {binary_path}",
            "hint": "请先运行 cmake --build . --target cunit_Ddscp -j4",
        }

    # 优先使用源码解析
    source_result = extract_tests_from_source()
    if "error" not in source_result:
        return source_result

    # 回退到符号表解析
    try:
        result = subprocess.run(
            ["nm", "-C", str(binary_path)], capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        return {"error": "nm 命令超时"}
    except FileNotFoundError:
        return {"error": "nm 命令未找到，请安装 binutils"}

    if result.returncode != 0:
        return {"error": f"nm 命令失败: {result.stderr}"}

    # 获取源码中已知的 suite 名称，用于辅助解析
    known_suites = get_known_suites_from_source()

    pattern = re.compile(r"\b[Tt]\s+CU_Test_(.+)")
    suites = defaultdict(list)

    for line in result.stdout.splitlines():
        match = pattern.search(line)
        if match:
            full_name = match.group(1)
            suite_name, test_name = split_suite_test(full_name, known_suites)
            if test_name not in suites[suite_name]:
                suites[suite_name].append(test_name)

    result_list = []
    for suite_name in sorted(suites.keys()):
        result_list.append(
            {
                "name": suite_name,
                "tests": sorted(suites[suite_name]),
                "test_count": len(suites[suite_name]),
                "run_example": f'./bin/cunit_Ddscp -s "{suite_name}"',
            }
        )

    return {
        "binary": str(binary_path),
        "method": "symbol_parsing",
        "total_suites": len(result_list),
        "total_tests": sum(s["test_count"] for s in result_list),
        "suites": result_list,
    }


def get_known_suites_from_source() -> set:
    """从测试源文件中提取所有已知的 suite 名称"""
    suites = set()
    if not TESTS_DIR.exists():
        return suites

    cu_test_pattern = re.compile(r"CU_Test\s*\(\s*(\w+)\s*,")

    for test_file in TESTS_DIR.glob("*.c"):
        try:
            content = test_file.read_text(encoding="utf-8", errors="ignore")
            for match in cu_test_pattern.finditer(content):
                suites.add(match.group(1))
        except Exception:
            continue

    return suites


def split_suite_test(full_name: str, known_suites: set | None = None) -> tuple:
    """
    将 CU_Test_ 后的完整名称分割为 (suite, test)

    改进策略：
    1. 使用已知 suite 名称精确匹配
    2. 常见模式匹配
    3. 回退到最短前缀匹配
    """
    if known_suites is None:
        known_suites = set()

    # 策略 1: 使用已知 suite 名称匹配（最准确）
    # 按长度降序排列，优先匹配更长的 suite 名称
    for suite in sorted(known_suites, key=len, reverse=True):
        prefix = suite + "_"
        if full_name.startswith(prefix):
            test_name = full_name[len(prefix) :]
            if test_name:  # 确保 test 名称非空
                return suite, test_name

    # 策略 2: 已知的 suite 名称模式
    known_patterns = [
        r"^(branch_coverage\d*)_(.+)$",
        r"^(ddsi_\w+_coverage)_(.+)$",
        r"^(ddsi_\w+_test)_(.+)$",
        r"^(dds_\w+_coverage)_(.+)$",
        r"^(dds_\w+_test)_(.+)$",
        r"^(ddsrt_\w+)_(.+)$",
        r"^(q_\w+_coverage)_(.+)$",
        r"^(q_\w+_test)_(.+)$",
        r"^(notify_\w+?)_(.+)$",
        r"^(xevent_\w+?)_(.+)$",
    ]

    for pattern in known_patterns:
        match = re.match(pattern, full_name)
        if match:
            return match.group(1), match.group(2)

    # 策略 3: 寻找常见后缀
    for suffix in ["_coverage", "_test", "_static", "_inline"]:
        idx = full_name.find(suffix)
        if idx > 0:
            suite_end = idx + len(suffix)
            if suite_end < len(full_name) and full_name[suite_end] == "_":
                return full_name[:suite_end], full_name[suite_end + 1 :]

    # 策略 4: 回退到第一个下划线分割
    parts = full_name.split("_", 1)
    if len(parts) == 2:
        return parts[0], parts[1]

    return full_name, ""


def filter_suites(data: dict, suite_filter: str) -> dict:
    if "error" in data:
        return data

    if not suite_filter:
        return data

    filtered = [s for s in data["suites"] if suite_filter.lower() in s["name"].lower()]

    result = {
        "filter": suite_filter,
        "total_suites": len(filtered),
        "total_tests": sum(s["test_count"] for s in filtered),
        "suites": filtered,
    }

    if "source" in data:
        result["source"] = data["source"]
        result["method"] = data.get("method", "source_parsing")
    elif "binary" in data:
        result["binary"] = data["binary"]

    return result


def find_suites_in_file(test_file: Path) -> list[str]:
    """从测试文件中提取 suite 名称"""
    if not test_file.exists():
        return []

    content = test_file.read_text(encoding="utf-8", errors="ignore")
    suite_matches = re.findall(r"CU_Test\s*\(\s*(\w+)\s*,", content)
    return list(set(suite_matches))


def filter_by_file(data: dict, file_filter: str) -> dict:
    """按测试文件过滤，支持源文件名或测试文件名"""
    if "error" in data:
        return data

    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        return {"error": "tests 目录不存在"}

    matched_suites = set()
    matched_files = []
    filter_lower = file_filter.lower()
    filter_stem = Path(file_filter).stem.lower()

    for test_file in tests_dir.glob("*.c"):
        test_name = test_file.name.lower()
        test_stem = test_file.stem.lower()

        if filter_lower in test_name or filter_stem in test_stem:
            matched_files.append(test_file.name)
            suites = find_suites_in_file(test_file)
            matched_suites.update(suites)
            continue

        content = test_file.read_text(encoding="utf-8", errors="ignore")
        if f'#include "{file_filter}"' in content or f"/{filter_stem}." in content:
            matched_files.append(test_file.name)
            suites = find_suites_in_file(test_file)
            matched_suites.update(suites)

    if not matched_files:
        base_name = filter_stem
        for suite in data["suites"]:
            suite_lower = suite["name"].lower()
            if base_name in suite_lower:
                matched_suites.add(suite["name"])

        if matched_suites:
            filtered = [s for s in data["suites"] if s["name"] in matched_suites]
            result = {
                "file_filter": file_filter,
                "note": "通过 suite 名称模糊匹配",
                "total_suites": len(filtered),
                "total_tests": sum(s["test_count"] for s in filtered),
                "suites": filtered,
            }
            if "source" in data:
                result["source"] = data["source"]
            return result

        return {
            "file_filter": file_filter,
            "error": f"未找到匹配的测试文件: {file_filter}",
            "hint": "请检查 tests/ 目录中的文件名，或使用 suite_filter 参数",
        }

    filtered = [s for s in data["suites"] if s["name"] in matched_suites]

    result = {
        "file_filter": file_filter,
        "matched_files": matched_files,
        "total_suites": len(filtered),
        "total_tests": sum(s["test_count"] for s in filtered),
        "suites": filtered,
    }
    if "source" in data:
        result["source"] = data["source"]
    return result


def main():
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("suite_filter", nargs="?", help="Suite 名称过滤（部分匹配）")
    parser.add_argument("--file", "-f", help="测试文件名过滤（部分匹配）")
    args = parser.parse_args()

    data = extract_tests_from_binary(BINARY_PATH)

    if args.file:
        data = filter_by_file(data, args.file)
    elif args.suite_filter:
        data = filter_suites(data, args.suite_filter)

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
