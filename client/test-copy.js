#!/usr/bin/env node
/**
 * 测试：通过Engine访问，验证事件流和打字机效果
 */

import { createOpencodeClient } from "@opencode-ai/sdk/v2";
import { fetch } from 'undici';

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

console.log('=== 通过Engine测试 ===\n');
console.log(`Engine: ${ENGINE_HOST}`);
console.log(`Domain: ${DOMAIN_ID}`);
console.log(`Sandbox: ${SANDBOX_ID}\n`);

// 创建一个持久的AbortController，防止被垃圾回收
const abortController = new AbortController();

const client = createOpencodeClient({
  baseUrl: `${ENGINE_HOST}/trans`,
  headers: {
    'X-Domain-ID': DOMAIN_ID,
    'X-Sandbox-ID': SANDBOX_ID,
  },
  fetch: fetch  // 使用undici的fetch
});

// 监听事件 - 不等待完成，让它持续运行
let eventCount = 0;
const eventStreamPromise = (async () => {
    console.log('开始监听事件流...');
    try {
        const events = await client.event.subscribe({
            signal: abortController.signal  // 传入持久的signal
        });
        for await (const event of events.stream) {
            eventCount++;
            console.log(`Event #${eventCount}:`, event.type, JSON.stringify(event.properties, null, 2));
            console.log('----Event----');
        }
        console.log('事件流正常结束');
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('事件流被中止');
        } else {
            console.error('Event stream error:', error);
        }
    }
})();

// 等待事件流建立
console.log('等待事件流建立...');
await new Promise(resolve => setTimeout(resolve, 2000));

// 发送prompt
const test = async function() {
    try {
        console.log('创建会话...');
        const sessionResponse = await client.session.create({
            body: { title: "测试事件流" },
        });
        console.log('Session response:', JSON.stringify(sessionResponse, null, 2));
        const session = sessionResponse.data || sessionResponse;
        console.log(`会话ID: ${session.id}\n`);

        const promptText = "帮我看下你workspace下有哪些文件，文件内容写的对不对，把评价写道另一个文件中，然后两个文件再合并到第三个文件中，然后再告诉我中国历朝历代君王介绍";
        console.log(`发送prompt: "${promptText}"\n`);
        const startTime = Date.now();
        const result = await client.session.prompt({
            sessionID: session.id,
            parts: [{ type: "text", text: promptText }],
        });
        const duration = ((Date.now() - startTime) / 1000).toFixed(2);

        console.log(`\n响应时间: ${duration}秒`);
        console.log(`结果:`, JSON.stringify(result, null, 2));
        console.log(`收到事件数: ${eventCount}`);

    // 等待一段时间看更多事件
    console.log('\n等待更多事件...');
    await new Promise(resolve => setTimeout(resolve, 30000));

    console.log('\n测试完成');
    console.log(`总共收到 ${eventCount} 个事件`);

    // 中止事件流
    abortController.abort();

    // 等待一下让清理完成
    await new Promise(resolve => setTimeout(resolve, 1000));

    process.exit(0);
}

test().catch(error => {
    console.error('Test error:', error);
    process.exit(1);
});
