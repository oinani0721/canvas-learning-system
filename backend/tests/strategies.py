"""Hypothesis strategies for Canvas Learning System domain types.

Reusable strategies for property-based testing of mastery, FSRS,
BKT, and canvas-related domain models.
"""

from hypothesis import strategies as st

# Mastery/proficiency scores: always 0.0-1.0
mastery_scores = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)

# Canvas node IDs: hex strings like those in Obsidian
node_ids = st.from_regex(r"[a-f0-9]{16}", fullmatch=True)

# Obsidian color codes: "1" through "6"
color_codes = st.sampled_from(["1", "2", "3", "4", "5", "6"])

# Canvas paths
canvas_paths = st.from_regex(r"[a-zA-Z0-9_]{1,50}\.canvas", fullmatch=True)

# FSRS ratings: 1-4 (Again, Hard, Good, Easy)
fsrs_ratings = st.integers(min_value=1, max_value=4)

# BKT difficulty levels
bkt_difficulties = st.sampled_from(["easy", "medium", "hard"])
