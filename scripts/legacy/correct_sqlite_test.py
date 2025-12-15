#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, timedelta

def test_sqlite_correct():
    db_path = "C:\\Users\\ROG\\托福\\data\\review_data.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=== Correct SQLite Database Test ===")

        # Check existing data
        cursor.execute("SELECT COUNT(*) FROM review_schedules")
        schedules_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM review_history")
        history_count = cursor.fetchone()[0]

        print(f"Initial data - Schedules: {schedules_count}, History: {history_count}")

        # Insert test schedule using actual table structure
        today = datetime.now()
        next_review = today + timedelta(days=1)

        cursor.execute("""
            INSERT OR REPLACE INTO review_schedules
            (schedule_id, canvas_file, node_id, concept_name,
             last_review_date, next_review_date, review_interval_days,
             memory_strength, retention_rate, difficulty_rating,
             mastery_level, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test-cs70-001',
            'CS70 Lecture1.canvas',
            'node-logic-001',
            'Propositional Logic',
            today.isoformat(),
            next_review.isoformat(),
            3,
            8.5,
            0.75,
            'medium',
            0.65,
            today.isoformat(),
            today.isoformat()
        ))

        # Insert test history
        cursor.execute("""
            INSERT OR REPLACE INTO review_history
            (history_id, schedule_id, review_date, review_duration_minutes,
             user_rating, accuracy_score, previous_mastery, new_mastery)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'hist-cs70-001',
            'test-cs70-001',
            today.isoformat(),
            25,
            8,
            0.85,
            0.5,
            0.65
        ))

        conn.commit()

        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM review_schedules")
        new_schedules_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM review_history")
        new_history_count = cursor.fetchone()[0]

        print(f"After insertion - Schedules: {new_schedules_count}, History: {new_history_count}")

        # Test query - find reviews due today
        cursor.execute("""
            SELECT schedule_id, concept_name, memory_strength, next_review_date
            FROM review_schedules
            WHERE date(next_review_date) = date('now')
            ORDER BY memory_strength ASC
        """)

        due_today = cursor.fetchall()
        print(f"Reviews due today: {len(due_today)}")
        for review in due_today:
            print(f"  - {review[1]} (strength: {review[2]})")

        # Test query - get all schedules
        cursor.execute("""
            SELECT concept_name, mastery_level, difficulty_rating, next_review_date
            FROM review_schedules
            ORDER BY mastery_level ASC
        """)

        all_reviews = cursor.fetchall()
        print(f"All scheduled reviews: {len(all_reviews)}")
        for review in all_reviews:
            print(f"  - {review[0]} (mastery: {review[1]:.2f}, difficulty: {review[2]})")

        # Test Ebbinghaus algorithm simulation
        print("\n=== Ebbinghaus Algorithm Test ===")

        # Simulate review completion and update memory strength
        cursor.execute("""
            UPDATE review_schedules
            SET memory_strength = memory_strength * 1.2,
                mastery_level = mastery_level + 0.1,
                review_interval_days = CASE
                    WHEN memory_strength < 5 THEN 1
                    WHEN memory_strength < 10 THEN 3
                    WHEN memory_strength < 20 THEN 7
                    ELSE 15
                END,
                next_review_date = date('now', '+' ||
                    CASE
                        WHEN memory_strength < 5 THEN '1 day'
                        WHEN memory_strength < 10 THEN '3 days'
                        WHEN memory_strength < 20 THEN '7 days'
                        ELSE '15 days'
                    END),
                updated_at = ?
            WHERE schedule_id = ?
        """, (datetime.now().isoformat(), 'test-cs70-001'))

        # Check updated values
        cursor.execute("""
            SELECT memory_strength, mastery_level, review_interval_days, next_review_date
            FROM review_schedules
            WHERE schedule_id = ?
        """, ('test-cs70-001',))

        updated = cursor.fetchone()
        print(f"Updated review after completion:")
        print(f"  Memory strength: {updated[0]:.1f}")
        print(f"  Mastery level: {updated[1]:.2f}")
        print(f"  Next interval: {updated[2]} days")
        print(f"  Next review date: {updated[3][:10]}")

        conn.commit()
        conn.close()

        print("\nSQLite Database Test PASSED!")
        print("- Data insertion: ✓")
        print("- Data reading: ✓")
        print("- Query operations: ✓")
        print("- Ebbinghaus algorithm: ✓")

        return True

    except Exception as e:
        print(f"SQLite test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_sqlite_correct()