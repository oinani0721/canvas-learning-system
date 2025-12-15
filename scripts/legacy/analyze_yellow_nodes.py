#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析Canvas中用户更新的黄色节点，识别需要补充解释的节点
"""

import json
import re

canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"

with open(canvas_path, 'r', encoding='utf-8') as f:
    canvas_data = json.load(f)

print("=" * 80)
print("分析黄色节点需求")
print("=" * 80)

# 找到所有黄色节点
yellow_nodes = [n for n in canvas_data['nodes'] if n.get('color') == '6']
print(f"\n找到 {len(yellow_nodes)} 个黄色节点")

# 分析需求
story_requests = []  # 需要故事化解释
clarification_requests = []  # 需要澄清解释
other_nodes = []  # 其他节点

keywords_story = ['故事', '类比', '记忆', '生动', '形象']
keywords_clarification = ['澄清', '解释', '说明', '不懂', '不理解', '没看懂']

for node in yellow_nodes:
    text = node.get('text', '').strip()

    if not text:  # 空白节点
        continue

    node_id = node['id']

    # 检查是否要求故事化解释
    has_story_request = any(kw in text for kw in keywords_story)

    # 检查是否要求澄清解释
    has_clarification_request = any(kw in text for kw in keywords_clarification)

    if has_story_request:
        story_requests.append({
            'id': node_id,
            'text': text[:200],
            'x': node.get('x'),
            'y': node.get('y')
        })

    if has_clarification_request:
        clarification_requests.append({
            'id': node_id,
            'text': text[:200],
            'x': node.get('x'),
            'y': node.get('y')
        })

    if not has_story_request and not has_clarification_request and len(text) > 10:
        other_nodes.append({
            'id': node_id,
            'text': text[:200]
        })

print(f"\n需求统计：")
print(f"  需要故事化解释: {len(story_requests)} 个")
print(f"  需要澄清解释: {len(clarification_requests)} 个")
print(f"  其他节点: {len(other_nodes)} 个")

# 输出需要故事化解释的节点
if story_requests:
    print("\n" + "=" * 80)
    print("需要故事化解释的节点 (memory-anchor):")
    print("=" * 80)
    for i, req in enumerate(story_requests, 1):
        print(f"\n{i}. ID: {req['id'][:16]}...")
        print(f"   位置: ({req['x']}, {req['y']})")
        print(f"   内容: {req['text'][:150]}...")

# 输出需要澄清解释的节点
if clarification_requests:
    print("\n" + "=" * 80)
    print("需要澄清解释的节点 (clarification-path):")
    print("=" * 80)
    for i, req in enumerate(clarification_requests, 1):
        print(f"\n{i}. ID: {req['id'][:16]}...")
        print(f"   位置: ({req['x']}, {req['y']})")
        print(f"   内容: {req['text'][:150]}...")

# 输出其他有内容的节点
if other_nodes:
    print("\n" + "=" * 80)
    print("其他有内容的黄色节点:")
    print("=" * 80)
    for i, node in enumerate(other_nodes[:5], 1):  # 只显示前5个
        print(f"\n{i}. ID: {node['id'][:16]}...")
        print(f"   内容: {node['text'][:100]}...")

# 保存分析结果到JSON
analysis_result = {
    'story_requests': story_requests,
    'clarification_requests': clarification_requests,
    'other_nodes': other_nodes
}

with open(r"C:\Users\ROG\托福\yellow_nodes_analysis.json", 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("分析结果已保存到: yellow_nodes_analysis.json")
print("=" * 80)
