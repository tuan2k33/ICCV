from fastapi import Depends

from app.core.setting import settings
from app.infra.database import get_conn
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.auth.security import TokenService
from app.modules.counting_group.dependencies import get_counting_group_repository
from app.modules.counting_group.repository import CountingGroupRepository


def get_auth_repository(db=Depends(get_conn)):
    return AuthRepository(db)


def get_token_service():
    return TokenService(settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM, settings.ACCESS_TOKEN_EXPIRES_IN_MINUTES,
                        settings.REFRESH_TOKEN_EXPIRES_IN_DAYS)


def get_auth_service(auth_repository: AuthRepository = Depends(get_auth_repository),
                     group_repository: CountingGroupRepository = Depends(get_counting_group_repository),
                     token_service: TokenService = Depends(get_token_service)):
    return AuthService(auth_repository, group_repository, token_service)
