"""
GetSandboxRouter 模块

职责: 处理查询单个沙箱的管理接口请求

HTTP接口: POST /admin/sandbox/get
参与流程: 3.2.3 - 管理接口：查询单个沙箱
"""

from datetime import datetime
from fastapi import Request, Response

from ..container import container
from ..exceptions import SandboxNotFoundError, EngineError


class GetSandboxRouter:
    """处理查询单个沙箱的路由模块"""

    async def handleGetSandbox(self, request: Request) -> Response:
        """
        查询单个沙箱

        流程: 3.2.3 - 管理接口：查询单个沙箱

        Args:
            request: FastAPI Request 对象,Body 包含 domainID 和 sandboxID

        Returns:
            Response: 包含沙箱详情的响应
        """
        # 1. 解析请求体
        try:
            body = await request.json()
        except:
            body = {}

        # 2. 验证参数
        try:
            domainID, sandboxID = container.request_validator.validateAdminGetRequest(body)
        except EngineError as e:
            return container.response_builder.handleException(e)

        # 3. 获取沙箱
        sandbox = container.get_sandbox_from_memory(domainID, sandboxID)

        if sandbox is None:
            return container.response_builder.handleException(
                SandboxNotFoundError(domainID, sandboxID)
            )

        # 4. 健康检查
        health_status = container.health_checker.checkHealth(sandbox)

        # 5. 获取资源占用
        resource_usage = container.resource_monitor.queryResourceUsage(sandbox.pid)

        # 6. 读取日志
        logs = container.log_reader.readLogs(sandbox.nasPath, limit=50)

        # 7. 计算空闲时间
        try:
            last_active = datetime.fromisoformat(sandbox.lastActiveAt.replace("Z", "+00:00"))
            idle_seconds = int((datetime.now(last_active.tzinfo) - last_active).total_seconds())
        except:
            idle_seconds = 0

        # 8. 构建响应
        return container.response_builder.buildSuccessResponse({
            "domainID": sandbox.domainID,
            "sandboxID": sandbox.sandboxID,
            "status": sandbox.status,
            "pid": sandbox.pid,
            "port": sandbox.port,
            "nasPath": sandbox.nasPath,
            "password": sandbox.password,
            "createdAt": sandbox.createdAt,
            "lastActiveAt": sandbox.lastActiveAt,
            "idleSeconds": idle_seconds,
            "healthStatus": health_status,
            "memoryUsage": resource_usage.get("memory") if resource_usage else None,
            "logs": logs
        })
