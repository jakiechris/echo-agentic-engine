#!/usr/bin/env node
/**
 * Echo Agentic Engine - 打字机效果演示客户端
 */

import { createOpencodeClient } from "@opencode-ai/sdk/v2";

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

console.log('=== Echo Agentic Engine 打字机效果演示 ===\n');
console.log(`Engine: ${ENGINE_HOST}\n`);

const client = createOpencodeClient({
  baseUrl: `${ENGINE_HOST}/trans`,
  headers: {
    'X-Domain-ID': DOMAIN_ID,
    'X-Sandbox-ID': SANDBOX_ID,
  }
});

// 监听事件流 - 打印所有事件
const listEvents = async function() {
    const events = await client.event.subscribe()
    for await (const event of events.stream) {
        console.log("Event:", event.type, event.properties)
        console.log('----Event----')
    }
}

listEvents();

// 发送prompt
const test = async function(){
  await new Promise(r => setTimeout(r, 1000));

  const session = await client.session.create({
    body: { title: "打字机效果测试" },
  });

  console.log(`\n会话已创建: ${session.data.id}`);
  console.log('问题: 介绍下中国历史\n');

  const startTime = Date.now();
  const result = await client.session.prompt({
    sessionID: session.data.id,
    parts: [{ type: "text", text: "请简要介绍中国历史，200字左右" }],
  });
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);

  console.log(`\n完成！响应时间: ${duration}秒`);
  console.log(`模型: ${result.data?.info?.modelID}\n`);

  setTimeout(() => process.exit(0), 2000);
}

test();
