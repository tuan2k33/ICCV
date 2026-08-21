from fastapi import Depends

from app.infra.database import get_conn
from app.modules.counting_group.repository import CountingGroupRepository
from app.modules.counting_group.service import CountingGroupService
from app.modules.task.repository import TaskRepository


def get_task_repository(db=Depends(get_conn)):
    return TaskRepository(db)


def get_counting_group_repository(db=Depends(get_conn)):
    return CountingGroupRepository(db)


def get_counting_group_service(
        counting_group_repository: CountingGroupRepository = Depends(get_counting_group_repository),
        task_repository: TaskRepository = Depends(get_task_repository)
):
    return CountingGroupService(counting_group_repository, task_repository)
