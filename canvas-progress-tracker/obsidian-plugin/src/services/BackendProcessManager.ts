/**
 * Canvas Learning System - Backend Process Manager
 *
 * Manages the FastAPI backend server process from within Obsidian.
 * Allows one-click start/stop of the backend service.
 *
 * @module BackendProcessManager
 * @version 2.1.0
 *
 * Fixes in v2.1.0:
 * - Added shell: true to fix Windows ENOENT error with Chinese character paths
 * - Use path.resolve() to normalize cwd (fixes paths with ../)
 * - Validate backend directory exists before spawning
 *
 * Fixes in v2.0.0:
 * - Added Python path auto-detection for virtual environments
 * - Increased startup timeout to 15 seconds with polling
 * - Fixed Windows process termination logic
 * - Simplified toggle debouncing
 */

import { Notice, requestUrl, RequestUrlResponse } from 'obsidian';
import { spawn, ChildProcess, exec } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export interface BackendProcessConfig {
    /** Path to the backend directory */
    backendPath: string;
    /** Port to run the server on */
    port: number;
    /** Host to bind to */
    host: string;
    /** Python executable path (optional, auto-detected if not provided) */
    pythonPath?: string;
    /** Enable hot reload */
    reload?: boolean;
}

export type BackendStatus = 'stopped' | 'starting' | 'running' | 'stopping' | 'error';

export interface BackendProcessCallbacks {
    onStatusChange?: (status: BackendStatus, message?: string) => void;
    onOutput?: (data: string) => void;
    onError?: (error: string) => void;
}

/**
 * BackendProcessManager - Manages the FastAPI backend process
 *
 * Features:
 * - Start/stop backend server
 * - Status monitoring
 * - Process output logging
 * - Python path auto-detection
 */
export class BackendProcessManager {
    private config: BackendProcessConfig;
    private callbacks: BackendProcessCallbacks;
    private process: ChildProcess | null = null;
    private status: BackendStatus = 'stopped';
    private outputLog: string[] = [];
    private maxLogLines: number = 100;
    private isToggling: boolean = false;
    private resolvedPythonPath: string | null = null;

    constructor(config: BackendProcessConfig, callbacks?: BackendProcessCallbacks) {
        this.config = {
            reload: true,
            ...config
        };
        this.callbacks = callbacks || {};
    }

    /**
     * Get current backend status
     */
    getStatus(): BackendStatus {
        return this.status;
    }

    /**
     * Get recent output log
     */
    getOutputLog(): string[] {
        return [...this.outputLog];
    }

    /**
     * Sync internal status with external state
     * Call this when external backend is detected running
     */
    syncStatus(status: BackendStatus, message?: string): void {
        this.setStatus(status, message);
    }

    /**
     * Check if backend is running (via health check)
     * Uses /api/v1/health endpoint (the actual FastAPI health endpoint)
     *
     * ✅ FIX: Use Obsidian's requestUrl instead of fetch()
     * This bypasses CORS issues in Electron environment
     * @see https://forum.obsidian.md/t/make-http-requests-from-plugins/15461
     */
    async isRunning(): Promise<boolean> {
        try {
            // Use 127.0.0.1 for local connection (0.0.0.0 is for binding, not connecting)
            const connectHost = this.config.host === '0.0.0.0' ? '127.0.0.1' : this.config.host;

            // Create timeout promise (requestUrl doesn't support AbortController)
            // FIX-4.14: Increased from 2s to 5s for better reliability
            const timeoutPromise = new Promise<never>((_, reject) =>
                setTimeout(() => reject(new Error('Health check timeout')), 5000)
            );

            const requestPromise = requestUrl({
                url: `http://${connectHost}:${this.config.port}/api/v1/health`,
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
                throw: false, // Don't throw on non-2xx status codes
            });

            const response: RequestUrlResponse = await Promise.race([
                requestPromise,
                timeoutPromise,
            ]);

            return response.status >= 200 && response.status < 300;
        } catch {
            return false;
        }
    }

