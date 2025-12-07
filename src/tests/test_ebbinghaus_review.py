"""
艾宾浩斯复习调度系统单元测试

测试EbbinghausReviewScheduler类的核心算法功能，确保：
- 记忆保持率计算精度误差<1%
- 复习间隔选择逻辑正确
- 边界条件处理正确

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import math
import os
import sqlite3
import tempfile

import pytest

from ebbinghaus_review import DEFAULT_REVIEW_INTERVALS, EbbinghausReviewScheduler


class TestEbbinghausReviewScheduler:
    """EbbinghausReviewScheduler类测试"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 使用临时数据库文件进行测试
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.scheduler = EbbinghausReviewScheduler(self.temp_db.name)

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 删除临时数据库文件
        if os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except (PermissionError, OSError):
                # 在Windows上可能无法立即删除文件，跳过
                pass

    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        # 测试使用默认数据库路径
        scheduler1 = EbbinghausReviewScheduler()
        assert scheduler1.db_path == "data/review_data.db"

        # 测试使用自定义数据库路径
        custom_path = "test_custom.db"
        scheduler2 = EbbinghausReviewScheduler(custom_path)
        assert scheduler2.db_path == custom_path

        # 验证数据库表已创建
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'review_schedules' in tables
            assert 'review_history' in tables
            assert 'user_review_stats' in tables

    def test_calculate_retention_rate_basic(self):
        """测试基本记忆保持率计算"""
        # 标准案例: 记忆强度S=10，时间t=10天
        expected = math.exp(-10/10)  # = 0.3679...
        actual = self.scheduler.calculate_retention_rate(10, 10)

        # 验证精度要求误差<1%
        assert math.isclose(actual, expected, rel_tol=0.01), f"期望值: {expected}, 实际值: {actual}"
        assert 0 <= actual <= 1

    def test_calculate_retention_rate_zero_time(self):
        """测试时间间隔为0的情况"""
        result = self.scheduler.calculate_retention_rate(0, 10)
        assert math.isclose(result, 1.0, rel_tol=0.01)  # 初始记忆保持率应为100%

    def test_calculate_retention_rate_large_time(self):
        """测试长时间间隔后的记忆保持率"""
        # 长时间后记忆保持率应接近0
        result = self.scheduler.calculate_retention_rate(100, 10)
        assert result < 0.01  # 应接近0但仍为正值

    def test_calculate_retention_rate_different_strengths(self):
        """测试不同记忆强度下的保持率"""
        time = 7  # 7天

        # 记忆强度越大，保持率应该越高
        rate_s5 = self.scheduler.calculate_retention_rate(time, 5)
        rate_s10 = self.scheduler.calculate_retention_rate(time, 10)
        rate_s20 = self.scheduler.calculate_retention_rate(time, 20)

        assert rate_s5 < rate_s10 < rate_s20

    def test_calculate_retention_rate_invalid_inputs(self):
        """测试无效输入的错误处理"""
        # 负数记忆强度
        with pytest.raises(ValueError, match="记忆强度必须大于0"):
            self.scheduler.calculate_retention_rate(10, -1)

        # 零记忆强度
        with pytest.raises(ValueError, match="记忆强度必须大于0"):
            self.scheduler.calculate_retention_rate(10, 0)

        # 负数时间间隔
        with pytest.raises(ValueError, match="时间间隔不能为负数"):
            self.scheduler.calculate_retention_rate(-5, 10)

    def test_calculate_optimal_review_interval_basic(self):
        """测试基本复习间隔计算"""
        current_strength = 10.0

        # 低评分应该推荐短间隔
        interval_score_3 = self.scheduler.calculate_optimal_review_interval(3, current_strength)
        interval_score_5 = self.scheduler.calculate_optimal_review_interval(5, current_strength)
        interval_score_8 = self.scheduler.calculate_optimal_review_interval(8, current_strength)

        assert interval_score_3 in DEFAULT_REVIEW_INTERVALS
        assert interval_score_5 in DEFAULT_REVIEW_INTERVALS
        assert interval_score_8 in DEFAULT_REVIEW_INTERVALS

        # 高评分应该推荐更长间隔
        assert interval_score_8 >= interval_score_5

    def test_calculate_optimal_review_interval_score_mapping(self):
        """测试评分到间隔的映射逻辑"""
        current_strength = 10.0

        # 测试不同评分对应的间隔
        for score in range(1, 11):
            interval = self.scheduler.calculate_optimal_review_interval(score, current_strength)
            assert interval in DEFAULT_REVIEW_INTERVALS
            assert isinstance(interval, int)
            assert interval > 0

    def test_calculate_optimal_review_interval_invalid_scores(self):
        """测试无效评分的错误处理"""
        current_strength = 10.0

        # 低于最小评分
        with pytest.raises(ValueError, match="复习评分必须在1-10之间"):
            self.scheduler.calculate_optimal_review_interval(0, current_strength)

        # 高于最大评分
        with pytest.raises(ValueError, match="复习评分必须在1-10之间"):
            self.scheduler.calculate_optimal_review_interval(11, current_strength)

        # 负数评分
        with pytest.raises(ValueError, match="复习评分必须在1-10之间"):
            self.scheduler.calculate_optimal_review_interval(-1, current_strength)

    def test_calculate_optimal_review_interval_invalid_strength(self):
        """测试无效记忆强度的错误处理"""
        # 负数记忆强度
        with pytest.raises(ValueError, match="记忆强度必须大于0"):
            self.scheduler.calculate_optimal_review_interval(5, -1)

        # 零记忆强度
        with pytest.raises(ValueError, match="记忆强度必须大于0"):
            self.scheduler.calculate_optimal_review_interval(5, 0)

    def test_retention_rate_calculation_accuracy(self):
        """验证记忆保持率计算精度"""
        # 标准验证案例
        test_cases = [
            (1, 10, math.exp(-0.1)),    # 1天，S=10
            (5, 10, math.exp(-0.5)),    # 5天，S=10
            (10, 20, math.exp(-0.5)),    # 10天，S=20
            (30, 15, math.exp(-2.0)),    # 30天，S=15
        ]

        for time, strength, expected in test_cases:
            actual = self.scheduler.calculate_retention_rate(time, strength)

            # 验证精度要求误差<1%
            assert math.isclose(actual, expected, rel_tol=0.01), \
                f"时间={time}, 强度={strength}: 期望={expected:.6f}, 实际={actual:.6f}"

    def test_algorithm_mathematical_properties(self):
        """测试算法的数学特性"""
        strength = 15.0

        # 特性1: 时间增加，保持率递减
        rate_1day = self.scheduler.calculate_retention_rate(1, strength)
        rate_7days = self.scheduler.calculate_retention_rate(7, strength)
        rate_30days = self.scheduler.calculate_retention_rate(30, strength)

        assert rate_1day > rate_7days > rate_30days

        # 特性2: 强度增加，保持率增加
        time = 10
        rate_weak = self.scheduler.calculate_retention_rate(time, 5)
        rate_medium = self.scheduler.calculate_retention_rate(time, 15)
        rate_strong = self.scheduler.calculate_retention_rate(time, 30)

        assert rate_weak < rate_medium < rate_strong

        # 特性3: 保持率范围在[0,1]之间
        for t in range(0, 100, 10):
            for s in [1, 5, 10, 20, 50]:
                rate = self.scheduler.calculate_retention_rate(t, s)
                assert 0 <= rate <= 1

