#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为21个红色问题节点创建配套的空白黄色节点（个人理解输出区）
"""

import json
import uuid

# 读取Canvas文件
canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"

with open(canvas_path, 'r', encoding='utf-8') as f:
    canvas_data = json.load(f)

# 找到所有红色问题节点（color == "1" 且包含问题标记）
question_nodes = []
for node in canvas_data['nodes']:
    if node.get('color') == '1' and node.get('type') == 'text':
        text = node.get('text', '')
        # 检查是否是问题节点（包含问题类型标记）
        if any(marker in text for marker in ['[定义型]', '[实例型]', '[对比型]', '[探索型]']):
            question_nodes.append(node)

print(f"找到 {len(question_nodes)} 个红色问题节点")

# 为每个问题节点创建空白黄色节点
yellow_nodes = []
edges_to_add = []

for question_node in question_nodes:
    q_id = question_node['id']
    q_x = question_node['x']
    q_y = question_node['y']
    q_width = question_node['width']
    q_height = question_node['height']

    # 创建空白黄色节点（在问题节点右侧）
    yellow_id = str(uuid.uuid4()).replace('-', '')
    yellow_x = q_x + q_width + 50  # 右侧50px间隔
    yellow_y = q_y  # 垂直对齐

    yellow_node = {
        "id": yellow_id,
        "x": yellow_x,
        "y": yellow_y,
        "width": 500,
        "height": 250,
        "color": "6",  # 黄色 = 个人理解输出区
        "type": "text",
        "text": ""  # 空白，供用户填写
    }

    yellow_nodes.append(yellow_node)

    # 创建从问题节点到黄色节点的边
    edge_id = str(uuid.uuid4()).replace('-', '')
    edge = {
        "id": edge_id,
        "fromNode": q_id,
        "fromSide": "right",
        "toNode": yellow_id,
        "toSide": "left",
        "label": "个人理解"
    }
    edges_to_add.append(edge)

# 添加新节点和边到Canvas
canvas_data['nodes'].extend(yellow_nodes)
canvas_data['edges'].extend(edges_to_add)

# 保存更新后的Canvas文件
with open(canvas_path, 'w', encoding='utf-8') as f:
    json.dump(canvas_data, f, ensure_ascii=False, indent='\t')

print(f"成功添加了 {len(yellow_nodes)} 个空白黄色节点！")
print(f"创建了 {len(edges_to_add)} 条'个人理解'连接边！")
print(f"\n现在Canvas结构：")
print(f"  - 21个红色问题节点（待回答）")
print(f"  - 21个空白黄色节点（填写个人理解）")
print(f"  - 21条'个人理解'边（连接问题和理解）")
