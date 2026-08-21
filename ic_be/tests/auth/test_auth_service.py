import pytest
from unittest.mock import Mock, AsyncMock
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import RegisterSchema
from app.constant.app_status import AppStatus
from app.utils.hasher import hash_password
from app.utils.response import error_exception_handler


class TestAuthService:
    """Test cases for AuthService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user_repository = AsyncMock()
        self.mock_token_service = Mock()
        self.auth_service = AuthService(self.mock_user_repository, self.mock_token_service)
        
        self.sample_user = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password('password123'),
            "is_active": True,
            "roles": ["USER", "ADMIN"]
        }
        
        self.sample_tokens = {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_456"
        }

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        # Arrange
        username = "testuser"
        password = "password123"
        
        self.mock_user_repository.find_user_by_username_or_email.return_value = self.sample_user
        self.mock_token_service.generate_token_pair.return_value = self.sample_tokens
        
        # Act
        result = await self.auth_service.login(username, password)
        
        # Assert
        assert result == self.sample_tokens
        self.mock_user_repository.find_user_by_username_or_email.assert_called_once_with(username)
        self.mock_token_service.generate_token_pair.assert_called_once_with(self.sample_user)

    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        """Test login with non-existent user."""
        # Arrange
        username = "nonexistent"
        password = "password123"
        
        self.mock_user_repository.find_user_by_username_or_email.return_value = None
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await self.auth_service.login(username, password)
        
        assert exc_info.value.status_code == AppStatus.ERROR_LOGIN_INVALID.status_code

    @pytest.mark.asyncio
    async def test_login_invalid_password(self):
        """Test login with invalid password."""
        # Arrange
        username = "testuser"
        password = "wrongpassword"
        
        self.mock_user_repository.find_user_by_username_or_email.return_value = self.sample_user
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await self.auth_service.login(username, password)
        
        assert exc_info.value.status_code == AppStatus.ERROR_LOGIN_INVALID.status_code

    @pytest.mark.asyncio
    async def test_register_success(self):
        """Test successful user registration."""
        # Arrange
        register_data = RegisterSchema(
            username="newuser",
            email="newuser@example.com",
            password="password123"
        )
        
        self.mock_user_repository.exists_user.return_value = False
        self.mock_user_repository.create_user.return_value = self.sample_user
        
        # Act
        result = await self.auth_service.register(register_data)
        
        # Assert
        assert result == self.sample_user
        self.mock_user_repository.exists_user.assert_called_once_with(
            register_data.username, 
            register_data.email
        )
        self.mock_user_repository.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_already_exists(self):
        """Test registration with existing user."""
        # Arrange
        register_data = RegisterSchema(
            username="existinguser",
            email="existinguser@example.com",
            password="password123"
        )
        
        self.mock_user_repository.exists_user.return_value = True
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await self.auth_service.register(register_data)
        
        assert exc_info.value.status_code == AppStatus.ERROR_USER_ALREADY_EXISTS.status_code

    @pytest.mark.asyncio
    async def test_get_all_users_success(self):
        """Test getting all users successfully."""
        # Arrange
        skip = 0
        limit = 10
        total_users = 25
        users_list = [self.sample_user] * 10
        
        self.mock_user_repository.count_users.return_value = total_users
        self.mock_user_repository.get_all_users.return_value = users_list
        
        # Act
        total, users = await self.auth_service.get_all_users(skip, limit)
        
        # Assert
        assert total == total_users
        assert users == users_list
        self.mock_user_repository.count_users.assert_called_once()
        self.mock_user_repository.get_all_users.assert_called_once_with(skip, limit)

    @pytest.mark.asyncio
    async def test_get_all_users_with_pagination(self):
        """Test getting users with pagination."""
        # Arrange
        skip = 20
        limit = 5
        total_users = 25
        users_list = [self.sample_user] * 5
        
        self.mock_user_repository.count_users.return_value = total_users
        self.mock_user_repository.get_all_users.return_value = users_list
        
        # Act
        total, users = await self.auth_service.get_all_users(skip, limit)
        
        # Assert
        assert total == total_users
        assert users == users_list
        self.mock_user_repository.get_all_users.assert_called_once_with(skip, limit)

    @pytest.mark.asyncio
    async def test_get_all_users_empty_result(self):
        """Test getting users when no users exist."""
        # Arrange
        skip = 0
        limit = 10
        
        self.mock_user_repository.count_users.return_value = 0
        self.mock_user_repository.get_all_users.return_value = []
        
        # Act
        total, users = await self.auth_service.get_all_users(skip, limit)
        
        # Assert
        assert total == 0
        assert users == []

    def test_auth_service_initialization(self):
        """Test AuthService initialization."""
        # Arrange & Act
        auth_service = AuthService(self.mock_user_repository, self.mock_token_service)
        
        # Assert
        assert auth_service.user_repository == self.mock_user_repository
        assert auth_service.token_service == self.mock_token_service 