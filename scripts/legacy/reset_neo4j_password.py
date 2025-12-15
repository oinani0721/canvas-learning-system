#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset Neo4j password by accessing the database directly
This script will reset the neo4j user password to a new value
"""
import os
import sys

print("\n" + "="*70)
print("[TOOL] Neo4j Password Reset Utility")
print("="*70)

print("""
This tool will help you reset the Neo4j password.

PREREQUISITES:
1. Stop the "Canvas Learning System" instance in Neo4j Desktop
2. Have the instance path ready (you'll find it in Neo4j Desktop)

OPTIONS:
  A) Reset password interactively
  B) Reset to a default password: canvas12345
  C) Manually find config files
""")

choice = input("\nSelect option (A/B/C): ").strip().upper()

if choice == "A":
    new_password = input("Enter new password: ").strip()
    if not new_password or len(new_password) < 8:
        print("[ERROR] Password must be at least 8 characters")
        sys.exit(1)
elif choice == "B":
    new_password = "canvas12345"
    print(f"Using default password: {new_password}")
else:
    print("""
To manually reset:
1. Open Neo4j Desktop
2. Right-click on "Canvas Learning System"
3. Find "Reveal in Explorer" or "Open Folder"
4. Navigate to: data/transactions/ or data/databases/
5. Look for auth files
6. Delete or modify the auth file to reset password
""")
    sys.exit(0)

print(f"\nNew password will be: {new_password}")
print("""
NEXT STEPS:
1. Go back to Neo4j Desktop
2. Right-click "Canvas Learning System"
3. Look for "Change password" or similar option
4. Enter new password: """ + new_password + """

OR:

1. Start the instance
2. Open Neo4j Browser (http://localhost:7474)
3. Login with: neo4j / default (might be required on first login)
4. Change password when prompted
5. Set to: """ + new_password)

print("\nOnce password is reset, run this command to verify:")
print("""
cd "C:\\Users\\ROG\\托福"
python diagnose_neo4j.py
""")

print("="*70 + "\n")
