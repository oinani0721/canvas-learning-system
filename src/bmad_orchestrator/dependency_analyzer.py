"""
BMad Dependency Analyzer - Story 依赖分析和冲突检测

为全自动化工作流提供:
1. Story 文件依赖分析
2. 潜在冲突检测
3. 执行模式推荐 (parallel/linear/hybrid)
4. 批次生成

核心算法:
- 读取 Story 文件的 Dev Notes 提取文件引用
- 构建 Story-File 依赖图
- 检测冲突对 (两个 Story 修改同一文件)
- 使用图着色算法生成并行批次

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-30
"""

import asyncio
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Tuple

# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class StoryDependency:
    """Story 依赖信息"""
    story_id: str
    files_to_create: List[str] = field(default_factory=list)
    files_to_modify: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)
    schema_refs: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


@dataclass
class ConflictInfo:
    """冲突信息"""
    story_a: str
    story_b: str
    conflicting_files: List[str]
    conflict_type: Literal["CREATE_CONFLICT", "MODIFY_CONFLICT", "API_CONFLICT"]


@dataclass
class AnalysisResult:
    """分析结果"""
    dependencies: Dict[str, StoryDependency]
    conflicts: Dict[str, List[str]]  # "story_a-story_b" -> [conflicting_files]
    recommended_mode: Literal["parallel", "linear", "hybrid"]
    batches: List[List[str]]
    conflict_details: List[ConflictInfo]


# ============================================================================
# 文件解析
# ============================================================================

async def parse_story_file(story_path: Path) -> Optional[StoryDependency]:
    """
    解析 Story 文件提取依赖信息

    从 Story 文件的 Dev Notes 部分提取:
    - 要创建的文件
    - 要修改的文件
    - API 端点引用
    - Schema 引用

    Args:
        story_path: Story 文件路径

    Returns:
        StoryDependency 或 None (如果文件不存在)
    """
    if not story_path.exists():
        return None

    content = story_path.read_text(encoding='utf-8')
    story_id = story_path.stem.replace('.story', '').replace('story-', '')

    dep = StoryDependency(story_id=story_id)

    # 提取要创建的文件
    # 匹配模式: "创建文件: path/to/file.py" 或 "Create: path/to/file.py"
    create_patterns = [
        r'创建(?:文件)?[：:]\s*[`"]?([^\s`"]+\.(?:py|ts|tsx|js|jsx|json|yaml|yml))[`"]?',
        r'[Cc]reate[：:]?\s*[`"]?([^\s`"]+\.(?:py|ts|tsx|js|jsx|json|yaml|yml))[`"]?',
        r'新建[：:]\s*[`"]?([^\s`"]+\.(?:py|ts|tsx|js|jsx|json|yaml|yml))[`"]?',
        r'- `([^`]+\.(?:py|ts|tsx|js|jsx|json|yaml|yml))`\s*\(新\)',
    ]

    for pattern in create_patterns:
        matches = re.findall(pattern, content)
        dep.files_to_create.extend(matches)

    # 提取要修改的文件
    # 匹配模式: "修改文件: path/to/file.py" 或 "Modify: path/to/file.py"
    modify_patterns = [
        r'修改(?:文件)?[：:]\s*[`"]?([^\s`"]+\.(?:py|ts|tsx|js|jsx|json|yaml|yml))[`"]?',
        r'[Mm]odify[：:]?\s*[`"]?([^\s`"]+\.(?:py|ts|tsx|js|jsx|json|yaml|yml))[`"]?',
        r'更新[：:]\s*[`"]?([^\s`"]+\.(?:py|ts|tsx|js|jsx|json|yaml|yml))[`"]?',
        r'- `([^`]+\.(?:py|ts|tsx|js|jsx|json|yaml|yml))`\s*\(改\)',
    ]

    for pattern in modify_patterns:
        matches = re.findall(pattern, content)
        dep.files_to_modify.extend(matches)

    # 提取 API 端点
    # 匹配模式: "POST /api/v1/canvas" 或 "GET /api/agents"
    api_pattern = r'(?:GET|POST|PUT|DELETE|PATCH)\s+(/[^\s\)]+)'
    dep.api_endpoints = re.findall(api_pattern, content)

    # 提取 Schema 引用
    # 匹配模式: "specs/data/xxx.schema.json" 或 "specs/api/xxx.openapi.yml"
    schema_pattern = r'specs/(?:data|api)/([^\s`"]+\.(?:schema\.json|openapi\.yml))'
    dep.schema_refs = re.findall(schema_pattern, content)

    # 去重
    dep.files_to_create = list(set(dep.files_to_create))
    dep.files_to_modify = list(set(dep.files_to_modify))
    dep.api_endpoints = list(set(dep.api_endpoints))
    dep.schema_refs = list(set(dep.schema_refs))

    return dep


