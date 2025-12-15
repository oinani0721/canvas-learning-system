#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
独立Canvas集成功能测试
"""

import sys
import os
import tempfile
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from review_manager_standalone import CanvasReviewManagerStandalone
from ebbinghaus_review import EbbinghausReviewScheduler

def test_standalone_canvas_integration():
    """测试独立Canvas集成功能"""

    # 创建临时数据库和Canvas文件
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    temp_canvas = tempfile.NamedTemporaryFile(delete=False, suffix='.canvas')
    temp_canvas.close()

    try:
        # 创建测试Canvas文件
        test_canvas_data = {
            "nodes": [
                {
                    "id": "test-node-1",
                    "type": "text",
                    "text": "测试概念1",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "1"  # 红色节点
                },
                {
                    "id": "test-node-2",
                    "type": "text",
                    "text": "测试概念2",
                    "x": 400,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "3"  # 紫色节点
                }
            ],
            "edges": []
        }

        with open(temp_canvas.name, 'w', encoding='utf-8') as f:
            json.dump(test_canvas_data, f, ensure_ascii=False, indent=2)

        # 创建复习管理器
        manager = CanvasReviewManagerStandalone(temp_db.name)

        # 测试1: Canvas节点集成
        print("测试1: Canvas节点集成")
        result1 = manager.integrate_review_with_canvas(
            canvas_path=temp_canvas.name,
            node_id="test-node-1",
            auto_create_schedule=True
        )

        if result1.get("success"):
            print(f"✅ 节点集成成功: {result1['concept_name']}")
            print(f"   复习计划ID: {result1['schedule_id']}")
        else:
            print(f"❌ 节点集成失败: {result1.get('error')}")

        # 测试2: 批量创建复习计划
        print("\n测试2: 批量创建复习计划")
        result2 = manager.create_review_schedules_from_canvas(temp_canvas.name)

        if result2.get("success"):
            print(f"✅ 批量创建成功: {result2['summary']}")
            print(f"   成功率: {result2.get('success_rate', 0):.1f}%")
        else:
            print(f"❌ 批量创建失败: {result2.get('error')}")

        # 测试3: 完成复习
        print("\n测试3: 完成复习")
        result3 = manager.complete_canvas_review(
            canvas_path=temp_canvas.name,
            node_id="test-node-1",
            score=8,
            confidence=7,
            time_minutes=5,
            notes="测试复习笔记"
        )

        if result3.get("success"):
            print(f"✅ 复习完成成功")
            print(f"   评分: {result3['score']}/10")
            print(f"   新颜色: {result3['new_color']}")
            print(f"   下次复习: {result3['next_review_date']}")
            print(f"   建议: {result3['suggestions']}")
        else:
            print(f"❌ 复习完成失败: {result3.get('error')}")

        print("\n独立Canvas集成功能测试通过!")
        return True

    except Exception as e:
        print(f"测试失败: {e}")
        return False

    finally:
        # 清理临时文件
        for temp_file in [temp_db.name, temp_canvas.name]:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass

if __name__ == "__main__":
    success = test_standalone_canvas_integration()
    sys.exit(0 if success else 1)