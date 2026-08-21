from fastapi import Depends

from app.infra.database import get_conn
from app.modules.batch.repository import BatchRepository
from app.modules.batch.service import BatchService


def get_batch_repository(db=Depends(get_conn)):
    return BatchRepository(db)


def get_batch_service(batch_repository: BatchRepository = Depends(get_batch_repository)):
    return BatchService(batch_repository)
