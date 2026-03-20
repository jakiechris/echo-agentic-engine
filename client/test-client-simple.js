#!/usr/bin/env node
/**
 * Echo Agentic Engine 测试客户端 - 打字机效果
 */

import { createOpencodeClient } from "@opencode-ai/sdk/v2";

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

console.log('=== Echo Agentic Engine 测试客户端 ===\n');
console.log(`Engine 地址: ${ENGINE_HOST}\n`);

const client = createOpencodeClient({
  baseUrl: `${ENGINE_HOST}/trans`,
  headers: {
    'X-Domain-ID': DOMAIN_ID,
    'X-Sandbox-ID': SANDBOX_ID,
  }
});

// 1. 监听事件流 - 不阻塞
const listEvents = async function() {
    const events = await client.event.subscribe()
    for await (const event of events.stream) {
        console.log("Event:", event.type, event.properties)
        console.log('----Event----')
    }
}
listEvents();

// 2. 发送prompt
const test = async function(){
    const session = await client.session.create({
        body: { title: "测试" },
    });
    console.log(`会话: ${session.data.id}\n`);

    const result = await client.session.prompt({
        sessionID: session.data.id,
        parts: [{ type: "text", text: "hello" }],
    });

    console.log(`\n完成: 模型=${result.data?.info?.modelID}\n`);

    setTimeout(() => process.exit(0), 2000);
}
test();
