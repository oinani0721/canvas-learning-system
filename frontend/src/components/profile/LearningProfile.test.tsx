/**
 * Tests for LearningProfile click-to-jump navigation (Feature 1.3).
 *
 * Verifies:
 * - Tips/weaknesses with sourceCanvasId render a navigate button
 * - Tips/weaknesses without sourceCanvasId do NOT render a navigate button
 * - Clicking navigate button calls onNavigateToSource with correct args
 * - Items without sourceCanvasId do not crash on click
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { LearningProfile } from './LearningProfile';
import type { ProfileSummary, TipItem, WeaknessItem } from '../../services/api-client';

// --- Test fixtures ---

const baseSummary: ProfileSummary = {
  conceptId: 'node-1',
  name: 'Test Concept',
  masteryLevel: 3,
  masteryLabel: 'Learning',
  masteryColor: '#fbbf24',
  effectiveProficiency: 0.45,
  prescriptiveMessage: 'Keep practicing!',
  interactionCount: 5,
  examCount: 2,
  lastExamDate: '2026-03-28T10:00:00Z',
  fsrsDueDate: null,
  freshness: 'fresh',
};

const tipWithSource: TipItem = {
  tipId: 'tip-with-source',
  content: 'Remember to review flashcards daily',
  category: 'study-technique',
  annotatedAt: '2026-03-29T10:00:00Z',
  contextMessages: [],
  sourceCanvasId: 'canvas-abc',
  sourceNodeId: 'node-xyz',
};

const tipWithoutSource: TipItem = {
  tipId: 'tip-no-source',
  content: 'Practice active recall',
  category: 'strategy',
  annotatedAt: '2026-03-29T11:00:00Z',
  contextMessages: [],
};

const weaknessWithSource: WeaknessItem = {
  direction: 'Needs more graph theory practice',
  frequency: 4,
  lastSeen: '2026-03-28T09:00:00Z',
  relatedExamSummaries: [],
  sourceCanvasId: 'canvas-def',
  sourceNodeId: 'node-uvw',
};

const weaknessWithoutSource: WeaknessItem = {
  direction: 'Review recursion concepts',
  frequency: 2,
  lastSeen: '2026-03-27T09:00:00Z',
  relatedExamSummaries: [],
};

// --- Mock setup ---

function mockFetchResponses(tips: TipItem[], weaknesses: WeaknessItem[]) {
  global.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/summary')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(baseSummary),
      });
    }
    if (url.includes('/tips')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ tips, total: tips.length }),
      });
    }
    if (url.includes('/weaknesses')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ weaknesses, total: weaknesses.length }),
      });
    }
    if (url.includes('/qa-highlights')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ clusters: [], total: 0 }),
      });
    }
    return Promise.resolve({ ok: false });
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('LearningProfile click-to-jump navigation', () => {
  it('renders navigate button for tip with sourceCanvasId', async () => {
    mockFetchResponses([tipWithSource], []);

    render(
      <LearningProfile
        nodeId="node-1"
        nodeTitle="Test"
        backendUrl="http://localhost:8001"
        onNavigateToSource={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText(/Review flashcards daily/i)).toBeInTheDocument();
    });

    const navButtons = screen.getAllByLabelText('Navigate to source');
    expect(navButtons.length).toBe(1);
  });

  it('does not render navigate button for tip without sourceCanvasId', async () => {
    mockFetchResponses([tipWithoutSource], []);

    render(
      <LearningProfile
        nodeId="node-1"
        nodeTitle="Test"
        backendUrl="http://localhost:8001"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText(/Practice active recall/i)).toBeInTheDocument();
    });

    expect(screen.queryAllByLabelText('Navigate to source')).toHaveLength(0);
  });

  it('calls onNavigateToSource when navigate button is clicked on a tip', async () => {
    const onNavigate = vi.fn();
    mockFetchResponses([tipWithSource], []);

    render(
      <LearningProfile
        nodeId="node-1"
        nodeTitle="Test"
        backendUrl="http://localhost:8001"
        onNavigateToSource={onNavigate}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText(/Review flashcards daily/i)).toBeInTheDocument();
    });

    const navButton = screen.getByLabelText('Navigate to source');
    await userEvent.click(navButton);

    expect(onNavigate).toHaveBeenCalledTimes(1);
    expect(onNavigate).toHaveBeenCalledWith('canvas-abc', 'node-xyz');
  });

  it('renders navigate button for weakness with sourceCanvasId', async () => {
    mockFetchResponses([], [weaknessWithSource]);

    render(
      <LearningProfile
        nodeId="node-1"
        nodeTitle="Test"
        backendUrl="http://localhost:8001"
        onNavigateToSource={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/Needs more graph theory practice/i),
      ).toBeInTheDocument();
    });

    const navButtons = screen.getAllByLabelText('Navigate to source');
    expect(navButtons.length).toBe(1);
  });

  it('does not render navigate button for weakness without sourceCanvasId', async () => {
    mockFetchResponses([], [weaknessWithoutSource]);

    render(
      <LearningProfile
        nodeId="node-1"
        nodeTitle="Test"
        backendUrl="http://localhost:8001"
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/Review recursion concepts/i),
      ).toBeInTheDocument();
    });

    expect(screen.queryAllByLabelText('Navigate to source')).toHaveLength(0);
  });

  it('items without sourceCanvasId do not crash on click', async () => {
    mockFetchResponses([tipWithoutSource], [weaknessWithoutSource]);

    render(
      <LearningProfile
        nodeId="node-1"
        nodeTitle="Test"
        backendUrl="http://localhost:8001"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText(/Practice active recall/i)).toBeInTheDocument();
    });

    // Click the tip expand button — should not throw
    const tipButton = screen.getByText(/Practice active recall/i).closest('button')!;
    await userEvent.click(tipButton);

    // Click the weakness expand button — should not throw
    const weaknessButton = screen.getByText(/Review recursion concepts/i).closest('button')!;
    await userEvent.click(weaknessButton);

    // If we got here without throwing, the test passes
    expect(true).toBe(true);
  });
});
