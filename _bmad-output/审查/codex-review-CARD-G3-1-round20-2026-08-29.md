结论先行：**CARD-G3-1 需再一轮；CARD-G3-4 仍保持可验收。**  
十九轮 HIGH 已有更强证据，可确认是另一车道对 S1 测试污染的授权清理，不是数据损坏，也不是 G3-1 所为；但代码/规范侧仍有 2 个 MEDIUM，文档另有 1 个 MEDIUM，不能按“只剩环境事件”验收。

审阅终态：HEAD=`59e56cd6f698cf0ea15d06f001785ceaf45c50ff`；tracked/cached 零改动。仅保留审阅前已有、未读取的 untracked round20 报告；负验证原脚本和 live 账本均未修改。

## 逐点裁定

### 1. 十九轮 HIGH：账本 23→22 行

**CONFIRMED-CLOSED — 环境事件定性有更强证据。**

- `37387a86..HEAD` 共 **21** 笔提交，`git log -- canvas-vault/` 为空；不是 G3-1 commit 所为。
- 当前 live 账本：22 行、7232 bytes、SHA-256  
  `2a18023e71a046db8a8c52e098cd48bd0b9898596e4ea3024e18695827796cb6`，mtime `2026-08-29 06:11:47 +0800`；校验器 exit 0，前后 SHA 不变。
- 主仓存在备份 `backups/learning_events.jsonl.pre-s1-cleanup-20260829-061014`：23 行、7492 bytes、SHA `f78b99f307…`。直接字节比较确认当前文件恰是备份的前 7232 bytes；缺少的末行是 `callout:c-409-guard` 测试探针。
- 独立 S1 裁定明确记录污染根因、用户授权和“先备份、再删除一行”，见[第五批独立复核裁定:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-29-第五批独立复核裁定.md:19)及[同文件:29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-29-第五批独立复核裁定.md:29)。

准确性质是：**另一车道经授权清理 S1 测试污染**；不是随机损坏，也不是回滚真实学习数据。第 23 行当前可从备份恢复，但该备份仍为 untracked，尚不是持久化、版本化存证。

**NEW-FINDING — MEDIUM（登记不再诚实完整）。**

[CURRENT_TASK.md:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:5)及[G3-1 UAT:394](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:394)仍写“待用户裁决、原因不可证、不可恢复”，遗漏已有备份和授权清理记录，制造了一个已经不存在的用户阻塞点。

### 2. 十九轮 5 MEDIUM + 2 LOW

1. **未知版本旧反例：CONFIRMED-CLOSED（窄义）；但有新的 MEDIUM。**

   合法 v1 `node=n,vault=a` 后追加保留旧形状的 v2 `node=n,vault=b`：

   - 主体校验：零 violation，仅 v2 WARN；
   - scanner：`unknown_version_lines=[2]`、`vault_ids={'a'}`；
   - proof：只报 unknown-version fail-closed，不再假报 vault 不符。

   实现见[validate_learning_events.py:526](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:526)和[同文件:710](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:710)。

2. **manifest 六键字面量：CONFIRMED-CLOSED。**

   字面量、常量等值门及逐键门见[contract test:2091](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2091)。从 `_SCHEDULER_CONFIG_KEYS` 删除 `parameters` 后恰有两项预期测试变红：常量集合门和 `[parameters]` 行为门；其余 `168 passed + 1 skipped`。

3. **`review_ext_lines` 分母：CONFIRMED-CLOSED。**

   L1 正常且带 vault；L2 为真正乱序、无 vault：

   ```text
   applicable=[1]
   review_ext_lines=[1,2]
   vault_id_lines=[1]
   proof -> “仅 1/2 条 review/1 事件带 vault_id”
   ```

   收集及比率见[validator:549](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:549)、[validator:748](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:748)；完整回退旧口径后恰[分母测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2240)一项变红。

4. **正规化：CONFIRMED-CLOSED。**

   `a / b != a/b`，而物理折行 `a /` + `b` 与 `a / b` 相等。退回 `re.sub(r"\s+","")` 后，仅[正规化直接测试:2261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2261)变红。

5. **负验证归因：STILL-OPEN — MEDIUM。**

   A–T 二十个 Perl 模式静态复算均**恰命中一处**，这一层闭合；但：

   - G 仍只匹配参数 ID 前缀：[脚本:187](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:187)；
   - L 只写参数化基名，不能证明两个实例各自变红：[脚本:221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:221)；
   - Q 实际删除 vault 收集，而不是忠实移到 `continue` 后；它因“无 vault 证据”的替代 fail-closed 变红：[脚本:257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:257)。
   - `COLLECTED` 还把实际 171 项重复累加为 334，存证数字不可信。

