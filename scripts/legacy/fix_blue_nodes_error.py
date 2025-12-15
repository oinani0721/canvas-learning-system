#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除Canvas中错误的蓝色问题节点
用户规则：问题节点只能用红色或紫色，蓝色只能用于AI解释文档
"""

import json

# 读取Canvas文件
canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"

with open(canvas_path, 'r', encoding='utf-8') as f:
    canvas_data = json.load(f)

print("=" * 60)
print("检查Canvas中的蓝色节点...")
print("=" * 60)

# 找到所有蓝色节点
blue_nodes = [n for n in canvas_data['nodes'] if n.get('color') == '5']
print(f"\n找到 {len(blue_nodes)} 个蓝色节点")

# 检查这些蓝色节点是否包含问题内容
blue_question_nodes = []
for node in blue_nodes:
    text = node.get('text', '')
    # 如果包含问题标题或拆解标记，就是错误的蓝色问题节点
    if '基础拆解问题' in text or '引导性问题' in text:
        blue_question_nodes.append(node)
        print(f"\n❌ 发现错误的蓝色问题节点:")
        print(f"  ID: {node['id'][:16]}...")
        print(f"  内容前50字: {text[:50]}...")

if not blue_question_nodes:
    print("\n✓ 没有发现错误的蓝色问题节点")
else:
    print(f"\n需要删除 {len(blue_question_nodes)} 个错误的蓝色节点")

    # 获取要删除的节点ID
    ids_to_delete = {node['id'] for node in blue_question_nodes}

    # 删除这些节点
    original_node_count = len(canvas_data['nodes'])
    canvas_data['nodes'] = [n for n in canvas_data['nodes'] if n['id'] not in ids_to_delete]
    print(f"  节点数: {original_node_count} → {len(canvas_data['nodes'])}")

    # 删除相关的边
    original_edge_count = len(canvas_data['edges'])
    canvas_data['edges'] = [
        e for e in canvas_data['edges']
        if e.get('fromNode') not in ids_to_delete and e.get('toNode') not in ids_to_delete
    ]
    print(f"  边数: {original_edge_count} → {len(canvas_data['edges'])}")

    # 保存修改后的Canvas文件
    with open(canvas_path, 'w', encoding='utf-8') as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent='\t')

    print(f"\n✅ 已删除 {len(blue_question_nodes)} 个错误的蓝色节点！")

# 验证最终状态
print("\n" + "=" * 60)
print("验证Canvas最终状态...")
print("=" * 60)

colors = {}
for n in canvas_data['nodes']:
    color = n.get('color', 'none')
    colors[color] = colors.get(color, 0) + 1

print("\n节点颜色统计:")
print(f"  红色(1) - 问题节点: {colors.get('1', 0)}个")
print(f"  绿色(2) - 完全理解: {colors.get('2', 0)}个")
print(f"  紫色(3) - 似懂非懂: {colors.get('3', 0)}个")
print(f"  蓝色(5) - AI解释: {colors.get('5', 0)}个 ⚠️ 应该为0！")
print(f"  黄色(6) - 个人理解: {colors.get('6', 0)}个")
print(f"  无色(none): {colors.get('none', 0)}个")

# 检查是否还有蓝色节点
if colors.get('5', 0) > 0:
    print("\n⚠️ 警告：仍然存在蓝色节点！需要手动检查")
else:
    print("\n✅ 确认：没有蓝色节点，颜色使用正确！")

# 统计边
understanding_edges = [e for e in canvas_data['edges'] if '个人理解' in e.get('label', '')]
decomp_edges = [e for e in canvas_data['edges'] if '基础拆解' in e.get('label', '')]

print(f"\n边统计:")
print(f"  总边数: {len(canvas_data['edges'])}条")
print(f"  '个人理解'边: {len(understanding_edges)}条")
print(f"  '基础拆解'边: {len(decomp_edges)}条")

print("\n" + "=" * 60)
print("修正完成！")
print("=" * 60)
