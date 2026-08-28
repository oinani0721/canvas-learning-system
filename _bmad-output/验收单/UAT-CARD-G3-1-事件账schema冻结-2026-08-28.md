# 验收单 · CARD-G3-1 D0 修订落文档 + 事件账 schema 冻结

> **批次**: BATCH-2026-08-28-第五批 · 车道 S3 第一卡
> **分支**: `card/s3-events`（不 push，等你验收）
> **日期**: 2026-08-28
> **一句话**: 你的复习系统现在有了一份"宪法"——白纸黑字写死：**笔记 frontmatter 是唯一的
> 复习状态真相**，`learning_events.jsonl` 事件账只负责"记录发生过什么"（审计/防重/可重放）。
> 这张卡**零代码改动**——既有账本实现（已在生产跑了一个月、22 条真实事件）原样不动，
> 只是把它的现实升格为冻结契约 + 配了一把可以随时检查账本健康的尺子。

---

## 一、你能看到什么（用户体验）

这张卡是"防暗坑"基础设施卡，没有界面变化。你可以做的两个 30 秒检查：

1. **打开 `docs/learning-events-schema-v1.md`**——你会看到账本每个字段的白纸黑字契约、
   9 类事件各自由谁在哪一行写入（8 个写点逐个 file:line）、以及"以后想加复习字段该怎么加"的规则。
2. **亲手跑一次账本体检**（可选）：
   ```bash
   cd /Users/Heishing/Desktop/canvas/canvas-learning-system
   .claude/worktrees/card-s3-events/backend/.venv/bin/python \
     .claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py \
     canvas-vault/learning_events.jsonl
   ```
   预期看到 `RESULT: PASS — schema v1 合规`——你现网的 22 条学习事件全部健康。

## 二、技术判据（Claude 已代跑）

| 裁判 | 结果 |
|---|---|
| 契约测试 `backend/tests/regression/test_learning_events_schema_contract.py` | **25 passed + 1 skipped**（本文件单跑口径；skip = 仓内 vault 根无账本的 worktree 环境，主仓自动生效。另有既有 `test_learning_event_log.py` 6 passed 零改动） |
| **真实 producer 执行**（Codex 一轮 HIGH 整改） | vault 三 skill 写点的 python 代码**从 SKILL.md 逐字提取执行**（ai-linked-doc 单行模板 / start-exam-board PYEOF 块 / quiz-answer 评分链账本段；仅路径常量重定向 tmp fixture），产物过校验器 + 幂等重放断言；backend 侧按 5 调用点实参形状经真实 `append_event` 写入后全过 |
| 既有账本回归 `test_learning_event_log.py` | 6 passed（零改动） |
| 校验脚本 vs 三 fixture | 合法 → exit 0 / 缺字段 → exit 1（点名 `effective_at`）/ 重复 event_id → exit 1（点名首见行号）（存证 `审查/g3-1-evidence/g3-1-fixture-validation.txt`） |
| 校验脚本 vs **现网账本**（22 行） | **exit 0**，且 sha256 运行前后一致（只读证明；存证 `审查/g3-1-evidence/g3-1-live-ledger-validation.txt`） |
| 现网写点 0 误报 | 按 8 个写点 1:1 建模的 `real_shapes.jsonl`（含 Z 后缀时间戳/紧凑分隔符/中文 event_id）全过 |
| 边界判定 | 截断行如实报 FAIL / 未知顶层字段拒绝 / naive 时间戳拒绝 / **NaN·Infinity 非标准常量拒绝（RFC 8259 严格）** / **行内重复键拒绝（json.loads 静默取后者的歧义面）** / 未知 event_version 走 WARN 前向兼容通道不误杀 |
| 漂移锁 | EVENT_VERSION=1、9 类白名单、7 键形状、校验器复制份 == 真相源，四路契约测试锁死 |
| 铁律遵守 | `learning_event_log.py` **零改动**；git diff 只含新增文件 + CLAUDE.md/architecture.md 引用行 + CURRENT_TASK；未新建任何第二套账本 |
| ruff | All checks passed |

## 三、写点普查结论（逐点核对现行号，2026-08-28）

**backend 5 调用点**（卡档案写 4，实查 5——errors.py 有两个，已在 schema 文档 §五如实勘误）：
`tips.py:565`（callout_ingested）/ `memory.py:815`（session_archived）/ `errors.py:198`（candidate_accepted）/
`errors.py:259`（candidate_disputed）/ `conversation_distiller.py:445`（candidate_created）

**vault 3 skill 静态写点**：`quiz-answer`（answer_scored/abandoned）/ `start-exam-board`（exam_created）/
`ai-linked-doc`（node_derived）

**同名陷阱排除**：`record_learning_event()`（Neo4j/Graphiti 管道）与本账本无关，全仓无第三套直写（grep 核验）。

