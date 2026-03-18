"""
ListSandboxRouter 模块

职责: 处理列出所有沙箱的管理接口请求

HTTP接口: POST /admin/sandbox/list
参与流程: 3.2.2 - 管理接口：列出所有沙箱
"""

from datetime import datetime
from fastapi import Request, Response

from ..container import container
from ..exceptions import EngineError


class ListSandboxRouter:
    """处理列出所有沙箱的路由模块"""

    async def handleListSandboxes(self, request: Request) -> Response:
        """
        列出所有沙箱

        流程: 3.2.2 - 管理接口：列出所有沙箱

        内部调用流程:
        1. RequestValidator.validateAdminListRequest(body) → 验证请求体为空
        2. SandboxManager.listAllSandboxes() → 获取所有沙箱列表
        3. HealthChecker.checkAllHealth(sandboxes) → 并发检查健康状态
        4. RedisClient.fetchBatchMetadata(sandboxIDs) → 批量查询 Redis 元数据
        5. ResourceMonitor.queryResourceUsage(pid) → 获取每个沙箱的资源占用
        6. 聚合数据并返回响应

        Args:
            request: FastAPI Request 对象 (Body 为空)

        Returns:
            Response: 包含所有沙箱列表的响应
        """
        # ========== 1. 参数验证 ==========
        try:
            body = await request.json() if request.headers.get("content-length") else {}
        except:
            body = {}

        try:
            container.request_validator.validateAdminListRequest(body)
        except EngineError as e:
            return container.response_builder.handleException(e)

        # ========== 2. 获取所有沙箱 ==========
        sandboxes = container.sandbox_manager.listAllSandboxes()

        # ========== 3. 批量健康检查 ==========
        health_result = container.health_checker.checkAllHealth(sandboxes)

        # ========== 4. 批量获取 Redis 元数据 ==========
        sandbox_ids = [f"{s.domainID}:{s.sandboxID}" for s in sandboxes]
        metadata_map = container.redis_client.fetchBatchMetadata(sandbox_ids)

        # ========== 5. 聚合数据 ==========
        result_sandboxes = []
        for sandbox in sandboxes:
            # 计算空闲时间
            idle_seconds = self._calculate_idle_seconds(sandbox.lastActiveAt)

            # 获取资源占用
            resource_usage = container.resource_monitor.queryResourceUsage(sandbox.pid)

            # 确定健康状态
            health_status = "healthy" if sandbox in health_result.get("healthy", []) else "unhealthy"

            # 构建返回数据
            sandbox_data = {
                "domainID": sandbox.domainID,
                "sandboxID": sandbox.sandboxID,
                "status": sandbox.status,
                "pid": sandbox.pid,
                "port": sandbox.port,
                "createdAt": sandbox.createdAt,
                "lastActiveAt": sandbox.lastActiveAt,
                "idleSeconds": idle_seconds,
                "memoryUsage": resource_usage.get("memory") if resource_usage else None,
                "healthStatus": health_status
            }

            result_sandboxes.append(sandbox_data)

        # ========== 6. 返回响应 ==========
        return container.response_builder.buildSuccessResponse({
            "total": len(result_sandboxes),
            "sandboxes": result_sandboxes
        })

    def _calculate_idle_seconds(self, last_active_at: str) -> int:
        """计算空闲时间（秒）"""
        try:
            if last_active_at.endswith('Z'):
                last_active_at = last_active_at[:-1] + "+00:00"
            last_active = datetime.fromisoformat(last_active_at)
            now = datetime.now(last_active.tzinfo)
            return int((now - last_active).total_seconds())
        except (ValueError, TypeError):
            return 0
