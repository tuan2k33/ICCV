from pydantic import BaseModel


class ChangeRackForGroupSchema(BaseModel):
    racks: list
    group_id: int
    tenant_id: int
    batch_id: int


class GroupCountingSchema(BaseModel):
    user_id_1: int
    fullname_1: str
    user_id_2: int
    fullname_2: str
    id: int

class SubmitCountingGroupSchema(BaseModel):
    tenant_id: int
    data: list


class ChangeRackForGroup(BaseModel):
    rack_name: str
    group_from_id: int
    group_to_id: int
