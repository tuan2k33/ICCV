from datetime import datetime

from app.constant.enums import TaskStatus
from app.constant.statements.task import TaskStatements
from app.utils.sql_builder import SQLBuilder


class TaskRepository:
    def __init__(self, db):
        self.db = db
        self.json_fields = {'flags_e', "flags_c", 'result_e', 'result_c', 'report_task'}
        self.query = SQLBuilder('tasks', self.json_fields)
        self.task_info_fields = ["id", "batch_id", "rack_name", "user_e", "flags_e", 'start_time_working',
                                 "user_c", "time_process_e", "time_process_c", 'progress', 'total_progress',
                                 "time_submit_e", "time_submit_c", "release", "status",
                                 "created_at", "updated_at"]
        self.task_info_fields_result = self.task_info_fields.copy()
        self.task_info_fields_result.append("result_e, result_c")

    async def __execute_single(self, query, params):
        await self.db.execute(query, params)
        return await self.db.fetchone()

    async def __execute_all(self, query, params):
        await self.db.execute(query, params)
        return await self.db.fetchall()

    async def create_task(self, task_data: dict):
        query = TaskStatements.INSERT_TASK
        await self.db.execute(query, (task_data.get("name"), task_data.get("images"), task_data.get("video"),))
        result = await self.db.fetchone()
        return result

    async def assign_task_et(self, data_assign: list, conditions_set: list = None):
        q, p = SQLBuilder('tasks', self.json_fields).bulk_update(data_assign, conditions_set).build()
        await self.db.execute(q, p)

    async def update_task_result(self, task_id: int, result: str, user_assign: int):
        query = TaskStatements.UPDATE_RESULT
        await self.db.execute(query, (result, task_id, user_assign))

    async def update_user_assign(self, task_id: int, user_id: int | None, time_assign: datetime, version: int):
        query = TaskStatements.UPDATE_USER_ASSIGN
        result = await self.db.execute(query, (user_id, time_assign, task_id, version))
        return result.rowcount

    async def find_task_not_assigned(self):
        query = TaskStatements.FIND_TASK_NOT_ASSIGNED
        await self.db.execute(query)
        return await self.db.fetchone()

    async def find_task_by_id(self, task_id: int):
        q, p = self.query.where(id=task_id).build()
        return await self.__execute_single(q, p)

    async def find_task_by_batch_id(self, batch_id: int):
        q, p = (self.query.select("report_task")
                .order_by('rack_name', 'ASC')
                .where(batch_id=batch_id, report_task__isnotnull=True).build())
        return await self.__execute_all(q, p)

    async def __fetch_page_with_total(self, query, skip, limit):
        q, p = query.copy().select().order_by('rack_name', 'ASC').offset(skip).limit(limit).build()
        tasks = await self.__execute_all(q, p)

        q, p = query.count().build()
        total = await self.__execute_single(q, p)
        return {"total": total.get('count'), "tasks": tasks}

    async def get_tasks(self, tenant_id: int, skip: int = None, limit: int = None):
        query = (self.query.select(*self.task_info_fields)
                 .where(release=False, tenant_id=tenant_id))
        return await self.__fetch_page_with_total(query, skip, limit)

    async def get_completed_tasks(self, batch_id: int):
        q, p = self.query.select('rack_name').where(batch_id=batch_id, status="COMPLETED").build()
        return await self.__execute_all(q, p)

    async def get_tasks_by_status(self, batch_id: int, status: list):
        q, p = (self.query.select('id').where(batch_id=batch_id, status__in=status)).build()
        return await self.__execute_all(q, p)

    async def get_tasks_by_racks_name_and_batch_id(self, batch_id: int, rack_name: list, status: list):
        q, p = (self.query.select('id').where(batch_id=batch_id, rack_name__in=rack_name, status__in=status)).build()
        return await self.__execute_all(q, p)

    async def find_task_by_user(self, user_id: int, tenant_id: int, batch_id: int, skip: int = None,
                                limit: int = None, ):
        query = (self.query.select(*self.task_info_fields_result)
                 .where(tenant_id=tenant_id, batch_id=batch_id).where_or(user_e=user_id, user_view_e=user_id))
        return await self.__fetch_page_with_total(query, skip, limit)

    async def create_tasks(self, tasks_data: list):
        q, p = self.query.bulk_insert(tasks_data).build()
        return await self.__execute_all(q, p)

    async def update_task(self, task_id: int, task_data: dict):
        q, p = self.query.update(**task_data).where(id=task_id).build()
        return await self.__execute_single(q, p)

    async def preview_task(self, batch_id: int, tenant_id: int):
        q, p = (self.query.select("id", 'rack_name', 'status').
                order_by('rack_name', 'ASC').where(batch_id=batch_id, tenant_id=tenant_id).build())
        return await self.__execute_all(q, p)

    async def find_task_by_rack_name(self, rack_name: str, tenant_id: int, batch_id: int):
        q, p = self.query.select(*self.task_info_fields_result).where(rack_name=rack_name, tenant_id=tenant_id,
                                                                      batch_id=batch_id).build()
        return await self.__execute_single(q, p)

    async def update_user_for_active_racks(self, rack_names: list, batch_id: int, user_e: int, user_view_e: int):
        q, p = (self.query.update(user_e=user_e, user_view_e=user_view_e)
                .where(rack_name__in=rack_names, batch_id=batch_id,
                       status=TaskStatus.NOT_STARTED).build())
        await self.db.execute(q, p)
        return await self.db.fetchall()

    async def get_task_of_user_progress(self, user_ids: list):
        q, p = (self.query.select()
                .where(status=TaskStatus.IN_PROGRESS)
                .where_or(user_e__in=user_ids, user_view_e__in=user_ids)).build()
        await self.__execute_all(q, p)
        return await self.db.fetchall()
