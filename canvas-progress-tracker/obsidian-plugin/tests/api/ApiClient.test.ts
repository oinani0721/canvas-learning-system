/**
 * Canvas Learning System - API Client Tests
 *
 * Comprehensive unit tests for the ApiClient class covering:
 * - All 19 API endpoints (health, canvas, agent, review)
 * - Error handling scenarios
 * - Retry mechanism with exponential backoff
 * - Timeout control
 *
 * @source Story 13.3 - Unit Tests (AC: 7)
 */

import { ApiClient, createDefaultApiClient } from '../../src/api/ApiClient';
import {
  ApiError,
  NodeCreate,
  EdgeCreate,
  DecomposeRequest,
  ScoreRequest,
  ExplainRequest,
  GenerateReviewRequest,
  RecordReviewRequest,
} from '../../src/api/types';

// ===========================================================================
// Mock Setup
// ===========================================================================

// Store original fetch
const originalFetch = global.fetch;

// Mock fetch implementation
let mockFetchImpl: jest.Mock;

beforeEach(() => {
  // Reset mock before each test
  mockFetchImpl = jest.fn();
  global.fetch = mockFetchImpl;
  jest.useFakeTimers();
});

afterEach(() => {
  global.fetch = originalFetch;
  jest.useRealTimers();
});

// Helper to create mock Response
function createMockResponse(
  data: unknown,
  status = 200,
  statusText = 'OK'
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json: jest.fn().mockResolvedValue(data),
    headers: new Headers(),
    redirected: false,
    type: 'basic',
    url: '',
    clone: jest.fn(),
    body: null,
    bodyUsed: false,
    arrayBuffer: jest.fn(),
    blob: jest.fn(),
    formData: jest.fn(),
    text: jest.fn(),
  } as unknown as Response;
}

// ===========================================================================
// Constructor Tests
// ===========================================================================

describe('ApiClient Constructor', () => {
  test('should create client with default configuration', () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
    });

    expect(client.getBaseUrl()).toBe('http://localhost:8000/api/v1');
    expect(client.getTimeout()).toBe(60000); // Story 12.F.6: increased from 30s to 60s
    expect(client.getRetryPolicy().maxRetries).toBe(3);
  });

  test('should create client with custom configuration', () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1/',
      timeout: 60000,
      maxRetries: 5,
      retryBackoffMs: 2000,
    });

    // Should remove trailing slash
    expect(client.getBaseUrl()).toBe('http://localhost:8000/api/v1');
    expect(client.getTimeout()).toBe(60000);
    expect(client.getRetryPolicy().maxRetries).toBe(5);
    expect(client.getRetryPolicy().backoffMs).toBe(2000);
  });

  test('createDefaultApiClient should create client with defaults', () => {
    const client = createDefaultApiClient();
    expect(client.getBaseUrl()).toBe('http://localhost:8000/api/v1');
  });

  test('createDefaultApiClient should accept custom baseUrl', () => {
    const client = createDefaultApiClient('http://custom:9000/api/v2');
    expect(client.getBaseUrl()).toBe('http://custom:9000/api/v2');
  });
});

// ===========================================================================
// Health Check Tests
// ===========================================================================

describe('Health Check API', () => {
  test('healthCheck should return health status', async () => {
    const mockResponse = {
      status: 'healthy',
      timestamp: '2025-01-27T10:00:00Z',
      version: '1.0.0',
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
    });
    const result = await client.healthCheck();

    expect(result.status).toBe('healthy');
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/health',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'Content-Type': 'application/json; charset=utf-8',
        }),
      })
    );
  });

  test('testConnection should return true on success', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({ status: 'healthy' })
    );

    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
    });
    const result = await client.testConnection();

    expect(result).toBe(true);
  });

  test('testConnection should return false on failure', async () => {
    mockFetchImpl.mockRejectedValueOnce(new TypeError('Network error'));

    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });
    const result = await client.testConnection();

    expect(result).toBe(false);
  });
});

// ===========================================================================
// Canvas API Tests
// ===========================================================================

