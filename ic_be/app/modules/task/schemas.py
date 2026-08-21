from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class TaskRole(str, Enum):
    ENTRY = "ENTRY"
    CHECKER = "CHECKER"


class SubmitTaskSchema(BaseModel):
    """
    Schema for submitting a task.
    """
    result: dict
    report_task: Optional[List[dict]] = Field(examples=[[{"Even/odd": "AE-009-3", "Level": 1, "Count sheet": "12", }]])
    progress: int = 0


class TimeTaskSchema(BaseModel):
    """
    Schema for submitting a task.
    """
    time_process: dict


class ParamProcessTaskSchema(BaseModel):
    task_id: int
    role_request: TaskRole


class ParamSubmitTaskSchema(ParamProcessTaskSchema):
    task_release: bool = False


class TaskCreateSchema(BaseModel):
    rack_name: str
    batch_id: int
    tenant_id: int
    result_e: Optional[dict] = None
    report_task: Optional[List[dict]] = None
    total_progress: int = 0


class TaskAssignETSchema(BaseModel):
    data: list[dict] = Field(examples=[[{"batch_id": 1, "rack_name": "AA-..", "user_e": 1, "user_view_e": 2},
                                        {"batch_id": 1, "rack_name": "AB-..", "user_e": 3, "user_view_e": 4}]])


class TaskAssignETSet(BaseModel):
    conditions_set: list[str] = ["batch_id", "rack_name"]


class TaskUpdateResultMiniSchema(BaseModel):
    keys: Optional[List[str]] = Field(examples=[["['BE-071']['BE-071-1']", "['BE-071']['BE-071-2']"]])
    values: Optional[List[dict]] = Field(examples=[[{"image": [], 'video': 'video url'}, {"image": [], 'video': ''}]])
    report_task: Optional[List[dict]] = Field(examples=[[{"Even/odd": "AE-009-3", "Level": 1, "Count sheet": "12", }]])
    progress: int = 0
