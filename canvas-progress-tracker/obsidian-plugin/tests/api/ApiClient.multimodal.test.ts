/**
 * Canvas Learning System - API Client Multimodal Tests
 *
 * Unit tests for the multimodal API methods:
 * - uploadMultimodal: FormData-based file upload
 * - getMediaByConceptId: Query media by concept with caching
 * - searchMultimodal: Vector similarity search
 * - deleteMultimodal: Delete with cache invalidation
 *
 * @source Story 35.3 - Obsidian Plugin ApiClient Multimodal Integration
 * @verified 2026-01-20
 */

import { ApiClient } from '../../src/api/ApiClient';
import {
  ApiError,
  MediaItem,
  MultimodalUploadResponse,
  MultimodalSearchResponse,
  MultimodalSearchResult,
  MultimodalDeleteResponse,
} from '../../src/api/types';

// ===========================================================================
// Mock Setup
// ===========================================================================

// Store original fetch
const originalFetch = global.fetch;

// Mock fetch implementation
let mockFetchImpl: jest.Mock;

// Mock File for upload tests
class MockFile {
  name: string;
  size: number;
  type: string;

  constructor(
    parts: BlobPart[],
    filename: string,
    options?: FilePropertyBag
  ) {
    this.name = filename;
    this.size = parts.reduce((acc, part) => {
      if (typeof part === 'string') return acc + part.length;
      return acc + (part as Blob).size;
    }, 0);
    this.type = options?.type ?? '';
  }
}

// @ts-expect-error - Mock File for Node.js environment
global.File = MockFile;

beforeEach(() => {
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
// uploadMultimodal Tests (AC 35.3.1, AC 35.3.5)
// ===========================================================================

describe('uploadMultimodal (Story 35.3 AC1, AC5)', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });
  });

  test('should upload file with FormData', async () => {
    const mockResponse: MultimodalUploadResponse = {
      id: 'uuid-123-456',
      media_type: 'image',
      path: '/uploads/test-image.png',
      created_at: '2026-01-20T10:00:00Z',
      related_concept_id: 'concept-node-1',
      thumbnail: '/thumbnails/test-image.png',
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse, 201));

    const file = new File(['test content'], 'test-image.png', {
      type: 'image/png',
    });
    const result = await client.uploadMultimodal(file as unknown as File, 'concept-node-1');

    expect(result.id).toBe('uuid-123-456');
    expect(result.media_type).toBe('image');
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/multimodal/upload',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      })
    );
  });

  test('should validate conceptId is non-empty', async () => {
    const file = new File(['test'], 'test.png', { type: 'image/png' });

    await expect(
      client.uploadMultimodal(file as unknown as File, '')
    ).rejects.toThrow(ApiError);

    await expect(
      client.uploadMultimodal(file as unknown as File, '   ')
    ).rejects.toThrow(ApiError);

    try {
      await client.uploadMultimodal(file as unknown as File, '');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('ValidationError');
      expect((error as ApiError).details).toEqual({ field: 'conceptId' });
    }
  });

  test('should call progress callback at start and end', async () => {
    const mockResponse: MultimodalUploadResponse = {
      id: 'uuid-789',
      media_type: 'pdf',
      path: '/uploads/doc.pdf',
      created_at: '2026-01-20T10:00:00Z',
      related_concept_id: 'concept-2',
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const progressCallback = jest.fn();
    const file = new File(['pdf content'], 'doc.pdf', { type: 'application/pdf' });

    await client.uploadMultimodal(file as unknown as File, 'concept-2', progressCallback);

    expect(progressCallback).toHaveBeenCalledWith(0);
    expect(progressCallback).toHaveBeenCalledWith(100);
  });

  test('should retry on transient failures (AC5)', async () => {
    jest.useRealTimers();

    const clientWithRetry = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 2,
      retryBackoffMs: 10,
    });

    // First call fails with 503, second succeeds
    mockFetchImpl
      .mockResolvedValueOnce(
        createMockResponse({ message: 'Service Unavailable' }, 503)
      )
      .mockResolvedValueOnce(
        createMockResponse({
          id: 'uuid-retry',
          media_type: 'image',
          path: '/test.png',
          created_at: '2026-01-20T10:00:00Z',
          related_concept_id: 'concept-retry',
        })
      );

    const file = new File(['test'], 'test.png', { type: 'image/png' });
    const result = await clientWithRetry.uploadMultimodal(file as unknown as File, 'concept-retry');

    expect(result.id).toBe('uuid-retry');
    expect(mockFetchImpl).toHaveBeenCalledTimes(2);

    jest.useFakeTimers();
  });

  test('should NOT retry on 4xx errors', async () => {
    const clientWithRetry = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 3,
    });

    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({ message: 'Bad Request' }, 400)
    );

    const file = new File(['test'], 'test.png', { type: 'image/png' });

    await expect(
      clientWithRetry.uploadMultimodal(file as unknown as File, 'concept-1')
    ).rejects.toThrow(ApiError);

    // Should only be called once (no retries for 4xx)
    expect(mockFetchImpl).toHaveBeenCalledTimes(1);
  });

  test('should include User-Agent header but not Content-Type for FormData', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({
        id: 'uuid-header',
        media_type: 'image',
        path: '/test.png',
        created_at: '2026-01-20T10:00:00Z',
        related_concept_id: 'concept-header',
      })
    );

    const file = new File(['test'], 'test.png', { type: 'image/png' });
    await client.uploadMultimodal(file as unknown as File, 'concept-header');

    expect(mockFetchImpl).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'User-Agent': 'Obsidian-Canvas-Review/1.0.0',
        }),
      })
    );

    // Content-Type should NOT be set manually for FormData
    const callArgs = mockFetchImpl.mock.calls[0][1];
    expect(callArgs.headers['Content-Type']).toBeUndefined();
  });
});

