#!/usr/bin/env node
/**
 * 简单测试：发送prompt并查看流式响应
 */

import { Agent, setGlobalDispatcher } from 'undici';

// 设置全局Agent，配置长超时
setGlobalDispatcher(new Agent({
    headersTimeout: 600000,      // 10分钟 - 等待响应头
    bodyTimeout: 600000,          // 10分钟 - 等待响应体
    keepAliveTimeout: 600000,     // 10分钟 - keep-alive超时
    keepAliveMaxTimeout: 600000,
}));

async function test() {
    console.log('=== 测试发送Prompt并接收流式响应 ===\n');

    const ENGINE_HOST = 'http://localhost:8000';
    const DOMAIN_ID = 'new-test';
    const SANDBOX_ID = 'new-sandbox';

    // 1. 订阅事件流
    console.log('1. 订阅事件流...');
    const eventResponse = await fetch(`${ENGINE_HOST}/trans/event`, {
        headers: {
            'X-Domain-ID': DOMAIN_ID,
            'X-Sandbox-ID': SANDBOX_ID,
            'Accept': 'text/event-stream',
        },
    });

    console.log(`事件流状态: ${eventResponse.status}\n`);

    // 后台持续读取事件
    const eventReader = eventResponse.body.getReader();
    const eventDecoder = new TextDecoder();
    let eventCount = 0;

    (async () => {
        while (true) {
            const { done, value } = await eventReader.read();
            if (done) break;

            eventCount++;
            const chunk = eventDecoder.decode(value, { stream: true });
            console.log(`[事件流] Event #${eventCount}: ${chunk.trim()}`);
        }
        console.log('[事件流] 结束');
    })();

    // 等待事件流建立
    await new Promise(resolve => setTimeout(resolve, 3000));

    // 2. 创建会话
    console.log('2. 创建会话...');
    const sessionResponse = await fetch(`${ENGINE_HOST}/trans/session`, {
        method: 'POST',
        headers: {
            'X-Domain-ID': DOMAIN_ID,
            'X-Sandbox-ID': SANDBOX_ID,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: '测试Prompt' }),
    });

    const sessionData = await sessionResponse.json();
    console.log(`会话创建结果:`, sessionData);
    const sessionId = sessionData.id;

    if (!sessionId) {
        console.error('无法获取会话ID');
        process.exit(1);
    }

    console.log(`\n会话ID: ${sessionId}\n`);

    // 3. 发送prompt
    console.log('3. 发送prompt...');
    const promptText = "列出有哪些文件";
    console.log(`Prompt: "${promptText}"\n`);

    const promptResponse = await fetch(`${ENGINE_HOST}/trans/session/${sessionId}/message`, {
        method: 'POST',
        headers: {
            'X-Domain-ID': DOMAIN_ID,
            'X-Sandbox-ID': SANDBOX_ID,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            parts: [{ type: 'text', text: promptText }]
        }),
    });

    console.log(`Prompt响应状态: ${promptResponse.status}`);
    console.log(`Content-Type: ${promptResponse.headers.get('content-type')}\n`);

    // 读取流式响应
    const reader = promptResponse.body.getReader();
    const decoder = new TextDecoder();
    let chunkCount = 0;
    let fullResponse = '';

    console.log('=== 开始接收流式响应 ===\n');

    while (true) {
        const { done, value } = await reader.read();
        if (done) {
            console.log('\n=== 流式响应结束 ===\n');
            break;
        }

        chunkCount++;
        const chunk = decoder.decode(value, { stream: true });
        fullResponse += chunk;
        console.log(`Chunk #${chunkCount} (${value.length} bytes):`, chunk.substring(0, 200));
    }

    console.log(`\n总共收到 ${chunkCount} 个chunk`);
    console.log(`总字节数: ${fullResponse.length}`);

    // 等待更多事件
    console.log('\n等待更多事件流...');
    await new Promise(resolve => setTimeout(resolve, 5000));

    console.log(`\n总共收到 ${eventCount} 个事件`);
    process.exit(0);
}

test().catch(error => {
    console.error('测试失败:', error);
    process.exit(1);
});
