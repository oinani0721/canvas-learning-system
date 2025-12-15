"""
GLM Rate Limiter Integration Test
集成测试GLM Coding Plan用量管理系统
"""

import asyncio
from datetime import datetime, timezone, timedelta
from glm_rate_limiter import create_rate_limiter, PlanType
from usage_monitor import UsageMonitor


async def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试GLM Rate Limiter基本功能 ===\n")

    # 创建pro套餐的速率限制器
    limiter = create_rate_limiter("pro")
    print(f"✓ 创建速率限制器 - 套餐: pro")
    print(f"  - 最大prompt数/5h: {limiter.config.max_prompts_per_period}")
    print(f"  - 速率限制: {limiter.config.rate_limit_requests_per_second} req/s")
    print(f"  - 最大并发: {limiter.config.max_concurrent_requests}")

    # 启动限制器
    await limiter.start()
    print("\n✓ 启动速率限制器")

    # 检查初始状态
    status = await limiter.get_usage_status()
    print(f"\n初始用量状态:")
    print(f"  - 总额度: {status.total_prompts}")
    print(f"  - 已使用: {status.used_prompts}")
    print(f"  - 剩余: {status.remaining_prompts}")
    print(f"  - 使用率: {status.usage_percentage:.1%}")

    # 测试消耗额度（关闭智能节流以便快速测试）
    limiter.config.enable_smart_throttling = False

    print("\n测试消耗额度:")
    success_count = 0
    for i in range(5):
        success = await limiter.consume_quota(10)
        if success:
            success_count += 1
            print(f"  ✓ 成功消耗 10 prompts (第{i+1}次)")
        else:
            print(f"  ✗ 消耗失败 (第{i+1}次)")

    # 更新状态
    status = await limiter.get_usage_status()
    print(f"\n消耗后状态:")
    print(f"  - 已使用: {status.used_prompts}")
    print(f"  - 剩余: {status.remaining_prompts}")
    print(f"  - 使用率: {status.usage_percentage:.1%}")

    # 测试套餐配置
    print("\n=== 测试不同套餐配置 ===")

    # Lite套餐
    lite_limiter = create_rate_limiter("lite")
    print(f"✓ Lite套餐: {lite_limiter.config.max_prompts_per_period} prompts/5h")

    # Pro套餐
    pro_limiter = create_rate_limiter("pro")
    print(f"✓ Pro套餐: {pro_limiter.config.max_prompts_per_period} prompts/5h")

    # Max套餐
    max_limiter = create_rate_limiter("max")
    print(f"✓ Max套餐: {max_limiter.config.max_prompts_per_period} prompts/5h")

    # 停止限制器
    await limiter.stop()
    print("\n✓ 停止速率限制器")

    return success_count > 0


async def test_usage_monitor():
    """测试用量监控器"""
    print("\n\n=== 测试UsageMonitor功能 ===\n")

    # 创建速率限制器
    limiter = create_rate_limiter("pro")
    await limiter.start()

    # 创建监控器
    monitor = UsageMonitor(limiter)
    await monitor.start_monitoring()
    print("✓ 启动用量监控器")

    # 模拟一些使用
    limiter.config.enable_smart_throttling = False
    for i in range(3):
        await limiter.consume_quota(5)

    # 获取实时指标
    metrics = await monitor.get_real_time_metrics()
    print("\n实时用量指标:")
    print(f"  - 当前使用率: {metrics['current_usage']['usage_percentage']:.1%}")
    print(f"  - 剩余时间: {metrics['remaining_time_hours']:.1f} 小时")
    print(f"  - 状态级别: {metrics['status']}")

    # 生成报告
    report = await monitor.generate_usage_report(days=1)
    if "error" not in report:
        print(f"\n用量报告:")
        print(f"  - 报告ID: {report['report_id']}")
        print(f"  - 覆盖期间: {report['period_covered']}")
        print(f"  - 使用趋势: {report['usage_trend']}")
    else:
        print("\n报告生成: 暂无历史数据")

    # 停止监控器
    await monitor.stop_monitoring()
    await limiter.stop()
    print("\n✓ 停止监控器和限制器")


