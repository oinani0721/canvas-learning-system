# 第四轮终裁

**需五轮，当前不可验收。**  
精确审阅对象为 `e3337504a5df1e266987b4f6b0397c4fab00203f`。第四笔提交确实补上多项第三轮点名规则，但仍残留 **BLOCKER ×1、HIGH ×5**。

| 审阅点 | 判定 |
|---|---|
| 一、§6.2 状态机 | **STILL-OPEN** |
| 二、review/1 校验器 | **STILL-OPEN** |
| 三、golden 回归断言 | **STILL-OPEN** |
| 四、MEDIUM 与负验证 | **NEW-FINDING** |
| 五、回归、账本、blob、UAT | **NEW-FINDING** |

## 一、状态机：STILL-OPEN

- a) A5 原反例 **CONFIRMED-CLOSED**：文档要求整秒，validator 也拒绝小数秒，见 `e3337504:docs/learning-events-schema-v1.md:122`、`validate_learning_events.py:226-235`。
- 但端到端时间口径仍 **HIGH**：[fsrs_bridge.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/scripts/fsrs_bridge.py:50) 会把 naive 时间静默当 UTC，并截掉微秒；validator 又允许省略秒和任意合法 offset。`18:00+08:00` 与 `10:00Z` 是同一瞬间，字符串比较却会误判 pending；反向 offset 也能漏掉真实较新的事件。§6.2 没有冻结“W 比较和排序必须按 aware UTC instant”。
- b) A4 宏观序列已写全，但并发协议仍是 **BLOCKER**。`锁/CAS` 不能当等价互斥；两个写者可在同秒都 durable append，胜者发布 `W=t1` 后，败者事件因 `review_time == W` 永久不进 pending。A3 的“等时改成 W+1s”又与移交的“等时拒绝/复合排序”未定一。CAS 冲突后的“全事件重折叠”也没有冻结基线、应用游标及掉电耐久语义。G3-3 原卡仍只写基础 last_review/revision 比较，见 [总账](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:283)。
- c) 三态按字段存在性形式覆盖，但语义仍有灰区，**HIGH**。仅含 `fsrs_last_review` 会被文档判“正常卡”，bridge 却因无 `fsrs_due` 当 New；真实复算结果与空字段完全相同，重新进入 Learning、due `+10m`。`due+W` 缺 state、非法/空 W 等也未 fail-closed。
- d) pending 排除 out-of-order、A3 只限在线写、迟到补录不推进，这三项文本冲突已闭。但 `out_of_order` 的位置、类型和真假语义未冻结；字符串或对象值均零违规。degraded pending 如何阻塞/恢复也未定义，仍可能遗漏或重复应用。

## 二、校验器：STILL-OPEN

已闭合：marker、挂载点、`grade_norm`、rating-grade 自洽、弃答恒 1、同仓 manifest 真值比较均真实生效。

- **HIGH：vault 身份未绑定。** `validate_learning_events.py:243-246` 只检查非空，`validate_file():380-455` 从未把账本路径/vault 身份送入规则。构造 `vault_id="evil-other-vault"` 得到 `([], [])`，等价 CLI exit 0，违反 schema `:92` 的“与文件位置互证”。绑定源应是同目录 `.canvas-config.yaml`；不能直接比较 basename，因为当前目录是 `canvas-vault`，配置 ID 是 `canvas_vault`。
- rating 当前与 bridge **逐档等价**：百万点网格加三个阈值两侧复算，0 mismatch。只是 HEAD 没有直接交叉锁；当前未提交测试才新增该门。
- manifest 不可达的 WARN 只适合作为非权威 standalone lint。canonical 仓内 manifest 缺失、损坏或空对象也会 WARN+exit 0，不能作为 CI/验收 PASS；非空 list/scalar 还可能 traceback。判 **MEDIUM**。
- 未复现已新增规则对合法 review/1 行的误报；现网账本也无 WARN。未知 `schema_ext` 被拒属于当前 v1 的显式 fail-closed 约定。

## 三、golden 断言：STILL-OPEN

