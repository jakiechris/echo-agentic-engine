"""
CreateSandboxRouter 模块

职责: 处理创建沙箱的管理接口请求

HTTP接口: POST /admin/sandbox/create
参与流程: 3.2.4 - 管理接口：创建沙箱
"""

from fastapi import Request, Response

from ..container import container
from ..exceptions import EngineError


class CreateSandboxRouter:
    """处理创建沙箱的路由模块"""

    async def handleCreateSandbox(self, request: Request) -> Response:
        """
        创建沙箱

        流程: 3.2.4 - 管理接口：创建沙箱

        Args:
            request: FastAPI Request 对象,Body 包含 domainID 和 sandboxID

        Returns:
            Response: 包含新创建沙箱信息的响应
        """
        # 1. 解析请求体
        try:
            body = await request.json()
        except:
            body = {}

        # 2. 验证参数
        try:
            domainID, sandboxID = container.request_validator.validateAdminCreateRequest(body)
        except EngineError as e:
            return container.response_builder.handleException(e)

        # 3. 创建沙箱
        try:
            sandbox = container.sandbox_manager.createSandbox(domainID, sandboxID)
        except EngineError as e:
            return container.response_builder.handleException(e)
        except Exception as e:
            return container.response_builder.handleException(
                EngineError("INTERNAL_ERROR", str(e))
            )

        # 4. 构建响应
        return container.response_builder.buildSuccessResponse({
            "domainID": sandbox.domainID,
            "sandboxID": sandbox.sandboxID,
            "pid": sandbox.pid,
            "port": sandbox.port,
            "nasPath": sandbox.nasPath,
            "status": sandbox.status,
            "createdAt": sandbox.createdAt,
            "lastActiveAt": sandbox.lastActiveAt
        })
