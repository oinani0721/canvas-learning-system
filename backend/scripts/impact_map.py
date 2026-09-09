"""AST-based impact map: source file -> related test files.

Parses all test_*.py files under tests/ to find `from app.xxx import ...`
and `import app.xxx` statements, then builds a reverse mapping from source
files to the test files that depend on them.

Usage:
    python scripts/impact_map.py app/services/review_service.py
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = BACKEND_ROOT / "tests"
CACHE_DIR = BACKEND_ROOT / ".cache"
CACHE_FILE = CACHE_DIR / "impact_map.json"


def _collect_test_files() -> list[Path]:
    """Recursively find all test_*.py files under tests/."""
    return sorted(TESTS_DIR.rglob("test_*.py"))


def _extract_app_modules(test_file: Path) -> list[str]:
    """Parse a test file's AST and return app.* module paths as file paths."""
    try:
        source = test_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(test_file))
    except (SyntaxError, UnicodeDecodeError):
        return []

    modules: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("app")
        ):
            # e.g. from app.services.review_service import X -> app/services/review_service.py
            mod_path = node.module.replace(".", "/") + ".py"
            modules.append(mod_path)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app"):
                    mod_path = alias.name.replace(".", "/") + ".py"
                    modules.append(mod_path)
    return modules


def _cache_is_fresh(test_files: list[Path]) -> bool:
    """Return True if cache exists and is newer than all test files."""
    if not CACHE_FILE.exists():
        return False
    cache_mtime = CACHE_FILE.stat().st_mtime
    return all(tf.stat().st_mtime <= cache_mtime for tf in test_files)


def build_impact_map() -> dict[str, list[str]]:
    """Build and cache the source->test-files mapping."""
    test_files = _collect_test_files()

    if _cache_is_fresh(test_files):
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    impact: dict[str, list[str]] = {}
    for tf in test_files:
        rel_test = str(tf.relative_to(BACKEND_ROOT))
        for mod_path in _extract_app_modules(tf):
            impact.setdefault(mod_path, []).append(rel_test)

    # Sort test lists for deterministic output
    for key in impact:
        impact[key] = sorted(set(impact[key]))

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(impact, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return impact


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/impact_map.py <source_file_path>", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    impact = build_impact_map()

    related = impact.get(query, [])
    if not related:
        # Try normalizing: strip leading ./ or backend/
        normalized = query.lstrip("./").removeprefix("backend/")
        related = impact.get(normalized, [])

    for test_path in related:
        print(test_path)


if __name__ == "__main__":
    main()
