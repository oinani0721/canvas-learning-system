# Canvas学习系统G6智能布局算法优化技术方案

## 项目概述

**版本**: v2.0 (G6集成版)
**创建日期**: 2025-10-18
**目标**: 解决现有v1.1布局算法的树状图结构不明显、黄色节点定位不严格、排版美观性差等问题

## 1. 现有系统问题分析

### 1.1 v1.1布局算法核心问题

**基于代码分析发现的关键问题**：

1. **黄色节点定位不严格**
   ```python
   # 现有代码：canvas_utils.py Line 130-131
   YELLOW_OFFSET_X = 0              # 水平对齐
   YELLOW_OFFSET_Y = 30             # 垂直偏移30px
   ```
   - 问题：仅实现简单的水平对齐，没有严格的"正下方"约束
   - 缺乏动态定位算法，无法适应不同节点尺寸

2. **树状图结构不明显**
   ```python
   # 现有代码：Line 2174-2181 (decomposition布局)
   base_pos = {
       "x": parent_node["x"],
       "y": parent_node["y"] + parent_node["height"] + VERTICAL_GAP
   }
   # 多个子节点横向错开
   base_pos = self._offset_for_siblings(base_pos, parent_node["id"])
   ```
   - 问题：简单的纵向排列 + 横向错开，缺乏层次感
   - 没有真正的树状分支结构

3. **布局一致性差**
   - 多种布局算法并存（v1.1、垂直瀑布流、紧凑布局等）
   - 缺乏统一的布局框架
   - 每次生成可能有差异

### 1.2 Canvas数据结构分析

**节点类型与关系**：
```javascript
// Canvas节点结构
{
  "id": "node-uuid",
  "type": "text",
  "x": 100,
  "y": 200,
  "width": 400,
  "height": 300,
  "color": "6",  // 1=灰白, 2=绿, 3=紫, 4=红, 5=蓝, 6=黄
  "text": "节点内容"
}

// 边关系结构
{
  "id": "edge-uuid",
  "fromNode": "parent-id",
  "toNode": "child-id",
  "fromSide": "right",
  "toSide": "left",
  "label": "拆解自"
}
```

**核心关系模式**：
1. **材料 → 问题** (学习拆解)
2. **问题 → 理解** (个人输出，黄色节点)
3. **理解 → 子问题** (进一步拆解)
4. **理解 → 解释** (AI补充，蓝色节点)

## 2. G6集成架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Canvas学习系统 v2.0                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: CanvasOrchestrator (高级接口)                      │
│  ├─ add_sub_question_with_yellow_node_g6()                  │
│  ├─ generate_review_canvas_file_g6()                       │
│  └─ optimize_canvas_layout_g6()                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: G6布局业务逻辑层                                   │
│  ├─ G6CanvasLayoutOptimizer (核心布局引擎)                  │
│  ├─ G6TreeLayoutBuilder (树状图构建器)                      │
│  ├─ G6PositionCalculator (精确位置计算)                     │
│  └─ G6LayoutPreferenceLearner (用户偏好学习)                │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: CanvasJSONOperator + G6集成层                     │
│  ├─ Canvas到G6数据转换                                       │
│  ├─ G6布局计算                                               │
│  └─ G6结果回写到Canvas                                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件设计

#### 2.2.1 G6CanvasLayoutOptimizer (核心布局引擎)

```python
class G6CanvasLayoutOptimizer:
    """G6智能布局优化器

    集成G6的多种布局算法，为Canvas学习系统提供专业的图布局能力
    """

    def __init__(self):
        self.supported_layouts = {
            'compactbox': self._compactbox_layout,      # 紧凑树布局
            'dendrogram': self._dendrogram_layout,      # 系统树图
            'mindmap': self._mindmap_layout,            # 思维导图
            'indented': self._indented_layout,          # 缩进树布局
        }

        # 用户偏好配置
        self.user_preferences = {
            'default_layout': 'compactbox',
            'yellow_node_alignment': 'strict_center',   # 严格居中对齐
            'tree_direction': 'TB',                     # Top to Bottom
            'node_spacing': {
                'vertical': 80,
                'horizontal': 120
            },
            'aesthetic_settings': {
                'symmetry': True,
                'balance': True,
                'hierarchy_clarity': 10  # 1-10评分
            }
        }

    def optimize_canvas_layout(self, canvas_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化Canvas布局

        Args:
            canvas_data: 原始Canvas数据结构

        Returns:
            Dict[str, Any]: 优化后的Canvas数据结构
        """
        # 1. 转换Canvas数据为G6格式
        g6_data = self._canvas_to_g6_data(canvas_data)

        # 2. 分析图结构和节点类型
        layout_config = self._analyze_and_configure_layout(g6_data)

        # 3. 应用G6布局算法
        positioned_data = self._apply_g6_layout(g6_data, layout_config)

        # 4. 优化黄色节点位置（严格正下方对齐）
        optimized_data = self._optimize_yellow_node_positions(positioned_data)

        # 5. 转换回Canvas格式
        return self._g6_to_canvas_data(optimized_data)
```