describe('Canvas API', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0, // Disable retries for faster tests
    });
  });

  test('readCanvas should fetch canvas data', async () => {
    const mockCanvas = {
      name: 'test.canvas',
      nodes: [{ id: 'node1', type: 'text', x: 0, y: 0 }],
      edges: [],
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockCanvas));

    const result = await client.readCanvas('test.canvas');

    expect(result.name).toBe('test.canvas');
    expect(result.nodes).toHaveLength(1);
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/canvas/test.canvas',
      expect.any(Object)
    );
  });

  test('readCanvas should encode canvas name', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({ name: '', nodes: [], edges: [] })
    );

    await client.readCanvas('test canvas.canvas');

    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/canvas/test%20canvas.canvas',
      expect.any(Object)
    );
  });

  test('createNode should create a new node', async () => {
    const nodeCreate: NodeCreate = {
      type: 'text',
      text: 'Test node',
      x: 100,
      y: 200,
      width: 400,
      height: 300,
      color: '1',
    };
    const mockNode = { id: 'new-node-id', ...nodeCreate };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockNode, 201));

    const result = await client.createNode('test.canvas', nodeCreate);

    expect(result.id).toBe('new-node-id');
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/canvas/test.canvas/nodes',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(nodeCreate),
      })
    );
  });

  test('updateNode should update an existing node', async () => {
    const update = { text: 'Updated text', color: '5' as const };
    const mockNode = { id: 'node1', type: 'text', x: 0, y: 0, ...update };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockNode));

    const result = await client.updateNode('test.canvas', 'node1', update);

    expect(result.text).toBe('Updated text');
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/canvas/test.canvas/nodes/node1',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify(update),
      })
    );
  });

  test('deleteNode should delete a node', async () => {
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(null, 204));

    await client.deleteNode('test.canvas', 'node1');

    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/canvas/test.canvas/nodes/node1',
      expect.objectContaining({ method: 'DELETE' })
    );
  });

  test('createEdge should create a new edge', async () => {
    const edgeCreate: EdgeCreate = {
      fromNode: 'node1',
      toNode: 'node2',
      fromSide: 'right',
      toSide: 'left',
    };
    const mockEdge = { id: 'new-edge-id', ...edgeCreate };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockEdge, 201));

    const result = await client.createEdge('test.canvas', edgeCreate);

    expect(result.id).toBe('new-edge-id');
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/canvas/test.canvas/edges',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(edgeCreate),
      })
    );
  });

  test('deleteEdge should delete an edge', async () => {
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(null, 204));

    await client.deleteEdge('test.canvas', 'edge1');

    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/canvas/test.canvas/edges/edge1',
      expect.objectContaining({ method: 'DELETE' })
    );
  });
});

// ===========================================================================
// Agent API Tests
// ===========================================================================

