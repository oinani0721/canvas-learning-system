终裁：**需四轮，当前不可验收**。HEAD 已绑定为 `4de42f69f79e275d5b6460797ca40a763858b38a`。第三笔提交未真正清零，残留 **1 个复合 BLOCKER + 3 个 HIGH**。

## 1. BLOCKER：A1/A2/A3 状态机

- **CONFIRMED-CLOSED（有条件）**：单进程、整秒时间、原子状态发布时，A2 确实会先恢复 E1 再允许追加 E2，原二轮交错反例被阻断。
- **STILL-OPEN / BLOCKER**：多进程可同时看到 `pending=[]` 并从旧状态计算。当前契约没有要求锁/CAS 覆盖完整的“扫描 pending → durable append → apply → 原子发布”临界区；[§6.2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:106)声称“构造上不可能”过强，[G3-3 卡面](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:283)也未规定 CAS 冲突后的全事件重折叠。
- **NEW-FINDING / BLOCKER**：小数秒导致真实二次推进。校验器允许 `10:00:00.500000Z`，[bridge](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/scripts/fsrs_bridge.py:55)却把 W 写成 `10:00:00Z`。实测首次应用后为 Learning、due `10:10`；重放同一事件再次推进为 Review、due `+2d`。
- **STILL-OPEN / HIGH（并入上述 BLOCKER）**：A2 重放崩溃安全未硬性要求六字段与 W 同一原子、durable 发布；现有 `os.replace` 可作为实现基础，但 A2 尚无实现或故障注入证明。
- **CONFIRMED-CLOSED**：字段名确为 `fsrs_last_review`，[FIELD_ORDER](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/scripts/fsrs_bridge.py:44)读写一致。
- **CONFIRMED-CLOSED（仅真新卡、整秒事件）**：完全无 FSRS 字段时 `W=-∞` 首事件路径成立。
- **NEW-FINDING / HIGH（并入 BLOCKER）**：已有 `fsrs_due/state` 但缺 `fsrs_last_review` 的残缺卡也会被当作 `W=-∞`，可能在旧状态上重放全账而二次推进。
- **STILL-OPEN / BLOCKER**：三态不自洽。[pending 定义](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:101)不排除 `out_of_order`；A3 又要求所有新事件 `>W`，与“迟到旧事件仍原时刻入账”冲突；schema 按账本最大时间判乱序，而 G3-3 按最新已应用事件判定。W 丢失后，原本承诺“不推进”的乱序事件还会进入重建。

## 2. HIGH 严格 JSON

- **CONFIRMED-CLOSED**：U+001C、VT、FF、ESC、BOM、裸 NUL、NBSP 均 exit 1；仅 space/tab/CR 等 RFC 合法空白通过。[`rstrip("\r\n")`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:248)修复有效。
- 5–8MB 的合法 JSON 行 exit 0；这本身不是 RFC 绕过，因为契约未设行长上限。
- **NEW-FINDING / MEDIUM**：约 1MB、50 万层合法嵌套触发未捕获 `RecursionError: Stack overflow`，stdout 为空并停止后续行；异常处理目前只覆盖 JSONDecodeError、ValueError 等，[见 261–273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:261)。

## 3. HIGH review/1 跨字段绑定

二轮点名的 `concept_id==node_id`、原字符串 `review_time==effective_at`、版本/hash 形状、degraded 成对/非空已闭合，但整体仍为 **STILL-OPEN / HIGH**。真实 CLI 下列坏行仍全部 exit 0：

- `vault_id` 与账本父 vault/.canvas-config.yaml 不符；
- `rating=4 + grade_norm=0`；
- `answer_abandoned + rating=4`；
- `schema_ext="review/01"` 或非字符串，完全降级为历史行；
- `review/1` 挂在 `session_archived`；
- `fsrs_library_version="999.999"`、hash 为 64 个零，未绑定 manifest 的真实 `6.3.1` 和 hash；
- `grade_norm` 缺失、错型或越界。

根因是扩展门只在 [`schema_ext == "review/1"`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:229)时启动，版本/hash 也只验形状。[manifest 真值](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/fsrs_golden_manifest.json:13)未被加载。

额外 payload 键 exit 0 与“payload 加性扩展”契约一致，**不算缺陷**。另有 **NEW-FINDING / MEDIUM**：同一瞬间的 `Z` 与 `+00:00` 会因原字符串不等被拒。

