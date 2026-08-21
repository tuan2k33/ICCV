from starlette import status

# error
ERROR_BATCH_NOT_FOUND = status.HTTP_404_NOT_FOUND, 404, "ERROR_BATCH_NOT_FOUND", "The requested batch was not found."
ERROR_EXPORT_NO_DATA = status.HTTP_404_NOT_FOUND, 4041, "ERROR_EXPORT_NO_DATA", "No data available to export."
ERROR_ACTIVE_BATCH_EXIST = status.HTTP_400_BAD_REQUEST, 400, "ERROR_ACTIVE_BATCH_EXIST", "An active batch already exists."
