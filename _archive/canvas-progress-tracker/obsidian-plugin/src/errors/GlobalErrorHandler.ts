/**
 * Global Error Handler - Canvas Review System
 *
 * Singleton class that captures all unhandled errors and provides
 * centralized error handling for the Obsidian plugin.
 *
 * @module errors/GlobalErrorHandler
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Plugin API)
 * ✅ Verified from Story 13.7 Dev Notes (GlobalErrorHandler design)
 */

import type { Plugin, App } from 'obsidian';
import {
    PluginError,
    isPluginError,
    toPluginError,
    ErrorSeverity
} from './PluginError';
import { ErrorNotifier } from './ErrorNotifier';
import { ErrorLogger, ErrorLogEntry } from './ErrorLogger';

/**
 * Error handler configuration options
 */
export interface ErrorHandlerConfig {
    /** Whether to capture unhandled promise rejections */
    captureUnhandledRejections: boolean;
    /** Whether to capture window errors */
    captureWindowErrors: boolean;
    /** Minimum time between duplicate error reports (ms) */
    dedupeWindowMs: number;
    /** Maximum number of errors to track for deduplication */
    maxDedupeEntries: number;
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: ErrorHandlerConfig = {
    captureUnhandledRejections: true,
    captureWindowErrors: true,
    dedupeWindowMs: 60000, // 1 minute
    maxDedupeEntries: 100
};

/**
 * Error fingerprint for deduplication
 */
interface ErrorFingerprint {
    hash: string;
    lastSeen: number;
    count: number;
}

/**
 * Global Error Handler Singleton
 *
 * Captures and processes all errors in the plugin, providing:
 * - Unhandled exception catching
 * - Error deduplication
 * - User notification
 * - Error logging
 *
 * ✅ Verified from Story 13.7 Dev Notes (GlobalErrorHandler class)
 */
export class GlobalErrorHandler {
    private static instance: GlobalErrorHandler | null = null;

    private app: App;
    private plugin: Plugin;
    private config: ErrorHandlerConfig;
    private notifier: ErrorNotifier;
    private logger: ErrorLogger;

    private errorFingerprints: Map<string, ErrorFingerprint> = new Map();
    private unhandledRejectionHandler: ((event: PromiseRejectionEvent) => void) | null = null;
    private windowErrorHandler: ((event: ErrorEvent) => void) | null = null;

    // User action context for error reports
    private currentUserAction: string = '';
    private pluginVersion: string = '1.0.0';
    private obsidianVersion: string = '';

    /**
     * Private constructor - use getInstance() instead
     */
    private constructor(
        app: App,
        plugin: Plugin,
        config: Partial<ErrorHandlerConfig> = {}
    ) {
        this.app = app;
        this.plugin = plugin;
        this.config = { ...DEFAULT_CONFIG, ...config };
        this.notifier = new ErrorNotifier();
        this.logger = new ErrorLogger(plugin);

        // Get versions for error reports
        // ✅ Verified from @obsidian-canvas Skill (App interface)
        this.obsidianVersion = (this.app as unknown as { version?: string }).version || 'unknown';
        this.pluginVersion = plugin.manifest.version;
    }

    /**
     * Gets the singleton instance of GlobalErrorHandler
     *
     * @param app - Obsidian App instance
     * @param plugin - Plugin instance
     * @param config - Optional configuration
     * @returns GlobalErrorHandler singleton
     */
    public static getInstance(
        app?: App,
        plugin?: Plugin,
        config?: Partial<ErrorHandlerConfig>
    ): GlobalErrorHandler {
        if (!GlobalErrorHandler.instance) {
            if (!app || !plugin) {
                throw new Error(
                    'GlobalErrorHandler must be initialized with app and plugin on first call'
                );
            }
            GlobalErrorHandler.instance = new GlobalErrorHandler(app, plugin, config);
        }
        return GlobalErrorHandler.instance;
    }