#### 2.2.2 黄色节点精确对齐算法

```python
def _optimize_yellow_node_positions(self, g6_data: Dict[str, Any]) -> Dict[str, Any]:
    """优化黄色节点位置 - 确保严格在材料节点正下方

    核心约束：
    1. 黄色节点x坐标 = 父节点x坐标 + (父节点宽度 - 黄色节点宽度) / 2
    2. 黄色节点y坐标 = 父节点y坐标 + 父节点高度 + 30px
    3. 特殊处理：避免与其他节点重叠
    """

    for node in g6_data['nodes']:
        if node.get('color') == '6':  # 黄色节点
            # 找到父节点（材料/问题节点）
            parent_edges = [e for e in g6_data['edges']
                           if e['to'] == node['id']]

            if parent_edges:
                parent_id = parent_edges[0]['from']
                parent_node = self._find_node_by_id(g6_data, parent_id)

                if parent_node:
                    # 严格居中对齐计算
                    ideal_x = parent_node['x'] + (parent_node['width'] - node['width']) / 2
                    ideal_y = parent_node['y'] + parent_node['height'] + 30

                    # 检查重叠并调整
                    final_position = self._adjust_for_overlap(
                        ideal_x, ideal_y, node, g6_data
                    )

                    node['x'] = final_position['x']
                    node['y'] = final_position['y']

    return g6_data

def _adjust_for_overlap(self, x: float, y: float, node: Dict, g6_data: Dict) -> Dict[str, float]:
    """调整位置以避免重叠"""

    node_rect = {
        'x': x, 'y': y,
        'width': node['width'],
        'height': node['height']
    }

    # 检查与其他节点的重叠
    for other_node in g6_data['nodes']:
        if other_node['id'] != node['id']:
            other_rect = {
                'x': other_node['x'],
                'y': other_node['y'],
                'width': other_node['width'],
                'height': other_node['height']
            }

            if self._rectangles_overlap(node_rect, other_rect):
                # 计算调整方向
                overlap_x = self._calculate_overlap_x(node_rect, other_rect)
                overlap_y = self._calculate_overlap_y(node_rect, other_rect)

                # 优先向下调整，保持水平对齐
                if overlap_y > 0:
                    y += overlap_y + 10  # 额外10px间距
                elif overlap_x > 0:
                    x += overlap_x + 10

    return {'x': x, 'y': y}
```

#### 2.2.3 树状图结构构建器

```python
class G6TreeLayoutBuilder:
    """G6树状图布局构建器

    根据Canvas学习系统的特点，构建清晰的层次化树状结构
    """

    def build_tree_structure(self, canvas_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建树状结构

        识别层次关系：
        - Level 0: 材料节点（无颜色）
        - Level 1: 问题节点（红色/紫色）
        - Level 2: 理解节点（黄色）
        - Level 3: 子问题节点（红色/紫色）
        - Level 4: 解释节点（蓝色）
        """

        tree_data = {
            'id': 'root',
            'children': []
        }

        # 按颜色和关系构建层次
        material_nodes = self._get_material_nodes(canvas_data)

        for material in material_nodes:
            material_tree = {
                'id': material['id'],
                'type': 'material',
                'children': []
            }

            # 获取材料的问题节点
            questions = self._get_child_questions(canvas_data, material['id'])

            for question in questions:
                question_tree = {
                    'id': question['id'],
                    'type': 'question',
                    'color': question.get('color'),
                    'children': []
                }

                # 获取问题的理解节点（黄色）
                understandings = self._get_child_understandings(canvas_data, question['id'])

                for understanding in understandings:
                    understanding_tree = {
                        'id': understanding['id'],
                        'type': 'understanding',
                        'color': '6',
                        'children': []
                    }

                    # 获取理解的子节点（子问题或解释）
                    sub_nodes = self._get_child_nodes(canvas_data, understanding['id'])

                    for sub_node in sub_nodes:
                        sub_tree = {
                            'id': sub_node['id'],
                            'type': 'sub_node',
                            'color': sub_node.get('color'),
                            'children': []
                        }
                        understanding_tree['children'].append(sub_tree)

                    question_tree['children'].append(understanding_tree)

                material_tree['children'].append(question_tree)

            tree_data['children'].append(material_tree)

        return tree_data
```

