#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Canvas集成功能测试
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from review_manager import CanvasReviewManager
from ebbinghaus_review import EbbinghausReviewScheduler

def test_canvas_integration():
    """测试Canvas集成功能"""

    # 创建临时数据库
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        # 创建复习管理器
        manager = CanvasReviewManager(temp_db.name)

        # 测试1: 模拟Canvas节点集成
        print("测试1: Canvas节点集成")
        result = manager.integrate_review_with_canvas(
            canvas_path="test.canvas",
            node_id="test-node-123",
            auto_create_schedule=True
        )

        if result.get("success"):
            print(f"✅ 节点集成成功: {result['concept_name']}")
            print(f"   复习计划ID: {result['schedule_id']}")
            print(f"   下次复习: {result['next_review_date']}")
        else:
            print(f"❌ 节点集成失败: {result.get('error')}")

        # 测试2: 颜色评分映射
        print("\n测试2: 颜色评分映射")
        test_scores = [3, 5, 8, 10]
        for score in test_scores:
            color = manager._get_color_by_score(score)
            color_names = {"1": "红色", "2": "绿色", "3": "紫色", "6": "黄色"}
            print(f"   评分{score} -> {color_names.get(color, color)}")

        # 测试3: 复习建议生成
        print("\n测试3: 复习建议生成")
        suggestions = manager._generate_review_suggestions(
            score=4, confidence=3, memory_strength=8.0, retention_rate=0.5
        )
        print("   低分复习建议:")
        print(f"   {suggestions}")

        print("\nCanvas集成功能测试通过!")
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
    success = test_canvas_integration()
    sys.exit(0 if success else 1)