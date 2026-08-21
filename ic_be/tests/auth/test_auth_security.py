import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from fastapi import Request, Response
from app.modules.auth.security import TokenService, CookieService
from app.constant.app_status import AppStatus


class TestTokenService:
    """Test cases for TokenService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.token_service = TokenService(
            secret_key="test_secret_key",
            algorithm="HS256",
            access_token_expires_in_minutes=60,
            refresh_token_expires_in_days=7
        )
        self.sample_user = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "testuser",
            "email": "test@example.com",
            "roles": ["USER", "ADMIN"]
        }

    def test_generate_access_token(self):
        """Test access token generation."""
        token = self.token_service.generate_access_token(self.sample_user)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_refresh_token(self):
        """Test refresh token generation."""
        token = self.token_service.generate_refresh_token(self.sample_user)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_token_pair(self):
        """Test token pair generation."""
        tokens = self.token_service.generate_token_pair(self.sample_user)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)

    def test_validate_token_valid(self):
        """Test token validation with valid token."""
        token = self.token_service.generate_access_token(self.sample_user)
        payload = self.token_service.validate_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(self.sample_user["id"])
        assert payload["username"] == self.sample_user["username"]

    def test_validate_token_invalid(self):
        """Test token validation with invalid token."""
        payload = self.token_service.validate_token("invalid_token")
        assert payload is None

    def test_validate_token_expired(self):
        """Test token validation with expired token."""
        # Create a token service with very short expiration
        short_token_service = TokenService(
            secret_key="test_secret_key",
            algorithm="HS256",
            access_token_expires_in_minutes=0,  # Expires immediately
            refresh_token_expires_in_days=0
        )
        
        token = short_token_service.generate_access_token(self.sample_user)
        # Wait a bit to ensure token expires
        import time
        time.sleep(0.1)
        
        payload = short_token_service.validate_token(token)
        assert payload is None

    def test_refresh_access_token_valid(self):
        """Test refreshing access token with valid refresh token."""
        tokens = self.token_service.generate_token_pair(self.sample_user)
        refresh_token = tokens["refresh_token"]
        
        new_access_token = self.token_service.refresh_access_token(refresh_token, self.sample_user)
        
        assert new_access_token is not None
        assert isinstance(new_access_token, str)
        assert new_access_token != tokens["access_token"]

    def test_refresh_access_token_invalid(self):
        """Test refreshing access token with invalid refresh token."""
        new_access_token = self.token_service.refresh_access_token("invalid_token", self.sample_user)
        assert new_access_token is None

    def test_get_token_payload_debug(self):
        """Test getting token payload without verification (debug mode)."""
        token = self.token_service.generate_access_token(self.sample_user)
        payload = self.token_service.get_token_payload(token)
        
        assert payload is not None
        assert "sub" in payload


class TestCookieService:
    """Test cases for CookieService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cookie_service = CookieService()

    def test_get_cookie(self):
        """Test getting cookies from request."""
        mock_request = Mock()
        mock_request.cookies = {"access_token": "test_token", "refresh_token": "refresh_token"}
        
        cookies = self.cookie_service.get_cookie(mock_request)
        
        assert cookies == {"access_token": "test_token", "refresh_token": "refresh_token"}

    def test_clear_cookie(self):
        """Test clearing cookies from response."""
        mock_response = Mock()
        
        self.cookie_service.clear_cookie(mock_response)
        
        # Verify delete_cookie was called twice (for access and refresh tokens)
        assert mock_response.delete_cookie.call_count == 2

    def test_get_token_from_cookie(self):
        """Test getting specific token from cookies."""
        mock_request = Mock()
        mock_request.cookies = {"access_token": "test_access_token"}
        
        token = self.cookie_service.get_token_from_cookie("access_token", mock_request)
        
        assert token == "test_access_token"

    def test_get_token_from_cookie_not_found(self):
        """Test getting token from cookies when it doesn't exist."""
        mock_request = Mock()
        mock_request.cookies = {}
        
        token = self.cookie_service.get_token_from_cookie("access_token", mock_request)
        
        assert token is None

    @patch('app.modules.auth.security.settings')
    def test_get_origin_from_request_origin_header(self, mock_settings):
        """Test getting origin from Origin header."""
        mock_request = Mock()
        mock_request.headers = {"origin": "http://localhost:3000"}
        mock_settings.ALLOW_ORIGINS = "http://localhost:3000,http://localhost:8000"
        
        origin = self.cookie_service.get_origin_from_request(mock_request)
        
        assert origin == "http://localhost:3000"

    @patch('app.modules.auth.security.settings')
    def test_get_origin_from_request_referer_header(self, mock_settings):
        """Test getting origin from Referer header."""
        mock_request = Mock()
        mock_request.headers = {"referer": "http://localhost:3000/dashboard"}
        mock_settings.ALLOW_ORIGINS = "http://localhost:3000,http://localhost:8000"
        
        origin = self.cookie_service.get_origin_from_request(mock_request)
        
        assert origin == "http://localhost:3000"

    @patch('app.modules.auth.security.settings')
    def test_get_origin_from_request_fallback(self, mock_settings):
        """Test getting origin with fallback when headers are missing."""
        mock_request = Mock()
        mock_request.headers = {}
        mock_settings.ALLOW_ORIGINS = "http://localhost:3000,http://localhost:8000"
        
        origin = self.cookie_service.get_origin_from_request(mock_request)
        
        assert origin == "http://localhost:3000"

    def test_is_allowed_origin_true(self):
        """Test checking if origin is allowed."""
        allowed_origins = ["http://localhost:3000", "http://localhost:8000"]
        
        result = self.cookie_service.is_allowed_origin("http://localhost:3000", allowed_origins)
        assert result is True

    def test_is_allowed_origin_false(self):
        """Test checking if origin is not allowed."""
        allowed_origins = ["http://localhost:3000", "http://localhost:8000"]
        
        result = self.cookie_service.is_allowed_origin("http://malicious.com", allowed_origins)
        assert result is False

    def test_is_allowed_origin_wildcard(self):
        """Test checking if origin is allowed with wildcard."""
        allowed_origins = ["*"]
        
        result = self.cookie_service.is_allowed_origin("http://anydomain.com", allowed_origins)
        assert result is True

    @patch('app.modules.auth.security.settings')
    def test_set_cookie_allowed_origin(self, mock_settings):
        """Test setting cookie for allowed origin."""
        mock_response = Mock()
        mock_request_origin = "http://localhost:3000"
        mock_settings.ALLOW_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
        
        self.cookie_service.set_cookie(
            mock_response, 
            "test_cookie", 
            "test_value", 
            mock_request_origin
        )
        
        mock_response.set_cookie.assert_called_once()

    @patch('app.modules.auth.security.settings')
    def test_set_cookie_forbidden_origin(self, mock_settings):
        """Test setting cookie for forbidden origin raises exception."""
        mock_response = Mock()
        mock_request_origin = "http://malicious.com"
        mock_settings.ALLOW_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
        
        with pytest.raises(Exception):
            self.cookie_service.set_cookie(
                mock_response, 
                "test_cookie", 
                "test_value", 
                mock_request_origin
            ) 