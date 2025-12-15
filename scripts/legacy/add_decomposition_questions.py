#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将基础拆解生成的21个问题添加到CS70HW2.canvas中
"""

import json
import uuid

# 读取Canvas文件
canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"

with open(canvas_path, 'r', encoding='utf-8') as f:
    canvas_data = json.load(f)

# 三个节点的拆解问题
decomposition_data = {
    # 节点1: 改善引理 (341570c6a730b5b1)
    "341570c6a730b5b1": [
        {"type": "定义型", "text": "数学归纳法是什么？它和多米诺骨牌的倒塌有什么相似之处？", "guidance": "💡 提示：想象推倒第一张骨牌，后面的牌会怎样？"},
        {"type": "定义型", "text": "在这个算法中，'工作向求职者发出offer'是什么意思？求职者可以同时拿着多个offer吗？", "guidance": ""},
        {"type": "实例型", "text": "如果你手里有两个offer，一个是Google，一个是小公司，你会'暂时保留'哪一个？为什么？", "guidance": "💡 提示：求职者会保留最好的offer"},
        {"type": "实例型", "text": "引理说'C手中的offer至少和J一样好'是什么意思？用刚才Google的例子能解释吗？", "guidance": ""},
        {"type": "探索型", "text": "为什么第k天C收到J的offer后，之后每天手里的offer不会变差？offer不能被撤回起了什么作用？", "guidance": "💡 提示：旧的offer还在，新的offer可能更好"},
        {"type": "定义型", "text": "归纳证明的'基础情形'(i=k)在说什么？为什么第k天C手里至少有一个和J一样好的offer？", "guidance": "💡 提示：第k天J刚给C发offer，C会保留最好的那个"},
        {"type": "探索型", "text": "归纳步骤是怎么证明'今天成立→明天也成立'的？为什么第i+1天C手里的offer不会比第i天差？", "guidance": "💡 提示：J'会继续发offer，C可以选择保留或换更好的"}
    ],

    # 节点2: 良序原则 (682d611321261951)
    "682d611321261951": [
        {"type": "定义型", "text": "什么是'反证法'？它的基本思路是什么？", "guidance": "💡 提示：假设某个结论是错的，然后看看会发生什么"},
        {"type": "定义型", "text": "什么是'归纳法'？它需要证明哪两个部分？", "guidance": "💡 提示：想想多米诺骨牌是怎么倒下的"},
        {"type": "定义型", "text": "什么叫'第一个反例'？为什么可以假设存在'第一个'反例？", "guidance": "💡 提示：如果有反例，它们能不能排个队？"},
        {"type": "实例型", "text": "'良序原则'是什么意思？能用一个简单的数字集合举例吗？", "guidance": "💡 提示：比如{3, 7, 2, 9}这个集合，哪个数最小？"},
        {"type": "对比型", "text": "为什么整数集合（包括负数）不满足良序原则？", "guidance": "💡 提示：负数可以无限小下去吗？"},
        {"type": "探索型", "text": "这个证明是怎么把'反证法'和'归纳法'结合起来的？", "guidance": "💡 提示：先假设有反例，再找第一个反例，然后推出矛盾"},
        {"type": "探索型", "text": "如果自然数不满足良序原则，'第一个反例'这个概念还成立吗？为什么？", "guidance": ""}
    ],

    # 节点5: 定义4.3+定理4.2 (af5e1ba5b395f823)
    "af5e1ba5b395f823": [
        {"type": "定义型", "text": "什么是'稳定匹配'？能用找工作的场景解释一下吗？", "guidance": "💡 提示：想象求职者和公司互相选择，什么情况下大家都不想换？"},
        {"type": "定义型", "text": "'求职者的最优工作'是什么意思？为什么要强调'在某个稳定匹配中'？", "guidance": "💡 提示：最优工作不一定是偏好列表第一名，为什么？"},
        {"type": "实例型", "text": "假设小明最喜欢Google，其次是Meta，最后是Apple。如果在某个稳定匹配中他只能去Meta或Apple，那他的最优工作是什么？", "guidance": ""},
        {"type": "定义型", "text": "'提议-拒绝算法'是怎么运作的？谁向谁提议？", "guidance": "💡 提示：这个算法的名字已经告诉你两个关键动作了"},
        {"type": "对比型", "text": "定理4.2说算法输出的匹配是'雇主最优的'，这对求职者意味着什么？", "guidance": ""},
        {"type": "探索型", "text": "证明中用'反证法'（假设不是雇主最优），然后找到了什么矛盾？", "guidance": "💡 提示：证明找到了一个不稳定配对，这和稳定匹配的定义矛盾"},
        {"type": "探索型", "text": "证明为什么要说'第k天是第一个发生这种情况的日子'？这和归纳证明有什么关系？", "guidance": "💡 提示：归纳证明通常要找一个'最小/最早'的反例"}
    ]
}

# 找到每个紫色节点的位置
purple_nodes_info = {}
for node in canvas_data['nodes']:
    if node['id'] in decomposition_data:
        purple_nodes_info[node['id']] = {
            'x': node['x'],
            'y': node['y'],
            'width': node['width'],
            'height': node['height']
        }

# 为每个紫色节点创建拆解问题节点
new_nodes = []
new_edges = []

for purple_id, questions in decomposition_data.items():
    if purple_id not in purple_nodes_info:
        continue

    purple_info = purple_nodes_info[purple_id]

    # 计算问题节点的起始位置（在紫色节点下方）
    start_x = purple_info['x']
    start_y = purple_info['y'] + purple_info['height'] + 100  # 下方100px间隔

    for i, question in enumerate(questions):
        # 创建问题节点
        question_id = str(uuid.uuid4()).replace('-', '')

        question_text = f"**[{question['type']}]** {question['text']}"
        if question['guidance']:
            question_text += f"\n\n{question['guidance']}"

        question_node = {
            "id": question_id,
            "x": start_x + (i % 3) * 420,  # 每行3个问题，横向间隔420px
            "y": start_y + (i // 3) * 280,  # 每个问题高度250px，纵向间隔280px
            "width": 400,
            "height": 250,
            "color": "1",  # 红色，表示待回答的问题
            "type": "text",
            "text": question_text
        }

        new_nodes.append(question_node)

        # 创建从紫色节点到问题节点的边
        if i == 0:  # 只在第一个问题节点创建边，避免太多连线
            edge_id = str(uuid.uuid4()).replace('-', '')
            edge = {
                "id": edge_id,
                "fromNode": purple_id,
                "fromSide": "bottom",
                "toNode": question_id,
                "toSide": "top",
                "label": "基础拆解"
            }
            new_edges.append(edge)

# 添加新节点和边到Canvas
canvas_data['nodes'].extend(new_nodes)
canvas_data['edges'].extend(new_edges)

# 保存更新后的Canvas文件
with open(canvas_path, 'w', encoding='utf-8') as f:
    json.dump(canvas_data, f, ensure_ascii=False, indent='\t')

print(f"成功添加了 {len(new_nodes)} 个拆解问题节点！")
print(f"创建了 {len(new_edges)} 条连接边！")
print(f"\n节点分布：")
print(f"  - 节点1 (改善引理): 7个问题")
print(f"  - 节点2 (良序原则): 7个问题")
print(f"  - 节点5 (定义4.3+定理4.2): 7个问题")
print(f"\n这些红色问题节点已添加到Canvas中，你可以在Obsidian中看到它们！")
