/**
 * Lightweight logger — zero-dependency console.* wrapper.
 * Provides module-scoped [ModuleName] prefix and level control.
 *
 * Usage:
 *   const logger = createLogger('ApiClient');
 *   logger.debug('request sent', { method, path, requestId });
 *   logger.warn('fetch failed', err);
 *
 * Levels (ascending): debug < info < warn < error
 * Default: 'debug' in dev, 'warn' in prod.
 * Override: VITE_LOG_LEVEL=debug|info|warn|error
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

function resolveLevel(): LogLevel {
  const override = import.meta.env.VITE_LOG_LEVEL as string | undefined;
  if (override && override in LEVELS) return override as LogLevel;
  return import.meta.env.DEV ? 'debug' : 'warn';
}

const ACTIVE_NUM = LEVELS[resolveLevel()];

export interface Logger {
  debug(message: string, ...args: unknown[]): void;
  info(message: string, ...args: unknown[]): void;
  warn(message: string, ...args: unknown[]): void;
  error(message: string, ...args: unknown[]): void;
}

export function createLogger(module: string): Logger {
  const prefix = `[${module}]`;
  return {
    debug(message, ...args) {
      if (ACTIVE_NUM <= LEVELS.debug) console.debug(prefix, message, ...args);
    },
    info(message, ...args) {
      if (ACTIVE_NUM <= LEVELS.info) console.info(prefix, message, ...args);
    },
    warn(message, ...args) {
      if (ACTIVE_NUM <= LEVELS.warn) console.warn(prefix, message, ...args);
    },
    error(message, ...args) {
      if (ACTIVE_NUM <= LEVELS.error) console.error(prefix, message, ...args);
    },
  };
}