    /**
     * Find Python executable path
     * Searches in order: configured path, virtual environments, system Python
     *
     * Fix: Use full paths for Windows since spawn() doesn't use shell PATH
     */
    private async findPythonPath(): Promise<string> {
        // If already resolved, return cached value
        if (this.resolvedPythonPath) {
            return this.resolvedPythonPath;
        }

        // If explicitly configured, use that
        if (this.config.pythonPath) {
            if (await this.isPythonValid(this.config.pythonPath)) {
                this.resolvedPythonPath = this.config.pythonPath;
                return this.resolvedPythonPath;
            }
        }

        // First, try to find Python using 'where' command on Windows
        // This is the most reliable way to get the full path
        if (process.platform === 'win32') {
            const wherePython = await this.findPythonWithWhere();
            if (wherePython) {
                this.resolvedPythonPath = wherePython;
                this.addLog(`Found Python via 'where': ${wherePython}`);
                return wherePython;
            }
        }

        // Search candidates in order of preference
        const candidates: string[] = [
            // Windows virtual environments
            path.join(this.config.backendPath, '.venv', 'Scripts', 'python.exe'),
            path.join(this.config.backendPath, 'venv', 'Scripts', 'python.exe'),
            // Unix virtual environments
            path.join(this.config.backendPath, '.venv', 'bin', 'python'),
            path.join(this.config.backendPath, 'venv', 'bin', 'python'),
        ];

        // Add common Windows Python installation paths
        if (process.platform === 'win32') {
            const userHome = process.env.USERPROFILE || process.env.HOME || '';
            const localAppData = process.env.LOCALAPPDATA || path.join(userHome, 'AppData', 'Local');
            const appData = process.env.APPDATA || path.join(userHome, 'AppData', 'Roaming');

            // Python versions to check (most common)
            const pyVersions = ['313', '312', '311', '310', '39', '38'];

            // Microsoft Store Python
            pyVersions.forEach(ver => {
                candidates.push(path.join(localAppData, 'Programs', 'Python', `Python${ver}`, 'python.exe'));
            });

            // Standard Python installer locations
            pyVersions.forEach(ver => {
                candidates.push(`C:\\Python${ver}\\python.exe`);
                candidates.push(`C:\\Program Files\\Python${ver}\\python.exe`);
                candidates.push(`C:\\Program Files (x86)\\Python${ver}\\python.exe`);
            });

            // Anaconda/Miniconda
            candidates.push(path.join(userHome, 'anaconda3', 'python.exe'));
            candidates.push(path.join(userHome, 'miniconda3', 'python.exe'));
            candidates.push(path.join(appData, 'Local', 'anaconda3', 'python.exe'));
            candidates.push(path.join(localAppData, 'anaconda3', 'python.exe'));

            // pyenv-win
            candidates.push(path.join(userHome, '.pyenv', 'pyenv-win', 'shims', 'python.exe'));
        }

        // Unix paths
        candidates.push('/usr/bin/python3');
        candidates.push('/usr/bin/python');
        candidates.push('/usr/local/bin/python3');
        candidates.push('/usr/local/bin/python');

        for (const candidate of candidates) {
            if (await this.isPythonValid(candidate)) {
                this.resolvedPythonPath = candidate;
                this.addLog(`Found Python at: ${candidate}`);
                return candidate;
            }
        }

        throw new Error('Python not found. Please configure pythonPath in settings or ensure Python is installed.');
    }

    /**
     * Find Python using 'where' command on Windows
     * This gets the full path that the system would use
     */
    private async findPythonWithWhere(): Promise<string | null> {
        return new Promise((resolve) => {
            exec('where python', { timeout: 5000 }, (error, stdout) => {
                if (error || !stdout.trim()) {
                    // Try python3
                    exec('where python3', { timeout: 5000 }, (err2, stdout2) => {
                        if (err2 || !stdout2.trim()) {
                            resolve(null);
                            return;
                        }
                        // Return first result
                        const firstPath = stdout2.trim().split('\n')[0].trim();
                        resolve(firstPath);
                    });
                    return;
                }
                // Return first result (most preferred Python)
                const firstPath = stdout.trim().split('\n')[0].trim();
                resolve(firstPath);
            });
        });
    }

    /**
     * Check if a Python path is valid and executable
     */
    private async isPythonValid(pythonPath: string): Promise<boolean> {
        return new Promise((resolve) => {
            // For absolute paths, check if file exists first
            if (path.isAbsolute(pythonPath)) {
                if (!fs.existsSync(pythonPath)) {
                    resolve(false);
                    return;
                }
            }

            // Try to run python --version
            exec(`"${pythonPath}" --version`, { timeout: 5000 }, (error) => {
                resolve(!error);
            });
        });
    }

