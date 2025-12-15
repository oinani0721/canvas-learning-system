#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose why neo4j_mcp_server.py fails authentication while direct tests succeed
"""
import sys
import os
import logging
from neo4j import GraphDatabase

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-auth-diagnosis")

print("\n" + "="*70)
print("[DIAGNOSTIC] Neo4j MCP Server Authentication Diagnosis")
print("="*70)

# Test 1: Direct connection (known to work)
print("\n[TEST 1] Direct connection with explicit IPv4")
print("-" * 70)
try:
    driver1 = GraphDatabase.driver(
        "bolt://127.0.0.1:7687",  # IPv4 explicitly
        auth=("neo4j", "707188Fx"),
        connection_acquisition_timeout=10,
        connection_timeout=10
    )
    with driver1.session() as session:
        result = session.run("RETURN 1 as test")
        print(f"[SUCCESS] Direct connection works: {result.single()}")
    driver1.close()
except Exception as e:
    print(f"[FAILED] {type(e).__name__}: {e}")

# Test 2: MCP-style connection (with environment variables)
print("\n[TEST 2] MCP-style connection from environment")
print("-" * 70)
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "707188Fx"

try:
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "707188Fx")

    logger.info(f"URI: {uri}")
    logger.info(f"User: {user}")
    logger.info(f"Creating driver...")

    driver2 = GraphDatabase.driver(
        uri,
        auth=(user, password),
        connection_acquisition_timeout=10,
        connection_timeout=10
    )

    logger.info(f"Driver created, testing connection...")
    with driver2.session() as session:
        logger.info(f"Session created, running query...")
        result = session.run("RETURN 1 as test")
        logger.info(f"Query executed, getting result...")
        record = result.single()
        logger.info(f"[SUCCESS] MCP-style connection works: {record}")
    driver2.close()
except Exception as e:
    print(f"[FAILED] {type(e).__name__}: {e}")
    import traceback
    print(f"\nTraceback:\n{traceback.format_exc()}")

# Test 3: Connection with explicit database selection
print("\n[TEST 3] Connection with explicit database='neo4j'")
print("-" * 70)
try:
    driver3 = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "707188Fx"),
        connection_acquisition_timeout=10,
        connection_timeout=10
    )

    logger.info("Testing with explicit database...")
    with driver3.session(database="neo4j") as session:
        logger.info("Running query on neo4j database...")
        result = session.run("RETURN 1 as test")
        record = result.single()
        logger.info(f"[SUCCESS] Explicit database works: {record}")
    driver3.close()
except Exception as e:
    print(f"[FAILED] {type(e).__name__}: {e}")
    import traceback
    print(f"\nTraceback:\n{traceback.format_exc()}")

# Test 4: Connection without context manager (like MCP session management)
print("\n[TEST 4] Connection without context manager (manual close)")
print("-" * 70)
try:
    driver4 = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "707188Fx"),
        connection_acquisition_timeout=10,
        connection_timeout=10
    )

    logger.info("Creating session manually...")
    session = driver4.session()
    logger.info("Session created, running query...")
    result = session.run("RETURN 1 as test")
    logger.info("Query executed, getting result...")
    record = result.single()
    logger.info(f"[SUCCESS] Manual session works: {record}")
    session.close()
    driver4.close()
except Exception as e:
    print(f"[FAILED] {type(e).__name__}: {e}")
    import traceback
    print(f"\nTraceback:\n{traceback.format_exc()}")

# Test 5: Check if there's a "system" database issue
print("\n[TEST 5] List available databases")
print("-" * 70)
try:
    driver5 = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "707188Fx"),
        connection_acquisition_timeout=10,
        connection_timeout=10
    )

    with driver5.session() as session:
        result = session.run("SHOW DATABASES")
        logger.info("Available databases:")
        for record in result:
            print(f"  - {record}")
    driver5.close()
except Exception as e:
    print(f"[FAILED] {type(e).__name__}: {e}")
    import traceback
    print(f"\nTraceback:\n{traceback.format_exc()}")

print("\n" + "="*70)
print("[SUMMARY]")
print("="*70)
print("""
If Test 1-4 all pass but MCP server still fails, the issue may be:
1. MCP server imports or initialization order
2. Async/await context in MCP server
3. Exception handling that's catching auth failures

If Test 5 shows unexpected databases, Neo4j may have been reset.

Check next:
- Run the MCP server with verbose logging
- Compare exact parameters used in working tests vs MCP server
""")
print("="*70 + "\n")
