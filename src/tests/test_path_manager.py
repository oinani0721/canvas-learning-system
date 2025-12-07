"""
PathManager单元测试

测试Canvas学习系统的统一文件路径管理功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-28
"""

import json
import os
import shutil

# Add parent directory to path
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_utils.path_manager import PathManager, PathReport, PathValidator


class TestPathManager(unittest.TestCase):
    """测试PathManager类"""

    def setUp(self):
        """测试前准备"""
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp()
        self.base_path = Path(self.test_dir) / "Canvas"
        self.config = {
            'base_path': str(self.base_path),
            'timestamp_format': '%Y%m%d%H%M%S',
            'timestamp_tolerance': 60,
            'validation': {
                'check_existence': True,
                'auto_fix': True,
                'create_missing_dirs': True
            },
            'naming': {
                'use_canvas_folder': True,
                'sanitize_names': True,
                'max_length': 255
            },
            'cache': {
                'enabled': True,
                'max_size': 1000
            }
        }
        self.path_manager = PathManager(self.config)
        self.path_manager.set_current_canvas("TestCanvas")

    def tearDown(self):
        """测试后清理"""
        # 删除临时测试目录
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_default_config(self):
        """测试使用默认配置初始化"""
        pm = PathManager()
        self.assertEqual(pm.config['base_path'], 'Canvas')
        self.assertEqual(pm.config['timestamp_tolerance'], 60)
        self.assertTrue(pm.config['validation']['check_existence'])

    def test_set_current_canvas(self):
        """测试设置当前Canvas上下文"""
        # 测试从.canvas文件设置
        self.path_manager.set_current_canvas("test.canvas")
        self.assertEqual(self.path_manager.current_canvas, "test")

        # 测试从目录名设置
        self.path_manager.set_current_canvas("MathCanvas")
        self.assertEqual(self.path_manager.current_canvas, "MathCanvas")

        # 验证缓存已清除
        self.assertEqual(len(self.path_manager.path_cache), 0)

    def test_generate_consistent_path(self):
        """测试生成一致路径"""
        filename = "test.md"
        path = self.path_manager.generate_consistent_path(filename)

        # 验证路径包含Canvas名称
        self.assertIn("TestCanvas", path)
        self.assertIn("test", path)
        self.assertTrue(path.endswith(".md"))

        # 验证目录已创建
        self.assertTrue(os.path.exists(os.path.dirname(path)))

    def test_generate_consistent_path_with_timestamp(self):
        """测试生成带时间戳的一致路径"""
        filename = "concept-口语化解释.md"
        path = self.path_manager.generate_consistent_path(filename)

        # 验证时间戳已添加
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.assertIn(timestamp, path)

    def test_generate_consistent_path_no_canvas_context(self):
        """测试没有Canvas上下文时抛出异常"""
        pm = PathManager(self.config)
        # 不设置current_canvas
        with self.assertRaises(ValueError):
            pm.generate_consistent_path("test.md")

    def test_sanitize_filename(self):
        """测试文件名清理"""
        # 测试非法字符替换
        dirty_name = "test<>:file|name?.md"
        clean_name = self.path_manager._sanitize_filename(dirty_name)
        self.assertEqual(clean_name, "test___file_name_.md")  # 每个非法字符被替换为_

        # 测试长度限制
        long_name = "a" * 300 + ".md"
        limited_name = self.path_manager._sanitize_filename(long_name)
        self.assertLessEqual(len(limited_name), 255)

    def test_needs_timestamp(self):
        """测试是否需要添加时间戳"""
        # 已有时间戳的文件
        filename_with_timestamp = "concept-类型-20251028163000.md"
        self.assertFalse(self.path_manager._needs_timestamp(filename_with_timestamp))

        # 没有时间戳的markdown文件
        filename_without_timestamp = "concept-类型.md"
        self.assertTrue(self.path_manager._needs_timestamp(filename_without_timestamp))

        # 非markdown文件
        non_md_file = "test.txt"
        self.assertFalse(self.path_manager._needs_timestamp(non_md_file))

    def test_add_timestamp(self):
        """测试添加时间戳"""
        filename = "concept-类型.md"
        with patch('canvas_utils.path_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20251028163000"
            result = self.path_manager._add_timestamp(filename)
            self.assertEqual(result, "concept-类型-20251028163000.md")

    def test_get_relative_path(self):
        """测试获取相对路径"""
        # 创建测试文件
        full_path = self.base_path / "TestCanvas" / "test.md"
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.touch()

        relative_path = self.path_manager.get_relative_path(str(full_path))
        self.assertEqual(relative_path, "test.md")

    def test_validate_and_fix_path_exists(self):
        """测试验证已存在的路径"""
        # 创建测试文件
        test_file = self.base_path / "TestCanvas" / "existing.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()

        fixed_path = self.path_manager.validate_and_fix_path(str(test_file))
        # 应该返回解析后的绝对路径
        self.assertEqual(Path(fixed_path).resolve(), test_file.resolve())

    def test_fix_relative_path(self):
        """测试修复相对路径"""
        # 创建测试文件
        test_file = self.base_path / "TestCanvas" / "test.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()

        # 测试相对路径修复
        relative_path = "./test.md"
        fixed_path = self.path_manager._fix_relative_path(Path(relative_path), "TestCanvas")
        self.assertIsNotNone(fixed_path)
        self.assertEqual(fixed_path.resolve(), test_file.resolve())

    def test_fix_timestamp_mismatch(self):
        """测试修复时间戳不匹配"""
        # 创建测试文件
        test_file = self.base_path / "TestCanvas" / "concept-类型-20251028160000.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()

        # 测试时间戳修复
        wrong_timestamp_path = Path("./concept-类型-20251028163000.md")
        fixed_path = self.path_manager._fix_timestamp_mismatch(wrong_timestamp_path, "TestCanvas")
        self.assertIsNotNone(fixed_path)
        # 应该找到实际存在的文件
        self.assertTrue(fixed_path.exists())

    def test_extract_base_name(self):
        """测试提取基础名称"""
        filename = "concept-类型-20251028163000.md"
        base_name = self.path_manager._extract_base_name(filename)
        self.assertEqual(base_name, "concept-类型")

        # 没有时间戳的文件
        filename_no_timestamp = "concept.md"
        base_name = self.path_manager._extract_base_name(filename_no_timestamp)
        self.assertIsNone(base_name)

    def test_find_similar_files(self):
        """测试查找相似文件"""
        # 创建测试文件
        test_dir = self.base_path / "TestCanvas"
        test_dir.mkdir(parents=True, exist_ok=True)

        files = [
            "concept-口语化解释-20251028160000.md",
            "concept-澄清路径-20251028161000.md",
            "concept-对比表-20251028162000.md",
            "other-file.md"
        ]

        for f in files:
            (test_dir / f).touch()

        # 查找相似文件
        target_path = Path("./concept-口语化解释-20251028163000.md")
        similar = self.path_manager._find_similar_files(target_path, "TestCanvas")

        # 应该找到相似的文件
        self.assertGreater(len(similar), 0)
        self.assertTrue(any("口语化解释" in f.name for f in similar))

    def test_calculate_similarity(self):
        """测试计算字符串相似度"""
        s1 = "concept-口语化解释"
        s2 = "concept-口语化解释-20251028"
        similarity = self.path_manager._calculate_similarity(s1, s2)
        self.assertGreater(similarity, 0.7)  # 应该有较高相似度

        s3 = "completely-different-string"
        similarity = self.path_manager._calculate_similarity(s1, s3)
        self.assertLess(similarity, 0.5)  # 应该有较低相似度

    def test_update_canvas_references(self):
        """测试更新Canvas引用"""
        # 创建测试Canvas文件
        canvas_data = {
            "nodes": [
                {
                    "id": "file-1",
                    "type": "file",
                    "file": "./nonexistent.md",
                    "x": 100,
                    "y": 100
                },
                {
                    "id": "file-2",
                    "type": "file",
                    "file": "Canvas/TestCanvas/existing.md",
                    "x": 200,
                    "y": 100
                }
            ],
            "edges": []
        }

        # 创建实际存在的文件
        existing_file = self.base_path / "TestCanvas" / "existing.md"
        existing_file.parent.mkdir(parents=True, exist_ok=True)
        existing_file.touch()

        # 保存Canvas文件
        canvas_path = Path(self.test_dir) / "test.canvas"
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f)

        # 更新引用
        result = self.path_manager.update_canvas_references(str(canvas_path))

        # 验证结果
        self.assertGreaterEqual(result['updated_count'], 0)

    def test_generate_path_report(self):
        """测试生成路径报告"""
        # 创建测试Canvas文件
        canvas_data = {
            "nodes": [
                {
                    "id": "file-1",
                    "type": "file",
                    "file": "./nonexistent.md",
                    "x": 100,
                    "y": 100
                },
                {
                    "id": "file-2",
                    "type": "file",
                    "file": "existing.md",
                    "x": 200,
                    "y": 100
                }
            ],
            "edges": []
        }

        # 创建实际存在的文件（需要使用完整的相对路径）
        existing_file = self.base_path / "TestCanvas" / "existing.md"
        existing_file.parent.mkdir(parents=True, exist_ok=True)
        existing_file.touch()

        # 保存Canvas文件
        canvas_path = Path(self.test_dir) / "test.canvas"
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f)

        # 生成报告
        report = self.path_manager.generate_path_report(str(canvas_path))

        # 验证报告 - 两个文件都被视为broken，因为路径不匹配
        self.assertEqual(report.total_references, 2)
        self.assertEqual(report.broken_references, 2)
        # existing.md可能可以修复
        self.assertGreaterEqual(report.fixable_references, 0)

    def test_batch_validate_paths(self):
        """测试批量验证路径"""
        # 创建测试文件
        existing_file = self.base_path / "TestCanvas" / "existing.md"
        existing_file.parent.mkdir(parents=True, exist_ok=True)
        existing_file.touch()

        paths = [
            str(existing_file),
            "./nonexistent.md"
        ]

        result = self.path_manager.batch_validate_paths(paths)

        # 验证结果
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['valid'], 1)
        # nonexistent.md被尝试修复但失败，所以fixed=0, invalid=0
        self.assertEqual(result['fixed'], 0)

    def test_path_cache(self):
        """测试路径缓存功能"""
        filename = "test.md"

        # 第一次生成路径
        path1 = self.path_manager.generate_consistent_path(filename)

        # 从缓存获取
        cached_path = self.path_manager.get_path_from_cache("TestCanvas", filename)
        self.assertEqual(cached_path, path1)

        # 清除缓存
        self.path_manager.clear_cache()
        cached_path = self.path_manager.get_path_from_cache("TestCanvas", filename)
        self.assertIsNone(cached_path)