describe('Agent API', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });
  });

  test('decomposeBasic should decompose a concept', async () => {
    const request: DecomposeRequest = {
      canvas_name: 'test.canvas',
      node_id: 'concept-node',
    };
    const mockResponse = {
      questions: ['What is X?', 'Why is X important?'],
      created_nodes: [{ id: 'q1', type: 'text', x: 0, y: 0 }],
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const result = await client.decomposeBasic(request);

    expect(result.questions).toHaveLength(2);
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/agents/decompose/basic',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(request),
      })
    );
  });

  test('decomposeDeep should perform deep decomposition', async () => {
    const request: DecomposeRequest = {
      canvas_name: 'test.canvas',
      node_id: 'concept-node',
    };
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({
        questions: ['Deep Q1'],
        created_nodes: [],
      })
    );

    await client.decomposeDeep(request);

    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/agents/decompose/deep',
      expect.any(Object)
    );
  });

  test('scoreUnderstanding should score nodes', async () => {
    const request: ScoreRequest = {
      canvas_name: 'test.canvas',
      node_ids: ['node1', 'node2'],
    };
    const mockResponse = {
      scores: [
        {
          node_id: 'node1',
          accuracy: 8,
          imagery: 7,
          completeness: 9,
          originality: 6,
          total: 30,
          new_color: '3',
        },
      ],
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const result = await client.scoreUnderstanding(request);

    expect(result.scores).toHaveLength(1);
    expect(result.scores[0].total).toBe(30);
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/agents/score',
      expect.any(Object)
    );
  });

  test.each([
    ['explainOral', '/agents/explain/oral'],
    ['explainClarification', '/agents/explain/clarification'],
    ['explainComparison', '/agents/explain/comparison'],
    ['explainMemory', '/agents/explain/memory'],
    ['explainFourLevel', '/agents/explain/four-level'],
    ['explainExample', '/agents/explain/example'],
  ])('%s should call correct endpoint', async (method, endpoint) => {
    const request: ExplainRequest = {
      canvas_name: 'test.canvas',
      node_id: 'node1',
    };
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({
        explanation: 'Test explanation',
        created_node_id: 'new-node',
      })
    );

    // Call the method dynamically
    const clientAny = client as any;
    await clientAny[method](request);

    expect(mockFetchImpl).toHaveBeenCalledWith(
      `http://localhost:8000/api/v1${endpoint}`,
      expect.objectContaining({ method: 'POST' })
    );
  });
});

// ===========================================================================
// Review API Tests
// ===========================================================================

describe('Review API', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });
  });

  test('getReviewSchedule should fetch schedule', async () => {
    const mockResponse = {
      items: [
        {
          canvas_name: 'test.canvas',
          node_id: 'node1',
          concept: 'Test',
          due_date: '2025-01-28',
          interval_days: 1,
        },
      ],
      total_count: 1,
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const result = await client.getReviewSchedule();

    expect(result.items).toHaveLength(1);
    expect(result.total_count).toBe(1);
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/review/schedule',
      expect.objectContaining({ method: 'GET' })
    );
  });

  test('generateReview should generate verification canvas', async () => {
    const request: GenerateReviewRequest = {
      source_canvas: 'test.canvas',
      node_ids: ['node1', 'node2'],
    };
    const mockResponse = {
      verification_canvas_name: 'test-verification-20250128.canvas',
      node_count: 2,
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const result = await client.generateReview(request);

    expect(result.verification_canvas_name).toContain('verification');
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/review/generate',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(request),
      })
    );
  });

  test('recordReview should record a review result', async () => {
    const request: RecordReviewRequest = {
      canvas_name: 'test.canvas',
      node_id: 'node1',
      score: 35,
    };
    const mockResponse = {
      next_review_date: '2025-02-04',
      new_interval: 7,
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const result = await client.recordReview(request);

    expect(result.next_review_date).toBe('2025-02-04');
    expect(result.new_interval).toBe(7);
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/review/record',
      expect.objectContaining({ method: 'POST' })
    );
  });
});

// ===========================================================================
// Error Handling Tests
// ===========================================================================

