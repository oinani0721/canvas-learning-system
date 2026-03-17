#!/usr/bin/env python
# Story 7.3: Prompt Regression Test CLI Trigger
# [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
"""
Command-line script to trigger prompt regression tests.

Usage:
    python scripts/run_prompt_regression.py                    # Run all
    python scripts/run_prompt_regression.py --prompt autoscore  # Run specific
    python scripts/run_prompt_regression.py --prompt autoscore --live  # With real LLM
    python scripts/run_prompt_regression.py --check             # Check for changes only

This script:
  1. Loads the PromptRegistry
  2. Compares current prompt hashes against baseline_metadata.json
  3. Runs the corresponding regression tests via pytest
  4. Reports results
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

# Paths
BACKEND_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BACKEND_DIR / "app" / "prompts"
BASELINES_DIR = BACKEND_DIR / "tests" / "fixtures" / "regression_baselines"
REGRESSION_DIR = BACKEND_DIR / "tests" / "regression"
METADATA_FILE = BASELINES_DIR / "baseline_metadata.json"

# Prompt name -> test file mapping (AC-3)
PROMPT_TEST_MAP = {
    "autoscore": "test_autoscore_regression.py",
    "question_gen": "test_question_gen_regression.py",
    "context_extract": "test_context_extract_regression.py",
}


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file's content."""
    content = filepath.read_bytes()
    return hashlib.sha256(content).hexdigest()


def detect_changes() -> dict:
    """
    Compare current prompt file hashes against stored baselines.

    Returns dict mapping prompt_name -> {"changed": bool, "current_hash": str, "baseline_hash": str}
    """
    metadata = {}
    if METADATA_FILE.exists():
        metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))

    baselines = metadata.get("baselines", {})
    results = {}

    for md_file in sorted(PROMPTS_DIR.glob("*_v*.md")):
        import re
        match = re.match(r"^(.+)_v(\d+)\.md$", md_file.name)
        if not match:
            continue
        name = match.group(1)
        current_hash = compute_file_hash(md_file)

        baseline_info = baselines.get(name, {})
        baseline_hash = baseline_info.get("prompt_hash")

        results[name] = {
            "changed": baseline_hash is None or baseline_hash != current_hash,
            "current_hash": current_hash,
            "baseline_hash": baseline_hash,
            "file": md_file.name,
        }

    return results


def run_regression(prompt_name: str = None, live: bool = False) -> int:
    """
    Run regression tests via pytest.

    Args:
        prompt_name: Specific prompt to test, or None for all
        live: Whether to use --live flag for real LLM calls

    Returns:
        pytest exit code
    """
    cmd = [sys.executable, "-m", "pytest", "-v"]

    if prompt_name:
        test_file = PROMPT_TEST_MAP.get(prompt_name)
        if not test_file:
            print("ERROR: Unknown prompt name: {}".format(prompt_name))
            print("Available: {}".format(", ".join(PROMPT_TEST_MAP.keys())))
            return 1
        cmd.append(str(REGRESSION_DIR / test_file))
    else:
        cmd.append(str(REGRESSION_DIR))

    if live:
        cmd.append("--live")

    print("Running: {}".format(" ".join(cmd)))
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR))
    return result.returncode


def update_baseline_hashes():
    """Update baseline_metadata.json with current prompt hashes."""
    metadata = {}
    if METADATA_FILE.exists():
        metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))

    baselines = metadata.get("baselines", {})
    changes = detect_changes()

    for name, info in changes.items():
        if name not in baselines:
            baselines[name] = {}
        baselines[name]["prompt_hash"] = info["current_hash"]

    metadata["baselines"] = baselines
    METADATA_FILE.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("Updated baseline hashes in {}".format(METADATA_FILE))


def main():
    parser = argparse.ArgumentParser(
        description="Prompt Regression Test Runner (Story 7.3)"
    )
    parser.add_argument(
        "--prompt",
        choices=list(PROMPT_TEST_MAP.keys()),
        help="Run tests for a specific prompt template",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real LLM calls instead of replay mode",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check for prompt changes, do not run tests",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline hashes after successful test run",
    )

    args = parser.parse_args()

    # Detect changes
    changes = detect_changes()
    print("\n=== Prompt Change Detection ===")
    any_changed = False
    for name, info in sorted(changes.items()):
        status = "CHANGED" if info["changed"] else "unchanged"
        print("  {} ({}): {}".format(name, info["file"], status))
        if info["changed"]:
            any_changed = True

    if not any_changed:
        print("\nNo prompt changes detected.")

    if args.check:
        return 0 if not any_changed else 1

    # Run tests
    print("\n=== Running Regression Tests ===")
    exit_code = run_regression(prompt_name=args.prompt, live=args.live)

    if exit_code == 0 and args.update_baseline:
        update_baseline_hashes()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
