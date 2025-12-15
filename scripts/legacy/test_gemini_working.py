#!/usr/bin/env python3
"""
测试修复后的Gemini集成
"""

import asyncio
import httpx
import json
from pathlib import Path
import sys

async def test_working_gemini():
    """测试修复后的Gemini配置"""
    print("Testing Fixed Gemini Configuration")
    print("=" * 50)

    try:
        # 使用支持的模型
        api_key = "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF"
        base_url = "https://binapi.shop/v1"

        # 尝试不同的模型
        models_to_test = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-pro"
        ]

        client = httpx.Client(
            base_url=base_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        for model in models_to_test:
            print(f"\nTesting model: {model}")

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Explain what a mathematical function is in one sentence."
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 200
            }

            try:
                response = client.post("/chat/completions", json=payload)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("choices") and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        print(f"✅ SUCCESS with {model}")
                        print(f"   Response: {content[:80]}...")

                        # 找到可用模型后测试集成
                        client.close()
                        return True, model
                    else:
                        print(f"⚠️  Empty response with {model}")
                else:
                    print(f"❌ HTTP {response.status_code} with {model}")

            except Exception as e:
                print(f"❌ Error with {model}: {e}")

        client.close()
        return False, None

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False, None


async def test_concept_analysis(model_name):
    """测试概念分析功能"""
    print(f"\nTesting Concept Analysis with {model_name}")
    print("-" * 50)

    try:
        api_key = "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF"
        base_url = "https://binapi.shop/v1"

        client = httpx.Client(
            base_url=base_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        # 概念分析请求
        analysis_prompt = """
        Analyze this mathematical concept and extract key information:

        Concept: "Linear Function y = mx + b"

        Please provide:
        1. Definition in simple terms
        2. Key components (m = slope, b = y-intercept)
        3. One example
        """

        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            "temperature": 0.5,
            "max_tokens": 500
        }

        response = client.post("/chat/completions", json=payload)

        if response.status_code == 200:
            result = response.json()
            if result.get("choices") and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print("✅ Concept analysis successful!")
                print(f"   Analysis length: {len(content)} characters")
                print(f"   Preview: {content[:100]}...")

                client.close()
                return True
            else:
                print("❌ Empty response for concept analysis")
        else:
            print(f"❌ HTTP {response.status_code} for concept analysis")

        client.close()
        return False

    except Exception as e:
        print(f"❌ Concept analysis failed: {e}")
        return False


async def test_graphiti_with_env():
    """测试Graphiti连接（带环境变量）"""
    print("\nTesting Graphiti with Environment Variables")
    print("-" * 50)

    try:
        # 设置环境变量
        import os
        os.environ["OPENAI_API_KEY"] = "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF"

        from graphiti_core import Graphiti

        print("✅ Graphiti import successful")

        # 尝试连接
        graphiti = Graphiti(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )

        print("✅ Graphiti client created")

        # 初始化
        await graphiti.build_indices_and_constraints()
        print("✅ Neo4j indices built successfully")

        # 测试基础操作
        from graphiti_core.nodes import EpisodeType

        episode = await graphiti.add_episode(
            name="Gemini Integration Test",
            episode_body="This is a test episode to verify Gemini API integration with Graphiti knowledge graph.",
            source=EpisodeType.text,
            source_description="AI-powered concept analysis using Gemini",
            reference_time=None,
            group_id="test_integration"
        )

        print(f"✅ Test episode created: {episode.episode.uuid}")

        await graphiti.close()
        return True

    except Exception as e:
        print(f"❌ Graphiti test failed: {e}")
        print("TIP: Make sure Neo4j Docker is running:")
        print("  cd docker && docker-compose -f neo4j-docker-compose.yml up -d")
        return False


async def main():
    """主测试函数"""
    print("Gemini Integration Test Suite")
    print("=" * 60)

    # 测试1: 找到可用的模型
    success, working_model = await test_working_gemini()

    if not success:
        print("\n❌ No working Gemini model found")
        return False

    print(f"\n✅ Working model found: {working_model}")

    # 测试2: 概念分析
    analysis_success = await test_concept_analysis(working_model)

    # 测试3: Graphiti集成
    graphiti_success = await test_graphiti_with_env()

    # 结果总结
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)

    results = [
        ("Gemini API", success),
        ("Concept Analysis", analysis_success),
        ("Graphiti Integration", graphiti_success)
    ]

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour Gemini-Graphiti integration is working!")
        print("\nNext steps:")
        print("1. Create configuration files for Canvas analysis")
        print("2. Test with your actual Canvas files")
        print("3. Monitor API usage and costs")
        print("4. Enjoy AI-powered concept analysis!")

        print(f"\nConfiguration Summary:")
        print(f"- Working Model: {working_model}")
        print(f"- API Endpoint: https://binapi.shop/v1")
        print(f"- Neo4j: localhost:7687")
        print(f"- Environment: OPENAI_API_KEY set")

    else:
        print(f"\n⚠️ {total-passed} tests failed")
        print("Check the errors above for troubleshooting")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)