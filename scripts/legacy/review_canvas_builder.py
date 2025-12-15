"""
复习Canvas构建器 - Canvas学习系统

本模块实现智能复习计划的Canvas白板构建功能，负责：
- 根据复习计划生成个性化复习Canvas文件
- 实现检验问题的智能生成和布局
- 提供提示信息和学习建议的集成
- 支持Canvas模板应用和动态定制

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-23
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path

# 导入相关模块
try:
    from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic, CanvasOrchestrator
    from intelligent_review_generator import ReviewPlan, ReviewSession, ReviewConcept
except ImportError as e:
    print(f"Warning: 无法导入依赖模块 {e}，某些功能可能受限")


class ReviewCanvasBuilder:
    """复习Canvas构建器

    负责根据智能复习计划生成个性化的复习Canvas白板文件。
    支持多种布局模式和内容定制，提供直观的可视化复习体验。
    """

    def __init__(self):
        """初始化Canvas构建器"""
        # Canvas布局配置
        self.LAYOUT_CONFIG = {
            "node_spacing": {
                "horizontal": 500,
                "vertical": 400,
                "question_to_yellow": 30,
                "session_spacing": 600,
            },
            "node_dimensions": {
                "intro": {"width": 600, "height": 200},
                "concept": {"width": 450, "height": 300},
                "question": {"width": 400, "height": 250},
                "yellow": {"width": 350, "height": 150},
                "hint": {"width": 300, "height": 120},
                "session_separator": {"width": 800, "height": 80},
            },
            "canvas_margins": {"top": 100, "left": 100, "right": 100, "bottom": 100},
        }

        # 颜色配置
        self.COLORS = {
            "intro": "5",       # 蓝色 - 介绍信息
            "concept": "1",     # 红色 - 待复习概念
            "question": "1",    # 红色 - 检验问题
            "yellow": "6",      # 黄色 - 个人理解区
            "hint": "5",        # 蓝色 - 提示信息
            "separator": "3",   # 紫色 - 分隔符
            "progress": "2",    # 绿色 - 进度信息
        }

    def create_review_canvas(
        self,
        review_plan: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """创建复习Canvas

        Args:
            review_plan: 复习计划数据
            output_path: 输出文件路径，None时自动生成

        Returns:
            str: 生成的Canvas文件路径
        """
        try:
            # 生成输出文件名
            if output_path is None:
                target_canvas = review_plan.get("target_canvas", "unknown")
                canvas_name = self._generate_canvas_name(target_canvas)
                output_path = f"笔记库/{canvas_name}.canvas"

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 创建Canvas结构
            canvas_data = self._create_canvas_structure(review_plan)

            # 写入Canvas文件
            CanvasJSONOperator.write_canvas(output_path, canvas_data)

            return output_path

        except Exception as e:
            raise RuntimeError(f"复习Canvas创建失败: {str(e)}")

    def _generate_canvas_name(self, target_canvas: str) -> str:
        """生成Canvas文件名

        Args:
            target_canvas: 目标Canvas名称

        Returns:
            str: 生成的文件名
        """
        # 提取基础名称
        base_name = os.path.splitext(os.path.basename(target_canvas))[0]

        # 添加时间戳
        timestamp = datetime.now().strftime("%Y%m%d")

        return f"{base_name}-智能复习-{timestamp}"

    def _create_canvas_structure(self, review_plan: Dict[str, Any]) -> Dict[str, Any]:
        """创建Canvas结构

        Args:
            review_plan: 复习计划数据

        Returns:
            Dict: Canvas JSON数据
        """
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        # 当前位置
        current_x = self.LAYOUT_CONFIG["canvas_margins"]["left"]
        current_y = self.LAYOUT_CONFIG["canvas_margins"]["top"]

        # 1. 添加介绍节点
        intro_node, current_y = self._add_intro_node(canvas_data, review_plan, current_x, current_y)

        # 2. 添加进度跟踪节点
        progress_node, current_y = self._add_progress_node(canvas_data, review_plan, current_x, current_y)

        # 3. 添加复习会话
        sessions = review_plan.get("review_sessions", [])
        for i, session in enumerate(sessions):
            # 添加会话分隔符
            if i > 0:
                separator_node, current_y = self._add_session_separator(
                    canvas_data, session, i + 1, current_x, current_y
                )

            # 添加会话内容
            session_nodes, current_y = self._add_review_session(
                canvas_data, session, current_x, current_y
            )

        # 4. 添加学习建议节点
        suggestions_node, current_y = self._add_suggestions_node(canvas_data, review_plan, current_x, current_y)

        # 5. 添加总结节点
        summary_node, current_y = self._add_summary_node(canvas_data, review_plan, current_x, current_y)

        return canvas_data

    def _add_intro_node(
        self,
        canvas_data: Dict[str, Any],
        review_plan: Dict[str, Any],
        x: int,
        y: int
    ) -> Tuple[Dict[str, Any], int]:
        """添加介绍节点

        Args:
            canvas_data: Canvas数据
            review_plan: 复习计划
            x: X坐标
            y: Y坐标

        Returns:
            Tuple[Dict, int]: 节点数据和新的Y坐标
        """
        plan_type = review_plan.get("plan_type", "weakness_focused")
        target_canvas = review_plan.get("target_canvas", "")
        generation_time = review_plan.get("generation_timestamp", "")

        # 格式化时间
        try:
            dt = datetime.fromisoformat(generation_time.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y年%m月%d日 %H:%M")
        except:
            formatted_time = generation_time

        plan_type_names = {
            "weakness_focused": "薄弱环节导向复习",
            "comprehensive_review": "全面复习",
            "targeted_review": "针对性复习"
        }

        intro_text = f"""# {plan_type_names.get(plan_type, plan_type)}

