// Migration 003: Canvas 图 vault 隔离 — group_id 回填 + 复合唯一约束
//
// P0-SYNC-ISO-2026-08-17 (Codex 对抗审查确认的 P0):
// sync_service 六条 Cypher 曾以裸 id 做 MERGE/MATCH/DELETE, 跨 vault 同 id
// 实体互相覆盖; _delete_board 级联可抹掉另一 vault 整块画布。写侧修复后
// MERGE 键变 {id, group_id} 复合键 — 本迁移负责:
//   1. 存量 group_id IS NULL 行 100% 回填 (⚠️ Neo4j 复合唯一约束对含 NULL
//      的行**不强制** — 回填不完 = 约束静默失效, STEP 3 verify 必须归零
//      后才允许 STEP 4)
//   2. 全局唯一约束 canvasnode_id_unique 替换为 (group_id, id) 复合约束
//      (否则两个 vault 根本写不进同 id 节点, 写侧修复形同虚设)
//
// ⚠️ 推荐执行方式: backend/scripts/migrate_canvas_group_isolation.py
// (--dry-run 出 census 全量清单供人工核对, --apply 自动按序执行 + verify
// gate)。本文件是同一迁移的 cypher-shell 手工版 + 唯一真相源文档。
//
// $default_physical_gid = to_physical_group_id(default_vault_group_id())
// (subject_config.py:415, 与启动回填/projection 同源; 现网单 vault 实测
// 应为 'vault__canvas_vault')。cypher-shell 手工跑时把 $default_physical_gid
// 替换为实际值, 或用 :param 设置。

// === STEP 0: CENSUS (dry-run — 先跑这些评估规模) ===
//
// 0a. 三 label 的 NULL 计数:
//
//   MATCH (n:CanvasNode) WHERE n.group_id IS NULL RETURN count(n) AS node_null;
//   MATCH (b:CanvasBoard) WHERE b.group_id IS NULL RETURN count(b) AS board_null;
//   MATCH ()-[e:CANVAS_EDGE]->() WHERE e.group_id IS NULL RETURN count(e) AS edge_null;
//
// 0b. 复合键 (group_id, id) 预重复检测 — 命中即人工处置, 否则 STEP 4
//     CREATE CONSTRAINT 会 ConstraintValidationFailed 中断:
//
//   MATCH (n:CanvasNode)
//   OPTIONAL MATCH (b:CanvasBoard {id: n.canvasId})
//   WITH n, coalesce(n.group_id, head([g IN collect(b.group_id) WHERE g IS NOT NULL]),
//                    $default_physical_gid) AS gid
//   WITH gid, n.id AS id, count(*) AS cnt
//   WHERE cnt > 1
//   RETURN gid, id, cnt ORDER BY cnt DESC;
//
//   MATCH (b:CanvasBoard)
//   WITH coalesce(b.group_id, $default_physical_gid) AS gid, b.id AS id, count(*) AS cnt
//   WHERE cnt > 1
//   RETURN gid, id, cnt ORDER BY cnt DESC;
//
// 0c. board (group_id, subjectId, name) 冲突检测 (001:31-39 同款模板升级版):
//
//   MATCH (b:CanvasBoard)
//   WITH coalesce(b.group_id, $default_physical_gid) AS gid,
//        b.subjectId AS subject_id, b.name AS name, count(*) AS cnt
//   WHERE cnt > 1
//   RETURN gid, subject_id, name, cnt;

// === STEP 1: 回填 CanvasBoard (先于 node — node 从 board 继承) ===
MATCH (b:CanvasBoard)
WHERE b.group_id IS NULL
SET b.group_id = $default_physical_gid;

// === STEP 2: 回填 CanvasNode + CANVAS_EDGE ===
//
// CanvasNode: 优先继承所属 board 的 group_id, 兜底 default。coalesce 幂等,
// 不覆盖 exam_service_ext / canvas_projection_sync 已写的值 (WHERE IS NULL
// 已保证)。head+collect 防 board id 历史重复时行爆炸。
MATCH (n:CanvasNode)
WHERE n.group_id IS NULL
OPTIONAL MATCH (b:CanvasBoard {id: n.canvasId})
WITH n, head([g IN collect(b.group_id) WHERE g IS NOT NULL]) AS board_gid
SET n.group_id = coalesce(board_gid, $default_physical_gid);

