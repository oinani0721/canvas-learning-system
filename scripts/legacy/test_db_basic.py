#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基本数据库功能测试
"""

from ebbinghaus_review import EbbinghausReviewScheduler
import tempfile
import os

def test_basic_database_operations():
    """测试基本数据库操作"""

    # 创建临时数据库测试
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        scheduler = EbbinghausReviewScheduler(temp_db.name)

        # 测试创建复习计划
        schedule_id = scheduler.create_review_schedule(
            canvas_path='test.canvas',
            node_id='node-123',
            concept_name='测试概念'
        )
        print(f"创建复习计划成功: {schedule_id}")

        # 测试获取复习计划
        schedule = scheduler.get_review_schedule(schedule_id)
        if schedule:
            print(f"获取复习计划成功: {schedule['concept_name']}")
        else:
            print("获取复习计划失败")

        # 测试获取今日复习
        today_reviews = scheduler.get_today_reviews()
        print(f"今日复习任务数量: {len(today_reviews)}")

        # 测试完成复习
        success = scheduler.complete_review(schedule_id, 8, 7, 5, '测试复习笔记')
        if success:
            print("完成复习记录成功")
        else:
            print("完成复习记录失败")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        return False

    finally:
        # 清理临时文件
        if os.path.exists(temp_db.name):
            try:
                os.unlink(temp_db.name)
                print("清理临时文件完成")
            except PermissionError:
                print("临时文件清理失败（权限问题）")

if __name__ == "__main__":
    success = test_basic_database_operations()
    if success:
        print("所有测试通过！")
    else:
        print("测试失败！")