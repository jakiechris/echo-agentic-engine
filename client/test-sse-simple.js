#!/usr/bin/env node
/**
 * 简单的SSE测试 - 直接使用原生fetch
 */

const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

async function testSSE() {
    console.log('测试SSE连接...\n');

    const url = `${ENGINE_HOST}/trans/event`;
    const headers = {
        'X-Domain-ID': DOMAIN_ID,
        'X-Sandbox-ID': SANDBOX_ID,
        'Accept': 'text/event-stream',
    };

    console.log(`URL: ${url}`);
    console.log(`Headers:`, headers);
    console.log('');

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: headers,
        });

        console.log(`Response status: ${response.status}`);
        console.log(`Response headers:`);
        response.headers.forEach((value, key) => {
            console.log(`  ${key}: ${value}`);
        });
        console.log('');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        if (!response.body) {
            throw new Error('No response body');
        }

        console.log('开始读取SSE流...\n');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let eventCount = 0;
        let totalBytes = 0;

        // 设置一个超时来测试流是否保持打开
        const timeout = setTimeout(() => {
            console.log('\n=== 30秒超时，停止读取 ===');
            reader.cancel();
        }, 30000);

        try {
            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    console.log('\n流结束 (done=true)');
                    break;
                }

                eventCount++;
                totalBytes += value.length;
                const chunk = decoder.decode(value, { stream: true });
                console.log(`\nEvent #${eventCount} (${value.length} bytes, total: ${totalBytes} bytes):`);
                console.log(chunk);
                console.log('---');

                // 如果连续读不到数据，等待一下
                if (eventCount === 1) {
                    console.log('\n等待更多数据...');
                    await new Promise(resolve => setTimeout(resolve, 5000));
                }
            }
        } finally {
            clearTimeout(timeout);
        }

        console.log(`\n总共收到 ${eventCount} 个事件，总计 ${totalBytes} 字节`);

    } catch (error) {
        console.error('错误:', error);
        throw error;
    }
}

// 保持进程运行
testSSE().then(() => {
    console.log('\n测试完成，保持进程运行...');
    // 不退出，让进程保持运行
}).catch(error => {
    console.error('测试失败:', error);
    process.exit(1);
});