**目标Canvas**: {target_canvas}
**生成时间**: {formatted_time}

## 📋 复习概览

- **复习策略**: {plan_type_names.get(plan_type, plan_type)}
- **预计时长**: {review_plan.get('estimated_completion_time', {}).get('total_estimated_minutes', 0)} 分钟
- **复习会话**: {len(review_plan.get('review_sessions', []))} 个

## 💡 使用指南

1. **按顺序复习**: 从上到下依次完成每个概念的复习
2. **充分思考**: 在黄色节点中用自己的话详细解释
3. **诚实评估**: 根据理解程度诚实填写，不要查阅资料
4. **标记难点**: 遇到困难的概念标记为红色，后续重点复习

## 🎯 复习目标

{self._generate_review_objectives_text(review_plan)}"""

        node = {
            "id": f"intro-{uuid.uuid4().hex[:12]}",
            "type": "text",
            "text": intro_text,
            "x": x,
            "y": y,
            "width": self.LAYOUT_CONFIG["node_dimensions"]["intro"]["width"],
            "height": self.LAYOUT_CONFIG["node_dimensions"]["intro"]["height"],
            "color": self.COLORS["intro"]
        }

        canvas_data["nodes"].append(node)

        new_y = y + node["height"] + self.LAYOUT_CONFIG["node_spacing"]["vertical"]
        return node, new_y

    def _generate_review_objectives_text(self, review_plan: Dict[str, Any]) -> str:
        """生成复习目标文本

        Args:
            review_plan: 复习计划

        Returns:
            str: 复习目标文本
        """
        objectives = []

        # 从学习分析中提取目标
        analysis_summary = review_plan.get("learning_analysis_summary", {})
        if analysis_summary:
            concepts_count = analysis_summary.get("concepts_needing_review", 0)
            if concepts_count > 0:
                objectives.append(f"• 掌握 {concepts_count} 个薄弱概念")

        # 从个性化特征中提取目标
        personalization = review_plan.get("personalization_features", {})
        motivation = personalization.get("motivation_elements", {})
        milestones = motivation.get("achievement_milestones", [])

        for milestone in milestones[:3]:
            objectives.append(f"• {milestone}")

        return "\n".join(objectives) if objectives else "• 巩固核心概念理解\n• 提升知识应用能力"

    def _add_progress_node(
        self,
        canvas_data: Dict[str, Any],
        review_plan: Dict[str, Any],
        x: int,
        y: int
    ) -> Tuple[Dict[str, Any], int]:
        """添加进度跟踪节点

        Args:
            canvas_data: Canvas数据
            review_plan: 复习计划
            x: X坐标
            y: Y坐标

        Returns:
            Tuple[Dict, int]: 节点数据和新的Y坐标
        """
        sessions = review_plan.get("review_sessions", [])
        total_concepts = sum(len(session.get("concepts", [])) for session in sessions)

        progress_text = f"""## 📊 复习进度跟踪

