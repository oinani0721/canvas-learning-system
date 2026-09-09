#!/usr/bin/env python3
"""Self-Improving Flywheel: Convert production errors to regression tests.

Reads bug_log.jsonl, failed_edge_syncs.jsonl, dead_letter_episodes.jsonl
and generates tests/regression/test_production_bugs.py.

Usage:
    python scripts/generate_regression_tests.py
    python scripts/generate_regression_tests.py --dry-run  # preview without writing
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = (
    Path(__file__).parent.parent / "tests" / "regression" / "test_production_bugs.py"
)


def read_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Read a JSONL file, return list of dicts."""
    if not file_path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def sanitize_func_name(raw: str, max_len: int = 60) -> str:
    """Turn an arbitrary string into a valid Python identifier fragment."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", raw).strip("_").lower()
    return cleaned[:max_len]


# Endpoints known to currently return 500 for certain error conditions.
# These are real bugs — the exception handler does not catch them yet.
# When the bug is fixed, remove the endpoint from this set so the test
# enforces the fix as a regression guard.
_KNOWN_500_ENDPOINTS: set[str] = {
    "/api/v1/canvas/nonexistent/sync-edges",
}


def generate_bug_test(bug: Dict[str, Any]) -> str:
    """Generate a test function from a bug_log entry.

    Each test hits the endpoint via TestClient and asserts the server
    does not crash with an unhandled 500.  The real production errors
    included CanvasNotFoundException, ValidationError, TypeError, etc.
    A well-behaved API should map those to 4xx, not 500.
    """
    bug_id = sanitize_func_name(bug.get("bug_id", "UNKNOWN"))
    endpoint = bug.get("endpoint", "/unknown")
    method = bug.get("request_params", {}).get("method", "GET").lower()
    error_type = bug.get("error_type", "Exception")
    error_msg = bug.get("error_message", "")[:120].replace('"', '\\"')
    timestamp = bug.get("timestamp", "unknown")[:19]

    # For POST endpoints we need a body; use an empty dict as minimum payload
    if method == "post":
        call_line = f'    response = client.post("{endpoint}", json={{}})'
    elif method == "put":
        call_line = f'    response = client.put("{endpoint}", json={{}})'
    elif method == "delete":
        call_line = f'    response = client.delete("{endpoint}")'
    else:
        call_line = f'    response = client.get("{endpoint}")'

    # Mark known-unfixed 500s as xfail so CI stays green while documenting the bug
    xfail_line = ""
    if endpoint in _KNOWN_500_ENDPOINTS:
        xfail_line = (
            f'@pytest.mark.xfail(reason="Known bug: {error_type} at '
            f'{endpoint} returns 500 instead of 4xx", strict=True)\n'
        )

    return f'''
{xfail_line}def test_bug_{bug_id}(client):
    """Regression: {error_type} at {endpoint}

    Original error: {error_msg}
    Recorded: {timestamp}
    """
{call_line}
    # The endpoint must return a structured error (4xx), never crash (500).
    assert response.status_code != 500, (
        f"Endpoint {endpoint} returned 500 — regression of {bug_id}: "
        f"{{response.text[:200]}}"
    )
'''


def generate_edge_sync_test(entry: Dict[str, Any]) -> str:
    """Generate a test from a failed edge sync entry."""
    edge_id = sanitize_func_name(entry.get("edge_id", "unknown"))
    canvas = entry.get("canvas_name", "unknown")
    error = entry.get("error", "")[:80].replace('"', '\\"')
    retry_count = entry.get("retry_count", 0)

    return f'''
def test_edge_sync_{edge_id}():
    """Regression: Edge sync failure for canvas '{canvas}'

    Error: {error}
    Retries exhausted: {retry_count}
    """
    # Documents a real Neo4j edge sync failure.
    # When Neo4j integration tests are enabled, verify the sync mechanism
    # handles this case gracefully (retry + dead-letter, no silent data loss).
    pytest.skip("Neo4j integration tests not yet enabled")
'''


def generate_dead_letter_test(entry: Dict[str, Any]) -> str:
    """Generate a test from a dead letter episode entry."""
    error_type = entry.get("error_type", "Unknown")
    name = entry.get("name", "unknown")
    error = entry.get("error", "")[:100].replace('"', '\\"')
    group_id = entry.get("group_id", "")

    func_name = sanitize_func_name(f"dead_letter_{name}_{error_type}")

    return f'''
def test_{func_name}():
    """Regression: Dead letter episode — {error_type}

    Name: {name}
    Group ID: {group_id}
    Error: {error}
    """
    # Documents a real Graphiti episode persistence failure.
    # When Graphiti integration tests are enabled, validate that the
    # error condition is caught and the episode lands in dead-letter queue.
    pytest.skip("Graphiti integration tests not yet enabled")
'''


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    bugs = read_jsonl(DATA_DIR / "bug_log.jsonl")
    edge_failures = read_jsonl(DATA_DIR / "failed_edge_syncs.jsonl")
    dead_letters = read_jsonl(DATA_DIR / "dead_letter_episodes.jsonl")

    print(
        f"Found: {len(bugs)} bugs, "
        f"{len(edge_failures)} edge failures, "
        f"{len(dead_letters)} dead letters"
    )

    # --- Build output --------------------------------------------------------
    parts: List[str] = []

    # File header
    parts.append(
        f'"""Auto-generated regression tests from production error logs.\n'
        f"\n"
        f"Generated: {datetime.now().isoformat()[:19]}\n"
        f"Source: scripts/generate_regression_tests.py (Self-Improving Flywheel)\n"
        f"\n"
        f"Bug log entries: {len(bugs)}\n"
        f"Edge sync failures: {len(edge_failures)}\n"
        f"Dead letter episodes: {len(dead_letters)}\n"
        f"\n"
        f"Re-generate:\n"
        f"    python scripts/generate_regression_tests.py\n"
        f'"""\n'
        f"import pytest\n"
    )

    # --- Bug log tests -------------------------------------------------------
    parts.append(
        "\n"
        "# ════════════════════════════════════════════════════════════════\n"
        f"# Bug Log Regression Tests  (deduplicated by endpoint+error_type)\n"
        "# ════════════════════════════════════════════════════════════════\n"
    )

    seen_bugs: set[tuple[str | None, str | None]] = set()
    bug_test_count = 0
    for bug in bugs:
        key = (bug.get("endpoint"), bug.get("error_type"))
        if key not in seen_bugs:
            seen_bugs.add(key)
            parts.append(generate_bug_test(bug))
            bug_test_count += 1

    # --- Edge sync tests -----------------------------------------------------
    parts.append(
        "\n"
        "# ════════════════════════════════════════════════════════════════\n"
        f"# Edge Sync Failure Tests  (deduplicated by edge_id)\n"
        "# ════════════════════════════════════════════════════════════════\n"
    )

    seen_edges: set[str | None] = set()
    edge_test_count = 0
    for entry in edge_failures:
        key = entry.get("edge_id")
        if key not in seen_edges:
            seen_edges.add(key)
            parts.append(generate_edge_sync_test(entry))
            edge_test_count += 1

    # --- Dead letter tests ---------------------------------------------------
    parts.append(
        "\n"
        "# ════════════════════════════════════════════════════════════════\n"
        f"# Dead Letter Episode Tests  (deduplicated by name+error_type)\n"
        "# ════════════════════════════════════════════════════════════════\n"
    )

    seen_dl: set[tuple[str | None, str | None]] = set()
    dl_test_count = 0
    for entry in dead_letters:
        key = (entry.get("name"), entry.get("error_type"))
        if key not in seen_dl:
            seen_dl.add(key)
            parts.append(generate_dead_letter_test(entry))
            dl_test_count += 1

    content = "\n".join(parts) + "\n"
    total_tests = bug_test_count + edge_test_count + dl_test_count

    if dry_run:
        print("=== DRY RUN (not writing) ===")
        print(content[:3000])
        if len(content) > 3000:
            print(f"... ({len(content)} chars total)")
        print(
            f"\nTests: {total_tests} "
            f"(bugs={bug_test_count}, edges={edge_test_count}, "
            f"dead_letters={dl_test_count})"
        )
    else:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(content, encoding="utf-8")
        print(f"Generated: {OUTPUT_FILE}")
        print(
            f"Tests: {total_tests} "
            f"(bugs={bug_test_count}, edges={edge_test_count}, "
            f"dead_letters={dl_test_count})"
        )


if __name__ == "__main__":
    main()
