"""
Annotation Checker - 零幻觉标注检查器

独立模块，用于检查代码文件中的技术栈API调用是否有验证注释。
可以作为:
- Pre-commit hook 的检查器
- Commit Gate G1/G2 的底层实现
- 独立的代码审查工具

零幻觉开发原则:
- 🔴 提到什么技术，立即查看对应Skill或Context 7
- 🔴 每个API调用必须标注文档来源
- 🔴 未验证的API不允许进入代码

✅ Reference: CLAUDE.md 零幻觉开发原则

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-11
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# ============================================================================
# 配置常量
# ============================================================================

# 验证注释模式
VERIFICATION_PATTERNS = [
    r"#\s*✅\s*Verified from\s+(.+)",
    r"#\s*✅\s*Reference:\s*(.+)",
    r"#\s*Source:\s*(.+)",
]

# 合并后的正则
VERIFICATION_COMMENT_REGEX = re.compile(
    r"#\s*✅\s*(?:Verified from|Reference:?)\s+(.+)",
    re.IGNORECASE
)

# 技术栈定义
TECH_STACK_CONFIG: Dict[str, Dict[str, Any]] = {
    "langgraph": {
        "display_name": "LangGraph",
        "import_patterns": [
            r"from\s+langgraph\b",
            r"import\s+langgraph\b",
        ],
        "api_patterns": [
            "StateGraph",
            "add_node",
            "add_edge",
            "add_conditional_edges",
            "Send",
            "RetryPolicy",
            "END",
            "START",
            "MessagesState",
            "compile",
        ],
        "doc_source": "LangGraph Skill",
        "skill_path": ".claude/skills/langgraph/SKILL.md",
    },
    "graphiti": {
        "display_name": "Graphiti",
        "import_patterns": [
            r"from\s+graphiti\b",
            r"import\s+graphiti\b",
        ],
        "api_patterns": [
            "GraphitiClient",
            "add_episode",
            "search_nodes",
            "search_facts",
            "add_memory",
        ],
        "doc_source": "Graphiti Skill",
        "skill_path": ".claude/skills/graphiti/SKILL.md",
    },
    "fastapi": {
        "display_name": "FastAPI",
        "import_patterns": [
            r"from\s+fastapi\b",
            r"import\s+fastapi\b",
        ],
        "api_patterns": [
            "FastAPI",
            "APIRouter",
            "Depends",
            "HTTPException",
            "Query",
            "Path",
            "Body",
            "Header",
            "Cookie",
            "Response",
            "Request",
            "BackgroundTasks",
        ],
        "doc_source": "Context 7",
        "context7": True,
    },
    "pydantic": {
        "display_name": "Pydantic",
        "import_patterns": [
            r"from\s+pydantic\b",
            r"import\s+pydantic\b",
        ],
        "api_patterns": [
            "BaseModel",
            "Field",
            "validator",
            "root_validator",
            "model_validator",
            "field_validator",
            "ConfigDict",
        ],
        "doc_source": "Context 7",
        "context7": True,
    },
    "lancedb": {
        "display_name": "LanceDB",
        "import_patterns": [
            r"import\s+lancedb\b",
            r"from\s+lancedb\b",
        ],
        "api_patterns": [
            "lancedb.connect",
            "table.search",
            "table.add",
            "create_table",
            "open_table",
        ],
        "doc_source": "Context 7",
        "context7": True,
    },
    "openai": {
        "display_name": "OpenAI",
        "import_patterns": [
            r"from\s+openai\b",
            r"import\s+openai\b",
        ],
        "api_patterns": [
            "OpenAI",
            "ChatCompletion",
            "Embedding",
            "AsyncOpenAI",
        ],
        "doc_source": "Context 7",
        "context7": True,
    },
}

# Python 标准库模块 (排除检查)
STDLIB_MODULES: Set[str] = {
    "os", "sys", "json", "typing", "pathlib", "datetime", "re", "ast",
    "asyncio", "collections", "functools", "itertools", "logging",
    "subprocess", "tempfile", "shutil", "hashlib", "base64", "uuid",
    "time", "copy", "io", "math", "random", "string", "textwrap",
    "dataclasses", "enum", "abc", "contextlib", "inspect", "types",
    "warnings", "traceback", "unittest", "typing_extensions",
    "argparse", "configparser", "csv", "xml", "html", "http",
    "urllib", "socket", "email", "mimetypes", "struct", "pickle",
    "sqlite3", "threading", "multiprocessing", "queue", "heapq",
    "bisect", "array", "weakref", "gc", "dis", "code", "codeop",
}


# ============================================================================
# 数据类
# ============================================================================


@dataclass
class AnnotationIssue:
    """标注问题记录"""
    file_path: str
    line_number: int
    tech_stack: str
    api_pattern: str
    code_snippet: str
    expected_annotation: str
    severity: str = "warning"  # "error" | "warning" | "info"


@dataclass
class AnnotationCheckResult:
    """检查结果"""
    file_path: str
    total_api_calls: int = 0
    annotated_calls: int = 0
    issues: List[AnnotationIssue] = field(default_factory=list)
    tech_stacks_used: Set[str] = field(default_factory=set)
    verification_comments: List[str] = field(default_factory=list)

    @property
    def annotation_ratio(self) -> float:
        """标注覆盖率"""
        if self.total_api_calls == 0:
            return 1.0
        return self.annotated_calls / self.total_api_calls

    @property
    def is_compliant(self) -> bool:
        """是否符合零幻觉原则 (≥80% 覆盖率)"""
        return self.annotation_ratio >= 0.8


@dataclass
class BatchCheckResult:
    """批量检查结果"""
    files_checked: int = 0
    total_api_calls: int = 0
    total_annotated: int = 0
    total_issues: int = 0
    file_results: List[AnnotationCheckResult] = field(default_factory=list)
    all_tech_stacks: Set[str] = field(default_factory=set)

    @property
    def overall_ratio(self) -> float:
        """总体标注覆盖率"""
        if self.total_api_calls == 0:
            return 1.0
        return self.total_annotated / self.total_api_calls

    @property
    def is_compliant(self) -> bool:
        """是否符合零幻觉原则"""
        return self.overall_ratio >= 0.8


# ============================================================================
# AnnotationChecker 类
# ============================================================================


class AnnotationChecker:
    """
    零幻觉标注检查器

    检查Python代码文件中的技术栈API调用是否有验证注释。

    Usage:
    ```python
    checker = AnnotationChecker()

    # 检查单个文件
    result = checker.check_file(Path("src/my_module.py"))
    print(f"覆盖率: {result.annotation_ratio:.1%}")
    print(f"问题数: {len(result.issues)}")

    # 批量检查目录
    batch_result = checker.check_directory(Path("src/"))
    print(f"总覆盖率: {batch_result.overall_ratio:.1%}")
    ```
    """

    def __init__(
        self,
        tech_config: Optional[Dict[str, Dict[str, Any]]] = None,
        strict_mode: bool = False,
        context_lines: int = 5,
    ):
        """
        Args:
            tech_config: 自定义技术栈配置 (默认使用内置配置)
            strict_mode: 严格模式 (要求100%覆盖率)
            context_lines: 检查验证注释的上下文行数
        """
        self.tech_config = tech_config or TECH_STACK_CONFIG
        self.strict_mode = strict_mode
        self.context_lines = context_lines

    def check_file(self, file_path: Path) -> AnnotationCheckResult:
        """
        检查单个Python文件

        Args:
            file_path: 文件路径

        Returns:
            AnnotationCheckResult 检查结果
        """
        result = AnnotationCheckResult(file_path=str(file_path))

        if not file_path.exists():
            return result

        if file_path.suffix != ".py":
            return result

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return result

        lines = content.split("\n")

        # 1. 检测使用的技术栈
        result.tech_stacks_used = self._detect_tech_stacks(content)

        # 2. 提取所有验证注释
        result.verification_comments = self._extract_verification_comments(content)

        # 3. 检查每个技术栈的API调用
        for tech_id in result.tech_stacks_used:
            tech_info = self.tech_config.get(tech_id, {})
            api_patterns = tech_info.get("api_patterns", [])
            doc_source = tech_info.get("doc_source", "Unknown")

            for pattern in api_patterns:
                for line_num, line in enumerate(lines, 1):
                    # 跳过注释行
                    if line.strip().startswith("#"):
                        continue

                    # 跳过字符串中的匹配
                    if f'"{pattern}"' in line or f"'{pattern}'" in line:
                        continue

                    if pattern in line:
                        result.total_api_calls += 1

                        # 检查上下文中是否有验证注释
                        context_start = max(0, line_num - 1 - self.context_lines)
                        context_end = line_num
                        context = "\n".join(lines[context_start:context_end])

                        has_annotation = bool(VERIFICATION_COMMENT_REGEX.search(context))

                        if has_annotation:
                            result.annotated_calls += 1
                        else:
                            issue = AnnotationIssue(
                                file_path=str(file_path),
                                line_number=line_num,
                                tech_stack=tech_id,
                                api_pattern=pattern,
                                code_snippet=line.strip()[:80],
                                expected_annotation=f"# ✅ Verified from {doc_source}",
                                severity="warning" if not self.strict_mode else "error",
                            )
                            result.issues.append(issue)

        return result

    def check_directory(
        self,
        directory: Path,
        exclude_patterns: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> BatchCheckResult:
        """
        批量检查目录

        Args:
            directory: 目录路径
            exclude_patterns: 排除模式 (e.g., ["test_*", "__pycache__"])
            recursive: 是否递归检查子目录

        Returns:
            BatchCheckResult 批量检查结果
        """
        if exclude_patterns is None:
            exclude_patterns = ["test_*", "*_test.py", "__pycache__", ".git", "venv"]

        result = BatchCheckResult()

        if not directory.exists():
            return result

        # 收集Python文件
        if recursive:
            py_files = list(directory.rglob("*.py"))
        else:
            py_files = list(directory.glob("*.py"))

        # 过滤排除模式
        def should_exclude(file_path: Path) -> bool:
            path_str = str(file_path)
            for pattern in exclude_patterns:
                if pattern in path_str:
                    return True
            return False

        py_files = [f for f in py_files if not should_exclude(f)]

        # 检查每个文件
        for file_path in py_files:
            file_result = self.check_file(file_path)
            result.files_checked += 1
            result.total_api_calls += file_result.total_api_calls
            result.total_annotated += file_result.annotated_calls
            result.total_issues += len(file_result.issues)
            result.file_results.append(file_result)
            result.all_tech_stacks.update(file_result.tech_stacks_used)

        return result

    def check_changed_files(self, files: List[Path]) -> BatchCheckResult:
        """
        检查指定的文件列表 (用于Git hook)

        Args:
            files: 文件路径列表

        Returns:
            BatchCheckResult 批量检查结果
        """
        result = BatchCheckResult()

        for file_path in files:
            if file_path.suffix != ".py":
                continue

            file_result = self.check_file(file_path)
            result.files_checked += 1
            result.total_api_calls += file_result.total_api_calls
            result.total_annotated += file_result.annotated_calls
            result.total_issues += len(file_result.issues)
            result.file_results.append(file_result)
            result.all_tech_stacks.update(file_result.tech_stacks_used)

        return result

    def _detect_tech_stacks(self, content: str) -> Set[str]:
        """检测文件中使用的技术栈"""
        used = set()

        for tech_id, config in self.tech_config.items():
            import_patterns = config.get("import_patterns", [])
            for pattern in import_patterns:
                if re.search(pattern, content):
                    used.add(tech_id)
                    break

        return used

    def _extract_verification_comments(self, content: str) -> List[str]:
        """提取所有验证注释"""
        matches = VERIFICATION_COMMENT_REGEX.findall(content)
        return matches

    def format_report(self, result: BatchCheckResult, verbose: bool = False) -> str:
        """
        格式化检查报告

        Args:
            result: 检查结果
            verbose: 是否显示详细信息

        Returns:
            格式化的报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("零幻觉标注检查报告")
        lines.append("=" * 60)
        lines.append(f"检查文件数: {result.files_checked}")
        lines.append(f"API调用总数: {result.total_api_calls}")
        lines.append(f"已标注调用: {result.total_annotated}")
        lines.append(f"标注覆盖率: {result.overall_ratio:.1%}")
        lines.append(f"问题总数: {result.total_issues}")
        lines.append(f"使用的技术栈: {', '.join(result.all_tech_stacks)}")
        lines.append("")

        status = "✅ 通过" if result.is_compliant else "❌ 未通过"
        lines.append(f"检查结果: {status}")

        if verbose and result.total_issues > 0:
            lines.append("")
            lines.append("-" * 60)
            lines.append("问题详情 (前20个):")
            lines.append("-" * 60)

            issue_count = 0
            for file_result in result.file_results:
                for issue in file_result.issues:
                    if issue_count >= 20:
                        break
                    lines.append(f"\n📍 {issue.file_path}:{issue.line_number}")
                    lines.append(f"   技术栈: {issue.tech_stack}")
                    lines.append(f"   API: {issue.api_pattern}")
                    lines.append(f"   代码: {issue.code_snippet}")
                    lines.append(f"   建议: 添加 {issue.expected_annotation}")
                    issue_count += 1

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# ============================================================================
# 便捷函数
# ============================================================================