6. **两个 LOW：未完全闭合。**

   - scanner 文档仍把 `node_event_lines` 称为该节点“全部事件”，实际排除了未知版本；无证据诊断仍写“适用事件均无 vault_id”，见[validator:484](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:484)和[validator:741](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:741)。
   - UAT 顶部仍称当前 23 条，[UAT:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:8)、[UAT:36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:36)；CURRENT_TASK 称 20 笔，实为 21 笔；[UAT:424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:424)还把“第二十一笔后的二十变体”写成“二十一轮负验证”。

### 3. 三处同文

**CONFIRMED-CLOSED（机械同文）；NEW-FINDING — LOW（内容遗漏）。**

我未调用被测正规化函数，而是固定抽取：

- schema：[§6.2:205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:205)
- 模块注释：[validator:337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:337)
- docstring：[validator:1131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1131)

仅去除 Markdown/Python 载体和缩进、用一个 ASCII 空格接回物理折行。六条三方逐字符 diff 为空，长度分别为 `57/50/163/94/156/62`。

但三处第⑤条都漏掉新增的 `event_version` 检查；[schema:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:203)也未列 `unknown_version_lines`、`review_ext_lines`。所以“同文”成立，“内容完整”不成立。

### 4. 未知版本策略与新 survivor

**NEW-FINDING — MEDIUM。**

schema 明许 v2 删除或改名任意顶层字段，见[schema:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:13)。以下合法未来形状放在完全合规的目标节点 v1 后：

```json
{
  "event_id": "future:1",
  "event_version": 2,
  "brand_new_field": true,
  "payload_v2": {"concept_ref": "n", "review": true}
}
```

实测：

```text
主体 violations=[]
主体仅 WARN
scan.unknown_version_lines=[]
proof problems=[]
```

原因是当前先按旧 `node_id` 过滤，再判断版本。v2 一旦改名/删除 `node_id`，proof 会静默放过无法解释的记录。

误拒方向也存在全绿 survivor：把版本判断移到 `node_id` 过滤之前，L2 为 `event_version=2,node_id=other` 时会误拒节点 n 的 proof，但完整契约仍 `170 passed + 1 skipped`。

结论：

- 当前实现并非“所有 v2 一律拒绝”；明确保留旧 `node_id=other` 的 v2 当前不会误伤。
- 对确属同节点但无法解释的 v2，proof 拒绝背书并不违反主体“跳过+告警”前向兼容条款。
- 真正缺口是跨版本 routing 未冻结。需要稳定 routing envelope、版本适配器，或明确成文的全局冻结策略；不能继续依赖 v1 `node_id` 猜测 v2 归属。
- 目前没有非测试生产调用方，因此定为 MEDIUM 而非 HIGH。

### 5. 新增测试有效性

**PARTIAL / NEW-FINDING — LOW。**

新增断言没有恒真 `if`、manifest 期望不再来自被测常量、分母断言精确到 `1/2`；这些都有效。

但版本和分母测试复用了[_event():1558](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1558)。该 review/1 记录经主体校验有 5 项违规：缺 `rating`、`concept_id`、`grade_norm`、`fsrs_library_version`、`fsrs_params_hash`，违反 verifier 明示的“账本已先通过主体校验”前提。现门杀得掉原分支，但没有锁住合法全链场景。

## 回归与 G3-4

**CONFIRMED-CLOSED。**

指定解释器实跑：

- 契约：`170 passed, 1 skipped`
- 契约 + golden + 既有账本：`195 passed, 1 skipped`
- golden：`19 passed`
- `tests/unit/test_fsrs_manager.py`：`37 passed`
- UAT 所列 11 文件 FSRS 全族：`191 passed`，无 F/E；有 2771 个既有 DeprecationWarning
- live 校验器：exit 0，SHA 前后及最终均为 `2a18023e…`

`9d985822..HEAD` 对 G3-4 generator/manifest/vectors 零 diff；blob：

- generator `9d6ab4f63b326dc3f604cb794ce9fd9e42de792e`
- manifest `b59f331d9a1f57e5778fd82399ef12b61eb0c967`
- vectors `33c601995d5274f7702a4d0ce501d2b81311d688`

锁定 blob：

- `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
- `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`

## 残留清单与验收结论

- BLOCKER：0
- HIGH：0
- MEDIUM：3
  - v2 跨版本 routing 未冻结，存在宽松逃逸及误拒方向全绿 survivor。
  - 负验证 G/L/Q 仍不能证明目标危险分支承重。
  - 验收单/CURRENT_TASK 错把已授权、可从备份恢复的 S1 清理写成待裁决且不可恢复。
- LOW：2
  - 三处范围声明及 scanner 键/诊断漏记新版本行为。
  - 新 scanner 测试未满足主体校验前置条件。

**CARD-G3-1：需再一轮；代码/规范侧目前也不可验收，并非只剩环境事件。**  
**CARD-G3-4：仍保持可验收。**


