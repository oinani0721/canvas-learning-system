#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Neo4jMemoryStore directly
"""
import sys
sys.path.insert(0, r'C:\Users\ROG\托福\graphiti\mcp_server')

print("\n" + "="*70)
print("[TEST] Neo4jMemoryStore Direct Test")
print("="*70)

# Import after path is set
from neo4j_mcp_server import Neo4jMemoryStore

print("\n[STEP 1] Creating Neo4jMemoryStore instance...")
try:
    store = Neo4jMemoryStore()
    print(f"[SUCCESS] Store created")
    print(f"  neo4j_connected: {store.neo4j_connected}")
except Exception as e:
    print(f"[FAIL] Error creating store: {e}")
    sys.exit(1)

# Check if connected
if store.neo4j_connected:
    print("\n[SUCCESS] Neo4j is CONNECTED!")
    print("  All relationship operations will use Neo4j")
else:
    print("\n[INFO] Neo4j connection failed, using memory fallback")
    print("  All relationship operations will use memory storage")

# Test add_relationship
print("\n[STEP 2] Testing add_relationship...")
try:
    r1 = store.add_relationship("Entity1", "Entity2", "RELATES_TO")
    print(f"[SUCCESS] Relationship added: {r1}")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

# Test export
print("\n[STEP 3] Testing export...")
try:
    export_data = store.export_memories()
    print(f"[SUCCESS] Export completed")
    print(f"  Relationships: {len(export_data['relationships'])}")
    print(f"  Memories: {len(export_data['memories'])}")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("[VERDICT]")
print("="*70)

if store.neo4j_connected:
    print("NEO4J CONNECTION: SUCCESS")
    print("System is using Neo4j database")
else:
    print("NEO4J CONNECTION: FAILED (using memory fallback)")
    print("System is using memory storage")
    print("\nTo fix: Check Neo4j credentials and connection")

print("="*70 + "\n")