### 2.3 G6布局算法配置

#### 2.3.1 CompactBox布局（主要推荐）

```python
def _configure_compactbox_layout(self) -> Dict[str, Any]:
    """配置紧凑树布局

    特点：
    - 节省空间
    - 清晰的层次结构
    - 适合Canvas学习系统的知识图谱
    """

    return {
        'type': 'compactbox',
        'direction': 'TB',  # Top to Bottom
        'getWidth': (d) => {
            // 根据节点类型动态设置宽度
            switch(d.type) {
                case 'material': return 400;
                case 'question': return 350;
                case 'understanding': return 300;  // 黄色节点稍窄
                case 'explanation': return 320;
                default: return 300;
            }
        },
        'getHeight': (d) => {
            // 根据节点类型动态设置高度
            switch(d.type) {
                case 'material': return 200;
                case 'question': return 120;
                case 'understanding': return 150;  // 黄色节点高度
                case 'explanation': return 100;
                default: return 80;
            }
        },
        'getVGap': (d) => {
            // 垂直间距：问题→黄色节点更紧密
            if (d.type === 'question') return 30;  // 紧密关联
            return 60;  // 一般间距
        },
        'getHGap': (d) => {
            // 水平间距
            return 100;
        }
    }
```

#### 2.3.2 Mindmap布局（备选方案）

```python
def _configure_mindmap_layout(self) -> Dict[str, Any]:
    """配置思维导图布局

    特点：
    - 有机的分支结构
    - 适合创意性的知识组织
    - 左右分布，平衡感好
    """

    return {
        'type': 'mindmap',
        'direction': 'H',  # Horizontal (左右分布)
        'getWidth': (d) => {
            if (d.type === 'understanding') return 250;
            if (d.type === 'question') return 280;
            return 300;
        },
        'getHeight': (d) => {
            if (d.type === 'understanding') return 80;
            return 60;
        },
        'getVGap': (d) => {
            // 黄色节点垂直间距更小
            if (d.type === 'understanding') return 15;
            return 25;
        },
        'getHGap': (d) => {
            return 80;
        },
        'getSide': (d) => {
            // 自定义左右分布规则
            // 可以根据节点类型、重要性等决定
            if (d.type === 'understanding') return 'right';
            if (d.color === '5') return 'left';  // 解释节点放在左边
            return 'right';
        }
    }
```

## 3. Canvas到G6数据转换

### 3.1 数据转换器

