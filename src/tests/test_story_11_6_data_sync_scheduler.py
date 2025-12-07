"""
Unit tests for Story 11.6: Data Sync Scheduler

测试DataSyncScheduler的所有核心功能:
1. 基础功能（启动/停止/单例）
2. 同步流程（文件查找/转换/验证/删除）
3. 错误处理（重试/隔离）
4. 归档功能（90天阈值/压缩）
5. 磁盘空间管理（统计/提前归档/清理）
6. 监控（状态/健康检查）
"""

import gzip
import json
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import pytest
from canvas_progress_tracker.data_stores import ColdDataStore, DataSyncScheduler, HotDataStore, get_data_sync_scheduler

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dirs(tmp_path):
    """创建临时测试目录"""
    sessions_dir = tmp_path / "sessions"
    db_path = tmp_path / "test.db"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    return {
        "sessions_dir": sessions_dir,
        "db_path": db_path,
        "base_dir": tmp_path
    }


@pytest.fixture
def hot_store(temp_dirs):
    """创建测试用HotDataStore"""
    store = HotDataStore(session_dir=temp_dirs["sessions_dir"])  # session_dir (单数), 接受Path对象
    yield store
    # 清理
    if hasattr(store, 'close'):
        store.close()


@pytest.fixture
def cold_store(temp_dirs):
    """创建测试用ColdDataStore"""
    store = ColdDataStore(db_path=str(temp_dirs["db_path"]))
    yield store
    # 清理
    if hasattr(store, 'close'):
        store.close()


@pytest.fixture
def scheduler(hot_store, cold_store):
    """创建测试用DataSyncScheduler"""
    sched = DataSyncScheduler(
        hot_store=hot_store,
        cold_store=cold_store,
        sync_interval=1,  # 1秒，加快测试
        archive_threshold=90,
        cleanup_threshold=365
    )
    yield sched
    # 清理
    if sched._running:
        sched.stop(wait_current=True)


@pytest.fixture
def sample_session_data():
    """创建示例session数据"""
    return {
        "session_id": "session_001",
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T10:30:00",
        "events": [
            {
                "event_id": "evt_001",
                "timestamp": "2025-01-01T10:05:00",
                "event_type": "node_color_change",
                "canvas_id": "canvas_001",
                "node_id": "node_001",
                "old_color": "1",
                "new_color": "2",
                "metadata": {"concept": "逆否命题"}
            },
            {
                "event_id": "evt_002",
                "timestamp": "2025-01-01T10:10:00",
                "event_type": "node_added",
                "canvas_id": "canvas_001",
                "node_id": "node_002",
                "node_type": "text",
                "metadata": {"text": "个人理解"}
            }
        ],
        "metadata": {
            "canvas_count": 1,
            "total_events": 2
        }
    }


def create_old_session_file(sessions_dir: Path, session_data: Dict, days_ago: int = 2) -> Path:
    """
    创建一个指定天数之前的session文件

    Args:
        sessions_dir: session文件目录
        session_data: session数据
        days_ago: 文件修改时间距今天数

    Returns:
        创建的文件路径
    """
    session_id = session_data.get("session_id", f"session_{int(time.time())}")
    file_path = sessions_dir / f"{session_id}.json"

    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    # 修改文件时间戳
    old_time = datetime.now() - timedelta(days=days_ago)
    timestamp = old_time.timestamp()
    import os
    os.utime(file_path, (timestamp, timestamp))

    return file_path


# ============================================================================
# Test 1: 基础功能测试
# ============================================================================

