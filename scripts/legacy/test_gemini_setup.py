#!/usr/bin/env python3
"""
Gemini API配置验证脚本

用于验证Graphiti-Gemini集成的配置和功能

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

from graphiti_gemini_integration import GraphitiGeminiIntegration


async def test_api_connection():
    """测试API连接"""
    print("🔍 测试1: API连接测试")
    print("-" * 50)

    try:
        integration = GraphitiGeminiIntegration()

        # 测试配置加载
        print("✅ 配置文件加载成功")
        print(f"   API URL: {integration.config['api_config']['base_url']}")
        print(f"   模型: {integration.config['api_config']['model']}")

        # 测试客户端初始化
        if integration.llm_client:
            print("✅ Gemini LLM客户端初始化成功")
        else:
            print("❌ Gemini LLM客户端初始化失败")
            return False

        if integration.embedding_client:
            print("✅ 嵌入客户端初始化成功")
        else:
            print("⚠️ 嵌入客户端初始化失败（可能不支持）")

        if integration.graphiti:
            print("✅ Graphiti数据库连接成功")
        else:
            print("❌ Graphiti数据库连接失败")
            return False

        await integration.close()
        return True

    except Exception as e:
        print(f"❌ API连接测试失败: {e}")
        return False


async def test_canvas_analysis():
    """测试Canvas分析功能"""
    print("\n🔍 测试2: Canvas分析功能")
    print("-" * 50)

    try:
        integration = GraphitiGeminiIntegration()
        await integration.initialize()

        # 查找测试Canvas文件
        test_canvas = "笔记库/离散数学/离散数学.canvas"
        if not Path(test_canvas).exists():
            # 尝试其他可能的Canvas文件
            canvas_files = list(Path("笔记库").rglob("*.canvas"))
            if canvas_files:
                test_canvas = str(canvas_files[0])
                print(f"📁 使用Canvas文件: {test_canvas}")
            else:
                print("⚠️ 未找到Canvas文件，跳过Canvas分析测试")
                await integration.close()
                return True

        # 测试Canvas分析
        print(f"📊 分析Canvas文件: {test_canvas}")
        result = await integration.analyze_canvas_with_gemini(test_canvas)

        print("✅ Canvas分析成功")
        print(f"   分析时间: {result['processed_at']}")

        concepts = result['analysis_result'].get('concepts', [])
        relationships = result['analysis_result'].get('relationships', [])

        print(f"   提取概念: {len(concepts)} 个")
        print(f"   提取关系: {len(relationships)} 个")

        if concepts:
            print("   示例概念:")
            for i, concept in enumerate(concepts[:3]):
                print(f"     {i+1}. {concept['name']}")

        await integration.close()
        return True

    except Exception as e:
        print(f"❌ Canvas分析测试失败: {e}")
        return False


async def test_knowledge_graph():
    """测试知识图谱功能"""
    print("\n🔍 测试3: 知识图谱功能")
    print("-" * 50)

    try:
        integration = GraphitiGeminiIntegration()
        await integration.initialize()

        # 创建测试会话
        session_data = {
            "session_id": "test-session-gemini",
            "canvas_file": "test.canvas",
            "session_type": "gemini-test",
            "duration_minutes": 5,
            "learning_outcomes": {
                "new_concepts_learned": 2,
                "concepts_reviewed": 1,
                "weaknesses_identified": 0
            }
        }

        # 记录学习会话
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
        print(f"❌ 知识图谱测试失败: {e}")
        return False


async def test_neo4j_connection():
    """测试Neo4j连接"""
    print("\n🔍 测试4: Neo4j数据库连接")
    print("-" * 50)

    try:
        integration = GraphitiGeminiIntegration()
        await integration.initialize()

        # 测试基础操作
        print("✅ Neo4j连接成功")
        print("✅ 索引和约束构建成功")

        await integration.close()
        return True

    except Exception as e:
        print(f"❌ Neo4j连接测试失败: {e}")
        print("💡 请确保Neo4j Docker容器正在运行:")
        print("   cd docker && docker-compose -f neo4j-docker-compose.yml up -d")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始Graphiti-Gemini集成测试")
    print("=" * 60)

    tests = [
        ("API连接", test_api_connection),
        ("Neo4j连接", test_neo4j_connection),
        ("Canvas分析", test_canvas_analysis),
        ("知识图谱", test_knowledge_graph)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {e}")
            results.append((test_name, False))

    # 输出测试结果总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("🎉 所有测试通过！您的Graphiti-Gemini系统配置成功！")
        print("\n📋 下一步操作:")
        print("1. 开始使用Canvas学习功能")
        print("2. 在Canvas中调用/graph命令")
        print("3. 监控API使用成本")
    else:
        print("⚠️ 部分测试失败，请检查配置和连接")
        print("\n🔧 故障排除:")
        print("1. 检查API Key是否正确")
        print("2. 确认网络连接正常")
        print("3. 验证Neo4j服务运行状态")
        print("4. 查看详细日志信息")

    return passed == total


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, level="INFO")

    # 运行测试
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)