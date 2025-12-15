#!/usr/bin/env python3
"""验证Neo4j中的时序记忆存储"""

from neo4j import GraphDatabase
import json

def verify_neo4j_storage():
    """查询Neo4j验证时序记忆是否真的存储了数据"""

    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "707188Fx"

    print(f"连接Neo4j: {uri}")
    print(f"数据库: ultrathink")
    print("="*60)

    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))

        # 1. 检查数据库中所有节点
        with driver.session(database="ultrathink") as session:
            print("\n[1] 检查数据库中所有节点...")
            print("-"*60)

            result = session.run("MATCH (n) RETURN count(n) as total")
            total_nodes = result.single()["total"]
            print(f"  总节点数: {total_nodes}")

            if total_nodes == 0:
                print("  [X] Database is empty!")
                return False

            # 2. 查找最近创建的节点
            print("\n[2] 查找最近创建的10个节点...")
            print("-"*60)

            result = session.run("""
                MATCH (n)
                RETURN n, labels(n) as labels, id(n) as node_id
                ORDER BY id(n) DESC
                LIMIT 10
            """)

            nodes_found = 0
            for record in result:
                nodes_found += 1
                node = record["n"]
                labels = record["labels"]
                node_id = record["node_id"]

                print(f"\n  节点 #{node_id}:")
                print(f"    标签: {labels}")
                print(f"    属性: {dict(node)}")

            if nodes_found == 0:
                print("  [!] No nodes found")

            # 3. 搜索包含session_id的节点
            print("\n[3] 搜索包含session_id的节点...")
            print("-"*60)

            target_session_id = "119fd7cf-c39c-4e78-9079-15e913aba9b3"
            print(f"  目标session_id: {target_session_id}")

            result = session.run("""
                MATCH (n)
                WHERE n.session_id = $session_id
                   OR n.id = $session_id
                   OR toString(n.session_id) = $session_id
                RETURN n, labels(n) as labels, id(n) as node_id
            """, session_id=target_session_id)

            session_nodes_found = 0
            for record in result:
                session_nodes_found += 1
                node = record["n"]
                labels = record["labels"]
                node_id = record["node_id"]

                print(f"\n  [OK] Found matching node #{node_id}:")
                print(f"    Labels: {labels}")
                print(f"    Properties: {json.dumps(dict(node), indent=4, ensure_ascii=False)}")

            if session_nodes_found == 0:
                print(f"  [X] No nodes found with session_id: {target_session_id}")

                # 4. 显示所有节点的属性，看看有没有其他命名方式
                print("\n[4] 显示所有节点的属性键...")
                print("-"*60)

                result = session.run("""
                    MATCH (n)
                    RETURN DISTINCT keys(n) as property_keys
                    LIMIT 20
                """)

                for record in result:
                    keys = record["property_keys"]
                    print(f"  属性键: {keys}")
            else:
                print(f"\n[OK] Verification successful: Found {session_nodes_found} session-related nodes in Neo4j")
                return True

            # 5. 检查是否有任何Learning相关的节点
            print("\n[5] 搜索Learning相关标签的节点...")
            print("-"*60)

            result = session.run("""
                MATCH (n)
                WHERE any(label IN labels(n) WHERE label CONTAINS 'Session'
                                              OR label CONTAINS 'Learning'
                                              OR label CONTAINS 'Temporal')
                RETURN n, labels(n) as labels, id(n) as node_id
                LIMIT 10
            """)

            learning_nodes = 0
            for record in result:
                learning_nodes += 1
                node = record["n"]
                labels = record["labels"]
                node_id = record["node_id"]

                print(f"\n  节点 #{node_id}:")
                print(f"    标签: {labels}")
                print(f"    属性: {json.dumps(dict(node), indent=4, ensure_ascii=False)}")

            if learning_nodes == 0:
                print("  [!] No Learning-related nodes found")

        driver.close()

        print("\n" + "="*60)
        print("验证完成")
        print("="*60)

        return total_nodes > 0

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_neo4j_storage()
