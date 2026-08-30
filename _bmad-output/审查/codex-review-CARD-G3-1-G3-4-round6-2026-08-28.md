## 第六轮终裁

**需七轮，不可验收。**

已按[总账卡定义](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:247)拆分边界：CARD-G3-1 只负责文档、schema、校验器。生产 bridge/backend 未实现之处只记为 G3-2/G3-3 已移交，不计入本卡残留。

精确 HEAD 为 `026d07351ae6bd5d7a230ff1e086bf0400002cf4`。本卡残留为 **BLOCKER ×1、HIGH ×3**。

### 逐点裁定

1. **A4：STILL-OPEN / BLOCKER / 属本卡契约**

   [A4.1–A4.5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:138)仍不足以描述 exactly-once，存在四组可达反例，合并计一个复合 BLOCKER：

   - [§二仍冻结 event_id 子串查重](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:23)。已有事件 payload 含字符串 `"quiz:E"` 时，真实 `event_id="quiz:E"` 会被误判 duplicate，结果是**零次落账**。A4.5 只写“查重”，未冻结 parsed-field equality，且与“改变幂等语义必须升 v2”冲突。
   - [A4.1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:141)允许 `pid/时间戳 + 超时接管`，却无 owner-death 证明或 fencing。A 暂停超过超时、B 接管并发布、A 恢复后仍可发布旧状态，形成双持与回退。
   - [A4.5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:147)把 `PIPE_BUF` 用于普通 JSONL 文件不成立；普通文件 `write` 仍可能短写。未要求检查返回字节数、处理部分尾行及重启对账。
   - duplicate 命中后缺少状态推进门：未定义“同 ID 同 canonical payload 仅恢复/no-op；同 ID 不同 payload 冲突 fail-closed；绝不再次 apply”。

   生产锁、fsync、增量重放尚未实现：**STILL-OPEN / 已移交 G3-3 / 非本卡**。但接收卡面目前仍只写锁/CAS，尚未吸收五项完整条款。

2. **时间：CONFIRMED-CLOSED（原 HIGH，契约主口径）+ NEW-FINDING / MEDIUM**

   [UTC instant 比较、排序及 A6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:121)和校验器的整秒、UTC 归一化、瞬间相等检查已闭合原 HIGH。

   bridge 的 offset 不转 UTC、naive 默认为 UTC、小数秒截断，均已正确登记：**STILL-OPEN / 已移交 G3-2 / 非本卡**。

   新 MEDIUM：`9999-12-31T23:59:59Z` 仍被校验器接受，但真实 Scheduler 增加 interval、以及 A3 的 `W+1s` 均抛 `OverflowError`。契约尚缺可调度时间上界/推进余量。

3. **三态：STILL-OPEN / HIGH / 属本卡契约**

   [当前 state 相容规则](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:107)仍接受不可执行或非 canonical tuple：

   - `state=3`、S/D 正常但缺 step：文档判正常，真实 review 抛 `AssertionError`。
   - `state=2, step=0`：成功但持续写回非 canonical Review tuple。
   - `state=1, step=0, S=D=0`：规则接受有限值，真实调用抛 `ZeroDivisionError`。
   - 正有限 `S=D=1e308`：规则接受，真实调度产生 NaN 路径并失败。

   仍需冻结 state=3 的 step、state=2 禁 step、state=1 的 S/D 成对/domain，以及可执行数值域或真实构造/调度有效性门。

4. **degraded 解冻：STILL-OPEN / HIGH / 属本卡契约**

   [§156–160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:156)方向正确，但“可证明起点”和事件 E 尚不可机械执行：

   - proof 未绑定 vault/node、账本 cursor 或 prefix hash、库版本和完整 scheduler 配置；
   - 未规定 E 必须是最后一个适用事件；W 只有 timestamp，无法表示损坏账本中的同瞬间 line-order；
   - `degraded:*` 无算法身份，不能自动进入确定性证明链；
   - 未冻结 canonical reducer 的逐事件持久化舍入边界。

   实测三次 Good：每步经真实 bridge 四位舍入后折叠得 stability `10.9711`；连续内存折叠、只在末尾舍入得 `10.9710`。两者都满足当前“折叠到 E”，故边界不唯一。

5. **vault_id：STILL-OPEN / HIGH / 属本卡 validator**

   [_vault_id_of()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:229)仍会对合法 YAML 静默错绑，CLI 无 WARN 且 exit 0：

   - `vault_id: team#1`：PyYAML=`team#1`，校验器=`team`。
   - 双引号 `\u0023`：PyYAML 解码为 `#`，校验器保留字面转义。
   - 早先单行值后跟 block-scalar 同名末项：PyYAML 取末项，校验器退回早项。
   - 多行引号内容中的列首 `vault_id:` 会被误认成顶层键。

   因而“重复键取末项”只在所有 occurrence 都被正则识别时成立；保守白名单尚不能保证不误绑。当前仓库的简单单行配置不受影响。

6. **G3-4：CONFIRMED-CLOSED**

   在声明范围——fsrs `6.3.1`、fuzz off、固定 5×4 向量和三点 retrievability——未发现可保持 13/13 全绿的语义级漂移。[结构门及重放门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:263)均有效；第五轮四类反例均会翻红。

   仅余 **LOW**：每个 `retrievability.at` point 的子键集未锁，[加入未知键仍可全绿](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:425)。这是结构覆盖缺口，不构成语义曲线漂移。

7. **回归核心：CONFIRMED-CLOSED；证据链：STILL-OPEN / MEDIUM**

   当前 HEAD 实测：

   - 契约：`42 passed + 1 skipped`
   - golden：`13 passed`
   - 既有账本：`6 passed`
   - 合跑：**`61 passed + 1 skipped`，10 warnings**
   - 验收单扩面：**`191 passed`，exit 0**
   - 现网账本：23 行，validator exit 0，只有 `RESULT: PASS`，零 WARN/FAIL；前后 SHA256 均为 `f78b99f…c11de`
   - 六笔提交中 `learning_event_log.py` blob 恒为 `28cdaa18…`，`fsrs_manager.py` 恒为 `980b3758…`

   两份验收单的主计数与实测一致。但 G3-4 的 SHA-bound 负验证声明不实：

   - [UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:31)称证据已绑定当前 bytes、脚本 exit code 能反映有效性；
   - [存证](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-4-evidence/g3-4-negative-verification.txt:3)仍是 HEAD `4de42f69`、旧 test SHA、`12 passed`，当前 test SHA 为 `cf34824c…`;
   - [脚本](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-4-evidence/negverify_v4.sh:16)只 grep `FAILED`，不校验 pytest ERROR/collection、mutation/restore 退出码，也只打印而不比较终态 SHA。

### 残留 BLOCKER/HIGH

- **BLOCKER ×1**：A4 exactly-once 契约复合缺口——parsed-ID、锁接管 fencing、普通文件短写恢复、duplicate 状态门。
- **HIGH ×3**：
  1. 三态仍接受不可执行/非 canonical tuple；
  2. degraded proof boundary 与 canonical reducer 未冻结；
  3. vault_id 正则仍可合法 YAML 静默错绑。

生产层另有 bridge 三项和 G3-3 五项 **STILL-OPEN，但均已移交，不计 CARD-G3-1 残留**。

审阅未修改任何文件。工作树仅有审阅前已存在的未跟踪 round6 文档；`CURRENT_TASK.md` 仍写“五轮整改待提交”，属 LOW 状态漂移。项目要求的 `graphiti-canvas` 工具本会话未暴露，无法执行其记忆检索，不影响上述本地证据裁决。
