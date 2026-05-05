/**
 * Story 2.5.X Task 7 — Error candidate helpers (testable pure functions).
 *
 * 与 main.ts 解耦的 candidate 过滤 + payload 构造逻辑.
 * Modal class 仍在 main.ts (使用 Obsidian API).
 *
 * Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md
 */

export interface ErrorCandidate {
  id: string;
  status: string;
  description?: string;
  pedagogy_type?: string;
  legacy_type?: string;
  confidence?: number;
  seen_count?: number;
  last_seen_at?: string;
  context?: string;
  ai_reason?: string | null;
}

export interface AcceptCandidatePayload {
  candidate_id: string;
  node_id: string;
  session_id: string;
  user_edits?: {
    description?: string;
    pedagogy_type?: string;
    legacy_type?: string;
  };
  fire_and_forget_graphiti?: boolean;
}

export interface DismissCandidatePayload {
  candidate_id: string;
  node_id: string;
}

export interface DisputeCandidatePayload {
  candidate_id: string;
  node_id: string;
  dispute_reason: string;
}

/**
 * Story 2.5.X AC #2 — 仅过滤 status="pending" 的候选 (active state).
 *
 * 终态 (accepted/edited/dismissed/disputed/expired) 不应再操作.
 */
export function filterPendingCandidates(
  candidates: unknown,
): ErrorCandidate[] {
  if (!Array.isArray(candidates)) {
    return [];
  }
  return candidates.filter(
    (c): c is ErrorCandidate =>
      typeof c === "object" &&
      c !== null &&
      typeof (c as ErrorCandidate).id === "string" &&
      ((c as ErrorCandidate).status ?? "pending") === "pending",
  );
}

/**
 * Story 2.5.X Task 7 — 构造 candidate 简短显示文本 (Modal 列表用).
 *
 * 格式: "[icon] description (pedagogy_type, conf=X.XX, seen=N)"
 * - icon: 🟢≥0.8 / 🟡≥0.6 / 🔴<0.6
 */
export function formatCandidateLabel(c: ErrorCandidate): string {
  const desc = (c.description ?? "(无描述)").slice(0, 60);
  const pt = c.pedagogy_type ?? "—";
  const conf = typeof c.confidence === "number" ? c.confidence : 0.5;
  const icon = conf >= 0.8 ? "🟢" : conf >= 0.6 ? "🟡" : "🔴";
  const seen = c.seen_count ?? 1;
  return `${icon} ${desc} (${pt}, conf=${conf.toFixed(2)}, seen=${seen})`;
}

/**
 * Story 2.5.X Task 7 — 构造 accept-candidate POST body.
 *
 * user_edits 为 null/undefined 时 → status=accepted (server side).
 * 含 user_edits 时 → status=edited.
 */
export function buildAcceptPayload(
  candidateId: string,
  nodeId: string,
  options: {
    sessionId?: string;
    userEdits?: AcceptCandidatePayload["user_edits"];
    fireAndForgetGraphiti?: boolean;
  } = {},
): AcceptCandidatePayload {
  const payload: AcceptCandidatePayload = {
    candidate_id: candidateId,
    node_id: nodeId,
    session_id: options.sessionId ?? "",
  };
  if (options.userEdits) {
    payload.user_edits = options.userEdits;
  }
  if (typeof options.fireAndForgetGraphiti === "boolean") {
    payload.fire_and_forget_graphiti = options.fireAndForgetGraphiti;
  }
  return payload;
}

export function buildDismissPayload(
  candidateId: string,
  nodeId: string,
): DismissCandidatePayload {
  return {
    candidate_id: candidateId,
    node_id: nodeId,
  };
}

export function buildDisputePayload(
  candidateId: string,
  nodeId: string,
  disputeReason: string,
): DisputeCandidatePayload {
  return {
    candidate_id: candidateId,
    node_id: nodeId,
    dispute_reason: disputeReason,
  };
}

/**
 * Story 2.5.X Task 7 — 校验 dispute_reason (空白被拒).
 */
export function validateDisputeReason(reason: string): {
  valid: boolean;
  error?: string;
} {
  if (!reason) {
    return { valid: false, error: "dispute_reason 不能为空" };
  }
  if (!reason.trim()) {
    return { valid: false, error: "dispute_reason 不能全为空白" };
  }
  return { valid: true };
}
