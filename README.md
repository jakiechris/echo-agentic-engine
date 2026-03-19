# Echo Agentic Engine

基于 Bubblewrap 的轻量级沙箱管理系统，为 OpenCode Serve 提供安全隔离的运行环境。

## 项目简介

Echo Agentic Engine 是一个高性能的沙箱管理服务，通过 Bubblewrap 容器技术为每个用户提供独立、安全的 OpenCode Serve 运行环境。系统采用无状态设计，支持水平扩展和跨节点恢复，适用于多租户 AI 对话服务场景。

### 核心特性

- **轻量级隔离**: 使用 Bubblewrap 实现进程级沙箱隔离，相比 Docker 攻击面更小，启动更快
- **多租户支持**: 通过 domainID + sandboxID 双层标识实现租户隔离
- **无状态设计**: 状态存储于 Redis + NAS，节点可随时增删
- **高可用架构**: 支持跨节点故障恢复，共享 NAS 存储
- **安全白名单**: 基于 Redis 的 domainID 白名单机制
- **透明代理**: 完全透传 OpenCode Serve API，零业务侵入

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│         OpenCode UI ←──→ 文件管理 Web UI                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  网关层 (Echo-Agent)                         │
│  • 白名单验证  • 路由决策  • 负载均衡  • 文件服务            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              沙箱管理层 (Echo-Agentic-Engine)                │
│  • 沙箱创建/销毁  • 请求透传  • 状态同步  • 心跳上报          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  沙箱运行层 (Bubblewrap)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Sandbox 1│  │ Sandbox 2│  │ Sandbox N│                   │
│  │ OpenCode │  │ OpenCode │  │ OpenCode │                   │
│  │  Serve   │  │  Serve   │  │  Serve   │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                        存储层                                │
│    Redis (状态/白名单)  ←→  NAS (共享存储)                  │
└─────────────────────────────────────────────────────────────┘
```

## 核心功能

### 1. 沙箱管理

每个沙箱包含:
- 独立的 PID namespace（进程隔离）
- 独立的 Mount namespace（文件系统隔离）
- 独立的 User namespace（非特权运行）
- 独立的 OpenCode Serve 实例

### 2. 请求路由

通过 HTTP Header 传递标识:
- `X-Domain-ID`: 域标识（租户级）
- `X-Sandbox-ID`: 沙箱标识（实例级）

### 3. 反向代理

透明代理 OpenCode Serve API:
```
ANY  /api/opencode/{path}            # OpenCode HTTP API
GET  /api/opencode/event             # SSE 事件流
WS   /api/opencode/pty/{id}/connect  # WebSocket 终端
```

### 4. 状态同步

实时同步到 Redis:
- 沙箱元数据（IP、端口、状态）
- 节点负载信息
- 心跳时间戳

## 快速开始

### 前置要求

- Linux 3.8+ 内核（支持 user namespace）
- Python 3.8+
- Redis 5.0+
- Bubblewrap
- OpenCode CLI

### 安装依赖

```bash
# Ubuntu/Debian
sudo apt-get install bubblewrap

# CentOS/RHEL/Fedora
sudo dnf install bubblewrap

# Arch Linux
sudo pacman -S bubblewrap

# 安装 OpenCode CLI
npm i -g opencode-ai@latest

# 安装 Python 依赖
pip3 install -r requirements.txt
```

### 配置 NAS

```bash
# 创建数据目录
sudo mkdir -p /data/users
sudo chmod 777 /data/users
```

### 配置 Redis

```bash
# 启动 Redis
redis-server --port 6379

# 配置白名单（可选）
redis-cli SADD whitelist:domainIDs "your-domain-id"
```

### 运行服务

```bash
# 克隆项目
git clone https://github.com/your-org/echo-agentic-engine.git
cd echo-agentic-engine

# 配置 config.json
# 修改 redis、nas 等配置项

