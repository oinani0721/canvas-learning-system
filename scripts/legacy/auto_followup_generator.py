"""
UltraThink自动评分决策器 - Follow-up节点生成系统

本脚本在scoring-agent评分后自动执行:
- 分析弱项维度 (Accuracy/Imagery/Completeness/Originality)
- 决策干预类型 (澄清路径/记忆锚点/深度拆解/口语化解释)
- 生成follow-up节点到当前canvas
- 更新进度追踪JSON
- 维护TodoList

Author: Canvas Learning System Team
Version: 1.0 (UltraThink Upgrade)
Created: 2025-10-16
"""

import io
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from canvas_utils import (
    CanvasJSONOperator,
    COLOR_CODE_PURPLE,
    COLOR_CODE_BLUE,
)


# ========== 常量定义 ==========

# 决策阈值
WEAK_DIMENSION_THRESHOLD = 12  # 分数 < 12/25 视为弱项
PASS_THRESHOLD = 80  # 总分 >= 80 为通过

# 干预类型
INTERVENTION_CLARIFICATION = "clarification-path"
INTERVENTION_MEMORY = "memory-anchor"
INTERVENTION_DEEP = "deep-decomposition"
INTERVENTION_ORAL = "oral-explanation"

# 布局常量
FOLLOWUP_X_OFFSET = 1500  # follow-up节点在原节点右侧1500px
FOLLOWUP_Y_OFFSET = 0     # 与原节点同一高度
FOLLOWUP_WIDTH = 400
FOLLOWUP_HEIGHT = 300

# 进度追踪文件
PROGRESS_TRACKER_FILENAME = "检验进度追踪.json"


# ========== 决策引擎 ==========

