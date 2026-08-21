import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from app.main import app
from app.core.setting import settings
from app.modules.auth.security import TokenService
from app.modules.auth.service import AuthService
from app.modules.auth.repository import AuthRepository


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database cursor."""
    mock_cursor = AsyncMock()
    mock_cursor.execute = AsyncMock()
    mock_cursor.fetchone = AsyncMock()
    mock_cursor.fetchall = AsyncMock()
    return mock_cursor


@pytest.fixture
def mock_token_service():
    """Mock token service."""
    return Mock(spec=TokenService)


@pytest.fixture
def mock_auth_repository(mock_db):
    """Mock auth repository."""
    return Mock(spec=AuthRepository)


@pytest.fixture
def mock_auth_service(mock_auth_repository, mock_token_service):
    """Mock auth service."""
    return Mock(spec=AuthService)


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "testuser",
        "email": "test@example.com",
        "password": "hashed_password",
        "is_active": True,
        "roles": ["USER", "ADMIN"]
    }


@pytest.fixture
def sample_token_payload():
    """Sample JWT token payload for testing."""
    return {
        "sub": "123e4567-e89b-12d3-a456-426614174000",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["USER", "ADMIN"],
        "iat": 1640995200,
        "jti": "token_id",
        "exp": 1640998800
    }


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return {
        "JWT_SECRET_KEY": "test_secret_key",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRES_IN_MINUTES": 60,
        "REFRESH_TOKEN_EXPIRES_IN_DAYS": 7,
        "ALLOW_ORIGINS": ["http://localhost:3000", "http://localhost:8000"]
    } 