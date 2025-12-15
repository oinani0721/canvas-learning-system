#!/usr/bin/env python3
"""测试Neo4j密码"""

from neo4j import GraphDatabase

passwords = ['707188Fx', 'canvas123', 'canvas12345', 'password', 'neo4j']

for pwd in passwords:
    try:
        print(f"Testing password: '{pwd}'...", end=" ")
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', pwd))
        driver.verify_connectivity()
        print("SUCCESS!")

        # 列出数据库
        with driver.session(database="system") as session:
            result = session.run("SHOW DATABASES")
            databases = [record["name"] for record in result]
            print(f"  Available databases: {databases}")

        driver.close()
        print(f"\nCorrect password is: {pwd}")
        break
    except Exception as e:
        print(f"Failed: {type(e).__name__}")