## 4. HIGH G3-4 矩阵伪装

- **CONFIRMED-CLOSED**：改中间 rating 会使 structure/replay 两门红。
- **CONFIRMED-CLOSED**：互换正式 `scenario+id` 会被场景 offset 锁抓住。
- **CONFIRMED-CLOSED**：expected 故意偏离真实库结果会被 replay 门抓住。
- **STILL-OPEN / HIGH**：前缀时刻仍可伪装。把 `review_ontime__good` 第二步 `00:10→00:05`，再同步最终时刻及真实库 expected，仍 `11 passed`。原因是[时刻门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:225)只锁首步，后续 due 又由已被篡改的 prefix 动态计算。
- **NEW-FINDING / HIGH**：完整 Scheduler 配置可自洽重定向。临时副本仅把 `desired_retention=0.9→0.8`，重算 manifest/vectors/hash，生成器仓库 bytes 不变，结果仍 `11 passed`。测试只独立锁了 21 个 parameters，没有字面锁 retention、steps、maximum_interval、fuzz。
- **NEW-FINDING / MEDIUM**：expected 无类型门，`state=true`、`step=false`、数值 `1.0→true` 后仍全绿，因为 Python bool 与 0/1 数值相等。

## 5. MEDIUM 三项

- **时间词法：STILL-OPEN**。原五个反例均已拒绝，现网 Z、`+00:00`、微秒形态均通过；但非法 offset `+00:60`、`+00:99` 仍 exit 0。正则只检查两位数字，[未限制分钟 00–59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:97)。
- **超长整数：CONFIRMED-CLOSED**。5000 位整数 exit 1，报告解析限额，无 traceback。
- **负验证 v3：STILL-OPEN / MEDIUM（证据质量）**。N1–N9 九个负例计数和失败门数可复算，恢复后 SHA 与 11 passed 属实；但 [`negverify_v3.sh:22`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-4-evidence/negverify_v3.sh:22)版本探针转义错误，存档真实记录 SyntaxError；脚本不校验预期失败，发生错误后仍 exit 0，存档中的部分 mutation 命令也被 echo 成断裂两行。
- **两份验收单：STILL-OPEN / MEDIUM**。
  - G3-1 同时写 `25+1` 与 `29+1`，写“零代码改动”但实际新增 validator/test，且“跨字段全部机械绑定”被上述 exit 0 反例推翻。
  - G3-4 一处称七门、一处仍称五门；“golden 被篡改必红”“间隔不会静默改变”被 retention=0.8 全绿反例推翻。
  - public re-export 与 CI `DEFERRED / NOT-EXECUTED` 措辞现已自洽。
- **SHA 存证仍不准确**：当前 validator SHA 为 `da79a024…`，两份 G3-1 存证仍记录 `13c03c7…`，不能证明当前 validator bytes 被执行。

## 6. 回归与铁律

- **CONFIRMED-CLOSED**：目标三文件合跑得到 `46 passed, 1 skipped, 10 warnings`：
  - 契约：29 passed + 1 skipped
  - golden：11 passed
  - 既有账本：6 passed
- **CONFIRMED-CLOSED**：现网当前 23 行账本 exit 0、零 WARN/FAIL；前后 SHA 均为 `1f7700dd0963592874f4aacbbc5ab629c8542d88c46b58f729ac461dcd458997`。
- **CONFIRMED-CLOSED**：三提交 blob 恒定：
  - `learning_event_log.py`：`28cdaa18602b…`
  - `fsrs_manager.py`：`980b3758758b…`
  - 三段 path diff 均为空。

残留清单：

- **BLOCKER ×1**：applied-watermark/exactly-once 复合状态机仍可多进程漏推进、小数秒二次推进，并与乱序重建语义冲突。
- **HIGH ×3**：
  1. review/1 完整语义绑定与 marker 降级绕过；
  2. G3-4 前缀时刻链可协调伪装；
  3. Scheduler 非 parameters 配置可自洽重定义而全绿。

因此：**BLOCKER/HIGH 未清零，终裁为“需四轮”**。审计全程未修改仓库；既有未跟踪 round3 草稿未触碰。Graphiti 本会话未暴露，无法执行其检索/记录要求。


