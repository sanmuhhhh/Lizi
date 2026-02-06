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
CONTEXT_LINES = 3


class CoverageHTMLParser(HTMLParser):
    """解析 gcovr HTML 覆盖率报告"""

    def __init__(self):
        super().__init__()
        self.reset_state()

    def reset_state(self):
        self.line_coverage = 0.0
        self.function_coverage = 0.0
        self.branch_coverage = 0.0
        self.file_path = ""

        self.uncovered_lines = []
        self.uncovered_branches = []
        self.uncovered_functions = []
        self.functions = []

        self._in_coverage_table = False
        self._in_function_table = False
        self._in_source_table = False
        self._current_row_type = None
        self._current_line_no = 0
        self._current_line_uncovered = False
        self._current_line_source = ""
        self._capture_text = False
        self._captured_text = ""
        self._in_file_td = False

        self._in_branch_summary = False
        self._current_total_branches = 0
        self._current_taken_branches = 0
        self._in_src_td = False
        self._current_src_content = ""
        self._pending_branch_line = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get("class", "") or ""

        if tag == "table":
            if "coverage" in class_name:
                self._in_coverage_table = True
            elif "listOfFunctions" in class_name:
                self._in_function_table = True

        if tag == "th" and attrs_dict.get("scope") == "row":
            self._capture_text = True
            self._captured_text = ""

        if tag == "td" and self._current_row_type == "file_next":
            self._in_file_td = True
            self._capture_text = True
            self._captured_text = ""

        if (
            tag == "td"
            and self._in_coverage_table
            and class_name
            and "coverage-" in class_name
        ):
            self._capture_text = True
            self._captured_text = ""

        id_val = attrs_dict.get("id", "")
        if tag == "a" and id_val and id_val.startswith("l") and id_val[1:].isdigit():
            self._current_line_no = int(id_val[1:])

        if tag == "td" and class_name and "uncoveredLine" in class_name:
            if "linecount" in class_name:
                self._current_line_uncovered = True
            elif "src" in class_name:
                self._capture_text = True
                self._captured_text = ""

        if tag == "summary" and class_name and "linebranchSummary" in class_name:
            self._in_branch_summary = True
            self._capture_text = True
            self._captured_text = ""
            self._pending_branch_line = self._current_line_no

        if tag == "div" and class_name and "notTakenBranch" in class_name:
            self._capture_text = True
            self._captured_text = ""

        if tag == "td" and class_name and "src" in class_name:
            self._in_src_td = True
            self._current_src_content = ""

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

            if self._current_line_uncovered and self._captured_text:
                source = self._strip_html_tags(self._captured_text.strip())
                if self._current_line_no and self._current_line_no not in [
                    u["line"] for u in self.uncovered_lines
                ]:
                    self.uncovered_lines.append(
                        {"line": self._current_line_no, "source": source[:100]}
                    )
                self._current_line_uncovered = False

            if self._in_src_td:
                self._in_src_td = False

            self._capture_text = False
            self._captured_text = ""

        if tag == "summary" and self._in_branch_summary:
            text = self._captured_text.strip()
            match = re.match(r"(\d+)/(\d+)", text)
            if match:
                self._current_taken_branches = int(match.group(1))
                self._current_total_branches = int(match.group(2))
            self._in_branch_summary = False
            self._capture_text = False
            self._captured_text = ""

        if tag == "div" and self._capture_text:
            text = self._captured_text.strip()
            if "not taken" in text.lower():
                branch_match = re.search(r"Branch\s+(\d+)", text)
                branch_id = branch_match.group(1) if branch_match else "?"

                branch_entry = {
                    "line": self._pending_branch_line
                    if self._pending_branch_line
                    else self._current_line_no,
                    "branch": branch_id,
                    "total_branches": self._current_total_branches,
                    "info": text,
                }

                self.uncovered_branches.append(branch_entry)
            self._capture_text = False
            self._captured_text = ""

        if tag == "tr":
            if self._current_src_content and self._pending_branch_line:
                for branch in self.uncovered_branches:
                    if (
                        branch["line"] == self._pending_branch_line
                        and "condition" not in branch
                    ):
                        clean_condition = self._strip_html_tags(
                            self._current_src_content
                        ).strip()
                        branch["condition"] = clean_condition[:200]

            self._current_line_uncovered = False
            self._current_src_content = ""
            self._pending_branch_line = 0
            self._current_total_branches = 0
            self._current_taken_branches = 0

    def handle_data(self, data):
        if self._capture_text:
            self._captured_text += data
        if self._in_src_td:
            self._current_src_content += data

    def _strip_html_tags(self, text):
        return re.sub(r"<[^>]+>", "", text)


