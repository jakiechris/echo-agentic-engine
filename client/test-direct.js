import { createOpencodeClient } from "@opencode-ai/sdk/v2";

// 直接访问OpenCode服务（不通过Engine）
const client = createOpencodeClient({
    baseUrl: "http://127.0.0.1:33602"
});

let eventCount = 0;

const test = async function() {
    console.log('=== 直接访问OpenCode服务测试 ===\n');
    
    // 监听事件
    console.log('开始监听事件流...');
    const events = await client.event.subscribe();
    
    const eventPromise = (async () => {
        for await (const event of events.stream) {
            eventCount++;
            console.log(`Event #${eventCount}:`, event.type);
            if (eventCount >= 10) break; // 收到10个事件后退出
        }
        console.log('事件流结束');
    })();

    // 等待事件流建立
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 创建会话并发送prompt
    const session = await client.session.create({
        body: { title: "测试" },
    });
    console.log(`\n会话ID: ${session.data.id}\n`);

    const result = await client.session.prompt({
        sessionID: session.data.id,
        parts: [{ type: "text", text: "列出当前目录下的文件" }],
    });

    console.log(`\n模型: ${result.data?.info?.modelID}`);
    console.log(`Tokens: ${JSON.stringify(result.data?.info?.tokens)}`);

    // 等待更多事件
    await new Promise(resolve => setTimeout(resolve, 10000));
    console.log(`\n总共收到 ${eventCount} 个事件`);
    process.exit(0);
};

test().catch(error => {
    console.error('Error:', error);
    process.exit(1);
});
