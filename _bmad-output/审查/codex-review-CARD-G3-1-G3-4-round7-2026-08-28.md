终裁：**需八轮，不可验收。**

已确认待审对象为 `2c8dc51722e97ff83f8b99ec48168680a204dc1a`。CARD-G3-4 可保持关闭；CARD-G3-1 仍残留 **BLOCKER ×1、HIGH ×3**。

## 一、A4 四分项

1. **parsed-field equality：原反例 CONFIRMED-CLOSED；文档自洽 NEW-FINDING / MEDIUM**

   [schema:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:163) 的逐行 `json.loads` 后按 `event_id` 字段等值比较，确实修掉了 payload 子串误命中；按规范意图，这是实现纠错，不必升 v2。

   但文档仍冲突：[schema:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:11) 称既有幂等语义原样生效，[schema:23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:23) 又把子串行为留在“幂等”契约行，而 :163 声称偏离已登记 §九，实际 §九没有该项。

2. **fencing + owner-death：STILL-OPEN / BLOCKER / 属本卡**

   [schema:153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:153) 关闭了“活进程仅因超时被接管”的原反例，但死亡证明没有与观察到的 `{epoch, owner}` 做原子条件绑定。

   可达竞态：B、C 都读取 `{7,A(dead)}` 并证明 A 已死；B 接管为 `{8,B}` 后，C 仍凭陈旧证明覆盖新 owner。发布前重读与 `os.replace` 之间也非原子，仍可双持、旧状态覆盖，或使败者已 durable 的同秒事件因 `review_time == W` 永久不进 pending。需要冻结 conditional takeover/CAS：只有 observed epoch+owner 未变时才可接管。

3. **短写、耐久与恢复：CONFIRMED-CLOSED（契约层）**

   [schema:157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:157) 至 :164 已覆盖完整 fsync 顺序、返回字节数检查、LF 守卫和坏尾行报告。生产实现尚未落地，仍为 **STILL-OPEN / 已移交 G3-3 / 不计本卡**。

4. **duplicate 门：STILL-OPEN / BLOCKER / 属本卡**

   [schema:165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:165) 只比较 canonical `payload`，没有比较顶层语义 envelope。

   已实测两条记录：

   - 同 `event_id`
   - 同 canonical payload
   - `event_type` 分别为 `answer_scored`、`answer_abandoned`
   - 两条分别经 validator 均为零违规

   当前规则会错误 no-op，而不是冲突 fail-closed。等价面至少应覆盖 `event_version/event_type/node_id/effective_at/payload`，仅明确排除重试自然变化的 `recorded_at`。

**A4 总体：STILL-OPEN / 复合 BLOCKER ×1。**

## 二、三态判别

**STILL-OPEN / HIGH / 属 CARD-G3-1。**

表格与函数在字段“有/无”层面一致；192 个 state/存在性组合未发现差异，六轮四个点名反例也已封堵。但可执行域仍不正确：

- [schema:117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:117) 把 `maximum_interval=36500` 错当 stability 上界。[classifier:221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:221) 先把 `S=36500` 判 normal；真实 bridge Easy 成功写回 `S=36547.3398`，下一次 classifier 立即判 degraded。FSRS 封顶的是 interval，不是 stability。
- [classifier:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:171) 通过 `float()` 判断“整数”，因此 frontmatter `fsrs_state: 1.0` 被判 normal；真实 [bridge:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/scripts/fsrs_bridge.py:106) 执行 `int("1.0")`，实测 `ValueError`。
- 文档要求重复 `fsrs_*` 键 fail-closed，但 `classify_card_state(fields: dict)` 接口已经丢失重复键信息，无法机械实现该条。

既有 bridge 的 offset/UTC 等实现偏差仍是 **已移交 G3-2/G3-3**；上述 classifier/契约缺陷则属于本卡。

## 三、degraded 解冻

**部分闭合，整体 STILL-OPEN / HIGH / 属本卡。**

- E 必须为最后适用事件、按 `(review_time, 行号)` 消歧：**CONFIRMED-CLOSED**。
- `degraded:*` 不进入自动证明链：**CONFIRMED-CLOSED**。
- canonical reducer 与 proof：**STILL-OPEN**。

[Schema:180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:180) 只动态引用“bridge 实际精度”，没有冻结四位精度、Python `round`/tie 语义、序列化规则或 bridge blob；因此 `10.9711` 与 `10.9710` 的区分仍依赖可漂移的外部实现。

[Schema:181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:181) 的“同源快照 + 其证明”也未定义快照边界、六字段/W hash、祖先 proof schema与终止条件；prefix hash 的确切 bytes/行尾范围未冻结。仍不能机械验真。

