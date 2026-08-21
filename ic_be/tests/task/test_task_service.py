import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock

import pytest

from app.modules.task.schemas import TaskCreateSchema
from app.modules.task.service import TaskService


class TestTaskService:
    """Test cases for TaskService class."""

    def setup_method(self, method):
        """Set up test fixtures."""
        self.mock_task_repository = AsyncMock()
        self.mock_websocket = AsyncMock()
        self.task_service = TaskService(self.mock_task_repository, self.mock_websocket)
        
        self.sample_task = {
            "id": 1,
            "title": "Test Task",
            "description": "Test Description",
            "user_assign": 123,
            "version": 1,
            "status": "ASSIGNED"
        }
        
        self.sample_task_data = TaskCreateSchema(
            name="Sample Task",
            images=["image1.png", "image2.png"],
            video="sample_video.mp4"
        )

    @pytest.mark.asyncio
    async def test_my_tasks_success(self):
        """Test getting user's tasks successfully."""
        # Arrange
        user_id = 123
        self.mock_task_repository.find_task_by_user.return_value = self.sample_task
        
        # Act
        result = await self.task_service.my_tasks(user_id)
        
        # Assert
        assert result == self.sample_task
        self.mock_task_repository.find_task_by_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_my_tasks_no_tasks(self):
        """Test getting user's tasks when no tasks exist."""
        # Arrange
        user_id = 123
        self.mock_task_repository.find_task_by_user.return_value = None
        
        # Act
        result = await self.task_service.my_tasks(user_id)
        
        # Assert
        assert result is None
        self.mock_task_repository.find_task_by_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_unassing_task_with_task(self):
        """Test unassigning task when user has a task."""
        # Arrange
        user_id = 123
        self.mock_task_repository.find_task_by_user.return_value = self.sample_task
        self.mock_task_repository.update_user_assign = AsyncMock()
        self.mock_websocket.broadcast = AsyncMock()
        
        # Act
        await self.task_service.unassing_task(user_id)
        
        # Assert
        self.mock_task_repository.find_task_by_user.assert_called_once_with(user_id)
        self.mock_task_repository.update_user_assign.assert_called_once()
        self.mock_websocket.broadcast.assert_called_once_with({'id': self.sample_task['id']})

    @pytest.mark.asyncio
    async def test_unassing_task_no_task(self):
        """Test unassigning task when user has no task."""
        # Arrange
        user_id = 123
        self.mock_task_repository.find_task_by_user.return_value = None
        self.mock_task_repository.update_user_assign = AsyncMock()
        self.mock_websocket.broadcast = AsyncMock()
        
        # Act
        await self.task_service.unassing_task(user_id)
        
        # Assert
        self.mock_task_repository.find_task_by_user.assert_called_once_with(user_id)
        self.mock_task_repository.update_user_assign.assert_not_called()
        self.mock_websocket.broadcast.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_task_success(self):
        """Test creating task successfully."""
        # Arrange
        self.mock_task_repository.create_task = AsyncMock(return_value=self.sample_task)
        self.mock_websocket.broadcast = AsyncMock()
        
        # Act
        result = await self.task_service.create_task(self.sample_task_data)
        
        # Assert
        assert result == {"message": "Task created successfully."}
        self.mock_task_repository.create_task.assert_called_once_with(self.sample_task_data.__dict__)
        self.mock_websocket.broadcast.assert_called_once_with(self.sample_task)

    @pytest.mark.asyncio
    async def test_assign_task_user_has_existing_task(self):
        """Test assigning task when user already has a task."""
        # Arrange
        user_id = 123
        self.mock_task_repository.find_task_by_user.return_value = self.sample_task
        self.mock_task_repository.update_user_assign = AsyncMock(return_value=1)
        
        # Act
        result = await self.task_service.assign_task(user_id)
        
        # Assert
        assert result == self.sample_task
        self.mock_task_repository.find_task_by_user.assert_called_once_with(user_id)
        self.mock_task_repository.find_task_not_assigned.assert_not_called()
        self.mock_task_repository.update_user_assign.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_task_user_no_existing_task(self):
        """Test assigning task when user has no existing task."""
        # Arrange
        user_id = 123
        self.mock_task_repository.find_task_by_user.return_value = None
        self.mock_task_repository.find_task_not_assigned.return_value = self.sample_task
        self.mock_task_repository.update_user_assign = AsyncMock(return_value=1)
        
        # Act
        result = await self.task_service.assign_task(user_id)
        
        # Assert
        assert result == self.sample_task
        self.mock_task_repository.find_task_by_user.assert_called_once_with(user_id)
        self.mock_task_repository.find_task_not_assigned.assert_called_once()
        self.mock_task_repository.update_user_assign.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_task_no_available_task(self):
        """Test assigning task when no tasks are available."""
        # Arrange
        user_id = 123
        self.mock_task_repository.find_task_by_user.return_value = None
        self.mock_task_repository.find_task_not_assigned.return_value = None
        
        # Act
        result = await self.task_service.assign_task(user_id)
        
        # Assert
        assert result == {"message": "Task is None."}
        self.mock_task_repository.find_task_by_user.assert_called_once_with(user_id)
        self.mock_task_repository.find_task_not_assigned.assert_called_once()
        self.mock_task_repository.update_user_assign.assert_not_called()

    @pytest.mark.asyncio
    async def test_assign_task_update_failed(self):
        """Test assigning task when update fails."""
        # Arrange
        user_id = 123
        self.mock_task_repository.find_task_by_user.return_value = None
        self.mock_task_repository.find_task_not_assigned.return_value = self.sample_task
        self.mock_task_repository.update_user_assign = AsyncMock(return_value=0)
        
        # Act
        result = await self.task_service.assign_task(user_id)
        
        # Assert
        assert result == {"message": "Task is None."}
        self.mock_task_repository.update_user_assign.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_task_success(self):
        """Test submitting task result successfully."""
        # Arrange
        task_id = 1
        result_data = {"score": 95, "feedback": "Great work!"}
        user_assign = 123
        
        self.mock_task_repository.update_task_result = AsyncMock(return_value=True)
        
        # Act
        result = await self.task_service.submit_task(task_id, result_data, user_assign)
        
        # Assert
        assert result is True
        self.mock_task_repository.update_task_result.assert_called_once_with(
            task_id, 
            json.dumps(result_data), 
            user_assign
        )

    def test_task_service_initialization(self):
        """Test TaskService initialization."""
        # Arrange & Act
        task_service = TaskService(self.mock_task_repository, self.mock_websocket)
        
        # Assert
        assert task_service.task_repository == self.mock_task_repository
        assert task_service.service_websocket == self.mock_websocket

    @pytest.mark.asyncio
    async def test_assign_task_time_assignment_calculation(self):
        """Test that task assignment time is calculated correctly (3 minutes from now)."""
        # Arrange
        user_id = 123
        self.mock_task_repository.find_task_by_user.return_value = None
        self.mock_task_repository.find_task_not_assigned.return_value = self.sample_task
        self.mock_task_repository.update_user_assign = AsyncMock(return_value=1)
        
        # Act
        await self.task_service.assign_task(user_id)
        
        # Assert
        call_args = self.mock_task_repository.update_user_assign.call_args
        time_assign = call_args[0][2]  # Third argument is time_assign
        
        # Check that time_assign is approximately 3 minutes from now
        now = datetime.now(tz=timezone.utc)
        expected_time = now + timedelta(minutes=3)
        
        # Allow for small time differences due to test execution
        time_diff = abs((time_assign - expected_time).total_seconds())
        assert time_diff < 1  # Less than 1 second difference 