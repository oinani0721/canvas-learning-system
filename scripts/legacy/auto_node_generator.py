"""
Canvas学习系统 - Story 10.4: 自动节点生成和连接系统

本模块实现自动为Agent处理结果生成解释节点（蓝色）和总结节点（黄色），
并自动将这些节点连接到用户填写的理解节点后面。

Author: Canvas Learning System Team
Story: 10.4
Date: 2025-10-27
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# 导入现有的Canvas操作工具
from canvas_utils import (
    CanvasJSONOperator,
    DEFAULT_NODE_HEIGHT,
    DEFAULT_NODE_WIDTH,
    LOGURU_ENABLED,
    logger
)


class NodeIDGenerator:
    """节点ID生成器"""

    @staticmethod
    def generate_explanation_node_id() -> str:
        """生成解释节点ID"""
        return f"exp-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def generate_summary_node_id() -> str:
        """生成总结节点ID"""
        return f"sum-{uuid.uuid4().hex[:8]}"


class NodeConnectionRules:
    """节点连接规则定义"""

    CONNECTION_PATTERNS = {
        "explanation": {
            "from": "reference_yellow_node",
            "to": "explanation_node",
            "style": {
                "color": "#4A90E2",  # 蓝色
                "style": "dashed",
                "label": "AI解释"
            }
        },
        "summary": {
            "from": "explanation_node",
            "to": "summary_node",
            "style": {
                "color": "#F5A623",  # 橙色
                "style": "solid",
                "label": "学习总结"
            }
        }
    }

    def create_connection(
        self,
        from_node: str,
        to_node: str,
        connection_type: str,
        context: Dict = None
    ) -> Dict:
        """根据规则创建连接"""
        pattern = self.CONNECTION_PATTERNS.get(connection_type, {})

        edge_data = {
            "id": f"edge-{uuid.uuid4().hex[:8]}",
            "fromNode": from_node,
            "toNode": to_node,
            "fromSide": "right",
            "toSide": "left",
            "label": pattern.get("style", {}).get("label", ""),
            "color": pattern.get("style", {}).get("color", ""),
            "style": pattern.get("style", {}).get("style", "solid")
        }

        return edge_data


class NodeContentGenerator:
    """节点内容生成器"""

    def generate_explanation_content(
        self,
        agent_result: Dict,
        agent_type: str
    ) -> str:
        """生成解释节点的内容"""
        content_template = self._get_content_template(agent_type)

        # 提取Agent结果的关键信息
        main_content = agent_result.get('content', str(agent_result))
        key_points = agent_result.get('key_points', [])
        examples = agent_result.get('examples', [])
        confidence = agent_result.get('confidence', 0.0)

        # 格式化关键要点
        if isinstance(key_points, list):
            key_points_str = "\n".join([f"• {point}" for point in key_points])
        else:
            key_points_str = str(key_points)

        # 格式化示例
        if isinstance(examples, list):
            examples_str = "\n".join([f"• {example}" for example in examples])
        else:
            examples_str = str(examples)

        content = content_template.format(
            agent_type=agent_type,
            main_content=main_content,
            key_points=key_points_str,
            examples=examples_str,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            agent_confidence=confidence
        )

        return content

    def generate_summary_prompt(
        self,
        explanation_content: str,
        original_understanding: str,
        agent_type: str
    ) -> str:
        """生成总结节点的引导提示"""
        # 清理和验证输入
        clean_agent_type = agent_type.replace("-", " ").title() if agent_type else "AI"

        return f"""# 学习总结

请在黄色节点中填写你对以上{clean_agent_type}解释的理解和总结：

## 核心要点
- 根据AI解释，提取最重要的3-5个要点

## 个人理解
- 用你自己的话重新解释这些概念
- 这个解释如何与你已有的知识联系起来

## 疑问之处
- 还有哪些地方不太清楚？
- 需要进一步的什么信息？

## 应用思考
- 如何将这个知识应用到实际问题中？
- 能想到相关的例子吗？

---
**提示**: 尝试不看上面的AI解释，凭记忆写出你的理解。这是检验是否真正掌握的最好方法。
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**AI解释类型**: {clean_agent_type}"""

    def _get_content_template(self, agent_type: str) -> str:
        """获取不同Agent类型的内容模板"""
        templates = {
            "basic-decomposition": """
# 基础拆解解释

## 引导问题解析
{main_content}

## 关键要点
{key_points}

## 学习建议
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
""",
            "deep-decomposition": """
