#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\ROG\托福\graphiti\mcp_server')

from neo4j_mcp_server import Neo4jMemoryStore

store = Neo4jMemoryStore()

# Test sequence exactly like test_neo4j_fix.py
result1 = store.add_relationship("Math53-Lecture5", "Level-Set-Concepts", "contains_struggling_topic")
result2 = store.add_relationship("Math53-Lecture5", "Partial-Derivatives", "contains_mastered_topic")
result3 = store.add_relationship("Level-Set-Concepts", "Partial-Derivatives", "prerequisite_for")

export_data = store.export_memories()
rel_count = len(export_data['relationships'])
test2_pass = rel_count == 3

print(f"Relationships exported: {rel_count}")
print(f"Test 2 result: {test2_pass}")
print(f"Export relationships list: {export_data['relationships']}")
