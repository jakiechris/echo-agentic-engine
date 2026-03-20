#!/usr/bin/env node
/**
 * 完整测试：SSE事件流 + Prompt响应
 * 使用undici的fetch解决Node.js原生fetch的问题
 */

import { createOpencodeClient } from "@opencode-ai/sdk/v2";
import { fetch, Request } from 'undici';

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

console.log('=== 通过Engine测试 ===\n');
console.log(`Engine: ${ENGINE_HOST}`);
console.log(`Domain: ${DOMAIN_ID}`);
console.log(`Sandbox: ${SANDBOX_ID}\n`);

// 创建持久的AbortController
const abortController = new AbortController();

// 创建自定义fetch，正确处理Request对象
const customFetch = async (input, init) => {
    // 如果input是Request对象，需要重新构造请求
    if (input instanceof Request) {
        const url = input.url;
        const method = input.method;
        const headers = {};
        input.headers.forEach((value, key) => {
            headers[key] = value;
        });

        // 尝试从input中获取body
        // Request.body是ReadableStream，但我们不能直接使用
        // 需要从init中获取原始body
        const body = init?.body || init?.serializedBody;

        console.log('SDK Request:', {
            url: url,
            method: method,
            hasBody: !!body,
            bodyPreview: body ? body.substring(0, 100) : null,
        });

        const requestOptions = {
            method: method,
            headers: headers,
            body: body,
            signal: input.signal || init?.signal,
        };

        // 如果有body，需要设置duplex
        if (body) {
            requestOptions.duplex = 'half';
        }

        const response = await fetch(url, requestOptions);
        console.log('SDK Response status:', response.status);
        return response;
    }

    // 如果是字符串URL
    return fetch(input, init);
};

// 创建客户端
const client = createOpencodeClient({
    baseUrl: `${ENGINE_HOST}/trans`,
    headers: {
        'X-Domain-ID': DOMAIN_ID,
        'X-Sandbox-ID': SANDBOX_ID,
    },
    fetch: customFetch
});

// 监听事件流
let eventCount = 0;
const eventStreamPromise = (async () => {
    console.log('开始监听事件流...');
    try {
        const events = await client.event.subscribe({
            signal: abortController.signal
        });
        for await (const event of events.stream) {
            eventCount++;
            console.log(`\nEvent #${eventCount}: ${event.type}`);
            console.log('Event details:', JSON.stringify(event.properties, null, 2));
        }
        console.log('事件流结束');
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('事件流被中止');
        } else {
            console.error('Event stream error:', error);
        }
    }
})();

// 主测试函数
async function test() {
    // 等待事件流建立
    console.log('等待事件流建立...');
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 创建会话
    console.log('\n创建会话...');
    const sessionResponse = await client.session.create({
        body: { title: "测试事件流" },
    });

    const sessionId = sessionResponse.data?.id;

    if (!sessionId) {
        console.error('无法获取会话ID');
        console.error('Session response:', sessionResponse);
        process.exit(1);
    }

    console.log(`会话ID: ${sessionId}\n`);

    // 发送prompt
    const promptText = "列出当前目录下的文件";
    console.log(`发送prompt: "${promptText}"\n`);
    const startTime = Date.now();

    const result = await client.session.prompt({
        sessionID: sessionId,
        parts: [{ type: "text", text: promptText }],
    });

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`\n响应时间: ${duration}秒`);
    console.log(`模型: ${result.data?.info?.modelID}`);
    console.log(`Tokens: ${JSON.stringify(result.data?.info?.tokens)}`);

    // 等待一段时间看更多事件
    console.log('\n等待更多事件...');
    await new Promise(resolve => setTimeout(resolve, 10000));

    console.log('\n测试完成');
    console.log(`总共收到 ${eventCount} 个事件`);

    // 中止事件流
    abortController.abort();
    await new Promise(resolve => setTimeout(resolve, 1000));
    process.exit(0);
}

test().catch(error => {
    console.error('Test error:', error);
    process.exit(1);
});