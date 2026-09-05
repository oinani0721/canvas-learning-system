#!/usr/bin/env python3
"""
Add Frontmatter to Planning Documents
为PRD和Architecture文档批量添加YAML frontmatter元数据
"""

import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from planning_utils import (
    init_utf8_encoding,
    get_project_root,
    read_file,
    write_file,
    get_git_sha,
    print_status,
    confirm_action,
)

# ========================================
# Frontmatter模板
# ========================================

PRD_FRONTMATTER_TEMPLATE = """---
document_type: "PRD"
version: "{version}"
last_modified: "{date}"
status: "approved"
iteration: 1

authors:
  - name: "PM Agent"
    role: "Product Manager"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  architecture: "v1.0"
  api_spec: "v1.0"

changes_from_previous:
  - "Initial PRD with frontmatter metadata"

git:
  commit_sha: "{git_sha}"
  tag: ""

metadata:
  project_name: "Canvas Learning System"
  epic_count: 0
  fr_count: 0
  nfr_count: 0
---

"""

ARCHITECTURE_FRONTMATTER_TEMPLATE = """---
document_type: "Architecture"
version: "{version}"
last_modified: "{date}"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "{api_spec_hash}"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: "{git_sha}"
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

"""

# ========================================
# 版本提取
# ========================================


