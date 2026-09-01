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

**第一步**，在终端粘这一条，看最后一行是不是 `R1-R7 + round-1 后续 N1-N5 全部 fail-closed / 幂等 — 裁判 2 PASS`：

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python backend/scripts/g32b_r1r7_counterexamples.py
```

它会把 12 类坏账本喂给**逐字提取的真实生产写点**，逐条打印真实退出码（29 条判据）。你重点看这四行：

- `R3/历史事件重跑` —— 应显示 `rc=0` + `幂等跳过` + `节点未改=True`（这就是上面说的、你会撞到的那条）；
- `R1/任意未知键` —— 应显示 `rc=1` + `fsrs_fields={}`（旧实现在这里是 `rc=0` 却把节点的复习调度字段写空了）；
- `R4/字节对拍` —— 应显示 `字节相同=True`（「中途崩了再跑一次」与「一次跑成」产出的节点文件必须一个字节都不差）；
- `N1/伪装成乱序的后继` —— 应显示 `rc=1`（这条是审查后新补的：账本里一条被标成「乱序补录」、时刻却比谁都晚的行，旧代码会静默把它排除掉，那次评分的复习调度就**永久丢了且没有任何提示**）。

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
| 2 | **裁判 1** 五文件回归 | `268 collected` / **`267 passed, 1 skipped`**（+13 门，零回归） | 新增 13 门全绿且原 254 门无一变红。**不**证明整仓其它测试 |
| 3 | **裁判 2** 生产入口反例（`g32b_r1r7_counterexamples.py`） | **31/31 PASS** | 用逐字提取的生产 PYEOF 块跑真实反例，含 8 条**验伪对照**（合法输入必须仍然通过），故不是「恒拒」的假门。**不**证明并发 |
| 4 | **裁判 3** validator 跑 fixture | `RESULT: PASS`，`rc=0` | fixture 由真实生产写点跑出（两次评分 E1/E2），非手写样例 |
| 5 | **变异验证**（`g32b_mutation_gates.py`，串行） | **34/34 KILLED**，34 次还原全部**逐字节相同** | 每个变异把生产代码**精确退回旧实现形态**，判据是**指定的那道门**必须变红。**不**证明门集覆盖了未被想到的缺陷 |
| 6 | **六格状态机逐格闭合**（门㉝） | 6 格全部断言终态通过 | round-3 判 3 格 FAIL + 1 格 PARTIAL，现逐格构造真实前置态并断言。**不**证明格间竞态（无锁） |
| 7 | **写点普查门**（门⑪）+ 全仓 grep | PASS；账本写点仍是 4 处（`quiz-answer` / `start-exam-board` / `ai-linked-doc` / `learning_event_log.py`） | 本卡未新增第三套实现，未动其它 skill 写点 |
| 8 | **live vault 零写** | 账本 `2a18023e…`（22 行），mtime `2026-08-29T06:11:47+0800` | mtime 远早于本 session（2026-09-02），**观测范围内**零写。**不**证明其它进程未写 |

### 七项残留的修法（逐条）

| # | 级别 | 根因 | 修法 | 承重门 / 变异 |
|---|---|---|---|---|
| R1 | BLOCKER | envelope 的 candidate 以 durable payload 为底 spread（`{**_dpl, ...}`），未知额外键被**自抄**⇒ 比较退化成「自己比自己」 | candidate **独立字面构造**成固定生产键集；键集本身进入等价面，多一键/少一键/值不同一律冲突 | 门㉖ / M1 |
| R2 | BLOCKER | A2 消费小数秒 durable `review_time`，bridge 入口截整秒写 `W` ⇒ `.500 > .000` 恒真，同一行反复二次推进 | `_durable_instant()` 在**适用集构造时逐行**强制 tz-aware + UTC 偏移 0 + 无小数秒，**只验不改** | 门㉗ / M2b·M10 |
| R3 | HIGH | 已应用态的 attempt 复算直接取 frontmatter tip ⇒ 把后继事件的计数当成历史事件的 | 沿账本回推 ordinal：`A_now − 其后已应用数`（未应用态 `A_now + 1 + 其前 pending 数`） | 门㉘ / M3 |
| R4 | HIGH | 正常路径 mastery 闲置折旧基准用 `p["ts"]`，恢复路径用 durable `review_time` | 正常路径同样改用 `review_time`（与 `last_examined` / calibration.ts 同源） | 门㉙ / M4 |
| R5 | HIGH | 显式 rating 只验类型与 abandoned，不验与 `grade_norm` 自洽 | bridge 在 apply 前机械复算 `rating_from_grade(grade_norm, abandoned)` 并要求相等（abandoned 分项被此门包含） | 门㉚ / M5 |
| R6 | MEDIUM | 两个身份键排除出等价面的裁决只活在实现与门㉕里，契约 §6.2 原文只排除 `recorded_at` | §6.2 回写四条：身份键归属（validator golden manifest 绑定门）+ candidate 独立构造禁令 + A5 消费侧强制 + A4.5 截断判据；round-1 后续再补 N1 的写点侧口径 | 门㉜ / M7·M17 |
| R7 | MEDIUM | 尾行容错只看「最后一行解析失败」，带终止 LF 的完整损坏行也被当截断容忍 | 读取时保留 EOF 的 LF 状态；**只有**「最后一行 **且** 文件不以 LF 结尾」才算截断 | 门㉛ / M6 |

### 六格状态机终态（对照 round-3 §六格状态机）

| 状态 | round-3 | 本卡终态 | 依据 |
|---|---|---|---|
| `dup=None, f1=F` | PARTIAL（foreign pending 输入门不完整） | **PASS** | R2 + R5 补齐 foreign pending 的时刻门与 rating 自洽门；门㉝格1 / 门㉗② / 门㉚ |
| `dup=None, f1=T` | PASS | **PASS** | 旧写序孤儿整体 no-op；门㉝格2 / M9 |
| `dup有, f1=T, applied=T` | FAIL（历史 attempt 误拒） | **PASS** | R3 ordinal 回推；门㉝格3 / 门㉘ / M3 |
| `dup有, f1=F, applied=T` | PASS | **PASS** | 顺序错乱无机械判据 → 人工裁定 fail-closed；门㉝格4 / M8 |
| `dup有, f1=T, applied=F` | FAIL（小数秒可重复推进） | **PASS** | R2 只验不改；门㉝格5 / 门㉗ / M10 |
| `dup有, f1=F, applied=F` | FAIL（额外键跳过 A2 且字节不等） | **PASS** | R1 + R4；门㉝格6 / 门㉖ / 门㉙ |

> round-3 的补充观察「一旦 `W` 被后续事件推进到 `W > durable.review_time`，状态切换即失去自洽」——这正是 R3 描述的历史事件面，已由 ordinal 回推口径消解（门㉘ 的 `E1→E2→重跑E1` 就是该场景的最小复现）。

---

## Codex 审查处置

### round-1（绑定 commit `91aaa11a`）：**正文被内容过滤器拦下，零字节**

`codex exec --sandbox read-only -m gpt-5.6-sol -c model_reasoning_effort=ultra` 跑完 rc=0，但
`codex-review-CARD-G3-2b.md` **0 字节**。stderr（226 KB，已留存）末尾显示：审查者为了跑测试而设
`DEBUG=true`，pytest 的 `Settings` 校验错误把 `.env` 里的 `AI_API_KEY` 值前缀打进了报错文本，
随后连续两次 `ERROR: This content was flagged for possible cybersecurity risk`，正文没能输出。

**这不是「审查通过」，是审查正文缺失。** 按手册 §四.2「正文为空一律不合并」，本卡此刻**不具备合并资格**。

### 但 stderr 保留了完整的推理标题序列，线索没浪费

codex 的 thinking 摘要标题逐条留在 stderr 里（`Identifying out_of_order schema validation issue`、
`Noting LF preservation limitation in text mode`、`Identifying duplicate key handling issue`、
`Assessing line-ending and UTF-8 error handling`、`Examining multiple pending attempt inconsistencies`…）。
我按这些标题**逐条写探针实测**，5 条中 **4 条复现为真缺陷 + 1 条诊断不精确**，全部修掉：

| # | 级别 | 实测复现 | 修法 | 承重门 / 变异 |
|---|---|---|---|---|
| N1 | **BLOCKER** | 外部写入一条标 `out_of_order`、`review_time` 却晚于一切适用事件的行 ⇒ 它被无条件排除出适用集，**该事件的 FSRS 永久丢失且 writer 照常 `rc=0`**（实测 W 只反映本次事件、账本 2 行） | 写点侧补 §6.2 三态语义 round-17 已冻结的语义门：标记行 `review_time > W`（含新卡无 W）⇒ **fail-closed**；并机械强制该键形态（唯一合法值布尔 `true`） | 门㉞ / M11·M12·M17 |
| N2 | HIGH | 账本以**裸 `\r`** 结尾时，文本模式 `open(encoding=)` 的 universal newlines 把它读成 `\n` ⇒ 截断文件被误判「完整写入的损坏行」而 fail-closed（实测 `rc=1`） | 改二进制读 + 显式 `decode`；`_ends_with_lf` 判在**字节**上，与追加侧 LF 守卫同源；行切分严格按 LF | 门㉞ / M13 |
| N3 | MEDIUM | 账本行含重复 JSON 键（如两个 `grade_norm`）时 `json.loads` 静默取最后一个 ⇒ 歧义行被接受（实测 `rc=0`） | `object_pairs_hook` 检测重复键，抛**不继承 `ValueError`** 的 `_DupKey`（否则会被坏行分支吞、末行还会被当截断容忍） | 门㉞ / M14 |
| N4 | MEDIUM | 账本含非 UTF-8 字节 ⇒ `UnicodeDecodeError` 未捕获，抛 traceback（零写但非 clean） | 捕获并 clean fail-closed | 门㉞ / M15 |
| N5 | MEDIUM | 多个 pending 并存（A2 不变量已被外部破坏）时，attempt 序数被**硬算**出一个期望值，碰巧相等就放行 | `_before_pending > 0` ⇒ 报真因 fail-closed，不伪装成 envelope 冲突 | 门㉞ / M16 |

> N1 与 R1 是同一个洞的两半：R1 堵住了「dup 自己带 `out_of_order`」，N1 堵住了「**别的**事件带 `out_of_order`」。
> 契约侧也一并写清了两个口径的分工——**proof/离线审计**侧是「报违规但仍计入适用集」（审计要把事实算全），
> **在线写路径**侧是 fail-closed（它没有权限替用户裁定那行是补录还是后继：算进去会多应用一次 FSRS，排除掉会丢一次评分）。

### round-1 的一个方法论收获（写进证据，不粉饰）

首版变异 M13 打在 `endswith(b"\n")` 上并 **SURVIVED**——因为 `bytes.decode()` 根本不做 universal newlines，
真正的承重点是「二进制读 vs 文本模式读」。变异脚本当场把我对自己修复的错误归因照了出来，M13 已改打在那一处并 KILLED。

### round-2（绑定 commit `cba60fc3`）：**同样被拦，正文仍是 0 字节**

规避措施生效了一半——这次 stderr 里**没有**任何配置值泄漏（`grep AIzaSy` = 0 命中），
审查者顺利跑完了静态核对、写了探针、跑到裁判 2 的 fixture 构建，然后在**要写正文时**
连续两次被同一个内容策略拦下。

**推断的真因（如实，未经证实）**：不是某一条输出，而是**被审内容本身在上下文里累积**。
审查者读了 SKILL.md、UAT、前身 round-3 报告——这几份文档里密集出现「篡改 / 绕过 / 穿透链 /
打穿 / fail-closed 反例」这类措辞（它们是**这类工作的正常术语**，但对内容分类器不友好）。
round-1 的 key 泄漏只是压垮它的最后一根稻草，不是唯一成因。

### round-2 的线索同样没浪费

stderr（337 KB）里保留了完整推理标题序列。我按其中每一条写探针实测：

| 线索（stderr 原文标题） | 实测结论 |
|---|---|
| `Investigating R7 blank bug` | ⚠️ **真缺陷，已修**（见下） |
| `Detecting orphan review event loss`、`Testing ledger validation with missing node_id`、`Identifying schema extension contract violation` | 分层成立：写点放行（不越权管别的节点），**校验器 5/5 全部拦下**（node_id 缺失/null/拼错、`schema_ext=review/2`、`reviews/1`）。已锁成门㊱② |
| `Investigating floating-point threshold rounding divergence`、`Comparing rounding consistency between validator and bridge` | 无误拒风险：0.00–1.00 的 **101 个两位小数值** JSON 往返后分档**无一改变**；边界 `gn=0.5` 的 `1.0+3.0*0.5` 恰为 `2.5`，走 `g < 2.5` 为 False ⇒ 稳定落 3。已锁成门㊱③ |
| `Identifying TOCTOU symlink vulnerability in CE_ROOT handling` | 守卫成立：symlink 指向别处时 `resolve()` 不等于约定路径 ⇒ 拒跑；且另有 marker 文件双重检查。已锁成门㊱④ |
| `Assessing datetime offset and separator compliance` | 无害：整秒门放行的 5 种宽松字面量（`Z`/`+00:00`/`-00:00`/小写 `t`/空格分隔）**全部归一到同一个 UTC 整秒瞬间**。已锁成门㉟⑥ |
| `Analyzing mastery loss in foreign pending replay` | 已声明边界（A2 重放只恢复 FSRS，mastery 无事件载荷可复放），见下方边界声明 6 |
| `Verifying trailing whitespace JSONL handling`、`Assessing event_version validation` | 已被现有门覆盖，实测无异常 |

#### R7-blank（round-2 找出的真缺陷，本卡已修）

截断的判据落错了位置：写的是「**文件**末尾有没有 LF」，而截断的定义是
「**最后一个非空行**有没有终止 LF」。反例：账本以 `坏行\n   ` 结尾（坏行后跟一个纯空白行、
文件不以 LF 收尾）时，旧判据说「无 LF ⇒ 截断，容忍」——可那个坏行后面明明还跟着东西，
它是**完整落盘之后损坏**的。实测 `rc=0`，写点照常追加并推进节点。

修法：`_last_idx` 定位最后一个非空行，`_ends_with_lf = _last_idx < len(_raw_lines) - 1`。
9 种行尾组合（真截断 / 带 LF / 带 CRLF / 末尾空白行两态 / 唯一行两态 / 尾随空格 / 前置空白行）
全部符合预期，锁成门㊱①，承重变异 M18。

### 我自己找到的 6 个覆盖缺口（门㉟）

等待 round-2 期间自查补的，都不是缺陷，是**已有门没覆盖到的面**：
删身份键（envelope 放行 + validator 拦，补强门㉕ 只测「篡改值」的分层声明）、
Unicode 归一化差异必须冲突（⚠️ 首版探针用汉字做 NFD 变异得出「放行」，那是**假阴性**——
汉字没有分解形式，变异根本没改字节；换 `café笔记` 重测即冲突）、
payload 键顺序不得误报冲突、attempt 复算成负值须 fail-closed、
同时刻两事件按行号稳定全序、整秒门宽松字面量语义等价。

### 已核查并澄清为「非缺陷」的面（逐条实测，附结论）

这些是两轮 stderr 线索 + 我自查列出的可疑点，**实测后确认不是缺陷**。列在这里是为了让
下一个人不用重跑一遍，也为了万一将来行为变了能对照：

| 面 | 实测结论 |
|---|---|
| 删掉一个 fsrs 身份键 | envelope 放行（两键排除出等价面 = 有意的分层），**校验器拦下**并明确报「必须为非空字符串」。分层成立 |
| 顶层多出未知键 | envelope 只比 5 个顶层键 ⇒ 写点放行，**校验器按「v1 冻结恰好 7 键」拦下**。分层成立 |
| `recorded_at` 变化 | 两侧都放行 —— 契约 §6.2:183 **显式排除**它（重试时自然变化，不构成事实差异）。设计如此 |
| payload 键顺序不同 | 不报冲突（canonical 用 `sort_keys`）。正确 |
| Unicode 归一化差异 | **报冲突**。⚠️ 首版探针用汉字做 NFD 变异得出「放行」，那是假阴性——汉字没有分解形式，变异根本没改字节；换 `café笔记` 重测即冲突 |
| 整秒门放行 `Z` / `+00:00` / `-00:00` / 小写 `t` / 空格分隔 | 5 种字面量**全部归一到同一个 UTC 整秒瞬间**，语义等价，放行无害 |
| `grade_norm` 浮点跨档 | 0.00–1.00 的 **101 个两位小数值** JSON 往返后分档**无一改变**；边界 `gn=0.5` 稳定落 3。不会误伤旧版合法行 |
| `node_id` 缺失/null/拼错、`schema_ext` 非法 | 写点放行（不越权管别的节点的行），**校验器 5/5 全部拦下**。分层成立 |
| 未标 `out_of_order` 的迟到事件（`review_time ≤ W`） | 不推进 current state —— 契约 §6.2 三态语义明写「无论已应用还是迟到乱序，对 current state 的动作完全相同」。正确 |
| `attempt_count` 复算成负值 | fail-closed（负数 ≠ durable 正整数 ⇒ 冲突）。方向安全 |
| 同节点两事件 `review_time` 完全相同 | 按行号稳定全序，两条都被重放。正确 |
| 同 `event_id` 两条不同内容 | 被**全文件唯一性检查**先拦（否则 A2 会双 apply）。正确 |
| `event_id` 为空串 | 结构性 `f1=False` ⇒ 重跑落到「FSRS 已应用但缺校准记录」的人工裁定分支，`rc=1` 零写。方向安全（空 `event_id` 属上游 bug） |
| R4 字节等价换 7 组参数 | 无 `last_examined` / 未来时间戳 / 损坏时间戳 / A3 只推 1 秒 / 走 `from_legacy` / `a,b` 为 0 的容错分支 / 带 callout —— **7/7 全部字节相同** |
| degraded 落账 → fsrs 恢复后重试 | 只补 FSRS、不二次吃 EMA，再重试一次完全幂等 |
| fixture 脚本被 symlink 劫持 | `resolve()` 不等于约定路径即拒跑，另有 marker 文件双重检查 |

### 本卡发现但**不在本卡范围**的移交事项

**校验器不强制迟到事件标 `out_of_order`**：契约 §6.2 说迟到/补录事件应「以原始 `review_time`
入账 + 标 `payload.out_of_order = true`」，但校验器当前对**未标**的迟到行放行（实测 `rc=0`）。
这是既存的契约-实现缺口，不是本卡引入。`validate_learning_events.py` 在本卡硬边界的禁改面上，
故**只登记不代改**。门㊱②c 用一条「当前放行」的断言锁住了这个事实——它某天变红就说明校验器
收紧了该面，届时应同步更新注释与本条移交记录。

### round-3（绑定 commit `cba60fc3`）：**拿到正文了，判「需整改」**

中性化措辞 + 收窄读取面（不让审查者读 UAT 与前身 round-3 报告，那两份术语最密集）之后，
round-3 产出 **17993 字节正文**，绑定的主程序 SHA-256 `41ef618b…` 与当时工作区一致。
结论：**需整改**，13 条规则里 7 条 FAIL，六格里 2 格 FAIL，共 **4 BLOCKER + 多条 HIGH**。

它找到的四条 BLOCKER，两条与我的内部审查**独立撞车**（互为交叉验证）：

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| ① | BLOCKER | **恢复与新写混在一次运行里**：A2 重放 foreign pending 只补 FSRS，那次评分的 mastery/校准无载荷可复放而**永久丢失**（实测：直接 A→B 得 `mastery=0.61`/校准 `[A,B]`，崩溃恢复后只剩 `0.57`/校准 `[B]`），`rc=0` 无信号 | **已改结构**：只要重放过非本次事件的行，就先把恢复结果**原子发布**下去，再以非零码退出要求重跑（正是 Step 4d 既有的续跑语义）。下一次运行 pending 已空，本次评分在干净基线上写入。mastery 丢失本身仍无解（durable payload 不带那部分载荷，属 §6.1 扩展，超本卡范围）——现在**如实打印告知**而不是静默 |
| ② | BLOCKER | **多 pending 守卫只覆盖 duplicate 排列**：预置 A/B 两条 pending 后写新 C，`rc=0`、重放两条、账本 `[1,2,3]`，而「连续两次发布前崩溃」在**单进程**下就能攒出这个状态（不必外部篡改） | 同 ①：两阶段发布后，第一阶段把两条都恢复并落盘，第二阶段才写 C。门㊳⑤ 锁住 |
| ③ | BLOCKER | **`attempt_count` 缺失/非法仍可消费**：删掉 `payload.attempt_count` 后 writer `rc=0`、validator 也 `rc=0`，账本 attempts=`[null,1]`——两次评分而笔记计数只有 1 | 加进适用集必填校验（≥1 的整数，拒 bool/字符串/0/负数）。门㊳③ |
| ④ | BLOCKER | **同秒未标行漏算**：E1@10:00 应用后 W=10:00，外部追加同节点 E2@10:00 未标 `out_of_order`，validator `rc=0`，再写 E3 时 E2 不进 pending ⇒ 永久漏算 | **未修，登记为裁决点**。根因在契约 §6.2「`≤W` 的歧义对 exactly-once 无影响」这句被同秒反例推翻——修它要改**契约本身**的三态语义，且窄化方案（对 `review_time == W` 且不在校准记录里的行 fail-closed）会误伤旧写序遗留行。见「待你裁决」⑧ |

HIGH 的处置：未知 `event_version` 不得按 v1 apply（门㊳①）、`effective_at` 与 `payload.review_time`
必须同一瞬间（门㊳②）、`payload` 非 object 须 clean fail-closed（门㊳④）、**缺少可用 `node_id`
必须 fail-closed**（schema §一「路由信封冻结」的读方义务明文要求，而我前一版的门㊱② 把这条违约
**锁成了正确行为**——已反转，见门㊱②）。

### 补跑的内部对抗审查（8 面并行 + 每条 3 票复现验证）

两轮正文缺失期间补跑的：8 个核查面各自在隔离 tmp 下用逐字提取的生产写点找反例，
每条发现再派 3 个独立怀疑者尝试证伪。119 个 agent、56 分钟。产出 37 条候选，
其中 **7 条实测复现为真缺陷并已修**（门㊲）：

| # | 级别 | 发现 | 修法 |
|---|---|---|---|
| B1 | BLOCKER | **R5 门被 `rating` 缺失整个绕过**：缺 rating 时 bridge 回落到推导，`grade_norm` 也缺时用默认 `0.0` ⇒ 一次可能是「答对」的评分被当成 `Rating.Again`（完全忘记）静默应用 | 适用行的评分事实必须**完整且可证**，rating/grade_norm 缺失或类型/范围非法一律 fail-closed |
| B2 | BLOCKER | **A2 重放不同步 `attempt_count`**，写点自己破坏了 ordinal 回推赖以成立的「每条适用行 = +1」不变量 ⇒ 崩溃恢复后合法历史重放被误报冲突 | 重放时把 attempt 推到 durable 值（它**有事件载荷**，与 mastery 不同）。顺带修好一个用户可见的错：崩溃恢复后「已考 N 次」旧实现会少算一次 |
| B3 | BLOCKER | **BOM 首行**让一条完整合法的事件行被当截断跳过；**整文件 decode** 让「腰斩多字节字符」这个最典型的崩溃产物反而无法自愈（切口落 ASCII 能自愈、落 CJK 中间就永久卡死） | 改按字节切行 + 逐行 decode（首行 `utf-8-sig`）。9 种行尾/编码组合全部符合预期 |
| C1 | HIGH | **挂载点与身份键错位的行被当复习应用**：`event_type=session_archived`、`concept_id` 指向别节点、`vault_id` 指向别 vault 的行都会照常重放并推进 FSRS（validator 事后判 FAIL，拦不回已推进的水位线） | 适用集校验三者对齐 |
| C2 | HIGH | **`event_id` 首尾空白 ⇒ 同一次评分双写双吃**（账本 2 行、mastery 双吃、attempt 多加一次），validator 看不出问题 | **拒绝**而不是静默 strip——strip 会把上游两个本来不同的 id 撞成一个 |
| C3 | MEDIUM | `attempt_count` 读取正则不容引号，而 Obsidian Properties 会写 `"3"` ⇒ 计数被重置为 1，还把一个**已被占用的序数**写进 append-only 账本 | 三处正则统一容引号 |
| C4 | MEDIUM | mastery 用**未舍入**的 `grade_norm`，而 durable 锁的是 `round(GN,2)` ⇒ 同一个 durable 事件在两次不同的未舍入输入下算出不同 mastery | 业务量恒取账本锁住的那个值 |

### ⛔ 作业事故：变异残留差点被提交（如实记，这是本卡最重要的教训）

我给变异脚本加的「变异窗口内文件被第三方改动就 `exit(3)` 别覆盖人家」防护，**方向是错的**：
它 exit 时**不还原**，于是 `if False:  # MUTANT` 这一行在 `SKILL.md` 里活了整整一轮。