# 深度拆解解释

## 深度问题解析
{main_content}

## 核心要点
{key_points}

## 应用场景
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
""",
            "clarification-path": """
# 深度澄清解释

## 核心概念解析
{main_content}

## 关键要点
{key_points}

## 实例说明
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
""",
            "comparison-table": """
# 概念对比分析

## 对比表格
{main_content}

## 主要区别
{key_points}

## 应用场景
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
""",
            "memory-anchor": """
# 记忆锚点解释

## 记忆策略
{main_content}

## 记忆要点
{key_points}

## 联想示例
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
""",
            "four-level-explanation": """
# 四层次渐进解释

## 渐进式解析
{main_content}

## 层次要点
{key_points}

## 进阶示例
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
""",
            "oral-explanation": """
# 口语化教授解释

## 教授讲解
{main_content}

## 核心知识点
{key_points}

## 生活实例
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
""",
            "example-teaching": """
# 例题教学解释

## 题目解析
{main_content}

## 解题要点
{key_points}

## 变式练习
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
""",
            "scoring-agent": """
# 评分结果解释

## 评分分析
{main_content}

## 改进建议
{key_points}

## 学习方向
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
""",
            "verification-question-agent": """
# 检验问题解释

## 问题设计思路
{main_content}

## 考察要点
{key_points}

## 答题提示
{examples}

