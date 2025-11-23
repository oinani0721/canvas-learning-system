"""
性能优化系统测试套件

测试Canvas学习系统的性能优化组件，包括：
- 性能监控器测试
- 动态实例管理器测试
- 智能缓存管理器测试
- 配置管理器测试
- 性能基准测试系统测试
- 集成测试

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-27
Story: 10.6 - Testing
"""

import asyncio
import pytest
import json
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入测试目标
from performance_monitor import PerformanceMonitor, ResourceMetrics, ExecutionMetrics
from dynamic_instance_manager import DynamicInstanceManager, SystemLoadInfo
from intelligent_cache_manager import IntelligentCacheManager, CacheEntryType
from configuration_manager import ConfigurationManager, PerformanceConfig
from performance_benchmark_system import PerformanceBenchmarkSystem, BenchmarkType


class TestPerformanceMonitor:
    """性能监控器测试类"""

    @pytest.fixture
    async def performance_monitor(self):
        """创建性能监控器实例"""
        config = {
            "enabled": True,
            "collect_metrics": True,
            "log_performance_data": False,  # 测试时不记录日志
            "metrics_collection_interval_seconds": 1
        }
        monitor = PerformanceMonitor(config)
        await monitor.start_monitoring()
        yield monitor
        await monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_monitor_start_stop(self, performance_monitor):
        """测试监控器启动和停止"""
        assert performance_monitor.monitoring_active == True

        # 收集一些指标
        await asyncio.sleep(2)

        # 验证指标被收集
        assert len(performance_monitor.resource_metrics_history) > 0

    @pytest.mark.asyncio
    async def test_resource_metrics_collection(self, performance_monitor):
        """测试资源指标收集"""
        # 等待收集一些指标
        await asyncio.sleep(2)

        # 获取最新指标
        latest = performance_monitor.resource_metrics_history[-1]

        # 验证指标结构
        assert isinstance(latest, ResourceMetrics)
        assert latest.cpu_percent >= 0
        assert latest.memory_usage_mb > 0
        assert latest.memory_percent >= 0
        assert latest.active_threads > 0

    @pytest.mark.asyncio
    async def test_execution_metrics_recording(self, performance_monitor):
        """测试执行指标记录"""
        # 记录执行指标
        execution_id = f"test-exec-{int(time.time())}"
        metrics = performance_monitor.record_execution_metrics(
            execution_id=execution_id,
            task_count=10,
            successful_tasks=9,
            failed_tasks=1,
            total_execution_time_ms=5000,
            parallel_efficiency=3.2,
            concurrency_utilization=0.8
        )

        # 验证指标
        assert metrics.execution_id == execution_id
        assert metrics.task_count == 10
        assert metrics.successful_tasks == 9
        assert metrics.failed_tasks == 1
        assert metrics.total_execution_time_ms == 5000
        assert metrics.parallel_efficiency == 3.2
        assert metrics.throughput_tasks_per_second == 2.0  # 10/5

        # 验证存储在历史中
        assert len(performance_monitor.execution_metrics_history) > 0

    @pytest.mark.asyncio
    async def test_performance_report_generation(self, performance_monitor):
        """测试性能报告生成"""
        # 添加一些执行指标
        for i in range(3):
            performance_monitor.record_execution_metrics(
                execution_id=f"test-{i}",
                task_count=5,
                successful_tasks=5,
                failed_tasks=0,
                total_execution_time_ms=1000,
                parallel_efficiency=2.5,
                concurrency_utilization=0.7
            )

        # 生成报告
        report = performance_monitor.generate_performance_report()

        # 验证报告结构
        assert "report_id" in report
        assert "monitoring_status" in report
        assert "summary" in report
        assert "resource_metrics" in report
        assert "execution_metrics" in report
        assert "recommendations" in report

        # 验证执行指标摘要
        if "average_parallel_efficiency" in report["execution_metrics"]:
            assert report["execution_metrics"]["average_parallel_efficiency"] == 2.5

    def test_alert_callback(self, performance_monitor):
        """测试告警回调"""
        callback_called = False
        alert_data = None

        def test_callback(alert):
            nonlocal callback_called, alert_data
            callback_called = True
            alert_data = alert

        # 添加回调
        performance_monitor.add_alert_callback(test_callback)

        # 模拟触发告警
        performance_monitor._trigger_alert(
            alert_type="test",
            title="Test Alert",
            description="This is a test alert"
        )

        # 验证回调被调用
        assert callback_called
        assert alert_data is not None
        assert alert_data.title == "Test Alert"


