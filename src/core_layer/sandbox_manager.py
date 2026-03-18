"""
SandboxManager 模块

职责: 沙箱生命周期管理的核心协调者,协调各模块完成沙箱的创建、销毁、重建

参与流程: 7 个流程 (3.2.1 - 3.2.5, 3.2.7, 3.2.8)
"""

from datetime import datetime
from typing import List, Optional

from ..container import container
from ..core_layer.models import Sandbox
from ..exceptions import (
    SandboxUnavailableError,
    PortAllocationError,
    NasPreparationError,
    BubblewrapStartError
)


class SandboxManager:
    """沙箱生命周期管理的核心协调者"""

    def getSandbox(self, domainID: str, sandboxID: str) -> Optional[Sandbox]:
        """
        从内存查找沙箱实例，若不存在返回 None，若存在则检查健康状态，不健康则自动重建

        流程: 3.2.1 - OpenCode API 代理主流程

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识

        Returns:
            Sandbox | None: 沙箱实例对象，不存在则返回 None
        """
        # 1. 从内存查找
        sandbox = container.get_sandbox_from_memory(domainID, sandboxID)

        if sandbox is None:
            return None

        # 2. 检查健康状态
        health_status = container.health_checker.checkHealth(sandbox)

        if health_status == "healthy":
            return sandbox

        # 3. 不健康则自动重建
        try:
            rebuilt_sandbox = self.rebuildSandbox(domainID, sandboxID)
            return rebuilt_sandbox
        except Exception:
            # 重建失败，返回 None
            return None

    def listAllSandboxes(self) -> List[Sandbox]:
        """
        从内存获取所有沙箱实例列表

        流程: 3.2.2 - 管理接口：列出所有沙箱
        流程: 3.2.7 - HealthCheckTask 调用链
        流程: 3.2.8 - IdleCleanupTask 调用链

        Returns:
            List[Sandbox]: 沙箱实例列表
        """
        return container.get_all_sandboxes_from_memory()

    def createSandbox(self, domainID: str, sandboxID: str) -> Sandbox:
        """
        协调各模块创建沙箱，包括分配端口、准备目录、启动进程、写入元数据

        流程: 3.2.4 - 管理接口：创建沙箱

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识

        Returns:
            Sandbox: 新创建的沙箱实例对象

        Raises:
            PortAllocationError: 端口分配失败
            NasPreparationError: NAS 目录准备失败
            BubblewrapStartError: Bubblewrap 启动失败
        """
        now = datetime.utcnow().isoformat() + "Z"

        # 1. 分配端口
        port = container.port_allocator.allocatePort()

        # 2. 准备 NAS 目录
        nasPath = container.nas_manager.prepareDirectory(domainID, sandboxID)

        # 3. 启动 Bubblewrap 沙箱
        pid, password = container.bubblewrap_launcher.launchSandbox(nasPath, port)

        # 4. 构建沙箱实例
        sandbox = Sandbox(
            domainID=domainID,
            sandboxID=sandboxID,
            pid=pid,
            port=port,
            nasPath=nasPath,
            password=password,
            status="running",
            createdAt=now,
            lastActiveAt=now
        )

        # 5. 写入 Redis 元数据
        metadata = {
            "domainID": domainID,
            "sandboxID": sandboxID,
            "pid": pid,
            "port": port,
            "nasPath": nasPath,
            "password": password,
            "status": "running",
            "createdAt": now,
            "lastActiveAt": now
        }
        container.redis_client.setSandboxMetadata(domainID, sandboxID, metadata)

        # 6. 存入内存
        container.set_sandbox_to_memory(sandbox)

        return sandbox

    def destroySandbox(self, domainID: str, sandboxID: str) -> bool:
        """
        协调各模块销毁沙箱，包括更新状态、终止进程、回收端口、删除元数据、移除内存实例

        流程: 3.2.5 - 管理接口：销毁沙箱

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识

        Returns:
            bool: 是否销毁成功
        """
        # 1. 从内存获取沙箱
        sandbox = container.get_sandbox_from_memory(domainID, sandboxID)

        if sandbox is None:
            return False

        # 2. 更新状态为 destroying
        container.redis_client.updateMetadata(domainID, sandboxID, status="destroying")

        # 3. 终止进程
        container.bubblewrap_launcher.killSandbox(sandbox.pid)

        # 4. 回收端口
        container.port_allocator.recyclePort(sandbox.port)

        # 5. 删除 Redis 元数据
        container.redis_client.deleteSandboxMetadata(domainID, sandboxID)

        # 6. 从内存移除
        container.remove_sandbox_from_memory(domainID, sandboxID)

        return True

    def rebuildSandbox(self, domainID: str, sandboxID: str) -> Sandbox:
        """
        重建沙箱，先销毁旧沙箱，再创建新沙箱

        流程: 3.2.1 - OpenCode API 代理主流程 (健康检查失败时)

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识

        Returns:
            Sandbox: 重建后的沙箱实例对象
        """
        # 1. 销毁旧沙箱（如果存在）
        old_sandbox = container.get_sandbox_from_memory(domainID, sandboxID)
        if old_sandbox:
            # 只终止进程和移除内存，保留 NAS 数据
            container.bubblewrap_launcher.killSandbox(old_sandbox.pid)
            container.redis_client.updateMetadata(domainID, sandboxID, status="destroying")
            container.remove_sandbox_from_memory(domainID, sandboxID)

        # 2. 创建新沙箱
        return self.createSandbox(domainID, sandboxID)

    def batchRebuild(self, sandboxes: List[Sandbox]) -> List[Sandbox]:
        """
        批量重建沙箱

        流程: 3.2.7 - HealthCheckTask 调用链

        Args:
            sandboxes: 需要重建的沙箱列表

        Returns:
            List[Sandbox]: 重建后的沙箱列表
        """
        results = []
        for sandbox in sandboxes:
            try:
                rebuilt = self.rebuildSandbox(sandbox.domainID, sandbox.sandboxID)
                results.append(rebuilt)
            except Exception:
                # 重建失败，跳过
                pass
        return results

    def batchDestroy(self, sandboxes: List[Sandbox]) -> List[bool]:
        """
        批量销毁沙箱

        流程: 3.2.8 - IdleCleanupTask 调用链

        Args:
            sandboxes: 需要销毁的沙箱列表

        Returns:
            List[bool]: 每个沙箱的销毁结果列表
        """
        results = []
        for sandbox in sandboxes:
            try:
                result = self.destroySandbox(sandbox.domainID, sandbox.sandboxID)
                results.append(result)
            except Exception:
                results.append(False)
        return results

    def getOrCreateSandbox(self, domainID: str, sandboxID: str) -> Sandbox:
        """
        获取或创建沙箱，若不存在则自动创建

        流程: 3.2.1 - OpenCode API 代理主流程

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识

        Returns:
            Sandbox: 沙箱实例对象
        """
        sandbox = self.getSandbox(domainID, sandboxID)

        if sandbox is None:
            sandbox = self.createSandbox(domainID, sandboxID)

        return sandbox
