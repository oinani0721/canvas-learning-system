# UAT · CARD-G3-2b — 清除 R1-R7 并闭合 write-ahead 六格状态机

> `[BATCH-2026-09-01-第九批 / CARD-G3-2b]`
> 车道 `card/w7-ledger`，开工 HEAD `02dbc426fb22018eb14cfda46d098c1b02126dab`。
> 前身：CARD-G3-2（第八批，三轮到顶停轮，留 R1-R7 残留）。

## 一句话：这张卡让你多了什么

上一张卡把「先记账、再改节点」的写序做出来了，但 Codex 第三轮用真实生产入口打穿了 7 个洞。
**这张卡把 7 个洞全堵上**，其中一个是你日常会撞到的：

> **翻旧检验白板重跑一次旧评分，之前会报「envelope 冲突」而拒绝**（不损数据，但看着像坏了）。
> 现在原样重跑 = 静默幂等跳过，什么都不改，跟契约要求的一致。

其余 6 个都是**账本被外部工具写坏**时的防线：坏行、坏时刻、坏评分不再被工具「顺手洗干净」后照常应用，而是停下来报错等你处理。

---

## ⛔ 开始验收前：本卡没有上线，无法在 Obsidian 里验

本卡改的是 worktree 里的 `quiz-answer` skill 与 fsrs 桥，**没有部署到 live vault**（手册 §四.1 第 2 条：live vault 只读，不得把 worktree skill 部署到 live）。
你在 Obsidian 里跑 `/quiz-answer` 用的仍是主仓那份旧代码。要验证只能走下面的 fixture 路径。

---

## 你要做的验收（4-B · fixture 路径，约 3 分钟）

`fixture 路径尚未部署`——以下命令跑的是隔离 tmp 目录，不碰你的任何真实笔记。

