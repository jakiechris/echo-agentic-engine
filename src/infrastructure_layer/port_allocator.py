"""
PortAllocator 模块

职责: 端口分配与回收管理,维护端口池状态

参与流程: 3 个流程 (3.2.1, 3.2.4, 3.2.5)
"""

import random
from typing import List


class PortAllocator:
    """端口分配与回收管理"""

    # 端口范围配置
    DEFAULT_PORT_MIN = 30001
    DEFAULT_PORT_MAX = 40000

    def __init__(self):
        self._port_min = self.DEFAULT_PORT_MIN
        self._port_max = self.DEFAULT_PORT_MAX

    def configure(self, port_min: int, port_max: int):
        """配置端口范围"""
        self._port_min = port_min
        self._port_max = port_max

    def allocatePort(self) -> int:
        """
        查询已占用端口,在端口范围 30001-40000 内随机选择可用端口进行分配

        流程: 3.2.1 - OpenCode API 代理主流程
        流程: 3.2.4 - 管理接口：创建沙箱

        Returns:
            int: 分配的可用端口号

        Raises:
            PortAllocationError: 无可用端口时抛出
        """
        from ..container import container
        from ..exceptions import PortAllocationError

        # 获取已占用端口
        allocated_ports = set(self.queryAllocatedPorts())

        # 同时检查内存中的端口
        for sandbox in container.get_all_sandboxes_from_memory():
            if sandbox.port:
                allocated_ports.add(sandbox.port)

        # 构建可用端口列表
        available_ports = [
            port for port in range(self._port_min, self._port_max + 1)
            if port not in allocated_ports
        ]

        if not available_ports:
            raise PortAllocationError("端口分配失败，无可用端口")

        # 随机选择一个端口
        return random.choice(available_ports)

    def recyclePort(self, port: int) -> bool:
        """
        回收端口,从已分配端口集合中移除

        流程: 3.2.5 - 管理接口：销毁沙箱

        Args:
            port: 需要回收的端口号

        Returns:
            bool: 是否回收成功
        """
        # 端口是动态分配的，不需要显式回收
        # 只要沙箱销毁后，端口自然可用
        # 这里只是返回成功，实际回收在沙箱销毁时自动完成
        return True

    def queryAllocatedPorts(self) -> List[int]:
        """
        查询 Redis 获取所有已分配端口列表

        流程: 3.2.1 - OpenCode API 代理主流程
        流程: 3.2.4 - 管理接口：创建沙箱

        Returns:
            List[int]: 已分配端口号列表
        """
        from ..container import container

        # 从 Redis 查询已分配端口
        return container.redis_client.queryAllocatedPorts()
