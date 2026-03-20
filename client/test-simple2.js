#!/usr/bin/env node
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
    const response = await client.session.create({
        body: { title: "测试" },
    });

    console.log('Response keys:', Object.keys(response));
    console.log('Response.data:', response.data);
    console.log('Response.error:', response.error);

    if (response.error) {
        console.error('Error:', response.error);
        process.exit(1);
    }

    const sessionId = response.data?.id;
    console.log(`\n会话ID: ${sessionId}`);

    console.log('\n发送prompt...');
    const result = await client.session.prompt({
        sessionID: sessionId,
        parts: [{ type: "text", text: "hi" }],
    });

    console.log('\nResult keys:', Object.keys(result));
    console.log('Result.data:', result.data);
}

test().catch(error => {
    console.error('Error:', error);
    process.exit(1);
});