// ===========================================================================
// getMediaByConceptId Tests (AC 35.3.2, AC 35.3.5)
// ===========================================================================

describe('getMediaByConceptId (Story 35.3 AC2, AC5)', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });
  });

  test('should fetch media items by concept ID', async () => {
    const mockResults: MultimodalSearchResult[] = [
      {
        id: 'media-1',
        media_type: 'image',
        file_path: '/images/concept1.png',
        score: 1.0,
        related_concept_id: 'concept-node-1',
        thumbnail: '/thumbnails/concept1.png',
      },
      {
        id: 'media-2',
        media_type: 'pdf',
        file_path: '/docs/concept1.pdf',
        score: 1.0,
        related_concept_id: 'concept-node-1',
      },
    ];
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResults));

    const result = await client.getMediaByConceptId('concept-node-1');

    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('media-1');
    expect(result[0].type).toBe('image'); // Transformed from media_type
    expect(result[0].path).toBe('/images/concept1.png'); // Transformed from file_path
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/multimodal/by-concept/concept-node-1',
      expect.objectContaining({ method: 'GET' })
    );
  });

  test('should validate conceptId is non-empty', async () => {
    await expect(client.getMediaByConceptId('')).rejects.toThrow(ApiError);
    await expect(client.getMediaByConceptId('   ')).rejects.toThrow(ApiError);

    try {
      await client.getMediaByConceptId('');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('ValidationError');
      expect((error as ApiError).details).toEqual({ field: 'conceptId' });
    }
  });

  test('should URL-encode conceptId', async () => {
    mockFetchImpl.mockResolvedValueOnce(createMockResponse([]));

    await client.getMediaByConceptId('concept with spaces');

    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/multimodal/by-concept/concept%20with%20spaces',
      expect.any(Object)
    );
  });

  test('should cache results for 5 minutes (ADR-007)', async () => {
    const mockResults: MultimodalSearchResult[] = [
      {
        id: 'cached-media',
        media_type: 'image',
        file_path: '/cached.png',
        score: 1.0,
        related_concept_id: 'concept-cache',
      },
    ];
    mockFetchImpl.mockResolvedValue(createMockResponse(mockResults));

    // First call - should fetch from API
    const result1 = await client.getMediaByConceptId('concept-cache');
    expect(result1[0].id).toBe('cached-media');
    expect(mockFetchImpl).toHaveBeenCalledTimes(1);

    // Second call - should use cache
    const result2 = await client.getMediaByConceptId('concept-cache');
    expect(result2[0].id).toBe('cached-media');
    expect(mockFetchImpl).toHaveBeenCalledTimes(1); // Still 1, cache hit

    // Advance time by 4 minutes - still within TTL
    jest.advanceTimersByTime(4 * 60 * 1000);

    const result3 = await client.getMediaByConceptId('concept-cache');
    expect(mockFetchImpl).toHaveBeenCalledTimes(1); // Still cached

    // Advance time by 2 more minutes (total 6 minutes) - cache expired
    jest.advanceTimersByTime(2 * 60 * 1000);

    const result4 = await client.getMediaByConceptId('concept-cache');
    expect(mockFetchImpl).toHaveBeenCalledTimes(2); // Cache miss, new fetch
  });

  test('should transform backend response to MediaItem format', async () => {
    const mockResults: MultimodalSearchResult[] = [
      {
        id: 'transform-test',
        media_type: 'audio',
        file_path: '/audio/lecture.mp3',
        score: 0.95,
        related_concept_id: 'concept-transform',
        description: 'Lecture recording',
        extracted_text: null,
        metadata: { duration: 3600 },
      },
    ];
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResults));

    const result = await client.getMediaByConceptId('concept-transform');

    const item = result[0];
    expect(item.id).toBe('transform-test');
    expect(item.type).toBe('audio'); // Transformed from media_type
    expect(item.path).toBe('/audio/lecture.mp3'); // Transformed from file_path
    expect(item.relevanceScore).toBe(0.95); // From score, default 1.0 for concept queries
    expect(item.conceptId).toBe('concept-transform'); // From related_concept_id
    expect(item.description).toBe('Lecture recording');
    expect(item.metadata).toEqual({ duration: 3600 });
  });

  test('should return empty array for concept with no media', async () => {
    mockFetchImpl.mockResolvedValueOnce(createMockResponse([]));

    const result = await client.getMediaByConceptId('concept-empty');

    expect(result).toEqual([]);
    expect(result).toHaveLength(0);
  });
});

