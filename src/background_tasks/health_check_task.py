"""
HealthCheckTask 模块

职责: 健康检查巡检任务,定期检查所有沙箱健康状态并重建不健康沙箱

参与流程: 1 个流程 (3.2.7)
执行间隔: Config.healthCheckInterval (默认 30 秒)
"""

import logging
from typing import List

from ..container import container
from ..core_layer.models import Sandbox

logger = logging.getLogger(__name__)


class HealthCheckTask:
    """健康检查巡检任务"""

    @property
    def name(self) -> str:
        """任务名称"""
        return "HealthCheckTask"

    def execute(self) -> None:
        """
        执行健康检查巡检任务。获取所有沙箱列表，并发检查每个沙箱的健康状态，
        对不健康的沙箱执行批量重建操作，确保所有沙箱处于正常运行状态。

        流程: 3.2.7 - HealthCheckTask 调用链

        内部调用流程:
        1. SandboxManager.listAllSandboxes() → 获取所有沙箱列表
        2. HealthChecker.checkAllHealth(sandboxes) → 并发检查健康状态
        3. SandboxManager.batchRebuild(unhealthySandboxes) → 批量重建不健康沙箱
        4. 记录健康检查日志
        """
        logger.debug(f"[{self.name}] Starting health check task")

        # 1. 获取所有沙箱列表
        sandboxes = container.sandbox_manager.listAllSandboxes()

        if not sandboxes:
            logger.debug(f"[{self.name}] No sandboxes to check")
            return

        logger.info(f"[{self.name}] Checking health of {len(sandboxes)} sandboxes")

        # 2. 并发检查健康状态
        health_results = container.health_checker.checkAllHealth(sandboxes)

        # 3. 找出不健康的沙箱
        unhealthy_sandboxes: List[Sandbox] = []
        for sandbox in sandboxes:
            health_status = health_results.get(sandbox.sandboxID, "unknown")
            if health_status != "healthy":
                unhealthy_sandboxes.append(sandbox)
                logger.warning(
                    f"[{self.name}] Sandbox {sandbox.domainID}/{sandbox.sandboxID} "
                    f"is unhealthy: {health_status}"
                )

        if not unhealthy_sandboxes:
            logger.info(f"[{self.name}] All {len(sandboxes)} sandboxes are healthy")
            return

        # 4. 批量重建不健康沙箱
        logger.info(f"[{self.name}] Rebuilding {len(unhealthy_sandboxes)} unhealthy sandboxes")

        rebuilt_sandboxes = container.sandbox_manager.batchRebuild(unhealthy_sandboxes)

        # 5. 记录结果
        success_count = len(rebuilt_sandboxes)
        fail_count = len(unhealthy_sandboxes) - success_count

        logger.info(
            f"[{self.name}] Health check completed: "
            f"{success_count} rebuilt, {fail_count} failed"
        )
