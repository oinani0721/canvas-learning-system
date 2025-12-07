"""
模型兼容性适配器单元测试

测试覆盖：
- 模型检测功能
- 各模型处理器功能
- 黄色节点检测
- Canvas操作处理
- 性能基准测试

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-28
"""

import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from canvas_utils.model_adapter import (
    BaseModelProcessor,
    DefaultProcessor,
    GLMProcessor,
    ModelCompatibilityAdapter,
    ModelDetectionResult,
    ModelDetector,
    NodeDetectionResult,
    OpusProcessor,
    ProcessingConfig,
    SonnetProcessor,
    create_adapter,
    detect_current_model,
    get_processor_for_model,
)


class TestModelDetector(unittest.TestCase):
    """测试模型检测器"""

    def setUp(self):
        self.detector = ModelDetector()

    def test_detect_model_from_api_response(self):
        """测试从API响应检测模型"""
        response = {"model": "opus-4.1"}
        result = self.detector.detect_model(response)

        self.assertIsInstance(result, ModelDetectionResult)
        self.assertEqual(result.model_name, "opus-4.1")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.detection_method, "api_response")
        self.assertGreaterEqual(result.processing_time_ms, 0)

    def test_detect_model_by_pattern(self):
        """测试通过响应模式检测模型"""
        # Opus 4.1 特征
        response = {
            "content": "这是一个详细的analysis内容，长度超过1000字符，" * 10,
            "usage": {"completion_tokens": 2500}
        }
        result = self.detector.detect_model(response)

        self.assertEqual(result.model_name, "opus-4.1")
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(result.detection_method, "pattern_matching")

    def test_detect_glm_by_chinese_content(self):
        """测试通过中文内容检测GLM"""
        response = {
            "content": "这是中文内容，包含很多汉字和中文表达方式"
        }
        result = self.detector.detect_model(response)

        self.assertEqual(result.model_name, "glm-4.6")
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(result.detection_method, "pattern_matching")

    def test_detect_sonnet_by_short_content(self):
        """测试通过短内容检测Sonnet"""
        response = {
            "content": "Short concise response",
            "usage": {"completion_tokens": 300}
        }
        result = self.detector.detect_model(response)

        self.assertEqual(result.model_name, "sonnet-3.5")
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(result.detection_method, "pattern_matching")

    def test_detect_model_from_env(self):
        """测试从环境变量检测模型"""
        with patch.dict(os.environ, {'CLAUDE_MODEL': 'claude-opus-4.1'}):
            result = self.detector.detect_model()

            self.assertEqual(result.model_name, "opus-4.1")
            self.assertEqual(result.confidence, 0.8)
            self.assertEqual(result.detection_method, "environment_variable")

    def test_normalize_model_name(self):
        """测试模型名称标准化"""
        test_cases = [
            ("opus-4.1", "opus-4.1"),
            ("claude-opus-4.1", "opus-4.1"),
            ("OPUS", "opus-4.1"),
            ("glm-4.6", "glm-4.6"),
            ("chatglm-4.6", "glm-4.6"),
            ("sonnet-3.5", "sonnet-3.5"),
            ("claude-3.5-sonnet", "sonnet-3.5"),
            ("unknown", "default"),
            ("", "default")
        ]

        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.detector._normalize_model_name(input_name)
                self.assertEqual(result, expected)