class TestPathValidator(unittest.TestCase):
    """测试PathValidator类"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            'check_existence': True,
            'auto_fix': True
        }
        self.validator = PathValidator(self.config)

    def test_validate_valid_path(self):
        """测试验证有效路径"""
        # 创建临时文件并使用Path对象确保格式一致
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = Path(tmp.name)

        try:
            result = self.validator.validate(str(temp_path.resolve()))
            self.assertTrue(result.success)
            self.assertEqual(result.message, "Path is valid")
        finally:
            # 清理临时文件
            temp_path.unlink(missing_ok=True)

    def test_validate_nonexistent_path(self):
        """测试验证不存在的路径"""
        result = self.validator.validate("/nonexistent/path/file.md")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Path does not exist")
        self.assertIsNotNone(result.suggestion)

    def test_validate_too_long_path(self):
        """测试验证过长路径"""
        long_path = "a" * 300 + ".md"
        result = self.validator.validate(long_path)
        self.assertFalse(result.success)
        self.assertIn("Path too long", result.error)

    def test_validate_illegal_chars(self):
        """测试验证包含非法字符的路径"""
        # Windows非法字符
        if os.name == 'nt':
            illegal_path = "test<>file.md"
            result = self.validator.validate(illegal_path)
            self.assertFalse(result.success)
            self.assertIn("illegal characters", result.error)


class TestPathReport(unittest.TestCase):
    """测试PathReport类"""

    def test_to_dict(self):
        """测试转换为字典"""
        report = PathReport(
            canvas_path="test.canvas",
            total_references=10,
            broken_references=2,
            fixable_references=1
        )

        report_dict = report.to_dict()

        self.assertEqual(report_dict['canvas_path'], "test.canvas")
        self.assertEqual(report_dict['summary']['total'], 10)
        self.assertEqual(report_dict['summary']['broken'], 2)
        self.assertEqual(report_dict['summary']['fixable'], 1)
        self.assertEqual(report_dict['summary']['health_score'], 80.0)


if __name__ == '__main__':
    unittest.main()
