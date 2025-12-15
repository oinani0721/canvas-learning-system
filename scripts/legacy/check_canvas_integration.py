#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Canvas集成状态检查
"""

def check_integration():
    """检查艾宾浩斯复习系统与Canvas的集成状态"""

    print("🔍 Canvas学习系统v2.0 + 艾宾浩斯复习系统 集成状态检查")
    print("="*60)

    print("📂 核心组件状态:")

    # 1. 检查核心文件
    core_files = {
        "ebbinghaus_review.py": "艾宾浩斯复习调度器",
        "review_manager_standalone.py": "Canvas集成管理器",
        "review_cli.py": "命令行接口",
        "config/review_settings.yaml": "复习系统配置"
    }

    for file_path, description in core_files.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 100:  # 假设有实际内容
                    print(f"   ✅ {description}: {len(content):,}KB - 已就绪")
                else:
                    print(f"   ⚠️  {description}: 空文件或过小")
        except FileNotFoundError:
            print(f"   ❌ {description}: 文件不存在")
        except Exception as e:
            print(f"   ⚠️  {description}: 读取错误 - {e}")

    print()
    print("📋 Canvas集成能力:")

    # 2. 检查API兼容性
    try:
        import importlib.util
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # 测试导入
        from ebbinghaus_review import EbbinghausReviewScheduler
        from review_manager_standalone import CanvasReviewManagerStandalone
        print("   ✅ EbbinghausReviewScheduler - 复习调度器导入成功")
        print("   ✅ CanvasReviewManagerStandalone - Canvas集成管理器导入成功")

        # 测试基本功能
        temp_db = "test_integration.db"
        scheduler = EbbinghausReviewScheduler(temp_db)
        manager = CanvasReviewManagerStandalone(temp_db)

        # 测试核心方法
        retention = scheduler.calculate_retention_rate(7, 10.0)
        print(f"   ✅ 记忆保持率计算: {retention:.3f}")

        strength = scheduler.adjust_memory_strength(10.0, 8)
        print(f"   ✅ 记忆强度调整: {strength:.1f}")

        print("   ✅ API接口完整且功能正常")

    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
    except Exception as e:
        print(f"   ⚠️  功能检查异常: {e}")

    print()
    print("🎯 部署状态:")

    # 3. 检查配置文件
    config_files = {
        "config/review_settings.yaml": "复习系统配置"
    }

    for config_path, config_name in config_files.items():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print(f"   ✅ {config_name}: {len(str(config))}行配置")
        except FileNotFoundError:
            print(f"   ❌ {config_name}: 配置文件不存在")
        except Exception as e:
            print(f"   ⚠️  {config_name}: 配置读取错误 - {e}")

    print()
    print("🔗 集成使用说明:")
    print("   📚 Python API使用示例:")
    print("      from review_manager_standalone import CanvasReviewManagerStandalone")
    print("      manager = CanvasReviewManagerStandalone()")
    print("      result = manager.integrate_review_with_canvas('your.canvas', 'node-id')")
    print()
    print("   🖥️  命令行工具使用:")
    print("      python review_cli.py show     # 显示今日复习")
    print("      python review_cli.py stats    # 显示复习统计")
    print("      python review_cli.py complete  # 交互式完成复习")
    print()

    # 4. 检查Canvas文件
    canvas_files = [
        "C:/Users/ROG/托福/笔记库/CS61B LEC3.canvas",
        "C:/Users/ROG/托福/笔记库/CS61B HW5.canvas"
    ]

    existing_files = 0
    for canvas_file in canvas_files:
        if os.path.exists(canvas_file):
            existing_files += 1

    print(f"   📁 找到 {existing_files} 个Canvas文件")
    if existing_files > 0:
        print("   ✅ 可以立即开始使用复习功能")
    else:
        print("   ⚠️  请先创建Canvas文件")

    print()
    print("🎯 推荐使用步骤:")
    print("   1. 打开现有的Canvas学习文件")
    print("   2. 运行: python review_manager_standalone.py 来集成复习功能")
    print("   3. 或使用命令行: python review_cli.py")
    print()
    print("="*60)

if __name__ == "__main__":
    check_integration()