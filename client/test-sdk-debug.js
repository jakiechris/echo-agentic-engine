#!/usr/bin/env node
/**
 * 调试SDK响应解析问题
 */

import { createOpencodeClient } from "@opencode-ai/sdk/v2";
import { fetch } from 'undici';

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

// 创建自定义fetch，处理Request对象
const customFetch = async (input, init) => {
    // 如果input是Request对象，提取URL
    if (input instanceof Request || (typeof input === 'object' && input?.url)) {
        const url = input.url || input.toString();
        const headers = {};
        input.headers?.forEach((value, key) => {
            headers[key] = value;
        });

        console.log('SDK Request:', {
            url: url,
            method: input.method || init?.method,
            hasBody: !!(init?.body),
        });

        // 使用init中的body，而不是input.body（因为input.body可能已被读取）
        const requestOptions = {
            method: input.method || init?.method,
            headers: { ...headers, ...init?.headers },
            signal: input.signal || init?.signal,
        };

        // 如果有body，需要设置duplex
        if (init?.body) {
            requestOptions.body = init.body;
            requestOptions.duplex = 'half';
        }

        const response = await fetch(url, requestOptions);

        console.log('SDK Response status:', response.status);

        return response;
    }
    return fetch(input, init);
};

const client = createOpencodeClient({
    baseUrl: `${ENGINE_HOST}/trans`,
    headers: {
        'X-Domain-ID': DOMAIN_ID,
        'X-Sandbox-ID': SANDBOX_ID,
    },
    fetch: customFetch
});

async function test() {
    console.log('创建会话...');
    const sessionResponse = await client.session.create({
        body: { title: "测试" },
    });

    console.log('Session response:', sessionResponse);
    console.log('Session.data:', sessionResponse.data);
    console.log('Session.error:', sessionResponse.error);

    const sessionId = sessionResponse.data?.id;
    console.log(`会话ID: ${sessionId}\n`);

    console.log('发送prompt...');
    const promptResponse = await client.session.prompt({
        sessionID: sessionId,
        parts: [{ type: "text", text: "列出当前目录下的文件" }],
    });

    console.log('\nPrompt response:', promptResponse);
    console.log('Prompt.data:', promptResponse.data);
    console.log('Prompt.error:', promptResponse.error);

    // 打印完整响应
    console.log('\n完整响应JSON:');
    console.log(JSON.stringify(promptResponse, null, 2).substring(0, 2000));
}

test().catch(error => {
    console.error('Error:', error);
    process.exit(1);
});