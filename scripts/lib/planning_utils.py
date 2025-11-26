#!/usr/bin/env python3
"""
Planning Phase Utilities
用于BMad Planning Phase迭代管理的共享工具函数
"""

import os
import json
import hashlib
import yaml
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import subprocess

# ========================================
# 路径和配置
# ========================================

def get_project_root() -> Path:
    """获取项目根目录"""
    # 假设scripts/lib/在项目根目录下
    return Path(__file__).parent.parent.parent

def get_planning_iterations_dir() -> Path:
    """获取planning-iterations目录"""
    return get_project_root() / ".bmad-core" / "planning-iterations"

def get_snapshots_dir() -> Path:
    """获取snapshots目录"""
    return get_planning_iterations_dir() / "snapshots"

def get_validators_dir() -> Path:
    """获取validators目录"""
    return get_project_root() / ".bmad-core" / "validators"

# ========================================
# 文件操作
# ========================================

def read_file(file_path: Path) -> str:
    """安全读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # 如果UTF-8失败，尝试其他编码
        with open(file_path, 'r', encoding='gbk') as f:
            return f.read()

def write_file(file_path: Path, content: str):
    """安全写入文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def compute_file_hash(file_path: Path) -> str:
    """计算文件的SHA-256 hash"""
    if not file_path.exists():
        return ""

    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ========================================
# YAML Frontmatter 处理
# ========================================

