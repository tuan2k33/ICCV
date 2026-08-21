from fastapi import APIRouter, Depends

from app.constant.enums import UserRole, CompanyNameEnum
from app.core.app_status import AppStatus
from app.modules.auth.dependencies import get_auth_service
from app.modules.auth.middleware import AuthMiddleware
from app.modules.auth.service import AuthService
from app.modules.batch.dependencies import get_batch_service
from app.modules.batch.schemas import BatchCreateSchema
from app.modules.batch.service import BatchService
from app.modules.counting_group.dependencies import get_counting_group_service
from app.modules.counting_group.schemas import ChangeRackForGroupSchema, GroupCountingSchema, SubmitCountingGroupSchema, \
    ChangeRackForGroup
from app.modules.counting_group.service import CountingGroupService
from app.modules.task.dependencies import get_task_service
from app.modules.task.distribute import DistributeTask
from app.modules.task.service import TaskService
from app.modules.temp_data.dependancies import get_temp_data_service
from app.modules.temp_data.service import TempDataSevice
from app.modules.tenant.dependencies import get_tenant_service
from app.modules.tenant.service import TenantService
from app.utils.response import handle_response, error_exception_handler

router = APIRouter()


@router.get("")
async def get_all_group_counting(
        batch_id: int,
        convert_racks: bool = False,
        service: CountingGroupService = Depends(get_counting_group_service),
        _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))
):
    result = await service.get_counting_group(batch_id, convert_racks)
    return handle_response(response=result)


@router.get("/process")
async def get_all_group_counting(
        batch_id: int,
        service: CountingGroupService = Depends(get_counting_group_service),
        _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))
):
    response = await service.get_process(batch_id)
    return response


@router.post("/random")
async def random_group_counting(
        tenant_id: int,
        group_service: CountingGroupService = Depends(get_counting_group_service),
        user_service: AuthService = Depends(get_auth_service),
        tenant_service: TenantService = Depends(get_tenant_service),
        _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    user_company_1 = await user_service.get_user_by_company(CompanyNameEnum.LINFOX, tenant_id, [UserRole.ENTRY])
    user_company_2 = await user_service.get_user_by_company(CompanyNameEnum.UNILEVER, tenant_id, [UserRole.ENTRY])
    tenant_info = await tenant_service.get_information_tenant_by_id(tenant_id)
    racks = list(tenant_info.get("information").get("racks", {}).keys())

    task_assigns = await group_service.random_counting_group(user_company_1, user_company_2, racks)
    return handle_response(task_assigns)


@router.post("/submit")
async def submit_group_counting(
        req: SubmitCountingGroupSchema,
        group_service: CountingGroupService = Depends(get_counting_group_service),
        tenant_service: TenantService = Depends(get_tenant_service),
        task_service: TaskService = Depends(get_task_service),
        temp_data_service: TempDataSevice = Depends(get_temp_data_service),
        batch_service: BatchService = Depends(get_batch_service),
        auth=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    batch_id = await batch_service.get_active_batch(req.tenant_id)
    if batch_id:
        raise error_exception_handler(AppStatus.ERROR_ACTIVE_BATCH_EXIST)
    batch = await batch_service.create_batch(BatchCreateSchema(tenant_id=req.tenant_id), auth.get("id"))
    await tenant_service.get_tenant_by_id(req.tenant_id)
    temp_data = await temp_data_service.get_temp_data_by_tenant_id(req.tenant_id)
    if not temp_data:
        temp_data = await tenant_service.reload_temp_data(req.tenant_id, temp_data_service)
    task_distribute = DistributeTask(batch_id=batch.get("id"),
                                     task_service=task_service,
                                     temp_data=temp_data)
    await task_distribute.excuse()
    task_assigns = await group_service.save_counting_group(req.data, batch.get('id'))
    if task_assigns:
        await task_service.assign_task_et(task_assigns)
    return handle_response(task_assigns)


@router.put("/change_user_in_group", description="""
This API changes the user in the group.

**Parameters**:
- `user_id_1`: user_id of the Linfox company.
- `user_id_2`: user_id of the Unilever company.
- `fullname_1`: fullname of the Linfox company.
- `fullname_2`: fullname of the Unilever company.
""")
async def change_user_in_group(
        req: GroupCountingSchema,
        group_service: CountingGroupService = Depends(get_counting_group_service),
        tasks_service: TaskService = Depends(get_task_service),
        _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    group = await group_service.change_user_in_group(req.model_dump())

    await tasks_service.update_user_for_active_racks(group.get('batch_id'), group.get('racks') or [],
                                                     group.get('user_id_2'),
                                                     group.get('user_id_1'))
    return handle_response(group)


@router.post("/export")
async def export_group_counting(batch_id: int, service=Depends(get_counting_group_service),
                                _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    result = await service.export_group_counting(batch_id)
    return result


@router.post("/move_rack")
async def move_rack(req: ChangeRackForGroup, group_service: CountingGroupService = Depends(get_counting_group_service),
                    tasks_service: TaskService = Depends(get_task_service),
                    _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    result = await group_service.move_rack_to_group(**req.model_dump())
    await tasks_service.change_user_assign([], [req.rack_name],
                                           result.get("batch_id"), user_e=result.get("user_id_2"),
                                           user_view_e=result.get("user_id_1"))
    return handle_response(app_status=AppStatus.SUCCESS)


@router.put("/change_racks_in_group")
async def change_racks_in_group(
        req: ChangeRackForGroupSchema,
        group_service: CountingGroupService = Depends(get_counting_group_service),
        tasks_service: TaskService = Depends(get_task_service),
        _=Depends(AuthMiddleware.is_user([UserRole.ADMIN]))):
    result = await group_service.sync_group_racks(req.group_id, req.racks)
    await tasks_service.change_user_assign(result.get("deleted_racks"), result.get('added_racks'),
                                           result.get('group').get("batch_id"), result.get('group').get("user_id_2"),
                                           result.get('group').get("user_id_1"))
    return handle_response(app_status=AppStatus.SUCCESS)
