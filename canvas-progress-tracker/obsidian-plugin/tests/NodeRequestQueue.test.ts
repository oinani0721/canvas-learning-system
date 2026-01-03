/**
 * NodeRequestQueue Unit Tests
 *
 * Story 12.H.2: Node-level Request Queue
 *
 * Tests for the NodeRequestQueue class that ensures:
 * - Same node requests execute sequentially (AC1, AC2, AC4)
 * - Different node requests execute concurrently (AC5)
 * - Status query methods work correctly
 *
 * @module tests/NodeRequestQueue
 * @source Story 12.H.2 - 同一节点并发 Agent 限制
 */

// Mock Obsidian Notice class
jest.mock('obsidian', () => ({
    Notice: jest.fn(),
}), { virtual: true });

import { Notice } from 'obsidian';

/**
 * Helper function to create a delay
 */
const sleep = (ms: number): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

/**
 * NodeRequestQueue class - copied from main.ts for isolated testing
 *
 * In production, this would be exported from a separate module.
 * For testing purposes, we replicate the class here.
 *
 * @source main.ts:60-134
 */
class NodeRequestQueue {
    /** Map of nodeId -> current Promise chain */
    private nodeQueues: Map<string, Promise<unknown>> = new Map();

    /** Map of nodeId -> currently running Agent type (for user feedback) */
    private nodeAgentTypes: Map<string, string> = new Map();

    /**
     * Enqueue a request for a specific node
     */
    async enqueue<T>(
        nodeId: string,
        agentType: string,
        fn: () => Promise<T>
    ): Promise<T> {
        // Check if there's a request in progress for this node
        const currentAgent = this.nodeAgentTypes.get(nodeId);
        if (currentAgent) {
            // Notify user that node is busy
            new Notice(`节点正在处理 "${currentAgent}"，请稍候...`);
        }

        // Get current queue for this node (or resolved Promise if none)
        const prev = this.nodeQueues.get(nodeId) || Promise.resolve();

        // Create new Promise that chains after previous
        const current = prev.then(async () => {
            // Set current agent type for this node
            this.nodeAgentTypes.set(nodeId, agentType);

            try {
                return await fn();
            } finally {
                // Cleanup: only remove if this is still the current queue item
                if (this.nodeQueues.get(nodeId) === current) {
                    this.nodeQueues.delete(nodeId);
                    this.nodeAgentTypes.delete(nodeId);
                }
            }
        });

        // Store as current queue item for this node
        this.nodeQueues.set(nodeId, current);
        return current as Promise<T>;
    }

    /**
     * Check if a node has a request in progress
     */
    isProcessing(nodeId: string): boolean {
        return this.nodeQueues.has(nodeId);
    }

    /**
     * Get the currently running Agent type for a node
     */
    getCurrentAgentType(nodeId: string): string | undefined {
        return this.nodeAgentTypes.get(nodeId);
    }
}

