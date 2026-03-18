"""
HealthChecker 模块

职责: 沙箱健康检查,通过 HTTP 请求探测沙箱状态

参与流程: 5 个流程 (3.2.1 - 3.2.4, 3.2.7)
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import httpx

from ..core_layer.models import Sandbox


class HealthChecker:
    """沙箱健康检查"""

    # 健康检查超时（秒）
    DEFAULT_TIMEOUT = 5

    def __init__(self):
        self._timeout = self.DEFAULT_TIMEOUT
        self._executor = ThreadPoolExecutor(max_workers=10)

    def configure(self, timeout: int):
        """配置健康检查超时"""
        self._timeout = timeout

    def checkHealth(self, sandbox: Sandbox) -> str:
        """
        检查单个沙箱的健康状态,通过发送 HTTP 健康检查请求探测沙箱是否正常运行

        流程: 3.2.1 - OpenCode API 代理主流程
        流程: 3.2.3 - 管理接口：查询单个沙箱
        流程: 3.2.4 - 管理接口：创建沙箱

        Args:
            sandbox: 沙箱实例对象

        Returns:
            str: 健康状态: healthy 或 unhealthy
        """
        url = f"http://127.0.0.1:{sandbox.port}/global/health"

        try:
            response = httpx.get(url, timeout=self._timeout)
            if response.status_code == 200:
                data = response.json()
                if data.get("healthy", False):
                    return "healthy"
            return "unhealthy"
        except Exception:
            return "unhealthy"

    def checkAllHealth(self, sandboxes: List[Sandbox]) -> Dict:
        """
        批量检查多个沙箱的健康状态,对每个沙箱并发执行健康检查,返回健康和不健康沙箱列表

        流程: 3.2.2 - 管理接口：列出所有沙箱
        流程: 3.2.7 - HealthCheckTask 调用链

        Args:
            sandboxes: 沙箱实例列表

        Returns:
            Dict: 健康状态映射,包含 healthy 和 unhealthy 两个列表
        """
        result = {
            "healthy": [],
            "unhealthy": []
        }

        if not sandboxes:
            return result

        # 使用线程池并发检查
        try:
            # 提交所有检查任务
            futures = {
                self._executor.submit(self.checkHealth, sandbox): sandbox
                for sandbox in sandboxes
            }

            # 收集结果
            for future in futures:
                sandbox = futures[future]
                try:
                    status = future.result(timeout=self._timeout + 1)
                    if status == "healthy":
                        result["healthy"].append(sandbox)
                    else:
                        result["unhealthy"].append(sandbox)
                except Exception:
                    result["unhealthy"].append(sandbox)
        except Exception:
            # 出错时，将所有沙箱标记为不健康
            result["unhealthy"] = list(sandboxes)

        return result