    /**
     * Start the backend server
     */
    async start(): Promise<boolean> {
        if (this.status === 'running' || this.status === 'starting') {
            new Notice('Backend is already running');
            return false;
        }

        // Check if already running externally
        if (await this.isRunning()) {
            this.setStatus('running', 'Backend is already running (external process)');
            new Notice('Backend is already running');
            return true;
        }

        // ========== Port Pre-cleanup Logic ==========
        // Check if port is occupied by stale process (health check failed but port still in use)
        // This prevents EADDRINUSE error when starting backend
        const portInUse = await this.isPortInUse(this.config.port);
        if (portInUse) {
            this.addLog(`Port ${this.config.port} is in use by stale process, cleaning up...`);

            // Get and display PIDs occupying the port
            const stalePids = await this.getPidsOnPort(this.config.port);
            if (stalePids.length > 0) {
                this.addLog(`Found stale processes: ${stalePids.join(', ')}`);
            }

            // Kill processes occupying the port
            await this.killProcessOnPort(this.config.port);

            // Wait for port to be released (max 5 seconds)
            const portReleased = await this.waitForPortRelease(this.config.port, 5000);
            if (!portReleased) {
                this.setStatus('error', `Port ${this.config.port} is still in use after cleanup`);
                new Notice(`Cannot start: port ${this.config.port} is occupied`);
                return false;
            }

            this.addLog(`Port ${this.config.port} is now free`);
        }
        // ========== End Port Pre-cleanup Logic ==========

        this.setStatus('starting', 'Starting backend server...');
        new Notice('Starting backend server...');

        try {
            // Find Python path
            const pythonPath = await this.findPythonPath();
            this.addLog(`Using Python: ${pythonPath}`);

            // Build the command arguments
            const args = [
                '-m', 'uvicorn',
                'app.main:app',
                '--host', this.config.host,
                '--port', this.config.port.toString(),
            ];

            if (this.config.reload) {
                args.push('--reload');
            }

            this.addLog(`Starting: ${pythonPath} ${args.join(' ')}`);

            // FIX v2.1.0: Normalize cwd to resolve paths with ../ and handle Chinese characters
            // See: https://maxschmitt.me/posts/error-spawn-node-enoent-node-js-child-process
            const normalizedCwd = path.resolve(this.config.backendPath);
            this.addLog(`Working directory (raw): ${this.config.backendPath}`);
            this.addLog(`Working directory (normalized): ${normalizedCwd}`);

            // Validate directory exists
            if (!fs.existsSync(normalizedCwd)) {
                throw new Error(`Backend directory not found: ${normalizedCwd}`);
            }

            // FIX v2.1.0: Use shell: true to handle Windows path issues
            // This runs through cmd.exe which properly handles:
            // - Unicode/Chinese characters in paths
            // - Complex path structures
            // - Environment variable resolution
            // Note: shell: true is incompatible with detached: true on Windows
            this.process = spawn(pythonPath, args, {
                cwd: normalizedCwd,
                shell: true,  // KEY FIX: Use shell to handle Windows path issues
                windowsHide: true,  // Hide console window on Windows
                stdio: ['ignore', 'pipe', 'pipe'],  // Redirect stdout/stderr
                env: {
                    ...process.env,
                    PYTHONUNBUFFERED: '1',  // Ensure unbuffered output
                    PATH: process.env.PATH  // Explicitly inherit PATH
                }
            });

            // Note: Cannot use unref() with shell: true on Windows
            // The process will be managed through the shell

            // Store the PID for later termination
            const pid = this.process.pid;
            this.addLog(`Process started with PID: ${pid}`);

            // Handle stdout
            this.process.stdout?.on('data', (data: Buffer) => {
                const text = data.toString();
                this.addLog(text);
                this.callbacks.onOutput?.(text);
            });

            // Handle stderr (uvicorn outputs to stderr by default)
            this.process.stderr?.on('data', (data: Buffer) => {
                const text = data.toString();
                this.addLog(`[stderr] ${text}`);
                this.callbacks.onError?.(text);
            });

            // Handle process exit
            this.process.on('exit', (code, signal) => {
                this.addLog(`Process exited with code ${code}, signal ${signal}`);
                this.process = null;

                if (this.status !== 'stopping' && this.status !== 'stopped') {
                    this.setStatus('error', `Backend stopped unexpectedly (code: ${code})`);
                    new Notice(`Backend stopped unexpectedly`);
                }
            });

            // Handle process error
            this.process.on('error', (error) => {
                this.addLog(`Process error: ${error.message}`);
                this.callbacks.onError?.(error.message);
                this.setStatus('error', `Failed to start: ${error.message}`);
                new Notice(`Failed to start backend: ${error.message}`);
                this.process = null;
            });

            // Poll for startup with 30 second timeout
            // FIX-4.14: Increased from 15s to 30s for slow startup scenarios
            const maxWaitMs = 30000;
            const pollInterval = 1000;
            const startTime = Date.now();

            while (Date.now() - startTime < maxWaitMs) {
                if (await this.isRunning()) {
                    this.setStatus('running', 'Backend server started successfully');
                    new Notice('Backend server started');
                    return true;
                }

                // Check if process died
                if (this.process === null) {
                    this.setStatus('error', 'Backend process exited unexpectedly');
                    return false;
                }

                await this.sleep(pollInterval);
            }

            // Timeout - check one more time
            if (await this.isRunning()) {
                this.setStatus('running', 'Backend server started successfully');
                new Notice('Backend server started');
                return true;
            }

            // Failed to start in time
            this.setStatus('error', 'Backend failed to start in time');
            new Notice('Backend startup timeout - check logs');
            return false;

        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            this.setStatus('error', `Failed to start: ${message}`);
            new Notice(`Failed to start backend: ${message}`);
            return false;
        }
    }

