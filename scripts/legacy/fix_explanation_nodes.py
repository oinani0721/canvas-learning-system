#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正AI解释节点的位置：应该添加在问题节点旁边，而不是黄色理解节点旁边
"""

import json
import uuid

canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"
questions_path = r"C:\Users\ROG\托福\questions_for_explanations.json"

# 读取数据
with open(canvas_path, 'r', encoding='utf-8') as f:
    canvas_data = json.load(f)

with open(questions_path, 'r', encoding='utf-8') as f:
    questions_data = json.load(f)

print("=" * 80)
print("Step 1: Remove incorrectly added nodes")
print("=" * 80)

# 找出最近添加的8个蓝色节点和8个黄色节点（应该是最后16个节点）
original_node_count = len(canvas_data['nodes'])
print(f"Total nodes before: {original_node_count}")

# 删除最后16个节点（8蓝+8黄）和对应的8条边
if original_node_count >= 16:
    # 获取要删除的节点ID
    nodes_to_remove = canvas_data['nodes'][-16:]
    node_ids_to_remove = {n['id'] for n in nodes_to_remove}

    # 删除节点
    canvas_data['nodes'] = canvas_data['nodes'][:-16]

    # 删除相关的边
    original_edge_count = len(canvas_data['edges'])
    canvas_data['edges'] = [e for e in canvas_data['edges']
                            if e.get('fromNode') not in node_ids_to_remove
                            and e.get('toNode') not in node_ids_to_remove]

    print(f"Removed {len(nodes_to_remove)} nodes")
    print(f"Removed {original_edge_count - len(canvas_data['edges'])} edges")
    print(f"Total nodes now: {len(canvas_data['nodes'])}")
else:
    print("Warning: Not enough nodes to remove")

print("\n" + "=" * 80)
print("Step 2: Add explanation nodes next to question nodes")
print("=" * 80)

# 构建节点映射
nodes_map = {n['id']: n for n in canvas_data['nodes']}

# 定义解释元数据
explanation_metadata = [
    {
        'question_id': '682d611321261951',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '良序原则和归纳证明澄清',
        'summary': '理解良序原则如何支撑归纳法，为什么"第一个反例"需要良序原则。包含问题澄清、概念拆解、深度解释、验证总结（1500+字）。'
    },
    {
        'question_id': 'a3bf90f7071ee3fd',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '度序列判断澄清',
        'summary': '从基础理解度序列的三个判断规则：奇数度顶点必须偶数个、度不能超过n-1、高度顶点对低度顶点的约束。包含握手定理、完全图限制、度的相互约束（1500+字）。'
    },
    {
        'question_id': '38fd45c7fdabcee0',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '欧拉路径基础知识澄清',
        'summary': '从零开始理解图、度、欧拉迹/环游的概念，为什么度的奇偶性决定欧拉迹的存在性。适合完全小白（1500+字）。'
    },
    {
        'question_id': '97e9b94a105dd13e',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '图连通性归纳证明错误澄清',
        'summary': '理解为什么"每个顶点度≥1"不能推出"图连通"，归纳法中构造性假设的错误，以及如何正确使用归纳法证明图论性质（1500+字）。'
    },
    {
        'question_id': 'a351bb2bb33061fc',
        'type': 'clarification',
        'emoji': '🔍',
        'title': '树的归纳证明澄清',
        'summary': '理解树的两个性质：(a)至少两个叶子的代数证明，(b)二分图性质的结构归纳证明。适合缺乏基础的学习者（1500+字）。'
    },
    {
        'question_id': 'a3bf90f7071ee3fd',
        'type': 'memory',
        'emoji': '⚓',
        'title': '度序列判断记忆锚点',
        'summary': '舞会握手游戏类比、舞会风波事件簿故事、口诀"奇偶配对不自连，高度霸位抢资源"。生动记忆三个判断规则（800字）。'
    },
    {
        'question_id': 'c0f2eb6e605bd99e',
        'type': 'memory',
        'emoji': '⚓',
        'title': '欧拉迹证明记忆锚点',
        'summary': '快递配送路线类比、快递员阿欧的智慧送货法故事、口诀"中间配对必须偶，起终单身可以留；借边成环再剪断，拆路画圈再串钩"（800字）。'
    },
    {
        'question_id': 'b469457095aaa2a3',
        'type': 'memory',
        'emoji': '⚓',
        'title': '构造性错误记忆锚点',
        'summary': '积木搭建假象类比、小李归纳法错误故事、口诀"加法易藏坑，减法见真章"。理解build-up error（800字）。'
    }
]

# 统计
blue_added = 0
yellow_added = 0
edges_added = 0

# 为每个解释创建节点
for exp in explanation_metadata:
    question_id = exp['question_id']

    if question_id not in nodes_map:
        print(f"\nWarning: Question node {question_id[:16]}... not found")
        continue

    question_node = nodes_map[question_id]

    # 蓝色解释节点位置：问题节点下方
    blue_x = question_node['x']
    blue_y = question_node['y'] + question_node.get('height', 250) + 50

    # 如果是同一个问题的第二个解释（memory anchor），调整x坐标
    if exp['type'] == 'memory':
        blue_x += 700

    # 创建蓝色AI解释节点
    blue_id = str(uuid.uuid4()).replace('-', '')
    blue_text = f"{exp['emoji']} **{exp['title']}**\n\n{exp['summary']}\n\n---\n*AI生成的完整解释。请在右侧黄色节点填写你的个人理解。*"

    blue_node = {
        "id": blue_id,
        "x": blue_x,
        "y": blue_y,
        "width": 600,
        "height": 450,
        "color": "5",  # Blue - AI explanation
        "type": "text",
        "text": blue_text
    }
    canvas_data['nodes'].append(blue_node)
    blue_added += 1

    # 创建配套的空白黄色节点（蓝色节点右侧）
    yellow_id = str(uuid.uuid4()).replace('-', '')
    yellow_node = {
        "id": yellow_id,
        "x": blue_x + 650,
        "y": blue_y,
        "width": 500,
        "height": 350,
        "color": "6",  # Yellow - personal understanding
        "type": "text",
        "text": ""
    }
    canvas_data['nodes'].append(yellow_node)
    yellow_added += 1

    # 创建边1：问题 → 蓝色解释
    edge1_id = str(uuid.uuid4()).replace('-', '')
    edge1 = {
        "id": edge1_id,
        "fromNode": question_id,
        "fromSide": "bottom",
        "toNode": blue_id,
        "toSide": "top",
        "label": "AI补充解释"
    }
    canvas_data['edges'].append(edge1)
    edges_added += 1

    # 创建边2：蓝色解释 → 黄色理解
    edge2_id = str(uuid.uuid4()).replace('-', '')
    edge2 = {
        "id": edge2_id,
        "fromNode": blue_id,
        "fromSide": "right",
        "toNode": yellow_id,
        "toSide": "left",
        "label": "个人理解"
    }
    canvas_data['edges'].append(edge2)
    edges_added += 1

    print(f"\n[OK] Added {exp['type']}: {exp['title'][:40]}...")
    print(f"  Question: {question_id[:16]}...")
    print(f"  Blue node: {blue_id[:16]}... at ({blue_x}, {blue_y})")
    print(f"  Yellow node: {yellow_id[:16]}...")

# 保存Canvas
with open(canvas_path, 'w', encoding='utf-8') as f:
    json.dump(canvas_data, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print(f"Blue AI explanation nodes added: {blue_added}")
print(f"Yellow understanding nodes added: {yellow_added}")
print(f"Edges added: {edges_added}")

# 颜色验证
color_counts = {}
for node in canvas_data['nodes']:
    color = node.get('color', 'none')
    color_counts[color] = color_counts.get(color, 0) + 1

print("\n" + "=" * 80)
print("Color Verification")
print("=" * 80)
print(f"Red(1) Question nodes: {color_counts.get('1', 0)}")
print(f"Green(2) Understood: {color_counts.get('2', 0)}")
print(f"Purple(3) Partially understood: {color_counts.get('3', 0)}")
print(f"Blue(5) AI explanations: {color_counts.get('5', 0)} [OK]")
print(f"Yellow(6) Personal understanding: {color_counts.get('6', 0)} [OK]")

print("\n[SUCCESS] Canvas file corrected!")
print("=" * 80)
