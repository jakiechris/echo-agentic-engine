"""
ConfigSyncTask 模块

职责: 配置同步任务,定期从 Redis 同步配置并处理配置变更影响

参与流程: 1 个流程 (3.2.9)
执行间隔: Config.configSyncInterval (默认 300 秒)
"""

import logging
from typing import Dict, Any, Optional

from ..container import container

logger = logging.getLogger(__name__)


class ConfigSyncTask:
    """配置同步任务"""

    @property
    def name(self) -> str:
        """任务名称"""
        return "ConfigSyncTask"

    def execute(self) -> None:
        """
        执行配置同步任务。从 Redis 读取最新配置，与本地配置进行比较，
        若有差异则更新本地内存配置，并处理配置变更带来的影响
        （如 maxSandboxes 减少需销毁多余沙箱，idleTimeout 减少需立即触发空闲清理任务）。

        流程: 3.2.9 - ConfigSyncTask 调用链

        内部调用流程:
        1. RedisClient.getConfig("engine:config") → 获取 Redis 配置
        2. ConfigManager.compareConfig(local, redis) → 比较配置差异
        3. 若差异字段为空 → 任务结束
        4. ConfigManager.updateConfig(changes) → 更新本地内存配置
        5. 配置变更影响处理:
           - maxSandboxes 减少: 销毁空闲时间最长的沙箱
           - idleTimeout 减少: 立即触发 IdleCleanupTask.execute()
        6. 记录配置同步日志
        """
        logger.debug(f"[{self.name}] Starting config sync task")

        # 1. 获取 Redis 配置
        redis_config = container.redis_client.getConfig("engine:config")

        if not redis_config:
            logger.debug(f"[{self.name}] No remote config found, using local config")
            return

        # 2. 获取本地配置
        local_config = container.config_manager.loadConfig()

        # 3. 比较配置差异
        changes: Dict[str, Any] = container.config_manager.compareConfig(
            local_config.__dict__, redis_config
        )

        if not changes:
            logger.debug(f"[{self.name}] Config is up to date")
            return

        logger.info(f"[{self.name}] Config changes detected: {list(changes.keys())}")

        # 4. 更新本地内存配置
        container.config_manager.updateConfig(changes)

        # 5. 处理配置变更影响
        self._handleConfigChanges(changes)

        logger.info(f"[{self.name}] Config sync completed")

    def _handleConfigChanges(self, changes: Dict[str, Any]) -> None:
        """
        处理配置变更带来的影响

        Args:
            changes: 变更的配置项
        """
        # maxSandboxes 减少: 销毁空闲时间最长的沙箱
        if "maxSandboxes" in changes:
            new_max = changes["maxSandboxes"]
            self._enforceMaxSandboxes(new_max)

        # idleTimeout 减少: 立即触发空闲清理任务
        if "idleTimeout" in changes:
            new_timeout = changes["idleTimeout"]
            logger.info(f"[{self.name}] idleTimeout changed to {new_timeout}, triggering idle cleanup")
            from .idle_cleanup_task import IdleCleanupTask
            IdleCleanupTask().execute()

    def _enforceMaxSandboxes(self, max_sandboxes: int) -> None:
        """
        强制执行最大沙箱数量限制

        Args:
            max_sandboxes: 最大沙箱数量
        """
        sandboxes = container.sandbox_manager.listAllSandboxes()
        current_count = len(sandboxes)

        if current_count <= max_sandboxes:
            return

        # 按空闲时间排序（最空闲的排在前面）
        from datetime import datetime
        sandboxes.sort(
            key=lambda s: s.lastActiveAt,
            reverse=False  # 最旧的排在前面
        )

        # 销毁多余的沙箱
        excess_count = current_count - max_sandboxes
        to_destroy = sandboxes[:excess_count]

        logger.info(
            f"[{self.name}] maxSandboxes reduced to {max_sandboxes}, "
            f"destroying {len(to_destroy)} excess sandboxes"
        )

        container.sandbox_manager.batchDestroy(to_destroy)