---
**生成Agent**: {agent_type}
**置信度**: {agent_confidence}
**生成时间**: {timestamp}
"""
        }
        return templates.get(agent_type, templates["clarification-path"])


class IntelligentLayoutOptimizer:
    """智能布局优化器"""

    def __init__(self):
        self.grid_size = 50  # 网格大小
        self.min_spacing = 100  # 最小间距
        self.alignment_threshold = 25  # 对齐阈值
        self.VERTICAL_SPACING_BASE = 380  # 基础垂直间距
        self.CLUSTER_GAP = 100  # 聚类间距
        self.HORIZONTAL_OFFSET = 50  # 水平偏移

    def optimize_new_nodes_layout(
        self,
        canvas_data: Dict[str, Any],
        new_nodes: List[Dict[str, Any]],
        reference_nodes: List[str]
    ) -> Dict[str, Any]:
        """优化新节点布局"""
        optimized_positions = {}

        # 获取现有节点位置信息
        existing_nodes = canvas_data.get("nodes", [])
        existing_positions = {(node.get("x", 0), node.get("y", 0)): node.get("id")
                           for node in existing_nodes}

        for i, new_node in enumerate(new_nodes):
            reference_node_id = reference_nodes[i] if i < len(reference_nodes) else None
            reference_node = None

            if reference_node_id:
                reference_node = next((n for n in existing_nodes if n.get("id") == reference_node_id), None)

            if reference_node:
                # 基于参考节点计算位置
                optimal_pos = self.calculate_optimal_position(
                    reference_node,
                    new_node.get("metadata", {}).get("node_type", "explanation"),
                    existing_nodes,
                    i
                )
            else:
                # 默认位置
                optimal_pos = (100 + i * 350, 100 + i * 200)

            # 检测并解决重叠
            final_pos = self.resolve_overlap(optimal_pos, existing_positions, new_nodes[:i])

            # 对齐到网格
            final_pos = self.align_to_grid(final_pos)

            optimized_positions[new_node.get("id")] = {
                "x": final_pos[0],
                "y": final_pos[1]
            }

        return optimized_positions

    def calculate_optimal_position(
        self,
        reference_node: Dict[str, Any],
        node_type: str,
        existing_nodes: List[Dict[str, Any]],
        index: int = 0
    ) -> Tuple[int, int]:
        """计算节点的最优位置"""
        ref_x = reference_node.get("x", 0)
        ref_y = reference_node.get("y", 0)
        ref_width = reference_node.get("width", 300)
        ref_height = reference_node.get("height", 200)

        if node_type == "explanation":
            # 解释节点在参考节点右侧
            x = ref_x + ref_width + self.HORIZONTAL_OFFSET
            y = ref_y
        elif node_type == "summary":
            # 总结节点在解释节点下方
            x = ref_x + self.HORIZONTAL_OFFSET
            y = ref_y + ref_height + 50
        else:
            # 默认位置
            x = ref_x + ref_width + self.HORIZONTAL_OFFSET
            y = ref_y + (index * 150)

        return (x, y)

    def resolve_overlap(
        self,
        position: Tuple[int, int],
        existing_positions: Dict[Tuple[int, int], str],
        new_nodes: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """检测并解决节点重叠"""
        x, y = position
        node_width = 320
        node_height = 200
        max_attempts = 100  # 防止无限循环
        attempts = 0

        while attempts < max_attempts:
            overlap_found = False

            # 检查与现有节点的重叠
            for (ex_x, ex_y), _ in existing_positions.items():
                if self._is_overlapping((x, y), (ex_x, ex_y), node_width, node_height, 300, 200):
                    y = ex_y + 250
                    overlap_found = True
                    break

            if not overlap_found:
                # 检查与新节点的重叠
                for new_node in new_nodes:
                    nx = new_node.get("x", 0)
                    ny = new_node.get("y", 0)
                    if self._is_overlapping((x, y), (nx, ny), node_width, node_height, 320, 200):
                        y = ny + 250
                        overlap_found = True
                        break

            if not overlap_found:
                break

            attempts += 1

        return (x, y)

    def _is_overlapping(
        self,
        pos1: Tuple[int, int],
        pos2: Tuple[int, int],
        width1: int,
        height1: int,
        width2: int,
        height2: int
    ) -> bool:
        """判断两个矩形是否重叠"""
        x1, y1 = pos1
        x2, y2 = pos2

        return not (x1 + width1 < x2 or x2 + width2 < x1 or
                   y1 + height1 < y2 or y2 + height2 < y1)

    def align_to_grid(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """将节点对齐到网格"""
        x, y = position
        aligned_x = round(x / self.grid_size) * self.grid_size
        aligned_y = round(y / self.grid_size) * self.grid_size
        return (aligned_x, aligned_y)


class AutoNodeGenerator:
    """自动节点生成器 - Story 10.4核心实现"""

    def __init__(self):
        self.canvas_operator = CanvasJSONOperator()
        self.layout_optimizer = IntelligentLayoutOptimizer()
        self.id_generator = NodeIDGenerator()
        self.content_generator = NodeContentGenerator()
        self.connection_rules = NodeConnectionRules()

        if LOGURU_ENABLED:
            logger.info("AutoNodeGenerator initialized successfully")

    async def generate_nodes_from_agent_results(
        self,
        canvas_path: str,
        agent_results: List[Dict[str, Any]],
        reference_nodes: List[str]
    ) -> Dict[str, Any]:
        """从Agent执行结果生成节点

        Args:
            canvas_path: Canvas文件路径
            agent_results: Agent执行结果列表
            reference_nodes: 参考节点ID列表

        Returns:
            Dict: 生成的节点和连接信息
        """
        try:
            # 读取Canvas数据
            canvas_data = self.canvas_operator.read_canvas(canvas_path)

            # 创建解释节点和总结节点
            new_nodes = []
            connections = []

            for i, (agent_result, reference_node_id) in enumerate(zip(agent_results, reference_nodes)):
                # 获取参考节点
                reference_node = self.canvas_operator.find_node_by_id(canvas_data, reference_node_id)
                if not reference_node:
                    if LOGURU_ENABLED:
                        logger.warning(f"Reference node not found: {reference_node_id}")
                    continue

                # 创建蓝色解释节点
                explanation_node = self.create_explanation_node(agent_result, reference_node)
                new_nodes.append(explanation_node)

                # 创建黄色总结节点
                summary_node = self.create_summary_node(explanation_node, reference_node)
                new_nodes.append(summary_node)

                # 创建连接
                # 连接1: 参考节点 -> 解释节点
                connection1 = self.connection_rules.create_connection(
                    reference_node_id,
                    explanation_node["id"],
                    "explanation"
                )
                connections.append(connection1)

                # 连接2: 解释节点 -> 总结节点
                connection2 = self.connection_rules.create_connection(
                    explanation_node["id"],
                    summary_node["id"],
                    "summary"
                )
                connections.append(connection2)

            # 优化布局
            reference_node_ids = [ref for ref in reference_nodes
                                if self.canvas_operator.find_node_by_id(canvas_data, ref)]
            optimized_positions = self.layout_optimizer.optimize_new_nodes_layout(
                canvas_data,
                new_nodes,
                reference_node_ids
            )

            # 应用优化后的位置
            for node in new_nodes:
                node_id = node.get("id")
                if node_id in optimized_positions:
                    node["x"] = optimized_positions[node_id]["x"]
                    node["y"] = optimized_positions[node_id]["y"]

            # 批量添加节点到Canvas
            added_nodes = []
            for node in new_nodes:
                added_node_id = self.canvas_operator.create_node(
                    canvas_data,
                    node["type"],
                    node["x"],
                    node["y"],
                    node["width"],
                    node["height"],
                    node["color"],
                    node["text"]
                )
                added_nodes.append(added_node_id)

            # 添加连接到Canvas
            added_edges = []
            for connection in connections:
                edge_id = self.canvas_operator.create_edge(
                    canvas_data,
                    connection["fromNode"],
                    connection["toNode"],
                    connection["fromSide"],
                    connection["toSide"],
                    connection["label"],
                    connection.get("color")
                )
                added_edges.append(edge_id)

            # 保存Canvas文件
            self.canvas_operator.write_canvas(canvas_path, canvas_data)

            result = {
                "status": "success",
                "added_nodes": len(added_nodes),
                "added_edges": len(added_edges),
                "node_ids": added_nodes,
                "edge_ids": added_edges,
                "message": f"Successfully generated {len(added_nodes)} nodes and {len(added_edges)} connections"
            }

            if LOGURU_ENABLED:
                logger.info(f"Generated {len(added_nodes)} nodes from {len(agent_results)} agent results")

            return result

        except FileNotFoundError as e:
            error_msg = f"Canvas file not found: {canvas_path}. {str(e)}"
            if LOGURU_ENABLED:
                logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "added_nodes": 0,
                "added_edges": 0
            }
        except json.JSONDecodeError as e:
            error_msg = f"Invalid Canvas file format: {canvas_path}. {str(e)}"
            if LOGURU_ENABLED:
                logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "added_nodes": 0,
                "added_edges": 0
            }
        except Exception as e:
            error_msg = f"Unexpected error generating nodes from agent results: {str(e)}"
            if LOGURU_ENABLED:
                logger.error(error_msg)
                logger.exception("Full traceback:")
            return {
                "status": "error",
                "error": error_msg,
                "added_nodes": 0,
                "added_edges": 0
            }

    def create_explanation_node(
        self,
        agent_result: Dict[str, Any],
        reference_node: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建蓝色解释节点"""
        agent_type = agent_result.get("agent_type", "clarification-path")

        # 生成解释内容
        explanation_content = self.content_generator.generate_explanation_content(
            agent_result,
            agent_type
        )

        # 创建节点
        explanation_node = {
            "id": self.id_generator.generate_explanation_node_id(),
            "type": "text",
            "text": explanation_content,
            "x": 0,  # 将由布局优化器设置
            "y": 0,
            "width": 320,
            "height": 200,
            "color": "5",  # 蓝色
            "metadata": {
                "node_type": "ai_explanation",
                "agent_name": agent_type,
                "generated_from": reference_node.get("id"),
                "generation_time": datetime.now().isoformat(),
                "content_type": "explanation",
                "version": "1.0"
            }
        }

        return explanation_node

    def create_summary_node(
        self,
        explanation_node: Dict[str, Any],
        reference_node: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建黄色总结节点"""
        agent_type = explanation_node.get("metadata", {}).get("agent_name", "agent")
        explanation_content = explanation_node.get("text", "")

        # 生成总结提示
        summary_prompt = self.content_generator.generate_summary_prompt(
            explanation_content,
            reference_node.get("text", ""),
            agent_type
        )

        # 创建节点
        summary_node = {
            "id": self.id_generator.generate_summary_node_id(),
            "type": "text",
            "text": summary_prompt,
            "x": 0,  # 将由布局优化器设置
            "y": 0,
            "width": 300,
            "height": 180,
            "color": "6",  # 黄色
            "metadata": {
                "node_type": "user_summary",
                "generated_from": explanation_node.get("id"),
                "reference_node": reference_node.get("id"),
                "generation_time": datetime.now().isoformat(),
                "prompt_type": "summary_reflection",
                "version": "1.0"
            }
        }

        return summary_node

    def connect_nodes_intelligently(
        self,
        canvas_data: Dict[str, Any],
        new_nodes: List[Dict[str, Any]],
        reference_nodes: List[str]
    ) -> None:
        """智能连接节点（已集成到主流程中）"""
        # 此方法的逻辑已集成到generate_nodes_from_agent_results中
        pass

    def optimize_node_layout(
        self,
        canvas_data: Dict[str, Any],
        new_nodes: List[Dict[str, Any]]
    ) -> None:
        """优化节点布局（已集成到主流程中）"""
        # 此方法的逻辑已集成到generate_nodes_from_agent_results中
        pass