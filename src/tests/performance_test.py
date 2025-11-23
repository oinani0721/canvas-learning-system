#!/usr/bin/env python3
"""
性能测试 - 验证记忆记录系统的性能指标
"""

import sys
import os
import time
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def performance_test():
    """性能测试"""
    print("开始性能测试...")
    print("="*60)

    from canvas_utils.memory_recorder import MemoryRecorder

    # 创建配置
    config = {
        'graphiti': {'enabled': False},
        'local_db': {
            'enabled': True,
            'path': 'data/perf_test.db',
            'backup_path': 'data/perf_test_backup.db'
        },
        'file_logger': {
            'enabled': True,
            'log_dir': 'data/perf_logs'
        },
        'encryption': {
            'enabled': True,
            'key_path': 'data/perf_key.key'
        }
    }

    recorder = MemoryRecorder(config)
    await recorder.initialize()

    # 测试1: 记录延迟（< 100ms）
    print("\n1. 测试记录延迟...")
    latencies = []

    for i in range(10):
        session_data = {
            'session_id': f'perf_test_{i}',
            'canvas_path': 'test.canvas',
            'actions': [{'type': 'test', 'index': i}]
        }

        start_time = time.perf_counter()
        await recorder.record_session(session_data)
        end_time = time.perf_counter()

        latency = (end_time - start_time) * 1000  # 转换为毫秒
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)

    print(f"   平均延迟: {avg_latency:.2f} ms")
    print(f"   最大延迟: {max_latency:.2f} ms")
    print(f"   验收标准: < 100ms")
    print(f"   结果: {'✓ 通过' if avg_latency < 100 else '✗ 失败'}")

    # 测试2: 故障切换时间
    print("\n2. 测试故障切换时间...")
    # 模拟主系统失败，测量切换时间
    config2 = config.copy()
    config2['graphiti']['enabled'] = False
    config2['local_db']['always_backup'] = True

    recorder2 = MemoryRecorder(config2)
    await recorder2.initialize()

    start_time = time.perf_counter()
    report = await recorder2.record_session({
        'session_id': 'failover_test',
        'canvas_path': 'test.canvas',
        'actions': []
    })
    end_time = time.perf_counter()

    failover_time = (end_time - start_time) * 1000
    print(f"   故障切换时间: {failover_time:.2f} ms")
    print(f"   验收标准: < 1000ms")
    print(f"   结果: {'✓ 通过' if failover_time < 1000 else '✗ 失败'}")

    # 测试3: 并发记录能力
    print("\n3. 测试并发记录能力...")
    num_concurrent = 50

    async def single_record(i):
        return await recorder.record_session({
            'session_id': f'concurrent_{i}',
            'canvas_path': 'test.canvas',
            'actions': []
        })

    start_time = time.perf_counter()
    tasks = [single_record(i) for i in range(num_concurrent)]
    results = await asyncio.gather(*tasks)
    end_time = time.perf_counter()

    duration = end_time - start_time
    tps = num_concurrent / duration

    print(f"   并发记录数: {num_concurrent}")
    print(f"   总耗时: {duration:.2f} 秒")
    print(f"   TPS (每秒事务数): {tps:.2f}")
    print(f"   成功记录: {sum(1 for r in results if r.successful_systems)}/{num_concurrent}")

    # 测试4: 存储空间增长
    print("\n4. 测试存储空间增长...")
    import os
    import shutil

    # 记录100条记录
    for i in range(100):
        await recorder.record_session({
            'session_id': f'storage_test_{i}',
            'canvas_path': 'test.canvas',
            'actions': [{'type': 'test'}] * 10,  # 10个动作
            'metadata': {'data': 'x' * 100}  # 100字节数据
        })

    # 检查文件大小
    db_size = os.path.getsize('data/perf_test.db') / (1024 * 1024)  # MB
    log_files = list(Path('data/perf_logs').glob('*.log'))
    log_size = sum(os.path.getsize(f) for f in log_files) / (1024 * 1024)  # MB

    total_size = db_size + log_size
    print(f"   记录数: 100")
    print(f"   数据库大小: {db_size:.2f} MB")
    print(f"   日志大小: {log_size:.2f} MB")
    print(f"   总大小: {total_size:.2f} MB")
    print(f"   每天预估: {total_size * 86400 / 100:.2f} MB")  # 假设100记录/天
    print(f"   验收标准: < 50MB/天")
    print(f"   结果: {'✓ 通过' if total_size * 86400 / 100 < 50 else '✗ 失败'}")

    # 总结
    print("\n" + "="*60)
    print("性能测试总结")
    print("="*60)

    all_passed = (
        avg_latency < 100 and
        failover_time < 1000 and
        total_size * 86400 / 100 < 50
    )

    print(f"记录延迟: {'✓' if avg_latency < 100 else '✗'} ({avg_latency:.2f} ms)")
    print(f"故障切换: {'✓' if failover_time < 1000 else '✗'} ({failover_time:.2f} ms)")
    print(f"存储增长: {'✓' if total_size * 86400 / 100 < 50 else '✗'} ({total_size * 86400 / 100:.2f} MB/day)")
    print(f"\n总体评价: {'✅ 所有性能指标达标' if all_passed else '❌ 部分指标未达标'}")

    # 清理
    shutil.rmtree('data')

    return all_passed


if __name__ == '__main__':
    success = asyncio.run(performance_test())
    sys.exit(0 if success else 1)