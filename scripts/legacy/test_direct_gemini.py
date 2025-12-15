#!/usr/bin/env python3
"""
直接测试Gemini API到Graphiti集成
"""

import asyncio
import sys
import json
import httpx
from pathlib import Path

# 直接测试Gemini API连接
async def test_gemini_api_direct():
    """直接测试Gemini API"""
    print("Testing Gemini API Direct Connection")
    print("-" * 50)

    try:
        # API配置
        api_key = "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF"
        base_url = "https://binapi.shop/v1"
        model = "gemini-2.5-flash-preview-05-20-thinking"

        # 创建HTTP客户端
        client = httpx.Client(
            base_url=base_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        # 测试请求
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": "What is 1+1? Give a brief answer."
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }

        print(f"Sending request to: {base_url}")
        print(f"Using model: {model}")

        # 发送请求
        response = client.post("/chat/completions", json=payload)

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print("SUCCESS: Gemini API working!")
            print(f"Response: {content}")
            client.close()
            return True
        else:
            print(f"ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            client.close()
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


async def test_graphiti_neo4j():
    """测试Neo4j连接"""
    print("\nTesting Neo4j Connection")
    print("-" * 50)

    try:
        # 尝试导入Graphiti
        from graphiti_core import Graphiti

        # 连接Neo4j
        graphiti = Graphiti(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )

        # 初始化
        await graphiti.build_indices_and_constraints()
        print("SUCCESS: Neo4j connection working!")

        # 测试基础操作
        from graphiti_core.nodes import EpisodeType
        episode = await graphiti.add_episode(
            name="Test Episode",
            episode_body="This is a test episode for Gemini integration",
            source=EpisodeType.text,
            reference_time=None
        )
        print(f"SUCCESS: Test episode created: {episode.episode.uuid}")

        await graphiti.close()
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        print("TIP: Make sure Neo4j Docker is running:")
        print("  cd docker && docker-compose -f neo4j-docker-compose.yml up -d")
        return False


async def test_gemini_to_graphiti():
    """测试Gemini到Graphiti的完整流程"""
    print("\nTesting Gemini to Graphiti Integration")
    print("-" * 50)

    try:
        # 1. 获取Gemini分析
        api_key = "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF"
        base_url = "https://binapi.shop/v1"
        model = "gemini-2.5-flash-preview-05-20-thinking"

        client = httpx.Client(
            base_url=base_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        # 2. 发送概念分析请求
        analysis_prompt = """
        Analyze this mathematical concept and return JSON:

        Concept: "Function y = 2x + 1"

        Please return:
        {
          "concepts": [
            {"name": "function", "description": "mathematical relationship"},
            {"name": "linear function", "description": "polynomial of degree 1"}
          ],
          "relationships": [
            {"source": "linear function", "target": "function", "type": "is_a", "confidence": 0.9}
          ]
        }
        """

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": analysis_prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        }

        response = client.post("/chat/completions", json=payload)

        if response.status_code != 200:
            print(f"ERROR: Gemini API failed - {response.status_code}")
            client.close()
            return False

        gemini_result = response.json()
        content = gemini_result["choices"][0]["message"]["content"]
        print(f"Gemini analysis: {content[:100]}...")

        # 3. 连接Graphiti并存储结果
        from graphiti_core import Graphiti
        from graphiti_core.nodes import EntityNode, EpisodeType

        graphiti = Graphiti(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )

        await graphiti.build_indices_and_constraints()

        # 4. 创建学习会话记录
        session_episode = await graphiti.add_episode(
            name="Gemini Analysis Session",
            episode_body=f"""
            Learning Session Details:
            - API Provider: Gemini (2.5 Flash Thinking)
            - Analysis Result: {content[:200]}...
            - Status: Successfully analyzed with AI reasoning
            """,
            source=EpisodeType.text,
            source_description="Gemini AI-powered concept analysis",
            reference_time=None,
            group_id="gemini_integration"
        )

        print(f"SUCCESS: Learning session recorded: {session_episode.episode.uuid}")

        # 5. 创建概念节点（如果可能解析JSON）
        try:
            # 尝试解析JSON响应
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())

                # 创建概念节点
                concepts = analysis_data.get('concepts', [])
                for concept in concepts[:2]:  # 限制创建数量
                    concept_node = EntityNode(
                        name=concept['name'],
                        labels=['Concept', 'Gemini-Analyzed'],
                        summary=concept.get('description', '')[:100],
                        group_id='gemini_concepts'
                    )

                    node_result = await graphiti.add_nodes([concept_node])
                    print(f"Created concept node: {concept['name']}")

        except Exception as parse_error:
            print(f"JSON parsing failed, but basic integration works: {parse_error}")

        await graphiti.close()
        client.close()

        print("SUCCESS: Complete Gemini to Graphiti integration working!")
        return True

    except Exception as e:
        print(f"ERROR: Integration test failed: {e}")
        return False


async def main():
    """主测试函数"""
    print("Gemini API to Graphiti Integration Test")
    print("=" * 60)

    tests = [
        ("Gemini API Connection", test_gemini_api_direct),
        ("Neo4j Connection", test_graphiti_neo4j),
        ("Full Integration", test_gemini_to_graphiti)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))

    # 结果总结
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:30} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nEXCELLENT! Your Gemini-Graphiti integration is ready!")
        print("\nNext steps:")
        print("1. Start analyzing your Canvas files")
        print("2. Monitor API usage costs")
        print("3. Enjoy AI-powered concept analysis")
    else:
        print(f"\n{total-passed} tests failed. Check the errors above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)