#!/usr/bin/env python3
"""
MCU Run Single Test Tool

运行单个测试或 suite，返回简洁的结果。
"""

import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/sanmu/MyProject/mcu_ctest/autosar-mcu")
BUILD_DIR = PROJECT_ROOT / "build"
BINARY_PATH = BUILD_DIR / "bin" / "cunit_Ddscp"


def run_test(suite: str | None = None, test: str | None = None) -> dict:
    """运行测试并解析结果"""
    if not BINARY_PATH.exists():
        return {
            "status": "error",
            "error": f"二进制文件不存在: {BINARY_PATH}",
            "hint": "请先运行 cmake --build . --target cunit_Ddscp -j4",
        }

    cmd = [str(BINARY_PATH)]
    if suite:
        cmd.extend(["-s", suite])
    if test:
        cmd.extend(["-t", test])

    try:
        result = subprocess.run(
            cmd,
            cwd=BUILD_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "测试超时 (60s)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

    output = result.stdout + result.stderr

    parsed = parse_cunit_output(output)
    parsed["exit_code"] = result.returncode
    parsed["command"] = " ".join(cmd)

    if result.returncode == 0:
        parsed["status"] = "passed"
    else:
        parsed["status"] = "failed"
        parsed["output_tail"] = get_last_lines(output, 30)

    if parsed["tests_ran"] == 0 and suite:
        parsed["warning"] = "0 tests ran - suite/test 名称可能不匹配"
        parsed["hint"] = (
            f"使用 mcu_list_tests(suite_filter='{suite}') 查找正确的 suite 名称。"
            f" CUnit -s 参数匹配 CU_Test(SUITE, test) 中的 SUITE 参数。"
        )
        similar = find_similar_suites(suite)
        if similar:
            parsed["similar_suites"] = similar

    return parsed


def parse_cunit_output(output: str) -> dict:
    """解析 CUnit 输出"""
    result = {
        "suites_ran": 0,
        "tests_ran": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "asserts_total": 0,
        "asserts_passed": 0,
        "asserts_failed": 0,
        "elapsed": "",
    }

    lines = output.splitlines()
    for line in lines:
        if "suites" in line.lower():
            match = re.search(r"suites\s+(\d+)\s+(\d+)", line, re.IGNORECASE)
            if match:
                result["suites_ran"] = int(match.group(2))

        if "tests" in line.lower() and "asserts" not in line.lower():
            match = re.search(
                r"tests\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line, re.IGNORECASE
            )
            if match:
                result["tests_ran"] = int(match.group(2))
                result["tests_passed"] = int(match.group(3))
                result["tests_failed"] = int(match.group(4))

        if "asserts" in line.lower():
            match = re.search(r"asserts\s+(\d+)\s+(\d+)\s+(\d+)", line, re.IGNORECASE)
            if match:
                result["asserts_total"] = int(match.group(2))
                result["asserts_passed"] = int(match.group(3))
                result["asserts_failed"] = int(match.group(1)) - int(match.group(3))

        if "elapsed" in line.lower():
            match = re.search(r"Elapsed time\s*=\s*([\d.]+)", line, re.IGNORECASE)
            if match:
                result["elapsed"] = f"{match.group(1)}s"

    return result


def get_last_lines(text: str, n: int = 30) -> str:
    lines = text.strip().splitlines()
    return "\n".join(lines[-n:])


def find_similar_suites(pattern: str, max_results: int = 5) -> list[str]:
    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        return []

    suites = set()
    cu_test_re = re.compile(r"CU_Test\s*\(\s*(\w+)\s*,")
    pattern_lower = pattern.lower()

    for test_file in tests_dir.glob("*.c"):
        try:
            content = test_file.read_text(encoding="utf-8", errors="ignore")
            for match in cu_test_re.finditer(content):
                suite_name = match.group(1)
                if pattern_lower in suite_name.lower():
                    suites.add(suite_name)
        except Exception:
            continue

    return sorted(suites)[:max_results]


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", "-s", help="Suite 名称")
    parser.add_argument("--test", "-t", help="Test 名称")
    args = parser.parse_args()

    if not args.suite and not args.test:
        print(
            json.dumps(
                {
                    "error": "必须指定 --suite 或 --test",
                    "usage": "mcu_run_single_test.py --suite <suite> [--test <test>]",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    result = run_test(args.suite, args.test)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
