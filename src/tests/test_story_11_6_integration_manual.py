"""
Story 11.6 快速集成验证脚本 - DataSyncScheduler

目的：端到端验证核心功能，不依赖pytest复杂fixture
测试流程：
1. 创建模拟学习会话数据（JSON）
2. 启动DataSyncScheduler同步
3. 验证数据已同步到SQLite
4. 测试归档功能
5. 测试磁盘空间管理
6. 清理测试环境

运行方式：python tests/test_story_11_6_integration_manual.py
"""

import os
import sys
import json
import time
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from canvas_progress_tracker.data_stores import (
    HotDataStore,
    ColdDataStore,
    DataSyncScheduler
)


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}[OK] {text}{Colors.END}")


def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}[FAIL] {text}{Colors.END}")


def print_info(text):
    """打印信息"""
    print(f"{Colors.YELLOW}[INFO] {text}{Colors.END}")


def create_test_session_data(session_id: str, days_ago: int = 0) -> dict:
    """
    创建测试会话数据

    Args:
        session_id: 会话ID
        days_ago: 几天前的数据

    Returns:
        会话数据字典
    """
    base_time = datetime.now() - timedelta(days=days_ago)

    return {
        "session_id": session_id,
        "start_time": base_time.isoformat(),
        "end_time": (base_time + timedelta(hours=1)).isoformat(),
        "events": [
            {
                "event_id": f"evt_{session_id}_001",
                "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
                "event_type": "node_color_change",
                "canvas_id": "test_canvas.canvas",
                "node_id": "node_001",
                "old_color": "1",
                "new_color": "2",
                "metadata": {"concept": "测试概念1"}
            },
            {
                "event_id": f"evt_{session_id}_002",
                "timestamp": (base_time + timedelta(minutes=10)).isoformat(),
                "event_type": "node_added",
                "canvas_id": "test_canvas.canvas",
                "node_id": "node_002",
                "node_type": "text",
                "metadata": {"text": "个人理解"}
            },
            {
                "event_id": f"evt_{session_id}_003",
                "timestamp": (base_time + timedelta(minutes=15)).isoformat(),
                "event_type": "node_color_change",
                "canvas_id": "test_canvas.canvas",
                "node_id": "node_003",
                "old_color": "3",
                "new_color": "2",
                "metadata": {"concept": "测试概念2"}
            }
        ],
        "metadata": {
            "canvas_count": 1,
            "total_events": 3
        }
    }


def create_test_session_file(sessions_dir: Path, session_data: dict, days_ago: int = 0) -> Path:
    """
    创建测试会话文件并设置修改时间

    Args:
        sessions_dir: 会话目录
        session_data: 会话数据
        days_ago: 几天前

    Returns:
        创建的文件路径
    """
    session_id = session_data["session_id"]
    file_path = sessions_dir / f"{session_id}.json"

    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    # 设置文件修改时间
    if days_ago > 0:
        old_time = datetime.now() - timedelta(days=days_ago)
        timestamp = old_time.timestamp()
        os.utime(file_path, (timestamp, timestamp))

    return file_path


def verify_test_environment():
    """验证测试环境"""
    print_header("Step 0: 验证测试环境")

    try:
        # 检查imports
        print_info("检查模块导入...")
        assert HotDataStore is not None
        assert ColdDataStore is not None
        assert DataSyncScheduler is not None
        print_success("所有模块导入成功")

        return True

    except Exception as e:
        print_error(f"环境验证失败: {e}")
        return False


