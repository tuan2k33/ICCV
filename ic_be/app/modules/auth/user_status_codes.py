from starlette import status

# success
LOGIN_SUCCESS  = status.HTTP_200_OK, 200, "LOGIN_SUCCESS", "Login successful."
LOGOUT_SUCCESS = status.HTTP_200_OK, 200, "LOGOUT_SUCCESS", "Logout successful."

# error
ERROR_LOGIN_INVALID       = status.HTTP_401_UNAUTHORIZED, 401, "ERROR_LOGIN_INVALID", "Invalid username or password."
ERROR_USER_ALREADY_EXISTS = status.HTTP_409_CONFLICT, 409, "ERROR_USER_ALREADY_EXISTS", "User already exists with the provided username or phone number."
ERROR_USER_PHONE_ALREADY_EXISTS = status.HTTP_409_CONFLICT, 409, "ERROR_USER_PHONE_ALREADY_EXISTS", "User already exists with the provided phone number."
ERROR_INVALID_ROLE        = status.HTTP_403_FORBIDDEN, 403, "ERROR_INVALID_ROLE", "The user role is not allowed to perform this action."
ERROR_USER_INACTIVE     = status.HTTP_403_FORBIDDEN, 403, "ERROR_USER_INACTIVE", "User account is inactive."
ERROR_USER_DATA_IMPORT   = status.HTTP_400_BAD_REQUEST, 400, "ERROR_USER_DATA_IMPORT", "There was an error importing user data."
ERROR_USER_MISSING_COLUMN  = status.HTTP_400_BAD_REQUEST, 400, "ERROR_USER_MISSING_COLUMN", "The uploaded file is missing required columns."

ERROR_USER_NOT_FOUND     = status.HTTP_404_NOT_FOUND, 404, "ERROR_USER_NOT_FOUND", "User not found."
