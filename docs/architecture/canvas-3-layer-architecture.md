---
document_type: "Architecture"
version: "1.1.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "0dc1d3610d28bf99"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

# Canvas学习系统架构设计

**版本**: v1.1 (Epic 6 - 知识图谱层)
**最后更新**: 2025-10-18

---

## 🏗️ 架构概述

Canvas学习系统采用**4层架构模式**，实现关注点分离和高内聚低耦合：

```
┌─────────────────────────────────────────┐
│      Layer 4: KnowledgeGraphLayer       │  ← 知识图谱持久化 (Epic 6)
│      (时间感知知识图谱，AI驱动)           │
├─────────────────────────────────────────┤
│      Layer 3: CanvasOrchestrator        │  ← Sub-agents调用
│      (高级接口，完整业务流程)            │
├─────────────────────────────────────────┤
│      Layer 2: CanvasBusinessLogic       │  ← 业务逻辑实现
│      (v1.1布局算法，节点关系管理)        │
├─────────────────────────────────────────┤
│      Layer 1: CanvasJSONOperator        │  ← 底层JSON操作
│      (读写文件，CRUD操作)                │
└─────────────────────────────────────────┘
                    ↕
         [.canvas JSON文件] + [Neo4j知识图谱]
```

### Epic 6更新: Layer 4 (KnowledgeGraphLayer)

**新增功能**:
- Canvas数据的持久化存储到Neo4j知识图谱
- 基于Graphiti的时间感知知识图谱
- 支持跨Canvas的知识关联和学习进度追踪
- AI驱动的智能分析和推荐

**技术栈**:
- Neo4j数据库 (图数据库)
- Graphiti (时间感知知识图谱框架)
- OpenAI API (LLM支持)

**可选集成**: Layer 4为可选层，不影响现有功能的正常运行。

---

## 📐 Layer 1: CanvasJSONOperator（底层操作层）

### 职责
- Canvas JSON文件的读写
- 节点和边的CRUD操作
- 不包含任何业务逻辑
- 纯函数式，无状态

### 完整代码实现