# 运行
python3 run.py
```

## 配置说明

### 配置文件示例 (config.json)

```json
{
    "redis": {
        "host": "localhost",
        "port": 6379,
        "password": "",
        "db": 0
    },
    "nas": {
        "rootPath": "/data/users"
    },
    "engine": {
        "port": 8000,
        "maxSandboxes": 50,
        "logLevel": "INFO"
    },
    "sandbox": {
        "portRange": {
            "min": 30001,
            "max": 40000
        },
        "idleTimeout": 3600,
        "openCodeCommand": "/usr/local/bin/opencode"
    },
    "tasks": {
        "healthCheckInterval": 30,
        "idleCheckInterval": 60,
        "configSyncInterval": 300,
        "healthCheckTimeout": 5,
        "maxRetries": 3
    }
}
```
  db: 0

nas:
  root_path: /mnt/nas

bubblewrap:
  port_range:
    start: 30000
    end: 40000

opencode:
  binary_path: /usr/local/bin/opencode
  workspace_name: defaultProject

log:
  level: info
  format: json
```

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ENGINE_HOST` | 监听地址 | `0.0.0.0` |
| `ENGINE_PORT` | 监听端口 | `8080` |
| `REDIS_ADDR` | Redis 地址 | `localhost:6379` |
| `NAS_ROOT` | NAS 根路径 | `/mnt/nas` |
| `PORT_RANGE_START` | 端口池起始 | `30000` |
| `PORT_RANGE_END` | 端口池结束 | `40000` |

## API 文档

### 业务接口

所有 OpenCode Serve API 均通过 `/api/opencode/` 前缀访问，需携带以下 Header:

```
X-Domain-ID: {domainID}
X-Sandbox-ID: {sandboxID}
```

### 管理接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/admin/sandbox` | GET | 列出所有本地沙箱 |
| `/admin/sandbox/{id}` | GET | 查询沙箱详情 |
| `/admin/sandbox/{id}/stop` | POST | 停止沙箱 |
| `/admin/sandbox/{id}/start` | POST | 启动沙箱 |
| `/admin/sandbox/{id}` | DELETE | 销毁沙箱 |
| `/admin/health` | GET | 健康检查 |
| `/admin/metrics` | GET | 性能指标 |

#### 示例

```bash
# 查询所有沙箱
curl http://localhost:8080/admin/sandbox

# 查询特定沙箱
curl http://localhost:8080/admin/sandbox/domain1-sandbox1

# 停止沙箱
curl -X POST http://localhost:8080/admin/sandbox/domain1-sandbox1/stop

# 健康检查
curl http://localhost:8080/admin/health
```

## 存储架构

### NAS 目录结构

```
/mnt/nas/
└── {domainID}/                    # 域级隔离
    └── {sandboxID}/               # 沙箱级隔离
        └── defaultProject/        # OpenCode workspace
            ├── .config/
            │   └── .opencode/
            │       └── opencode.json    # 工程配置
            ├── .sessions/              # Session 数据
            └── [用户文件]               # Workspace 文件
```

### Redis 数据结构

```
# 沙箱元数据 (Hash)
sandbox:{domainID}:{sandboxID} = {
    "engine_ip": "10.0.1.1",
    "engine_port": 8080,
    "sandbox_port": 30001,
    "status": "running",
    "pid": 12345,
    "created_at": "2026-03-13T10:00:00Z"
}

# 节点信息 (Hash)
engine:nodes = {
    "10.0.1.1:8080": {
        "capacity": 500,
        "running": 123,
        "heartbeat": 1709520060
    }
}

# 白名单 (Set)
whitelist:domainIDs = ["domain1", "domain2"]
```

## 安全机制

### Bubblewrap 隔离

- **PID namespace**: 进程树隔离，看不到宿主进程
- **Mount namespace**: 文件系统隔离，独立挂载视图
- **User namespace**: UID/GID 映射，非特权用户运行
- **只读挂载**: 系统目录使用 `--ro-bind` 防止篡改
- **自动清理**: `--die-with-parent` 防止孤儿进程