class TestOpusProcessor(unittest.TestCase):
    """测试Opus 4.1处理器"""

    def setUp(self):
        self.processor = OpusProcessor()
        self.sample_canvas = {
            "nodes": [],
            "edges": []
        }

    def test_config_initialization(self):
        """测试配置初始化"""
        config = self.processor.get_optimized_config()

        self.assertTrue(config.use_fuzzy_matching)
        self.assertEqual(config.confidence_threshold, 0.95)
        self.assertEqual(config.retry_count, 3)
        self.assertEqual(config.balance_mode, "quality")

    def test_detect_yellow_nodes_opus_enhanced(self):
        """测试Opus增强的黄色节点检测"""
        self.sample_canvas["nodes"] = [
            {
                "id": "yellow-1",
                "type": "text",
                "text": "我认为逆否命题是...",
                "color": "6"
            },
            {
                "id": "yellow-2",
                "type": "text",
                "text": "My understanding is...",
                "color": "6"
            },
            {
                "id": "yellow-3",
                "type": "text",
                "text": "简而言之",
                "color": "6"
            },
            {
                "id": "red-1",
                "type": "text",
                "text": "红色节点",
                "color": "1"
            }
        ]

        result = self.processor.detect_yellow_nodes(self.sample_canvas)

        self.assertIsInstance(result, NodeDetectionResult)
        self.assertEqual(result.detection_method, "opus_enhanced")
        self.assertEqual(len(result.nodes), 3)
        self.assertGreaterEqual(result.confidence_score, 0.95)
        self.assertEqual(result.false_positive_rate, 0.001)

    def test_is_yellow_node_opus(self):
        """测试Opus黄色节点判断逻辑"""
        # 包含个人理解特征的节点
        node_with_understanding = {
            "id": "test-1",
            "text": "我认为这个概念很重要",
            "color": "6"
        }
        self.assertTrue(self.processor._is_yellow_node_opus(node_with_understanding))

        # 长度合适的节点
        node_with_length = {
            "id": "test-2",
            "text": "这是我的理解内容，长度适中",
            "color": "6"
        }
        self.assertTrue(self.processor._is_yellow_node_opus(node_with_length))

        # 不符合条件的节点
        node_invalid = {
            "id": "test-3",
            "text": "",
            "color": "6"
        }
        self.assertFalse(self.processor._is_yellow_node_opus(node_invalid))

    def test_process_canvas_operation(self):
        """测试Canvas操作处理"""
        result = self.processor.process_canvas_operation(
            "intelligent_parallel",
            "test.canvas",
            options={"optimize": True}
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "opus-4.1")
        self.assertIn("canvas_validated", result)

    def test_batch_processing(self):
        """测试批处理功能"""
        items = ["item1", "item2", "item3", "item4", "item5"]
        result = self.processor._process_batch(items)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(items))
        self.assertTrue(all(item.startswith("processed_") for item in result))


class TestGLMProcessor(unittest.TestCase):
    """测试GLM 4.6处理器"""

    def setUp(self):
        self.processor = GLMProcessor()

    def test_config_initialization(self):
        """测试配置初始化"""
        config = self.processor.get_optimized_config()

        self.assertEqual(config.batch_size, 20)
        self.assertEqual(config.parallel_limit, 10)  # GLM并行限制是10
        self.assertEqual(config.balance_mode, "speed")

    def test_detect_yellow_nodes_glm(self):
        """测试GLM黄色节点检测"""
        canvas_data = {
            "nodes": [
                {
                    "id": "yellow-1",
                    "type": "text",
                    "text": "黄色节点内容",
                    "color": "6"
                },
                {
                    "id": "red-1",
                    "type": "text",
                    "text": "红色节点",
                    "color": "1"
                }
            ]
        }

        result = self.processor.detect_yellow_nodes(canvas_data)

        self.assertEqual(result.detection_method, "glm_optimized")
        self.assertEqual(len(result.nodes), 1)
        self.assertEqual(result.confidence_score, 0.90)

    def test_intelligent_parallel_processing(self):
        """测试智能并行处理"""
        result = self.processor._process_intelligent_parallel(
            "test.canvas",
            {"parallel": True}
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "glm-4.6")
        self.assertTrue(result["batch_processed"])


class TestSonnetProcessor(unittest.TestCase):
    """测试Sonnet处理器"""

    def setUp(self):
        self.processor = SonnetProcessor()

    def test_config_initialization(self):
        """测试配置初始化"""
        config = self.processor.get_optimized_config()

        self.assertEqual(config.balance_mode, "quality")
        self.assertEqual(config.batch_size, 15)
        self.assertEqual(config.parallel_limit, 5)

    def test_detect_yellow_nodes_sonnet(self):
        """测试Sonnet黄色节点检测"""
        canvas_data = {
            "nodes": [
                {
                    "id": "yellow-1",
                    "type": "text",
                    "text": "这是一个较长的理解内容，超过10个字符",
                    "color": "6"
                },
                {
                    "id": "yellow-2",
                    "type": "text",
                    "text": "短",
                    "color": "6"
                }
            ]
        }

        result = self.processor.detect_yellow_nodes(canvas_data)

        self.assertEqual(result.detection_method, "sonnet_balanced")
        self.assertEqual(len(result.nodes), 1)  # 只有长文本被检测到
        self.assertEqual(result.confidence_score, 0.92)


