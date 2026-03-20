#!/usr/bin/env node
/**
 * 简单测试：只创建会话并发送prompt
 */

import { createOpencodeClient } from "@opencode-ai/sdk/v2";
import { fetch } from 'undici';

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

const client = createOpencodeClient({
    baseUrl: `${ENGINE_HOST}/trans`,
    headers: {
        'X-Domain-ID': DOMAIN_ID,
        'X-Sandbox-ID': SANDBOX_ID,
    },
    fetch: fetch
});

async function test() {
    console.log('创建会话...');
    const sessionResponse = await client.session.create({
        body: { title: "测试" },
    });

    console.log('Session response type:', typeof sessionResponse);
    console.log('Session response:', JSON.stringify(sessionResponse, null, 2));

    const sessionId = sessionResponse.data?.id || sessionResponse.id;
    console.log(`\n会话ID: ${sessionId}`);

    if (!sessionId) {
        console.error('无法获取会话ID');
        process.exit(1);
    }

    console.log('\n发送prompt...');
    const result = await client.session.prompt({
        sessionID: sessionId,
        parts: [{ type: "text", text: "列出当前目录" }],
    });

    console.log('\nPrompt result:');
    console.log(JSON.stringify(result, null, 2));
}

test().catch(error => {
    console.error('Error:', error);
    process.exit(1);
});
