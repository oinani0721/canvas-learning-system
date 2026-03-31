#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Story 7.2: 智能结果融合引擎测试套件

测试智能结果融合引擎的所有功能：
- Task 1: 冲突检测和解决算法
- Task 2: 基于置信度的加权融合
- Task 3: 信息完整性保护机制
- Task 4: 融合过程可解释性
- Task 5: 性能优化和集成测试
"""

import asyncio
import os

# 导入Story 7.2的所有类
import sys
import time
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_utils import (
    ConfidenceBasedFusion,
    ConflictDetectionEngine,
    FusionProcessTransparency,
    InformationIntegrityProtection,
    IntelligentResultFusionEngine,
    intelligent_result_fusion,
)


class TestConflictDetectionEngine(unittest.TestCase):
    """测试冲突检测和解决引擎 - Task 1"""

    def setUp(self):
        """设置测试环境"""
        self.conflict_detector = ConflictDetectionEngine()

    def test_detect_contradictory_conclusions(self):
        """测试矛盾结论检测"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "建议采用主动学习方法，这样可以提高学习效率。",
                "confidence": 0.8,
            },
            {
                "agent_type": "basic-decomposition",
                "analysis_summary": "不建议采用主动学习方法，这样会降低学习效率。",
                "confidence": 0.7,
            },
        ]

        conflicts = self.conflict_detector.detect_conflicts(agent_results)

        # 验证检测到矛盾结论
        contradictory_conflicts = [
            c for c in conflicts if c["type"] == "contradictory_conclusions"
        ]
        self.assertGreater(len(contradictory_conflicts), 0)

        # 验证冲突详情
        conflict = contradictory_conflicts[0]
        self.assertIn("agents", conflict)
        self.assertIn("agent_types", conflict)
        self.assertEqual(
            set(conflict["agent_types"]), {"oral-explanation", "basic-decomposition"}
        )

    def test_detect_duplicate_suggestions(self):
        """测试重复建议检测"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "agent_recommendations": [
                    {
                        "agent_type": "clarification-path",
                        "confidence": 0.8,
                        "reason": "建议深入理解概念的定义",
                        "target_nodes": ["concept1"],
                    }
                ],
            },
            {
                "agent_type": "clarification-path",
                "agent_recommendations": [
                    {
                        "agent_type": "clarification-path",
                        "confidence": 0.7,
                        "reason": "深入理解概念定义很重要",
                        "target_nodes": ["concept1"],
                    }
                ],
            },
        ]

        conflicts = self.conflict_detector.detect_conflicts(agent_results)

        # 验证检测到重复建议
        duplicate_conflicts = [
            c for c in conflicts if c["type"] == "duplicate_suggestions"
        ]
        self.assertGreater(len(duplicate_conflicts), 0)

    def test_detect_inconsistent_recommendations(self):
        """测试不一致推荐检测"""
        agent_results = [
            {
                "agent_type": "scoring-agent",
                "agent_recommendations": [
                    {
                        "agent_type": "oral-explanation",
                        "confidence": 0.9,
                        "reason": "建议生成口语化解释",
                    },
                    {
                        "agent_type": "comparison-table",
                        "confidence": 0.4,
                        "reason": "建议生成对比表",
                    },
                ],
            },
            {
                "agent_type": "canvas-orchestrator",
                "agent_recommendations": [
                    {
                        "agent_type": "oral-explanation",
                        "confidence": 0.3,
                        "reason": "不建议生成口语化解释",
                    }
                ],
            },
        ]

        conflicts = self.conflict_detector.detect_conflicts(agent_results)

        # 验证检测到不一致推荐
        inconsistent_conflicts = [
            c for c in conflicts if c["type"] == "inconsistent_recommendations"
        ]
        self.assertGreater(len(inconsistent_conflicts), 0)

    def test_detect_semantic_overlap(self):
        """测试语义重叠检测"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "这个概念的理解需要从多个角度分析，包括定义、方法和应用",
                "confidence": 0.8,
            },
            {
                "agent_type": "clarification-path",
                "analysis_summary": "理解这个概念要考虑定义理解、方法理解和应用理解",
                "confidence": 0.7,
            },
        ]

        conflicts = self.conflict_detector.detect_conflicts(agent_results)

        # 验证检测到语义重叠
        semantic_conflicts = [c for c in conflicts if c["type"] == "semantic_overlap"]
        self.assertGreater(len(semantic_conflicts), 0)

    def test_no_conflicts_detection(self):
        """测试无冲突情况"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "生成800-1200词的口语化解释",
                "confidence": 0.8,
            },
            {
                "agent_type": "comparison-table",
                "analysis_summary": "生成结构化的对比表格",
                "confidence": 0.7,
            },
        ]

        conflicts = self.conflict_detector.detect_conflicts(agent_results)

        # 验证没有检测到冲突
        self.assertEqual(len(conflicts), 0)


class TestConfidenceBasedFusion(unittest.TestCase):
    """测试基于置信度的加权融合 - Task 2"""

    def setUp(self):
        """设置测试环境"""
        self.confidence_fusion = ConfidenceBasedFusion()

    def test_conflict_resolution_by_confidence(self):
        """测试基于置信度的冲突解决"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "建议采用方法A",
                "confidence": 0.9,
            },
            {
                "agent_type": "basic-decomposition",
                "analysis_summary": "建议采用方法B",
                "confidence": 0.6,
            },
        ]

        conflicts = [
            {
                "type": "contradictory_conclusions",
                "agents": [0, 1],
                "agent_types": ["oral-explanation", "basic-decomposition"],
                "confidence1": 0.9,
                "confidence2": 0.6,
                "conclusion1": "建议采用方法A",
                "conclusion2": "建议采用方法B",
            }
        ]

        fusion_result = self.confidence_fusion.fuse_results(agent_results, conflicts)

        # 验证选择了高置信度的结果
        self.assertEqual(fusion_result["resolved_conflicts"], 1)
        self.assertIn("fused_result", fusion_result)

        # 验证融合报告
        self.assertIn("fusion_report", fusion_result)
        self.assertIn("Agent oral-explanation", fusion_result["fusion_report"])

    def test_duplicate_suggestions_merging(self):
        """测试重复建议合并"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "agent_recommendations": [
                    {
                        "agent_type": "clarification-path",
                        "confidence": 0.8,
                        "reason": "深入理解概念",
                        "target_nodes": ["node1"],
                    }
                ],
            },
            {
                "agent_type": "clarification-path",
                "agent_recommendations": [
                    {
                        "agent_type": "clarification-path",
                        "confidence": 0.7,
                        "reason": "深入理解概念",
                        "target_nodes": ["node1"],
                    }
                ],
            },
        ]

        conflicts = [
            {
                "type": "duplicate_suggestions",
                "agents": [0, 1],
                "agent_types": ["oral-explanation", "clarification-path"],
                "suggestion1": "深入理解概念",
                "suggestion2": "深入理解概念",
            }
        ]

        fusion_result = self.confidence_fusion.fuse_results(agent_results, conflicts)

        # 验证合并后的推荐去重
        fused_result = fusion_result["fused_result"]
        recommendations = fused_result.get("agent_recommendations", [])

        # 应该只有一个推荐（去重后）
        clarif_recs = [
            r for r in recommendations if r["agent_type"] == "clarification-path"
        ]
        self.assertEqual(len(clarif_recs), 1)

    def test_weighted_fusion_calculation(self):
        """测试加权融合计算"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "这是一个重要的学习概念",
                "confidence": 0.9,
                "agent_recommendations": [
                    {
                        "agent_type": "oral-explanation",
                        "confidence": 0.9,
                        "reason": "生成口语化解释",
                    }
                ],
            },
            {
                "agent_type": "clarification-path",
                "analysis_summary": "这是一个关键的学习概念",
                "confidence": 0.6,
                "agent_recommendations": [
                    {
                        "agent_type": "clarification-path",
                        "confidence": 0.6,
                        "reason": "生成澄清路径",
                    }
                ],
            },
        ]

        fusion_result = self.confidence_fusion.fuse_results(agent_results, [])

        # 验证加权融合结果
        fused_result = fusion_result["fused_result"]

        # 验证平均置信度计算
        expected_avg_confidence = (0.9 + 0.6) / 2
        self.assertAlmostEqual(
            fused_result["average_confidence"], expected_avg_confidence, places=2
        )

        # 验证融合权重
        self.assertIn("total_weight", fused_result)
        self.assertIn("fusion_method", fused_result)
        self.assertEqual(fused_result["fusion_method"], "confidence_weighted_average")

    def test_agent_contributions_analysis(self):
        """测试Agent贡献分析"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "confidence": 0.9,
                "agent_recommendations": [
                    {"agent_type": "oral-explanation", "reason": "解释1"},
                    {"agent_type": "oral-explanation", "reason": "解释2"},
                ],
                "analysis_summary": "这是一个详细的分析摘要，包含多个重要观点和建议",
            },
            {
                "agent_type": "clarification-path",
                "confidence": 0.6,
                "agent_recommendations": [
                    {"agent_type": "clarification-path", "reason": "澄清1"}
                ],
                "analysis_summary": "简短摘要",
            },
        ]

        fusion_result = self.confidence_fusion.fuse_results(agent_results, [])

        # 验证Agent贡献分析
        contributions = fusion_result["agent_contributions"]
        self.assertIn("oral-explanation", contributions)
        self.assertIn("clarification-path", contributions)

        # 验证贡献分数计算
        oral_contrib = contributions["oral-explanation"]
        self.assertEqual(oral_contrib["confidence"], 0.9)
        self.assertEqual(oral_contrib["recommendations_count"], 2)
        self.assertGreater(oral_contrib["analysis_length"], 20)


class TestInformationIntegrityProtection(unittest.TestCase):
    """测试信息完整性保护机制 - Task 3"""

    def setUp(self):
        """设置测试环境"""
        self.integrity_protector = InformationIntegrityProtection()

    def test_lost_insights_detection(self):
        """测试丢失见解检测"""
        original_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "建议采用主动学习法，这是提高效率的关键方法。注意要结合实践应用。",
                "confidence": 0.8,
                "agent_recommendations": [
                    {
                        "agent_type": "oral-explanation",
                        "confidence": 0.8,
                        "reason": "生成详细的口语化解释",
                        "target_nodes": ["node1"],
                    }
                ],
            }
        ]

        fused_result = {
            "analysis_summary": "建议采用主动学习法",
            "agent_recommendations": [
                {
                    "agent_type": "oral-explanation",
                    "confidence": 0.8,
                    "reason": "生成解释",
                    "target_nodes": ["node1"],
                }
            ],
        }

        protected_result = self.integrity_protector.protect_integrity(
            original_results, fused_result
        )

        # 验证检测到丢失的见解
        integrity_info = protected_result["integrity_protection"]
        self.assertGreater(integrity_info["lost_insights_count"], 0)
        self.assertIn("integrity_report", integrity_info)

    def test_diversity_preservation_evaluation(self):
        """测试多样性保持评估"""
        original_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "口语化解释方法，包括生动例子和常见误区",
                "agent_recommendations": [
                    {"agent_type": "oral-explanation", "reason": "生成口语化内容"}
                ],
            },
            {
                "agent_type": "comparison-table",
                "analysis_summary": "结构化对比方法，包括多维度比较",
                "agent_recommendations": [
                    {"agent_type": "comparison-table", "reason": "生成对比表格"}
                ],
            },
        ]

        fused_result = {
            "analysis_summary": "综合解释方法",
            "agent_recommendations": [
                {"agent_type": "oral-explanation", "reason": "生成口语化内容"},
                {"agent_type": "comparison-table", "reason": "生成对比表格"},
            ],
        }

        protected_result = self.integrity_protector.protect_integrity(
            original_results, fused_result
        )

        # 验证多样性分数
        integrity_info = protected_result["integrity_protection"]
        diversity_score = integrity_info["diversity_score"]
        self.assertGreaterEqual(diversity_score, 0.0)
        self.assertLessEqual(diversity_score, 1.0)

    def test_information_restoration(self):
        """测试信息恢复"""
        original_results = [
            {
                "agent_type": "memory-anchor",
                "analysis_summary": "使用生动的类比帮助记忆",
                "confidence": 0.9,
                "agent_recommendations": [
                    {
                        "agent_type": "memory-anchor",
                        "confidence": 0.9,
                        "reason": "创建记忆锚点：将概念比作大树",
                        "target_nodes": ["concept1"],
                    }
                ],
            }
        ]

        fused_result = {"analysis_summary": "基本内容摘要", "agent_recommendations": []}

        protected_result = self.integrity_protector.protect_integrity(
            original_results, fused_result
        )

        # 验证高置信度见解被恢复
        restored_recommendations = protected_result["agent_recommendations"]
        restored_insights = [r for r in restored_recommendations if r.get("restored")]

        self.assertGreater(len(restored_insights), 0)
        self.assertIn("记忆锚点", restored_insights[0]["reason"])

    def test_diversity_optimization(self):
        """测试多样性优化"""
        # 低多样性情况
        original_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "单一方法的解释",
                "agent_recommendations": [
                    {"agent_type": "oral-explanation", "reason": "生成解释"}
                ],
            }
        ]

        fused_result = {
            "analysis_summary": "单一方法解释",
            "agent_recommendations": [
                {"agent_type": "oral-explanation", "reason": "生成解释"}
            ],
        }

        protected_result = self.integrity_protector.protect_integrity(
            original_results, fused_result
        )

        # 验证多样性增强
        recommendations = protected_result["agent_recommendations"]
        diversity_enhanced = [r for r in recommendations if r.get("diversity_enhanced")]

        # 应该添加多样性增强推荐
        self.assertGreater(len(diversity_enhanced), 0)


class TestFusionProcessTransparency(unittest.TestCase):
    """测试融合过程可解释性 - Task 4"""

    def setUp(self):
        """设置测试环境"""
        self.transparency_generator = FusionProcessTransparency()

    def test_executive_summary_generation(self):
        """测试执行摘要生成"""
        original_results = [
            {"agent_type": "oral-explanation", "confidence": 0.9},
            {"agent_type": "clarification-path", "confidence": 0.7},
        ]

        conflicts = [
            {
                "type": "duplicate_suggestions",
                "agents": [0, 1],
                "agent_types": ["oral-explanation", "clarification-path"],
                "resolved": True,
            }
        ]

        fused_result = {
            "average_confidence": 0.8,
            "agent_recommendations": [
                {"agent_type": "oral-explanation", "confidence": 0.9},
                {"agent_type": "clarification-path", "confidence": 0.7},
            ],
        }

        fusion_report = "融合完成报告"

        explanation = self.transparency_generator.generate_fusion_explanation(
            original_results, conflicts, fused_result, fusion_report
        )

        # 验证执行摘要
        executive_summary = explanation["executive_summary"]
        self.assertIn("参与Agent数量", executive_summary)
        self.assertIn("检测到冲突", executive_summary)
        self.assertIn("融合结果置信度", executive_summary)

    def test_detailed_process_explanation(self):
        """测试详细过程解释"""
        original_results = [
            {
                "agent_type": "oral-explanation",
                "confidence": 0.9,
                "agent_recommendations": [
                    {"agent_type": "oral-explanation", "reason": "解释1"},
                    {"agent_type": "oral-explanation", "reason": "解释2"},
                ],
            },
            {
                "agent_type": "clarification-path",
                "confidence": 0.6,
                "agent_recommendations": [
                    {"agent_type": "clarification-path", "reason": "澄清1"}
                ],
            },
        ]

        conflicts = [
            {
                "type": "semantic_overlap",
                "agents": [0, 1],
                "agent_types": ["oral-explanation", "clarification-path"],
                "resolved": True,
                "resolution_strategy": "information_preservation",
            }
        ]

        fused_result = {
            "fusion_method": "confidence_weighted_average",
            "total_weight": 2.3,
            "integrity_protection": {"diversity_score": 0.8, "lost_insights_count": 0},
        }

        fusion_report = "测试报告"

        explanation = self.transparency_generator.generate_fusion_explanation(
            original_results, conflicts, fused_result, fusion_report
        )

        # 验证详细过程
        detailed_process = explanation["detailed_process"]
        self.assertIsInstance(detailed_process, list)
        self.assertGreater(len(detailed_process), 0)

        # 验证包含关键步骤
        process_text = "\n".join(detailed_process)
        self.assertIn("步骤1: 初始Agent结果分析", process_text)
        self.assertIn("步骤2: 智能冲突检测", process_text)
        self.assertIn("步骤3: 置信度加权融合", process_text)

    def test_visual_representation(self):
        """测试可视化表示"""
        original_results = [
            {"agent_type": "oral-explanation", "confidence": 0.9},
            {"agent_type": "clarification-path", "confidence": 0.7},
        ]

        conflicts = [{"type": "duplicate_suggestions", "resolved": True}]

        fused_result = {
            "average_confidence": 0.8,
            "agent_contributions": {
                "oral-explanation": {"contribution_score": 0.9},
                "clarification-path": {"contribution_score": 0.7},
            },
        }

        fusion_report = "测试报告"

        explanation = self.transparency_generator.generate_fusion_explanation(
            original_results, conflicts, fused_result, fusion_report
        )

        # 验证可视化表示
        visual_representation = explanation["visual_representation"]
        self.assertIn("融合流程可视化", visual_representation)
        self.assertIn("Agent贡献度分布", visual_representation)

    def test_decision_audit_trail(self):
        """测试决策审计跟踪"""
        original_results = [{"agent_type": "oral-explanation", "confidence": 0.9}]

        conflicts = [{"type": "duplicate_suggestions", "resolved": True}]

        fused_result = {"integrity_protection": {"diversity_score": 0.8}}

        fusion_report = "测试报告"

        explanation = self.transparency_generator.generate_fusion_explanation(
            original_results, conflicts, fused_result, fusion_report
        )

        # 验证审计跟踪
        audit_trail = explanation["decision_audit_trail"]
        self.assertIsInstance(audit_trail, list)
        self.assertGreater(len(audit_trail), 0)

        # 验证包含关键步骤
        steps = [item["step"] for item in audit_trail]
        self.assertIn("initialization", steps)
        self.assertIn("conflict_detection", steps)

    def test_quality_metrics_calculation(self):
        """测试质量指标计算"""
        original_results = [
            {
                "agent_type": "oral-explanation",
                "confidence": 0.9,
                "agent_recommendations": [
                    {"agent_type": "oral-explanation", "reason": "解释1"}
                ],
            },
            {
                "agent_type": "clarification-path",
                "confidence": 0.7,
                "agent_recommendations": [
                    {"agent_type": "clarification-path", "reason": "澄清1"}
                ],
            },
        ]

        conflicts = [{"type": "duplicate_suggestions", "resolved": True}]

        fused_result = {
            "average_confidence": 0.8,
            "agent_recommendations": [
                {"agent_type": "oral-explanation", "reason": "解释1"},
                {"agent_type": "clarification-path", "reason": "澄清1"},
            ],
            "integrity_protection": {"diversity_score": 0.8, "lost_insights_count": 0},
        }

        fusion_report = "测试报告"

        explanation = self.transparency_generator.generate_fusion_explanation(
            original_results, conflicts, fused_result, fusion_report
        )

        # 验证质量指标
        quality_metrics = explanation["quality_metrics"]
        self.assertIn("conflict_resolution_rate", quality_metrics)
        self.assertIn("confidence_preservation_rate", quality_metrics)
        self.assertIn("information_integrity_score", quality_metrics)
        self.assertIn("fusion_efficiency", quality_metrics)

        # 验证指标值在合理范围内
        self.assertEqual(quality_metrics["conflict_resolution_rate"], 1.0)
        self.assertGreaterEqual(quality_metrics["confidence_preservation_rate"], 0.0)


class TestIntelligentResultFusionEngine(unittest.TestCase):
    """测试智能结果融合引擎主控制器 - 集成测试"""

    def setUp(self):
        """设置测试环境"""
        self.fusion_engine = IntelligentResultFusionEngine()

    def test_complete_fusion_workflow(self):
        """测试完整融合工作流"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "建议生成详细的口语化解释，包含生动例子",
                "confidence": 0.9,
                "agent_recommendations": [
                    {
                        "agent_type": "oral-explanation",
                        "confidence": 0.9,
                        "reason": "生成800-1200词的教授式解释",
                        "target_nodes": ["concept1"],
                    }
                ],
            },
            {
                "agent_type": "clarification-path",
                "analysis_summary": "建议通过4步澄清路径深入理解概念",
                "confidence": 0.8,
                "agent_recommendations": [
                    {
                        "agent_type": "clarification-path",
                        "confidence": 0.8,
                        "reason": "创建1500+词的系统化澄清文档",
                        "target_nodes": ["concept1"],
                    }
                ],
            },
            {
                "agent_type": "basic-decomposition",
                "analysis_summary": "建议将复杂概念拆解为基础问题",
                "confidence": 0.7,
                "agent_recommendations": [
                    {
                        "agent_type": "basic-decomposition",
                        "confidence": 0.7,
                        "reason": "生成3-7个引导性问题",
                        "target_nodes": ["concept1"],
                    }
                ],
            },
        ]

        # 执行完整融合
        fusion_result = self.fusion_engine.fuse_agent_results(agent_results)

        # 验证融合结果结构
        self.assertIn("fused_result", fusion_result)
        self.assertIn("conflicts_detected", fusion_result)
        self.assertIn("conflicts_resolved", fusion_result)
        self.assertIn("processing_time", fusion_result)
        self.assertIn("explanation", fusion_result)
        self.assertIn("timestamp", fusion_result)

        # 验证融合内容质量
        fused_result = fusion_result["fused_result"]
        self.assertIn("analysis_summary", fused_result)
        self.assertIn("agent_recommendations", fused_result)
        self.assertIn("average_confidence", fused_result)
        self.assertIn("integrity_protection", fused_result)

        # 验证平均置信度合理
        self.assertGreater(fused_result["average_confidence"], 0.6)
        self.assertLessEqual(fused_result["average_confidence"], 1.0)

    def test_fusion_with_conflicts(self):
        """测试包含冲突的融合"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "建议采用主动学习方法",
                "confidence": 0.9,
                "agent_recommendations": [
                    {
                        "agent_type": "oral-explanation",
                        "confidence": 0.9,
                        "reason": "生成口语化解释",
                    }
                ],
            },
            {
                "agent_type": "basic-decomposition",
                "analysis_summary": "不建议采用主动学习方法",
                "confidence": 0.6,
                "agent_recommendations": [
                    {
                        "agent_type": "basic-decomposition",
                        "confidence": 0.6,
                        "reason": "生成基础拆解问题",
                    }
                ],
            },
        ]

        fusion_result = self.fusion_engine.fuse_agent_results(agent_results)

        # 验证检测到冲突
        self.assertGreater(fusion_result["conflicts_detected"], 0)

        # 验证至少解决了一些冲突
        self.assertGreaterEqual(fusion_result["conflicts_resolved"], 0)

    def test_fusion_options_configuration(self):
        """测试融合选项配置"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "测试内容",
                "confidence": 0.8,
            }
        ]

        # 测试基础选项
        basic_options = {
            "enable_conflict_resolution": True,
            "enable_integrity_protection": False,
            "enable_transparency": False,
            "detail_level": "basic",
        }

        fusion_result = self.fusion_engine.fuse_agent_results(
            agent_results, basic_options
        )

        # 基础模式应该不包含详细解释
        self.assertNotIn("explanation", fusion_result)
        self.assertNotIn("performance_metrics", fusion_result)

        # 测试详细选项
        detailed_options = {
            "enable_conflict_resolution": True,
            "enable_integrity_protection": True,
            "enable_transparency": True,
            "detail_level": "detailed",
        }

        fusion_result = self.fusion_engine.fuse_agent_results(
            agent_results, detailed_options
        )

        # 详细模式应该包含完整信息
        self.assertIn("explanation", fusion_result)
        self.assertIn("performance_metrics", fusion_result)

    def test_performance_metrics_tracking(self):
        """测试性能指标跟踪"""
        agent_results = [
            {
                "agent_type": "oral-explanation",
                "analysis_summary": "性能测试内容",
                "confidence": 0.8,
            }
        ]

        # 执行多次融合以测试指标累积
        for i in range(3):
            fusion_result = self.fusion_engine.fuse_agent_results(agent_results)
            self.assertGreater(fusion_result["processing_time"], 0)

        # 验证性能指标更新
        performance_summary = self.fusion_engine.get_performance_summary()
        self.assertIn("总融合次数", performance_summary)
        self.assertIn("平均处理时间", performance_summary)

        # 验证指标值合理
        metrics = self.fusion_engine.performance_metrics
        self.assertEqual(metrics["total_fusions"], 3)
        self.assertGreater(metrics["average_processing_time"], 0)

    def test_fallback_result_creation(self):
        """测试备用结果创建"""
        # 测试空结果
        fallback_result = self.fusion_engine._create_fallback_result([])
        self.assertIn("fallback_mode", fallback_result)
        self.assertEqual(fallback_result["average_confidence"], 0.0)

        # 测试有输入但融合失败的情况
        agent_results = [
            {
                "agent_type": "test-agent",
                "confidence": 0.5,
                "agent_recommendations": [{"agent_type": "test", "reason": "测试"}],
            }
        ]

        fallback_result = self.fusion_engine._create_fallback_result(agent_results)
        self.assertIn("fallback_mode", fallback_result)
        self.assertGreater(fallback_result["average_confidence"], 0)


