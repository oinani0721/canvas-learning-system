"""
测试三级记忆记录系统

测试覆盖：
- MemoryRecorder核心功能
- 三级备份系统
- 数据加密/解密
- 验证和恢复机制
- 健康检查
- 并发性能

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-28
"""

import asyncio
import os
import shutil

# 导入要测试的模块
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_utils.memory_recorder import (
    DataEncryption,
    FileLogger,
    LocalMemoryDB,
    MemoryRecord,
    MemoryRecorder,
    MemoryRecordReport,
    RecoveryReport,
    SystemHealthChecker,
    SystemHealthStatus,
    VerificationReport,
    create_memory_recorder,
    quick_record_session,
)


class TestDataEncryption(unittest.TestCase):
    """测试数据加密功能"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.key_path = os.path.join(self.temp_dir, 'test_encryption.key')
        self.encryption = DataEncryption(self.key_path)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    async def test_encrypt_decrypt_data(self):
        """测试数据加密和解密"""
        # 准备测试数据
        test_data = {
            'session_id': 'test_session_001',
            'canvas_path': 'test.canvas',
            'actions': [{'type': 'test', 'data': 'example'}],
            'metadata': {'user_id': 'test_user'}
        }

        # 加密数据
        encrypted = await self.encryption.encrypt(test_data)
        self.assertIn('content', encrypted)
        self.assertIn('encrypted', encrypted)

        # 解密数据
        decrypted = await self.encryption.decrypt(
            encrypted['content'],
            encrypted['encrypted']
        )

        # 验证数据一致性
        self.assertEqual(decrypted, test_data)

    async def test_encrypt_without_cipher(self):
        """测试无加密器时的行为"""
        # 创建一个无法初始化的加密器
        bad_encryption = DataEncryption('/invalid/path/key.key')
        self.assertIsNone(bad_encryption.cipher)

        test_data = {'test': 'data'}
        encrypted = await bad_encryption.encrypt(test_data)

        # 应该返回未加密的数据
        self.assertFalse(encrypted['encrypted'])
        decrypted = await bad_encryption.decrypt(encrypted['content'], False)
        self.assertEqual(decrypted, test_data)

    async def test_key_generation_and_persistence(self):
        """测试密钥生成和持久化"""
        # 验证密钥文件已创建
        self.assertTrue(os.path.exists(self.key_path))

        # 读取密钥
        with open(self.key_path, 'rb') as f:
            key1 = f.read()

        # 创建新的加密器实例，应该加载相同密钥
        encryption2 = DataEncryption(self.key_path)
        with open(self.key_path, 'rb') as f:
            key2 = f.read()

        self.assertEqual(key1, key2)


class TestSystemHealthChecker(unittest.TestCase):
    """测试系统健康检查器"""

    def setUp(self):
        """测试前准备"""
        self.health_checker = SystemHealthChecker(check_interval=1)

    async def test_initial_health_status(self):
        """测试初始健康状态"""
        status = await self.health_checker.check_system_health()
        self.assertIsInstance(status, SystemHealthStatus)
        self.assertTrue(status.is_healthy)

    async def test_failure_counting(self):
        """测试失败计数功能"""
        # 模拟主系统失败
        self.health_checker.status.primary_system_healthy = False
        await self.health_checker._update_failure_counts()

        # 验证失败计数增加
        self.assertEqual(
            self.health_checker.status.consecutive_failures['primary'],
            1
        )

        # 模拟恢复
        self.health_checker.status.primary_system_healthy = True
        await self.health_checker._update_failure_counts()

        # 验证失败计数重置
        self.assertEqual(
            self.health_checker.status.consecutive_failures['primary'],
            0
        )


class TestFileLogger(unittest.TestCase):
    """测试文件日志记录器"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'log_dir': os.path.join(self.temp_dir, 'logs'),
            'max_files': 3
        }
        self.file_logger = FileLogger(self.config)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    async def test_log_record(self):
        """测试记录日志"""
        # 创建测试记录
        record = MemoryRecord(
            id='test_record_001',
            timestamp=datetime.now(),
            session_id='test_session',
            canvas_path='test.canvas',
            user_id='test_user',
            actions=[{'type': 'test'}],
            metadata={}
        )

        # 记录到文件
        success = await self.file_logger.log(record)
        self.assertTrue(success)

        # 验证文件存在
        log_files = list(Path(self.config['log_dir']).glob('memory_*.log'))
        self.assertEqual(len(log_files), 1)

    async def test_get_logs(self):
        """测试获取日志"""
        # 创建并记录多个测试记录
        session_id = 'test_session_001'
        for i in range(3):
            record = MemoryRecord(
                id=f'test_record_{i:03d}',
                timestamp=datetime.now(),
                session_id=session_id,
                canvas_path='test.canvas',
                user_id='test_user',
                actions=[{'type': f'test_{i}'}],
                metadata={}
            )
            await self.file_logger.log(record)

        # 获取日志
        logs = await self.file_logger.get_logs(session_id)
        self.assertEqual(len(logs), 3)

        # 验证日志内容
        for log in logs:
            self.assertEqual(log['session_id'], session_id)
            self.assertIn('source', log)
            self.assertEqual(log['source'], 'tertiary')

    async def test_log_rotation(self):
        """测试日志轮转"""
        # 创建超过限制的日志文件
        dates = [
            datetime(2025, 1, 25),
            datetime(2025, 1, 26),
            datetime(2025, 1, 27),
            datetime(2025, 1, 28),
        ]

        for date in dates:
            record = MemoryRecord(
                id='test_record',
                timestamp=date,
                session_id='test_session',
                canvas_path='test.canvas',
                user_id='test_user',
                actions=[],
                metadata={}
            )
            await self.file_logger.log(record)

        # 检查文件数量（应该保留最新的3个）
        log_files = list(Path(self.config['log_dir']).glob('memory_*.log'))
        self.assertLessEqual(len(log_files), self.config['max_files'])


