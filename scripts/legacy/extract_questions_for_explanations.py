#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取需要补充解释的问题内容
"""

import json

canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"
analysis_path = r"C:\Users\ROG\托福\yellow_nodes_analysis.json"

# 读取Canvas和分析结果
with open(canvas_path, 'r', encoding='utf-8') as f:
    canvas_data = json.load(f)

with open(analysis_path, 'r', encoding='utf-8') as f:
    analysis = json.load(f)

# 构建节点ID到节点的映射
nodes_map = {n['id']: n for n in canvas_data['nodes']}

# 构建边的映射：toNode -> fromNode
edges_map = {}
for edge in canvas_data['edges']:
    to_node = edge.get('toNode')
    from_node = edge.get('fromNode')
    if to_node:
        edges_map[to_node] = from_node

print("=" * 80)
print("提取需要解释的问题内容")
print("=" * 80)

# 处理故事化解释请求
story_data = []
for req in analysis['story_requests']:
    yellow_id = req['id']
    # 找到连接到这个黄色节点的问题节点
    question_id = edges_map.get(yellow_id)

    if question_id and question_id in nodes_map:
        question_node = nodes_map[question_id]
        question_text = question_node.get('text', '')

        story_data.append({
            'yellow_id': yellow_id,
            'question_id': question_id,
            'question_text': question_text,
            'user_request': req['text'],
            'position': (req['x'], req['y'])
        })

# 处理澄清解释请求
clarification_data = []
for req in analysis['clarification_requests']:
    yellow_id = req['id']
    # 找到连接到这个黄色节点的问题节点
    question_id = edges_map.get(yellow_id)

    if question_id and question_id in nodes_map:
        question_node = nodes_map[question_id]
        question_text = question_node.get('text', '')

        clarification_data.append({
            'yellow_id': yellow_id,
            'question_id': question_id,
            'question_text': question_text,
            'user_request': req['text'],
            'position': (req['x'], req['y'])
        })

print(f"\n故事化解释请求: {len(story_data)} 个")
print(f"澄清解释请求: {len(clarification_data)} 个")

# 输出故事化解释的问题
if story_data:
    print("\n" + "=" * 80)
    print("需要故事化解释的问题:")
    print("=" * 80)
    for i, data in enumerate(story_data, 1):
        print(f"\n{i}. 问题ID: {data['question_id'][:16]}...")
        print(f"   问题内容: {data['question_text'][:200]}...")
        print(f"   用户要求: {data['user_request']}")

# 输出澄清解释的问题
if clarification_data:
    print("\n" + "=" * 80)
    print("需要澄清解释的问题:")
    print("=" * 80)
    for i, data in enumerate(clarification_data, 1):
        print(f"\n{i}. 问题ID: {data['question_id'][:16]}...")
        print(f"   问题内容: {data['question_text'][:200]}...")
        print(f"   用户要求: {data['user_request'][:100]}...")

# 保存提取结果
result = {
    'story_requests': story_data,
    'clarification_requests': clarification_data
}

with open(r"C:\Users\ROG\托福\questions_for_explanations.json", 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("问题内容已保存到: questions_for_explanations.json")
print("=" * 80)
