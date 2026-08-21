from fastapi import Depends

from app.infra.database import get_conn
from app.modules.temp_data.repository import TempDataRepository
from app.modules.temp_data.service import TempDataSevice


def get_temp_data_repository(db=Depends(get_conn)):
    return TempDataRepository(db)


def get_temp_data_service(repo: TempDataRepository = Depends(get_temp_data_repository)):
    return TempDataSevice(repo)
