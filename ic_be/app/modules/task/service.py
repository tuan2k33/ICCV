import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone

from app.constant.enums import TaskStatus
from app.constant.enums import UserRole
from app.core.app_status import AppStatus
from app.infra.websocket import ConnectionManager
from app.modules.batch.repository import BatchRepository
from app.modules.task.repository import TaskRepository
from app.modules.task.schemas import TaskCreateSchema, TaskAssignETSchema, TaskRole, TaskUpdateResultMiniSchema, \
    TaskAssignETSet
from app.utils.response import error_exception_handler, handle_response


class TaskService:
    def __init__(self, task_repository: TaskRepository,
                 batch_repository: BatchRepository,
                 service_websocket: ConnectionManager):
        self.task_repository = task_repository
        self.batch_repository = batch_repository
        self.service_websocket = service_websocket
        self.service_delivery = None

    @staticmethod
    def _get_field_by_role(role_request, field: str):
        ROLE_FIELD_MAPPING = {
            TaskRole.ENTRY: {
                "user": "user_e",
                "result": "result_e",
                "flags": "flags_e",
                "time_process": "time_process_e",
                "time_submit": "time_submit_e",
            },
            TaskRole.CHECKER: {
                "user": "user_c",
                "result": "result_c",
                "flags": "flags_c",
                "time_process": "time_process_c",
                "time_submit": "time_submit_c",
            },
        }
        try:
            return ROLE_FIELD_MAPPING[role_request][field]
        except KeyError:
            raise error_exception_handler(AppStatus.ERROR_INVALID_ROLE)

    @staticmethod
    def _check_role_request_in_role_system(user: dict, role_request: str):
        if role_request not in user["roles"]:
            raise error_exception_handler(AppStatus.FORBIDDEN)

    def _check_assign_task(self, task, user_id, role_request):
        user_field = self._get_field_by_role(role_request, "user")
        if user_id != task.get(user_field):
            raise error_exception_handler(AppStatus.FORBIDDEN)

    def _check_role_request(self, task, user, role_request):
        self._check_role_request_in_role_system(user, role_request)
        self._check_assign_task(task, user.get('id'), role_request)

    def _check_permission_task(self, task, user, role_request=None):
        if UserRole.ADMIN in user.get("roles", []) or UserRole.CHECKER in user.get("roles", []):
            return

        if role_request:
            self._check_role_request(task, user, role_request)

    @staticmethod
    def _checker_permission_task(user):
        if not any(role in user.get("roles", []) for role in ("CHECKER", "ADMIN")):
            raise error_exception_handler(AppStatus.FORBIDDEN)

    @staticmethod
    def _check_exist_task(task):
        if not task:
            raise error_exception_handler(AppStatus.ERROR_TASK_NOT_FOUND)

    async def get_tasks(self, tenant_id: int, skip: int, limit: int):
        task = await self.task_repository.get_tasks(tenant_id, skip, limit)
        return task

    async def get_tasks_by_status(self, batch_id: int, status: list = None):
        task = await self.task_repository.get_tasks_by_status(batch_id, status)
        return task

    async def my_tasks(self, user: dict, skip: int, limit: int, batch_id: int):
        tenant_id = user.get("tenant_id", 1)
        user_id = user.get("id")
        tasks = await self.task_repository.find_task_by_user(user_id, tenant_id, batch_id, skip, limit)
        for task in tasks.get("tasks", []):
            task["record_status"] = 'IN_PROGRESS' if not task.get("result_e") else 'COMPLETED'
            del task["result_e"]
            del task["result_c"]
        return tasks

    async def get_task_by_id(self, task_id: int):
        task = await self.task_repository.find_task_by_id(task_id)
        return task

    async def create_task(self, task_data: TaskCreateSchema):
        task = await self.task_repository.create_task(task_data.__dict__)
        await self.service_websocket.broadcast(task)
        return handle_response(app_status=AppStatus.TASK_CREATED)

    async def assign_task(self, user_id: int):
        old_task = await self.task_repository.find_task_by_user(user_id)
        task = old_task if old_task else await self.task_repository.find_task_not_assigned()
        self._check_exist_task(task)
        version = task.get("version")
        time_assign = datetime.now(tz=timezone.utc) + timedelta(minutes=3)
        updated_rows = await self.task_repository.update_user_assign(
            task.get("id"), user_id, time_assign, version
        )
        if updated_rows == 0:
            raise error_exception_handler(AppStatus.ERROR_TASK_NOT_FOUND)

        return task

    async def assign_task_et(self, list_data_assign: list):
        conditions = TaskAssignETSet().conditions_set
        """
        Example:
        {
            "data": [{"batch_id" : 1, "rack_name": "AA-odd", "user_e": 2, "user_view_e": 3}, {"batch_id" : 1,"rack_name": "AB-odd", "user_e": 2, "user_view_e": 3}]
        }
        """
        await self.task_repository.assign_task_et(list_data_assign, conditions)
        return handle_response(app_status=AppStatus.TASK_ASSIGNED)

    @staticmethod
    async def get_role_mapping_by_user(role_request, user_roles):
        for role in user_roles:
            if role_request in role:
                return role
        return None

    async def submit_task(self, result: dict, task_id: int, release: bool, role_request: str,
                          user_assign: dict, report_task: dict, progress: int):
        """
        Example:
        result = {
            "BE-071": {"BE-071-5": {}, "BE-071-6": {}},
            "BE-073": {"BE-073-0": {}, "BE-073-6": {}}
        }
        role_request: ENTRY or CHECKER
        """

        task = await self.task_repository.find_task_by_id(task_id)
        self._check_exist_task(task)

        result_field = self._get_field_by_role(role_request, "result")
        time_submit_field = self._get_field_by_role(role_request, "time_submit")

        self._check_permission_task(task, user_assign, role_request)
        task_data = {
            result_field: result,
            time_submit_field: datetime.now(tz=timezone.utc),
            "release": release,
            "status": TaskStatus.COMPLETED if release else TaskStatus.IN_PROGRESS,
            "report_task": report_task,
            "progress": progress,
        }
        if release:
            task_data.update(self.update_result_checker_when_entry_release(role_request, result))
        await self.task_repository.update_task(task_id, task_data)
        return handle_response(app_status=AppStatus.TASK_SUBMITTED)

    @staticmethod
    def update_result_checker_when_entry_release(role_request, result_e) -> dict:
        if role_request == TaskRole.ENTRY:
            return {"result_c": result_e}
        return {}

    async def update_time_process_task(self, time_process: dict, task_id: int, role_request: str, user_assign: dict):
        """
        Example:
        time_process = {
            "BE-071": {"BE-071-5": 12, "BE-071-6": 16},
            "BE-073": {"BE-073-0": 20, "BE-073-6": 40}
        }
        role_request: ENTRY or CHECKER
        """

        task = await self.task_repository.find_task_by_id(task_id)
        self._check_exist_task(task)
        self._check_permission_task(task, user_assign, role_request)

        time_process_field = self._get_field_by_role(role_request, "time_process")
        task_data = {
            time_process_field: time_process
        }
        await self.task_repository.update_task(task_id, task_data)
        return handle_response(app_status=AppStatus.TASK_UPDATED_PROCESS)

    async def flag_task(self, task_id: int, user: dict, data: dict, role_request: str):
        """
        Example:
        data = {
            "BE-071": {"BE-071-3": {"reason": "string", "note": "string"}}
        }
        role_request: ENTRY or CHECKER
        """
        task = await self.task_repository.find_task_by_id(task_id)
        self._check_exist_task(task)
        self._check_permission_task(task, user, role_request)

        flags_field = self._get_field_by_role(role_request, "flags")
        task_data = {flags_field: data}
        await self.task_repository.update_task(task_id, task_data)
        return handle_response(app_status=AppStatus.TASK_FLAGGED)

    async def update_result_task(self, task_id: int, user: dict, result_data: TaskUpdateResultMiniSchema,
                                 role_request: str):
        """
        Example:
        {
            "keys": ["['BE-071']['BE-071-3']"],
            "values": [{"image": [], "video": "video url", "alo": 123}]
        }
        role_request: ENTRY or CHECKER
        """

        task = await self.task_repository.find_task_by_id(task_id)
        self._check_exist_task(task)
        self._check_permission_task(task, user, role_request)
        result_field = self._get_field_by_role(role_request, "result")

        result = task.get(result_field, {})
        for key, value in zip(result_data.keys, result_data.values):
            try:
                current_data = eval("result" + key)
                current_data.update(value)
            except Exception:
                raise error_exception_handler(AppStatus.ERROR_TASK_INVALID_DATA)

        task_data = {result_field: result, "report_task": result_data.report_task, "progress": result_data.progress}
        await self.task_repository.update_task(task_id, task_data)

        await self.task_repository.update_task(task_id, task_data)
        return handle_response(app_status=AppStatus.TASK_RESULT_UPDATED)

    async def create_tasks(self, tasks_data: list):
        await self.task_repository.create_tasks(tasks_data)
        return handle_response(app_status=AppStatus.TASK_CREATED)

    async def preview_task(self, batch_id: int, tenant_id: int):
        tasks = await self.task_repository.preview_task(batch_id, tenant_id)
        result = dict(batch_id=batch_id, tasks=tasks)
        return result

    async def check_racks_name_in_progress(self, batch_id, rack_names):
        tasks = await self.task_repository.get_tasks_by_racks_name_and_batch_id(batch_id, rack_names,
                                                                                [TaskStatus.COMPLETED])
        return len(tasks) > 0

    async def change_user_assign(self, delete_racks: list, add_racks: list, batch_id: int, user_e: int,
                                 user_view_e: int):
        if (delete_racks and await self.check_racks_name_in_progress(batch_id, delete_racks)) or (
                add_racks and await self.check_racks_name_in_progress(
                batch_id, add_racks)):
            raise error_exception_handler(AppStatus.ERROR_TASK_IN_PROGRESS)
        list_data_update = []
        for rack_name in delete_racks:
            list_data_update.append(
                {"batch_id": batch_id, "rack_name": rack_name, "user_e": None, "user_view_e": None})
        for rack_name in add_racks:
            list_data_update.append(
                {"batch_id": batch_id, "rack_name": rack_name, "user_e": user_e or 0, "user_view_e": user_view_e or 0})
        return await self.assign_task_et(list_data_update) if list_data_update else []

    async def get_task_of_user_progress(self, user_ids: list):
        return await self.task_repository.get_task_of_user_progress(user_ids)

    async def update_user_for_active_racks(self, batch_id: int, racks: list, user_e: int, user_view_e: int):
        await self.task_repository.update_user_for_active_racks(racks, batch_id, user_e, user_view_e)

    async def working_task(self, task_id: int, user: dict):
        task = await self.task_repository.find_task_by_id(task_id)
        self._check_exist_task(task)
        self._check_permission_task(task, user)

        time_start = datetime.now(tz=timezone.utc)
        task_data = {
            "status": TaskStatus.IN_PROGRESS,
            "start_time_working": time_start
        }
        return await self.task_repository.update_task(task_id, task_data)

    async def process_data_of_ai(self, data: dict, rack_name: str, tenant_id: int, batch_id: int):
        task = await self.task_repository.find_task_by_rack_name(rack_name, tenant_id, batch_id)
        self._check_exist_task(task)
        result = task.get('result_e') if task.get('result_e') else {}
        new_result = {}
        for k, v in data.items():
            key = '-'.join(str(k).split("-", 2)[:2])
            new_result.setdefault(key, {})[k] = v

        for rack, items in new_result.items():
            for slot, fields in items.items():
                if rack in result and slot in result[rack]:
                    result[rack][slot].update(fields)
                else:
                    result.setdefault(rack, {})[slot] = fields

        task_data = {
            "result_e": result,
            "total_progress": sum(len(v) for v in result.values())
        }
        return await self.task_repository.update_task(task.get("id"), task_data)

    async def export_data(self, user: dict, batch_id: int):
        start_time = time.time()
        batch = await self.batch_repository.get_batch(batch_id)
        if not batch:
            raise error_exception_handler(AppStatus.ERROR_BATCH_NOT_FOUND)

        self._checker_permission_task(user=user)
        tasks = await self.task_repository.find_task_by_batch_id(batch_id)
        if not tasks:
            raise error_exception_handler(AppStatus.ERROR_EXPORT_NO_DATA)
        end_time = time.time()

        data_export = []
        for row in tasks:
            data_export.extend(row.get("report_task"))
        print("READ:", end_time - start_time)

        start_time_1 = time.time()
        result = await self.export_data_for_tasks(data_export)
        end_time_1 = time.time()
        print("EXPORT:", end_time_1 - start_time_1)
        return result

    # export direct by result from database

    async def export_data_for_tasks(self, tasks_data: list):
        if not tasks_data:
            raise error_exception_handler(AppStatus.ERROR_EXPORT_NO_DATA)
        return self.run_go_export(tasks_data)

    @staticmethod
    def run_go_export(tasks):

        data = json.dumps(tasks)
        result = subprocess.run(
            ["./export"],
            input=data,
            capture_output=True,
            text=True
        )

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        result.check_returncode()

        file_path = result.stdout.strip()
        try:
            with open(file_path, "rb") as f:
                excel_bytes = f.read()
            return excel_bytes
        finally:
            os.remove(file_path)
