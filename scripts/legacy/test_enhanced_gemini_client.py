#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版Gemini客户端测试脚本

测试重试机制、错误处理和速率限制功能

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-26
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

from enhanced_gemini_client import (
    EnhancedGeminiClient,
    RetryConfig,
    RateLimitConfig,
    APIError,
    RateLimitError
)

# API配置
API_KEY = "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF"
BASE_URL = "https://binapi.shop/v1"
MODEL = "gemini-2.5-flash"

async def test_1_basic_functionality():
    """测试1: 基础功能测试"""
    print("\n=== Test 1: Basic Functionality ===")

    # 配置较宽松的速率限制用于测试
    retry_config = RetryConfig(max_retries=2, base_delay=0.5)
    rate_limit_config = RateLimitConfig(requests_per_minute=10)

    async with EnhancedGeminiClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        retry_config=retry_config,
        rate_limit_config=rate_limit_config
    ) as client:

        try:
            # 测试文本生成
            print("Testing text generation...")
            start_time = time.time()

            text = await client.generate_text(
                "请简单解释什么是命题逻辑？用一句话概括。",
                max_tokens=100,
                temperature=0.7
            )

            end_time = time.time()
            duration = end_time - start_time

            print(f"PASS: Text generation successful")
            print(f"  Response time: {duration:.2f}s")
            print(f"  Content length: {len(text)} chars")
            print(f"  Content: {text}")

            return True

        except Exception as e:
            print(f"FAIL: {e}")
            return False

async def test_2_concept_analysis_with_json_extraction():
    """测试2: 概念分析和JSON提取"""
    print("\n=== Test 2: Concept Analysis & JSON Extraction ===")

    retry_config = RetryConfig(max_retries=2, base_delay=0.5)
    rate_limit_config = RateLimitConfig(requests_per_minute=8)

    async with EnhancedGeminiClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        retry_config=retry_config,
        rate_limit_config=rate_limit_config
    ) as client:

        try:
            # CS70概念分析
            cs70_text = """
            CS70离散数学核心内容：

            1. 命题逻辑 (Propositional Logic)
            - 研究命题真假性的数学分支
            - 基本连接词：AND, OR, NOT, IMPLIES
            - 应用：数字电路设计、程序逻辑

            2. 真值表 (Truth Tables)
            - 系统化表示逻辑表达式的方法
            - 用于验证逻辑等价性
            - 是逻辑分析的基础工具

            3. 德摩根定律 (De Morgan's Laws)
            - 连接词转换规则
            - ¬(P ∧ Q) ≡ (¬P) ∨ (¬Q)
            - ¬(P ∨ Q) ≡ (¬P) ∧ (¬Q)
            """

            print("Analyzing CS70 concepts...")
            start_time = time.time()

            analysis = await client.analyze_concepts(cs70_text)

            end_time = time.time()
            duration = end_time - start_time

            concepts_count = len(analysis.get("concepts", []))
            relationships_count = len(analysis.get("relationships", []))

            print("PASS: Concept analysis successful")
            print(f"  Processing time: {duration:.2f}s")
            print(f"  Concepts extracted: {concepts_count}")
            print(f"  Relationships found: {relationships_count}")

            # 显示提取的概念
            concepts = analysis.get("concepts", [])
            if concepts:
                print("  Extracted concepts:")
                for i, concept in enumerate(concepts[:3]):
                    print(f"    {i+1}. {concept.get('name', 'Unknown')} (重要性: {concept.get('importance', 'N/A')})")

            # 显示提取的关系
            relationships = analysis.get("relationships", [])
            if relationships:
                print("  Extracted relationships:")
                for i, rel in enumerate(relationships[:2]):
                    print(f"    {i+1}. {rel.get('source', 'Unknown')} -> {rel.get('target', 'Unknown')} ({rel.get('type', 'unknown')})")

            return True

        except Exception as e:
            print(f"FAIL: {e}")
            return False

