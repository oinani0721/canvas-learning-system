1. HIGH-1 弱摘要 — STILL-OPEN

round‑2 的顶层最小反例已修复：当前 metadata renderer 位于 [archive_legacy_lance_tables_g24.py:236](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:236)，顶层 field/schema metadata 在 [archive_legacy_lance_tables_g24.py:258](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:258) 纳入 `schema_repr`。

实跑同 `x:int64`、同 `[1]`：

- 无 metadata：`9360935347b96d21`
- 仅 schema metadata：`80830ae507092541`
- 仅 field metadata：`f8bbf4b0a14d2721`
- 两组 `Schema.equals(check_metadata=True)=False`，三者 `content_sha256` 相同。

`export_table` 在 [脚本:306](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:306) 对两侧调用该摘要，并在 [脚本:317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:317) 比较 `schema_repr`；模拟丢失顶层 schema/field metadata 时均得到 `reconciled=False`。

但实现只遍历顶层 `f.metadata`，没有递归渲染 nested `Field.metadata`。构造非 list 的 `struct<x:int64>`，仅子字段 metadata 为 `{unit: cm}` / `{unit: m}`：

```text
Schema.equals(check_metadata=True) = False
schema_repr 两侧 = s:struct<x: int64>:null:meta=-||schema:meta=-
schema_sha16 两侧 = d0ac09fbe574a9df
```

强制让 `export_table` 回读第二张 schema 后，仍得到 `reconciled=True`，随后 [脚本:403](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:403) 允许进入 [drop:410](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:410)。这不是已声明的 list 标签例外，因此“与 `check_metadata=True` 同语义”仍不成立。当前正常 Lance→Parquet 往返确实保留该 nested metadata，但对账闸无法识别不保真的回读，不能据此关闭原 HIGH。

回归检查 5 条：

- BLOCKER-1 — CONFIRMED-CLOSED (未重开) — URI 仍在 [脚本:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:94) fail-closed；同一 canonical path 用于 guard/connect；零动作锁见 [测试:294](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:294)。
- BLOCKER-2 — CONFIRMED-CLOSED (未重开) — DB 树内 archive 仍被 [脚本:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:357) 拒绝；外置 Parquet/drop 与真实 schema-repair 锁见 [测试:434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:434)、[测试:461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:461)。
- BLOCKER-3 — CONFIRMED-CLOSED (未重开) — round‑2 exact-byte 结论见 [round2:17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/codex-review-CARD-G2-4-G2-5-round2.md:17)；校验脚本、YAML、测试从 `a94caa3d` 到当前工作树 `git diff --quiet` 返回 0。遵守读取边界，本轮未重新打开三文件复算。
- HIGH-2 — CONFIRMED-CLOSED (未重开) — 仍强制导入应用 sanitizer，失败即拒绝：[脚本:115](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:115)；锁见 [测试:271](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:271)。
- HIGH-3 — CONFIRMED-CLOSED (未重开) — unknown 仍进入 `unknown_bare` 和 pending：[脚本:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:139)、[脚本:296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:296)；锁见 [测试:108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:108)。

(b) 六锁死门审查：

- ① `test_digest_distinguishes_schema_metadata` — 有效。`/tmp` 删除全部 metadata 渲染后在 [测试:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:171) 转红。
- ② `test_digest_distinguishes_field_metadata` — 有效。同一变异在 [测试:180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:180) 转红。
- ③ `test_digest_equal_for_identical_and_key_order_permuted_metadata` — 有效。把 `sorted(md)` 改为插入序后，在 [测试:199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:199) 转红。
- ④ `test_digest_equality_tracks_arrow_check_metadata` — 死门。把 renderer 改成“只按 value 排序、完全忽略 key”后，指定 7 个测试仍 `7 passed`；`{a:1}` 与 `{z:1}` 实测 Arrow=False、digest=True。其有限 pair 集 [测试:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:208) 同时漏 key-only 和 nested-field 差异。
- ⑤ `test_apply_reconciles_and_drops_metadata_bearing_table` — 有效（正向对照）。删除 renderer 时仍绿符合设计；另将写出路径变异为删除 schema metadata，独立 Arrow oracle 在 [测试:265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:265) 转红。
- ⑥ `test_live_shaped_fixture_flags_bare_fingerprints` — 有效。把裸 `file_fingerprints` 错判 scoped 后，[测试:421](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:421) 转红。
- ⑥ `test_apply_exports_parquet_outside_db_then_drops` — 有效。跳过 source drop 后，[测试:441](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:441) 转红。

核心变异结果：删除 metadata renderer=`3 failed/4 passed`（①②④红）；删除排序=`2 failed/5 passed`（③④红）；忽略 key、仅保留 value=`7 passed`。

证据引用核对：

- `evidence-g24/` 10 个文件全部存在。
- [a-judge-probe.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/evidence-g24/a-judge-probe.txt:1) 为 `True`；[b-pre:71](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/evidence-g24/b-locks-pre-fix-red.txt:71) 为③⑤绿、①②④红；[b-post:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/evidence-g24/b-locks-post-fix-green.txt:66) 为 `20 passed`。
- [c-mutation:71](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/evidence-g24/c-mutation-red.txt:71) 确为①②④红、⑤绿。
- [baseline:666](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/evidence-g24/baseline-round3.txt:666) 为 `13 failed/284 passed`；[post:671](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/evidence-g24/post-fix-suite-round3.txt:671) 为 `13 failed/289 passed`。两份失败清单 SHA 相同且 `cmp=0`；`comm-new-failures.txt` 为 0 bytes。
- [live census:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/evidence-g24/live-lancedb-census-2026-08-31.json:48) 确有裸 `file_fingerprints` 77 行，且 schema 表示为旧算法，符合 §八声明。
- 当前脚本独立 SHA-256 为 `7a555308…c3796`，与 [验收单:426](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/验收单/UAT-CARD-G2-4-Lance旧表回退删除-2026-08-31.md:426) 一致。

新问题：

- HIGH（HIGH-1 残余）— nested `Field.metadata` 未参与摘要，可使 Arrow metadata 不等却对账通过。
- MEDIUM — ④不是其名称/docstring 所称的等价性门；key-blind 变异与当前 nested 漏洞均能全绿。
- LOW — [验收单:388](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/验收单/UAT-CARD-G2-4-Lance旧表回退删除-2026-08-31.md:388) 的 `export_table :290-295` 已漂移，实际为 306–321。
- LOW — [验收单:441](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/验收单/UAT-CARD-G2-4-Lance旧表回退删除-2026-08-31.md:441) 写“297 collected”，证据实际是 [4542 collected、297 selected](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/evidence-g24/baseline-round3.txt:7)。
- LOW — `a-judge-probe.txt` 只有结果；`c-mutation-red.txt` 未保存验收单所称的变异前后 SHA、`cmp` 和恢复后全量复跑。独立复核补足了当前状态，但原证据包不能单独复算完整过程。

当前定向测试实跑：`20 passed, 16 warnings`。未把存档中的宽套件结果冒充本轮完整 CI。

BLOCKER/HIGH 清零：否


