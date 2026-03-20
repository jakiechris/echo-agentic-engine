#!/usr/bin/env node
/**
 * 直接测试OpenCode serve的SSE端点（不通过Engine代理）
 */

async function testDirectSSE() {
    // 先获取沙箱端口
    const port = process.env.PORT || '33602';
    const url = `http://127.0.0.1:${port}/event`;

    console.log(`测试OpenCode原生SSE: ${url}\n`);

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'text/event-stream',
            },
        });

        console.log(`Status: ${response.status}`);
        console.log(`Content-Type: ${response.headers.get('content-type')}\n`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let count = 0;

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                console.log('\n流结束');
                break;
            }
            count++;
            const chunk = decoder.decode(value);
            console.log(`Chunk #${count}: ${chunk}`);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

testDirectSSE();