```python
class CanvasG6DataConverter:
    """Canvas数据与G6数据格式转换器"""

    def canvas_to_g6_data(self, canvas_data: Dict[str, Any]) -> Dict[str, Any]:
        """将Canvas数据转换为G6格式"""

        nodes = []
        edges = []

        # 转换节点
        for canvas_node in canvas_data.get('nodes', []):
            g6_node = {
                'id': canvas_node['id'],
                'data': {
                    'label': self._extract_text_content(canvas_node),
                    'type': self._determine_node_type(canvas_node),
                    'color': canvas_node.get('color'),
                    'original_canvas_data': canvas_node  # 保留原始数据
                },
                'style': {
                    'x': canvas_node['x'],
                    'y': canvas_node['y'],
                    'width': canvas_node.get('width', 400),
                    'height': canvas_node.get('height', 300)
                }
            }
            nodes.append(g6_node)

        # 转换边
        for canvas_edge in canvas_data.get('edges', []):
            g6_edge = {
                'id': canvas_edge['id'],
                'source': canvas_edge['fromNode'],
                'target': canvas_edge['toNode'],
                'data': {
                    'label': canvas_edge.get('label', ''),
                    'type': self._determine_edge_type(canvas_edge)
                },
                'style': {
                    'type': 'cubic-horizontal',  # 默认边样式
                    'endArrow': True
                }
            }
            edges.append(g6_edge)

        return {
            'nodes': nodes,
            'edges': edges
        }

    def g6_to_canvas_data(self, g6_data: Dict[str, Any]) -> Dict[str, Any]:
        """将G6数据转换回Canvas格式"""

        canvas_nodes = []
        canvas_edges = []

        # 转换节点
        for g6_node in g6_data['nodes']:
            original_data = g6_node['data'].get('original_canvas_data', {})

            canvas_node = {
                'id': g6_node['id'],
                'type': original_data.get('type', 'text'),
                'x': int(g6_node['style']['x']),
                'y': int(g6_node['style']['y']),
                'width': int(g6_node['style']['width']),
                'height': int(g6_node['style']['height']),
                'color': g6_node['data'].get('color'),
                'text': g6_node['data']['label']
            }

            # 保留原始Canvas的其他属性
            for key, value in original_data.items():
                if key not in ['x', 'y', 'width', 'height', 'id']:
                    canvas_node[key] = value

            canvas_nodes.append(canvas_node)

        # 转换边
        for g6_edge in g6_data['edges']:
            canvas_edge = {
                'id': g6_edge['id'],
                'fromNode': g6_edge['source'],
                'toNode': g6_edge['target'],
                'fromSide': 'right',
                'toSide': 'left',
                'label': g6_edge['data'].get('label', '')
            }
            canvas_edges.append(canvas_edge)

        return {
            'nodes': canvas_nodes,
            'edges': canvas_edges
        }
```

## 4. 用户交互与偏好学习

### 4.1 布局调整记录系统

```python
class G6LayoutPreferenceLearner:
    """布局偏好学习系统

    记录用户的手动调整，学习个人布局偏好
    """

    def __init__(self):
        self.adjustment_history = []
        self.preference_patterns = {}

    def record_user_adjustment(self,
                             canvas_data_before: Dict[str, Any],
                             canvas_data_after: Dict[str, Any],
                             adjusted_node_ids: List[str]):
        """记录用户的手动调整"""

        adjustment_record = {
            'timestamp': datetime.now().isoformat(),
            'node_ids': adjusted_node_ids,
            'changes': self._calculate_changes(canvas_data_before, canvas_data_after),
            'context': self._extract_layout_context(canvas_data_before)
        }

        self.adjustment_history.append(adjustment_record)
        self._update_preference_patterns(adjustment_record)

    def _calculate_changes(self, before: Dict, after: Dict) -> List[Dict]:
        """计算节点位置变化"""

        changes = []

        before_nodes = {node['id']: node for node in before.get('nodes', [])}
        after_nodes = {node['id']: node for node in after.get('nodes', [])}

        for node_id in before_nodes:
            if node_id in after_nodes:
                before_node = before_nodes[node_id]
                after_node = after_nodes[node_id]

                dx = after_node['x'] - before_node['x']
                dy = after_node['y'] - before_node['y']

                if abs(dx) > 5 or abs(dy) > 5:  # 只记录显著调整
                    changes.append({
                        'node_id': node_id,
                        'node_type': before_node.get('color'),
                        'dx': dx,
                        'dy': dy,
                        'relative_change': self._calculate_relative_change(
                            before_node, after_node
                        )
                    })

        return changes

    def learn_layout_preferences(self) -> Dict[str, Any]:
        """学习布局偏好模式"""

        preferences = {
            'yellow_node_alignment': self._learn_yellow_alignment_preference(),
            'spacing_preferences': self._learn_spacing_preferences(),
            'layout_direction_preference': self._learn_direction_preference(),
            'aesthetic_preferences': self._learn_aesthetic_preferences()
        }

        return preferences

    def _learn_yellow_alignment_preference(self) -> str:
        """学习黄色节点对齐偏好"""

        yellow_adjustments = []

        for record in self.adjustment_history:
            for change in record['changes']:
                if change['node_type'] == '6':  # 黄色节点
                    yellow_adjustments.append(change)

        if not yellow_adjustments:
            return 'strict_center'  # 默认严格居中

        # 分析调整模式
        left_moves = sum(1 for adj in yellow_adjustments if adj['dx'] < -10)
        right_moves = sum(1 for adj in yellow_adjustments if adj['dx'] > 10)

        if left_moves > right_moves * 1.5:
            return 'left_aligned'
        elif right_moves > left_moves * 1.5:
            return 'right_aligned'
        else:
            return 'strict_center'
```