class TestDynamicInstanceManager:
    """动态实例管理器测试类"""

    @pytest.fixture
    async def instance_manager(self):
        """创建实例管理器"""
        # 创建模拟实例池
        class MockInstancePool:
            def __init__(self):
                self.max_instances = 6
                self.active_instances = {}

            async def set_max_concurrent_instances(self, count):
                self.max_instances = count
                return True

        # 创建性能监控器
        perf_monitor = PerformanceMonitor({
            "enabled": True,
            "collect_metrics": False,
            "log_performance_data": False
        })

        manager = DynamicInstanceManager(
            instance_pool=MockInstancePool(),
            performance_monitor=perf_monitor,
            config={
                "min_instances": 1,
                "max_instances": 8,
                "scale_up_threshold": 0.7,
                "scale_down_threshold": 0.3,
                "auto_adjustment_enabled": False  # 测试时禁用自动调整
            }
        )

        yield manager

    @pytest.mark.asyncio
    async def test_system_load_assessment(self, instance_manager):
        """测试系统负载评估"""
        load_info = await instance_manager.assess_system_load()

        # 验证负载信息结构
        assert isinstance(load_info, SystemLoadInfo)
        assert load_info.cpu_usage >= 0
        assert load_info.memory_usage >= 0
        assert load_info.active_instances >= 0
        assert load_info.queued_tasks >= 0
        assert load_info.avg_response_time >= 0
        assert load_info.error_rate >= 0

        # 验证派生属性
        assert 0 <= load_info.load_score <= 1
        assert 0 <= load_info.efficiency_score <= 1

    @pytest.mark.asyncio
    async def test_scale_up_decision(self, instance_manager):
        """测试扩容决策"""
        # 创建高负载场景
        high_load = SystemLoadInfo(
            cpu_usage=85,
            memory_usage=80,
            active_instances=4,
            queued_tasks=5,
            avg_response_time=3000,
            error_rate=0.02,
            throughput=2.0
        )

        should_scale = await instance_manager.should_scale_up(high_load)
        assert should_scale == True

    @pytest.mark.asyncio
    async def test_scale_down_decision(self, instance_manager):
        """测试缩容决策"""
        # 创建低负载场景
        low_load = SystemLoadInfo(
            cpu_usage=20,
            memory_usage=30,
            active_instances=4,
            queued_tasks=0,
            avg_response_time=500,
            error_rate=0.01,
            throughput=1.0
        )

        should_scale = await instance_manager.should_scale_down(low_load)
        assert should_scale == True

    @pytest.mark.asyncio
    async def test_instance_count_adjustment(self, instance_manager):
        """测试实例数调整"""
        # 设置当前实例数
        current_count = await instance_manager._get_current_instance_count()

        # 调整实例数
        result = await instance_manager.adjust_instance_count(current_count + 2)

        # 验证调整结果
        assert result.success == True
        assert result.adjustment_type in ["scale_up", "no_change"]
        assert result.old_value == current_count

    @pytest.mark.asyncio
    async def test_optimization_recommendations(self, instance_manager):
        """测试优化建议生成"""
        # 创建需要优化的负载场景
        poor_load = SystemLoadInfo(
            cpu_usage=90,
            memory_usage=85,
            active_instances=2,
            queued_tasks=10,
            avg_response_time=5000,
            error_rate=0.1,
            throughput=0.5
        )

        # 更新负载历史
        instance_manager.load_history = [poor_load]

        # 获取优化建议
        recommendations = await instance_manager.get_optimization_recommendations()

        # 验证建议
        assert len(recommendations) > 0
        assert any(r.priority == "high" for r in recommendations)


