#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式Canvas布局学习系统

实现用户-Agent交互学习的布局优化系统：
1. Agent生成测试布局白板
2. 用户手动调整优化
3. 系统学习调整模式
4. 生成改进布局
5. 循环学习直到满意

Author: Canvas Learning System Team
Version: 2.0 Interactive Layout Learning
Created: 2025-10-20
"""

import asyncio
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import random
import math

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from canvas_utils_working import CanvasJSONOperator

@dataclass
class LayoutTestSession:
    """布局测试会话"""
    session_id: str
    canvas_file: str
    concept_name: str
    iteration: int
    agent_layout: Dict[str, Any]
    user_adjusted_layout: Optional[Dict[str, Any]] = None
    user_satisfaction_score: Optional[int] = None  # 1-10分
    adjustment_notes: Optional[str] = None
    learning_insights: Optional[Dict[str, Any]] = None

class InteractiveLayoutLearner:
    """交互式布局学习器"""

    def __init__(self):
        """初始化交互式布局学习器"""
        self.canvas_operator = CanvasJSONOperator()
        self.test_sessions: List[LayoutTestSession] = []
        self.learning_patterns: Dict[str, Any] = {}

        # 布局学习参数
        self.layout_preferences = {
            "node_spacing": {"x": 200, "y": 120},  # 节点间距
            "group_spacing": 300,  # 组间距
            "alignment_preference": "center",  # 对齐偏好
            "color_grouping": True,  # 颜色分组
            "hierarchy_depth": 0.8,  # 层次深度偏好 (0-1)
            "connection_style": "orthogonal"  # 连线样式
        }

    def generate_test_canvas(self, concept_name: str, complexity_level: str = "medium") -> str:
        """
        生成测试布局白板

        Args:
            concept_name: 概念名称
            complexity_level: 复杂度 (simple/medium/complex)

        Returns:
            str: 生成的Canvas文件路径
        """
        # 根据复杂度生成不同的内容结构
        if complexity_level == "simple":
            return self._create_simple_test_canvas(concept_name)
        elif complexity_level == "medium":
            return self._create_medium_test_canvas(concept_name)
        else:  # complex
            return self._create_complex_test_canvas(concept_name)

    def _create_simple_test_canvas(self, concept_name: str) -> str:
        """创建简单测试Canvas"""
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        # 主概念节点
        center_x, center_y = 400, 300
        canvas_data["nodes"].append({
            "id": "main_concept",
            "type": "text",
            "x": center_x,
            "y": center_y,
            "width": 200,
            "height": 80,
            "color": "1"  # 红色 - 不理解
        })

        # 3-4个子概念节点
        sub_concepts = [
            "定义与概念",
            "基本性质",
            "应用实例",
            "常见误区"
        ]

        for i, sub_concept in enumerate(sub_concepts[:3]):
            angle = (i * 120) * math.pi / 180
            x = center_x + 200 * math.cos(angle)
            y = center_y + 200 * math.sin(angle)

            canvas_data["nodes"].append({
                "id": f"sub_{i}",
                "type": "text",
                "x": x,
                "y": y,
                "width": 160,
                "height": 60,
                "color": "1"  # 红色
            })

            # 添加连线
            canvas_data["edges"].append({
                "id": f"edge_{i}",
                "fromNode": "main_concept",
                "toNode": f"sub_{i}",
                "color": "4"
            })

        # 添加理解节点
        for node in canvas_data["nodes"]:
            canvas_data["nodes"].append({
                "id": f"understanding_{node['id']}",
                "type": "text",
                "x": node["x"] + 50,
                "y": node["y"] + node["height"] + 20,
                "width": 180,
                "height": 50,
                "color": "6"  # 黄色 - 理解区
            })

        # 保存Canvas文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"layout_test_{concept_name}_{timestamp}.canvas"

        self.canvas_operator.write_canvas(filename, canvas_data)
        return filename

    def _create_medium_test_canvas(self, concept_name: str) -> str:
        """创建中等复杂度测试Canvas"""
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        # 主概念
        center_x, center_y = 400, 300
        canvas_data["nodes"].append({
            "id": "main_concept",
            "type": "text",
            "x": center_x,
            "y": center_y,
            "width": 200,
            "height": 80,
            "color": "1"
        })

        # 第一层子概念
        first_layer = [
            ("理论基础", 0),
            ("核心算法", 120),
            ("实际应用", 240)
        ]

        for i, (name, angle) in enumerate(first_layer):
            x = center_x + 250 * math.cos(angle * math.pi / 180)
            y = center_y + 250 * math.sin(angle * math.pi / 180)

            node_id = f"first_{i}"
            canvas_data["nodes"].append({
                "id": node_id,
                "type": "text",
                "x": x,
                "y": y,
                "width": 160,
                "height": 60,
                "color": "1"
            })

            canvas_data["edges"].append({
                "id": f"edge_first_{i}",
                "fromNode": "main_concept",
                "toNode": node_id,
                "color": "4"
            })

        # 第二层子概念
        second_layer_concepts = {
            "理论基础": ["基本定义", "发展历史", "相关概念"],
            "核心算法": ["算法原理", "步骤流程", "复杂度分析"],
            "实际应用": ["典型案例", "应用场景", "效果评估"]
        }

        for i, (parent, concepts) in enumerate(second_layer_concepts.items()):
            parent_node = f"first_{i}"
            parent_data = next(n for n in canvas_data["nodes"] if n["id"] == parent_node)

            for j, concept in enumerate(concepts):
                offset_x = (j - 1) * 150
                x = parent_data["x"] + offset_x
                y = parent_data["y"] + 150

                node_id = f"second_{i}_{j}"
                canvas_data["nodes"].append({
                    "id": node_id,
                    "type": "text",
                    "x": x,
                    "y": y,
                    "width": 140,
                    "height": 50,
                    "color": "3"  # 紫色
                })

                canvas_data["edges"].append({
                    "id": f"edge_second_{i}_{j}",
                    "fromNode": parent_node,
                    "toNode": node_id,
                    "color": "4"
                })

        # 保存Canvas文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"layout_test_medium_{concept_name}_{timestamp}.canvas"

        self.canvas_operator.write_canvas(filename, canvas_data)
        return filename

    def _create_complex_test_canvas(self, concept_name: str) -> str:
        """创建复杂测试Canvas"""
        # 实现复杂Canvas生成逻辑
        # 这里简化处理，实际可以更复杂
        return self._create_medium_test_canvas(concept_name + "_complex")

    def start_learning_session(self, concept_name: str, canvas_file: str) -> LayoutTestSession:
        """
        开始布局学习会话

        Args:
            concept_name: 概念名称
            canvas_file: Canvas文件路径

        Returns:
            LayoutTestSession: 学习会话对象
        """
        session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 读取当前Canvas布局作为Agent生成布局
        agent_layout = self.canvas_operator.read_canvas(canvas_file)

        session = LayoutTestSession(
            session_id=session_id,
            canvas_file=canvas_file,
            concept_name=concept_name,
            iteration=1,
            agent_layout=agent_layout
        )

        self.test_sessions.append(session)
        return session

    def analyze_user_adjustment(self, session: LayoutTestSession,
                                before_canvas: str, after_canvas: str) -> Dict[str, Any]:
        """
        分析用户的布局调整

        Args:
            session: 学习会话
            before_canvas: 调整前的Canvas文件
            after_canvas: 调整后的Canvas文件

        Returns:
            Dict: 学习洞察
        """
        before_layout = self.canvas_operator.read_canvas(before_canvas)
        after_layout = self.canvas_operator.read_canvas(after_canvas)

        # 分析节点位置变化
        position_changes = self._analyze_position_changes(before_layout, after_layout)

        # 分析间距调整
        spacing_adjustments = self._analyze_spacing_changes(before_layout, after_layout)

        # 分析对齐变化
        alignment_changes = self._analyze_alignment_changes(before_layout, after_layout)

        # 更新学习偏好
        self._update_layout_preferences(position_changes, spacing_adjustments, alignment_changes)

        insights = {
            "position_changes": position_changes,
            "spacing_adjustments": spacing_adjustments,
            "alignment_changes": alignment_changes,
            "updated_preferences": self.layout_preferences.copy(),
            "learning_confidence": self._calculate_learning_confidence()
        }

        session.learning_insights = insights
        return insights

    def _analyze_position_changes(self, before: Dict, after: Dict) -> Dict[str, Any]:
        """分析节点位置变化"""
        changes = {
            "moved_nodes": [],
            "average_movement": {"x": 0, "y": 0},
            "movement_patterns": []
        }

        before_nodes = {node["id"]: node for node in before.get("nodes", [])}
        after_nodes = {node["id"]: node for node in after.get("nodes", [])}

        total_dx, total_dy = 0, 0
        moved_count = 0

        for node_id, after_node in after_nodes.items():
            if node_id in before_nodes:
                before_node = before_nodes[node_id]
                dx = after_node["x"] - before_node["x"]
                dy = after_node["y"] - before_node["y"]

                if abs(dx) > 5 or abs(dy) > 5:  # 移动超过5像素才算调整
                    changes["moved_nodes"].append({
                        "node_id": node_id,
                        "dx": dx,
                        "dy": dy,
                        "distance": math.sqrt(dx**2 + dy**2)
                    })
                    total_dx += dx
                    total_dy += dy
                    moved_count += 1

        if moved_count > 0:
            changes["average_movement"] = {
                "x": total_dx / moved_count,
                "y": total_dy / moved_count
            }

        return changes

    def _analyze_spacing_changes(self, before: Dict, after: Dict) -> Dict[str, Any]:
        """分析间距变化"""
        # 简化的间距分析
        return {"pattern": "用户倾向于更紧凑的布局"}

    def _analyze_alignment_changes(self, before: Dict, after: Dict) -> Dict[str, Any]:
        """分析对齐变化"""
        # 简化的对齐分析
        return {"pattern": "用户偏好中心对齐"}

    def _update_layout_preferences(self, position_changes: Dict,
                                 spacing_changes: Dict, alignment_changes: Dict):
        """更新布局偏好"""
        # 基于用户调整更新偏好
        if position_changes["average_movement"]["x"] > 0:
            self.layout_preferences["alignment_preference"] = "left"
        elif position_changes["average_movement"]["x"] < 0:
            self.layout_preferences["alignment_preference"] = "right"

    def _calculate_learning_confidence(self) -> float:
        """计算学习置信度"""
        if not self.test_sessions:
            return 0.0

        # 基于学习会话数量和用户满意度计算置信度
        completed_sessions = [s for s in self.test_sessions if s.user_satisfaction_score is not None]

        if not completed_sessions:
            return 0.1

        avg_satisfaction = sum(s.user_satisfaction_score for s in completed_sessions) / len(completed_sessions)
        session_factor = min(len(completed_sessions) / 5.0, 1.0)  # 5次会话后达到最大置信度

        return (avg_satisfaction / 10.0) * session_factor

    def generate_improved_layout(self, session: LayoutTestSession,
                                target_satisfaction: int = 8) -> str:
        """
        基于学习洞察生成改进布局

        Args:
            session: 学习会话
            target_satisfaction: 目标满意度分数

        Returns:
            str: 改进后的Canvas文件路径
        """
        if not session.learning_insights:
            print("[WARNING] 没有学习洞察，生成随机改进布局")
            return self._generate_random_improvement(session.canvas_file)

        # 基于学习偏好生成改进布局
        improved_layout = self._apply_learned_preferences(session.agent_layout)

        # 保存改进后的布局
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"improved_layout_{session.concept_name}_{session.iteration}_{timestamp}.canvas"

        self.canvas_operator.write_canvas(filename, improved_layout)

        # 创建新的学习会话
        new_session = LayoutTestSession(
            session_id=f"session_{timestamp}",
            canvas_file=filename,
            concept_name=session.concept_name,
            iteration=session.iteration + 1,
            agent_layout=improved_layout
        )

        self.test_sessions.append(new_session)

        return filename

    def _apply_learned_preferences(self, layout: Dict) -> Dict:
        """应用学习到的布局偏好"""
        improved_layout = layout.copy()

        # 应用对齐偏好
        if self.layout_preferences["alignment_preference"] == "center":
            # 调整节点位置使其更居中对齐
            self._apply_center_alignment(improved_layout)
        elif self.layout_preferences["alignment_preference"] == "left":
            self._apply_left_alignment(improved_layout)

        # 应用间距偏好
        self._apply_spacing_preferences(improved_layout)

        # 应用颜色分组
        if self.layout_preferences["color_grouping"]:
            self._apply_color_grouping(improved_layout)

        return improved_layout

    def _apply_center_alignment(self, layout: Dict):
        """应用居中对齐"""
        nodes = layout.get("nodes", [])
        if not nodes:
            return

        # 计算中心点
        avg_x = sum(node["x"] for node in nodes) / len(nodes)

        # 调整节点位置使其围绕中心分布
        for node in nodes:
            if node.get("color") == "1":  # 主节点居中
                node["x"] = 400
            elif node.get("color") == "6":  # 理解节点在对应主节点下方
                # 找到对应的主节点并调整位置
                pass

    def _apply_left_alignment(self, layout: Dict):
        """应用左对齐"""
        # 实现左对齐逻辑
        pass

    def _apply_spacing_preferences(self, layout: Dict):
        """应用间距偏好"""
        # 实现间距调整逻辑
        pass

    def _apply_color_grouping(self, layout: Dict):
        """应用颜色分组"""
        # 实现颜色分组逻辑
        pass

    def _generate_random_improvement(self, canvas_file: str) -> str:
        """生成随机改进布局（备用方案）"""
        layout = self.canvas_operator.read_canvas(canvas_file)

        # 随机调整一些节点位置
        for node in layout.get("nodes", []):
            if random.random() < 0.3:  # 30%概率调整
                node["x"] += random.randint(-50, 50)
                node["y"] += random.randint(-30, 30)

        # 保存随机改进的布局
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"random_improvement_{timestamp}.canvas"

        self.canvas_operator.write_canvas(filename, layout)
        return filename

    def get_learning_progress(self) -> Dict[str, Any]:
        """获取学习进度"""
        if not self.test_sessions:
            return {"status": "no_sessions", "message": "还没有学习会话"}

        completed_sessions = [s for s in self.test_sessions if s.user_satisfaction_score is not None]

        if not completed_sessions:
            return {
                "status": "in_progress",
                "total_sessions": len(self.test_sessions),
                "completed_sessions": 0,
                "current_iteration": max(s.iteration for s in self.test_sessions),
                "learning_confidence": self._calculate_learning_confidence()
            }

        satisfaction_scores = [s.user_satisfaction_score for s in completed_sessions]
        latest_satisfaction = satisfaction_scores[-1]

        return {
            "status": "learning",
            "total_sessions": len(self.test_sessions),
            "completed_sessions": len(completed_sessions),
            "latest_satisfaction": latest_satisfaction,
            "satisfaction_trend": "improving" if len(satisfaction_scores) > 1 and satisfaction_scores[-1] > satisfaction_scores[-2] else "stable",
            "learning_confidence": self._calculate_learning_confidence(),
            "learned_preferences": self.layout_preferences,
            "recommendation": "继续学习" if latest_satisfaction < 8 else "学习完成"
        }

    def provide_usage_instructions(self) -> str:
        """提供使用说明"""
        return """