- **所有门都照常通过**：26 个变异全 KILLED、265 个测试全绿、三个裁判全过——因为残留恰好落在一个
  `if False:` 分支里，它让 `concept_id` 校验静默失效，而当时还没有门覆盖那条；
- **抓住它的是 `grep MUTANT`**，不是任何一道门。MEMORY 里「commit 前必跑 diff 对账」这条今天兜住了；
- **旁证**：内部审查的两个 agent 在报告里主动写了「作业期间被审文件被并行进程改动，我改用
  `git show HEAD:` 的纯净版本重跑」——它们察觉到了，而我的脚本自检没有；
- **已修**：防护改为「先把第三方内容存证到 tmp，再**无条件**还原」。变异体绝不能留在生产文件里，
  第三方改动也不能无声蒸发。这条也进了 `g32b_mutation_gates.py` 的注释。

---

## 如实边界声明（本卡未证明什么）

1. **并发面仍不成立**（最重要，与前卡同）：本卡**没有实现任何锁**，G3-3 的 per-node sidecar 锁 / fencing epoch / per-vault 账本锁一项未做。单写者（同一 vault 内不并行跑任何两个 `quiz-answer`）是本卡正确性的前提。两个 writer 同时跑，本卡的所有 fail-closed 判据都可能在「读—算—写」的间隙被绕过。
2. **跨日 / 长期运行未证明**：所有反例都是单次进程内的确定性构造，没有跨日调度、没有真实 launchd 推送链路参与。
3. **live 部署未做**：worktree 的 skill/bridge **没有**复制到 live vault，本卡不改变你在 Obsidian 里的实际行为。
4. **耐久性只到调用序列**：`write→flush→fsync→replace` 的调用顺序被 spy 门锁住，但**不**证明真实断电后数据存活。
5. **R2 的作用域是本节点的适用集**：整秒/UTC 强制只施于「本节点 + `schema_ext=review/1` + 未标 `out_of_order`」的行——即参与 `W` 比较、决定 pending 与否的那一集合。别的节点的历史脏行不阻塞本节点评分（否则一条脏数据会锁死整个 vault）；标了 `out_of_order` 的行不参与 `W` 比较，故不校验。这是**有意的窄化**，不是漏网。
6. **A2 重放仍只恢复 FSRS**：mastery（衰减 Beta）与疑问 callout 没有事件载荷可复放。跨事件 pending（别的板的事件）恢复时其 mastery 副作用**永久丢失**，只有 FSRS 被补上——与前卡同，本卡未改变。
7. **`learning_event_log.py` 本卡未改**：R7 修的是 `quiz-answer` 读账本的判据。backend 通用 `append_event()` 的坏行处理是「warning + 跳过该行」（查重不把坏行算作命中），它不做「截断容忍」声明，故不在 R7 射程内。如实登记，不代改（卡文限定只允许尾行/查重最小修正）。
8. **N5 的窄化如实记**：多个 pending 并存时本卡选择 fail-closed 而非硬算。代价是——如果账本真被外部写成那样，你必须人工修账本才能继续评分。收益是：不在一个「attempt 序数无法从账本边界证明」的基线上继续写。
9. **三轮审查里只有第三轮拿到正文，而它判「需整改」**：round-3 报的 4 BLOCKER 我修了 3 条、登记 1 条为裁决点，但**这些修复本身没有再经过独立审查**（卡文上限 3 轮已用尽）。内部对抗审查（8 面 + 3 票验证）可以部分替代，但它和我共享同一个模型，不是真正的独立第三方。**这是本卡最大的证据缺口**。前两轮的正文缺失情况见上「Codex 审查处置」。
9b. **旧表述（保留以便对照）**：两轮审查的正文都缺失：见上「Codex 审查处置」。N1-N5 与 R7-blank 都是**我按 stderr 推理标题线索自测**出来的，不是独立审查者给出的完整结论。**独立审查这一环到目前为止仍是空的**——线索来自独立审查者不假，但「哪些成立、哪些不成立、有没有漏的」全是自评。这是本卡最大的证据缺口。
10. **门集不等于穷尽**：变异 10/10 只证明**这 10 个已知缺陷形态**会被指定门抓住，不证明没有第 11 类。三轮审查的历史（每轮修复都会长出新分支）说明这个方向上的清零在对抗范式下不可达。
11. **未自动解锁下游**：本卡未改写 G3-7、G8-4 的总账依赖。
12. **Obsidian 插件是既存第二写路径**：`frontend/obsidian-plugin/src/main.ts` 的 node_derived 直写不在本卡写点门 grep 范围，本卡未动它，沿用前卡登记。

