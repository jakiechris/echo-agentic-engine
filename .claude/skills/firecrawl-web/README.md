# Firecrawl Web Skill 安装说明

## 前置要求

1. Python 3.6+
2. Firecrawl API密钥（从 https://firecrawl.dev 获取）

## 安装步骤

### 1. 安装Python依赖

在项目根目录运行：

```bash
pip install -r .claude/skills/firecrawl-web/requirements.txt
```

或者手动安装：

```bash
pip install firecrawl-py python-dotenv
```

### 2. 配置API密钥

创建 `.env` 文件在项目根目录或用户主目录：

```bash
# 在项目根目录
echo "FIRECRAWL_API_KEY=your_api_key_here" > .env

# 或在用户主目录（全局使用）
echo "FIRECRAWL_API_KEY=your_api_key_here" > ~/.env
```

### 3. 验证安装

测试脚本是否正常工作：

```bash
python .claude/skills/firecrawl-web/fc.py --help
```

如果成功，你应该看到帮助信息。

### 4. 测试功能

测试搜索功能：

```bash
python .claude/skills/firecrawl-web/fc.py search "Python tutorial" --limit 2
```

## 使用示例

### 获取网页内容

```bash
python .claude/skills/firecrawl-web/fc.py markdown "https://example.com"
```

### 截图

```bash
python .claude/skills/firecrawl-web/fc.py screenshot "https://example.com" -o screenshot.png
```

### 搜索

```bash
python .claude/skills/firecrawl-web/fc.py search "React hooks tutorial" --limit 5
```

### 爬取文档

```bash
python .claude/skills/firecrawl-web/fc.py crawl "https://docs.python.org" --limit 10 --output ./python-docs
```

## 故障排查

### 问题：找不到firecrawl模块

**解决方案**：确保已安装依赖
```bash
pip install firecrawl-py
```

### 问题：API密钥错误

**解决方案**：
1. 检查 `.env` 文件是否存在
2. 确认API密钥格式正确
3. 验证API密钥是否有效（登录Firecrawl控制台）

### 问题：Windows上路径问题

**解决方案**：使用相对路径或绝对路径
```bash
# 相对路径（从项目根目录）
python .claude\skills\firecrawl-web\fc.py search "test"

# 或使用绝对路径
python D:\code\echo-agentic-engine\.claude\skills\firecrawl-web\fc.py search "test"
```

## API使用限制

- 免费计划有每月请求限制
- 爬取功能每个页面消耗1个credit
- 建议设置合理的limit参数以避免配额耗尽

## 更多信息

- [Firecrawl官方文档](https://docs.firecrawl.dev)
- [Firecrawl API参考](https://docs.firecrawl.dev/api-reference)