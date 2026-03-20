"""
ListSandboxRouter 模块

职责: 管理接口 - 列出所有引擎和沙箱信息

流程: 3.2.2 - 管理接口：列出所有信息
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from ..container import container
from ..api_layer.response_builder import ResponseBuilder


class ListSandboxRouter:
    """列出所有信息的路由模块"""

    def __init__(self):
        self._response_builder: ResponseBuilder = container.response_builder

    async def handleListSandboxes(self, request: Request) -> JSONResponse:
        """
        处理列出所有引擎和沙箱信息的请求

        流程: 3.2.2 - 管理接口：列出所有信息

        Returns:
            JSONResponse: 包含引擎信息表和沙箱信息表的响应
        """
        try:
            # 1. 从Redis获取所有引擎信息
            engines = container.redis_client.getAllEngines()

            # 2. 从Redis获取所有沙箱信息
            sandboxes = container.redis_client.getAllSandboxes()

            # 3. 构建响应
            response_data = {
                "status": "success",
                "data": {
                    "engines": engines,
                    "sandboxes": sandboxes,
                    "summary": {
                        "totalEngines": len(engines),
                        "totalSandboxes": len(sandboxes)
                    }
                }
            }

            return JSONResponse(
                status_code=200,
                content=response_data
            )

        except Exception as e:
            return self._response_builder.handleException(e)
