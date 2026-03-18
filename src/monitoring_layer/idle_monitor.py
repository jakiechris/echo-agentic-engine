"""
IdleMonitor 模块

职责: 空闲超时监控,识别长时间未活跃的沙箱

参与流程: 1 个流程 (3.2.8)
"""

from datetime import datetime
from typing import List

from ..core_layer.models import Sandbox
from ..container import container


class IdleMonitor:
    """空闲超时监控"""

    def scanIdleSandboxes(self, sandboxes: List[Sandbox]) -> List[Sandbox]:
        """
        扫描所有沙箱,识别空闲超时的沙箱,用于触发清理操作

        流程: 3.2.8 - IdleCleanupTask 调用链

        Args:
            sandboxes: 沙箱实例列表

        Returns:
            List[Sandbox]: 超时沙箱列表
        """
        # 获取空闲超时配置
        idle_timeout = container.config.idleTimeout

        timeout_sandboxes = []
        now = datetime.utcnow()

        for sandbox in sandboxes:
            try:
                # 解析最后活跃时间
                last_active_str = sandbox.lastActiveAt
                if last_active_str.endswith('Z'):
                    last_active_str = last_active_str[:-1]

                last_active = datetime.fromisoformat(last_active_str)

                # 计算空闲时长
                idle_seconds = (now - last_active).total_seconds()

                # 判断是否超时
                if idle_seconds > idle_timeout:
                    timeout_sandboxes.append(sandbox)

            except (ValueError, TypeError):
                # 时间解析失败，跳过
                continue

        return timeout_sandboxes