def extract_version_from_content(content: str) -> str:
    """
    从文档内容中提取版本号

    匹配模式:
    - **版本**: v2.0
    - **文档版本：** v1.0
    - version: v1.0.0
    """
    patterns = [
        r"\*\*版本\*\*\s*[：:]\s*v?(\d+\.\d+(?:\.\d+)?)",
        r"\*\*文档版本[：:]\*\*\s*v?(\d+\.\d+(?:\.\d+)?)",
        r"version\s*[：:]\s*v?(\d+\.\d+(?:\.\d+)?)",
        r"Version\s*[：:]\s*v?(\d+\.\d+(?:\.\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            version = match.group(1)
            # 确保是三位版本号
            parts = version.split(".")
            if len(parts) == 2:
                version = f"{version}.0"
            return version

    # 默认版本
    return "1.0.0"


def has_frontmatter(content: str) -> bool:
    """检查文档是否已有YAML frontmatter"""
    return content.strip().startswith("---")


# ========================================
# Frontmatter添加
# ========================================


def add_frontmatter_to_prd(file_path: Path, dry_run: bool = False) -> bool:
    """
    为PRD文档添加frontmatter

    Args:
        file_path: PRD文件路径
        dry_run: 如果为True，只打印变更不实际写入

    Returns:
        True if successful
    """
    content = read_file(file_path)

    # 检查是否已有frontmatter
    if has_frontmatter(content):
        print_status(f"  Skip (already has frontmatter): {file_path.name}", "info")
        return False

    # 提取版本号
    version = extract_version_from_content(content)

    # 生成frontmatter
    frontmatter = PRD_FRONTMATTER_TEMPLATE.format(
        version=version, date=datetime.now().strftime("%Y-%m-%d"), git_sha=get_git_sha()[:8]
    )

    # 添加frontmatter到文档开头
    new_content = frontmatter + content

    if dry_run:
        print_status(f"  Would add frontmatter (v{version}): {file_path.name}", "info")
        return True
    else:
        write_file(file_path, new_content)
        print_status(f"  Added frontmatter (v{version}): {file_path.name}", "success")
        return True


def add_frontmatter_to_architecture(file_path: Path, dry_run: bool = False) -> bool:
    """
    为Architecture文档添加frontmatter

    Args:
        file_path: Architecture文件路径
        dry_run: 如果为True，只打印变更不实际写入

    Returns:
        True if successful
    """
    content = read_file(file_path)

    # 检查是否已有frontmatter
    if has_frontmatter(content):
        print_status(f"  Skip (already has frontmatter): {file_path.name}", "info")
        return False

    # 提取版本号
    version = extract_version_from_content(content)

    # 计算API spec hash（如果存在）
    root = get_project_root()
    api_spec_path = root / "specs" / "api" / "agent-api.openapi.yml"
    api_spec_hash = ""
    if api_spec_path.exists():
        from planning_utils import compute_file_hash

        api_spec_hash = compute_file_hash(api_spec_path)[:16]

    # 生成frontmatter
    frontmatter = ARCHITECTURE_FRONTMATTER_TEMPLATE.format(
        version=version,
        date=datetime.now().strftime("%Y-%m-%d"),
        git_sha=get_git_sha()[:8],
        api_spec_hash=api_spec_hash,
    )

    # 添加frontmatter到文档开头
    new_content = frontmatter + content

    if dry_run:
        print_status(f"  Would add frontmatter (v{version}): {file_path.name}", "info")
        return True
    else:
        write_file(file_path, new_content)
        print_status(f"  Added frontmatter (v{version}): {file_path.name}", "success")
        return True


# ========================================
# 批量处理
# ========================================


def process_prd_documents(dry_run: bool = False):
    """处理所有PRD文档"""
    root = get_project_root()
    prd_dir = root / "docs" / "prd"

    if not prd_dir.exists():
        print_status("PRD directory not found", "error")
        return 0

    prd_files = list(prd_dir.glob("*.md"))

    print_status(f"Found {len(prd_files)} PRD file(s)", "info")

    count = 0
    for prd_file in prd_files:
        if add_frontmatter_to_prd(prd_file, dry_run):
            count += 1

    return count


def process_architecture_documents(dry_run: bool = False):
    """处理所有Architecture文档"""
    root = get_project_root()
    arch_dir = root / "docs" / "architecture"

    if not arch_dir.exists():
        print_status("Architecture directory not found", "error")
        return 0

    arch_files = list(arch_dir.glob("*.md"))

    print_status(f"Found {len(arch_files)} Architecture file(s)", "info")

    count = 0
    for arch_file in arch_files:
        if add_frontmatter_to_architecture(arch_file, dry_run):
            count += 1

    return count


# ========================================
# CLI接口
# ========================================


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Add YAML frontmatter metadata to PRD and Architecture documents")
    parser.add_argument(
        "--type", choices=["prd", "architecture", "all"], default="all", help="Document type to process (default: all)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    parser.add_argument("--file", type=str, help="Process a single file instead of all files")

    args = parser.parse_args()

    # Initialize UTF-8 encoding for Windows
    init_utf8_encoding()

    print("=" * 60)
    print("📝 Add Frontmatter to Planning Documents")
    print("=" * 60)
    print()

    if args.dry_run:
        print_status("Running in DRY-RUN mode (no files will be modified)", "warning")
        print()

    # 处理单个文件
    if args.file:
        file_path = Path(args.file)

        if not file_path.exists():
            print_status(f"File not found: {file_path}", "error")
            return 1

        print_status(f"Processing single file: {file_path.name}", "progress")

        if "prd" in str(file_path):
            add_frontmatter_to_prd(file_path, args.dry_run)
        elif "architecture" in str(file_path):
            add_frontmatter_to_architecture(file_path, args.dry_run)
        else:
            print_status("Cannot determine document type from path", "error")
            return 1

        print()
        print("✅ Done!")
        return 0

    # 批量处理
    prd_count = 0
    arch_count = 0

    if args.type in ["prd", "all"]:
        print_status("Processing PRD documents...", "progress")
        prd_count = process_prd_documents(args.dry_run)
        print()

    if args.type in ["architecture", "all"]:
        print_status("Processing Architecture documents...", "progress")
        arch_count = process_architecture_documents(args.dry_run)
        print()

    # 打印摘要
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"PRD documents processed: {prd_count}")
    print(f"Architecture documents processed: {arch_count}")
    print(f"Total: {prd_count + arch_count}")
    print("=" * 60)

    if args.dry_run:
        print()
        print_status("This was a DRY-RUN. No files were modified.", "warning")
        print_status("Run without --dry-run to apply changes.", "info")
    else:
        print()
        print_status("Frontmatter added successfully!", "success")
        print()
        print("Next steps:")
        print("  1. Review the changes: git diff")
        print("  2. Create a snapshot: python scripts/snapshot-planning.py")
        print("  3. Commit changes: git add . && git commit -m 'Add frontmatter metadata'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
