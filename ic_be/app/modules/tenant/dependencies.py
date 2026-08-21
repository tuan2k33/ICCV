from fastapi import Depends

from app.infra.database import get_conn
from app.modules.tenant.repository import TenantRepository
from app.modules.tenant.service import TenantService


def get_tenant_repository(db=Depends(get_conn)):
    return TenantRepository(db)


def get_tenant_service(tenant_repository: TenantRepository = Depends(get_tenant_repository)):
    return TenantService(tenant_repository)
