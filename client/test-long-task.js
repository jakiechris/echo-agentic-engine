#!/usr/bin/env node
/**
 * 长时间任务测试 - 使用自定义fetch解决超时问题
 */

import { Agent, setGlobalDispatcher } from 'undici';

// 设置全局Agent，配置长超时
setGlobalDispatcher(new Agent({
    headersTimeout: 600000,  // 10分钟 - 等待响应头
    bodyTimeout: 600000,      // 10分钟 - 等待响应体
    keepAliveTimeout: 600000, // 10分钟 - keep-alive超时
    keepAliveMaxTimeout: 600000,
}));

async function test() {
    console.log('=== 测试长时间AI对话 ===\n');

    const ENGINE_HOST = 'http://localhost:8000';
    const DOMAIN_ID = 'test';
    const SANDBOX_ID = 'test';

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

    // 解析SSE事件
    const eventReader = eventResponse.body.getReader();
    const eventDecoder = new TextDecoder();
    let eventCount = 0;

    (async () => {
        while (true) {
            const { done, value } = await eventReader.read();
            if (done) break;

            eventCount++;
            const chunk = eventDecoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data:')) {
                    try {
                        const data = JSON.parse(line.substring(5).trim());
                        if (data.type === 'message.part.delta' && data.properties.field === 'text') {
                            process.stdout.write(data.properties.delta);
                        }
                    } catch (e) {}
                }
            }
        }
        console.log('\n[事件流结束]');
    })();

    // 等待事件流建立
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 2. 创建会话
    console.log('2. 创建会话...\n');
    const sessionResponse = await fetch(`${ENGINE_HOST}/trans/session`, {
        method: 'POST',
        headers: {
            'X-Domain-ID': DOMAIN_ID,
            'X-Sandbox-ID': SANDBOX_ID,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: '长时间任务测试' }),
    });

    const sessionData = await sessionResponse.json();
    const sessionId = sessionData.id;
    console.log(`会话ID: ${sessionId}\n`);

    // 3. 发送prompt
    console.log('3. 发送复杂任务...\n');
    const promptText = "列出当前目录下的文件,读取该文件的内容并评论内容是否正确，评论结果写在另一个文件中，然后两个文件合并，最后关于这次你完成任务带来的成就感，给我吟诗一首";
    console.log(`任务: "${promptText}"\n`);
    console.log('AI正在处理（可能需要几分钟）...\n');
    console.log('【AI回复内容】');

    const startTime = Date.now();
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

    const responseData = await promptResponse.json();
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);

    console.log(`\n\n【统计信息】`);
    console.log(`处理时间: ${duration}秒`);
    console.log(`收到事件: ${eventCount}个`);
    console.log(`响应状态: ${promptResponse.status}`);

    if (responseData.info) {
        console.log(`\n【最终结果】`);
        console.log(`模型: ${responseData.info.modelID}`);
        console.log(`状态: ${responseData.info.finish}`);
        if (responseData.info.tokens) {
            console.log(`Token使用:`);
            console.log(`  输入: ${responseData.info.tokens.input}`);
            console.log(`  输出: ${responseData.info.tokens.output}`);
            console.log(`  缓存命中: ${responseData.info.tokens.cache?.read || 0}`);
        }
    }

    process.exit(0);
}

test().catch(error => {
    console.error('\n测试失败:', error.message);
    console.error(error.stack);
    process.exit(1);
});