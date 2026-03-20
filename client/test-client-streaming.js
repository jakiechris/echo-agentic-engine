#!/usr/bin/env node
/**
 * Echo Agentic Engine 流式测试客户端
 *
 * 使用 SSE 事件流实现真正的实时流式输出
 */

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

console.log('=== Echo Agentic Engine 流式测试客户端 ===\n');
console.log(`Engine 地址: ${ENGINE_HOST}`);
console.log(`Domain ID: ${DOMAIN_ID}`);
console.log(`Sandbox ID: ${SANDBOX_ID}\n`);

async function createSession() {
  const response = await fetch(`${ENGINE_HOST}/trans/session`, {
    method: 'POST',
    headers: {
      'X-Domain-ID': DOMAIN_ID,
      'X-Sandbox-ID': SANDBOX_ID,
    },
  });
  const data = await response.json();
  return data.id;
}

async function sendStreamingMessage(sessionId) {
  console.log('--- 发送消息（流式接收）---');
  console.log('消息: "查下都有哪些文件，帮忙看下文件的内容对不对，给个评论,再把结论输出到b.txt中"\n');
  console.log('=' .repeat(60));

  // 1. 连接 SSE 事件流
  const eventResponse = await fetch(`${ENGINE_HOST}/trans/event`, {
    headers: {
      'X-Domain-ID': DOMAIN_ID,
      'X-Sandbox-ID': SANDBOX_ID,
    },
  });

  const reader = eventResponse.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  // 跟踪状态
  let messageStarted = false;
  let currentText = '';
  let resolveComplete;
  const completePromise = new Promise(resolve => {
    resolveComplete = resolve;
  });

  // 2. 启动事件处理（后台）
  const eventHandler = (async () => {
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;

          try {
            const event = JSON.parse(line.slice(6));
            const payload = event.payload;

            if (!payload) continue;

            // 处理不同事件类型
            if (payload.type === 'message.part.delta') {
              // 实时文本片段
              if (payload.field === 'text' && payload.delta) {
                process.stdout.write(payload.delta);
                currentText += payload.delta;
              }
            } else if (payload.type === 'message.part.updated') {
              const part = payload.part;

              if (part.type === 'step-start') {
                if (messageStarted) {
                  console.log('\n[步骤开始]');
                }
                messageStarted = true;
              } else if (part.type === 'reasoning') {
                console.log('\n[推理]');
              } else if (part.type === 'text') {
                console.log('\n[文本]');
              } else if (part.type === 'step-finish') {
                console.log('\n[步骤完成]');
                resolveComplete();
                return;
              }
            } else if (payload.type === 'server.connected') {
              // SSE 连接成功
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    } catch (error) {
      console.error('\n事件流错误:', error.message);
    }
  })();

  // 3. 发送消息
  const messagePromise = fetch(`${ENGINE_HOST}/trans/session/${sessionId}/message`, {
    method: 'POST',
    headers: {
      'X-Domain-ID': DOMAIN_ID,
      'X-Sandbox-ID': SANDBOX_ID,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      parts: [
        {
          type: 'text',
          text: '查下都有哪些文件，帮忙看下文件的内容对不对，给个评论,再把结论输出到b.txt中'
        }
      ]
    }),
  });

  // 4. 等待消息完成
  await completePromise;

  // 5. 读取完整响应（验证）
  const response = await messagePromise;
  const data = await response.json();

  console.log('\n' + '=' .repeat(60));
  console.log('\n✅ 消息接收完成\n');

  if (data.info) {
    console.log('消息信息:');
    console.log('  - 模型:', data.info.modelID);
    console.log('  - Tokens:', JSON.stringify(data.info.tokens));
    console.log('  - 成本:', data.info.cost);
  }

  // 清理
  reader.cancel();
}

async function main() {
  try {
    console.log('创建会话...');
    const sessionId = await createSession();
    console.log(`会话 ID: ${sessionId}\n`);

    await sendStreamingMessage(sessionId);

    console.log('\n=== 测试完成 ===');
    console.log('✅ 流式输出成功');
    process.exit(0);
  } catch (error) {
    console.error('\n❌ 错误:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

process.on('unhandledRejection', (error) => {
  console.error('\n❌ 未处理的错误:', error);
  process.exit(1);
});

main();
