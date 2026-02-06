/**
 * Color Change Memory Integration Tests - Canvas Learning System
 *
 * Tests for Story 30.6: Node Color Change Memory Trigger
 *
 * Integration Test Coverage:
 * - Task 7.1: End-to-end: canvas file change → API call
 * - Task 7.2: Multiple rapid color changes batch correctly
 * - Task 7.3: Watcher lifecycle (start/stop)
 *
 * These tests verify the complete flow from file modification to API call,
 * simulating real-world usage patterns in Obsidian.
 *
 * @module color-change-memory.test
 * @version 1.0.0
 * @source Story 30.6: docs/stories/30.6.story.md
 */

import {
    NodeColorChangeWatcher,
    ColorMasteryLevel,
    ColorChangeEvent,
    ColorChangeEventType,
} from '../../src/services/NodeColorChangeWatcher';
import { TFile } from '../__mocks__/obsidian';

// Mock requestUrl from Obsidian
const mockRequestUrl = jest.fn();
jest.mock('obsidian', () => ({
    ...jest.requireActual('../__mocks__/obsidian'),
    requestUrl: (...args: any[]) => mockRequestUrl(...args),
}));

// ============================================================================
// Mock App with Vault event support (reused from unit tests)
// ============================================================================

function createMockApp() {
    const eventListeners: Map<string, Array<(file: TFile) => void>> = new Map();
    let eventRefCounter = 0;
    const eventRefs: Map<number, { event: string; callback: (file: TFile) => void }> = new Map();

    const mockVault = {
        _files: new Map<string, string>(),

        on: jest.fn((event: string, callback: (file: TFile) => void) => {
            if (!eventListeners.has(event)) {
                eventListeners.set(event, []);
            }
            eventListeners.get(event)!.push(callback);
            const refId = ++eventRefCounter;
            eventRefs.set(refId, { event, callback });
            return refId;
        }),

        offref: jest.fn((ref: number) => {
            const eventRef = eventRefs.get(ref);
            if (eventRef) {
                const listeners = eventListeners.get(eventRef.event);
                if (listeners) {
                    const index = listeners.indexOf(eventRef.callback);
                    if (index > -1) {
                        listeners.splice(index, 1);
                    }
                }
                eventRefs.delete(ref);
            }
        }),

        read: jest.fn(async (file: TFile) => {
            const content = mockVault._files.get(file.path);
            if (content === undefined) {
                throw new Error(`File not found: ${file.path}`);
            }
            return content;
        }),

        _triggerModify: async (file: TFile): Promise<void> => {
            const listeners = eventListeners.get('modify') || [];
            await Promise.all(listeners.map(cb => cb(file)));
        },

        _setFile: (path: string, content: string) => {
            mockVault._files.set(path, content);
        },

        getFiles: jest.fn(() => {
            return Array.from(mockVault._files.keys()).map(path => new TFile(path));
        }),

        _clear: () => {
            mockVault._files.clear();
            eventListeners.clear();
            eventRefs.clear();
        },

        _getListenerCount: (event: string) => {
            return (eventListeners.get(event) || []).length;
        },
    };

    return {
        vault: mockVault,
        workspace: {},
    } as any;
}

// ============================================================================
// Integration Tests
// ============================================================================