    /**
     * Resets the singleton instance (for testing)
     */
    public static resetInstance(): void {
        if (GlobalErrorHandler.instance) {
            GlobalErrorHandler.instance.cleanup();
            GlobalErrorHandler.instance = null;
        }
    }

    /**
     * Initializes global error handlers
     */
    public initialize(): void {
        this.setupUnhandledRejectionHandler();
        this.setupWindowErrorHandler();
        this.logger.initialize();

        console.log('Canvas复习系统: 全局错误处理器已初始化');
    }

    /**
     * Cleans up global error handlers
     */
    public cleanup(): void {
        if (this.unhandledRejectionHandler) {
            window.removeEventListener(
                'unhandledrejection',
                this.unhandledRejectionHandler
            );
            this.unhandledRejectionHandler = null;
        }

        if (this.windowErrorHandler) {
            window.removeEventListener('error', this.windowErrorHandler);
            this.windowErrorHandler = null;
        }

        this.errorFingerprints.clear();
        this.logger.cleanup();

        console.log('Canvas复习系统: 全局错误处理器已清理');
    }

    /**
     * Sets the current user action context
     *
     * @param action - Description of what the user is doing
     */
    public setUserAction(action: string): void {
        this.currentUserAction = action;
    }

    /**
     * Clears the current user action context
     */
    public clearUserAction(): void {
        this.currentUserAction = '';
    }

    /**
     * Handles an error with full processing pipeline
     *
     * @param error - The error to handle
     * @param context - Additional context about the error
     * @param silent - If true, don't show user notification
     */
    public async handleError(
        error: unknown,
        context?: Record<string, unknown>,
        silent: boolean = false
    ): Promise<void> {
        const pluginError = toPluginError(error);

        // Add context if provided
        if (context) {
            pluginError.context = { ...pluginError.context, ...context };
        }

        // Check for duplicate errors
        if (this.isDuplicateError(pluginError)) {
            console.debug('Canvas复习系统: 重复错误已忽略', pluginError.message);
            return;
        }

        // Log the error
        const logEntry = this.createLogEntry(pluginError);
        await this.logger.log(logEntry);

        // Show user notification unless silent
        if (!silent) {
            this.notifier.showError(pluginError);
        }

        // Console output for debugging
        this.logToConsole(pluginError);
    }

    /**
     * Handles a fatal error that requires plugin restart
     *
     * @param error - The fatal error
     */
    public async handleFatalError(error: unknown): Promise<void> {
        const pluginError = toPluginError(error);
        pluginError.context = {
            ...pluginError.context,
            fatal: true
        };

        // Log as critical
        const logEntry = this.createLogEntry(pluginError);
        logEntry.severity = 'critical';
        await this.logger.log(logEntry);

        // Show persistent error notification
        this.notifier.showFatalError(pluginError);

        // Console error
        console.error('Canvas复习系统: 致命错误', pluginError);
    }

    /**
     * Handles errors from command callbacks
     *
     * @param error - The error from command execution
     * @param commandId - The ID of the command that failed
     */
    public async handleCommandError(
        error: unknown,
        commandId: string
    ): Promise<void> {
        await this.handleError(error, {
            commandId,
            type: 'command_error'
        });
    }

    /**
     * Gets the error logger instance
     */
    public getLogger(): ErrorLogger {
        return this.logger;
    }

    /**
     * Gets the error notifier instance
     */
    public getNotifier(): ErrorNotifier {
        return this.notifier;
    }

    // ========== Private Methods ==========

    /**
     * Sets up unhandled promise rejection handler
     */
    private setupUnhandledRejectionHandler(): void {
        if (!this.config.captureUnhandledRejections) return;

        this.unhandledRejectionHandler = (event: PromiseRejectionEvent) => {
            // Only handle plugin-related errors
            const stack = event.reason?.stack || '';
            if (!this.isPluginRelatedError(stack)) {
                return; // Not our error, let it propagate
            }

            event.preventDefault();
            this.handleError(event.reason, {
                type: 'unhandled_rejection',
                promise: 'unhandled'
            });
        };

        window.addEventListener('unhandledrejection', this.unhandledRejectionHandler);
    }

