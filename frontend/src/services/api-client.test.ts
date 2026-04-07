/**
 * FR-KG-04 Phase 2 Task 2.11: ApiClient X-CLS-Internal-Key header injection.
 *
 * Verifies that ApiClient threads the device-scoped internal API key through
 * every fetch path (the main private `request<T>` and the side-path `indexImage`).
 *
 * The backend dependency `require_internal_api_key` rejects requests with 403
 * when the header is missing in production, so the front-end injection is the
 * load-bearing piece for the fail-closed contract.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiClient } from './api-client';

describe('ApiClient — X-CLS-Internal-Key header injection (FR-KG-04 Phase 2)', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Mock global fetch with a permissive 200 response so we can inspect the
    // RequestInit that ApiClient passes in.
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    });
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe('constructor + buildHeaders', () => {
    it('injects X-CLS-Internal-Key when constructed with a key', async () => {
      const client = new ApiClient('http://localhost:8001', 'my-key');
      await client.get('/api/v1/health');

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [, init] = fetchMock.mock.calls[0];
      expect((init.headers as Record<string, string>)['X-CLS-Internal-Key']).toBe('my-key');
    });

    it('omits X-CLS-Internal-Key when no key is provided', async () => {
      const client = new ApiClient('http://localhost:8001');
      await client.get('/api/v1/health');

      const [, init] = fetchMock.mock.calls[0];
      expect((init.headers as Record<string, string>)['X-CLS-Internal-Key']).toBeUndefined();
    });

    it('always sets Content-Type and X-Request-ID alongside the auth header', async () => {
      const client = new ApiClient('http://localhost:8001', 'k');
      await client.get('/api/v1/health');

      const [, init] = fetchMock.mock.calls[0];
      const headers = init.headers as Record<string, string>;
      expect(headers['Content-Type']).toBe('application/json');
      expect(headers['X-Request-ID']).toMatch(/[0-9a-f-]{36}/);
      expect(headers['X-CLS-Internal-Key']).toBe('k');
    });
  });

  describe('setInternalApiKey', () => {
    it('updates the key for subsequent requests', async () => {
      const client = new ApiClient('http://localhost:8001');
      // Initial request: no header
      await client.get('/api/v1/health');
      let init = fetchMock.mock.calls[0][1];
      expect((init.headers as Record<string, string>)['X-CLS-Internal-Key']).toBeUndefined();

      // After provisioning the key, the next request must carry it
      client.setInternalApiKey('rotated-key');
      await client.get('/api/v1/health');
      init = fetchMock.mock.calls[1][1];
      expect((init.headers as Record<string, string>)['X-CLS-Internal-Key']).toBe('rotated-key');
    });

    it('clearing the key (empty string) removes the header on next request', async () => {
      const client = new ApiClient('http://localhost:8001', 'first');
      await client.get('/api/v1/health');
      expect(
        (fetchMock.mock.calls[0][1].headers as Record<string, string>)['X-CLS-Internal-Key'],
      ).toBe('first');

      client.setInternalApiKey('');
      await client.get('/api/v1/health');
      expect(
        (fetchMock.mock.calls[1][1].headers as Record<string, string>)['X-CLS-Internal-Key'],
      ).toBeUndefined();
    });
  });

  describe('all HTTP verbs honor the auth header', () => {
    it('GET sends the header', async () => {
      const client = new ApiClient('http://localhost:8001', 'tk');
      await client.get('/api/v1/health');
      expect(
        (fetchMock.mock.calls[0][1].headers as Record<string, string>)['X-CLS-Internal-Key'],
      ).toBe('tk');
    });

    it('POST sends the header', async () => {
      const client = new ApiClient('http://localhost:8001', 'tk');
      await client.post('/api/v1/sync/batch', { canvasId: 'c1', operations: [] });
      expect(
        (fetchMock.mock.calls[0][1].headers as Record<string, string>)['X-CLS-Internal-Key'],
      ).toBe('tk');
    });

    it('PATCH sends the header', async () => {
      const client = new ApiClient('http://localhost:8001', 'tk');
      await client.patch('/api/v1/canvas/abc', { name: 'updated' });
      expect(
        (fetchMock.mock.calls[0][1].headers as Record<string, string>)['X-CLS-Internal-Key'],
      ).toBe('tk');
    });
  });

  describe('side-path indexImage', () => {
    it('also injects X-CLS-Internal-Key', async () => {
      const client = new ApiClient('http://localhost:8001', 'tk');
      await client.indexImage('node-1', 'data:image/png;base64,iVBOR');

      const [, init] = fetchMock.mock.calls[0];
      expect((init.headers as Record<string, string>)['X-CLS-Internal-Key']).toBe('tk');
      expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json');
    });
  });
});
