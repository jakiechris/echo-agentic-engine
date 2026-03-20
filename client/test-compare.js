#!/usr/bin/env node
/**
 * 对比测试：直接访问OpenCode vs 通过Engine代理
 * 测试SSE事件流的行为差异
 */

async function testSSE(url, label, headers = {}) {
    console.log(`\n=== ${label} ===`);
    console.log(`URL: ${url}`);
    console.log(`Headers:`, headers);
    console.log('');

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'text/event-stream',
                ...headers,
            },
        });

        console.log(`Status: ${response.status}`);
        console.log(`Content-Type: ${response.headers.get('content-type')}`);
        console.log(`Transfer-Encoding: ${response.headers.get('transfer-encoding')}\n`);

        if (!response.ok) {
            console.error(`HTTP ${response.status}: ${response.statusText}`);
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let eventCount = 0;
        let totalBytes = 0;

        // 设置超时
        const timeout = setTimeout(() => {
            console.log('\n=== 10秒超时，停止读取 ===');
            reader.cancel();
        }, 10000);

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

                // 解析SSE事件
                const lines = chunk.split('\n');
                lines.forEach(line => {
                    if (line.startsWith('data:')) {
                        const data = line.substring(5).trim();
                        if (data) {
                            try {
                                const event = JSON.parse(data);
                                console.log(`Event #${eventCount}: ${event.type}`);
                            } catch (e) {
                                console.log(`Event #${eventCount}: (parse error)`);
                            }
                        }
                    }
                });
            }
        } finally {
            clearTimeout(timeout);
        }

        console.log(`\n总共收到 ${eventCount} 个事件，总计 ${totalBytes} 字节`);

    } catch (error) {
        console.error('Error:', error.message);
    }
}

async function main() {
    // 测试1: 直接访问OpenCode服务
    await testSSE(
        'http://127.0.0.1:30145/event',
        '直接访问OpenCode服务'
    );

    // 等待一下
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 测试2: 通过Engine代理访问（带认证headers）
    await testSSE(
        'http://localhost:8000/trans/event',
        '通过Engine代理访问',
        {
            'X-Domain-ID': 'test',
            'X-Sandbox-ID': 'test',
        }
    );
}

main().catch(console.error);