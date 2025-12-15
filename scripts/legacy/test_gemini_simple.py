#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API 简化测试脚本

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import sys
import json
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

try:
    from graphiti_gemini_integration import GraphitiGeminiIntegration
    from gemini_llm_client import GeminiLLMClient
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖文件都在当前目录")
    sys.exit(1)


async def test_basic_config():
    """测试基础配置"""
    print("测试1: 基础配置检查")
    print("-" * 40)

    try:
        # 检查配置文件
        config_file = Path("config/gemini_api_config.yaml")
        if not config_file.exists():
            print("❌ 配置文件不存在: config/gemini_api_config.yaml")
            return False

        print("✅ 配置文件存在")

        # 加载配置
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print("✅ 配置文件加载成功")
        print(f"   API地址: {config['api_config']['base_url']}")
        print(f"   模型: {config['api_config']['model']}")
        print(f"   API Key: {config['api_config']['api_key'][:20]}...")

        return True

    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False


async def test_api_connection():
    """测试API连接"""
    print("\n测试2: API连接")
    print("-" * 40)

    try:
        # 直接创建Gemini客户端
        config = {
            "api_config": {
                "api_key": "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF",
                "base_url": "https://binapi.shop/v1",
                "model": "gemini-2.5-flash-preview-05-20-thinking",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }

        client = GeminiLLMClient(config)
        print("✅ Gemini客户端创建成功")

        # 测试简单文本生成
        test_prompt = "请简单回答：1+1等于几？"
        result = await client.generate_text(test_prompt)

        print("✅ API调用成功")
        print(f"   响应长度: {len(result)} 字符")
        print(f"   响应内容: {result[:100]}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ API连接测试失败: {e}")
        return False


async def test_graphiti_integration():
    """测试Graphiti集成"""
    print("\n测试3: Graphiti集成")
    print("-" * 40)

    try:
        integration = GraphitiGeminiIntegration()
        await integration.initialize()
        print("✅ Graphiti集成初始化成功")

        # 测试学习会话记录
        session_data = {
            "canvas_file": "test.canvas",
            "session_type": "test",
            "duration_minutes": 5,
            "learning_outcomes": {
                "new_concepts_learned": 1,
                "concepts_reviewed": 0
            }
        }

        session_id = await integration.record_learning_session(session_data)
        print(f"✅ 学习会话记录成功: {session_id}")

        # 获取使用统计
        stats = await integration.get_usage_stats()
        print("✅ 使用统计获取成功")
        print(f"   API提供商: {stats['api_provider']}")
        print(f"   模型: {stats['model']}")
        print(f"   状态: {stats['status']}")

        await integration.close()
        return True

    except Exception as e:
        print(f"❌ Graphiti集成测试失败: {e}")
        return False


async def test_canvas_analysis():
    """测试Canvas分析"""
    print("\n测试4: Canvas概念分析")
    print("-" * 40)

    try:
        # 创建简单的测试文本
        test_text = """
        数学概念：函数
        定义：f(x) = 2x + 1
        这是一个线性函数
        斜率为2，截距为1
        """

        # 使用Gemini客户端分析概念
        config = {
            "api_config": {
                "api_key": "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF",
                "base_url": "https://binapi.shop/v1",
                "model": "gemini-2.5-flash-preview-05-20-thinking",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }

        client = GeminiLLMClient(config)
        result = await client.analyze_concepts(test_text)

        print("✅ Canvas概念分析成功")
        concepts = result.get('concepts', [])
        relationships = result.get('relationships', [])
        print(f"   提取概念: {len(concepts)} 个")
        print(f"   提取关系: {len(relationships)} 个")

        if concepts:
            print("   提取的概念:")
            for i, concept in enumerate(concepts[:3]):
                print(f"     {i+1}. {concept.get('name', 'unknown')}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Canvas分析测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("开始Gemini API集成测试")
    print("=" * 50)

    tests = [
        ("基础配置", test_basic_config),
        ("API连接", test_api_connection),
        ("Graphiti集成", test_graphiti_integration),
        ("Canvas分析", test_canvas_analysis)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))

    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        print("您的Gemini API集成配置成功！")
        print("\n下一步:")
        print("1. 开始使用Canvas学习功能")
        print("2. 监控API使用成本")
        print("3. 体验强大的思维推理能力")
    else:
        print("\n⚠️ 部分测试失败")
        print("请检查:")
        print("1. API Key是否正确")
        print("2. 网络连接是否正常")
        print("3. 模型名称是否支持")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)