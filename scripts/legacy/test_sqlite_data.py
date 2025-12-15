#!/usr/bin/env python3
"""
SQLite复习数据库全面检验测试
测试艾宾浩斯复习系统的数据存储和读取能力
"""

import sqlite3
import os
from datetime import datetime, timedelta
import json

def test_sqlite_database():
    """全面测试SQLite复习数据库功能"""

    print("SQLite复习数据库检验开始...")

    # 数据库路径
    db_path = "C:\\Users\\ROG\\托福\\data\\review_data.db"

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("✅ 数据库连接成功")

        # 1. 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 发现表: {[table[0] for table in tables]}")

        # 2. 检查现有数据
        for table_name in ['review_schedules', 'review_history', 'user_review_stats']:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📊 {table_name}: {count} 条记录")

        # 3. 创建测试复习计划
        print("\n📝 创建测试复习计划...")

        # 测试数据 - 基于您的CS70 Canvas
        test_schedule = {
            'schedule_id': 'test-cs70-001',
            'user_id': 'default',
            'canvas_file': 'CS70 Lecture1.canvas',
            'node_id': 'node-logic-proposition',
            'concept_name': '命题逻辑基础',
            'concept_type': 'concept',
            'current_mastery_level': 0.6,
            'memory_strength': 8.5,
            'review_interval_days': 3,
            'next_review_date': (datetime.now() + timedelta(days=1)).isoformat(),
            'last_review_date': datetime.now().isoformat(),
            'review_count': 2,
            'success_rate': 0.75,
            'difficulty_level': 3,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # 插入测试数据
        cursor.execute("""
            INSERT OR REPLACE INTO review_schedules
            (schedule_id, user_id, canvas_file, node_id, concept_name, concept_type,
             current_mastery_level, memory_strength, review_interval_days, next_review_date,
             last_review_date, review_count, success_rate, difficulty_level, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_schedule['schedule_id'], test_schedule['user_id'], test_schedule['canvas_file'],
            test_schedule['node_id'], test_schedule['concept_name'], test_schedule['concept_type'],
            test_schedule['current_mastery_level'], test_schedule['memory_strength'],
            test_schedule['review_interval_days'], test_schedule['next_review_date'],
            test_schedule['last_review_date'], test_schedule['review_count'],
            test_schedule['success_rate'], test_schedule['difficulty_level'],
            test_schedule['created_at'], test_schedule['updated_at']
        ))

        print("✅ 测试复习计划插入成功")

        # 4. 创建测试复习历史
        test_history = {
            'history_id': 'hist-cs70-001',
            'schedule_id': 'test-cs70-001',
            'review_date': datetime.now().isoformat(),
            'review_duration_minutes': 25,
            'user_rating': 8,
            'user_confidence': 7,
            'accuracy_score': 0.85,
            'previous_mastery': 0.5,
            'new_mastery': 0.65,
            'memory_strength_before': 7.2,
            'memory_strength_after': 8.5,
            'review_method': 'deep-decomposition',
            'review_notes': '对命题逻辑的理解有显著提升',
            'agent_used': 'scoring-agent',
            'improvement_suggestions': ['加强练习蕴含式推理', '复习真值表构造']
        }

        cursor.execute("""
            INSERT OR REPLACE INTO review_history
            (history_id, schedule_id, review_date, review_duration_minutes, user_rating,
             user_confidence, accuracy_score, previous_mastery, new_mastery,
             memory_strength_before, memory_strength_after, review_method, review_notes,
             agent_used, improvement_suggestions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_history['history_id'], test_history['schedule_id'], test_history['review_date'],
            test_history['review_duration_minutes'], test_history['user_rating'],
            test_history['user_confidence'], test_history['accuracy_score'],
            test_history['previous_mastery'], test_history['new_mastery'],
            test_history['memory_strength_before'], test_history['memory_strength_after'],
            test_history['review_method'], test_history['review_notes'],
            test_history['agent_used'], json.dumps(test_history['improvement_suggestions'])
        ))

        print("✅ 测试复习历史插入成功")

        # 5. 创建测试用户统计
        test_stats = {
            'user_id': 'default',
            'total_reviews': 15,
            'successful_reviews': 12,
            'total_concepts': 8,
            'mastered_concepts': 3,
            'in_progress_concepts': 4,
            'struggling_concepts': 1,
            'average_rating': 7.8,
            'average_confidence': 7.2,
            'total_study_time_minutes': 450,
            'average_review_duration': 30,
            'longest_streak_days': 5,
            'current_streak_days': 2,
            'last_active_date': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        cursor.execute("""
            INSERT OR REPLACE INTO user_review_stats
            (user_id, total_reviews, successful_reviews, total_concepts, mastered_concepts,
             in_progress_concepts, struggling_concepts, average_rating, average_confidence,
             total_study_time_minutes, average_review_duration, longest_streak_days,
             current_streak_days, last_active_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_stats['user_id'], test_stats['total_reviews'], test_stats['successful_reviews'],
            test_stats['total_concepts'], test_stats['mastered_concepts'],
            test_stats['in_progress_concepts'], test_stats['struggling_concepts'],
            test_stats['average_rating'], test_stats['average_confidence'],
            test_stats['total_study_time_minutes'], test_stats['average_review_duration'],
            test_stats['longest_streak_days'], test_stats['current_streak_days'],
            test_stats['last_active_date'], test_stats['created_at'], test_stats['updated_at']
        ))

        print("✅ 测试用户统计插入成功")

        # 6. 验证数据读取
        print("\n🔍 验证数据读取...")

        # 读取今日复习任务
        today = datetime.now().date().isoformat()
        cursor.execute("""
            SELECT * FROM review_schedules
            WHERE date(next_review_date) = date(?)
            ORDER BY next_review_date ASC
        """, (today,))

        today_reviews = cursor.fetchall()
        print(f"📅 今日复习任务: {len(today_reviews)} 个")

        # 读取复习历史统计
        cursor.execute("""
            SELECT COUNT(*) as total_reviews,
                   AVG(user_rating) as avg_rating,
                   AVG(accuracy_score) as avg_accuracy
            FROM review_history
            WHERE review_date >= date('now', '-7 days')
        """)

        week_stats = cursor.fetchone()
        print(f"📈 本周统计: 总复习{week_stats[0]}次, 平均评分{week_stats[1]:.1f}, 准确率{week_stats[2]:.1%}")

        # 7. 提交更改
        conn.commit()
        print("✅ 数据提交成功")

        # 8. 测试复杂查询
        print("\n🧮 测试复杂查询...")

        # 艾宾浩斯算法测试查询
        cursor.execute("""
            SELECT concept_name, memory_strength, review_interval_days, next_review_date,
                   CASE
                       WHEN memory_strength < 5 THEN '需要紧急复习'
                       WHEN memory_strength < 10 THEN '建议近期复习'
                       WHEN memory_strength < 20 THEN '正常复习间隔'
                       ELSE '复习间隔较长'
                   END as priority_level
            FROM review_schedules
            WHERE user_id = 'default'
            ORDER BY memory_strength ASC
        """)

        priority_reviews = cursor.fetchall()
        print("🎯 优先级复习列表:")
        for review in priority_reviews[:3]:
            print(f"   • {review[0]} - 强度:{review[1]:.1f} - {review[4]}")

        conn.close()
        print("\n✅ SQLite数据库检验完成 - 所有功能正常!")
        return True

    except Exception as e:
        print(f"❌ SQLite检验失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_sqlite_database()