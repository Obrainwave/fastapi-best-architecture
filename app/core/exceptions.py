class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
        )

class AuthorizationError(AppException):
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
        )

class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND",
        )

class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
        )

class InternalServerError(AppException):
    def __init__(self, message: str="Internal server error"):
        super().__init__(
            message=message,
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
        )

class BadRequestError(AppException):
    def __init__(self, message: str="Bad request"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BAD_REQUEST",
        )


class InsufficientFundsError(AppException):
    def __init__(self, message: str="Insufficient funds"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="INSUFFICIENT_FUNDS",
        )
