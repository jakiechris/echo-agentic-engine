#!/usr/bin/env node
/**
 * 正确的测试：保持事件流连接的同时运行其他操作
 * 模拟成功案例的方式
 */

async function testEventStream() {
    console.log('=== 测试Engine的SSE事件流 ===\n');

    const ENGINE_HOST = 'http://localhost:8000';
    const DOMAIN_ID = 'test';
    const SANDBOX_ID = 'test';

    // 持久化的事件流连接（不主动关闭）
    let eventCount = 0;
    const eventStreamPromise = (async () => {
        console.log('开始建立事件流连接...');
        try {
            const response = await fetch(`${ENGINE_HOST}/trans/event`, {
                headers: {
                    'X-Domain-ID': DOMAIN_ID,
                    'X-Sandbox-ID': SANDBOX_ID,
                    'Accept': 'text/event-stream',
                },
            });

            console.log(`事件流状态: ${response.status}`);
            console.log(`Content-Type: ${response.headers.get('content-type')}\n`);

            if (!response.ok) {
                console.error('事件流连接失败');
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('\n事件流自然结束 (done=true)');
                    break;
                }

                eventCount++;
                const chunk = decoder.decode(value, { stream: true });
                console.log(`Event #${eventCount}: ${chunk.trim().substring(0, 100)}`);
            }
        } catch (error) {
            console.error('事件流错误:', error.message);
        }
    })();

    // 等待事件流建立
    await new Promise(resolve => setTimeout(resolve, 3000));

    console.log('\n事件流已建立，现在保持连接30秒观察...\n');

    // 等待一段时间，观察是否有更多事件
    await new Promise(resolve => setTimeout(resolve, 30000));

    console.log(`\n测试结束，总共收到 ${eventCount} 个事件`);
}

testEventStream().catch(console.error);