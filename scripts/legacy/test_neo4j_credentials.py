#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Neo4j credentials directly
"""
import sys
sys.path.insert(0, r'C:\Users\ROG\托福\graphiti\mcp_server')

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("neo4j.test")

print("\n" + "="*70)
print("[TEST] Neo4j Credentials Verification")
print("="*70)

# Test different password combinations
passwords_to_test = [
    "707188Fx",      # Original password
    "password",      # Default
    "",              # Empty
]

for password in passwords_to_test:
    print(f"\n[TEST] Trying password: '{password}'")
    print("-" * 70)

    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", password),
            connection_acquisition_timeout=5
        )

        with driver.session() as session:
            result = session.run("RETURN 1")
            print(f"[SUCCESS] Password '{password}' works!")
            print(f"Response: {result.single()}")
            driver.close()
            sys.exit(0)

    except Exception as e:
        print(f"[FAILED] Error: {type(e).__name__}")
        print(f"Message: {str(e)[:100]}")
        driver.close()

print("\n" + "="*70)
print("[ACTION REQUIRED]")
print("="*70)
print("""
No passwords worked. This could mean:

1. The password was changed during Neo4j setup
2. The Neo4j instance needs to be restarted
3. The database file is corrupted

NEXT STEPS:
1. Open Neo4j Desktop
2. Right-click on "Canvas Learning System"
3. Look for "Reset password" or similar option
4. Set a new password (recommend: canvas123)
5. Update start_neo4j_mcp.bat with the new password
6. Restart the database instance
7. Try running this script again
""")
print("="*70 + "\n")