async def test_alert_system():
    """测试预警系统"""
    print("\n\n=== 测试预警系统 ===\n")

    # 创建限制器
    limiter = create_rate_limiter("lite")  # 使用小套餐便于测试
    await limiter.start()

    # 设置预警回调
    alerts_received = []

    async def alert_handler(alert):
        alerts_received.append(alert)
        print(f"  ⚠️ 收到预警: {alert.message} ({alert.percentage:.1%})")

    await limiter.set_alert_callback(alert_handler)
    print("✓ 设置预警回调函数")

    # 关闭智能节流以便快速测试
    limiter.config.enable_smart_throttling = False

    # 消耗到80%（96/120）
    print("\n消耗到80%阈值...")
    await limiter.consume_quota(96)
    await asyncio.sleep(0.1)  # 等待异步处理

    # 消耗到90%（108/120）
    print("消耗到90%阈值...")
    await limiter.consume_quota(12)
    await asyncio.sleep(0.1)

    print(f"\n收到的预警数量: {len(alerts_received)}")

    # 停止限制器
    await limiter.stop()
    print("✓ 测试完成")


async def test_enhanced_pool():
    """测试增强版实例池"""
    print("\n\n=== 测试增强版实例池集成 ===\n")

    try:
        from enhanced_agent_instance_pool import create_enhanced_instance_pool

        # 创建增强版实例池
        pool = await create_enhanced_instance_pool(
            max_concurrent_instances=2,
            plan_type="pro"
        )
        print("✓ 创建增强版实例池（带用量控制）")

        # 创建实例
        instance_id = await pool.create_instance("clarification-path")
        print(f"✓ 创建实例: {instance_id}")

        # 提交任务
        task_data = {
            "task_id": "test-001",
            "node_data": {"content": "test content"}
        }

        result = await pool.submit_task(instance_id, task_data)
        print(f"✓ 提交任务结果: {result['status']}")

        # 获取池状态
        pool_status = await pool.get_pool_status()
        print(f"\n实例池状态:")
        print(f"  - 活跃实例数: {pool_status['active_instances']}")
        print(f"  - 成功任务数: {pool_status['performance_metrics']['successful_tasks']}")
        print(f"  - 用量控制: {'启用' if pool_status['quota_status']['quota_control_enabled'] else '禁用'}")

        # 关闭实例
        await pool.shutdown_instance(instance_id)
        print(f"\n✓ 关闭实例: {instance_id}")

        # 停止池
        await pool.stop()
        print("✓ 停止实例池")

    except ImportError as e:
        print(f"✗ 无法导入增强版实例池: {e}")


async def main():
    """主测试函数"""
    print("Canvas Learning System - GLM Coding Plan 智能用量管理集成测试\n")
    print("=" * 70)

    test_results = []

    # 测试1: 基本功能
    try:
        result = await test_basic_functionality()
        test_results.append(("基本功能", result))
    except Exception as e:
        test_results.append(("基本功能", False))
        print(f"\n✗ 基本功能测试失败: {e}")

    # 测试2: 用量监控
    try:
        await test_usage_monitor()
        test_results.append(("用量监控", True))
    except Exception as e:
        test_results.append(("用量监控", False))
        print(f"\n✗ 用量监控测试失败: {e}")

    # 测试3: 预警系统
    try:
        await test_alert_system()
        test_results.append(("预警系统", True))
    except Exception as e:
        test_results.append(("预警系统", False))
        print(f"\n✗ 预警系统测试失败: {e}")

    # 测试4: 增强版实例池
    try:
        await test_enhanced_pool()
        test_results.append(("增强版实例池", True))
    except Exception as e:
        test_results.append(("增强版实例池", False))
        print(f"\n✗ 增强版实例池测试失败: {e}")

    # 输出测试总结
    print("\n\n" + "=" * 70)
    print("测试总结:")
    print("-" * 70)

    passed = 0
    for test_name, success in test_results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name:20} {status}")
        if success:
            passed += 1

    print("-" * 70)
    print(f"总计: {passed}/{len(test_results)} 项测试通过")

    if passed == len(test_results):
        print("\n🎉 所有测试通过！GLM Coding Plan智能用量管理系统运行正常。")
    else:
        print("\n⚠️ 部分测试失败，请检查相关模块。")


if __name__ == "__main__":
    asyncio.run(main())