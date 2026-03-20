#!/usr/bin/env node
/**
 * Echo Agentic Engine 测试客户端
 *
 * 功能：
 * 1. 携带自定义 headers 访问 /trans 接口
 * 2. 使用 OpenCode SDK 与 OpenCode Serve 交互
 * 3. 发送消息并打印流式响应
 */

import { OpencodeClient } from '@opencode-ai/sdk';

// 配置
const ENGINE_HOST = process.env.ENGINE_HOST || 'http://localhost:8000';
const DOMAIN_ID = process.env.DOMAIN_ID || 'test-domain';
const SANDBOX_ID = process.env.SANDBOX_ID || 'test-sandbox';

console.log('=== Echo Agentic Engine 测试客户端 ===\n');
console.log(`Engine 地址: ${ENGINE_HOST}`);
console.log(`Domain ID: ${DOMAIN_ID}`);
console.log(`Sandbox ID: ${SANDBOX_ID}\n`);

// 创建 OpenCode 客户端
const client = new OpencodeClient({
  baseURL: `${ENGINE_HOST}/trans`,
  defaultHeaders: {
    'X-Domain-ID': DOMAIN_ID,
    'X-Sandbox-ID': SANDBOX_ID,
  },
});

async function testHealthCheck() {
  console.log('--- 测试健康检查接口 ---');
  try {
    const response = await fetch(`${ENGINE_HOST}/trans/global/health`, {
      headers: {
        'X-Domain-ID': DOMAIN_ID,
        'X-Sandbox-ID': SANDBOX_ID,
      },
    });
    const data = await response.json();
    console.log('健康检查结果:', JSON.stringify(data, null, 2));
    console.log('✅ 健康检查通过\n');
    return true;
  } catch (error) {
    console.error('❌ 健康检查失败:', error.message);
    return false;
  }
}

async function testSessionChat() {
  console.log('--- 测试会话聊天接口 ---');

  try {
    // 1. 创建会话
    console.log('1. 创建会话...');
    const session = await client.session.create();
    console.log('会话创建成功:', JSON.stringify(session, null, 2));
    console.log('会话 ID:', session.id);

    // 2. 初始化会话
    console.log('\n2. 初始化会话...');
    const initResponse = await client.session.init(session.id);
    console.log('初始化成功:', JSON.stringify(initResponse, null, 2));

    // 3. 发送消息并接收流式响应
    console.log('\n3. 发送消息: "帮忙看看你的workspace都有什么文件"');
    console.log('开始接收流式响应...\n');
    console.log('=' .repeat(60));

    const chatStream = await client.session.chat(session.id, {
      content: [
        {
          type: 'text',
          text: '帮忙看看你的workspace都有什么文件'
        }
      ]
    });

    // 处理流式响应
    let fullResponse = '';
    let stepCount = 0;

    for await (const event of chatStream) {
      stepCount++;

      // 打印每个事件
      console.log(`\n[事件 ${stepCount}] ${event.type || 'unknown'}`);

      if (event.type === 'text') {
        // 文本片段
        console.log('文本内容:', event.text || event.content);
        fullResponse += event.text || event.content || '';
      } else if (event.type === 'step_start') {
        console.log('步骤开始:', event.name || event.step);
      } else if (event.type === 'step_finish') {
        console.log('步骤完成:', event.name || event.step);
      } else if (event.type === 'tool') {
        console.log('工具调用:', event.tool?.name || event.name);
        console.log('工具状态:', event.state);
        if (event.result) {
          console.log('工具结果:', JSON.stringify(event.result, null, 2));
        }
      } else if (event.type === 'file') {
        console.log('文件信息:', event.path || event.name);
      } else {
        // 其他事件类型
        console.log('事件数据:', JSON.stringify(event, null, 2));
      }
    }

    console.log('\n' + '=' .repeat(60));
    console.log('\n✅ 流式响应接收完成');
    console.log('\n=== 完整响应 ===');
    console.log(fullResponse || '(无文本响应)');

    // 4. 获取会话消息历史
    console.log('\n--- 获取会话消息历史 ---');
    const messages = await client.session.messages(session.id);
    console.log('消息数量:', messages.length);
    console.log('最后一条消息:', JSON.stringify(messages[messages.length - 1], null, 2));

    return true;
  } catch (error) {
    console.error('\n❌ 会话测试失败:', error.message);
    if (error.response) {
      console.error('响应状态:', error.response.status);
      console.error('响应数据:', error.response.data);
    }
    return false;
  }
}

async function testStreamingEvents() {
  console.log('\n--- 测试事件流接口 ---');

  try {
    console.log('连接事件流...');
    const eventStream = await client.event.list();

    let eventCount = 0;
    const maxEvents = 5; // 最多接收5个事件

    console.log('监听事件流（最多5个事件）...\n');

    for await (const event of eventStream) {
      eventCount++;
      console.log(`[事件 ${eventCount}]`, JSON.stringify(event, null, 2));

      if (eventCount >= maxEvents) {
        console.log('\n已接收5个事件，停止监听');
        eventStream.controller?.abort();
        break;
      }
    }

    console.log('✅ 事件流测试完成\n');
    return true;
  } catch (error) {
    console.error('❌ 事件流测试失败:', error.message);
    return false;
  }
}

async function listSessions() {
  console.log('\n--- 列出现有会话 ---');
  try {
    const sessions = await client.session.list();
    console.log('会话数量:', sessions.length);
    if (sessions.length > 0) {
      console.log('最近的会话:');
      sessions.slice(0, 3).forEach((s, i) => {
        console.log(`  ${i + 1}. ID: ${s.id}, 创建时间: ${s.createdAt}`);
      });
    }
    console.log('✅ 会话列表获取成功\n');
    return true;
  } catch (error) {
    console.error('❌ 获取会话列表失败:', error.message);
    return false;
  }
}

// 主测试流程
async function main() {
  console.log('开始测试...\n');

  // 测试1: 健康检查
  const healthOk = await testHealthCheck();

  if (!healthOk) {
    console.error('\n⚠️  Engine 未启动，请先启动服务');
    process.exit(1);
  }

  // 测试2: 列出会话
  await listSessions();

  // 测试3: 会话聊天（核心测试）
  const chatOk = await testSessionChat();

  if (!chatOk) {
    console.error('\n⚠️  会话聊天测试失败');
    process.exit(1);
  }

  console.log('\n=== 所有测试完成 ===');
  console.log('✅ 测试通过');

  process.exit(0);
}

// 错误处理
process.on('unhandledRejection', (error) => {
  console.error('\n❌ 未处理的错误:', error);
  process.exit(1);
});

// 运行测试
main().catch((error) => {
  console.error('\n❌ 测试执行失败:', error);
  process.exit(1);
});