**总概念数**: {total_concepts}
**已完成**: 0/{total_concepts}
**完成率**: 0%

### 复习记录表

| 概念名称 | 理解程度(1-10) | 用时(分钟) | 备注 |
|---------|---------------|----------|------|
"""

        # 为每个概念添加记录行
        for session in sessions:
            for concept in session.get("concepts", []):
                concept_name = concept.get("concept_name", "")
                progress_text += f"| {concept_name} | ⏳ | ⏳ | |\n"

        progress_text += """
### 完成标准

- ✅ **优秀理解** (8-10分): 能清晰解释并举例
- ⚠️ **基本理解** (5-7分): 理解核心但需练习
- ❌ **需要加强** (1-4分): 理解不足需重新学习

### 🎯 奖励机制

- 完成率达到80%以上: 🏆 复习达人
- 所有概念达到7分以上: ⭐ 掌握大师
- 用时控制在预估范围内: ⚡ 效率之星"""

        node = {
            "id": f"progress-{uuid.uuid4().hex[:12]}",
            "type": "text",
            "text": progress_text,
            "x": x,
            "y": y,
            "width": self.LAYOUT_CONFIG["node_dimensions"]["intro"]["width"],
            "height": 400,  # 根据内容调整高度
            "color": self.COLORS["progress"]
        }

        canvas_data["nodes"].append(node)

        new_y = y + node["height"] + self.LAYOUT_CONFIG["node_spacing"]["vertical"]
        return node, new_y

    def _add_session_separator(
        self,
        canvas_data: Dict[str, Any],
        session: Dict[str, Any],
        session_number: int,
        x: int,
        y: int
    ) -> Tuple[Dict[str, Any], int]:
        """添加会话分隔符

        Args:
            canvas_data: Canvas数据
            session: 复习会话
            session_number: 会话编号
            x: X坐标
            y: Y坐标

        Returns:
            Tuple[Dict, int]: 节点数据和新的Y坐标
        """
        difficulty = session.get("difficulty_level", "medium")
        duration = session.get("estimated_duration", 0)
        objectives = session.get("learning_objectives", [])

        separator_text = f"""# 📚 复习会话 {session_number}

**难度级别**: {difficulty} | **预计时长**: {duration} 分钟

**学习目标**:
{chr(10).join(f'• {obj}' for obj in objectives)}

