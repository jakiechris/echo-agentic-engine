#!/usr/bin/env node
import { fetch } from 'undici';

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

async function test() {
    console.log('测试原始API调用...\n');

    // 创建会话
    console.log('1. 创建会话...');
    let response = await fetch(`${ENGINE_HOST}/trans/session`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Domain-ID': DOMAIN_ID,
            'X-Sandbox-ID': SANDBOX_ID,
        },
        body: JSON.stringify({ title: "测试" }),
    });

    console.log(`Status: ${response.status} ${response.statusText}`);
    console.log(`Content-Type: ${response.headers.get('content-type')}`);

    const session = await response.json();
    console.log('Session:', JSON.stringify(session, null, 2));
    console.log(`\n会话ID: ${session.id}\n`);

    // 发送prompt
    console.log('2. 发送prompt...');
    response = await fetch(`${ENGINE_HOST}/trans/session/${session.id}/message`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Domain-ID': DOMAIN_ID,
            'X-Sandbox-ID': SANDBOX_ID,
        },
        body: JSON.stringify({
            parts: [{ type: "text", text: "列出当前目录下的文件" }],
        }),
    });

    console.log(`Status: ${response.status} ${response.statusText}`);
    console.log(`Content-Type: ${response.headers.get('content-type')}`);
    console.log(`Transfer-Encoding: ${response.headers.get('transfer-encoding')}`);

    // 读取响应
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let result = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        result += decoder.decode(value, { stream: true });
    }

    console.log('\n响应内容:');
    console.log(result.substring(0, 500) + (result.length > 500 ? '...' : ''));
}

test().catch(error => {
    console.error('Error:', error);
    process.exit(1);
});