// 审查 F1 修正 (2026-08-17): 边继承 source 端点 group (node 先回填完),
// 兜底 default — 边 group ≠ 端点 group 会让 group 限定的 _delete_edge /
// 幽灵边对账永远看不见它 (悬挂脏边)。
MATCH (s)-[e:CANVAS_EDGE]->()
WHERE e.group_id IS NULL
SET e.group_id = coalesce(s.group_id, $default_physical_gid);

// === STEP 3: VERIFY — NULL 三 label 必须归零, 否则禁止执行 STEP 4 ===
//
//   MATCH (n:CanvasNode) WHERE n.group_id IS NULL RETURN count(n) AS node_null;
//   MATCH (b:CanvasBoard) WHERE b.group_id IS NULL RETURN count(b) AS board_null;
//   MATCH ()-[e:CANVAS_EDGE]->() WHERE e.group_id IS NULL RETURN count(e) AS edge_null;
//   -- 三个都必须是 0。复合唯一约束对含 NULL 的行不强制 — 有残留 NULL
//   -- 时建约束不报错但保护不了那些行 (静默失效)。

// === STEP 4: 约束替换 (先建新、后删旧 — 全程无保护真空窗口) ===
//
// 复合唯一约束自带支撑索引, 无需另建 (group_id, id) 索引。
CREATE CONSTRAINT canvasnode_group_id_unique IF NOT EXISTS
FOR (n:CanvasNode) REQUIRE (n.group_id, n.id) IS UNIQUE;

CREATE CONSTRAINT canvasboard_group_id_unique IF NOT EXISTS
FOR (b:CanvasBoard) REQUIRE (b.group_id, b.id) IS UNIQUE;

CREATE CONSTRAINT canvasboard_group_subject_name_unique IF NOT EXISTS
FOR (b:CanvasBoard) REQUIRE (b.group_id, b.subjectId, b.name) IS UNIQUE;

// 旧全局约束此刻才可安全删除 — 它们的存在会阻止两个 vault 写同 id/同名板
DROP CONSTRAINT canvasnode_id_unique IF EXISTS;
DROP CONSTRAINT canvasboard_subject_name_unique IF EXISTS;

// === STEP 5: 最终验证 ===
//
//   SHOW CONSTRAINTS WHERE name IN [
//     'canvasnode_group_id_unique',
//     'canvasboard_group_id_unique',
//     'canvasboard_group_subject_name_unique'
//   ];
//   -- 三行都在; canvasnode_id_unique / canvasboard_subject_name_unique 不在。

// === ROLLBACK (emergency only) ===
//
// 前提: --apply 后尚未产生跨 vault 同 id 数据 (apply 后立即回滚的窗口内
// 安全)。若已有两个 vault 写入同 id 实体, 重建全局唯一约束会
// ConstraintValidationFailed — 此时只能从 Neo4j backup 恢复。
//
//   DROP CONSTRAINT canvasnode_group_id_unique IF EXISTS;
//   DROP CONSTRAINT canvasboard_group_id_unique IF EXISTS;
//   DROP CONSTRAINT canvasboard_group_subject_name_unique IF EXISTS;
//   CREATE CONSTRAINT canvasnode_id_unique IF NOT EXISTS
//   FOR (n:CanvasNode) REQUIRE n.id IS UNIQUE;
//   CREATE CONSTRAINT canvasboard_subject_name_unique IF NOT EXISTS
//   FOR (b:CanvasBoard) REQUIRE (b.subjectId, b.name) IS UNIQUE;
//
// 回填的 group_id 属性冗余无害, 无需清除 — 旧 Cypher 按裸 id 匹配,
// 多余属性透明 (代码 revert 后行为与迁移前一致)。
