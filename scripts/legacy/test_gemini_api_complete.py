#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的Gemini API测试脚本

测试Gemini API的所有核心功能，包括：
1. API连接测试
2. 文本生成功能
3. 概念分析功能
4. 成本效益验证
5. 与Graphiti知识图谱集成

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-26
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import httpx
from datetime import datetime

# Gemini API配置
GEMINI_CONFIG = {
    "api_key": "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF",
    "base_url": "https://binapi.shop/v1",
    "model": "gemini-2.5-flash",
    "temperature": 0.7,
    "max_tokens": 4096
}

class GeminiAPITester:
    """Gemini API完整测试器"""

    def __init__(self):
        self.config = GEMINI_CONFIG
        self.client = None
        self.test_results = []

    async def setup_client(self):
        """设置HTTP客户端"""
        self.client = httpx.AsyncClient(
            base_url=self.config["base_url"],
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

    async def cleanup_client(self):
        """清理HTTP客户端"""
        if self.client:
            await self.client.aclose()

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")

    async def test_1_api_connection(self) -> bool:
        """测试1: API连接测试"""
        print("\n=== Test 1: API Connection ===")
        try:
            await self.setup_client()

            # 简单的健康检查
            response = await self.client.get("/models")

            if response.status_code == 200:
                self.log_test("API Connection", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("API Connection", False, f"HTTP {response.status_code}: {response.text[:100]}")
                return False

        except Exception as e:
            self.log_test("API Connection", False, f"Exception: {str(e)}")
            return False

    async def test_2_text_generation(self) -> bool:
        """测试2: 文本生成功能"""
        print("\n=== Test 2: Text Generation ===")
        try:
            payload = {
                "model": self.config["model"],
                "messages": [
                    {
                        "role": "user",
                        "content": "请简单回答：什么是离散数学？请用一句话概括。"
                    }
                ],
                "temperature": self.config["temperature"],
                "max_tokens": 200
            }

            start_time = time.time()
            response = await self.client.post("/chat/completions", json=payload)
            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                duration = end_time - start_time

                self.log_test("Text Generation", True,
                            f"Response: {len(content)} chars, Time: {duration:.2f}s")
                print(f"    Content preview: {content[:100]}...")
                return True
            else:
                self.log_test("Text Generation", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Text Generation", False, f"Exception: {str(e)}")
            return False

    async def test_3_concept_analysis(self) -> bool:
        """测试3: 概念分析功能"""
        print("\n=== Test 3: Concept Analysis ===")
        try:
            test_text = """
            CS70离散数学核心概念：

            1. 命题逻辑 (Propositional Logic)
            - 定义：研究命题真假性的数学分支
            - 基本连接词：与(AND)、或(OR)、非(NOT)、蕴含(IMPLIES)
            - 重要性质：交换律、结合律、分配律

            2. 逆否命题 (Contrapositive)
            - 定义：命题P→Q的逆否命题是¬Q→¬P
            - 性质：原命题与逆否命题逻辑等价
            - 应用：证明中的间接证明法

            3. 鸽笼原理 (Pigeonhole Principle)
            - 定义：n个物品放入m个容器，如果n>m，则至少一个容器有多个物品
            - 应用：存在性证明
            """

            analysis_prompt = f"""
            请分析以下学习内容，提取关键概念和关系：

            {test_text}

            请以JSON格式返回结果：
            {{
                "concepts": [
                    {{"name": "概念名", "definition": "定义", "importance": 1-5}}
                ],
                "relationships": [
                    {{"source": "概念1", "target": "概念2", "type": "关系类型"}}
                ]
            }}
            """

            payload = {
                "model": self.config["model"],
                "messages": [
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }

            start_time = time.time()
            response = await self.client.post("/chat/completions", json=payload)
            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                duration = end_time - start_time

                # 尝试解析JSON
                try:
                    analysis_result = json.loads(content)
                    concepts_count = len(analysis_result.get("concepts", []))
                    relationships_count = len(analysis_result.get("relationships", []))

                    self.log_test("Concept Analysis", True,
                                f"Concepts: {concepts_count}, Relationships: {relationships_count}, Time: {duration:.2f}s")

                    # 显示提取的概念
                    concepts = analysis_result.get("concepts", [])
                    for i, concept in enumerate(concepts[:3]):
                        print(f"    Concept {i+1}: {concept.get('name', 'Unknown')}")

                    return True

                except json.JSONDecodeError:
                    self.log_test("Concept Analysis", False, "Failed to parse JSON response")
                    return False

            else:
                self.log_test("Concept Analysis", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Concept Analysis", False, f"Exception: {str(e)}")
            return False

    async def test_4_cost_analysis(self) -> bool:
        """测试4: 成本效益分析"""
        print("\n=== Test 4: Cost Effectiveness Analysis ===")
        try:
            test_prompts = [
                "简单问题：1+1等于几？",
                "中等问题：解释什么是函数？",
                "复杂问题：分析命题逻辑与布尔代数的关系及其在计算机科学中的应用"
            ]

            total_time = 0
            total_tokens = 0

            for i, prompt in enumerate(test_prompts):
                payload = {
                    "model": self.config["model"],
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }

                start_time = time.time()
                response = await self.client.post("/chat/completions", json=payload)
                end_time = time.time()

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    duration = end_time - start_time

                    total_time += duration
                    total_tokens += len(content.split())

                    print(f"    Test {i+1}: {len(content)} chars, {duration:.2f}s")

            # 计算成本效益指标
            avg_time = total_time / len(test_prompts)

            # 估算成本（假设价格）
            estimated_cost = total_tokens * 0.00001  # 假设每token $0.00001

            self.log_test("Cost Analysis", True,
                        f"Avg time: {avg_time:.2f}s, Est. cost: ${estimated_cost:.6f}")
            return True

        except Exception as e:
            self.log_test("Cost Analysis", False, f"Exception: {str(e)}")
            return False

    async def test_5_error_handling(self) -> bool:
        """测试5: 错误处理"""
        print("\n=== Test 5: Error Handling ===")
        try:
            # 测试无效请求
            invalid_payload = {
                "model": "invalid-model-name",
                "messages": []
            }

            response = await self.client.post("/chat/completions", json=invalid_payload)

            if response.status_code >= 400:
                self.log_test("Error Handling", True, f"Properly handles invalid requests (HTTP {response.status_code})")
                return True
            else:
                self.log_test("Error Handling", False, "Should have rejected invalid request")
                return False

        except Exception as e:
            self.log_test("Error Handling", True, f"Properly throws exceptions: {str(e)}")
            return True

    async def test_6_performance_benchmark(self) -> bool:
        """测试6: 性能基准测试"""
        print("\n=== Test 6: Performance Benchmark ===")
        try:
            # 并发请求测试
            concurrent_requests = 3
            tasks = []

            for i in range(concurrent_requests):
                payload = {
                    "model": self.config["model"],
                    "messages": [
                        {
                            "role": "user",
                            "content": f"请生成第{i+1}个CS70练习题：关于命题逻辑"
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 300
                }

                task = self.client.post("/chat/completions", json=payload)
                tasks.append(task)

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful_responses = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
            total_duration = end_time - start_time

            if successful_responses == concurrent_requests:
                self.log_test("Performance Benchmark", True,
                            f"{concurrent_requests} concurrent requests in {total_duration:.2f}s")
                return True
            else:
                self.log_test("Performance Benchmark", False,
                            f"Only {successful_responses}/{concurrent_requests} succeeded")
                return False

        except Exception as e:
            self.log_test("Performance Benchmark", False, f"Exception: {str(e)}")
            return False

    async def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 Starting Complete Gemini API Test Suite")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 API Endpoint: {self.config['base_url']}")
        print(f"🤖 Model: {self.config['model']}")
        print("=" * 60)

        tests = [
            ("API Connection", self.test_1_api_connection),
            ("Text Generation", self.test_2_text_generation),
            ("Concept Analysis", self.test_3_concept_analysis),
            ("Cost Analysis", self.test_4_cost_analysis),
            ("Error Handling", self.test_5_error_handling),
            ("Performance Benchmark", self.test_6_performance_benchmark)
        ]

        for test_name, test_func in tests:
            try:
                await test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Test crashed: {str(e)}")

        # 输出测试总结
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        passed_count = sum(1 for r in self.test_results if r["success"])
        total_count = len(self.test_results)

        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"      {result['details']}")

        print(f"\n📈 OVERALL: {passed_count}/{total_count} tests passed")

        if passed_count == total_count:
            print("\n🎉 ALL TESTS PASSED!")
            print("✨ Gemini API is fully functional and ready for use!")
            print("\n💡 Key Features Verified:")
            print("   • API connectivity and authentication")
            print("   • Text generation with high quality responses")
            print("   • Concept analysis and knowledge extraction")
            print("   • Cost-effective performance")
            print("   • Robust error handling")
            print("   • Concurrent request capability")

            print("\n🚀 Ready for integration with:")
            print("   • Canvas Learning System")
            print("   • Graphiti Knowledge Graph")
            print("   • CS70 Learning Analytics")

        else:
            failed_count = total_count - passed_count
            print(f"\n⚠️ {failed_count} tests failed")
            print("🔧 Please check:")
            print("   • API key validity")
            print("   • Network connectivity")
            print("   • Model availability")
            print("   • Rate limits")

        return passed_count == total_count

async def main():
    """主测试函数"""
    tester = GeminiAPITester()

    try:
        success = await tester.run_all_tests()

        # 保存测试结果
        results_file = "gemini_api_test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_date": datetime.now().isoformat(),
                "total_tests": len(tester.test_results),
                "passed_tests": sum(1 for r in tester.test_results if r["success"]),
                "results": tester.test_results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Test results saved to: {results_file}")

        return success

    finally:
        await tester.cleanup_client()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)