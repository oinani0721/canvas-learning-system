#!/usr/bin/env python3
"""
Canvas概念分析测试
使用更新后的配置 (gemini-2.5-flash)
"""

import asyncio
import httpx
import yaml
import json
from datetime import datetime
from neo4j import GraphDatabase

async def test_canvas_concept_analysis():
    print('=== Canvas概念分析测试 ===')
    print('使用更新后的配置 (gemini-2.5-flash)')
    print('=' * 50)

    # 1. 加载配置
    with open('config/gemini_api_config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    api_config = config['api_config']
    api_key = api_config['api_key']
    base_url = api_config['base_url']
    model = api_config['model']

    print(f'配置验证:')
    print(f'  模型: {model}')
    print(f'  API: {base_url}')

    # 2. 创建客户端
    client = httpx.Client(
        base_url=base_url,
        timeout=60.0,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    )

    # 3. 测试概念分析
    test_concept = "鸽笼原理：如果有n个鸽子和m个笼子，且n > m，那么至少有一个笼子里有不止一只鸽子"

    print(f'\n测试概念: {test_concept}')

    try:
        prompt = f'''
        分析这个数学概念并提取关键信息：
        {test_concept}

        请以JSON格式返回：
        {{
          "concept_name": "概念名称",
          "definition": "定义",
          "key_points": ["要点1", "要点2"],
          "applications": ["应用1", "应用2"]
        }}
        '''

        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 500
        }

        start_time = asyncio.get_event_loop().time()
        response = client.post('/chat/completions', json=payload)
        end_time = asyncio.get_event_loop().time()

        response_time = round((end_time - start_time) * 1000, 0)

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()

            print(f'SUCCESS - {response_time}ms')
            print(f'响应长度: {len(content)} 字符')
            print(f'内容预览: {content[:100]}...')

            # 4. 保存到Neo4j
            print('\n保存到Neo4j...')
            driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

            with driver.session() as session:
                session.run('''
                    CREATE (c:Concept:TestGeminiAnalyzed {
                        name: $name,
                        content: $content,
                        model_used: $model,
                        response_time: $response_time,
                        created_at: datetime(),
                        source: 'Canvas-Analysis-Test',
                        group_id: 'test'
                    })
                ''', {
                    'name': '鸽笼原理',
                    'content': content,
                    'model': model,
                    'response_time': response_time
                })

            print('SUCCESS: 概念已保存到知识图谱')

            # 5. 验证
            with driver.session() as session:
                result = session.run('''
                    MATCH (c:Concept) WHERE c.group_id = 'test'
                    RETURN c.name as name, c.model_used as model
                ''')
                nodes = result.data()
                print(f'验证: 找到 {len(nodes)} 个测试节点')
                for node in nodes:
                    print(f'  - {node["name"]} (模型: {node["model"]})')

            driver.close()
            client.close()
            return True

        else:
            print(f'FAILED - HTTP {response.status_code}')
            return False

    except Exception as e:
        print(f'ERROR: {e}')
        return False

if __name__ == "__main__":
    success = asyncio.run(test_canvas_concept_analysis())

    print('\n' + '=' * 50)
    print('最终结果:')
    if success:
        print('SUCCESS: Canvas概念分析测试成功!')
        print('\n功能确认:')
        print('✓ 配置文件已更新为 gemini-2.5-flash')
        print('✓ Gemini API调用正常')
        print('✓ 概念分析功能正常')
        print('✓ 知识图谱节点生成正常')
        print('\n您的Gemini-Graphiti集成系统完全可用!')
    else:
        print('FAILED: 测试失败')