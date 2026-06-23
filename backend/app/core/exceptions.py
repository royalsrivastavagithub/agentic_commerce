class AppException(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail, status_code=404)


class ConflictError(AppException):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=409)


class BadRequestError(AppException):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=400)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail, status_code=403)


class BadGatewayError(AppException):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=502)
