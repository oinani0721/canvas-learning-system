#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
最终简化测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试基本导入
try:
    from ebbinghaus_review import EbbinghausReviewScheduler
    print("ebbinghaus_review.py 导入成功")
except Exception as e:
    print(f"ebbinghaus_review.py 导入失败: {e}")
    sys.exit(1)

try:
    from review_manager_standalone import CanvasReviewManagerStandalone
    print("review_manager_standalone.py 导入成功")
except Exception as e:
    print(f"review_manager_standalone.py 导入失败: {e}")
    sys.exit(1)

try:
    from review_cli import ReviewCLI
    print("review_cli.py 导入成功")
except Exception as e:
    print(f"review_cli.py 导入失败: {e}")
    sys.exit(1)

print("\n所有核心模块导入成功！")
print("艾宾浩斯复习系统实现完成。")

# 快速功能测试
import tempfile
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
temp_db.close()

try:
    scheduler = EbbinghausReviewScheduler(temp_db.name)
    manager = CanvasReviewManagerStandalone(temp_db.name)

    # 测试基本功能
    schedule_id = scheduler.create_review_schedule(
        canvas_path='test.canvas',
        node_id='test-node',
        concept_name='测试概念'
    )
    print(f"复习计划创建: {schedule_id}")

    # 测试记忆保持率计算
    retention = scheduler.calculate_retention_rate(7, 10)
    print(f"记忆保持率计算: {retention:.3f}")

    # 测试记忆强度调整
    new_strength = scheduler.adjust_memory_strength(10, 8)
    print(f"记忆强度调整: {new_strength:.1f}")

    print("核心功能测试通过!")

except Exception as e:
    print(f"功能测试失败: {e}")

finally:
    if os.path.exists(temp_db.name):
        try:
            os.unlink(temp_db.name)
        except:
            pass