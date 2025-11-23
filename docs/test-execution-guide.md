# Canvas Learning System - Test Execution Guide

**Epic 9 - Canvas System Robustness Enhancement**
**Story 9.6 - Integration Testing and Validation**
**Version**: 1.0
**Last Updated**: 2025-10-28

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Prerequisites](#prerequisites)
4. [Running Tests Locally](#running-tests-locally)
5. [Test Categories](#test-categories)
6. [Continuous Integration](#continuous-integration)
7. [Test Reports](#test-reports)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best practices)

---

## 🎯 Overview

This guide provides comprehensive instructions for executing the Canvas Learning System test suite. The test suite is designed to ensure system reliability, performance, and compatibility across different AI models and environments.

### Test Coverage Goals

- **Unit Tests**: 95% code coverage
- **Integration Tests**: All component interactions
- **Performance Tests**: Benchmark thresholds
- **End-to-End Tests**: Complete user workflows

---

## 🏗️ Test Structure

```
tests/
├── unit/                           # Unit tests
│   ├── test_model_adapter.py       # Model compatibility adapter
│   ├── test_canvas_validator.py    # Canvas validation
│   ├── test_memory_recorder.py     # Memory recording system
│   ├── test_path_manager.py        # Path management
│   └── test_session_monitor.py     # Session monitoring
├── integration/                    # Integration tests
│   ├── test_epic9_integration.py   # Epic 9 feature integration
│   ├── test_canvas_workflow.py     # Canvas workflow tests
│   └── test_model_compatibility.py # Model compatibility
├── performance/                    # Performance tests
│   ├── test_load_performance.py    # Load and stress tests
│   ├── test_memory_usage.py        # Memory usage tests
│   └── test_response_time.py       # Response time tests
├── e2e/                          # End-to-end tests
│   ├── test_full_learning_session.py
│   └── test_multi_model_scenario.py
├── fixtures/                      # Test data
│   ├── canvases/                  # Sample canvas files
│   └── test_data.json             # Test data sets
└── utils/                         # Test utilities
    ├── test_helpers.py
    └── mock_services.py
```

---

## ✅ Prerequisites

### System Requirements

- **Python**: 3.9, 3.10, or 3.11
- **Operating System**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Memory**: Minimum 4GB RAM (8GB recommended for performance tests)
- **Disk Space**: 1GB free space for test artifacts

### Python Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
pip install pytest-benchmark pytest-xdist
pip install memory-profiler psutil
pip install coverage[toml]
```

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd canvas-learning-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

---

## 🚀 Running Tests Locally

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=canvas_utils --cov-report=html

# Run with verbose output
pytest -v
```

### Running Specific Test Categories

#### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific unit test
pytest tests/unit/test_model_adapter.py -v

# Run with coverage
pytest tests/unit/ --cov=canvas_utils --cov-report=term-missing
```

#### Integration Tests
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run Epic 9 integration tests
pytest tests/integration/test_epic9_integration.py -v -s
```

#### Performance Tests
```bash
# Run performance tests
pytest tests/performance/ -v --benchmark-only

# Run specific performance test
pytest tests/performance/test_load_performance.py -v

# Generate benchmark report
pytest tests/performance/ --benchmark-json=benchmark.json
```

#### End-to-End Tests
```bash
# Run E2E tests
pytest tests/e2e/ -v -s

# Run with custom workspace
pytest tests/e2e/ -v --test-workspace=/tmp/test-workspace
```

### Running Tests in Parallel

```bash
# Use all CPU cores
pytest -n auto

# Use specific number of workers
pytest -n 4

# Distribute tests by directory
pytest tests/unit/ tests/integration/ -n auto --dist=loadscope
```

### Filtering Tests

```bash
# Run tests by marker
pytest -m "unit"
pytest -m "integration"
pytest -m "performance"
pytest -m "not slow"

# Run tests by keyword
pytest -k "test_model_adapter"
pytest -k "test_opus41"
pytest -k "performance and load"
```

### Debugging Tests

```bash
# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Run with maximum verbosity
pytest -vv -s
```

---

## 📊 Test Categories

### Unit Tests

**Purpose**: Test individual components in isolation

**Key Features**:
- Mock external dependencies
- Fast execution (< 1 second per test)
- High coverage requirements
- Component boundary testing

**Examples**:
```bash
# Test model detection
pytest tests/unit/test_model_adapter.py::TestModelCompatibilityAdapter::test_detect_model_opus41

# Test canvas validation
pytest tests/unit/test_canvas_validator.py::TestCanvasValidator::test_validate_canvas_structure_valid
```

### Integration Tests

**Purpose**: Test component interactions

**Key Features**:
- Real component interactions
- Database/file system access
- Network calls (with mocking when needed)
- Workflow testing

**Examples**:
```bash
# Test full Opus 4.1 workflow
pytest tests/integration/test_epic9_integration.py::TestEpic9Integration::test_full_opus41_workflow

# Test concurrent operations
pytest tests/integration/test_epic9_integration.py::TestEpic9Integration::test_concurrent_operations
```

### Performance Tests

**Purpose**: Validate performance requirements

**Key Features**:
- Benchmark measurement
- Threshold validation
- Load testing
- Resource monitoring

**Performance Benchmarks**:
- Model detection: < 1ms
- Canvas validation: < 2ms per 100 nodes
- Path generation: < 10ms
- Session recording: < 100ms

**Examples**:
```bash
# Run load test
pytest tests/performance/test_load_performance.py::TestLoadPerformance::test_concurrent_sessions_load

# Generate benchmark comparison
pytest tests/performance/ --benchmark-compare
```

### End-to-End Tests

**Purpose**: Validate complete user workflows

**Key Features**:
- Real user scenarios
- Multiple component coordination
- File system operations
- Time-based operations

**Examples**:
```bash
# Test complete learning session
pytest tests/e2e/test_full_learning_session.py::TestFullLearningSession::test_complete_learning_workflow
```

---

## 🔄 Continuous Integration

### GitHub Actions Workflow

The CI/CD pipeline (`.github/workflows/epic9-tests.yml`) includes:

1. **Matrix Testing**: Multiple Python versions and OS
2. **Parallel Execution**: Tests run in parallel across environments
3. **Performance Monitoring**: Automated benchmark comparisons
4. **Security Scanning**: Dependency and code security checks
5. **Artifact Management**: Test results and reports storage

### Running Tests in CI

```yaml
# Trigger CI manually
gh workflow run epic9-tests.yml

# Trigger with parameters
gh workflow run epic9-tests.yml \
  --field test_type=performance \
  --field python_version=3.10
```

### CI Environment Variables

```bash
# Configure test environment
export PYTHONUNBUFFERED=1
export PYTEST_ADDOPTS="--strict-markers --strict-config"
export TEST_WORKSPACE=/tmp/canvas-tests
```

---

## 📈 Test Reports

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=canvas_utils --cov-report=html

# View report
open htmlcov/index.html
```

### Benchmark Report

```bash
# Generate benchmark report
pytest tests/performance/ --benchmark-json=benchmark.json

# Compare with previous results
pytest tests/performance/ --benchmark-compare=benchmark-old.json
```

### JUnit XML Report

```bash
# Generate JUnit XML for CI systems
pytest --junit-xml=test-results.xml

# Generate separate reports per test type
pytest tests/unit/ --junit-xml=unit-tests.xml
pytest tests/integration/ --junit-xml=integration-tests.xml
```

### Custom Test Reports

```python
# Create custom test reporter
import json
import pytest

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        # Custom report logic
        test_result = {
            "name": item.name,
            "status": "passed" if report.passed else "failed",
            "duration": report.duration,
            "markers": [m.name for m in item.iter_markers()]
        }

        with open("custom-test-results.json", "a") as f:
            json.dump(test_result, f)
            f.write("\n")
```

---

## 🔧 Troubleshooting

### Common Issues

#### Test Import Errors

```bash
# Error: ModuleNotFoundError
# Solution: Check Python path and installation
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pip install -e .
```

#### Async Test Failures

```bash
# Error: RuntimeError: Event loop is closed
# Solution: Use proper async fixtures
@pytest.fixture
async def async_fixture():
    async with SomeAsyncResource() as resource:
        yield resource
```

#### Permission Errors

```bash
# Error: Permission denied
# Solution: Check file permissions or use temporary directory
pytest --basetemp=/tmp/pytest-tmp
```

#### Performance Test Failures

```bash
# Error: Performance threshold exceeded
# Solution: Check system load or adjust thresholds
# Run with higher threshold
pytest tests/performance/ --benchmark-min-rounds=1
```

### Debugging Failed Tests

```bash
# Run with debugging output
pytest -vv -s --tb=long

# Run specific test with pdb
pytest tests/unit/test_model_adapter.py::test_detect_model -x --pdb

# Print captured output
pytest -s --capture=no
```

### Memory Issues

```bash
# Monitor memory usage
pytest --memprof

# Limit test workers
pytest -n 1  # Reduce parallelism

# Use memory profiler
python -m memory_profiler pytest tests/
```

### Test Isolation Issues

```bash
# Clean up test data
pytest --cache-clear

# Use fresh database
pytest --create-db

# Reset test environment
pytest --reset-db
```

---

## 🎯 Best Practices

### Writing Tests

1. **Follow Naming Conventions**
   ```python
   def test_component_function_scenario():
       """Test: component_function should handle scenario correctly"""
       pass
   ```

2. **Use Descriptive Assertions**
   ```python
   assert result.is_valid, f"Validation failed: {result.errors}"
   assert len(nodes) == expected, f"Expected {expected} nodes, got {len(nodes)}"
   ```

3. **Organize Tests with Fixtures**
   ```python
   @pytest.fixture
   def sample_canvas():
       return {"nodes": [], "edges": []}

   def test_canvas_validation(sample_canvas):
       validator = CanvasValidator()
       result = validator.validate_canvas_structure(sample_canvas)
       assert result.is_valid
   ```

4. **Mock External Dependencies**
   ```python
   @patch('canvas_utils.model_adapter.mcp__graphiti_memory__add_memory')
   async def test_memory_recording(mock_add_memory):
       mock_add_memory.return_value = {"success": True}
       # Test logic
   ```

5. **Parametrize Tests**
   ```python
   @pytest.mark.parametrize("model,expected", [
       ("opus-4.1", True),
       ("sonnet-3.5", True),
       ("unknown", False)
   ])
   def test_model_support(model, expected):
       assert model_supports(model) == expected
   ```

### Test Organization

1. **Group Related Tests**
   ```python
   class TestModelCompatibilityAdapter:
       """Tests for ModelCompatibilityAdapter"""

       def test_initialization(self):
           pass

       def test_model_detection(self):
           pass
   ```

2. **Use Markers for Test Types**
   ```python
   @pytest.mark.unit
   @pytest.mark.asyncio
   async def test_async_function():
       pass

   @pytest.mark.performance
   def test_performance():
       pass
   ```

3. **Document Test Scenarios**
   ```python
   def test_canvas_validation_with_large_dataset():
       """
       Test: Canvas validator should handle large datasets efficiently

       Given: A canvas with 1000 nodes
       When: Validating the canvas structure
       Then: Validation should complete within 1 second
       """
       pass
   ```

### Performance Testing

1. **Use Benchmark Fixtures**
   ```python
   @pytest.mark.benchmark
   def test_model_detection_performance(benchmark):
       result = benchmark(detect_model, test_response)
       assert result == "opus-4.1"
   ```

2. **Monitor Resources**
   ```python
   def test_memory_usage():
       initial_memory = psutil.Process().memory_info().rss
       # Run test
       final_memory = psutil.Process().memory_info().rss
       assert final_memory - initial_memory < 50 * 1024 * 1024  # 50MB
   ```

3. **Set Realistic Thresholds**
   ```python
   @pytest.mark.performance
   def test_response_time():
       start = time.time()
       result = function_under_test()
       duration = time.time() - start
       assert duration < 0.1, f"Response time {duration}s exceeds threshold"
   ```

---

## 📝 Test Checklist

Before committing code, ensure:

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Code coverage ≥ 95%
- [ ] Performance benchmarks meet thresholds
- [ ] No new security vulnerabilities
- [ ] Tests are properly documented
- [ ] Fixtures are cleaned up
- [ ] No hardcoded paths or credentials
- [ ] Tests run on all supported Python versions

---

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Asyncio Plugin](https://pytest-asyncio.readthedocs.io/)
- [Pytest Benchmark](https://pytest-benchmark.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## 🤝 Contributing

When contributing new tests:

1. Follow the existing test structure
2. Add appropriate documentation
3. Include performance benchmarks if relevant
4. Update this guide if adding new test types
5. Ensure tests are maintainable and readable

---

**Document Status**: ✅ Complete
**Review Date**: 2025-10-28
**Next Review**: 2025-11-28