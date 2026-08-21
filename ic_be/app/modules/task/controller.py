import io
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.constant.enums import UserRole
from app.core.app_status import AppStatus
from app.modules.auth.middleware import AuthMiddleware
from app.modules.batch.dependencies import get_batch_service
from app.modules.task.dependencies import get_task_service
from app.modules.task.schemas import SubmitTaskSchema, TaskCreateSchema, TaskAssignETSchema, ParamSubmitTaskSchema, \
    TaskUpdateResultMiniSchema, TaskRole, TimeTaskSchema, ParamProcessTaskSchema
from app.modules.task.service import TaskService
from app.modules.temp_data.dependancies import get_temp_data_service
from app.utils.response import handle_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{task_id:int}")
async def get_task_by_id(task_id: int,
                         task_service: TaskService = Depends(get_task_service),
                         _=Depends(AuthMiddleware.get_current_user)):
    task = await task_service.get_task_by_id(task_id)
    return task


@router.get("/list_tasks")
async def get_tasks(tenant_id: int, skip: int = 0, limit: int = 10,
                    task_service: TaskService = Depends(get_task_service),
                    _=Depends(AuthMiddleware.get_current_user)):
    task = await task_service.get_tasks(tenant_id, skip, limit)
    return task


@router.get("/my_tasks")
async def my_tasks(skip: int = 0, limit: int = 10, batch_id: int = None,
                   task_service: TaskService = Depends(get_task_service),
                   batch_service=Depends(get_batch_service),
                   auth=Depends(AuthMiddleware.get_current_user)):
    if batch_id is None:
        batch_id = await batch_service.get_active_batch(auth.get('tenant_id', 1))

    task = await task_service.my_tasks(auth, skip, limit, batch_id)
    return task


@router.put("", description="""
    This API receives AI processing results.

    **Parameters**:
    - `rack_name`: Rack name with format `<AA,BB>-<odd/even>`.  
      Example: `AA-odd`, `BB-even`.

    - `data`: Dictionary containing AI output to be processed.

    - `tenant_id`: Tenant identifier (default = 1).
    """)
async def update_media(rack_name: str, data: dict, tenant_id: int = 1,
                       task_service: TaskService = Depends(get_task_service),
                       temp_data_service=Depends(get_temp_data_service),
                       batch_service=Depends(get_batch_service)):
    """
    This API is used to receive information returned from AI, which will be processed and updated into the ET results.
    """

    batch_id_latest = await batch_service.get_active_batch(tenant_id)
    if batch_id_latest:
        logging.info("New batch detected: %s", batch_id_latest)
        await task_service.process_data_of_ai(data, rack_name, tenant_id, batch_id_latest)
    else:
        logging.info("No new batch")
        await temp_data_service.process_data_of_ai(data, rack_name, tenant_id)
    return handle_response(app_status=AppStatus.SUCCESS)


@router.put("/assign_task")
async def assign_task(task_service: TaskService = Depends(get_task_service),
                      auth=Depends(AuthMiddleware.is_user([UserRole.ENTRY]))):
    user_id = auth.get("id")
    task = await task_service.assign_task(user_id)
    return task


@router.put("/assign_task_et")
async def assign_task_et(data_assign: TaskAssignETSchema,
                         task_service: TaskService = Depends(get_task_service),
                         _=Depends(AuthMiddleware.get_current_user)):
    task = await task_service.assign_task_et(data_assign.data)
    return task


@router.put("/{task_id:int}/start_working")
async def working(task_id: int, task_service: TaskService = Depends(get_task_service),
                  auth=Depends(AuthMiddleware.get_current_user)):
    task = await task_service.working_task(task_id, auth)
    return handle_response(task)


@router.put("/{task_id:int}/submit_task")
async def submit_task(body: SubmitTaskSchema,
                      param: ParamSubmitTaskSchema = Depends(),
                      task_service: TaskService = Depends(get_task_service),
                      auth=Depends(AuthMiddleware.get_current_user)):
    task = await task_service.submit_task(result=body.result, task_id=param.task_id,
                                          release=param.task_release, role_request=param.role_request,
                                          user_assign=auth, report_task=body.report_task, progress=body.progress)
    return task


@router.put("/{task_id:int}/time_process_task")
async def time_process_task(body: TimeTaskSchema,
                            param: ParamProcessTaskSchema = Depends(),
                            task_service: TaskService = Depends(get_task_service),
                            auth=Depends(AuthMiddleware.get_current_user)):
    task = await task_service.update_time_process_task(time_process=body.time_process, task_id=param.task_id,
                                                       role_request=param.role_request, user_assign=auth)
    return task


@router.put("/{task_id:int}/flag")
async def flag_task(task_id: int, role_request: TaskRole, flags: dict,
                    task_service: TaskService = Depends(get_task_service),
                    user=Depends(AuthMiddleware.get_current_user)):
    task = await task_service.flag_task(task_id, user, flags, role_request)
    return task


@router.put("/{task_id:int}/update_result")
async def update_result(task_id: int, role_request: TaskRole, result_data: TaskUpdateResultMiniSchema,
                        task_service: TaskService = Depends(get_task_service),
                        user=Depends(AuthMiddleware.get_current_user)):
    task = await task_service.update_result_task(task_id, user, result_data, role_request)
    return task


@router.post("/create_task")
async def create_task(task_data: TaskCreateSchema,
                      task_service: TaskService = Depends(get_task_service)):
    task = await task_service.create_task(task_data)
    return task


@router.get("/export_data")
async def export_data(
        batch_id: int,
        task_service: TaskService = Depends(get_task_service),
        user=Depends(AuthMiddleware.get_current_user)
):
    output = await task_service.export_data(user, batch_id)

    headers = {
        'Content-Disposition': 'attachment; filename="export_data.xlsx"'
    }
    return StreamingResponse(
        io.BytesIO(output),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )
