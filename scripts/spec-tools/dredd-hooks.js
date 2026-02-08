/**
 * Dredd Hooks for Canvas Learning System API Contract Testing
 *
 * 这个文件定义了 Dredd 合约测试的钩子函数，用于：
 * 1. 跳过需要认证的端点
 * 2. 设置测试数据
 * 3. 处理动态路径参数
 * 4. 跳过 WebSocket 端点
 */

const hooks = require('hooks');

// ═══════════════════════════════════════════════════════════════════════════════
// 全局配置
// ═══════════════════════════════════════════════════════════════════════════════

// 跳过需要特殊处理的端点
const SKIP_ENDPOINTS = [
    // WebSocket 端点
    '/ws/intelligent-parallel/{session_id}',

    // 需要预先存在数据的端点
    '/api/v1/memory/entities/{entity_id}',
    '/api/v1/memory/graphs/{graph_id}',
    '/api/v1/review/sessions/{session_id}',

    // 可能有副作用的端点
    '/api/v1/rollback/execute',
    '/api/v1/debug/reset',
];

// 需要特殊请求体的端点
const ENDPOINTS_WITH_BODY = {
    '/api/v1/canvas/parse': {
        content: '# Test Canvas\n\n- Node 1\n- Node 2',
        format: 'markdown'
    },
    '/api/v1/rag/query': {
        query: 'test query',
        top_k: 5
    },
    '/api/v1/agents/process': {
        input: 'test input',
        agent_type: 'default'
    }
};

// ═══════════════════════════════════════════════════════════════════════════════
// 全局钩子
// ═══════════════════════════════════════════════════════════════════════════════

hooks.beforeAll((transactions, done) => {
    console.log('Starting Canvas API contract tests...');
    console.log(`Total transactions: ${transactions.length}`);
    done();
});

hooks.afterAll((transactions, done) => {
    const passed = transactions.filter(t => t.test && t.test.status === 'pass').length;
    const failed = transactions.filter(t => t.test && t.test.status === 'fail').length;
    const skipped = transactions.filter(t => t.skip).length;

    console.log('\n=== Contract Test Summary ===');
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Skipped: ${skipped}`);
    done();
});

// ═══════════════════════════════════════════════════════════════════════════════
// 单个请求钩子
// ═══════════════════════════════════════════════════════════════════════════════

hooks.beforeEach((transaction, done) => {
    const endpoint = transaction.name.split(' > ')[0];

    // 跳过特定端点
    if (SKIP_ENDPOINTS.some(skip => endpoint.includes(skip))) {
        console.log(`Skipping: ${endpoint}`);
        transaction.skip = true;
        return done();
    }

    // 设置通用请求头
    if (!transaction.request.headers) {
        transaction.request.headers = {};
    }
    transaction.request.headers['Content-Type'] = 'application/json';
    transaction.request.headers['Accept'] = 'application/json';

    // 替换路径参数为测试值
    transaction.fullPath = transaction.fullPath
        .replace('{session_id}', 'test-session-001')
        .replace('{entity_id}', 'test-entity-001')
        .replace('{graph_id}', 'test-graph-001')
        .replace('{node_id}', 'test-node-001')
        .replace('{subject}', 'test-subject');

    // 设置特殊请求体
    const bodyConfig = ENDPOINTS_WITH_BODY[endpoint];
    if (bodyConfig && transaction.request.method !== 'GET') {
        transaction.request.body = JSON.stringify(bodyConfig);
    }

    done();
});

hooks.afterEach((transaction, done) => {
    if (transaction.test && transaction.test.status === 'fail') {
        console.log(`\nFailed: ${transaction.name}`);
        console.log(`  Expected: ${transaction.expected.statusCode}`);
        console.log(`  Actual: ${transaction.real.statusCode}`);
        if (transaction.real.body) {
            try {
                const body = JSON.parse(transaction.real.body);
                console.log(`  Response: ${JSON.stringify(body, null, 2).substring(0, 500)}`);
            } catch (e) {
                console.log(`  Response: ${transaction.real.body.substring(0, 500)}`);
            }
        }
    }
    done();
});

// ═══════════════════════════════════════════════════════════════════════════════
// 特定端点钩子
// ═══════════════════════════════════════════════════════════════════════════════

// Health 端点 - 应该总是成功
hooks.before('/api/v1/health > GET', (transaction, done) => {
    console.log('Testing health endpoint...');
    done();
});

// Memory 端点 - 可能需要 Neo4j 连接
hooks.before('/api/v1/memory/* > *', (transaction, done) => {
    // 如果 Neo4j 不可用，跳过测试
    // 这里可以添加连接检查逻辑
    done();
});

// Canvas 解析端点 - 需要有效的 Canvas 内容
hooks.before('/api/v1/canvas/parse > POST', (transaction, done) => {
    transaction.request.body = JSON.stringify({
        content: '# Test Canvas\n\n%%\n{"nodes":[],"edges":[]}\n%%',
        format: 'obsidian'
    });
    done();
});

// RAG 查询端点 - 需要有效的查询
hooks.before('/api/v1/rag/query > POST', (transaction, done) => {
    transaction.request.body = JSON.stringify({
        query: 'What is machine learning?',
        top_k: 3,
        subject: 'test'
    });
    done();
});

// 监控端点 - 需要有效的时间范围
hooks.before('/api/v1/monitoring/metrics > GET', (transaction, done) => {
    transaction.fullPath += '?window=60';
    done();
});

module.exports = hooks;
