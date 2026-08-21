from fastapi import APIRouter, Depends, UploadFile
from fastapi.params import File

from app.core.app_status import AppStatus
from app.modules.auth.middleware import AuthMiddleware
from app.modules.temp_data.dependancies import get_temp_data_service
from app.modules.temp_data.service import TempDataSevice
from app.modules.tenant.dependencies import get_tenant_service
from app.modules.tenant.schemas import TenantCreateSchema, ParamTenantIdSchema, TenantUpdateSchema, \
    TenantUpdateSettingsSchema, TenantUpdateInformationSchema
from app.modules.tenant.service import TenantService
from app.utils.response import handle_response

router = APIRouter()


@router.get("/{tenant_id}")
async def get_tenant_by_id(query: ParamTenantIdSchema = Depends(),
                           tenant_service: TenantService = Depends(get_tenant_service),
                           _=Depends(AuthMiddleware.get_current_user)):
    response = await tenant_service.get_tenant_by_id(tenant_id=query.tenant_id)
    return response


@router.get("/{tenant_id}/settings")
async def get_settings_tenant_by_id(query: ParamTenantIdSchema = Depends(),
                                    tenant_service: TenantService = Depends(get_tenant_service),
                                    _=Depends(AuthMiddleware.get_current_user)):
    response = await tenant_service.get_settings_tenant_by_id(tenant_id=query.tenant_id)
    return response


@router.get("/{tenant_id}/information")
async def get_information_tenant_by_id(query: ParamTenantIdSchema = Depends(),
                                       tenant_service: TenantService = Depends(get_tenant_service),
                                       _=Depends(AuthMiddleware.get_current_user)):
    response = await tenant_service.get_information_tenant_by_id(tenant_id=query.tenant_id)
    return response


@router.get("/{tenant_id}/information/racks")
async def get_racks_tenant_by_id(tenant_id: int, rack: str,
                                 tenant_service: TenantService = Depends(get_tenant_service),
                                 _=Depends(AuthMiddleware.get_current_user)):
    response = await tenant_service.get_information_tenant_by_id(tenant_id=tenant_id)
    racks = response.get("information", {}).get("racks", {}).get(rack, {})
    return handle_response(racks)


@router.post("")
async def create_tenant(tenant_data: TenantCreateSchema,
                        tenant_service: TenantService = Depends(get_tenant_service),
                        _=Depends(AuthMiddleware.get_current_user)):
    response = await tenant_service.create_tenant(tenant_data)
    return response


@router.put("/{tenant_id}")
async def update_tenant(tenant_data: TenantUpdateSchema,
                        query: ParamTenantIdSchema = Depends(),
                        tenant_service: TenantService = Depends(get_tenant_service),
                        _=Depends(AuthMiddleware.get_current_user)):
    response = await tenant_service.update_tenant(tenant_id=query.tenant_id, tenant_data=tenant_data.model_dump())
    return response


@router.put("/{tenant_id}/settings")
async def update_settings_tenant(tenant_data: TenantUpdateSettingsSchema,
                                 query: ParamTenantIdSchema = Depends(),
                                 tenant_service: TenantService = Depends(get_tenant_service),
                                 _=Depends(AuthMiddleware.get_current_user)):
    response = await tenant_service.update_settings_tenant(tenant_id=query.tenant_id,
                                                           tenant_data=tenant_data.model_dump())
    return response


@router.put("/{tenant_id}/information")
async def update_information_tenant(tenant_data: TenantUpdateInformationSchema,
                                    query: ParamTenantIdSchema = Depends(),
                                    tenant_service: TenantService = Depends(get_tenant_service),
                                    _=Depends(AuthMiddleware.get_current_user)):
    response = await tenant_service.update_information_tenant(tenant_id=query.tenant_id,
                                                              tenant_data=tenant_data.model_dump())
    return response


@router.post("/{tenant_id}/information")
async def import_template(file: UploadFile = File(...),
                          query: ParamTenantIdSchema = Depends(),
                          temp_data_service: TempDataSevice = Depends(get_temp_data_service),
                          tenant_service: TenantService = Depends(get_tenant_service),
                          ):
    content = await file.read()
    temp_data = await tenant_service.import_template(tenant_id=query.tenant_id, content=content)
    await temp_data_service.bulk_insert_data(temp_data, tenant_id=query.tenant_id)
    return handle_response(app_status=AppStatus.TENANT_INFORMATION_UPDATED)