## 四、vault_id 解析

**STILL-OPEN / HIGH / 属 CARD-G3-1 validator。**

[_scan_vault_id():320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:320) 仍会对合法 YAML 静默错绑：

- `vault_id: first\n  second\n`：PyYAML 真值为 `"first second"`，scanner 返回 `"first"`；匹配错误 payload 时 CLI 可 `exit 0`、零 WARN。
- `vault_id: old\ndescription: it's fine\nvault_id: new\n`：PyYAML 取 `new`，scanner 把普通 plain scalar 中的撇号误当跨行引号起点，返回 `old`。
- `vault_id : second`、quoted/explicit key、隐式类型及带首尾空格的 quoted value 也存在漏识别或 `.strip()` 错绑。

所以“任何不确定形态一律 None + WARN”尚未成立。

## 五、A7 时间上界

**上界取值 CONFIRMED-CLOSED；执行范围 NEW-FINDING / MEDIUM / 属本卡。**

`9000-01-01Z` 作为人类学习数据上界足够保守，现实误报风险很低。但 [_parse_ts():133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:133) 把该上界通用于所有时间字段及 `fsrs_due`：

- 允许的 `review_time=9000-01-01Z` 经真实 bridge 产 `due=9000-01-09Z`；
- [classifier:200](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:200) 随即因 due 超过同一上界判 degraded；
- 非 review 事件的 `recorded_at/effective_at` 也被施加了文档未声明的限制。

需要把 review 输入上界与 due/general timestamp 的受理范围分开。

## 六、G3-4

**CONFIRMED-CLOSED。**

[Golden test:425](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:425) 已锁定每个 `retrievability.at` point 的精确键集与 `expected` float 类型。

在隔离的 exact HEAD 重跑 v4：

- N0–N12：13/13 符合预期；
- N5、N11：各精确两门红；
- 恢复后 hash 全等。

六轮 LOW 已闭合，未发现新的 G3-4 语义缺口。

## 七、回归与验收单一致性

核心结果均复现：

- 契约 `44 passed + 1 skipped`
- golden `13 passed`
- 既有账本 `6 passed`
- 合跑：**63 passed + 1 skipped，10 warnings，exit 0**
- UAT 扩面 11 文件：**191 passed，2721 warnings，exit 0**
- 现网账本：23 行、exit 0、零 WARN/FAIL，前后 SHA256 均为 `f78b99f…c11de`
- 七笔提交 blob 恒定：
  - `learning_event_log.py`：`28cdaa18602b…`
  - `fsrs_manager.py`：`980b3758758b…`

两份 UAT 的主测试计数正确，但证据声明不完全一致：

- [G3-4 存证:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-4-evidence/g3-4-negative-verification.txt:3) 仍记录父 HEAD `026d0735`，不是 `2c8dc517`；其 test/manifest/vector SHA 与当前 bytes 相等，本轮 exact-HEAD 隔离重跑补足了行为证明。
- [G3-4 UAT:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:121) 的“在当前 HEAD 重跑”不符合已提交存证头，属 **NEW-FINDING / MEDIUM（证据锚点）**。
- G3-1 UAT 仍写 vault 矩阵 18 形态，当前实际为 23；测试 docstring 还写“11 种、重复键取首项”，属 LOW 文档漂移。
- `g3-round6-counterexamples.txt` 未包含 A4/degraded 复验，却被 UAT 宣称为“全部点名反例通过”，属 MEDIUM 证据声明。
- 工作树未被本轮修改；仅保留审阅前已存在的未跟踪 round7 文件。

## 残留 BLOCKER/HIGH

- **BLOCKER ×1**
  - A4 exactly-once 复合缺口：接管证明未与 epoch/owner 原子绑定；duplicate 等价面只含 payload。

- **HIGH ×3**
  1. 三态 executable contract：stability 域、整数词法及重复键边界不正确；
  2. degraded canonical reducer/proof 尚不可机械唯一复算；
  3. vault_id 状态机仍可对合法 YAML 静默错绑。

生产锁、parsed 查重、短写处理、duplicate apply 门及 bridge 偏差：**STILL-OPEN / 已移交 G3-2/G3-3 / 不计 CARD-G3-1 残留**。

**最终裁定：需八轮。CARD-G3-1 不可验收；CARD-G3-4 保持 CONFIRMED-CLOSED。**

本会话未暴露 `graphiti-canvas`，因此无法执行其记忆检索协议；不影响上述本地 exact-byte、真实入口和回归证据。


