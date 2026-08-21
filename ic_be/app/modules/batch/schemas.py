from typing import Optional

from enum import Enum
from pydantic import BaseModel

class BatchStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"

class BatchCreateSchema(BaseModel):
    """
    Schema for creating a batch.
    """
    tenant_id: Optional[int]
    code: Optional[str] = ""
    status: Optional[BatchStatus] = BatchStatus.ACTIVE


class BatchUpdateSchema(BaseModel):
    """
    Schema for updating a batch.
    """
    status: Optional[BatchStatus]
