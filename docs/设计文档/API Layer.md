# API Layer (接口层)

## 层级定位

API Layer 是 Engine 对外提供服务的入口层,负责处理 HTTP 请求和响应,参数验证以及响应格式化。

## 核心功能

1. **请求验证**: 提取并验证 HTTP 请求中的参数 (Headers, Body)
2. **响应构建**: 统一响应格式,处理错误和异常
3. **协议转换**: 将 HTTP 请求转换为内部调用,将内部结果转换为 HTTP 响应

## 包含模块

| 模块名称 | 职责 | 参与流程数 |
|---------|------|----------|
| **RequestValidator** | 请求参数验证与提取 | 5 个流程 (3.2.1 - 3.2.5) |
| **ResponseBuilder** | 响应构建与错误处理 | 5 个流程 (3.2.1 - 3.2.5) |

## 调用关系

- **被调用**: 由 FastAPI 路由函数调用
- **调用下游**: Core Layer 的 SandboxManager, ConfigManager 等模块
- **不依赖**: Infrastructure Layer, Monitoring Layer 等底层模块

## 设计原则

- 无状态: 不持有任何运行时状态
- 轻量级: 仅做参数验证和格式转换,不包含业务逻辑
- 统一格式: 所有接口统一使用 `{"status": "...", "data": {...}}` 格式