class TestLocalMemoryDB(unittest.TestCase):
    """测试本地SQLite数据库"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'path': os.path.join(self.temp_dir, 'test_memory.db'),
            'backup_path': os.path.join(self.temp_dir, 'test_memory_backup.db'),
            'max_size_mb': 1
        }
        self.db = LocalMemoryDB(self.config)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    async def test_database_initialization(self):
        """测试数据库初始化"""
        await self.db.initialize()

        # 验证数据库文件存在
        self.assertTrue(os.path.exists(self.config['path']))

    async def test_record_and_retrieve(self):
        """测试记录和检索"""
        await self.db.initialize()

        # 创建测试记录
        record = MemoryRecord(
            id='test_record_001',
            timestamp=datetime.now(),
            session_id='test_session',
            canvas_path='test.canvas',
            user_id='test_user',
            actions=[{'type': 'test'}],
            metadata={}
        )

        # 记录到数据库
        encrypted_data = b'encrypted_data_placeholder'
        success = await self.db.record(record, encrypted_data)
        self.assertTrue(success)

        # 检索记录
        records = await self.db.get_records('test_session')
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['id'], 'test_record_001')
        self.assertEqual(records[0]['source'], 'backup')

    async def test_database_backup(self):
        """测试数据库备份"""
        await self.db.initialize()

        # 记录一些数据
        record = MemoryRecord(
            id='test_record',
            timestamp=datetime.now(),
            session_id='test_session',
            canvas_path='test.canvas',
            user_id='test_user',
            actions=[],
            metadata={}
        )
        await self.db.record(record, b'data')

        # 执行备份
        success = await self.db.backup()
        self.assertTrue(success)

        # 验证备份文件存在
        self.assertTrue(os.path.exists(self.config['backup_path']))


class TestMemoryRecorder(unittest.TestCase):
    """测试记忆记录器核心功能"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

        # 创建测试配置
        self.config = {
            'graphiti': {
                'enabled': False  # 测试时禁用Graphiti
            },
            'local_db': {
                'enabled': True,
                'path': os.path.join(self.temp_dir, 'test_memory.db'),
                'backup_path': os.path.join(self.temp_dir, 'test_memory_backup.db'),
                'always_backup': True
            },
            'file_logger': {
                'enabled': True,
                'log_dir': os.path.join(self.temp_dir, 'logs'),
                'max_files': 10
            },
            'encryption': {
                'enabled': True,
                'key_path': os.path.join(self.temp_dir, 'test_encryption.key')
            }
        }

        self.recorder = MemoryRecorder(self.config)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    async def test_recorder_initialization(self):
        """测试记录器初始化"""
        await self.recorder.initialize()
        self.assertTrue(self.recorder._initialized)
        self.assertIsNotNone(self.recorder._backup_system)
        self.assertIsNotNone(self.recorder._file_logger)

    async def test_record_session_success(self):
        """测试成功记录会话"""
        await self.recorder.initialize()

        # 准备会话数据
        session_data = {
            'session_id': 'test_session_001',
            'canvas_path': 'test.canvas',
            'user_id': 'test_user',
            'actions': [
                {'type': 'agent_call', 'agent': 'scoring-agent'},
                {'type': 'node_update', 'node_id': 'node-001'}
            ],
            'metadata': {
                'duration_minutes': 30,
                'score': 85
            }
        }

        # 记录会话
        report = await self.recorder.record_session(session_data)

        # 验证报告
        self.assertIsInstance(report, MemoryRecordReport)
        self.assertIsNotNone(report.record_id)
        self.assertGreater(len(report.successful_systems), 0)
        self.assertIn('backup', report.successful_systems)
        self.assertIn('tertiary', report.successful_systems)

    async def test_record_session_with_primary_failure(self):
        """测试主系统失败时的行为"""
        await self.recorder.initialize()

        # 禁用主系统
        self.recorder.config['graphiti']['enabled'] = False

        session_data = {
            'session_id': 'test_session_002',
            'canvas_path': 'test.canvas',
            'actions': []
        }

        report = await self.recorder.record_session(session_data)

        # 应该仍然成功（备份和文件系统工作）
        self.assertGreater(len(report.successful_systems), 0)
        self.assertNotIn('primary', report.successful_systems)

    async def test_verify_records(self):
        """测试记录验证"""
        await self.recorder.initialize()

        # 记录一些会话
        session_id = 'test_session_verify'
        for i in range(3):
            session_data = {
                'session_id': session_id,
                'canvas_path': 'test.canvas',
                'actions': [{'type': f'action_{i}'}]
            }
            await self.recorder.record_session(session_data)

        # 验证记录
        verification = await self.recorder.verify_records(session_id)

        self.assertIsInstance(verification, VerificationReport)
        self.assertEqual(verification.session_id, session_id)
        self.assertGreater(verification.total_unique_records, 0)

    async def test_recover_records(self):
        """测试记录恢复"""
        await self.recorder.initialize()

        # 记录会话
        session_id = 'test_session_recover'
        session_data = {
            'session_id': session_id,
            'canvas_path': 'test.canvas',
            'actions': []
        }
        await self.recorder.record_session(session_data)

        # 尝试恢复
        recovery = await self.recorder.recover_records(session_id)

        self.assertIsInstance(recovery, RecoveryReport)
        self.assertEqual(recovery.session_id, session_id)

    async def test_get_statistics(self):
        """测试获取统计信息"""
        await self.recorder.initialize()

        # 记录一些会话
        for i in range(5):
            session_data = {
                'session_id': f'test_session_stats_{i}',
                'canvas_path': 'test.canvas',
                'actions': []
            }
            await self.recorder.record_session(session_data)

        # 获取统计
        stats = await self.recorder.get_statistics()

        self.assertIn('statistics', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('system_health', stats)
        self.assertEqual(stats['statistics']['total_records'], 5)

    async def test_get_system_health(self):
        """测试获取系统健康状态"""
        await self.recorder.initialize()

        health = await self.recorder.get_system_health()

        self.assertIsInstance(health, SystemHealthStatus)
        self.assertIn('last_check', str(health))
        self.assertTrue(health.is_healthy)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    async def test_create_memory_recorder_function(self):
        """测试便捷创建函数"""
        config = {
            'local_db': {
                'enabled': True,
                'path': os.path.join(self.temp_dir, 'integration_test.db')
            },
            'file_logger': {
                'enabled': True,
                'log_dir': os.path.join(self.temp_dir, 'logs')
            },
            'graphiti': {
                'enabled': False
            }
        }

        recorder = await create_memory_recorder(config)
        self.assertIsInstance(recorder, MemoryRecorder)
        self.assertTrue(recorder._initialized)

    async def test_quick_record_session_function(self):
        """测试快速记录函数"""
        report = await quick_record_session(
            session_id='quick_test_session',
            canvas_path='quick_test.canvas',
            actions=[{'type': 'quick_test'}],
            metadata={'test': True}
        )

        self.assertIsInstance(report, MemoryRecordReport)
        self.assertIsNotNone(report.record_id)

    async def test_concurrent_recording(self):
        """测试并发记录"""
        config = {
            'local_db': {
                'enabled': True,
                'path': os.path.join(self.temp_dir, 'concurrent_test.db')
            },
            'file_logger': {
                'enabled': True,
                'log_dir': os.path.join(self.temp_dir, 'logs')
            },
            'graphiti': {
                'enabled': False
            }
        }

        recorder = await create_memory_recorder(config)

        # 并发记录多个会话
        tasks = []
        for i in range(10):
            session_data = {
                'session_id': f'concurrent_session_{i}',
                'canvas_path': 'concurrent_test.canvas',
                'actions': [{'type': 'concurrent_test', 'index': i}]
            }
            task = recorder.record_session(session_data)
            tasks.append(task)

        # 等待所有任务完成
        reports = await asyncio.gather(*tasks)

        # 验证所有记录都成功
        self.assertEqual(len(reports), 10)
        for report in reports:
            self.assertGreater(len(report.successful_systems), 0)


class TestStress(unittest.TestCase):
    """压力测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    async def test_large_volume_recording(self):
        """测试大量记录"""
        config = {
            'local_db': {
                'enabled': True,
                'path': os.path.join(self.temp_dir, 'stress_test.db')
            },
            'file_logger': {
                'enabled': True,
                'log_dir': os.path.join(self.temp_dir, 'logs')
            },
            'graphiti': {
                'enabled': False
            }
        }

        recorder = await create_memory_recorder(config)

        # 记录大量会话
        start_time = datetime.now()
        num_records = 100

        for i in range(num_records):
            session_data = {
                'session_id': f'stress_session_{i:04d}',
                'canvas_path': 'stress_test.canvas',
                'actions': [{'type': 'stress_test', 'index': i}],
                'metadata': {
                    'large_data': 'x' * 1000,  # 1KB数据
                    'timestamp': datetime.now().isoformat()
                }
            }
            await recorder.record_session(session_data)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 验证性能（每秒至少10条记录）
        self.assertGreater(num_records / duration, 10)

        # 验证统计
        stats = await recorder.get_statistics()
        self.assertEqual(stats['statistics']['total_records'], num_records)

    async def test_long_running_session(self):
        """测试长时间运行会话"""
        config = {
            'local_db': {
                'enabled': True,
                'path': os.path.join(self.temp_dir, 'long_running.db')
            },
            'file_logger': {
                'enabled': True,
                'log_dir': os.path.join(self.temp_dir, 'logs')
            },
            'graphiti': {
                'enabled': False
            }
        }

        recorder = await create_memory_recorder(config)

        # 模拟长时间会话（记录间隔增长）
        session_start = datetime.now()
        for i in range(20):
            session_data = {
                'session_id': 'long_running_session',
                'canvas_path': 'long_running.canvas',
                'actions': [{
                    'type': 'progress_update',
                    'step': i,
                    'timestamp': datetime.now().isoformat()
                }]
            }
            await recorder.record_session(session_data)

            # 间隔递增
            await asyncio.sleep(0.01)

        # 验证所有记录都保存了
        verification = await recorder.verify_records('long_running_session')
        self.assertGreater(verification.total_unique_records, 15)


# 测试运行器
class TestRunner:
    """测试运行器"""

    @staticmethod
    async def run_all_tests():
        """运行所有测试"""
        test_classes = [
            TestDataEncryption,
            TestSystemHealthChecker,
            TestFileLogger,
            TestLocalMemoryDB,
            TestMemoryRecorder,
            TestIntegration,
            TestStress
        ]

        total_tests = 0
        passed_tests = 0
        failed_tests = []

        for test_class in test_classes:
            print(f"\n运行 {test_class.__name__} 测试...")

            # 创建测试套件
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)

            # 运行测试
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)

            total_tests += result.testsRun
            passed_tests += result.testsRun - len(result.failures) - len(result.errors)

            if result.failures:
                failed_tests.extend([
                    (test_class.__name__, f[0], f[1])
                    for f in result.failures
                ])

            if result.errors:
                failed_tests.extend([
                    (test_class.__name__, e[0], e[1])
                    for e in result.errors
                ])

        # 打印总结
        print(f"\n{'='*60}")
        print("测试总结")
        print(f"{'='*60}")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {len(failed_tests)}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests:
            print("\n失败的测试:")
            for class_name, test_name, error in failed_tests[:5]:  # 只显示前5个
                print(f"  - {class_name}.{test_name}: {error[:100]}...")

        return total_tests == passed_tests


if __name__ == '__main__':
    # 运行测试
    print("开始运行三级记忆记录系统测试...")
    success = asyncio.run(TestRunner.run_all_tests())

    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败，请检查上述错误信息。")