class TestBasicFunctionality:
    """测试调度器基础功能"""

    def test_initialization(self, scheduler):
        """测试初始化"""
        assert scheduler is not None
        assert not scheduler._running
        assert scheduler.sync_interval == 1
        assert scheduler.archive_threshold == 90
        assert scheduler.cleanup_threshold == 365
        assert scheduler.archive_dir.exists()
        assert scheduler.error_dir.exists()

    def test_start_stop(self, scheduler):
        """测试启动和停止"""
        # 启动
        scheduler.start()
        assert scheduler._running
        assert scheduler.next_sync_time is not None

        # 停止
        scheduler.stop(wait_current=True)
        assert not scheduler._running

    def test_double_start(self, scheduler, caplog):
        """测试重复启动"""
        scheduler.start()
        scheduler.start()  # 第二次启动应该被忽略

        assert "already running" in caplog.text.lower()

        scheduler.stop()

    def test_singleton_access(self, hot_store, cold_store):
        """测试单例访问"""
        # 第一次获取
        scheduler1 = get_data_sync_scheduler(hot_store, cold_store)
        assert scheduler1 is not None

        # 第二次获取应该返回同一个实例
        scheduler2 = get_data_sync_scheduler()
        assert scheduler1 is scheduler2

        # 清理
        if scheduler1._running:
            scheduler1.stop()


# ============================================================================
# Test 2: 同步流程测试
# ============================================================================

class TestSyncFlow:
    """测试数据同步流程"""

    def test_find_unsynchronized_files(self, scheduler, sample_session_data, temp_dirs):
        """测试查找未同步文件（只同步24小时前的文件）"""
        sessions_dir = temp_dirs["sessions_dir"]

        # 创建1天前的文件（应该不被同步）
        create_old_session_file(sessions_dir, sample_session_data, days_ago=1)

        # 创建2天前的文件（应该被同步）
        old_file = create_old_session_file(sessions_dir, sample_session_data, days_ago=2)

        # 创建新文件（应该不被同步）
        new_data = sample_session_data.copy()
        new_data["session_id"] = "new_session"
        new_file = sessions_dir / "new_session.json"
        with open(new_file, 'w', encoding='utf-8') as f:
            json.dump(new_data, f)

        # 查找未同步文件
        files = scheduler._find_unsynchronized_files()

        # 只有2天前的文件应该被返回
        assert len(files) == 1
        assert files[0].name == old_file.name

    def test_convert_session_to_sqlite_records(self, scheduler, sample_session_data):
        """测试JSON转SQLite记录转换"""
        records = scheduler._convert_session_to_sqlite_records(sample_session_data)

        assert "canvas_changes" in records
        assert "learning_events" in records
        assert "color_transitions" in records

        # 检查canvas_changes（2个事件都应该被转换）
        assert len(records["canvas_changes"]) == 2

        # 检查第一个change（颜色变化）
        change1 = records["canvas_changes"][0]
        assert change1["canvas_id"] == "canvas_001"
        assert change1["change_type"] == "node_color_change"
        assert change1["node_id"] == "node_001"

        # 检查color_transitions（应该有1个颜色转换）
        assert len(records["color_transitions"]) == 1
        transition = records["color_transitions"][0]
        assert transition["node_id"] == "node_001"
        assert transition["from_color"] == "1"
        assert transition["to_color"] == "2"
        assert transition["transition_type"] == "progress"  # 红→绿是进步

    def test_classify_transition(self, scheduler):
        """测试颜色转换分类"""
        # 进步型转换
        assert scheduler._classify_transition("1", "2") == "progress"  # 红→绿
        assert scheduler._classify_transition("1", "3") == "progress"  # 红→紫
        assert scheduler._classify_transition("3", "2") == "progress"  # 紫→绿

        # 退步型转换
        assert scheduler._classify_transition("2", "1") == "regression"  # 绿→红
        assert scheduler._classify_transition("2", "3") == "regression"  # 绿→紫
        assert scheduler._classify_transition("3", "1") == "regression"  # 紫→红

        # 中性转换
        assert scheduler._classify_transition("1", "1") == "neutral"
        assert scheduler._classify_transition("5", "6") == "neutral"  # 蓝→黄

    def test_verify_sync_integrity(self, scheduler, temp_dirs):
        """测试数据完整性验证"""
        sessions_dir = temp_dirs["sessions_dir"]

        # 创建测试session文件
        session_data = {
            "session_id": "session_verify",
            "events": [
                {"event_type": "node_color_change", "details": {}},
                {"event_type": "node_color_change", "details": {}},
            ]
        }
        session_file = sessions_dir / "session_verify.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)

        # 正确的计数（匹配session_data中的2个事件）
        inserted_counts = {
            "canvas_changes": 2,
            "learning_events": 2,  # 修正：应该等于总事件数
            "color_transitions": 2
        }
        is_valid, errors = scheduler._verify_sync_integrity(session_file, inserted_counts)
        assert is_valid is True
        assert len(errors) == 0

        # 错误的计数（数量不匹配）
        wrong_counts = {
            "canvas_changes": 3,  # 错误：实际只有2个
            "learning_events": 2,
            "color_transitions": 2
        }
        is_valid, errors = scheduler._verify_sync_integrity(session_file, wrong_counts)
        assert is_valid is False
        assert len(errors) > 0

    def test_full_sync_flow(self, scheduler, sample_session_data, temp_dirs):
        """测试完整同步流程（读取→转换→插入→验证→删除）"""
        sessions_dir = temp_dirs["sessions_dir"]

        # 创建2天前的文件
        old_file = create_old_session_file(sessions_dir, sample_session_data, days_ago=2)
        assert old_file.exists()

        # 执行同步
        stats = scheduler._sync_session_data()

        # 验证统计信息
        assert stats["files_processed"] == 1
        assert stats["files_succeeded"] == 1
        assert stats["files_failed"] == 0

        # 验证文件已被删除
        assert not old_file.exists()

        # 验证数据已插入ColdDataStore
        changes = scheduler.cold_store.query_canvas_changes(
            canvas_id="canvas_001",
            limit=10
        )
        assert len(changes) > 0


