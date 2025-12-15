#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test /learning command Neo4j connectivity
"""
import sys
import os
import time

# 设置环境变量（在导入前）
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "707188Fx"

print("\n" + "="*80)
print("/learning 命令 Neo4j 连接测试")
print("="*80)

print("\n[配置] 环境变量:")
print(f"  NEO4J_URI: {os.getenv('NEO4J_URI')}")
print(f"  NEO4J_USER: {os.getenv('NEO4J_USER')}")
print(f"  NEO4J_PASSWORD: *** (已隐藏)")

# 添加路径
sys.path.insert(0, r'C:\Users\ROG\托福\graphiti\mcp_server')

print("\n[步骤 1] 导入 Neo4jMemoryStore...")
try:
    from neo4j_mcp_server import Neo4jMemoryStore
    print("✓ 导入成功")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

print("\n[步骤 2] 创建 Neo4jMemoryStore 实例...")
print("  (这将测试 Neo4j 连接并执行重试逻辑)\n")

try:
    store = Neo4jMemoryStore()
    print(f"\n✓ 实例创建成功")
    print(f"  连接状态: {'已连接到 Neo4j ✓' if store.neo4j_connected else '使用内存备份存储'}")
except Exception as e:
    print(f"\n✗ 实例创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if not store.neo4j_connected:
    print("\n⚠️  警告: Neo4j 连接失败，使用内存备份模式")
    print("\n可能的原因:")
    print("  1. Neo4j 速率限制（短时间内太多认证尝试）")
    print("  2. 密码已更改")
    print("  3. Neo4j 服务重启中")
    print("\n建议:")
    print("  1. 等待 1-2 分钟后重试")
    print("  2. 在 Neo4j Browser 中手动登录测试")
    print("  3. 检查 Neo4j Desktop 状态")
else:
    print("\n[步骤 3] 测试 /learning 命令所需的功能...")

    # 测试 add_memory
    try:
        memory_id = store.add_memory(
            key="test_learning_session",
            content="这是一个学习会话测试记录"
        )
        print(f"  ✓ add_memory() 工作正常: {memory_id}")
    except Exception as e:
        print(f"  ✗ add_memory() 失败: {e}")

    # 测试 add_relationship
    try:
        rel = store.add_relationship(
            "学习会话", "Canvas白板", "USES"
        )
        print(f"  ✓ add_relationship() 工作正常")
    except Exception as e:
        print(f"  ✗ add_relationship() 失败: {e}")

    # 测试 export_memories
    try:
        data = store.export_memories()
        mem_count = len(data.get('memories', []))
        rel_count = len(data.get('relationships', []))
        print(f"  ✓ export_memories() 工作正常")
        print(f"    - 记忆数: {mem_count}")
        print(f"    - 关系数: {rel_count}")
    except Exception as e:
        print(f"  ✗ export_memories() 失败: {e}")

print("\n" + "="*80)
print("测试完成")
print("="*80)

if store.neo4j_connected:
    print("\n✓✓✓ 成功！/learning 命令可以使用 Neo4j 数据库")
    print("    现在可以执行 /learning start 命令了")
else:
    print("\n⚠️  /learning 命令将使用内存备份模式")
    print("    功能可用但数据不会持久化到 Neo4j")

print("="*80 + "\n")