**第一步**，在终端粘这一条，看最后一行是不是 `R1-R7 全部 fail-closed / 幂等 — 裁判 2 PASS`：

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python backend/scripts/g32b_r1r7_counterexamples.py
```

它会把 7 类坏账本喂给**逐字提取的真实生产写点**，逐条打印真实退出码。你重点看这三行：

- `R3/历史事件重跑` —— 应显示 `rc=0` + `幂等跳过` + `节点未改=True`（这就是上面说的、你会撞到的那条）；
- `R1/out_of_order (旧实现完整穿透链)` —— 应显示 `rc=1` + `fsrs_fields={}`（旧实现在这里是 `rc=0` 却把节点的复习调度字段写空了）；
- `R4/字节对拍` —— 应显示 `字节相同=True`（「中途崩了再跑一次」与「一次跑成」产出的节点文件必须一个字节都不差）。

**第二步**，确认账本本身仍然合规：

```bash
cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/validate_learning_events.py /private/tmp/card-g3-2b-fixture/learning_events.jsonl
```

期望：`RESULT: PASS`，退出码 0。

**要重建 fixture**（第二步的文件被删了）：`PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python backend/scripts/g32b_build_fixture.py`。

---

## 我已经代你跑完的（4-A · 技术项，全部真实执行）

| # | 判据 | 结果 | 证明了什么 / **不**证明什么 |
|---|---|---|---|
| 1 | **开工基线实收**（HEAD `02dbc426` 临时还原后 `--collect-only`） | `255 collected` / `254 passed, 1 skipped` | 基线是实收的，不是照抄历史数字。还原用备份 + `finally` 恢复，4 文件恢复后**逐字节相同** |
| 2 | **裁判 1** 五文件回归 | `263 collected` / **`262 passed, 1 skipped`**（+8 门，零回归） | 新增 8 门全绿且原 254 门无一变红。**不**证明整仓其它测试 |
| 3 | **裁判 2** R1-R7 生产入口反例（`g32b_r1r7_counterexamples.py`） | **19/19 PASS** | 用逐字提取的生产 PYEOF 块跑真实反例，含 4 条**验伪对照**（合法输入必须仍然通过），故不是「恒拒」的假门。**不**证明并发 |
| 4 | **裁判 3** validator 跑 fixture | `RESULT: PASS`，`rc=0` | fixture 由真实生产写点跑出（两次评分 E1/E2），非手写样例 |
| 5 | **变异验证**（`g32b_mutation_gates.py`，串行） | **10/10 KILLED**，10 次还原全部**逐字节相同** | 每个变异把生产代码**精确退回旧实现形态**，判据是**指定的那道门**必须变红。**不**证明门集覆盖了未被想到的缺陷 |
| 6 | **六格状态机逐格闭合**（门㉝） | 6 格全部断言终态通过 | round-3 判 3 格 FAIL + 1 格 PARTIAL，现逐格构造真实前置态并断言。**不**证明格间竞态（无锁） |
| 7 | **写点普查门**（门⑪）+ 全仓 grep | PASS；账本写点仍是 4 处（`quiz-answer` / `start-exam-board` / `ai-linked-doc` / `learning_event_log.py`） | 本卡未新增第三套实现，未动其它 skill 写点 |
| 8 | **live vault 零写** | 账本 `2a18023e…`（22 行），mtime `2026-08-29T06:11:47+0800` | mtime 远早于本 session（2026-09-02），**观测范围内**零写。**不**证明其它进程未写 |

### 七项残留的修法（逐条）

| # | 级别 | 根因 | 修法 | 承重门 / 变异 |
|---|---|---|---|---|
| R1 | BLOCKER | envelope 的 candidate 以 durable payload 为底 spread（`{**_dpl, ...}`），未知额外键被**自抄**⇒ 比较退化成「自己比自己」 | candidate **独立字面构造**成固定生产键集；键集本身进入等价面，多一键/少一键/值不同一律冲突 | 门㉖ / M1 |
| R2 | BLOCKER | A2 消费小数秒 durable `review_time`，bridge 入口截整秒写 `W` ⇒ `.500 > .000` 恒真，同一行反复二次推进 | `_durable_instant()` 在**适用集构造时逐行**强制 tz-aware + UTC 偏移 0 + 无小数秒，**只验不改** | 门㉗ / M2a·M2b |
| R3 | HIGH | 已应用态的 attempt 复算直接取 frontmatter tip ⇒ 把后继事件的计数当成历史事件的 | 沿账本回推 ordinal：`A_now − 其后已应用数`（未应用态 `A_now + 1 + 其前 pending 数`） | 门㉘ / M3 |
| R4 | HIGH | 正常路径 mastery 闲置折旧基准用 `p["ts"]`，恢复路径用 durable `review_time` | 正常路径同样改用 `review_time`（与 `last_examined` / calibration.ts 同源） | 门㉙ / M4 |
| R5 | HIGH | 显式 rating 只验类型与 abandoned，不验与 `grade_norm` 自洽 | bridge 在 apply 前机械复算 `rating_from_grade(grade_norm, abandoned)` 并要求相等（abandoned 分项被此门包含） | 门㉚ / M5 |
| R6 | MEDIUM | 两个身份键排除出等价面的裁决只活在实现与门㉕里，契约 §6.2 原文只排除 `recorded_at` | §6.2 回写三条：身份键归属（validator golden manifest 绑定门）+ candidate 独立构造禁令 + A5 消费侧强制 + A4.5 截断判据 | 门㉜ / M7 |
| R7 | MEDIUM | 尾行容错只看「最后一行解析失败」，带终止 LF 的完整损坏行也被当截断容忍 | 读取时保留 EOF 的 LF 状态；**只有**「最后一行 **且** 文件不以 LF 结尾」才算截断 | 门㉛ / M6 |

### 六格状态机终态（对照 round-3 §六格状态机）

| 状态 | round-3 | 本卡终态 | 依据 |
|---|---|---|---|
| `dup=None, f1=F` | PARTIAL（foreign pending 输入门不完整） | **PASS** | R2 + R5 补齐 foreign pending 的时刻门与 rating 自洽门；门㉝格1 / 门㉗② / 门㉚ |
| `dup=None, f1=T` | PASS | **PASS** | 旧写序孤儿整体 no-op；门㉝格2 / M9 |
| `dup有, f1=T, applied=T` | FAIL（历史 attempt 误拒） | **PASS** | R3 ordinal 回推；门㉝格3 / 门㉘ / M3 |
| `dup有, f1=F, applied=T` | PASS | **PASS** | 顺序错乱无机械判据 → 人工裁定 fail-closed；门㉝格4 / M8 |
| `dup有, f1=T, applied=F` | FAIL（小数秒可重复推进） | **PASS** | R2 只验不改；门㉝格5 / 门㉗ / M2a |
| `dup有, f1=F, applied=F` | FAIL（额外键跳过 A2 且字节不等） | **PASS** | R1 + R4；门㉝格6 / 门㉖ / 门㉙ |

> round-3 的补充观察「一旦 `W` 被后续事件推进到 `W > durable.review_time`，状态切换即失去自洽」——这正是 R3 描述的历史事件面，已由 ordinal 回推口径消解（门㉘ 的 `E1→E2→重跑E1` 就是该场景的最小复现）。

---

## Codex 审查处置

<!-- 审查绑定 final commit；round 结果落地后回填本段 -->
（见下方「证据位置」的 `codex-review-CARD-G3-2b*.md`；round 结论与逐条处置在审查完成后回填。）

---

## 如实边界声明（本卡未证明什么）

1. **并发面仍不成立**（最重要，与前卡同）：本卡**没有实现任何锁**，G3-3 的 per-node sidecar 锁 / fencing epoch / per-vault 账本锁一项未做。单写者（同一 vault 内不并行跑任何两个 `quiz-answer`）是本卡正确性的前提。两个 writer 同时跑，本卡的所有 fail-closed 判据都可能在「读—算—写」的间隙被绕过。
2. **跨日 / 长期运行未证明**：所有反例都是单次进程内的确定性构造，没有跨日调度、没有真实 launchd 推送链路参与。
3. **live 部署未做**：worktree 的 skill/bridge **没有**复制到 live vault，本卡不改变你在 Obsidian 里的实际行为。
4. **耐久性只到调用序列**：`write→flush→fsync→replace` 的调用顺序被 spy 门锁住，但**不**证明真实断电后数据存活。
5. **R2 的作用域是本节点的适用集**：整秒/UTC 强制只施于「本节点 + `schema_ext=review/1` + 未标 `out_of_order`」的行——即参与 `W` 比较、决定 pending 与否的那一集合。别的节点的历史脏行不阻塞本节点评分（否则一条脏数据会锁死整个 vault）；标了 `out_of_order` 的行不参与 `W` 比较，故不校验。这是**有意的窄化**，不是漏网。
6. **A2 重放仍只恢复 FSRS**：mastery（衰减 Beta）与疑问 callout 没有事件载荷可复放。跨事件 pending（别的板的事件）恢复时其 mastery 副作用**永久丢失**，只有 FSRS 被补上——与前卡同，本卡未改变。
7. **`learning_event_log.py` 本卡未改**：R7 修的是 `quiz-answer` 读账本的判据。backend 通用 `append_event()` 的坏行处理是「warning + 跳过该行」（查重不把坏行算作命中），它不做「截断容忍」声明，故不在 R7 射程内。如实登记，不代改（卡文限定只允许尾行/查重最小修正）。
8. **门集不等于穷尽**：变异 10/10 只证明**这 10 个已知缺陷形态**会被指定门抓住，不证明没有第 11 类。三轮审查的历史（每轮修复都会长出新分支）说明这个方向上的清零在对抗范式下不可达。
9. **未自动解锁下游**：本卡未改写 G3-7、G8-4 的总账依赖。
10. **Obsidian 插件是既存第二写路径**：`frontend/obsidian-plugin/src/main.ts` 的 node_derived 直写不在本卡写点门 grep 范围，本卡未动它，沿用前卡登记。

---

## 待你裁决

| # | 事项 | 默认（本卡已按默认实现） | 备选 |
|---|---|---|---|
| ① | 畸形 durable 事件（小数秒 / 非 UTC / 未知额外键 / rating 不自洽 / 带 LF 坏行） | **零写退出 + 报错**，等你人工修账本 | 自动隔离该行继续跑（会在无法证明的基线上叠加，契约禁止） |
| ② | 单写者前提 | **保留**（G3-3 前无锁，同一 vault 内不得并行跑两个 `quiz-answer`） | 现在就实现锁（= 提前做 G3-3，超出本卡范围） |
| ③ | 两个 fsrs 身份键的完整性归属 | **由 schema/validator 明确归属**（排除出 envelope 等价面，完整性交 golden manifest 绑定门）——已回写 §6.2 | 纳入 envelope 等价面（一次合法的库升级会让所有历史事件重放变冲突） |
| ④ | 是否部署到 live | **不部署**（手册 §四.1 第 2 条） | 你确认后另开部署动作 |
| ⑤ | R2 的作用域窄化（边界声明 5） | **只施于本节点适用集** | 全账本所有 `review/1` 行（一条别节点的脏行会锁死整个 vault 的评分） |

---

## 证据位置

| 内容 | 路径 |
|---|---|
| 卡文（只读） | `…/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第九批-goals/W7.md`（SHA256 `5accbca8…3eb287f8`） |
| 前卡 UAT / round-3 | `_bmad-output/验收单/UAT-CARD-G3-2-复习事件账本write-ahead-2026-09-01.md`、`_bmad-output/审查/codex-review-CARD-G3-2-round3.md` |
| 生产改动 | `canvas-vault/.claude/skills/quiz-answer/SKILL.md`、`canvas-vault/.claude/scripts/fsrs_bridge.py` |
| 契约回写 | `docs/learning-events-schema-v1.md` §6.2（A4.5 duplicate 门 / A4.5 短写段 / A5） |
| 行为门 | `backend/tests/regression/test_g3_2_review_ledger.py` 门㉖-㉝ |
| 反例复现脚本 | `backend/scripts/g32b_r1r7_counterexamples.py` |
| fixture 生成脚本 | `backend/scripts/g32b_build_fixture.py`（`--check` 复算 sha） |
| 变异脚本 | `backend/scripts/g32b_mutation_gates.py` |
| fixture sha256 | `learning_events.jsonl` `8838ce3a5859213d68bc0ac0fa06dd2536d940aac81ac75b46503291df0872c7`；`.canvas-config.yaml` `6444cad8deb0cd6c0224076f375176a57635056cd7188085ace169ee07f02ddd` |
| 开工登记的 3 个 untracked stderr | `codex-review-CARD-G3-2-round{1,2,3}.stderr` = `8e5820dc…`、`e2f09b74…`、`c6a770f2…`（前卡 CARD-G3-2 产物，本卡未删未改） |
