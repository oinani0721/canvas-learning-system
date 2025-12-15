#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep diagnostic for Neo4j startup issues
"""
import socket
import subprocess
import sys
import os

print("\n" + "="*70)
print("[DEEP DIAGNOSTIC] Neo4j Service Status Check")
print("="*70)

# Test 1: Check port 7474 (Neo4j Browser)
print("\n[TEST 1] Checking Neo4j Browser port (7474)")
print("-" * 70)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(3)
result = sock.connect_ex(('localhost', 7474))

if result == 0:
    print("[PASS] Port 7474 is OPEN - Neo4j Browser should be accessible")
    print("       Try: http://localhost:7474")
else:
    print("[FAIL] Port 7474 is CLOSED - Neo4j Browser is not listening")
    print("       This means the Neo4j service is NOT running properly")

sock.close()

# Test 2: Check port 7687 (Bolt)
print("\n[TEST 2] Checking Neo4j Bolt port (7687)")
print("-" * 70)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(3)
result = sock.connect_ex(('localhost', 7687))

if result == 0:
    print("[PASS] Port 7687 is OPEN - Neo4j database is listening")
else:
    print("[FAIL] Port 7687 is CLOSED - Neo4j database is not listening")

sock.close()

# Test 3: Check for Neo4j processes
print("\n[TEST 3] Checking for running Neo4j processes")
print("-" * 70)

try:
    result = subprocess.run(
        'tasklist | findstr /i neo4j',
        shell=True,
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.stdout:
        print("[FOUND] Neo4j processes:")
        print(result.stdout)
    else:
        print("[NONE] No Neo4j processes found in task list")
        print("       This suggests the service is NOT running")
except Exception as e:
    print(f"[ERROR] Could not check processes: {e}")

# Test 4: Check Java processes (Neo4j uses Java)
print("\n[TEST 4] Checking for Java processes (Neo4j runs on Java)")
print("-" * 70)

try:
    result = subprocess.run(
        'tasklist | findstr /i java',
        shell=True,
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.stdout:
        print("[FOUND] Java processes:")
        print(result.stdout)
    else:
        print("[NONE] No Java processes found")
except Exception as e:
    print(f"[ERROR] Could not check Java processes: {e}")

# Test 5: Try to find Neo4j installation
print("\n[TEST 5] Looking for Neo4j Desktop installation")
print("-" * 70)

possible_paths = [
    r"C:\Users\ROG\AppData\Local\Programs\neo4j-desktop",
    r"C:\Program Files\Neo4j",
    r"C:\Program Files (x86)\Neo4j",
]

found = False
for path in possible_paths:
    if os.path.exists(path):
        print(f"[FOUND] Neo4j Desktop at: {path}")
        found = True

        # Try to find the database instance folder
        dbms_path = os.path.join(path, "resources", "app", "dist", "neo4j-dbms")
        if os.path.exists(dbms_path):
            print(f"[FOUND] DBMS folder: {dbms_path}")

if not found:
    print("[INFO] Neo4j Desktop installation not found in common locations")

# Test 6: Check Neo4j logs
print("\n[TEST 6] Looking for Neo4j logs")
print("-" * 70)

log_paths = [
    r"C:\Users\ROG\AppData\Local\neo4j-desktop",
    r"C:\Users\ROG\.neo4j",
]

for base_path in log_paths:
    if os.path.exists(base_path):
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".log") or "debug" in file.lower():
                    full_path = os.path.join(root, file)
                    print(f"[FOUND] Log file: {full_path}")

print("\n" + "="*70)
print("[DIAGNOSIS SUMMARY]")
print("="*70)

print("""
If you see:
✅ Port 7474 OPEN → Neo4j Browser should work (try http://localhost:7474)
✅ Port 7687 OPEN → Database is responding
❌ Port 7474 CLOSED → Service is not running properly
❌ No Java processes → Neo4j is definitely not running

LIKELY PROBLEMS:
1. Neo4j instance failed to start
   → Check Neo4j Desktop for error messages
   → Try clicking [Stop] then [Start] again

2. Instance is corrupted
   → Delete instance and recreate it
   → Or reset database state

3. System resources exhausted
   → Restart Neo4j Desktop
   → Restart your computer

NEXT ACTIONS:
A) Go back to Neo4j Desktop
B) Right-click on "Canvas Learning System"
C) Look at the status and any error messages
D) Try [Stop] then [Start] again
E) Wait 1-2 minutes for it to fully start
F) Check if http://localhost:7474 is accessible now
""")

print("="*70 + "\n")