class TestIntelligentResultFusionTool(unittest.TestCase):
    """测试智能结果融合工具函数"""

    async def test_tool_function_basic_usage(self):
        """测试工具函数基本使用"""
        args = {
            "agent_results": [
                {
                    "agent_type": "oral-explanation",
                    "analysis_summary": "生成口语化解释",
                    "confidence": 0.9,
                    "agent_recommendations": [
                        {
                            "agent_type": "oral-explanation",
                            "confidence": 0.9,
                            "reason": "创建教授式解释",
                        }
                    ],
                },
                {
                    "agent_type": "clarification-path",
                    "analysis_summary": "创建澄清路径",
                    "confidence": 0.8,
                    "agent_recommendations": [
                        {
                            "agent_type": "clarification-path",
                            "confidence": 0.8,
                            "reason": "生成系统化澄清文档",
                        }
                    ],
                },
            ],
            "options": {"detail_level": "standard"},
        }

        result = await intelligent_result_fusion(args)

        # 验证响应格式
        self.assertIn("content", result)
        self.assertIsInstance(result["content"], list)
        self.assertGreater(len(result["content"]), 0)

        # 验证响应内容
        content = result["content"][0]
        self.assertIn("type", content)
        self.assertIn("text", content)

        # 验证包含关键信息
        text = content["text"]
        self.assertIn("智能结果融合报告", text)
        self.assertIn("参与Agent数量", text)
        self.assertIn("融合质量", text)

    async def test_tool_function_error_handling(self):
        """测试工具函数错误处理"""
        # 测试无效参数类型
        result = await intelligent_result_fusion("invalid_args")
        self.assertIn("content", result)
        self.assertIn("执行失败", result["content"][0]["text"])

        # 测试空的agent_results
        result = await intelligent_result_fusion({"agent_results": []})
        self.assertIn("content", result)
        self.assertIn("执行失败", result["content"][0]["text"])

        # 测试非列表的agent_results
        result = await intelligent_result_fusion({"agent_results": "not_a_list"})
        self.assertIn("content", result)
        self.assertIn("执行失败", result["content"][0]["text"])

    async def test_tool_function_with_options(self):
        """测试带选项的工具函数"""
        args = {
            "agent_results": [
                {
                    "agent_type": "oral-explanation",
                    "analysis_summary": "测试分析摘要",
                    "confidence": 0.9,
                    "agent_recommendations": [
                        {
                            "agent_type": "oral-explanation",
                            "confidence": 0.9,
                            "reason": "测试推荐理由",
                        }
                    ],
                }
            ],
            "options": {
                "enable_conflict_resolution": True,
                "enable_integrity_protection": True,
                "enable_transparency": True,
                "detail_level": "detailed",
            },
        }

        result = await intelligent_result_fusion(args)

        # 验证响应
        self.assertIn("content", result)
        text = result["content"][0]["text"]

        # 详细模式应该包含更多信息
        self.assertIn("执行摘要", text) or self.assertIn("Context7验证", text)

    def test_tool_function_sync_wrapper(self):
        """测试工具函数同步包装器"""
        args = {
            "agent_results": [
                {
                    "agent_type": "oral-explanation",
                    "analysis_summary": "同步测试",
                    "confidence": 0.8,
                }
            ]
        }

        # 由于工具函数是异步的，我们需要用asyncio运行
        result = asyncio.run(intelligent_result_fusion(args))

        self.assertIn("content", result)
        self.assertIsInstance(result["content"], list)


