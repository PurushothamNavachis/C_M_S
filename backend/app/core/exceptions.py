from fastapi import HTTPException, status

class CMSException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred.",
        headers: dict[str, str] | None = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class CredentialsException(CMSException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class EntityNotFoundException(CMSException):
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with identifier '{identifier}' was not found."
        )

class EntityAlreadyExistsException(CMSException):
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{entity_name} with unique identifier '{identifier}' already exists."
        )

class InsufficientPermissionsException(CMSException):
    def __init__(self, detail: str = "Operation not permitted due to insufficient permissions."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
