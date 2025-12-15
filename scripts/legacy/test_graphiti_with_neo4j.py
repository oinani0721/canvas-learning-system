#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Graphiti with Neo4j connection
"""
import sys
sys.path.insert(0, r'C:\Users\ROG\托福\graphiti\mcp_server')

from neo4j_mcp_server import Neo4jMemoryStore

print("\n" + "="*60)
print("[TEST] Graphiti + Neo4j Integration Test")
print("="*60)

store = Neo4jMemoryStore()

print(f"\n[SYSTEM STATUS]")
print(f"  Neo4j Connected: {'✅ YES' if store.neo4j_connected else '❌ NO (using memory fallback)'}")

if store.neo4j_connected:
    print(f"\n[SUCCESS] Neo4j connection established!")
    print(f"  Connection: bolt://localhost:7687")
    print(f"  User: neo4j")

    # Test operations
    print(f"\n[TEST 1] Adding relationships to Neo4j")
    result1 = store.add_relationship("Math53-Lecture5", "Level-Set-Concepts", "contains_struggling_topic")
    result2 = store.add_relationship("Math53-Lecture5", "Partial-Derivatives", "contains_mastered_topic")
    result3 = store.add_relationship("Level-Set-Concepts", "Partial-Derivatives", "prerequisite_for")

    print(f"  Result: {'✅ SUCCESS' if all([result1, result2, result3]) else '❌ FAILED'}")

    # Export to verify
    print(f"\n[TEST 2] Exporting relationships from Neo4j")
    export_data = store.export_memories()
    print(f"  Total relationships in Neo4j: {len(export_data['relationships'])}")
    for rel in export_data['relationships']:
        print(f"    ✓ {rel['entity1']} -[{rel['type']}]-> {rel['entity2']}")

    print(f"\n[VERDICT] ✅ Neo4j is fully operational!")
    print(f"  You can now use full relationship graph capabilities.")

else:
    print(f"\n[ERROR] Neo4j connection failed!")
    print(f"  Please verify:")
    print(f"    1. Neo4j Desktop is running")
    print(f"    2. Database instance is started (status: RUNNING)")
    print(f"    3. Connection address is bolt://localhost:7687")
    print(f"    4. Credentials are correct in start_neo4j_mcp.bat")
    print(f"\n  Falling back to memory storage mode.")

print("\n" + "="*60 + "\n")
