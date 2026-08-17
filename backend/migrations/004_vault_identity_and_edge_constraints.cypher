// Migration 004: VaultIdentity 唯一约束 + CANVAS_EDGE (group_id, id) 复合唯一约束
//
// P0-SYNC-ISO-2026-08-17 R10 复审 (P0-01 / P2-01, P2-02):
//   1. vault_identity_gid_unique — 身份注册表并发兜底: vault_identity_registry
//      并发注册同一 physical_gid 时应用层 MERGE 有竞态窗口, 数据库层唯一
//      约束保证第二条写入被拒绝 (而不是产生两个同 gid 的身份节点)。
//   2. canvas_edge_group_id_unique — 边唯一性: 003 只给 CanvasNode/CanvasBoard
//      建了复合唯一约束, CANVAS_EDGE 的 (group_id, id) 无数据库层保护 —
//      写侧 bug 可静默产生跨 vault 同 id 重复边。
//
// 前置依赖: 003 已执行完毕 (CANVAS_EDGE.group_id 已 100% 回填, 无 NULL —
// 唯一约束对含 NULL 的行不强制, 003 未跑完时本约束对 NULL 边静默失效)。
//
// 本迁移只建约束、不改数据 — 无回填, ROLLBACK 纯 DROP 无数据风险。

// === STEP 0: 前置检查 (只读 — 命中即人工处置, 否则 CREATE 会
// ConstraintValidationFailed 中断) ===
//
// 0a. VaultIdentity physical_gid 预重复检测:
//
//   MATCH (v:VaultIdentity)
//   WITH v.physical_gid AS gid, count(*) AS cnt
//   WHERE cnt > 1
//   RETURN gid, cnt ORDER BY cnt DESC;
//
// 0b. CANVAS_EDGE (group_id, id) 复合键预重复检测:
//
//   MATCH ()-[e:CANVAS_EDGE]->()
//   WITH e.group_id AS gid, e.id AS id, count(*) AS cnt
//   WHERE cnt > 1
//   RETURN gid, id, cnt ORDER BY cnt DESC;
//
// 0c. CANVAS_EDGE group_id NULL 残留复查 (必须为 0 — 非 0 先跑 003):
//
//   MATCH ()-[e:CANVAS_EDGE]->() WHERE e.group_id IS NULL
//   RETURN count(e) AS edge_null;

// === STEP 1: 执行 ===
//
// R10 P0-01: 身份注册表并发兜底 — 同一 physical_gid 只允许一个
// VaultIdentity 节点 (应用层 MERGE 竞态的数据库层保险)。
CREATE CONSTRAINT vault_identity_gid_unique IF NOT EXISTS
FOR (v:VaultIdentity) REQUIRE v.physical_gid IS UNIQUE;

// P2-01: 边唯一性 — (group_id, id) 复合键, 与 003 的节点/板约束对齐。
// ⚠️ 关系属性唯一约束需要 Neo4j 5.7+ (relationship property uniqueness
// constraint, 5.7 引入)。版本不足时: 跳过此条 (其余照常), 用下面的
// 替代检测查询做周期巡检, 升级到 5.7+ 后再补建:
//
//   -- 替代检测 (Neo4j < 5.7, 只读, 返回 ≥1 行 = 有重复边需人工清理):
//   MATCH ()-[e:CANVAS_EDGE]->()
//   WITH e.group_id AS gid, e.id AS id, count(*) AS cnt
//   WHERE cnt > 1
//   RETURN gid, id, cnt ORDER BY cnt DESC;
CREATE CONSTRAINT canvas_edge_group_id_unique IF NOT EXISTS
FOR ()-[e:CANVAS_EDGE]-() REQUIRE (e.group_id, e.id) IS UNIQUE;

// === STEP 2: 验证 ===
//
//   SHOW CONSTRAINTS WHERE name IN [
//     'vault_identity_gid_unique',
//     'canvas_edge_group_id_unique'
//   ];
//   -- 两行都在 (Neo4j < 5.7 跳过边约束时: 只有 vault_identity_gid_unique)。

// === ROLLBACK (纯 DROP — 本迁移不改数据, 无数据风险) ===
//
//   DROP CONSTRAINT canvas_edge_group_id_unique IF EXISTS;
//   DROP CONSTRAINT vault_identity_gid_unique IF EXISTS;
