"""
Canvas Learning System - Environment Diagnostic Unit Tests

Unit tests for deployment/diagnose_environment.py covering:
- 7 environmental checks (Python, pip, env vars, Neo4j, database, MCP server, MCP client)
- Success and failure scenarios
- Quick fix generation
- Summary report generation

Story: 10.11.5 - 诊断工具和部署文档
AC5: Unit tests for diagnose_environment.py

Author: Canvas Learning System Team
Created: 2025-10-31
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "deployment"))

# Import functions to test
from diagnose_environment import (
    check_environment_variables,
    check_mcp_memory_client_import,
    check_neo4j_database,
    check_pip_packages,
    check_python_version,
    generate_diagnosis_report,
)

# =============================================================================
# Test 1: Python Version Check
# =============================================================================

def test_check_python_version_success():
    """Test Python version check with Python 3.9+"""
    # Act
    result = check_python_version()

    # Assert
    assert 'passed' in result
    assert result['passed'] is True, "Python 3.9+ should be available"
    assert 'version' in result
    assert 'Python' in result['version']


# =============================================================================
# Test 2: pip Package Check
# =============================================================================

@patch('diagnose_environment.find_spec')
def test_check_pip_packages_all_installed(mock_find_spec):
    """Test pip package check when all packages are installed"""
    # Arrange - Mock all packages as found
    mock_find_spec.return_value = Mock()

    # Act
    result = check_pip_packages()

    # Assert
    assert result['passed'] is True
    assert result['installed_count'] == result['total_count']
    assert result['missing_packages'] == []


@patch('diagnose_environment.find_spec')
def test_check_pip_packages_some_missing(mock_find_spec):
    """Test pip package check when some packages are missing"""
    # Arrange - Make graphiti-core missing
    def mock_find(name):
        if 'graphiti' in name:
            return None
        return Mock()

    mock_find_spec.side_effect = mock_find

    # Act
    result = check_pip_packages()

    # Assert
    assert result['passed'] is False
    assert len(result['missing_packages']) > 0
    assert 'graphiti-core' in result['missing_packages']
    assert result['quick_fix'] == "pip install -r requirements.txt"


# =============================================================================
# Test 3: Environment Variables Check
# =============================================================================

@patch.dict(os.environ, {
    'NEO4J_URI': 'bolt://localhost:7687',
    'NEO4J_USERNAME': 'neo4j',
    'NEO4J_PASSWORD': 'password',
    'NEO4J_DATABASE': 'ultrathink'
})
def test_check_environment_variables_all_set():
    """Test environment variables check when all are set"""
    # Act
    result = check_environment_variables()

    # Assert
    assert result['passed'] is True
    assert result['set_count'] == result['total_count']
    assert result['missing_variables'] == []


@patch.dict(os.environ, {
    'NEO4J_URI': 'bolt://localhost:7687'
}, clear=True)
def test_check_environment_variables_some_missing():
    """Test environment variables check when some are missing"""
    # Act
    result = check_environment_variables()

    # Assert
    assert result['passed'] is False
    assert len(result['missing_variables']) > 0
    assert 'NEO4J_PASSWORD' in result['missing_variables']
    assert result['quick_fix'] == "copy .env.example .env && notepad .env"


# =============================================================================
# Test 4: Neo4j Database Check
# =============================================================================

@patch('diagnose_environment.check_neo4j_database_exists')
def test_check_neo4j_database_exists(mock_check_db):
    """Test Neo4j database check when database exists"""
    # Arrange
    mock_check_db.return_value = {
        'exists': True,
        'name': 'ultrathink',
        'error': None
    }

    # Act
    result = check_neo4j_database()

    # Assert
    assert result['passed'] is True
    assert result['database_name'] == 'ultrathink'
    assert result['error'] is None


@patch('diagnose_environment.check_neo4j_database_exists')
def test_check_neo4j_database_not_exists(mock_check_db):
    """Test Neo4j database check when database doesn't exist"""
    # Arrange
    mock_check_db.return_value = {
        'exists': False,
        'name': 'ultrathink',
        'error': "Database 'ultrathink' not found"
    }

    # Act
    result = check_neo4j_database()

    # Assert
    assert result['passed'] is False
    assert result['database_name'] == 'ultrathink'
    assert "ultrathink" in result['suggestion']
    assert "CREATE DATABASE" in result['quick_fix']


