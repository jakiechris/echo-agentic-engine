# Core Layer (核心层)

## 层级定位

Core Layer 是 Engine 的业务逻辑核心,负责协调各模块完成沙箱生命周期管理、请求代理、配置管理等核心业务流程。

## 核心功能

1. **沙箱管理**: 创建、销毁、重建沙箱,协调基础设施模块
2. **请求代理**: 将业务请求代理到沙箱内 OpenCode Serve
3. **配置管理**: 加载和更新配置,处理配置变更

## 包含模块

| 模块名称 | 职责 | 参与流程数 |
|---------|------|----------|
| **SandboxManager** | 沙箱生命周期管理 (核心协调者) | 7 个流程 (3.2.1 - 3.2.5, 3.2.7, 3.2.8) |
| **RequestProxy** | HTTP 请求代理 | 1 个流程 (3.2.1) |
| **ConfigManager** | 配置管理 | 2 个流程 (3.2.6, 3.2.9) |

## 调用关系

- **被调用**: 由 API Layer 调用
- **调用下游**:
  - Infrastructure Layer: PortAllocator, NasManager, BubblewrapLauncher, RedisClient
  - Monitoring Layer: HealthChecker, ResourceMonitor, IdleMonitor
- **横向依赖**: Core Layer 内部模块可能相互调用

## 设计原则

- 单一职责: 每个模块职责单一,边界清晰
- 协调者模式: SandboxManager 作为核心协调者,不直接操作资源
- 异步优先: 使用 FastAPI 异步特性,避免阻塞调用
