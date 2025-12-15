#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"

with open(canvas_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找所有问题节点
question_markers = ['[定义型]', '[实例型]', '[对比型]', '[探索型]']
question_nodes = []

for node in data['nodes']:
    text = node.get('text', '')
    if any(marker in text for marker in question_markers):
        question_nodes.append({
            'id': node['id'][:16],
            'color': node.get('color', 'none'),
            'text_preview': text[:60]
        })

print(f"找到 {len(question_nodes)} 个问题节点\n")

# 按颜色分组
by_color = {}
for q in question_nodes:
    color = q['color']
    by_color[color] = by_color.get(color, 0) + 1

print("问题节点颜色统计:")
for color, count in by_color.items():
    color_name = {
        '1': '红色(1)基础问题',
        '3': '紫色(3)进阶问题',
        '5': '蓝色(5)错误!',
        'none': '无色(错误!)'
    }.get(color, f'未知颜色({color})')
    print(f"  {color_name}: {count}个")

print(f"\n示例问题节点:")
for i, q in enumerate(question_nodes[:3], 1):
    print(f"{i}. 颜色:{q['color']} | {q['text_preview']}...")
