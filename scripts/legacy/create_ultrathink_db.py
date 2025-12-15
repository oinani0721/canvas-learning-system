#!/usr/bin/env python3
"""
创建Neo4j ultrathink数据库
"""

from neo4j import GraphDatabase
import sys

def create_database():
    """创建ultrathink数据库"""

    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "707188Fx"

    print(f"连接Neo4j: {uri}")

    try:
        # 连接到system数据库（用于管理操作）
        driver = GraphDatabase.driver(uri, auth=(username, password))

        with driver.session(database="system") as session:
            # 检查数据库是否存在
            result = session.run("SHOW DATABASES")
            databases = [record["name"] for record in result]

            print(f"现有数据库: {databases}")

            if "ultrathink" in databases:
                print("✅ 数据库 'ultrathink' 已存在")
            else:
                print("创建数据库 'ultrathink'...")
                session.run("CREATE DATABASE ultrathink IF NOT EXISTS")
                print("✅ 数据库 'ultrathink' 创建成功")

        driver.close()
        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
