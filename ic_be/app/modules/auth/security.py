import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Union, List
from urllib.parse import urlparse

import jwt
from fastapi import Response, Request

from app.core.app_status import AppStatus
from app.core.setting import settings
from app.utils.response import error_exception_handler


class TokenService:
    def __init__(
            self,
            secret_key: str,
            algorithm: str,
            access_token_expires_in_minutes: int,
            refresh_token_expires_in_days: int,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expires_in_minutes = access_token_expires_in_minutes
        self.refresh_token_expires_in_days = refresh_token_expires_in_days

    def generate_access_token(self, user: Dict[str, Any]) -> str:
        """
        Generate an access token for a user.

        Args:
            user (dict): A dictionary containing user details.

        Returns:
            str: The generated access token.
        """
        now = datetime.now(tz=timezone.utc)
        exp_time = now + timedelta(minutes=self.access_token_expires_in_minutes)

        payload = {
            "sub": str(user.get("id")),  # Subject (user ID) - MUST be string
            "username": user.get("username"),  # Username
            "email": user.get("email"),  # Email
            "roles": user.get("roles", []),  # Roles for the user
            "iat": int(now.timestamp()),  # Issued at - UNIX timestamp
            "jti": str(uuid.uuid4()),  # JWT ID (unique identifier for the token)
            "exp": int(exp_time.timestamp()),  # Expiration time - UNIX timestamp
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def generate_refresh_token(self, user: Dict[str, Any]) -> str:
        """
        Generate a refresh token for a user.

        Args:
            user (dict): A dictionary containing user details.

        Returns:
            str: The generated refresh token.
        """
        now = datetime.now(tz=timezone.utc)
        exp_time = now + timedelta(days=self.refresh_token_expires_in_days)

        payload = {
            "sub": str(user.get("id")),  # Subject (user ID) - MUST be string
            "iat": int(now.timestamp()),  # Issued at - UNIX timestamp
            "jti": str(uuid.uuid4()),  # JWT ID (unique identifier for the token)
            "exp": int(exp_time.timestamp()),  # Expiration time - UNIX timestamp
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def validate_token(self, token: str) -> Union[Dict[str, Any], None]:
        """
        Validate a given token (access or refresh).

        Args:
            token (str): The token to validate.

        Returns:
            dict | None: Decoded token payload if valid; None if invalid or expired.
        """
        try:
            decoded_token = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            return decoded_token
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def generate_token_pair(self, user: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate both access and refresh tokens.

        Args:
            user (dict): A dictionary containing user details.

        Returns:
            dict: A dictionary containing both access and refresh tokens.
        """
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)
        return {"access_token": access_token, "refresh_token": refresh_token}

    def get_token_payload(self, token: str) -> Union[Dict[str, Any], None]:
        """
        Get token payload without verification (for debugging).
        WARNING: Only use for debugging, not for production validation!

        Args:
            token (str): The token to decode.

        Returns:
            dict | None: Decoded payload or None if invalid format.
        """
        try:
            # Decode the token without verifying signature
            decoded = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return decoded
        except Exception as e:
            print(f"Error decoding token: {e}")
            return None

    def refresh_access_token(self, refresh_token: str, user: Dict[str, Any]) -> Union[str, None]:
        """
        Generate a new access token using a valid refresh token.

        Args:
            refresh_token (str): The refresh token to validate.
            user (dict): User data for the new access token.

        Returns:
            str | None: New access token if refresh token is valid, None otherwise.
        """
        refresh_payload = self.validate_token(refresh_token)
        if refresh_payload and refresh_payload.get("sub") == str(user.get("id")):
            return self.generate_access_token(user)
        return None


class CookieService:

    @staticmethod
    def get_cookie(request: Request) -> dict:
        token = request.cookies
        return token

    @staticmethod
    def clear_cookie(response: Response):
        response.delete_cookie(key="access_token", samesite='lax', httponly=True, secure=False)
        response.delete_cookie(key="refresh_token", samesite='lax', httponly=True, secure=False)

    @staticmethod
    def get_token_from_cookie(cookie_name: str, request: Request) -> Union[str, None]:
        """
        Get a token from the request cookies.

        Args:
            cookie_name (str): The name of the cookie to retrieve.
            request (Request): The FastAPI Request object.

        Returns:
            str | None: The value of the cookie if it exists, None otherwise.
        """
        return request.cookies.get(cookie_name, None)

    @staticmethod
    def get_origin_from_request(request: Request) -> str:
        """
        Extract the origin from the request using the Origin or Referer headers.
        If both are missing, fall back to a trusted default.

        Returns:
            str: Origin in the format "scheme://host[:port]"
        """
        # 1. Ưu tiên Origin
        origin = request.headers.get("origin")
        if origin:
            return origin

        referer = request.headers.get("referer")
        if referer:
            parsed = urlparse(referer)
            origin = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                origin += f":{parsed.port}"
            return origin

        fallback_origin = settings.ALLOW_ORIGINS.split(",")[0]
        return fallback_origin

    @staticmethod
    def is_allowed_origin(origin: str, allowed_origins: List[str]) -> bool:
        """
        Check if the request origin is in the list of allowed origins.

        Args:
            origin (str): The request origin.
            allowed_origins (list): List of allowed hosts.

        Returns:
            bool: True if the origin is allowed, False otherwise.
        """
        return origin in allowed_origins or "*" in allowed_origins

    @staticmethod
    def set_cookie(response: Response, key: str, value: str, request_origin: str,
                   max_age: timedelta = timedelta(hours=1)):
        """
        Set a cookie dynamically based on the allowed origins (hosts).

        Args:
            response (Response): FastAPI Response object to set the cookie on.
            key (str): The cookie name.
            value (str): The cookie value.
            request_origin (str): The origin of the incoming request.
            max_age (int): Lifetime of the cookie in seconds (default: 3600 = 1 hour).
        """
        if CookieService.is_allowed_origin(request_origin, settings.ALLOW_ORIGINS):
            response.set_cookie(
                key=key,
                value=value,
                httponly=True,
                secure=False,
                samesite='lax',
                expires=datetime.now(timezone.utc) + max_age

            )
        else:
            raise error_exception_handler(AppStatus.FORBIDDEN)