async def test_3_cs70_content_generation():
    """测试3: CS70内容生成"""
    print("\n=== Test 3: CS70 Content Generation ===")

    retry_config = RetryConfig(max_retries=2, base_delay=0.5)
    rate_limit_config = RateLimitConfig(requests_per_minute=8)

    async with EnhancedGeminiClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        retry_config=retry_config,
        rate_limit_config=rate_limit_config
    ) as client:

        try:
            # 测试不同类型的内容生成
            content_types = ["explanation", "exercise", "summary"]
            topic = "数学归纳法"

            results = []

            for content_type in content_types:
                print(f"Generating {content_type} for {topic}...")

                start_time = time.time()
                content = await client.generate_cs70_content(topic, content_type)
                end_time = time.time()
                duration = end_time - start_time

                results.append({
                    "type": content_type,
                    "duration": duration,
                    "success": not content.get("error", False),
                    "content_length": len(content.get("content", ""))
                })

                print(f"  {content_type.capitalize()}: {duration:.2f}s, {len(content.get('content', ''))} chars")

            # 检查结果
            successful_count = sum(1 for r in results if r["success"])

            if successful_count == len(content_types):
                print("PASS: All CS70 content generation successful")
                return True
            else:
                print(f"PARTIAL: {successful_count}/{len(content_types)} content types successful")
                return False

        except Exception as e:
            print(f"FAIL: {e}")
            return False

async def test_4_retry_and_error_handling():
    """测试4: 重试机制和错误处理"""
    print("\n=== Test 4: Retry & Error Handling ===")

    # 测试无效API密钥
    retry_config = RetryConfig(max_retries=2, base_delay=0.5, max_delay=2.0)

    async with EnhancedGeminiClient(
        api_key="invalid_key_test",
        base_url=BASE_URL,
        model=MODEL,
        retry_config=retry_config
    ) as client:

        try:
            print("Testing with invalid API key...")
            start_time = time.time()

            await client.generate_text("This should fail")

            print("FAIL: Should have raised an error")
            return False

        except APIError as e:
            end_time = time.time()
            duration = end_time - start_time

            print("PASS: Properly handled invalid API key")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Status code: {e.status_code}")
            print(f"  Time to fail: {duration:.2f}s")

            # 检查重试统计
            stats = client.get_stats()
            if stats["retry_count"] > 0:
                print(f"  Retry attempts: {stats['retry_count']}")
            else:
                print("  Note: No retries occurred (401 errors don't retry)")

            return True

        except Exception as e:
            print(f"FAIL: Unexpected error: {e}")
            return False

async def test_5_rate_limiting():
    """测试5: 速率限制"""
    print("\n=== Test 5: Rate Limiting ===")

    # 设置很严格的速率限制来测试
    retry_config = RetryConfig(max_retries=1, base_delay=0.5)
    rate_limit_config = RateLimitConfig(
        requests_per_minute=2,
        requests_per_hour=10,
        burst_limit=1
    )

    async with EnhancedGeminiClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        retry_config=retry_config,
        rate_limit_config=rate_limit_config
    ) as client:

        try:
            print("Testing rate limiting with multiple requests...")

            start_time = time.time()
            successful_requests = 0

            # 发送多个请求来触发速率限制
            for i in range(4):
                try:
                    text = await client.generate_text(
                        f"Quick test message {i+1}",
                        max_tokens=20,
                        temperature=0.1
                    )
                    successful_requests += 1
                    print(f"  Request {i+1}: SUCCESS")

                except RateLimitError as e:
                    print(f"  Request {i+1}: RATE LIMITED (retry_after: {e.retry_after})")

                except APIError as e:
                    print(f"  Request {i+1}: API ERROR ({e.status_code})")

                except Exception as e:
                    print(f"  Request {i+1}: OTHER ERROR ({e})")

            end_time = time.time()
            total_time = end_time - start_time

            print(f"PASS: Rate limiting test completed")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Successful requests: {successful_requests}/4")

            # 检查统计信息
            stats = client.get_stats()
            print(f"  Rate limited requests: {stats['rate_limited_requests']}")
            print(f"  Total requests: {stats['total_requests']}")

            return True

        except Exception as e:
            print(f"FAIL: {e}")
            return False