describe('Error Handling', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0, // Disable retries for error tests
    });
  });

  test('should throw NetworkError on fetch TypeError', async () => {
    mockFetchImpl.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    try {
      await client.healthCheck();
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('NetworkError');
    }
  });

  test('should throw TimeoutError on abort', async () => {
    // Simulate timeout by having fetch throw AbortError
    const abortError = new Error('Aborted');
    abortError.name = 'AbortError';
    mockFetchImpl.mockRejectedValueOnce(abortError);

    try {
      await client.healthCheck();
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('TimeoutError');
      expect((error as ApiError).statusCode).toBe(408);
    }
  });

  test('should throw HttpError4xx on 400 response', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse(
        { code: 400, message: 'Bad Request', details: { field: 'invalid' } },
        400,
        'Bad Request'
      )
    );

    try {
      await client.healthCheck();
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('HttpError4xx');
      expect((error as ApiError).statusCode).toBe(400);
    }
  });

  test('should throw HttpError4xx on 404 response', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({ code: 404, message: 'Not Found' }, 404, 'Not Found')
    );

    try {
      await client.readCanvas('nonexistent.canvas');
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('HttpError4xx');
      expect((error as ApiError).statusCode).toBe(404);
    }
  });

  test('should throw HttpError4xx on 422 validation error', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse(
        {
          code: 422,
          message: 'Validation Error',
          details: { body: ['Invalid format'] },
        },
        422,
        'Unprocessable Entity'
      )
    );

    try {
      await client.healthCheck();
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('HttpError4xx');
      expect((error as ApiError).statusCode).toBe(422);
    }
  });

  test('should throw HttpError5xx on 500 response', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse(
        { code: 500, message: 'Internal Server Error' },
        500,
        'Internal Server Error'
      )
    );

    try {
      await client.healthCheck();
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('HttpError5xx');
      expect((error as ApiError).statusCode).toBe(500);
    }
  });

  test('should throw HttpError5xx on 503 response', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse(
        { code: 503, message: 'Service Unavailable' },
        503,
        'Service Unavailable'
      )
    );

    try {
      await client.healthCheck();
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('HttpError5xx');
      expect((error as ApiError).statusCode).toBe(503);
    }
  });

  test('ApiError should provide user-friendly messages', () => {
    const networkError = new ApiError('Connection failed', 'NetworkError', 0);
    expect(networkError.getUserFriendlyMessage()).toBe(
      '无法连接到服务器，请检查网络连接'
    );

    const timeoutError = new ApiError('Timeout', 'TimeoutError', 408);
    expect(timeoutError.getUserFriendlyMessage()).toBe('请求超时，请重试');

    const http4xxError = new ApiError('Not found', 'HttpError4xx', 404);
    expect(http4xxError.getUserFriendlyMessage()).toBe(
      '请求参数错误: Not found'
    );

    const http5xxError = new ApiError('Server error', 'HttpError5xx', 500);
    expect(http5xxError.getUserFriendlyMessage()).toBe(
      '服务器错误: Server error'
    );

    // Test ValidationError message
    const validationError = new ApiError(
      'Validation failed',
      'ValidationError',
      422,
      { field: 'name', error: 'required' }
    );
    expect(validationError.getUserFriendlyMessage()).toBe(
      '数据验证失败: {"field":"name","error":"required"}'
    );

    // Test UnknownError message
    const unknownError = new ApiError('Something went wrong', 'UnknownError', 0);
    expect(unknownError.getUserFriendlyMessage()).toBe(
      '未知错误: Something went wrong'
    );
  });

  test('should handle non-Error throws as UnknownError', async () => {
    // Test case where fetch throws a non-Error value (like a string)
    mockFetchImpl.mockRejectedValueOnce('string error');

    try {
      await client.healthCheck();
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('UnknownError');
      expect((error as ApiError).message).toBe('Unknown error occurred');
    }
  });
});

// ===========================================================================
// Retry Mechanism Tests
// ===========================================================================

