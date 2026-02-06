#!/usr/bin/env python3
"""
MCU List Tests Tool

列出 CUnit 测试二进制中的所有 suite 和 test。

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
BINARY_PATH = PROJECT_ROOT / "build" / "bin" / "cunit_Ddscp"


def extract_tests_from_binary(binary_path: Path) -> dict:
    """从二进制文件的符号表中提取测试信息"""
    if not binary_path.exists():
        return {
            "error": f"二进制文件不存在: {binary_path}",
            "hint": "请先运行 cmake --build . --target cunit_Ddscp -j4",
        }

    # 使用 nm 提取符号
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

    # 解析 CU_Test_ 符号
    # 格式: CU_Test_<suite>_<test>
    # 注意: suite 和 test 名称中可能包含下划线
    pattern = re.compile(r"\b[Tt]\s+CU_Test_(.+)")

    suites = defaultdict(list)

    for line in result.stdout.splitlines():
        match = pattern.search(line)
        if match:
            full_name = match.group(1)
            # 分割 suite 和 test
            # 策略: 已知的 suite 前缀列表，或者取第一个下划线之前的部分
            suite_name, test_name = split_suite_test(full_name)
            if test_name not in suites[suite_name]:
                suites[suite_name].append(test_name)

    # 转换为列表格式
    result_list = []
    for suite_name in sorted(suites.keys()):
        result_list.append(
            {
                "name": suite_name,
                "tests": sorted(suites[suite_name]),
                "test_count": len(suites[suite_name]),
            }
        )

    return {
        "binary": str(binary_path),
        "total_suites": len(result_list),
        "total_tests": sum(s["test_count"] for s in result_list),
        "suites": result_list,
    }


def split_suite_test(full_name: str) -> tuple:
    """
    将 CU_Test_ 后的完整名称分割为 (suite, test)

    策略:
    1. 已知 suite 前缀匹配
    2. 常见模式匹配 (如 xxx_coverage, xxx_test, xxx_static)
    3. 回退到第一个下划线分割
    """
    # 已知的 suite 名称模式（按长度降序，优先匹配更长的）
    known_patterns = [
        # 带后缀的模式
        r"^(branch_coverage\d*)_(.+)$",
        r"^(ddsi_\w+_coverage)_(.+)$",
        r"^(ddsi_\w+_test)_(.+)$",
        r"^(dds_\w+_coverage)_(.+)$",
        r"^(dds_\w+_test)_(.+)$",
        r"^(ddsrt_\w+)_(.+)$",
        r"^(q_\w+_coverage)_(.+)$",
        r"^(q_\w+_test)_(.+)$",
        r"^(q_\w+)_(.+)$",
        # 简单前缀模式
        r"^(ddsi_\w+?)_(.+)$",
        r"^(dds_\w+?)_(.+)$",
        r"^(ddsc_\w+?)_(.+)$",
        r"^(flexible_types)_(.+)$",
        r"^(notify_\w+?)_(.+)$",
        r"^(xevent_\w+?)_(.+)$",
        r"^(lifespan)_(.+)$",
        r"^(whc)_(.+)$",
        r"^(minimal)_(.+)$",
    ]

    for pattern in known_patterns:
        match = re.match(pattern, full_name)
        if match:
            return match.group(1), match.group(2)

    # 回退: 寻找 _coverage, _test, _static 等常见后缀作为 suite 结尾
    for suffix in ["_coverage", "_test", "_static", "_inline"]:
        idx = full_name.find(suffix)
        if idx > 0:
            suite_end = idx + len(suffix)
            if suite_end < len(full_name) and full_name[suite_end] == "_":
                return full_name[:suite_end], full_name[suite_end + 1 :]

    # 最终回退: 第一个下划线分割
    parts = full_name.split("_", 1)
    if len(parts) == 2:
        return parts[0], parts[1]

    return full_name, ""


def filter_suites(data: dict, suite_filter: str) -> dict:
    """过滤 suite"""
    if "error" in data:
        return data

    if not suite_filter:
        return data

    filtered = [s for s in data["suites"] if suite_filter.lower() in s["name"].lower()]

    return {
        "binary": data["binary"],
        "filter": suite_filter,
        "total_suites": len(filtered),
        "total_tests": sum(s["test_count"] for s in filtered),
        "suites": filtered,
    }


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
            return {
                "binary": data["binary"],
                "file_filter": file_filter,
                "note": "通过 suite 名称模糊匹配",
                "total_suites": len(filtered),
                "total_tests": sum(s["test_count"] for s in filtered),
                "suites": filtered,
            }

        return {
            "binary": data["binary"],
            "file_filter": file_filter,
            "error": f"未找到匹配的测试文件: {file_filter}",
            "hint": "请检查 tests/ 目录中的文件名，或使用 suite_filter 参数",
        }

    filtered = [s for s in data["suites"] if s["name"] in matched_suites]

    return {
        "binary": data["binary"],
        "file_filter": file_filter,
        "matched_files": matched_files,
        "total_suites": len(filtered),
        "total_tests": sum(s["test_count"] for s in filtered),
        "suites": filtered,
    }


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
