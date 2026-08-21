# Unit Tests for AI-AC Application

This directory contains comprehensive unit tests for the AI-AC FastAPI application.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test fixtures and configuration
├── test_auth_security.py       # Tests for TokenService and CookieService
├── test_auth_service.py        # Tests for AuthService
├── test_auth_repository.py     # Tests for AuthRepository
├── test_task_service.py        # Tests for TaskService
├── test_uploader_service.py    # Tests for MinIOService
├── test_websocket.py           # Tests for ConnectionManager
├── test_utils.py               # Tests for utility functions
├── test_main.py                # Tests for main application
├── requirements-test.txt        # Testing dependencies
└── README.md                   # This file
```

## Test Coverage

The tests cover the following modules:

### 1. Auth Module
- **TokenService**: JWT token generation, validation, and refresh
- **CookieService**: Cookie management and origin validation
- **AuthService**: Authentication business logic
- **AuthRepository**: Database operations for authentication

### 2. Task Module
- **TaskService**: Task management business logic
- **Task assignment, creation, and submission**

### 3. Uploader Module
- **MinIOService**: File upload to MinIO storage
- **File handling and storage operations**

### 4. Infrastructure
- **ConnectionManager**: WebSocket connection management
- **Database**: Connection pool and lifecycle management

### 5. Utilities
- **Password hashing and verification**
- **Response formatting and error handling**

### 6. Main Application
- **FastAPI app configuration**
- **Middleware setup**
- **Route registration**

## Running Tests

### Prerequisites
Install testing dependencies:
```bash
poetry install --with test
```

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_auth_security.py
```

### Run Tests with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Tests with Verbose Output
```bash
pytest -v
```

### Run Only Unit Tests
```bash
pytest -m unit
```

### Run Only Integration Tests
```bash
pytest -m integration
```

## Test Configuration

The tests use the following configuration:

- **pytest.ini**: Main pytest configuration
- **conftest.py**: Shared fixtures and test setup
- **Async support**: Tests use pytest-asyncio for async operations
- **Mocking**: Extensive use of unittest.mock for isolation
- **Coverage**: Built-in coverage reporting

## Test Patterns

### 1. Arrange-Act-Assert (AAA)
All tests follow the AAA pattern:
```python
def test_example():
    # Arrange - Set up test data and mocks
    mock_service = Mock()
    test_data = {"key": "value"}
    
    # Act - Execute the method under test
    result = service.process_data(test_data)
    
    # Assert - Verify the results
    assert result == expected_value
```

### 2. Mocking Strategy
- **External dependencies**: Database, external APIs, file system
- **Async operations**: Proper async mocking with AsyncMock
- **Configuration**: Settings and environment variables

### 3. Test Isolation
- Each test is independent
- No shared state between tests
- Proper cleanup in teardown methods

## Adding New Tests

### 1. Test File Naming
- Test files should be named `test_<module_name>.py`
- Test classes should be named `Test<ClassName>`
- Test methods should be named `test_<method_name>_<scenario>`

### 2. Test Organization
```python
class TestClassName:
    """Test cases for ClassName class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        pass
    
    def test_method_success(self):
        """Test successful method execution."""
        pass
    
    def test_method_failure(self):
        """Test method failure scenario."""
        pass
```

### 3. Async Tests
```python
@pytest.mark.asyncio
async def test_async_method(self):
    """Test async method."""
    result = await service.async_method()
    assert result == expected_value
```

## Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Test Isolation**: Each test should be independent and not affect others
3. **Mock External Dependencies**: Don't rely on external services or databases
4. **Cover Edge Cases**: Test both success and failure scenarios
5. **Assertion Messages**: Provide clear error messages in assertions
6. **Test Documentation**: Document complex test scenarios

## Coverage Goals

- **Line Coverage**: Aim for >90%
- **Branch Coverage**: Aim for >85%
- **Function Coverage**: Aim for >95%

## Continuous Integration

Tests should be run automatically in CI/CD pipelines:
- On every pull request
- Before merging to main branch
- On scheduled intervals

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the app module is in Python path
2. **Async Test Failures**: Use `@pytest.mark.asyncio` decorator
3. **Mock Configuration**: Verify mock setup in test methods
4. **Database Connections**: Use mocked database connections

### Debug Mode
Run tests with debug output:
```bash
pytest -s -v --tb=long
```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain test coverage
4. Update this documentation if needed 