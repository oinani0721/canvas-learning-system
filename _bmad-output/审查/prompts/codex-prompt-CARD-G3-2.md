# CARD-G3-2 对抗性审查 round-3（第八批 W7 · 最终轮）

你是独立对抗审查者。第 **3** 轮（卡文上限最后一轮）；round-2 裁定「需整改」（3 BLOCKER + 4 HIGH + 1 MEDIUM），全部整改完毕，本轮专核整改与残留。

被审工作在这个 git worktree（未 commit）：

    WT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger

卡文（只读，在编排 worktree）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W7.md`

## 你只读以下文件

1. `WT/canvas-vault/.claude/skills/quiz-answer/SKILL.md` — 主写点（Step 4c 主 PYEOF 块）
2. `WT/canvas-vault/.claude/scripts/fsrs_bridge.py`
3. `WT/backend/app/services/learning_event_log.py`
4. `WT/backend/tests/regression/test_g3_2_review_ledger.py` — 现 25 门
5. `WT/docs/learning-events-schema-v1.md` §6.1-§6.3
6. `WT/_bmad-output/审查/codex-review-CARD-G3-2-round2.md` — 你上一轮的报告

## round-2 发现 → 整改对照（逐条复核）

| # | round-2 发现 | 整改方式 |
|---|---|---|
| B-a | F1 在 A2 与 envelope 门之前早退（吞冲突事实 / degraded pending 永不恢复） | 分诊重排：**已应用判据改为 W >= durable.review_time**（F1 只是 calibration 域证据）。dup 存在时 envelope 门**最先**执行（对已应用 no-op 与恢复两态都生效）；已应用+f1 → no-op；已应用+非 f1 → fail-closed（补齐会引入顺序错乱，人工裁定）；未应用 → 恢复路径（f1=T 只补 FSRS 防 EMA 双吃 / f1=F 全套补齐）。门㉑（degraded 遗留重试：FSRS 补齐+EMA 不双吃+账本 1 行）、门㉒（完整应用态换事实必须拒）锁定 |
| B-b | envelope 门自抄 fsrs 两键与 attempt_count（篡改穿透） | **fsrs 两键显式排除出等价面**（环境快照非评分事实——durable 行身份完整性由校验器 golden manifest 绑定门承担，门㉕锁定该分层：身份篡改 envelope 放行 + validator FAIL）；**attempt_count 按态独立复算**（已应用/degraded 遗留态 frontmatter 已是 durable 值；崩溃窗口①态 = 前置值+1） |
| B-c | A2 不拒绝全文件重复 event_id（双行会二次 apply） | 账本读取后做**全文件 event_id 唯一性检查**，重复 → fail-closed 拒写人工修复。门㉓锁定 |
| H-a | abandoned 分支绕过严格 rating 门 | 显式 rating 的类型/范围验证提到 abandoned 分支之前（无论是否 abandoned 都先验）；新增自洽门：abandoned=true 且 rating!=1 → 拒（§6.1 弃答恒 1）。门⑰补 abandoned rating=1.5 与 rating=3 两变体 |
| H-b | 门②未做到「逐字节相同」（last_examined/calibration.ts 用了重试 ts） | **全部副作用以 durable.review_time 为业务时刻基准**：mastery 计算抽函数（恢复路径传 review_time）、calibration ts、last_examined 统一；门②升级为**整节点字节对拍**（恢复产物 sha == 直接应用产物 sha） |
| H-c | _fm_has_event 不反解转义引号（假阴性 → 双重副作用） | 双引号 scalar 用 `json.loads` 与写侧 json.dumps 同源反解；单引号/裸词剥引号。门㉔（含 `\"` 转义形态的 eid 重跑必须幂等零写） |
| H-d | LF 守卫在零字节文件 seek(-1) 抛错 → append_event 返回 False | 守卫改 `path.stat().st_size > 0` 才读尾字节。门⑳补空文件首写变体 |
| M-a | 单写者声明范围过窄（「同一节点」） | 改为「同一 vault 内不得并行运行任何两个 quiz-answer（账本 per-vault 共享，与节点无关）」 |

## 本轮审查要求

1. 逐条复核上表整改（引用整改后代码行）。
2. 重点扫新状态机的分支完备性：dup∈{None,有} × f1∈{T,F} × fsrs_applied∈{T,F} 六格，每格行为是否明确且与契约一致；envelope 门的 attempt 按态复算在两态切换时是否自洽。
3. 正常路径回归：25 门有没有被整改改坏。
4. 六项审查重点最终结论（写序 / A2 / 查重 / 哨兵 / 边界 / fixture）。

## 输出格式

    [BLOCKER|HIGH|MEDIUM|LOW] <文件>:<函数或行> — <问题一句话>
    依据: ...
    建议: ...

最后一行：`VERDICT: PASS` 或 `VERDICT: 需整改`。没有 finding 的项写「未发现」。