### 4.2 迭代优化工作流

```python
class G6IterativeOptimizer:
    """G6迭代优化工作流

    支持用户调整 → 学习 → 优化的迭代过程
    """

    def __init__(self):
        self.optimizer = G6CanvasLayoutOptimizer()
        self.preference_learner = G6LayoutPreferenceLearner()
        self.iteration_count = 0

    def optimization_workflow(self, canvas_file_path: str) -> Dict[str, Any]:
        """完整优化工作流

        Steps:
        1. 分析当前Canvas布局
        2. 应用G6智能布局
        3. 生成测试Canvas文件
        4. 等待用户调整
        5. 记录调整并学习偏好
        6. 生成优化版本
        """

        workflow_result = {
            'iterations': [],
            'final_layout': None,
            'learned_preferences': {},
            'quality_metrics': {}
        }

        # Step 1: 读取原始Canvas
        original_canvas = self._read_canvas_file(canvas_file_path)

        # Step 2: 应用初始G6布局
        optimized_canvas = self.optimizer.optimize_canvas_layout(original_canvas)

        # Step 3: 生成测试文件
        test_file_path = self._generate_test_canvas(optimized_canvas, self.iteration_count)

        workflow_result['iterations'].append({
            'iteration': self.iteration_count,
            'action': 'g6_layout_applied',
            'output_file': test_file_path,
            'layout_config': self.optimizer.get_current_config()
        })

        return workflow_result

    def process_user_adjustment(self,
                               before_file: str,
                               after_file: str,
                               adjusted_nodes: List[str]) -> Dict[str, Any]:
        """处理用户调整"""

        before_data = self._read_canvas_file(before_file)
        after_data = self._read_canvas_file(after_file)

        # 记录调整
        self.preference_learner.record_user_adjustment(
            before_data, after_data, adjusted_nodes
        )

        # 学习偏好
        learned_preferences = self.preference_learner.learn_layout_preferences()

        # 更新优化器配置
        self.optimizer.update_preferences(learned_preferences)

        self.iteration_count += 1

        return {
            'iteration': self.iteration_count,
            'learned_preferences': learned_preferences,
            'adjustments_processed': len(adjusted_nodes)
        }
```

## 5. 测试Canvas文件设计

### 5.1 真实使用场景模拟

