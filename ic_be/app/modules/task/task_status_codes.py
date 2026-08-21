from starlette import status

# success
TASK_CREATED = status.HTTP_201_CREATED, 201, "TASK_CREATED", "Task created successfully."
TASK_UPDATED = status.HTTP_200_OK, 200, "TASK_UPDATED", "Task updated successfully."
TASK_FLAGGED = status.HTTP_200_OK, 200, "TASK_FLAGGED", "Task flagged successfully."
TASK_UPDATED_PROCESS = status.HTTP_200_OK, 200, "TASK_UPDATED_PROCESS", "Task update process data successfully."
TASK_RESULT_UPDATED = status.HTTP_200_OK, 200, "TASK_RESULT_UPDATED", "Task result updated successfully."
TASK_SUBMITTED = status.HTTP_200_OK, 200, "TASK_SUBMITTED", "Task submitted successfully."
TASK_ASSIGNED  = status.HTTP_200_OK, 200, "TASK_ASSIGNED", "Task assigned successfully."


# error
ERROR_TASK_NOT_FOUND = status.HTTP_404_NOT_FOUND, 404, "ERROR_TASK_NOT_FOUND", "The requested task was not found."
ERROR_TASK_RESULT_NOT_EXITS = status.HTTP_400_BAD_REQUEST, 400, "ERROR_TASK_RESULT_NOT_EXITS", "The result task not exits."
ERROR_INVALID_DATA = status.HTTP_400_BAD_REQUEST, 400, "ERROR_INVALID_DATA", "The provided data is invalid."
ERROR_TASK_IN_PROGRESS = status.HTTP_403_FORBIDDEN, 403, 'ERROR_TASK_IN_PROGRESS', "There is already a task running that cannot perform this action"