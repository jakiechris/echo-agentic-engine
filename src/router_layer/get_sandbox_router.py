"""
CleanupSandboxRouter 模块

职责: 管理接口 - 清理空闲超过指定时长的沙箱

流程: 3.2.3 - 管理接口：清理空闲沙箱
"""

import logging
from datetime import datetime, timedelta
from fastapi import Request
from fastapi.responses import JSONResponse

from ..container import container
from ..api_layer.response_builder import ResponseBuilder

logger = logging.getLogger(__name__)


class GetSandboxRouter:
    """处理清理空闲沙箱的路由模块"""

    def __init__(self):
        self._response_builder: ResponseBuilder = container.response_builder

    async def handleGetSandbox(self, request: Request) -> JSONResponse:
        """
        清理空闲超过指定时长的沙箱

        流程: 3.2.3 - 管理接口：清理空闲沙箱

        Args:
            request: FastAPI Request 对象
                     Body: {"idleSeconds": 300}  # 清理空闲超过300秒（5分钟）的沙箱

        Returns:
            JSONResponse: 包含清理结果的响应
        """
        try:
            # 1. 解析请求参数
            try:
                body = await request.json()
            except:
                body = {}

            idle_seconds = body.get("idleSeconds", 300)  # 默认300秒（5分钟）

            if not isinstance(idle_seconds, (int, float)) or idle_seconds <= 0:
                idle_seconds = 300

            logger.info(f"[CleanupSandbox] Cleaning up sandboxes idle for {idle_seconds} seconds")

            # 2. 获取当前引擎URL
            import socket
            config = container.config_manager.loadConfig()

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
            except Exception:
                ip = config.engineHost

            engine_url = f"http://{ip}:{config.enginePort}/trans"

            # 3. 获取本引擎的所有沙箱
            sandboxes = container.sandbox_manager.listAllSandboxes()

            # 4. 找出空闲超过指定时长的沙箱
            cutoff_time = datetime.utcnow() - timedelta(seconds=idle_seconds)
            cutoff_str = cutoff_time.isoformat() + "Z"

            to_destroy = []
            for sandbox in sandboxes:
                try:
                    last_active_str = sandbox.lastActiveAt
                    if last_active_str.endswith('Z'):
                        last_active_str = last_active_str[:-1] + "+00:00"
                    last_active = datetime.fromisoformat(last_active_str)

                    if last_active < cutoff_time:
                        to_destroy.append(sandbox)
                        logger.info(
                            f"[CleanupSandbox] Sandbox {sandbox.domainID}/{sandbox.sandboxID} "
                            f"idle since {sandbox.lastActiveAt}, marking for cleanup"
                        )
                except Exception as e:
                    logger.error(f"[CleanupSandbox] Error parsing time for sandbox: {e}")

            # 5. 销毁空闲沙箱
            destroyed_count = 0
            failed_count = 0

            for sandbox in to_destroy:
                try:
                    container.sandbox_manager.destroySandbox(sandbox.domainID, sandbox.sandboxID)
                    # 从Redis删除沙箱信息
                    container.redis_client.deleteSandboxInfo(sandbox.domainID, sandbox.sandboxID)
                    destroyed_count += 1
                    logger.info(
                        f"[CleanupSandbox] Destroyed sandbox {sandbox.domainID}/{sandbox.sandboxID}"
                    )
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"[CleanupSandbox] Failed to destroy sandbox "
                        f"{sandbox.domainID}/{sandbox.sandboxID}: {e}"
                    )

            # 6. 返回响应
            response_data = {
                "status": "success",
                "data": {
                    "idleSeconds": idle_seconds,
                    "totalScanned": len(sandboxes),
                    "destroyed": destroyed_count,
                    "failed": failed_count
                }
            }

            logger.info(
                f"[CleanupSandbox] Cleanup completed: "
                f"{destroyed_count} destroyed, {failed_count} failed"
            )

            return JSONResponse(
                status_code=200,
                content=response_data
            )

        except Exception as e:
            logger.error(f"[CleanupSandbox] Error: {e}")
            return self._response_builder.handleException(e)