    /**
     * Stop the backend server
     */
    async stop(): Promise<boolean> {
        // Check both internal status AND actual running state
        const actuallyRunning = await this.isRunning();
        const portInUse = await this.isPortInUse(this.config.port);

        if (this.status === 'stopped' && !actuallyRunning && !portInUse) {
            new Notice('Backend is not running');
            return true;
        }

        this.setStatus('stopping', 'Stopping backend server...');
        new Notice('Stopping backend server...');

        try {
            // Get PIDs before killing for user feedback
            const pids = await this.getPidsOnPort(this.config.port);
            if (pids.length > 0) {
                this.addLog(`Found ${pids.length} process(es) to stop: ${pids.join(', ')}`);
            }

            // Kill all processes on port - this is the most reliable method
            await this.killProcessOnPort(this.config.port);

            // Clear internal process reference
            this.process = null;

            // Wait for port to be released
            const portReleased = await this.waitForPortRelease(this.config.port, 8000);

            if (portReleased) {
                this.setStatus('stopped', 'Backend stopped');
                new Notice('Backend stopped successfully');
                return true;
            } else {
                // Port still in use - try one more aggressive kill
                this.addLog('Port still in use, trying aggressive kill...');
                await this.forceKillAllPython();
                await this.sleep(1000);

                if (await this.waitForPortRelease(this.config.port, 3000)) {
                    this.setStatus('stopped', 'Backend stopped');
                    new Notice('Backend stopped successfully');
                    return true;
                }

                // Still failed
                this.setStatus('error', 'Failed to stop backend completely');
                new Notice('Could not stop backend - try closing terminal manually');
                return false;
            }

        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            this.setStatus('error', `Failed to stop: ${message}`);
            new Notice(`Failed to stop backend: ${message}`);
            return false;
        }
    }

    /**
     * Force kill all Python processes (last resort)
     */
    private async forceKillAllPython(): Promise<void> {
        return new Promise((resolve) => {
            if (process.platform === 'win32') {
                // Kill all python processes listening on our port using wmic
                exec(`wmic process where "name='python.exe'" get processid`, (error, stdout) => {
                    if (error || !stdout) {
                        resolve();
                        return;
                    }

                    // Extract PIDs and kill only those on our port
                    this.getPidsOnPort(this.config.port).then(pids => {
                        pids.forEach(pid => {
                            exec(`taskkill /pid ${pid} /T /F`, () => {});
                        });
                        resolve();
                    });
                });
            } else {
                resolve();
            }
        });
    }

    /**
     * Restart the backend server
     */
    async restart(): Promise<boolean> {
        await this.stop();
        await this.sleep(1000);
        return this.start();
    }

    /**
     * Toggle backend (start if stopped, stop if running)
     */
    async toggle(): Promise<boolean> {
        // Prevent concurrent toggle operations
        if (this.isToggling) {
            new Notice('Operation in progress...');
            return false;
        }

        this.isToggling = true;

        try {
            const actuallyRunning = await this.isRunning();

            // Sync internal status with actual state
            if (actuallyRunning && this.status !== 'running') {
                this.setStatus('running', 'External backend detected');
            } else if (!actuallyRunning && this.status === 'running') {
                this.setStatus('stopped', 'Backend no longer running');
            }

            // Toggle based on actual state
            if (actuallyRunning) {
                return await this.stop();
            } else {
                return await this.start();
            }
        } finally {
            this.isToggling = false;
        }
    }

    /**
     * Cleanup on plugin unload
     */
    async cleanup(): Promise<void> {
        // Don't auto-stop on cleanup - let the backend run independently
        // User can manually stop if needed
        this.process = null;
    }