```python
def create_test_canvas_file() -> str:
    """创建模拟真实使用情况的测试Canvas文件

    场景设计：
    - 材料节点：离散数学 - 逆否命题
    - 问题节点：3个不同难度的问题（红/紫色）
    - 理解节点：对应的黄色输出区
    - 子问题：进一步拆解
    - 解释节点：AI补充说明
    """

    test_canvas = {
        "nodes": [],
        "edges": []
    }

    # 材料节点
    material_node = {
        "id": "material-inverse-proposition",
        "type": "text",
        "x": 100,
        "y": 100,
        "width": 400,
        "height": 200,
        "color": None,  # 无颜色=材料节点
        "text": "离散数学 - 逆否命题\n\n逆否命题是逻辑学中的重要概念，给定命题P→Q，其逆否命题为¬Q→¬P。两个命题逻辑等价。"
    }
    test_canvas["nodes"].append(material_node)

    # 问题节点1 (红色 - 不理解)
    question1 = {
        "id": "question-1-basic",
        "type": "text",
        "x": 600,
        "y": 80,
        "width": 350,
        "height": 120,
        "color": "4",  # 红色
        "text": "什么是逆否命题？如何判断两个命题是否为逆否关系？"
    }
    test_canvas["nodes"].append(question1)

    # 问题节点2 (紫色 - 似懂非懂)
    question2 = {
        "id": "question-2-application",
        "type": "text",
        "x": 600,
        "y": 250,
        "width": 350,
        "height": 120,
        "color": "3",  # 紫色
        "text": "在实际证明中，什么时候使用逆否命题证明法更有效？"
    }
    test_canvas["nodes"].append(question2)

    # 问题节点3 (红色 - 不理解)
    question3 = {
        "id": "question-3-advanced",
        "type": "text",
        "x": 600,
        "y": 420,
        "width": 350,
        "height": 120,
        "color": "4",  # 红色
        "text": "逆否命题与原命题、否命题、逆命题之间有什么关系？"
    }
    test_canvas["nodes"].append(question3)

    # 黄色理解节点（每个问题下方）
    yellow_nodes = [
        {
            "id": "understanding-1",
            "x": 600,  # 应该严格在问题1正下方
            "y": 230,  # question1.y + question1.height + 30
            "width": 300,
            "height": 150,
            "color": "6",
            "text": ""  # 空白，等待用户填写
        },
        {
            "id": "understanding-2",
            "x": 600,  # 严格在问题2正下方
            "y": 400,
            "width": 300,
            "height": 150,
            "color": "6",
            "text": ""
        },
        {
            "id": "understanding-3",
            "x": 600,  # 严格在问题3正下方
            "y": 570,
            "width": 300,
            "height": 150,
            "color": "6",
            "text": ""
        }
    ]

    for yellow in yellow_nodes:
        test_canvas["nodes"].append(yellow)

    # 子问题拆解示例（从黄色理解节点拆解）
    sub_questions = [
        {
            "id": "subquestion-1-1",
            "parent": "understanding-1",
            "x": 1000,
            "y": 200,
            "width": 300,
            "height": 100,
            "color": "4",
            "text": "逆否命题的定义是什么？"
        },
        {
            "id": "subquestion-1-2",
            "parent": "understanding-1",
            "x": 1000,
            "y": 320,
            "width": 300,
            "height": 100,
            "color": "4",
            "text": "如何构造一个命题的逆否命题？"
        },
        {
            "id": "subquestion-2-1",
            "parent": "understanding-2",
            "x": 1000,
            "y": 450,
            "width": 300,
            "height": 100,
            "color": "3",
            "text": "逆否命题证明法的适用场景？"
        }
    ]

    for sub_q in sub_questions:
        test_canvas["nodes"].append(sub_q)

    # 解释节点（蓝色）
    explanations = [
        {
            "id": "explanation-oral",
            "parent": "understanding-1",
            "x": 1400,
            "y": 180,
            "width": 280,
            "height": 80,
            "color": "5",
            "text": "🗣️ 口语化解释：逆否命题"
        },
        {
            "id": "explanation-comparison",
            "parent": "understanding-1",
            "x": 1400,
            "y": 280,
            "width": 280,
            "height": 80,
            "color": "5",
            "text": "📊 对比表：四种命题关系"
        }
    ]

    for explanation in explanations:
        test_canvas["nodes"].append(explanation)

    # 边关系
    edges = [
        # 材料 → 问题
        {"id": "edge-material-q1", "fromNode": material_node["id"], "toNode": question1["id"], "label": "拆解自"},
        {"id": "edge-material-q2", "fromNode": material_node["id"], "toNode": question2["id"], "label": "拆解自"},
        {"id": "edge-material-q3", "fromNode": material_node["id"], "toNode": question3["id"], "label": "拆解自"},

        # 问题 → 理解
        {"id": "edge-q1-yellow", "fromNode": question1["id"], "toNode": "understanding-1", "label": "个人理解"},
        {"id": "edge-q2-yellow", "fromNode": question2["id"], "toNode": "understanding-2", "label": "个人理解"},
        {"id": "edge-q3-yellow", "fromNode": question3["id"], "toNode": "understanding-3", "label": "个人理解"},

        # 理解 → 子问题
        {"id": "edge-yellow-sub1-1", "fromNode": "understanding-1", "toNode": "subquestion-1-1", "label": "拆解自"},
        {"id": "edge-yellow-sub1-2", "fromNode": "understanding-1", "toNode": "subquestion-1-2", "label": "拆解自"},
        {"id": "edge-yellow-sub2-1", "fromNode": "understanding-2", "toNode": "subquestion-2-1", "label": "拆解自"},

        # 理解 → 解释
        {"id": "edge-yellow-exp1", "fromNode": "understanding-1", "toNode": "explanation-oral", "label": "补充解释"},
        {"id": "edge-yellow-exp2", "fromNode": "understanding-1", "toNode": "explanation-comparison", "label": "补充解释"}
    ]

    for edge in edges:
        test_canvas["edges"].append(edge)

    # 保存测试文件
    test_filename = "test-canvas-g6-layout-20251018.canvas"
    test_filepath = os.path.join("C:/Users/ROG/托福/笔记库/测试/", test_filename)

    # 确保目录存在
    os.makedirs(os.path.dirname(test_filepath), exist_ok=True)

    with open(test_filepath, 'w', encoding='utf-8') as f:
        json.dump(test_canvas, f, ensure_ascii=False, indent=2)

    return test_filepath
```