```python
import json
import uuid
import os
from typing import Dict, List, Optional
from pathlib import Path

class CanvasJSONOperator:
    """Canvas JSON文件的底层操作

    提供读写、节点CRUD、边CRUD等基础操作，不包含业务逻辑。
    所有方法都是静态方法，无状态设计。
    """

    @staticmethod
    def read_canvas(canvas_path: str) -> Dict:
        """读取Canvas文件并返回JSON数据

        Args:
            canvas_path: Canvas文件的绝对或相对路径

        Returns:
            Dict: Canvas JSON数据，包含 nodes 和 edges 字段

        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果JSON格式错误或缺少必要字段
        """
        if not os.path.exists(canvas_path):
            raise FileNotFoundError(f"Canvas文件不存在: {canvas_path}")

        try:
            with open(canvas_path, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Canvas文件JSON格式错误: {canvas_path}\n错误详情: {e}")

        # 验证必要字段
        if "nodes" not in canvas_data:
            canvas_data["nodes"] = []
        if "edges" not in canvas_data:
            canvas_data["edges"] = []

        return canvas_data

    @staticmethod
    def write_canvas(canvas_path: str, canvas_data: Dict) -> None:
        """将Canvas数据写入文件

        Args:
            canvas_path: Canvas文件路径
            canvas_data: Canvas JSON数据

        Raises:
            ValueError: 如果canvas_data格式不正确
        """
        # 验证数据结构
        if not isinstance(canvas_data, dict):
            raise ValueError("canvas_data必须是字典类型")
        if "nodes" not in canvas_data or "edges" not in canvas_data:
            raise ValueError("canvas_data必须包含'nodes'和'edges'字段")

        # 确保目录存在
        os.makedirs(os.path.dirname(canvas_path) or '.', exist_ok=True)

        # 写入文件（格式化，便于阅读）
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def create_node(
        canvas_data: Dict,
        node_type: str,
        x: int,
        y: int,
        width: int = 400,
        height: int = 300,
        text: str = "",
        file: str = "",
        color: Optional[str] = None
    ) -> str:
        """创建节点并添加到canvas_data

        Args:
            canvas_data: Canvas数据字典
            node_type: 节点类型（"text", "file", "group"）
            x, y: 节点位置
            width, height: 节点尺寸
            text: 文本内容（type="text"时使用）
            file: 文件路径（type="file"时使用）
            color: 颜色代码（"1"-"6"，可选）

        Returns:
            str: 新创建的节点ID

        Raises:
            ValueError: 如果参数不合法
        """
        if node_type not in ["text", "file", "group"]:
            raise ValueError(f"不支持的节点类型: {node_type}")

        # 生成唯一ID
        node_id = f"{node_type}-{uuid.uuid4().hex[:16]}"

        # 构建节点数据
        node_data = {
            "id": node_id,
            "type": node_type,
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height)
        }

        # 添加类型特定字段
        if node_type == "text":
            node_data["text"] = text
        elif node_type == "file":
            node_data["file"] = file

        # 添加颜色（如果指定）
        if color is not None:
            if color not in ["1", "2", "3", "4", "5", "6"]:
                raise ValueError(f"不合法的颜色代码: {color}")
            node_data["color"] = color

        # 添加到canvas_data
        canvas_data["nodes"].append(node_data)

        return node_id

    @staticmethod
    def get_node_by_id(canvas_data: Dict, node_id: str) -> Optional[Dict]:
        """根据ID获取节点

        Args:
            canvas_data: Canvas数据字典
            node_id: 节点ID

        Returns:
            Optional[Dict]: 节点数据，如果不存在返回None
        """
        for node in canvas_data.get("nodes", []):
            if node.get("id") == node_id:
                return node
        return None

    @staticmethod
    def update_node(canvas_data: Dict, node_id: str, updates: Dict) -> bool:
        """更新节点属性

        Args:
            canvas_data: Canvas数据字典
            node_id: 节点ID
            updates: 要更新的字段字典

        Returns:
            bool: 是否成功更新
        """
        node = CanvasJSONOperator.get_node_by_id(canvas_data, node_id)
        if node is None:
            return False

        # 更新字段
        for key, value in updates.items():
            node[key] = value

        return True

    @staticmethod
    def delete_node(canvas_data: Dict, node_id: str) -> bool:
        """删除节点

        Args:
            canvas_data: Canvas数据字典
            node_id: 节点ID

        Returns:
            bool: 是否成功删除
        """
        nodes = canvas_data.get("nodes", [])
        for i, node in enumerate(nodes):
            if node.get("id") == node_id:
                nodes.pop(i)
                # 同时删除相关的边
                CanvasJSONOperator._delete_edges_by_node(canvas_data, node_id)
                return True
        return False

    @staticmethod
    def create_edge(
        canvas_data: Dict,
        from_node: str,
        to_node: str,
        from_side: str = "right",
        to_side: str = "left",
        label: str = ""
    ) -> str:
        """创建边（连接线）

        Args:
            canvas_data: Canvas数据字典
            from_node: 源节点ID
            to_node: 目标节点ID
            from_side: 源节点连接侧（top/right/bottom/left）
            to_side: 目标节点连接侧
            label: 边标签（可选）

        Returns:
            str: 新创建的边ID
        """
        edge_id = f"edge-{uuid.uuid4().hex[:16]}"

        edge_data = {
            "id": edge_id,
            "fromNode": from_node,
            "toNode": to_node,
            "fromSide": from_side,
            "toSide": to_side
        }

        if label:
            edge_data["label"] = label

        canvas_data["edges"].append(edge_data)

        return edge_id

    @staticmethod
    def _delete_edges_by_node(canvas_data: Dict, node_id: str) -> None:
        """删除与指定节点相关的所有边（私有方法）"""
        edges = canvas_data.get("edges", [])
        canvas_data["edges"] = [
            edge for edge in edges
            if edge.get("fromNode") != node_id and edge.get("toNode") != node_id
        ]

    @staticmethod
    def get_nodes_by_color(canvas_data: Dict, color: str) -> List[Dict]:
        """获取指定颜色的所有节点

        Args:
            canvas_data: Canvas数据字典
            color: 颜色代码（"1"-"6"）

        Returns:
            List[Dict]: 匹配的节点列表
        """
        return [
            node for node in canvas_data.get("nodes", [])
            if node.get("color") == color
        ]
```

