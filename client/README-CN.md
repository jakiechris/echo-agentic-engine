# Echo Agentic Engine 客户端测试程序

这个目录包含测试 Echo Agentic Engine 的客户端程序。

## 快速开始

### 前提条件

确保 Engine 服务已启动（默认地址: `http://localhost:8000`）

### 测试项与触发命令

#### 测试1：基本接口测试（Bash 脚本）

**测试内容**：
- 健康检查 (`/trans/global/health`)
- 事件流监听 (`/trans/event`) - 监听5秒
- 会话列表 (`/trans/session`)
- 配置获取 (`/trans/config`)

**触发命令**：
```bash
cd client
./test.sh
```

自定义环境变量：
```bash
ENGINE_HOST=http://localhost:8000 DOMAIN_ID=my-domain SANDBOX_ID=my-sandbox ./test.sh
```

---

#### 测试2：完整功能测试（Node.js 客户端）

**测试内容**：
- 健康检查
- 列出现有会话
- 创建新会话
- 初始化会话
- **发送消息 "帮忙看看你的workspace都有什么文件"**
- **接收并打印流式响应（包括中间步骤和最终结果）**

**触发命令**：
```bash
cd client
npm install  # 首次需要安装依赖
node test-client-simple.js
```

自定义环境变量：
```bash
ENGINE_HOST=http://localhost:8000 DOMAIN_ID=my-domain SANDBOX_ID=my-sandbox node test-client-simple.js
```

---

#### 测试3：SDK 集成测试（高级）

**测试内容**：
- 健康检查
- 会话列表
- 完整会话聊天流程（创建、初始化、发送消息、流式响应）
- 获取会话消息历史

**触发命令**：
```bash
cd client
npm install
npm run test:sdk
```

---

## 环境变量说明

所有测试程序都支持以下环境变量：

- `ENGINE_HOST`: Engine 服务地址（默认: `http://localhost:8000`）
- `DOMAIN_ID`: 租户标识（默认: `test-domain`）
- `SANDBOX_ID`: 沙箱标识（默认: `test-sandbox`）

## 预期输出

### 测试1：基本接口测试

```bash
./test.sh
```

输出：
```
=== Echo Agentic Engine 测试 ===
Engine: http://localhost:8000
Domain ID: test-domain
Sandbox ID: test-sandbox

--- 1. 测试健康检查 ---
{
    "healthy": true,
    "version": "1.2.27"
}

--- 2. 测试事件流 ---
监听事件流5秒...
data: {"type":"server.connected","properties":{}}

(超时或结束)

--- 3. 测试会话列表 ---
[]

--- 4. 测试配置获取 ---
{
    "agent": {},
    "mode": {},
    "plugin": [],
    "command": {},
    "username": "unknown"
}

=== 测试完成 ===
```

### 测试2：完整功能测试

```bash
node test-client-simple.js
```

输出：
```
=== Echo Agentic Engine 测试客户端 ===

Engine 地址: http://localhost:8000
Domain ID: test-domain
Sandbox ID: test-sandbox

开始测试...

--- 测试健康检查接口 ---
响应: { "healthy": true, "version": "1.2.27" }
✅ 健康检查通过

--- 测试列出会话 ---
会话列表: []
✅ 会话列表获取成功

--- 测试创建会话 ---
会话创建成功: { "id": "session-xxx", ... }

--- 测试初始化会话 ---
初始化成功: { "status": "initialized" }

--- 测试发送消息 ---
发送消息: "帮忙看看你的workspace都有什么文件"

============================================================

[事件] text
文本: 我来帮你看看...

[事件] step_start
步骤开始: list_files

[事件] tool
工具调用: file_list
状态: running

...

============================================================

✅ 流式响应接收完成

=== 所有测试完成 ===
✅ 测试通过
```

## 文件说明

- `package.json` - NPM 包配置
- `test-client-simple.js` - Node.js 测试客户端（推荐）
- `test-client.js` - SDK 测试客户端（高级）
- `test.sh` - Bash 测试脚本（最简单）
- `README-CN.md` - 本文档

## 自定义 Headers

客户端通过以下方式携带自定义 headers：

```javascript
const headers = {
  'X-Domain-ID': DOMAIN_ID,
  'X-Sandbox-ID': SANDBOX_ID,
  'Content-Type': 'application/json',
};

fetch(`${ENGINE_HOST}/trans/session`, { headers });
```

## 流式响应处理

Node.js 客户端使用 ReadableStream API 处理流式响应：

```javascript
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value, { stream: true });
  // 解析 Server-Sent Events 格式
  const lines = text.split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      console.log('事件:', event);
    }
  }
}
```

## 常见问题

### Q: 创建会话失败怎么办？

A: 确保：
1. Engine 服务正在运行
2. OpenCode 配置正确（`~/.config/opencode/opencode.json`）
3. Headers 包含正确的 `X-Domain-ID` 和 `X-Sandbox-ID`

### Q: 如何查看详细日志？

A: 查看 Engine 日志：
```bash
tail -f ../log/server.log
```

### Q: 如何测试流式响应？

A: 使用事件流接口或发送消息接口：
```bash
# 监听事件流
curl -N http://localhost:8000/trans/event \
  -H "X-Domain-ID: test-domain" \
  -H "X-Sandbox-ID: test-sandbox"
```

## 相关链接

- [OpenCode SDK](https://github.com/anomalyco/opencode-sdk-js)
- [OpenCode 文档](https://opencode.ai/docs)
- [Engine API 文档](../docs/架构说明.md)