#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的命令行测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ebbinghaus_review import EbbinghausReviewScheduler

def test_cli_functions():
    """测试CLI核心功能"""

    # 创建临时数据库
    import tempfile
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        scheduler = EbbinghausReviewScheduler(temp_db.name)

        # 创建测试复习计划
        schedule_id = scheduler.create_review_schedule(
            canvas_path='test.canvas',
            node_id='node-123',
            concept_name='测试概念'
        )
        print(f"创建复习计划: {schedule_id}")

        # 测试今日复习
        reviews = scheduler.get_today_reviews()
        print(f"今日复习任务数: {len(reviews)}")

        # 测试统计
        stats = scheduler.get_review_statistics()
        print(f"用户统计 - 总复习: {stats['total_reviews']}")

        # 完成复习测试
        success = scheduler.complete_review(schedule_id, 8, 7, 5)
        print(f"完成复习: {success}")

        print("CLI功能测试通过!")
        return True

    except Exception as e:
        print(f"测试失败: {e}")
        return False

    finally:
        if os.path.exists(temp_db.name):
            try:
                os.unlink(temp_db.name)
            except:
                pass

if __name__ == "__main__":
    success = test_cli_functions()
    sys.exit(0 if success else 1)