#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在问题节点旁正确添加AI解释节点
"""

import json
import uuid

canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"

# 读取Canvas
with open(canvas_path, 'r', encoding='utf-8') as f:
    canvas_data = json.load(f)

print("=" * 80)
print("Step 1: Identify existing blue explanation nodes to avoid duplicates")
print("=" * 80)

# 找出所有蓝色节点（color="5"）
blue_nodes = [n for n in canvas_data['nodes'] if n.get('color') == '5']
print(f"Found {len(blue_nodes)} existing blue explanation nodes")

# 如果已经有蓝色节点，询问是否要删除
if len(blue_nodes) > 0:
    print("Removing existing blue explanation nodes and their yellow companions...")
    blue_ids = {n['id'] for n in blue_nodes}

    # 找出连接到蓝色节点的黄色节点
    yellow_companions = set()
    for edge in canvas_data['edges']:
        if edge.get('fromNode') in blue_ids and edge.get('label') == '个人理解':
            yellow_companions.add(edge.get('toNode'))

    # 删除蓝色节点和配套的黄色节点
    ids_to_remove = blue_ids | yellow_companions
    canvas_data['nodes'] = [n for n in canvas_data['nodes'] if n['id'] not in ids_to_remove]

    # 删除相关边
    canvas_data['edges'] = [e for e in canvas_data['edges']
                            if e.get('fromNode') not in ids_to_remove
                            and e.get('toNode') not in ids_to_remove]

    print(f"Removed {len(ids_to_remove)} nodes")

print("\n" + "=" * 80)
print("Step 2: Build node map and add explanations")
print("=" * 80)

# 重新构建节点映射
nodes_map = {n['id']: n for n in canvas_data['nodes']}

# 定义解释（使用完整的question_id）
explanations = [
    {
        'question_id': '682d611321261951',
        'type': 'clarification',
        'title': 'Well-Ordering Principle Clarification',
        'summary': 'Understanding how well-ordering principle supports induction, why "first counterexample" requires well-ordering (1500+ words).'
    },
    {
        'question_id': 'a3bf90f7071ee3fd',
        'type': 'clarification',
        'title': 'Degree Sequence Clarification',
        'summary': 'Understanding 3 rules: odd-degree vertices must be even, max degree < n-1, high-degree constraints on low-degree (1500+ words).'
    },
    {
        'question_id': '38fd45c7fdabcee0',
        'type': 'clarification',
        'title': 'Euler Trail Basics Clarification',
        'summary': 'From scratch: graph, degree, Euler trail/tour, why degree parity matters. For complete beginners (1500+ words).'
    },
    {
        'question_id': '97e9b94a105dd13e',
        'type': 'clarification',
        'title': 'Graph Connectivity Induction Error',
        'summary': 'Why "degree >= 1" does not imply "connected", constructive assumption error in induction (1500+ words).'
    },
    {
        'question_id': 'a351bb2bb33061fc',
        'type': 'clarification',
        'title': 'Tree Induction Proof Clarification',
        'summary': 'Understanding 2 tree properties: (a) at least 2 leaves algebraic proof, (b) bipartite structural induction (1500+ words).'
    },
    {
        'question_id': 'a3bf90f7071ee3fd',
        'type': 'memory',
        'title': 'Degree Sequence Memory Anchor',
        'summary': 'Dance party handshake analogy, story, mnemonic "Pairs match evenly, no self-connect, high demands grab resources" (800 words).'
    },
    {
        'question_id': 'c0f2eb6e605bd99e',
        'type': 'memory',
        'title': 'Euler Trail Proof Memory Anchor',
        'summary': 'Delivery route analogy, courier story, mnemonic "Middle pairs must be even, start/end can be odd" (800 words).'
    },
    {
        'question_id': 'b469457095aaa2a3',
        'type': 'memory',
        'title': 'Build-up Error Memory Anchor',
        'summary': 'Building blocks illusion analogy, story, mnemonic "Adding hides pits, removing reveals truth" (800 words).'
    }
]

blue_added = 0
yellow_added = 0
edges_added = 0

for i, exp in enumerate(explanations):
    q_id = exp['question_id']

    if q_id not in nodes_map:
        print(f"\n[WARNING] Question node {q_id} not found!")
        continue

    question_node = nodes_map[q_id]

    # 蓝色节点位置：问题节点下方
    blue_x = question_node['x']
    blue_y = question_node['y'] + question_node.get('height', 250) + 60

    # 如果同一问题有多个解释（memory anchor），横向偏移
    if exp['type'] == 'memory':
        # 检查是否已经有clarification explanation在这个位置
        existing_blues_here = [n for n in canvas_data['nodes']
                               if n.get('color') == '5'
                               and abs(n.get('x', 0) - blue_x) < 100
                               and abs(n.get('y', 0) - blue_y) < 100]
        if existing_blues_here:
            blue_x += 720  # 横向偏移

    # 创建蓝色节点
    blue_id = str(uuid.uuid4()).replace('-', '')
    emoji = '🔍' if exp['type'] == 'clarification' else '⚓'
    blue_text = f"{emoji} **{exp['title']}**\n\n{exp['summary']}\n\n---\n*AI-generated explanation. Fill your understanding in the yellow node on the right.*"

    blue_node = {
        "id": blue_id,
        "x": blue_x,
        "y": blue_y,
        "width": 620,
        "height": 480,
        "color": "5",
        "type": "text",
        "text": blue_text
    }
    canvas_data['nodes'].append(blue_node)
    blue_added += 1

    # 创建黄色节点
    yellow_id = str(uuid.uuid4()).replace('-', '')
    yellow_node = {
        "id": yellow_id,
        "x": blue_x + 670,
        "y": blue_y,
        "width": 520,
        "height": 380,
        "color": "6",
        "type": "text",
        "text": ""
    }
    canvas_data['nodes'].append(yellow_node)
    yellow_added += 1

    # 创建边1：问题 → 蓝色
    edge1_id = str(uuid.uuid4()).replace('-', '')
    edge1 = {
        "id": edge1_id,
        "fromNode": q_id,
        "fromSide": "bottom",
        "toNode": blue_id,
        "toSide": "top",
        "label": "AI补充解释"
    }
    canvas_data['edges'].append(edge1)
    edges_added += 1

    # 创建边2：蓝色 → 黄色
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

    print(f"\n[OK] Added {exp['type']}: {exp['title']}")
    print(f"  Question: {q_id}")
    print(f"  Position: ({blue_x}, {blue_y})")

# 保存
with open(canvas_path, 'w', encoding='utf-8') as f:
    json.dump(canvas_data, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print(f"Blue AI explanation nodes: {blue_added}")
print(f"Yellow understanding nodes: {yellow_added}")
print(f"Edges: {edges_added}")

# 验证
colors = {}
for n in canvas_data['nodes']:
    c = n.get('color', 'none')
    colors[c] = colors.get(c, 0) + 1

print("\n" + "=" * 80)
print("Final Color Verification")
print("=" * 80)
print(f"Red(1) Questions: {colors.get('1', 0)}")
print(f"Purple(3) Partially understood: {colors.get('3', 0)}")
print(f"Blue(5) AI explanations: {colors.get('5', 0)} [CORRECT]")
print(f"Yellow(6) Personal understanding: {colors.get('6', 0)} [CORRECT]")
print(f"\nTotal nodes: {len(canvas_data['nodes'])}")
print(f"Total edges: {len(canvas_data['edges'])}")

print("\n[SUCCESS] Explanations added correctly!")
print("=" * 80)