---

## 🎯 Layer 2: CanvasBusinessLogic（业务逻辑层）

### 职责
- 实现v1.1布局算法
- 管理节点关系（问题-理解配对）
- 实现颜色管理逻辑
- 生成检验白板

### 完整代码实现

```python
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 布局参数常量
HORIZONTAL_SPACING = 450  # 材料到问题的水平间距
VERTICAL_SPACING_BASE = 380  # 问题+黄色组合的垂直间距
YELLOW_OFFSET_X = 0  # 黄色节点水平偏移（相对问题节点）
YELLOW_OFFSET_Y = 30  # 黄色节点垂直偏移（相对问题节点底部）
QUESTION_NODE_HEIGHT = 120  # 问题节点高度
YELLOW_NODE_WIDTH = 350  # 黄色理解节点宽度
YELLOW_NODE_HEIGHT = 150  # 黄色理解节点高度

# 颜色常量
COLOR_RED = "1"
COLOR_GREEN = "2"
COLOR_PURPLE = "3"
COLOR_YELLOW = "6"

class CanvasBusinessLogic:
    """Canvas业务逻辑层

    实现v1.1布局算法、节点关系管理等业务逻辑。
    依赖Layer 1的CanvasJSONOperator进行底层操作。
    """

    def __init__(self, canvas_path: str):
        """初始化业务逻辑层

        Args:
            canvas_path: Canvas文件路径
        """
        self.canvas_path = canvas_path
        self.canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

    def save(self) -> None:
        """保存Canvas数据到文件"""
        CanvasJSONOperator.write_canvas(self.canvas_path, self.canvas_data)

    def add_sub_question_with_yellow_node(
        self,
        material_node_id: str,
        question_text: str,
        guidance: str = ""
    ) -> Tuple[str, str]:
        """添加子问题和黄色理解节点（使用v1.1布局）

        v1.1布局特点：
        - 黄色节点在问题节点正下方（垂直对齐）
        - 水平偏移为0

        Args:
            material_node_id: 材料节点ID
            question_text: 问题文本
            guidance: 引导性提示（可选）

        Returns:
            Tuple[str, str]: (问题节点ID, 黄色节点ID)

        Raises:
            ValueError: 如果material_node_id不存在
        """
        # 获取材料节点
        material_node = CanvasJSONOperator.get_node_by_id(
            self.canvas_data,
            material_node_id
        )
        if material_node is None:
            raise ValueError(f"材料节点不存在: {material_node_id}")

        # 计算问题节点位置
        question_pos = self._calculate_question_position(material_node)

        # 创建问题节点（红色）
        question_id = CanvasJSONOperator.create_node(
            self.canvas_data,
            node_type="text",
            x=question_pos["x"],
            y=question_pos["y"],
            width=400,
            height=QUESTION_NODE_HEIGHT,
            text=question_text + (f"\n\n{guidance}" if guidance else ""),
            color=COLOR_RED
        )

        # 计算黄色节点位置（v1.1: 在问题下方）
        yellow_pos = {
            "x": question_pos["x"] + YELLOW_OFFSET_X,  # 水平对齐
            "y": question_pos["y"] + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y
        }

        # 创建黄色理解节点
        yellow_id = CanvasJSONOperator.create_node(
            self.canvas_data,
            node_type="text",
            x=yellow_pos["x"],
            y=yellow_pos["y"],
            width=YELLOW_NODE_WIDTH,
            height=YELLOW_NODE_HEIGHT,
            text="",  # 用户填写
            color=COLOR_YELLOW
        )

        # 创建边：材料 → 问题
        CanvasJSONOperator.create_edge(
            self.canvas_data,
            from_node=material_node_id,
            to_node=question_id,
            from_side="right",
            to_side="left"
        )

        # 创建边：问题 → 黄色理解
        CanvasJSONOperator.create_edge(
            self.canvas_data,
            from_node=question_id,
            to_node=yellow_id,
            from_side="bottom",
            to_side="top"
        )

        return question_id, yellow_id

    def _calculate_question_position(self, material_node: Dict) -> Dict[str, int]:
        """计算问题节点位置（v1.1布局算法）

        规则：
        - 水平位置：材料节点右侧 + HORIZONTAL_SPACING
        - 垂直位置：查找同一材料的其他子问题，垂直排列

        Args:
            material_node: 材料节点数据

        Returns:
            Dict: {"x": int, "y": int}
        """
        # 基础水平位置
        base_x = material_node["x"] + material_node["width"] + HORIZONTAL_SPACING

        # 查找该材料的现有子问题数量
        existing_questions = self._count_child_questions(material_node["id"])

        # 垂直位置（每个问题+黄色组合占用VERTICAL_SPACING_BASE高度）
        base_y = material_node["y"] + (existing_questions * VERTICAL_SPACING_BASE)

        return {"x": base_x, "y": base_y}

    def _count_child_questions(self, material_node_id: str) -> int:
        """统计材料节点的子问题数量"""
        count = 0
        for edge in self.canvas_data.get("edges", []):
            if edge.get("fromNode") == material_node_id:
                to_node = CanvasJSONOperator.get_node_by_id(
                    self.canvas_data,
                    edge.get("toNode")
                )
                if to_node and to_node.get("color") == COLOR_RED:
                    count += 1
        return count

    def update_node_color_after_scoring(
        self,
        yellow_node_id: str,
        score: int,
        passing_score: int = 80
    ) -> str:
        """根据评分结果更新问题节点颜色

        逻辑：
        - 如果≥passing_score，问题节点变绿
        - 否则保持红色

        Args:
            yellow_node_id: 黄色理解节点ID
            score: 评分结果（0-100）
            passing_score: 及格分数（默认80）

        Returns:
            str: 更新后的颜色（"2"=绿色 或 "1"=红色）
        """
        # 找到对应的问题节点
        question_node_id = self._find_parent_question(yellow_node_id)
        if question_node_id is None:
            raise ValueError(f"找不到黄色节点 {yellow_node_id} 的父问题节点")

        # 确定新颜色
        new_color = COLOR_GREEN if score >= passing_score else COLOR_RED

        # 更新问题节点颜色
        CanvasJSONOperator.update_node(
            self.canvas_data,
            question_node_id,
            {"color": new_color}
        )

        return new_color

    def _find_parent_question(self, yellow_node_id: str) -> Optional[str]:
        """查找黄色节点对应的问题节点"""
        for edge in self.canvas_data.get("edges", []):
            if edge.get("toNode") == yellow_node_id:
                from_node_id = edge.get("fromNode")
                from_node = CanvasJSONOperator.get_node_by_id(
                    self.canvas_data,
                    from_node_id
                )
                if from_node and from_node.get("color") in [COLOR_RED, COLOR_GREEN]:
                    return from_node_id
        return None

    def generate_review_canvas(
        self,
        output_path: str,
        include_red: bool = True,
        include_purple: bool = True
    ) -> Dict[str, List[Dict]]:
        """生成检验白板

        Args:
            output_path: 输出Canvas文件路径
            include_red: 是否包含红色节点
            include_purple: 是否包含紫色节点

        Returns:
            Dict: {"red_nodes": [...], "purple_nodes": [...]}
        """
        # 收集需要检验的节点
        red_nodes = CanvasJSONOperator.get_nodes_by_color(
            self.canvas_data,
            COLOR_RED
        ) if include_red else []

        purple_nodes = CanvasJSONOperator.get_nodes_by_color(
            self.canvas_data,
            COLOR_PURPLE
        ) if include_purple else []

        # 创建新Canvas
        review_canvas = {
            "nodes": [],
            "edges": []
        }

        # 添加说明节点
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        CanvasJSONOperator.create_node(
            review_canvas,
            node_type="text",
            x=100,
            y=100,
            width=500,
            height=150,
            text=f"# 检验白板\n\n生成时间: {timestamp}\n"
                 f"红色节点: {len(red_nodes)} 个\n"
                 f"紫色节点: {len(purple_nodes)} 个\n\n"
                 f"请尝试回答以下问题，不要查看原白板。",
            color="4"  # 蓝色说明节点
        )

        # 添加检验问题（简化版，实际应由review-verification agent生成）
        y_offset = 300
        for i, node in enumerate(red_nodes + purple_nodes):
            # 创建检验问题节点
            question_text = f"检验问题 {i+1}:\n{node.get('text', '')[:100]}..."
            CanvasJSONOperator.create_node(
                review_canvas,
                node_type="text",
                x=100,
                y=y_offset,
                width=400,
                height=120,
                text=question_text,
                color=COLOR_RED
            )
            y_offset += 200

        # 保存检验白板
        CanvasJSONOperator.write_canvas(output_path, review_canvas)

        return {
            "red_nodes": red_nodes,
            "purple_nodes": purple_nodes
        }
```

