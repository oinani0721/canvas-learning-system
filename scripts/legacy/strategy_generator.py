"""
策略节点生成器 - UltraThink智能策略系统

根据理解程度生成不同类型的检验节点：
- 补充解释策略：蓝色解释节点 + 黄色总结节点
- 拆分问题策略：紫色子问题组 + 多个黄色回答节点

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-16
"""

import io
import sys
import uuid
from typing import Dict, List

# Note: encoding fix moved to main scripts to avoid import issues

from canvas_utils import (
    COLOR_CODE_PURPLE,
    COLOR_CODE_BLUE,
    COLOR_CODE_YELLOW,
)


class StrategyNodeGenerator:
    """策略节点生成器

    根据理解程度生成不同类型的检验节点组
    """

    def __init__(self):
        pass

    def generate_explanation_strategy_nodes(
        self,
        node_id: str,
        node_content: str,
        yellow_understanding: str,
        understanding_percentage: int,
        base_x: int,
        base_y: int
    ) -> List[Dict]:
        """生成补充解释策略节点组

        适用于理解程度0-40%的节点

        生成结构：
        [问题节点] --> [蓝色解释节点] --> [黄色总结节点]

        Args:
            node_id: 原节点ID
            node_content: 原节点内容
            yellow_understanding: 黄色理解内容
            understanding_percentage: 理解程度百分比
            base_x, base_y: 基础坐标

        Returns:
            节点列表（解释节点 + 总结节点）
        """
        nodes = []

        # 选择解释类型
        if understanding_percentage < 20:
            explanation_type = "澄清路径"
            prompt = self._generate_clarification_prompt(node_content, yellow_understanding)
        else:
            explanation_type = "故事化解释"
            prompt = self._generate_story_prompt(node_content, yellow_understanding)

        # 1. 蓝色解释节点
        explanation_id = f"explanation-{uuid.uuid4().hex[:8]}"
        explanation_node = {
            "id": explanation_id,
            "type": "text",
            "text": f"""# 📘 {explanation_type}

**原问题**: {node_content[:100]}...

**你的理解**: {yellow_understanding[:100]}...

---

{prompt}

---

💡 **下一步**: 请在右侧黄色节点用自己的话总结""",
            "x": base_x + 800,
            "y": base_y,
            "width": 600,
            "height": 400,
            "color": COLOR_CODE_BLUE
        }
        nodes.append(explanation_node)

        # 2. 黄色总结节点
        summary_id = f"summary-{uuid.uuid4().hex[:8]}"
        summary_node = {
            "id": summary_id,
            "type": "text",
            "text": f"""# 💡 我的总结

读完左侧解释后，请用自己的话总结：

1. **核心概念是什么？**（1句话）


2. **关键要点有哪些？**（3-5个要点）


3. **举一个你自己想到的例子**：


---

⚠️ 不要复制粘贴，用自己的语言！
这是检验你是否真正理解的关键。""",
            "x": base_x + 1600,
            "y": base_y + 50,
            "width": 400,
            "height": 300,
            "color": COLOR_CODE_YELLOW
        }
        nodes.append(summary_node)

        # 3. 连接边
        edges = [
            {
                "id": f"edge-{node_id}-{explanation_id}",
                "fromNode": node_id,
                "fromSide": "right",
                "toNode": explanation_id,
                "toSide": "left",
                "label": "补充解释"
            },
            {
                "id": f"edge-{explanation_id}-{summary_id}",
                "fromNode": explanation_id,
                "fromSide": "right",
                "toNode": summary_id,
                "toSide": "left",
                "label": "总结要点"
            }
        ]

        return {"nodes": nodes, "edges": edges}

    def generate_split_questions_strategy_nodes(
        self,
        node_id: str,
        node_content: str,
        yellow_understanding: str,
        base_x: int,
        base_y: int,
        num_sub_questions: int = 3
    ) -> List[Dict]:
        """生成拆分问题策略节点组

        适用于理解程度40-70%的节点

        生成结构：
        [问题节点] --> [紫色子问题组] --> [黄色回答节点×3-5]

        Args:
            node_id: 原节点ID
            node_content: 原节点内容
            yellow_understanding: 黄色理解内容
            base_x, base_y: 基础坐标
            num_sub_questions: 子问题数量（默认3）

        Returns:
            节点列表（子问题组 + 多个回答节点）
        """
        nodes = []
        edges = []

        # 生成子问题
        sub_questions = self._generate_sub_questions(node_content, yellow_understanding, num_sub_questions)

        # 1. 紫色子问题组节点
        sub_q_id = f"subquestions-{uuid.uuid4().hex[:8]}"
        sub_q_text = f"""# 🔬 问题拆解

**原问题**: {node_content[:100]}...

**你的理解**: {yellow_understanding[:100]}...

---

你说"似懂非懂"，让我们拆解成具体问题：

"""

        for i, sq in enumerate(sub_questions, 1):
            sub_q_text += f"""## 子问题 {i}

{sq['question']}

💡 提示：{sq['hint']}

---

"""

        sub_q_node = {
            "id": sub_q_id,
            "type": "text",
            "text": sub_q_text,
            "x": base_x + 800,
            "y": base_y,
            "width": 500,
            "height": 300 + num_sub_questions * 100,
            "color": COLOR_CODE_PURPLE
        }
        nodes.append(sub_q_node)

        # 边：原问题 -> 子问题组
        edges.append({
            "id": f"edge-{node_id}-{sub_q_id}",
            "fromNode": node_id,
            "fromSide": "right",
            "toNode": sub_q_id,
            "toSide": "left",
            "label": "拆分问题"
        })

        # 2. 为每个子问题生成黄色回答节点
        current_y = base_y
        for i, sq in enumerate(sub_questions, 1):
            answer_id = f"answer-{i}-{uuid.uuid4().hex[:8]}"
            answer_node = {
                "id": answer_id,
                "type": "text",
                "text": f"""# 💡 子问题 {i} 的回答

**问题**: {sq['question']}

在这里写下你的回答...

（尝试用自己的理解回答，不确定也没关系）

---

提示：{sq['hint']}""",
                "x": base_x + 1400,
                "y": current_y,
                "width": 400,
                "height": 200,
                "color": COLOR_CODE_YELLOW
            }
            nodes.append(answer_node)

            # 边：子问题组 -> 回答节点
            edges.append({
                "id": f"edge-{sub_q_id}-{answer_id}",
                "fromNode": sub_q_id,
                "fromSide": "right",
                "toNode": answer_id,
                "toSide": "left",
                "label": f"回答{i}"
            })

            current_y += 250  # 垂直间隔

        return {"nodes": nodes, "edges": edges}

    def _generate_clarification_prompt(self, content: str, understanding: str) -> str:
        """生成澄清路径提示"""
        return f"""## 🎯 系统化澄清

这个概念对你来说比较抽象。让我们用系统化的方法理解它：

### 第1步：最简单的定义

用最简单的一句话来说，这个概念是：
（建议：调用clarification-path Agent生成完整澄清文档）

### 第2步：生活中的例子

想象一个生活中的场景...
（建议：如果还是抽象，切换到memory-anchor Agent生成故事化解释）

### 第3步：它要解决什么问题

为什么需要这个概念？不用它会有什么问题？

### 第4步：关键要点

记住这3-5个关键要点就够了..."""

    def _generate_story_prompt(self, content: str, understanding: str) -> str:
        """生成故事化解释提示"""
        return f"""## 📖 故事化理解

让我用一个生动的故事来解释这个概念：

（建议：调用memory-anchor Agent生成生动的类比和故事）

### 类比

这个概念就像...

### 故事

想象你在...

### 记忆口诀

记住这个简单的口诀：..."""

    def _generate_sub_questions(self, content: str, understanding: str, num: int) -> List[Dict]:
        """生成子问题列表

        TODO: 未来可以调用deep-decomposition Agent生成更智能的子问题
        """
        # 简化版：生成通用子问题模板
        templates = [
            {
                "question": "这个概念的准确定义是什么？",
                "hint": "用最简洁的语言，不要有歧义"
            },
            {
                "question": "它与相关概念有什么区别？容易混淆在哪里？",
                "hint": "对比思考，找出关键差异"
            },
            {
                "question": "实际应用场景是什么？什么时候应该使用它？",
                "hint": "举一个具体的例子"
            },
            {
                "question": "如何判断应该使用这个概念？有什么信号词或特征？",
                "hint": "总结识别模式"
            },
            {
                "question": "常见的错误理解是什么？你的理解有没有这些误区？",
                "hint": "检查自己的理解"
            }
        ]

        return templates[:num]


if __name__ == "__main__":
    # 测试
    generator = StrategyNodeGenerator()

    # 测试补充解释策略
    result1 = generator.generate_explanation_strategy_nodes(
        node_id="test-red-1",
        node_content="什么是鸽笼原理？",
        yellow_understanding="完全不懂，感觉很抽象",
        understanding_percentage=10,
        base_x=0,
        base_y=0
    )
    print(f"补充解释策略生成了 {len(result1['nodes'])} 个节点")

    # 测试拆分问题策略
    result2 = generator.generate_split_questions_strategy_nodes(
        node_id="test-purple-1",
        node_content="如何应用鸽笼原理？",
        yellow_understanding="好像懂了，但不知道什么时候用",
        base_x=0,
        base_y=0,
        num_sub_questions=3
    )
    print(f"拆分问题策略生成了 {len(result2['nodes'])} 个节点")
