/**
 * Round-23 Phase B0.3 (2026-05-11) — Onboarding helpers (pure functions).
 *
 * ChatGPT Deep Research P1 fix (2026-05-11): 把 buildOnboardingYaml 从
 * main.ts private method 提取到独立模块,与 error-candidate-helpers.ts 同模式
 * (plugin 纯函数 helpers 独立模块 → node:test 可测试)。
 *
 * 跑测试: cd frontend/obsidian-plugin && npm test
 */

/**
 * 生成 .canvas-config.yaml v2 schema 内容(round-23 §3.1.2 schema 对齐)。
 *
 * 纯函数:
 * - 输入: vaultId + displayName + subject + (可选) timestamp
 * - 输出: yaml 字符串
 * - 副作用: 0(不读不写文件,不依赖时间默认值见 testTimestamp)
 *
 * @param vaultId — sanitized vault_id(由 inferVaultId 生成,如 "cs_61b" / "数学101")
 * @param displayName — 人类可读名(如 "CS 61B 数据结构")
 * @param subject — 学科 slug(如 "cs-61b" / "math-101");留空走 "general"
 * @param testTimestamp — 可选 ISO 8601 时间字符串,默认 new Date().toISOString()
 *                       (注入用于 deterministic 测试)
 */
export function buildOnboardingYaml(
  vaultId: string,
  displayName: string,
  subject: string,
  testTimestamp?: string,
): string {
  const createdAt = testTimestamp ?? new Date().toISOString();
  const subjectValue = subject || "general";
  return `# Canvas Learning System · Vault 级配置 (Phase B0.3 onboarding 生成)
# 本 vault 只学一个学科 (subject), 不跨学科.
# 所有 Skill 从此文件读 subject + vault_id, 不再向用户问.

# Phase B0.3 (2026-05-11): 显式 vault_id 字段
vault_id: "${vaultId}"
vault_display_name: "${displayName}"

subject: ${subjectValue}            # 机器代码 (lowercase+数字+连字符)
subject_display: "${displayName}"   # 人类显示名

# 当前活动白板 (ai-linked-doc Skill active_board 默认值)
active_board: null

# 架构版本 (Skill 兼容检查)
schema_version: "2.0-multi-vault-2026-05-10"
created_at: "${createdAt}"

# 弃用路径 (Skill 不再向这些路径写入)
deprecated_paths:
  - "wiki/canvases/"
  - "wiki/concepts/"
`;
}

/**
 * 验证 onboarding 表单输入是否合法。
 *
 * 纯函数:
 * - 输入: displayName + subject
 * - 输出: { valid: boolean, error?: string }
 *
 * 规则:
 * - displayName 必填(trim 后非空)
 * - subject 可选(空字符串走 "general")
 * - displayName 不允许只含空白
 */
export function validateOnboardingInput(
  displayName: string,
  subject: string,
): { valid: boolean; error?: string } {
  void subject; // subject 可空,保留参数为未来扩展
  if (!displayName) {
    return { valid: false, error: "vault 显示名不能为空" };
  }
  if (!displayName.trim()) {
    return { valid: false, error: "vault 显示名不能全为空白" };
  }
  return { valid: true };
}

/**
 * 判断当前 vault 是否需要 onboarding(.canvas-config.yaml 不存在)。
 *
 * 纯函数:
 * - 输入: exists boolean(由调用方用 vault.adapter.exists 检测)
 * - 输出: boolean — true 表示需要 onboarding
 *
 * 设计哲学: 把 IO(adapter.exists)与决策(是否触发 onboarding)分离,让决策可测试。
 */
export function shouldTriggerOnboarding(configExists: boolean): boolean {
  return !configExists;
}
