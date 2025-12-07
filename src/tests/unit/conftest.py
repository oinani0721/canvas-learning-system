# -*- coding: utf-8 -*-
"""
Unit Test Configuration - Environment Setup

Sets up environment variables before any imports to avoid
pydantic_settings validation errors during test collection.
"""

import os

# Force set required environment variables BEFORE any src.api imports
# Use direct assignment to override any existing (possibly empty) values
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
os.environ["DEBUG"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["API_V1_PREFIX"] = "/api/v1"
os.environ["PROJECT_NAME"] = "Canvas Learning System Test"

import pytest


@pytest.fixture
def mock_canvas_data():
    """Sample canvas data for testing."""
    return {
        "nodes": [
            {"id": "node1", "type": "text", "text": "Concept 1", "color": "1"},
            {"id": "node2", "type": "text", "text": "Answer 1", "sourceNodeId": "node1", "color": "2"},
            {"id": "node3", "type": "text", "text": "Concept 2", "color": "1"},
            {"id": "node4", "type": "text", "text": "Answer 2", "sourceNodeId": "node3", "color": "1"},
        ],
        "edges": []
    }


@pytest.fixture
def mock_canvas_data_updated():
    """Updated canvas data with color change."""
    return {
        "nodes": [
            {"id": "node1", "type": "text", "text": "Concept 1", "color": "1"},
            {"id": "node2", "type": "text", "text": "Answer 1", "sourceNodeId": "node1", "color": "2"},
            {"id": "node3", "type": "text", "text": "Concept 2", "color": "1"},
            {"id": "node4", "type": "text", "text": "Answer 2", "sourceNodeId": "node3", "color": "2"},  # Changed
        ],
        "edges": []
    }