    /**
     * Sets up window error handler
     */
    private setupWindowErrorHandler(): void {
        if (!this.config.captureWindowErrors) return;

        this.windowErrorHandler = (event: ErrorEvent) => {
            // Only handle plugin-related errors
            if (!this.isPluginRelatedError(event.filename || '')) {
                return; // Not our error
            }

            event.preventDefault();
            this.handleError(event.error || event.message, {
                type: 'window_error',
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        };

        window.addEventListener('error', this.windowErrorHandler);
    }

    /**
     * Checks if an error is related to this plugin
     */
    private isPluginRelatedError(stackOrFilename: string): boolean {
        const pluginPatterns = [
            'canvas-review',
            'canvas_review',
            'CanvasReview',
            this.plugin.manifest.id
        ];

        return pluginPatterns.some(pattern =>
            stackOrFilename.toLowerCase().includes(pattern.toLowerCase())
        );
    }

    /**
     * Checks if this error is a duplicate (within dedupe window)
     */
    private isDuplicateError(error: PluginError): boolean {
        const hash = this.hashError(error);
        const now = Date.now();

        const existing = this.errorFingerprints.get(hash);
        if (existing && (now - existing.lastSeen) < this.config.dedupeWindowMs) {
            existing.count++;
            existing.lastSeen = now;
            return true;
        }

        // Clean up old fingerprints if too many
        if (this.errorFingerprints.size >= this.config.maxDedupeEntries) {
            this.cleanupFingerprints();
        }

        // Record new fingerprint
        this.errorFingerprints.set(hash, {
            hash,
            lastSeen: now,
            count: 1
        });

        return false;
    }

    /**
     * Creates a hash for error deduplication
     */
    private hashError(error: PluginError): string {
        const parts = [
            error.name,
            error.message,
            error.severity
        ];
        return parts.join('|');
    }

    /**
     * Removes old error fingerprints
     */
    private cleanupFingerprints(): void {
        const now = Date.now();
        const cutoff = now - this.config.dedupeWindowMs;

        for (const [hash, fingerprint] of this.errorFingerprints) {
            if (fingerprint.lastSeen < cutoff) {
                this.errorFingerprints.delete(hash);
            }
        }
    }

    /**
     * Creates a log entry from an error
     */
    private createLogEntry(error: PluginError): ErrorLogEntry {
        return {
            timestamp: new Date().toISOString(),
            errorType: error.name,
            severity: error.severity,
            message: error.message,
            stack: error.stack,
            context: error.context,
            userAction: this.currentUserAction || undefined,
            pluginVersion: this.pluginVersion,
            obsidianVersion: this.obsidianVersion
        };
    }

    /**
     * Logs error to console with appropriate level
     */
    private logToConsole(error: PluginError): void {
        const prefix = 'Canvas复习系统:';

        switch (error.severity) {
            case 'critical':
                console.error(prefix, error.message, error);
                break;
            case 'warning':
                console.warn(prefix, error.message, error);
                break;
            case 'info':
            default:
                console.info(prefix, error.message, error);
                break;
        }
    }
}

/**
 * Decorator for wrapping async methods with error handling
 *
 * @example
 * class MyClass {
 *   \@withErrorHandling('MyClass.myMethod')
 *   async myMethod() { ... }
 * }
 */
export function withErrorHandling(operationName: string) {
    return function (
        _target: unknown,
        _propertyKey: string,
        descriptor: PropertyDescriptor
    ) {
        const originalMethod = descriptor.value;

        descriptor.value = async function (...args: unknown[]) {
            const handler = GlobalErrorHandler.getInstance();
            handler.setUserAction(operationName);

            try {
                return await originalMethod.apply(this, args);
            } catch (error) {
                await handler.handleError(error, { operation: operationName });
                throw error; // Re-throw to allow caller to handle
            } finally {
                handler.clearUserAction();
            }
        };

        return descriptor;
    };
}