---

## 🚀 Layer 3: CanvasOrchestrator（高级接口层）

### 职责
- 提供Sub-agents调用的高级接口
- 封装完整的业务流程
- 协调Layer 2的多个操作

### 完整代码实现

```python
from typing import Dict, List

class CanvasOrchestrator:
    """Canvas操作的高级接口

    供Sub-agents调用的高级接口，封装完整的业务流程。
    每个方法对应一个Sub-agent的处理逻辑。
    """

    def __init__(self, canvas_path: str):
        """初始化Orchestrator

        Args:
            canvas_path: Canvas文件路径
        """
        self.business_logic = CanvasBusinessLogic(canvas_path)

    def handle_basic_decomposition(
        self,
        material_node_id: str,
        sub_questions: List[Dict]
    ) -> Dict[str, List[str]]:
        """处理基础拆解Agent的结果

        Args:
            material_node_id: 材料节点ID
            sub_questions: 基础拆解Agent返回的子问题列表
                [
                    {
                        "text": "问题文本",
                        "type": "定义型",
                        "difficulty": "基础",
                        "guidance": "💡 提示..."
                    },
                    ...
                ]

        Returns:
            Dict: {
                "question_ids": [问题节点ID列表],
                "yellow_ids": [黄色节点ID列表]
            }
        """
        question_ids = []
        yellow_ids = []

        for question in sub_questions:
            q_id, y_id = self.business_logic.add_sub_question_with_yellow_node(
                material_node_id=material_node_id,
                question_text=question["text"],
                guidance=question.get("guidance", "")
            )
            question_ids.append(q_id)
            yellow_ids.append(y_id)

        # 保存Canvas
        self.business_logic.save()

        return {
            "question_ids": question_ids,
            "yellow_ids": yellow_ids
        }

    def handle_scoring(
        self,
        yellow_node_id: str,
        score_result: Dict
    ) -> Dict[str, any]:
        """处理评分Agent的结果

        Args:
            yellow_node_id: 黄色节点ID
            score_result: 评分Agent返回的结果
                {
                    "total_score": 85,
                    "pass": true,
                    "feedback": "很好！..."
                }

        Returns:
            Dict: {
                "new_color": "2" or "1",
                "passed": bool
            }
        """
        new_color = self.business_logic.update_node_color_after_scoring(
            yellow_node_id=yellow_node_id,
            score=score_result["total_score"]
        )

        # 保存Canvas
        self.business_logic.save()

        return {
            "new_color": new_color,
            "passed": score_result["pass"]
        }

    def handle_review_verification(
        self,
        output_canvas_path: str
    ) -> Dict[str, any]:
        """处理无纸化检验Agent的请求

        Args:
            output_canvas_path: 输出检验白板的路径

        Returns:
            Dict: {
                "review_canvas_path": str,
                "red_count": int,
                "purple_count": int
            }
        """
        result = self.business_logic.generate_review_canvas(
            output_path=output_canvas_path,
            include_red=True,
            include_purple=True
        )

        return {
            "review_canvas_path": output_canvas_path,
            "red_count": len(result["red_nodes"]),
            "purple_count": len(result["purple_nodes"])
        }
```

