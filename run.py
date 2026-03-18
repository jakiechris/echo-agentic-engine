#!/usr/bin/env python3
"""
Echo Agentic Engine 启动脚本
"""

import uvicorn
import os
import sys

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.container import container


def init_engine():
    """初始化引擎"""
    print("Initializing Echo Agentic Engine...")

    # 尝试连接 Redis
    print("Connecting to Redis...")
    if container.redis_client.connectRedis():
        print("Redis connected successfully")
    else:
        print("Warning: Redis connection failed, using in-memory mode")

    # 加载配置
    print("Loading configuration...")
    config = container.config_manager.loadConfig()
    print(f"Configuration loaded:")
    print(f"  - Port Range: {config.portRange.min}-{config.portRange.max}")
    print(f"  - Max Sandboxes: {config.maxSandboxes}")
    print(f"  - Idle Timeout: {config.idleTimeout}s")

    # 配置各模块
    container.port_allocator.configure(config.portRange.min, config.portRange.max)
    container.nas_manager.configure(config.nasRootPath)
    container.bubblewrap_launcher.configure(config.openCodeCommand)
    container.health_checker.configure(config.healthCheckTimeout)
    container.request_proxy.configure(config.maxRetries * 60)  # 请求超时

    print("Engine initialized successfully")


def main():
    """主入口"""
    init_engine()

    # 启动 FastAPI
    port = container.config.enginePort
    print(f"Starting server on port {port}...")

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
