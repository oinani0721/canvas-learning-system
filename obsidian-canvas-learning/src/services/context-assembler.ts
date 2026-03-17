/**
 * Canvas Learning System - Context Assembler
 * Story 3.4: Learning Context Auto-Injection (AC-1, AC-2, AC-4)
 *
 * Assembles the learning context for a canvas node into a structured Markdown
 * string suitable for injection via `--append-system-prompt`.
 *
 * Three-tier context architecture:
 *   Tier 1: Current node full context (Tips, errors, mastery)
 *   Tier 2: Adjacent node summaries (1-hop neighbors from graph)
 *   Tier 3: Remote context via MCP search_memories (not preloaded)
 *
 * Token budget: Tier 1 + Tier 2 < 4K tokens (~16K chars conservative estimate).
 *
 * [Source: _bmad-output/implementation-artifacts/3-4-learning-context-auto-injection.md#Task 1]
 */

import type { ApiClient } from './api-client';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

/** Tier 1 context: full data for the current node. */
interface Tier1Context {
  nodeName: string;
  mastery: {
    pMastery: number | null;
    stability: number | null;
    nextReview: string | null;
  };
  tips: Array<{
    content: string;
    category: string;
    annotatedAt: string;
  }>;
  errors: Array<{
    errorType: string;
    description: string;
    remedy: string;
  }>;
  edgeReasons: Array<{
    neighborName: string;
    reason: string;
  }>;
}

/** Tier 2 context: summary data for adjacent nodes. */
interface Tier2Context {
  neighbors: Array<{
    name: string;
    masteryLevel: number | null;
    edgeReason: string;
  }>;
}

/** Full context response from the backend API. */
interface ContextApiResponse {
  nodeId: string;
  nodeName: string;
  tier1: Tier1Context;
  tier2: Tier2Context;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Token Budget Constants
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Approximate char budget. 4K tokens ~ 16K chars for CJK text.
 * Using a conservative ratio of 4 chars/token for mixed CJK+English.
 */
const MAX_CONTEXT_CHARS = 16_000;

/** Reserve ratio for Tier 1 vs Tier 2. Tier 1 gets priority. */
const TIER1_RATIO = 0.7;

// ═══════════════════════════════════════════════════════════════════════════════
// Context Assembler
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Assembles learning context for injection into Claude Code's system prompt.
 *
 * Story 3.4 AC-1: Context injected via --append-system-prompt
 * Story 3.4 AC-2: Three-tier management (Tier 1 full, Tier 2 summary, Tier 3 on-demand)
 * Story 3.4 AC-4: Re-assembled on every sendMessage (always fresh)
 */
export class ContextAssembler {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /**
   * Assemble the full context string for a node.
   *
   * Called before every sendMessage to ensure freshness (AC-4).
   * Returns an empty string for nodes with no learning history.
   *
   * @param nodeId - The canvas node identifier.
   * @returns Structured Markdown context string.
   */
  async assembleContext(nodeId: string): Promise<string> {
    let contextData: ContextApiResponse;
    try {
      contextData = await this.apiClient.get<ContextApiResponse>(
        `/api/v1/context/${encodeURIComponent(nodeId)}`,
      );
    } catch (err) {
      console.warn(
        `[Canvas Learning] ContextAssembler: failed to fetch context for node "${nodeId}":`,
        err,
      );
      return '';
    }

    const tier1Md = this.formatTier1(contextData.tier1);
    const tier2Md = this.formatTier2(contextData.tier2);

    // Token budget enforcement
    const combined = this.enforceTokenBudget(tier1Md, tier2Md);
    return combined;
  }

  /**
   * Format Tier 1 context into Markdown.
   *
   * Handles empty data gracefully: sections with no data are omitted.
   */
  private formatTier1(tier1: Tier1Context): string {
    const sections: string[] = [];

    // Node header
    sections.push(`## 当前节点：${tier1.nodeName}`);

    // Mastery section
    if (
      tier1.mastery.pMastery !== null ||
      tier1.mastery.stability !== null ||
      tier1.mastery.nextReview !== null
    ) {
      const lines = ['### 精通度'];
      if (tier1.mastery.pMastery !== null) {
        lines.push(`- BKT掌握概率: ${(tier1.mastery.pMastery * 100).toFixed(1)}%`);
      }
      if (tier1.mastery.stability !== null) {
        lines.push(`- FSRS记忆稳定性: ${tier1.mastery.stability.toFixed(1)}`);
      }
      if (tier1.mastery.nextReview) {
        lines.push(`- 下次复习: ${tier1.mastery.nextReview}`);
      }
      sections.push(lines.join('\n'));
    }

    // Tips section
    if (tier1.tips.length > 0) {
      const lines = ['### 关键笔记 (Tips)'];
      for (const tip of tier1.tips) {
        lines.push(`- [${tip.category}] ${tip.content}`);
      }
      sections.push(lines.join('\n'));
    }

    // Errors section
    if (tier1.errors.length > 0) {
      const lines = ['### 历史错误'];
      for (const err of tier1.errors) {
        lines.push(`- [${err.errorType}] ${err.description} → 建议: ${err.remedy}`);
      }
      sections.push(lines.join('\n'));
    }

    // Edge reasons
    if (tier1.edgeReasons.length > 0) {
      const lines = ['### 连线理由'];
      for (const edge of tier1.edgeReasons) {
        lines.push(`- ${edge.neighborName}: ${edge.reason}`);
      }
      sections.push(lines.join('\n'));
    }

    return sections.join('\n\n');
  }

  /**
   * Format Tier 2 context into Markdown.
   */
  private formatTier2(tier2: Tier2Context): string {
    if (tier2.neighbors.length === 0) return '';

    const lines = ['### 相关节点'];
    for (const n of tier2.neighbors) {
      const mastery =
        n.masteryLevel !== null ? `精通度: ${(n.masteryLevel * 100).toFixed(0)}%` : '未评估';
      lines.push(`- ${n.name}: ${n.edgeReason} (${mastery})`);
    }

    return lines.join('\n');
  }

  /**
   * Enforce token budget: Tier 1 + Tier 2 must fit within MAX_CONTEXT_CHARS.
   * If over budget, Tier 2 is truncated first.
   */
  private enforceTokenBudget(tier1: string, tier2: string): string {
    if (!tier1 && !tier2) return '';

    const total = tier1.length + tier2.length;
    if (total <= MAX_CONTEXT_CHARS) {
      return tier2 ? `${tier1}\n\n${tier2}` : tier1;
    }

    // Over budget: prioritize Tier 1
    const tier1Budget = Math.floor(MAX_CONTEXT_CHARS * TIER1_RATIO);
    const truncatedTier1 =
      tier1.length > tier1Budget ? tier1.slice(0, tier1Budget) + '\n...(截断)' : tier1;

    const remaining = MAX_CONTEXT_CHARS - truncatedTier1.length;
    if (remaining <= 0 || !tier2) return truncatedTier1;

    const truncatedTier2 =
      tier2.length > remaining ? tier2.slice(0, remaining) + '\n...(截断)' : tier2;

    return `${truncatedTier1}\n\n${truncatedTier2}`;
  }
}