---

## 📊 使用示例

### 示例1：Sub-agent调用基础拆解

```python
# basic-decomposition agent返回了子问题JSON
sub_questions = [
    {
        "text": "什么是逆否命题的定义？",
        "type": "定义型",
        "difficulty": "基础",
        "guidance": "💡 从原命题的结构出发"
    },
    {
        "text": "逆否命题和原命题有什么关系？",
        "type": "对比型",
        "difficulty": "基础",
        "guidance": "💡 思考真值表"
    }
]

# Canvas-Orchestrator调用CanvasOrchestrator
orchestrator = CanvasOrchestrator("笔记库/离散数学/离散数学.canvas")

result = orchestrator.handle_basic_decomposition(
    material_node_id="node-abc123",
    sub_questions=sub_questions
)

print(f"创建了 {len(result['question_ids'])} 个问题节点")
print(f"创建了 {len(result['yellow_ids'])} 个黄色理解节点")
```

### 示例2：Sub-agent调用评分

```python
# scoring-agent返回了评分结果
score_result = {
    "total_score": 85,
    "breakdown": {
        "accuracy": 22,
        "imagery": 21,
        "completeness": 23,
        "originality": 19
    },
    "pass": True,
    "feedback": "很好！你的类比很生动，理解基本准确。"
}

# Canvas-Orchestrator调用CanvasOrchestrator
orchestrator = CanvasOrchestrator("笔记库/离散数学/离散数学.canvas")

result = orchestrator.handle_scoring(
    yellow_node_id="node-xyz789",
    score_result=score_result
)

print(f"节点颜色更新为: {result['new_color']}")  # "2" (绿色)
print(f"是否通过: {result['passed']}")  # True
```

