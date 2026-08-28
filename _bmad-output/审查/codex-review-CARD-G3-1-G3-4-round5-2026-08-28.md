# 第五轮终裁

**需六轮，当前不可验收。**  
审阅对象为 `60568d9c48fcaed3d2c76b9a38c42d9403ce8454`。残留 **BLOCKER ×1、HIGH ×4**。

| 审阅点 | 判定 |
|---|---|
| 一、并发协议 | **STILL-OPEN / BLOCKER** |
| 二、时间口径 | **STILL-OPEN / HIGH** |
| 三、三态判别 | **STILL-OPEN / HIGH** |
| 四、out_of_order / degraded pending | **STILL-OPEN / HIGH** |
| 五、vault_id / manifest | **STILL-OPEN / HIGH** |
| 六、G3-4 曲线门 | **CONFIRMED-CLOSED**，另有非 HIGH 新缺口 |
| 七、回归与一致性 | 核心实测 **CONFIRMED**；UAT 存证 **NEW-FINDING / MEDIUM** |

## 一、并发协议：STILL-OPEN / BLOCKER

A3 的 `W+1s`、拒绝乐观 CAS、锁内重读 W、账本先 fsync 等直接矛盾已经修正，但四条仍不是 exactly-once 的充分集：

- 锁对象不稳定：[A4.1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:130) 允许“文件锁”，而 A4.4 会 `os.replace` 节点文件。若锁节点 inode，可出现 `A 锁旧 inode → replace → C 锁新 inode → B 随后获得旧 inode 锁`，B/C 同时自认为排他。必须冻结不会被 replace 的 sidecar/目录锁、规范化 `{vault,node}` key 与崩溃回收。
- [A4.2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:131) 同时要求“基线恒为当前 state”和允许“从头折叠全账本”：从当前 S1 再折 E1 会重复；从 New 折叠又违反前句。
- `event_id` 的 parsed-equality claim/check+append 未进入 A4 临界区；per-node 锁也不串行化不同节点对同一 JSONL 的并发追加。
- 耐久性不完整：账本首次创建缺 parent-dir fsync；frontmatter 缺 temp `flush+fsync` 和 replace 后目录 fsync。仓库已有完整正确模式可对照：[sync_board_concepts.py:583](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/scripts/sync_board_concepts.py:583)。
- schema/CURRENT_TASK 的三项移交相互一致，但实际 [G3-3 卡面](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:283) 仍写“锁/CAS”，缺 W+1s 锁内重算和 fsync；第五笔未更新它。

## 二、时间口径：STILL-OPEN / HIGH

validator 的完整整秒和同瞬间比较已闭合，但端到端仍断：