describe('Retry Mechanism', () => {
  test('should retry on network error and succeed', async () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 2,
      retryBackoffMs: 100,
    });

    // First call fails, second succeeds
    mockFetchImpl
      .mockRejectedValueOnce(new TypeError('Network error'))
      .mockResolvedValueOnce(createMockResponse({ status: 'healthy' }));

    // Start the request
    const promise = client.healthCheck();

    // Advance timer for retry delay
    await jest.advanceTimersByTimeAsync(100);

    const result = await promise;

    expect(result.status).toBe('healthy');
    expect(mockFetchImpl).toHaveBeenCalledTimes(2);
  });

  test('should retry on 5xx error and succeed', async () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 2,
      retryBackoffMs: 100,
    });

    // First call returns 503, second succeeds
    mockFetchImpl
      .mockResolvedValueOnce(
        createMockResponse(
          { code: 503, message: 'Unavailable' },
          503,
          'Service Unavailable'
        )
      )
      .mockResolvedValueOnce(createMockResponse({ status: 'healthy' }));

    const promise = client.healthCheck();
    await jest.advanceTimersByTimeAsync(100);

    const result = await promise;

    expect(result.status).toBe('healthy');
    expect(mockFetchImpl).toHaveBeenCalledTimes(2);
  });

  test('should use exponential backoff', async () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 3,
      retryBackoffMs: 1000,
    });

    // All calls fail except last
    mockFetchImpl
      .mockRejectedValueOnce(new TypeError('Network error'))
      .mockRejectedValueOnce(new TypeError('Network error'))
      .mockRejectedValueOnce(new TypeError('Network error'))
      .mockResolvedValueOnce(createMockResponse({ status: 'healthy' }));

    const promise = client.healthCheck();

    // First retry after 1000ms
    await jest.advanceTimersByTimeAsync(1000);
    // Second retry after 2000ms (1000 * 2^1)
    await jest.advanceTimersByTimeAsync(2000);
    // Third retry after 4000ms (1000 * 2^2)
    await jest.advanceTimersByTimeAsync(4000);

    const result = await promise;

    expect(result.status).toBe('healthy');
    expect(mockFetchImpl).toHaveBeenCalledTimes(4);
  });

  test('should fail after max retries exceeded', async () => {
    // Use real timers for this test with very short backoff
    jest.useRealTimers();

    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 2,
      retryBackoffMs: 10, // Very short for fast testing
    });

    // All calls fail
    mockFetchImpl.mockRejectedValue(new TypeError('Network error'));

    try {
      await client.healthCheck();
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('NetworkError');
    }

    // Original + 2 retries = 3 calls
    expect(mockFetchImpl).toHaveBeenCalledTimes(3);

    // Restore fake timers for other tests
    jest.useFakeTimers();
  });

  test('should NOT retry on 4xx errors', async () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 3,
      retryBackoffMs: 100,
    });

    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({ code: 400, message: 'Bad Request' }, 400)
    );

    await expect(client.healthCheck()).rejects.toThrow(ApiError);

    // Should only be called once (no retries for 4xx)
    expect(mockFetchImpl).toHaveBeenCalledTimes(1);
  });
});

// ===========================================================================
// Timeout Tests
// ===========================================================================

describe('Timeout Control', () => {
  test('should timeout after configured duration', async () => {
    // Use real timers for timeout test
    jest.useRealTimers();

    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      timeout: 100, // Very short timeout for fast testing
      maxRetries: 0,
    });

    // Mock a slow request that takes longer than timeout
    mockFetchImpl.mockImplementationOnce(
      () =>
        new Promise((_, reject) => {
          // Simulate abort after timeout
          setTimeout(() => {
            const error = new Error('Aborted');
            error.name = 'AbortError';
            reject(error);
          }, 200); // Longer than timeout
        })
    );

    try {
      await client.healthCheck();
      fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('TimeoutError');
      expect((error as ApiError).statusCode).toBe(408);
    }

    // Restore fake timers
    jest.useFakeTimers();
  });

  test('should complete before timeout', async () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      timeout: 30000,
      maxRetries: 0,
    });

    // Fast response
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({ status: 'healthy' })
    );

    const result = await client.healthCheck();

    expect(result.status).toBe('healthy');
  });
});

// ===========================================================================
// Request Headers Tests
// ===========================================================================

describe('Request Headers', () => {
  test('should include required headers', async () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });

    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({ status: 'healthy' })
    );

    await client.healthCheck();

    expect(mockFetchImpl).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json; charset=utf-8',
          'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
        }),
      })
    );
  });
});

// ===========================================================================
// 204 No Content Tests
// ===========================================================================

describe('204 No Content Handling', () => {
  test('should handle 204 response for delete operations', async () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });

    const response204 = createMockResponse(null, 204, 'No Content');
    mockFetchImpl.mockResolvedValueOnce(response204);

    // Should not throw
    await expect(
      client.deleteNode('test.canvas', 'node1')
    ).resolves.toBeUndefined();
  });
});

// ===========================================================================
// Story 12.H.4: AbortController Request Cancellation Tests
// ===========================================================================