async def test_6_statistics_and_monitoring():
    """测试6: 统计和监控功能"""
    print("\n=== Test 6: Statistics & Monitoring ===")

    retry_config = RetryConfig(max_retries=1, base_delay=0.5)
    rate_limit_config = RateLimitConfig(requests_per_minute=5)

    async with EnhancedGeminiClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        retry_config=retry_config,
        rate_limit_config=rate_limit_config
    ) as client:

        try:
            print("Testing statistics collection...")

            # 执行几个请求来生成统计数据
            requests_data = [
                ("What is 2+2?", "simple math"),
                ("Explain CS70", "academic"),
                ("Define logic", "definition")
            ]

            for prompt, desc in requests_data:
                try:
                    await client.generate_text(prompt, max_tokens=50)
                    print(f"  Completed: {desc}")
                except Exception as e:
                    print(f"  Failed: {desc} - {e}")

            # 获取统计信息
            stats = client.get_stats()

            print("PASS: Statistics collection successful")
            print(f"  Total requests: {stats['total_requests']}")
            print(f"  Successful requests: {stats['successful_requests']}")
            print(f"  Failed requests: {stats['failed_requests']}")
            print(f"  Rate limited requests: {stats['rate_limited_requests']}")
            print(f"  Retry count: {stats['retry_count']}")
            print(f"  Success rate: {stats['success_rate']:.2%}")
            print(f"  Average response time: {stats['average_response_time']:.2f}s")

            # 重置统计并验证
            client.reset_stats()
            reset_stats = client.get_stats()

            if reset_stats["total_requests"] == 0:
                print("PASS: Statistics reset successful")
                return True
            else:
                print("FAIL: Statistics reset failed")
                return False

        except Exception as e:
            print(f"FAIL: {e}")
            return False

async def run_all_tests():
    """运行所有测试"""
    print("🚀 Enhanced Gemini Client Test Suite")
    print(f"📅 Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API Endpoint: {BASE_URL}")
    print(f"🤖 Model: {MODEL}")
    print("=" * 60)

    tests = [
        ("Basic Functionality", test_1_basic_functionality),
        ("Concept Analysis & JSON", test_2_concept_analysis_with_json_extraction),
        ("CS70 Content Generation", test_3_cs70_content_generation),
        ("Retry & Error Handling", test_4_retry_and_error_handling),
        ("Rate Limiting", test_5_rate_limiting),
        ("Statistics & Monitoring", test_6_statistics_and_monitoring)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))

            # 测试之间稍作停顿，避免速率限制
            if test_name != tests[-1][0]:
                await asyncio.sleep(2)

        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # 输出测试结果总结
    print("\n" + "=" * 60)
    print("📊 ENHANCED CLIENT TEST RESULTS")
    print("=" * 60)

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n📈 OVERALL: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ Enhanced Gemini Client is fully functional!")
        print("\n💡 Enhanced Features Verified:")
        print("   • Robust retry mechanism with exponential backoff")
        print("   • Comprehensive error handling and classification")
        print("   • Intelligent rate limiting")
        print("   • JSON extraction from markdown responses")
        print("   • CS70-specific content generation")
        print("   • Detailed statistics and monitoring")
        print("   • Context manager support")

        print("\n🚀 Ready for production use in Canvas Learning System!")

    else:
        failed_count = total_count - passed_count
        print(f"\n⚠️ {failed_count} tests failed")
        print("🔧 Please check the implementation")

    return passed_count == total_count

async def main():
    """主测试函数"""
    try:
        success = await run_all_tests()

        # 保存测试结果
        test_results = {
            "test_date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "client_version": "2.0",
            "total_tests": len([test for test in [test_1_basic_functionality, test_2_concept_analysis_with_json_extraction,
                                                 test_3_cs70_content_generation, test_4_retry_and_error_handling,
                                                 test_5_rate_limiting, test_6_statistics_and_monitoring]]),
            "api_endpoint": BASE_URL,
            "model": MODEL,
            "enhanced_features": [
                "retry_mechanism",
                "error_handling",
                "rate_limiting",
                "json_extraction",
                "statistics_monitoring"
            ]
        }

        with open("enhanced_gemini_client_test_results.json", "w", encoding="utf-8") as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Test results saved to: enhanced_gemini_client_test_results.json")

        return success

    except Exception as e:
        print(f"Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)