// ===========================================================================
// searchMultimodal Tests (AC 35.3.3, AC 35.3.5)
// ===========================================================================

describe('searchMultimodal (Story 35.3 AC3, AC5)', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });
  });

  test('should search multimodal content with query', async () => {
    const mockResponse: MultimodalSearchResponse = {
      results: [
        {
          id: 'search-1',
          media_type: 'image',
          file_path: '/images/result1.png',
          score: 0.95,
          related_concept_id: 'concept-1',
          description: 'Matching image',
        },
        {
          id: 'search-2',
          media_type: 'pdf',
          file_path: '/docs/result2.pdf',
          score: 0.87,
          related_concept_id: 'concept-2',
        },
      ],
      total_count: 2,
      query: '数学公式',
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const result = await client.searchMultimodal('数学公式');

    expect(result).toHaveLength(2);
    expect(result[0].relevanceScore).toBe(0.95);
    expect(result[1].relevanceScore).toBe(0.87);
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/multimodal/search',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          query: '数学公式',
          limit: 20,
          media_types: undefined,
        }),
      })
    );
  });

  test('should validate query is non-empty', async () => {
    await expect(client.searchMultimodal('')).rejects.toThrow(ApiError);
    await expect(client.searchMultimodal('   ')).rejects.toThrow(ApiError);

    try {
      await client.searchMultimodal('');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('ValidationError');
      expect((error as ApiError).details).toEqual({ field: 'query' });
    }
  });

  test('should pass optional limit and media_types', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({
        results: [],
        total_count: 0,
        query: 'test',
      })
    );

    await client.searchMultimodal('test', {
      limit: 10,
      media_types: ['image', 'pdf'],
    });

    expect(mockFetchImpl).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({
          query: 'test',
          limit: 10,
          media_types: ['image', 'pdf'],
        }),
      })
    );
  });

  test('should use default limit of 20', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({
        results: [],
        total_count: 0,
        query: 'test',
      })
    );

    await client.searchMultimodal('test');

    expect(mockFetchImpl).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: expect.stringContaining('"limit":20'),
      })
    );
  });

  test('should transform search results to MediaItem format', async () => {
    const mockResponse: MultimodalSearchResponse = {
      results: [
        {
          id: 'transform-search',
          media_type: 'video',
          file_path: '/videos/lecture.mp4',
          score: 0.92,
          related_concept_id: 'concept-video',
          thumbnail: '/thumbnails/lecture.jpg',
          description: 'Video lecture',
          extracted_text: 'Transcript...',
          metadata: { duration: 1800 },
        },
      ],
      total_count: 1,
      query: 'lecture',
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const result = await client.searchMultimodal('lecture');

    expect(result[0]).toEqual<MediaItem>({
      id: 'transform-search',
      type: 'video',
      path: '/videos/lecture.mp4',
      relevanceScore: 0.92,
      conceptId: 'concept-video',
      thumbnail: '/thumbnails/lecture.jpg',
      description: 'Video lecture',
      extractedText: 'Transcript...',
      metadata: { duration: 1800 },
    });
  });

  test('should return empty array for no matches', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({
        results: [],
        total_count: 0,
        query: 'nonexistent',
      })
    );

    const result = await client.searchMultimodal('nonexistent');

    expect(result).toEqual([]);
  });
});