---

## 待你裁决

| # | 事项 | 默认（本卡已按默认实现） | 备选 |
|---|---|---|---|
| ① | 畸形 durable 事件（小数秒 / 非 UTC / 未知额外键 / rating 不自洽 / 带 LF 坏行） | **零写退出 + 报错**，等你人工修账本 | 自动隔离该行继续跑（会在无法证明的基线上叠加，契约禁止） |
| ② | 单写者前提 | **保留**（G3-3 前无锁，同一 vault 内不得并行跑两个 `quiz-answer`） | 现在就实现锁（= 提前做 G3-3，超出本卡范围） |
| ③ | 两个 fsrs 身份键的完整性归属 | **由 schema/validator 明确归属**（排除出 envelope 等价面，完整性交 golden manifest 绑定门）——已回写 §6.2 | 纳入 envelope 等价面（一次合法的库升级会让所有历史事件重放变冲突） |
| ④ | 是否部署到 live | **不部署**（手册 §四.1 第 2 条） | 你确认后另开部署动作 |
| ⑤ | R2 的作用域窄化（边界声明 5） | **只施于本节点适用集** | 全账本所有 `review/1` 行（一条别节点的脏行会锁死整个 vault 的评分） |
| ⑥ | 标了 `out_of_order` 但时刻晚于 W 的行（N1） | **写点侧 fail-closed 拒写**，等你人工裁定那行是补录还是真后继 | 照搬 proof 侧的「报违规但仍计入适用集」（会多应用一次 FSRS） |
| ⑦ | 三轮审查用尽，round-3 判「需整改」 | **不合并**（手册 §四.2：B/H 未清零不进合并队列）。修复已做但未经第 4 轮独立审查 | ① 破例合并；② 另开一张卡专收 round-3 残留 + 跑新一轮审查 |
| ⑧ | 同秒未标 `out_of_order` 的行被漏算（round-3 BLOCKER①，**未修**） | **登记不修**：根因是契约 §6.2「`≤W` 的歧义对 exactly-once 无影响」这句被同秒反例推翻，修它要动三态语义本身；窄化方案会误伤旧写序遗留行 | ① 改契约：同节点未标行按物理行序强制业务时刻严格递增，重复/回退即 fail-closed；② 维持现状并接受该漏算面 |
| ⑨ | 存在 foreign pending 时改为「恢复先落定 + 要求重跑」 | **已改**（round-3 BLOCKER①②的修法）：多一次重跑，换来恢复结果独立持久化、新事件在干净基线上写入 | 维持旧的「一次运行内既恢复又追加」（会静默丢被恢复事件的 mastery/校准，且多 pending 时 attempt 不可证） |

