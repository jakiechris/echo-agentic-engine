"""
Sandbox 数据模型

定义沙箱实例的数据结构
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Sandbox:
    """沙箱实例对象"""

    domainID: str                          # 租户标识
    sandboxID: str                         # 沙箱标识
    pid: int                               # 进程 ID
    port: int                              # 宿主机端口
    nasPath: str                           # NAS 目录路径
    password: str                          # OpenCode 访问密码
    engineHost: str = "127.0.0.1"          # Engine 主机地址
    status: str = "running"                # 沙箱状态: running, destroying, error
    createdAt: str = ""                    # 创建时间 (ISO 8601)
    lastActiveAt: str = ""                 # 最后活跃时间 (ISO 8601)

    def __post_init__(self):
        """初始化后处理"""
        if not self.createdAt:
            self.createdAt = datetime.utcnow().isoformat() + "Z"
        if not self.lastActiveAt:
            self.lastActiveAt = self.createdAt

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "domainID": self.domainID,
            "sandboxID": self.sandboxID,
            "pid": self.pid,
            "port": self.port,
            "nasPath": self.nasPath,
            "password": self.password,
            "engineHost": self.engineHost,
            "status": self.status,
            "createdAt": self.createdAt,
            "lastActiveAt": self.lastActiveAt
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Sandbox':
        """从字典创建实例"""
        return cls(
            domainID=data.get("domainID", ""),
            sandboxID=data.get("sandboxID", ""),
            pid=data.get("pid", 0),
            port=data.get("port", 0),
            nasPath=data.get("nasPath", ""),
            password=data.get("password", ""),
            engineHost=data.get("engineHost", "127.0.0.1"),
            status=data.get("status", "running"),
            createdAt=data.get("createdAt", ""),
            lastActiveAt=data.get("lastActiveAt", "")
        )
