#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\ROG\托福\graphiti\mcp_server')

from neo4j_mcp_server import Neo4jMemoryStore

store = Neo4jMemoryStore()

# Add relationships
store.add_relationship("Math53-Lecture5", "Level-Set-Concepts", "contains_struggling_topic")
store.add_relationship("Math53-Lecture5", "Partial-Derivatives", "contains_mastered_topic")
store.add_relationship("Level-Set-Concepts", "Partial-Derivatives", "prerequisite_for")

# Export
export_data = store.export_memories()

print(f"Export data keys: {export_data.keys()}")
print(f"Relationships count: {len(export_data.get('relationships', []))}")
print(f"Relationships: {export_data.get('relationships', [])}")
print(f"Type of relationships: {type(export_data['relationships'])}")
print(f"Check: len(export_data['relationships']) == 3: {len(export_data['relationships']) == 3}")