### 白名单控制

- 请求前验证 domainID 合法性
- 从 Redis 动态加载白名单
- 非白名单请求返回 403 Forbidden

### 文件系统隔离

- 按 domainID + sandboxID 双层隔离
- 不同沙箱无法互相访问文件
- 系统目录只读挂载

## 高可用设计

### 故障恢复

| 故障类型 | 检测方式 | 恢复策略 | RTO |
|---------|---------|---------|-----|
| 沙箱崩溃 | 进程监控 | 自动重建 | < 10s |
| 节点故障 | 心跳超时 | 流量切换 | < 30s |
| Redis 故障 | 连接超时 | 主从切换 | < 60s |

### 水平扩展

- Echo-Agentic-Engine 节点无状态，可随时增删
- 共享 NAS 存储，支持跨节点恢复
- Redis 维护全局状态一致性

## 开发指南

### 项目结构

```
echo-agentic-engine/
├── cmd/                    # 应用入口
│   └── main.go
├── internal/               # 内部模块
│   ├── sandbox/           # 沙箱管理
│   ├── proxy/             # 反向代理
│   ├── redis/             # Redis 客户端
│   └── config/            # 配置管理
├── pkg/                    # 公共库
│   ├── bwrap/             # Bubblewrap 封装
│   └── utils/             # 工具函数
├── docs/                   # 文档
│   └── 需求文档.md
├── config.yaml             # 配置文件
└── README.md
```

### 技术栈

- **语言**: Go 1.21+ 或 Rust 1.70+
- **Web 框架**: Gin (Go) 或 Actix (Rust)
- **容器技术**: Bubblewrap
- **存储**: Redis 5.0+, NAS (CIFS/NFS)
- **服务发现**: Redis Heartbeat

### 开发环境搭建

```bash
# 安装依赖
go mod download

# 运行测试
go test ./...

# 构建镜像（可选）
docker build -t echo-engine:latest .
```

## 部署指南

### Docker 部署

```dockerfile
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN go build -o echo-engine cmd/main.go

FROM ubuntu:22.04
RUN apt-get update && apt-get install -y bubblewrap
COPY --from=builder /app/echo-engine /usr/local/bin/
CMD ["echo-engine"]
```

### Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: echo-engine
  template:
    spec:
      containers:
      - name: echo-engine
        image: echo-engine:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: nas
          mountPath: /mnt/nas
      volumes:
      - name: nas
        nfs:
          server: nas-server
          path: /export/data
```

## 监控与运维

### 健康检查

```bash
# 节点健康检查
curl http://localhost:8080/admin/health

# 性能指标
curl http://localhost:8080/admin/metrics
```

### 日志管理

- 结构化 JSON 日志
- 支持日志级别配置（debug/info/warn/error）
- 建议配合 ELK 或 Loki 收集分析

### 性能监控

建议监控指标:
- 沙箱数量和状态
- 请求成功率
- CPU/内存占用
- 端口池使用率

## 故障排查

### 常见问题

**Q: 沙箱创建失败**
- 检查 Bubblewrap 是否安装
- 验证内核版本是否 >= 3.8
- 确认 NAS 挂载正常

**Q: 白名单验证失败**
- 检查 Redis 连接状态
- 确认 domainID 已添加到白名单
- 验证 HTTP Header 格式

**Q: 跨节点恢复失败**
- 检查 NAS 是否在所有节点挂载到相同路径
- 验证 Redis 连接和权限
- 确认 OpenCode 配置文件存在

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 相关链接

- [Bubblewrap 官方文档](https://github.com/containers/bubblewrap)
- [OpenCode Serve 文档](https://opencode.ai/docs/zh-cn/server/)
- [需求文档](docs/需求文档.md)

## 联系方式

- Issue: [GitHub Issues](https://github.com/your-org/echo-agentic-engine/issues)
- Email: support@example.com
