#!/usr/bin/env python3
"""
MCU Build and Coverage Tool

一键编译、运行测试、生成覆盖率报告。
成功返回覆盖率数据，失败只返回最后 50 行错误日志。
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/sanmu/MyProject/mcu_ctest/autosar-mcu")
BUILD_DIR = PROJECT_ROOT / "build"
BINARY_PATH = BUILD_DIR / "bin" / "cunit_Ddscp"


def run_command(cmd: list, cwd: Path, timeout: int = 300) -> tuple[int, str, str]:
    """运行命令，返回 (exit_code, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"命令超时 ({timeout}s): {' '.join(cmd)}"
    except Exception as e:
        return -1, "", str(e)


def get_last_lines(text: str, n: int = 50) -> str:
    """获取最后 n 行"""
    lines = text.strip().splitlines()
    return "\n".join(lines[-n:])


def reconfigure_cmake() -> dict | None:
    cmd = [
        "cmake",
        "-DBUILD_TESTING=ON",
        "-DBUILD_EXAMPLES=ON",
        "-DENABLE_COVERAGE=on",
        "..",
    ]
    exit_code, stdout, stderr = run_command(cmd, BUILD_DIR, timeout=60)

    if exit_code != 0:
        combined = stdout + "\n" + stderr
        return {
            "stage": "configure",
            "error": "CMake 配置失败",
            "last_50_lines": get_last_lines(combined, 50),
        }
    return None


def build_tests(reconfigure: bool = False) -> dict | None:
    if reconfigure:
        error = reconfigure_cmake()
        if error:
            return error

    cmd = ["cmake", "--build", ".", "--target", "cunit_Ddscp", "-j4"]
    exit_code, stdout, stderr = run_command(cmd, BUILD_DIR, timeout=120)

    if exit_code != 0:
        combined = stdout + "\n" + stderr
        return {
            "stage": "build",
            "error": "编译失败",
            "last_50_lines": get_last_lines(combined, 50),
        }
    return None


def run_tests(suite: str | None = None) -> dict | None:
    """运行测试，返回错误信息或 None"""
    cmd = [str(BINARY_PATH)]
    if suite:
        cmd.extend(["-s", suite])

    exit_code, stdout, stderr = run_command(cmd, BUILD_DIR, timeout=60)

    if exit_code != 0:
        combined = stdout + "\n" + stderr
        return {
            "stage": "test",
            "error": "测试失败",
            "last_50_lines": get_last_lines(combined, 50),
        }
    return None


def run_full_coverage() -> tuple[dict | None, str]:
    """运行完整覆盖率测试，返回 (错误信息或None, 完整输出)"""
    cmd = ["./scripts/test.sh", "--COVERAGE=on"]
    exit_code, stdout, stderr = run_command(cmd, PROJECT_ROOT, timeout=600)
    combined = stdout + "\n" + stderr

    if exit_code != 0:
        return {
            "stage": "coverage",
            "error": "覆盖率测试失败",
            "last_50_lines": get_last_lines(combined, 50),
        }, combined
    return None, combined


def get_coverage_report(file_name: str) -> dict:
    """获取覆盖率报告"""
    tools_dir = Path(__file__).parent
    sys.path.insert(0, str(tools_dir))
    from mcu_coverage_report import parse_coverage_report

    return parse_coverage_report(file_name)


def infer_suite_from_file(file_name: str) -> list[str]:
    """根据源文件名推断对应的测试 suite，返回所有匹配的 suites"""
    tools_dir = Path(__file__).parent
    sys.path.insert(0, str(tools_dir))
    from mcu_find_test_file import find_related_test_files

    base_name = Path(file_name).stem.lower()
    related = find_related_test_files(file_name)
    matched_suites = []

    for item in related:
        if item.get("relevance", 0) < 3:
            continue
        for suite in item.get("suites", []):
            suite_lower = suite.lower()
            if base_name in suite_lower or suite_lower in base_name:
                if suite not in matched_suites:
                    matched_suites.append(suite)

    if not matched_suites and related:
        best = related[0]
        matched_suites = best.get("suites", [])[:3]

    return matched_suites


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="目标源文件名")
    parser.add_argument("--suite", help="只运行指定 suite（可选）")
    parser.add_argument(
        "--quick", action="store_true", help="快速模式：只编译运行，不生成覆盖率"
    )
    parser.add_argument(
        "--reconfigure",
        action="store_true",
        help="重新运行 cmake 配置（测试文件新增/删除后需要）",
    )
    args = parser.parse_args()

    result = {"file": args.file}

    suites_to_run = []
    if args.suite:
        suites_to_run = [args.suite]
    elif args.quick:
        suites_to_run = infer_suite_from_file(args.file)
        if suites_to_run:
            result["inferred_suites"] = suites_to_run

    error = build_tests(reconfigure=args.reconfigure)
    if error:
        print(json.dumps(error, ensure_ascii=False, indent=2))
        sys.exit(1)

    result["build"] = "ok"

    if args.quick:
        if not suites_to_run:
            print(
                json.dumps(
                    {
                        "stage": "test",
                        "error": "quick 模式需要指定 suite 或能自动推断 suite",
                        "hint": "请使用 --suite 参数，或确保源文件有对应的测试文件",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            sys.exit(1)

        for suite in suites_to_run:
            error = run_tests(suite)
            if error:
                print(json.dumps(error, ensure_ascii=False, indent=2))
                sys.exit(1)
        result["test"] = "ok"
        result["suites_ran"] = suites_to_run
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    error, output = run_full_coverage()
    if error:
        print(json.dumps(error, ensure_ascii=False, indent=2))
        sys.exit(1)

    result["coverage_test"] = "ok"

    coverage = get_coverage_report(args.file)
    result["coverage"] = coverage

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
