"""
RequestProxy 模块

职责: HTTP 请求代理,将请求转发到沙箱内 OpenCode Serve

参与流程: 1 个流程 (3.2.1)
"""

from typing import Dict, Optional

import httpx

from fastapi import Response

from ..core_layer.models import Sandbox


class RequestProxy:
    """HTTP 请求代理"""

    # 请求超时（秒）
    DEFAULT_TIMEOUT = 120

    def __init__(self):
        self._timeout = self.DEFAULT_TIMEOUT

    def configure(self, timeout: int):
        """配置请求超时"""
        self._timeout = timeout

    def proxyRequest(
        self,
        sandbox: Sandbox,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[Dict] = None
    ) -> Response:
        """
        将 HTTP 请求代理到沙箱内 OpenCode Serve，进行路径转换、Headers 转换、构建请求 URL

        流程: 3.2.1 - OpenCode API 代理主流程

        Args:
            sandbox: 沙箱实例对象
            method: HTTP 方法: GET, POST, PUT, DELETE
            path: 请求路径，如 /api/chat
            headers: HTTP Headers 字典
            body: HTTP Body (JSON), 可选

        Returns:
            Response: HTTP Response 对象

        Raises:
            SandboxUnavailableError: 沙箱不可用
            SandboxTimeoutError: 请求超时
        """
        from ..exceptions import SandboxUnavailableError, SandboxTimeoutError

        # 1. 构建请求 URL
        url = f"http://127.0.0.1:{sandbox.port}{path}"

        # 2. 转换 Headers
        # 移除 X-Domain-ID, X-Sandbox-ID
        proxy_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in ["x-domain-id", "x-sandbox-id"]
        }

        # 添加 Authorization (使用沙箱密码)
        proxy_headers["Authorization"] = f"Bearer {sandbox.password}"

        # 3. 发送请求
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.request(
                    method=method.upper(),
                    url=url,
                    headers=proxy_headers,
                    json=body if body else None
                )

                # 4. 构建响应
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    media_type=response.headers.get("content-type", "application/json"),
                    headers=dict(response.headers)
                )

        except httpx.TimeoutException:
            raise SandboxTimeoutError(
                f"请求沙箱超时",
                domainID=sandbox.domainID,
                sandboxID=sandbox.sandboxID
            )
        except httpx.ConnectError:
            raise SandboxUnavailableError(
                f"无法连接到沙箱",
                domainID=sandbox.domainID,
                sandboxID=sandbox.sandboxID
            )
        except Exception as e:
            raise SandboxUnavailableError(
                f"请求代理失败: {str(e)}",
                domainID=sandbox.domainID,
                sandboxID=sandbox.sandboxID
            )