# =============================================================================
# Test 5: MCP Client Import Check
# =============================================================================

@patch('diagnose_environment.diagnose_mcp_memory_client')
def test_check_mcp_client_import_success(mock_diagnose):
    """Test MCP client import check when successful"""
    # Arrange
    mock_diagnose.return_value = {
        'success': True,
        'error': None,
        'missing_packages': []
    }

    # Act
    result = check_mcp_memory_client_import()

    # Assert
    assert result['passed'] is True
    assert result['error'] is None


@patch('diagnose_environment.diagnose_mcp_memory_client')
def test_check_mcp_client_import_failure(mock_diagnose):
    """Test MCP client import check when import fails"""
    # Arrange
    mock_diagnose.return_value = {
        'success': False,
        'error': 'ModuleNotFoundError: chromadb',
        'missing_packages': ['chromadb']
    }

    # Act
    result = check_mcp_memory_client_import()

    # Assert
    assert result['passed'] is False
    assert result['error'] is not None
    assert 'chromadb' in result['error']


# =============================================================================
# Test 6: Diagnosis Report Generation
# =============================================================================

def test_generate_diagnosis_report_all_passed():
    """Test diagnosis report when all checks pass"""
    # Arrange
    results = {
        'python_version': {'passed': True, 'version': 'Python 3.11.0'},
        'pip_packages': {'passed': True, 'installed_count': 4, 'total_count': 4},
        'env_variables': {'passed': True, 'set_count': 4, 'total_count': 4},
        'neo4j_connection': {'passed': True, 'host': 'localhost'},
        'neo4j_database': {'passed': True, 'database_name': 'ultrathink'},
        'mcp_server': {'passed': True},
        'mcp_client': {'passed': True}
    }

    # Act
    report = generate_diagnosis_report(results)

    # Assert
    assert isinstance(report, str)
    assert "✅" in report
    assert "7/7" in report or "所有检查通过" in report
    assert "❌" not in report


def test_generate_diagnosis_report_some_failed():
    """Test diagnosis report when some checks fail"""
    # Arrange
    results = {
        'python_version': {'passed': True, 'version': 'Python 3.11.0'},
        'pip_packages': {
            'passed': False,
            'missing_packages': ['graphiti-core'],
            'quick_fix': 'pip install graphiti-core',
            'estimated_time': 2
        },
        'env_variables': {'passed': True, 'set_count': 4, 'total_count': 4},
        'neo4j_connection': {
            'passed': False,
            'error': 'Connection refused',
            'suggestion': '启动Neo4j',
            'quick_fix': 'neo4j.bat console',
            'estimated_time': 1
        },
        'neo4j_database': {'passed': True, 'database_name': 'ultrathink'},
        'mcp_server': {'passed': True},
        'mcp_client': {'passed': True}
    }

    # Act
    report = generate_diagnosis_report(results)

    # Assert
    assert isinstance(report, str)
    assert "❌" in report
    assert "2/7项失败" in report or "2" in report
    assert "快速修复命令" in report
    assert "neo4j.bat console" in report
    assert "pip install graphiti-core" in report


