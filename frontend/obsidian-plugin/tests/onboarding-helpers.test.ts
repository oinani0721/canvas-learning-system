/**
 * Round-23 Phase B0.3 onboarding helpers tests.
 *
 * ChatGPT Deep Research P1 fix (2026-05-11): 补 a4c1d95 缺失的 onboarding 测试。
 * 测试粒度: 纯函数级（buildOnboardingYaml / validateOnboardingInput /
 * shouldTriggerOnboarding）— 不 mock 整个 Plugin/Vault（成本过高），让决策逻辑
 * 与 IO 分离后独立可测。
 *
 * 跑命令: cd frontend/obsidian-plugin && npm test
 */

import assert from "node:assert";
import { describe, test } from "node:test";
import {
  buildOnboardingYaml,
  shouldTriggerOnboarding,
  validateOnboardingInput,
} from "../src/onboarding-helpers";

// ─────────────────────────────────────────────────────────────
// shouldTriggerOnboarding — 决策与 IO 分离的核心
// ─────────────────────────────────────────────────────────────

describe("shouldTriggerOnboarding", () => {
  test("returns true when config does not exist", () => {
    assert.strictEqual(shouldTriggerOnboarding(false), true);
  });

  test("returns false when config exists (skip onboarding)", () => {
    assert.strictEqual(shouldTriggerOnboarding(true), false);
  });
});

// ─────────────────────────────────────────────────────────────
// validateOnboardingInput — 表单合法性
// ─────────────────────────────────────────────────────────────

describe("validateOnboardingInput", () => {
  test("accepts non-empty displayName + empty subject (走 general)", () => {
    const r = validateOnboardingInput("CS 61B", "");
    assert.strictEqual(r.valid, true);
    assert.strictEqual(r.error, undefined);
  });

  test("accepts displayName + subject 都非空", () => {
    const r = validateOnboardingInput("CS 61B 数据结构", "cs-61b");
    assert.strictEqual(r.valid, true);
  });

  test("rejects empty displayName", () => {
    const r = validateOnboardingInput("", "cs-61b");
    assert.strictEqual(r.valid, false);
    assert.ok(r.error?.includes("不能为空"));
  });

  test("rejects displayName 只含空白", () => {
    const r = validateOnboardingInput("   ", "cs-61b");
    assert.strictEqual(r.valid, false);
    assert.ok(r.error?.includes("空白"));
  });

  test("accepts 中文 displayName (Phase B0.1 sanitize 已支持)", () => {
    const r = validateOnboardingInput("数学 101", "math-101");
    assert.strictEqual(r.valid, true);
  });
});

// ─────────────────────────────────────────────────────────────
// buildOnboardingYaml — schema v2 输出格式
// ─────────────────────────────────────────────────────────────

const FIXED_TS = "2026-05-11T17:00:00.000Z";

describe("buildOnboardingYaml", () => {
  test("生成含必需字段的 yaml (vault_id / display_name / subject / schema_version)", () => {
    const yaml = buildOnboardingYaml("cs_61b", "CS 61B 数据结构", "cs-61b", FIXED_TS);
    assert.ok(yaml.includes('vault_id: "cs_61b"'));
    assert.ok(yaml.includes('vault_display_name: "CS 61B 数据结构"'));
    assert.ok(yaml.includes("subject: cs-61b"));
    assert.ok(yaml.includes('schema_version: "2.0-multi-vault-2026-05-10"'));
    assert.ok(yaml.includes(`created_at: "${FIXED_TS}"`));
  });

  test("subject 留空 → 走 'general' fallback", () => {
    const yaml = buildOnboardingYaml("数学101", "数学 101", "", FIXED_TS);
    assert.ok(yaml.includes('vault_id: "数学101"'));
    assert.ok(yaml.includes("subject: general"));
  });

  test("含 deprecated_paths section (Skill 不再写入)", () => {
    const yaml = buildOnboardingYaml("test", "Test", "general", FIXED_TS);
    assert.ok(yaml.includes("deprecated_paths:"));
    assert.ok(yaml.includes('"wiki/canvases/"'));
    assert.ok(yaml.includes('"wiki/concepts/"'));
  });

  test("active_board 默认 null", () => {
    const yaml = buildOnboardingYaml("test", "Test", "test", FIXED_TS);
    assert.ok(yaml.includes("active_board: null"));
  });

  test("中文 vault_id 保留(Phase B0.1 sanitize 不再坍缩 default)", () => {
    const yaml = buildOnboardingYaml("数学101", "数学 101", "math-101", FIXED_TS);
    assert.ok(yaml.includes('vault_id: "数学101"'));
    assert.ok(!yaml.includes('vault_id: "default"'));
  });

  test("无 testTimestamp 时 fallback new Date().toISOString() (deterministic via mock)", () => {
    const yaml = buildOnboardingYaml("test", "Test", "general");
    // 验证 created_at 字段格式: ISO 8601
    const match = yaml.match(/created_at: "(\d{4}-\d{2}-\d{2}T[\d:.]+Z)"/);
    assert.ok(match, "created_at 应包含合法 ISO 8601 时间戳");
  });

  test("不同 input 产生不同 yaml (snapshot diff)", () => {
    const y1 = buildOnboardingYaml("cs_61b", "CS 61B", "cs-61b", FIXED_TS);
    const y2 = buildOnboardingYaml("math_101", "Math 101", "math", FIXED_TS);
    assert.notStrictEqual(y1, y2);
    assert.ok(y1.includes("cs_61b"));
    assert.ok(y2.includes("math_101"));
    assert.ok(!y1.includes("math_101"));
  });

  test("multi-line yaml 输出含正确换行", () => {
    const yaml = buildOnboardingYaml("test", "Test", "general", FIXED_TS);
    const lines = yaml.split("\n");
    assert.ok(lines.length >= 15, `期望 >= 15 行, 实际 ${lines.length}`);
  });
});
