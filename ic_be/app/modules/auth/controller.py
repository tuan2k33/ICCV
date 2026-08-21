import logging
from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Request, UploadFile, Query

from app.constant.enums import UserRole, CompanyNameEnum
from app.core.app_status import AppStatus
from app.core.setting import settings
from app.modules.auth.dependencies import get_auth_service
from app.modules.auth.middleware import AuthMiddleware
from app.modules.auth.schemas import LoginSchema, RegisterSchema, UserUpdateSchema, UserFilterSchema, UserDeleteSchema, \
    CheckExistPhoneNumberSchema
from app.modules.auth.security import CookieService
from app.modules.auth.service import AuthService
from app.modules.batch.dependencies import get_batch_service
from app.modules.batch.schemas import BatchCreateSchema
from app.modules.batch.service import BatchService
from app.modules.counting_group.dependencies import get_counting_group_service
from app.modules.counting_group.service import CountingGroupService
from app.modules.task.dependencies import get_task_service
from app.modules.task.service import TaskService
from app.utils.response import handle_response, error_exception_handler

logger = logging.getLogger(__name__)
auth_router = APIRouter()
user_router = APIRouter()


@auth_router.post("/register")
async def register(req: RegisterSchema, auth_service: AuthService = Depends(get_auth_service),
                   batch_service: BatchService = Depends(get_batch_service),
                   group_service: CountingGroupService = Depends(get_counting_group_service),
                   task_service: TaskService = Depends(get_task_service),
                   _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    result_register = await auth_service.register(req)
    if UserRole.ENTRY in req.roles:
        batch_id = await batch_service.get_active_batch(req.tenant_id)
        if batch_id:
            group, is_update = await group_service.create_or_update_user_into_counting_group(result_register.get("id"),
                                                                                             req.fullname,
                                                                                             req.company, batch_id)
            if is_update:
                await task_service.change_user_assign([], group.get("racks") or [],
                                                      group.get("batch_id"), group.get("user_id_2"),
                                                      group.get("user_id_1"))

    return result_register


@auth_router.post("/login")
async def login(request: Request, user_login: LoginSchema,
                auth_service: AuthService = Depends(get_auth_service)):
    logger.info(f"endpoint: {request.url.path}, method: {request.method}, user: {user_login.username}")
    token = await auth_service.login(user_login.username, user_login.password)
    response = handle_response(app_status=AppStatus.LOGIN_SUCCESS)
    CookieService.set_cookie(response, 'access_token', token.get("access_token"),
                             request_origin=request.headers.get("origin"),
                             max_age=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN_MINUTES))
    CookieService.set_cookie(response, 'refresh_token', token.get("refresh_token"),
                             request_origin=request.headers.get("origin"),
                             max_age=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_IN_DAYS))
    return response


@auth_router.post("/import_users")
async def import_users(file_excel: UploadFile, tenant_id: int, roles: list[UserRole], company: CompanyNameEnum = None,
                       auth_service: AuthService = Depends(get_auth_service),
                       _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    logger.info(f"endpoint: Import users")
    content = await file_excel.read()
    result = await auth_service.import_users(content, tenant_id, roles, company)
    return handle_response(result)


@auth_router.get("/check_exist_username")
async def check_exist_username(username: str, auth_service: AuthService = Depends(get_auth_service),
                               _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    return await auth_service.check_exist_username(username)


@auth_router.get("/check_exist_phone_number")
async def check_exist_username(param: CheckExistPhoneNumberSchema = Depends(),
                               auth_service: AuthService = Depends(get_auth_service),
                               _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    return await auth_service.check_exist_phone(param.phone_numbers)


@auth_router.get("/me")
async def me(user: AuthMiddleware = Depends(AuthMiddleware.get_current_user)):
    return user


@auth_router.post("/logout")
async def logout(_=Depends(AuthMiddleware.get_current_user)):
    response = handle_response(app_status=AppStatus.LOGOUT_SUCCESS)
    CookieService.clear_cookie(response)
    return response


@user_router.get("")
async def get_all_users(skip: int = 0, limit: int = 10, roles: Optional[List[UserRole]] = Query(None),
                        user_filter=Depends(UserFilterSchema),
                        auth_service: AuthService = Depends(get_auth_service),
                        _: AuthMiddleware = Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    response = await auth_service.get_all_users(skip, limit, roles, user_filter)
    return handle_response(response=response)


@user_router.get("/fetch_all_users")
async def fetch_all_users(user_filter=Depends(UserFilterSchema), roles: Optional[List[UserRole]] = Query(None),
                          auth_service: AuthService = Depends(get_auth_service),
                          _: AuthMiddleware = Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    response = await auth_service.fetch_all_users(roles, user_filter)
    return handle_response(response=response)


@user_router.put("/{user_id:int}")
async def update_user(user_id: int, user_data: UserUpdateSchema,
                      auth_service: AuthService = Depends(get_auth_service),
                      _: AuthMiddleware = Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    users = await auth_service.update_user(user_id, user_data)
    return users


@user_router.delete("/delete_users")
async def delete_users(data: UserDeleteSchema,
                       auth_service: AuthService = Depends(get_auth_service),
                       task_service: TaskService = Depends(get_task_service),
                       _: AuthMiddleware = Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    result = await auth_service.delete_users(data)
    tasks = await task_service.get_task_of_user_progress(result)
    if tasks:
        raise error_exception_handler(AppStatus.ERROR_TASK_IN_PROGRESS)
    return handle_response(app_status=AppStatus.SUCCESS)


@user_router.delete("/{user_id:int}")
async def delete_user(user_id: int,
                      auth_service: AuthService = Depends(get_auth_service),
                      _: AuthMiddleware = Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    users = await auth_service.delete_user(user_id)
    return users
