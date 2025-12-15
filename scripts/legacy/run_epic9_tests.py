#!/usr/bin/env python3
"""
Epic 9 Test Runner
Canvas Learning System - Epic 9 Integration Testing and Validation
Story 9.6

This script runs all Epic 9 tests and generates comprehensive reports.
Usage: python run_epic9_tests.py [options]
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class TestRunner:
    """Epic 9 Test Runner"""

    def __init__(self, workspace: Optional[str] = None):
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.test_dir = self.workspace / "tests"
        self.reports_dir = self.workspace / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Test results
        self.results = {
            "timestamp": self.timestamp,
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0
            },
            "categories": {},
            "coverage": {},
            "performance": {},
            "duration": 0
        }

    def run_command(self, cmd: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run command and return result"""
        print(f"Running: {' '.join(cmd)}")
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                cwd=self.workspace
            )
            duration = time.time() - start_time
            print(f"Completed in {duration:.2f}s")
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
            return e

    def run_unit_tests(self) -> Dict:
        """Run unit tests with coverage"""
        print("\n" + "="*60)
        print("🔬 Running Unit Tests")
        print("="*60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v",
            "--cov=canvas_utils",
            "--cov-report=json",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--junit-xml", f"test_reports/unit_tests_{self.timestamp}.xml"
        ]

        result = self.run_command(cmd)

        # Parse results
        if result.returncode == 0:
            # Read coverage report
            coverage_file = self.workspace / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    self.results["coverage"] = {
                        "total": coverage_data["totals"]["percent_covered"],
                        "files": {
                            file: info["summary"]["percent_covered"]
                            for file, info in coverage_data["files"].items()
                        }
                    }

        return {
            "exit_code": result.returncode,
            "output": result.stdout if result.stdout else result.stderr,
            "duration": 0  # Pytest provides duration in output
        }

    def run_integration_tests(self) -> Dict:
        """Run integration tests"""
        print("\n" + "="*60)
        print("🔗 Running Integration Tests")
        print("="*60)

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v",
            "--junit-xml", f"test_reports/integration_tests_{self.timestamp}.xml"
        ]

        result = self.run_command(cmd)
        return {
            "exit_code": result.returncode,
            "output": result.stdout if result.stdout else result.stderr,
            "duration": 0
        }

    def run_performance_tests(self) -> Dict:
        """Run performance tests"""
        print("\n" + "="*60)
        print("⚡ Running Performance Tests")
        print("="*60)

        # First check if performance tests exist
        perf_dir = self.test_dir / "performance"
        if not perf_dir.exists():
            print("No performance tests directory found")
            return {"exit_code": 0, "output": "No performance tests", "duration": 0}

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/performance/",
            "-v",
            "--benchmark-only",
            "--benchmark-json", f"test_reports/performance_{self.timestamp}.json",
            "--benchmark-sort=mean"
        ]

        result = self.run_command(cmd)

        # Parse benchmark results
        if result.returncode == 0:
            benchmark_file = self.reports_dir / f"performance_{self.timestamp}.json"
            if benchmark_file.exists():
                with open(benchmark_file) as f:
                    benchmark_data = json.load(f)

                self.results["performance"] = {
                    "benchmarks": benchmark_data.get("benchmarks", []),
                    "machine_info": benchmark_data.get("machine_info", {}),
                    "commit_info": benchmark_data.get("commit_info", {})
                }

        return {
            "exit_code": result.returncode,
            "output": result.stdout if result.stdout else result.stderr,
            "duration": 0
        }

    def run_e2e_tests(self) -> Dict:
        """Run end-to-end tests"""
        print("\n" + "="*60)
        print("🎯 Running End-to-End Tests")
        print("="*60)

        e2e_dir = self.test_dir / "e2e"
        if not e2e_dir.exists():
            print("No E2E tests directory found")
            return {"exit_code": 0, "output": "No E2E tests", "duration": 0}

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/e2e/",
            "-v",
            "-s",
            "--junit-xml", f"test_reports/e2e_tests_{self.timestamp}.xml"
        ]

        result = self.run_command(cmd)
        return {
            "exit_code": result.returncode,
            "output": result.stdout if result.stdout else result.stderr,
            "duration": 0
        }

    def parse_pytest_output(self, output: str) -> Dict:
        """Parse pytest output for test results"""
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0
        }

        lines = output.split('\n')
        for line in lines:
            if '=' in line and 'passed' in line:
                # Parse summary line like: "5 passed, 2 failed, 1 skipped in 10.5s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        count = int(part)
                        if i + 1 < len(parts):
                            status = parts[i + 1].rstrip(',')
                            if status in results:
                                results[status] = count
                        results["total"] += count

        return results

    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report_file = self.reports_dir / f"epic9_test_report_{self.timestamp}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Epic 9 Test Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Workspace**: {self.workspace}\n\n")

            # Summary
            f.write("## 📊 Test Summary\n\n")
            f.write("| Category | Status | Details |\n")
            f.write("|----------|--------|---------|\n")

            for category, result in self.results["categories"].items():
                status = "✅ Passed" if result["exit_code"] == 0 else "❌ Failed"
                f.write(f"| {category.title()} | {status} | {result.get('duration', 'N/A')}s |\n")

            # Coverage
            if self.results["coverage"]:
                f.write(f"\n## 📈 Coverage Report\n\n")
                f.write(f"**Total Coverage**: {self.results['coverage']['total']:.1f}%\n\n")

                if self.results["coverage"]["total"] >= 95:
                    f.write("✅ Coverage target met (≥95%)\n\n")
                else:
                    f.write(f"⚠️ Coverage below target (≥95%). Current: {self.results['coverage']['total']:.1f}%\n\n")

                f.write("### Coverage by File\n\n")
                f.write("| File | Coverage |\n")
                f.write("|------|----------|\n")

                for file, coverage in self.results["coverage"]["files"].items():
                    f.write(f"| {file} | {coverage:.1f}% |\n")

            # Performance
            if self.results["performance"]:
                f.write(f"\n## ⚡ Performance Benchmarks\n\n")

                benchmarks = self.results["performance"]["benchmarks"]
                if benchmarks:
                    f.write("| Benchmark | Mean (s) | Min (s) | Max (s) | Status |\n")
                    f.write("|-----------|----------|---------|---------|--------|\n")

                    for bench in benchmarks[:10]:  # Show top 10
                        name = bench.get("name", "Unknown")
                        mean = bench.get("stats", {}).get("mean", 0)
                        min_val = bench.get("stats", {}).get("min", 0)
                        max_val = bench.get("stats", {}).get("max", 0)

                        # Check against thresholds
                        status = "✅"
                        if "load" in name.lower() and mean > 60:
                            status = "⚠️"
                        elif "validation" in name.lower() and mean > 1:
                            status = "⚠️"

                        f.write(f"| {name} | {mean:.4f} | {min_val:.4f} | {max_val:.4f} | {status} |\n")

            # Recommendations
            f.write(f"\n## 💡 Recommendations\n\n")

            if self.results["coverage"].get("total", 0) < 95:
                f.write("- Add more unit tests to reach 95% coverage target\n")

            failed_categories = [cat for cat, res in self.results["categories"].items() if res["exit_code"] != 0]
            if failed_categories:
                f.write(f"- Fix failing tests in: {', '.join(failed_categories)}\n")

            if not any([self.results["coverage"], self.results["performance"]]):
                f.write("- Enable coverage and performance testing\n")

            f.write("\n---\n")
            f.write("*Report generated by Epic 9 Test Runner*\n")

        return str(report_file)

    def run_all_tests(self, categories: Optional[List[str]] = None) -> bool:
        """Run all specified test categories"""
        start_time = time.time()

        # Default to all categories
        if not categories:
            categories = ["unit", "integration", "performance", "e2e"]

        # Define test runners
        runners = {
            "unit": self.run_unit_tests,
            "integration": self.run_integration_tests,
            "performance": self.run_performance_tests,
            "e2e": self.run_e2e_tests
        }

        # Run tests
        for category in categories:
            if category in runners:
                self.results["categories"][category] = runners[category]()

        # Calculate total duration
        self.results["duration"] = time.time() - start_time

        # Parse results from outputs
        for category, result in self.results["categories"].items():
            if result["output"]:
                parsed = self.parse_pytest_output(result["output"])
                for key, value in parsed.items():
                    self.results["summary"][key] += value

        # Generate report
        report_path = self.generate_report()
        print(f"\n📋 Test report generated: {report_path}")

        # Print summary
        self.print_summary()

        # Return True if all tests passed
        return all(r["exit_code"] == 0 for r in self.results["categories"].values())

    def print_summary(self):
        """Print test summary to console"""
        print("\n" + "="*60)
        print("📊 EPIC 9 TEST SUMMARY")
        print("="*60)

        print(f"Total Tests: {self.results['summary']['total']}")
        print(f"Passed: {self.results['summary']['passed']} ✅")
        print(f"Failed: {self.results['summary']['failed']} ❌")
        print(f"Skipped: {self.results['summary']['skipped']} ⏭️")
        print(f"Errors: {self.results['summary']['errors']} 💥")
        print(f"Duration: {self.results['duration']:.2f}s")

        if self.results["coverage"]:
            print(f"\nCoverage: {self.results['coverage']['total']:.1f}% ", end="")
            if self.results['coverage']['total'] >= 95:
                print("✅")
            else:
                print("⚠️ (Target: 95%)")

        print("\n" + "="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Epic 9 Test Runner for Canvas Learning System"
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["unit", "integration", "performance", "e2e"],
        help="Test categories to run (default: all)"
    )
    parser.add_argument(
        "--workspace",
        help="Workspace directory (default: current directory)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )

    args = parser.parse_args()

    # Create test runner
    runner = TestRunner(workspace=args.workspace)

    # Run tests
    success = runner.run_all_tests(categories=args.categories)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()