---"""

        node = {
            "id": f"separator-{session_number}-{uuid.uuid4().hex[:12]}",
            "type": "text",
            "text": separator_text,
            "x": x,
            "y": y,
            "width": self.LAYOUT_CONFIG["node_dimensions"]["session_separator"]["width"],
            "height": self.LAYOUT_CONFIG["node_dimensions"]["session_separator"]["height"],
            "color": self.COLORS["separator"]
        }

        canvas_data["nodes"].append(node)

        new_y = y + node["height"] + 30
        return node, new_y

    def _add_review_session(
        self,
        canvas_data: Dict[str, Any],
        session: Dict[str, Any],
        x: int,
        y: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        """添加复习会话内容

        Args:
            canvas_data: Canvas数据
            session: 复习会话
            x: X坐标
            y: Y坐标

        Returns:
            Tuple[List[Dict], int]: 节点列表和新的Y坐标
        """
        session_nodes = []
        current_y = y
        current_x = x

        concepts = session.get("concepts", [])

        for i, concept in enumerate(concepts):
            # 添加概念节点
            concept_node, current_x, current_y = self._add_concept_node(
                canvas_data, concept, current_x, current_y
            )
            session_nodes.append(concept_node)

            # 如果一行放不下，换行
            if (i + 1) % 2 == 0:
                current_x = x
                current_y += self.LAYOUT_CONFIG["node_spacing"]["vertical"]
            else:
                current_x += self.LAYOUT_CONFIG["node_spacing"]["horizontal"]

        # 添加提示节点（如果有空间）
        if concepts:
            hint_node = self._add_session_hint_node(
                canvas_data, session, x, current_y + 50
            )
            session_nodes.append(hint_node)
            current_y = hint_node["y"] + hint_node["height"] + self.LAYOUT_CONFIG["node_spacing"]["vertical"]

        return session_nodes, current_y

    def _add_concept_node(
        self,
        canvas_data: Dict[str, Any],
        concept: Dict[str, Any],
        x: int,
        y: int
    ) -> Tuple[Dict[str, Any], int, int]:
        """添加概念节点组（概念+问题+黄色理解区）

        Args:
            canvas_data: Canvas数据
            concept: 概念数据
            x: X坐标
            y: Y坐标

        Returns:
            Tuple[Dict, int, int]: 概念节点、新的X和Y坐标
        """
        concept_name = concept.get("concept_name", "")
        difficulty = concept.get("difficulty", "medium")
        estimated_time = concept.get("estimated_time_minutes", 10)
        focus_areas = concept.get("recommended_focus_areas", [])
        review_questions = concept.get("review_questions", [])

        # 1. 概念介绍节点
        concept_text = f"""## 📖 {concept_name}

**难度**: {difficulty} | **预计时间**: {estimated_time} 分钟

**重点关注**:
{chr(10).join(f'• {area}' for area in focus_areas[:3])}

**复习要点**:
- 🎯 掌握核心定义和特征
- 💡 理解实际应用场景
- 🔗 建立与其他概念的联系"""

        concept_node = {
            "id": f"concept-{uuid.uuid4().hex[:12]}",
            "type": "text",
            "text": concept_text,
            "x": x,
            "y": y,
            "width": self.LAYOUT_CONFIG["node_dimensions"]["concept"]["width"],
            "height": self.LAYOUT_CONFIG["node_dimensions"]["concept"]["height"],
            "color": self.COLORS["concept"]
        }

        canvas_data["nodes"].append(concept_node)

        # 2. 问题节点（在概念节点下方）
        question_y = y + concept_node["height"] + self.LAYOUT_CONFIG["node_spacing"]["question_to_yellow"]

        if review_questions:
            question_text = f"""## ❓ 复习检验

**问题**: {review_questions[0].get('question_text', '请解释这个概念的核心要点')}

**建议方法**: {review_questions[0].get('suggested_approach', '从定义开始，逐步展开')}
**预计时间**: {review_questions[0].get('estimated_time_minutes', 8)} 分钟

**评估标准**: {', '.join(review_questions[0].get('evaluation_criteria', ['准确性', '完整性']))}"""
        else:
            question_text = f"""## ❓ 复习检验

请用自己的话详细解释 **{concept_name}** 的核心概念，包括：

1. **定义**: 它是什么？
2. **特征**: 它有哪些主要特点？
3. **应用**: 在什么情况下会用到？
4. **例子**: 能举一个具体的例子吗？

**要求**: 不查阅资料，诚实评估自己的理解程度。"""

        question_node = {
            "id": f"question-{uuid.uuid4().hex[:12]}",
            "type": "text",
            "text": question_text,
            "x": x,
            "y": question_y,
            "width": self.LAYOUT_CONFIG["node_dimensions"]["question"]["width"],
            "height": self.LAYOUT_CONFIG["node_dimensions"]["question"]["height"],
            "color": self.COLORS["question"]
        }

        canvas_data["nodes"].append(question_node)

        # 3. 黄色理解区（在问题节点下方）
        yellow_y = question_y + question_node["height"] + self.LAYOUT_CONFIG["node_spacing"]["question_to_yellow"]

        yellow_text = f"""## 💭 我的理解

