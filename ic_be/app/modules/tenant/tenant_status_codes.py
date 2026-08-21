from starlette import status

# success
TENANT_CREATED = status.HTTP_201_CREATED, 201, "TENANT_CREATED", "Tenant created successfully."
TENANT_UPDATED = status.HTTP_200_OK, 200, "TENANT_UPDATED", "Tenant updated successfully."
TENANT_SETTING_UPDATED = status.HTTP_200_OK, 200, "TENANT_SETTING_UPDATED", "Tenant setting updated successfully."
TENANT_INFORMATION_UPDATED = status.HTTP_200_OK, 200, "TENANT_INFORMATION_UPDATED", "Tenant information updated successfully."

# error
ERROR_TENANT_NOT_FOUND = status.HTTP_404_NOT_FOUND, 404, "ERROR_TENANT_NOT_FOUND", "The requested tenant was not found."