def extract_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
    """
    从Markdown文件中提取YAML frontmatter

    Returns:
        (frontmatter_dict, content_without_frontmatter)
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1))
            content_body = match.group(2)
            return frontmatter, content_body
        except yaml.YAMLError:
            return None, content

    return None, content

def update_frontmatter(content: str, updates: Dict) -> str:
    """
    更新Markdown文件的YAML frontmatter

    Args:
        content: 原始内容
        updates: 要更新的字段字典

    Returns:
        更新后的内容
    """
    frontmatter, body = extract_frontmatter(content)

    if frontmatter is None:
        # 如果没有frontmatter，创建新的
        frontmatter = updates
    else:
        # 更新现有frontmatter
        frontmatter.update(updates)

    # 重新组装
    yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    return f"---\n{yaml_str}---\n\n{body}"

def get_version_from_frontmatter(file_path: Path) -> Optional[str]:
    """从文件的frontmatter中获取version字段"""
    if not file_path.exists():
        return None

    content = read_file(file_path)
    frontmatter, _ = extract_frontmatter(content)

    if frontmatter and 'version' in frontmatter:
        return frontmatter['version']

    return None

# ========================================
# OpenAPI 处理
# ========================================

def read_openapi_spec(file_path: Path) -> Dict:
    """读取OpenAPI spec文件"""
    content = read_file(file_path)
    return yaml.safe_load(content)

def get_openapi_version(file_path: Path) -> Optional[str]:
    """获取OpenAPI spec的版本号"""
    try:
        spec = read_openapi_spec(file_path)
        return spec.get('info', {}).get('version')
    except Exception:
        return None

def get_openapi_endpoints(spec: Dict) -> List[str]:
    """获取OpenAPI spec中的所有endpoint路径"""
    return list(spec.get('paths', {}).keys())

# ========================================
# Git 操作
# ========================================

def get_git_sha() -> str:
    """获取当前Git commit SHA"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            check=True,
            cwd=get_project_root()
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def get_git_status() -> str:
    """获取Git status"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True,
            cwd=get_project_root()
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""

def is_git_clean() -> bool:
    """检查Git工作目录是否干净"""
    return get_git_status().strip() == ""

def create_git_tag(tag_name: str, message: str):
    """创建Git tag"""
    try:
        subprocess.run(
            ['git', 'tag', '-a', tag_name, '-m', message],
            check=True,
            cwd=get_project_root()
        )
        print(f"✅ Git tag created: {tag_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create Git tag: {e}")

# ========================================
# 迭代管理
# ========================================

def get_next_iteration_number() -> int:
    """获取下一个迭代编号"""
    snapshots_dir = get_snapshots_dir()

    if not snapshots_dir.exists():
        return 1

    # 查找所有iteration-XXX.json文件
    pattern = re.compile(r'iteration-(\d{3})\.json')
    max_num = 0

    for file in snapshots_dir.iterdir():
        match = pattern.match(file.name)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)

    return max_num + 1

def get_iteration_snapshot_path(iteration_num: int) -> Path:
    """获取指定迭代的snapshot文件路径"""
    return get_snapshots_dir() / f"iteration-{iteration_num:03d}.json"

def load_snapshot(iteration_num: int) -> Optional[Dict]:
    """加载指定迭代的snapshot"""
    path = get_iteration_snapshot_path(iteration_num)

    if not path.exists():
        return None

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_snapshot(snapshot: Dict, iteration_num: int) -> Path:
    """保存snapshot到文件

    Returns:
        Path: 保存的文件路径
    """
    path = get_iteration_snapshot_path(iteration_num)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"✅ Snapshot saved: {path}")
    return path  # Bug fix: 返回保存路径

# ========================================
# 版本比较
# ========================================

def parse_semver(version: str) -> Tuple[int, int, int]:
    """解析语义化版本号"""
    # 去除可能的'v'前缀
    version = version.lstrip('v')

    # 提取Major.Minor.Patch
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
    if match:
        return tuple(map(int, match.groups()))

    raise ValueError(f"Invalid semver: {version}")

def compare_versions(v1: str, v2: str) -> int:
    """
    比较两个版本号

    Returns:
        1 if v1 > v2
        0 if v1 == v2
        -1 if v1 < v2
    """
    try:
        parts1 = parse_semver(v1)
        parts2 = parse_semver(v2)

        if parts1 > parts2:
            return 1
        elif parts1 < parts2:
            return -1
        else:
            return 0
    except ValueError:
        # 如果不是标准semver，使用字符串比较
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
        else:
            return 0

def increment_version(version: str, increment_type: str = "patch") -> str:
    """
    递增版本号

    Args:
        version: 当前版本号 (e.g., "1.2.3")
        increment_type: "major" | "minor" | "patch"

    Returns:
        新版本号
    """
    major, minor, patch = parse_semver(version)

    if increment_type == "major":
        return f"{major + 1}.0.0"
    elif increment_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"

# ========================================
# 验证规则加载
# ========================================

def load_validation_rules() -> Dict:
    """加载验证规则配置"""
    rules_path = get_validators_dir() / "iteration-rules.yaml"

    if not rules_path.exists():
        raise FileNotFoundError(f"Validation rules not found: {rules_path}")

    with open(rules_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# ========================================
# 报告生成
# ========================================

def generate_markdown_report(title: str, sections: List[Dict]) -> str:
    """
    生成Markdown格式的报告

    Args:
        title: 报告标题
        sections: 章节列表，每个章节是字典 {"title": "...", "content": "..."}

    Returns:
        Markdown字符串
    """
    md = f"# {title}\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"

    for section in sections:
        md += f"## {section['title']}\n\n"
        md += f"{section['content']}\n\n"
        md += "---\n\n"

    return md

# ========================================
# 工具函数
# ========================================

def init_utf8_encoding():
    """
    Initialize UTF-8 encoding for Windows console
    Call this at the start of any script that uses Unicode characters
    """
    import sys
    import io

    if sys.platform == 'win32':
        # Fix stdout
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        # Fix stderr
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def print_status(message: str, status: str = "info"):
    """打印带状态图标的消息"""
    import sys
    import io

    # Windows UTF-8 encoding fix
    if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "progress": "⏳"
    }
    icon = icons.get(status, "•")

    try:
        print(f"{icon} {message}")
    except UnicodeEncodeError:
        # Fallback to ASCII icons
        ascii_icons = {
            "success": "[OK]",
            "error": "[ERROR]",
            "warning": "[WARN]",
            "info": "[INFO]",
            "progress": "[...]"
        }
        ascii_icon = ascii_icons.get(status, "*")
        print(f"{ascii_icon} {message}")

def confirm_action(prompt: str) -> bool:
    """请求用户确认

    在非交互模式（如 Claude Code）下，如果无法获取输入，返回 False
    """
    try:
        import sys
        # Check if stdin is available for interactive input
        if not sys.stdin.isatty():
            print_status(f"{prompt} - Skipped (non-interactive mode)", "warning")
            return False
        response = input(f"{prompt} (y/N): ").strip().lower()
        return response == 'y'
    except (EOFError, OSError):
        print_status(f"{prompt} - Skipped (no input available)", "warning")
        return False

# ========================================
# 文件扫描
# ========================================

def scan_planning_files() -> Dict[str, List[Path]]:
    """
    扫描所有Planning Phase相关文件

    Returns:
        分类的文件列表字典
    """
    root = get_project_root()

    files = {
        'prd': [],
        'architecture': [],
        'epics': [],
        'api_specs': [],
        'data_schemas': [],
        'behavior_specs': []
    }

    # PRD文件
    prd_dir = root / "docs" / "prd"
    if prd_dir.exists():
        files['prd'] = list(prd_dir.glob("*.md"))

    # Architecture文件
    arch_dir = root / "docs" / "architecture"
    if arch_dir.exists():
        files['architecture'] = list(arch_dir.glob("*.md"))

    # Epic文件
    epics_dir = root / "docs" / "epics"
    if epics_dir.exists():
        files['epics'] = list(epics_dir.glob("*.md"))

    # API Specs
    api_dir = root / "specs" / "api"
    if api_dir.exists():
        files['api_specs'] = list(api_dir.glob("*.yml")) + list(api_dir.glob("*.yaml"))

    # Data Schemas
    data_dir = root / "specs" / "data"
    if data_dir.exists():
        files['data_schemas'] = list(data_dir.glob("*.json")) + list(data_dir.glob("*.schema.json"))

    # Behavior Specs
    behavior_dir = root / "specs" / "behavior"
    if behavior_dir.exists():
        files['behavior_specs'] = list(behavior_dir.glob("*.feature"))

    return files

# ========================================
# 测试工具（用于验证）
# ========================================

def test_utils():
    """测试工具函数"""
    print("Testing Planning Utils...")

    # 测试版本比较
    assert compare_versions("1.0.0", "1.0.1") == -1
    assert compare_versions("2.0.0", "1.9.9") == 1
    assert compare_versions("1.2.3", "1.2.3") == 0
    print("✅ Version comparison works")

    # 测试版本递增
    assert increment_version("1.2.3", "major") == "2.0.0"
    assert increment_version("1.2.3", "minor") == "1.3.0"
    assert increment_version("1.2.3", "patch") == "1.2.4"
    print("✅ Version increment works")

    # 测试Git操作
    sha = get_git_sha()
    print(f"✅ Git SHA: {sha[:8]}...")

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_utils()