    /**
     * Update configuration
     */
    updateConfig(config: Partial<BackendProcessConfig>): void {
        this.config = { ...this.config, ...config };
        // Clear cached Python path if config changes
        if (config.pythonPath !== undefined || config.backendPath !== undefined) {
            this.resolvedPythonPath = null;
        }
    }

    // Private methods

    private setStatus(status: BackendStatus, message?: string): void {
        this.status = status;
        this.callbacks.onStatusChange?.(status, message);
    }

    private addLog(text: string): void {
        const timestamp = new Date().toISOString().slice(11, 19);
        const lines = text.split('\n').filter(line => line.trim());
        lines.forEach(line => {
            this.outputLog.push(`[${timestamp}] ${line}`);
        });

        // Keep only last N lines
        if (this.outputLog.length > this.maxLogLines) {
            this.outputLog = this.outputLog.slice(-this.maxLogLines);
        }
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Kill all processes listening on the specified port
     * Uses /T flag to kill entire process tree (important for uvicorn --reload)
     */
    private async killProcessOnPort(port: number): Promise<void> {
        if (process.platform === 'win32') {
            // Windows: find and kill all processes on port
            // Try up to 3 times to ensure all processes are killed
            for (let attempt = 0; attempt < 3; attempt++) {
                const pids = await this.getPidsOnPort(port);

                if (pids.length === 0) {
                    this.addLog(`Port ${port} is free`);
                    return;
                }

                this.addLog(`Attempt ${attempt + 1}: Found ${pids.length} PIDs on port ${port}: ${pids.join(', ')}`);

                // Kill all processes with /T flag to kill process tree
                for (const pid of pids) {
                    await new Promise<void>((resolve) => {
                        // Use /T to kill entire process tree (important for uvicorn workers)
                        exec(`taskkill /pid ${pid} /T /F`, (killError, stdout, stderr) => {
                            if (killError) {
                                this.addLog(`Failed to kill PID ${pid}: ${killError.message}`);
                            } else {
                                this.addLog(`Killed PID ${pid} and its process tree`);
                            }
                            resolve();
                        });
                    });
                }

                // Wait a bit for processes to terminate
                await this.sleep(500);
            }
        } else {
            // Unix: use lsof and kill
            await new Promise<void>((resolve) => {
                exec(`lsof -ti:${port} | xargs kill -9 2>/dev/null`, () => {
                    resolve();
                });
            });
        }
    }

    /**
     * Get all PIDs listening on a specific port
     */
    private async getPidsOnPort(port: number): Promise<string[]> {
        return new Promise((resolve) => {
            exec(`netstat -ano | findstr :${port} | findstr LISTENING`, (error, stdout) => {
                if (error || !stdout.trim()) {
                    resolve([]);
                    return;
                }

                const pids = new Set<string>();
                stdout.split('\n').forEach(line => {
                    // Extract PID from end of line: "  TCP    0.0.0.0:8001  ...  LISTENING  12345"
                    const parts = line.trim().split(/\s+/);
                    if (parts.length >= 5) {
                        const pid = parts[parts.length - 1];
                        if (pid && pid !== '0' && /^\d+$/.test(pid)) {
                            pids.add(pid);
                        }
                    }
                });

                resolve(Array.from(pids));
            });
        });
    }

    /**
     * Wait for port to be released (no process listening)
     */
    private async waitForPortRelease(port: number, maxWaitMs: number = 5000): Promise<boolean> {
        const startTime = Date.now();
        const checkInterval = 500;

        while (Date.now() - startTime < maxWaitMs) {
            const isInUse = await this.isPortInUse(port);
            if (!isInUse) {
                return true;
            }
            await this.sleep(checkInterval);
        }

        return false;
    }

    /**
     * Check if port is in use (via netstat, not health check)
     */
    private async isPortInUse(port: number): Promise<boolean> {
        return new Promise((resolve) => {
            if (process.platform === 'win32') {
                exec(`netstat -ano | findstr :${port} | findstr LISTENING`, (error, stdout) => {
                    resolve(!error && stdout.trim().length > 0);
                });
            } else {
                exec(`lsof -ti:${port}`, (error, stdout) => {
                    resolve(!error && stdout.trim().length > 0);
                });
            }
        });
    }
}

/**
 * Create BackendProcessManager with default configuration
 */
export function createBackendProcessManager(
    backendPath: string,
    callbacks?: BackendProcessCallbacks
): BackendProcessManager {
    return new BackendProcessManager({
        backendPath,
        port: 8000,  // FIX: 统一端口为8000 (后端实际运行端口)
        host: '0.0.0.0',
        reload: false,  // FIX: Windows uvicorn --reload bug (WinError 6)
    }, callbacks);
}
