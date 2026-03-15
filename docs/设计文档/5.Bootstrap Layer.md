# Bootstrap Layer (启动层)

## 层级定位

Bootstrap Layer 负责 Engine 进程启动时的初始化工作,包括配置加载、模块初始化和定时任务注册。

## 核心功能

1. **启动初始化**: 加载 Redis 配置,初始化各模块
2. **任务调度**: 注册定时任务,触发后台巡检
3. **配置同步**: 配置变更时通知相关模块

## 包含模块

| 模块名称 | 职责 | 参与流程数 |
|---------|------|----------|
| **EngineBootstrap** | Engine 启动初始化 | 1 个流程 (3.2.6) |
| **TaskScheduler** | 定时任务调度器 | 2 个流程 (3.2.6, 3.2.9) |

## 调用关系

- **被调用**: Engine 进程启动时执行 (main.py 入口)
- **调用下游**:
  - Infrastructure Layer: RedisClient (加载配置)
  - Core Layer: ConfigManager (初始化配置)
  - Background Tasks: 注册定时任务
- **横向依赖**: TaskScheduler 与 Background Tasks 协作

## 设计原则

- 启动失败快速退出: 初始化失败时立即终止进程
- 依赖顺序: 先初始化 Infrastructure,再初始化 Core
- 幂等性: 重复执行不会产生副作用
