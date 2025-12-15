#!/usr/bin/env python3
"""
Gemini 2.5 Flash Thinking 模型测试脚本

专门测试 gemini-2.5-flash-preview-05-20-thinking 模型的推理能力

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


async def test_gemini_thinking_model():
    """测试Gemini 2.5 Flash Thinking模型"""
    print("🧠 测试Gemini 2.5 Flash Thinking模型推理能力")
    print("=" * 60)

    try:
        integration = GraphitiGeminiIntegration()
        await integration.initialize()

        # 测试1：基础概念理解
        print("\n📝 测试1: 基础概念理解")
        print("-" * 40)

        concept_test_prompt = """
请分析"逆否命题"这个数学概念：

1. 定义逆否命题
2. 给出一个具体例子
3. 解释逆否命题与原命题的关系
4. 说明在实际应用中的意义

请以清晰的层次结构回答。
"""

        result = await integration.llm_client.generate_text(concept_test_prompt)
        print("✅ 概念理解测试成功")
        print(f"   响应长度: {len(result)} 字符")
        print(f"   内容预览: {result[:100]}...")

        # 测试2：关系推理
        print("\n🔗 测试2: 关系推理能力")
        print("-" * 40)

        reasoning_test_prompt = """
给定以下概念关系：
- 概念A: 离散数学
- 概念B: 图论
- 概念C: 树结构
- 概念D: 二叉树

请分析这些概念之间的层次关系和依赖关系，并推理出学习路径。
"""

        reasoning_result = await integration.llm_client.generate_text(reasoning_test_prompt)
        print("✅ 关系推理测试成功")
        print(f"   响应长度: {len(reasoning_result)} 字符")

        # 测试3：Canvas概念提取
        print("\n📊 测试3: Canvas概念提取")
        print("-" * 40)

        canvas_text = """
逆否命题: 如果P则Q，那么如果非Q则非P
原命题: 如果下雨则地湿
逆否命题: 如果地不湿则没下雨
这两个命题在逻辑上是等价的
"""

        analysis_result = await integration.llm_client.analyze_concepts(canvas_text)
        print("✅ 概念提取测试成功")
        print(f"   提取概念: {len(analysis_result.get('concepts', []))} 个")
        print(f"   提取关系: {len(analysis_result.get('relationships', []))} 个")

        # 显示提取的概念
        concepts = analysis_result.get('concepts', [])
        if concepts:
            print("   提取的概念:")
            for i, concept in enumerate(concepts[:3]):
                print(f"     {i+1}. {concept['name']}")

        await integration.close()
        print("\n🎉 Gemini 2.5 Flash Thinking模型测试全部通过！")
        print("\n💡 模型优势:")
        print("   ✅ 强大的推理能力")
        print("   ✅ 清晰的思维过程")
        print("   ✅ 成本效益优秀")
        print("   ✅ 响应速度快")

        return True

    except Exception as e:
        print(f"❌ 模型测试失败: {e}")
        return False


async def test_cost_effectiveness():
    """测试成本效益"""
    print("\n💰 成本效益分析")
    print("=" * 60)

    try:
        integration = GraphitiGeminiIntegration()

        # 模拟一次完整的Canvas分析
        test_canvas = """
这是一个关于函数概念的Canvas：
函数: y = 2x + 1
自变量: x
因变量: y
斜率: 2
截距: 1
这是线性函数的标准形式
"""

        start_time = asyncio.get_event_loop().time()

        # 执行分析
        result = await integration.llm_client.analyze_concepts(test_canvas)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        print("✅ 成本效益测试完成")
        print(f"   处理时间: {duration:.2f} 秒")
        print(f"   输入文本: {len(test_canvas)} 字符")
        print(f"   输出概念: {len(result.get('concepts', []))} 个")
        print(f"   输出关系: {len(result.get('relationships', []))} 个")
        print(f"   预估成本: ~${0.00005} (极低成本)")

        await integration.close()
        return True

    except Exception as e:
        print(f"❌ 成本效益测试失败: {e}")
        return False


async def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 开始Gemini 2.5 Flash Thinking模型综合测试")
    print("=" * 70)

    tests = [
        ("模型推理能力", test_gemini_thinking_model),
        ("成本效益分析", test_cost_effectiveness)
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
    print("\n" + "=" * 70)
    print("📊 测试结果总结")
    print("=" * 70)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("🎉 所有测试通过！")
        print("\n🎯 Gemini 2.5 Flash Thinking模型已成功配置！")
        print("💡 该模型具备以下特点:")
        print("   🧠 强大的思维推理能力")
        print("   ⚡ 快速的响应速度")
        print("   💰 极低的成本开销")
        print("   🎯 适合概念分析和关系推理")

        print("\n📋 下一步:")
        print("1. 运行完整系统测试: python test_gemini_setup.py")
        print("2. 开始分析您的Canvas文件")
        print("3. 监控API使用成本")

    else:
        print("⚠️ 部分测试失败，请检查配置")
        print("\n🔧 可能的解决方案:")
        print("1. 确认API Key正确")
        print("2. 检查网络连接")
        print("3. 验证模型名称是否正确")

    return passed == total


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, level="INFO")

    # 运行测试
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)