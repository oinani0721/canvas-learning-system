#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime, timedelta

def test_sqlite():
    db_path = "C:\\Users\\ROG\\托福\\data\\review_data.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=== SQLite Database Test ===")

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables found: {[t[0] for t in tables]}")

        # Check existing data
        for table in ['review_schedules', 'review_history', 'user_review_stats']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count} records")

        # Create test schedule
        today = datetime.now().date()
        next_review = today + timedelta(days=1)

        cursor.execute("""
            INSERT OR REPLACE INTO review_schedules
            (schedule_id, user_id, canvas_file, node_id, concept_name,
             current_mastery_level, memory_strength, review_interval_days,
             next_review_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test-schedule-001',
            'default',
            'CS70 Lecture1.canvas',
            'node-logic-001',
            'Propositional Logic',
            0.6,
            8.5,
            3,
            next_review.isoformat(),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        # Create test history
        cursor.execute("""
            INSERT OR REPLACE INTO review_history
            (history_id, schedule_id, review_date, review_duration_minutes,
             user_rating, accuracy_score, previous_mastery, new_mastery)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test-history-001',
            'test-schedule-001',
            datetime.now().isoformat(),
            25,
            8,
            0.85,
            0.5,
            0.65
        ))

        # Create test stats
        cursor.execute("""
            INSERT OR REPLACE INTO user_review_stats
            (user_id, total_reviews, successful_reviews, total_concepts,
             mastered_concepts, average_rating, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'default',
            15,
            12,
            8,
            3,
            7.8,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        conn.commit()

        # Verify data
        cursor.execute("SELECT COUNT(*) FROM review_schedules")
        schedules_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM review_history")
        history_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM user_review_stats")
        stats_count = cursor.fetchone()[0]

        print(f"Test results:")
        print(f"  Schedules: {schedules_count}")
        print(f"  History: {history_count}")
        print(f"  Stats: {stats_count}")

        # Test query for today's reviews
        cursor.execute("""
            SELECT concept_name, memory_strength, next_review_date
            FROM review_schedules
            WHERE user_id = 'default'
            ORDER BY memory_strength ASC
        """)

        reviews = cursor.fetchall()
        print(f"Upcoming reviews:")
        for review in reviews:
            print(f"  - {review[0]} (strength: {review[1]}, next: {review[2][:10]})")

        conn.close()
        print("SQLite test PASSED!")
        return True

    except Exception as e:
        print(f"SQLite test FAILED: {e}")
        return False

if __name__ == "__main__":
    test_sqlite()