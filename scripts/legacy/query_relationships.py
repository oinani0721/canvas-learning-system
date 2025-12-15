#!/usr/bin/env python3
"""
自定义关系查询工具
"""

from neo4j import GraphDatabase

def custom_query():
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

    with driver.session() as session:
        print("=== 自定义查询工具 ===")
        print("1. 查看线性函数相关的所有关系")

        result = session.run('''
            MATCH path = (start:Concept)-[*]-(end:Concept)
            WHERE start.name CONTAINS "线性" OR end.name CONTAINS "线性"
            RETURN [node in nodes(path) | node.name] as concepts
        ''')

        paths = result.data()
        print(f"   找到 {len(paths)} 条相关路径")

        print("\n2. 查看HAS_COMPONENT关系")
        result = session.run('''
            MATCH (c1)-[r:HAS_COMPONENT]->(c2)
            RETURN c1.name as parent, c2.name as component, r.created_at as when
            ORDER BY r.created_at
        ''')

        components = result.data()
        for comp in components:
            print(f"   {comp['parent']} -> {comp['component']}")

        print("\n3. 查看最新创建的5个节点")
        result = session.run('''
            MATCH (n)
            WHERE n.created_at IS NOT NULL
            RETURN n.name as name, n.created_at as created, labels(n) as labels
            ORDER BY n.created_at DESC
            LIMIT 5
        ''')

        recent = result.data()
        for node in recent:
            labels = ', '.join(node['labels'])
            print(f"   {node['name']} ({labels})")

    driver.close()

if __name__ == "__main__":
    custom_query()