第三轮三项均 **CONFIRMED-CLOSED**：[测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:189) 已锁 scheduler 全字段、逐步时刻 skeleton、`expected` 类型；当前 manifest/vectors 可由真实 fsrs 6.3.1 两次字节级复算。

但有一个新 **HIGH**：

- retrievability 只检查三时点升序唯一，然后信任 JSON 自带的 `steps/at/expected`；`retrievability.card` 完全未读。把历史改成 Easy@T0、采样改 due+1/+2/+3 并用真实库同步 expected，或单独把 `card` 换成 bogus object，仍 **12/12 passed**。因此“due/+7/+30 已冻结”“golden 任意误改必红”不成立。

另有 **MEDIUM**：`state_before_final_review=true` 仍全绿，因为 bool 与整数 1 相等。manifest 的 `card/frozen_on/generator`、description 和完整键集未锁为 LOW。

## 四、MEDIUM 与负验证：NEW-FINDING

- offset 分钟范围、深层 `RecursionError`、`Z/+00:00` 同瞬间比较：**CONFIRMED-CLOSED**。直接复算 20 万层坏行后仍继续报告第二坏行。
- [negverify_v4.sh](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-4-evidence/negverify_v4.sh:19) 语法有效；存档确为 196 行；健康环境原样复跑 N0+N1–N12，13 个判定全部一致、exit 0。
- 但证据门仍 **PARTIAL / MEDIUM**：
  - `expect_gates` 每次启动 pytest 三遍；
  - 只数 `^FAILED`，不校验 pytest exit code、ERROR、collection 数或完整 12 门；
  - 实测 pytest collection error 时，N0 仍打印“判定符合预期”；
  - mutation/restore 不查成功，终态 SHA 只打印不机器比较；
  - 存档 HEAD 是父提交 `4de42f69`，虽 test/manifest/vector SHA 与 e333 精确 bytes 一致。

## 五、回归、账本与 UAT：NEW-FINDING

- 精确 HEAD 三文件：**53 passed + 1 skipped + 10 warnings**：
  - 契约：**35 passed + 1 skipped**，共 36 collected；所以“36 passed +1 skipped”**不能复现**。
  - golden：**12 passed**。
  - 既有账本：**6 passed**。
- UAT 的扩面回归可复现：核心六文件 **91/91**，扩面五文件 **100/100**，合计 **191/191**。
- 主仓现网账本当前 **23 行**；精确 e333 validator exit 0，仅 PASS、无 WARN/FAIL；运行前后 SHA 均为 `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`。
- 四笔提交 blob 恒定，**CONFIRMED-CLOSED**：
  - `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
  - `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`
- UAT 问题：
  - G3-1 的 35+1、53+1 正确；“vault_id 不符已全部 FAIL”错误；22 行只是历史存证，已不是当前 live。
  - G3-4 技术表仍写 v3/N1–N9/11 passed/已删除的 `negverify_v3.sh`，与后文 v4/12 passed 自相矛盾；“任意 golden 篡改必红”被 retrievability 反例推翻。
  - ruff 对两卡交付文件通过；whole backend 仍有两项既有 F821，UAT 的 `ruff All checks passed` 未注明范围。

## 残留 BLOCKER/HIGH

- **BLOCKER ×1**：A4/CAS/等时/应用游标/折叠基线/账本耐久组成的 exactly-once 并发协议未闭合。
- **HIGH ×5**：
  1. W 与 review_time 的 UTC instant 规范、bridge 输入精度未端到端锁定；
  2. “正常卡”未要求完整、可解析且状态一致的 FSRS tuple；
  3. `out_of_order`、补录和 degraded pending 语义未机械冻结；
  4. `vault_id` 与账本所属 vault 未绑定；
  5. retrievability 历史、采样点和 card 快照可协调漂移而全绿。

审计未修改仓库；临时快照已清理。工作树原有及审计期间出现的未提交 validator/test/schema/report 变化均未纳入 `e3337504` 结论。`graphiti-canvas` 本会话未暴露，无法执行其检索/记录；不影响以上 Git 对象与本地测试复算。