class TestDefaultProcessor(unittest.TestCase):
    """测试默认处理器"""

    def setUp(self):
        self.processor = DefaultProcessor()

    def test_config_initialization(self):
        """测试配置初始化"""
        config = self.processor.get_optimized_config()

        self.assertEqual(config.balance_mode, "safe")
        self.assertEqual(config.batch_size, 5)
        self.assertEqual(config.parallel_limit, 2)

    def test_detect_yellow_nodes_default(self):
        """测试默认黄色节点检测"""
        canvas_data = {
            "nodes": [
                {
                    "id": "yellow-1",
                    "type": "text",
                    "text": "黄色节点",
                    "color": "6"
                }
            ]
        }

        result = self.processor.detect_yellow_nodes(canvas_data)

        self.assertEqual(result.detection_method, "default_basic")
        self.assertEqual(len(result.nodes), 1)
        self.assertEqual(result.confidence_score, 0.75)


class TestModelCompatibilityAdapter(unittest.TestCase):
    """测试模型兼容性适配器主类"""

    def setUp(self):
        self.adapter = ModelCompatibilityAdapter()

    def test_initialization(self):
        """测试初始化"""
        self.assertIn("opus-4.1", self.adapter.model_processors)
        self.assertIn("glm-4.6", self.adapter.model_processors)
        self.assertIn("sonnet-3.5", self.adapter.model_processors)
        self.assertIn("default", self.adapter.model_processors)

    def test_detect_model_integration(self):
        """测试模型检测集成"""
        response = {"model": "opus-4.1"}
        result = self.adapter.detect_model(response)

        self.assertEqual(result.model_name, "opus-4.1")
        self.assertEqual(self.adapter.current_model, "opus-4.1")
        self.assertIsInstance(self.adapter.current_processor, OpusProcessor)

    def test_get_processor(self):
        """测试获取处理器"""
        # 测试获取特定模型处理器
        processor = self.adapter.get_processor("glm-4.6")
        self.assertIsInstance(processor, GLMProcessor)

        # 测试获取当前模型处理器
        self.adapter.current_model = "sonnet-3.5"
        processor = self.adapter.get_processor()
        self.assertIsInstance(processor, SonnetProcessor)

        # 测试未知模型返回默认处理器
        processor = self.adapter.get_processor("unknown-model")
        self.assertIsInstance(processor, DefaultProcessor)

    def test_process_canvas_operation(self):
        """测试Canvas操作处理"""
        # 模拟响应
        response = {"model": "opus-4.1"}

        result = self.adapter.process_canvas_operation(
            "intelligent_parallel",
            "test.canvas",
            response=response,
            options={"test": True}
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)

    def test_detect_yellow_nodes(self):
        """测试黄色节点检测"""
        canvas_data = {
            "nodes": [
                {
                    "id": "yellow-1",
                    "type": "text",
                    "text": "我认为这是一个理解",
                    "color": "6"
                }
            ]
        }

        result = self.adapter.detect_yellow_nodes(canvas_data)

        self.assertIsInstance(result, NodeDetectionResult)
        self.assertGreater(len(result.nodes), 0)

    def test_get_model_stats(self):
        """测试获取模型统计"""
        # 执行一些操作
        self.adapter.process_canvas_operation("test_op")
        self.adapter.process_canvas_operation("test_op")

        stats = self.adapter.get_model_stats()

        self.assertIn("current_model", stats)
        self.assertIn("processors", stats)
        self.assertIn("opus-4.1", stats["processors"])

    def test_register_custom_processor(self):
        """测试注册自定义处理器"""
        class CustomProcessor(BaseModelProcessor):
            def detect_yellow_nodes(self, canvas_data):
                return NodeDetectionResult([], 0.8, "custom")

            def process_canvas_operation(self, operation_type, *args, **kwargs):
                return {"custom": True}

            def get_optimized_config(self):
                return ProcessingConfig()

        custom_processor = CustomProcessor()
        self.adapter.register_custom_processor("custom-model", custom_processor)

        self.assertIn("custom-model", self.adapter.model_processors)
        self.assertEqual(
            self.adapter.get_processor("custom-model"),
            custom_processor
        )

    def test_get_supported_models(self):
        """测试获取支持的模型列表"""
        models = self.adapter.get_supported_models()

        self.assertIsInstance(models, list)
        self.assertIn("opus-4.1", models)
        self.assertIn("glm-4.6", models)
        self.assertIn("sonnet-3.5", models)
        self.assertIn("default", models)