def check_file_annotations(file_path: Path) -> AnnotationCheckResult:
    """便捷函数: 检查单个文件"""
    checker = AnnotationChecker()
    return checker.check_file(file_path)


def check_directory_annotations(
    directory: Path,
    strict: bool = False,
) -> BatchCheckResult:
    """便捷函数: 检查目录"""
    checker = AnnotationChecker(strict_mode=strict)
    return checker.check_directory(directory)


def get_annotation_ratio(files: List[Path]) -> float:
    """便捷函数: 获取文件列表的标注覆盖率"""
    checker = AnnotationChecker()
    result = checker.check_changed_files(files)
    return result.overall_ratio


# ============================================================================
# CLI 支持
# ============================================================================


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="零幻觉标注检查器 - 检查代码中的技术栈API调用是否有验证注释"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="要检查的文件或目录路径",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细信息",
    )
    parser.add_argument(
        "-s", "--strict",
        action="store_true",
        help="严格模式 (要求100%覆盖率)",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="不符合时返回非零退出码",
    )

    args = parser.parse_args()

    checker = AnnotationChecker(strict_mode=args.strict)

    if args.path.is_file():
        result = checker.check_file(args.path)
        batch_result = BatchCheckResult(
            files_checked=1,
            total_api_calls=result.total_api_calls,
            total_annotated=result.annotated_calls,
            total_issues=len(result.issues),
            file_results=[result],
            all_tech_stacks=result.tech_stacks_used,
        )
    else:
        batch_result = checker.check_directory(args.path)

    report = checker.format_report(batch_result, verbose=args.verbose)
    print(report)

    if args.exit_code and not batch_result.is_compliant:
        exit(1)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "AnnotationChecker",
    "AnnotationCheckResult",
    "BatchCheckResult",
    "AnnotationIssue",
    "check_file_annotations",
    "check_directory_annotations",
    "get_annotation_ratio",
    "TECH_STACK_CONFIG",
    "VERIFICATION_COMMENT_REGEX",
]


if __name__ == "__main__":
    main()
