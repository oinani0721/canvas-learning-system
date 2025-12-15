#!/usr/bin/env python3
"""
Graphiti知识图谱关系查看工具
"""

from neo4j import GraphDatabase
import json

def view_knowledge_graph():
    """查看知识图谱的节点和关系"""

    print("=== Graphiti知识图谱关系查看器 ===")
    print("=" * 60)

    # 连接到Neo4j
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

    with driver.session() as session:

        # 1. 统计总览
        print("\n📊 知识图谱总览:")

        result = session.run('MATCH (n) RETURN count(n) as node_count')
        node_count = result.single()['node_count']
        print(f"  节点总数: {node_count}")

        result = session.run('MATCH ()-[r]->() RETURN count(r) as rel_count')
        rel_count = result.single()['rel_count']
        print(f"  关系总数: {rel_count}")

        # 2. 按类型统计
        print("\n🏷️  节点类型统计:")
        result = session.run('''
            MATCH (n)
            WITH labels(n) as labels, count(n) as count
            RETURN labels, count
            ORDER BY count DESC
        ''')

        type_stats = result.data()
        for stat in type_stats:
            labels = ",".join(stat['labels'])
            print(f"  {labels}: {stat['count']} 个")

        # 3. 所有概念节点
        print("\n🧠 概念节点列表:")
        result = session.run('''
            MATCH (c:Concept)
            RETURN c.name as name,
                   c.description as description,
                   c.difficulty as difficulty,
                   c.created_at as created,
                   labels(c) as labels
            ORDER BY c.created_at DESC
        ''')

        concepts = result.data()
        for i, concept in enumerate(concepts, 1):
            difficulty = concept.get('difficulty', '未知')
            desc = concept.get('description', '无描述')[:50]
            labels = ",".join(concept['labels'])
            print(f"  {i}. {concept['name']}")
            print(f"     难度: {difficulty} | 类型: {labels}")
            print(f"     描述: {desc}...")
            print()

        # 4. 关系详情
        print("🔗 概念关系详情:")
        result = session.run('''
            MATCH (c1:Concept)-[r]->(c2:Concept)
            RETURN c1.name as from_concept,
                   type(r) as relationship,
                   c2.name as to_concept,
                   r.confidence as confidence,
                   r.created_at as created
            ORDER BY r.created_at DESC
        ''')

        relationships = result.data()
        if relationships:
            for i, rel in enumerate(relationships, 1):
                confidence = rel.get('confidence', 'N/A')
                print(f"  {i}. {rel['from_concept']} → {rel['to_concept']}")
                print(f"     关系: {rel['relationship']} | 置信度: {confidence}")
                print()
        else:
            print("  (暂无关系记录)")

        # 5. 按组查看
        print("📂 按学习组查看:")
        result = session.run('''
            MATCH (n) WHERE n.group_id IS NOT NULL
            RETURN n.group_id as group_id, count(n) as count
            ORDER BY count DESC
        ''')

        groups = result.data()
        for group in groups:
            print(f"  {group['group_id']}: {group['count']} 个节点")

            # 显示该组的节点
            result = session.run('''
                MATCH (n) WHERE n.group_id = $group_id
                RETURN n.name as name, labels(n) as labels
                ORDER BY n.created_at DESC
            ''', group_id=group['group_id'])

            group_nodes = result.data()
            for node in group_nodes[:3]:  # 只显示前3个
                labels = ",".join(node['labels'])
                print(f"    - {node['name']} ({labels})")
            if len(group_nodes) > 3:
                print(f"    ... 还有 {len(group_nodes) - 3} 个节点")
            print()

        # 6. 搜索示例
        print("🔍 搜索示例:")
        search_terms = ["线性", "函数", "鸽笼", "归纳"]

        for term in search_terms:
            result = session.run('''
                MATCH (n) WHERE n.name CONTAINS $term OR n.description CONTAINS $term
                RETURN n.name as name, labels(n) as labels
                LIMIT 3
            ''', term=term)

            matches = result.data()
            if matches:
                print(f"  '{term}' 相关节点:")
                for match in matches:
                    labels = ",".join(match['labels'])
                    print(f"    - {match['name']} ({labels})")

    driver.close()
    print("\n" + "=" * 60)
    print("💡 提示: 你也可以使用 Neo4j Browser (http://localhost:7474) 进行可视化查看")

if __name__ == "__main__":
    view_knowledge_graph()