"""
ResponseBuilder 模块

职责: 统一响应格式构建与错误处理

参与流程: 5 个流程 (3.2.1 - 3.2.5)
"""

import json
from typing import Any, Dict, Optional

from fastapi import Response

from ..exceptions import EngineError


class ResponseBuilder:
    """统一响应格式构建与错误处理"""

    def buildSuccessResponse(self, data: Any) -> Response:
        """
        构建成功响应，统一格式为 {"status": "success", "data": {...}}

        流程: 3.2.1 - 3.2.5

        Args:
            data: 成功数据，可以是字典、列表或任意类型

        Returns:
            Response: FastAPI Response 对象，包含状态码和 JSON 响应体
        """
        response_body = {
            "status": "success",
            "data": data
        }

        return Response(
            content=json.dumps(response_body, ensure_ascii=False),
            status_code=200,
            media_type="application/json"
        )

    def buildErrorResponse(
        self,
        code: str,
        message: str,
        details: Optional[Dict] = None,
        status_code: int = 500
    ) -> Response:
        """
        构建错误响应，统一格式为 {"status": "error", "error": {"code": "...", "message": "...", "details": {...}}}

        流程: 3.2.1 - 3.2.5

        Args:
            code: 错误码，如 MISSING_DOMAIN_ID、SANDBOX_UNAVAILABLE
            message: 错误描述信息
            details: 错误详细信息，可选
            status_code: HTTP 状态码

        Returns:
            Response: FastAPI Response 对象，包含状态码和 JSON 响应体
        """
        response_body = {
            "status": "error",
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            }
        }

        return Response(
            content=json.dumps(response_body, ensure_ascii=False),
            status_code=status_code,
            media_type="application/json"
        )

    def handleException(self, exception: Exception) -> Response:
        """
        异常统一处理，根据异常类型映射 HTTP 状态码，并构建错误响应

        流程: 3.2.1 - 3.2.5

        Args:
            exception: 捕获的异常对象

        Returns:
            Response: FastAPI Response 对象，包含状态码和 JSON 响应体
        """
        # 错误码到 HTTP 状态码的映射
        status_code_map = {
            "MISSING_DOMAIN_ID": 400,
            "MISSING_SANDBOX_ID": 400,
            "INVALID_REQUEST_BODY": 400,
            "SANDBOX_NOT_FOUND": 404,
            "SANDBOX_ALREADY_EXISTS": 409,
            "SANDBOX_UNAVAILABLE": 503,
            "SANDBOX_TIMEOUT": 503,
            "PORT_ALLOCATION_FAILED": 503,
            "NAS_PREPARATION_FAILED": 503,
            "REDIS_CONNECTION_FAILED": 503,
            "BUBBLEWRAP_START_FAILED": 500,
            "PROCESS_KILL_FAILED": 500,
        }

        if isinstance(exception, EngineError):
            status_code = status_code_map.get(exception.code, 500)
            return self.buildErrorResponse(
                code=exception.code,
                message=exception.message,
                details=exception.details,
                status_code=status_code
            )

        # 其他异常
        return self.buildErrorResponse(
            code="INTERNAL_ERROR",
            message=str(exception) or "内部错误",
            details={},
            status_code=500
        )

    def buildRawResponse(self, content: bytes, status_code: int, headers: Dict = None) -> Response:
        """
        构建原始响应（用于代理透传）

        Args:
            content: 响应内容
            status_code: HTTP 状态码
            headers: 响应头

        Returns:
            Response: FastAPI Response 对象
        """
        return Response(
            content=content,
            status_code=status_code,
            media_type="application/json",
            headers=headers
        )