## 四、交付物清单

| 文件 | 说明 |
|---|---|
| `docs/fsrs-truth-source-d0-revision.md` | D0/D2-A 正式修订（frontmatter=current state；事件账=审计/幂等/重放；禁第二套；现存偏离登记表→G3-2/3/5/7/8 交接） |
| `docs/learning-events-schema-v1.md` | EVENT_VERSION=1 逐字段冻结契约 + 9 类事件契约 + 写点普查 + 复习域扩展规则（G3-2 预备）+ 白名单对账评审记录 |
| `backend/scripts/validate_learning_events.py` | stdlib 确定性校验器（exit 0/1/2；可独立对任意 vault 账本跑） |
| `backend/tests/fixtures/learning_events/*.jsonl` | 合法/缺字段/重复/真实形状 四 fixture |
| `backend/tests/regression/test_learning_events_schema_contract.py` | 契约测试（漂移即红） |
| CLAUDE.md / docs/architecture.md | 各 +1 处引用（判据要求"被 CLAUDE.md/架构文档引用"） |

## 五、Codex 审查处置（一轮 → 整改全落地）

一轮存档 `_bmad-output/审查/codex-review-CARD-G3-1-2026-08-28.md`（裁定"需整改"：1 BLOCKER + 6 HIGH + 4 MEDIUM/LOW）。逐条处置：

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| e-1 | **BLOCKER** | §六只定写序无恢复语义：崩溃后无法区分"事件已应用/仅落账"，跳过漏推进、重放可能二次推进 | **已修**：§6.2 冻结 applied-watermark 状态机（`frontmatter.last_review` 为水位线，`review_time` 比较机械判定 applied/pending；覆盖三种崩溃窗口；并列 review_time 归 G3-3 CAS 禁止） |
| a-1 | HIGH | `append_event` False 折叠 duplicate/IO 两义；tips.py:572-578 把 IO 失败误报 duplicate 并中止管道，"不阻断主链"在该写点不成立 | **已修（文档）**：§二失败语义如实登记折叠语义 + 消费者偏离；§6.2 冻结"G3-2 禁依赖折叠布尔、先显式查重再追加"；生产修复移交（§九） |
| a-2 | HIGH | tips 入口接受 naive `added_at` 可产 naive `effective_at` | **已登记 §九**（producer 潜在缺陷，现网未命中；校验器会抓；修复属生产路径，移交 G3-7/micro-patch） |
| b-1 | HIGH | 未知 event_version 行 WARN+FAIL 双发，前向兼容失实 | **已修（代码）**：前向兼容分流——未知 int 版本只 WARN、完全跳过 v1 形状校验；新形状 v2 行测试锚定 exit 0 |
| b-2 | HIGH | NaN 非标准常量静默 PASS | **已修（代码）**：严格 JSON（`parse_constant` 拒 NaN/Infinity；`object_pairs_hook` 拒重复键——连带修掉 MEDIUM 重复 member） |
| c-1 | HIGH | "8 写点 1:1"仅手工 fixture，未执行真实 producer | **已修（测试）**：新增 4 条真实 producer 测试（SKILL.md 逐字提取执行 ×3 + append_event 按 5 调用点实参 ×1） |
| c-2 | HIGH | 测试计数 19 归给单一新文件，口径失真 | **已修**：本单与 CURRENT_TASK 改为"25 passed + 1 skipped（单文件）+ 既有 6 passed" |
| d-1 | HIGH | G3-1/G3-4 混在同一工作树无独立 commit，diff 无法单卡切出 | **已修（流程）**：两卡**分开 commit**（G3-1 文件清单先行独立提交，G3-4 后续独立提交） |
| e-2 | HIGH | 截断尾行无 LF 时后续 append 粘连坏行 | **已修（契约）**：§二"截断自愈"冻结 G3-2 追加前 LF 守卫 |
| e-3 | HIGH | 扩展键无机械标记、`rating: true` 可过、降级无诚实 hash 口径 | **已修（代码+契约）**：§6.1 冻结 `schema_ext: "review/1"` 机械标记；校验器强制扩展键类型（bool 伪装/越界/缺键全抓，测试锚定）；降级哨兵 `degraded:<原因>` 口径冻结 |
| b-3 | MEDIUM | 非法 UTF-8 炸 traceback；`Q` 分隔符可过 | **已修（代码）**：逐行二进制读+独立解码（坏行=违规不中断）；分隔符显式限 T/t/空格（§三受理语法成文） |
| d-2 | MEDIUM | 存证未绑定 HEAD/文件 SHA/python 版本/完整命令 | **已修**：两份证据重新生成，含 git HEAD、validator/测试/fixture sha256、python 版本、完整命令 |
| e-4 | MEDIUM | fsrs hash 与 G3-4 同源但无显式依赖声明 | **已修（文档）**：§6.1 显式绑定 G3-4 manifest 的 `library_version`/`params_hash`（同分支交付，依赖闭合） |
| a-3 | LOW | "紧凑分隔符"归因失实；D0 引用的 v2 总账不在本 HEAD | **已修（文档）**：§二措辞改为"风格不冻结、现网两种并存"；D0 头注显式注明 v2 总账所在 worktree |

