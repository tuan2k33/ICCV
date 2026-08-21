from typing import Optional, List

from fastapi import Query
from pydantic import BaseModel, Field, field_validator

from app.constant.enums import UserRole, CompanyNameEnum
from app.utils.validator import validate_fullname


class LoginSchema(BaseModel):
    username: str
    password: str


class GetUserSchema(BaseModel):
    roles: Optional[UserRole] = None
    tenant_id: Optional[int] = None
    company: Optional[str] = None
    fullname: Optional[str] = None
    skip: Optional[int] = 0
    limit: Optional[int] = 10


class RegisterSchema(BaseModel):
    fullname: str
    username: str
    password: str
    phone_number: str
    company: Optional[CompanyNameEnum] = None
    tenant_id: int
    roles: Optional[List[UserRole]] = None

    @field_validator('fullname')
    def validate_fullname(cls, v: str) -> str:
        if not validate_fullname(v):
            raise ValueError("Fullname cannot contain numbers or special characters")
        return v


class UserUpdateSchema(BaseModel):
    fullname: str | None = None
    phone_number: str | None = None
    username: str | None = None
    password: str | None = None


class CheckExistPhoneNumberSchema(BaseModel):
    phone_numbers: List[str] = Field(Query(), examples=[["0912345678", "0912345679"]])

class UserFilterSchema(BaseModel):
    fullname__ilike: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    company: Optional[CompanyNameEnum] = None


class UserDeleteSchema(BaseModel):
    data: List[dict] = Field(examples=[[{"id": 1, "is_active": False}, {"id": 2, "is_active": False}]])
