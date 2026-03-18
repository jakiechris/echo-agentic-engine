"""
Config 数据模型

定义配置对象的数据结构
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PortRange:
    """端口范围配置"""
    min: int = 30001
    max: int = 40000


@dataclass
class Config:
    """配置对象"""

    portRange: PortRange = field(default_factory=PortRange)
    idleTimeout: int = 3600                    # 空闲超时时长 (秒)
    healthCheckInterval: int = 30              # 健康检查间隔 (秒)
    idleCheckInterval: int = 60                # 空闲检查间隔 (秒)
    configSyncInterval: int = 300              # 配置同步间隔 (秒)
    maxRetries: int = 3                        # 请求重试次数
    healthCheckTimeout: int = 5                # 健康检查超时 (秒)
    maxSandboxes: int = 50                     # 最大沙箱数量
    redisHost: str = "localhost"               # Redis 主机地址
    redisPort: int = 6379                      # Redis 端口
    redisPassword: str = ""                    # Redis 密码 (可选)
    redisDB: int = 0                           # Redis 数据库编号
    nasRootPath: str = "/nas"                  # NAS 根路径
    enginePort: int = 8000                     # Engine 监听端口
    openCodeCommand: str = "/usr/local/bin/opencode"  # OpenCode 命令路径
    logLevel: str = "INFO"                     # 日志级别
    logFile: str = "engine.log"                # 日志文件路径