class TestPerformanceBenchmarks(unittest.TestCase):
    """性能基准测试"""

    def setUp(self):
        self.adapter = ModelCompatibilityAdapter()
        # 创建测试Canvas数据
        self.test_canvas = {
            "nodes": [
                {
                    "id": f"node-{i}",
                    "type": "text",
                    "text": f"我认为这是第{i}个节点的理解内容",
                    "color": "6"
                }
                for i in range(100)
            ]
        }

    def test_model_detection_performance(self):
        """测试模型检测性能"""
        response = {"model": "opus-4.1"}

        start_time = time.time()
        for _ in range(100):
            self.adapter.detect_model(response)
        end_time = time.time()

        avg_time = (end_time - start_time) / 100 * 1000  # 转换为毫秒

        # 验证平均检测时间 < 100ms
        self.assertLess(avg_time, 100, f"模型检测平均时间 {avg_time:.2f}ms 超过100ms")

    def test_yellow_node_detection_performance(self):
        """测试黄色节点检测性能"""
        processors = [
            OpusProcessor(),
            GLMProcessor(),
            SonnetProcessor(),
            DefaultProcessor()
        ]

        for processor in processors:
            with self.subTest(processor=processor.__class__.__name__):
                start_time = time.time()
                result = processor.detect_yellow_nodes(self.test_canvas)
                end_time = time.time()

                processing_time = (end_time - start_time) * 1000  # 转换为毫秒

                # 验证处理时间 < 50ms
                self.assertLess(
                    processing_time,
                    50,
                    f"{processor.__class__.__name__} 处理时间 {processing_time:.2f}ms 超过50ms"
                )

    def test_concurrent_processing(self):
        """测试并发处理性能"""
        import threading

        results = []
        errors = []

        def worker():
            try:
                result = self.adapter.process_canvas_operation(
                    "batch_processing",
                    list(range(10))
                )
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 启动10个并发线程
        threads = []
        start_time = time.time()

        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        end_time = time.time()

        # 验证没有错误
        self.assertEqual(len(errors), 0, f"并发处理出现错误: {errors}")
        self.assertEqual(len(results), 10, "并发处理结果数量不正确")

        # 验证总处理时间合理
        total_time = end_time - start_time
        self.assertLess(total_time, 5, f"并发处理总时间 {total_time:.2f}s 过长")


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""

    def test_create_adapter(self):
        """测试创建适配器"""
        adapter = create_adapter()
        self.assertIsInstance(adapter, ModelCompatibilityAdapter)

    def test_detect_current_model(self):
        """测试检测当前模型"""
        with patch.dict(os.environ, {'CLAUDE_MODEL': 'opus-4.1'}):
            model = detect_current_model()
            self.assertEqual(model, "opus-4.1")

    def test_get_processor_for_model(self):
        """测试获取模型处理器"""
        processor = get_processor_for_model("glm-4.6")
        self.assertIsInstance(processor, GLMProcessor)


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    def setUp(self):
        self.adapter = ModelCompatibilityAdapter()

    def test_invalid_canvas_data(self):
        """测试无效Canvas数据处理"""
        # 测试空数据
        result = self.adapter.detect_yellow_nodes({})
        self.assertEqual(len(result.nodes), 0)

        # 测试非字典数据
        with self.assertRaises(Exception):
            self.adapter.detect_yellow_nodes("invalid")

    def test_missing_model_in_response(self):
        """测试响应中缺少模型信息"""
        response = {"content": "test content"}
        result = self.adapter.detect_model(response)

        # 应该回退到默认检测
        self.assertIsNotNone(result.model_name)
        self.assertGreater(result.confidence, 0)

    def test_processor_error_handling(self):
        """测试处理器错误处理"""
        # 使用不存在的操作类型
        result = self.adapter.process_canvas_operation("unknown_operation")

        # 默认处理器应该能够处理
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    # 运行所有测试
    unittest.main(verbosity=2)