整改后复跑：契约测试 25+1 全绿、现网账本 exit 0（SHA-bound 存证）、ruff 全过。

### 二轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round2-2026-08-28.md`，G3-1 残留 1 BLOCKER + 2 HIGH + 1 MEDIUM）

| # | 级别 | 二轮发现 | 处置 |
|---|---|---|---|
| e-1 | **BLOCKER** | 水位线只覆盖"恢复先于新写"的简单三窗，**交错窗口漏事件**：FM=t0，E1@t1 落账后崩溃，恢复前 E2@t2 从旧状态推进到 t2，E1 随后因 `t1 ≤ W` 被误判已应用 → E1 对 current state 的贡献永久丢失 | **已修（契约）**：§6.2 重写为三条硬约束 **A1 write-ahead + A2 恢复先于新写 + A3 严格递增**。A2 使任意时刻至多一条事件 pending，交错窗口在构造上不可能出现（反例逐字写入文档作为"为什么必要"） |
| e-1 | **BLOCKER 附项** | 契约字段名 `frontmatter.last_review` 与真实键 `fsrs_last_review` 不符；新卡无该键；`≤ ⇔ 已应用` 不能区分"已应用"与"迟到乱序"；秒级时间戳可自然等时，而 G3-3 卡面未定义等时拒绝 | **已修（契约）**：字段名按 `fsrs_bridge.py:44-46` FIELD_ORDER 真相源改为 **`fsrs_last_review`**（秒级、缺键 ⇒ `W = -∞`）；新增**三态语义**论证——`≤ W` 的事件无论已应用还是迟到乱序，对 current state 的动作**完全相同**，歧义对 exactly-once 无影响，乱序标注改由**事件到达序**判定（G3-3 地盘）；A3 等时消解 + **显式移交条款**要求 G3-3 补等时拒绝/复合排序 |
| b-2 | **HIGH** | `decoded.strip()` 剥除 RFC 8259 禁止的控制字符（U+001C 等），敌对行伪装成合法 JSON 后 exit 0 | **已修（代码）**：改 `rstrip("\r\n")` 只剥行尾；U+001C 包裹行现判 FAIL（对抗复验留档） |
| e-3 | **HIGH** | review/1 扩展只查基础类型，不查 `concept_id==node_id`、`review_time==effective_at`、version/hash 形状、degraded 成对与非空原因；`DEGRADED_PREFIX` 定义后未使用 | **已修（代码）**：跨字段绑定全部机械校验（含 hash 须 64 位小写 hex、version 须数字点版、degraded 两键必须成对且原因非空），综合坏例现报 4 项违规 |
| b-3 | MEDIUM | 时间词法仍收 week-date / 省略分钟 / `+00` / 逗号小数 / offset 秒；5000 位整数触发未捕获 ValueError | **已修（代码）**：§三受理语法改为**白名单正则**先判词法再验语义；超限 ValueError 单行判违规不炸整体 |
| d-2 | MEDIUM | 存证 HEAD 仍写预提交 `37387a…`；fixture 存证缺完整命令 | **已修**：两份存证按 round-3 重生成，HEAD 写实际 commit、每 fixture 附完整命令 |
| c-1 | — | "4 条真实 producer"中第四条只走共享 `append_event` + 手写实参，未经五个 backend callsite，标题略宽 | **已如实收窄**：本单 §二该行已写明"backend 侧按 5 调用点实参形状经真实 `append_event`"，不宣称走 endpoint |
| a-1/a-2 | — | tips 两偏离 owner 不够确定（G3-7 卡面不含 tips） | **已收紧**：schema §九移交栏改为"**独立 micro-patch**（G3-7 卡面不含 tips）" |

三轮复核状态：本轮整改后契约测试 **29 passed + 1 skipped**（本文件）、现网账本 exit 0、round-2 全部点名反例对抗复验翻红（`审查/g3-1-evidence/g3-round2-counterexamples.txt`）。

## 六、移交登记

1. `learning_event_log.py:11/:73` docstring "8 类"实为 9 类——注释滞后，本卡边界禁改该文件，**移交 G3-2 顺手修**（一行注释，零行为变化）。
2. 复习域 payload 扩展键（rating/review_time/fsrs_library_version/fsrs_params_hash/vault_id/concept_id）的实际写入 = **G3-2 范围**，本卡只冻结规则。
3. 跨进程写锁缺失（当前仅 backend 进程内 threading.Lock）已在 schema 文档 §二如实登记，归 **G3-3**。
