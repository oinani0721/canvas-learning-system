#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成无纸化检验白板
为Canvas中的每个分组生成独立的检验白板文件
"""

import json
import os
from datetime import datetime

# Canvas颜色常量
COLOR_RED = "4"      # 红色 - 不理解
COLOR_GREEN = "2"    # 绿色 - 完全理解
COLOR_PURPLE = "3"   # 紫色 - 似懂非懂
COLOR_BLUE = "5"     # 蓝色 - AI内容
COLOR_YELLOW = "6"   # 黄色 - 个人理解

# 布局常量
BASE_X = 0
BASE_Y = 0
QUESTION_WIDTH = 500
QUESTION_HEIGHT = 300
UNDERSTANDING_WIDTH = 400
UNDERSTANDING_HEIGHT = 200
HORIZONTAL_GAP = 700
VERTICAL_SPACING = 400

def extract_groups_with_review_nodes(canvas_path):
    """从Canvas文件中提取包含红色/紫色节点的分组"""
    with open(canvas_path, 'r', encoding='utf-8') as f:
        canvas = json.load(f)

    group_nodes = [n for n in canvas['nodes'] if n.get('type') == 'group']
    groups_data = []

    for group in group_nodes:
        group_id = group['id']
        label = group.get('label', '(无标签)')
        gx = group.get('x', 0)
        gy = group.get('y', 0)
        gw = group.get('width', 0)
        gh = group.get('height', 0)

        # 找到分组内的节点（通过坐标边界判断）
        nodes_in_group = []
        for node in canvas['nodes']:
            if node.get('type') == 'group':
                continue
            nx = node.get('x', 0)
            ny = node.get('y', 0)

            if gx <= nx <= gx + gw and gy <= ny <= gy + gh:
                nodes_in_group.append(node)

        # 筛选红色和紫色节点
        red_nodes = [n for n in nodes_in_group if n.get('color') == COLOR_RED]
        purple_nodes = [n for n in nodes_in_group if n.get('color') == COLOR_PURPLE]
        review_nodes = red_nodes + purple_nodes

        if len(review_nodes) > 0:
            groups_data.append({
                'group_id': group_id,
                'label': label,
                'red_count': len(red_nodes),
                'purple_count': len(purple_nodes),
                'review_nodes': review_nodes,
                'all_nodes': nodes_in_group
            })

    return groups_data

def create_simple_review_question(node, index):
    """为节点创建简单的检验问题"""
    node_text = node.get('text', node.get('label', ''))
    node_color = node.get('color')

    # 根据颜色类型生成不同的检验问题
    if node_color == COLOR_RED:  # 红色 - 完全不懂
        question_text = f"# 检验问题 {index}\n\n**原始内容**:\n{node_text[:200]}...\n\n**检验问题**:\n\n请用自己的话解释这个概念的核心含义。如果完全不懂，请尝试从你已知的相关概念出发，猜测它可能是什么意思。"
    else:  # 紫色 - 似懂非懂
        question_text = f"# 检验问题 {index}\n\n**原始内容**:\n{node_text[:200]}...\n\n**检验问题**:\n\n1. 请用自己的话重新解释这个概念\n2. 请举一个具体的例子来说明\n3. 请说明这个概念与其他相关概念的区别"

    return question_text

def generate_review_canvas(group_data, original_canvas_name, output_dir):
    """为单个分组生成检验白板"""
    group_label = group_data['label']
    review_nodes = group_data['review_nodes']

    # 创建时间戳
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    # 清理文件名（移除特殊字符）
    safe_label = group_label.replace('/', '-').replace('\\', '-').replace(':', '-').replace('?', '').replace('*', '')
    canvas_filename = f"{safe_label}-检验白板-{timestamp}.canvas"
    canvas_path = os.path.join(output_dir, canvas_filename)

    # 创建Canvas结构
    canvas_data = {
        "nodes": [],
        "edges": []
    }

    # 添加标题节点
    title_node = {
        "id": "review-title",
        "type": "text",
        "text": f"# 🎯 检验白板: {group_label}\n\n**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n**来源**: {original_canvas_name}\n**检验节点数**: {len(review_nodes)}个\n\n---\n\n## 📝 使用说明\n\n1. 在黄色节点中填写你的理解（不要查看原白板）\n2. 完成后可以调用评分Agent进行评分\n3. 根据评分结果决定是否需要返回原白板复习",
        "x": BASE_X,
        "y": BASE_Y - 600,
        "width": 800,
        "height": 500,
        "color": COLOR_BLUE
    }
    canvas_data['nodes'].append(title_node)

    # 为每个需要检验的节点创建检验问题和理解区域
    current_y = BASE_Y

    for i, node in enumerate(review_nodes, 1):
        # 创建检验问题节点（红色）
        question_text = create_simple_review_question(node, i)
        question_node = {
            "id": f"review-q{i}",
            "type": "text",
            "text": question_text,
            "x": BASE_X,
            "y": current_y,
            "width": QUESTION_WIDTH,
            "height": QUESTION_HEIGHT,
            "color": COLOR_RED
        }
        canvas_data['nodes'].append(question_node)

        # 创建理解节点（黄色）- 用户填写区
        understanding_node = {
            "id": f"review-u{i}",
            "type": "text",
            "text": f"# 💡 我的理解 {i}\n\n在这里写下你对这个问题的理解...\n\n（不要查看原白板！尝试用自己的话解释）",
            "x": BASE_X + HORIZONTAL_GAP,
            "y": current_y + 50,
            "width": UNDERSTANDING_WIDTH,
            "height": UNDERSTANDING_HEIGHT,
            "color": COLOR_YELLOW
        }
        canvas_data['nodes'].append(understanding_node)

        # 创建连接边
        edge = {
            "id": f"edge-q{i}-u{i}",
            "fromNode": question_node['id'],
            "fromSide": "right",
            "toNode": understanding_node['id'],
            "toSide": "left",
            "label": "我的理解"
        }
        canvas_data['edges'].append(edge)

        current_y += VERTICAL_SPACING

    # 保存Canvas文件
    with open(canvas_path, 'w', encoding='utf-8') as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)

    return canvas_filename

def main():
    """主函数"""
    import sys
    import io

    # 设置UTF-8输出
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 路径配置
    canvas_path = r'C:\Users\ROG\托福\笔记库\CS70\CS70 Lecture1.canvas'
    output_dir = r'C:\Users\ROG\托福\笔记库\CS70'

    print("=" * 60)
    print("Canvas Learning System - 无纸化检验白板生成器")
    print("=" * 60)
    print()

    # 提取分组数据
    print("正在读取Canvas文件...")
    groups_data = extract_groups_with_review_nodes(canvas_path)
    print(f"找到 {len(groups_data)} 个包含检验节点的分组\n")

    # 为每个分组生成检验白板
    generated_files = []

    for i, group_data in enumerate(groups_data, 1):
        label = group_data['label']
        count = len(group_data['review_nodes'])

        print(f"[{i}/{len(groups_data)}] 正在生成: {label} ({count}个节点)...")

        filename = generate_review_canvas(group_data, "CS70 Lecture1", output_dir)
        generated_files.append(filename)

        print(f"    已生成: {filename}")
        print()

    # 输出总结
    print("=" * 60)
    print(f"完成！共生成 {len(generated_files)} 个检验白板文件")
    print("=" * 60)
    print("\n生成的文件:")
    for i, filename in enumerate(generated_files, 1):
        print(f"  {i}. {filename}")

    print("\n文件位置:", output_dir)
    print("\n下一步:")
    print("  1. 在Obsidian中打开这些检验白板文件")
    print("  2. 在黄色节点中填写你的理解（不查看原白板）")
    print("  3. 使用 @检验白板文件 评分所有黄色节点 来进行评分")

if __name__ == '__main__':
    main()