class TestMemoryStrengthAdjustment:
    """测试记忆强度动态调整功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.scheduler = EbbinghausReviewScheduler(self.temp_db.name)

    def teardown_method(self):
        """每个测试方法后的清理"""
        if os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except (PermissionError, OSError):
                pass

    def test_adjust_memory_strength_neutral_score(self):
        """测试中性评分(5分)的记忆强度调整"""
        initial_strength = 10.0
        score = 5  # 中性评分

        adjusted_strength = self.scheduler.adjust_memory_strength(initial_strength, score)

        # 5分应该保持当前强度不变
        assert math.isclose(adjusted_strength, initial_strength, rel_tol=0.01)

    def test_adjust_memory_strength_high_scores(self):
        """测试高分对记忆强度的增强效果"""
        initial_strength = 10.0

        # 测试不同高分
        for score in [6, 7, 8, 9, 10]:
            adjusted_strength = self.scheduler.adjust_memory_strength(initial_strength, score)

            # 高分应该增加记忆强度
            assert adjusted_strength > initial_strength
            assert adjusted_strength <= 100.0  # 不应超过最大值

        # 分数越高，增强效果应该越明显
        strength_6 = self.scheduler.adjust_memory_strength(initial_strength, 6)
        strength_10 = self.scheduler.adjust_memory_strength(initial_strength, 10)
        assert strength_10 > strength_6

    def test_adjust_memory_strength_low_scores(self):
        """测试低分对记忆强度的减弱效果"""
        initial_strength = 10.0

        # 测试不同低分
        for score in [1, 2, 3, 4]:
            adjusted_strength = self.scheduler.adjust_memory_strength(initial_strength, score)

            # 低分应该减少记忆强度
            assert adjusted_strength < initial_strength
            assert adjusted_strength >= 0.5  # 不应低于最小值

        # 分数越低，减弱效果应该越明显
        strength_4 = self.scheduler.adjust_memory_strength(initial_strength, 4)
        strength_1 = self.scheduler.adjust_memory_strength(initial_strength, 1)
        assert strength_1 < strength_4

    def test_adjust_memory_strength_custom_factor(self):
        """测试自定义调整因子"""
        initial_strength = 10.0
        score = 8
        custom_factor = 0.3  # 更大的调整因子

        default_adjusted = self.scheduler.adjust_memory_strength(initial_strength, score)
        custom_adjusted = self.scheduler.adjust_memory_strength(initial_strength, score, custom_factor)

        # 更大的调整因子应该产生更明显的调整效果
        assert custom_adjusted > default_adjusted

    def test_adjust_memory_strength_boundary_values(self):
        """测试边界值的处理"""
        initial_strength = 10.0

        # 测试最低评分
        adjusted_min = self.scheduler.adjust_memory_strength(initial_strength, 1)
        assert adjusted_min >= 0.5  # 不应低于最小值

        # 测试最高评分
        adjusted_max = self.scheduler.adjust_memory_strength(initial_strength, 10)
        assert adjusted_max <= 100.0  # 不应超过最大值

    def test_adjust_memory_strength_invalid_inputs(self):
        """测试无效输入的错误处理"""
        initial_strength = 10.0

        # 无效评分
        with pytest.raises(ValueError, match="复习评分必须在1-10之间"):
            self.scheduler.adjust_memory_strength(initial_strength, 0)

        with pytest.raises(ValueError, match="复习评分必须在1-10之间"):
            self.scheduler.adjust_memory_strength(initial_strength, 11)

        # 无效记忆强度
        with pytest.raises(ValueError, match="当前记忆强度必须大于0"):
            self.scheduler.adjust_memory_strength(0, 5)

        # 无效调整因子
        with pytest.raises(ValueError, match="调整因子必须大于0"):
            self.scheduler.adjust_memory_strength(initial_strength, 5, -0.1)

    def test_get_memory_strength_trend_no_data(self):
        """测试无数据时的趋势分析"""
        result = self.scheduler.get_memory_strength_trend([])

        assert result["trend"] == "no_data"
        assert result["recent_scores"] == []
        assert result["strength_progression"] == []
        assert result["average_score"] == 0.0
        assert result["improvement_rate"] == 0.0

    def test_get_memory_strength_trend_insufficient_data(self):
        """测试数据不足时的趋势分析"""
        review_history = [
            {"review_date": "2025-01-20", "score": 7},
            {"review_date": "2025-01-22", "score": 8}
        ]

        result = self.scheduler.get_memory_strength_trend(review_history)

        assert result["trend"] == "insufficient_data"
        assert len(result["recent_scores"]) == 2
        assert result["average_score"] == 7.5
        assert len(result["strength_progression"]) == 2

    def test_get_memory_strength_trend_improving(self):
        """测试成绩上升趋势分析"""
        review_history = [
            {"review_date": "2025-01-15", "score": 5},
            {"review_date": "2025-01-17", "score": 6},
            {"review_date": "2025-01-19", "score": 7},
            {"review_date": "2025-01-21", "score": 8},
            {"review_date": "2025-01-23", "score": 9}
        ]

        result = self.scheduler.get_memory_strength_trend(review_history)

        assert result["trend"] == "improving"
        assert result["improvement_rate"] > 0
        assert len(result["strength_progression"]) == 5
        assert result["average_score"] == 7.0

    def test_get_memory_strength_trend_declining(self):
        """测试成绩下降趋势分析"""
        review_history = [
            {"review_date": "2025-01-15", "score": 9},
            {"review_date": "2025-01-17", "score": 8},
            {"review_date": "2025-01-19", "score": 7},
            {"review_date": "2025-01-21", "score": 6},
            {"review_date": "2025-01-23", "score": 5}
        ]

        result = self.scheduler.get_memory_strength_trend(review_history)

        assert result["trend"] == "declining"
        assert result["improvement_rate"] < 0
        assert len(result["strength_progression"]) == 5
        assert result["average_score"] == 7.0

    def test_strength_progression_accuracy(self):
        """测试记忆强度进展计算的准确性"""
        review_history = [
            {"review_date": "2025-01-20", "score": 7},
            {"review_date": "2025-01-22", "score": 8}
        ]

        result = self.scheduler.get_memory_strength_trend(review_history)
        progression = result["strength_progression"]

        # 验证第一次复习后的强度变化
        first_review = progression[0]
        expected_first_strength = 10.0 * (1.0 + (7 - 5) * 0.2)  # 10.0 * 1.4 = 14.0
        assert math.isclose(first_review["strength_after"], expected_first_strength, rel_tol=0.01)
        assert first_review["strength_before"] == 10.0
        assert first_review["score"] == 7

        # 验证第二次复习后的强度变化
        second_review = progression[1]
        expected_second_strength = 14.0 * (1.0 + (8 - 5) * 0.2)  # 14.0 * 1.6 = 22.4
        assert math.isclose(second_review["strength_after"], expected_second_strength, rel_tol=0.01)
        assert second_review["strength_before"] == expected_first_strength
        assert second_review["score"] == 8

class TestEbbinghausConstants:
    """测试常量定义的正确性"""

    def test_default_intervals(self):
        """测试默认复习间隔定义"""
        assert DEFAULT_REVIEW_INTERVALS == [1, 3, 7, 15, 30]
        assert all(isinstance(interval, int) for interval in DEFAULT_REVIEW_INTERVALS)
        assert all(interval > 0 for interval in DEFAULT_REVIEW_INTERVALS)
        assert DEFAULT_REVIEW_INTERVALS == sorted(DEFAULT_REVIEW_INTERVALS)  # 应该是递增的

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