async def parse_story_files(
    story_ids: List[str],
    base_path: Path,
) -> Dict[str, StoryDependency]:
    """
    并行解析多个 Story 文件

    Args:
        story_ids: Story ID 列表
        base_path: 项目根目录

    Returns:
        Story ID -> StoryDependency 映射
    """
    tasks = []
    for story_id in story_ids:
        # 尝试多种命名约定
        possible_paths = [
            base_path / "docs" / "stories" / f"{story_id}.story.md",
            base_path / "docs" / "stories" / f"story-{story_id}.md",
            base_path / "docs" / "stories" / f"{story_id}.md",
        ]

        for path in possible_paths:
            if path.exists():
                tasks.append(parse_story_file(path))
                break
        else:
            # 如果没找到，尝试第一个路径
            tasks.append(parse_story_file(possible_paths[0]))

    results = await asyncio.gather(*tasks)

    dependencies = {}
    for story_id, result in zip(story_ids, results):
        if result:
            dependencies[story_id] = result
        else:
            # 创建空依赖
            dependencies[story_id] = StoryDependency(story_id=story_id)

    return dependencies


# ============================================================================
# 冲突检测
# ============================================================================

def detect_conflicts(
    dependencies: Dict[str, StoryDependency],
) -> Tuple[Dict[str, List[str]], List[ConflictInfo]]:
    """
    检测 Story 间的文件冲突

    冲突类型:
    1. CREATE_CONFLICT: 两个 Story 创建同一文件
    2. MODIFY_CONFLICT: 两个 Story 修改同一文件
    3. API_CONFLICT: 两个 Story 修改同一 API 端点

    Args:
        dependencies: Story 依赖映射

    Returns:
        (conflicts_dict, conflict_details)
        - conflicts_dict: "story_a-story_b" -> [conflicting_files]
        - conflict_details: 详细冲突信息列表
    """
    conflicts: Dict[str, List[str]] = {}
    conflict_details: List[ConflictInfo] = []

    story_ids = list(dependencies.keys())

    for i, story_a in enumerate(story_ids):
        for story_b in story_ids[i + 1:]:
            dep_a = dependencies[story_a]
            dep_b = dependencies[story_b]

            conflicting_files: List[str] = []
            conflict_type: Optional[str] = None

            # 检测创建冲突
            create_overlap = set(dep_a.files_to_create) & set(dep_b.files_to_create)
            if create_overlap:
                conflicting_files.extend(create_overlap)
                conflict_type = "CREATE_CONFLICT"

            # 检测修改冲突
            modify_overlap = set(dep_a.files_to_modify) & set(dep_b.files_to_modify)
            if modify_overlap:
                conflicting_files.extend(modify_overlap)
                conflict_type = conflict_type or "MODIFY_CONFLICT"

            # 检测创建-修改冲突
            create_modify_a = set(dep_a.files_to_create) & set(dep_b.files_to_modify)
            create_modify_b = set(dep_b.files_to_create) & set(dep_a.files_to_modify)
            if create_modify_a or create_modify_b:
                conflicting_files.extend(create_modify_a | create_modify_b)
                conflict_type = conflict_type or "MODIFY_CONFLICT"

            # 检测 API 冲突
            api_overlap = set(dep_a.api_endpoints) & set(dep_b.api_endpoints)
            if api_overlap:
                conflicting_files.extend([f"API:{ep}" for ep in api_overlap])
                conflict_type = conflict_type or "API_CONFLICT"

            if conflicting_files:
                key = f"{story_a}-{story_b}"
                conflicts[key] = list(set(conflicting_files))
                conflict_details.append(ConflictInfo(
                    story_a=story_a,
                    story_b=story_b,
                    conflicting_files=list(set(conflicting_files)),
                    conflict_type=conflict_type or "MODIFY_CONFLICT",
                ))

    return conflicts, conflict_details


# ============================================================================
# 批次生成 (图着色算法)
# ============================================================================

def generate_batches(
    story_ids: List[str],
    conflicts: Dict[str, List[str]],
) -> List[List[str]]:
    """
    使用贪心图着色算法生成并行批次

    将 Stories 分组，使得同一批次内的 Stories 没有冲突。

    算法:
    1. 构建冲突图 (节点=Story, 边=冲突)
    2. 贪心着色: 按顺序分配颜色，选择最小可用颜色
    3. 同一颜色的 Stories 形成一个批次

    Args:
        story_ids: Story ID 列表
        conflicts: 冲突映射

    Returns:
        批次列表，每个批次是可并行的 Story ID 列表
    """
    if not story_ids:
        return []

    # 构建邻接表
    adj: Dict[str, Set[str]] = defaultdict(set)
    for key in conflicts:
        parts = key.split("-")
        if len(parts) == 2:
            story_a, story_b = parts
            adj[story_a].add(story_b)
            adj[story_b].add(story_a)

    # 贪心着色
    colors: Dict[str, int] = {}

    for story_id in story_ids:
        # 收集邻居的颜色
        neighbor_colors = {colors[n] for n in adj[story_id] if n in colors}

        # 选择最小可用颜色
        color = 0
        while color in neighbor_colors:
            color += 1

        colors[story_id] = color

    # 按颜色分组
    batches: Dict[int, List[str]] = defaultdict(list)
    for story_id, color in colors.items():
        batches[color].append(story_id)

    # 转换为列表
    return [batches[c] for c in sorted(batches.keys())]