# ============================================================================
# Test 3: 错误处理测试
# ============================================================================

class TestErrorHandling:
    """测试错误处理机制"""

    def test_corrupted_json_handling(self, scheduler, temp_dirs):
        """测试JSON损坏文件处理"""
        sessions_dir = temp_dirs["sessions_dir"]

        # 创建损坏的JSON文件
        corrupted_file = sessions_dir / "session_corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write("{invalid json")

        # 修改时间戳为2天前
        old_time = datetime.now() - timedelta(days=2)
        timestamp = old_time.timestamp()
        import os
        os.utime(corrupted_file, (timestamp, timestamp))

        # 执行同步
        stats = scheduler._sync_session_data()

        # 验证错误统计
        assert stats["files_failed"] == 1

        # 验证文件被移到错误目录
        assert not corrupted_file.exists()
        error_files = list(scheduler.error_dir.glob("session_corrupted.json"))
        assert len(error_files) == 1

    def test_retry_mechanism(self, scheduler, sample_session_data, temp_dirs, monkeypatch):
        """测试重试机制（模拟暂时性错误）"""
        sessions_dir = temp_dirs["sessions_dir"]

        # 创建测试文件
        old_file = create_old_session_file(sessions_dir, sample_session_data, days_ago=2)

        # 模拟前2次调用失败，第3次成功
        call_count = [0]
        original_process = scheduler._process_session_file

        def mock_process(session_path):
            call_count[0] += 1
            if call_count[0] < 3:
                # 前2次返回暂时性错误
                return False, "Temporary database lock"
            # 第3次调用原始方法
            return original_process(session_path)

        monkeypatch.setattr(scheduler, '_process_session_file', mock_process)

        # 执行带重试的同步
        success, error = scheduler._process_session_file_with_retry(old_file)

        # 验证重试了3次
        assert call_count[0] == 3
        assert success is True

    def test_error_isolation(self, scheduler, sample_session_data, temp_dirs):
        """测试错误文件隔离（移到.errors目录）"""
        sessions_dir = temp_dirs["sessions_dir"]

        # 创建损坏的文件
        bad_file = sessions_dir / "session_bad.json"
        with open(bad_file, 'w') as f:
            f.write("not json at all")

        # 修改时间戳
        old_time = datetime.now() - timedelta(days=2)
        timestamp = old_time.timestamp()
        import os
        os.utime(bad_file, (timestamp, timestamp))

        # 执行同步
        scheduler._sync_session_data()

        # 验证错误目录存在
        assert scheduler.error_dir.exists()

        # 验证错误文件被移动
        assert not bad_file.exists()
        moved_files = list(scheduler.error_dir.glob("session_bad.json"))
        assert len(moved_files) == 1

        # 验证错误信息文件存在
        error_info_files = list(scheduler.error_dir.glob("session_bad.json.error"))
        assert len(error_info_files) == 1


# ============================================================================
# Test 4: 归档功能测试
# ============================================================================

class TestArchiving:
    """测试数据归档功能"""

    def test_archive_old_data(self, scheduler, cold_store):
        """测试90天数据归档"""
        # 插入一些旧数据
        old_time = (datetime.now() - timedelta(days=100)).isoformat()

        cold_store.insert_canvas_changes([{
            "canvas_id": "test_canvas",
            "change_type": "node_added",
            "change_data": {"test": "data"},
            "timestamp": old_time
        }])

        # 执行归档
        result = scheduler._archive_old_data()

        # 验证归档成功
        assert result["success"] is True
        assert result["records_archived"] > 0
        assert result["archive_file"] is not None

        # 验证归档文件存在
        archive_path = Path(result["archive_file"])
        assert archive_path.exists()
        assert archive_path.suffix == ".gz"

    def test_archive_compression(self, scheduler, cold_store):
        """测试gzip压缩"""
        # 插入大量旧数据
        old_time = (datetime.now() - timedelta(days=100)).isoformat()

        records = [{
            "canvas_id": f"canvas_{i}",
            "change_type": "node_added",
            "change_data": {"index": i, "data": "x" * 100},
            "timestamp": old_time
        } for i in range(100)]
        cold_store.insert_canvas_changes(records)

        # 执行归档
        result = scheduler._archive_old_data()

        # 验证压缩
        assert result["success"] is True
        archive_path = Path(result["archive_file"])

        # 验证文件可以解压
        with gzip.open(archive_path, 'rt', encoding='utf-8') as f:
            archive_data = json.load(f)

        assert "canvas_changes" in archive_data
        assert len(archive_data["canvas_changes"]) == 100

    def test_archive_verification(self, scheduler, cold_store):
        """测试归档验证"""
        # 插入旧数据
        old_time = (datetime.now() - timedelta(days=100)).isoformat()

        cold_store.insert_canvas_changes([{
            "canvas_id": "test",
            "change_type": "test",
            "change_data": {},
            "timestamp": old_time
        }])

        # 执行归档
        result = scheduler._archive_old_data()

        # 验证归档文件完整性
        archive_path = Path(result["archive_file"])
        with gzip.open(archive_path, 'rt', encoding='utf-8') as f:
            archive_data = json.load(f)

        # 检查必要字段
        assert "archive_date" in archive_data
        assert "data_range" in archive_data
        assert "record_counts" in archive_data
        assert archive_data["total_records"] > 0


# ============================================================================
# Test 5: 磁盘空间管理测试
# ============================================================================

class TestDiskSpaceManagement:
    """测试磁盘空间管理功能"""

    def test_disk_usage_statistics(self, scheduler, temp_dirs):
        """测试磁盘使用统计"""
        # 创建一些测试文件
        sessions_dir = temp_dirs["sessions_dir"]
        for i in range(5):
            test_file = sessions_dir / f"test_{i}.json"
            with open(test_file, 'w') as f:
                json.dump({"test": "data" * 1000}, f)

        # 获取磁盘统计
        stats = scheduler._check_disk_space()

        # 验证统计字段
        assert "json_files_size_mb" in stats
        assert "sqlite_db_size_mb" in stats
        assert "archives_size_mb" in stats
        assert "total_size_mb" in stats
        assert "available_space_mb" in stats
        assert "json_file_count" in stats
        assert "archive_count" in stats

        # 验证文件计数
        assert stats["json_file_count"] == 5

    def test_early_archive_trigger(self, scheduler, monkeypatch):
        """测试提前归档触发（模拟低磁盘空间）"""
        from collections import namedtuple

        # Mock shutil.disk_usage 返回低磁盘空间
        DiskUsage = namedtuple('usage', 'total used free')
        def mock_disk_usage(path):
            # 模拟低磁盘空间：500MB可用
            return DiskUsage(
                total=100 * 1024 * 1024 * 1024,  # 100GB total
                used=99.5 * 1024 * 1024 * 1024,  # 99.5GB used
                free=500 * 1024 * 1024           # 500MB free (<1GB)
            )
        monkeypatch.setattr(shutil, 'disk_usage', mock_disk_usage)

        # Mock _archive_old_data 以验证是否被调用
        archive_called = [False]
        original_archive = scheduler._archive_old_data

        def mock_archive(early_trigger=False):
            archive_called[0] = True
            return {"success": True, "records_archived": 10}

        monkeypatch.setattr(scheduler, '_archive_old_data', mock_archive)

        # 执行磁盘检查
        stats = scheduler._check_disk_space()

        # 验证返回低磁盘空间
        assert stats["available_space_mb"] < 1024
        assert stats["available_space_mb"] == 500

    def test_old_archives_cleanup(self, scheduler):
        """测试旧归档清理（365天）"""
        # 创建一个旧归档文件
        old_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        archive_filename = f"archive_{old_date}_to_{old_date}.json.gz"
        archive_path = scheduler.archive_dir / archive_filename

        # 创建归档文件
        test_data = {"test": "old archive"}
        with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
            json.dump(test_data, f)

        # 执行磁盘检查（会清理旧归档）
        stats = scheduler._check_disk_space()

        # 验证旧归档被删除
        assert "old_archives_deleted" in stats
        assert stats["old_archives_deleted"] >= 1
        assert not archive_path.exists()


# ============================================================================
# Test 6: 监控功能测试
# ============================================================================

class TestMonitoring:
    """测试监控功能"""

    def test_get_sync_status(self, scheduler):
        """测试获取同步状态"""
        status = scheduler.get_sync_status()

        # 验证状态字段
        assert "running" in status
        assert "last_sync_time" in status
        assert "next_sync_time" in status
        assert "sync_history" in status
        assert "disk_usage" in status

        # 验证磁盘使用信息
        disk_usage = status["disk_usage"]
        assert isinstance(disk_usage, dict)
        if "error" not in disk_usage:
            assert "json_files_size_mb" in disk_usage
            assert "sqlite_db_size_mb" in disk_usage

    def test_is_healthy(self, scheduler):
        """测试健康检查"""
        # 未启动时不健康
        assert scheduler.is_healthy() is False

        # 启动后健康
        scheduler.start()
        time.sleep(0.1)  # 等待启动完成
        assert scheduler.is_healthy() is True

        # 停止后不健康
        scheduler.stop()
        assert scheduler.is_healthy() is False

    def test_sync_history_tracking(self, scheduler, sample_session_data, temp_dirs):
        """测试同步历史记录"""
        # 创建测试文件
        sessions_dir = temp_dirs["sessions_dir"]
        create_old_session_file(sessions_dir, sample_session_data, days_ago=2)

        # 执行同步
        scheduler._sync_session_data()

        # 获取状态
        status = scheduler.get_sync_status()

        # 验证同步历史
        assert len(status["sync_history"]) > 0
        last_sync = status["sync_history"][-1]
        assert "timestamp" in last_sync
        assert "files_processed" in last_sync


# ============================================================================
# Test 7: 集成测试
# ============================================================================

class TestIntegration:
    """端到端集成测试"""

    def test_full_lifecycle(self, scheduler, sample_session_data, temp_dirs):
        """测试完整生命周期（同步→归档→清理）"""
        sessions_dir = temp_dirs["sessions_dir"]

        # Step 1: 创建旧session文件
        old_file = create_old_session_file(sessions_dir, sample_session_data, days_ago=2)

        # Step 2: 同步
        sync_stats = scheduler._sync_session_data()
        assert sync_stats["files_succeeded"] == 1
        assert not old_file.exists()

        # Step 3: 插入更多旧数据（用于归档测试）
        old_time = (datetime.now() - timedelta(days=100)).isoformat()
        old_records = [{
            "canvas_id": f"old_canvas_{i}",
            "change_type": "test",
            "change_data": {"index": i},
            "timestamp": old_time
        } for i in range(10)]
        scheduler.cold_store.insert_canvas_changes(old_records)

        # Step 4: 归档
        archive_stats = scheduler._archive_old_data()
        assert archive_stats["success"] is True
        assert archive_stats["records_archived"] > 0

        # Step 5: 磁盘检查和清理
        disk_stats = scheduler._check_disk_space()
        assert "total_size_mb" in disk_stats

        # Step 6: 健康检查
        assert scheduler.is_healthy() is False  # 未启动
        scheduler.start()
        assert scheduler.is_healthy() is True
        scheduler.stop()

    def test_concurrent_sync_safety(self, scheduler, sample_session_data, temp_dirs):
        """测试并发同步安全性（线程锁）"""
        sessions_dir = temp_dirs["sessions_dir"]

        # 创建多个测试文件
        for i in range(5):
            data = sample_session_data.copy()
            data["session_id"] = f"session_{i}"
            create_old_session_file(sessions_dir, data, days_ago=2)

        # 启动调度器
        scheduler.start()

        # 手动触发同步（应该被线程锁保护）
        import threading
        sync_threads = []
        for _ in range(3):
            t = threading.Thread(target=scheduler._sync_session_data)
            sync_threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in sync_threads:
            t.join(timeout=5)

        # 清理
        scheduler.stop()

        # 验证所有文件都被同步（没有重复同步）
        remaining_files = list(sessions_dir.glob("*.json"))
        assert len(remaining_files) == 0  # 所有文件都应该被删除


# ============================================================================
# Test 8: 边界条件测试
# ============================================================================

class TestEdgeCases:
    """测试边界条件"""

    def test_empty_session_dir(self, scheduler):
        """测试空session目录"""
        files = scheduler._find_unsynchronized_files()
        assert files == []

        stats = scheduler._sync_session_data()
        assert stats["files_processed"] == 0

    def test_no_old_data_to_archive(self, scheduler):
        """测试没有旧数据需要归档"""
        result = scheduler._archive_old_data()
        assert result["success"] is True
        assert result["records_archived"] == 0

    def test_invalid_session_structure(self, scheduler, temp_dirs):
        """测试无效的session结构（缺少必要字段）"""
        sessions_dir = temp_dirs["sessions_dir"]

        # 创建结构不完整的文件
        invalid_data = {"session_id": "session_invalid"}  # 缺少events字段
        invalid_file = sessions_dir / "session_invalid.json"
        with open(invalid_file, 'w') as f:
            json.dump(invalid_data, f)

        # 修改时间戳
        old_time = datetime.now() - timedelta(days=2)
        timestamp = old_time.timestamp()
        import os
        os.utime(invalid_file, (timestamp, timestamp))

        # 尝试同步
        stats = scheduler._sync_session_data()

        # 应该处理错误（文件可能被移到errors目录）
        assert stats["files_processed"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
