"""
艾宾浩斯复习调度系统 - Canvas学习系统v2.0

基于艾宾浩斯遗忘曲线的智能复习调度算法实现。
该模块提供科学的记忆保持率计算和个性化复习间隔调度功能。

核心算法: R(t) = e^(-t/S)
其中:
- R(t): t时间后的记忆保持率 (0-1)
- t: 时间间隔 (天)
- S: 记忆强度参数 (根据用户表现动态调整)

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import math
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# ========== 常量定义 ==========

# 默认复习间隔(天)
DEFAULT_REVIEW_INTERVALS = [1, 3, 7, 15, 30]

# 记忆强度参数
DEFAULT_MEMORY_STRENGTH = 10.0
STRENGTH_ADJUSTMENT_FACTOR = 0.2

# 复习评分范围
MIN_REVIEW_SCORE = 1
MAX_REVIEW_SCORE = 10

# 数据库配置
DEFAULT_DB_PATH = "data/review_data.db"

# 颜色代码(与Canvas系统保持一致)
COLOR_RED = "1"      # 不理解
COLOR_GREEN = "2"    # 完全理解
COLOR_PURPLE = "3"   # 似懂非懂
COLOR_YELLOW = "6"   # 个人理解

# ========== EbbinghausReviewScheduler类 ==========

class EbbinghausReviewScheduler:
    """艾宾浩斯复习调度器

    基于遗忘曲线理论实现智能复习调度，支持：
    - 记忆保持率计算
    - 动态记忆强度调整
    - 个性化复习间隔
    - SQLite数据存储
    - Canvas集成
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """初始化复习调度器

        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path
        self._ensure_database_exists()
        self._create_tables()

    def calculate_retention_rate(self, time_elapsed_days: float, memory_strength: float) -> float:
        """计算记忆保持率

        基于艾宾浩斯遗忘曲线公式: R(t) = e^(-t/S)

        Args:
            time_elapsed_days: 经过的时间(天)
            memory_strength: 记忆强度参数S

        Returns:
            float: 记忆保持率 (0-1)

        Example:
            >>> scheduler = EbbinghausReviewScheduler()
            >>> rate = scheduler.calculate_retention_rate(10, 10)
            >>> print(f"10天后的记忆保持率: {rate:.3f}")
        """
        if memory_strength <= 0:
            raise ValueError("记忆强度必须大于0")

        if time_elapsed_days < 0:
            raise ValueError("时间间隔不能为负数")

        # 艾宾浩斯遗忘曲线公式
        retention_rate = math.exp(-time_elapsed_days / memory_strength)

        # 确保返回值在合理范围内
        return max(0.0, min(1.0, retention_rate))

    def adjust_memory_strength(self, current_strength: float, last_review_score: int,
                           adjustment_factor: float = STRENGTH_ADJUSTMENT_FACTOR) -> float:
        """调整记忆强度参数

        基于用户复习评分动态调整记忆强度，实现个性化学习效果。

        Args:
            current_strength: 当前记忆强度S
            last_review_score: 上次复习评分(1-10)
            adjustment_factor: 个性化调整因子(默认0.2)

        Returns:
            float: 调整后的记忆强度

        Raises:
            ValueError: 如果输入参数无效
        """
        if not (MIN_REVIEW_SCORE <= last_review_score <= MAX_REVIEW_SCORE):
            raise ValueError(f"复习评分必须在{MIN_REVIEW_SCORE}-{MAX_REVIEW_SCORE}之间")

        if current_strength <= 0:
            raise ValueError("当前记忆强度必须大于0")

        if adjustment_factor <= 0:
            raise ValueError("调整因子必须大于0")

        # 基于评分的调整逻辑
        # 评分5分: 保持当前强度 (1.0 + (5-5) * factor = 1.0)
        # 评分>5分: 增强记忆强度 (1.0 + 正值 * factor > 1.0)
        # 评分<5分: 减弱记忆强度 (1.0 + 负值 * factor < 1.0)
        strength_multiplier = 1.0 + (last_review_score - 5) * adjustment_factor

        # 应用调整
        new_strength = current_strength * strength_multiplier

        # 确保记忆强度在合理范围内 (避免极端值)
        min_strength = 0.5
        max_strength = 100.0

        return max(min_strength, min(max_strength, new_strength))

    def calculate_optimal_review_interval(self, last_review_score: int, current_strength: float) -> int:
        """计算最佳复习间隔

        根据用户评分动态调整记忆强度，并选择合适的复习间隔。

        Args:
            last_review_score: 上次复习评分(1-10)
            current_strength: 当前记忆强度

        Returns:
            int: 推荐的复习间隔(天)

        Raises:
            ValueError: 如果评分不在有效范围内
        """
        if not (MIN_REVIEW_SCORE <= last_review_score <= MAX_REVIEW_SCORE):
            raise ValueError(f"复习评分必须在{MIN_REVIEW_SCORE}-{MAX_REVIEW_SCORE}之间")

        if current_strength <= 0:
            raise ValueError("记忆强度必须大于0")

        # 使用专门的记忆强度调整方法
        adjusted_strength = self.adjust_memory_strength(current_strength, last_review_score)

        # 选择标准复习间隔
        if adjusted_strength < 5:
            return DEFAULT_REVIEW_INTERVALS[0]  # 1天
        elif adjusted_strength < 10:
            return DEFAULT_REVIEW_INTERVALS[1]  # 3天
        elif adjusted_strength < 20:
            return DEFAULT_REVIEW_INTERVALS[2]  # 7天
        elif adjusted_strength < 40:
            return DEFAULT_REVIEW_INTERVALS[3]  # 15天
        else:
            return DEFAULT_REVIEW_INTERVALS[4]  # 30天

    def get_memory_strength_trend(self, review_history: List[Dict]) -> Dict:
        """分析记忆强度变化趋势

        Args:
            review_history: 复习历史记录列表

        Returns:
            Dict: 包含趋势分析的结果
        """
        if not review_history:
            return {
                "trend": "no_data",
                "recent_scores": [],
                "strength_progression": [],
                "average_score": 0.0,
                "improvement_rate": 0.0
            }

        # 提取最近的评分
        recent_scores = [review["score"] for review in review_history[-5:]]

        # 计算强度进展
        strength_progression = []
        current_strength = DEFAULT_MEMORY_STRENGTH

        for review in review_history:
            new_strength = self.adjust_memory_strength(current_strength, review["score"])
            strength_progression.append({
                "review_date": review["review_date"],
                "score": review["score"],
                "strength_before": current_strength,
                "strength_after": new_strength
            })
            current_strength = new_strength

        # 分析趋势
        if len(recent_scores) >= 3:
            recent_avg = sum(recent_scores[-3:]) / 3
            earlier_avg = sum(recent_scores[:-3]) / len(recent_scores[:-3]) if len(recent_scores) > 3 else recent_avg
            improvement_rate = (recent_avg - earlier_avg) / earlier_avg * 100 if earlier_avg > 0 else 0

            if improvement_rate > 10:
                trend = "improving"
            elif improvement_rate < -10:
                trend = "declining"
            else:
                trend = "stable"
        else:
            improvement_rate = 0.0
            trend = "insufficient_data"

        return {
            "trend": trend,
            "recent_scores": recent_scores,
            "strength_progression": strength_progression,
            "average_score": sum(recent_scores) / len(recent_scores),
            "improvement_rate": improvement_rate
        }

    def _ensure_database_exists(self) -> None:
        """确保数据库目录和文件存在"""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def _create_tables(self) -> None:
        """创建数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 复习计划表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS review_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    canvas_file TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    concept_name TEXT NOT NULL,
                    last_review_date TEXT,
                    next_review_date TEXT,
                    review_interval_days INTEGER,
                    memory_strength REAL,
                    retention_rate REAL,
                    difficulty_rating TEXT,
                    mastery_level REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 复习历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS review_history (
                    history_id TEXT PRIMARY KEY,
                    schedule_id TEXT NOT NULL,
                    review_date TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    time_spent_minutes INTEGER,
                    confidence_rating INTEGER,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (schedule_id) REFERENCES review_schedules (schedule_id)
                )
            ''')

            # 用户统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_review_stats (
                    user_id TEXT PRIMARY KEY,
                    total_reviews INTEGER DEFAULT 0,
                    completed_reviews INTEGER DEFAULT 0,
                    average_score REAL DEFAULT 0.0,
                    average_retention_rate REAL DEFAULT 0.0,
                    concepts_mastered INTEGER DEFAULT 0,
                    concepts_in_progress INTEGER DEFAULT 0,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def create_review_schedule(self, canvas_path: str, node_id: str, concept_name: str,
                           initial_memory_strength: float = DEFAULT_MEMORY_STRENGTH,
                           first_review_interval: int = 1) -> str:
        """为新概念创建复习计划

        Args:
            canvas_path: Canvas文件路径
            node_id: 节点ID
            concept_name: 概念名称
            initial_memory_strength: 初始记忆强度
            first_review_interval: 首次复习间隔(天)

        Returns:
            str: 复习计划ID

        Raises:
            ValueError: 如果输入参数无效
        """
        if not canvas_path or not node_id or not concept_name:
            raise ValueError("Canvas路径、节点ID和概念名称不能为空")

        if initial_memory_strength <= 0:
            raise ValueError("初始记忆强度必须大于0")

        # 生成唯一复习计划ID
        schedule_id = f"review-{uuid.uuid4().hex[:16]}"

        # 计算首次复习日期
        today = datetime.now().date()
        next_review_date = today + timedelta(days=first_review_interval)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 插入复习计划
                cursor.execute('''
                    INSERT INTO review_schedules (
                        schedule_id, canvas_file, node_id, concept_name,
                        last_review_date, next_review_date, review_interval_days,
                        memory_strength, retention_rate, difficulty_rating, mastery_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    schedule_id, canvas_path, node_id, concept_name,
                    today.isoformat(), next_review_date.isoformat(), first_review_interval,
                    initial_memory_strength, 1.0, "medium", 0.1
                ))

                # 初始化用户统计记录
                self._ensure_user_stats_exists()

                conn.commit()
                return schedule_id

        except sqlite3.Error as e:
            raise ValueError(f"数据库操作失败: {e}")

    def get_review_schedule(self, schedule_id: str) -> Optional[Dict]:
        """获取指定复习计划

        Args:
            schedule_id: 复习计划ID

        Returns:
            Optional[Dict]: 复习计划信息，如果不存在返回None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM review_schedules WHERE schedule_id = ?
                ''', (schedule_id,))

                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None

        except sqlite3.Error as e:
            raise ValueError(f"数据库查询失败: {e}")

    def update_review_schedule(self, schedule_id: str, **kwargs) -> bool:
        """更新复习计划

        Args:
            schedule_id: 复习计划ID
            **kwargs: 要更新的字段

        Returns:
            bool: 是否更新成功
        """
        if not kwargs:
            return False

        # 构建动态更新语句
        set_clauses = []
        values = []

        for key, value in kwargs.items():
            if key in ['next_review_date', 'review_interval_days', 'memory_strength',
                      'retention_rate', 'difficulty_rating', 'mastery_level']:
                set_clauses.append(f"{key} = ?")
                values.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([schedule_id])

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(f'''
                    UPDATE review_schedules
                    SET {', '.join(set_clauses)}
                    WHERE schedule_id = ?
                ''', values)

                conn.commit()
                return cursor.rowcount > 0

        except sqlite3.Error as e:
            raise ValueError(f"数据库更新失败: {e}")

    def delete_review_schedule(self, schedule_id: str) -> bool:
        """删除复习计划

        Args:
            schedule_id: 复习计划ID

        Returns:
            bool: 是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 先删除相关的复习历史
                cursor.execute('DELETE FROM review_history WHERE schedule_id = ?', (schedule_id,))

                # 再删除复习计划
                cursor.execute('DELETE FROM review_schedules WHERE schedule_id = ?', (schedule_id,))

                conn.commit()
                return cursor.rowcount > 0

        except sqlite3.Error as e:
            raise ValueError(f"数据库删除失败: {e}")

    def get_all_review_schedules(self, canvas_file: str = None) -> List[Dict]:
        """获取所有复习计划

        Args:
            canvas_file: 可选的Canvas文件路径过滤

        Returns:
            List[Dict]: 复习计划列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if canvas_file:
                    cursor.execute('''
                        SELECT * FROM review_schedules
                        WHERE canvas_file = ?
                        ORDER BY next_review_date ASC
                    ''', (canvas_file,))
                else:
                    cursor.execute('''
                        SELECT * FROM review_schedules
                        ORDER BY next_review_date ASC
                    ''')

                return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            raise ValueError(f"数据库查询失败: {e}")

    def get_today_reviews(self, user_id: str = "default") -> List[Dict]:
        """获取今日需要复习的任务

        Args:
            user_id: 用户ID

        Returns:
            List[Dict]: 今日复习任务列表
        """
        today = datetime.now().date().isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT rs.*,
                           GROUP_CONCAT(
                               json_object(
                                   'history_id', rh.history_id,
                                   'review_date', rh.review_date,
                                   'score', rh.score,
                                   'confidence_rating', rh.confidence_rating
                               ), ', '
                           ) as recent_history
                    FROM review_schedules rs
                    LEFT JOIN review_history rh ON rs.schedule_id = rh.schedule_id
                    WHERE rs.next_review_date <= ?
                    GROUP BY rs.schedule_id
                    ORDER BY rs.next_review_date ASC
                ''', (today,))

                schedules = []
                for row in cursor.fetchall():
                    schedule = dict(row)
                    # 处理历史记录
                    if schedule['recent_history']:
                        schedule['recent_history'] = [
                            json.loads(h) for h in schedule['recent_history'].split(',') if h.strip()
                        ]
                    else:
                        schedule['recent_history'] = []
                    schedules.append(schedule)

                return schedules

        except sqlite3.Error as e:
            raise ValueError(f"数据库查询失败: {e}")

    def complete_review(self, schedule_id: str, score: int, confidence: int,
                      time_minutes: int, notes: str = None) -> bool:
        """完成复习并记录结果

        Args:
            schedule_id: 复习计划ID
            score: 满意度评分 (1-10)
            confidence: 信心评分 (1-10)
            time_minutes: 复习用时
            notes: 可选的复习笔记

        Returns:
            bool: 是否成功记录
        """
        if not (MIN_REVIEW_SCORE <= score <= MAX_REVIEW_SCORE):
            raise ValueError(f"满意度评分必须在{MIN_REVIEW_SCORE}-{MAX_REVIEW_SCORE}之间")

        if not (1 <= confidence <= 10):
            raise ValueError("信心评分必须在1-10之间")

        if time_minutes < 0:
            raise ValueError("复习时间不能为负数")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 获取当前复习计划
                cursor.execute('''
                    SELECT memory_strength, canvas_file, node_id, concept_name
                    FROM review_schedules
                    WHERE schedule_id = ?
                ''', (schedule_id,))

                schedule_data = cursor.fetchone()
                if not schedule_data:
                    raise ValueError(f"复习计划不存在: {schedule_id}")

                current_strength, canvas_file, node_id, concept_name = schedule_data

                # 调整记忆强度
                new_strength = self.adjust_memory_strength(current_strength, score)

                # 计算下次复习间隔
                next_interval = self.calculate_optimal_review_interval(score, current_strength)
                today = datetime.now().date()
                next_review_date = today + timedelta(days=next_interval)

                # 计算当前记忆保持率
                time_elapsed = 1  # 假设刚好到复习时间
                retention_rate = self.calculate_retention_rate(time_elapsed, current_strength)

                # 更新复习计划
                cursor.execute('''
                    UPDATE review_schedules
                    SET last_review_date = ?,
                        next_review_date = ?,
                        review_interval_days = ?,
                        memory_strength = ?,
                        retention_rate = ?,
                        mastery_level = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE schedule_id = ?
                ''', (
                    today.isoformat(),
                    next_review_date.isoformat(),
                    next_interval,
                    new_strength,
                    retention_rate,
                    min(1.0, retention_rate + 0.1),  # 简单的掌握度计算
                    schedule_id
                ))

                # 记录复习历史
                history_id = f"hist-{uuid.uuid4().hex[:16]}"
                cursor.execute('''
                    INSERT INTO review_history (
                        history_id, schedule_id, review_date, score,
                        time_spent_minutes, confidence_rating, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    history_id, schedule_id, today.isoformat(),
                    score, time_minutes, confidence, notes
                ))

                # 更新用户统计
                self._update_user_stats(score, retention_rate)

                conn.commit()
                return True

        except sqlite3.Error as e:
            raise ValueError(f"数据库操作失败: {e}")

    def _ensure_user_stats_exists(self, user_id: str = "default") -> None:
        """确保用户统计记录存在"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR IGNORE INTO user_review_stats (user_id)
                    VALUES (?)
                ''', (user_id,))

                conn.commit()

        except sqlite3.Error:
            pass  # 忽略统计记录创建失败

    def _update_user_stats(self, score: int, retention_rate: float, user_id: str = "default") -> None:
        """更新用户统计数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 更新统计信息
                cursor.execute('''
                    UPDATE user_review_stats
                    SET total_reviews = total_reviews + 1,
                        completed_reviews = completed_reviews + 1,
                        average_score = (average_score * (total_reviews - 1) + ?) / total_reviews,
                        average_retention_rate = (average_retention_rate * (total_reviews - 1) + ?) / total_reviews,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (score, retention_rate, user_id))

                conn.commit()

        except sqlite3.Error:
            pass  # 忽略统计更新失败

    def backup_database(self, backup_path: str = None) -> str:
        """备份数据库

        Args:
            backup_path: 备份文件路径，如果为None则生成默认路径

        Returns:
            str: 备份文件路径
        """
        import os
        import shutil
        from datetime import datetime

        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backups/review_backup_{timestamp}.db"

        # 确保备份目录存在
        backup_dir = os.path.dirname(backup_path)
        if backup_dir:
            os.makedirs(backup_dir, exist_ok=True)

        try:
            # 创建备份
            shutil.copy2(self.db_path, backup_path)
            return backup_path

        except Exception as e:
            raise ValueError(f"数据库备份失败: {e}")

    def restore_database(self, backup_path: str) -> bool:
        """从备份恢复数据库

        Args:
            backup_path: 备份文件路径

        Returns:
            bool: 是否恢复成功
        """
        import shutil

        if not os.path.exists(backup_path):
            raise ValueError(f"备份文件不存在: {backup_path}")

        try:
            # 关闭所有数据库连接（确保文件不被锁定）
            # 创建备份当前数据库
            current_backup = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_path, current_backup)

            # 恢复数据库
            shutil.copy2(backup_path, self.db_path)
            return True

        except Exception as e:
            raise ValueError(f"数据库恢复失败: {e}")

    def get_review_statistics(self, user_id: str = "default", days: int = 30) -> Dict:
        """获取复习统计数据

        Args:
            user_id: 用户ID
            days: 统计天数

        Returns:
            Dict: 复习统计数据
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 获取用户基本统计
                cursor.execute('''
                    SELECT * FROM user_review_stats WHERE user_id = ?
                ''', (user_id,))

                user_stats = cursor.fetchone()
                if not user_stats:
                    return {
                        "user_id": user_id,
                        "date_range": {
                            "start_date": None,
                            "end_date": None
                        },
                        "total_reviews": 0,
                        "completed_reviews": 0,
                        "average_score": 0.0,
                        "average_retention_rate": 0.0,
                        "concepts_mastered": 0,
                        "concepts_in_progress": 0,
                        "subject_breakdown": {},
                        "learning_efficiency": {
                            "time_per_review_minutes": 0.0,
                            "retention_improvement_rate": 0.0,
                            "optimal_study_time_identified": None
                        }
                    }

                # 获取最近的复习历史
                start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
                cursor.execute('''
                    SELECT rs.canvas_file, rs.concept_name, rh.score,
                           rh.time_spent_minutes, rh.review_date,
                           rs.memory_strength, rs.retention_rate
                    FROM review_history rh
                    JOIN review_schedules rs ON rh.schedule_id = rs.schedule_id
                    WHERE rh.review_date >= ?
                    ORDER BY rh.review_date DESC
                ''', (start_date,))

                recent_reviews = [dict(row) for row in cursor.fetchall()]

                # 计算主题统计
                subject_stats = {}
                total_time = 0
                completed_count = 0

                for review in recent_reviews:
                    canvas_file = review['canvas_file']
                    subject = os.path.basename(canvas_file).replace('.canvas', '')

                    if subject not in subject_stats:
                        subject_stats[subject] = {
                            "total_concepts": 0,
                            "mastered": 0,
                            "in_progress": 0,
                            "struggling": 0
                        }

                    subject_stats[subject]["total_concepts"] += 1

                    # 根据评分分类
                    score = review['score']
                    if score >= 8:
                        subject_stats[subject]["mastered"] += 1
                    elif score >= 5:
                        subject_stats[subject]["in_progress"] += 1
                    else:
                        subject_stats[subject]["struggling"] += 1

                    total_time += review['time_spent_minutes'] or 0
                    completed_count += 1

                # 计算效率指标
                avg_time_per_review = total_time / completed_count if completed_count > 0 else 0

                return {
                    "user_id": user_id,
                    "date_range": {
                        "start_date": start_date,
                        "end_date": datetime.now().date().isoformat()
                    },
                    "total_reviews": dict(user_stats)["total_reviews"],
                    "completed_reviews": dict(user_stats)["completed_reviews"],
                    "average_score": float(dict(user_stats)["average_score"]),
                    "average_retention_rate": float(dict(user_stats)["average_retention_rate"]),
                    "concepts_mastered": dict(user_stats)["concepts_mastered"],
                    "concepts_in_progress": dict(user_stats)["concepts_in_progress"],
                    "subject_breakdown": subject_stats,
                    "learning_efficiency": {
                        "time_per_review_minutes": avg_time_per_review,
                        "retention_improvement_rate": 0.0,  # 需要历史数据计算
                        "optimal_study_time_identified": "morning"  # 简化实现
                    }
                }

        except sqlite3.Error as e:
            raise ValueError(f"统计查询失败: {e}")

    def export_review_data(self, file_path: str, format: str = "json") -> bool:
        """导出复习数据

        Args:
            file_path: 导出文件路径
            format: 导出格式 ("json" 或 "csv")

        Returns:
            bool: 是否导出成功
        """
        try:
            # 获取所有数据
            schedules = self.get_all_review_schedules()
            stats = self.get_review_statistics()

            export_data = {
                "export_date": datetime.now().isoformat(),
                "schedules": schedules,
                "statistics": stats
            }

            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            elif format.lower() == "csv":
                import csv

                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if schedules:
                        writer = csv.DictWriter(f, fieldnames=schedules[0].keys())
                        writer.writeheader()
                        writer.writerows(schedules)
            else:
                raise ValueError(f"不支持的导出格式: {format}")

            return True

        except Exception as e:
            raise ValueError(f"数据导出失败: {e}")
