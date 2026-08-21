from fastapi import APIRouter, Depends

from app.core.app_status import AppStatus
from app.constant.enums import UserRole, CompanyNameEnum
from app.modules.auth.dependencies import get_auth_service
from app.modules.auth.middleware import AuthMiddleware
from app.modules.auth.service import AuthService
from app.modules.batch.dependencies import get_batch_service
from app.modules.batch.schemas import BatchCreateSchema, BatchUpdateSchema
from app.modules.batch.service import BatchService
from app.modules.counting_group.dependencies import get_counting_group_service
from app.modules.counting_group.service import CountingGroupService
from app.modules.task.dependencies import get_task_service
from app.modules.task.distribute import DistributeTask
from app.modules.task.service import TaskService
from app.modules.tenant.dependencies import get_tenant_service
from app.modules.tenant.service import TenantService
from app.utils.response import handle_response

router = APIRouter()


@router.get("")
async def get_all(skip: int = 0, limit: int = 10, service: BatchService = Depends(get_batch_service)):
    """
    Endpoint to get a list of batch processes.
    """
    total, batches = await service.get_list(skip, limit)
    return handle_response({"total": total, "batches": batches})


@router.get("/preview")
async def preview(
        batch_id: int = None,
        batch_service: BatchService = Depends(get_batch_service),
        task_service: TaskService = Depends(get_task_service),
        auth_info: dict = Depends(AuthMiddleware.get_current_user)):
    """
    Endpoint to preview batch processing results.
    """
    tenant_id = 1
    if batch_id is None:
        batch_id = await batch_service.get_active_batch(tenant_id)
    if not batch_id:
        return handle_response(app_status=AppStatus.ERROR_BATCH_NOT_FOUND)
    result = await task_service.preview_task(batch_id, tenant_id)
    return handle_response(response=result)


@router.get("/active")
async def get_batch_in_active(tenant_id: int = 1, service: BatchService = Depends(get_batch_service),
                              auth=Depends(AuthMiddleware.get_current_user)):
    tenant_id = auth.get('tenant_id', 1) if auth.get('tenant_id', 1) is not None else tenant_id
    batch = await service.get_active_batch(tenant_id)
    return handle_response(response=batch)


@router.get("/{batch_id}")
async def get(batch_id: str, service: BatchService = Depends(get_batch_service)):
    """
    Endpoint to get a specific batch process by its ID.
    """
    batch = await service.get_batch(batch_id)
    if not batch:
        return handle_response({"message": "Batch not found"}, app_status=AppStatus.NOT_FOUND)
    return batch


@router.post("")
async def create(batch_data: BatchCreateSchema,
                 group_service: CountingGroupService = Depends(get_counting_group_service),
                 user_service: AuthService = Depends(get_auth_service),
                 batch_service: BatchService = Depends(get_batch_service),
                 tenant_service: TenantService = Depends(get_tenant_service),
                 task_service: TaskService = Depends(get_task_service),
                 auth_info=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    """
    Endpoint to start batch processing.
    """

    result = await batch_service.create_batch(batch_data, auth_info.get("id"))
    tenant = await tenant_service.get_information_tenant_by_id(batch_data.tenant_id)
    task_distribute = DistributeTask(batch_id=result.get("id"), tenant_id=batch_data.tenant_id,
                                     task_service=task_service,
                                     tenant_info=tenant.get('information', {}),
                                     )
    await task_distribute.excuse()

    user_company_1 = await user_service.get_user_by_company(CompanyNameEnum.LINFOX, batch_data.tenant_id,
                                                            [UserRole.ENTRY])
    user_company_2 = await user_service.get_user_by_company(CompanyNameEnum.UNILEVER, batch_data.tenant_id,
                                                            [UserRole.ENTRY])
    racks = list(task_distribute.__racks_info__().keys())

    task_assigns = await group_service.random_counting_group(user_company_1, user_company_2, racks, result.get("id"))
    await task_service.assign_task_et(task_assigns)
    return result


@router.put("/{batch_id}")
async def update(batch_id: str, batch_data: BatchUpdateSchema, service: BatchService = Depends(get_batch_service),
                 _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    """
    Endpoint to update a specific batch process.
    """
    return await service.update_batch(batch_id, batch_data)
