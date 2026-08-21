from enum import Enum

from app.constant import common_status_codes as common
from app.modules.auth import user_status_codes as user
from app.modules.batch import batch_status_codes as batch
from app.modules.counting_group import app_status as counting_group
from app.modules.task import task_status_codes as task
from app.modules.tenant import tenant_status_codes


class AppStatus(Enum):
    # common
    SUCCESS = common.SUCCESS
    BAD_REQUEST = common.BAD_REQUEST
    NOT_FOUND = common.NOT_FOUND
    FORBIDDEN = common.FORBIDDEN
    ERROR_INTERNAL_SERVER_ERROR = common.ERROR_INTERNAL_SERVER_ERROR
    UNAUTHORIZED = common.UNAUTHORIZED

    # user
    LOGIN_SUCCESS = user.LOGIN_SUCCESS
    LOGOUT_SUCCESS = user.LOGOUT_SUCCESS

    ERROR_LOGIN_INVALID = user.ERROR_LOGIN_INVALID
    ERROR_USER_INACTIVE = user.ERROR_USER_INACTIVE
    ERROR_USER_ALREADY_EXISTS = user.ERROR_USER_ALREADY_EXISTS
    ERROR_USER_PHONE_ALREADY_EXISTS = user.ERROR_USER_PHONE_ALREADY_EXISTS
    ERROR_INVALID_ROLE = user.ERROR_INVALID_ROLE
    ERROR_USER_NOT_FOUND = user.ERROR_USER_NOT_FOUND
    ERROR_USER_DATA_IMPORT = user.ERROR_USER_DATA_IMPORT
    ERROR_USER_MISSING_COLUMN = user.ERROR_USER_MISSING_COLUMN

    # tenant
    TENANT_CREATED = tenant_status_codes.TENANT_CREATED
    TENANT_UPDATED = tenant_status_codes.TENANT_UPDATED
    TENANT_SETTING_UPDATED = tenant_status_codes.TENANT_SETTING_UPDATED
    TENANT_INFORMATION_UPDATED = tenant_status_codes.TENANT_INFORMATION_UPDATED

    ERROR_TENANT_NOT_FOUND = tenant_status_codes.ERROR_TENANT_NOT_FOUND

    # batch
    ERROR_BATCH_NOT_FOUND = batch.ERROR_BATCH_NOT_FOUND
    ERROR_EXPORT_NO_DATA = batch.ERROR_EXPORT_NO_DATA
    ERROR_ACTIVE_BATCH_EXIST = batch.ERROR_ACTIVE_BATCH_EXIST

    # task
    TASK_CREATED = task.TASK_CREATED
    TASK_UPDATED = task.TASK_UPDATED
    TASK_FLAGGED = task.TASK_FLAGGED
    TASK_UPDATED_PROCESS = task.TASK_UPDATED_PROCESS
    TASK_RESULT_UPDATED = task.TASK_RESULT_UPDATED
    TASK_SUBMITTED = task.TASK_SUBMITTED
    TASK_ASSIGNED = task.TASK_ASSIGNED

    ERROR_TASK_NOT_FOUND = task.ERROR_TASK_NOT_FOUND
    ERROR_TASK_INVALID_DATA = task.ERROR_INVALID_DATA
    ERROR_TASK_RESULT_NOT_EXITS = task.ERROR_TASK_RESULT_NOT_EXITS
    ERROR_TASK_IN_PROGRESS = task.ERROR_TASK_IN_PROGRESS
    ERROR_RACK_NOT_FOUND = counting_group.ERROR_RACK_NOT_FOUND

    @property
    def status_code(self):
        return self.value[0]

    @property
    def custom_status_code(self):
        return self.value[1]

    @property
    def error_code(self):
        return self.value[2]

    @property
    def message(self):
        return self.value[3]

    @property
    def meta(self):
        return {
            "custom_status_code": self.custom_status_code,
            "error_code": self.error_code,
            "message": self.message,
        }