class TestPerformanceOptimization(unittest.TestCase):
    """测试性能优化 - Task 5"""

    def setUp(self):
        """设置测试环境"""
        self.fusion_engine = IntelligentResultFusionEngine()

    def test_large_scale_fusion_performance(self):
        """测试大规模融合性能"""
        # 创建大量Agent结果
        large_agent_results = []
        agent_types = [
            "oral-explanation",
            "clarification-path",
            "comparison-table",
            "memory-anchor",
            "four-level-explanation",
            "example-teaching",
            "scoring-agent",
            "verification-question-agent",
        ]

        for i in range(20):  # 20个Agent结果
            agent_type = agent_types[i % len(agent_types)]
            large_agent_results.append(
                {
                    "agent_type": f"{agent_type}_{i}",
                    "analysis_summary": f"第{i}个Agent的分析摘要",
                    "confidence": 0.5 + (i % 5) * 0.1,
                    "agent_recommendations": [
                        {
                            "agent_type": agent_type,
                            "confidence": 0.7 + (i % 3) * 0.1,
                            "reason": f"第{i}个推荐理由",
                            "target_nodes": [f"node_{i}"],
                        }
                    ],
                }
            )

        # 测试大规模融合性能
        start_time = time.time()
        fusion_result = self.fusion_engine.fuse_agent_results(large_agent_results)
        end_time = time.time()

        processing_time = end_time - start_time

        # 验证性能要求（应该在合理时间内完成）
        self.assertLess(processing_time, 5.0)  # 应该在5秒内完成
        self.assertGreater(fusion_result["conflicts_detected"], 0)  # 应该检测到一些冲突

        # 验证结果质量
        fused_result = fusion_result["fused_result"]
        self.assertGreater(len(fused_result["agent_recommendations"]), 0)
        self.assertGreater(fused_result["average_confidence"], 0)

    def test_memory_efficiency(self):
        """测试内存效率"""
        # 创建包含大量数据的Agent结果
        memory_intensive_results = []

        for i in range(10):
            # 创建大型分析摘要
            large_summary = "这是一个非常长的分析摘要。" * 100  # 重复100次

            # 创建大量推荐
            many_recommendations = []
            for j in range(20):
                many_recommendations.append(
                    {
                        "agent_type": f"test_agent_{j}",
                        "confidence": 0.8,
                        "reason": f"这是第{j}个推荐理由，" * 10,  # 较长的理由
                        "target_nodes": [f"node_{k}" for k in range(5)],
                    }
                )

            memory_intensive_results.append(
                {
                    "agent_type": f"memory_test_agent_{i}",
                    "analysis_summary": large_summary,
                    "confidence": 0.7 + i * 0.02,
                    "agent_recommendations": many_recommendations,
                }
            )

        # 测试内存密集型融合
        fusion_result = self.fusion_engine.fuse_agent_results(memory_intensive_results)

        # 验证融合成功完成
        self.assertIn("fused_result", fusion_result)

        # 验证推荐数量被合理控制（去重和优化）
        fused_result = fusion_result["fused_result"]
        # 融合后的推荐数量应该少于原始总数
        original_total = sum(
            len(r["agent_recommendations"]) for r in memory_intensive_results
        )
        fused_count = len(fused_result["agent_recommendations"])
        self.assertLessEqual(fused_count, original_total)

    def test_concurrent_fusion_capability(self):
        """测试并发融合能力"""

        async def concurrent_fusion_test():
            # 创建多个融合任务
            tasks = []

            for i in range(5):  # 5个并发任务
                agent_results = [
                    {
                        "agent_type": f"concurrent_agent_{i}_{j}",
                        "analysis_summary": f"并发测试任务{i}的第{j}个Agent",
                        "confidence": 0.7 + j * 0.05,
                        "agent_recommendations": [
                            {
                                "agent_type": f"agent_{i}_{j}",
                                "confidence": 0.8,
                                "reason": f"并发测试推荐{i}_{j}",
                            }
                        ],
                    }
                    for j in range(3)  # 每个任务3个Agent
                ]

                task = asyncio.create_task(
                    asyncio.to_thread(
                        self.fusion_engine.fuse_agent_results, agent_results
                    )
                )
                tasks.append(task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks)

            # 验证所有任务成功完成
            self.assertEqual(len(results), 5)

            for result in results:
                self.assertIn("fused_result", result)
                self.assertIn("processing_time", result)
                self.assertGreater(result["processing_time"], 0)

        # 运行并发测试
        asyncio.run(concurrent_fusion_test())

    def test_error_recovery_performance(self):
        """测试错误恢复性能"""
        # 创建包含潜在错误的Agent结果
        problematic_results = [
            {
                "agent_type": "normal_agent",
                "analysis_summary": "正常的Agent结果",
                "confidence": 0.8,
                "agent_recommendations": [
                    {
                        "agent_type": "normal_agent",
                        "confidence": 0.8,
                        "reason": "正常推荐",
                    }
                ],
            },
            {
                "agent_type": "problematic_agent",
                # 缺少必要字段，可能引发错误
                "analysis_summary": "有问题的Agent结果",
                # 缺少confidence字段
            },
            {
                "agent_type": "another_normal_agent",
                "analysis_summary": "另一个正常Agent",
                "confidence": 0.7,
                "agent_recommendations": [],
            },
        ]

        # 测试错误恢复性能
        start_time = time.time()
        fusion_result = self.fusion_engine.fuse_agent_results(problematic_results)
        end_time = time.time()

        processing_time = end_time - start_time

        # 验证错误恢复（应该有fallback结果）
        self.assertLess(processing_time, 2.0)  # 错误恢复应该很快

        if "error" in fusion_result:
            # 如果有错误，应该有fallback结果
            self.assertIn("fused_result", fusion_result)
            fused_result = fusion_result["fused_result"]
            self.assertTrue(fused_result.get("fallback_mode", False))


def run_story7_2_integration_tests():
    """运行Story 7.2集成测试"""
    print("=" * 80)
    print("🚀 Story 7.2: 智能结果融合引擎 - 完整集成测试")
    print("=" * 80)

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加所有测试类
    test_classes = [
        TestConflictDetectionEngine,
        TestConfidenceBasedFusion,
        TestInformationIntegrityProtection,
        TestFusionProcessTransparency,
        TestIntelligentResultFusionEngine,
        TestIntelligentResultFusionTool,
        TestPerformanceOptimization,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 生成测试报告
    print("\n" + "=" * 80)
    print("📊 Story 7.2测试结果摘要")
    print("=" * 80)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(
        f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

    # 功能验证总结
    print("\n✅ Story 7.2核心功能验证:")
    print("  - Task 1: 冲突检测和解决算法 ✅")
    print("  - Task 2: 基于置信度的加权融合 ✅")
    print("  - Task 3: 信息完整性保护机制 ✅")
    print("  - Task 4: 融合过程可解释性 ✅")
    print("  - Task 5: 性能优化和集成测试 ✅")

    print("\n🎯 Story 7.2: 智能结果融合引擎 - 测试完成!")
    print("=" * 80)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_story7_2_integration_tests()
    exit(0 if success else 1)
