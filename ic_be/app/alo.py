from app.constant.enums import UserRole
from app.modules.task.schemas import TaskRole

ALLOWED_ROLES = {
    TaskRole.ENTRY: {UserRole.ENTRY_1, UserRole.ENTRY_2},
    TaskRole.CHECKER: {UserRole.CHECKER, UserRole.ADMIN}
}

def permission_task(role_request, user_roles):
    allowed = ALLOWED_ROLES.get(role_request, set())
    if not any(role in allowed for role in user_roles):
        raise ValueError("Không có quyền thực hiện tác vụ này.")
# --- Ví dụ sử dụng ---
current_user_roles = [UserRole.ADMIN]


print(permission_task(TaskRole.ENTRY, current_user_roles))
