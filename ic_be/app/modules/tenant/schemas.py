from typing import Optional

from pydantic import BaseModel


class ParamTenantIdSchema(BaseModel):
    tenant_id: int


class TenantCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    banner: Optional[str] = None
    settings: Optional[dict] = None
    information: Optional[dict] = None


class TenantUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    banner: Optional[str] = None


class TenantUpdateSettingsSchema(BaseModel):
    settings: dict


class TenantUpdateInformationSchema(BaseModel):
    information: dict