class AutoFollowupDecisionEngine:
    """自动Follow-up决策引擎

    根据scoring-agent的评分结果自动决策干预策略并生成follow-up节点
    """

    def __init__(self, canvas_path: str):
        """初始化决策引擎

        Args:
            canvas_path: 当前Canvas文件路径（检验白板或原白板）
        """
        self.canvas_path = canvas_path
        self.canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

        # 进度追踪路径（假设在同目录）
        canvas_dir = str(Path(canvas_path).parent)
        self.progress_tracker_path = os.path.join(
            canvas_dir,
            PROGRESS_TRACKER_FILENAME
        )

    def process_scoring_result(
        self,
        node_id: str,
        score: int,
        breakdown: Dict[str, int],
        understanding_text: str
    ) -> Optional[Dict[str, Any]]:
        """处理单个节点的评分结果

        Args:
            node_id: 被评分的节点ID
            score: 总分 (0-100)
            breakdown: 4维评分详情 {"accuracy": 18, "imagery": 15, ...}
            understanding_text: 用户的理解文本

        Returns:
            Dict: 生成的follow-up节点信息，如果通过(≥80)则返回None
        """
        print(f"\n{'='*60}")
        print(f"📊 处理评分结果: {node_id[:8]}... (总分: {score}/100)")
        print(f"{'='*60}\n")

        # 检查是否通过
        if score >= PASS_THRESHOLD:
            print(f"✅ 节点已通过 (≥80分)，无需干预")
            self._mark_node_completed(node_id, score)
            return None

        # 分析弱项维度
        weak_dims = self._analyze_weak_dimensions(breakdown)
        print(f"📉 弱项维度: {', '.join(weak_dims) if weak_dims else '无明显弱项'}")

        # 决策干预类型
        intervention_type = self._decide_intervention(weak_dims, breakdown)
        print(f"🎯 干预策略: {intervention_type}")

        # 生成follow-up节点
        followup_node = self._generate_followup_node(
            node_id,
            intervention_type,
            weak_dims,
            understanding_text
        )

        # 添加到canvas
        self._add_followup_to_canvas(node_id, followup_node, intervention_type)

        # 记录到进度追踪
        self._record_intervention(node_id, score, intervention_type, followup_node)

        print(f"✅ Follow-up节点已生成并添加到Canvas")

        return followup_node

    def _analyze_weak_dimensions(self, breakdown: Dict[str, int]) -> List[str]:
        """分析弱项维度

        Args:
            breakdown: 4维评分 {"accuracy": 18, "imagery": 15, ...}

        Returns:
            List[str]: 弱项维度列表 (分数 < WEAK_DIMENSION_THRESHOLD)
        """
        weak = []
        for dim, score in breakdown.items():
            if score < WEAK_DIMENSION_THRESHOLD:
                weak.append(dim)
        return weak

    def _decide_intervention(
        self,
        weak_dims: List[str],
        breakdown: Dict[str, int]
    ) -> str:
        """决策干预类型

        优先级:
        1. accuracy低 → clarification-path (澄清路径)
        2. imagery低 → memory-anchor (记忆锚点)
        3. completeness低 → deep-decomposition (深度拆解)
        4. originality低 → oral-explanation (口语化解释)
        5. 无明显弱项 → deep-decomposition (默认深度拆解)

        Args:
            weak_dims: 弱项维度列表
            breakdown: 4维评分详情

        Returns:
            str: 干预类型
        """
        if "accuracy" in weak_dims:
            return INTERVENTION_CLARIFICATION
        elif "imagery" in weak_dims:
            return INTERVENTION_MEMORY
        elif "completeness" in weak_dims:
            return INTERVENTION_DEEP
        elif "originality" in weak_dims:
            return INTERVENTION_ORAL
        else:
            # 无明显弱项，使用深度拆解
            return INTERVENTION_DEEP

    def _generate_followup_node(
        self,
        original_node_id: str,
        intervention_type: str,
        weak_dims: List[str],
        understanding_text: str
    ) -> Dict[str, Any]:
        """生成follow-up节点内容

        Args:
            original_node_id: 原节点ID
            intervention_type: 干预类型
            weak_dims: 弱项维度列表
            understanding_text: 用户理解文本

        Returns:
            Dict: follow-up节点数据
        """
        # 生成节点ID
        followup_id = f"followup-{uuid.uuid4().hex[:12]}"

        # 根据干预类型生成不同的节点内容
        if intervention_type == INTERVENTION_CLARIFICATION:
            node_type = "blue_doc"  # 蓝色文档节点
            text = self._generate_clarification_prompt(weak_dims, understanding_text)
            color = COLOR_CODE_BLUE
        elif intervention_type == INTERVENTION_MEMORY:
            node_type = "blue_doc"
            text = self._generate_memory_anchor_prompt(understanding_text)
            color = COLOR_CODE_BLUE
        elif intervention_type == INTERVENTION_DEEP:
            node_type = "purple_question"  # 紫色问题节点
            text = self._generate_deep_question(understanding_text)
            color = COLOR_CODE_PURPLE
        elif intervention_type == INTERVENTION_ORAL:
            node_type = "blue_doc"
            text = self._generate_oral_explanation_prompt()
            color = COLOR_CODE_BLUE
        else:
            node_type = "purple_question"
            text = "请重新解释这个概念，并举例说明。"
            color = COLOR_CODE_PURPLE

        return {
            "id": followup_id,
            "type": "text",
            "text": text,
            "color": color,
            "node_type": node_type,
            "intervention": intervention_type,
            "source_node": original_node_id,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    def _generate_clarification_prompt(
        self,
        weak_dims: List[str],
        understanding: str
    ) -> str:
        """生成澄清路径提示"""
        return f"""# 🔍 澄清路径 - Accuracy增强

**弱项维度**: {', '.join(weak_dims)}

**你的理解**:
{understanding[:300]}...

**澄清任务**:

1. 请重新定义这个概念，确保准确性
2. 指出你当前理解中可能存在的误解
3. 提供准确的定义和关键要点
4. 用严谨的语言重新表述

**建议**: 调用clarification-path Agent生成完整的澄清文档"""

    def _generate_memory_anchor_prompt(self, understanding: str) -> str:
        """生成记忆锚点提示"""
        return f"""# ⚓ 记忆锚点 - Imagery增强

**你的理解**:
{understanding[:300]}...

**记忆任务**:

1. 为这个概念创建一个生动的类比
2. 编造一个容易记忆的故事
3. 设计一个具象的图景或场景
4. 创建记忆口诀或助记词

**建议**: 调用memory-anchor Agent生成生动的记忆材料"""

    def _generate_deep_question(self, understanding: str) -> str:
        """生成深层问题"""
        return f"""# 🔬 深度检验问题

**基于你的理解**:
{understanding[:200]}...

**深度问题**:

1. 这个概念与哪些相关概念容易混淆？有何区别？
2. 在什么场景下应用这个概念？举一个具体例子。
3. 如果这个概念不存在，会有什么问题？
4. 你能从不同角度重新解释这个概念吗？

**请在下方黄色节点回答这些问题**"""

    def _generate_oral_explanation_prompt(self) -> str:
        """生成口语化解释提示"""
        return f"""# 🗣️ 口语化解释 - Originality增强

**任务**:

请用你自己的语言重新解释这个概念，就像在教一个朋友。

**要求**:
1. 不要照抄书本定义
2. 用口语化、通俗的语言
3. 加入你的个人理解和见解
4. 举一个你自己想到的例子

**建议**: 调用oral-explanation Agent生成教授式的解释"""

    def _add_followup_to_canvas(
        self,
        original_node_id: str,
        followup_node: Dict[str, Any],
        intervention_type: str
    ):
        """将follow-up节点添加到Canvas

        Args:
            original_node_id: 原节点ID
            followup_node: follow-up节点数据
            intervention_type: 干预类型
        """
        # 查找原节点位置
        original = CanvasJSONOperator.find_node_by_id(
            self.canvas_data,
            original_node_id
        )

        if original is None:
            print(f"⚠️ 警告: 找不到原节点 {original_node_id}，跳过添加")
            return

        # 计算follow-up节点位置（原节点右侧）
        followup_x = original.get("x", 0) + FOLLOWUP_X_OFFSET
        followup_y = original.get("y", 0) + FOLLOWUP_Y_OFFSET

        # 创建节点
        node_id = CanvasJSONOperator.create_node(
            self.canvas_data,
            node_type="text",
            x=followup_x,
            y=followup_y,
            width=FOLLOWUP_WIDTH,
            height=FOLLOWUP_HEIGHT,
            color=followup_node["color"],
            text=followup_node["text"]
        )

        # 创建连接边
        edge_label = self._get_edge_label(intervention_type)
        CanvasJSONOperator.create_edge(
            self.canvas_data,
            from_node=original_node_id,
            to_node=node_id,
            from_side="right",
            to_side="left",
            label=edge_label
        )

        # 保存Canvas
        CanvasJSONOperator.write_canvas(self.canvas_path, self.canvas_data)

        print(f"   ✓ Follow-up节点已添加到Canvas: {node_id[:12]}...")

    def _get_edge_label(self, intervention_type: str) -> str:
        """获取边标签"""
        labels = {
            INTERVENTION_CLARIFICATION: "澄清路径",
            INTERVENTION_MEMORY: "记忆锚点",
            INTERVENTION_DEEP: "深度检验",
            INTERVENTION_ORAL: "口语化解释"
        }
        return labels.get(intervention_type, "Follow-up")

    def _record_intervention(
        self,
        node_id: str,
        score: int,
        intervention_type: str,
        followup_node: Dict[str, Any]
    ):
        """记录干预到进度追踪JSON

        Args:
            node_id: 原节点ID
            score: 评分
            intervention_type: 干预类型
            followup_node: follow-up节点数据
        """
        # 加载进度追踪
        if not os.path.exists(self.progress_tracker_path):
            print(f"⚠️ 警告: 进度追踪文件不存在: {self.progress_tracker_path}")
            return

        with open(self.progress_tracker_path, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        # 查找对应的未完成节点
        for node in progress.get("unfinished_nodes", []):
            if node["node_id"] == node_id:
                # 更新attempts
                node["attempts"] = node.get("attempts", 0) + 1
                node["last_score"] = score

                # 添加干预记录
                intervention_record = {
                    "type": intervention_type,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "score_at_intervention": score,
                    "followup_node_id": followup_node["id"]
                }
                node["interventions"].append(intervention_record)
                break

        # 更新最新session的interventions
        if progress.get("review_sessions"):
            latest_session = progress["review_sessions"][-1]
            latest_session["interventions"].append({
                "node_id": node_id,
                "type": intervention_type,
                "score": score,
                "followup_node_id": followup_node["id"],
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        # 保存
        with open(self.progress_tracker_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 干预已记录到进度追踪")

    def _mark_node_completed(self, node_id: str, score: int):
        """标记节点为已完成

        Args:
            node_id: 节点ID
            score: 最终得分
        """
        if not os.path.exists(self.progress_tracker_path):
            return

        with open(self.progress_tracker_path, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        # 从unfinished_nodes中移除
        progress["unfinished_nodes"] = [
            node for node in progress.get("unfinished_nodes", [])
            if node["node_id"] != node_id
        ]

        # 更新metadata
        metadata = progress.get("metadata", {})
        metadata["total_nodes_completed"] = metadata.get("total_nodes_completed", 0) + 1

        total_ever = metadata.get("total_nodes_ever_reviewed", 1)
        completed = metadata["total_nodes_completed"]
        metadata["completion_rate"] = (completed / total_ever) * 100 if total_ever > 0 else 0

        # 更新最新session
        if progress.get("review_sessions"):
            latest_session = progress["review_sessions"][-1]
            latest_session["nodes_completed"] = latest_session.get("nodes_completed", 0) + 1

        # 保存
        with open(self.progress_tracker_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 节点已标记为完成，从待办列表移除")


# ========== 批量处理接口 ==========

def process_batch_scoring_results(
    canvas_path: str,
    scoring_results: List[Dict[str, Any]]
):
    """批量处理评分结果

    用于scoring-agent批量评分后的自动处理

    Args:
        canvas_path: Canvas文件路径
        scoring_results: 评分结果列表
            [
                {
                    "node_id": "review-q1",
                    "score": 65,
                    "breakdown": {
                        "accuracy": 18,
                        "imagery": 12,
                        "completeness": 20,
                        "originality": 15
                    },
                    "understanding": "用户的理解文本..."
                },
                ...
            ]
    """
    engine = AutoFollowupDecisionEngine(canvas_path)

    print(f"\n{'='*60}")
    print(f"🚀 开始批量处理评分结果")
    print(f"📊 总计: {len(scoring_results)} 个节点")
    print(f"{'='*60}\n")

    results = {
        "passed": 0,
        "interventions": 0,
        "intervention_types": {}
    }

    for result in scoring_results:
        followup = engine.process_scoring_result(
            node_id=result["node_id"],
            score=result["score"],
            breakdown=result["breakdown"],
            understanding_text=result.get("understanding", "")
        )

        if followup is None:
            results["passed"] += 1
        else:
            results["interventions"] += 1
            int_type = followup["intervention"]
            results["intervention_types"][int_type] = \
                results["intervention_types"].get(int_type, 0) + 1

    print(f"\n{'='*60}")
    print(f"✅ 批量处理完成!")
    print(f"{'='*60}")
    print(f"✅ 通过节点: {results['passed']}")
    print(f"🎯 需要干预: {results['interventions']}")
    if results["intervention_types"]:
        print(f"\n干预类型分布:")
        for int_type, count in results["intervention_types"].items():
            print(f"  - {int_type}: {count}")
    print(f"{'='*60}\n")


# ========== 命令行接口 ==========

def main():
    """命令行主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="UltraThink自动评分决策器 - Follow-up节点生成系统"
    )
    parser.add_argument(
        "canvas_path",
        help="Canvas白板文件路径"
    )
    parser.add_argument(
        "--scoring-json",
        required=True,
        help="评分结果JSON文件路径"
    )

    args = parser.parse_args()

    # 验证文件存在
    if not os.path.exists(args.canvas_path):
        print(f"❌ 错误: Canvas文件不存在: {args.canvas_path}")
        sys.exit(1)

    if not os.path.exists(args.scoring_json):
        print(f"❌ 错误: 评分结果文件不存在: {args.scoring_json}")
        sys.exit(1)

    # 读取评分结果
    with open(args.scoring_json, 'r', encoding='utf-8') as f:
        scoring_results = json.load(f)

    # 批量处理
    process_batch_scoring_results(args.canvas_path, scoring_results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