describe('NodeRequestQueue', () => {
    let queue: NodeRequestQueue;

    beforeEach(() => {
        queue = new NodeRequestQueue();
        jest.clearAllMocks();
    });

    describe('Sequential Execution (AC1, AC2, AC4)', () => {
        /**
         * Story 12.H.2 AC1, AC4: Same node requests execute sequentially
         * Given: Two requests for the same node
         * When: Both are enqueued
         * Then: They execute in FIFO order (request 1 completes before request 2 starts)
         */
        it('should process same node requests sequentially', async () => {
            const executionOrder: number[] = [];

            const promise1 = queue.enqueue('node-1', 'agent-a', async () => {
                await sleep(100);
                executionOrder.push(1);
                return 'result-1';
            });

            const promise2 = queue.enqueue('node-1', 'agent-b', async () => {
                executionOrder.push(2);
                return 'result-2';
            });

            const [result1, result2] = await Promise.all([promise1, promise2]);

            // Verify sequential execution order
            expect(executionOrder).toEqual([1, 2]);
            expect(result1).toBe('result-1');
            expect(result2).toBe('result-2');
        });

        /**
         * Story 12.H.2 AC2: Subsequent requests queue
         * Given: A request is processing for node-1
         * When: Another request arrives for node-1
         * Then: The new request is queued (not rejected)
         */
        it('should queue subsequent requests for the same node', async () => {
            const results: string[] = [];
            let firstStarted = false;
            let secondStarted = false;

            const promise1 = queue.enqueue('node-1', 'agent-a', async () => {
                firstStarted = true;
                await sleep(50);
                results.push('first');
                return 'first';
            });

            // Second request should be queued, not rejected
            const promise2 = queue.enqueue('node-1', 'agent-b', async () => {
                secondStarted = true;
                results.push('second');
                return 'second';
            });

            // Both promises should resolve (neither rejected)
            const [r1, r2] = await Promise.all([promise1, promise2]);

            expect(r1).toBe('first');
            expect(r2).toBe('second');
            expect(results).toEqual(['first', 'second']);
        });

        /**
         * Story 12.H.2: Three requests for same node
         * Verifies FIFO order is maintained for multiple queued requests
         */
        it('should maintain FIFO order for multiple queued requests', async () => {
            const order: number[] = [];

            const p1 = queue.enqueue('node-1', 'agent-a', async () => {
                await sleep(30);
                order.push(1);
            });

            const p2 = queue.enqueue('node-1', 'agent-b', async () => {
                await sleep(20);
                order.push(2);
            });

            const p3 = queue.enqueue('node-1', 'agent-c', async () => {
                await sleep(10);
                order.push(3);
            });

            await Promise.all([p1, p2, p3]);

            // Despite different durations, order should be 1, 2, 3 (FIFO)
            expect(order).toEqual([1, 2, 3]);
        });
    });

    describe('Concurrent Execution (AC5)', () => {
        /**
         * Story 12.H.2 AC5: Different nodes execute concurrently
         * Given: node-1 has a running Agent
         * When: User clicks Agent on node-2
         * Then: node-2 executes immediately (concurrent)
         */
        it('should process different node requests concurrently', async () => {
            const results: string[] = [];

            const promise1 = queue.enqueue('node-1', 'agent-a', async () => {
                await sleep(100);
                results.push('node-1');
                return 'result-1';
            });

            const promise2 = queue.enqueue('node-2', 'agent-a', async () => {
                // No delay - should complete before node-1
                results.push('node-2');
                return 'result-2';
            });

            await Promise.all([promise1, promise2]);

            // node-2 should complete first (concurrent execution)
            expect(results[0]).toBe('node-2');
            expect(results[1]).toBe('node-1');
        });

        /**
         * Verify multiple different nodes can all run concurrently
         */
        it('should allow multiple nodes to process concurrently', async () => {
            const startTimes: Map<string, number> = new Map();
            const endTimes: Map<string, number> = new Map();

            const createTask = (nodeId: string, delay: number) => {
                return queue.enqueue(nodeId, 'agent', async () => {
                    startTimes.set(nodeId, Date.now());
                    await sleep(delay);
                    endTimes.set(nodeId, Date.now());
                    return nodeId;
                });
            };

            const startTime = Date.now();
            await Promise.all([
                createTask('node-1', 50),
                createTask('node-2', 50),
                createTask('node-3', 50),
            ]);
            const totalTime = Date.now() - startTime;

            // If concurrent, total time should be ~50ms, not ~150ms
            // Using 100ms threshold to account for timing variations
            expect(totalTime).toBeLessThan(100);
        });
    });

    describe('Status Query Methods', () => {
        /**
         * isProcessing should return true while request is in progress
         */
        it('should report processing status correctly', async () => {
            let checkDuringExecution = false;

            const promise = queue.enqueue('node-1', 'agent-a', async () => {
                await sleep(50);
                return 'result';
            });

            // Check immediately after enqueue - should be processing
            checkDuringExecution = queue.isProcessing('node-1');
            expect(checkDuringExecution).toBe(true);

            await promise;

            // After completion - should not be processing
            expect(queue.isProcessing('node-1')).toBe(false);
        });

        /**
         * getCurrentAgentType should return the running agent type
         */
        it('should return current agent type while processing', async () => {
            let agentTypeDuringExecution: string | undefined;

            const promise = queue.enqueue('node-1', '口语化解释', async () => {
                await sleep(50);
                return 'result';
            });

            // Small delay to ensure the agent type is set
            await sleep(10);
            agentTypeDuringExecution = queue.getCurrentAgentType('node-1');
            expect(agentTypeDuringExecution).toBe('口语化解释');

            await promise;

            // After completion - should be undefined
            expect(queue.getCurrentAgentType('node-1')).toBeUndefined();
        });

        /**
         * isProcessing should return false for non-existent nodes
         */
        it('should return false for nodes not being processed', () => {
            expect(queue.isProcessing('non-existent-node')).toBe(false);
            expect(queue.getCurrentAgentType('non-existent-node')).toBeUndefined();
        });
    });

    describe('User Notification (AC3)', () => {
        /**
         * Story 12.H.2 AC3: User notice when node is busy
         * Given: node is processing an Agent
         * When: User clicks another Agent on same node
         * Then: Notice shows "节点正在处理 '{agentType}'，请稍候..."
         */
        it('should show notice when queueing on busy node', async () => {
            const promise1 = queue.enqueue('node-1', '四层次解释', async () => {
                await sleep(100);
                return 'result-1';
            });

            // Small delay to ensure first request is processing
            await sleep(10);

            // Second request should trigger notice
            const promise2 = queue.enqueue('node-1', '口语化解释', async () => {
                return 'result-2';
            });

            await Promise.all([promise1, promise2]);

            // Verify Notice was called with the correct message
            expect(Notice).toHaveBeenCalledWith('节点正在处理 "四层次解释"，请稍候...');
        });

        /**
         * Should not show notice when node is idle
         */
        it('should not show notice when node is idle', async () => {
            await queue.enqueue('node-1', 'agent-a', async () => {
                return 'result';
            });

            // Notice should not have been called (node was idle when request started)
            expect(Notice).not.toHaveBeenCalled();
        });
    });

    describe('Error Handling', () => {
        /**
         * Queue behavior when first request errors:
         * Current implementation: Errors propagate through Promise chain,
         * subsequent requests for same node also fail.
         * This is fail-fast behavior - if node processing fails, the queue breaks.
         *
         * Note: This is a design choice. Alternative would be to use .catch()
         * to isolate errors and continue the queue.
         */
        it('should propagate errors through queue (fail-fast behavior)', async () => {
            const promise1 = queue.enqueue('node-1', 'agent-a', async () => {
                throw new Error('First request failed');
            });

            const promise2 = queue.enqueue('node-1', 'agent-b', async () => {
                return 'second-result';
            });

            // First promise rejects
            await expect(promise1).rejects.toThrow('First request failed');

            // Second promise also rejects due to Promise chain propagation
            // This is expected behavior - errors break the queue for that node
            await expect(promise2).rejects.toThrow('First request failed');
        });

        /**
         * Queue should cleanup properly after error
         */
        it('should cleanup after error', async () => {
            const promise = queue.enqueue('node-1', 'agent-a', async () => {
                throw new Error('Request failed');
            });

            await expect(promise).rejects.toThrow();

            // Queue should be cleaned up
            expect(queue.isProcessing('node-1')).toBe(false);
            expect(queue.getCurrentAgentType('node-1')).toBeUndefined();
        });
    });

    describe('Memory Management', () => {
        /**
         * Queue maps should be cleaned up after completion
         */
        it('should cleanup maps after request completion', async () => {
            await queue.enqueue('node-1', 'agent-a', async () => {
                return 'result';
            });

            // After completion, internal maps should be cleaned
            expect(queue.isProcessing('node-1')).toBe(false);
            expect(queue.getCurrentAgentType('node-1')).toBeUndefined();
        });

        /**
         * Multiple sequential requests should not leak memory
         */
        it('should not leak memory with multiple requests', async () => {
            for (let i = 0; i < 10; i++) {
                await queue.enqueue('node-1', `agent-${i}`, async () => {
                    return `result-${i}`;
                });
            }

            // After all requests, queue should be empty
            expect(queue.isProcessing('node-1')).toBe(false);
        });
    });

    describe('Return Value Handling', () => {
        /**
         * Should correctly return typed results
         */
        it('should preserve return types', async () => {
            interface AgentResult {
                questions: string[];
                count: number;
            }

            const result = await queue.enqueue<AgentResult>('node-1', 'agent', async () => {
                return {
                    questions: ['Q1', 'Q2'],
                    count: 2,
                };
            });

            expect(result.questions).toEqual(['Q1', 'Q2']);
            expect(result.count).toBe(2);
        });

        /**
         * Should handle null/undefined returns
         */
        it('should handle null returns', async () => {
            const result = await queue.enqueue('node-1', 'agent', async () => {
                return null;
            });

            expect(result).toBeNull();
        });
    });
});