// ===========================================================================
// deleteMultimodal Tests (AC 35.3.4, AC 35.3.5)
// ===========================================================================

describe('deleteMultimodal (Story 35.3 AC4, AC5)', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });
  });

  test('should delete content by ID', async () => {
    const mockResponse: MultimodalDeleteResponse = {
      success: true,
      deleted_id: 'delete-me-123',
      message: 'Content deleted successfully',
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const result = await client.deleteMultimodal('delete-me-123');

    expect(result).toBe(true);
    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/multimodal/delete-me-123',
      expect.objectContaining({ method: 'DELETE' })
    );
  });

  test('should validate contentId is non-empty', async () => {
    await expect(client.deleteMultimodal('')).rejects.toThrow(ApiError);
    await expect(client.deleteMultimodal('   ')).rejects.toThrow(ApiError);

    try {
      await client.deleteMultimodal('');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('ValidationError');
      expect((error as ApiError).details).toEqual({ field: 'contentId' });
    }
  });

  test('should URL-encode contentId', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        deleted_id: 'id with/special',
        message: 'Deleted',
      })
    );

    await client.deleteMultimodal('id with/special');

    expect(mockFetchImpl).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/multimodal/id%20with%2Fspecial',
      expect.any(Object)
    );
  });

  test('should return false when deletion fails', async () => {
    const mockResponse: MultimodalDeleteResponse = {
      success: false,
      deleted_id: 'nonexistent',
      message: 'Content not found',
    };
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockResponse));

    const result = await client.deleteMultimodal('nonexistent');

    expect(result).toBe(false);
  });

  test('should invalidate all multimodal caches on successful deletion (ADR-007)', async () => {
    // First, populate the cache
    const mockMediaResults: MultimodalSearchResult[] = [
      {
        id: 'to-delete',
        media_type: 'image',
        file_path: '/test.png',
        score: 1.0,
        related_concept_id: 'concept-1',
      },
    ];
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockMediaResults));

    await client.getMediaByConceptId('concept-1');
    expect(mockFetchImpl).toHaveBeenCalledTimes(1);

    // Verify cache is populated (second call should not fetch)
    await client.getMediaByConceptId('concept-1');
    expect(mockFetchImpl).toHaveBeenCalledTimes(1); // Still 1

    // Now delete - should invalidate cache
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        deleted_id: 'to-delete',
        message: 'Deleted',
      })
    );

    const deleteResult = await client.deleteMultimodal('to-delete');
    expect(deleteResult).toBe(true);
    expect(mockFetchImpl).toHaveBeenCalledTimes(2);

    // Now fetch again - should make new API call (cache was invalidated)
    mockFetchImpl.mockResolvedValueOnce(createMockResponse([]));
    await client.getMediaByConceptId('concept-1');
    expect(mockFetchImpl).toHaveBeenCalledTimes(3); // New fetch after invalidation
  });

  test('should NOT invalidate cache when deletion fails', async () => {
    // Populate cache
    const mockMediaResults: MultimodalSearchResult[] = [
      {
        id: 'keep-me',
        media_type: 'image',
        file_path: '/keep.png',
        score: 1.0,
        related_concept_id: 'concept-keep',
      },
    ];
    mockFetchImpl.mockResolvedValueOnce(createMockResponse(mockMediaResults));

    await client.getMediaByConceptId('concept-keep');
    expect(mockFetchImpl).toHaveBeenCalledTimes(1);

    // Delete fails
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({
        success: false,
        deleted_id: 'nonexistent',
        message: 'Not found',
      })
    );

    const deleteResult = await client.deleteMultimodal('nonexistent');
    expect(deleteResult).toBe(false);

    // Cache should still be valid
    await client.getMediaByConceptId('concept-keep');
    expect(mockFetchImpl).toHaveBeenCalledTimes(2); // Only delete call added
  });
});

