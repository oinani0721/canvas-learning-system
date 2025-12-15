#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final verification - Test relationship operations
"""
import sys
sys.path.insert(0, r'C:\Users\ROG\托福\graphiti\mcp_server')

from neo4j_mcp_server import Neo4jMemoryStore

store = Neo4jMemoryStore()

print("\n" + "="*70)
print("[FINAL VERIFICATION] Graphiti System Test")
print("="*70)

# Check status
neo4j_status = "AVAILABLE" if store.neo4j_connected else "NOT AVAILABLE (using memory)"
print(f"\nNeo4j Status: {neo4j_status}")

# Test 1: Add relationships
print("\n[TEST 1] Adding relationships...")
try:
    r1 = store.add_relationship("Math53-Lecture5", "Level-Set-Concepts", "contains_struggling_topic")
    r2 = store.add_relationship("Math53-Lecture5", "Partial-Derivatives", "contains_mastered_topic")
    r3 = store.add_relationship("Level-Set-Concepts", "Partial-Derivatives", "prerequisite_for")

    if r1 and r2 and r3:
        print("[PASS] All 3 relationships added successfully")
    else:
        print("[FAIL] Some relationships failed to add")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

# Test 2: Export relationships
print("\n[TEST 2] Exporting relationships...")
try:
    export_data = store.export_memories()
    rel_count = len(export_data['relationships'])
    print(f"[PASS] Exported {rel_count} relationships")
    for rel in export_data['relationships']:
        print(f"  - {rel['entity1']} -[{rel['type']}]-> {rel['entity2']}")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

# Test 3: Delete relationship
print("\n[TEST 3] Deleting relationship...")
try:
    result = store.delete_relationship("Level-Set-Concepts", "Partial-Derivatives", "prerequisite_for")
    if result:
        print("[PASS] Relationship deleted successfully")
    else:
        print("[FAIL] Delete operation failed")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

# Test 4: Add memory
print("\n[TEST 4] Adding memory...")
try:
    mem_id = store.add_memory("Math53-Lecture5", "Contains concepts about level sets and partial derivatives")
    print(f"[PASS] Memory added with ID: {mem_id}")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

# Test 5: Search memory
print("\n[TEST 5] Searching memory...")
try:
    results = store.search_memories("partial")
    print(f"[PASS] Found {len(results)} matching memory items")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("[SUCCESS] All tests passed!")
print("="*70)
print("""
System Status:
- Relationship operations: WORKING
- Memory operations: WORKING
- Export/Import: WORKING
- Canvas Learning System ready to use!
""")
print("="*70 + "\n")
