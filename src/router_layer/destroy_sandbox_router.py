"""
DestroySandboxRouter 模块

职责: 处理销毁沙箱的管理接口请求

HTTP接口: POST /admin/sandbox/destroy
流程: 3.2.5 - 管理接口：销毁沙箱
"""

from datetime import datetime
from fastapi import Request, Response

from ..container import container
from ..exceptions import SandboxNotFoundError, EngineError


class DestroySandboxRouter:
    """处理销毁沙箱的路由模块"""

    async def handleDestroySandbox(self, request: Request) -> Response:
        """
        销毁沙箱

        流程: 3.2.5 - 管理接口：销毁沙箱

        Args:
            request: FastAPI Request 对象,Body 包含 domainID 和 sandboxID

        Returns:
            Response: 包含销毁结果的标准响应
        """
        # 1. 解析请求体
        try:
            body = await request.json()
        except:
            body = {}

        # 2. 验证参数
        try:
            domainID, sandboxID = container.request_validator.validateAdminDestroyRequest(body)
        except EngineError as e:
            return container.response_builder.handleException(e)

        # 3. 获取沙箱信息（用于返回端口信息）
        sandbox = container.get_sandbox_from_memory(domainID, sandboxID)

        if sandbox is None:
            return container.response_builder.handleException(
                SandboxNotFoundError(domainID, sandboxID)
            )

        port = sandbox.port

        # 4. 销毁沙箱
        try:
            result = container.sandbox_manager.destroySandbox(domainID, sandboxID)
        except EngineError as e:
            return container.response_builder.handleException(e)

        # 5. 从Redis删除沙箱信息
        try:
            container.redis_client.deleteSandboxInfo(domainID, sandboxID)
        except Exception:
            # Redis删除失败不影响销毁
            pass

        # 6. 构建响应
        return container.response_builder.buildSuccessResponse({
            "domainID": domainID,
            "sandboxID": sandboxID,
            "destroyedAt": datetime.utcnow().isoformat() + "Z",
            "port": port,
            "portRecycled": result
        })