def find_source_file(file_name: str) -> Path | None:
    """查找源文件路径（排除 tests 目录）"""
    base_name = Path(file_name).name

    # 优先在 src 目录下查找
    for src_file in PROJECT_ROOT.rglob(base_name):
        if src_file.is_file():
            path_str = str(src_file)
            # 排除 build 和 tests 目录
            if "build" not in path_str and "/tests/" not in path_str:
                return src_file
    return None


def get_source_context(
    source_file: Path, line_no: int, context_lines: int = CONTEXT_LINES
) -> dict:
    """获取源码上下文"""
    if not source_file or not source_file.exists():
        return {}

    try:
        lines = source_file.read_text(encoding="utf-8").splitlines()
        total_lines = len(lines)

        start = max(0, line_no - context_lines - 1)
        end = min(total_lines, line_no + context_lines)

        before = []
        after = []
        current = ""

        for i in range(start, end):
            line_content = lines[i].rstrip() if i < total_lines else ""
            if i < line_no - 1:
                before.append(line_content)
            elif i == line_no - 1:
                current = line_content
            else:
                after.append(line_content)

        return {
            "before": before,
            "current": current,
            "after": after,
        }
    except Exception:
        return {}


def find_function_for_line(source_file: Path, line_no: int) -> str:
    """查找行所在的函数名"""
    if not source_file or not source_file.exists():
        return ""

    try:
        lines = source_file.read_text(encoding="utf-8").splitlines()

        func_pattern = re.compile(
            r"^(?:STATIC\s+|static\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*\{?\s*$"
        )

        current_func = ""
        brace_count = 0
        in_function = False

        for i, line in enumerate(lines[:line_no], 1):
            match = func_pattern.match(line.strip())
            if match and not line.strip().startswith("//"):
                current_func = match.group(1)
                in_function = True
                brace_count = 0

            if in_function:
                brace_count += line.count("{") - line.count("}")
                if brace_count <= 0 and "{" in line:
                    in_function = False

        return current_func
    except Exception:
        return ""


def find_report_file(file_name: str) -> Path | None:
    if not PUBLIC_DIR.exists():
        return None

    base_name = Path(file_name).name

    pattern = f"codecov.{base_name}.*.html"
    matches = list(PUBLIC_DIR.glob(pattern))

    if matches:
        return matches[0]

    for html_file in PUBLIC_DIR.glob("codecov.*.html"):
        if base_name in html_file.name:
            return html_file

    return None


