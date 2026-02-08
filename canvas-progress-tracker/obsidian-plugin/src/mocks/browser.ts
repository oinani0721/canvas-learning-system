/**
 * Canvas Learning System - MSW Browser Worker
 *
 * 在浏览器环境中使用的 MSW Worker。
 * 用于开发时的 API Mock。
 *
 * 使用方法:
 *   在 main.ts 或入口文件中:
 *
 *   if (process.env.NODE_ENV === 'development') {
 *     const { worker } = await import('./mocks/browser');
 *     await worker.start();
 *   }
 *
 * 注意:
 *   需要在 public 目录放置 mockServiceWorker.js
 *   运行: npx msw init public/
 */

import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

// 创建 MSW Worker
export const worker = setupWorker(...handlers);

// 导出便捷方法
export { handlers };