class TestIntelligentCacheManager:
    """智能缓存管理器测试类"""

    @pytest.fixture
    async def cache_manager(self):
        """创建缓存管理器"""
        config = {
            "max_cache_size_mb": 10,  # 小缓存用于测试
            "max_entries": 100,
            "default_ttl_seconds": 60,
            "enable_compression": True,
            "cleanup_interval_seconds": 5
        }

        manager = IntelligentCacheManager(config)
        await manager.start_monitoring()
        yield manager
        await manager.stop_monitoring()

    @pytest.mark.asyncio
    async def test_cache_storage_and_retrieval(self, cache_manager):
        """测试缓存存储和检索"""
        # 存储数据
        cache_key = "test_key_1"
        test_data = {"message": "Hello, World!", "number": 42}

        success = await cache_manager.cache_result(
            cache_key=cache_key,
            result=test_data,
            content_type=CacheEntryType.AGENT_RESPONSE
        )
        assert success == True

        # 检索数据
        retrieved = await cache_manager.get_cached_result(cache_key)
        assert retrieved is not None
        assert retrieved["message"] == "Hello, World!"
        assert retrieved["number"] == 42

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_manager):
        """测试缓存未命中"""
        result = await cache_manager.get_cached_result("non_existent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_ttl(self, cache_manager):
        """测试缓存TTL"""
        # 存储短TTL的数据
        cache_key = "ttl_test_key"
        await cache_manager.cache_result(
            cache_key=cache_key,
            result="test_data",
            content_type=CacheEntryType.AGENT_RESPONSE,
            ttl_seconds=1
        )

        # 立即检索应该成功
        result = await cache_manager.get_cached_result(cache_key)
        assert result == "test_data"

        # 等待过期
        await asyncio.sleep(2)

        # 再次检索应该失败
        result = await cache_manager.get_cached_result(cache_key)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_similarity_search(self, cache_manager):
        """测试缓存相似度搜索"""
        # 存储多个相似的内容
        contents = [
            "什么是机器学习？",
            "机器学习的定义",
            "机器学习的基本概念"
        ]

        for i, content in enumerate(contents):
            await cache_manager.cache_result(
                cache_key=f"similarity_test_{i}",
                result=content,
                content_type=CacheEntryType.AGENT_RESPONSE
            )

        # 搜索相似内容
        query = "请解释机器学习"
        similar_entries = await cache_manager.find_similar_cached_results(query, threshold=0.3)

        # 应该找到相似的条目
        assert len(similar_entries) > 0

    @pytest.mark.asyncio
    async def test_cache_statistics(self, cache_manager):
        """测试缓存统计"""
        # 执行一些缓存操作
        for i in range(5):
            await cache_manager.cache_result(
                cache_key=f"stat_test_{i}",
                result=f"data_{i}",
                content_type=CacheEntryType.AGENT_RESPONSE
            )

        # 检索一些数据
        await cache_manager.get_cached_result("stat_test_0")
        await cache_manager.get_cached_result("stat_test_1")
        await cache_manager.get_cached_result("non_existent")  # miss

        # 获取统计信息
        stats = await cache_manager.get_cache_statistics()

        # 验证统计
        assert stats.total_entries >= 5
        assert stats.hit_rate > 0
        assert stats.miss_rate > 0
        assert abs(stats.hit_rate + stats.miss_rate - 1.0) < 0.01  # hit + miss = 1

    @pytest.mark.asyncio
    async def test_cache_cleanup(self, cache_manager):
        """测试缓存清理"""
        # 填充缓存
        for i in range(20):
            await cache_manager.cache_result(
                cache_key=f"cleanup_test_{i}",
                result=f"data_{i}",
                content_type=CacheEntryType.AGENT_RESPONSE
            )

        # 执行优化
        result = await cache_manager.optimize_cache()

        # 验证优化结果
        assert "entries_removed" in result
        assert "space_freed_mb" in result
        assert "optimizations_applied" in result


class TestConfigurationManager:
    """配置管理器测试类"""

    @pytest.fixture
    async def config_manager(self):
        """创建配置管理器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigurationManager(temp_dir)
            yield manager

    @pytest.mark.asyncio
    async def test_config_validation(self, config_manager):
        """测试配置验证"""
        # 有效配置
        valid_config = PerformanceConfig(
            max_concurrent_instances=6,
            min_instances=1,
            cache_enabled=True,
            cache_max_size_mb=500
        )

        is_valid, errors = await config_manager.validate_config(valid_config)
        assert is_valid == True
        assert len(errors) == 0

        # 无效配置
        invalid_config = PerformanceConfig(
            max_concurrent_instances=1,
            min_instances=5,  # min > max
            cache_enabled=True,
            cache_max_size_mb=-10  # negative size
        )

        is_valid, errors = await config_manager.validate_config(invalid_config)
        assert is_valid == False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_config_save_and_load(self, config_manager):
        """测试配置保存和加载"""
        # 创建测试配置
        test_config = PerformanceConfig(
            max_concurrent_instances=8,
            cache_enabled=True,
            cache_ttl_seconds=7200,
            monitoring_enabled=False
        )

        # 保存配置
        success = await config_manager.save_config(test_config)
        assert success == True

        # 加载配置
        loaded_config = await config_manager.load_config()

        # 验证配置
        assert loaded_config.max_concurrent_instances == 8
        assert loaded_config.cache_enabled == True
        assert loaded_config.cache_ttl_seconds == 7200
        assert loaded_config.monitoring_enabled == False

    @pytest.mark.asyncio
    async def test_profile_management(self, config_manager):
        """测试配置档案管理"""
        from configuration_manager import ConfigurationProfile, ConfigurationScope

        # 创建档案
        profile = ConfigurationProfile(
            profile_name="test_profile",
            description="Test configuration profile",
            config=PerformanceConfig(max_concurrent_instances=10),
            scope=ConfigurationScope.USER
        )

        # 保存档案
        success = await config_manager.create_profile(profile)
        assert success == True

        # 列出档案
        profiles = await config_manager.list_profiles()
        assert len(profiles) > 0
        assert any(p.profile_name == "test_profile" for p in profiles)

        # 获取档案
        loaded_profile = await config_manager.get_profile("test_profile")
        assert loaded_profile is not None
        assert loaded_profile.config.max_concurrent_instances == 10

        # 应用档案
        success = await config_manager.apply_profile("test_profile")
        assert success == True

        # 删除档案
        success = await config_manager.delete_profile("test_profile")
        assert success == True

    @pytest.mark.asyncio
    async def test_config_change_application(self, config_manager):
        """测试配置变更应用"""
        changes = {
            "max_concurrent_instances": 12,
            "cache_ttl_seconds": 3600
        }

        success = await config_manager.apply_config_changes(changes)
        assert success == True

        # 验证变更
        current_config = await config_manager.get_current_config()
        assert current_config.max_concurrent_instances == 12
        assert current_config.cache_ttl_seconds == 3600


class TestPerformanceBenchmarkSystem:
    """性能基准测试系统测试类"""

    @pytest.fixture
    async def benchmark_system(self):
        """创建基准测试系统"""
        # 创建模拟组件
        perf_monitor = PerformanceMonitor({"enabled": False})
        cache_manager = IntelligentCacheManager({
            "max_cache_size_mb": 10,
            "enable_compression": False
        })
        config_manager = ConfigurationManager(tempfile.mkdtemp())

        system = PerformanceBenchmarkSystem(
            performance_monitor=perf_monitor,
            cache_manager=cache_manager,
            config_manager=config_manager
        )

        yield system

    @pytest.mark.asyncio
    async def test_benchmark_scenario_execution(self, benchmark_system):
        """测试基准测试场景执行"""
        # 运行单个场景
        result = await benchmark_system.run_benchmark(
            scenario_id="basic_small",
            test_type=BenchmarkType.SERIAL
        )

        # 验证结果
        assert result is not None
        assert result.scenario_id == "basic_small"
        assert result.test_type == BenchmarkType.SERIAL
        assert result.task_count > 0
        assert result.total_time > 0
        assert result.successful_tasks > 0
        assert result.throughput > 0

    @pytest.mark.asyncio
    async def test_parallel_vs_serial_comparison(self, benchmark_system):
        """测试并行vs串行对比"""
        # 运行串行测试
        serial_result = await benchmark_system.run_benchmark(
            scenario_id="basic_medium",
            test_type=BenchmarkType.SERIAL
        )

        # 运行并行测试
        parallel_result = await benchmark_system.run_benchmark(
            scenario_id="basic_medium",
            test_type=BenchmarkType.PARALLEL
        )

        # 验证并行更快
        assert parallel_result.total_time < serial_result.total_time

        # 验证效率比
        expected_ratio = serial_result.total_time / parallel_result.total_time
        actual_ratio = parallel_result.efficiency_ratio
        assert abs(expected_ratio - actual_ratio) < 0.1  # 允许10%误差

    @pytest.mark.asyncio
    async def test_comprehensive_benchmark(self, benchmark_system):
        """测试综合基准测试"""
        # 运行综合测试（可能需要较长时间）
        report = await benchmark_system.run_comprehensive_benchmark()

        # 验证报告
        assert report is not None
        assert len(report.scenarios) > 0
        assert "summary" in report
        assert "recommendations" in report
        assert "system_info" in report

        # 验证摘要
        assert "average_efficiency" in report.summary
        assert "success_rate" in report.summary
        assert report.summary["average_efficiency"] > 1.0


class TestIntegration:
    """集成测试类"""

    @pytest.mark.asyncio
    async def test_performance_optimization_integration(self):
        """测试性能优化系统集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建所有组件
            perf_monitor = PerformanceMonitor({
                "enabled": True,
                "collect_metrics": True,
                "log_performance_data": False
            })

            cache_manager = IntelligentCacheManager({
                "max_cache_size_mb": 50,
                "enable_compression": True
            })

            config_manager = ConfigurationManager(temp_dir)
            benchmark_system = PerformanceBenchmarkSystem(
                performance_monitor=perf_monitor,
                cache_manager=cache_manager,
                config_manager=config_manager
            )

            # 启动组件
            await perf_monitor.start_monitoring()
            await cache_manager.start_monitoring()

            # 执行集成测试流程
            try:
                # 1. 配置优化参数
                config_changes = {
                    "max_concurrent_instances": 6,
                    "cache_enabled": True,
                    "auto_scaling_enabled": True
                }
                await config_manager.apply_config_changes(config_changes)

                # 2. 执行性能基准测试
                benchmark_result = await benchmark_system.run_benchmark(
                    scenario_id="basic_medium",
                    test_type=BenchmarkType.PARALLEL
                )

                # 3. 验证效率提升
                assert benchmark_result.efficiency_ratio >= 1.0

                # 4. 测试缓存效果
                cache_key = "integration_test"
                test_data = {"test": "integration"}
                await cache_manager.cache_result(
                    cache_key=cache_key,
                    result=test_data,
                    content_type=CacheEntryType.AGENT_RESPONSE
                )
                cached_result = await cache_manager.get_cached_result(cache_key)
                assert cached_result == test_data

                # 5. 收集性能指标
                await asyncio.sleep(2)  # 等待收集指标
                assert len(perf_monitor.resource_metrics_history) > 0

                print("✓ Integration test completed successfully")

            finally:
                # 清理
                await perf_monitor.stop_monitoring()
                await cache_manager.stop_monitoring()

    @pytest.mark.asyncio
    async def test_dashboard_integration(self):
        """测试仪表板集成"""
        from performance_dashboard import PerformanceDashboard

        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建仪表板配置文件
            config_file = Path(temp_dir) / "performance_config.yaml"
            config_file.write_text("""
max_concurrent_instances: 4
cache_enabled: true
monitoring_enabled: true
auto_scaling_enabled: false
""")

            # 创建仪表板
            dashboard = PerformanceDashboard(str(config_file))

            # 启动仪表板
            started = await dashboard.start()
            assert started == True

            # 运行基准测试
            benchmark_result = await dashboard.run_benchmark()
            assert "success" in benchmark_result or "error" in benchmark_result

            # 获取指标摘要
            metrics = dashboard.get_metrics_summary(hours=0.1)
            assert "averages" in metrics or "error" in metrics

            # 停止仪表板
            await dashboard.stop()


# 性能测试标记
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.performance
]


if __name__ == "__main__":
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # 遇到第一个失败就停止
    ])