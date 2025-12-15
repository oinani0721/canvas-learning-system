#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为Canvas添加AI生成的解释节点（蓝色）和配套的空白黄色节点
"""

import json
import uuid
from datetime import datetime

canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"

# 读取Canvas数据
with open(canvas_path, 'r', encoding='utf-8') as f:
    canvas_data = json.load(f)

# 构建节点映射
nodes_map = {n['id']: n for n in canvas_data['nodes']}

# 定义8个解释的元数据
explanations = [
    {
        'yellow_id': 'fd20a00a626f4113b6d36def0e6b4af1',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '良序原则和归纳证明澄清',
        'summary': '理解良序原则如何支撑归纳法，为什么"第一个反例"需要良序原则。包含问题澄清、概念拆解、深度解释、验证总结（1500+字）。'
    },
    {
        'yellow_id': '72eb7c38f730a123',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '度序列判断澄清',
        'summary': '从基础理解度序列的三个判断规则：奇数度顶点必须偶数个、度不能超过n-1、高度顶点对低度顶点的约束。包含握手定理、完全图限制、度的相互约束（1500+字）。'
    },
    {
        'yellow_id': 'f2a82cce25549df0',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '欧拉路径基础知识澄清',
        'summary': '从零开始理解图、度、欧拉迹/环游的概念，为什么度的奇偶性决定欧拉迹的存在性。适合完全小白（1500+字）。'
    },
    {
        'yellow_id': 'e1172d9e21af88c9',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '图连通性归纳证明错误澄清',
        'summary': '理解为什么"每个顶点度≥1"不能推出"图连通"，归纳法中构造性假设的错误，以及如何正确使用归纳法证明图论性质（1500+字）。'
    },
    {
        'yellow_id': 'd3a3c155cfb2ebde',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '树的归纳证明澄清',
        'summary': '理解树的两个性质：(a)至少两个叶子的代数证明，(b)二分图性质的结构归纳证明。适合缺乏基础的学习者（1500+字）。'
    },
    {
        'yellow_id': '72eb7c38f730a123',
        'type': 'memory',
        'emoji': '⚓',
        'title': '度序列判断记忆锚点',
        'summary': '舞会握手游戏类比、舞会风波事件簿故事、口诀"奇偶配对不自连，高度霸位抢资源"。生动记忆三个判断规则（800字）。'
    },
    {
        'yellow_id': '18da353e38a2ac00',
        'type': 'memory',
        'emoji': '⚓',
        'title': '欧拉迹证明记忆锚点',
        'summary': '快递配送路线类比、快递员阿欧的智慧送货法故事、口诀"中间配对必须偶，起终单身可以留；借边成环再剪断，拆路画圈再串钩"（800字）。'
    },
    {
        'yellow_id': '0eb33165683225d3',
        'type': 'memory',
        'emoji': '⚓',
        'title': '构造性错误记忆锚点',
        'summary': '积木搭建假象类比、小李归纳法错误故事、口诀"加法易藏坑，减法见真章"。理解build-up error（800字）。'
    }
]

print("=" * 80)
print("添加AI解释节点到Canvas")
print("=" * 80)

# 统计
blue_count = 0
yellow_count = 0
edge_count = 0

for exp in explanations:
    yellow_id = exp['yellow_id']

    # 找到对应的黄色节点
    if yellow_id not in nodes_map:
        print(f"\n警告：找不到节点 {yellow_id[:16]}...")
        continue

    yellow_node = nodes_map[yellow_id]

    # 蓝色解释节点位置（黄色节点右侧）
    blue_x = yellow_node['x'] + yellow_node.get('width', 500) + 100
    blue_y = yellow_node['y']

    # 如果是同一个黄色节点的第二个解释，调整y坐标
    if exp['type'] == 'memory' and yellow_id == '72eb7c38f730a123':
        blue_y += 900  # 向下偏移

    # 创建蓝色解释节点
    blue_id = str(uuid.uuid4()).replace('-', '')
    blue_text = f"{exp['emoji']} **{exp['title']}**\n\n{exp['summary']}\n\n---\n*此节点包含AI生成的完整解释内容。请在右侧黄色节点填写你的个人理解。*"

    blue_node = {
        "id": blue_id,
        "x": blue_x,
        "y": blue_y,
        "width": 600,
        "height": 500,
        "color": "5",  # 蓝色 - AI解释
        "type": "text",
        "text": blue_text
    }
    canvas_data['nodes'].append(blue_node)
    blue_count += 1

    # 创建配套的空白黄色节点
    new_yellow_id = str(uuid.uuid4()).replace('-', '')
    new_yellow_node = {
        "id": new_yellow_id,
        "x": blue_x + 650,
        "y": blue_y,
        "width": 500,
        "height": 400,
        "color": "6",  # 黄色 - 个人理解
        "type": "text",
        "text": ""  # 空白
    }
    canvas_data['nodes'].append(new_yellow_node)
    yellow_count += 1

    # 创建边
    edge_id = str(uuid.uuid4()).replace('-', '')
    edge = {
        "id": edge_id,
        "fromNode": blue_id,
        "fromSide": "right",
        "toNode": new_yellow_id,
        "toSide": "left",
        "label": "个人理解"
    }
    canvas_data['edges'].append(edge)
    edge_count += 1

    print(f"\n[OK] Added {exp['type']} explanation")
    print(f"  Blue node ID: {blue_id[:16]}...")
    print(f"  Yellow node ID: {new_yellow_id[:16]}...")

# 保存Canvas
with open(canvas_path, 'w', encoding='utf-8') as f:
    json.dump(canvas_data, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("添加完成统计")
print("=" * 80)
print(f"新增蓝色AI解释节点: {blue_count}个")
print(f"新增黄色理解节点: {yellow_count}个")
print(f"新增边: {edge_count}条")

# 颜色验证
color_counts = {}
for node in canvas_data['nodes']:
    color = node.get('color', 'none')
    color_counts[color] = color_counts.get(color, 0) + 1

print("\n" + "=" * 80)
print("Color Verification")
print("=" * 80)
print(f"Red(1) Question nodes: {color_counts.get('1', 0)}")
print(f"Green(2) Fully understood: {color_counts.get('2', 0)}")
print(f"Purple(3) Partially understood: {color_counts.get('3', 0)}")
print(f"Blue(5) AI explanation nodes: {color_counts.get('5', 0)} [OK]")
print(f"Yellow(6) Personal understanding nodes: {color_counts.get('6', 0)} [OK]")

print("\n[SUCCESS] Canvas file updated successfully!")
print("=" * 80)
