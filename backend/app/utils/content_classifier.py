# Canvas Learning System - Content Classification Utility
# Shared function for classifying text as knowledge vs problem content.
#
# Extracted from ExamService._classify_content and QuestionGenerator._classify_content
# to eliminate duplication (6-3 M1 fix).
"""
Shared content classification: counts knowledge vs problem signals in text.

Used by:
  - ExamService.analyze_canvas_content (Story 6.2)
  - QuestionGenerator.assemble_acp (Story 6.3)
"""

import re
from typing import Tuple

# Knowledge-oriented signal words (definitions, concepts, properties)
KNOWLEDGE_KEYWORDS = [
    "定义",
    "概念",
    "原理",
    "特征",
    "性质",
    "分类",
    "是指",
    "定义为",
    "指的是",
    "含义",
    "本质",
    "区别",
    "联系",
    "比较",
    "组成",
    "结构",
]

# Problem-oriented signal words (calculations, proofs, exercises)
PROBLEM_KEYWORDS = [
    "求",
    "计算",
    "证明",
    "解",
    "例题",
    "练习",
    "应用",
    "设计",
    "分析",
    "推导",
    "解答",
    "已知",
    "问",
    "题",
    "求解",
]


def classify_content(text: str) -> Tuple[int, int]:
    """Count knowledge vs problem signals in text.

    Args:
        text: Text content to classify.

    Returns:
        Tuple of (knowledge_signal_count, problem_signal_count).
    """
    k_count = sum(1 for kw in KNOWLEDGE_KEYWORDS if kw in text)
    p_count = sum(1 for kw in PROBLEM_KEYWORDS if kw in text)

    # LaTeX formulas are a strong problem signal
    latex_count = len(re.findall(r"\$[^$]+\$", text))
    if latex_count > 2:
        p_count += latex_count

    return k_count, p_count
