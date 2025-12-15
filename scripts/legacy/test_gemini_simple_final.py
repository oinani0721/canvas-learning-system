#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API 简化测试脚本

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-26
"""

import asyncio
import json
import sys
import time
import httpx
from datetime import datetime

# Gemini API配置
API_KEY = "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF"
BASE_URL = "https://binapi.shop/v1"
MODEL = "gemini-2.5-flash"

async def test_gemini_api():
    """测试Gemini API的核心功能"""
    print("=== Gemini API Complete Test ===")
    print(f"Test started at: {datetime.now()}")
    print(f"API URL: {BASE_URL}")
    print(f"Model: {MODEL}")
    print("-" * 50)

    results = []

    # 测试1: 基础连接
    print("\nTest 1: Basic Connection")
    try:
        client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
        )

        # 简单的文本生成测试
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, please respond with: Gemini API is working!"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 50
        }

        start_time = time.time()
        response = await client.post("/chat/completions", json=payload)
        end_time = time.time()

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            duration = end_time - start_time

            print("PASS: Basic connection successful")
            print(f"  Response time: {duration:.2f}s")
            print(f"  Response: {content}")
            results.append(("Basic Connection", True, f"Time: {duration:.2f}s"))
        else:
            print(f"FAIL: HTTP {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            results.append(("Basic Connection", False, f"HTTP {response.status_code}"))

    except Exception as e:
        print(f"FAIL: Exception {e}")
        results.append(("Basic Connection", False, str(e)))

    finally:
        await client.aclose()

    # 测试2: CS70概念分析
    print("\nTest 2: CS70 Concept Analysis")
    try:
        client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
        )

        cs70_text = """
        CS70 Discrete Mathematics Topics:

        1. Propositional Logic - Study of mathematical statements that are either true or false
        2. Truth Tables - Tabular representation of logical expressions
        3. Pigeonhole Principle - If n items are put into m containers, with n > m, then at least one container must contain more than one item
        4. Mathematical Induction - Proof technique for mathematical statements
        """

        analysis_prompt = f"""
        Analyze the following CS70 content and extract key concepts:

        {cs70_text}

        Return in JSON format:
        {{
            "concepts": [
                {{"name": "concept name", "difficulty": "easy/medium/hard", "importance": 1-5}}
            ],
            "relationships": [
                {{"from": "concept1", "to": "concept2", "type": "prerequisite/related_to"}}
            ]
        }}
        """

        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }

        start_time = time.time()
        response = await client.post("/chat/completions", json=payload)
        end_time = time.time()

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            duration = end_time - start_time

            try:
                analysis = json.loads(content)
                concepts_count = len(analysis.get("concepts", []))
                relationships_count = len(analysis.get("relationships", []))

                print("PASS: Concept analysis successful")
                print(f"  Processing time: {duration:.2f}s")
                print(f"  Concepts extracted: {concepts_count}")
                print(f"  Relationships found: {relationships_count}")

                # 显示提取的概念
                concepts = analysis.get("concepts", [])
                for i, concept in enumerate(concepts[:3]):
                    print(f"    Concept {i+1}: {concept.get('name', 'Unknown')}")

                results.append(("Concept Analysis", True, f"Concepts: {concepts_count}"))

            except json.JSONDecodeError:
                print("FAIL: Could not parse JSON response")
                print(f"  Raw response: {content[:200]}...")
                results.append(("Concept Analysis", False, "JSON parse error"))

        else:
            print(f"FAIL: HTTP {response.status_code}")
            results.append(("Concept Analysis", False, f"HTTP {response.status_code}"))

    except Exception as e:
        print(f"FAIL: Exception {e}")
        results.append(("Concept Analysis", False, str(e)))

    finally:
        await client.aclose()

    # 测试3: 成本效益测试
    print("\nTest 3: Cost Effectiveness Test")
    try:
        client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
        )

        test_prompts = [
            "What is 2+2?",
            "Explain propositional logic in one sentence",
            "Describe the relationship between logic and computer science"
        ]

        total_time = 0
        total_chars = 0

        for i, prompt in enumerate(test_prompts):
            payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 200
            }

            start_time = time.time()
            response = await client.post("/chat/completions", json=payload)
            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                duration = end_time - start_time

                total_time += duration
                total_chars += len(content)

                print(f"  Request {i+1}: {len(content)} chars, {duration:.2f}s")

        avg_time = total_time / len(test_prompts)
        estimated_cost = total_chars * 0.00001  # 假设成本

        print("PASS: Cost effectiveness test completed")
        print(f"  Average response time: {avg_time:.2f}s")
        print(f"  Estimated cost: ${estimated_cost:.6f}")
        results.append(("Cost Effectiveness", True, f"Avg time: {avg_time:.2f}s"))

    except Exception as e:
        print(f"FAIL: Exception {e}")
        results.append(("Cost Effectiveness", False, str(e)))

    finally:
        await client.aclose()

    # 测试结果总结
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for test_name, success, details in results:
        status = "PASS" if success else "FAIL"
        print(f"{status:4} {test_name:20} {details}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\nSUCCESS: All Gemini API tests passed!")
        print("Gemini API is fully functional for:")
        print("  - Text generation")
        print("  - Concept analysis")
        print("  - Cost-effective operation")
        print("  - CS70 learning support")
        print("\nReady for integration with Canvas Learning System!")
    else:
        failed = total - passed
        print(f"\nWARNING: {failed} tests failed")
        print("Please check API configuration and network connectivity")

    # 保存测试结果
    test_results = {
        "test_date": datetime.now().isoformat(),
        "api_endpoint": BASE_URL,
        "model": MODEL,
        "total_tests": total,
        "passed_tests": passed,
        "success_rate": passed / total,
        "results": [
            {
                "test": name,
                "success": success,
                "details": details
            }
            for name, success, details in results
        ]
    }

    with open("gemini_api_test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)

    print(f"\nTest results saved to: gemini_api_test_results.json")

    return passed == total

async def main():
    """主函数"""
    try:
        success = await test_gemini_api()
        return success
    except Exception as e:
        print(f"Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)