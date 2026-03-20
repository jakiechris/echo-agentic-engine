#!/usr/bin/env node
/**
 * 简单测试：直连OpenCode，看是否能收到事件
 */

import { createOpencodeClient } from "@opencode-ai/sdk/v2";

const client = createOpencodeClient({
  baseUrl: "http://127.0.0.1:39083",
  headers: {
    "Authorization": "Bearer test-password"
  }
});

// 监听事件
const listEvents = async function() {
    console.log('开始监听事件流...');
    const events = await client.event.subscribe();
    for await (const event of events.stream) {
        console.log("Event:", event.type, JSON.stringify(event.properties, null, 2));
        console.log('----Event----');
    }
}

listEvents();

// 等待1秒让事件流建立
await new Promise(resolve => setTimeout(resolve, 1000));

// 发送prompt
const test = async function() {
    console.log('创建会话...');
    const session = await client.session.create({
        body: { title: "测试事件流" },
    });
    console.log(`会话ID: ${session.data.id}\n`);

    console.log('发送prompt...');
    const startTime = Date.now();
    const result = await client.session.prompt({
        sessionID: session.data.id,
        parts: [{ type: "text", text: "hello" }],
    });
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    console.log(`\n响应时间: ${duration}秒`);
    console.log(`模型: ${result.data?.info?.modelID}`);

    // 等待一下看是否有更多事件
    setTimeout(() => {
        console.log('\n测试完成');
        process.exit(0);
    }, 2000);
}

test();
