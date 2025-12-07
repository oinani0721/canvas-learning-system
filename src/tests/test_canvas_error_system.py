#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Canvas Error System - ErrorSeverity enum and related functionality
Tests for Story 8.1: 修复ErrorSeverity枚举缺失INFO属性
"""
import os
import sys

import pytest

# Add the parent directory to the path to import canvas_error_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_error_system import CanvasError, ErrorCategory, ErrorSeverity


class TestErrorSeverityEnum:
    """Test ErrorSeverity enum functionality"""

    def test_all_error_severity_levels_exist(self):
        """Test that all required error severity levels exist"""
        # Test all error levels are available
        assert ErrorSeverity.LOW is not None
        assert ErrorSeverity.MEDIUM is not None
        assert ErrorSeverity.HIGH is not None
        assert ErrorSeverity.CRITICAL is not None
        assert ErrorSeverity.INFO is not None  # This is the fix for Story 8.1

    def test_error_severity_values(self):
        """Test that error severity enum values are correct"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
        assert ErrorSeverity.INFO.value == "info"  # This is the fix for Story 8.1

    def test_error_severity_comparison(self):
        """Test that error severity levels can be compared"""
        assert ErrorSeverity.LOW == ErrorSeverity.LOW
        assert ErrorSeverity.MEDIUM == ErrorSeverity.MEDIUM
        assert ErrorSeverity.HIGH == ErrorSeverity.HIGH
        assert ErrorSeverity.CRITICAL == ErrorSeverity.CRITICAL
        assert ErrorSeverity.INFO == ErrorSeverity.INFO

        assert ErrorSeverity.LOW != ErrorSeverity.MEDIUM
        assert ErrorSeverity.INFO != ErrorSeverity.LOW

    def test_error_severity_iteration(self):
        """Test that all error severity levels can be iterated"""
        all_levels = list(ErrorSeverity)
        expected_levels = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL, ErrorSeverity.INFO]

        assert len(all_levels) == 5  # Should have 5 levels after the fix
        for level in expected_levels:
            assert level in all_levels

    def test_error_severity_string_representation(self):
        """Test string representation of error severity levels"""
        assert str(ErrorSeverity.LOW) == "ErrorSeverity.LOW"
        assert str(ErrorSeverity.MEDIUM) == "ErrorSeverity.MEDIUM"
        assert str(ErrorSeverity.HIGH) == "ErrorSeverity.HIGH"
        assert str(ErrorSeverity.CRITICAL) == "ErrorSeverity.CRITICAL"
        assert str(ErrorSeverity.INFO) == "ErrorSeverity.INFO"

    def test_error_severity_usage_with_canvas_error(self):
        """Test that ErrorSeverity.INFO can be used in CanvasError"""
        error_record = CanvasError(
            error_id="test-001",
            timestamp="2025-10-21T10:00:00Z",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.INFO,  # This should work after the fix
            error_type="Test Info",
            error_message="This is a test info message",
            context={"test": True}
        )

        assert error_record.severity == ErrorSeverity.INFO
        assert error_record.severity.value == "info"

    def test_error_severity_backward_compatibility(self):
        """Test that existing error severity levels still work (backward compatibility)"""
        # Test that all existing functionality still works
        error_record = CanvasError(
            error_id="test-compat-001",
            timestamp="2025-10-21T10:00:00Z",
            category=ErrorCategory.CANVAS_OPERATION,
            severity=ErrorSeverity.HIGH,  # Existing level
            error_type="Canvas Error",
            error_message="Canvas operation failed",
            context={"operation": "read"}
        )

        assert error_record.severity == ErrorSeverity.HIGH
        assert error_record.severity.value == "high"


class TestErrorSeverityIntegration:
    """Test ErrorSeverity integration with other system components"""

    def test_error_severity_with_error_category(self):
        """Test ErrorSeverity works correctly with ErrorCategory"""
        test_combinations = [
            (ErrorSeverity.INFO, ErrorCategory.SYSTEM),
            (ErrorSeverity.LOW, ErrorCategory.USER_INPUT),
            (ErrorSeverity.MEDIUM, ErrorCategory.VALIDATION),
            (ErrorSeverity.HIGH, ErrorCategory.CANVAS_OPERATION),
            (ErrorSeverity.CRITICAL, ErrorCategory.MEMORY_SYSTEM),
        ]

        for severity, category in test_combinations:
            error_record = CanvasError(
                error_id=f"test-{severity.value}-{category.value}",
                timestamp="2025-10-21T10:00:00Z",
                category=category,
                severity=severity,
                error_type="Test Error",
                error_message=f"Test {severity.value} error in {category.value}",
                context={}
            )

            assert error_record.severity == severity
            assert error_record.category == category

    def test_all_five_error_levels_complete_coverage(self):
        """Test that we have complete coverage of all 5 error levels"""
        expected_levels = {
            "low": ErrorSeverity.LOW,
            "medium": ErrorSeverity.MEDIUM,
            "high": ErrorSeverity.HIGH,
            "critical": ErrorSeverity.CRITICAL,
            "info": ErrorSeverity.INFO
        }

        actual_levels = {level.value: level for level in ErrorSeverity}

        assert expected_levels == actual_levels
        assert len(actual_levels) == 5  # Story 8.1 ensures we have 5 levels


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
