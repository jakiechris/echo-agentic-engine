#!/bin/bash
# Echo Agentic Engine 简单测试脚本

ENGINE_HOST="${ENGINE_HOST:-http://localhost:8000}"
DOMAIN_ID="${DOMAIN_ID:-test-domain}"
SANDBOX_ID="${SANDBOX_ID:-test-sandbox}"

echo "=== Echo Agentic Engine 测试 ==="
echo "Engine: $ENGINE_HOST"
echo "Domain ID: $DOMAIN_ID"
echo "Sandbox ID: $SANDBOX_ID"
echo ""

echo "--- 1. 测试健康检查 ---"
curl -s "$ENGINE_HOST/trans/global/health" \
  -H "X-Domain-ID: $DOMAIN_ID" \
  -H "X-Sandbox-ID: $SANDBOX_ID" | python3 -m json.tool
echo ""

echo "--- 2. 测试事件流 ---"
echo "监听事件流5秒..."
timeout 5 curl -N -s "$ENGINE_HOST/trans/event" \
  -H "X-Domain-ID: $DOMAIN_ID" \
  -H "X-Sandbox-ID: $SANDBOX_ID" || echo "(超时或结束)"
echo ""

echo "--- 3. 测试会话列表 ---"
curl -s "$ENGINE_HOST/trans/session" \
  -H "X-Domain-ID: $DOMAIN_ID" \
  -H "X-Sandbox-ID: $SANDBOX_ID" | python3 -m json.tool
echo ""

echo "--- 4. 测试配置获取 ---"
curl -s "$ENGINE_HOST/trans/config" \
  -H "X-Domain-ID: $DOMAIN_ID" \
  -H "X-Sandbox-ID: $SANDBOX_ID" | python3 -m json.tool
echo ""

echo "=== 测试完成 ==="