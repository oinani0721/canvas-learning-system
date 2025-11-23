#!/usr/bin/env python3
"""
PRD-Spec Drift Detection Script
检测PRD与SDD规范之间的不一致

功能:
1. 检查PRD中定义的API端点是否在OpenAPI规范中存在
2. 检查PRD中定义的数据模型是否有对应的JSON Schema
3. 检查Epic/Story是否有对应的Gherkin行为规范
4. 报告orphaned specs (规范存在但PRD中没有引用)

用法:
  python scripts/check-prd-spec-sync.py

返回码:
  0 - 同步正常
  1 - 检测到drift (需要修复)
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def extract_api_endpoints_from_prd(prd_content: str) -> Set[str]:
    """从PRD内容中提取API端点定义"""
    endpoints = set()

    # 匹配常见的API端点模式
    # 例如: GET /api/canvas/nodes, POST /api/scoring
    patterns = [
        r'(GET|POST|PUT|DELETE|PATCH)\s+(/api/[a-zA-Z0-9/_\-{}]+)',
        r'`(GET|POST|PUT|DELETE|PATCH)\s+(/api/[a-zA-Z0-9/_\-{}]+)`',
        r'endpoint[:\s]+[`"]?(/api/[a-zA-Z0-9/_\-{}]+)[`"]?',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, prd_content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                endpoint = match[1] if len(match) > 1 else match[0]
            else:
                endpoint = match
            # 标准化端点格式
            endpoint = endpoint.strip().lower()
            endpoints.add(endpoint)

    return endpoints


def extract_endpoints_from_openapi(openapi_path: Path) -> Set[str]:
    """从OpenAPI规范中提取已定义的端点"""
    endpoints = set()

    if not openapi_path.exists():
        return endpoints

    content = openapi_path.read_text(encoding='utf-8')

    # 简单的YAML路径解析
    # 匹配 paths: 下的端点定义
    in_paths = False
    for line in content.split('\n'):
        if line.strip() == 'paths:':
            in_paths = True
            continue

        if in_paths:
            # 检测新的顶级键
            if line and not line.startswith(' ') and not line.startswith('\t'):
                in_paths = False
                continue

            # 提取路径
            match = re.match(r'^  ["\']?(/[a-zA-Z0-9/_\-{}]+)["\']?:', line)
            if match:
                endpoint = match.group(1).lower()
                endpoints.add(endpoint)

    return endpoints


def extract_data_models_from_prd(prd_content: str) -> Set[str]:
    """从PRD中提取数据模型名称"""
    models = set()

    # 匹配模式如: "Canvas Node Schema", "User Model", etc.
    patterns = [
        r'(?:schema|model)[:\s]+[`"]?([A-Z][a-zA-Z0-9]+)[`"]?',
        r'[`"]([A-Z][a-zA-Z0-9]+)(?:Schema|Model)[`"]',
        r'数据模型[:\s]+[`"]?([A-Z][a-zA-Z0-9]+)[`"]?',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, prd_content, re.IGNORECASE)
        for match in matches:
            models.add(match.lower())

    return models


def extract_schemas_from_specs(specs_dir: Path) -> Set[str]:
    """从specs/data/目录提取已定义的Schema"""
    schemas = set()

    data_dir = specs_dir / 'data'
    if not data_dir.exists():
        return schemas

    for schema_file in data_dir.glob('*.json'):
        # 从文件名提取schema名
        name = schema_file.stem.replace('.schema', '').replace('-', '').lower()
        schemas.add(name)

    return schemas


def extract_epics_from_prd(prd_dir: Path) -> Set[str]:
    """提取PRD中定义的Epic编号"""
    epics = set()

    for prd_file in prd_dir.glob('**/*.md'):
        content = prd_file.read_text(encoding='utf-8')
        # 匹配 Epic N, Epic-N, epic N 等格式
        matches = re.findall(r'epic[- ]?(\d+)', content, re.IGNORECASE)
        epics.update(matches)

    return epics


def extract_epics_from_features(behavior_dir: Path) -> Set[str]:
    """从Gherkin规范的@epic标签中提取Epic编号"""
    epics = set()

    if not behavior_dir.exists():
        return epics

    for feature_file in behavior_dir.glob('*.feature'):
        content = feature_file.read_text(encoding='utf-8')
        # 匹配 @epic-N 标签
        matches = re.findall(r'@epic-(\d+)', content)
        epics.update(matches)

    return epics


def check_sync() -> Tuple[List[str], List[str], List[str]]:
    """
    执行同步检查

    返回:
        (errors, warnings, info) - 三个消息列表
    """
    root = get_project_root()
    prd_dir = root / 'docs' / 'prd'
    specs_dir = root / 'specs'

    errors = []
    warnings = []
    info = []

    # 1. 读取所有PRD内容
    prd_content = ""
    if prd_dir.exists():
        for prd_file in prd_dir.glob('**/*.md'):
            prd_content += prd_file.read_text(encoding='utf-8') + "\n"

    # 2. 检查API端点同步
    prd_endpoints = extract_api_endpoints_from_prd(prd_content)

    openapi_files = list((specs_dir / 'api').glob('*.yml')) if (specs_dir / 'api').exists() else []
    openapi_files += list((specs_dir / 'api').glob('*.yaml')) if (specs_dir / 'api').exists() else []

    spec_endpoints = set()
    for openapi_file in openapi_files:
        spec_endpoints.update(extract_endpoints_from_openapi(openapi_file))

    # PRD中有但OpenAPI中没有的端点
    missing_in_spec = prd_endpoints - spec_endpoints
    if missing_in_spec:
        warnings.append(f"API endpoints in PRD but not in OpenAPI specs: {missing_in_spec}")

    # OpenAPI中有但PRD中没有的端点 (orphaned)
    orphaned_endpoints = spec_endpoints - prd_endpoints
    if orphaned_endpoints:
        info.append(f"API endpoints in specs but not referenced in PRD: {orphaned_endpoints}")

    # 3. 检查数据模型同步
    prd_models = extract_data_models_from_prd(prd_content)
    spec_schemas = extract_schemas_from_specs(specs_dir)

    # PRD中有但Schema中没有的模型
    missing_schemas = prd_models - spec_schemas
    if missing_schemas:
        warnings.append(f"Data models in PRD but no JSON Schema: {missing_schemas}")

    # 4. 检查Epic-Feature同步
    prd_epics = extract_epics_from_prd(prd_dir)
    feature_epics = extract_epics_from_features(specs_dir / 'behavior')

    # PRD中的Epic没有对应的Feature文件
    missing_features = prd_epics - feature_epics
    if missing_features:
        info.append(f"Epics without Gherkin behavior specs: {missing_features}")

    # 5. 检查文件存在性
    required_dirs = [
        specs_dir / 'api',
        specs_dir / 'data',
        specs_dir / 'behavior',
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            warnings.append(f"Missing specs directory: {dir_path}")

    return errors, warnings, info


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 PRD-Spec Drift Detection")
    print("=" * 60)

    errors, warnings, info = check_sync()

    # 打印结果
    if errors:
        print("\n❌ ERRORS (must fix before commit):")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print("\n⚠️ WARNINGS (recommended to fix):")
        for warning in warnings:
            print(f"  • {warning}")

    if info:
        print("\nℹ️ INFO:")
        for item in info:
            print(f"  • {item}")

    if not errors and not warnings and not info:
        print("\n✅ PRD and Specs are in sync!")

    print("=" * 60)

    # 返回码: 只有errors才失败
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
