#!/usr/bin/env python3
"""
Canvas Learning System - Iteration Finalization Script

在 Story/迭代完成时自动执行规范同步和验证。
集成到 BMad 工作流中，确保每次迭代后规范与代码保持同步。

Usage:
    python scripts/spec-tools/finalize-iteration.py [--story STORY_ID] [--auto-commit]

Examples:
    python scripts/spec-tools/finalize-iteration.py
    python scripts/spec-tools/finalize-iteration.py --story 15.6 --auto-commit
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'


def color(text: str, c: str) -> str:
    """Add color to text"""
    if os.environ.get('NO_COLOR'):
        return text
    return f"{c}{text}{Colors.END}"


def print_header(title: str):
    """Print section header"""
    print()
    print(color("=" * 60, Colors.CYAN))
    print(color(f"  {title}", Colors.CYAN))
    print(color("=" * 60, Colors.CYAN))


def print_step(step: int, description: str):
    """Print step indicator"""
    print(f"\n{color(f'[Step {step}]', Colors.BLUE)} {description}")


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def check_api_changes(project_root: Path) -> Tuple[bool, List[str]]:
    """Check if there are staged API-related changes"""
    api_patterns = [
        "backend/app/api/",
        "backend/app/models/",
        "backend/app/schemas/",
    ]

    returncode, stdout, _ = run_command(
        ["git", "diff", "--cached", "--name-only"],
        cwd=project_root
    )

    if returncode != 0:
        return False, []

    changed_files = stdout.strip().split('\n') if stdout.strip() else []
    api_changes = [f for f in changed_files if any(f.startswith(p) for p in api_patterns)]

    return len(api_changes) > 0, api_changes


def export_openapi(project_root: Path) -> Tuple[bool, str]:
    """Export OpenAPI specification"""
    script_path = project_root / "scripts" / "spec-tools" / "export-openapi.py"

    returncode, stdout, stderr = run_command(
        ["python", str(script_path), "--stats"],
        cwd=project_root / "backend"
    )

    if returncode == 0:
        return True, stdout
    else:
        return False, stderr or "Export failed"


def verify_sync(project_root: Path) -> Tuple[bool, Dict]:
    """Verify specification sync status"""
    script_path = project_root / "scripts" / "spec-tools" / "verify-sync.py"

    returncode, stdout, _ = run_command(
        ["python", str(script_path), "--json"],
        cwd=project_root
    )

    if returncode == 0:
        try:
            result = json.loads(stdout)
            sync_rate = result.get('comparison', {}).get('sync_rate', 0)
            return sync_rate >= 95, result
        except json.JSONDecodeError:
            pass

    return False, {}


def run_contract_tests(project_root: Path) -> Tuple[bool, str]:
    """Run contract tests"""
    returncode, stdout, stderr = run_command(
        ["pytest", "tests/contract/", "-v", "--tb=short"],
        cwd=project_root / "backend"
    )

    return returncode == 0, stdout + stderr


def diff_openapi(project_root: Path) -> Tuple[bool, str]:
    """Compare current spec with main branch"""
    spec_path = project_root / "openapi.json"

    # Get spec from main branch
    returncode, main_spec, _ = run_command(
        ["git", "show", "main:openapi.json"],
        cwd=project_root
    )

    if returncode != 0:
        return True, "No main branch spec to compare"

    # Save temporarily and compare
    temp_path = project_root / ".temp-openapi-main.json"
    try:
        temp_path.write_text(main_spec, encoding='utf-8')

        diff_script = project_root / "scripts" / "spec-tools" / "diff-openapi.py"
        returncode, stdout, _ = run_command(
            ["python", str(diff_script), str(temp_path), str(spec_path)],
            cwd=project_root
        )

        return True, stdout
    finally:
        if temp_path.exists():
            temp_path.unlink()


def update_changelog(project_root: Path, story_id: Optional[str], changes: str) -> bool:
    """Update API changelog"""
    changelog_path = project_root / "specs" / "api" / "versions" / "CHANGELOG.md"

    if not changelog_path.parent.exists():
        changelog_path.parent.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")

    entry = f"""
## [{today}] - Story {story_id or 'N/A'}

### Changes
{changes}

