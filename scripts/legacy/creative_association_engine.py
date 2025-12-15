"""
创意联想引擎
Canvas Learning System - Story 8.8

提供跨域概念连接、类比推理、学习路径建议等创意联想功能。
"""

import json
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# 第三方库导入
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy not available. Install with: pip install numpy")

from mcp_memory_client import MCPSemanticMemory

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CreativeInsight:
    """创意洞察数据类"""
    insight_type: str
    insight: str
    confidence: float
    domains_connected: List[str]
    educational_value: str
    creativity_score: float


@dataclass
class LearningPathStep:
    """学习路径步骤数据类"""
    step_number: int
    title: str
    description: str
    estimated_duration_minutes: int
    difficulty_level: str
    prerequisites: List[str]
    resources: List[str]


@dataclass
class LearningPath:
    """学习路径数据类"""
    path_id: str
    title: str
    description: str
    total_steps: int
    estimated_duration_hours: float
    difficulty_level: str
    steps: List[LearningPathStep]
    learning_objectives: List[str]


@dataclass
class Analogy:
    """类比数据类"""
    source_concept: str
    target_concept: str
    analogy_description: str
    similarity_strength: float
    explanation: str


class CreativeAssociationEngine:
    """创意联想引擎"""

    def __init__(self, memory_client: MCPSemanticMemory = None, config: Dict = None):
        """初始化创意联想引擎

        Args:
            memory_client: MCP记忆客户端
            config: 配置字典
        """
        self.memory_client = memory_client
        self.config = config or self._get_default_config()

        # 跨域连接模板
        self.cross_domain_templates = {
            "math_programming": [
                "{数学概念}的逻辑结构类似于编程中的{编程概念}",
                "理解{数学概念}有助于掌握{编程技能}",
                "{数学原理}在{编程场景}中有直接应用"
            ],
            "science_daily": [
                "{科学原理}在日常生活中体现为{日常现象}",
                "理解{科学概念}可以帮助我们解释{日常问题}",
                "{科学规律}指导着我们的{生活决策}"
            ],
            "abstract_concrete": [
                "抽象的{抽象概念}可以通过具体的{具体例子}来理解",
                "{理论知识}的实际应用包括{实践案例}",
                "{概念A}与{概念B}在{应用场景}中相互关联"
            ]
        }

        # 创意联想策略
        self.association_strategies = [
            "analogy_based",        # 基于类比
            "cross_domain",        # 跨域连接
            "application_focused",  # 应用导向
            "historical_context",   # 历史背景
            "future_implications",  # 未来意义
            "interdisciplinary"     # 跨学科
        ]

        # 难度级别映射
        self.difficulty_levels = {
            "beginner": "入门级",
            "intermediate": "进阶级",
            "advanced": "高级",
            "expert": "专家级"
        }

        logger.info("创意联想引擎初始化完成")

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "creativity_levels": {
                "conservative": {
                    "temperature": 0.7,
                    "max_associations": 5,
                    "similarity_threshold": 0.8
                },
                "moderate": {
                    "temperature": 0.9,
                    "max_associations": 8,
                    "similarity_threshold": 0.6
                },
                "creative": {
                    "temperature": 1.2,
                    "max_associations": 12,
                    "similarity_threshold": 0.4
                }
            },
            "domains": [
                "数学", "物理", "化学", "生物", "计算机科学",
                "语言文学", "历史", "地理", "艺术", "哲学",
                "经济学", "心理学", "社会学", "工程学"
            ]
        }

    def generate_creative_associations(self, concept: str, creativity_level: str = "moderate") -> Dict:
        """生成创意联想

        Args:
            concept: 核心概念
            creativity_level: 创意级别 ("conservative", "moderate", "creative")

        Returns:
            Dict: 创意联想结果
        """
        try:
            if creativity_level not in self.config["creativity_levels"]:
                creativity_level = "moderate"

            level_config = self.config["creativity_levels"][creativity_level]
            max_associations = level_config["max_associations"]
            similarity_threshold = level_config["similarity_threshold"]

            # 获取相关概念
            related_concepts = []
            if self.memory_client:
                related_concepts = self.memory_client.find_related_concepts(
                    concept, similarity_threshold
                )

            # 生成多种类型的创意联想
            insights = []
            analogies = []
            applications = []
            learning_paths = []

            # 1. 基于类比的洞察
            analogies = self._generate_analogies(concept, related_concepts, max_associations // 3)

            # 2. 跨域连接
            cross_domain_insights = self._generate_cross_domain_insights(
                concept, related_concepts, max_associations // 3
            )
            insights.extend(cross_domain_insights)

            # 3. 实际应用
            applications = self._generate_practical_applications(
                concept, related_concepts, max_associations // 3
            )

            # 4. 学习路径
            learning_paths = self._generate_learning_paths(concept)

            # 计算总体创意分数
            overall_creativity = self._calculate_overall_creativity(insights, analogies, applications)

            result = {
                "association_id": f"assoc-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "query_concept": concept,
                "creativity_level": creativity_level,
                "creative_insights": [asdict(insight) for insight in insights],
                "analogies": [asdict(analogy) for analogy in analogies],
                "practical_applications": applications,
                "learning_paths": [asdict(path) for path in learning_paths],
                "related_concepts_count": len(related_concepts),
                "overall_creativity_score": overall_creativity,
                "generated_at": datetime.now().isoformat(),
                "algorithm_version": "creative_association_v1.0"
            }

            logger.info(f"为概念 '{concept}' 生成了 {len(insights)} 个创意洞察")
            return result

        except Exception as e:
            logger.error(f"创意联想生成失败: {e}")
            return {"error": str(e)}

    def _generate_analogies(self, concept: str, related_concepts: List[Dict], max_count: int) -> List[Analogy]:
        """生成类比"""
        analogies = []

        # 预定义的类比模板
        analogy_templates = {
            "structure": "{concept}的结构就像{target}的{feature}一样",
            "function": "{concept}的作用类似于{target}在{context}中的作用",
            "process": "理解{concept}的过程就像学习{target}的过程",
            "relationship": "{concept}与{other}的关系就像{target1}与{target2}的关系"
        }

        # 常见的类比对象
        common_targets = [
            ("建造房子", "基础建设"),
            ("烹饪美食", "过程组合"),
            ("驾驶汽车", "系统协调"),
            ("种植植物", "成长发展"),
            ("编织织物", "结构连接"),
            ("演奏乐器", "协调配合")
        ]

        for i, template_type in enumerate(analogy_templates.keys()):
            if len(analogies) >= max_count:
                break

            if related_concepts and i < len(related_concepts):
                target_concept = related_concepts[i]["concept"]
                similarity = related_concepts[i]["similarity_score"]
            else:
                target_concept, context = random.choice(common_targets)
                similarity = 0.6

            template = analogy_templates[template_type]
            analogy_desc = template.format(
                concept=concept,
                target=target_concept,
                context=context if 'context' in locals() else "相关场景",
                feature="核心特征",
                other="相关概念",
                target1="组成部分A",
                target2="组成部分B"
            )

            analogy = Analogy(
                source_concept=concept,
                target_concept=target_concept,
                analogy_description=analogy_desc,
                similarity_strength=similarity,
                explanation=f"通过类比{target_concept}来理解{concept}的核心特征"
            )

            analogies.append(analogy)

        return analogies

    def _generate_cross_domain_insights(self, concept: str, related_concepts: List[Dict], max_count: int) -> List[CreativeInsight]:
        """生成跨域洞察"""
        insights = []

        # 跨域连接模式
        domain_connections = [
            {
                "domains": ["数学", "计算机科学"],
                "pattern": "{concept}的数学原理在{应用场景}中体现为{技术实现}",
                "examples": [
                    ("算法复杂度", "程序性能优化"),
                    ("概率统计", "机器学习模型"),
                    ("逻辑推理", "程序控制流"),
                    ("图论", "网络拓扑结构")
                ]
            },
            {
                "domains": ["科学", "日常生活"],
                "pattern": "{concept}的科学原理解释了我们生活中的{日常现象}",
                "examples": [
                    ("重力", "物体下落"),
                    ("热力学", "烹饪过程"),
                    ("光学", "彩虹形成"),
                    ("声学", "音乐传播")
                ]
            },
            {
                "domains": ["理论", "实践"],
                "pattern": "抽象的{理论概念}在{实践领域}中有具体的应用价值",
                "examples": [
                    ("系统思维", "项目管理"),
                    ("批判思维", "问题分析"),
                    ("创造性思维", "创新设计"),
                    ("系统性思维", "组织管理")
                ]
            }
        ]

        for connection in domain_connections:
            if len(insights) >= max_count:
                break

            for example in connection["examples"]:
                if len(insights) >= max_count:
                    break

                theory, practice = example
                if concept in theory or concept in practice:
                    pattern = connection["pattern"]
                    insight_text = pattern.format(
                        concept=concept,
                        theory概念=theory,
                        实践领域=practice,
                        应用场景=practice,
                        日常现象="相关现象",
                        技术实现="具体实现"
                    )

                    insight = CreativeInsight(
                        insight_type="cross_domain_connection",
                        insight=insight_text,
                        confidence=0.8,
                        domains_connected=connection["domains"],
                        educational_value="high",
                        creativity_score=0.85
                    )

                    insights.append(insight)

        # 如果还没有足够的洞察，生成通用洞察
        while len(insights) < max_count:
            domains = random.sample(self.config["domains"], 2)
            insight_text = f"{concept}的概念可以在{domains[0]}和{domains[1]}之间建立有意义的联系"

            insight = CreativeInsight(
                insight_type="cross_domain_connection",
                insight=insight_text,
                confidence=0.6,
                domains_connected=domains,
                educational_value="moderate",
                creativity_score=0.7
            )

            insights.append(insight)

        return insights

    def _generate_practical_applications(self, concept: str, related_concepts: List[Dict], max_count: int) -> List[Dict]:
        """生成实际应用"""
        applications = []

        # 应用模式
        application_patterns = {
            "problem_solving": {
                "title": f"运用{concept}解决实际问题",
                "description": "通过分析具体问题，应用相关原理和策略",
                "steps": [
                    "问题识别和分析",
                    f"应用{concept}的核心原理",
                    "制定解决方案",
                    "实施和评估效果"
                ]
            },
            "skill_development": {
                "title": f"基于{concept}的技能培养",
                "description": "将理论知识转化为实践技能",
                "steps": [
                    "理解基础概念",
                    "掌握核心方法",
                    "进行实践练习",
                    "反思和改进"
                ]
            },
            "innovation_creativity": {
                "title": f"利用{concept}进行创新思维",
                "description": "运用概念原理进行创新和创造",
                "steps": [
                    "发散思维构思",
                    "概念组合重组",
                    "原型设计和测试",
                    "迭代优化完善"
                ]
            }
        }

        for pattern_name, pattern in application_patterns.items():
            if len(applications) >= max_count:
                break

            # 添加具体的应用场景
            scenarios = self._generate_application_scenarios(concept, pattern_name)
            pattern["scenarios"] = scenarios
            pattern["application_id"] = f"app-{len(applications) + 1}"
            applications.append(pattern)

        return applications

    def _generate_application_scenarios(self, concept: str, pattern_name: str) -> List[str]:
        """生成应用场景"""
        scenario_templates = {
            "problem_solving": [
                f"在学术研究中运用{concept}分析复杂问题",
                f"在工作中利用{concept}提高效率",
                f"通过{concept}解决日常生活中的困难"
            ],
            "skill_development": [
                f"系统学习{concept}相关技能",
                f"通过实践掌握{concept}的应用方法",
                f"在项目中运用{concept}提升专业能力"
            ],
            "innovation_creativity": [
                f"结合{concept}与其他知识进行创新",
                f"运用{concept}开发新的解决方案",
                f"通过{concept}的思维方法激发创意"
            ]
        }

        templates = scenario_templates.get(pattern_name, [f"应用{concept}进行实践"])
        return random.sample(templates, min(3, len(templates)))

    def _generate_learning_paths(self, concept: str) -> List[LearningPath]:
        """生成学习路径"""
        paths = []

        # 不同难度的学习路径
        path_templates = {
            "beginner": {
                "title": f"{concept}入门学习路径",
                "description": "从基础概念开始，逐步建立对概念的理解",
                "difficulty_level": "beginner",
                "duration_hours": 8
            },
            "intermediate": {
                "title": f"{concept}深入学习路径",
                "description": "在掌握基础后，探索概念的高级应用和相关理论",
                "difficulty_level": "intermediate",
                "duration_hours": 16
            },
            "advanced": {
                "title": f"{concept}专业学习路径",
                "description": "深入研究概念的专业应用和前沿发展",
                "difficulty_level": "advanced",
                "duration_hours": 32
            }
        }

        for level, template in path_templates.items():
            steps = self._generate_learning_steps(concept, level)
            learning_objectives = self._generate_learning_objectives(concept, level)

            path = LearningPath(
                path_id=f"path-{level}-{datetime.now().strftime('%Y%m%d')}",
                title=template["title"],
                description=template["description"],
                total_steps=len(steps),
                estimated_duration_hours=template["duration_hours"],
                difficulty_level=template["difficulty_level"],
                steps=steps,
                learning_objectives=learning_objectives
            )

            paths.append(path)

        return paths

    def _generate_learning_steps(self, concept: str, difficulty_level: str) -> List[LearningPathStep]:
        """生成学习步骤"""
        if difficulty_level == "beginner":
            step_templates = [
                ("了解基本定义", f"理解{concept}的核心概念和基本特征", 60),
                ("学习基础理论", f"掌握{concept}的基础原理和理论框架", 120),
                ("观察实际例子", f"通过具体例子加深对{concept}的理解", 90),
                ("尝试简单应用", f"在简单场景中应用{concept}进行练习", 120),
                ("总结和反思", f"总结学习要点，反思理解程度", 30)
            ]
        elif difficulty_level == "intermediate":
            step_templates = [
                ("深入理论分析", f"深入学习{concept}的理论基础", 180),
                ("掌握应用方法", f"学习{concept}的多种应用方法和技巧", 240),
                ("分析复杂案例", f"研究{concept}在复杂场景中的应用", 200),
                ("进行实践项目", f"通过项目实践巩固{concept}的掌握", 300),
                ("探索相关问题", f"了解{concept}相关的问题和挑战", 120)
            ]
        else:  # advanced
            step_templates = [
                ("研究前沿发展", f"了解{concept}的最新研究和发展趋势", 240),
                ("专业应用实践", f"在专业场景中深度应用{concept}", 400),
                ("创新应用探索", f"探索{concept}的创新应用方式", 300),
                ("跨领域整合", f"将{concept}与其他领域知识整合", 360),
                ("知识贡献", f"基于对{concept}的理解做出知识贡献", 300)
            ]

        steps = []
        for i, (title, description, duration) in enumerate(step_templates):
            step = LearningPathStep(
                step_number=i + 1,
                title=title,
                description=description,
                estimated_duration_minutes=duration,
                difficulty_level=difficulty_level,
                prerequisites=self._generate_prerequisites(i, concept, difficulty_level),
                resources=self._generate_resources(concept, difficulty_level)
            )
            steps.append(step)

        return steps

    def _generate_prerequisites(self, step_number: int, concept: str, difficulty_level: str) -> List[str]:
        """生成先决条件"""
        if step_number == 0:
            return []
        elif step_number == 1:
            return [f"完成第{step_number}步的学习"]
        else:
            return [f"掌握{concept}的基础知识", f"完成前面{step_number}个学习步骤"]

    def _generate_resources(self, concept: str, difficulty_level: str) -> List[str]:
        """生成学习资源"""
        resource_templates = [
            f"{concept}相关教材和参考资料",
            f"在线课程和教学视频",
            f"练习题和实践项目",
            f"学习社区和讨论论坛"
        ]
        return resource_templates

    def _generate_learning_objectives(self, concept: str, difficulty_level: str) -> List[str]:
        """生成学习目标"""
        objectives_map = {
            "beginner": [
                f"理解{concept}的基本定义和特征",
                f"能够识别{concept}在不同情境中的表现",
                f"掌握{concept}的基础应用方法"
            ],
            "intermediate": [
                f"深入理解{concept}的理论基础",
                f"熟练运用{concept}解决实际问题",
                f"分析{concept}与其他概念的关联"
            ],
            "advanced": [
                f"精通{concept}的专业应用",
                f"能够创新性地运用{concept}",
                f"对{concept}的发展做出贡献"
            ]
        }

        return objectives_map.get(difficulty_level, objectives_map["intermediate"])

    def _calculate_overall_creativity(self, insights: List[CreativeInsight], analogies: List[Analogy], applications: List[Dict]) -> float:
        """计算总体创意分数"""
        if not insights and not analogies and not applications:
            return 0.0

        scores = []

        # 洞察创意分数
        for insight in insights:
            scores.append(insight.creativity_score * insight.confidence)

        # 类比创意分数
        for analogy in analogies:
            scores.append(analogy.similarity_strength * 0.8)  # 类比的权重系数

        # 应用创意分数
        for app in applications:
            scores.append(0.7)  # 应用的固定创意分数

        return sum(scores) / len(scores) if scores else 0.0


if __name__ == "__main__":
    # 简单测试
    from mcp_memory_client import create_memory_client

    try:
        memory_client = create_memory_client()
        engine = CreativeAssociationEngine(memory_client)

        # 测试概念
        test_concept = "逆否命题"
        result = engine.generate_creative_associations(test_concept, "moderate")

        print(json.dumps(result, ensure_ascii=False, indent=2))

        memory_client.close()
    except Exception as e:
        print(f"测试失败: {e}")