- [bridge `_aware()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/scripts/fsrs_bridge.py:50) 不把 aware offset 转成 UTC。只读真实库复算中，validator 合法的 `12:00:00+08:00` 传入 `review()` 后，fsrs 6.3.1 抛出 `ValueError: datetime must be timezone-aware and set to UTC`。
- naive 时间仍被静默当 UTC，小数秒仍被 `_iso()` 截掉；validator 只是 standalone lint，未冻结 bridge `ts` 必须等于已验证 `payload.review_time`。
- [pending 排序](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:119) 未明确按 UTC instant 排序。字符串序会把 `10:00:02Z` 排在真实更早的 `18:00:01+08:00` 前面。
- NEW-FINDING / MEDIUM：validator 接受 UTC 归一化会越界的极端日期，bridge `_iso()` 会 `OverflowError`。

## 三、三态判别：STILL-OPEN / HIGH

所谓“完整 tuple”实际只检查 due/state/last_review，[但 bridge 消费六字段](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/scripts/fsrs_bridge.py:102)：

- 合法三键、`state=2/3`、缺 stability/difficulty/step：文档判正常，真实 `review()` 均 `AssertionError`。
- `state=1` 缺 step 会默认 step 0，可走出与原状态不同的 Learning 路径。
- 非法或非有限的 step/stability/difficulty、重复 frontmatter 键均未纳入 fail-closed 判别。

正常卡应按 state 冻结完整、有限、相容的持久化字段形状，而不只是三个字段可解析。

## 四、out_of_order / degraded pending：STILL-OPEN / HIGH

`payload.out_of_order` 的 `true/absent` 二态已正确机械冻结，[false、字符串、数字、对象、null 均被拒](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:259)。

但 degraded 恢复仍不充分：[文档](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:141) 只说“修复水位线后重放”，没有要求把六字段与 W 原子重建到同一个可证明账本边界：

- state 已含 E2、修复为 `W=t1` ⇒ E2 二次应用。
- state 仅含 E1、修复为 `W=t2` ⇒ E2 永久遗漏。

不可证明 state/W 同源时必须继续冻结，不能仅凭语法三态解冻。

## 五、vault_id / manifest：STILL-OPEN / HIGH

当前主仓简单形态能正确绑定，但 [正则解析器](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:197) 不是可靠 YAML 子集：

- `vault_id: "team#1"` 被解析为 `team`；payload=`team` 可通过，而真实 YAML 身份是 `team#1`。
- `vault_id:\nsubject: cs61b` 被跨行解析成 `subject: cs61b`。
- 重复键取首项，而应用 PyYAML 路径取末项。
- block scalar 被解析成 `|`/`>-`；未闭引号仍可能被接受；非法 UTF-8 未捕获。

因此既可身份错绑后 PASS，也可对合法配置误 FAIL。当前现网 `vault_id: "canvas_vault"` 未命中这些问题。

manifest 的 list/scalar/坏 JSON 不再 traceback，直接残留已闭；但仅检查两个值是字符串，不验非空/版本/hash 形状，canonical manifest 缺失或损坏仍 WARN 后 `RESULT: PASS`，判 **MEDIUM**。

## 六、G3-4 曲线门：CONFIRMED-CLOSED

第四轮 HIGH 已闭合：[测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:346) 已锁历史 rating、逐步时刻、card 快照、`due+(0,7,30)` 和真实 retrievability 复算；矩阵、state_before bool、manifest 出处也已锁。

仍有非 HIGH 覆盖缺口：

- `retrievability.card.state` 从 `2` 改为 `2.0` 仍 13/13。
- 修改 description、增加嵌套未知键仍全绿。
- `comparison_tolerance` 未锁子键集。

所以行为曲线漂移已封闭，但不能宣称“任意 golden 数据变化必红”。

## 七、回归与一致性：核心 CONFIRMED，UAT 有 NEW-FINDING

- 精确 HEAD：**60 passed + 1 skipped + 10 warnings**。因工作树已有一条 HEAD 外未提交测试，复算时显式排除，显示 `1 deselected`。
  - 契约：41 passed + 1 skipped
  - golden：13 passed
  - 既有账本：6 passed
- 主仓账本：23 行，validator exit 0；stdout 只有 PASS，无 WARN/FAIL；前后 SHA 均为 `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`。
- 五笔提交 blob 恒定：
  - `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
  - `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`
- 两份 UAT 的上述测试计数、23 行账本、blob 与曲线主数据一致。
- NEW-FINDING / MEDIUM：G3-4 UAT 声称 `negverify_v4` exit code 能反映证据有效性，但[脚本](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-4-evidence/negverify_v4.sh:16)仍只 grep `FAILED`、重复启动 pytest、且不检查 mutation/restore；存证仍绑定 `4de42f69` 和 12 门旧 SHA，不是当前 60568d9c/13 门。

## 残留 BLOCKER/HIGH

- **BLOCKER ×1**：A4 exactly-once 协议仍缺稳定锁身份、可执行折叠基线、原子幂等 claim/共享账本串行化及完整目录耐久。
- **HIGH ×4**：
  1. review_time/bridge/pending 排序未端到端统一为 UTC instant；
  2. 正常卡未验证完整且状态相容的 FSRS 持久化 tuple；
  3. degraded 解冻未绑定可证明的 state+W 原子重建边界；
  4. vault_id 最小解析会错绑、漏绑合法 YAML。

审计未修改工作树；原有未提交测试和 round5 草稿保持原状。`graphiti-canvas` 本会话未暴露，无法执行规定检索；未将此限制包装成已完成证据。


