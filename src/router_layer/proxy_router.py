"""
ProxyRouter 模块

职责: 处理 OpenCode API 代理请求,协调沙箱管理和请求代理

HTTP接口: ANY /trans/{path}
参与流程: 3.2.1 - OpenCode API 代理主流程
"""

from fastapi import Request, Response

from ..container import container
from ..exceptions import ValidationError, SandboxUnavailableError


class ProxyRouter:
    """处理 OpenCode API 代理请求的路由模块"""

    async def handleProxyRequest(
        self,
        path: str,
        request: Request,
        x_domain_id: str = None,
        x_sandbox_id: str = None
    ) -> Response:
        """
        处理 OpenCode API 代理请求

        流程: 3.2.1 - OpenCode API 代理主流程

        Args:
            path: OpenCode API 路径 (如 api/chat, api/files/read)
            request: FastAPI Request 对象
            x_domain_id: 租户标识 (从 X-Domain-ID Header 提取)
            x_sandbox_id: 沙箱标识 (从 X-Sandbox-ID Header 提取)

        Returns:
            Response: OpenCode 原生响应
        """
        try:
            # ========== 1. 参数验证 ==========
            # 提取 Headers
            headers = dict(request.headers)

            # 如果没有通过参数传入，从 Headers 提取
            if not x_domain_id:
                x_domain_id = headers.get("X-Domain-ID") or headers.get("x-domain-id")
            if not x_sandbox_id:
                x_sandbox_id = headers.get("X-Sandbox-ID") or headers.get("x-sandbox-id")

            # 验证参数
            try:
                domainID, sandboxID = container.request_validator.validateProxyRequest({
                    "X-Domain-ID": x_domain_id,
                    "X-Sandbox-ID": x_sandbox_id
                })
            except ValidationError as e:
                return container.response_builder.handleException(e)

            # ========== 2. 获取或创建沙箱 ==========
            # 沙箱不存在则自动创建，不健康则自动重建
            try:
                sandbox = container.sandbox_manager.getOrCreateSandbox(domainID, sandboxID)
            except Exception as e:
                return container.response_builder.handleException(e)

            # ========== 3. 代理请求 ==========
            # 获取请求方法
            method = request.method

            # 构建请求路径（添加前导斜杠）
            request_path = f"/{path}" if not path.startswith("/") else path

            # 获取请求体
            try:
                body = await request.json()
            except:
                body = None

            # 代理请求到沙箱
            try:
                proxy_response = await container.request_proxy.proxyRequest(
                    sandbox=sandbox,
                    method=method,
                    path=request_path,
                    headers=headers,
                    body=body
                )

                # ========== 4. 更新活跃时间 ==========
                from datetime import datetime
                timestamp = datetime.utcnow().isoformat() + "Z"

                container.redis_client.updateSandboxLastRequest(domainID, sandboxID, timestamp)

                # 更新内存中的沙箱活跃时间
                sandbox.lastActiveAt = timestamp

                # ========== 5. 返回响应 ==========
                return proxy_response

            except SandboxUnavailableError as e:
                return container.response_builder.handleException(e)
            except Exception as e:
                return container.response_builder.handleException(e)

        except Exception as e:
            return container.response_builder.handleException(e)