describe('Color Change Memory Integration', () => {
    let mockApp: ReturnType<typeof createMockApp>;
    let watcher: NodeColorChangeWatcher;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        mockApp = createMockApp();
    });

    afterEach(() => {
        if (watcher) {
            watcher.stop();
        }
        mockApp.vault._clear();
        jest.useRealTimers();
    });

    // ========================================================================
    // Task 7.1: End-to-end canvas file change → API call
    // ========================================================================

    describe('End-to-End Flow (Task 7.1)', () => {
        it('should complete full flow: file change → detection → API call', async () => {
            // Setup API mock
            mockRequestUrl.mockResolvedValue({ status: 200, json: {} });

            // Create watcher with settings matching production defaults
            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 500, // AC-30.6.4: 500ms debounce
                apiBaseUrl: 'http://localhost:8000/api/v1',
                timeout: 500, // ADR-0004: 500ms timeout
                enableLogging: true, // Enable for debugging
            });

            // Setup initial canvas state (simulating existing Canvas)
            const initialCanvas = {
                nodes: [
                    {
                        id: 'concept-001',
                        type: 'text',
                        text: '逆否命题',
                        x: 100,
                        y: 200,
                        width: 250,
                        height: 60,
                        color: '1', // Red - NOT_UNDERSTOOD
                    },
                ],
                edges: [],
            };
            mockApp.vault._setFile('离散数学/命题逻辑.canvas', JSON.stringify(initialCanvas));

            // Start watching
            await watcher.start();
            expect(watcher.isActive()).toBe(true);

            // Seed the initial state by triggering a modify event
            await mockApp.vault._triggerModify(new TFile('离散数学/命题逻辑.canvas'));
            // Clear any pending changes from seeding
            jest.advanceTimersByTime(600);
            await Promise.resolve();
            mockRequestUrl.mockClear();

            // Simulate user changing node color (red → green: learning progress!)
            const updatedCanvas = {
                ...initialCanvas,
                nodes: [
                    {
                        ...initialCanvas.nodes[0],
                        color: '2', // Green - MASTERED
                    },
                ],
            };
            mockApp.vault._setFile('离散数学/命题逻辑.canvas', JSON.stringify(updatedCanvas));

            // Trigger modify event (simulating Obsidian file system event)
            await mockApp.vault._triggerModify(new TFile('离散数学/命题逻辑.canvas'));

            // Verify change was detected
            expect(watcher.getPendingChangesCount()).toBe(1);

            // Wait for debounce (500ms)
            jest.advanceTimersByTime(600);
            await Promise.resolve();

            // Verify API was called
            expect(mockRequestUrl).toHaveBeenCalledTimes(1);

            // Verify API payload structure
            const apiCall = mockRequestUrl.mock.calls[0][0];
            expect(apiCall.url).toBe('http://localhost:8000/api/v1/memory/episodes/batch');
            expect(apiCall.method).toBe('POST');
            expect(apiCall.headers['Content-Type']).toBe('application/json');

            // Parse and verify payload content
            const payload = JSON.parse(apiCall.body);
            expect(payload.events).toHaveLength(1);

            const event = payload.events[0];
            expect(event.event_type).toBe('color_changed');
            expect(event.canvas_path).toBe('离散数学/命题逻辑.canvas');
            expect(event.node_id).toBe('concept-001');
            expect(event.metadata.old_color).toBe('1');
            expect(event.metadata.new_color).toBe('2');
            expect(event.metadata.old_level).toBe(ColorMasteryLevel.NOT_UNDERSTOOD);
            expect(event.metadata.new_level).toBe(ColorMasteryLevel.MASTERED);
            expect(event.metadata.node_text).toBe('逆否命题');
            expect(event.timestamp).toBeDefined();
        });

        it('should track learning progression: red → yellow → green', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 100,
                enableLogging: false,
            });

            // Initial state: red (not understood)
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', text: 'Concept', color: '1' }],
            }));

            await watcher.start();

            // Seed the initial state
            await mockApp.vault._triggerModify(new TFile('test.canvas'));
            jest.advanceTimersByTime(150);
            await Promise.resolve();
            mockRequestUrl.mockClear();

            // Step 1: red → yellow (started learning)
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', text: 'Concept', color: '6' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            jest.advanceTimersByTime(150);
            await Promise.resolve();

            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
            let payload = JSON.parse(mockRequestUrl.mock.calls[0][0].body);
            expect(payload.events[0].metadata.old_level).toBe(ColorMasteryLevel.NOT_UNDERSTOOD);
            expect(payload.events[0].metadata.new_level).toBe(ColorMasteryLevel.LEARNING);

            // Step 2: yellow → green (mastered)
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', text: 'Concept', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            jest.advanceTimersByTime(150);
            await Promise.resolve();

            expect(mockRequestUrl).toHaveBeenCalledTimes(2);
            payload = JSON.parse(mockRequestUrl.mock.calls[1][0].body);
            expect(payload.events[0].metadata.old_level).toBe(ColorMasteryLevel.LEARNING);
            expect(payload.events[0].metadata.new_level).toBe(ColorMasteryLevel.MASTERED);
        });
    });

    // ========================================================================
    // Task 7.2: Multiple rapid color changes batch correctly
    // ========================================================================

    describe('Rapid Changes Batching (Task 7.2)', () => {
        it('should batch rapid consecutive saves from Obsidian auto-save', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 500,
                enableLogging: false,
            });

            // Setup initial state
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));

            await watcher.start();

            // Simulate Obsidian's rapid auto-save behavior
            // (multiple save events in quick succession)
            for (let i = 0; i < 5; i++) {
                mockApp.vault._setFile('test.canvas', JSON.stringify({
                    nodes: [{ id: 'node1', color: '2' }],
                }));
                await mockApp.vault._triggerModify(new TFile('test.canvas'));
                jest.advanceTimersByTime(50); // 50ms between saves
            }

            // Wait for debounce
            jest.advanceTimersByTime(500);
            await Promise.resolve();

            // Should only make ONE API call despite 5 save events
            // (only first save detected a change, subsequent saves had same color)
            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
        });

        it('should batch changes across multiple nodes', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 500,
                enableLogging: false,
            });

            // Setup initial state with 3 nodes
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', color: '1' },
                    { id: 'node2', color: '1' },
                    { id: 'node3', color: '1' },
                ],
            }));

            await watcher.start();

            // Seed the initial state
            await mockApp.vault._triggerModify(new TFile('test.canvas'));
            jest.advanceTimersByTime(600);
            await Promise.resolve();
            mockRequestUrl.mockClear();

            // User quickly changes all 3 nodes (within 500ms debounce)
            // Change 1
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', color: '2' },
                    { id: 'node2', color: '1' },
                    { id: 'node3', color: '1' },
                ],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));
            jest.advanceTimersByTime(100);

            // Change 2
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', color: '2' },
                    { id: 'node2', color: '3' },
                    { id: 'node3', color: '1' },
                ],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));
            jest.advanceTimersByTime(100);

            // Change 3
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', color: '2' },
                    { id: 'node2', color: '3' },
                    { id: 'node3', color: '6' },
                ],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Wait for debounce
            jest.advanceTimersByTime(600);
            await Promise.resolve();

            // Should make ONE API call with all 3 changes batched
            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
            const payload = JSON.parse(mockRequestUrl.mock.calls[0][0].body);
            expect(payload.events).toHaveLength(3);
        });

        it('should batch changes across multiple canvas files', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 500,
                enableLogging: false,
            });

            // Setup multiple canvas files
            mockApp.vault._setFile('math.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));
            mockApp.vault._setFile('physics.canvas', JSON.stringify({
                nodes: [{ id: 'node2', color: '1' }],
            }));
            mockApp.vault._setFile('chemistry.canvas', JSON.stringify({
                nodes: [{ id: 'node3', color: '1' }],
            }));

            await watcher.start();

            // Seed the initial states for all canvases
            await mockApp.vault._triggerModify(new TFile('math.canvas'));
            await mockApp.vault._triggerModify(new TFile('physics.canvas'));
            await mockApp.vault._triggerModify(new TFile('chemistry.canvas'));
            jest.advanceTimersByTime(600);
            await Promise.resolve();
            mockRequestUrl.mockClear();

            // User switches between canvases and makes changes
            mockApp.vault._setFile('math.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('math.canvas'));
            jest.advanceTimersByTime(100);

            mockApp.vault._setFile('physics.canvas', JSON.stringify({
                nodes: [{ id: 'node2', color: '3' }],
            }));
            await mockApp.vault._triggerModify(new TFile('physics.canvas'));
            jest.advanceTimersByTime(100);

            mockApp.vault._setFile('chemistry.canvas', JSON.stringify({
                nodes: [{ id: 'node3', color: '6' }],
            }));
            await mockApp.vault._triggerModify(new TFile('chemistry.canvas'));

            // Wait for debounce
            jest.advanceTimersByTime(600);
            await Promise.resolve();

            // Should batch all 3 canvas changes into ONE API call
            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
            const payload = JSON.parse(mockRequestUrl.mock.calls[0][0].body);
            expect(payload.events).toHaveLength(3);
            expect(payload.events.map((e: any) => e.canvas_path).sort()).toEqual([
                'chemistry.canvas',
                'math.canvas',
                'physics.canvas',
            ]);
        });
    });

    // ========================================================================
    // Task 7.3: Watcher lifecycle (start/stop)
    // ========================================================================

    describe('Watcher Lifecycle (Task 7.3)', () => {
        it('should properly initialize and start watching', async () => {
            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 500,
            });

            expect(watcher.isActive()).toBe(false);
            expect(mockApp.vault._getListenerCount('modify')).toBe(0);

            await watcher.start();

            expect(watcher.isActive()).toBe(true);
            expect(mockApp.vault._getListenerCount('modify')).toBe(1);
            expect(mockApp.vault.on).toHaveBeenCalledWith('modify', expect.any(Function));
        });

        it('should properly stop and cleanup', async () => {
            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 500,
            });

            await watcher.start();
            expect(watcher.isActive()).toBe(true);

            watcher.stop();

            expect(watcher.isActive()).toBe(false);
            expect(mockApp.vault.offref).toHaveBeenCalled();
        });

        it('should flush pending changes when stopped', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 500,
            });

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));

            await watcher.start();

            // Make a change
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Don't wait for debounce - stop immediately
            expect(watcher.getPendingChangesCount()).toBe(1);

            watcher.stop();
            await Promise.resolve();

            // Should have flushed the pending change
            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
        });

        it('should survive multiple start/stop cycles', async () => {
            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 500,
            });

            // Cycle 1
            await watcher.start();
            expect(watcher.isActive()).toBe(true);
            watcher.stop();
            expect(watcher.isActive()).toBe(false);

            // Cycle 2
            await watcher.start();
            expect(watcher.isActive()).toBe(true);
            watcher.stop();
            expect(watcher.isActive()).toBe(false);

            // Cycle 3
            await watcher.start();
            expect(watcher.isActive()).toBe(true);
            watcher.stop();
            expect(watcher.isActive()).toBe(false);
        });

        it('should handle being disabled via settings update', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 500,
            });

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));

            await watcher.start();
            expect(watcher.isActive()).toBe(true);

            // Disable via settings
            watcher.updateSettings({ enabled: false });
            expect(watcher.isActive()).toBe(false);

            // Changes should not be processed
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            jest.advanceTimersByTime(600);
            await Promise.resolve();

            expect(mockRequestUrl).not.toHaveBeenCalled();
        });

        it('should restart when re-enabled via settings', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: false, // Start disabled
                debounceMs: 500,
            });

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));

            // Manually start - should be no-op since disabled
            await watcher.start();
            expect(watcher.isActive()).toBe(false);

            // Enable via settings (updateSettings calls start() internally)
            watcher.updateSettings({ enabled: true });
            expect(watcher.isActive()).toBe(true);

            // Wait for async start() to complete (initializeState + event listener registration)
            for (let i = 0; i < 5; i++) {
                await Promise.resolve();
            }

            // Now changes should be processed
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            jest.advanceTimersByTime(600);
            await Promise.resolve();

            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
        });
    });

    // ========================================================================
    // Error Recovery Tests
    // ========================================================================

    describe('Error Recovery', () => {
        it('should continue working after API failure', async () => {
            // First call fails, second succeeds
            mockRequestUrl
                .mockRejectedValueOnce(new Error('Network error'))
                .mockResolvedValueOnce({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 100,
            });

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));

            await watcher.start();

            // First change - will fail
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            jest.advanceTimersByTime(150);
            await Promise.resolve();

            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
            expect(watcher.isActive()).toBe(true); // Still running

            // Second change - should succeed
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '3' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            jest.advanceTimersByTime(150);
            await Promise.resolve();

            expect(mockRequestUrl).toHaveBeenCalledTimes(2);
        });

        it('should handle file read errors gracefully', async () => {
            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 100,
            });

            await watcher.start();

            // Trigger modify for non-existent file
            await mockApp.vault._triggerModify(new TFile('non-existent.canvas'));

            // Should not crash
            await Promise.resolve();
            expect(watcher.isActive()).toBe(true);
        });
    });

    // ========================================================================
    // Story 30.9: Color Removal & Node Deletion Integration
    // ========================================================================

    describe('Story 30.9: Color Removal & Node Deletion', () => {
        it('should detect color removal and send color_removed event', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 100,
                apiBaseUrl: 'http://localhost:8000/api/v1',
                timeout: 500,
                enableLogging: false,
            });

            // Initial state: node with color
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', text: 'Test Concept', color: '1' },
                ],
                edges: [],
            }));

            await watcher.start();
            mockRequestUrl.mockClear();

            // Remove color (node still exists, but no color property)
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', text: 'Test Concept' },
                ],
                edges: [],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            jest.advanceTimersByTime(150);
            await Promise.resolve();

            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
            const payload = JSON.parse(mockRequestUrl.mock.calls[0][0].body);
            expect(payload.events).toHaveLength(1);
            expect(payload.events[0].event_type).toBe('color_removed');
            expect(payload.events[0].metadata.old_color).toBe('1');
            expect(payload.events[0].metadata.new_color).toBeNull();
        });

        it('should detect node deletion and send node_removed event', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 100,
                apiBaseUrl: 'http://localhost:8000/api/v1',
                timeout: 500,
                enableLogging: false,
            });

            // Initial state: two nodes with colors
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', text: 'Keep This', color: '2' },
                    { id: 'node2', text: 'Delete This', color: '1' },
                ],
                edges: [],
            }));

            await watcher.start();
            mockRequestUrl.mockClear();

            // Delete node2 entirely
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', text: 'Keep This', color: '2' },
                ],
                edges: [],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            jest.advanceTimersByTime(150);
            await Promise.resolve();

            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
            const payload = JSON.parse(mockRequestUrl.mock.calls[0][0].body);
            expect(payload.events).toHaveLength(1);
            expect(payload.events[0].event_type).toBe('node_removed');
            expect(payload.events[0].metadata.old_color).toBe('1');
            expect(payload.events[0].metadata.new_color).toBeNull();
        });

        it('should include concept field in API payload', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 100,
                apiBaseUrl: 'http://localhost:8000/api/v1',
                timeout: 500,
                enableLogging: false,
            });

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', text: '监督学习概念', color: '1' }],
                edges: [],
            }));

            await watcher.start();
            mockRequestUrl.mockClear();

            // Change color
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', text: '监督学习概念', color: '2' }],
                edges: [],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            jest.advanceTimersByTime(150);
            await Promise.resolve();

            expect(mockRequestUrl).toHaveBeenCalledTimes(1);
            const payload = JSON.parse(mockRequestUrl.mock.calls[0][0].body);
            expect(payload.events[0].metadata.concept).toBe('监督学习概念');
        });

        it('should preload state on startup preventing spurious events', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            // Setup files BEFORE starting watcher
            mockApp.vault._setFile('math.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', text: 'Algebra', color: '1' },
                    { id: 'node2', text: 'Calculus', color: '2' },
                ],
                edges: [],
            }));

            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 100,
                enableLogging: false,
            });

            await watcher.start();

            // Trigger modify WITHOUT changing any colors
            await mockApp.vault._triggerModify(new TFile('math.canvas'));

            jest.advanceTimersByTime(150);
            await Promise.resolve();

            // No API call since no actual color change occurred
            expect(mockRequestUrl).not.toHaveBeenCalled();
        });
    });
});
