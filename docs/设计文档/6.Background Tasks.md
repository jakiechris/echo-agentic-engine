# Background Tasks (后台任务层)

## 层级定位

Background Tasks Layer 包含 Engine 的后台定时任务,负责沙箱巡检、清理和配置同步等后台工作。

## 核心功能

1. **健康检查巡检**: 定期检查所有沙箱健康状态,自动重建不健康沙箱
2. **空闲清理**: 定期扫描空闲超时沙箱,自动销毁
3. **配置同步**: 定期从 Redis 同步配置,触发更新

## 包含模块

| 模块名称 | 职责 | 执行周期 | 参与流程数 |
|---------|------|---------|----------|
| **HealthCheckTask** | 健康检查巡检任务 | 每 30 秒 | 1 个流程 (3.2.7) |
| **IdleCleanupTask** | 空闲沙箱清理任务 | 每 60 秒 | 2 个流程 (3.2.8, 3.2.9) |
| **ConfigSyncTask** | 配置同步任务 | 每 300 秒 | 1 个流程 (3.2.9) |

## 调用关系

- **被触发**: 由 TaskScheduler 定时触发
- **调用下游**:
  - Core Layer: SandboxManager (批量重建/销毁), ConfigManager (配置更新)
  - Monitoring Layer: HealthChecker, IdleMonitor
  - Infrastructure Layer: RedisClient (读取配置)
- **横向依赖**: ConfigSyncTask 可能触发 IdleCleanupTask 更新配置

## 设计原则

- 并发执行: 多个任务可以并发执行
- 失败重试: 单个任务失败不影响其他任务
- 数据保留: 销毁沙箱时保留 NAS 数据
