#!/usr/bin/env python3
"""
MCU Coverage Report Parser

解析 gcovr 生成的 HTML 覆盖率报告，提取结构化数据。

用法:
    mcu_coverage_report(file="ddsi_ownip.c")
    mcu_coverage_report(file="src/CDD/CDD_Dds/core/ddsi/src/ddsi_ownip.c")
"""

import json
import re
import sys
from pathlib import Path
from html.parser import HTMLParser

PROJECT_ROOT = Path("/home/sanmu/MyProject/mcu_ctest/autosar-mcu")
PUBLIC_DIR = PROJECT_ROOT / "public"


class CoverageHTMLParser(HTMLParser):
    """解析 gcovr HTML 覆盖率报告"""

    def __init__(self):
        super().__init__()
        self.reset_state()

    def reset_state(self):
        # 覆盖率数据
        self.line_coverage = 0.0
        self.function_coverage = 0.0
        self.branch_coverage = 0.0
        self.file_path = ""

        # 未覆盖数据
        self.uncovered_lines = []
        self.uncovered_branches = []
        self.uncovered_functions = []

        # 函数列表
        self.functions = []

        # 解析状态
        self._in_coverage_table = False
        self._in_function_table = False
        self._in_source_table = False
        self._current_row_type = None  # "Lines", "Functions", "Branches"
        self._current_line_no = 0
        self._current_line_uncovered = False
        self._current_line_source = ""
        self._capture_text = False
        self._captured_text = ""
        self._in_file_td = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get("class", "")

        # 检测表格类型
        if tag == "table":
            if "coverage" in class_name:
                self._in_coverage_table = True
            elif "listOfFunctions" in class_name:
                self._in_function_table = True

        # 检测文件路径
        if tag == "th" and attrs_dict.get("scope") == "row":
            self._capture_text = True
            self._captured_text = ""

        if tag == "td" and self._current_row_type == "file_next":
            self._in_file_td = True
            self._capture_text = True
            self._captured_text = ""

        # 解析覆盖率百分比
        if tag == "td" and self._in_coverage_table and "coverage-" in class_name:
            self._capture_text = True
            self._captured_text = ""

        # 解析行号
        if tag == "a" and "id" in attrs_dict:
            id_val = attrs_dict["id"]
            if id_val.startswith("l") and id_val[1:].isdigit():
                self._current_line_no = int(id_val[1:])

        # 检测未覆盖行
        if tag == "td" and "uncoveredLine" in class_name:
            if "linecount" in class_name:
                self._current_line_uncovered = True
            elif "src" in class_name:
                self._capture_text = True
                self._captured_text = ""

        # 检测未覆盖分支
        if tag == "div" and "notTakenBranch" in class_name:
            self._capture_text = True
            self._captured_text = ""

        # 函数表行
        if tag == "td" and self._in_function_table:
            self._capture_text = True
            self._captured_text = ""

    def handle_endtag(self, tag):
        if tag == "table":
            self._in_coverage_table = False
            self._in_function_table = False
            self._in_source_table = False

        if tag == "th" and self._capture_text:
            text = self._captured_text.strip()
            if text == "File:":
                self._current_row_type = "file_next"
            elif text == "Lines:":
                self._current_row_type = "Lines"
            elif text == "Functions:":
                self._current_row_type = "Functions"
            elif text == "Branches:":
                self._current_row_type = "Branches"
            self._capture_text = False
            self._captured_text = ""

        if tag == "td":
            if self._in_file_td:
                self.file_path = self._captured_text.strip()
                self._in_file_td = False
                self._current_row_type = None

            if self._in_coverage_table and self._current_row_type:
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

            # 记录未覆盖行
            if self._current_line_uncovered and self._captured_text:
                source = self._strip_html_tags(self._captured_text.strip())
                if self._current_line_no and self._current_line_no not in [
                    u["line"] for u in self.uncovered_lines
                ]:
                    self.uncovered_lines.append(
                        {"line": self._current_line_no, "source": source[:100]}
                    )
                self._current_line_uncovered = False

            self._capture_text = False
            self._captured_text = ""

        if tag == "div" and self._capture_text:
            text = self._captured_text.strip()
            if "not taken" in text.lower():
                # 提取分支信息
                branch_match = re.search(r"Branch\s+(\d+)", text)
                branch_id = branch_match.group(1) if branch_match else "?"
                self.uncovered_branches.append(
                    {"line": self._current_line_no, "branch": branch_id, "info": text}
                )
            self._capture_text = False
            self._captured_text = ""

        if tag == "tr":
            self._current_line_uncovered = False

    def handle_data(self, data):
        if self._capture_text:
            self._captured_text += data

    def _strip_html_tags(self, text):
        """移除 HTML 标签"""
        return re.sub(r"<[^>]+>", "", text)


def find_report_file(file_name: str) -> Path | None:
    """根据文件名查找对应的覆盖率报告"""
    if not PUBLIC_DIR.exists():
        return None

    # 提取基础文件名
    base_name = Path(file_name).name

    # 查找匹配的报告文件
    pattern = f"codecov.{base_name}.*.html"
    matches = list(PUBLIC_DIR.glob(pattern))

    if matches:
        return matches[0]

    # 尝试部分匹配
    for html_file in PUBLIC_DIR.glob("codecov.*.html"):
        if base_name in html_file.name:
            return html_file

    return None


def parse_coverage_report(file_name: str) -> dict:
    """解析覆盖率报告并返回结构化数据"""
    report_path = find_report_file(file_name)

    if not report_path:
        return {
            "error": f"找不到 '{file_name}' 的覆盖率报告",
            "hint": "请先运行 ./scripts/test.sh --COVERAGE=on 生成报告",
            "public_dir": str(PUBLIC_DIR),
        }

    # 解析 HTML
    parser = CoverageHTMLParser()
    html_content = report_path.read_text(encoding="utf-8")
    parser.feed(html_content)

    # 构建结果
    result = {
        "file": parser.file_path or file_name,
        "report_path": str(report_path.relative_to(PROJECT_ROOT)),
        "line_coverage": parser.line_coverage,
        "function_coverage": parser.function_coverage,
        "branch_coverage": parser.branch_coverage,
        "uncovered_line_count": len(parser.uncovered_lines),
        "uncovered_branch_count": len(parser.uncovered_branches),
        "uncovered_lines": parser.uncovered_lines,
        "uncovered_branches": parser.uncovered_branches,
    }

    return result


def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "用法: mcu_coverage_report.py <file_name>",
                    "example": "mcu_coverage_report.py ddsi_ownip.c",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    file_name = sys.argv[1]
    result = parse_coverage_report(file_name)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
