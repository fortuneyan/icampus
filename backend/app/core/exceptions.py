from fastapi import HTTPException, status
from enum import Enum


class ErrorCode(str, Enum):
    """错误码枚举"""
    # 通用错误
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    
    # 工作流错误
    WORKFLOW_NOT_FOUND = "WORKFLOW_NOT_FOUND"
    WORKFLOW_INSTANCE_NOT_FOUND = "WORKFLOW_INSTANCE_NOT_FOUND"
    WORKFLOW_TASK_NOT_FOUND = "WORKFLOW_TASK_NOT_FOUND"
    WORKFLOW_ALREADY_APPROVED = "WORKFLOW_ALREADY_APPROVED"
    WORKFLOW_ALREADY_REJECTED = "WORKFLOW_ALREADY_REJECTED"
    WORKFLOW_CANNOT_WITHDRAW = "WORKFLOW_CANNOT_WITHDRAW"
    WORKFLOW_NODE_NOT_FOUND = "WORKFLOW_NODE_NOT_FOUND"
    WORKFLOW_NO_APPROVER = "WORKFLOW_NO_APPROVER"
    WORKFLOW_TIMEOUT = "WORKFLOW_TIMEOUT"
    
    # 业务错误
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    INVALID_OPERATION = "INVALID_OPERATION"


class BaseException(HTTPException):
    def __init__(self, status_code: int, message: str, errors: list = None, error_code: ErrorCode = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.errors = errors or []
        self.error_code = error_code


class NotFoundException(BaseException):
    def __init__(self, message: str = "资源不存在", error_code: ErrorCode = ErrorCode.NOT_FOUND):
        super().__init__(status_code=404, message=message, error_code=error_code)


class UnauthorizedException(BaseException):
    def __init__(self, message: str = "未授权"):
        super().__init__(status_code=401, message=message, error_code=ErrorCode.UNAUTHORIZED)


class ForbiddenException(BaseException):
    def __init__(self, message: str = "禁止访问"):
        super().__init__(status_code=403, message=message, error_code=ErrorCode.FORBIDDEN)


class ValidationException(BaseException):
    def __init__(self, message: str = "验证失败", errors: list = None, error_code: ErrorCode = ErrorCode.VALIDATION_ERROR):
        super().__init__(status_code=422, message=message, errors=errors, error_code=error_code)


class ConflictException(BaseException):
    def __init__(self, message: str = "资源冲突", error_code: ErrorCode = ErrorCode.CONFLICT):
        super().__init__(status_code=409, message=message, error_code=error_code)


class BusinessException(BaseException):
    """业务异常"""
    def __init__(self, error_code: ErrorCode, message: str, errors: list = None):
        super().__init__(status_code=400, message=message, errors=errors, error_code=error_code)
