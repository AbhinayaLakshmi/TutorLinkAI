from fastapi import HTTPException, status

class CredentialsException(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class RoleForbiddenException(HTTPException):
    def __init__(self, detail: str = "Operation not permitted for this user role"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class ResourceNotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class BadRequestException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
