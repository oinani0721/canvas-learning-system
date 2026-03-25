/**
 * Canvas Learning System - MSW Request Handlers
 *
 * Mock Service Worker 处理器，用于前端开发和测试时的 API Mock。
 *
 * 使用场景:
 * 1. 后端不可用时的前端开发
 * 2. 单元测试中隔离 API 调用
 * 3. Storybook 组件预览
 *
 * 配置:
 *   在 src/mocks/browser.ts 中启动 MSW
 *   在测试中使用 src/mocks/server.ts
 */

import { http, HttpResponse, delay } from 'msw';

// ═══════════════════════════════════════════════════════════════════════════════
// 类型定义
// ═══════════════════════════════════════════════════════════════════════════════

interface MemorySubject {
    id: string;
    name: string;
    entity_count: number;
    created_at: string;
}

interface MemoryEntity {
    id: string;
    name: string;
    summary: string;
    subject_id: string;
    created_at: string;
}

interface SearchResult {
    id: string;
    content: string;
    score: number;
    metadata: Record<string, unknown>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Mock 数据
// ═══════════════════════════════════════════════════════════════════════════════

const mockSubjects: MemorySubject[] = [
    {
        id: 'subj-math-001',
        name: 'Mathematics',
        entity_count: 15,
        created_at: new Date().toISOString(),
    },
    {
        id: 'subj-physics-001',
        name: 'Physics',
        entity_count: 10,
        created_at: new Date().toISOString(),
    },
    {
        id: 'subj-cs-001',
        name: 'Computer Science',
        entity_count: 20,
        created_at: new Date().toISOString(),
    },
];

const mockEntities: MemoryEntity[] = [
    {
        id: 'ent-calc-001',
        name: 'Calculus',
        summary: 'Study of continuous change and motion',
        subject_id: 'subj-math-001',
        created_at: new Date().toISOString(),
    },
    {
        id: 'ent-linear-001',
        name: 'Linear Algebra',
        summary: 'Study of vectors, matrices, and linear transformations',
        subject_id: 'subj-math-001',
        created_at: new Date().toISOString(),
    },
    {
        id: 'ent-quantum-001',
        name: 'Quantum Mechanics',
        summary: 'Study of matter and energy at atomic scales',
        subject_id: 'subj-physics-001',
        created_at: new Date().toISOString(),
    },
];

// ═══════════════════════════════════════════════════════════════════════════════
// API 基础 URL
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = 'http://localhost:8000';

// ═══════════════════════════════════════════════════════════════════════════════
// Request Handlers
// ═══════════════════════════════════════════════════════════════════════════════

export const handlers = [
    // ─────────────────────────────────────────────────────────────────────────────
    // Health Endpoint
    // ─────────────────────────────────────────────────────────────────────────────
    http.get(`${API_BASE}/api/v1/health`, async () => {
        await delay(50); // 模拟网络延迟

        return HttpResponse.json({
            status: 'healthy',
            services: {
                neo4j: { status: 'connected', latency_ms: 25 },
                graphiti: { status: 'connected', latency_ms: 15 },
                lancedb: { status: 'connected', latency_ms: 10 },
            },
            timestamp: new Date().toISOString(),
        });
    }),

    // ─────────────────────────────────────────────────────────────────────────────
    // Memory Subjects
    // ─────────────────────────────────────────────────────────────────────────────
    http.get(`${API_BASE}/api/v1/memory/subjects`, async () => {
        await delay(100);

        return HttpResponse.json({
            subjects: mockSubjects,
            total: mockSubjects.length,
        });
    }),

    http.get(`${API_BASE}/api/v1/memory/subjects/:subjectId`, async ({ params }) => {
        await delay(50);
        const { subjectId } = params;

        const subject = mockSubjects.find((s) => s.id === subjectId);
        if (!subject) {
            return HttpResponse.json(
                {
                    code: 404,
                    message: 'Subject not found',
                    error_type: 'NOT_FOUND',
                },
                { status: 404 }
            );
        }

        return HttpResponse.json(subject);
    }),

    // ─────────────────────────────────────────────────────────────────────────────
    // Memory Entities
    // ─────────────────────────────────────────────────────────────────────────────
    http.get(`${API_BASE}/api/v1/memory/entities`, async ({ request }) => {
        await delay(100);
        const url = new URL(request.url);
        const subjectId = url.searchParams.get('subject');

        let entities = mockEntities;
        if (subjectId) {
            entities = mockEntities.filter((e) => e.subject_id === subjectId);
        }

        return HttpResponse.json({
            entities,
            total: entities.length,
        });
    }),

    http.get(`${API_BASE}/api/v1/memory/entities/:entityId`, async ({ params }) => {
        await delay(50);
        const { entityId } = params;

        const entity = mockEntities.find((e) => e.id === entityId);
        if (!entity) {
            return HttpResponse.json(
                {
                    code: 404,
                    message: 'Entity not found',
                    error_type: 'NOT_FOUND',
                },
                { status: 404 }
            );
        }

        return HttpResponse.json(entity);
    }),

    // ─────────────────────────────────────────────────────────────────────────────
    // Memory Search
    // ─────────────────────────────────────────────────────────────────────────────
    http.post(`${API_BASE}/api/v1/memory/search`, async ({ request }) => {
        await delay(200);

        const body = (await request.json()) as { query?: string; limit?: number };

        if (!body.query) {
            return HttpResponse.json(
                {
                    detail: [
                        {
                            loc: ['body', 'query'],
                            msg: 'Field required',
                            type: 'missing',
                        },
                    ],
                },
                { status: 422 }
            );
        }

        // 模拟搜索结果
        const results: SearchResult[] = mockEntities
            .filter(
                (e) =>
                    e.name.toLowerCase().includes(body.query!.toLowerCase()) ||
                    e.summary.toLowerCase().includes(body.query!.toLowerCase())
            )
            .slice(0, body.limit || 10)
            .map((e, index) => ({
                id: `result-${e.id}`,
                content: e.summary,
                score: 0.95 - index * 0.1,
                metadata: {
                    source: 'canvas',
                    entity_id: e.id,
                    entity_name: e.name,
                },
            }));

        return HttpResponse.json({
            results,
            total: results.length,
            query_time_ms: Math.floor(Math.random() * 100) + 50,
        });
    }),

    // ─────────────────────────────────────────────────────────────────────────────
    // RAG Query
    // ─────────────────────────────────────────────────────────────────────────────
    http.post(`${API_BASE}/api/v1/rag/query`, async ({ request }) => {
        await delay(500);

        const body = (await request.json()) as { query?: string; top_k?: number };

        if (!body.query) {
            return HttpResponse.json(
                {
                    detail: [
                        {
                            loc: ['body', 'query'],
                            msg: 'Field required',
                            type: 'missing',
                        },
                    ],
                },
                { status: 422 }
            );
        }

        return HttpResponse.json({
            answer: `Based on your query about "${body.query}", here is a comprehensive response based on the knowledge graph...`,
            sources: mockEntities.slice(0, body.top_k || 3).map((e) => ({
                id: e.id,
                content: e.summary,
                relevance: 0.9,
            })),
            confidence: 0.85,
            processing_time_ms: 450,
        });
    }),

    // ─────────────────────────────────────────────────────────────────────────────
    // Canvas Operations
    // ─────────────────────────────────────────────────────────────────────────────
    http.post(`${API_BASE}/api/v1/canvas/parse`, async ({ request }) => {
        await delay(100);

        const body = (await request.json()) as { content?: string; format?: string };

        if (!body.content) {
            return HttpResponse.json(
                {
                    detail: [
                        {
                            loc: ['body', 'content'],
                            msg: 'Field required',
                            type: 'missing',
                        },
                    ],
                },
                { status: 422 }
            );
        }

        return HttpResponse.json({
            nodes: [
                { id: 'node-1', type: 'text', text: 'Parsed node 1', x: 0, y: 0 },
                { id: 'node-2', type: 'text', text: 'Parsed node 2', x: 200, y: 0 },
            ],
            edges: [{ id: 'edge-1', fromNode: 'node-1', toNode: 'node-2' }],
            metadata: {
                parse_time_ms: 50,
                node_count: 2,
                edge_count: 1,
            },
        });
    }),

    // ─────────────────────────────────────────────────────────────────────────────
    // Monitoring
    // ─────────────────────────────────────────────────────────────────────────────
    http.get(`${API_BASE}/api/v1/monitoring/metrics`, async ({ request }) => {
        await delay(50);
        const url = new URL(request.url);
        const window = parseInt(url.searchParams.get('window') || '60', 10);

        return HttpResponse.json({
            window_seconds: window,
            metrics: {
                request_count: 1250,
                error_rate: 0.02,
                avg_response_time_ms: 150,
                p95_response_time_ms: 350,
                p99_response_time_ms: 500,
            },
            endpoints: [
                { path: '/api/v1/health', count: 500, avg_ms: 20 },
                { path: '/api/v1/memory/search', count: 300, avg_ms: 200 },
                { path: '/api/v1/rag/query', count: 150, avg_ms: 450 },
            ],
            timestamp: new Date().toISOString(),
        });
    }),

    // ─────────────────────────────────────────────────────────────────────────────
    // Review System
    // ─────────────────────────────────────────────────────────────────────────────
    http.get(`${API_BASE}/api/v1/review/schedule`, async () => {
        await delay(100);

        return HttpResponse.json({
            items: [
                {
                    id: 'review-001',
                    entity_id: 'ent-calc-001',
                    entity_name: 'Calculus',
                    due_date: new Date().toISOString(),
                    priority: 'high',
                    retention: 0.7,
                },
                {
                    id: 'review-002',
                    entity_id: 'ent-linear-001',
                    entity_name: 'Linear Algebra',
                    due_date: new Date(Date.now() + 86400000).toISOString(),
                    priority: 'medium',
                    retention: 0.85,
                },
            ],
            total: 2,
            next_review: new Date().toISOString(),
        });
    }),
];

export default handlers;
