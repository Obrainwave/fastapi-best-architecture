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

class ModuleAccessError(AppException):
    def __init__(self, message: str = "Module not licensed"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="MODULE_NOT_LICENSED",
        )

class JournalImbalancedError(AppException):
    def __init__(self, message: str = "Journal is imbalanced"):
        super().__init__(
            message=message,
            status_code=422,
            error_code="JOURNAL_IMBALANCED",
        )

class PostingControlViolationError(AppException):
    def __init__(self, message: str = "Posting control violated"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="POSTING_CONTROL_VIOLATED",
        )

class ClosedPeriodError(AppException):
    def __init__(self, message: str = "Fiscal period is closed"):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CLOSED_PERIOD",
        )

class DuplicatePostingError(AppException):
    def __init__(self, message: str = "Journal already posted"):
        super().__init__(
            message=message,
            status_code=409,
            error_code="DUPLICATE_POSTING",
        )