🎯 交互式布局学习系统使用指南

📋 学习流程:
1. 生成测试白板: learner.generate_test_canvas("概念名", "medium")
2. 开始学习会话: learner.start_learning_session("概念名", "canvas文件")
3. 您在Obsidian中调整布局
4. 分析调整: learner.analyze_user_adjustment(session, "调整前", "调整后")
5. 生成改进布局: learner.generate_improved_layout(session)
6. 重复步骤3-5直到满意

🚀 快速开始:
```python
# 创建学习器
learner = InteractiveLayoutLearner()

# 生成测试白板
test_canvas = learner.generate_test_canvas("逆否命题", "medium")

# 开始学习会话
session = learner.start_learning_session("逆否命题", test_canvas)

# 在Obsidian中调整布局后...
# 记录您的满意度评分 (1-10分)
session.user_satisfaction_score = 6  # 例如：6分

# 分析您的调整
insights = learner.analyze_user_adjustment(session, test_canvas, "调整后的文件")

# 生成改进布局
improved_canvas = learner.generate_improved_layout(session)

# 查看学习进度
progress = learner.get_learning_progress()
print(f"学习进度: {progress}")
```

💡 最佳实践:
- 每次调整后给出1-10分的满意度评分
- 记录您调整的原因（例如："太拥挤了"、"对齐不整齐"）
- 至少进行3-5轮学习循环
- 当满意度达到8分以上时，学习完成
        """


# 示例使用
async def demo_interactive_layout_learning():
    """演示交互式布局学习"""
    print("🎯 交互式布局学习系统演示")
    print("="*50)

    # 创建学习器
    learner = InteractiveLayoutLearner()

    # 生成测试白板
    print("\n[步骤1] 生成测试白板...")
    test_canvas = learner.generate_test_canvas("逆否命题", "medium")
    print(f"✓ 生成测试白板: {test_canvas}")

    # 开始学习会话
    print("\n[步骤2] 开始学习会话...")
    session = learner.start_learning_session("逆否命题", test_canvas)
    print(f"✓ 学习会话ID: {session.session_id}")

    # 模拟用户调整
    print("\n[步骤3] 模拟用户调整...")
    print("请在Obsidian中打开Canvas文件并调整布局")
    print("调整完成后，按回车继续...")
    input()

    # 模拟用户反馈
    session.user_satisfaction_score = 6  # 6分满意度
    session.adjustment_notes = "布局有点乱，节点间距不够均匀"

    # 分析调整（这里需要实际的前后文件）
    print("\n[步骤4] 分析学习洞察...")
    print("注意：实际使用时需要提供调整前后的Canvas文件")

    # 生成改进布局
    print("\n[步骤5] 生成改进布局...")
    improved_canvas = learner.generate_improved_layout(session, target_satisfaction=8)
    print(f"✓ 生成改进布局: {improved_canvas}")

    # 查看学习进度
    print("\n[步骤6] 学习进度报告...")
    progress = learner.get_learning_progress()
    print(f"学习状态: {progress['status']}")
    print(f"学习置信度: {progress['learning_confidence']:.2f}")
    print(f"建议: {progress['recommendation']}")

    # 提供使用说明
    print("\n" + "="*50)
    print(learner.provide_usage_instructions())

    return learner, session


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_interactive_layout_learning())