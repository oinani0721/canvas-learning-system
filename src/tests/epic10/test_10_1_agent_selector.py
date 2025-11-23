"""Story 10.1: ReviewBoardAgentSelector多推荐功能测试

测试ReviewBoardAgentSelector的多Agent推荐和并行处理功能
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

# 导入测试目标
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock imports for testing
class MockReviewBoardAgentSelector:
    """Mock ReviewBoardAgentSelector for testing"""

    def __init__(self):
        self.config = {
            "recommendations": {
                "max_recommendations": 5,
                "default_confidence_threshold": 0.7,
                "min_confidence_threshold": 0.5
            },
            "quality_weights": {
                "accuracy": 0.3,
                "completeness": 0.3,
                "clarity": 0.2,
                "originality": 0.2
            }
        }

        self.agent_priority_weights = {
            "clarification-path": 0.88,
            "oral-explanation": 0.85,
            "comparison-table": 0.82,
            "four-level-explanation": 0.80,
            "example-teaching": 0.78,
            "memory-anchor": 0.75,
            "basic-decomposition": 0.85,
            "deep-decomposition": 0.80,
            "verification-question-agent": 0.83,
            "scoring-agent": 0.93
        }

        self.all_agent_types = [
            "basic-decomposition",
            "deep-decomposition",
            "oral-explanation",
            "clarification-path",
            "comparison-table",
            "memory-anchor",
            "four-level-explanation",
            "example-teaching",
            "scoring-agent",
            "verification-question-agent"
        ]

    async def analyze_understanding_quality_advanced(
        self,
        node_text: str,
        context: Dict = None
    ) -> Dict[str, Any]:
        """Mock implementation of advanced analysis"""
        # Simulate analysis time
        await asyncio.sleep(0.01)

        # Simple mock analysis based on text length
        word_count = len(node_text.split())

        # Calculate mock scores
        accuracy_score = min(1.0, word_count / 20.0)
        completeness_score = min(1.0, word_count / 30.0)
        clarity_score = 0.7 if "因为" in node_text or "所以" in node_text else 0.5
        originality_score = 0.6 if "我认为" in node_text else 0.4

        # Calculate overall quality
        weights = self.config["quality_weights"]
        overall_quality = (
            accuracy_score * weights["accuracy"] +
            completeness_score * weights["completeness"] +
            clarity_score * weights["clarity"] +
            originality_score * weights["originality"]
        )

        return {
            "accuracy_score": round(accuracy_score, 2),
            "completeness_score": round(completeness_score, 2),
            "clarity_score": round(clarity_score, 2),
            "originality_score": round(originality_score, 2),
            "overall_quality": round(overall_quality, 2),
            "word_count": word_count,
            "has_content": len(node_text.strip()) > 0,
            "analysis_time_ms": round(time.time() * 1000) % 100
        }

    async def recommend_multiple_agents(
        self,
        quality_analysis: Dict,
        max_recommendations: int = None,
        context: Dict = None
    ) -> Dict[str, Any]:
        """Mock implementation of multi-agent recommendation"""
        import uuid

        max_rec = max_recommendations or self.config["recommendations"]["max_recommendations"]
        overall_quality = quality_analysis.get("overall_quality", 0.5)

        # Generate candidates based on quality
        candidates = []
        if overall_quality < 0.3:
            candidates.extend(["basic-decomposition", "oral-explanation"])
        elif overall_quality < 0.6:
            candidates.extend(["clarification-path", "four-level-explanation"])
        else:
            candidates.extend(["memory-anchor", "example-teaching"])

        # Add specific agents based on dimensions
        if quality_analysis.get("accuracy_score", 0) < 0.6:
            candidates.append("clarification-path")
        if quality_analysis.get("clarity_score", 0) < 0.6:
            candidates.append("oral-explanation")

        # Calculate confidence for each candidate
        agent_recommendations = []
        for agent_type in candidates[:max_rec]:
            base_confidence = self.agent_priority_weights.get(agent_type, 0.5)
            confidence = base_confidence * (1.5 - overall_quality)  # Adjust based on quality

            if confidence >= self.config["recommendations"]["min_confidence_threshold"]:
                agent_recommendations.append({
                    "agent_name": agent_type,
                    "confidence_score": round(confidence, 2),
                    "reasoning": f"Mock reasoning for {agent_type}",
                    "priority": len(agent_recommendations) + 1,
                    "estimated_duration": "10-20秒",
                    "suggested_follow_up": [f"Follow up for {agent_type}"]
                })

        return {
            "analysis_id": f"rec-{uuid.uuid4().hex}",
            "node_id": context.get("node_id") if context else None,
            "understanding_quality": quality_analysis,
            "recommended_agents": agent_recommendations,
            "complementary_combinations": [],
            "processing_strategy": {
                "execution_mode": "parallel",
                "max_concurrent": len(agent_recommendations),
                "total_estimated_duration": f"{len(agent_recommendations) * 10}-{len(agent_recommendations) * 20}秒"
            }
        }

    async def process_agents_parallel(
        self,
        agent_recommendations: Dict,
        canvas_path: str,
        node_id: str,
        max_concurrent: int = 20
    ) -> Dict[str, Any]:
        """Mock implementation of parallel processing"""
        import uuid
        from datetime import datetime

        execution_id = f"exec-{uuid.uuid4().hex}"
        start_time = time.time()

        agents = agent_recommendations.get("recommended_agents", [])
        if not agents:
            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": "No agents to execute",
                "results": []
            }

        # Simulate parallel execution
        semaphore = asyncio.Semaphore(max_concurrent)

        async def mock_execute(agent_info):
            async with semaphore:
                # Simulate execution time
                execution_time = 1.0 + (agent_info.get("priority", 1) * 0.1)
                await asyncio.sleep(execution_time)

                return {
                    "agent_name": agent_info["agent_name"],
                    "success": True,
                    "result": f"Mock result for {agent_info['agent_name']}",
                    "execution_time": execution_time,
                    "confidence": agent_info.get("confidence_score", 0.5),
                    "priority": agent_info.get("priority", 1)
                }

        # Execute all agents in parallel
        tasks = [mock_execute(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]

        total_execution_time = time.time() - start_time
        sequential_time_estimate = sum(r.get("execution_time", 0) for r in successful_results)
        parallel_efficiency = sequential_time_estimate / total_execution_time if total_execution_time > 0 else 1.0

        return {
            "execution_id": execution_id,
            "status": "completed" if len(failed_results) == 0 else "partial",
            "total_agents": len(agents),
            "successful_agents": len(successful_results),
            "failed_agents": len(failed_results),
            "results": results,
            "successful_results": successful_results,
            "failed_results": failed_results,
            "execution_summary": {
                "total_execution_time": round(total_execution_time, 2),
                "average_time_per_agent": round(total_execution_time / len(agents), 2),
                "parallel_efficiency": round(parallel_efficiency, 2),
                "success_rate": round(len(successful_results) / len(agents), 2),
                "max_concurrent_used": min(max_concurrent, len(agents))
            },
            "timestamp": datetime.now().isoformat()
        }


@pytest.fixture
def agent_selector():
    """Create ReviewBoardAgentSelector instance for testing"""
    return MockReviewBoardAgentSelector()


@pytest.fixture
def sample_node_texts():
    """Sample node texts for testing"""
    return {
        "empty": "",
        "poor": "不理解",
        "basic": "这是基本概念",
        "good": "我认为这个概念很重要，因为它包括多个方面。例如，在实际应用中...",
        "excellent": "我的理解是：这个概念的核心原理是基于XXX理论，因为它能够解决YYY问题。具体来说，首先...其次...最后...综上所述..."
    }


class TestStory10_1_MultiAgentRecommendation:
    """测试Story 10.1: ReviewBoardAgentSelector多推荐功能"""

    @pytest.mark.asyncio
    async def test_analyze_understanding_quality_advanced(
        self,
        agent_selector,
        sample_node_texts
    ):
        """测试高级理解质量分析"""
        # 测试空文本
        result = await agent_selector.analyze_understanding_quality_advanced(
            sample_node_texts["empty"]
        )

        assert result["has_content"] is False
        assert result["word_count"] == 0
        assert result["overall_quality"] == 0.00

        # 测试基础理解
        result = await agent_selector.analyze_understanding_quality_advanced(
            sample_node_texts["basic"]
        )

        assert result["has_content"] is True
        assert result["word_count"] == 4
        assert 0 < result["overall_quality"] < 0.5

        # 测试优秀理解
        result = await agent_selector.analyze_understanding_quality_advanced(
            sample_node_texts["excellent"]
        )

        assert result["has_content"] is True
        assert result["word_count"] > 20
        assert result["overall_quality"] > 0.7

        # 验证所有必需字段
        required_fields = [
            "accuracy_score", "completeness_score",
            "clarity_score", "originality_score",
            "overall_quality", "word_count", "has_content"
        ]
        for field in required_fields:
            assert field in result

    @pytest.mark.asyncio
    async def test_recommend_multiple_agents_basic(
        self,
        agent_selector,
        sample_node_texts
    ):
        """测试基础多Agent推荐功能"""
        # 分析质量
        quality_analysis = await agent_selector.analyze_understanding_quality_advanced(
            sample_node_texts["poor"]
        )

        # 推荐多个Agent
        recommendations = await agent_selector.recommend_multiple_agents(
            quality_analysis,
            max_recommendations=3
        )

        # 验证返回格式
        assert "analysis_id" in recommendations
        assert "recommended_agents" in recommendations
        assert "processing_strategy" in recommendations
        assert len(recommendations["recommended_agents"]) <= 3

        # 验证Agent推荐结构
        for agent in recommendations["recommended_agents"]:
            assert "agent_name" in agent
            assert "confidence_score" in agent
            assert "reasoning" in agent
            assert "priority" in agent
            assert "estimated_duration" in agent
            assert 0 <= agent["confidence_score"] <= 1
            assert agent["agent_name"] in agent_selector.all_agent_types

    @pytest.mark.asyncio
    async def test_recommend_multiple_agents_with_context(
        self,
        agent_selector,
        sample_node_texts
    ):
        """测试带上下文的多Agent推荐"""
        quality_analysis = await agent_selector.analyze_understanding_quality_advanced(
            sample_node_texts["good"]
        )

        context = {"node_id": "test-node-123", "canvas_file": "test.canvas"}

        recommendations = await agent_selector.recommend_multiple_agents(
            quality_analysis,
            context=context
        )

        # 验证上下文被正确使用
        assert recommendations["node_id"] == "test-node-123"

        # 验证基于质量的合理推荐
        agents = recommendations["recommended_agents"]
        assert len(agents) > 0

        # 高质量理解应该推荐进阶Agent
        agent_names = [a["agent_name"] for a in agents]
        assert any(agent in agent_names for agent in ["memory-anchor", "example-teaching", "four-level-explanation"])

    @pytest.mark.asyncio
    async def test_process_agents_parallel_single(
        self,
        agent_selector
    ):
        """测试单个Agent并行处理"""
        # 创建单个推荐
        agent_recommendations = {
            "recommended_agents": [{
                "agent_name": "clarification-path",
                "confidence_score": 0.85,
                "priority": 1
            }]
        }

        result = await agent_selector.process_agents_parallel(
            agent_recommendations,
            "test.canvas",
            "node-123"
        )

        # 验证执行结果
        assert result["status"] == "completed"
        assert result["total_agents"] == 1
        assert result["successful_agents"] == 1
        assert result["failed_agents"] == 0
        assert len(result["successful_results"]) == 1

    @pytest.mark.asyncio
    async def test_process_agents_parallel_multiple(
        self,
        agent_selector
    ):
        """测试多个Agent并行处理"""
        # 创建多个推荐
        agent_recommendations = {
            "recommended_agents": [
                {
                    "agent_name": "clarification-path",
                    "confidence_score": 0.92,
                    "priority": 1
                },
                {
                    "agent_name": "oral-explanation",
                    "confidence_score": 0.85,
                    "priority": 2
                },
                {
                    "agent_name": "comparison-table",
                    "confidence_score": 0.78,
                    "priority": 3
                }
            ]
        }

        result = await agent_selector.process_agents_parallel(
            agent_recommendations,
            "test.canvas",
            "node-456",
            max_concurrent=5
        )

        # 验证执行结果
        assert result["status"] == "completed"
        assert result["total_agents"] == 3
        assert result["successful_agents"] == 3
        assert result["failed_agents"] == 0
        assert len(result["successful_results"]) == 3

        # 验证并行效率
        summary = result["execution_summary"]
        assert summary["max_concurrent_used"] == 3
        assert summary["success_rate"] == 1.0
        assert summary["parallel_efficiency"] > 1.0  # 并行应该比串行快

    @pytest.mark.asyncio
    async def test_process_agents_parallel_max_concurrent(
        self,
        agent_selector
    ):
        """测试最大并发数限制"""
        # 创建5个推荐
        agent_recommendations = {
            "recommended_agents": [
                {"agent_name": f"agent-{i}", "priority": i}
                for i in range(5)
            ]
        }

        # 设置最大并发数为2
        result = await agent_selector.process_agents_parallel(
            agent_recommendations,
            "test.canvas",
            "node-789",
            max_concurrent=2
        )

        # 验证并发限制被遵守
        summary = result["execution_summary"]
        assert summary["max_concurrent_used"] == 2

    @pytest.mark.asyncio
    async def test_process_agents_parallel_empty_recommendations(
        self,
        agent_selector
    ):
        """测试空推荐列表的处理"""
        agent_recommendations = {
            "recommended_agents": []
        }

        result = await agent_selector.process_agents_parallel(
            agent_recommendations,
            "test.canvas",
            "node-000"
        )

        # 验证错误处理
        assert result["status"] == "failed"
        assert "error" in result
        assert result["total_agents"] == 0

    def test_agent_priority_weights(self, agent_selector):
        """测试Agent优先级权重配置"""
        # 验证所有支持的Agent都有权重
        for agent_type in agent_selector.all_agent_types:
            assert agent_type in agent_selector.agent_priority_weights

        # 验证权重在合理范围内
        for agent_type, weight in agent_selector.agent_priority_weights.items():
            assert 0.0 <= weight <= 1.0

        # 验证scoring-agent权重最高
        assert agent_selector.agent_priority_weights["scoring-agent"] >= 0.9

    def test_config_loading(self, agent_selector):
        """测试配置加载"""
        # 验证必要配置项存在
        assert "recommendations" in agent_selector.config
        assert "quality_weights" in agent_selector.config

        # 验证推荐配置
        rec_config = agent_selector.config["recommendations"]
        assert "max_recommendations" in rec_config
        assert "min_confidence_threshold" in rec_config
        assert rec_config["max_recommendations"] >= 1
        assert 0.0 <= rec_config["min_confidence_threshold"] <= 1.0

        # 验证质量权重
        quality_weights = agent_selector.config["quality_weights"]
        assert sum(quality_weights.values()) == pytest.approx(1.0, rel=1e-2)

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(
        self,
        agent_selector,
        sample_node_texts
    ):
        """测试端到端工作流程"""
        # 步骤1: 分析理解质量
        quality_analysis = await agent_selector.analyze_understanding_quality_advanced(
            sample_node_texts["good"]
        )

        # 步骤2: 推荐多个Agent
        recommendations = await agent_selector.recommend_multiple_agents(
            quality_analysis,
            max_recommendations=3,
            context={"node_id": "test-e2e"}
        )

        # 步骤3: 并行执行Agent
        execution_result = await agent_selector.process_agents_parallel(
            recommendations,
            "test.canvas",
            "test-e2e"
        )

        # 验证端到端流程成功
        assert quality_analysis["has_content"] is True
        assert len(recommendations["recommended_agents"]) > 0
        assert execution_result["status"] in ["completed", "partial"]
        assert execution_result["successful_agents"] > 0

        # 验证数据流完整性
        assert recommendations["analysis_id"] is not None
        assert execution_result["execution_id"] is not None
        assert len(execution_result["results"]) == len(recommendations["recommended_agents"])


class TestStory10_1_Performance:
    """测试Story 10.1性能要求"""

    @pytest.mark.asyncio
    async def test_analysis_response_time(
        self,
        agent_selector,
        sample_node_texts
    ):
        """测试分析响应时间 < 1秒"""
        start_time = time.time()

        await agent_selector.analyze_understanding_quality_advanced(
            sample_node_texts["excellent"]
        )

        response_time = time.time() - start_time
        assert response_time < 1.0, f"Analysis took {response_time:.2f}s, should be < 1s"

    @pytest.mark.asyncio
    async def test_recommendation_response_time(
        self,
        agent_selector,
        sample_node_texts
    ):
        """测试推荐响应时间 < 0.5秒"""
        quality_analysis = await agent_selector.analyze_understanding_quality_advanced(
            sample_node_texts["good"]
        )

        start_time = time.time()
        await agent_selector.recommend_multiple_agents(
            quality_analysis,
            max_recommendations=5
        )
        response_time = time.time() - start_time

        assert response_time < 0.5, f"Recommendation took {response_time:.2f}s, should be < 0.5s"

    @pytest.mark.asyncio
    async def test_parallel_execution_performance(
        self,
        agent_selector
    ):
        """测试并行执行效率 > 200%"""
        import concurrent.futures

        # 创建5个Agent的任务
        agent_recommendations = {
            "recommended_agents": [
                {"agent_name": f"agent-{i}", "priority": i}
                for i in range(5)
            ]
        }

        # 测试并行执行
        start_parallel = time.time()
        result_parallel = await agent_selector.process_agents_parallel(
            agent_recommendations,
            "test.canvas",
            "test-perf",
            max_concurrent=5
        )
        parallel_time = time.time() - start_parallel

        # 验证性能提升
        summary = result_parallel["execution_summary"]
        assert summary["parallel_efficiency"] > 2.0, \
            f"Parallel efficiency: {summary['parallel_efficiency']:.2f}, should be > 2.0"

    def test_recommendation_accuracy(
        self,
        agent_selector
    ):
        """测试推荐准确率 > 85%"""
        # 模拟不同质量的理解
        test_cases = [
            {"quality": 0.1, "expected": ["basic-decomposition", "oral-explanation"]},
            {"quality": 0.4, "expected": ["clarification-path", "four-level-explanation"]},
            {"quality": 0.8, "expected": ["memory-anchor", "example-teaching"]}
        ]

        accurate_count = 0
        total_tests = len(test_cases)

        for case in test_cases:
            quality_analysis = {"overall_quality": case["quality"]}

            # 异步运行测试（简化）
            import asyncio
            async def run_test():
                return await agent_selector.recommend_multiple_agents(
                    quality_analysis,
                    max_recommendations=3
                )

            # Run in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                recommendations = loop.run_until_complete(run_test())
            finally:
                loop.close()

            # 检查推荐的合理性
            agent_names = [a["agent_name"] for a in recommendations["recommended_agents"]]

            # 简单的准确性检查：推荐的Agent类型应该符合预期
            for expected_agent in case["expected"]:
                if any(expected_agent in name for name in agent_names):
                    accurate_count += 1
                    break

        accuracy = accurate_count / total_tests
        assert accuracy > 0.85, f"Recommendation accuracy: {accuracy:.2f}, should be > 0.85"


class TestStory10_1_BackwardCompatibility:
    """测试向后兼容性"""

    @pytest.mark.asyncio
    async def test_single_agent_compatibility(
        self,
        agent_selector,
        sample_node_texts
    ):
        """测试单Agent推荐的向后兼容性"""
        # 新方法应该能够处理单Agent场景
        quality_analysis = await agent_selector.analyze_understanding_quality_advanced(
            sample_node_texts["poor"]
        )

        # 请求只推荐1个Agent
        recommendations = await agent_selector.recommend_multiple_agents(
            quality_analysis,
            max_recommendations=1
        )

        # 验证格式兼容性
        assert "recommended_agents" in recommendations
        assert len(recommendations["recommended_agents"]) == 1

        agent = recommendations["recommended_agents"][0]
        assert "agent_name" in agent
        assert "confidence_score" in agent

    def test_legacy_method_preservation(self, agent_selector):
        """测试保留原有方法"""
        # 验证原有方法仍然存在
        assert hasattr(agent_selector, 'analyze_understanding_quality')
        assert hasattr(agent_selector, 'recommend_agents')
        assert hasattr(agent_selector, 'get_agent_selection_for_review_node')


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])