describe('AbortController Request Cancellation (Story 12.H.4)', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
      timeout: 60000,
    });
  });

  describe('callAgentWithCancel', () => {
    test('AC1/AC2: should register AbortController for pending requests', async () => {
      const lockKey = 'test-oral-node123';

      // Mock a slow response
      mockFetchImpl.mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            setTimeout(() => {
              resolve(createMockResponse({ explanation: 'test' }));
            }, 100);
          })
      );

      // Start the request but don't await yet
      const promise = client.callAgentWithCancel<{ explanation: string }>(
        lockKey,
        '/agents/explain/oral',
        { canvas_name: 'test.canvas', node_id: 'node123' }
      );

      // AC2: Verify request is tracked while pending
      expect(client.isRequestPending(lockKey)).toBe(true);
      expect(client.getPendingRequests()).toContain(lockKey);

      // Complete the request
      jest.advanceTimersByTime(100);
      const result = await promise;

      expect(result?.explanation).toBe('test');

      // AC6: Verify cleanup after completion
      expect(client.isRequestPending(lockKey)).toBe(false);
      expect(client.getPendingRequests()).not.toContain(lockKey);
    });

    test('AC3: cancelRequest should abort pending request and return true', async () => {
      jest.useRealTimers();
      const lockKey = 'test-cancel-1';

      // Mock a long-running request that will be cancelled
      let abortCalled = false;
      mockFetchImpl.mockImplementationOnce(
        (_url: string, options: RequestInit) =>
          new Promise((resolve, reject) => {
            const signal = options?.signal as AbortSignal;
            if (signal) {
              signal.addEventListener('abort', () => {
                abortCalled = true;
                const error = new Error('Aborted');
                error.name = 'AbortError';
                reject(error);
              });
            }
            // Request would take 5 seconds normally
            setTimeout(() => resolve(createMockResponse({ data: 'done' })), 5000);
          })
      );

      // Start the request
      const promise = client.callAgentWithCancel<{ data: string }>(
        lockKey,
        '/agents/test',
        {}
      );

      // Small delay to ensure request started
      await new Promise((r) => setTimeout(r, 10));

      // AC3: Cancel the request
      const cancelled = client.cancelRequest(lockKey);

      // Verify cancel returned true
      expect(cancelled).toBe(true);

      // AC5: Result should be null (not an error throw)
      const result = await promise;
      expect(result).toBeNull();

      // Verify abort was actually called
      expect(abortCalled).toBe(true);

      // AC6: Verify cleanup
      expect(client.isRequestPending(lockKey)).toBe(false);

      jest.useFakeTimers();
    });

    test('AC3: cancelRequest should return false for non-existent request', () => {
      const result = client.cancelRequest('non-existent-key');
      expect(result).toBe(false);
    });

    test('AC5: cancelled request should return null, not throw', async () => {
      jest.useRealTimers();
      const lockKey = 'test-null-return';

      // Mock request that will be cancelled
      mockFetchImpl.mockImplementationOnce(
        (_url: string, options: RequestInit) =>
          new Promise((resolve, reject) => {
            const signal = options?.signal as AbortSignal;
            if (signal) {
              signal.addEventListener('abort', () => {
                const error = new Error('Aborted');
                error.name = 'AbortError';
                reject(error);
              });
            }
            setTimeout(() => resolve(createMockResponse({})), 10000);
          })
      );

      const promise = client.callAgentWithCancel(lockKey, '/test', {});

      await new Promise((r) => setTimeout(r, 10));
      client.cancelRequest(lockKey);

      // AC5: Should return null, not throw an error
      const result = await promise;
      expect(result).toBeNull();

      jest.useFakeTimers();
    });

    test('AC6: should cleanup AbortController after request completion', async () => {
      const lockKey = 'test-cleanup';

      mockFetchImpl.mockResolvedValueOnce(
        createMockResponse({ success: true })
      );

      await client.callAgentWithCancel(lockKey, '/test', {});

      // AC6: After completion, request should no longer be pending
      expect(client.isRequestPending(lockKey)).toBe(false);
      expect(client.getPendingRequests()).not.toContain(lockKey);
    });
  });

  describe('cancelAllRequests', () => {
    test('should cancel all pending requests', async () => {
      jest.useRealTimers();

      // Create mock that tracks abort for multiple requests
      const abortCounts: Record<string, boolean> = {};
      mockFetchImpl.mockImplementation(
        (_url: string, options: RequestInit) =>
          new Promise((resolve, reject) => {
            const lockKey = _url.includes('req-1')
              ? 'req-1'
              : _url.includes('req-2')
                ? 'req-2'
                : 'req-3';

            const signal = options?.signal as AbortSignal;
            if (signal) {
              signal.addEventListener('abort', () => {
                abortCounts[lockKey] = true;
                const error = new Error('Aborted');
                error.name = 'AbortError';
                reject(error);
              });
            }
            setTimeout(() => resolve(createMockResponse({})), 10000);
          })
      );

      // Start multiple requests
      const promise1 = client.callAgentWithCancel('req-1', '/api/req-1', {});
      const promise2 = client.callAgentWithCancel('req-2', '/api/req-2', {});
      const promise3 = client.callAgentWithCancel('req-3', '/api/req-3', {});

      await new Promise((r) => setTimeout(r, 10));

      // Verify all are pending
      expect(client.getPendingRequests().length).toBe(3);

      // Cancel all
      client.cancelAllRequests();

      // Verify all cleared
      expect(client.getPendingRequests().length).toBe(0);

      // All should return null
      const results = await Promise.all([promise1, promise2, promise3]);
      results.forEach((r) => expect(r).toBeNull());

      jest.useFakeTimers();
    });

    test('should handle cancelAllRequests when no requests pending', () => {
      // Should not throw
      expect(() => client.cancelAllRequests()).not.toThrow();
      expect(client.getPendingRequests().length).toBe(0);
    });
  });

  describe('isRequestPending and getPendingRequests', () => {
    test('should track multiple concurrent requests', async () => {
      // Mock delayed responses
      mockFetchImpl.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve(createMockResponse({})), 100);
          })
      );

      // Start multiple requests
      const p1 = client.callAgentWithCancel('key-1', '/test1', {});
      const p2 = client.callAgentWithCancel('key-2', '/test2', {});
      const p3 = client.callAgentWithCancel('key-3', '/test3', {});

      // All should be pending
      expect(client.isRequestPending('key-1')).toBe(true);
      expect(client.isRequestPending('key-2')).toBe(true);
      expect(client.isRequestPending('key-3')).toBe(true);

      const pending = client.getPendingRequests();
      expect(pending).toHaveLength(3);
      expect(pending).toContain('key-1');
      expect(pending).toContain('key-2');
      expect(pending).toContain('key-3');

      // Complete all
      jest.advanceTimersByTime(100);
      await Promise.all([p1, p2, p3]);

      // All should be cleared
      expect(client.getPendingRequests()).toHaveLength(0);
    });
  });

  describe('User Cancel vs Timeout Distinction', () => {
    test('should distinguish user cancel from timeout', async () => {
      jest.useRealTimers();

      const consoleSpy = jest.spyOn(console, 'log');
      const lockKey = 'test-user-cancel';

      mockFetchImpl.mockImplementationOnce(
        (_url: string, options: RequestInit) =>
          new Promise((resolve, reject) => {
            const signal = options?.signal as AbortSignal;
            if (signal) {
              signal.addEventListener('abort', () => {
                const error = new Error('Aborted');
                error.name = 'AbortError';
                reject(error);
              });
            }
            setTimeout(() => resolve(createMockResponse({})), 10000);
          })
      );

      const promise = client.callAgentWithCancel(lockKey, '/test', {});

      await new Promise((r) => setTimeout(r, 10));

      // User-initiated cancel
      client.cancelRequest(lockKey);
      await promise;

      // Should log as "cancelled by user"
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('cancelled by user')
      );

      consoleSpy.mockRestore();
      jest.useFakeTimers();
    });
  });
});
