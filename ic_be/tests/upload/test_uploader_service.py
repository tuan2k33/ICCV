import pytest
import io
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from minio import Minio
from minio.error import S3Error
from app.modules.uploader.service import MinIOService
from app.core.minio_config import MinIOConfig


class TestMinIOService:
    """Test cases for MinIOService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=MinIOConfig)
        self.mock_config.endpoint = "localhost:9000"
        self.mock_config.public_endpoint = "localhost:9000"
        self.mock_config.access_key = "test_access_key"
        self.mock_config.secret_key = "test_secret_key"
        self.mock_config.secure = False
        self.mock_config.public_secure = False
        self.mock_config.bucket_name = "test-bucket"
        
        self.sample_file_data = io.BytesIO(b"test file content")
        self.sample_filename = "test_video.mp4"

    @patch('app.modules.uploader.service.Minio')
    def test_create_client_success(self, mock_minio_class):
        """Test successful MinIO client creation."""
        # Arrange
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        
        # Act
        service = MinIOService(self.mock_config)
        
        # Assert
        mock_minio_class.assert_called_once_with(
            self.mock_config.endpoint,
            access_key=self.mock_config.access_key,
            secret_key=self.mock_config.secret_key,
            secure=self.mock_config.secure
        )
        assert service.client == mock_minio_instance

    @patch('app.modules.uploader.service.Minio')
    def test_create_client_failure(self, mock_minio_class):
        """Test MinIO client creation failure."""
        # Arrange
        mock_minio_class.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Connection failed"):
            MinIOService(self.mock_config)

    @patch('app.modules.uploader.service.Minio')
    def test_create_public_client_different_endpoint(self, mock_minio_class):
        """Test public client creation when endpoints are different."""
        # Arrange
        self.mock_config.public_endpoint = "public.localhost:9000"
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        
        # Act
        _ = MinIOService(self.mock_config)
        
        # Assert
        # Should be called twice - once for internal client, once for public
        assert mock_minio_class.call_count == 2

    @patch('app.modules.uploader.service.Minio')
    def test_create_public_client_same_endpoint(self, mock_minio_class):
        """Test public client creation when endpoints are the same."""
        # Arrange
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        
        # Act
        service = MinIOService(self.mock_config)
        
        # Assert
        # Should be called once since endpoints are the same
        assert mock_minio_class.call_count == 1
        assert service.public_client == service.client

    @patch('app.modules.uploader.service.Minio')
    def test_create_bucket_if_not_exists_bucket_exists(self, mock_minio_class):
        """Test bucket creation when bucket already exists."""
        # Arrange
        mock_minio_instance = Mock()
        mock_minio_instance.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_minio_instance
        
        # Act
        _ = MinIOService(self.mock_config)
        
        # Assert
        mock_minio_instance.bucket_exists.assert_called_once_with(self.mock_config.bucket_name)
        mock_minio_instance.make_bucket.assert_not_called()

    @patch('app.modules.uploader.service.Minio')
    def test_create_bucket_if_not_exists_bucket_not_exists(self, mock_minio_class):
        """Test bucket creation when bucket doesn't exist."""
        # Arrange
        mock_minio_instance = Mock()
        mock_minio_instance.bucket_exists.return_value = False
        mock_minio_class.return_value = mock_minio_instance
        
        # Act
        _ = MinIOService(self.mock_config)
        
        # Assert
        mock_minio_instance.bucket_exists.assert_called_once_with(self.mock_config.bucket_name)
        mock_minio_instance.make_bucket.assert_called_once_with(self.mock_config.bucket_name)

    @patch('app.modules.uploader.service.Minio')
    def test_create_bucket_if_not_exists_s3_error(self, mock_minio_class):
        """Test bucket creation when S3Error occurs."""
        # Arrange
        mock_minio_instance = Mock()
        fake_response = Mock()
        fake_response.status = 500
        fake_response.reason = "Internal Server Error"
        fake_response.getheader = lambda *_args, **_kwargs: None

        mock_minio_instance.bucket_exists.side_effect = S3Error(
            code="InternalError",
            message="Bucket error",
            resource="/my-bucket",
            request_id="req-123",
            host_id="host-abc",
            response=fake_response,
        )
        mock_minio_class.return_value = mock_minio_instance
        
        # Act & Assert
        with pytest.raises(S3Error, match="Bucket error"):
            MinIOService(self.mock_config)

    @patch('app.modules.uploader.service.Minio')
    def test_generate_unique_filename(self, mock_minio_class):
        """Test unique filename generation."""
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        # Arrange
        service = MinIOService(self.mock_config)
        original_filename = "test_video.mp4"
        file_type = "videos"
        
        # Act
        result = service._generate_unique_filename(original_filename, file_type)
        
        # Assert
        assert result.startswith(datetime.now().strftime('%Y%m%d'))
        assert "/videos/" in result
        assert result.endswith(".mp4")
        assert len(result.split("/")[-1].replace(".mp4", "")) == 32  # UUID hex length

    @patch('app.modules.uploader.service.Minio')
    def test_upload_file_success(self, mock_minio_class):
        """Test successful file upload."""
        # Arrange
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        
        service = MinIOService(self.mock_config)
        
        # Act
        result = service.upload_file(
            self.sample_file_data,
            self.sample_filename,
            "videos"
        )
        
        # Assert
        assert isinstance(result, str)
        mock_minio_instance.put_object.assert_called_once()
        call_args = mock_minio_instance.put_object.call_args
        assert call_args[1]['bucket_name'] == self.mock_config.bucket_name
        assert call_args[1]['object_name'].startswith(datetime.now().strftime('%Y%m%d'))
        assert call_args[1]['object_name'].endswith('.mp4')

    @patch('app.modules.uploader.service.Minio')
    def test_upload_file_without_unique_name(self, mock_minio_class):
        """Test file upload without unique name generation."""
        # Arrange
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        
        service = MinIOService(self.mock_config)
        
        # Act
        _ = service.upload_file(
            self.sample_file_data,
            self.sample_filename,
            "videos",
            unique_name=False
        )
        
        # Assert
        mock_minio_instance.put_object.assert_called_once()
        call_args = mock_minio_instance.put_object.call_args
        assert call_args[1]['object_name'] == self.sample_filename

    @patch('app.modules.uploader.service.Minio')
    def test_upload_file_with_content_type(self, mock_minio_class):
        """Test file upload with specified content type."""
        # Arrange
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        
        service = MinIOService(self.mock_config)
        content_type = "video/mp4"
        
        # Act
        _ = service.upload_file(
            self.sample_file_data,
            self.sample_filename,
            "videos",
            content_type=content_type
        )
        
        # Assert
        mock_minio_instance.put_object.assert_called_once()
        call_args = mock_minio_instance.put_object.call_args
        assert call_args[1]['content_type'] == content_type

    @patch('app.modules.uploader.service.Minio')
    def test_upload_file_s3_error(self, mock_minio_class):
        """Test file upload when S3Error occurs."""
        # Arrange
        mock_minio_instance = Mock()

        mock_minio_instance.put_object.side_effect = S3Error(
        code="InternalError",
        message="Upload failed",
        resource="/my-bucket",
        request_id="req-123",
        host_id="host-abc",
        response=Mock(status=500, reason="Internal Server Error", getheader=lambda *_args, **_kwargs: None)
    )
        mock_minio_class.return_value = mock_minio_instance
        
        service = MinIOService(self.mock_config)
        
        # Act & Assert
        with pytest.raises(S3Error, match="Upload failed"):
            service.upload_file(
                self.sample_file_data,
                self.sample_filename,
                "videos"
            )

    @patch('app.modules.uploader.service.Minio')
    def test_upload_file_io_error(self, mock_minio_class):
        """Test file upload when IO error occurs."""
        # Arrange
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        
        # Create a file-like object that raises an error
        problematic_file = Mock()
        problematic_file.seek.side_effect = IOError("File read error")
        
        service = MinIOService(self.mock_config)
        
        # Act & Assert
        with pytest.raises(IOError, match="File read error"):
            service.upload_file(
                problematic_file,
                self.sample_filename,
                "videos"
            )

    def test_minio_service_initialization_default_config(self):
        """Test MinIOService initialization with default config."""
        # Arrange & Act
        with patch('app.modules.uploader.service.Minio') as mock_minio_class:
            mock_minio_instance = Mock()
            mock_minio_instance.bucket_exists.return_value = True
            mock_minio_class.return_value = mock_minio_instance
            
            service = MinIOService()
            
            # Assert
            assert service.config is not None
            assert service.client is not None

    @patch('app.modules.uploader.service.Minio')
    def test_generate_unique_filename_different_file_types(self, mock_minio_class):
        """Test unique filename generation for different file types."""

        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        # Arrange
        service = MinIOService(self.mock_config)
        original_filename = "document.pdf"
        
        # Act
        result_videos = service._generate_unique_filename(original_filename, "videos")
        result_documents = service._generate_unique_filename(original_filename, "documents")
        result_images = service._generate_unique_filename(original_filename, "images")
        
        # Assert
        assert "/videos/" in result_videos
        assert "/documents/" in result_documents
        assert "/images/" in result_images
        assert result_videos.endswith(".pdf")
        assert result_documents.endswith(".pdf")
        assert result_images.endswith(".pdf") 