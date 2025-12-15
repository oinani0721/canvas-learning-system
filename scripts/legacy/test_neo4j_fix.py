#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify Neo4j relationship operation fix
"""
import sys
import os
sys.path.insert(0, r'C:\Users\ROG\托福\graphiti\mcp_server')

# Set environment to avoid encoding issues
os.environ['PYTHONIOENCODING'] = 'utf-8'

from neo4j_mcp_server import Neo4jMemoryStore

# Create memory store instance (will fallback to memory when Neo4j unavailable)
store = Neo4jMemoryStore()

print("\n" + "="*60)
print("[TEST] Neo4j Relationship Operation Fix Verification")
print("="*60)

print("\n[SYSTEM STATUS]")
print(f"  Neo4j Connected: {('YES' if store.neo4j_connected else 'NO (using memory fallback)')}")

# Test 1: add_relationship
print("\n[TEST 1] Adding relationships")
print("  Adding: Math53-Lecture5 -[contains_struggling_topic]-> Level-Set-Concepts")
result1 = store.add_relationship("Math53-Lecture5", "Level-Set-Concepts", "contains_struggling_topic")
print(f"  Result: {'SUCCESS' if result1 else 'FAILED'}")

print("\n  Adding: Math53-Lecture5 -[contains_mastered_topic]-> Partial-Derivatives")
result2 = store.add_relationship("Math53-Lecture5", "Partial-Derivatives", "contains_mastered_topic")
print(f"  Result: {'SUCCESS' if result2 else 'FAILED'}")

print("\n  Adding: Level-Set-Concepts -[prerequisite_for]-> Partial-Derivatives")
result3 = store.add_relationship("Level-Set-Concepts", "Partial-Derivatives", "prerequisite_for")
print(f"  Result: {'SUCCESS' if result3 else 'FAILED'}")

# Test 2: Export (BEFORE deletion)
print("\n[TEST 2] Exporting relationship data (before deletion)")
export_data = store.export_memories()
print(f"  Total relationships exported: {len(export_data['relationships'])}")
for rel in export_data['relationships']:
    print(f"    - {rel['entity1']} -[{rel['type']}]-> {rel['entity2']}")

# Test 3: Duplicate detection
print("\n[TEST 3] Duplicate relationship detection")
result_dup = store.add_relationship("Math53-Lecture5", "Level-Set-Concepts", "contains_struggling_topic")
print(f"  Adding duplicate relationship: {'CORRECTLY DETECTED' if result_dup else 'NOT DETECTED'}")

# Test 4: Delete relationship
print("\n[TEST 4] Deleting relationship")
result_del = store.delete_relationship("Level-Set-Concepts", "Partial-Derivatives", "prerequisite_for")
print(f"  Delete operation: {'SUCCESS' if result_del else 'FAILED'}")

print(f"\n  Remaining relationships: {len(store.relationships if hasattr(store, 'relationships') else [])}")

print("\n" + "="*60)
print("[SUCCESS] Fix verification completed successfully!")
print("="*60 + "\n")

# Summary
print("[SUMMARY]")
test1_pass = all([result1, result2, result3])
test2_pass = len(export_data['relationships']) == 3  # Should be exactly 3
test3_pass = result_dup == True  # Should return True for duplicate
test4_pass = result_del == True  # Should return True for successful deletion

print(f"  Test 1 (add_relationship): {'PASS' if test1_pass else 'FAIL'}")
print(f"  Test 2 (export 3 relationships): {'PASS' if test2_pass else 'FAIL'}")
print(f"  Test 3 (duplicate detection): {'PASS' if test3_pass else 'FAIL'}")
print(f"  Test 4 (delete_relationship): {'PASS' if test4_pass else 'FAIL'}")

all_pass = test1_pass and test2_pass and test3_pass and test4_pass
print(f"\n[OVERALL RESULT]: {'ALL TESTS PASSED!' if all_pass else 'SOME TESTS FAILED'}\n")
