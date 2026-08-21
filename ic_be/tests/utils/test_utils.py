import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from pydantic import ValidationError
from app.utils.hasher import hash_password, verify_password
from app.utils.response import make_error_response, error_exception_handler, handle_response
from app.constant.app_status import AppStatus


class TestHasher:
    """Test cases for hasher utility functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        result = verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        result = verify_password(wrong_password, hashed)
        assert result is False

    def test_verify_password_empty_strings(self):
        """Test password verification with empty strings."""
        hashed = hash_password("")
        result = verify_password("", hashed)
        assert result is True

    def test_hash_password_special_characters(self):
        """Test password hashing with special characters."""
        password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_special_characters(self):
        """Test password verification with special characters."""
        password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = hash_password(password)

        result = verify_password(password, hashed)
        assert result is True


class TestResponse:
    """Test cases for response utility functions."""

    def test_make_error_response_default(self):
        """Test make_error_response with default parameters."""
        response = make_error_response()

        assert response.status_code == AppStatus.ERROR_INTERNAL_SERVER_ERROR.status_code
        assert "detail" in response.body.decode()

    def test_make_error_response_custom_status(self):
        """Test make_error_response with custom status."""
        response = make_error_response(AppStatus.BAD_REQUEST)

        assert response.status_code == AppStatus.BAD_REQUEST.status_code
        assert "detail" in response.body.decode()

    def test_make_error_response_with_detail(self):
        """Test make_error_response with custom detail."""
        custom_detail = {"error": "Custom error message"}
        response = make_error_response(AppStatus.BAD_REQUEST, custom_detail)

        assert response.status_code == AppStatus.BAD_REQUEST.status_code
        response_body = response.body.decode()
        assert "Custom error message" in response_body

    def test_error_exception_handler_validation_error(self):
        """Test error_exception_handler with ValidationError."""
        validation_error = ValidationError.from_exception_data(
            title="TestModel",
            line_errors=[{
                "type": "value_error",
                "loc": ("field_name",),
                "input": None,
                "ctx": {"error": ValueError("Invalid value")},
                "msg": "Invalid value",
            }]
        )

        with pytest.raises(HTTPException) as exc_info:
            raise error_exception_handler(validation_error, AppStatus.BAD_REQUEST)

        assert exc_info.value.status_code == AppStatus.BAD_REQUEST.status_code
        assert "Invalid value: field_name" in str(exc_info.value.detail)

    def test_error_exception_handler_value_error_with_app_status(self):
        """Test error_exception_handler with ValueError containing AppStatus."""
        app_status = AppStatus.NOT_FOUND
        value_error = ValueError(app_status, {"key": "value"})

        with pytest.raises(HTTPException) as exc_info:
            raise error_exception_handler(value_error, AppStatus.BAD_REQUEST)

        assert exc_info.value.status_code == AppStatus.NOT_FOUND.status_code
        assert exc_info.value.detail["error_code"] == AppStatus.NOT_FOUND.error_code
        assert exc_info.value.detail["data"] == {"key": "value"}

    def test_error_exception_handler_generic_error(self):
        """Test error_exception_handler with generic error."""
        generic_error = Exception("Generic error")

        with pytest.raises(HTTPException) as exc_info:
            raise error_exception_handler(generic_error, AppStatus.ERROR_INTERNAL_SERVER_ERROR)

        assert exc_info.value.status_code == AppStatus.ERROR_INTERNAL_SERVER_ERROR.status_code
        assert exc_info.value.detail["error_code"] == AppStatus.ERROR_INTERNAL_SERVER_ERROR.error_code

    def test_handle_response_dict(self):
        """Test handle_response with dictionary response."""
        response_data = {"key": "value", "count": 42}
        response = handle_response(response_data, AppStatus.SUCCESS)

        assert response.status_code == AppStatus.SUCCESS.status_code
        response_body = response.body.decode()
        assert "key" in response_body
        assert "value" in response_body
        assert "count" in response_body

    def test_handle_response_http_exception(self):
        """Test handle_response with HTTPException."""
        http_exception = HTTPException(status_code=400, detail="Bad request")

        with pytest.raises(HTTPException) as exc_info:
            handle_response(http_exception, AppStatus.SUCCESS)

        assert exc_info.value == http_exception

    def test_handle_response_non_dict(self):
        """Test handle_response with non-dictionary response."""
        response_data = "Simple string response"
        response = handle_response(response_data, AppStatus.SUCCESS)

        assert response.status_code == AppStatus.SUCCESS.status_code
        response_body = response.body.decode()
        assert "Simple string response" not in response_body  # Only message should be included

    def test_handle_response_default_status(self):
        """Test handle_response with default status."""
        response_data = {"key": "value"}
        response = handle_response(response_data)

        assert response.status_code == AppStatus.SUCCESS.status_code
        assert "SUCCESS" in response.body.decode()
