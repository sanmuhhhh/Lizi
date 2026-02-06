#!/usr/bin/env python3
"""
MCU Quick Coverage Tool

快速验证单个测试的覆盖率效果，无需完整测试。

用法:
    mcu_quick_coverage --suite=dds_participant --test=lookup_with_actual_domain_id --file=dds_participant.c
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from html.parser import HTMLParser
import re
import shutil
import tempfile

PROJECT_ROOT = Path("/home/sanmu/MyProject/mcu_ctest/autosar-mcu")
BUILD_DIR = PROJECT_ROOT / "build"
BINARY_PATH = BUILD_DIR / "bin" / "cunit_Ddscp"
PUBLIC_DIR = PROJECT_ROOT / "public"


class QuickCoverageHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.line_coverage = 0.0
        self.function_coverage = 0.0
        self.branch_coverage = 0.0
        self._current_row_type = None
        self._capture_text = False
        self._captured_text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get("class", "")

        if tag == "th" and attrs_dict.get("scope") == "row":
            self._capture_text = True
            self._captured_text = ""

        if tag == "td" and class_name and "coverage-" in class_name:
            self._capture_text = True
            self._captured_text = ""

    def handle_endtag(self, tag):
        if tag == "th" and self._capture_text:
            text = self._captured_text.strip()
            if text == "Lines:":
                self._current_row_type = "Lines"
            elif text == "Functions:":
                self._current_row_type = "Functions"
            elif text == "Branches:":
                self._current_row_type = "Branches"
            self._capture_text = False
            self._captured_text = ""

        if tag == "td" and self._current_row_type:
            text = self._captured_text.strip()
            if "%" in text:
                try:
                    val = float(text.replace("%", ""))
                    if self._current_row_type == "Lines":
                        self.line_coverage = val
                    elif self._current_row_type == "Functions":
                        self.function_coverage = val
                    elif self._current_row_type == "Branches":
                        self.branch_coverage = val
                except ValueError:
                    pass
                self._current_row_type = None
            self._capture_text = False
            self._captured_text = ""

    def handle_data(self, data):
        if self._capture_text:
            self._captured_text += data


def find_report_file(file_name: str, search_dir: Path) -> Path | None:
    base_name = Path(file_name).name
    pattern = f"codecov.{base_name}.*.html"
    matches = list(search_dir.glob(pattern))
    if matches:
        return matches[0]
    for html_file in search_dir.glob("codecov.*.html"):
        if base_name in html_file.name:
            return html_file
    return None


def parse_coverage(html_path: Path) -> dict:
    parser = QuickCoverageHTMLParser()
    content = html_path.read_text(encoding="utf-8")
    parser.feed(content)
    return {
        "line_coverage": parser.line_coverage,
        "function_coverage": parser.function_coverage,
        "branch_coverage": parser.branch_coverage,
    }


def get_baseline_coverage(source_file: str) -> dict | None:
    report = find_report_file(source_file, PUBLIC_DIR)
    if not report:
        return None
    return parse_coverage(report)


def backup_gcda_files(backup_dir: Path) -> list[tuple[Path, Path]]:
    """备份所有 .gcda 文件，返回 (原路径, 备份路径) 列表"""
    gcda_files = list(BUILD_DIR.rglob("*.gcda"))
    backup_map = []

    for gcda in gcda_files:
        rel_path = gcda.relative_to(BUILD_DIR)
        backup_path = backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gcda, backup_path)
        backup_map.append((gcda, backup_path))
        gcda.unlink()

    return backup_map


def restore_gcda_files(backup_map: list[tuple[Path, Path]]) -> int:
    """从备份恢复 .gcda 文件，返回恢复的文件数"""
    restored = 0
    for orig_path, backup_path in backup_map:
        if backup_path.exists():
            orig_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, orig_path)
            restored += 1
    return restored


def run_quick_coverage(
    suite: str, test: str, source_file: str, restore: bool = True
) -> dict:
    if not BINARY_PATH.exists():
        return {"error": f"二进制文件不存在: {BINARY_PATH}"}

    baseline = get_baseline_coverage(source_file)
    if baseline is None:
        return {
            "error": f"找不到 {source_file} 的基线覆盖率报告",
            "hint": "请先运行 ./scripts/test.sh --COVERAGE=on 生成完整报告",
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        backup_dir = tmp_path / "gcda_backup"
        backup_dir.mkdir()

        backup_map = backup_gcda_files(backup_dir)
        if not backup_map:
            return {"error": "找不到 .gcda 文件，请确保项目已用覆盖率选项编译"}

        # 运行单个测试
        test_cmd = [str(BINARY_PATH), "-s", suite, "-t", test]
        try:
            result = subprocess.run(
                test_cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return {"error": "测试运行超时"}

        tests_ran = 0
        for line in result.stdout.splitlines():
            if "tests" in line.lower() and (
                "ran" in line.lower() or "run" in line.lower()
            ):
                match = re.search(r"(\d+)\s*test", line)
                if match:
                    tests_ran = int(match.group(1))
                    break

        if tests_ran == 0:
            # 尝试用完整名称运行
            full_test_name = f"{suite}_{test}"
            test_cmd2 = [str(BINARY_PATH), "-t", full_test_name]
            result2 = subprocess.run(
                test_cmd2,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=60,
            )
            for line in result2.stdout.splitlines():
                if "tests" in line.lower() and (
                    "ran" in line.lower() or "run" in line.lower()
                ):
                    match = re.search(r"(\d+)\s*test", line)
                    if match:
                        tests_ran = int(match.group(1))
                        break

        # 生成覆盖率报告到临时目录
        gcovr_cmd = [
            "gcovr",
            "-r",
            str(PROJECT_ROOT),
            "-e",
            "(.+/)?tests/",
            "--gcov-ignore-parse-errors",
            "--html-details",
            "-o",
            str(tmp_path / "codecov.html"),
        ]

        try:
            subprocess.run(
                gcovr_cmd, cwd=str(BUILD_DIR), capture_output=True, timeout=120
            )
        except subprocess.TimeoutExpired:
            return {"error": "gcovr 报告生成超时"}

        # 解析新的覆盖率
        after_report = find_report_file(source_file, tmp_path)
        if after_report is None:
            return {
                "error": f"无法生成 {source_file} 的快速覆盖率报告",
                "tests_ran": tests_ran,
                "test_output": result.stdout[:500] if result.stdout else "",
            }

        after = parse_coverage(after_report)

        delta = {
            "line_coverage": round(
                after["line_coverage"] - baseline["line_coverage"], 2
            ),
            "function_coverage": round(
                after["function_coverage"] - baseline["function_coverage"], 2
            ),
            "branch_coverage": round(
                after["branch_coverage"] - baseline["branch_coverage"], 2
            ),
        }

        result_dict: dict = {
            "suite": suite,
            "test": test,
            "source_file": source_file,
            "tests_ran": tests_ran,
            "before": baseline,
            "after": after,
            "delta": delta,
        }

        if restore:
            restored_count = restore_gcda_files(backup_map)
            result_dict["gcda_restored"] = restored_count
            result_dict["note"] = "gcda 文件已自动恢复，覆盖率数据完整"
        else:
            result_dict["warning"] = "gcda 文件未恢复，需重新运行完整测试"

        return result_dict


def main():
    parser = argparse.ArgumentParser(description="快速验证单测覆盖率")
    parser.add_argument("--suite", "-s", required=True, help="Suite 名称")
    parser.add_argument("--test", "-t", required=True, help="Test 名称")
    parser.add_argument("--file", "-f", required=True, help="目标源文件")
    parser.add_argument(
        "--no-restore",
        action="store_true",
        help="不恢复 gcda 文件（默认会自动恢复）",
    )

    args = parser.parse_args()

    result = run_quick_coverage(
        args.suite, args.test, args.file, restore=not args.no_restore
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
