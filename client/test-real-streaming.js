#!/usr/bin/env node
/**
 * 测试真正的事件流式输出
 */

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

console.log('=== 测试事件流 ===\n');

async function testEventStream() {
  console.log('1. 连接事件流...');
  const eventResponse = await fetch(`${ENGINE_HOST}/trans/event`, {
    headers: {
      'X-Domain-ID': DOMAIN_ID,
      'X-Sandbox-ID': SANDBOX_ID,
    },
  });

  console.log('事件流已连接，状态:', eventResponse.status);
  console.log('Content-Type:', eventResponse.headers.get('content-type'));

  const reader = eventResponse.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  console.log('\n开始监听事件（10秒）...\n');

  const timeout = setTimeout(() => {
    console.log('\n超时，停止监听');
    reader.cancel();
    process.exit(0);
  }, 10000);

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        console.log('流结束');
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));
            console.log('事件:', JSON.stringify(event, null, 2));
          } catch (e) {
            console.log('原始行:', line);
          }
        }
      }
    }
  } catch (error) {
    console.error('错误:', error.message);
  }

  clearTimeout(timeout);
}

testEventStream();
