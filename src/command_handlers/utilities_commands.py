"""
Canvas学习系统 - 实用工具命令处理器

实现文件处理和验证相关的斜杠命令处理器。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from slash_command_system import CommandExecutionContext

async def handle_validate_command(context: CommandExecutionContext) -> Dict[str, Any]:
    """处理Canvas文件验证命令

    Args:
        context: 命令执行上下文

    Returns:
        Dict: 验证结果
    """
    canvas_file = context.parameters.get('canvas_file')
    check_types = context.parameters.get('check_types', 'all')
    fix = context.parameters.get('fix', False)

    try:
        # 检查文件是否存在
        if not os.path.exists(canvas_file):
            return {
                "success": False,
                "error": f"Canvas文件不存在: {canvas_file}"
            }

        # 执行验证
        validation_results = await _validate_canvas_file(
            canvas_file, check_types
        )

        # 如果需要修复且存在错误
        if fix and validation_results.get("has_errors"):
            fix_results = await _fix_canvas_errors(
                canvas_file, validation_results.get("errors", [])
            )
            validation_results["fix_results"] = fix_results

        result = {
            "success": True,
            "type": "canvas_validation",
            "canvas_file": canvas_file,
            "check_types": check_types,
            "validation_results": validation_results,
            "validated_at": datetime.now().isoformat()
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"验证Canvas文件失败: {str(e)}",
            "canvas_file": canvas_file
        }

async def handle_export_command(context: CommandExecutionContext) -> Dict[str, Any]:
    """处理Canvas导出命令

    Args:
        context: 命令执行上下文

    Returns:
        Dict: 导出结果
    """
    canvas_file = context.parameters.get('canvas_file')
    export_format = context.parameters.get('format', 'json')
    output_dir = context.parameters.get('output_dir', 'exports')
    include_metadata = context.parameters.get('include_metadata', True)

    try:
        # 检查源文件
        if not os.path.exists(canvas_file):
            return {
                "success": False,
                "error": f"Canvas文件不存在: {canvas_file}"
            }

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 生成输出文件名
        source_name = Path(canvas_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{source_name}_export_{timestamp}.{export_format}"
        output_path = os.path.join(output_dir, output_filename)

        # 执行导出
        export_result = await _export_canvas_data(
            canvas_file, output_path, export_format, include_metadata
        )

        result = {
            "success": True,
            "type": "canvas_export",
            "source_file": canvas_file,
            "output_file": output_path,
            "export_format": export_format,
            "include_metadata": include_metadata,
            "export_statistics": export_result.get("statistics", {}),
            "exported_at": datetime.now().isoformat()
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"导出Canvas失败: {str(e)}",
            "source_file": canvas_file
        }

# ========== 内部辅助函数 ==========

async def _validate_canvas_file(canvas_file: str, check_types: str) -> Dict[str, Any]:
    """验证Canvas文件"""
    errors = []
    warnings = []
    info = []

    try:
        # 读取Canvas文件
        with open(canvas_file, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        info.append(f"文件大小: {os.path.getsize(canvas_file)} bytes")

        # 基础结构验证
        if check_types in ['all', 'structure']:
            structure_errors = await _validate_canvas_structure(canvas_data)
            errors.extend(structure_errors)

        # 语法验证
        if check_types in ['all', 'syntax']:
            syntax_errors = await _validate_canvas_syntax(canvas_data)
            errors.extend(syntax_errors)

        # 颜色验证
        if check_types in ['all', 'colors']:
            color_errors, color_warnings = await _validate_canvas_colors(canvas_data)
            errors.extend(color_errors)
            warnings.extend(color_warnings)

        # 链接验证
        if check_types in ['all', 'links']:
            link_errors, link_warnings = await _validate_canvas_links(canvas_data)
            errors.extend(link_errors)
            warnings.extend(link_warnings)

        return {
            "has_errors": len(errors) > 0,
            "has_warnings": len(warnings) > 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "validation_summary": {
                "total_nodes": len(canvas_data.get('nodes', [])),
                "total_edges": len(canvas_data.get('edges', [])),
                "file_version": canvas_data.get('version', 'unknown')
            }
        }

    except json.JSONDecodeError as e:
        return {
            "has_errors": True,
            "error_count": 1,
            "errors": [{"type": "json_syntax", "message": f"JSON格式错误: {str(e)}"}],
            "warnings": [],
            "info": [],
            "validation_summary": {}
        }

async def _validate_canvas_structure(canvas_data: Dict) -> List[Dict]:
    """验证Canvas文件结构"""
    errors = []

    # 检查必需字段
    required_fields = ['nodes', 'edges']
    for field in required_fields:
        if field not in canvas_data:
            errors.append({
                "type": "missing_field",
                "message": f"缺少必需字段: {field}"
            })

    # 检查nodes字段
    if 'nodes' in canvas_data:
        if not isinstance(canvas_data['nodes'], list):
            errors.append({
                "type": "invalid_type",
                "message": "nodes字段必须是数组"
            })
        else:
            # 验证每个节点
            for i, node in enumerate(canvas_data['nodes']):
                node_errors = await _validate_node_structure(node, i)
                errors.extend(node_errors)

    # 检查edges字段
    if 'edges' in canvas_data:
        if not isinstance(canvas_data['edges'], list):
            errors.append({
                "type": "invalid_type",
                "message": "edges字段必须是数组"
            })

    return errors

async def _validate_node_structure(node: Dict, index: int) -> List[Dict]:
    """验证节点结构"""
    errors = []
    required_fields = ['id', 'type', 'x', 'y']

    for field in required_fields:
        if field not in node:
            errors.append({
                "type": "missing_node_field",
                "message": f"节点 {index} 缺少必需字段: {field}",
                "node_id": node.get('id', f'node_{index}')
            })

    # 检查节点类型
    if 'type' in node:
        valid_types = ['text', 'file', 'group']
        if node['type'] not in valid_types:
            errors.append({
                "type": "invalid_node_type",
                "message": f"节点 {node.get('id', index)} 类型无效: {node['type']}",
                "node_id": node.get('id', f'node_{index}')
            })

    # 检查坐标
    if 'x' in node and not isinstance(node['x'], (int, float)):
        errors.append({
            "type": "invalid_coordinate",
            "message": f"节点 {node.get('id', index)} 的x坐标必须是数字",
            "node_id": node.get('id', f'node_{index}')
        })

    if 'y' in node and not isinstance(node['y'], (int, float)):
        errors.append({
            "type": "invalid_coordinate",
            "message": f"节点 {node.get('id', index)} 的y坐标必须是数字",
            "node_id": node.get('id', f'node_{index}')
        })

    return errors

async def _validate_canvas_syntax(canvas_data: Dict) -> List[Dict]:
    """验证Canvas语法"""
    errors = []

    # 检查节点ID唯一性
    if 'nodes' in canvas_data:
        node_ids = []
        for node in canvas_data['nodes']:
            if 'id' in node:
                if node['id'] in node_ids:
                    errors.append({
                        "type": "duplicate_id",
                        "message": f"节点ID重复: {node['id']}",
                        "node_id": node['id']
                    })
                node_ids.append(node['id'])

    # 检查边的引用
    if 'edges' in canvas_data and 'nodes' in canvas_data:
        node_ids = set(node.get('id', '') for node in canvas_data['nodes'])
        for edge in canvas_data['edges']:
            if 'fromNode' in edge and edge['fromNode'] not in node_ids:
                errors.append({
                    "type": "invalid_edge_reference",
                    "message": f"边的fromNode引用了不存在的节点: {edge['fromNode']}",
                    "edge_id": edge.get('id', 'unknown')
                })
            if 'toNode' in edge and edge['toNode'] not in node_ids:
                errors.append({
                    "type": "invalid_edge_reference",
                    "message": f"边的toNode引用了不存在的节点: {edge['toNode']}",
                    "edge_id": edge.get('id', 'unknown')
                })

    return errors

async def _validate_canvas_colors(canvas_data: Dict) -> tuple[List[Dict], List[Dict]]:
    """验证Canvas颜色"""
    errors = []
    warnings = []

    valid_colors = ["1", "2", "3", "4", "5", "6"]
    color_mapping = {
        "1": "红色",
        "2": "绿色",
        "3": "紫色",
        "4": "橙色",
        "5": "蓝色",
        "6": "黄色"
    }

    if 'nodes' in canvas_data:
        color_counts = {}
        for node in canvas_data['nodes']:
            if 'color' in node:
                color = node['color']
                color_counts[color] = color_counts.get(color, 0) + 1

                if color not in valid_colors:
                    errors.append({
                        "type": "invalid_color",
                        "message": f"节点 {node.get('id', 'unknown')} 颜色无效: {color}",
                        "node_id": node.get('id', 'unknown')
                    })

        # 颜色使用统计
        if color_counts:
            for color, count in color_counts.items():
                if color in color_mapping:
                    warnings.append({
                        "type": "color_usage",
                        "message": f"使用了 {color_mapping[color]} {count} 次"
                    })

    return errors, warnings

async def _validate_canvas_links(canvas_data: Dict) -> tuple[List[Dict], List[Dict]]:
    """验证Canvas链接"""
    errors = []
    warnings = []

    if 'nodes' in canvas_data:
        for node in canvas_data['nodes']:
            if node.get('type') == 'file':
                file_path = node.get('file', '')
                if file_path and not os.path.exists(file_path):
                    warnings.append({
                        "type": "missing_file",
                        "message": f"文件节点引用的文件不存在: {file_path}",
                        "node_id": node.get('id', 'unknown')
                    })

    return errors, warnings

async def _fix_canvas_errors(canvas_file: str, errors: List[Dict]) -> Dict[str, Any]:
    """修复Canvas错误"""
    try:
        # 读取原始文件
        with open(canvas_file, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        fixes_applied = []

        # 创建备份
        backup_file = f"{canvas_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(canvas_file, backup_file)
        fixes_applied.append(f"创建备份文件: {backup_file}")

        # 应用修复
        for error in errors:
            fix_result = await _apply_canvas_fix(canvas_data, error)
            if fix_result:
                fixes_applied.append(fix_result)

        # 保存修复后的文件
        with open(canvas_file, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "fixes_applied": fixes_applied,
            "backup_file": backup_file
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"修复Canvas文件失败: {str(e)}"
        }

async def _apply_canvas_fix(canvas_data: Dict, error: Dict) -> Optional[str]:
    """应用单个修复"""
    error_type = error.get('type')

    if error_type == 'missing_node_field':
        # 这里可以实现具体的修复逻辑
        return f"跳过修复: {error_type}"

    # 其他修复逻辑...

    return None

async def _export_canvas_data(canvas_file: str, output_path: str,
                            export_format: str, include_metadata: bool) -> Dict[str, Any]:
    """导出Canvas数据"""
    try:
        # 读取Canvas文件
        with open(canvas_file, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        export_data = {}
        statistics = {}

        if export_format == 'json':
            # JSON导出
            export_data = canvas_data
            if include_metadata:
                export_data['_export_metadata'] = {
                    'exported_at': datetime.now().isoformat(),
                    'source_file': canvas_file,
                    'export_format': export_format,
                    'version': '1.0'
                }

            statistics = {
                'nodes_exported': len(canvas_data.get('nodes', [])),
                'edges_exported': len(canvas_data.get('edges', [])),
                'file_size_bytes': len(json.dumps(export_data, ensure_ascii=False))
            }

        elif export_format == 'markdown':
            # Markdown导出
            export_data = await _convert_to_markdown(canvas_data, include_metadata)
            statistics = {
                'nodes_exported': len(canvas_data.get('nodes', [])),
                'edges_exported': len(canvas_data.get('edges', [])),
                'word_count': len(export_data.split())
            }

        elif export_format == 'html':
            # HTML导出
            export_data = await _convert_to_html(canvas_data, include_metadata)
            statistics = {
                'nodes_exported': len(canvas_data.get('nodes', [])),
                'edges_exported': len(canvas_data.get('edges', [])),
                'html_size_bytes': len(export_data)
            }

        # 保存导出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            if export_format == 'json':
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            else:
                f.write(export_data)

        return {
            "success": True,
            "statistics": statistics
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"导出失败: {str(e)}"
        }

async def _convert_to_markdown(canvas_data: Dict, include_metadata: bool) -> str:
    """转换为Markdown格式"""
    markdown = f"# Canvas内容导出\n\n"

    if include_metadata:
        markdown += f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # 导出节点
    if 'nodes' in canvas_data:
        markdown += "## 节点内容\n\n"
        for i, node in enumerate(canvas_data['nodes']):
            markdown += f"### 节点 {i+1}\n"
            if node.get('text'):
                markdown += f"{node.get('text', '')}\n\n"
            if node.get('color'):
                color_names = {"1": "红色", "2": "绿色", "3": "紫色", "6": "黄色"}
                color_name = color_names.get(node.get('color'), "未知")
                markdown += f"**颜色**: {color_name}\n\n"

    return markdown

async def _convert_to_html(canvas_data: Dict, include_metadata: bool) -> str:
    """转换为HTML格式"""
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Canvas内容导出</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .node { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .node-red { border-left: 5px solid #ff6b6b; }
        .node-green { border-left: 5px solid #51cf66; }
        .node-purple { border-left: 5px solid #845ef7; }
        .node-yellow { border-left: 5px solid #ffd43b; }
    </style>
</head>
<body>
    <h1>Canvas内容导出</h1>
"""

    if include_metadata:
        html += f"<p><strong>导出时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"

    # 导出节点
    if 'nodes' in canvas_data:
        html += "<h2>节点内容</h2>"
        for node in canvas_data['nodes']:
            color_class = f"node-{node.get('color', 'default')}"
            html += f'<div class="node {color_class}">'
            if node.get('text'):
                html += f"<p>{node.get('text', '')}</p>"
            html += "</div>"

    html += "</body></html>"
    return html