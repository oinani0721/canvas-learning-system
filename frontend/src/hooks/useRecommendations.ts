import { useState, useEffect, useCallback, useRef } from 'react';
import type { Node, Edge } from '@xyflow/react';
import type { Recommendation } from '../services/api-client';
import { ApiClient } from '../services/api-client';
import { createLogger } from '../services/logger';

const SETTINGS_KEY = 'canvas-learning-settings';
const DEBOUNCE_MS = 5000;
const MIN_NODES = 5;

const logger = createLogger('Recommendations');

interface UseRecommendationsInput {
  boardId: string | null;
  nodes: Node[];
  edges: Edge[];
  apiClient: ApiClient;
}

interface UseRecommendationsResult {
  recommendations: Recommendation[];
  loading: boolean;
  accept: (rec: Recommendation) => void;
  dismiss: (rec: Recommendation) => void;
}

function isEnabled(): boolean {
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as { enableRecommendations?: boolean };
      return parsed.enableRecommendations === true;
    }
  } catch { /* ignore */ }
  return false;
}

/** Creates a normalized pair key so A↔B and B↔A are the same. */
function pairKey(a: string, b: string): string {
  return a < b ? `${a}:${b}` : `${b}:${a}`;
}

/** Finds nodes that have no edges connecting them to any other node. */
function hasUnconnectedNodes(nodes: Node[], edges: Edge[]): boolean {
  const connected = new Set<string>();
  for (const e of edges) {
    connected.add(e.source);
    connected.add(e.target);
  }
  return nodes.some((n) => !connected.has(n.id));
}

export function useRecommendations({
  boardId,
  nodes,
  edges,
  apiClient,
}: UseRecommendationsInput): UseRecommendationsResult {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const dismissedRef = useRef<Set<string>>(new Set());

  // Read enabled state on every render so view transitions pick up changes
  const enabled = isEnabled();

  // Fetch recommendations with debounce
  useEffect(() => {
    if (!enabled) {
      logger.debug('skipped: toggle off');
      setRecommendations([]);
      return;
    }
    if (!boardId) {
      logger.debug('skipped: no boardId');
      setRecommendations([]);
      return;
    }
    if (nodes.length < MIN_NODES) {
      logger.debug('skipped: not enough nodes', { count: nodes.length, min: MIN_NODES });
      setRecommendations([]);
      return;
    }
    if (!hasUnconnectedNodes(nodes, edges)) {
      logger.debug('skipped: all nodes connected');
      setRecommendations([]);
      return;
    }

    logger.debug('debounce started', { debounceMs: DEBOUNCE_MS, boardId, nodeCount: nodes.length });

    const timer = setTimeout(() => {
      setLoading(true);

      const dismissedPairs = Array.from(dismissedRef.current).map((key) => {
        const [nodeIdA, nodeIdB] = key.split(':');
        return { nodeIdA, nodeIdB };
      });

      logger.debug('fetching', { boardId, dismissedCount: dismissedPairs.length });

      apiClient
        .fetchRecommendations(boardId, dismissedPairs)
        .then((resp) => {
          const filtered = resp.recommendations.filter(
            (r) => !dismissedRef.current.has(pairKey(r.sourceNodeId, r.targetNodeId)),
          );
          logger.debug('received', { total: resp.recommendations.length, afterFilter: filtered.length });
          setRecommendations(filtered);
        })
        .finally(() => {
          setLoading(false);
        });
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [enabled, boardId, nodes.length, edges.length, apiClient]);

  const accept = useCallback((rec: Recommendation) => {
    setRecommendations((prev) => prev.filter((r) => r.id !== rec.id));
  }, []);

  const dismiss = useCallback((rec: Recommendation) => {
    dismissedRef.current.add(pairKey(rec.sourceNodeId, rec.targetNodeId));
    setRecommendations((prev) => prev.filter((r) => r.id !== rec.id));
  }, []);

  return { recommendations, loading, accept, dismiss };
}