---

## ✅ 架构验证清单

在实现代码时，确认以下设计原则得到遵守：

**Layer 1 验证**:
- [ ] 所有方法都是静态方法（无状态）
- [ ] 不包含任何业务逻辑（纯CRUD）
- [ ] 不直接调用Layer 2或Layer 3
- [ ] 错误处理明确

**Layer 2 验证**:
- [ ] 只调用Layer 1的方法
- [ ] 实现了v1.1布局算法
- [ ] 包含业务逻辑（如颜色管理）
- [ ] 不直接被Sub-agents调用

**Layer 3 验证**:
- [ ] 只调用Layer 2的方法
- [ ] 每个方法对应一个Sub-agent的处理逻辑
- [ ] 封装了完整的业务流程
- [ ] 返回结构化的结果

---

## 🧠 Layer 4: KnowledgeGraphLayer（知识图谱层）

### Epic 6新增 - 时间感知知识图谱

**版本**: v1.0 (Epic 6)
**创建时间**: 2025-10-18

### 职责
- Canvas数据的持久化存储到Neo4j知识图谱
- 基于Graphiti的时间感知知识图谱构建
- 跨Canvas的知识关联和语义搜索
- 学习进度的实时追踪和分析
- AI驱动的智能推荐和学习路径优化

### 技术栈
- **Neo4j**: 原生图数据库，支持复杂关系查询
- **Graphiti**: 时间感知知识图谱框架，支持实体关系的时序演化
- **OpenAI API**: LLM支持，用于智能分析和推荐
- **Python asyncio**: 异步操作支持

### 核心类设计

