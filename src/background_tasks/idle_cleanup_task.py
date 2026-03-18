"""
IdleCleanupTask 模块

职责: 空闲沙箱清理任务,定期清理长时间未活跃的沙箱

参与流程: 2 个流程 (3.2.8, 3.2.9)
执行间隔: Config.idleCheckInterval (默认 60 秒)
"""

import logging
from typing import List

from ..container import container
from ..core_layer.models import Sandbox

logger = logging.getLogger(__name__)


class IdleCleanupTask:
    """空闲沙箱清理任务"""

    @property
    def name(self) -> str:
        """任务名称"""
        return "IdleCleanupTask"

    def execute(self) -> None:
        """
        执行空闲沙箱清理任务。获取所有沙箱列表，扫描空闲超时的沙箱
        （lastActiveAt 超过 Config.idleTimeout），对超时沙箱执行批量销毁操作，释放系统资源。

        流程: 3.2.8 - IdleCleanupTask 调用链
        流程: 3.2.9 - ConfigSyncTask 调用链（由 ConfigSyncTask 立即触发）

        内部调用流程:
        1. SandboxManager.listAllSandboxes() → 获取所有沙箱列表
        2. IdleMonitor.scanIdleSandboxes(sandboxes) → 扫描空闲超时沙箱
        3. SandboxManager.batchDestroy(timeoutSandboxes) → 批量销毁超时沙箱
        4. 记录空闲清理日志
        """
        logger.debug(f"[{self.name}] Starting idle cleanup task")

        # 1. 获取所有沙箱列表
        sandboxes = container.sandbox_manager.listAllSandboxes()

        if not sandboxes:
            logger.debug(f"[{self.name}] No sandboxes to check")
            return

        logger.debug(f"[{self.name}] Checking idle status of {len(sandboxes)} sandboxes")

        # 2. 扫描空闲超时沙箱
        idle_sandboxes: List[Sandbox] = container.idle_monitor.scanIdleSandboxes(sandboxes)

        if not idle_sandboxes:
            logger.debug(f"[{self.name}] No idle sandboxes to clean up")
            return

        # 3. 批量销毁超时沙箱
        logger.info(
            f"[{self.name}] Cleaning up {len(idle_sandboxes)} idle sandboxes: "
            f"{[s.sandboxID for s in idle_sandboxes]}"
        )

        destroy_results = container.sandbox_manager.batchDestroy(idle_sandboxes)

        # 4. 记录结果
        success_count = sum(1 for r in destroy_results if r)
        fail_count = len(destroy_results) - success_count

        logger.info(
            f"[{self.name}] Idle cleanup completed: "
            f"{success_count} destroyed, {fail_count} failed"
        )
