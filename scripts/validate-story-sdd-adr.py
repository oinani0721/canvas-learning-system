#!/usr/bin/env python3
"""
Story SDD/ADR Section Validator
验证Story文件是否包含必需的SDD和ADR引用sections

功能:
1. 检测Story是否有"SDD规范引用"section
2. 检测Story是否有"ADR关联"section
3. Epic 15+: 强制要求 (缺失则阻止提交)
4. Epic 1-14: Legacy模式 (仅警告)

用法:
  python scripts/validate-story-sdd-adr.py [story_files...]

  无参数时扫描docs/stories/目录下所有.story.md文件

返回码:
  0 - 所有验证通过
  1 - 验证失败 (阻止提交)
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# Set UTF-8 encoding for Windows console
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# Stories before this Epic number are considered legacy
LEGACY_EPIC_THRESHOLD = 15


def extract_epic_number(filename: str) -> int:
    """
    从Story文件名中提取Epic编号

    Examples:
        '15.1.story.md' -> 15
        '8.17.story.md' -> 8
        'story-15-1.md' -> 15
    """
    # Pattern 1: {epicNum}.{storyNum}.story.md
    match = re.match(r'(\d+)\.\d+\.story\.md', filename)
    if match:
        return int(match.group(1))

    # Pattern 2: story-{epicNum}-{storyNum}.md
    match = re.match(r'story-(\d+)-\d+\.md', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 3: Any number at the start
    match = re.match(r'(\d+)', filename)
    if match:
        return int(match.group(1))

    return 0


def check_sdd_section(content: str) -> Tuple[bool, str]:
    """
    检查Story是否有SDD规范引用section

    Returns:
        (has_sdd, message)
    """
    # Patterns that indicate SDD references
    sdd_patterns = [
        r'SDD规范引用',           # Chinese section header
        r'SDD Specification',     # English section header
        r'OpenAPI.*specs/',       # OpenAPI reference
        r'specs/api/',            # API spec path
        r'specs/data/',           # Data schema path
        r'\.schema\.json',        # JSON Schema file
        r'\.openapi\.yml',        # OpenAPI file
        r'\.openapi\.yaml',       # OpenAPI file (yaml extension)
    ]

    for pattern in sdd_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True, "Found SDD references"

    return False, "Missing SDD specification references (SDD规范引用 section)"


def check_adr_section(content: str) -> Tuple[bool, str]:
    """
    检查Story是否有ADR关联section

    Returns:
        (has_adr, message)
    """
    # Patterns that indicate ADR references
    adr_patterns = [
        r'ADR关联',                      # Chinese section header
        r'ADR References',               # English section header
        r'ADR-\d{3}',                    # ADR number (e.g., ADR-001)
        r'docs/architecture/decisions/', # ADR file path
        r'No ADRs apply',                # Explicit no ADR statement
        r'无相关ADR',                    # Chinese no ADR statement
        r'N/A.*ADR',                     # N/A with ADR mention
    ]

    for pattern in adr_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True, "Found ADR references"

    return False, "Missing ADR references (ADR关联 section)"


def validate_story_file(filepath: Path) -> Tuple[bool, List[str]]:
    """
    验证单个Story文件

    Returns:
        (passed, issues)
    """
    issues = []

    # Extract epic number to determine if legacy
    epic_num = extract_epic_number(filepath.name)
    is_legacy = 0 < epic_num < LEGACY_EPIC_THRESHOLD

    # Read file content
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"[ERROR] Cannot read file: {e}"]

    # Check SDD section
    sdd_ok, sdd_msg = check_sdd_section(content)
    if not sdd_ok:
        if is_legacy:
            issues.append(f"[WARNING] {sdd_msg} (Legacy story - Epic {epic_num})")
        else:
            issues.append(f"[ERROR] {sdd_msg}")

    # Check ADR section
    adr_ok, adr_msg = check_adr_section(content)
    if not adr_ok:
        if is_legacy:
            issues.append(f"[WARNING] {adr_msg} (Legacy story - Epic {epic_num})")
        else:
            issues.append(f"[ERROR] {adr_msg}")

    # Determine pass/fail
    # Only ERROR issues cause failure (not WARNING)
    has_errors = any("[ERROR]" in issue for issue in issues)
    return not has_errors, issues


def main():
    """主函数"""
    print("=" * 60)
    print("[VALIDATE] Story SDD/ADR Section Validator")
    print("=" * 60)
    print(f"  Legacy threshold: Epic < {LEGACY_EPIC_THRESHOLD} (warnings only)")
    print(f"  Enforced: Epic >= {LEGACY_EPIC_THRESHOLD} (errors block commit)")
    print()

    # Get story files from arguments or find all
    if len(sys.argv) > 1:
        # Files passed as arguments (from pre-commit)
        story_files = [Path(f) for f in sys.argv[1:] if f.endswith('.story.md')]
    else:
        # No arguments - scan docs/stories/ directory
        story_dir = Path('docs/stories')
        if story_dir.exists():
            story_files = list(story_dir.glob('*.story.md'))
        else:
            print("[INFO] No docs/stories/ directory found")
            print("[INFO] No story files to validate")
            return 0

    if not story_files:
        print("[INFO] No story files to validate")
        return 0

    print(f"Validating {len(story_files)} story file(s)...")
    print()

    all_passed = True
    total_errors = 0
    total_warnings = 0
    files_with_issues = 0

    for story_file in sorted(story_files):
        passed, issues = validate_story_file(story_file)

        if issues:
            files_with_issues += 1
            print(f"{story_file.name}:")
            for issue in issues:
                print(f"  {issue}")
                if "[ERROR]" in issue:
                    total_errors += 1
                elif "[WARNING]" in issue:
                    total_warnings += 1
            print()

        if not passed:
            all_passed = False

    # Summary
    print("=" * 60)
    print("[SUMMARY]")
    print(f"  Files checked: {len(story_files)}")
    print(f"  Files with issues: {files_with_issues}")
    print(f"  Errors: {total_errors}")
    print(f"  Warnings: {total_warnings}")
    print()

    if all_passed:
        if total_warnings > 0:
            print(f"[SUCCESS] Validation passed with {total_warnings} warning(s)")
            print("  Legacy stories (Epic 1-14) may lack SDD/ADR sections.")
            print("  This is acceptable for historical stories.")
        else:
            print("[SUCCESS] All stories have required SDD/ADR sections!")
    else:
        print(f"[FAILED] {total_errors} error(s) found")
        print()
        print("Stories with [ERROR] status are missing required sections.")
        print("For Epic 15+ stories, SDD/ADR sections are MANDATORY.")
        print()
        print("To fix:")
        print("  1. Open the story file")
        print("  2. Add 'SDD规范引用' section with OpenAPI/Schema references")
        print("  3. Add 'ADR关联' section with relevant ADRs (or 'No ADRs apply')")
        print()
        print("Reference: .bmad-core/tasks/create-next-story.md (Step 3.3, 3.4)")

    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
