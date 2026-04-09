from fastapi import HTTPException, status


class BaseException(HTTPException):
    def __init__(self, status_code: int, message: str, errors: list = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.errors = errors or []


class NotFoundException(BaseException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(status_code=404, message=message)


class UnauthorizedException(BaseException):
    def __init__(self, message: str = "未授权"):
        super().__init__(status_code=401, message=message)


class ForbiddenException(BaseException):
    def __init__(self, message: str = "禁止访问"):
        super().__init__(status_code=403, message=message)


class ValidationException(BaseException):
    def __init__(self, message: str = "验证失败", errors: list = None):
        super().__init__(status_code=422, message=message, errors=errors)


class ConflictException(BaseException):
    def __init__(self, message: str = "资源冲突"):
        super().__init__(status_code=409, message=message)
