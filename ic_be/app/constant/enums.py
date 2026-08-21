from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    ENTRY = "ENTRY"
    CHECKER = "CHECKER"


class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REVIEW = "REVIEW"


class CompanyNameEnum(str, Enum):
    LINFOX = 'Linfox'
    UNILEVER = 'Unilever'
