"""
ConfigSyncTask 模块

职责: 定时向Redis写入引擎信息表和沙箱信息表，并清理不健康沙箱

执行间隔: 5秒 (配置在config.json的tasks.configSyncInterval)
"""

import logging
import socket
from typing import List, Dict
from datetime import datetime, timedelta

from ..container import container
from ..core_layer.models import Sandbox

logger = logging.getLogger(__name__)


class ConfigSyncTask:
    """配置同步任务"""

    @property
    def name(self) -> str:
        """任务名称"""
        return "ConfigSyncTask"

    def execute(self) -> None:
        """
        执行配置同步任务：
        1. 向Redis写入引擎信息表
        2. 检测并清理不健康沙箱
        3. 向Redis写入沙箱信息表

        流程: 定时任务每5秒执行一次
        """
        logger.debug(f"[{self.name}] Starting config sync task")

        # 1. 获取引擎信息
        engine_url = self._getEngineUrl()
        max_sandboxes = container.config_manager.loadConfig().maxSandboxes
        sandboxes = container.sandbox_manager.listAllSandboxes()
        used_sandboxes = len(sandboxes)
        timestamp = datetime.utcnow().isoformat() + "Z"

        # 2. 写入引擎信息表
        container.redis_client.setEngineInfo(
            engine_url=engine_url,
            max_sandboxes=max_sandboxes,
            used_sandboxes=used_sandboxes,
            timestamp=timestamp
        )
        logger.debug(f"[{self.name}] Engine info written: {engine_url}, {used_sandboxes}/{max_sandboxes}")

        # 3. 检测并清理不健康沙箱
        self._checkAndCleanUnhealthySandboxes(sandboxes)

        # 4. 更新沙箱信息表
        self._syncSandboxTable(engine_url, timestamp)

        logger.debug(f"[{self.name}] Config sync completed")

    def _getEngineUrl(self) -> str:
        """
        获取引擎完整URL

        Returns:
            str: 引擎URL (如 http://ip:8000/trans)
        """
        config = container.config_manager.loadConfig()

        # 获取本机IP
        try:
            # 尝试获取外网IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            # 如果获取失败，使用配置中的host
            ip = config.engineHost

        return f"http://{ip}:{config.enginePort}/trans"

    def _checkAndCleanUnhealthySandboxes(self, sandboxes: List[Sandbox]) -> None:
        """
        检测并清理不健康沙箱

        Args:
            sandboxes: 当前沙箱列表
        """
        if not sandboxes:
            return

        logger.debug(f"[{self.name}] Checking health of {len(sandboxes)} sandboxes")

        # 检查所有沙箱健康状态
        health_results = container.health_checker.checkAllHealth(sandboxes)
        unhealthy_sandboxes = health_results.get("unhealthy", [])

        # 杀死不健康的沙箱
        for sandbox in unhealthy_sandboxes:
            logger.warning(
                f"[{self.name}] Sandbox {sandbox.domainID}/{sandbox.sandboxID} is unhealthy, destroying..."
            )
            try:
                container.sandbox_manager.destroySandbox(sandbox.domainID, sandbox.sandboxID)
                # 从Redis删除沙箱信息
                container.redis_client.deleteSandboxInfo(sandbox.domainID, sandbox.sandboxID)
                logger.info(f"[{self.name}] Unhealthy sandbox destroyed: {sandbox.domainID}/{sandbox.sandboxID}")
            except Exception as e:
                logger.error(f"[{self.name}] Failed to destroy unhealthy sandbox: {e}")

    def _syncSandboxTable(self, engine_url: str, timestamp: str) -> None:
        """
        同步沙箱信息表

        Args:
            engine_url: 引擎URL
            timestamp: 当前时间戳
        """
        # 1. 从Redis获取本引擎的所有沙箱记录
        redis_sandboxes = container.redis_client.getSandboxesByEngine(engine_url)
        redis_sandbox_keys = {
            f"{sb['domainID']}:{sb['sandboxID']}" for sb in redis_sandboxes
        }

        # 2. 获取当前鲜活的沙箱
        live_sandboxes = container.sandbox_manager.listAllSandboxes()
        live_sandbox_keys = {
            f"{sb.domainID}:{sb.sandboxID}" for sb in live_sandboxes
        }

        # 3. 删除Redis中已不存在的沙箱记录（多退）
        to_delete = redis_sandbox_keys - live_sandbox_keys
        for key in to_delete:
            parts = key.split(":")
            if len(parts) == 2:
                domain_id, sandbox_id = parts
                container.redis_client.deleteSandboxInfo(domain_id, sandbox_id)
                logger.debug(f"[{self.name}] Deleted stale sandbox record: {key}")

        # 4. 添加新沙箱记录到Redis（少补）
        for sandbox in live_sandboxes:
            last_request_time = sandbox.lastActiveAt or timestamp
            container.redis_client.setSandboxInfo(
                domain_id=sandbox.domainID,
                sandbox_id=sandbox.sandboxID,
                engine_url=engine_url,
                timestamp=timestamp,
                last_request_time=last_request_time
            )
            logger.debug(f"[{self.name}] Updated sandbox record: {sandbox.domainID}/{sandbox.sandboxID}")

        logger.info(
            f"[{self.name}] Sandbox table synced: "
            f"{len(live_sandboxes)} live, {len(to_delete)} removed"
        )
