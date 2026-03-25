/**
 * Canvas Learning System - Memory API Contract Tests (Pact)
 *
 * 消费者驱动的契约测试，验证前端与后端 API 的契约一致性。
 *
 * 使用方法:
 *   npm run test:pact
 *
 * 生成的契约文件:
 *   pacts/canvas-frontend-canvas-backend.json
 */

import { PactV4, MatchersV3 } from '@pact-foundation/pact';
import path from 'path';

// 模拟 API 客户端（根据实际项目调整）
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

interface HealthResponse {
    status: string;
    services: Record<string, { status: string; latency_ms?: number }>;
    timestamp: string;
}

// 使用 MatchersV3 进行灵活匹配
const { like, eachLike, string, integer, timestamp } = MatchersV3;

describe('Canvas Memory API Contract', () => {
    // Pact 配置
    const pact = new PactV4({
        consumer: 'Canvas-Frontend',
        provider: 'Canvas-Backend',
        dir: path.resolve(__dirname, '../../../pacts'),
        logLevel: 'warn',
    });

    // ═══════════════════════════════════════════════════════════════════════════════
    // Health Endpoint
    // ═══════════════════════════════════════════════════════════════════════════════

    describe('GET /api/v1/health', () => {
        it('returns health status', async () => {
            await pact
                .addInteraction()
                .given('the API is healthy')
                .uponReceiving('a request for health status')
                .withRequest('GET', '/api/v1/health')
                .willRespondWith(200, (builder) => {
                    builder.headers({ 'Content-Type': 'application/json' });
                    builder.jsonBody({
                        status: string('healthy'),
                        services: like({
                            neo4j: like({
                                status: string('connected'),
                                latency_ms: integer(50),
                            }),
                        }),
                        timestamp: timestamp("yyyy-MM-dd'T'HH:mm:ss.SSSXXX"),
                    });
                })
                .executeTest(async (mockServer) => {
                    const response = await fetch(`${mockServer.url}/api/v1/health`);
                    expect(response.status).toBe(200);

                    const data: HealthResponse = await response.json();
                    expect(data.status).toBe('healthy');
                    expect(data.services).toBeDefined();
                    expect(data.timestamp).toBeDefined();
                });
        });
    });

    // ═══════════════════════════════════════════════════════════════════════════════
    // Memory Subjects
    // ═══════════════════════════════════════════════════════════════════════════════

    describe('GET /api/v1/memory/subjects', () => {
        it('returns list of memory subjects', async () => {
            await pact
                .addInteraction()
                .given('memory subjects exist')
                .uponReceiving('a request for all memory subjects')
                .withRequest('GET', '/api/v1/memory/subjects')
                .willRespondWith(200, (builder) => {
                    builder.headers({ 'Content-Type': 'application/json' });
                    builder.jsonBody({
                        subjects: eachLike({
                            id: string('subj-001'),
                            name: string('Mathematics'),
                            entity_count: integer(10),
                            created_at: timestamp("yyyy-MM-dd'T'HH:mm:ss.SSSXXX"),
                        }),
                        total: integer(1),
                    });
                })
                .executeTest(async (mockServer) => {
                    const response = await fetch(`${mockServer.url}/api/v1/memory/subjects`);
                    expect(response.status).toBe(200);

                    const data = await response.json();
                    expect(Array.isArray(data.subjects)).toBe(true);
                    expect(typeof data.total).toBe('number');
                });
        });

        it('returns empty list when no subjects exist', async () => {
            await pact
                .addInteraction()
                .given('no memory subjects exist')
                .uponReceiving('a request for memory subjects when empty')
                .withRequest('GET', '/api/v1/memory/subjects')
                .willRespondWith(200, (builder) => {
                    builder.headers({ 'Content-Type': 'application/json' });
                    builder.jsonBody({
                        subjects: [],
                        total: integer(0),
                    });
                })
                .executeTest(async (mockServer) => {
                    const response = await fetch(`${mockServer.url}/api/v1/memory/subjects`);
                    expect(response.status).toBe(200);

                    const data = await response.json();
                    expect(data.subjects).toEqual([]);
                    expect(data.total).toBe(0);
                });
        });
    });

    // ═══════════════════════════════════════════════════════════════════════════════
    // Memory Entities
    // ═══════════════════════════════════════════════════════════════════════════════

    describe('GET /api/v1/memory/entities', () => {
        it('returns list of entities for a subject', async () => {
            await pact
                .addInteraction()
                .given('entities exist for subject math-001')
                .uponReceiving('a request for entities by subject')
                .withRequest('GET', '/api/v1/memory/entities', (builder) => {
                    builder.query({ subject: 'math-001' });
                })
                .willRespondWith(200, (builder) => {
                    builder.headers({ 'Content-Type': 'application/json' });
                    builder.jsonBody({
                        entities: eachLike({
                            id: string('ent-001'),
                            name: string('Calculus'),
                            summary: string('Study of continuous change'),
                            subject_id: string('math-001'),
                            created_at: timestamp("yyyy-MM-dd'T'HH:mm:ss.SSSXXX"),
                        }),
                        total: integer(1),
                    });
                })
                .executeTest(async (mockServer) => {
                    const response = await fetch(
                        `${mockServer.url}/api/v1/memory/entities?subject=math-001`
                    );
                    expect(response.status).toBe(200);

                    const data = await response.json();
                    expect(Array.isArray(data.entities)).toBe(true);
                    data.entities.forEach((entity: MemoryEntity) => {
                        expect(entity.subject_id).toBe('math-001');
                    });
                });
        });
    });

    // ═══════════════════════════════════════════════════════════════════════════════
    // Memory Search
    // ═══════════════════════════════════════════════════════════════════════════════

    describe('POST /api/v1/memory/search', () => {
        it('searches memory with query', async () => {
            await pact
                .addInteraction()
                .given('memory contains searchable content')
                .uponReceiving('a search request')
                .withRequest('POST', '/api/v1/memory/search', (builder) => {
                    builder.headers({ 'Content-Type': 'application/json' });
                    builder.jsonBody({
                        query: string('calculus derivative'),
                        limit: integer(10),
                    });
                })
                .willRespondWith(200, (builder) => {
                    builder.headers({ 'Content-Type': 'application/json' });
                    builder.jsonBody({
                        results: eachLike({
                            id: string('result-001'),
                            content: string('Derivative is the rate of change'),
                            score: like(0.95),
                            metadata: like({
                                source: string('canvas'),
                            }),
                        }),
                        total: integer(1),
                        query_time_ms: integer(50),
                    });
                })
                .executeTest(async (mockServer) => {
                    const response = await fetch(`${mockServer.url}/api/v1/memory/search`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            query: 'calculus derivative',
                            limit: 10,
                        }),
                    });
                    expect(response.status).toBe(200);

                    const data = await response.json();
                    expect(Array.isArray(data.results)).toBe(true);
                    expect(typeof data.query_time_ms).toBe('number');
                });
        });
    });

    // ═══════════════════════════════════════════════════════════════════════════════
    // Error Handling
    // ═══════════════════════════════════════════════════════════════════════════════

    describe('Error Responses', () => {
        it('returns 404 for non-existent entity', async () => {
            await pact
                .addInteraction()
                .given('entity with id non-existent does not exist')
                .uponReceiving('a request for a non-existent entity')
                .withRequest('GET', '/api/v1/memory/entities/non-existent')
                .willRespondWith(404, (builder) => {
                    builder.headers({ 'Content-Type': 'application/json' });
                    builder.jsonBody({
                        code: integer(404),
                        message: string('Entity not found'),
                        error_type: string('NOT_FOUND'),
                    });
                })
                .executeTest(async (mockServer) => {
                    const response = await fetch(
                        `${mockServer.url}/api/v1/memory/entities/non-existent`
                    );
                    expect(response.status).toBe(404);

                    const data = await response.json();
                    expect(data.code).toBe(404);
                    expect(data.error_type).toBe('NOT_FOUND');
                });
        });

        it('returns 400 for invalid request body', async () => {
            await pact
                .addInteraction()
                .given('API expects valid JSON')
                .uponReceiving('a request with invalid body')
                .withRequest('POST', '/api/v1/memory/search', (builder) => {
                    builder.headers({ 'Content-Type': 'application/json' });
                    builder.jsonBody({
                        // Missing required 'query' field
                        limit: integer(10),
                    });
                })
                .willRespondWith(422, (builder) => {
                    builder.headers({ 'Content-Type': 'application/json' });
                    builder.jsonBody({
                        detail: eachLike({
                            loc: eachLike(string('body')),
                            msg: string('Field required'),
                            type: string('missing'),
                        }),
                    });
                })
                .executeTest(async (mockServer) => {
                    const response = await fetch(`${mockServer.url}/api/v1/memory/search`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ limit: 10 }),
                    });
                    expect(response.status).toBe(422);

                    const data = await response.json();
                    expect(Array.isArray(data.detail)).toBe(true);
                });
        });
    });
});
