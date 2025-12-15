#!/usr/bin/env python3
"""
Simple test to verify memory system storage
"""

import asyncio
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

from command_handlers.learning_commands import LearningSessionManager

async def test_storage():
    """Test if memory systems actually store data"""

    print("="*60)
    print("Testing Memory Storage - Simple Test")
    print("="*60)
    print()

    # Create test canvas
    test_canvas_path = "test_simple_canvas.canvas"
    test_canvas = {
        "nodes": [{"id": "test1", "type": "text", "text": "Test concept",
                   "x": 0, "y": 0, "width": 250, "height": 60, "color": "1"}],
        "edges": []
    }

    with open(test_canvas_path, 'w', encoding='utf-8') as f:
        json.dump(test_canvas, f, indent=2, ensure_ascii=False)

    print(f"[1] Test Canvas created: {test_canvas_path}")
    print()

    # Initialize manager
    manager = LearningSessionManager(session_dir=".learning_sessions")
    print("[2] LearningSessionManager initialized")
    print()

    # Start session
    print("[3] Starting session...")
    print("-"*60)

    try:
        result = await manager.start_session(
            canvas_path=test_canvas_path,
            user_id="test_user",
            session_name="Simple Test Session",
            allow_partial_start=True,
            interactive=False
        )

        print()
        print("[4] Session started successfully")
        print(f"    Session ID: {result['session_id']}")
        print(f"    Running systems: {result['running_systems']}/{result['total_systems']}")
        print()

        # Print memory system status
        print("[5] Memory System Status:")
        print("-"*60)
        for sys_name, sys_data in result['memory_systems'].items():
            print(f"  {sys_name.upper()}:")
            print(f"    Status: {sys_data.get('status')}")
            print(f"    Memory ID: {sys_data.get('memory_id', sys_data.get('session_id', 'N/A'))}")
            if 'error' in sys_data:
                print(f"    Error: {sys_data['error']}")
            print()

        # Verify Graphiti storage
        print("[6] Verifying Graphiti Storage...")
        print("-"*60)
        try:
            from claude_tools import mcp__graphiti_memory__list_memories
            memories = await mcp__graphiti_memory__list_memories()
            print(f"  Total memories in Graphiti: {len(memories) if isinstance(memories, list) else 0}")
            if memories and len(memories) > 0:
                print(f"  Latest memory: {memories[0] if isinstance(memories, list) else memories}")
            else:
                print("  NO MEMORIES STORED IN GRAPHITI!")
        except Exception as e:
            print(f"  Error querying Graphiti: {e}")
        print()

        # Verify Temporal storage
        print("[7] Verifying Temporal Storage...")
        print("-"*60)
        db_path = Path("data/memory_local.db")
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory_records WHERE session_id LIKE ?",
                          (f"%{result['session_id']}%",))
            count = cursor.fetchone()[0]
            print(f"  Records in memory_local.db: {count}")
            if count == 0:
                print("  NO RECORDS STORED IN TEMPORAL DB!")
            conn.close()
        else:
            print(f"  Database not found: {db_path}")
        print()

        # Verify Semantic storage
        print("[8] Verifying Semantic Storage...")
        print("-"*60)
        semantic_db = Path(".semantic_cache.db")
        if semantic_db.exists():
            conn = sqlite3.connect(str(semantic_db))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM semantic_memories
                WHERE content LIKE ? OR metadata LIKE ?
            """, (f"%{result['session_id']}%", f"%{result['session_id']}%"))
            count = cursor.fetchone()[0]
            print(f"  Records in semantic_cache.db: {count}")
            if count == 0:
                print("  NO RECORDS STORED IN SEMANTIC DB!")
            conn.close()
        else:
            print(f"  Database not found: {semantic_db}")
        print()

        print("="*60)
        print("Test Complete")
        print("="*60)

        return result

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_storage())
    if result:
        print("\nTest completed successfully")
    else:
        print("\nTest failed")
        sys.exit(1)
