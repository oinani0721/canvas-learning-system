/**
 * Canvas Learning System - MSW Server for Node.js Tests
 *
 * 在 Jest/Vitest 测试环境中使用的 MSW 服务器。
 *
 * 使用方法:
 *   在测试文件中:
 *   import { server } from '../mocks/server';
 *
 *   beforeAll(() => server.listen());
 *   afterEach(() => server.resetHandlers());
 *   afterAll(() => server.close());
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// 创建 MSW 服务器
export const server = setupServer(...handlers);

// 导出便捷方法
export { handlers };
