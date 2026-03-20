#!/usr/bin/env node
/**
 * 清晰输出测试：提取关键内容
 */

async function test() {
    console.log('=== 测试AI对话 ===\n');

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

    // 解析SSE事件
    const eventReader = eventResponse.body.getReader();
    const eventDecoder = new TextDecoder();

    let aiText = '';        // AI的回复文本
    let reasoning = '';     // AI的思考过程
    let toolCalls = [];     // AI调用的工具

    (async () => {
        let buffer = '';
        while (true) {
            const { done, value } = await eventReader.read();
            if (done) break;

            buffer += eventDecoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 保留不完整的行

            for (const line of lines) {
                if (line.startsWith('data:')) {
                    try {
                        const data = JSON.parse(line.substring(5).trim());

                        // 提取AI的思考
                        if (data.type === 'message.part.delta' && data.properties.field === 'text') {
                            if (data.properties.partID.includes('reasoning')) {
                                reasoning += data.properties.delta;
                            } else if (data.properties.partID.includes('text')) {
                                aiText += data.properties.delta;
                            }
                        }

                        // 提取工具调用结果
                        if (data.type === 'message.part.updated' &&
                            data.properties.part?.type === 'tool' &&
                            data.properties.part?.state?.status === 'completed') {
                            toolCalls.push({
                                tool: data.properties.part.tool,
                                input: data.properties.part.state.input,
                                output: data.properties.part.state.output
                            });
                        }
                    } catch (e) {}
                }
            }
        }
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
        body: JSON.stringify({ title: '测试对话' }),
    });

    const sessionData = await sessionResponse.json();
    const sessionId = sessionData.id;
    console.log(`会话ID: ${sessionId}\n`);

    // 3. 发送prompt
    const promptText = "列出当前目录下的文件";
    console.log(`3. 发送问题: "${promptText}"\n`);

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

    // 等待AI处理完成
    console.log('4. 等待AI回复...\n');
    await new Promise(resolve => setTimeout(resolve, 8000));

    // 输出结果
    console.log('=== AI回复 ===\n');

    if (reasoning) {
        console.log('【AI的思考过程】');
        console.log(reasoning);
        console.log('');
    }

    if (toolCalls.length > 0) {
        console.log('【AI调用的工具】');
        toolCalls.forEach((call, i) => {
            console.log(`${i+1}. ${call.tool}:`);
            console.log(`   输入: ${JSON.stringify(call.input)}`);
            console.log(`   输出: ${call.output}`);
            console.log('');
        });
    }

    if (aiText) {
        console.log('【AI的最终回复】');
        console.log(aiText);
    } else {
        console.log('【AI的最终回复】');
        console.log('(未收到文本回复)');
    }

    process.exit(0);
}

test().catch(error => {
    console.error('测试失败:', error);
    process.exit(1);
});