在这里写下你对 **{concept_name}** 的理解和解释...

**写作提示**:
- ✍️ 尽量详细，不要怕写错
- 🤔 用自己的话，不要照搬定义
- 💡 可以举例说明
- 🔗 如果知道相关概念，也可以提及

**完成后评分** (1-10分): ⏳"""

        yellow_node = {
            "id": f"yellow-{uuid.uuid4().hex[:12]}",
            "type": "text",
            "text": yellow_text,
            "x": x,
            "y": yellow_y,
            "width": self.LAYOUT_CONFIG["node_dimensions"]["yellow"]["width"],
            "height": self.LAYOUT_CONFIG["node_dimensions"]["yellow"]["height"],
            "color": self.COLORS["yellow"]
        }

        canvas_data["nodes"].append(yellow_node)

        # 添加边连接（概念 -> 问题 -> 黄色）
        self._add_edge(canvas_data, concept_node["id"], question_node["id"], "复习")
        self._add_edge(canvas_data, question_node["id"], yellow_node["id"], "回答")

        # 计算下一个概念的位置
        next_y = yellow_y + yellow_node["height"] + 50
        next_x = x + self.LAYOUT_CONFIG["node_spacing"]["horizontal"]

        return concept_node, next_x, next_y

    def _add_session_hint_node(
        self,
        canvas_data: Dict[str, Any],
        session: Dict[str, Any],
        x: int,
        y: int
    ) -> Dict[str, Any]:
        """添加会话提示节点

        Args:
            canvas_data: Canvas数据
            session: 复习会话
            x: X坐标
            y: Y坐标

        Returns:
            Dict: 提示节点数据
        """
        adaptive_elements = session.get("adaptive_elements", {})

        hint_text = """## 💡 复习建议

**时间管理**:
- ⏰ 每个概念控制在预计时间内
- 🔄 遇到困难可以先标记，继续后面的内容
- ☕ 复习过程中适当休息

**学习方法**:
- 📝 先思考再下笔，整理思路
- 🎯 重点关注自己的薄弱环节
- 💭 尝试联系实际生活经验

**遇到困难时**:
- 🤚 不要立即查阅资料
- 🗺️ 尝试画图帮助理解
- 💭 回想相关的已知知识
- ⭐ 可以先写下自己不确定的理解

**完成后**:
- ✅ 检查是否覆盖所有要点
- 📊 诚实评分，记录难点
- 🎯 为下次复习制定计划"""

        node = {
            "id": f"hint-{uuid.uuid4().hex[:12]}",
            "type": "text",
            "text": hint_text,
            "x": x,
            "y": y,
            "width": self.LAYOUT_CONFIG["node_dimensions"]["hint"]["width"],
            "height": self.LAYOUT_CONFIG["node_dimensions"]["hint"]["height"],
            "color": self.COLORS["hint"]
        }

        canvas_data["nodes"].append(node)
        return node

    def _add_suggestions_node(
        self,
        canvas_data: Dict[str, Any],
        review_plan: Dict[str, Any],
        x: int,
        y: int
    ) -> Tuple[Dict[str, Any], int]:
        """添加学习建议节点

        Args:
            canvas_data: Canvas数据
            review_plan: 复习计划
            x: X坐标
            y: Y坐标

        Returns:
            Tuple[Dict, int]: 节点数据和新的Y坐标
        """
        personalization = review_plan.get("personalization_features", {})
        learning_style = personalization.get("learning_style_adaptation", {})
        time_optimization = personalization.get("time_optimization", {})

        preferred_approach = learning_style.get("preferred_approach", "balanced_approach")
        optimal_duration = time_optimization.get("optimal_study_duration", 45)
        peak_time = time_optimization.get("peak_performance_time", "morning")

        approach_names = {
            "self_explanation_focused": "自我解释导向",
            "inquiry_based": "探究式学习",
            "guided_learning": "指导性学习",
            "balanced_approach": "平衡式学习"
        }

        suggestions_text = f"""## 🎯 个性化学习建议