// ===========================================================================
// invalidateMultimodalCacheForConcept Tests
// ===========================================================================

describe('invalidateMultimodalCacheForConcept', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });
  });

  test('should invalidate cache for specific concept', async () => {
    // Populate caches for two concepts
    mockFetchImpl
      .mockResolvedValueOnce(
        createMockResponse([
          { id: 'm1', media_type: 'image', file_path: '/1.png', score: 1, related_concept_id: 'c1' },
        ])
      )
      .mockResolvedValueOnce(
        createMockResponse([
          { id: 'm2', media_type: 'pdf', file_path: '/2.pdf', score: 1, related_concept_id: 'c2' },
        ])
      );

    await client.getMediaByConceptId('c1');
    await client.getMediaByConceptId('c2');
    expect(mockFetchImpl).toHaveBeenCalledTimes(2);

    // Invalidate only c1
    client.invalidateMultimodalCacheForConcept('c1');

    // c1 should refetch
    mockFetchImpl.mockResolvedValueOnce(createMockResponse([]));
    await client.getMediaByConceptId('c1');
    expect(mockFetchImpl).toHaveBeenCalledTimes(3);

    // c2 should still be cached
    await client.getMediaByConceptId('c2');
    expect(mockFetchImpl).toHaveBeenCalledTimes(3); // No new fetch
  });

  test('should handle invalidating non-cached concept gracefully', () => {
    // Should not throw
    expect(() => {
      client.invalidateMultimodalCacheForConcept('nonexistent-concept');
    }).not.toThrow();
  });
});

// ===========================================================================
// Error Handling Tests (AC 35.3.5)
// ===========================================================================

describe('Multimodal Error Handling (Story 35.3 AC5)', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      maxRetries: 0,
    });
  });

  test('uploadMultimodal should throw HttpError4xx on 400', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse(
        { message: 'Invalid file type' },
        400,
        'Bad Request'
      )
    );

    const file = new File(['test'], 'test.exe', { type: 'application/x-msdownload' });

    try {
      await client.uploadMultimodal(file as unknown as File, 'concept-1');
      fail('Expected ApiError');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('HttpError4xx');
      expect((error as ApiError).statusCode).toBe(400);
    }
  });

  test('getMediaByConceptId should throw HttpError4xx on 404', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({ message: 'Concept not found' }, 404)
    );

    try {
      await client.getMediaByConceptId('nonexistent');
      fail('Expected ApiError');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('HttpError4xx');
      expect((error as ApiError).statusCode).toBe(404);
    }
  });

  test('searchMultimodal should throw HttpError5xx on 500', async () => {
    mockFetchImpl.mockResolvedValueOnce(
      createMockResponse({ message: 'Internal error' }, 500)
    );

    try {
      await client.searchMultimodal('test query');
      fail('Expected ApiError');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('HttpError5xx');
      expect((error as ApiError).statusCode).toBe(500);
    }
  });

  test('deleteMultimodal should throw NetworkError on fetch failure', async () => {
    mockFetchImpl.mockRejectedValueOnce(new TypeError('Network error'));

    try {
      await client.deleteMultimodal('content-1');
      fail('Expected ApiError');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).type).toBe('NetworkError');
    }
  });
});