# ============================================================================
# 模式推荐
# ============================================================================

def recommend_mode(
    story_ids: List[str],
    conflicts: Dict[str, List[str]],
    batches: List[List[str]],
) -> Literal["parallel", "linear", "hybrid"]:
    """
    推荐执行模式

    规则:
    - 无冲突 & 单批次 → parallel
    - 全冲突 (每对都冲突) → linear
    - 部分冲突 → hybrid

    Args:
        story_ids: Story ID 列表
        conflicts: 冲突映射
        batches: 生成的批次

    Returns:
        推荐的执行模式
    """
    if len(story_ids) <= 1:
        return "linear"

    if not conflicts:
        return "parallel"

    # 计算冲突比例
    total_pairs = len(story_ids) * (len(story_ids) - 1) / 2
    conflict_pairs = len(conflicts)
    conflict_ratio = conflict_pairs / total_pairs if total_pairs > 0 else 0

    # 检查批次效率
    batch_efficiency = len(story_ids) / len(batches) if batches else 1

    if conflict_ratio >= 0.8:
        return "linear"
    elif conflict_ratio == 0:
        return "parallel"
    elif batch_efficiency >= 2:
        return "hybrid"
    else:
        return "linear"


# ============================================================================
# 主分析函数
# ============================================================================

async def analyze_dependencies(
    story_ids: List[str],
    base_path: Path,
) -> Dict:
    """
    分析 Stories 依赖关系

    完整分析流程:
    1. 解析 Story 文件
    2. 检测冲突
    3. 生成批次
    4. 推荐模式

    Args:
        story_ids: Story ID 列表
        base_path: 项目根目录

    Returns:
        分析结果字典:
        - dependencies: Story 依赖映射
        - conflicts: 冲突映射
        - recommended_mode: 推荐模式
        - batches: 并行批次
        - conflict_details: 冲突详情
    """
    print(f"[DependencyAnalyzer] Analyzing {len(story_ids)} stories...")

    # Step 1: 解析 Story 文件
    dependencies = await parse_story_files(story_ids, base_path)
    print(f"[DependencyAnalyzer] Parsed {len(dependencies)} story files")

    # Step 2: 检测冲突
    conflicts, conflict_details = detect_conflicts(dependencies)
    print(f"[DependencyAnalyzer] Found {len(conflicts)} conflict pairs")

    # Step 3: 生成批次
    batches = generate_batches(story_ids, conflicts)
    print(f"[DependencyAnalyzer] Generated {len(batches)} batches")

    # Step 4: 推荐模式
    recommended_mode = recommend_mode(story_ids, conflicts, batches)
    print(f"[DependencyAnalyzer] Recommended mode: {recommended_mode}")

    return {
        "dependencies": {k: vars(v) for k, v in dependencies.items()},
        "conflicts": conflicts,
        "recommended_mode": recommended_mode,
        "batches": batches,
        "conflict_details": [vars(c) for c in conflict_details],
    }


# ============================================================================
# 辅助函数
# ============================================================================

def print_analysis_report(result: Dict) -> str:
    """
    生成分析报告

    Args:
        result: analyze_dependencies 返回的结果

    Returns:
        格式化的报告字符串
    """
    lines = [
        "=" * 60,
        "BMad Dependency Analysis Report",
        "=" * 60,
        "",
        f"Stories Analyzed: {len(result['dependencies'])}",
        f"Conflicts Found: {len(result['conflicts'])}",
        f"Batches Generated: {len(result['batches'])}",
        f"Recommended Mode: {result['recommended_mode'].upper()}",
        "",
    ]

    # 批次详情
    lines.append("Parallel Batches:")
    for i, batch in enumerate(result['batches'], 1):
        lines.append(f"  Batch {i}: {', '.join(batch)}")

    # 冲突详情
    if result['conflict_details']:
        lines.append("")
        lines.append("Conflicts:")
        for conflict in result['conflict_details']:
            lines.append(f"  {conflict['story_a']} <-> {conflict['story_b']}: "
                        f"{', '.join(conflict['conflicting_files'][:3])}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == "__main__":
    import asyncio

    async def main():
        # 测试分析
        result = await analyze_dependencies(
            story_ids=["15.1", "15.2", "15.3"],
            base_path=Path("."),
        )
        print(print_analysis_report(result))

    asyncio.run(main())
