#!/usr/bin/env python3
"""
性能优化系统演示脚本

展示Canvas学习系统的性能优化功能，包括：
- 性能监控
- 智能缓存
- 动态实例调整
- 配置管理
- 基准测试

Usage:
    python performance_optimization_demo.py [demo_type]

Demo Types:
    monitor      - 演示性能监控
    cache        - 演示智能缓存
    scaling      - 演示动态实例调整
    config       - 演示配置管理
    benchmark    - 演示基准测试
    dashboard    - 启动完整仪表板
    all          - 运行所有演示
"""

import asyncio
import argparse
import json
import time
import os
from datetime import datetime
from pathlib import Path

# 导入性能组件
try:
    from performance_monitor import PerformanceMonitor
    from intelligent_cache_manager import IntelligentCacheManager, CacheEntryType
    from dynamic_instance_manager import DynamicInstanceManager
    from configuration_manager import ConfigurationManager, PerformanceConfig, ConfigurationProfile, ConfigurationScope
    from performance_benchmark_system import PerformanceBenchmarkSystem
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Could not import performance components: {e}")
    print("Please ensure all performance modules are in the same directory")
    COMPONENTS_AVAILABLE = False


class PerformanceOptimizationDemo:
    """性能优化系统演示类"""

    def __init__(self):
        self.demo_dir = Path("demo_data")
        self.demo_dir.mkdir(exist_ok=True)

    async def demo_monitoring(self):
        """演示性能监控"""
        print("\n" + "=" * 60)
        print("🎯 演示：性能监控系统")
        print("=" * 60)

        if not COMPONENTS_AVAILABLE:
            print("❌ Performance components not available")
            return

        # 创建性能监控器
        config = {
            "enabled": True,
            "collect_metrics": True,
            "log_performance_data": False,
            "metrics_collection_interval_seconds": 1,
            "cpu_usage_alert_threshold_percent": 70
        }

        monitor = PerformanceMonitor(config)

        print("\n📊 启动性能监控...")
        await monitor.start_monitoring()

        # 运行监控10秒
        print("\n监控运行中（10秒）...")
        for i in range(10):
            await asyncio.sleep(1)
            if monitor.resource_metrics_history:
                latest = monitor.resource_metrics_history[-1]
                print(f"  [{i+1}/10] CPU: {latest.cpu_percent:.1f}%, "
                      f"Memory: {latest.memory_usage_mb:.1f}MB, "
                      f"Threads: {latest.active_threads}")

        print("\n📈 生成性能报告...")
        report = monitor.generate_performance_report()

        print("\n性能摘要：")
        print(f"  平均CPU使用率: {report['resource_metrics'].get('average', {}).get('cpu_percent', 0):.1f}%")
        print(f"  平均内存使用: {report['resource_metrics'].get('average', {}).get('memory_usage_mb', 0):.1f}MB")
        print(f"  活跃告警数: {len(report['alerts'])}")

        print("\n💡 优化建议：")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"  {i}. {rec}")

        await monitor.stop_monitoring()
        print("\n✅ 性能监控演示完成")

    async def demo_caching(self):
        """演示智能缓存"""
        print("\n" + "=" * 60)
        print("💾 演示：智能缓存系统")
        print("=" * 60)

        if not COMPONENTS_AVAILABLE:
            print("❌ Performance components not available")
            return

        # 创建缓存管理器
        config = {
            "max_cache_size_mb": 10,
            "max_entries": 100,
            "default_ttl_seconds": 30,
            "enable_compression": True,
            "similarity_threshold": 0.7
        }

        cache = IntelligentCacheManager(config)
        await cache.start_monitoring()

        print("\n📝 缓存测试数据...")
        test_data = [
            ("概念1_机器学习", "机器学习是一种使计算机系统自动学习和改进的技术"),
            ("概念2_深度学习", "深度学习是机器学习的一个子集，使用神经网络"),
            ("概念3_神经网络", "神经网络是模拟人脑神经元结构的计算模型"),
            ("概念4_机器学习", "机器学习让计算机从数据中学习模式"),  # 相似内容
        ]

        # 存储数据
        for key, content in test_data:
            success = await cache.cache_result(
                cache_key=key,
                result=content,
                content_type=CacheEntryType.AGENT_RESPONSE
            )
            print(f"  {'✓' if success else '✗'} 缓存: {key}")

        print("\n🔍 测试缓存检索...")
        for key, _ in test_data[:3]:
            result = await cache.get_cached_result(key)
            print(f"  {'✓' if result else '✗'} 检索: {key}")

        print("\n🔍 测试相似度搜索...")
        query = "请解释深度学习和机器学习"
        similar_entries = await cache.find_similar_cached_results(query, threshold=0.5)
        print(f"  找到 {len(similar_entries)} 个相似条目")
        for entry in similar_entries[:2]:
            # 解压数据以显示
            if hasattr(entry, 'cached_result') and entry.cached_result:
                content = cache._decompress_data(entry.cached_result, entry.compression_enabled)
                print(f"    - {content[:50]}...")

        print("\n📊 缓存统计信息：")
        stats = await cache.get_cache_statistics()
        print(f"  总条目数: {stats.total_entries}")
        print(f"  缓存大小: {stats.total_size_mb:.2f}MB")
        print(f"  命中率: {stats.hit_rate:.1%}")
        print(f"  缓存效率: {stats.cache_efficiency:.1f}/100")

        await cache.stop_monitoring()
        print("\n✅ 智能缓存演示完成")

    async def demo_scaling(self):
        """演示动态实例调整"""
        print("\n" + "=" * 60)
        print("🔄 演示：动态实例调整")
        print("=" * 60)

        if not COMPONENTS_AVAILABLE:
            print("❌ Performance components not available")
            return

        # 创建模拟实例池
        class MockInstancePool:
            def __init__(self):
                self.max_instances = 6
                self.current_instances = 3

            async def set_max_concurrent_instances(self, count):
                old = self.current_instances
                self.current_instances = count
                self.max_instances = count
                print(f"    实例数调整: {old} → {count}")
                return True

        # 创建性能监控器
        perf_monitor = PerformanceMonitor({"enabled": False})

        # 创建动态实例管理器
        manager = DynamicInstanceManager(
            instance_pool=MockInstancePool(),
            performance_monitor=perf_monitor,
            config={
                "min_instances": 1,
                "max_instances": 8,
                "scale_up_threshold": 0.6,
                "scale_down_threshold": 0.3,
                "auto_adjustment_enabled": False
            }
        )

        print("\n📊 模拟不同负载场景...")

        # 场景1：低负载
        print("\n场景1：低负载")
        low_load = await manager.assess_system_load()
        low_load.cpu_usage = 25
        low_load.queued_tasks = 0
        low_load.avg_response_time = 500

        should_scale = await manager.should_scale_down(low_load)
        print(f"  CPU使用率: {low_load.cpu_usage}%")
        print(f"  队列长度: {low_load.queued_tasks}")
        print(f"  建议缩容: {'是' if should_scale else '否'}")

        # 场景2：高负载
        print("\n场景2：高负载")
        high_load = await manager.assess_system_load()
        high_load.cpu_usage = 85
        high_load.queued_tasks = 8
        high_load.avg_response_time = 4000

        should_scale = await manager.should_scale_up(high_load)
        print(f"  CPU使用率: {high_load.cpu_usage}%")
        print(f"  队列长度: {high_load.queued_tasks}")
        print(f"  建议扩容: {'是' if should_scale else '否'}")

        # 获取优化建议
        print("\n💡 优化建议：")
        recommendations = await manager.get_optimization_recommendations()
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec.description}")

        print("\n✅ 动态实例调整演示完成")

    async def demo_config_management(self):
        """演示配置管理"""
        print("\n" + "=" * 60)
        print("⚙️ 演示：配置管理系统")
        print("=" * 60)

        if not COMPONENTS_AVAILABLE:
            print("❌ Performance components not available")
            return

        # 创建配置管理器
        config_dir = self.demo_dir / "config"
        manager = ConfigurationManager(str(config_dir))

        print("\n📝 创建配置档案...")

        # 创建高性能配置档案
        high_perf_profile = ConfigurationProfile(
            profile_name="high_performance",
            description="高性能配置档案",
            config=PerformanceConfig(
                max_concurrent_instances=8,
                min_instances=2,
                cache_enabled=True,
                cache_max_size_mb=1000,
                auto_scaling_enabled=True,
                adjustment_strategy="aggressive"
            ),
            scope=ConfigurationScope.USER,
            tags=["performance", "high-throughput"]
        )

        # 创建节能配置档案
        eco_profile = ConfigurationProfile(
            profile_name="eco_mode",
            description="节能模式配置",
            config=PerformanceConfig(
                max_concurrent_instances=2,
                min_instances=1,
                cache_enabled=True,
                cache_max_size_mb=100,
                auto_scaling_enabled=False,
                adjustment_strategy="conservative"
            ),
            scope=ConfigurationScope.USER,
            tags=["eco", "low-resource"]
        )

        # 保存档案
        await manager.create_profile(high_perf_profile)
        await manager.create_profile(eco_profile)
        print("  ✓ 创建了2个配置档案")

        # 列出所有档案
        print("\n📋 配置档案列表：")
        profiles = await manager.list_profiles()
        for profile in profiles:
            print(f"  - {profile.profile_name}: {profile.description}")
            print(f"    最大实例数: {profile.config.max_concurrent_instances}")
            print(f"    缓存大小: {profile.config.cache_max_size_mb}MB")

        # 应用高性能配置
        print("\n✨ 应用高性能配置...")
        success = await manager.apply_profile("high_performance")
        print(f"  {'✓' if success else '✗'} 配置应用成功")

        # 验证当前配置
        current = await manager.get_current_config()
        print("\n当前配置摘要：")
        print(f"  最大并发实例: {current.max_concurrent_instances}")
        print(f"  自动扩缩容: {current.auto_scaling_enabled}")
        print(f"  缓存启用: {current.cache_enabled}")

        # 导出配置
        export_file = self.demo_dir / "exported_config.json"
        await manager.export_config(str(export_file))
        print(f"\n💾 配置已导出到: {export_file}")

        print("\n✅ 配置管理演示完成")

    async def demo_benchmark(self):
        """演示基准测试"""
        print("\n" + "=" * 60)
        print("🏁 演示：性能基准测试")
        print("=" * 60)

        if not COMPONENTS_AVAILABLE:
            print("❌ Performance components not available")
            return

        # 创建基准测试系统
        perf_monitor = PerformanceMonitor({"enabled": False})
        cache_manager = IntelligentCacheManager({
            "max_cache_size_mb": 50,
            "enable_compression": False
        })
        config_manager = ConfigurationManager(self.demo_dir / "benchmark_config")

        benchmark = PerformanceBenchmarkSystem(
            performance_monitor=perf_monitor,
            cache_manager=cache_manager,
            config_manager=config_manager
        )

        print("\n🏃 运行基准测试场景...")

        # 运行单个场景测试
        scenarios = ["basic_small", "basic_medium"]
        results = []

        for scenario_id in scenarios:
            print(f"\n测试场景: {scenario_id}")

            # 串行测试
            serial_result = await benchmark.run_benchmark(
                scenario_id=scenario_id,
                test_type=benchmark.BenchmarkType.SERIAL
            )

            # 并行测试
            parallel_result = await benchmark.run_benchmark(
                scenario_id=scenario_id,
                test_type=benchmark.BenchmarkType.PARALLEL
            )

            results.append((scenario_id, serial_result, parallel_result))

            print(f"  串行时间: {serial_result.total_time:.3f}s")
            print(f"  并行时间: {parallel_result.total_time:.3f}s")
            print(f"  效率提升: {parallel_result.efficiency_ratio:.2f}x")
            print(f"  达到目标: {'✓' if parallel_result.meets_target else '✗'}")

        # 生成简报
        print("\n📊 基准测试摘要：")
        avg_efficiency = sum(r[2].efficiency_ratio for r in results) / len(results)
        met_target = sum(1 for _, _, r in results if r.meets_target)

        print(f"  平均效率提升: {avg_efficiency:.2f}x")
        print(f"  达到目标的场景: {met_target}/{len(results)}")
        print(f"  目标达成率: {met_target/len(results):.1%}")

        # 保存测试报告
        print("\n💾 保存基准测试报告...")
        report_file = self.demo_dir / "benchmark_report.json"
        await benchmark.export_benchmark_data(str(report_file))
        print(f"  报告已保存到: {report_file}")

        print("\n✅ 基准测试演示完成")

    async def demo_dashboard(self):
        """启动完整仪表板"""
        print("\n" + "=" * 60)
        print("📊 启动完整性能仪表板")
        print("=" * 60)

        try:
            from performance_dashboard import PerformanceDashboard

            # 创建仪表板
            dashboard = PerformanceDashboard(
                config_file=str(self.demo_dir / "dashboard_config.yaml")
            )

            print("\n🚀 启动仪表板...")
            print("提示：按 Ctrl+C 停止仪表板\n")

            # 启动仪表板
            if await dashboard.start():
                try:
                    # 运行直到用户中断
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    print("\n\n🛑 停止仪表板...")
                    await dashboard.stop()
                    print("✅ 仪表板已停止")
            else:
                print("❌ 仪表板启动失败")

        except ImportError:
            print("❌ 无法导入仪表板组件")
            print("请确保 performance_dashboard.py 在当前目录")

    async def demo_all(self):
        """运行所有演示"""
        print("\n🎪 运行所有演示...\n")

        demos = [
            ("性能监控", self.demo_monitoring),
            ("智能缓存", self.demo_caching),
            ("动态实例调整", self.demo_scaling),
            ("配置管理", self.demo_config_management),
            ("基准测试", self.demo_benchmark)
        ]

        for name, demo_func in demos:
            print(f"\n{'='*20} {name} {'='*20}")
            try:
                await demo_func()
                await asyncio.sleep(1)  # 演示间隔
            except Exception as e:
                print(f"❌ 演示失败: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "=" * 60)
        print("🎉 所有演示完成！")
        print("要查看交互式仪表板，请运行: python performance_optimization_demo.py dashboard")
        print("=" * 60)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Canvas学习系统性能优化演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python performance_optimization_demo.py monitor
  python performance_optimization_demo.py all
  python performance_optimization_demo.py dashboard
        """
    )

    parser.add_argument(
        "demo_type",
        choices=["monitor", "cache", "scaling", "config", "benchmark", "dashboard", "all"],
        help="选择演示类型"
    )

    args = parser.parse_args()

    # 创建演示实例
    demo = PerformanceOptimizationDemo()

    # 检查组件可用性
    if not COMPONENTS_AVAILABLE:
        print("❌ 性能优化组件不可用")
        print("请确保所有性能模块文件在当前目录")
        return

    # 运行选定的演示
    demo_map = {
        "monitor": demo.demo_monitoring,
        "cache": demo.demo_caching,
        "scaling": demo.demo_scaling,
        "config": demo.demo_config_management,
        "benchmark": demo.demo_benchmark,
        "dashboard": demo.demo_dashboard,
        "all": demo.demo_all
    }

    try:
        await demo_map[args.demo_type]()
    except KeyboardInterrupt:
        print("\n\n🛑 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())