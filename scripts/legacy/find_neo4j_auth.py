#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find Neo4j authentication file and provide reset options
"""
import os
import glob
from pathlib import Path

print("\n" + "="*70)
print("[DIAGNOSTIC] Finding Neo4j Authentication Files")
print("="*70)

# Common Neo4j Desktop paths
possible_paths = [
    r"C:\Users\ROG\AppData\Local\Programs\neo4j-desktop\resources\app\dist\data",
    r"C:\Users\ROG\AppData\Local\Neo4j",
    r"C:\Users\ROG\.neo4j",
    r"C:\Users\ROG\AppData\Local\neo4j",
]

print("\n[SEARCH] Looking for Neo4j data directories...\n")

found_paths = []
for path in possible_paths:
    if os.path.exists(path):
        print(f"[FOUND] {path}")
        found_paths.append(path)

        # Look for specific files
        for root, dirs, files in os.walk(path):
            for file in files:
                if "auth" in file.lower() or "password" in file.lower():
                    full_path = os.path.join(root, file)
                    print(f"  ├─ Auth file: {full_path}")
                if file.endswith(".conf") or file.endswith(".config"):
                    full_path = os.path.join(root, file)
                    print(f"  ├─ Config file: {full_path}")

# Also search for instance folder paths
print("\n[SEARCH] Looking for instance-specific paths...\n")
instance_base = r"C:\Users\ROG\AppData\Local\neo4j-desktop\profiles\project_2025109\dbms"
if os.path.exists(instance_base):
    print(f"[FOUND] {instance_base}")
    for item in os.listdir(instance_base):
        item_path = os.path.join(instance_base, item)
        if os.path.isdir(item_path):
            print(f"  ├─ {item}")
            # Look for data directories
            for subitem in os.listdir(item_path):
                subpath = os.path.join(item_path, subitem)
                if os.path.isdir(subpath) and "data" in subpath.lower():
                    print(f"      ├─ {subpath}")

print("\n" + "="*70)
print("[SOLUTION] Password Reset Methods")
print("="*70)

print("""
METHOD 1: Via Neo4j Browser (Recommended)
────────────────────────────────────────
1. In Neo4j Desktop, click [Start] on "Canvas Learning System"
2. Wait for status to become RUNNING
3. Click [Open] in the instance card (or go to http://localhost:7474)
4. You may need to set initial password on first login
5. Use Neo4j Browser's UI to change password
6. New password: canvas12345

METHOD 2: Via Terminal (Advanced)
──────────────────────────────────
If you have Neo4j command line tools installed:
  neo4j-admin dbms set-initial-password canvas12345

METHOD 3: Direct File Modification (If others fail)
────────────────────────────────────────────────────
1. Stop the instance completely
2. Delete the auth file (usually in data/dbms/auth or similar)
3. Start instance again - it will prompt for initial password
4. Set new password: canvas12345

METHOD 4: Docker/Command Line (If installed)
──────────────────────────────────────────────
  docker run -it neo4j-enterprise:latest neo4j-admin help

NOTE: Neo4j Desktop uses embedded instances, not Docker by default.
""")

print("\n" + "="*70)
print("[NEXT STEP]")
print("="*70)
print("""
1. Make sure Neo4j instance is RUNNING
2. Open: http://localhost:7474 in your browser
3. You should see Neo4j Browser login page
4. Try logging in with different credentials to find what works
5. Once in, change password to: canvas12345

After changing password, update this file:
  C:\\Users\\ROG\\托福\\graphiti\\mcp_server\\neo4j_mcp_server.py

Change line 39:
  password = os.getenv("NEO4J_PASSWORD", "canvas12345")
""")
print("="*70 + "\n")