---

## 证据位置

| 内容 | 路径 |
|---|---|
| 卡文（只读） | `…/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第九批-goals/W7.md`（SHA256 `5accbca8…3eb287f8`） |
| 前卡 UAT / round-3 | `_bmad-output/验收单/UAT-CARD-G3-2-复习事件账本write-ahead-2026-09-01.md`、`_bmad-output/审查/codex-review-CARD-G3-2-round3.md` |
| 生产改动 | `canvas-vault/.claude/skills/quiz-answer/SKILL.md`、`canvas-vault/.claude/scripts/fsrs_bridge.py` |
| 契约回写 | `docs/learning-events-schema-v1.md` §6.2（A4.5 duplicate 门 / A4.5 短写段 / A5） |
| 行为门 | `backend/tests/regression/test_g3_2_review_ledger.py` 门㉖-㊳（㉖-㉜=R1-R7，㉝=六格状态机，㉞=N1-N5，㉟=自查覆盖缺口，㊱=round-2 线索复核，㊲=内部对抗审查 7 条，㊳=round-3 的 BLOCKER/HIGH） |
| 反例复现脚本 | `backend/scripts/g32b_r1r7_counterexamples.py` |
| fixture 生成脚本 | `backend/scripts/g32b_build_fixture.py`（`--check` 复算 sha） |
| 变异脚本 | `backend/scripts/g32b_mutation_gates.py`（17 个变异，串行 + 逐字节还原） |
| round-1 审查 | `_bmad-output/审查/codex-review-CARD-G3-2b.md`（**0 字节**，已入库作为「正文缺失」本身的证据） |
| round-3 审查 | `_bmad-output/审查/codex-review-CARD-G3-2b-round3.md`（**17993 字节，唯一拿到正文的一轮**，判「需整改」）+ `.stderr` sha256 `1e093c12c70d0ee011c929e51c97cb8d4ca3245d21b989268809663daabfbb7e`（820 KB，同样不入库） |
| round-3 提示词 | `_bmad-output/审查/prompts/codex-prompt-CARD-G3-2b-round3.md`（中性化措辞 + 收窄读取面） |
| 内部对抗审查 | 8 核查面 × 3 票复现验证，119 agent / 56 分钟；产出 37 条候选，7 条实测复现为真缺陷（门㊲） |
| round-2 审查 | `_bmad-output/审查/codex-review-CARD-G3-2b-round2.md`（**0 字节**）+ `.stderr`（337 KB，**同样不入库**：虽无配置值泄漏，但与 round-1 同类处理），sha256 `22d386315a9f7685bf6a3809acdf09897693f23ef5f9f2ec4bb45b11941e6df1` |
| round-1 stderr | `_bmad-output/审查/codex-review-CARD-G3-2b.stderr`，sha256 `c223e825fdfc1ce823d614fb648c1fd5e83a8032e0aea0050a5fa9c8603df1da`（226 KB）——**故意不入库**：文件里含 `.env` 某配置值的截断前缀（正是它触发了内容过滤器），凭据片段不进版本库。保留在工作区 untracked，与前卡三个 stderr 同处理 |
| round-2 提示词 | `_bmad-output/审查/prompts/codex-prompt-CARD-G3-2b-round2.md`（已写明用 `INTERNAL_API_KEY` 占位值跑 pytest，规避 round-1 的拦截成因） |
| 审查提示词 | `_bmad-output/审查/prompts/codex-prompt-CARD-G3-2b.md` |
| fixture sha256 | `learning_events.jsonl` `8838ce3a5859213d68bc0ac0fa06dd2536d940aac81ac75b46503291df0872c7`；`.canvas-config.yaml` `6444cad8deb0cd6c0224076f375176a57635056cd7188085ace169ee07f02ddd` |
| 开工登记的 3 个 untracked stderr | `codex-review-CARD-G3-2-round{1,2,3}.stderr` = `8e5820dc…`、`e2f09b74…`、`c6a770f2…`（前卡 CARD-G3-2 产物，本卡未删未改） |
