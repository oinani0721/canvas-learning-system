#!/usr/bin/env python3
"""
Breaking Change Detector Module
检测SDD文件中的Breaking Changes

功能:
1. Git对比检测字段删除
2. 检测必填性变更 (optional → required)
3. 检测类型变更
4. 检测API端点删除/修改
5. 生成Breaking Changes报告

用法:
  from lib.breaking_change_detector import BreakingChangeDetector

  detector = BreakingChangeDetector(project_root)
  changes = detector.detect_breaking_changes()

Reference: Section 16.5.5 of planning document
"""

import sys
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum


class ChangeType(Enum):
    """变更类型"""
    FIELD_REMOVED = "field_removed"
    FIELD_REQUIRED_ADDED = "field_required_added"  # optional → required
    TYPE_CHANGED = "type_changed"
    ENDPOINT_REMOVED = "endpoint_removed"
    ENDPOINT_METHOD_REMOVED = "endpoint_method_removed"
    SCHEMA_REMOVED = "schema_removed"


class ChangeSeverity(Enum):
    """变更严重程度"""
    ERROR = "error"      # Breaking change, blocks commit
    WARNING = "warning"  # Potentially breaking, needs review
    INFO = "info"        # Informational, backward compatible


class BreakingChangeDetector:
    """Breaking Changes检测器"""

    def __init__(self, project_root: Path, base_ref: str = "HEAD~1"):
        """
        初始化检测器

        Args:
            project_root: 项目根目录
            base_ref: Git基准引用 (默认上一个commit)
        """
        self.project_root = project_root
        self.base_ref = base_ref
        self.specs_dir = project_root / "specs"

        # 检测结果
        self.changes: List[Dict] = []

    def get_git_diff(self, file_path: Path) -> Optional[str]:
        """获取文件的Git diff"""
        try:
            result = subprocess.run(
                ['git', 'diff', self.base_ref, '--', str(file_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.stdout if result.returncode == 0 else None
        except Exception:
            return None

    def get_file_content_at_ref(self, file_path: Path, ref: str) -> Optional[str]:
        """获取指定Git ref的文件内容"""
        try:
            relative_path = file_path.relative_to(self.project_root)
            result = subprocess.run(
                ['git', 'show', f'{ref}:{relative_path.as_posix()}'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.stdout if result.returncode == 0 else None
        except Exception:
            return None

    def detect_schema_breaking_changes(self, schema_file: Path) -> List[Dict]:
        """检测JSON Schema的Breaking Changes"""
        changes = []

        # 获取当前和之前的内容
        current_content = None
        previous_content = None

        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
            current_schema = json.loads(current_content)
        except Exception:
            return changes

        previous_content = self.get_file_content_at_ref(schema_file, self.base_ref)
        if not previous_content:
            return changes  # 新文件，不算breaking change

        try:
            previous_schema = json.loads(previous_content)
        except Exception:
            return changes

        # 比较字段
        changes.extend(self._compare_schema_fields(
            schema_file.name, previous_schema, current_schema
        ))

        return changes

    def _compare_schema_fields(self, schema_name: str, prev: Dict, curr: Dict) -> List[Dict]:
        """比较Schema字段变更"""
        changes = []

        prev_props = prev.get('properties', {})
        curr_props = curr.get('properties', {})
        prev_required = set(prev.get('required', []))
        curr_required = set(curr.get('required', []))

        # 检测字段删除
        for field in prev_props:
            if field not in curr_props:
                changes.append({
                    'file': schema_name,
                    'type': ChangeType.FIELD_REMOVED.value,
                    'field': field,
                    'severity': ChangeSeverity.ERROR.value,
                    'description': f"Field '{field}' was removed",
                    'migration': f"Consumer code using '{field}' will break"
                })

        # 检测新增required字段 (optional → required)
        for field in curr_required:
            if field not in prev_required and field in prev_props:
                changes.append({
                    'file': schema_name,
                    'type': ChangeType.FIELD_REQUIRED_ADDED.value,
                    'field': field,
                    'severity': ChangeSeverity.ERROR.value,
                    'description': f"Field '{field}' changed from optional to required",
                    'migration': f"Existing data without '{field}' will become invalid"
                })

        # 检测类型变更
        for field in prev_props:
            if field in curr_props:
                prev_type = prev_props[field].get('type')
                curr_type = curr_props[field].get('type')
                if prev_type and curr_type and prev_type != curr_type:
                    changes.append({
                        'file': schema_name,
                        'type': ChangeType.TYPE_CHANGED.value,
                        'field': field,
                        'severity': ChangeSeverity.ERROR.value,
                        'description': f"Field '{field}' type changed from {prev_type} to {curr_type}",
                        'migration': f"Data migration may be required"
                    })

        return changes

    def detect_openapi_breaking_changes(self, openapi_file: Path) -> List[Dict]:
        """检测OpenAPI的Breaking Changes"""
        changes = []

        try:
            with open(openapi_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except Exception:
            return changes

        previous_content = self.get_file_content_at_ref(openapi_file, self.base_ref)
        if not previous_content:
            return changes  # 新文件

        # 检测端点删除
        prev_endpoints = self._extract_openapi_endpoints(previous_content)
        curr_endpoints = self._extract_openapi_endpoints(current_content)

        for endpoint in prev_endpoints:
            if endpoint not in curr_endpoints:
                path, method = endpoint.rsplit(':', 1)
                changes.append({
                    'file': openapi_file.name,
                    'type': ChangeType.ENDPOINT_REMOVED.value,
                    'field': endpoint,
                    'severity': ChangeSeverity.ERROR.value,
                    'description': f"Endpoint {method.upper()} {path} was removed",
                    'migration': f"Clients using this endpoint will receive 404"
                })

        return changes

    def _extract_openapi_endpoints(self, content: str) -> Set[str]:
        """从OpenAPI内容提取端点列表"""
        endpoints = set()

        # 简单正则匹配路径和方法
        # 匹配模式: /path:\n  method:
        path_pattern = r'^  ([/\w{}-]+):\s*$'
        method_pattern = r'^\s{4}(get|post|put|delete|patch):\s*$'

        lines = content.split('\n')
        current_path = None

        for line in lines:
            path_match = re.match(path_pattern, line)
            if path_match:
                current_path = path_match.group(1)
                continue

            if current_path:
                method_match = re.match(method_pattern, line)
                if method_match:
                    method = method_match.group(1)
                    endpoints.add(f"{current_path}:{method}")

        return endpoints

    def detect_all_breaking_changes(self) -> List[Dict]:
        """检测所有SDD文件的Breaking Changes"""
        self.changes = []

        # 检测JSON Schema变更
        schema_dir = self.specs_dir / "data"
        if schema_dir.exists():
            for schema_file in schema_dir.glob("*.schema.json"):
                self.changes.extend(self.detect_schema_breaking_changes(schema_file))

        # 检测OpenAPI变更
        api_dir = self.specs_dir / "api"
        if api_dir.exists():
            for openapi_file in list(api_dir.glob("*.yml")) + list(api_dir.glob("*.yaml")):
                self.changes.extend(self.detect_openapi_breaking_changes(openapi_file))

        return self.changes

    def has_breaking_changes(self) -> bool:
        """是否有Breaking Changes"""
        return any(c['severity'] == ChangeSeverity.ERROR.value for c in self.changes)

    def generate_report(self) -> str:
        """生成Breaking Changes报告"""
        errors = [c for c in self.changes if c['severity'] == ChangeSeverity.ERROR.value]
        warnings = [c for c in self.changes if c['severity'] == ChangeSeverity.WARNING.value]

        report = f"""# Breaking Changes Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Base Reference**: {self.base_ref}
**Status**: {'BLOCKED - Breaking Changes Detected' if errors else 'OK - No Breaking Changes'}

---

## Summary

| Severity | Count |
|----------|-------|
| Error (Breaking) | {len(errors)} |
| Warning | {len(warnings)} |
| **Total** | **{len(self.changes)}** |

---

## Breaking Changes ({len(errors)})

"""
        if errors:
            report += "| File | Type | Field | Description | Migration |\n"
            report += "|------|------|-------|-------------|----------|\n"
            for change in errors:
                report += f"| {change['file']} | {change['type']} | {change['field']} | {change['description']} | {change['migration']} |\n"
        else:
            report += "_No breaking changes detected._\n"

        report += f"""
---

## Resolution Options

"""
        if errors:
            report += "1. **Revert the changes** - Roll back to previous version\n"
            report += "2. **Accept Breaking Changes** - Bump major version (v1.x → v2.0)\n"
            report += "3. **Add Migration Path** - Implement backward compatibility layer\n\n"

            report += "### To accept breaking changes:\n"
            report += "```bash\n"
            report += "@planning-orchestrator *finalize --accept-breaking-changes\n"
            report += "```\n\n"

            report += "### API Version Impact:\n"
            report += "- Current: vX.Y.Z\n"
            report += "- After accepting: v(X+1).0.0 (MAJOR version bump)\n"
        else:
            report += "No resolution needed. Changes are backward compatible.\n"

        report += f"""
---

**Report generated by**: scripts/lib/breaking_change_detector.py
**Reference**: Section 16.5.5 of planning document
"""
        return report


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Detect breaking changes in SDD files')
    parser.add_argument('--base-ref', type=str, default='HEAD~1', help='Git base reference (default: HEAD~1)')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--output', type=str, help='Report output path')

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent

    detector = BreakingChangeDetector(project_root, args.base_ref)
    changes = detector.detect_all_breaking_changes()

    print("=" * 60)
    print("[DETECT] Breaking Changes Detection")
    print("=" * 60)
    print(f"  Base reference: {args.base_ref}")
    print(f"  Changes found: {len(changes)}")
    print()

    if detector.has_breaking_changes():
        print("[BLOCKED] Breaking changes detected!")
        for change in changes:
            if change['severity'] == 'error':
                print(f"  - {change['file']}: {change['description']}")
    else:
        print("[OK] No breaking changes detected")

    print("=" * 60)

    if args.report:
        report = detector.generate_report()
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = project_root / "docs" / "specs" / "breaking-changes-report.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nReport saved to: {output_path}")

    return 1 if detector.has_breaking_changes() else 0


if __name__ == "__main__":
    sys.exit(main())
