"""
CreateSandboxRouter 模块

职责: 处理创建沙箱的管理接口请求

HTTP接口: POST /admin/sandbox/create
流程: 3.2.4 - 管理接口：创建沙箱
"""

import socket
from datetime import datetime
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

        # 4. 写入Redis沙箱信息表
        try:
            config = container.config_manager.loadConfig()

            # 获取引擎URL
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
            except Exception:
                ip = config.engineHost

            engine_url = f"http://{ip}:{config.enginePort}/trans"
            timestamp = datetime.utcnow().isoformat() + "Z"

            # 写入Redis
            container.redis_client.setSandboxInfo(
                domain_id=domainID,
                sandbox_id=sandboxID,
                engine_url=engine_url,
                timestamp=timestamp,
                last_request_time=timestamp
            )
        except Exception as e:
            # Redis写入失败不影响创建
            pass

        # 5. 构建响应
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
