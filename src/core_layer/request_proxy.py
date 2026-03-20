"""
RequestProxy 模块

职责: HTTP 请求代理,将请求转发到沙箱内 OpenCode Serve

参与流程: 1 个流程 (3.2.1)
"""

from typing import Dict, Optional

import httpx
import httpcore

from fastapi import Response

from ..core_layer.models import Sandbox


class RequestProxy:
    """HTTP 请求代理"""

    # 请求超时（秒）- 设置为10分钟，支持长时间对话
    DEFAULT_TIMEOUT = 600

    def __init__(self):
        self._timeout = self.DEFAULT_TIMEOUT

    def configure(self, timeout: int):
        """配置请求超时"""
        self._timeout = timeout

    async def proxyRequest(
        self,
        sandbox: Sandbox,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[Dict] = None
    ) -> Response:
        """
        将 HTTP 请求代理到沙箱内 OpenCode Serve，进行路径转换、Headers 转换、构建请求 URL
        支持流式响应（SSE）和普通响应

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
        from fastapi.responses import StreamingResponse
        import json
        import logging

        logger = logging.getLogger(__name__)

        # 1. 构建请求 URL
        url = f"http://127.0.0.1:{sandbox.port}{path}"

        # 2. 转换 Headers
        # 移除 X-Domain-ID, X-Sandbox-ID, X-Project-Name
        proxy_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in ["x-domain-id", "x-sandbox-id", "x-project-name", "host", "content-length"]
        }

        # 添加 Authorization (使用沙箱密码)
        proxy_headers["Authorization"] = f"Bearer {sandbox.password}"

        # 3. 发送请求（完全透传，支持流式和非流式）
        try:
            logger.info(f"[Proxy] Sending request to OpenCode: {method.upper()} {url}")
            # 不使用 context manager，避免过早关闭连接
            # 对于可能的长耗时请求，使用更长的超时或无超时
            client = httpx.AsyncClient(timeout=None)  # 无超时限制，依靠heartbeat保持连接
            try:
                # 先发送请求，获取响应头
                req = client.build_request(
                    method=method.upper(),
                    url=url,
                    headers=proxy_headers,
                    json=body if body else None
                )
                response = await client.send(req, stream=True)
                logger.info(f"[Proxy] Received response from OpenCode: status={response.status_code}")

                # 读取响应头，判断是否为 SSE 流式响应
                content_type = response.headers.get("content-type", "")
                transfer_encoding = response.headers.get("transfer-encoding", "")
                content_length = response.headers.get("content-length")

                # 调试日志：记录响应头信息
                logger.info(f"[Proxy] Response headers: content-type={content_type}, transfer-encoding={transfer_encoding}, content-length={content_length}, url={url}")

                # 判断是否为流式响应：
                # 1. SSE流：content-type包含text/event-stream
                # 2. 分块传输：transfer-encoding为chunked（即使content-type是application/json）
                is_sse = "text/event-stream" in content_type
                is_chunked = "chunked" in transfer_encoding.lower() if transfer_encoding else False
                is_streaming = is_sse or is_chunked

                if is_streaming:
                    # 流式响应（SSE或分块传输）：使用 StreamingResponse
                    logger.info(f"[Proxy Stream] Starting streaming response, is_sse={is_sse}, is_chunked={is_chunked}")

                    async def stream_generator():
                        try:
                            chunk_count = 0
                            logger.info(f"[Proxy Stream] Starting to read chunks from upstream")
                            async for chunk in response.aiter_bytes():
                                chunk_count += 1
                                logger.info(f"[Proxy Stream] Received chunk #{chunk_count}, size={len(chunk)} bytes, preview={chunk[:100]}")
                                yield chunk
                                logger.info(f"[Proxy Stream] Yielded chunk #{chunk_count} to client, waiting for next chunk...")
                            logger.info(f"[Proxy Stream] Upstream stream ended naturally, total chunks={chunk_count}")
                        except (httpx.ReadError, httpcore.ReadError) as e:
                            # 客户端断开连接，这是正常现象，不需要记录错误
                            logger.info(f"[Proxy Stream] ReadError during streaming (type={type(e).__name__}): {e}")
                        except Exception as e:
                            # 其他异常记录详细信息
                            logger.error(f"[Proxy Stream] Unexpected error during streaming (type={type(e).__name__}): {e}", exc_info=True)
                        finally:
                            logger.info(f"[Proxy Stream] Closing upstream response and client in finally block")
                            await response.aclose()
                            await client.aclose()

                    # 过滤掉 hop-by-hop headers 和已经在下游设置的headers
                    excluded_headers = {
                        "transfer-encoding",
                        "connection",
                        "keep-alive",
                        "cache-control",  # 避免重复
                        "x-accel-buffering"  # 避免重复
                    }
                    response_headers = {
                        k: v for k, v in response.headers.items()
                        if k.lower() not in excluded_headers
                    }

                    # 对于流式响应，需要禁用缓冲
                    # 注意：这些headers是新建的，不会重复
                    response_headers["X-Accel-Buffering"] = "no"
                    response_headers["Cache-Control"] = "no-cache"
                    response_headers["Connection"] = "keep-alive"

                    return StreamingResponse(
                        stream_generator(),
                        media_type=content_type,
                        headers=response_headers
                    )
                else:
                    # 非 SSE 响应：读取完整内容
                    try:
                        content = await response.aread()
                    finally:
                        await response.aclose()
                        await client.aclose()

                    # 过滤掉 hop-by-hop headers
                    excluded_headers = {"transfer-encoding", "connection", "keep-alive", "content-encoding"}
                    response_headers = {
                        k: v for k, v in response.headers.items()
                        if k.lower() not in excluded_headers
                    }

                    return Response(
                        content=content,
                        status_code=response.status_code,
                        media_type=content_type,
                        headers=response_headers
                    )
            except Exception as e:
                # 确保在任何异常情况下都关闭client
                await client.aclose()
                raise

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
