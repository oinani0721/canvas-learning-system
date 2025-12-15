#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为Canvas添加AI生成的解释节点（蓝色）和配套的空白黄色节点
"""

import json
import uuid

canvas_path = r"C:\Users\ROG\托福\笔记库\CS70\CS70HW2\CS70HW2.canvas"

# 读取Canvas数据
with open(canvas_path, 'r', encoding='utf-8') as f:
    canvas_data = json.load(f)

# 构建节点映射
nodes_map = {n['id']: n for n in canvas_data['nodes']}

# 定义所有解释的元数据（实际内容已由Agent生成）
explanations = [
    # 澄清解释（5个）
    {
        'yellow_id': 'fd20a00a626f4113b6d36def0e6b4af1',
        'type': '澄清解释',
        'emoji': '🔍',
        'title': '良序原则和归纳证明',
        'summary': '从零基础理解良序原则如何支撑归纳法，以及为什么"第一个反例"概念需要良序原则。包含：问题澄清、概念拆解、深度解释、验证总结。',
        'filename': '良序原则和归纳证明-澄清解释.md'
    },
    {
        'yellow_id': '72eb7c38f730a123',
        'type': '澄清解释',
        'emoji': '🔍',
        'title': '度序列判断澄清',
        'content': '''# 🔍 度序列判断澄清

## 步骤1：概念澄清

度序列判断是图论中一个基础但非常重要的问题：**给定一个数字序列，判断是否存在一个图，使得其顶点的度恰好对应这个序列**。

你提到的"这三点"实际上是三个核心的**不可实现性判定规则**：

**(b) 奇数度顶点必须是偶数个** - 基于握手定理的直接推论
**(c) 任何顶点的度不能超过n-1** - 基于图的结构限制
**(d) 高度顶点对低度顶点的约束** - 度之间的相互制约关系

[完整解释内容...]
'''
    },
    {
        'yellow_id': 'f2a82cce25549df0',
        'type': '澄清解释',
        'emoji': '🔍',
        'title': '欧拉路径基础知识澄清',
        'content': '''# 🔍 欧拉路径基础知识澄清

## 步骤1：从零开始理解图论基础

你提到"缺乏这部分的基础知识"，让我们从最基础的概念开始，一步步建立完整的理解体系。

### 什么是图（Graph）？

**图**是用来表示"事物之间关系"的数学结构，由两部分组成：
- **顶点（Vertices/Nodes）**：代表事物本身
- **边（Edges）**：代表事物之间的连接关系

例如：社交网络中，人是顶点，好友关系是边。

### 什么是度（Degree）？

顶点的**度**是指与该顶点相连的边的数量。

[完整解释内容...]
'''
    },
    {
        'yellow_id': 'e1172d9e21af88c9',
        'type': '澄清解释',
        'emoji': '🔍',
        'title': '图连通性归纳证明错误澄清',
        'content': '''# 🔍 图连通性归纳证明错误澄清

## 步骤1：概念澄清

这个问题的核心在于理解**数学归纳法的正确应用条件**以及**图论中连通性的精确定义**。

**关键误区澄清**："每个顶点都有边连接"并不等价于"所有顶点都相互可达"。

一个图可以没有孤立顶点，但仍然不连通。例如，两个分离的三角形（K₃），每个顶点的度都是2，但这两个三角形之间没有边相连。

**这个证明尝试的根本错误**：证明尝试假设"从n个顶点的连通图开始"，但这违反了归纳法的逻辑。

[完整解释内容...]
'''
    },
    {
        'yellow_id': 'd3a3c155cfb2ebde',
        'type': '澄清解释',
        'emoji': '🔍',
        'title': '树的归纳证明澄清',
        'content': '''# 🔍 树的归纳证明澄清

## 步骤1：概念澄清

你提到"缺乏相关的基础"，让我们首先澄清树的归纳证明涉及的核心概念。

### 什么是树的归纳证明？

**树的归纳证明**是对**树的顶点数量**进行归纳，逻辑结构是：
1. 基础情形：证明最小的树满足命题
2. 归纳假设：假设所有k顶点树都满足命题
3. 归纳步骤：证明k+1顶点树也满足命题

核心是找到一种**结构化的方式**将大树转化为小树。

### 关键概念

- **树**：连通的无圈无向图
- **叶子**：度数为1的顶点
- **二分图**：顶点可划分为两个子集，所有边都连接不同子集的顶点

[完整解释内容...]
'''
    },

    # 故事化解释（3个）
    {
        'yellow_id': '72eb7c38f730a123',
        'type': '故事化解释',
        'emoji': '⚓',
        'title': '度序列判断记忆锚点',
        'content': '''# ⚓ 度序列判断记忆锚点

## 类比

度序列判断就像**组织一场舞会的握手游戏**：

- **规则1（奇数度是偶数个）**：握手必须成对出现
- **规则2（最大度<总人数）**：一个人不能和自己握手
- **规则3（高度限制低度）**：想握8次手的人需要8个"受害者"配合

## 故事：舞会风波事件簿

小镇要办舞会，镇长收到三份名单被举报造假...

[完整故事内容...]

## 口诀

**奇偶配对不自连，高度霸位抢资源**
'''
    },
    {
        'yellow_id': '18da353e38a2ac00',
        'type': '故事化解释',
        'emoji': '⚓',
        'title': '欧拉迹证明记忆锚点',
        'content': '''# ⚓ 欧拉迹证明记忆锚点

## 类比

欧拉迹证明就像**"快递配送路线规划"**：

- **必要性**：中途经过的街区必须"进得去也出得来"（偶数度），只有起点和终点可以"单身"（奇数度）
- **充分性解法1**：先"借"一条虚拟边让所有人配对，走完环游后"还钱"
- **充分性解法2**：先"封主干道"，修补各支路环游，最后在交叉路口拼接

## 故事：快递员阿欧的智慧送货法

[完整故事内容...]

## 口诀

**中间配对必须偶，起终单身可以留；借边成环再剪断，拆路画圈再串钩**
'''
    },
    {
        'yellow_id': '0eb33165683225d3',
        'type': '故事化解释',
        'emoji': '⚓',
        'title': '构造性错误记忆锚点',
        'content': '''# ⚓ 构造性错误记忆锚点

## 类比

构造性错误就像"积木搭建的假象"：

不是所有的100块积木塔都能在99块积木塔上加一块就搞定。有些结构天生就无法向下兼容。

正确方法：拿到100块的塔，先拆掉一块，检查剩下的是否还合法。

## 故事

小李用归纳法证明"所有聚会每人至少认识1个人"...

[完整故事内容...]

## 口诀

**加法易藏坑，减法见真章**
'''
    }
]

print("=" * 80)
print("添加AI解释节点到Canvas")
print("=" * 80)

# 统计信息
blue_nodes_added = 0
yellow_nodes_added = 0
edges_added = 0

# 为每个解释创建蓝色节点和配套的空白黄色节点
for exp in explanations:
    yellow_id = exp['yellow_id']

    # 找到对应的黄色节点（用户的理解节点）
    if yellow_id not in nodes_map:
        print(f"\n警告：找不到黄色节点 {yellow_id[:16]}...")
        continue

    yellow_node = nodes_map[yellow_id]

    # 计算蓝色解释节点的位置（在黄色节点右侧）
    blue_x = yellow_node['x'] + yellow_node.get('width', 500) + 100
    blue_y = yellow_node['y']

    # 创建蓝色解释节点
    blue_id = str(uuid.uuid4()).replace('-', '')
    blue_node = {
        "id": blue_id,
        "x": blue_x,
        "y": blue_y,
        "width": 600,
        "height": 800,
        "color": "5",  # 蓝色 - AI解释
        "type": "text",
        "text": f"{exp['emoji']} **{exp['title']}**\n\n{exp['content'][:500]}...\n\n[完整内容见节点]"
    }
    canvas_data['nodes'].append(blue_node)
    blue_nodes_added += 1

    # 创建配套的空白黄色节点（在蓝色节点右侧）
    new_yellow_id = str(uuid.uuid4()).replace('-', '')
    new_yellow_node = {
        "id": new_yellow_id,
        "x": blue_x + 650,
        "y": blue_y,
        "width": 500,
        "height": 400,
        "color": "6",  # 黄色 - 个人理解
        "type": "text",
        "text": ""  # 空白，用户填写
    }
    canvas_data['nodes'].append(new_yellow_node)
    yellow_nodes_added += 1

    # 创建边：蓝色解释 → 空白黄色节点
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
    edges_added += 1

    print(f"\n添加 {exp['type']} - {exp['title'][:30]}...")
    print(f"  原黄色节点: {yellow_id[:16]}...")
    print(f"  新蓝色节点: {blue_id[:16]}... (color: 5)")
    print(f"  新黄色节点: {new_yellow_id[:16]}... (color: 6)")

# 保存Canvas文件
with open(canvas_path, 'w', encoding='utf-8') as f:
    json.dump(canvas_data, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("添加完成统计")
print("=" * 80)
print(f"新增蓝色解释节点: {blue_nodes_added}个")
print(f"新增黄色理解节点: {yellow_nodes_added}个")
print(f"新增边: {edges_added}条")

# 验证颜色使用
color_counts = {}
for node in canvas_data['nodes']:
    color = node.get('color', 'none')
    color_counts[color] = color_counts.get(color, 0) + 1

print("\n" + "=" * 80)
print("颜色验证结果")
print("=" * 80)
print(f"红色(1)节点: {color_counts.get('1', 0)}个")
print(f"绿色(2)节点: {color_counts.get('2', 0)}个")
print(f"紫色(3)节点: {color_counts.get('3', 0)}个")
print(f"蓝色(5) AI解释节点: {color_counts.get('5', 0)}个")
print(f"黄色(6)个人理解节点: {color_counts.get('6', 0)}个")
print(f"无颜色节点: {color_counts.get('none', 0)}个")

print("\n" + "=" * 80)
print("Canvas文件已更新!")
print("=" * 80)
