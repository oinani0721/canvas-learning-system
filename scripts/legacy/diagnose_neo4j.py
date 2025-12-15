#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose Neo4j connection issues
"""
import socket
import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("[DIAGNOSTIC] Neo4j Connection Troubleshooting")
print("="*70)

# Test 1: Check if port 7687 is open
print("\n[TEST 1] Checking if port 7687 is accessible")
print("-" * 70)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(3)

result = sock.connect_ex(('localhost', 7687))

if result == 0:
    print("[PASS] Port 7687 is OPEN and listening")
    print("       Neo4j service appears to be running")
else:
    print("[FAIL] Port 7687 is CLOSED or not responding")
    print("       Possible causes:")
    print("       1. Neo4j service is not running")
    print("       2. Firewall is blocking the port")
    print("       3. Neo4j is configured to use a different port")

sock.close()

# Test 2: Try Neo4j connection
print("\n[TEST 2] Attempting Neo4j authentication")
print("-" * 70)

try:
    from neo4j import GraphDatabase

    print("Step 1: Creating driver...")
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "707188Fx")
    )

    print("Step 2: Testing connection...")
    with driver.session() as session:
        result = session.run("RETURN 1 as num")
        for record in result:
            print(f"[PASS] SUCCESS! Neo4j responded: {record}")
            print("       Database is fully operational")
            driver.close()
            sys.exit(0)

except ConnectionError as e:
    print(f"[FAIL] Connection Error: {str(e)[:100]}")
    print("       The driver exists but cannot connect")
    print("       Make sure Neo4j is running on localhost:7687")

except Exception as e:
    print(f"[FAIL] Error: {type(e).__name__}: {str(e)[:100]}")
    print("       This could be authentication or configuration issue")

print("\n" + "="*70)
print("[NEXT STEPS]")
print("="*70)
print("""
If port 7687 is CLOSED:
  1. Open Neo4j Desktop
  2. Find "Canvas Learning System" project
  3. Expand "Databases (2)" section
  4. Click [Start] button on the database instance
  5. Wait for status to become RUNNING (green circle)
  6. Re-run this diagnostic script

If port 7687 is OPEN but authentication fails:
  1. Verify username is "neo4j"
  2. Verify password is "707188Fx"
  3. Try logging in with Neo4j Browser: http://localhost:7474
  4. If login works in browser, the issue may be with the driver

ACTION REQUIRED:
  Please take a screenshot of Neo4j Desktop showing:
  - "Canvas Learning System" project
  - Expanded "Databases (2)" section
  - All database instances and their statuses
  - Send screenshot to continue troubleshooting
""")
print("="*70 + "\n")
