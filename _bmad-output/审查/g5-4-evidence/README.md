# CARD-G5-4 live 只读实测证据（BATCH-2026-08-28-第五批）

- **时间**: 2026-08-28（取证时刻见 scan JSON 的 `source_revision.scan_at_utc`；本目录为 **Codex round-1 F1 修复后重取版**）
- **对象**: live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault`（只读铁律）
- **方法**:
  1. `find . -type f -print0 | sort -z | xargs -0 shasum -a 256` → `shasum-before.txt`（**全 vault 324 文件，含 `.claude/`**——原先只覆盖四个数据目录，漏掉了脚本目录的写侧）
  2. worktree 版 `recap_scan.py` 对 3 真实板 collect（无 `--manifest`，fallback 模式），stdout 重定向 scratchpad（不落 vault）：
     - `CS 61B` → `scan-CS-61B.json`（exit 0）
     - `特征值与特征向量` → `scan-特征值与特征向量.json`（exit 0）
     - `CS188 lecture 2` → `scan-CS188-lecture-2.json`（exit 0）
  3. 同法重取 → `shasum-after.txt`；`diff` 为空 → **SHASUM-IDENTICAL**（零写侧取证）

## 信号实测摘要（fallback 模式，真实数据，F1 修复后）

| 板 | 未答问题年龄 | 来源覆盖率 | 无来源结论 | 重复堆积 |
|---|---|---|---|---|
| CS 61B | 最老 17 天 (3 条)【文件】 | 0/2【文件】 | 无据 (无派生角色成员) | 0/3【文件】 |
| 特征值与特征向量 | 最老 40 天 (3 条)【文件】 | 2/3【文件】 | 0/2【推定】 | 0/3【文件】 |
| CS188 lecture 2 | 最老 78 天 (4 条)【文件】 | 7/8【文件】 | 0/7【推定】 | 0/4【文件】 |

注：live 后端未连（fallback），availability 档位如实为 文件/推定；判读留人——本表不含任何偏航判定。
F1 修复对本三板的可见影响：特征值与特征向量 来源覆盖率由修复前 2/3（仅 source_note 计锚）——本表数值恰未变
（该板带 derived-from 的成员同时带 source_note）；修复的语义差异由 fixture 回归
`test_cross_mode_signal_consistency_real_manifest` 锁定。

**本目录为 round-3 全部处置后的最终重取**（role 改与后端 `_node_role` 同构的 truthiness 判定 /
`_fm_scalar` 同行夹逼 + 剥行尾注释 + 顶格 / manifest 侧归一改幂等的 passthrough 版 / verifier 整行严格绑定 等）：
三板信号值与前两次重取逐项相同——这三板的 frontmatter 都用连字符拼写、无空键、无 null 值、无 wikilink-null 名，
所以这些修复对它们的**取值**无影响；修复真正改变行为的输入形态由 fixture 回归覆盖
（`test_role_matches_backend_node_role_exactly` 等）。shasum 依旧全等。
