#!/usr/bin/env node
/**
 * 简单的 SSE 测试 - 不使用 SDK
 */

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test';

console.log('=== 简单 SSE 测试 ===\n');

// 使用原生 fetch 订阅 SSE
async function testSSE() {
    console.log('连接到事件流...');

    const response = await fetch(`${ENGINE_HOST}/trans/event`, {
        headers: {
            'X-Domain-ID': DOMAIN_ID,
            'X-Sandbox-ID': SANDBOX_ID,
            'Accept': 'text/event-stream',
        }
    });

    console.log('响应状态:', response.status);
    console.log('Content-Type:', response.headers.get('content-type'));

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let eventCount = 0;
    let buffer = '';

    console.log('\n开始接收事件:\n');

    try {
        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                console.log('\n流结束 (done=true)');
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    eventCount++;
                    const data = line.substring(6);
                    console.log(`事件 #${eventCount}:`, data);

                    try {
                        const event = JSON.parse(data);
                        console.log('  类型:', event.type);
                    } catch (e) {
                        // ignore
                    }
                }
            }

            // 接收10个事件后停止
            if (eventCount >= 10) {
                console.log('\n已接收10个事件，停止');
                break;
            }
        }
    } catch (error) {
        console.error('读取错误:', error);
    } finally {
        reader.releaseLock();
    }

    console.log(`\n总共接收 ${eventCount} 个事件`);
}

testSSE().catch(console.error);
