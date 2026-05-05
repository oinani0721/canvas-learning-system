/**
 * Story 2.5.X Task 7 — Error candidate helper tests (node:test 兼容).
 *
 * 跑命令: cd frontend/obsidian-plugin && npm test
 */

import assert from "node:assert";
import { describe, test } from "node:test";
import {
  buildAcceptPayload,
  buildDismissPayload,
  buildDisputePayload,
  type ErrorCandidate,
  filterPendingCandidates,
  formatCandidateLabel,
  validateDisputeReason,
} from "../src/error-candidate-helpers";

describe("filterPendingCandidates", () => {
  test("returns empty array for non-array input", () => {
    assert.deepEqual(filterPendingCandidates(undefined), []);
    assert.deepEqual(filterPendingCandidates(null), []);
    assert.deepEqual(filterPendingCandidates("not array"), []);
    assert.deepEqual(filterPendingCandidates({}), []);
  });

  test("filters only status=pending candidates", () => {
    const cands = [
      { id: "1", status: "pending", description: "a" },
      { id: "2", status: "accepted", description: "b" },
      { id: "3", status: "dismissed", description: "c" },
      { id: "4", status: "pending", description: "d" },
      { id: "5", status: "expired", description: "e" },
    ];
    const result = filterPendingCandidates(cands);
    assert.deepEqual(
      result.map((c) => c.id),
      ["1", "4"],
    );
  });

  test("treats missing status as pending (frontmatter 兼容)", () => {
    const cands = [
      { id: "1", description: "a" },
      { id: "2", status: "accepted", description: "b" },
    ];
    const result = filterPendingCandidates(cands);
    assert.deepEqual(
      result.map((c) => c.id),
      ["1"],
    );
  });

  test("rejects malformed candidates (no id)", () => {
    const cands = [
      { status: "pending", description: "no id" },
      { id: "valid", status: "pending", description: "ok" },
    ];
    const result = filterPendingCandidates(cands);
    assert.deepEqual(
      result.map((c) => c.id),
      ["valid"],
    );
  });
});

describe("formatCandidateLabel", () => {
  const baseC: ErrorCandidate = {
    id: "x",
    status: "pending",
    description: "学生混淆 admissibility 与 consistency",
    pedagogy_type: "conceptual_confusion",
    confidence: 0.85,
    seen_count: 2,
  };

  test("uses 🟢 for confidence >= 0.8", () => {
    const label = formatCandidateLabel({ ...baseC, confidence: 0.9 });
    assert.ok(label.includes("🟢"));
  });

  test("uses 🟡 for confidence >= 0.6 and < 0.8", () => {
    const label = formatCandidateLabel({ ...baseC, confidence: 0.7 });
    assert.ok(label.includes("🟡"));
  });

  test("uses 🔴 for confidence < 0.6", () => {
    const label = formatCandidateLabel({ ...baseC, confidence: 0.4 });
    assert.ok(label.includes("🔴"));
  });

  test("includes pedagogy_type, confidence, seen_count", () => {
    const label = formatCandidateLabel(baseC);
    assert.ok(label.includes("conceptual_confusion"));
    assert.ok(label.includes("0.85"));
    assert.ok(label.includes("seen=2"));
  });

  test("truncates description to 60 chars", () => {
    const long = "z".repeat(100);  // 用 'z' 避免与其他字段冲突 (pedagogy_type 含 'a' 等)
    const label = formatCandidateLabel({ ...baseC, description: long });
    const zCount = (label.match(/z/g) || []).length;
    assert.equal(zCount, 60, `expected exactly 60 'z' chars, got ${zCount}`);
  });

  test("falls back to '(无描述)' when description missing", () => {
    const label = formatCandidateLabel({ id: "x", status: "pending" });
    assert.ok(label.includes("(无描述)"));
  });
});

describe("buildAcceptPayload", () => {
  test("constructs minimal payload without edits", () => {
    const p = buildAcceptPayload("cand-1", "节点/x.md");
    assert.deepEqual(p, {
      candidate_id: "cand-1",
      node_id: "节点/x.md",
      session_id: "",
    });
    assert.equal(p.user_edits, undefined);
  });

  test("includes user_edits when provided", () => {
    const p = buildAcceptPayload("cand-1", "节点/x.md", {
      userEdits: { description: "修改后" },
    });
    assert.deepEqual(p.user_edits, { description: "修改后" });
  });

  test("includes session_id when provided", () => {
    const p = buildAcceptPayload("cand-1", "节点/x.md", {
      sessionId: "s-2026-05-05-001",
    });
    assert.equal(p.session_id, "s-2026-05-05-001");
  });

  test("includes fire_and_forget_graphiti when explicitly set", () => {
    const p = buildAcceptPayload("cand-1", "节点/x.md", {
      fireAndForgetGraphiti: false,
    });
    assert.equal(p.fire_and_forget_graphiti, false);
  });
});

describe("buildDismissPayload", () => {
  test("constructs minimal dismiss payload", () => {
    const p = buildDismissPayload("cand-1", "节点/x.md");
    assert.deepEqual(p, {
      candidate_id: "cand-1",
      node_id: "节点/x.md",
    });
  });
});

describe("buildDisputePayload", () => {
  test("constructs dispute payload with reason", () => {
    const p = buildDisputePayload("cand-1", "节点/x.md", "我没误解");
    assert.deepEqual(p, {
      candidate_id: "cand-1",
      node_id: "节点/x.md",
      dispute_reason: "我没误解",
    });
  });
});

describe("validateDisputeReason", () => {
  test("accepts non-empty trimmed reason", () => {
    const r = validateDisputeReason("我没误解");
    assert.equal(r.valid, true);
  });

  test("rejects empty string", () => {
    const r = validateDisputeReason("");
    assert.equal(r.valid, false);
    assert.ok(r.error?.includes("不能为空"));
  });

  test("rejects whitespace-only string", () => {
    const r = validateDisputeReason("   \n\t  ");
    assert.equal(r.valid, false);
    assert.ok(r.error?.includes("空白"));
  });
});