def test_sync_flow(test_dir: Path):
    """
    测试1: 核心同步流程
    JSON → SQLite → 删除JSON
    """
    print_header("Test 1: 核心同步流程 (JSON → SQLite)")

    sessions_dir = test_dir / "sessions"
    db_path = test_dir / "test.db"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 创建stores
        print_info("创建HotDataStore和ColdDataStore...")
        hot_store = HotDataStore(session_dir=sessions_dir)
        cold_store = ColdDataStore(db_path=db_path)
        print_success(f"Stores创建成功: sessions={sessions_dir}, db={db_path}")

        # 创建3天前的测试数据（应该被同步）
        # 注意：文件名必须匹配 session_*.json 格式
        print_info("创建测试会话文件（3天前）...")
        session_data_1 = create_test_session_data("session_001", days_ago=3)
        session_data_2 = create_test_session_data("session_002", days_ago=3)

        file1 = create_test_session_file(sessions_dir, session_data_1, days_ago=3)
        file2 = create_test_session_file(sessions_dir, session_data_2, days_ago=3)
        print_success(f"创建了2个测试文件: {file1.name}, {file2.name}")

        # 创建调度器
        print_info("创建DataSyncScheduler（同步间隔=1秒）...")
        scheduler = DataSyncScheduler(
            hot_store=hot_store,
            cold_store=cold_store,
            sync_interval=1,  # 1秒
            archive_threshold=90,
            cleanup_threshold=365
        )
        print_success("DataSyncScheduler创建成功")

        # 手动触发一次同步（不启动后台线程）
        print_info("手动触发同步...")
        sync_stats = scheduler._sync_session_data()

        print_info(f"同步统计: {json.dumps(sync_stats, ensure_ascii=False, indent=2)}")

        # 验证同步结果
        print_info("验证同步结果...")

        # 检查文件是否被删除
        if file1.exists():
            print_error(f"文件未被删除: {file1.name}")
            return False
        print_success("测试文件1已被删除")

        if file2.exists():
            print_error(f"文件未被删除: {file2.name}")
            return False
        print_success("测试文件2已被删除")

        # 检查SQLite中的数据
        print_info("查询SQLite中的canvas_changes...")
        changes = cold_store.query_canvas_changes(
            canvas_id="test_canvas.canvas",
            limit=100
        )

        print_info(f"查询到 {len(changes)} 条canvas_changes记录")

        if len(changes) < 4:  # 每个session有2个颜色变化事件
            print_error(f"canvas_changes记录数不足: 期望>=4, 实际={len(changes)}")
            return False
        print_success(f"canvas_changes记录数正确: {len(changes)} 条")

        # 检查color_transitions
        print_info("查询SQLite中的color_transitions...")
        transitions = cold_store.query_color_transitions(
            canvas_id="test_canvas.canvas",
            limit=100
        )

        print_info(f"查询到 {len(transitions)} 条color_transitions记录")

        if len(transitions) < 2:  # 每个session有1个颜色转换
            print_error(f"color_transitions记录数不足: 期望>=2, 实际={len(transitions)}")
            return False
        print_success(f"color_transitions记录数正确: {len(transitions)} 条")

        # 检查统计信息
        if sync_stats.get("files_succeeded", 0) != 2:
            print_error(f"同步成功文件数错误: 期望=2, 实际={sync_stats.get('files_succeeded')}")
            return False
        print_success(f"同步统计正确: {sync_stats.get('files_succeeded')} 个文件成功")

        print_success(">>> Test 1 PASSED: 核心同步流程正常 <<<")
        return True

    except Exception as e:
        print_error(f"Test 1 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling(test_dir: Path):
    """
    测试2: 错误处理
    损坏的JSON → 移到.errors目录
    """
    print_header("Test 2: 错误处理机制")

    sessions_dir = test_dir / "sessions2"
    db_path = test_dir / "test2.db"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 创建stores和scheduler
        hot_store = HotDataStore(session_dir=sessions_dir)
        cold_store = ColdDataStore(db_path=db_path)
        scheduler = DataSyncScheduler(
            hot_store=hot_store,
            cold_store=cold_store,
            sync_interval=1
        )

        # 创建损坏的JSON文件（必须匹配session_*.json格式）
        print_info("创建损坏的JSON文件...")
        bad_file = sessions_dir / "session_corrupted.json"
        with open(bad_file, 'w') as f:
            f.write("{invalid json content")

        # 设置为3天前
        old_time = datetime.now() - timedelta(days=3)
        os.utime(bad_file, (old_time.timestamp(), old_time.timestamp()))
        print_success("创建损坏文件: session_corrupted.json")

        # 执行同步
        print_info("执行同步...")
        sync_stats = scheduler._sync_session_data()

        # 验证错误处理
        print_info("验证错误处理...")

        # 文件应该被移到.errors目录
        if bad_file.exists():
            print_error("损坏文件未被移动")
            return False
        print_success("损坏文件已从原目录移除")

        # 检查.errors目录
        error_files = list(scheduler.error_dir.glob("session_corrupted.json"))
        if len(error_files) == 0:
            print_error(".errors目录中未找到损坏文件")
            return False
        print_success(f"损坏文件已移至: {error_files[0]}")

        # 检查错误信息文件
        error_info_files = list(scheduler.error_dir.glob("session_corrupted.json.error"))
        if len(error_info_files) == 0:
            print_error("未找到错误信息文件")
            return False
        print_success(f"错误信息文件存在: {error_info_files[0]}")

        # 检查同步统计
        if sync_stats.get("files_failed", 0) != 1:
            print_error(f"失败文件数错误: 期望=1, 实际={sync_stats.get('files_failed')}")
            return False
        print_success("同步统计正确: 1个文件失败")

        print_success(">>> Test 2 PASSED: 错误处理正常 <<<")
        return True

    except Exception as e:
        print_error(f"Test 2 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_archiving(test_dir: Path):
    """
    测试3: 数据归档
    90天前数据 → gzip压缩归档
    """
    print_header("Test 3: 数据归档功能")

    sessions_dir = test_dir / "sessions3"
    db_path = test_dir / "test3.db"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 创建stores和scheduler
        hot_store = HotDataStore(session_dir=sessions_dir)
        cold_store = ColdDataStore(db_path=db_path)
        scheduler = DataSyncScheduler(
            hot_store=hot_store,
            cold_store=cold_store,
            sync_interval=1,
            archive_threshold=90
        )

        # 插入100天前的数据到ColdDataStore
        print_info("插入100天前的测试数据到SQLite...")
        old_time = (datetime.now() - timedelta(days=100)).isoformat()

        test_changes = []
        for i in range(10):
            test_changes.append({
                "change_id": f"old_change_{i}",
                "canvas_id": "old_canvas.canvas",
                "change_type": "node_added",
                "change_data": json.dumps({"index": i}),
                "timestamp": old_time
            })

        inserted_count = cold_store.insert_canvas_changes(test_changes)
        print_success(f"插入了 {inserted_count} 条旧数据")

        # 执行归档
        print_info("执行归档...")
        archive_result = scheduler._archive_old_data()

        print_info(f"归档结果: {json.dumps(archive_result, ensure_ascii=False, indent=2)}")

        # 验证归档
        if not archive_result.get("success"):
            print_error(f"归档失败: {archive_result.get('error', 'Unknown')}")
            return False
        print_success("归档操作成功")

        if archive_result.get("records_archived", 0) < 10:
            print_error(f"归档记录数不足: 期望>=10, 实际={archive_result.get('records_archived')}")
            return False
        print_success(f"归档记录数正确: {archive_result.get('records_archived')} 条")

        # 检查归档文件存在
        archive_path = Path(archive_result.get("archive_file", ""))
        if not archive_path.exists():
            print_error(f"归档文件不存在: {archive_path}")
            return False
        print_success(f"归档文件存在: {archive_path.name}")

        # 检查压缩
        if not archive_path.suffix == ".gz":
            print_error("归档文件未压缩")
            return False
        print_success("归档文件已gzip压缩")

        # 验证归档文件可读
        print_info("验证归档文件完整性...")
        import gzip
        with gzip.open(archive_path, 'rt', encoding='utf-8') as f:
            archive_data = json.load(f)

        if "canvas_changes" not in archive_data:
            print_error("归档文件缺少canvas_changes字段")
            return False

        if len(archive_data["canvas_changes"]) < 10:
            print_error(f"归档数据不完整: 期望>=10, 实际={len(archive_data['canvas_changes'])}")
            return False

        print_success(f"归档文件完整: {len(archive_data['canvas_changes'])} 条记录")

        print_success(">>> Test 3 通过: 数据归档正常 >>>")
        return True

    except Exception as e:
        print_error(f"Test 3 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_disk_space_management(test_dir: Path):
    """
    测试4: 磁盘空间管理
    统计 + 清理旧归档
    """
    print_header("Test 4: 磁盘空间管理")

    sessions_dir = test_dir / "sessions4"
    db_path = test_dir / "test4.db"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 创建stores和scheduler
        hot_store = HotDataStore(session_dir=sessions_dir)
        cold_store = ColdDataStore(db_path=db_path)
        scheduler = DataSyncScheduler(
            hot_store=hot_store,
            cold_store=cold_store,
            sync_interval=1,
            cleanup_threshold=365
        )

        # 创建一些测试JSON文件
        print_info("创建测试JSON文件...")
        for i in range(3):
            test_data = create_test_session_data(f"test_{i}")
            create_test_session_file(sessions_dir, test_data)
        print_success("创建了3个测试文件")

        # 创建一个旧归档文件（400天前）
        print_info("创建旧归档文件（400天前）...")
        old_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        old_archive_name = f"archive_{old_date}_to_{old_date}.json.gz"
        old_archive_path = scheduler.archive_dir / old_archive_name

        import gzip
        with gzip.open(old_archive_path, 'wt', encoding='utf-8') as f:
            json.dump({"test": "old archive"}, f)
        print_success(f"创建旧归档: {old_archive_name}")

        # 执行磁盘检查
        print_info("执行磁盘空间检查...")
        disk_stats = scheduler._check_disk_space()

        print_info(f"磁盘统计: {json.dumps(disk_stats, ensure_ascii=False, indent=2)}")

        # 验证统计字段
        required_fields = [
            "json_files_size_mb",
            "sqlite_db_size_mb",
            "archives_size_mb",
            "total_size_mb",
            "available_space_mb",
            "json_file_count",
            "archive_count"
        ]

        for field in required_fields:
            if field not in disk_stats:
                print_error(f"缺少统计字段: {field}")
                return False
        print_success("所有统计字段存在")

        # 验证文件计数
        if disk_stats["json_file_count"] != 3:
            print_error(f"JSON文件计数错误: 期望=3, 实际={disk_stats['json_file_count']}")
            return False
        print_success(f"JSON文件计数正确: {disk_stats['json_file_count']}")

        # 验证旧归档被删除
        if disk_stats.get("old_archives_deleted", 0) < 1:
            print_error("旧归档未被删除")
            return False
        print_success(f"旧归档已删除: {disk_stats['old_archives_deleted']} 个")

        # 验证旧归档文件不存在
        if old_archive_path.exists():
            print_error(f"旧归档文件仍存在: {old_archive_path}")
            return False
        print_success("旧归档文件已被清理")

        print_success(">>> Test 4 通过: 磁盘空间管理正常 >>>")
        return True

    except Exception as e:
        print_error(f"Test 4 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monitoring(test_dir: Path):
    """
    测试5: 监控功能
    状态查询 + 健康检查
    """
    print_header("Test 5: 监控功能")

    sessions_dir = test_dir / "sessions5"
    db_path = test_dir / "test5.db"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 创建stores和scheduler
        hot_store = HotDataStore(session_dir=sessions_dir)
        cold_store = ColdDataStore(db_path=db_path)
        scheduler = DataSyncScheduler(
            hot_store=hot_store,
            cold_store=cold_store,
            sync_interval=1
        )

        # 测试健康检查（未启动）
        print_info("测试健康检查（未启动状态）...")
        is_healthy = scheduler.is_healthy()
        if is_healthy:
            print_error("未启动状态应该不健康")
            return False
        print_success("未启动状态健康检查: False [OK]")

        # 启动scheduler
        print_info("启动scheduler...")
        scheduler.start()
        time.sleep(0.5)  # 等待启动
        print_success("Scheduler已启动")

        # 测试健康检查（已启动）
        print_info("测试健康检查（已启动状态）...")
        is_healthy = scheduler.is_healthy()
        if not is_healthy:
            print_error("已启动状态应该健康")
            scheduler.stop()
            return False
        print_success("已启动状态健康检查: True [OK]")

        # 获取状态
        print_info("获取同步状态...")
        status = scheduler.get_sync_status()

        # 验证状态字段
        required_fields = ["running", "last_sync_time", "next_sync_time", "sync_history", "disk_usage"]
        for field in required_fields:
            if field not in status:
                print_error(f"缺少状态字段: {field}")
                scheduler.stop()
                return False
        print_success("所有状态字段存在")

        # 验证running状态
        if not status["running"]:
            print_error("running状态错误")
            scheduler.stop()
            return False
        print_success("running状态正确: True")

        # 验证disk_usage
        if not isinstance(status["disk_usage"], dict):
            print_error("disk_usage应该是字典")
            scheduler.stop()
            return False
        print_success("disk_usage字段正确")

        # 停止scheduler
        print_info("停止scheduler...")
        scheduler.stop()
        time.sleep(0.5)
        print_success("Scheduler已停止")

        # 再次检查健康状态
        print_info("测试健康检查（已停止状态）...")
        is_healthy = scheduler.is_healthy()
        if is_healthy:
            print_error("已停止状态应该不健康")
            return False
        print_success("已停止状态健康检查: False [OK]")

        print_success(">>> Test 5 通过: 监控功能正常 >>>")
        return True

    except Exception as e:
        print_error(f"Test 5 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Story 11.6 DataSyncScheduler 快速集成验证{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    # 创建临时测试目录
    test_dir = Path(tempfile.mkdtemp(prefix="story_11_6_test_"))
    print_info(f"测试目录: {test_dir}")

    results = {}

    try:
        # Step 0: 环境验证
        if not verify_test_environment():
            print_error("环境验证失败，终止测试")
            return False

        # Test 1: 核心同步流程
        results["sync_flow"] = test_sync_flow(test_dir)

        # Test 2: 错误处理
        results["error_handling"] = test_error_handling(test_dir)

        # Test 3: 数据归档
        results["archiving"] = test_archiving(test_dir)

        # Test 4: 磁盘空间管理
        results["disk_management"] = test_disk_space_management(test_dir)

        # Test 5: 监控功能
        results["monitoring"] = test_monitoring(test_dir)

    finally:
        # 清理测试目录
        print_header("清理测试环境")
        try:
            shutil.rmtree(test_dir)
            print_success(f"测试目录已删除: {test_dir}")
        except Exception as e:
            print_error(f"清理失败: {e}")

    # 打印总结
    print_header("测试总结")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name:20s}: {status}")

    print(f"\n{Colors.BOLD}总计: {passed}/{total} 通过{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}>>> 所有测试通过！DataSyncScheduler核心功能正常 >>>{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}>>> 部分测试失败，请检查实现 >>>{Colors.END}\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
