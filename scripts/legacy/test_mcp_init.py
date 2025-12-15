#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test MCP server initialization directly
"""
import sys
import os
import logging

# Setup logging BEFORE importing neo4j_mcp_server
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("\n" + "="*70)
print("[TEST] MCP Server Initialization")
print("="*70)

# Set environment variables before import
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "707188Fx"

print(f"\nEnvironment variables set:")
print(f"  NEO4J_URI={os.getenv('NEO4J_URI')}")
print(f"  NEO4J_USER={os.getenv('NEO4J_USER')}")
print(f"  NEO4J_PASSWORD=707188Fx (hidden for security)")

# Add the MCP server path to Python path
sys.path.insert(0, r'C:\Users\ROG\托福\graphiti\mcp_server')

print(f"\n[STEP 1] Importing Neo4jMemoryStore...")
try:
    from neo4j_mcp_server import Neo4jMemoryStore
    print("[SUCCESS] Import successful")
except Exception as e:
    print(f"[FAILED] Import failed: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

print(f"\n[STEP 2] Creating Neo4jMemoryStore instance...")
try:
    store = Neo4jMemoryStore()
    print(f"[SUCCESS] Store created")
    print(f"  neo4j_connected: {store.neo4j_connected}")
    if store.neo4j_connected:
        print(f"  Driver: {store.driver}")
    else:
        print(f"  Using memory fallback")
except Exception as e:
    print(f"[FAILED] Store creation failed: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

print(f"\n[STEP 3] Testing store methods...")
try:
    # Test add_memory
    memory_id = store.add_memory("test_key", "test_content")
    print(f"[SUCCESS] add_memory works: {memory_id}")

    # Test add_relationship (this is what was failing before)
    rel = store.add_relationship("Entity1", "Entity2", "RELATES_TO")
    print(f"[SUCCESS] add_relationship works: {rel}")
except Exception as e:
    print(f"[FAILED] Method test failed: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

print("\n" + "="*70)
print("[RESULT]")
print("="*70)
if store.neo4j_connected:
    print("✅ Neo4j connection is WORKING in MCP server context!")
else:
    print("⚠️ Neo4j connection failed, but memory fallback is ACTIVE")
print("="*70 + "\n")