def analyze_reachability(source_file: Path, line_info: dict) -> dict:
    """
    分析未覆盖代码的可达性，返回可达性信息。

    可达性分类：
    - unit_testable: 可通过单元测试覆盖
    - stub_required: 需要 stub 才能覆盖
    - multiproc_required: 需要多进程测试
    - platform_specific: 平台特定代码
    - defensive: 防御性代码（不应到达）
    """
    source_code = line_info.get("source", "")
    context = line_info.get("context", {})
    func_name = line_info.get("function", "")

    result = {"reachability": "unit_testable", "reason": ""}

    NEW_FUNC_PATTERNS = [
        r"\bnew_\w+\s*\(",
        r"\bnn_xpack_\w+\s*\(",
        r"\bnn_xmsg_new\s*\(",
        r"\bremote_\w+\s*\(",
        r"\bproxy_\w+\s*\(",
    ]
    for pattern in NEW_FUNC_PATTERNS:
        if re.search(pattern, source_code):
            result["reachability"] = "multiproc_required"
            result["reason"] = f"调用 new_*/proxy_* 函数，需要远程实体交互"
            return result

    if func_name and func_name.startswith("new_"):
        result["reachability"] = "multiproc_required"
        result["reason"] = f"函数 {func_name} 是 new_* 路径，需要多进程测试"
        return result

    ALLOC_PATTERNS = [
        (r"\bmalloc\s*\(", "malloc 失败路径"),
        (r"\bddsrt_malloc\s*\(", "ddsrt_malloc 失败路径"),
        (r"\bcalloc\s*\(", "calloc 失败路径"),
        (r"\brealloc\s*\(", "realloc 失败路径"),
    ]
    context_str = " ".join(context.get("before", []) + [context.get("current", "")])
    for pattern, reason in ALLOC_PATTERNS:
        if re.search(pattern, context_str) and (
            "NULL" in source_code or "== 0" in source_code
        ):
            result["reachability"] = "stub_required"
            result["reason"] = reason
            return result

    DEFENSIVE_PATTERNS = [
        (r"\bassert\s*\(\s*false\s*\)", "assert(false) - 不应到达"),
        (r"\bassert\s*\(\s*0\s*\)", "assert(0) - 不应到达"),
        (r"DDS_FATAL", "DDS_FATAL - 致命错误"),
        (r"__builtin_unreachable", "unreachable 代码"),
        (r"abort\s*\(\s*\)", "abort() - 不应到达"),
    ]
    for pattern, reason in DEFENSIVE_PATTERNS:
        if re.search(pattern, source_code):
            result["reachability"] = "defensive"
            result["reason"] = reason
            return result

    PLATFORM_PATTERNS = [
        (r"#ifdef\s+_WIN32", "Windows 特定代码"),
        (r"#ifdef\s+__linux__", "Linux 特定代码"),
        (r"#ifdef\s+__APPLE__", "macOS 特定代码"),
        (r"#if\s+defined.*POSIX", "POSIX 特定代码"),
    ]
    for pattern, reason in PLATFORM_PATTERNS:
        if re.search(pattern, context_str):
            result["reachability"] = "platform_specific"
            result["reason"] = reason
            return result

    return result


def parse_coverage_report(file_name: str, with_context: bool = True) -> dict:
    report_path = find_report_file(file_name)

    if not report_path:
        return {
            "error": f"找不到 '{file_name}' 的覆盖率报告",
            "hint": "请先运行 ./scripts/test.sh --COVERAGE=on 生成报告",
            "public_dir": str(PUBLIC_DIR),
        }

    parser = CoverageHTMLParser()
    html_content = report_path.read_text(encoding="utf-8")
    parser.feed(html_content)

    source_file = find_source_file(file_name) if with_context else None

    uncovered_lines = parser.uncovered_lines
    uncovered_branches = parser.uncovered_branches

    reachability_stats = {
        "unit_testable": 0,
        "stub_required": 0,
        "multiproc_required": 0,
        "platform_specific": 0,
        "defensive": 0,
    }

    if source_file and with_context:
        for line_info in uncovered_lines:
            line_no = line_info["line"]
            context = get_source_context(source_file, line_no)
            if context:
                line_info["context"] = context
            func_name = find_function_for_line(source_file, line_no)
            if func_name:
                line_info["function"] = func_name
            reach = analyze_reachability(source_file, line_info)
            line_info["reachability"] = reach["reachability"]
            if reach["reason"]:
                line_info["reachability_reason"] = reach["reason"]
            reachability_stats[reach["reachability"]] += 1

        for branch_info in uncovered_branches:
            line_no = branch_info["line"]
            context = get_source_context(source_file, line_no)
            if context:
                branch_info["context"] = context
            func_name = find_function_for_line(source_file, line_no)
            if func_name:
                branch_info["function"] = func_name
            reach = analyze_reachability(source_file, branch_info)
            branch_info["reachability"] = reach["reachability"]
            if reach["reason"]:
                branch_info["reachability_reason"] = reach["reason"]

    result = {
        "file": parser.file_path or file_name,
        "report_path": str(report_path.relative_to(PROJECT_ROOT)),
        "line_coverage": parser.line_coverage,
        "function_coverage": parser.function_coverage,
        "branch_coverage": parser.branch_coverage,
        "uncovered_line_count": len(uncovered_lines),
        "uncovered_branch_count": len(uncovered_branches),
        "reachability_summary": reachability_stats,
        "uncovered_lines": uncovered_lines,
        "uncovered_branches": uncovered_branches,
    }

    return result


def main():
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
