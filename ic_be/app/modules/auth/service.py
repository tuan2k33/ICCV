import logging
from io import BytesIO
from typing import List

import pandas as pd

from app.constant.enums import UserRole
from app.core.app_status import AppStatus
from app.modules.auth.hanldle_data_user import DataFrameValidator
from app.modules.auth.schemas import RegisterSchema, UserUpdateSchema, UserFilterSchema, UserDeleteSchema
from app.utils.hasher import hash_password, verify_password
from app.utils.response import error_exception_handler, handle_response
from app.utils.user_utils import username_slug

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repository, group_repository, token_service):
        self.user_repository = user_repository
        self.group_repository = group_repository
        self.token_service = token_service

    async def login(self, username, password):
        logger.info("AuthService.login called with username: %s", username)
        user = await self.user_repository.find_user_by_username_or_email(username)
        if not user or not verify_password(password, user.get("password")):
            logger.info("AuthService.login - Invalid login attempt for username: %s", username)
            raise error_exception_handler(app_status=AppStatus.ERROR_LOGIN_INVALID)
        if user.get("is_active", False) is False:
            raise error_exception_handler(app_status=AppStatus.ERROR_USER_INACTIVE)
        return self.token_service.generate_token_pair(user)

    async def register(self, param: RegisterSchema):
        if await self.user_repository.exists_user(param.username, param.phone_number):
            logger.error(
                f"AuthService.register - User already exists with username: {param.username}")
            raise error_exception_handler(app_status=AppStatus.ERROR_USER_ALREADY_EXISTS)
        param.password = hash_password(param.password)
        user = await self.user_repository.create_user({**param.__dict__, "username_tmp": username_slug(param.username)})
        return user

    async def get_all_users(self, skip: int, limit: int, roles: list, user_filter: UserFilterSchema):
        user_filter = user_filter.model_dump(exclude_unset=True, exclude_none=True)
        total, users = await self.user_repository.get_all_users(skip, limit, roles, user_filter)
        result = dict(total=total, users=users)
        return result

    async def fetch_all_users(self, roles, user_filter: UserFilterSchema):
        user_filter = user_filter.model_dump(exclude_unset=True, exclude_none=True)
        users = await self.user_repository.fetch_all_users(roles, user_filter)
        return users

    async def update_user(self, user_id: int, user_data: UserUpdateSchema):
        user_data = user_data.model_dump(exclude_unset=True, exclude_none=True)
        if user_data.get("password"):
            user_data["password"] = hash_password(user_data["password"])
        if "username" in user_data:
            user_data["username_tmp"] = username_slug(user_data["username"])
        result = await self.user_repository.update_user(user_id, user_data)
        if "fullname" in user_data:
            await self.group_repository.update_by_cond({"fullname_1": user_data["fullname"]},
                                                       {"user_id_1": user_id})
            await self.group_repository.update_by_cond({"fullname_2": user_data["fullname"]},
                                                       {"user_id_2": user_id})
        return result

    async def delete_user(self, user_id: int):
        result = await self.user_repository.delete_user(user_id)
        if not result:
            raise error_exception_handler(AppStatus.ERROR_USER_NOT_FOUND)
        return handle_response(app_status=AppStatus.SUCCESS)

    async def delete_users(self, data_users: UserDeleteSchema):
        data_users = data_users.data
        if not data_users:
            raise error_exception_handler(AppStatus.ERROR_USER_NOT_FOUND)
        conditions_set = ["id"]
        ids_user = await self.user_repository.delete_users(data_users, conditions_set)
        if not ids_user:
            raise error_exception_handler(AppStatus.ERROR_USER_NOT_FOUND)
        await self.group_repository.update_by_cond({"fullname_1": None, "user_id_1": None},
                                                   {"user_id_1__in": ids_user})
        await self.group_repository.update_by_cond({"fullname_2": None, "user_id_2": None},
                                                   {"user_id_2__in": ids_user})
        return ids_user

    async def check_exist_username(self, username):
        return await self.user_repository.exists_user(username)

    async def check_exist_phone(self, phone_numbers: List[str]):
        result = await self.get_existing_values("phone_number", phone_numbers)
        return list(set(result))

    async def get_user_by_company(self, company: str, tenant_id: int, roles: list):
        return await self.user_repository.get_user_by_company(company, tenant_id, roles)

    async def import_users(self, content_template, tenant_id: int, roles: List[UserRole], company: str):
        data = pd.read_excel(BytesIO(content_template), dtype={"Số điện thoại\n(Ví dụ: 086867563)": str})

        validator = DataFrameValidator(data, company, tenant_id, roles)
        validator.validate()
        detailed_errors = validator.get_structured_errors()
        if detailed_errors:
            raise error_exception_handler(app_status=AppStatus.ERROR_USER_DATA_IMPORT,
                                          data={"errors": detailed_errors, "total": validator.count_rows})
        list_phone_number = validator.get_phone_number_list()
        phone_already_exist = await self.get_existing_values("phone_number", list_phone_number)
        if phone_already_exist:
            validator.check_duplicate_phones(phone_already_exist)
            data_errors = validator.get_structured_errors()
            raise error_exception_handler(app_status=AppStatus.ERROR_USER_PHONE_ALREADY_EXISTS,
                                          data={"errors": data_errors, "total": validator.count_rows})

        # handle username
        list_username = validator.get_username_list()
        username_already_exist = await self.user_repository.get_users_by_field("username_tmp", list_username,
                                                                               ["username"])
        username_already_exist = {r.get('username') for r in username_already_exist}
        validator.update_duplicate_usernames_in_sheet(username_already_exist)

        data_valid = validator.cleanup_error_columns().to_list()
        await self.user_repository.create_users(data_valid)
        result = dict(total=validator.count_rows, users=data_valid)
        return result

    async def get_existing_values(self, field: str, values: list) -> list:
        records = await self.user_repository.get_users_by_field(field, values, [field])
        return [r.get(field) for r in records]