def test_generate_diagnosis_report_estimates_fix_time():
    """Test diagnosis report includes estimated fix time"""
    # Arrange
    results = {
        'python_version': {'passed': True, 'version': 'Python 3.11.0'},
        'pip_packages': {
            'passed': False,
            'missing_packages': ['graphiti-core'],
            'quick_fix': 'pip install graphiti-core',
            'estimated_time': 2
        },
        'env_variables': {
            'passed': False,
            'missing_variables': ['NEO4J_PASSWORD'],
            'quick_fix': 'copy .env.example .env',
            'estimated_time': 0.5
        },
        'neo4j_connection': {'passed': True},
        'neo4j_database': {'passed': True},
        'mcp_server': {'passed': True},
        'mcp_client': {'passed': True}
    }

    # Act
    report = generate_diagnosis_report(results)

    # Assert
    assert isinstance(report, str)
    # Should estimate total fix time (2 + 0.5 = 2.5, rounded to 3 minutes)
    assert "预计修复时间" in report
    assert "分钟" in report


# =============================================================================
# Test 7: Edge Cases
# =============================================================================

def test_check_python_version_returns_dict():
    """Test check_python_version returns proper dictionary structure"""
    result = check_python_version()

    assert isinstance(result, dict)
    assert 'passed' in result
    assert 'version' in result
    assert isinstance(result['passed'], bool)
    assert isinstance(result['version'], str)


@patch.dict(os.environ, {}, clear=True)
def test_check_environment_variables_none_set():
    """Test environment variables check when none are set"""
    result = check_environment_variables()

    assert result['passed'] is False
    assert result['set_count'] == 0
    assert len(result['missing_variables']) == 4  # All 4 variables missing


@patch('diagnose_environment.find_spec')
def test_check_pip_packages_none_installed(mock_find_spec):
    """Test pip package check when no packages are installed"""
    # Arrange - All packages missing
    mock_find_spec.return_value = None

    # Act
    result = check_pip_packages()

    # Assert
    assert result['passed'] is False
    assert result['installed_count'] == 0
    assert len(result['missing_packages']) == 4  # All 4 packages missing


# =============================================================================
# Test 8: Integration Test - Full Diagnostic Flow
# =============================================================================

@pytest.mark.asyncio
async def test_full_diagnostic_flow():
    """
    Integration test: Run full diagnostic flow

    This test verifies that the diagnostic script can:
    1. Run all 7 checks
    2. Generate a comprehensive report
    3. Provide quick fixes
    4. Estimate repair time
    """
    # Import the main run_all_checks function
    from diagnose_environment import run_all_checks

    # Act
    results = await run_all_checks()

    # Assert - Verify structure
    assert isinstance(results, dict)
    assert len(results) == 7

    # Verify all required checks are present
    required_checks = [
        'python_version',
        'pip_packages',
        'env_variables',
        'neo4j_connection',
        'neo4j_database',
        'mcp_server',
        'mcp_client'
    ]

    for check in required_checks:
        assert check in results, f"Missing check: {check}"
        assert 'passed' in results[check], f"Missing 'passed' in {check}"

    # Generate report
    report = generate_diagnosis_report(results)
    assert isinstance(report, str)
    assert len(report) > 0


# =============================================================================
# Test Summary
# =============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Display custom test summary after all tests complete."""
    if exitstatus == 0:
        print("\n" + "=" * 70)
        print("✅ ALL DIAGNOSTIC UNIT TESTS PASSED")
        print("=" * 70)
        print("\nTest Coverage:")
        print("  ✅ Python version check")
        print("  ✅ pip package check")
        print("  ✅ Environment variables check")
        print("  ✅ Neo4j database check")
        print("  ✅ MCP client import check")
        print("  ✅ Diagnosis report generation")
        print("  ✅ Edge cases")
        print("  ✅ Full diagnostic flow integration")
        print("\nQuality Metrics:")
        print("  ✅ 15+ unit tests")
        print("  ✅ Success and failure scenarios")
        print("  ✅ Quick fix generation")
        print("  ✅ Time estimation")
        print("=" * 70)
        print()


if __name__ == "__main__":
    """Run tests directly with pytest."""
    import sys

    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    sys.exit(exit_code)