---
"""

    if changelog_path.exists():
        content = changelog_path.read_text(encoding='utf-8')
        # Insert after header
        if "# API Changelog" in content:
            content = content.replace("# API Changelog\n", f"# API Changelog\n{entry}")
        else:
            content = f"# API Changelog\n{entry}\n{content}"
    else:
        content = f"# API Changelog\n\nTrack all API specification changes.\n{entry}"

    changelog_path.write_text(content, encoding='utf-8')
    return True


def generate_summary(results: Dict) -> str:
    """Generate finalization summary"""
    lines = []

    lines.append("## Iteration Finalization Summary")
    lines.append(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    # API Changes
    if results.get('api_changes'):
        lines.append("### API Files Changed")
        for f in results['api_changes']:
            lines.append(f"  - {f}")
        lines.append("")

    # Sync Status
    if 'sync_result' in results:
        sync = results['sync_result']
        rate = sync.get('comparison', {}).get('sync_rate', 0)
        lines.append(f"### Sync Rate: {rate:.1f}%")

    # Contract Tests
    if 'contract_tests' in results:
        status = "PASSED" if results['contract_tests'] else "FAILED"
        lines.append(f"### Contract Tests: {status}")

    # Breaking Changes
    if results.get('has_breaking_changes'):
        lines.append("")
        lines.append("### ⚠️ Breaking Changes Detected")
        lines.append("Review required before merging.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Finalize iteration with spec sync and validation"
    )
    parser.add_argument(
        "--story", "-s",
        help="Story ID for changelog entry"
    )
    parser.add_argument(
        "--auto-commit", "-c",
        action="store_true",
        help="Automatically commit spec changes"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip contract tests"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    results = {'timestamp': datetime.now(timezone.utc).isoformat()}

    print_header("Canvas Learning System - Iteration Finalization")

    # Step 1: Check for API changes
    print_step(1, "Checking for API-related changes...")
    has_api_changes, api_changes = check_api_changes(project_root)
    results['has_api_changes'] = has_api_changes
    results['api_changes'] = api_changes

    if has_api_changes:
        print(f"  {color('Found', Colors.YELLOW)} {len(api_changes)} API-related files changed")
        for f in api_changes[:5]:
            print(f"    - {f}")
        if len(api_changes) > 5:
            print(f"    ... and {len(api_changes) - 5} more")
    else:
        print(f"  {color('No API changes detected', Colors.GREEN)}")

    # Step 2: Export OpenAPI spec
    print_step(2, "Exporting OpenAPI specification...")
    success, output = export_openapi(project_root)
    results['export_success'] = success

    if success:
        print(f"  {color('Successfully exported', Colors.GREEN)}")
        # Show stats
        for line in output.split('\n'):
            if line.strip().startswith(('OpenAPI', 'API', 'Paths', 'Schemas', 'Total')):
                print(f"    {line.strip()}")
    else:
        print(f"  {color('Export failed:', Colors.RED)} {output}")
        if not args.json:
            sys.exit(1)

    # Step 3: Verify sync
    print_step(3, "Verifying specification sync...")
    is_synced, sync_result = verify_sync(project_root)
    results['is_synced'] = is_synced
    results['sync_result'] = sync_result

    if is_synced:
        rate = sync_result.get('comparison', {}).get('sync_rate', 0)
        print(f"  {color(f'Sync rate: {rate:.1f}%', Colors.GREEN)}")
    else:
        rate = sync_result.get('comparison', {}).get('sync_rate', 0)
        print(f"  {color(f'Sync rate: {rate:.1f}% (below 95% threshold)', Colors.RED)}")

    # Step 4: Run contract tests (optional)
    if not args.skip_tests:
        print_step(4, "Running contract tests...")
        tests_passed, test_output = run_contract_tests(project_root)
        results['contract_tests'] = tests_passed

        if tests_passed:
            print(f"  {color('All contract tests passed', Colors.GREEN)}")
        else:
            print(f"  {color('Some contract tests failed', Colors.YELLOW)}")
            # Show first few lines of failure
            for line in test_output.split('\n')[:10]:
                if 'FAILED' in line or 'ERROR' in line:
                    print(f"    {line}")
    else:
        print_step(4, "Skipping contract tests (--skip-tests)")
        results['contract_tests'] = None

    # Step 5: Diff with main
    print_step(5, "Comparing with main branch...")
    _, diff_output = diff_openapi(project_root)
    results['has_breaking_changes'] = 'BREAKING CHANGES' in diff_output

    if results['has_breaking_changes']:
        print(f"  {color('Breaking changes detected!', Colors.RED)}")
    else:
        print(f"  {color('No breaking changes', Colors.GREEN)}")

    # Step 6: Update changelog
    if has_api_changes:
        print_step(6, "Updating API changelog...")
        changes = "\n".join([f"- Modified: `{f}`" for f in api_changes])
        update_changelog(project_root, args.story, changes)
        print(f"  {color('Changelog updated', Colors.GREEN)}")

    # Step 7: Auto-commit (optional)
    if args.auto_commit and has_api_changes:
        print_step(7, "Auto-committing spec changes...")
        run_command(["git", "add", "openapi.json"], cwd=project_root)
        run_command(["git", "add", "specs/"], cwd=project_root)

        commit_msg = f"chore(spec): update OpenAPI specification"
        if args.story:
            commit_msg += f" [Story {args.story}]"

        returncode, _, _ = run_command(
            ["git", "commit", "-m", commit_msg],
            cwd=project_root
        )

        if returncode == 0:
            print(f"  {color('Changes committed', Colors.GREEN)}")
        else:
            print(f"  {color('Nothing to commit or commit failed', Colors.YELLOW)}")

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print()
        print_header("Finalization Complete")
        summary = generate_summary(results)
        print(summary)

        # Final status
        all_passed = (
            results.get('export_success', False) and
            results.get('is_synced', False) and
            results.get('contract_tests', True) is not False
        )

        if all_passed:
            print(f"\n{color('✓ All checks passed!', Colors.GREEN)}")
            print("Ready for QA review.")
        else:
            print(f"\n{color('⚠ Some checks need attention.', Colors.YELLOW)}")
            print("Review the issues above before proceeding.")

    sys.exit(0 if results.get('is_synced', False) else 1)


if __name__ == "__main__":
    main()