## 6. 实施计划

### 6.1 Phase 1: G6集成基础架构 (Week 1)

1. **安装和配置G6**
   ```bash
   npm install @antv/g6
   # 或使用CDN
   ```

2. **创建核心G6集成模块**
   - `g6_canvas_optimizer.py` - 主要优化器
   - `g6_data_converter.py` - 数据转换器
   - `g6_layout_builder.py` - 布局构建器

3. **实现Canvas↔G6数据转换**
   - 支持现有所有节点类型和颜色
   - 保持向后兼容性

### 6.2 Phase 2: 智能布局算法实现 (Week 2)

1. **实现CompactBox布局**
   - 黄色节点严格对齐算法
   - 树状层次结构构建

2. **实现Mindmap布局备选**
   - 左右平衡分布
   - 有机分支效果

3. **布局质量评估系统**
   - 对称性评分
   - 层次清晰度评分
   - 重叠检测

### 6.3 Phase 3: 用户交互和学习 (Week 3)

1. **调整记录系统**
   - 实时监控用户拖拽操作
   - 计算调整模式

2. **偏好学习算法**
   - 黄色节点对齐偏好
   - 间距偏好
   - 布局方向偏好

3. **迭代优化工作流**
   - 自动测试文件生成
   - 偏好应用和验证

### 6.4 Phase 4: 测试和优化 (Week 4)

1. **创建测试Canvas文件**
   - 模拟真实学习场景
   - 多种节点类型组合

2. **用户测试循环**
   - 布局生成
   - 用户调整
   - 偏好学习
   - 优化迭代

3. **性能优化**
   - 大型Canvas文件处理
   - 实时布局更新

## 7. 预期效果

### 7.1 解决的核心问题

1. **黄色节点严格对齐** ✅
   - 精确的数学计算确保居中对齐
   - 动态适应不同节点尺寸
   - 重叠避免机制

2. **清晰的树状图结构** ✅
   - 专业的图布局算法
   - 明确的层次关系
   - 美观的分支效果

3. **布局一致性** ✅
   - 统一的布局框架
   - 可重现的布局结果
   - 个性化偏好支持

### 7.2 用户体验提升

- **视觉清晰度**: 树状图结构一目了然
- **操作便利性**: 黄色节点严格对齐，填写更自然
- **个性化**: 系统学习个人布局偏好
- **专业性**: 基于G6的专业图可视化效果

### 7.3 技术优势

- **高性能**: G6专业图渲染引擎
- **可扩展**: 支持多种布局算法
- **智能化**: 用户偏好学习机制
- **兼容性**: 与现有Canvas系统完全兼容

## 8. 风险评估与缓解

### 8.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| G6集成复杂度高 | 中 | 高 | 分阶段实施，充分测试 |
| 性能问题 | 中 | 低 | 性能基准测试，优化算法 |
| 兼容性问题 | 高 | 低 | 保持现有API不变，新增G6选项 |

### 8.2 用户接受度风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 学习成本 | 中 | 中 | 提供详细文档和教程 |
| 布局不符合预期 | 高 | 中 | 迭代优化，用户反馈循环 |
| 现有工作流被打断 | 中 | 低 | 保持向后兼容，渐进式升级 |

## 9. 总结

本技术方案通过集成AntV G6专业图可视化引擎，为Canvas学习系统提供智能布局算法优化。核心解决用户反馈的黄色节点定位不严格、树状图结构不明显、排版美观性差等问题。

**关键创新点**：
1. **精确的黄色节点对齐算法** - 数学计算确保严格居中对齐
2. **专业的树状图布局** - 基于G6的CompactBox和Mindmap算法
3. **用户偏好学习机制** - 记录手动调整，持续优化布局
4. **迭代优化工作流** - 支持用户调整→学习→优化的完整循环

通过这个方案，Canvas学习系统将获得专业级的图布局能力，显著提升用户体验和学习效率。

---

**文档版本**: v1.0
**创建日期**: 2025-10-18
**作者**: Canvas学习系统开发团队
**审核状态**: 待审核