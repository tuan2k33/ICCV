import pytest
import json
from unittest.mock import Mock, AsyncMock
from fastapi import WebSocket
from app.infra.websocket import ConnectionManager


class TestConnectionManager:
    """Test cases for ConnectionManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.connection_manager = ConnectionManager()
        self.mock_websocket1 = Mock(spec=WebSocket)
        self.mock_websocket2 = Mock(spec=WebSocket)
        self.mock_websocket3 = Mock(spec=WebSocket)
        
        # Mock the async methods
        self.mock_websocket1.accept = AsyncMock()
        self.mock_websocket2.accept = AsyncMock()
        self.mock_websocket3.accept = AsyncMock()

    @pytest.mark.asyncio
    async def test_connect_new_user(self):
        """Test connecting a new user."""
        # Arrange
        user_id = "user123"
        
        # Act
        await self.connection_manager.connect(self.mock_websocket1, user_id)
        
        # Assert
        self.mock_websocket1.accept.assert_called_once()
        assert user_id in self.connection_manager.connections
        assert self.mock_websocket1 in self.connection_manager.connections[user_id]
        assert len(self.connection_manager.connections[user_id]) == 1

    @pytest.mark.asyncio
    async def test_connect_existing_user(self):
        """Test connecting an existing user with additional websocket."""
        # Arrange
        user_id = "user123"
        await self.connection_manager.connect(self.mock_websocket1, user_id)
        
        # Act
        await self.connection_manager.connect(self.mock_websocket2, user_id)
        
        # Assert
        assert user_id in self.connection_manager.connections
        assert self.mock_websocket1 in self.connection_manager.connections[user_id]
        assert self.mock_websocket2 in self.connection_manager.connections[user_id]
        assert len(self.connection_manager.connections[user_id]) == 2

    def test_disconnect_user_with_multiple_connections(self):
        """Test disconnecting a user with multiple websocket connections."""
        # Arrange
        user_id = "user123"
        # Use asyncio.run to handle the async connect method
        import asyncio
        asyncio.run(self.connection_manager.connect(self.mock_websocket1, user_id))
        asyncio.run(self.connection_manager.connect(self.mock_websocket2, user_id))
        
        # Act
        self.connection_manager.disconnect(self.mock_websocket1)
        
        # Assert
        assert user_id in self.connection_manager.connections
        assert self.mock_websocket1 not in self.connection_manager.connections[user_id]
        assert self.mock_websocket2 in self.connection_manager.connections[user_id]
        assert len(self.connection_manager.connections[user_id]) == 1

    def test_disconnect_user_last_connection(self):
        """Test disconnecting a user's last websocket connection."""
        # Arrange
        user_id = "user123"
        import asyncio
        asyncio.run(self.connection_manager.connect(self.mock_websocket1, user_id))
        
        # Act
        self.connection_manager.disconnect(self.mock_websocket1)
        
        # Assert
        assert user_id not in self.connection_manager.connections

    def test_disconnect_nonexistent_websocket(self):
        """Test disconnecting a websocket that doesn't exist."""
        # Arrange
        user_id = "user123"
        import asyncio
        asyncio.run(self.connection_manager.connect(self.mock_websocket1, user_id))
        initial_connections = self.connection_manager.count_all_connections()
        
        # Act
        self.connection_manager.disconnect(self.mock_websocket2)  # Non-existent websocket
        
        # Assert
        assert self.connection_manager.count_all_connections() == initial_connections

    @pytest.mark.asyncio
    async def test_send_to_user_success(self):
        """Test sending message to user successfully."""
        # Arrange
        user_id = "user123"
        message = {"type": "notification", "content": "Hello!"}
        await self.connection_manager.connect(self.mock_websocket1, user_id)
        
        # Mock send_text method
        self.mock_websocket1.send_text = AsyncMock()
        
        # Act
        result = await self.connection_manager.send_to_user(user_id, message)
        
        # Assert
        assert result is True
        self.mock_websocket1.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_send_to_user_not_found(self):
        """Test sending message to non-existent user."""
        # Arrange
        user_id = "nonexistent"
        message = {"type": "notification", "content": "Hello!"}
        
        # Act
        result = await self.connection_manager.send_to_user(user_id, message)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_user_websocket_error(self):
        """Test sending message when websocket raises an error."""
        # Arrange
        user_id = "user123"
        message = {"type": "notification", "content": "Hello!"}
        await self.connection_manager.connect(self.mock_websocket1, user_id)
        
        # Mock send_text to raise an error
        self.mock_websocket1.send_text = AsyncMock(side_effect=Exception("Connection lost"))
        
        # Act
        result = await self.connection_manager.send_to_user(user_id, message)
        
        # Assert
        assert result is True
        # The websocket should be disconnected due to the error
        assert user_id not in self.connection_manager.connections

    @pytest.mark.asyncio
    async def test_broadcast_success(self):
        """Test broadcasting message to all users successfully."""
        # Arrange
        user1_id = "user1"
        user2_id = "user2"
        message = {"type": "broadcast", "content": "System message"}
        
        await self.connection_manager.connect(self.mock_websocket1, user1_id)
        await self.connection_manager.connect(self.mock_websocket2, user2_id)
        
        # Mock send_text methods
        self.mock_websocket1.send_text = AsyncMock()
        self.mock_websocket2.send_text = AsyncMock()
        
        # Act
        await self.connection_manager.broadcast(message)
        
        # Assert
        self.mock_websocket1.send_text.assert_called_once_with(json.dumps(message))
        self.mock_websocket2.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_broadcast_with_websocket_error(self):
        """Test broadcasting when some websockets raise errors."""
        # Arrange
        user1_id = "user1"
        user2_id = "user2"
        message = {"type": "broadcast", "content": "System message"}
        
        await self.connection_manager.connect(self.mock_websocket1, user1_id)
        await self.connection_manager.connect(self.mock_websocket2, user2_id)
        
        # Mock send_text methods - one succeeds, one fails
        self.mock_websocket1.send_text = AsyncMock()
        self.mock_websocket2.send_text = AsyncMock(side_effect=Exception("Connection lost"))
        
        # Act
        await self.connection_manager.broadcast(message)
        
        # Assert
        self.mock_websocket1.send_text.assert_called_once_with(json.dumps(message))
        self.mock_websocket2.send_text.assert_called_once_with(json.dumps(message))
        # The failing websocket should be disconnected
        assert user2_id not in self.connection_manager.connections

    @pytest.mark.asyncio
    async def test_push_task_to_users(self):
        """Test pushing task to specific users."""
        # Arrange
        users = ["user1", "user2"]
        message = {"type": "task", "content": "New task assigned"}
        
        await self.connection_manager.connect(self.mock_websocket1, "user1")
        await self.connection_manager.connect(self.mock_websocket2, "user2")
        
        # Mock send_text methods
        self.mock_websocket1.send_text = AsyncMock()
        self.mock_websocket2.send_text = AsyncMock()
        
        # Act
        await self.connection_manager.push_task_to_users(users, message)
        
        # Assert
        self.mock_websocket1.send_text.assert_called_once_with(json.dumps(message))
        self.mock_websocket2.send_text.assert_called_once_with(json.dumps(message))

    def test_get_online_users(self):
        """Test getting list of online users."""
        # Arrange
        user1_id = "user1"
        user2_id = "user2"
        
        import asyncio
        asyncio.run(self.connection_manager.connect(self.mock_websocket1, user1_id))
        asyncio.run(self.connection_manager.connect(self.mock_websocket2, user2_id))
        
        # Act
        online_users = self.connection_manager.get_online_users()
        
        # Assert
        assert len(online_users) == 2
        assert user1_id in online_users
        assert user2_id in online_users

    def test_count_all_connections(self):
        """Test counting total number of connections."""
        # Arrange
        user1_id = "user1"
        user2_id = "user2"
        
        import asyncio
        asyncio.run(self.connection_manager.connect(self.mock_websocket1, user1_id))
        asyncio.run(self.connection_manager.connect(self.mock_websocket2, user1_id))  # Same user, 2 connections
        asyncio.run(self.connection_manager.connect(self.mock_websocket3, user2_id))
        
        # Act
        total_connections = self.connection_manager.count_all_connections()
        
        # Assert
        assert total_connections == 3

    def test_count_all_connections_empty(self):
        """Test counting connections when no users are connected."""
        # Act
        total_connections = self.connection_manager.count_all_connections()
        
        # Assert
        assert total_connections == 0

    def test_connection_manager_initialization(self):
        """Test ConnectionManager initialization."""
        # Arrange & Act
        connection_manager = ConnectionManager()
        
        # Assert
        assert isinstance(connection_manager.connections, dict)
        assert len(connection_manager.connections) == 0 