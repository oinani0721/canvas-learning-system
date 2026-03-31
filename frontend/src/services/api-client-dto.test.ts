/**
 * Tests for TipItem and WeaknessItem DTO interfaces.
 * Feature 1.1: Verify sourceCanvasId and sourceNodeId optional fields
 * exist on both interfaces for Profile Click-to-Jump navigation.
 */
import { describe, it, expect } from 'vitest';
import type { TipItem, WeaknessItem } from './api-client';
import type { TipItem as TipItemTypes } from '../types';

describe('TipItem (api-client)', () => {
  it('accepts object without optional source fields (backward compat)', () => {
    const tip: TipItem = {
      tipId: 'tip-001',
      content: 'Review spaced repetition',
      category: 'study-technique',
      annotatedAt: '2026-03-30T10:00:00Z',
      contextMessages: ['msg-1'],
    };
    expect(tip.tipId).toBe('tip-001');
    expect(tip.sourceCanvasId).toBeUndefined();
    expect(tip.sourceNodeId).toBeUndefined();
  });

  it('accepts sourceCanvasId and sourceNodeId optional fields', () => {
    const tip: TipItem = {
      tipId: 'tip-002',
      content: 'Focus on weak areas',
      category: 'strategy',
      annotatedAt: '2026-03-30T11:00:00Z',
      contextMessages: [],
      sourceCanvasId: 'canvas-abc',
      sourceNodeId: 'node-xyz',
    };
    expect(tip.sourceCanvasId).toBe('canvas-abc');
    expect(tip.sourceNodeId).toBe('node-xyz');
  });
});

describe('WeaknessItem (api-client)', () => {
  it('accepts object without optional source fields (backward compat)', () => {
    const weakness: WeaknessItem = {
      direction: 'forward',
      frequency: 3,
      lastSeen: '2026-03-29T09:00:00Z',
      relatedExamSummaries: ['exam-1'],
    };
    expect(weakness.direction).toBe('forward');
    expect(weakness.sourceCanvasId).toBeUndefined();
    expect(weakness.sourceNodeId).toBeUndefined();
  });

  it('accepts sourceCanvasId and sourceNodeId optional fields', () => {
    const weakness: WeaknessItem = {
      direction: 'reverse',
      frequency: 5,
      lastSeen: null,
      relatedExamSummaries: [],
      sourceCanvasId: 'canvas-def',
      sourceNodeId: 'node-uvw',
    };
    expect(weakness.sourceCanvasId).toBe('canvas-def');
    expect(weakness.sourceNodeId).toBe('node-uvw');
  });
});

describe('TipItem (types.ts)', () => {
  it('accepts object without optional source fields (backward compat)', () => {
    const tip: TipItemTypes = {
      tipId: 'tip-003',
      content: 'Use active recall',
      category: 'technique',
      annotatedAt: '2026-03-30T12:00:00Z',
      contextMessages: ['msg-a'],
    };
    expect(tip.tipId).toBe('tip-003');
    expect(tip.sourceCanvasId).toBeUndefined();
    expect(tip.sourceNodeId).toBeUndefined();
  });

  it('accepts sourceCanvasId and sourceNodeId optional fields', () => {
    const tip: TipItemTypes = {
      tipId: 'tip-004',
      content: 'Interleave topics',
      category: 'strategy',
      annotatedAt: '2026-03-30T13:00:00Z',
      contextMessages: [],
      sourceCanvasId: 'canvas-ghi',
      sourceNodeId: 'node-rst',
    };
    expect(tip.sourceCanvasId).toBe('canvas-ghi');
    expect(tip.sourceNodeId).toBe('node-rst');
  });
});
