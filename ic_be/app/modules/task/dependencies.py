from fastapi import Depends

from app.infra.database import get_conn
from app.infra.websocket import socket_manage
from app.modules.batch.repository import BatchRepository
from app.modules.task.repository import TaskRepository
from app.modules.task.service import TaskService


def get_task_repository(db=Depends(get_conn)):
    return TaskRepository(db)


def get_batch_repository(db=Depends(get_conn)):
    return BatchRepository(db)


def get_task_service(task_repository: TaskRepository = Depends(get_task_repository),
                     batch_repository: BatchRepository = Depends(get_batch_repository)):
    return TaskService(task_repository, batch_repository, socket_manage)