**你的学习风格**: {approach_names.get(preferred_approach, preferred_approach)}

**最佳学习时间**: {peak_time}
**建议学习时长**: {optimal_duration} 分钟

### 📈 学习优化建议

**基于你的学习模式**:
- 🎯 优先理解核心概念，再深入细节
- 🔗 主动建立知识联系，形成网络
- 💡 结合实例加深理解

**复习策略**:
- 📅 制定固定复习计划
- 🔄 定期回顾已学内容
- 📝 记录学习心得和难点

**下次复习重点**:
- ⭐ 关注本次标记的薄弱概念
- 🎯 加强应用练习
- 📊 提升理解深度

### 📞 需要帮助时

如果遇到特别困难的概念：
1. 🤚 主动寻求解释和帮助
2. 📚 查找补充学习材料
3. 👥 与同学讨论交流
4. 🎯 重新梳理基础知识"""

        node = {
            "id": f"suggestions-{uuid.uuid4().hex[:12]}",
            "type": "text",
            "text": suggestions_text,
            "x": x,
            "y": y,
            "width": self.LAYOUT_CONFIG["node_dimensions"]["intro"]["width"],
            "height": 450,
            "color": self.COLORS["intro"]
        }

        canvas_data["nodes"].append(node)

        new_y = y + node["height"] + self.LAYOUT_CONFIG["node_spacing"]["vertical"]
        return node, new_y

    def _add_summary_node(
        self,
        canvas_data: Dict[str, Any],
        review_plan: Dict[str, Any],
        x: int,
        y: int
    ) -> Tuple[Dict[str, Any], int]:
        """添加总结节点

        Args:
            canvas_data: Canvas数据
            review_plan: 复习计划
            x: X坐标
            y: Y坐标

        Returns:
            Tuple[Dict, int]: 节点数据和新的Y坐标
        """
        plan_id = review_plan.get("plan_id", "")
        next_review_date = review_plan.get("next_review_date", "")
        success_metrics = review_plan.get("success_metrics", {})

        # 格式化下次复习日期
        try:
            dt = datetime.fromisoformat(next_review_date.replace('Z', '+00:00'))
            formatted_date = dt.strftime("%Y年%m月%d日")
        except:
            formatted_date = next_review_date

        target_completion_rate = success_metrics.get("target_completion_rate", 0.9)
        target_score = success_metrics.get("target_average_score", 7.5)

        summary_text = f"""## 📋 复习总结

**计划ID**: {plan_id}
**完成日期**: ⏳ 待填写
**下次复习**: {formatted_date}

### 🎯 成功目标

- ✅ 完成率目标: {target_completion_rate*100:.0f}%
- 📊 平均分目标: {target_score:.1f}分
- ⏰ 时间效率目标: 80%

### 📝 完成后的反思

1. **哪些概念掌握得比较好？**


2. **哪些概念还需要进一步学习？**


3. **本次复习有什么收获？**


4. **下次复习可以如何改进？**


### 🏆 成就记录

- 🌟 完成复习时间: ⏳
- 🎯 达成目标数: ⏳
- 💡 新获得的理解: ⏳

