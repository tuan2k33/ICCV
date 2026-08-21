import pytest
from unittest.mock import Mock, AsyncMock
from app.modules.auth.repository import AuthRepository


class TestAuthRepository:
    """Test cases for AuthRepository class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.auth_repository = AuthRepository(self.mock_db)
        
        self.sample_user = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "testuser",
            "email": "test@example.com",
            "password": "hashed_password",
            "is_active": True,
            "roles": ["USER", "ADMIN"]
        }

    @pytest.mark.asyncio
    async def test_find_user_by_username_or_email_success(self):
        """Test finding user by username or email successfully."""
        # Arrange
        username = "testuser"
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value=self.sample_user)
        
        # Act
        result = await self.auth_repository.find_user_by_username_or_email(username)
        
        # Assert
        assert result == self.sample_user
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_user_by_username_or_email_not_found(self):
        """Test finding user by username or email when user doesn't exist."""
        # Arrange
        username = "nonexistent"
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value=None)
        
        # Act
        result = await self.auth_repository.find_user_by_username_or_email(username)
        
        # Assert
        assert result is None
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test creating user successfully."""
        # Arrange
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "hashed_password"
        }
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value=self.sample_user)
        
        # Act
        result = await self.auth_repository.create_user(user_data)
        
        # Assert
        assert result == self.sample_user
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_user_true(self):
        """Test checking if user exists when user exists."""
        # Arrange
        username = "existinguser"
        email = "existinguser@example.com"
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value={"exists": True})
        
        # Act
        result = await self.auth_repository.exists_user(username, email)
        
        # Assert
        assert result is True
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_user_false(self):
        """Test checking if user exists when user doesn't exist."""
        # Arrange
        username = "newuser"
        email = "newuser@example.com"
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value={"exists": False})
        
        # Act
        result = await self.auth_repository.exists_user(username, email)
        
        # Assert
        assert result is False
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_user_no_result(self):
        """Test checking if user exists when no result is returned."""
        # Arrange
        username = "newuser"
        email = "newuser@example.com"
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value=None)
        
        # Act
        result = await self.auth_repository.exists_user(username, email)
        
        # Assert
        assert result is False
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_user_by_id_success(self):
        """Test finding user by ID successfully."""
        # Arrange
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value=self.sample_user)
        
        # Act
        result = await self.auth_repository.find_user_by_id(user_id)
        
        # Assert
        assert result == self.sample_user
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_user_by_id_not_found(self):
        """Test finding user by ID when user doesn't exist."""
        # Arrange
        user_id = "nonexistent-id"
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value=None)
        
        # Act
        result = await self.auth_repository.find_user_by_id(user_id)
        
        # Assert
        assert result is None
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_users_success(self):
        """Test getting all users successfully."""
        # Arrange
        skip = 0
        limit = 10
        users_list = [self.sample_user] * 10
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchall = AsyncMock(return_value=users_list)
        
        # Act
        result = await self.auth_repository.get_all_users(skip, limit)
        
        # Assert
        assert result == users_list
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchall.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_users_with_pagination(self):
        """Test getting users with pagination."""
        # Arrange
        skip = 20
        limit = 5
        users_list = [self.sample_user] * 5
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchall = AsyncMock(return_value=users_list)
        
        # Act
        result = await self.auth_repository.get_all_users(skip, limit)
        
        # Assert
        assert result == users_list
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchall.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_users_empty_result(self):
        """Test getting all users when no users exist."""
        # Arrange
        skip = 0
        limit = 10
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchall = AsyncMock(return_value=[])
        
        # Act
        result = await self.auth_repository.get_all_users(skip, limit)
        
        # Assert
        assert result == []
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchall.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_users_success(self):
        """Test counting users successfully."""
        # Arrange
        total_count = 25
        
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value={"count": total_count})
        
        # Act
        result = await self.auth_repository.count_users()
        
        # Assert
        assert result == total_count
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_users_zero(self):
        """Test counting users when no users exist."""
        # Arrange
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value={"count": 0})
        
        # Act
        result = await self.auth_repository.count_users()
        
        # Assert
        assert result == 0
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_users_no_result(self):
        """Test counting users when no result is returned."""
        # Arrange
        self.mock_db.execute = AsyncMock()
        self.mock_db.fetchone = AsyncMock(return_value=None)
        
        # Act
        result = await self.auth_repository.count_users()
        
        # Assert
        assert result == 0
        self.mock_db.execute.assert_called_once()
        self.mock_db.fetchone.assert_called_once()

    def test_auth_repository_initialization(self):
        """Test AuthRepository initialization."""
        # Arrange & Act
        auth_repository = AuthRepository(self.mock_db)
        
        # Assert
        assert auth_repository.db == self.mock_db 