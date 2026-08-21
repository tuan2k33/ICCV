from starlette import status

SUCCESS = status.HTTP_200_OK, 200, "SUCCESS", "Success."
BAD_REQUEST = status.HTTP_400_BAD_REQUEST, 400, "BAD_REQUEST", "The request is invalid."
NOT_FOUND = status.HTTP_404_NOT_FOUND, 404, "NOT_FOUND", "The requested resource was not found."
FORBIDDEN = status.HTTP_403_FORBIDDEN, 403, "FORBIDDEN", "You do not have permission to access this resource."
ERROR_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR, 500, "ERROR_INTERNAL_SERVER_ERROR", "An unexpected error occurred."
UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED, 401, "UNAUTHORIZED", "Authentication is required to access this resource."