---
*复习完成后，记得将此Canvas保存到你的学习档案中！*"""

        node = {
            "id": f"summary-{uuid.uuid4().hex[:12]}",
            "type": "text",
            "text": summary_text,
            "x": x,
            "y": y,
            "width": self.LAYOUT_CONFIG["node_dimensions"]["intro"]["width"],
            "height": 400,
            "color": self.COLORS["progress"]
        }

        canvas_data["nodes"].append(node)

        new_y = y + node["height"] + self.LAYOUT_CONFIG["node_spacing"]["vertical"]
        return node, new_y

    def _add_edge(
        self,
        canvas_data: Dict[str, Any],
        from_node: str,
        to_node: str,
        label: str = ""
    ) -> None:
        """添加边连接

        Args:
            canvas_data: Canvas数据
            from_node: 起始节点ID
            to_node: 目标节点ID
            label: 边标签
        """
        edge = {
            "id": f"edge-{uuid.uuid4().hex[:12]}",
            "fromNode": from_node,
            "toNode": to_node,
            "fromSide": "bottom",
            "toSide": "top",
            "label": label
        }

        canvas_data["edges"].append(edge)

    def apply_canvas_template(
        self,
        canvas_data: Dict[str, Any],
        template_name: str = "standard_review"
    ) -> Dict[str, Any]:
        """应用Canvas模板

        Args:
            canvas_data: 原始Canvas数据
            template_name: 模板名称

        Returns:
            Dict: 应用模板后的Canvas数据
        """
        # 模板配置
        templates = {
            "standard_review": {
                "color_scheme": "default",
                "layout_style": "vertical",
                "node_style": "rounded",
            },
            "minimal_review": {
                "color_scheme": "minimal",
                "layout_style": "compact",
                "node_style": "simple",
            },
            "visual_review": {
                "color_scheme": "colorful",
                "layout_style": "spacious",
                "node_style": "decorated",
            }
        }

        template = templates.get(template_name, templates["standard_review"])

        # 应用模板样式
        # 这里简化实现，实际应用中可以根据模板调整样式
        return canvas_data

    def customize_canvas_content(
        self,
        canvas_data: Dict[str, Any],
        customizations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """定制Canvas内容

        Args:
            canvas_data: 原始Canvas数据
            customizations: 定制配置

        Returns:
            Dict: 定制后的Canvas数据
        """
        # 实现内容定制逻辑
        # 这里简化实现，实际应用中可以根据定制配置调整内容
        return canvas_data


# 示例使用
if __name__ == "__main__":
    # 创建Canvas构建器
    builder = ReviewCanvasBuilder()

    # 示例复习计划
    example_review_plan = {
        "plan_id": "plan-example123",
        "user_id": "default",
        "target_canvas": "离散数学.canvas",
        "plan_type": "weakness_focused",
        "review_sessions": [
            {
                "session_id": "session-001",
                "difficulty_level": "medium",
                "estimated_duration": 45,
                "learning_objectives": [
                    "复习和巩固指定概念的核心知识",
                    "提高概念理解的准确性和完整性"
                ],
                "concepts": [
                    {
                        "concept_name": "逻辑等价性",
                        "difficulty": "medium",
                        "estimated_time_minutes": 12,
                        "recommended_focus_areas": [
                            "概念定义复习",
                            "实例练习加强",
                            "与其他概念的关系理解"
                        ],
                        "review_questions": [
                            {
                                "question_text": "请用自己的话解释什么是逻辑等价性？",
                                "suggested_approach": "从真值表角度理解",
                                "estimated_time_minutes": 8,
                                "evaluation_criteria": ["准确性", "完整性", "清晰度"]
                            }
                        ]
                    }
                ]
            }
        ],
        "personalization_features": {
            "learning_style_adaptation": {
                "preferred_approach": "self_explanation_focused",
                "complexity_tolerance": "gradual_increase",
                "feedback_preference": "immediate_explanations",
            },
            "time_optimization": {
                "optimal_study_duration": 45,
                "break_intervals": 15,
                "peak_performance_time": "morning",
            }
        },
        "next_review_date": datetime.now().isoformat(),
    }

    try:
        # 创建复习Canvas
        canvas_path = builder.create_review_canvas(example_review_plan)
        print(f"复习Canvas已创建: {canvas_path}")

        # 验证Canvas文件
        if os.path.exists(canvas_path):
            with open(canvas_path, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)
            print(f"Canvas包含 {len(canvas_data['nodes'])} 个节点和 {len(canvas_data['edges'])} 条边")
        else:
            print("Canvas文件创建失败")

    except Exception as e:
        print(f"Canvas创建失败: {e}")