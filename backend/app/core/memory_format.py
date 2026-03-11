"""
Unified Memory Format for Canvas Learning System

Ensures consistent entity naming, episode_body formatting, and classification
across all write paths:
  - Canvas backend (graphiti_bridge_service.py)
  - React Agent (react_agent.py record_learning_memory tool)
  - Claude Code MCP (mcp__graphiti-cs188__add_memory)

Color reference (canvas_utils.py authoritative, plugin CSS remapped):
  "1"=Gray, "2"=Green, "3"=Purple, "4"=Red, "5"=Blue, "6"=Yellow
"""

from collections import defaultdict
from typing import Dict, Optional, Set


# ═══════════════════════════════════════════════════════════════════════════════
# Entity Type Registry
# ═══════════════════════════════════════════════════════════════════════════════

ENTITY_TYPES: Dict[str, dict] = {
    "Misconception": {
        "name_prefix": "Misconception",
        "source_description": "misconception-record",
        "keywords": {"知识", "概念", "理论", "定义", "不理解", "不懂"},
        "body_template": (
            "[Topic: {topic}] 误解内容: {error} | "
            "正确理解: {correct} | 来源: {source}"
        ),
    },
    "ProblemTrap": {
        "name_prefix": "ProblemTrap",
        "source_description": "problem-trap-record",
        "keywords": {"题", "逻辑", "误区", "做题", "错", "陷阱"},
        "body_template": (
            "[Topic: {topic}] [Problem: {problem}] "
            "错误做法: {wrong} | 正确做法: {correct} | "
            "关键区别: {insight}"
        ),
    },
    "LogicalFallacy": {
        "name_prefix": "LogicalFallacy",
        "source_description": "logical-fallacy-record",
        "keywords": {"推理", "谬误", "因果"},
        "body_template": (
            "[Topic: {topic}] 错误推理: {flawed} | "
            "为什么错: {why} | 正确推理: {correct}"
        ),
    },
    "GuidedThinking": {
        "name_prefix": "GuidedThinking",
        "source_description": "guided-thinking-record",
        "keywords": set(),  # Triggered by agent, not keywords
        "body_template": (
            "问题: {question} | 学生回答: {answer} | "
            "正确答案: {correct_answer} | 理解程度: {grade} | "
            "后续建议: {next_steps}"
        ),
    },
    "Concept": {
        "name_prefix": "Concept",
        "source_description": "concept-record",
        "keywords": set(),
        "body_template": (
            "[Topic: {topic}] 概念: {concept} | "
            "定义: {definition} | 关联: {relations}"
        ),
    },
    "Problem": {
        "name_prefix": "Problem",
        "source_description": "problem-record",
        "keywords": set(),
        "body_template": (
            "[Topic: {topic}] [Problem: {problem_id}] "
            "题型: {type} | 难度: {difficulty} | 考点: {key_points}"
        ),
    },
    "Topic": {
        "name_prefix": "Topic",
        "source_description": "topic-record",
        "keywords": set(),
        "body_template": (
            "[Topic: {topic}] 子主题: {subtopics} | "
            "权重: {weight} | 常见问题: {common_issues}"
        ),
    },
    "MasteryUpdate": {
        "name_prefix": "MasteryUpdate",
        "source_description": "mastery-update-record",
        "keywords": set(),
        "body_template": (
            "[Topic: {topic}] 概念: {concept} | "
            "Grade: {grade} | p_mastery: {p_mastery} | "
            "effective: {effective} | level: {level}"
        ),
    },
    "SelfAssessment": {
        "name_prefix": "SelfAssessment",
        "source_description": "self-assessment-record",
        "keywords": set(),
        "body_template": (
            "[Topic: {topic}] 概念: {concept} | "
            "颜色: {color} | 自评值: {value} | "
            "AI评分: {ai_score}"
        ),
    },
    "ColorTransition": {
        "name_prefix": "ColorTransition",
        "source_description": "color-transition-record",
        "keywords": set(),
        "body_template": (
            "[Topic: {topic}] 概念: {concept} | "
            "旧状态: {old_color}({old_meaning}) | "
            "新状态: {new_color}({new_meaning}) | "
            "评分: {score}/100 | "
            "维度: 准确{accuracy}/形象{imagery}/完整{completeness}/原创{originality} | "
            "触发: {trigger} | 时间: {timestamp}"
        ),
    },
}

# Color code → semantic name (canvas_utils.py authoritative)
COLOR_SEMANTICS: Dict[str, str] = {
    "1": "Gray/无特殊含义",
    "2": "Green/已掌握",
    "3": "Purple/似懂非懂",
    "4": "Red/不理解",
    "5": "Blue/AI生成",
    "6": "Yellow/个人理解",
}


def build_entity_name(entity_type: str, concept: str) -> str:
    """Build standardized entity name: '{Prefix}: {concept}'."""
    config = ENTITY_TYPES.get(entity_type)
    if not config:
        return f"{entity_type}: {concept}"
    return f"{config['name_prefix']}: {concept}"


def build_episode_body(entity_type: str, **kwargs) -> str:
    """Build structured episode_body from template with safe defaults."""
    config = ENTITY_TYPES.get(entity_type)
    if not config:
        return str(kwargs)
    template = config["body_template"]
    safe_kwargs = defaultdict(str, **kwargs)
    return template.format_map(safe_kwargs)


def get_source_description(entity_type: str) -> str:
    """Get the canonical source_description for an entity type."""
    config = ENTITY_TYPES.get(entity_type)
    return config["source_description"] if config else f"{entity_type.lower()}-record"


def classify_entity_type(
    text: str,
    color: Optional[str] = None,
    group_label: Optional[str] = None,
) -> Optional[str]:
    """
    Unified entity type classification logic.

    Priority:
      1. Group label keyword matching (most reliable)
      2. Text content keyword matching
      3. Color mapping fallback
    """
    # Priority 1: Group label keywords
    if group_label:
        label_lower = group_label.lower()
        for etype, config in ENTITY_TYPES.items():
            if not config["keywords"]:
                continue
            if any(kw in label_lower for kw in config["keywords"]):
                return etype

    # Priority 2: Text content keywords
    if text:
        text_lower = text.lower() if text else ""
        for etype, config in ENTITY_TYPES.items():
            if not config["keywords"]:
                continue
            if any(kw in text_lower for kw in config["keywords"]):
                return etype

    # Priority 3: Color mapping fallback
    # "4" (Red/不理解) → Misconception
    # "3" (Purple/似懂非懂) → Misconception
    if color == "4":
        return "Misconception"
    if color == "3":
        return "Misconception"

    return None


def get_color_meaning(color_code: str) -> str:
    """Get human-readable meaning for a color code."""
    return COLOR_SEMANTICS.get(color_code, f"Unknown({color_code})")
