# ✅ Verified from Story 12.4 AC 2 - SQLite Schema
"""
SQLite Schema definitions for Temporal Memory.

Provides schema for:
- learning_behaviors: Time-series learning activity tracking
- fsrs_cards: FSRS spaced repetition card state storage
"""

# Learning behaviors table schema
BEHAVIOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS learning_behaviors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    canvas_file TEXT NOT NULL,
    concept TEXT NOT NULL,
    action_type TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,

    -- Indexes for common queries
    UNIQUE(session_id, canvas_file, concept, action_type, timestamp)
);

-- Index for querying by canvas file
CREATE INDEX IF NOT EXISTS idx_behavior_canvas
ON learning_behaviors(canvas_file);

-- Index for querying by concept
CREATE INDEX IF NOT EXISTS idx_behavior_concept
ON learning_behaviors(concept);

-- Index for querying by timestamp
CREATE INDEX IF NOT EXISTS idx_behavior_timestamp
ON learning_behaviors(timestamp);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_behavior_canvas_concept
ON learning_behaviors(canvas_file, concept);
"""

# FSRS cards table schema
FSRS_CARD_SCHEMA = """
CREATE TABLE IF NOT EXISTS fsrs_cards (
    concept TEXT PRIMARY KEY,
    canvas_file TEXT NOT NULL,
    difficulty REAL DEFAULT 0.0,
    stability REAL DEFAULT 0.0,
    due DATETIME,
    state INTEGER DEFAULT 0,
    last_review DATETIME,
    reps INTEGER DEFAULT 0,
    lapses INTEGER DEFAULT 0,
    card_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by canvas file
CREATE INDEX IF NOT EXISTS idx_fsrs_canvas
ON fsrs_cards(canvas_file);

-- Index for querying by stability (for weak concept ranking)
CREATE INDEX IF NOT EXISTS idx_fsrs_stability
ON fsrs_cards(stability);

-- Index for querying by due date
CREATE INDEX IF NOT EXISTS idx_fsrs_due
ON fsrs_cards(due);

-- Composite index for canvas + stability queries
CREATE INDEX IF NOT EXISTS idx_fsrs_canvas_stability
ON fsrs_cards(canvas_file, stability);
"""

# Error tracking table (optional, for monitoring)
ERROR_TRACKING_SCHEMA = """
CREATE TABLE IF NOT EXISTS concept_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept TEXT NOT NULL,
    canvas_file TEXT NOT NULL,
    error_count INTEGER DEFAULT 0,
    last_error DATETIME,
    error_rate REAL DEFAULT 0.0,

    UNIQUE(concept, canvas_file)
);

-- Index for error rate queries
CREATE INDEX IF NOT EXISTS idx_error_rate
ON concept_errors(error_rate DESC);
"""

# All schemas combined
ALL_SCHEMAS = [
    BEHAVIOR_SCHEMA,
    FSRS_CARD_SCHEMA,
    ERROR_TRACKING_SCHEMA,
]


def get_all_schemas() -> str:
    """Get all schema definitions as a single string."""
    return "\n".join(ALL_SCHEMAS)


def get_drop_statements() -> str:
    """Get DROP TABLE statements for all tables."""
    return """
    DROP TABLE IF EXISTS learning_behaviors;
    DROP TABLE IF EXISTS fsrs_cards;
    DROP TABLE IF EXISTS concept_errors;
    """