```python
class KnowledgeGraphLayer:
    """Canvas学习系统的知识图谱层 (Layer 4)"""

    def __init__(self, config: Optional[Dict[str, str]] = None):
        """初始化知识图谱层"""

    async def initialize(self) -> bool:
        """初始化Graphiti客户端和数据库连接"""

    async def add_canvas_entity(self, canvas_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """添加Canvas实体到知识图谱"""

    async def add_node_entity(self, canvas_id: str, node_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """添加节点实体到知识图谱"""

    async def add_relationship(self, from_entity_id: str, to_entity_id: str,
                             relationship_type: str, properties: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """添加实体关系"""

    async def search_entities(self, query: str, entity_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索知识图谱中的实体"""

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
```

### 数据模型设计

#### 实体类型 (Entity Types)
```python
ENTITY_TYPES = {
    "Canvas": "Canvas文件实体",
    "Node": "Canvas节点实体",
    "Concept": "知识概念实体",
    "Topic": "主题实体",
    "User": "用户实体"
}
```

#### 关系类型 (Relationship Types)
```python
RELATIONSHIP_TYPES = {
    "CONTAINS": "包含关系",      # Canvas包含Node
    "CONNECTS_TO": "连接关系",   # Node之间的连接
    "LEARNS": "学习关系",        # User学习Concept
    "EXPLORES": "探索关系",      # User探索Topic
    "RELATED_TO": "相关关系",    # Concept之间的关联
    "REQUIRES": "前置关系"       # 概念之间的依赖关系
}
```

### 使用示例

```python
# 创建知识图谱层
kg_layer = await create_knowledge_graph_layer()

# 保存Canvas到知识图谱
canvas_data = CanvasJSONOperator.read_canvas("learning.canvas")
await kg_layer.add_canvas_entity(canvas_data)

# 搜索相关概念
results = await kg_layer.search_entities("机器学习", entity_type="Concept")

# 执行自定义查询
query = "MATCH (c:Concept)-[:RELATED_TO]->(c2:Concept) RETURN c, c2"
related_concepts = await kg_layer.execute_query(query)
```

### 性能指标
- **基础查询响应时间**: <500ms
- **数据库连接初始化**: <2秒
- **单次实体写入**: <100ms
- **支持规模**: 10,000+节点

### 集成策略

#### 可选集成模式
- Layer 4为**可选层**，不影响现有3层架构功能
- 通过`CanvasJSONOperatorWithKG`扩展现有功能
- 支持动态启用/禁用知识图谱功能

#### 配置管理
```bash
# .env配置
GRAPHITI_ENABLED=true        # 启用知识图谱功能
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=canvas123
OPENAI_API_KEY=your-api-key
```

---

## 🔍 架构验证清单

**Layer 1 验证**:
- [x] 错误处理明确
- [x] 只操作JSON文件，不包含业务逻辑

**Layer 2 验证**:
- [x] 只调用Layer 1的方法
- [x] 实现了v1.1布局算法
- [x] 包含业务逻辑（如颜色管理）
- [x] 不直接被Sub-agents调用

**Layer 3 验证**:
- [x] 只调用Layer 2的方法
- [x] 每个方法对应一个Sub-agent的处理逻辑
- [x] 封装了完整的业务流程
- [x] 返回结构化的结果

**Layer 4 验证**:
- [x] 基于Graphiti和Neo4j实现
- [x] 支持时间感知知识图谱
- [x] 提供Canvas数据的持久化存储
- [x] 支持异步操作和错误处理
- [x] 可选集成，不影响现有功能

---

**文档版本**: v1.1 (Epic 6)
**最后更新**: 2025-10-18
**维护者**: Architect Agent

**相关文档**:
- [canvas-layout-v1.1.md](canvas-layout-v1.1.md) - v1.1布局算法详细说明
- [coding-standards.md](coding-standards.md) - 编码规范
- [sub-agent-calling-protocol.md](sub-agent-calling-protocol.md) - Agent调用协议
- [GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md](GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md) - 知识图谱集成架构
