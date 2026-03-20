#!/usr/bin/env node
/**
 * 详细对比OpenCode和Engine的SSE流差异
 */

async function testSSE(url, label, headers = {}) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`${label}`);
    console.log(`URL: ${url}`);
    console.log(`Headers:`, headers);
    console.log(`${'='.repeat(60)}\n`);

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'text/event-stream',
                ...headers,
            },
        });

        console.log(`Status: ${response.status} ${response.statusText}`);
        console.log(`Headers:`);
        response.headers.forEach((value, key) => {
            console.log(`  ${key}: ${value}`);
        });
        console.log('');

        if (!response.ok) {
            console.error(`HTTP Error: ${response.status}`);
            const text = await response.text();
            console.error(`Body: ${text}`);
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let chunkCount = 0;
        let totalBytes = 0;

        console.log('开始读取流...\n');

        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                console.log('\n✓ 流正常结束 (done=true)');
                break;
            }

            chunkCount++;
            totalBytes += value.length;
            const chunk = decoder.decode(value, { stream: true });

            console.log(`Chunk #${chunkCount} (${value.length} bytes):`);
            console.log('Raw:', chunk.substring(0, 200));
            console.log('');

            // 解析事件
            const lines = chunk.split('\n');
            let eventType = '';
            let eventData = '';
            lines.forEach(line => {
                if (line.startsWith('data:')) {
                    eventData = line.substring(5).trim();
                } else if (line.startsWith('event:')) {
                    eventType = line.substring(6).trim();
                }
            });

            if (eventData) {
                try {
                    const data = JSON.parse(eventData);
                    console.log(`Parsed Event: type=${data.type || eventType}`);
                } catch (e) {
                    console.log(`Parse Error: ${e.message}`);
                }
            }
            console.log('---\n');

            // 只读取前3个chunk进行对比
            if (chunkCount >= 3) {
                console.log('读取了3个chunk，主动停止');
                reader.cancel();
                break;
            }
        }

        console.log(`\n统计:`);
        console.log(`  总chunks: ${chunkCount}`);
        console.log(`  总bytes: ${totalBytes}`);

    } catch (error) {
        console.error('Error:', error.message);
        console.error(error.stack);
    }
}

async function main() {
    // 测试1: 直接访问OpenCode
    await testSSE(
        'http://127.0.0.1:30145/event',
        '测试1: 直接访问OpenCode服务'
    );

    await new Promise(resolve => setTimeout(resolve, 2000));

    // 测试2: 通过Engine代理
    await testSSE(
        'http://localhost:8000/trans/event',
        '测试2: 通过Engine代理访问',
        {
            'X-Domain-ID': 'test',
            'X-Sandbox-ID': 'test',
        }
    );
}

main().catch(console.error);