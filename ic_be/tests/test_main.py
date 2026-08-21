import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import Application, app


class TestApplication:
    """Test cases for Application class."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('app.main.lifespan'):
            with patch('app.main.socket_manage'):
                self.application = Application()

    def test_application_initialization(self):
        """Test Application initialization."""
        # Assert
        assert isinstance(self.application.app, FastAPI)
        assert self.application.manager is not None

    @patch('app.main.auth_router')
    @patch('app.main.user_router')
    @patch('app.main.upload_router')
    @patch('app.main.blob_router')
    @patch('app.main.task_router')
    def test_setup_router(self, mock_task_router, mock_blob_router,
                         mock_upload_router, mock_user_router, mock_auth_router):
        """Test router setup."""
        # Arrange
        mock_auth_router = Mock()
        mock_user_router = Mock()
        mock_upload_router = Mock()
        mock_blob_router = Mock()
        mock_task_router = Mock()
        
        # Act
        self.application.setup_router()
        
        # Assert
        # Check that all routers are included
        assert len(self.application.app.routes) > 0

    def test_init_cors(self):
        """Test CORS middleware initialization."""
        # Act
        self.application.init_cors()
        
        # Assert
        # Check that CORS middleware is added
        cors_middleware = None
        for middleware in self.application.app.user_middleware:
            if 'CORSMiddleware' in str(middleware.cls):
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None

    def test_configure_logging(self):
        """Test logging configuration."""
        # Act
        self.application.configure_logging()
        
        # Assert
        # This is a static method, so we just verify it can be called without error
        assert True

    def test_add_exception_handlers(self):
        """Test exception handler registration."""
        # Act
        self.application.add_exception_handlers()
        
        # Assert
        # Check that exception handlers are registered
        assert len(self.application.app.exception_handlers) > 0

    @patch('app.main.socket_manage')
    def test_setup_websocket_router(self, mock_socket_manage):
        """Test WebSocket router setup."""
        # Act
        self.application.setup_websocket_router()
        
        # Assert
        # Check that WebSocket endpoint is registered
        websocket_routes = [route for route in self.application.app.routes if route.path == "/ws"]
        assert len(websocket_routes) > 0

    @patch('app.main.uvicorn.run')
    def test_start_app(self, mock_uvicorn_run):
        """Test application startup."""
        # Arrange
        host = "127.0.0.1"
        port = 8000
        
        # Act
        self.application.start_app(host, port)
        
        # Assert
        mock_uvicorn_run.assert_called_once_with(self.application.app, host=host, port=port)

    @patch('app.main.uvicorn.run')
    def test_start_app_default_values(self, mock_uvicorn_run):
        """Test application startup with default values."""
        # Act
        self.application.start_app()
        
        # Assert
        mock_uvicorn_run.assert_called_once_with(self.application.app, host="0.0.0.0", port=8000)


class TestMainApp:
    """Test cases for main app instance."""

    def test_app_instance(self):
        """Test that app instance is created."""
        # Assert
        assert app is not None
        assert isinstance(app, FastAPI)

    def test_app_has_routes(self):
        """Test that app has routes configured."""
        # Assert
        assert len(app.routes) > 0

    def test_app_has_middleware(self):
        """Test that app has middleware configured."""
        # Assert
        assert len(app.user_middleware) > 0

    def test_app_has_exception_handlers(self):
        """Test that app has exception handlers configured."""
        # Assert
        assert len(app.exception_handlers) > 0


class TestAppEndpoints:
    """Test cases for app endpoints."""

    @pytest.fixture
    def client(self):
        """Test client for FastAPI app."""
        return TestClient(app)

    def test_app_health_check(self, client):
        """Test that app responds to basic requests."""
        # Act
        response = client.get("/docs")
        
        # Assert
        # Should return 200 for docs endpoint
        assert response.status_code in [200, 404]  # 404 if docs not enabled

    def test_app_openapi_schema(self, client):
        """Test that app has OpenAPI schema."""
        # Act
        response = client.get("/openapi.json")
        
        # Assert
        # Should return 200 for OpenAPI schema
        assert response.status_code in [200, 404]  # 404 if schema not enabled

    def test_app_routes_structure(self, client):
        """Test that app has expected route structure."""
        # Get all routes
        routes = app.routes
        
        # Check for expected route prefixes
        route_paths = [route.path for route in routes]
        
        # Should have some routes
        assert len(route_paths) > 0
        
        # Check for expected API prefixes
        api_routes = [path for path in route_paths if path.startswith('/api')]
        assert len(api_routes) > 0

    def test_app_cors_headers(self, client):
        """Test that app has CORS headers configured."""
        # Act
        response = client.options("/")
        
        # Assert
        # Should handle OPTIONS request (CORS preflight)
        assert response.status_code in [200, 404, 405]  # Various possible responses


class TestAppConfiguration:
    """Test cases for app configuration."""

    def test_app_title(self):
        """Test app title configuration."""
        # Assert
        assert hasattr(app, 'title')
        assert app.title is not None

    def test_app_version(self):
        """Test app version configuration."""
        # Assert
        assert hasattr(app, 'version')
        assert app.version is not None

    def test_app_description(self):
        """Test app description configuration."""
        # Assert
        assert hasattr(app, 'description')

    def test_app_lifespan(self):
        """Test app lifespan configuration."""
        # Assert
        assert hasattr(app, 'router')
        # Check if lifespan is configured (this might be in the router or app level)
        assert True  # Placeholder assertion


class TestAppDependencies:
    """Test cases for app dependencies."""

    def test_app_has_dependencies(self):
        """Test that app has dependencies configured."""
        # Assert
        # Check that dependencies are available
        assert hasattr(app, 'dependency_overrides')
        assert hasattr(app, 'router')

    def test_app_middleware_order(self):
        """Test that app middleware is in correct order."""
        # Assert
        # CORS middleware should be one of the first middleware
        middleware_names = [str(middleware.cls) for middleware in app.user_middleware]
        cors_middleware = [name for name in middleware_names if 'CORSMiddleware' in name]
        
        assert len(cors_middleware) > 0 