# 验收单 · CARD-G3-1 D0 修订落文档 + 事件账 schema 冻结

> **批次**: BATCH-2026-08-28-第五批 · 车道 S3 第一卡
> **分支**: `card/s3-events`（不 push，等你验收）
> **日期**: 2026-08-28
> **一句话**: 你的复习系统现在有了一份"宪法"——白纸黑字写死：**笔记 frontmatter 是唯一的
> 复习状态真相**，`learning_events.jsonl` 事件账只负责"记录发生过什么"（审计/防重/可重放）。
> 这张卡**零生产代码改动**（新增的是一个独立校验器脚本与测试，不动任何既有生产路径）——既有账本实现（已在生产跑了一个月、当前 23 条真实事件）原样不动，
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
   预期看到 `RESULT: PASS — schema v1 合规`——你现网的学习事件全部健康。

## 二、技术判据（Claude 已代跑）

| 裁判 | 结果 |
|---|---|
| 契约测试 `backend/tests/regression/test_learning_events_schema_contract.py` | **166 passed + 1 skipped**（本文件单跑口径，十九轮整改后；skip = 仓内 vault 根无账本的 worktree 环境，主仓自动生效。与 golden 门 + 既有账本测试合跑 = **191 passed + 1 skipped**） |
| **真实 producer 执行**（Codex 一轮 HIGH 整改） | vault 三 skill 写点的 python 代码**从 SKILL.md 逐字提取执行**（ai-linked-doc 单行模板 / start-exam-board PYEOF 块 / quiz-answer 评分链账本段；仅路径常量重定向 tmp fixture），产物过校验器 + 幂等重放断言；backend 侧按 5 调用点实参形状经真实 `append_event` 写入后全过 |
| 既有账本回归 `test_learning_event_log.py` | 6 passed（零改动） |
| 校验脚本 vs 三 fixture | 合法 → exit 0 / 缺字段 → exit 1（点名 `effective_at`）/ 重复 event_id → exit 1（点名首见行号）（存证 `审查/g3-1-evidence/g3-1-fixture-validation.txt`） |
| 校验脚本 vs **现网账本**（当前 23 行，用户仍在产生新事件） | **exit 0** 零 WARN 零 FAIL，且 sha256 运行前后一致（只读证明；存证按每轮整改重生成，含 HEAD/validator SHA/完整命令） |
| 现网写点 0 误报 | 按 8 个写点 1:1 建模的 `real_shapes.jsonl`（含 Z 后缀时间戳/紧凑分隔符/中文 event_id）全过 |
| 边界判定 | 截断行如实报 FAIL / 未知顶层字段拒绝 / naive 时间戳拒绝 / **NaN·Infinity 非标准常量拒绝（RFC 8259 严格）** / **行内重复键拒绝（json.loads 静默取后者的歧义面）** / 未知 event_version 走 WARN 前向兼容通道不误杀 |
| 漂移锁 | EVENT_VERSION=1、9 类白名单、7 键形状、校验器复制份 == 真相源（四路契约测试）+ **`rating_from_grade` 与 `fsrs_bridge` 逐档等价**（千点网格 + 三档分界两侧）+ **W 与 review_time 的瞬间等价关系**（bridge `_iso` 写出格式改变即红）+ **vault_id 对真实生产入口 `Settings.vault_id` 的「绝不错绑」性质**（PyYAML 解析 + backend `sanitize_vault_id` 本体；25 形态含 r5~r11 各轮点名反例，逐例断言「要么等值、要么不绑定」，**错绑即红**） |
| 铁律遵守 | `learning_event_log.py` **零改动**；git diff 只含新增文件 + CLAUDE.md/architecture.md 引用行 + CURRENT_TASK；未新建任何第二套账本 |
| ruff | 本卡交付文件 All checks passed（`backend/scripts/` + 契约测试；**范围声明**：仓库其余既有告警不在本卡范围） |
| 依赖口径（r10/r11 修正） | **账本校验主体 stdlib-only**；**vault_id 绑定层**需 PyYAML + 可 import 的 backend `app.config`（必须与生产 `Settings.vault_id` 逐环节同源），不可达时降级为不绑定 + WARN。schema §八、validator docstring、本单三处口径已统一 |

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
| `backend/scripts/validate_learning_events.py` | 确定性校验器（exit 0/1/2）。**账本校验主体 stdlib-only**，可独立对任意 vault 的 jsonl 跑；**vault_id 绑定层**需 PyYAML + 可 import 的 backend `app.config`（须与生产 `Settings.vault_id` 逐环节同源），不可达或配置解析异常时降级为不绑定 + WARN，主体不受影响 |
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

### 三轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round3-2026-08-28.md`，G3-1 残留 1 复合 BLOCKER + 1 HIGH + 3 MEDIUM）

| # | 级别 | 三轮发现 | 处置 |
|---|---|---|---|
| 1a | **BLOCKER（新）** | **小数秒二次推进**：校验器允许 `10:00:00.500000Z`，而 bridge 把 `fsrs_last_review` 写成整秒 → 同一事件恒满足 `> W`，实测重放后 Learning→Review、due 从 10:10 跳到 +2d | **已修（契约+代码）**：§6.2 新增 **A5 整秒精度**硬约束；校验器对 `review/1` 行机械强制整秒（反例现报 FAIL） |
| 1b | **BLOCKER** | **并发下 A2 可被绕过**：两进程可同时看到 `pending=[]` 并各自从同一旧状态计算；契约未要求锁覆盖完整临界区，"构造上不可能"措辞过强 | **已修（契约）**：§6.2 新增 **A4 临界区**——"读 W→扫 pending→重放→durable append→apply→原子发布"整段须在 per-node 互斥内；六字段与 W 须同一次原子替换（`os.replace`）；A2 措辞收窄为"单写者下"；**移交 G3-3 补三项**（per-node 锁/CAS、等时拒绝、CAS 冲突后全事件重折叠） |
| 1c | **BLOCKER（新）** | **残缺卡**（有 `fsrs_due`/`fsrs_state` 但缺 `fsrs_last_review`）被当 `W=-∞`，会在已推进的旧状态上重放全账 | **已修（契约）**：§6.2 水位线三态——真新卡（无任何 `fsrs_*`）=`-∞`；正常卡=该值；**残缺卡 = fail-closed**（禁止自动重放，报 degraded 待修复） |
| 1d | **BLOCKER** | **三态不自洽**：pending 定义未排除 `out_of_order`；A3"新事件 > W"与"迟到旧事件原时刻入账"冲突；乱序判据 schema（账本最大时间）与 G3-3 卡面（已应用最新事件）两口径 | **已修（契约）**：pending 定义显式排除 `out_of_order` 行；乱序判据**统一采用 G3-3 卡面口径**（`review_time ≤ W`）；新增**账本补录通道**——迟到事件以原时刻入账 + 标 `out_of_order`、不进 pending、不推进 current state，与 A3（只约束在线评分）无冲突 |
| 2 | HIGH | review/1 语义绑定仍不全：`vault_id` 不符 / `rating=4+grade_norm=0` / 弃答 `rating=4` / `schema_ext="review/01"` 降级 / 挂 `session_archived` / 假版本+全零 hash / `grade_norm` 缺失越界，**均 exit 0** | **已修（代码+契约）**：挂载点限 `answer_scored`/`answer_abandoned`；marker 值非法或带扩展键无 marker 均判违规（封堵降级）；`grade_norm` 必填 ∈[0,1]；`rating` 与 `grade_norm` 按 `rating_from_grade` 口径自洽、弃答恒为 1；**库指纹与 G3-4 golden manifest 真值相等**（manifest 不可达 → 形状校验 + WARN）。七条反例现全部 FAIL |
| 3 | MEDIUM | offset 分钟 `\d{2}` 收了 `+00:60`/`+00:99` | **已修**：正则改 `[0-5]\d`（合法 `+08:45`/`-03:30` 仍过） |
| 4 | MEDIUM | 深层嵌套（~50 万层）触发未捕获 `RecursionError`，stdout 空并中断后续行 | **已修**：捕获 `RecursionError`，单行判违规不中断 |
| 5 | MEDIUM | `Z` 与 `+00:00` 同一瞬间因原字符串不等被拒 | **已修**：跨字段时刻改按**绝对瞬间**比较（混写变体测试锚定 exit 0） |
| — | MEDIUM | 存证 SHA 过期（记 `13c03c7…`，实际 validator 已变） | **已修**：round-4 存证重生成，SHA 与当前 bytes 一致 |
| — | MEDIUM | 本单同时写 `25+1` 与 `29+1`；"零代码改动"与新增 validator/test 矛盾 | **已修**：全单计数统一为 **35 passed + 1 skipped**（本轮实测）；"零代码改动"改为"**零生产代码改动**（新增独立校验器与测试，不动任何既有生产路径）" |

三轮整改后复跑：契约测试 35 passed + 1 skipped、现网账本 exit 0（SHA-bound）、round-2/round-3 全部点名反例对抗复验翻红。

### 四轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round4-2026-08-28.md`，G3-1 残留 1 BLOCKER + 4 HIGH + 2 MEDIUM）

| # | 级别 | 四轮发现 | 处置 |
|---|---|---|---|
| 一b | **BLOCKER** | **并发协议未闭合**："锁/CAS"不能当等价互斥——两写者可在同秒都 durable append，胜者发布 `W=t1` 后败者事件因 `review_time == W` **永久不进 pending**；A3 的"等时改 W+1s"与移交的"等时拒绝"自相矛盾；CAS 冲突后的"全事件重折叠"无冻结基线、应用游标与掉电耐久语义 | **已修（契约）**：§6.2 A4 重写为**并发正确性最小充分集四条**——**A4.1 真互斥**（per-node 排他锁，持有期覆盖到发布之后；明确乐观 CAS 不满足并写入该反例）、**A4.2 应用游标与折叠基线**（基线恒为当前 frontmatter current state，游标 = 锁内读到的 W，全量折叠须与增量重放等价）、**A4.3 账本耐久先于发布**（write+flush+fsync 后再 apply）、**A4.4 原子发布**（六字段与 W 同一次 `os.replace`；半态被三态判别识别为残缺卡 fail-closed）。A3 **等时唯一口径统一为"推进 W+1s"**，"等时拒绝"作废（拒绝会丢真实评分）；移交 G3-3 三项同步改写 |
| 一a | HIGH#1 | 端到端时间口径未冻结：bridge 把 naive 当 UTC 并截微秒；校验器允许省略秒与任意 offset；`18:00+08:00` 与 `10:00Z` 同瞬间但字符串比较会误判 pending | **已修（契约+代码+测试）**：§6.2 新增**比较语义条款**——W 与 review_time 的所有比较**必须按绝对瞬间**（写入实测反例：两者是同一瞬间的不同字符串）；整秒性按 UTC 归一化后计；校验器对 `review/1` 强制**完整整秒形态**（省略秒段判违规）；新增测试钉死 bridge `_iso` 写出格式与瞬间等价关系 |
| 一c | HIGH#2 | 三态按字段存在性判别有灰区：只有 `fsrs_last_review` 会被判"正常卡"，bridge 却因无 `fsrs_due` 当 New 卡处理 | **已修（契约）**：正常卡定义收紧为**完整可解析 FSRS tuple**（`fsrs_last_review` + `fsrs_due` 可解析 + `fsrs_state ∈ {1,2,3}`）；其余组合（含"只有 last_review"、缺 state、空串/不可解析/越界）**一律 fail-closed**，四类灰区逐条列举 |
| 一d | HIGH#3 | `out_of_order` 的位置/类型/真假语义未冻结（字符串或对象值均零违规）；degraded pending 的阻塞/恢复未定义 | **已修（契约+代码+测试）**：冻结 `payload.out_of_order` **唯一合法值为布尔 `true`**，未标则不写该键（`false`/字符串/对象/数字/null 全判违规，测试锚定）；degraded pending 处置成文——残缺卡节点 pending **整体冻结**（不重放不追加，新评分如实报错），修复后正常重放且事件不失效 |
| 二 | HIGH#4 | `vault_id` 只查非空，账本路径/vault 身份从未送入规则（`vault_id="evil-other-vault"` 等价 exit 0） | **已修（代码+测试）**：校验器从账本**同目录 `.canvas-config.yaml`** 解析声明 `vault_id`（stdlib 最小行解析，不引 PyYAML）并强制相等；配置不可达时降级 WARN 保持独立可跑。反例现 FAIL（R4-1） |
| 二 | MEDIUM | manifest 缺失/损坏/空对象仍 WARN+exit 0；非空 list/scalar 可 traceback | **已修（代码+测试）**：`_golden_manifest` 只接受**含两个真值键的 dict**，其余（空对象/list/标量/坏 JSON）一律 None + 形状降级 WARN；`_validate_review_ext` 再加一层 `isinstance` 防御。四种损坏形态实测零 traceback（R4-7） |
| 五 | MEDIUM | UAT 计数与宣称不实：`36+1` 不能复现（HEAD 为 35+1）、"vault_id 不符已全部 FAIL"错误、22 行已非当前 live、ruff 未注明范围 | **已修**：本单计数改为**实测 41 passed + 1 skipped**（本轮）、账本行数改为**当前 23 行且声明用户仍在产生新事件**、ruff 加范围声明；vault_id 绑定改为**本轮真实实现后**再宣称（不再是空头声明） |
| 二 | — | rating 与 bridge **逐档等价**（百万点网格 0 mismatch），但 HEAD 无交叉锁 | **已补测试**：`test_rating_from_grade_parity_with_bridge` 千点网格 + 三档分界两侧 + 弃答前提，直接对 `fsrs_bridge.rating_from_grade` 交叉断言 |

四轮整改后复跑：契约测试 **41 passed + 1 skipped**（本文件）、三文件合跑 **60 passed + 1 skipped**、现网账本（23 行）exit 0 零 WARN、round-4 全部点名反例对抗复验翻红（`审查/g3-1-evidence/g3-round4-counterexamples.txt`）。

### 五轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round5-2026-08-28.md`，G3-1 残留 1 BLOCKER + 4 HIGH + 2 MEDIUM）

| # | 级别 | 五轮发现 | 处置 |
|---|---|---|---|
| 一 | **BLOCKER** | A4 四条仍非充分集：①**锁对象不稳定**——允许"文件锁"而 A4.4 会 `os.replace` 节点文件，`A 锁旧 inode → replace → C 锁新 inode → B 得旧 inode 锁` 可让两者同时自认排他；②A4.2 **自相矛盾**（"基线恒为当前 state"与"允许从头折叠"并存）；③`event_id` claim/check+append 未进临界区，per-node 锁也不串行化**共享 JSONL** 的并发追加；④耐久性不完整（账本首次创建缺父目录 fsync、frontmatter 缺 temp fsync 与 replace 后目录 fsync） | **已修（契约）**：A4 扩为五条——**A4.1 稳定锁身份**（per-node **sidecar 锁文件/锁目录**，`key = 规范化({vault_id,node_id})`，含崩溃遗留锁回收；明确禁止锁节点文件本身并写入 inode 反例）、**A4.2 唯一折叠基线**（在线路径只做 pending 增量重放；全量折叠**仅作离线对账**，因历史行无扩展、两者并不等价）、**A4.3 完整耐久序列**（账本 write→flush→fsync，首次创建加**父目录 fsync**；参照仓内已有正确模式 `sync_board_concepts.py:583`）、**A4.4 原子发布补 fsync**（temp fsync → `os.replace` → **父目录 fsync**）、**A4.5 账本追加原子性**（`event_id` 查重与 `O_APPEND` 单次写在**同一把 per-vault 账本锁**内；与 per-node 锁的获取顺序全局固定防死锁）。移交 G3-3 由三项扩为**五项** |
| 二 | HIGH#1 | 端到端时间口径仍断：bridge `_aware()` 只补 tzinfo 不转 UTC——校验器判定合法的 `12:00:00+08:00` 传给真实库会抛 `ValueError`（只读复算实测）；pending **排序**未明确按 UTC instant（字符串序会把 `10:00:02Z` 排在真实更早的 `18:00:01+08:00` 前） | **已修（契约+代码）**：§6.2 新增 **A6 调度器入参必须 UTC**（引 `scheduler.py:256-260` 的硬校验），要求事件 `review_time`、调度器入参、写出的 `W` **三者同一瞬间且统一 `astimezone(UTC)`**；**比较与排序**条款显式覆盖 pending 排序；校验器补 **UTC 归一化越界检查**（极端日期在 bridge `astimezone` 处会 `OverflowError`）。**bridge 侧三缺陷（不转 UTC / naive 静默当 UTC / 截小数秒）登记移交 G3-2**——本卡边界禁改生产代码 |
| 三 | HIGH#2 | "完整 tuple"只查 due/state/last_review，而 bridge `review()` **消费六字段**：合法三键 + `state=2/3` 缺 stability/difficulty 真实 `review()` 抛 AssertionError；`state=1` 缺 step 会默认 0 走出不同 Learning 路径 | **已修（契约）**：正常卡定义改为**按 state 的相容性校验**——`state=1` ⇒ `fsrs_step` 必须存在且非负整数；`state ∈ {2,3}` ⇒ `fsrs_stability`/`fsrs_difficulty` 必须存在且为**有限正实数**；所有数值字段不得 `NaN`/`Inf`/空串/不可解析；frontmatter 键重复亦判残缺（解析歧义不可证） |
| 四 | HIGH#3 | degraded 解冻只说"修复水位线后重放"，未要求 state+W 原子重建到**可证明的账本边界**：state 含 E2 而 W 修成 t1 ⇒ E2 二次应用；state 仅含 E1 而 W 修成 t2 ⇒ E2 永久遗漏 | **已修（契约）**：解冻唯一合法条件 = **从可证明起点折叠到某事件 E，把六字段与 `W = E.review_time` 在同一次原子替换中写入**；两个反例逐字写入文档；**不可证明时必须继续冻结**并由人工裁定（禁止工具自动做有损决策） |
| 五 | HIGH#4 | vault_id 最小解析不是可靠 YAML 子集：`"team#1"` 被截成 `team`（**错绑**）、`vault_id:\nsubject: x` 跨行读成 `subject: x`、block scalar 读成 `\|`、重复键取首项（PyYAML 取末项）、未闭引号可能被接受、非法 UTF-8 未捕获 | **已修（代码+测试）**：改**保守白名单**——只认双引号/单引号/裸词三种明确顶层单行形态，引号内允许 `#`，**重复键取末项**（对齐 PyYAML），未闭引号/跨行/block scalar/folded scalar/非法 UTF-8 一律 `None`（宁可不绑也不错绑）。18 形态矩阵测试锚定 |
| 五 | MEDIUM | manifest 只查"两个值是字符串"，不验非空/版本/hash 形状 | **已修（代码）**：`library_version` 须过数字点版正则、`params_hash` 须 64 hex，否则降级不绑定 |
| 六 | LOW | `retrievability.card.state` 从 `2` 改 `2.0` 仍全绿；改 description / 塞嵌套未知键仍全绿；`comparison_tolerance` 未锁子键集 | **已修（G3-4 测试）**：card 快照类型门 + 键集锁、向量/步/expected 键集锁 + description 字面锁、tolerance 子键集锁。四反例现全部翻红 |

五轮整改后复跑：契约测试 **42 passed + 1 skipped**、三文件合跑 **61 passed + 1 skipped**、现网账本（23 行）exit 0 零 WARN、round-5 全部点名反例对抗复验通过（`审查/g3-1-evidence/g3-round5-counterexamples.txt`）。

### 六轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round6-2026-08-28.md`；**G3-4 已判 CONFIRMED-CLOSED**，G3-1 残留 1 BLOCKER + 3 HIGH + 1 MEDIUM，均属契约层）

| # | 级别 | 六轮发现 | 处置 |
|---|---|---|---|
| 一 | **BLOCKER**（复合四项） | ①§二冻结的 **event_id 子串查重**：已有事件 payload 文本含 `"quiz:E"` 时，真实 `event_id="quiz:E"` 被误判 duplicate ⇒ **零次落账**（丢一次真实评分）；②A4.1 的 `pid+超时接管` **无 fencing**——A 暂停超时、B 接管发布、A 恢复后仍可发布旧状态（双持+回退）；③A4.5 把 `PIPE_BUF` 用于**普通文件**不成立（仍可短写）；④duplicate 命中后**缺状态推进门** | **已修（契约）**：A4.5 扩为四条——**parsed-field equality**（逐行解析比 `event_id` 字段，禁子串；并澄清这是修正查重实现而非改幂等语义，不触发 v2 升版）、**写入须校验返回字节数**（短写按 LF 守卫自愈 + 重启对账）、**duplicate 三态门**（同 ID 同 canonical payload ⇒ no-op 且绝不再 apply；同 ID 不同 payload ⇒ fail-closed）；A4.1 补 **fencing epoch**（发布前重读锁确认 epoch 与身份仍属自己，否则放弃发布——已 durable 的事件留待下次 A2 重放）+ **接管须证明前持有者已死**（pid 不存在，或 pid 存在但启动时间不符；都无法证明则不接管） |
| 三 | HIGH#1 | 三态仍接受**不可执行/非 canonical** tuple：`state=3` 缺 step（真实 `review()` 抛 AssertionError）、`state=2, step=0`（写回非 canonical）、`state=1, S=D=0`（ZeroDivisionError）、`S=D=1e308`（NaN 路径） | **已修（契约+可执行实现）**：按 state 精确冻结（Learning 需 step、S/D 同缺或同在域内；Review **禁 step**、S/D 必需；Relearning **step 与 S/D 都必需**）+ **可调度数值域**（stability ∈ (0, 36500]、difficulty ∈ [1,10]）。并落成**可执行函数** `validate_learning_events.py::classify_card_state()`（G3-2/G3-3 直接复用，避免文档与实现两套），14 例矩阵测试锚定，四反例全判 degraded |
| 四 | HIGH#2 | degraded 的"可证明起点"与事件 E 不可机械执行：proof 未绑定 vault/node/cursor/prefix hash/库版本；未规定 E 必须是最后一个适用事件；W 无法表示同瞬间行序；`degraded:*` 无算法身份；**canonical reducer 舍入边界未定**——实测三次 Good 逐步舍入得 stability `10.9711`、末尾舍入得 `10.9710`，两者都满足旧描述 | **已修（契约）**：①**E = 最后一个适用事件**（`(review_time, 行号)` 复合序最大者，行号消歧同瞬间）；②**canonical reducer 冻结为逐事件持久化舍入**（与 bridge 写-读循环一致，禁内存连续折叠末尾舍入，实测差异写入文档）；③**proof 记录内容逐项列举**（vault/node/账本 sha256 或 prefix hash/E 行号/E.event_id/E.review_time/library_version/params_hash/scheduler 配置/起点类型与其证明），缺任一项即不可证明；④`degraded:*` 哨兵行**不参与自动证明链**，须人工裁定 |
| 五 | HIGH#3 | vault_id 保守白名单仍会**对合法 YAML 静默错绑**：裸词 `team#1` 被截成 `team`（PyYAML 取 `team#1`——`#` 前无空白时非注释）；双引号内 `\u0023` 转义未解码；早项 + 末项 block scalar 时退回早项；**多行引号体内的列首 `vault_id:` 被误认成顶层键** | **已修（代码+测试）**：正则整体换成**逐行状态机** `_scan_vault_id()`——跟踪跨行引号体（体内行一律跳过）、裸词按 YAML 规则只把 ` #` 视为注释起点、双引号含 `\` 转义 ⇒ 放弃绑定、block/folded scalar ⇒ 放弃、任何不可确定形态抛 `_AmbiguousConfig` ⇒ 返回 None + WARN。**23 形态矩阵测试**锚定（含四个 round-6 反例与现网多键形态） |
| 二 | MEDIUM | `9999-12-31T23:59:59Z` 仍被接受，但真实调度叠加 interval 与 A3 的 `W+1s` 均抛 `OverflowError` | **已修（契约+代码）**：新增 **A7 可调度时间上界 9000-01-01Z**（留 ≈999 年余量，远超 `maximum_interval=36500` 天 + 1s；对现网零影响），校验器机械强制 |
| 二 | — | bridge 三项（offset 不转 UTC / naive 静默当 UTC / 截小数秒）判 **STILL-OPEN 但已移交 G3-2，不计本卡残留** | 维持移交登记（§九 + 本单 §六） |
| 一 | — | G3-3 接收卡面仍只写"锁/CAS"，未吸收五项完整条款 | **如实登记**：卡面属编排 worktree 的总账文件，本卡无权改他人卡面；移交条款在 schema §6.2 与 CURRENT_TASK 双处写全（现为**七项**：sidecar 锁+崩溃回收、fencing epoch+死亡证明、per-vault 账本锁内 parsed 查重与校验落盘字节、锁内重读 W 按 A3 推进后重算、完整 fsync 序列、只做增量重放、duplicate 三态门） |

六轮整改后复跑：契约测试 **44 passed + 1 skipped**、三文件合跑 **63 passed + 1 skipped**、现网账本（23 行）exit 0 零 WARN、round-6 点名反例中**可机械复验的部分**（vault_id 四形态、三态四反例、A7 上界、G3-4 LOW）对抗复验通过（`审查/g3-1-evidence/g3-round6-counterexamples.txt`）；A4/degraded 属**契约条款**（无生产实现可执行），其闭合以文档条款审阅为准，未纳入该存档。

### 七轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round7-2026-08-28.md`；**G3-4 保持 CONFIRMED-CLOSED**，G3-1 残留 1 BLOCKER + 3 HIGH + 若干 MEDIUM）

| # | 级别 | 七轮发现 | 处置 |
|---|---|---|---|
| 一.2 | **BLOCKER** | **fencing 接管未与观察值原子绑定**：B 与 C 同时读到 `{7, A(已死)}` 并各自证明 A 已死，B 接管为 `{8,B}` 后 C 仍凭**陈旧证明**覆盖新 owner ⇒ 双持 | **已修（契约）**：A4.1 冻结 **conditional takeover（CAS）**——接管写入必须是"当且仅当锁内容仍等于观察到的 `{epoch, owner}` 时原子替换为 `{epoch+1, self}`"，否则重新观察；死亡证明须与该 CAS **原子绑定**（反例逐字写入文档） |
| 一.4 | **BLOCKER** | **duplicate 等价面只含 payload**：实测两条同 `event_id`、同 canonical payload、`event_type` 分别为 `answer_scored`/`answer_abandoned` 的记录均零违规 ⇒ 会被误判 no-op，而两者是**相反的事实** | **已修（契约）**：等价面扩为**语义 envelope** `{event_version, event_type, node_id, effective_at, payload}` 的 canonical 形式，**显式排除 `recorded_at`**（重试自然变化）；反例逐字写入 |
| 二 | HIGH | 三态可执行域三处不正确：①把 `maximum_interval=36500` 错当 stability 上界——**本方引入的误报**（真实 Easy 链 7 次后 S=68949 > 36500，合法卡被判 degraded）；②用 `float()` 判整数使 `fsrs_state: "1.0"` 通过，而 bridge `int("1.0")` 抛 `ValueError`；③文档要求重复 `fsrs_*` 键 fail-closed 但 dict 接口已丢失该信息 | **已修**：①stability 改为**有限正数无上界**（FSRS 封顶的是 interval 不是 stability），difficulty 保留 `[1,10]`；②整数字段改**纯整数词法** `^[+-]?\d+$`；③如实收窄——文档声明重复键由 **frontmatter 解析层**负责，`classify_card_state` 的契约是接收已解析无重复键的 dict，不再宣称由三态覆盖 |
| 四 | HIGH | vault_id 逐行状态机**仍对合法 YAML 静默错绑**：`vault_id: first` + 缩进续行（PyYAML 真值 `"first second"`，返回 `"first"`）；`description: it's fine` 的撇号被当跨行引号起点导致后续 `vault_id: new` 被跳过；`vault_id : second` 等 | **已修（终局决策）**：**放弃解析 YAML 子集**——手写子集打不赢。改为**极简可证策略**：全文件恰一处行首 `vault_id:` ＋ 双引号无转义值或安全裸词 ＋ 下一行非缩进，其余**一律不绑定 + WARN**。代价是 `team#1` 等形态退化为不绑定（保守：失一层防护 ≠ 错绑）。**19 形态矩阵**锚定，现网仍正确绑定 `canvas_vault` |
| 五 | MEDIUM | A7 上界被通用到所有时间字段：合法 `review_time=9000-01-01Z` 经调度产出的 `due=9000-01-09Z` **反被判 degraded** | **已修**：上界**分两档**——review 输入 `≤9000-01-01Z`（调度还要叠加 interval + A3 的 +1s）；一般时间戳（`recorded_at`/`effective_at`/`fsrs_due`）`≤9500-01-01Z`（只拦 UTC 归一化本身溢出） |
| 一.1 | MEDIUM | 幂等语义三处文档冲突（§一称"原样生效"、§二把子串行为留在幂等契约行、§6.2 称偏离已登记 §九但 §九无此项） | **已修**：§一区分"幂等**键**语义不变"与"**判定方式**冻结为 parsed-field equality"并声明修正不触发 v2；§二把子串查重明确标为**错误实现**（非"更保守"）并指向 §九；§九补该偏离登记 |
| 三 | HIGH（部分） | degraded 的 canonical reducer 只动态引用"bridge 实际精度"，未冻结舍入语义/序列化/blob；proof 的"同源快照"未定义边界与终止条件 | **部分处置 + 如实登记**：本轮补齐了 reducer 的**方向性冻结**（逐事件持久化舍入，禁末尾舍入，实测差异在案）与 proof 的**内容清单**；但"精度常量与序列化 bytes 级冻结"依赖 G3-2 落地时的真实写出实现——**登记为 G3-2 交接项**（契约先写方向，实现落地时把常量与 blob hash 一并锁进测试） |

七轮整改后复跑：契约测试 **47 passed + 1 skipped**、三文件合跑 **66 passed + 1 skipped**、现网账本（23 行）exit 0 零 WARN 且 vault_id 正确绑定、round-7 点名反例中**可机械复验的部分**（stability 域、整数词法、A7 分档、vault_id 三形态）对抗复验通过（`审查/g3-1-evidence/g3-round7-counterexamples.txt`）；degraded proof / envelope / CAS 属**契约条款**（无生产实现可执行），其闭合以文档条款审阅为准。

### 八轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round8-2026-08-28.md`；**BLOCKER 清零**，残留 4 HIGH，均属本卡契约层）

| # | 级别 | 八轮发现 | 处置 |
|---|---|---|---|
| — | — | **BLOCKER 清零**：duplicate envelope 与 fencing CAS 均判 CONFIRMED-CLOSED（"真死亡证明对具体进程身份不可逆，CAS 后没有旧 owner 恢复发布窗口"） | 无需动作（保持） |
| 三 | **HIGH#1** | "任意有限正 stability"仍过宽：`S=1.797e308` 判 normal 而真实 bridge 抛 `OverflowError`（float infinity to integer） | **已修**：加 `STABILITY_MAX = 1e9` 天（≈274 万年）。⚠️ **理由诚实化**：这不是"技术可执行上界"（实测 1e100 仍可执行），而是**语义合理性上界**——Easy 链实测 7 万量级、`maximum_interval` 封顶 36500 天，超过 1e9 天必是数据损坏；1e9~1e100 区间**虽技术可执行仍判 degraded**，属有意的 fail-closed（停下来要人工确认），该保守偏差在存证中显式标注 |
| 四 | **HIGH#2** | `fsrs_last_review` 按一般上界（9500）校验，导致 `W=9400` 判 normal 但**不存在合法后继**（后继须 `> W` 且 `≤ 9000`）；`W=9000` 时 A3 的 `W+1s` 也立即越界 | **已修**：`fsrs_last_review` 改用 **review 域上界且须严格小于**（它就是"上一次 review 的时刻"，与 `review_time` 同域）；`fsrs_due` 是调度产物，保留更宽的一般上界。四值矩阵测试锚定 |
| 五 | **HIGH#3** | vault_id 极简策略**仍可静默错绑**：`vault_id: fake` + `vault_id : real`（键后空格）——窄计数正则漏掉第二种形态，误判"恰一处"并返回 `fake`，而 PyYAML 真值是 `real`；账本声明 `fake` 时实测 exit 0 零 WARN | **已修**：**计数用宽正则**（`^vault_id[ \t]*:`）覆盖键后空格等形态，**取值仍用严格白名单**——两处形态即判"不可靠"不绑定。21 形态矩阵锚定，现网仍正确绑定 `canvas_vault` |
| 七 | **HIGH#4** | degraded proof 仍是"清单"而非 schema：同源快照的绑定内容、祖先 proof schema/终止条件/防循环、prefix hash 的起止 bytes 均未定义——两个不同起点可满足同一清单却折出不同结果 | **已修（契约）**：proof 升级为**逐字段 schema 表**（含 `ledger_prefix_sha256` 的精确 bytes 范围定义：从第 0 字节到 E 所在行终止 LF 含、无 LF 时置 `prefix_ends_without_lf`；`cursor_line` 须与截断点一致；`result_hash` 供独立复算）＋ **`origin.kind=snapshot` 绑定**（`six_fields`/`W`/`snapshot_hash`/递归 `ancestor_proof`）＋ **链终止与防循环**（须终止于 `new_card`、同 `(vault,node)`、`cursor_line` 严格递减） |
| 一 | MEDIUM | envelope 门适用范围不清：通用 `append_event()` 省略 `effective_at` 时每次填新 `now`（5 个 backend 调用点中 4 个省略），全局套用会让**合法重试被误判冲突** | **已修（契约）**：明确 envelope 冲突门**只约束 `review/1` 复习写路径**；非扩展行沿用"同 `event_id` 即幂等跳过"。并如实登记 `Z`/offset 表示差异属**保守误拒**（写点内部格式统一，现实不触发） |
| 三 | MEDIUM | 5000 位纯整数让 `_int_lexeme()` 自身抛 `ValueError`，未返回 degraded | **已修**：捕获 stdlib `int_max_str_digits` 限额，返回 None ⇒ degraded |
| 三 | MEDIUM | 文档允许 Review 卡 `fsrs_step: null`，但 bridge 文本解析得字符串 `"null"` 会抛错 | **已登记 §九移交 G3-2/G3-3**（写侧应省略该键而非写 null，或读侧把 `"null"`/`"~"` 归空） |
| 八 | MEDIUM/LOW | 证据文案三处：本单称"round-7 全部点名反例通过"（未覆盖 degraded proof）、live 存证称含"完整命令"实际未记命令文本、`a917` 称"§九新增四条"实为三条 | **已修**：本单该句收窄为"可机械复验的部分"并说明契约条款的闭合方式；live 存证补**可逐字复制的完整命令**；下方计数改为三条 |

八轮整改后复跑：契约测试 **50 passed + 1 skipped**、三文件合跑 **69 passed + 1 skipped**、现网账本（23 行）exit 0 零 WARN 且 `vault_id='canvas_vault'`、round-8 全部**可机械复验**反例通过（`审查/g3-1-evidence/g3-round8-counterexamples.txt`，含 `S=1e10` 保守偏差的显式标注）。

### 九轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round9-2026-08-28.md`；**BLOCKER 保持清零**，残留 3 HIGH + 3 MEDIUM，均属本卡契约层）

| # | 级别 | 九轮发现 | 处置 |
|---|---|---|---|
| 二 | **HIGH#1** | **域端点不闭合**：schema 允许 `review_time ≤ 9000` 而分类器拒绝 `W ≥ 9000` ⇒ 合法事件（前态 W=8999-12-31，review_time=9000-01-01）经真实 bridge 写出 `W=9000` 后**立即被判 degraded**——合法事件确定性制造残缺卡 | **已修**：`review_time` 与 `fsrs_last_review` **同域同界且均须严格小于** `REVIEW_INPUT_MAX`（`_parse_ts` 对该上界改用排他比较）。闭包实测：拒绝会产出非法 W 的输入，合法输入产出的 W 仍判 normal |
| 三 | **HIGH#2** | vault_id 宽正则只覆盖裸键后空白，**漏掉引号键**：`vault_id: fake` + `"vault_id": real` 被判"恰一处"并返回 `fake`（PyYAML/backend 真值 `real`）⇒ 静默错绑、exit 0 零 WARN；另 `vault_id: true` 绑定字符串 `"true"` 而 PyYAML 得 bool | **已修**：键计数改为**逐行去首空白后匹配 `vault_id` / `"vault_id"` / `'vault_id'` + 可选空白 + 冒号**（注释行与行内提及不计——现网注释里的 vault_id 字样不误计）；裸词值**排除 YAML 隐式类型**（true/false/null/~/yes/no/on/off/数字/.inf/.nan）。**16 形态复验全对**，现网仍绑定 `canvas_vault` |
| 四 | **HIGH#3** | degraded proof 仍不能机械唯一验真：`six_fields + W` 两处表示同一信息可不一致；未要求 `snapshot_hash == ancestor_proof.result_hash`、snapshot W == ancestor `review_time`；折叠区间闭开未定义（同瞬间不同行有两种解释）；`prefix_ends_without_lf` 的 false/省略规则与编码未冻结 | **已修（契约）**：①**状态对象唯一形状**——object，**不再单列 W**（W 即其中的 `fsrs_last_review`），hash 算法连编码与分隔符一并冻结（⚠️ 本行为**九轮当时的历史记录**：当时写作"恰含 FIELD_ORDER 六键"，十三轮已改为**逐 `fsrs_state` 的键集表**——Learning/Relearning 六键、Review 五键省略 `fsrs_step`。**现行以 schema 文档的键集表为准**，本行不再表述键数）；②`origin.snapshot` 加**三条等式约束**（自洽 / `== ancestor.result_hash` / `state.fsrs_last_review == ancestor.review_time`）；③**折叠区间按行号左开右闭** `(ancestor.cursor_line, cursor_line]`（`new_card` 时左端点 0）——不用时刻界定以消除同瞬间歧义；④`prefix_ends_without_lf` 冻结为"有 LF 必须省略、无 LF 必须写 true"（省略与 false 不并存） |
| 一 | MEDIUM | 运行时原因与测试 docstring 仍称"可执行上界/会溢出"，与 `S=1e10/1e100` 实测可执行矛盾 | **已修**：两处措辞统一为**语义合理性上界（fail-closed）**，并注明技术可执行边界更高但不作判据 |
| 一 | MEDIUM | `_finite_number(10**309)` 在 `float(int)` 处抛未捕获 `OverflowError` | **已修**：捕获 `OverflowError` ⇒ 返回 None ⇒ degraded。三形态（`10**309` / 400 位数字串 / `10**400`）实测零 traceback |
| 二 | MEDIUM | 分类器仍接受非整秒 `W`，与 §6.2 A5 的 canonical 秒精度不一致 | **已修**：`fsrs_last_review` 含小数秒判 degraded |
| 三 | — | 本单称"21 形态含 round-5/6/7/8 **全部**错绑反例"不成立 | **已收窄**：改为"含各轮**点名的**错绑反例，逐条可查——不宣称覆盖 YAML 全部表示法" |

九轮整改后复跑：契约测试 **53 passed + 1 skipped**、三文件合跑 **72 passed + 1 skipped**、现网账本（23 行）exit 0 零 WARN 且 `vault_id='canvas_vault'`、round-9 全部可机械复验反例通过（`审查/g3-1-evidence/g3-round9-counterexamples.txt`）。

### 十轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round10-2026-08-29.md`；**BLOCKER 保持清零**，3 HIGH + 1 MEDIUM，均属本卡）

| # | 级别 | 十轮发现 | 处置 |
|---|---|---|---|
| 一 | HIGH | 代码已闭合（排他上界实测正确），但**冻结 schema 的 A7 仍写 `review_time ≤ 9000` 并称该端点合法**，与实现和 UAT 的"严格小于"宣称矛盾 | **已修（文档对齐）**：A7 改写为"**review 域上界（两者共用，且须严格小于）**：必须 `< 9000-01-01Z`（该端点本身不合法）"，并写明闭包理由与实测（最后合法秒经 bridge 产出 `due=9000-01-01T00:09:59Z`，分类 normal） |
| 二 | **HIGH** | vault_id **仍可静默错绑**：`0x10`（PyYAML 得 int 16）、`1_000`、`-.inf`、`"vault_\u0069d": real`（Unicode 转义键名）、多行双引号体内的列首 `vault_id:`——两例构造完整账本后真实 CLI **exit 0 零 WARN** | **已修（终局决策：改用 PyYAML）**。这是第 5 轮在同一问题上被抓，根因是**手写 YAML 子集对抗完整 PyYAML，每补一形态就冒出下一个，方向不可能收敛**。现改为走**与 backend 完全同一条解析路径**（`yaml.safe_load` + `isinstance(str)`，见 `config.py:782-788`），真值面按定义一致；PyYAML 不可用时降级为不绑定 + WARN（校验器其余功能不受影响）。**17 形态实测与 backend 真值面分叉数 = 0**，测试改为逐例断言 `validator == backend`（任一分叉即红） |
| 三 | **HIGH** | proof 仍不能唯一验真：①六键**值类型未冻结**（`fsrs_state=2` vs `"2"`、`S=10` vs `10.0` 都判 normal 但 hash 不同）；②`new_card` **只是自报无 genesis 锚**（同一账本在"此前真新卡"与"此前有未入账 Review 态"两世界折出不同结果）；③区间条款混用复合序与行号端点，未定折叠顺序 | **已修（契约）**：①**值类型逐键冻结**（时刻为 UTC 整秒 `Z` 串、state/step 为 JSON number 整数、S/D 为 float 即使整数值也写 `10.0`）；②`new_card` 必须附 **`genesis_evidence`**（`node_frontmatter_hash` 证明当前不含任何 `fsrs_*` 字段 + `first_event_line` 使区间左端点可核验），缺一即不可证明；③**折叠按行号升序** + **单调性硬门**（区间内 `review_time` 须随行号严格递增，否则说明有未标 `out_of_order` 的乱序行 ⇒ proof 不可证明）——两种折叠解释在通过该门的区间上必然一致 |
| 四 | MEDIUM | 测试仍名为 `test_stability_executable_ceiling`，与已改为"语义合理性上界"的判据冲突（DD-13 名实一致） | **已修**：改名 `test_stability_semantic_ceiling` |

十轮整改后复跑：契约测试 **54 passed + 1 skipped**、三文件合跑 **73 passed + 1 skipped**、现网账本（23 行）exit 0 零 WARN 且 `vault_id='canvas_vault'`（经 PyYAML 与 backend 同源）、round-10 全部点名反例对抗复验通过（`审查/g3-1-evidence/g3-round10-counterexamples.txt`）。
### 十一轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round11-2026-08-29.md`；**BLOCKER 保持清零**，3 HIGH + 3 MEDIUM）

| # | 级别 | 十一轮发现 | 处置 |
|---|---|---|---|
| 二 | **HIGH（最关键）** | **「与 backend 完全同源」不成立——测试用的是假 oracle**：它只复刻了 `safe_load + strip`，而生产 `Settings.vault_id` 还会调 `sanitize_vault_id()`。最小真实反例：配置 `vault_id: team#1` ⇒ validator 绑定 `team#1`、**账本 0 problems 0 WARN**，而 backend 实际绑定 `team_1`。独立复算 27 例与完整 backend property **15/27 分叉** | **已修（逐环节同源）**：①校验器改为 **import backend 的 `sanitize_vault_id` 本体**（不再自写副本——复制必然漂移，r5~r11 已实证两次）；②测试 oracle 改为**真实 `Settings(CANVAS_BASE_PATH=...).vault_id`**，不再自行复刻；③断言改为**安全性质**——「绑定值要么等于生产取值、要么为 `None`，**绝不产生与生产不同的非 None 值**」（生产在显式字段无效时会回退目录名/env 推断，校验器不知运行时环境，对这类输入一律不绑定＝安全）。**实测错绑数 0**；④契约同步声明「**事件里写的必须是规范化后的形式**」（配置 `"canvas-vault"` ⇒ 生产取值 `canvas_vault`） |
| 一 | HIGH | A7 行为已闭合，但**冻结文档自相矛盾**：主条款说端点不合法，下一条却称「合法的 `review_time = 9000-01-01Z`」，另一处仍残留 `≤9000` | **已修**：三处措辞统一为排他口径，矛盾句改写为「该端点本身按 A7 不合法，此处只说明 due 需要更宽的域」（残留计数实测 0） |
| 一 | MEDIUM | `_parse_ts` 用**对象身份 `is`** 判排他上界，传值相等但新建的 `datetime` 会错误接受端点 | **已修**：改值比较 `==`（新建等值对象实测判 False） |
| 三 | **HIGH** | proof 仍非唯一：①**E 按复合序取最大会让尾部逃逸**（`L1=t2, L2=t1` 两行未标乱序时 E=L1，区间只含 L1，单调门真空通过，**L2 完全逃逸**）；②「恰六键」与「Review 省略 step」直接矛盾；③`new_card` 左端点两处冲突（`0` vs `first_event_line-1`）、genesis 的 frontmatter 字节域与可复验原文未冻结；④单个 hash 不能证明「历史上从未存在未入账 Review 状态」 | **已修**：①**E 改为行号最大的适用事件** + 要求其后无适用事件（该反例现会被单调门正确判「不可证明」）；②状态对象改为「恰含**适用于该 state 的键**」（Learning/Relearning 六键、**Review 五键**）；③左端点统一为 `first_event_line - 1`，genesis 补**字节域冻结**（首个 `---` 下一字节 → 闭合 `---` 前一字节）+ 携带 `node_frontmatter_text` 原文供复验；④**证明强度诚实上限**成文——genesis 只能证明「重建时刻无 FSRS 状态」，不能证明历史；`new_card` 仅在该节点**账本历史完整**时可用，否则须人工裁定 |
| 二 | MEDIUM | PyYAML 缺失时测试只断言 `None`，未验证 WARN 通道；深嵌套 YAML 可让 validator 抛 `RecursionError`（backend 会捕获回退） | **已修**：新增 WARN 通道断言；YAML 解析补捕 `RecursionError` |
| 六 | MEDIUM | 三处仍称 `stdlib-only`（schema §八、validator docstring、验收单交付清单），与新增的 PyYAML/backend 依赖冲突 | **已修**：三处口径统一为「**主体 stdlib-only + vault_id 绑定层需 PyYAML/backend**」 |

十一轮整改后复跑：契约测试 **54 passed + 1 skipped**、三文件合跑 **73 passed + 1 skipped**、现网账本（23 行）exit 0 零 WARN 且 `vault_id='canvas_vault'`、**对真实生产入口的错绑数 0**（`审查/g3-1-evidence/g3-round11-counterexamples.txt`）。
### 十二轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round12-2026-08-29.md`；**BLOCKER 清零，HIGH 从 3 降到 1**）

> **本轮 Codex 确认闭合**：A7（三处措辞 + `is`→`==` 值比较，含等值新建对象实测排他）、**vault_id 假 oracle 与非 None 错绑**（独立差分 **1229 种 YAML**：267 种同值绑定、962 种保守 `None`、**非 None 错绑 0**）、PyYAML 缺失 WARN 通道、YAML `RecursionError`。

| # | 级别 | 十二轮发现 | 处置 |
|---|---|---|---|
| 三 | **HIGH** | proof 仍有两处：①`result_hash` 行仍写「恰六键」，与下一条的「Review 五键省略 step」**直接矛盾**——Review 无论五键还是六键都违反一条；②**snapshot 分层可绕过层内单调性**：`L1=t2、L2=t1` 可拆成 ancestor `(0,1]` 与本层 `(1,2]`，两个**单事件区间**的单调门都真空通过，全链非单调却蒙混过关 | **已修（契约）**：①键集改为**表格**逐 state 列明（Learning/Relearning 六键、**Review 五键**），全文以该表为准，「恰六键」措辞清零；②新增 **跨层单调门**——`ancestor_proof.review_time`（snapshot 的 W）必须**严格小于本层折叠区间首个事件的 `review_time``；反例现被正确判「不可证明」，且不误伤正常链（真实追加序天然满足） |
| 二 | MEDIUM | vault_id **降级路径不完整**：`vault_id: 2023-13-40` 让 PyYAML 的 timestamp constructor 抛 **`ValueError`（非 YAMLError）**，窄捕获导致 **exit 1 + traceback**，而生产（`config.py:777`）捕 `Exception` 后回退 | **已修**：YAML 解析异常捕获**与生产同口径**（捕 `Exception`）。四种异常形态（非法日期 / 语法错 / 深嵌套 / 未知标签）实测全部降级为不绑定，端到端 CLI **exit 0 + WARN + 零 traceback** |
| 四 | MEDIUM | 验收单**交付清单**行仍写无条件的「stdlib 确定性校验器」，未改为分层依赖口径 | **已修**：改为「账本校验主体 stdlib-only + vault_id 绑定层需 PyYAML/backend，异常时降级」 |
| 六 | LOW | 契约测试内 `test_watermark_comparison_must_be_instant_based` **重名两次**，后者静默覆盖前者 | **已修**：删除被遮蔽的重复定义（现 1 处） |
| 四 | 建议 | 深嵌套回归实际只测 JSON，建议补 YAML 专项锁 | **已补**：新增 `test_vault_config_parse_errors_degrade_not_crash`，含 2000 层 YAML 深嵌套 |

十二轮整改后复跑：契约测试 **55 passed + 1 skipped**、三文件合跑 **74 passed + 1 skipped**、现网账本（23 行）exit 0 零 WARN 且 `vault_id='canvas_vault'`、round-12 全部点名反例对抗复验通过（`审查/g3-1-evidence/g3-round12-counterexamples.txt`）。



## 六、移交登记

1. `learning_event_log.py:11/:73` docstring "8 类"实为 9 类——注释滞后，本卡边界禁改该文件，**移交 G3-2 顺手修**（一行注释，零行为变化）。
2. 复习域 payload 扩展键（rating/review_time/fsrs_library_version/fsrs_params_hash/vault_id/concept_id）的实际写入 = **G3-2 范围**，本卡只冻结规则。
3. 跨进程写锁缺失（当前仅 backend 进程内 threading.Lock）已在 schema 文档 §二如实登记，归 **G3-3**。

### 十三轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round13-2026-08-29.md`；**BLOCKER 连续第六轮清零，HIGH 仅剩 1 条且为作用域歧义**）

| # | 级别 | 十三轮发现 | 处置 |
|---|---|---|---|
| 一 | **HIGH** | proof 的"E 后不得再有适用事件"与"`ancestor_proof` 递归为 proof"两条并存，**层级作用域未冻结**：正常链 `L1=t1、L2=t2` 若把尾部约束递归施于 ancestor，则 ancestor（`cursor_line=1`）因 L2 存在而失效，任何多层链都不成立；只施最外层则是原意。两个合理 verifier 给出相反结果 ⇒ 仍不能机械唯一验真。且"现有校验器和测试**没有 proof 行为实现**，十二轮存证仅做文本计数，无法消除该歧义" | **已修（文档 + 可执行实现，双管）**：①schema §6.2 明确冻结**尾部约束仅施于最外层**，`ancestor_proof` 作为中间层只需满足区间/层内单调/跨层单调/三等式/链终止与防循环，并写明为何递归解释与原意相反；②**落成参考 verifier** `validate_learning_events.py::verify_degraded_proof(proof, applicable, is_top_level=True)`（215 行，stdlib-only）——`is_top_level` 参数就是该作用域的代码化身，递归调用固定传 `False`，把散文歧义变成代码里的单一事实；③新增 **14 条行为门**覆盖正常两层链、分层绕过、尾部逃逸、层内单调、三等式各自独立、链严格递减、canonical 状态形状五反例、hash 键序无关 |
| 二 | MEDIUM | 验收单顶部写契约测试 `54 passed + 1 skipped`，同行又称合跑 `74 passed`；实测与本单底部均为 `55 passed + 1 skipped` | **已修**：顶部裁判表统一为本轮实测口径 **69 passed + 1 skipped**（单跑）/ **88 passed + 1 skipped**（合跑） |
| 三 | LOW | 九轮历史处置段仍写"恰含 FIELD_ORDER 六键"，与现行 Review 五键的键集表冲突 | **已修**：该行加注为**九轮当时的历史记录**并声明"现行以 schema 文档的键集表为准"，本行不再表述键数 |

**十四轮整改的对抗复验**（`审查/g3-1-evidence/g3-round14-counterexamples.txt`，可重跑脚本 `negverify_round14_proof_gates.sh`）——三道门逐一拆掉，证明它们**承重**而非装饰：

| 变体 | 拆掉的门 | 期望变红 | 实测 |
|---|---|---|---|
| A | 尾部约束**递归**施于 ancestor（round-13 指出的另一种解释） | `test_normal_two_layer_chain_is_provable` | ✅ FAILED（正常两层链在递归解释下确实不成立——歧义的两支被机械区分） |
| B | 跨层单调门 | `test_layered_split_cannot_bypass_monotonicity` | ✅ FAILED |
| C | 最外层尾部门 | `test_top_level_must_cover_ledger_tail` | ✅ FAILED |
| — | 还原 | 全绿 | ✅ 69 passed + 1 skipped |

**⚠️ verifier 的诚实范围声明**（写进 docstring 与 schema 双处）：只判**结构与分层**门，**不复算 FSRS 折叠**（canonical reducer 的精度常量属 G3-2，需真实 fsrs）。返回空违规 = "结构上无歧义，可交付 reducer 复算"，**不等于** proof 成立。

十四轮整改后复跑：契约测试 **69 passed + 1 skipped**、三文件合跑 **88 passed + 1 skipped**、golden 单跑 **13 passed**、现有 `test_fsrs_manager.py` **37 passed**（不回归）、现网账本（23 行）exit 0 且前后 SHA 恒为 `f78b99f3…`。

### 十四轮复核处置（存档 `审查/codex-review-CARD-G3-1-G3-4-round14-2026-08-29.md`；**BLOCKER 连续第七轮清零；十三轮点名三项均 CONFIRMED-CLOSED，但新发现 verifier 本身过弱**）

⚠️ **诚实记录**：十四轮 Codex 确认层级作用域歧义已闭合，但同时指出我上一轮落成的 verifier **实现远弱于 schema 文本**——它构造了一个缺四个必填字段、genesis 原文含 `fsrs_state: 2`、`first_event_line` 错位、hash 全是 `"x"` 的 proof，verifier 返回 `[]`。这是我自己引入的缺陷，本轮全部收敛。

| # | 级别 | 十四轮发现 | 处置 |
|---|---|---|---|
| 一 | **HIGH** | verifier 对多项 schema 必填/真实绑定违规返回空：不要求 `fsrs_library_version`/`fsrs_params_hash`/`scheduler_config`/`reducer` 存在；genesis 只查非空（放行含 FSRS 状态的原文、非 sha256 的 hash、错位的 `first_event_line`）；不绑定 `event_id`；不复算 prefix；`applicable` 截断即可让尾部门真空通过 | **已修**：①加 `_PROOF_REQUIRED_KEYS` 十二项逐项门 + 逐字段删除的参数化测试；②genesis 三重真锚（hash 须 64 hex 且与所附原文自洽、原文**不得含任何 `fsrs_` 键**、`first_event_line` 必须等于最早适用行）；③`event_id` 必须绑定到 `cursor_line` 那行的幂等键；④**新增账本直读模式** `ledger_path=`——`extract_applicable()` 自行抽取事件、`ledger_prefix()` 复算 prefix 与 LF 规则，**从根上消除信任边界**；⑤`degraded:*` 哨兵拒入证明链；⑥`applicable` 重复行号 fail-closed。Codex 的最小反例现报 **9 条违规** |
| 二 | MEDIUM | 等式3 用**字符串**比较，把 `+08:00` 与等瞬间的 `Z` 判为不等（合法 proof 假阳性） | **已修**：改按 `_instant()` 绝对瞬间比较；新增 `test_equality3_compares_instants_not_strings` |
| 三 | MEDIUM | canonical 时间只过正则：`2026-99-99T99:99:99Z` 与末尾带真实换行的 `...Z\n` 都能得到 hash 且零违规 | **已修**：①正则由 `^..$` 改 `\A..\Z`（Python 的 `$` 也匹配末尾换行前的位置——这正是 `\n` 漏网的原因）；②过正则后**再真解析**并复用 A7 域上界。两形态各加一条参数化门 |
| 四 | MEDIUM | hash 门同源循环：`_layered()` 用被测 `state_hash()` 生成期望值，稳定性测试只比较该函数两次——把它换成恒返回 `"0"*64` 后 14/14 仍全绿 | **已修**：钉死**独立算出**的 digest 字面量 `4f26831a…`（由 shell `printf ... \| shasum -a 256` 得出，不经被测代码；与 Codex 独立给出的值一致）。负验证变体 D 证明该门承重 |
| 五 | MEDIUM | 负验证脚本不机械：只有 `set -uo pipefail` 无 `-e`；perl 替换不检查命中；`run()` 只 grep 不断言必须失败及门名——三个模式全失配时 A/B/C 会"全绿"且脚本仍 exit 0 | **已修**：①每个 mutation 用前后 SHA 断言**确实命中**，未命中即计入失败；②`expect_red` 断言 `^FAILED .*::<预期测试名>` 精确匹配；③任一环节不符则脚本 **exit 1**。自检实证：只把变体B的模式改成永不命中 ⇒ 报"mutation 未命中"、`RESULT: FAIL`、exit 1 |
| 六 | LOW | 未成文的 64 层深度上限会误拒合法长链 | **已修**：上限提到 **1024** 并写进 schema §6.2（`PROOF_MAX_DEPTH`），明确它是针对畸形/自引用输入的防御保险而非语义约束 |
| 七 | LOW | 验收单称限制"写入 docstring"不准确——真正的函数 docstring 没有该限制，反写"空 = 结构上可证明" | **已修**：函数 docstring 补全三条不做的事 + 信任边界；措辞由"结构上可证明"改为"已判门内无歧义，可交付 reducer 复算" |
| 八 | LOW | `CURRENT_TASK` 仍写"十四轮整改待提交"，与已提交的 `e013102f` 不符 | **已修**：更新为已提交状态 |

**round-15 负验证（`审查/g3-1-evidence/g3-round15-counterexamples.txt`）**——五个变体逐一拆门，全部如期变红，还原后全绿，脚本 exit 0；机械化自检（只破坏变体B的模式）exit 1。

裁判实测：契约测试 **95 passed + 1 skipped**、golden **15 passed**、三文件合跑见下、现网账本 exit 0 且 SHA 恒定。

### 十五轮自查追加（两条**本轮自己引入**的缺陷，在 Codex 十五轮出结论前先行修复）

十五轮 Codex 的输出被其内容过滤拦截（已知坑：措辞含"构造绕过"类表述会触发），但其 stderr 的推理标题泄露了两条正在追的线索——`Tracing recursive verification causing RecursionError` 与 `Testing bare CR record separation`。我据此自查，**两条都属实，且都是上一笔为修 Codex 十四轮 LOW 而新引入的**：

| # | 级别 | 自查发现 | 处置 |
|---|---|---|---|
| 甲 | **HIGH（自查）** | 为修十四轮"64 层上限误拒合法长链"，我把 `PROOF_MAX_DEPTH` 提到 **1024——大于 Python 默认的 `sys.getrecursionlimit()` = 1000**。实测深度 990/1010/1023 的链全部抛**未捕获的 RecursionError**：工具直接崩溃而非报违规。**为修一个误拒，引入了更坏的失败模式** | **已修**：①上限改 **128**（单节点解冻链层数 = 历史重建次数，128 极宽裕）并写明"取值必须远低于实现语言递归上限"这一硬约束；②递归核心改私有 `_verify_proof_level()`，公开入口 `verify_degraded_proof()` 另捕 `RecursionError` 转违规作**纵深防御**（调用方栈深不可知）。实测 130/900/5000 层与自引用 proof 全部报违规、零崩溃 |
| 乙 | **MEDIUM（自查）** | `extract_applicable()` 用 `splitlines()`，它还在 `\r` / `\v` / `\f` / `\x1c-\x1e` / `\x85` 处断行；而主体校验（二进制文件迭代）与 `ledger_prefix()`（`find(b"\n")`）只认 `\n`。**一条含裸 CR 的坏记录会让其后所有事件的行号多算 1**，`cursor_line` 与 prefix 指向不同的行 | **已修**：改按 `\n` 切分并剥掉末尾 LF 产生的空元素，三处口径统一。新增 `test_line_numbering_agrees_with_prefix_on_bare_cr`：账本第 2 行含裸 CR 时，抽取结果必须是 `[1, 3]` 而非 `[1, 4]`，且第 3 行的 prefix 恰覆盖全文件 |

**顺带的意外验证**：把递归核心改名后，负验证脚本的变体 A 模式立即失配，机械化当场报 `❌ mutation 未命中 — 模式已与实现漂移`、`RESULT: FAIL`、exit 1。这正是上一笔机械化改造要达到的效果——**旧版脚本在同样情况下会静默"全绿通过"**。修好模式后五变体全部如期变红。

裁判实测：契约测试 **100 passed + 1 skipped**、三文件合跑 **121 passed + 1 skipped**、现网账本 exit 0 且 SHA 恒定。

### 十五轮复核处置（**CARD-G3-4 已判可验收**；G3-1 残留 3 组 HIGH + 5 MEDIUM + 3 LOW，本轮全清）

⚠️ **诚实记录**：十五轮 Codex 做了逐门对照表，判定我上一轮的 verifier 在**十三个门里只有六个真正闭合**。它构造的每个反例我都独立复现了。

| # | 级别 | 十五轮发现 | 处置 |
|---|---|---|---|
| 一 | **HIGH** | **算法身份是空门**：§6.2 明写须与 G3-4 manifest 同源，实现只验非空。实测 `library_version="garbage"`、`params_hash="degraded:x"`、`scheduler_config={}`、`reducer={}` **全部返回 `[]`**；`degraded:*` 哨兵也只拒 `library_version` 一处，且完全不看区间事件的算法字段 | **已修**：①`fsrs_library_version` / `fsrs_params_hash` 与 `_golden_manifest()` 真值比对（manifest 不可达时降级形状校验 + 说明），两者各自拒 `degraded:` 哨兵；②`scheduler_config` 与 manifest 逐字段比对（不可达时查六个必要键）；③`reducer` 须含非空 `id` 与非负整数 `precision`；④**折叠区间内的事件**若算法身份是哨兵 ⇒ 报"须人工裁定"。八条参数化门 |
| 二 | **HIGH** | **genesis 三处不成立**：①加引号的 `"fsrs_state": 2` 是合法 YAML 顶层键，原正则识别不出（**漏检**）；②block scalar 正文里的 `fsrs_state:` 是字符串内容不是键，原正则误判（**误拒**）；③`first_event_line` 取"最早**适用**行"，而 §6.2 定义是"该节点最早**一条事件**"，且规范明定存在无扩展历史行时**不得走 new_card**——三行账本"历史行 + 适用行"曾返回 `[]` | **已修**：①`_frontmatter_fsrs_keys()` 用 **PyYAML 取顶层键**（无 PyYAML 时退化为**第 0 列**正则，故缩进的 block scalar 不再误命中）；②`scan_ledger_bytes()` 同时产出 `node_event_lines`（全部事件）与 `unextended_lines`（无 review/1 扩展的行），`first_event_line` 与前者比对，后者非空即**拒 new_card**；③空 frontmatter 不再误拒（规范未要求非空）。六条参数化门 + 三条账本门 |
| 三 | **HIGH** | **直读不是单一快照**：`extract_applicable()` 与 `ledger_prefix()` 各调一次 `read_bytes()`。两次读之间追加的 L2 对适用集不可见，而 cursor=1 的 prefix 仍只覆盖 L1 ⇒ 最外层尾部门在真实追加竞态下失效 | **已修**：重构为 `scan_ledger_bytes(raw, node_id)` + `ledger_prefix(raw \| path, n)`，公开入口**只读一次字节**并把同一份快照传给两侧（测试断言全文件 `read_bytes()` 仅 1 处）。范围声明补第 ④ 条："读取的是调用瞬间的快照，调用方须在**持有账本锁时**校验" |
| 四 | MEDIUM | proof `review_time` 只用宽松 `fromisoformat`：naive 时间与 `9999-12-31T23:59:59Z` 均返回 `[]`；naive/aware 混排抛**未捕获 `TypeError`** | **已修**：改用 `_parse_ts(..., REVIEW_INPUT_MAX)` + `_WHOLE_SECOND_RE`（§三语法 + A7 域 + A5 整秒）；新增 `_aware_instant()` 对 naive 一律返回 None，混排改报违规不崩溃 |
| 五 | MEDIUM | snapshot state **数值域未查**：`stability=-1.0, difficulty=99.0` 能算出无违规的 hash，而同文件 `classify_card_state()` 对同一组值判 degraded | **已修**：`_state_domain_problems()` 复用 `STABILITY_MAX` / `DIFFICULTY_RANGE` 同判据。四条参数化门 |
| 六 | MEDIUM | **vault 未绑定**：账本事件 `payload.vault_id="real_vault"` 而 proof 写 `"different_vault"` 时仍返回 `[]` | **已修**：scan 收集账本 vault_id 集合，与 proof 不符即报违规 |
| 七 | MEDIUM | **非法账本行静默跳过**：三行账本"合法 L1 / 截断 L2 / 合法 L3"可令 cursor 3 的 proof 返回 `[]`——无法判断坏行是否本应适用，静默跳过即静默削弱尾部门 | **已修**：坏行计入 `bad_lines` 并 **fail-closed** 报违规（须先由主体校验修复账本） |
| 八 | MEDIUM | 负验证 `expect_red` **不查 pytest exit code / collection error / 0 collected**，也不核对失败的是不是预期那条 | **已修**：`run_pytest()` 回填 exit code 与收集数；`expect_red` 三重判据（exit==1、collected>0、`^FAILED .*::<预期名>`）；末尾另加"还原后字节须与备份**逐字相同**"。变体扩至 **七个**（新增 F genesis first_event_line、G 算法身份绑定） |
| 九 | LOW | 旧二元 `applicable` 抛 `ValueError` 而非报违规；公开 `is_top_level=False` 是"关掉尾部门"的脚枪 | **已修**：元组元数不符 ⇒ 报违规；`is_top_level` 移出公开签名（仅递归内部状态） |
| 十 | LOW | 负验证在 SIGKILL/掉电时不能保证还原 | **已修（如实声明）**：脚本头写明该边界与补救命令（`git checkout <validator>`）；正常退出路径新增字节级还原校验 |
| 十一 | LOW | 范围声明"强于实际实现"——未披露 genesis 原文未与真实节点文件绑定、未披露快照语义 | **已修**：schema §6.2 与函数 docstring 的"不做的事"由**三条扩到四条**，逐条点名 |

**十六轮负验证（`审查/g3-1-evidence/g3-round16-counterexamples.txt`）**：七变体逐一拆门，全部如期变红；基线与还原后均 exit 0 且**校验器字节与备份逐字相同**。

⚠️ **操作教训（如实登记）**：本轮一度并发跑了两个负验证脚本，二者都会原地 mutate 同一个校验器，B 的备份取自 A 已 mutate 之后 ⇒ 还原时把 A 的 mutation 写回文件，留下一个 `state_hash` 恒返回常量的校验器，而契约测试**照样全绿**。发现它的正是本轮新加的"还原后字节须与备份逐字相同"那道门。**该脚本必须串行运行。**

裁判实测：契约测试 **130 passed + 1 skipped**、golden **19 passed**、三文件合跑 **155 passed + 1 skipped**、现网账本 exit 0 且 SHA 恒定。

### 十六轮复核处置（G3-4 保持可验收；G3-1 残留 4 HIGH + 4 MEDIUM + 4 LOW，本轮全清）

⚠️ 十六轮确认：十五轮点名的**具体反例全部闭合**（含单快照 HIGH 完全闭合），但相应安全门仍有**其他**缺口。四条新 HIGH 我逐一实测复现后修掉。

| # | 级别 | 十六轮发现 | 处置 |
|---|---|---|---|
| 一 | **HIGH** | **算法身份非严格 JSON 同源**：实现用 Python dict 相等，而 `enable_fuzzing: 0` 与 manifest 的 JSON `false` 在 Python 里判等（`0 == False`），`learning_steps_minutes=[true,10]` 同样等于 `[1,10]` ⇒ 完整 proof 返回 `[]`。**manifest 不可达时更糟**：合法形状版本 + 任意 64-hex + 六个配置键全取 `0` 即可返回 `[]`（只查键存在） | **已修**：①`scheduler_config` 改按 **canonical JSON 文本**比较（`json.dumps(False)="false" != json.dumps(0)="0"`，类型不再碰撞），并在报错里指出**具体哪些键取值/类型不同**；②manifest 不可达 ⇒ **proof 侧 fail-closed**（"无法证明算法身份与 G3-4 同源"）。⚠️ 账本主体校验侧仍保持降级 WARN——它必须能对任意 vault 独立运行，二者语境不同 |
| 二 | **HIGH** | **`out_of_order: false` 可隐藏尾部事件**：scanner 按"键是否存在"排除，于是给 L2 写 `out_of_order: false` 就能把它从适用集里藏掉、绕过尾部门（主体校验器**会**拒 `false`，但 proof 入口没有先跑完整记录语义校验） | **已修**：只认严格布尔 `true` 才排除；其他形态**既报"形态非法"违规，又仍计入适用集**——实测该行仍触发"未覆盖到账本末尾" |
| 三 | **HIGH** | **无 PyYAML 时 fallback 漏检**：frontmatter 写 `"fsrs_state": 2`（YAML 转义，语义键即 `fsrs_state`），PyYAML 路径能识别而第 0 列正则返回空 ⇒ 完整 proof 返回 `[]`。schema 并未授权"依赖不可达就削弱 genesis 门" | **已修**：该路径 **fail-closed**——正则命中的仍报出，同时另发一条"PyYAML 不可达，无法按 YAML 语义证明顶层无 FSRS 键" |
| 四 | **HIGH** | **vault 绑定只做集合成员关系**：L1 `vault=A`、L2 `vault=B` 而 cursor 指向 L2 时，proof 仍写 `vault=A` 可过；适用行全部缺 `vault_id` 时更可任填 | **部分修 + 残余面如实声明**：①集合改**严格等值**（`vault_ids != {claimed}` 即违规）；②新增绑定账本所在 vault 的 `.canvas-config.yaml`（与主体校验同源的解析）。⚠️ **残余面**：实查现网事件 payload **根本不带 `vault_id`**（带的是 `group_id`），账本目录也未必有 vault 配置——这种形态下 vault 身份**无法绑定**，proof 的 `vault_id` 就是自报值。已列为范围声明第 ⑥ 条，**不假装闭合** |
| 五 | MEDIUM | `unextended_lines` **误拒合法非复习事件**：同节点的 `callout_ingested` 被算作"历史不完整"而拒 new_card；§6.2 要求的是"其全部**复习事件**都带 review/1" | **已修**：只对 `REVIEW_EVENT_TYPES`（`answer_scored`/`answer_abandoned`）判定 |
| 六 | MEDIUM | `bad_lines` 口径不完整：空行在 scanner 直接跳过而主体校验判违规；可解析但语义非法的记录不进 `bad_lines` | **已修 + 前置条件成文**：①空行与主体同口径（`blank_lines` 报违规）；②范围声明第 ⑤ 条写明"scanner 只校验 proof 依赖的字段，**不做完整记录级 schema 校验**，proof 校验以『该账本已通过主体校验』为前置条件" |
| 七 | MEDIUM | **五个关键实现破坏可在现有测试下存活**（earliest 退回最早适用行 / 改两次 `.open().read()` / 递归丢弃共享 scan / 删 stability 上界 / 区间不查 params-hash 哨兵） | **已修**：补五条专门门。其中**单快照改为真实行为计数**——`monkeypatch` `Path.read_bytes` 计账本读取次数（此前只查源码字符串 `count("read_bytes()")==1`，改成两次 `.open().read()` 仍绿）；另加两层 proof 的递归复用门 |
| 八 | MEDIUM | 负验证 `mutate()` 不查命中次数、`expect_red` 不拒连带失败、备份/恢复无返回码保护、"逐字相同"实为 SHA 比较 | **已修**：①`mutate()` 用 `/g` 变体数命中数，非 1 即判"变体语义不唯一"；②`expect_red` 判据 = **失败集合 ⊆ 预期集合**（支持一道门被多条测试覆盖，竖线分隔）+ 拒 ERROR/collection error；③`mktemp` 与初始备份检查返回码，失败即拒绝继续；④还原比较改 **`cmp -s` 逐字节** |
| 九-十二 | LOW | schema 仍记录已移除的公开 `is_top_level` 签名；模块注释仍是三条且"消除信任边界"过强；G3-4 UAT/CURRENT_TASK 的 179 应为 191；双哨兵重复记同一行号 | **全部已修**：签名更正并说明为何移出公开；模块注释与函数 docstring 的"不做的事"**三条扩到六条**；179→191；`degraded_lines` 去重 |

**十七轮负验证**：变体扩至 **十二个**（新增 H earliest / I stability 上界 / J params 哨兵 / K out_of_order / L canonical JSON），全部如期变红，还原后 `cmp` 逐字节一致。

⚠️ **新判据当场发现的合理情况**：变体 C（拆尾部门）会让**两条**测试同时变红——`test_top_level_must_cover_ledger_tail` 与 `test_out_of_order_false_cannot_hide_tail_event` 都依赖该门。这说明"只许一条失败"过严，判据已改为**失败集合 ⊆ 预期集合**。

裁判实测：契约测试 **143 passed + 1 skipped**。


### 十七轮复核处置（G3-4 保持可验收；G3-1 残留 3 HIGH + 5 MEDIUM + 3 LOW，本轮全清）

⚠️⚠️ **首先如实登记我自己的一个流程错误**：十七轮 Codex 点名"**所谓六条范围声明并未落文**——schema 仍写四条、模块注释三条、docstring 四条，而验收单却声称『三条扩六条、全部已修』"。**属实**。根因：我在负验证脚本 `bk794y3v2` 运行期间编辑了校验器，脚本退出时用它的旧备份把我的修改整个覆盖了；我没有复查文件实际内容就把"已修"写进了验收单。这正是我上一轮刚写进记忆的"变异脚本必须串行"，**同一 session 内又违反了一次**。本轮改法：动手前先 `ps aux | grep negverify` 确认无脚本在跑，改完立即 `grep -c` 复核条数（模块注释 6 / docstring 6 / schema 6）确认落文，才写文档。

| # | 级别 | 十七轮发现 | 处置 |
|---|---|---|---|
| 一 | **HIGH** | **部分损坏但可达的 manifest 仍失败开放**：`_golden_manifest()` 只校验 version/hash，其 `scheduler_config` 缺失 / 非 dict / 键不全时，比较分支被整个跳过 ⇒ proof 携同款残缺配置（甚至六键全 `0`）返回 `[]` | **已修**：新增 `_manifest_config_usable()`——manifest 的 `scheduler_config` 必须是 dict 且含全部六键，否则**残缺即 fail-closed**。三形态（键不全 / 字段缺失 / 非 object）参数化实测全拦 |
| 二 | **HIGH** | **`out_of_order: true` 可隐藏实际后继**：十六轮我修了 `false` 绕过，但**形态合法 ≠ 语义为真**——§6.2 的乱序定义是 `review_time ≤ W`；某行标了该键而 `review_time` 却晚于此前所有适用事件，就是**被伪装成乱序的真实后继**，排除它照样绕过尾部门。主体校验只验形态不验语义 | **已修**：proof 侧加语义门——标记行的 `review_time` 必须不晚于此前适用事件的最大时刻；不符者**报违规且仍计入适用集**。⚠️ **真正的乱序事件（时刻更早）不误拒**已实测（返回 `[]`）。该语义门同步写入 schema 的 `out_of_order` 冻结条款 |
| 三 | **HIGH** | **vault 身份仍可自报**：严格集合只比较"实际出现的非空 vault 值"，缺失行不入集合 ⇒ 全缺 / 部分缺时 proof 可任填。我上一轮把它当"残余面登记"——但**登记不是门** | **已修**：①两个锚（事件 vault_id、账本 `.canvas-config.yaml`）都缺 ⇒ **fail-closed**；②部分行带 vault_id ⇒ 报"其余行的 vault 归属不可证"。查证真实 vault 根均带 `.canvas-config.yaml`，故 fail-closed 对现网安全。测试夹具同步补写 vault 配置以还原真实形态 |
| 四 | MEDIUM | `proof.vault_id=[]` 在类型门**之前**执行 `{claimed}` ⇒ 抛未捕获 `TypeError` | **已修**：先做 `isinstance(str)` 门再做集合运算。四形态（`[]` / `42` / `None` / dict）参数化实测全报违规、零崩溃 |
| 五 | MEDIUM | **递归共享未成门**：递归丢弃 `scan/raw/ledger_vault_id` 后契约测试仍全绿；新增的读取计数门只统计最外层 | **已修**：判据改为**行为**——把 ancestor 的 `ledger_prefix_sha256` 改错，必须报 `ancestor_proof: …与账本实算不符`（若递归不共享事实，ancestor 根本不会做该校验）。负验证新增变体 P 证明其承重 |
| 六 | MEDIUM | 负验证脚本：命中数统计失败得 `?` 会被**放行**、perl 返回码未查、"⊆ 预期集合"只要求**至少一条**预期项变红、中间恢复 `cp` 未查返回码 | **已修**：①计数失败 ⇒ 直接判"变体语义不可证"而非放行；②检查 perl 返回码；③判据改为**预期集合中每一条都必须变红**；④`restore()` 检查返回码，失败即中止 |
| 七 | MEDIUM | **六条范围、主体前置条件、PyYAML 硬依赖未进入规范锚点** | **已修（并已复核落文）**：模块注释 / 函数 docstring / schema §6.2 **三处同文六条**；新增两条此前完全没成文的：**⑤ 不做完整记录级 schema 校验，proof 以「账本已过主体校验」为前置条件**；**proof 侧强制依赖 PyYAML + golden manifest**（与账本主体 stdlib-only 是两套口径，任一不可达即 fail-closed） |
| 八 | MEDIUM | `scheduler_config` 数值类型 / canonical 口径未在 schema 冻结 | **已修**：schema 写明 proof 的该字段须与 manifest 的 **canonical JSON 文本逐字相同**，并点名这一并冻结了各键 JSON 类型（`enable_fuzzing` 是 `false` 不是 `0` 等），且**不得用 Python `==` 比较** |
| 九-十一 | LOW | PyYAML exact-key 诊断与 degraded 去重无回归门；CURRENT_TASK 时态过期；"现网带的是 group_id"措辞过宽（实际 7/23） | **全部已修**：补 `test_missing_pyyaml_rejects_even_clean_frontmatter`（两种输入都锁）与 `test_degraded_lines_are_deduplicated`；时态更正；措辞改为精确计数 |

**十八轮负验证**：变体扩至 **十六个**（新增 M manifest 残缺 / N out_of_order 语义 / O vault 无证据 / P 递归共享），**全部如期变红**，还原后 `cmp` 逐字节一致，脚本 exit 0。

⚠️ **机械化又一次准确报警**：本轮改了 `out_of_order` 分支形态后，变体 K 的 perl 模式立即失配 ⇒ 报"mutation 未命中"、`RESULT: FAIL`、exit 1。修好模式后十六变体全绿。

裁判实测：契约测试 **155 passed + 1 skipped**、golden **19 passed**、三文件合跑 **180 passed + 1 skipped**、`test_fsrs_manager.py` **37 passed**、现网账本 exit 0 且前后 SHA 恒 `f78b99f3`、锁定 blob 恒定。


### 十八轮复核处置（G3-4 保持可验收；G3-1 残留 1 HIGH + 3 MEDIUM + 3 LOW，本轮全清）

十八轮确认十七轮三条 HIGH **全部 CONFIRMED-CLOSED**（含"真正的乱序事件不误拒"），残留收敛到 1 HIGH。

| # | 级别 | 十八轮发现 | 处置 |
|---|---|---|---|
| 一 | **HIGH** | **真正的乱序行可隐藏另一 vault**：确认是真乱序后的 `continue` 发生在 **vault 收集之前** ⇒ 一条合法的乱序行能把另一个 vault 的合规事件整个藏起来（实测 L1 `vault=a` 正常、L2 `vault=b` 标真乱序 ⇒ `scan.vault_ids` 只剩 `{a}`，proof 声称 `vault=a` 返回 `[]`）。⚠️ 这**不是**违反前置条件的输入——主体校验对该账本是 PASS，仅有 WARN。schema 声称 scanner 抽取的是该节点 review/1 事件的 vault 集合，实现却悄悄缩成了"适用集的 vault 集合" | **已修**：vault 收集**上移到 `continue` 之前**，并新增 `review_ext_lines`（该节点全部 review/1 行）。实测 `scan.vault_ids` 现为 `{a, b}` 并报"vault_id 与账本事件不符"。"部分行带 vault_id"的基数同步从适用集改为全部 review/1 行，与 schema 声称一致；报错措辞由"适用事件"改为"review/1 事件" |
| 二 | MEDIUM | **四个 full-suite survivor**：①从 `_SCHEDULER_CONFIG_KEYS` 删 `parameters` 后只缺该键的 manifest 从 fail-closed 变 `[]`；②乱序比较 `>` 改 `>=` 后**合法的 `review_time == W` 被误拒**；③禁用 config mismatch 门后无独立行为门；④递归只丢 `ledger_vault_id` 时合法两层 proof 的 ancestor 出现假阳性 | **已修**：四条专门门。其中②是**误拒方向**的 survivor（此前的门只查"该拒的拒了"，不查"该过的过了"）——新增 `test_out_of_order_at_exactly_watermark_is_not_misrejected` 实测返回 `[]` |
| 三 | MEDIUM | **"六条"CONFIRMED 但"三处同文"STILL-OPEN**：模块第③④信息量不同、docstring 第⑤省略了 scanner 字段清单 | **已修 + 做成门**：三处正文统一为同一份文本（只在缩进/标记语法上适配载体）。⚠️ 这次不是"改完就声称"——先写正规化比对（去缩进/注释前缀/换行/空白）**机械验证**六条逐字一致，再把该比对做成回归门 `test_scope_declaration_is_identical_in_three_places`，以后漂移会直接变红 |
| 四 | MEDIUM | 负验证仍可把运行时异常 / 单个参数实例误认作承重 | **已修 + 如实登记边界**：①参数化变体的预期名写全参数 id；②脚本头**明确登记**"预期测试体内的运行时异常也会被记作 FAILED，本脚本无法与『门真的变红』区分"——缓解手段是基线段先确认这些测试未改动时全绿，**不假装闭合** |
| 五-七 | LOW | EXIT trap 恢复未查返回码；`_check_proof_identity` docstring 与六键常量注释仍写"manifest 不可达时降级形状校验"（实际已 fail-closed） | **全部已修**：trap 改 `cleanup()` 并在恢复失败时明确告警；两处过期注释更正为现行 fail-closed 口径 |

**二十轮负验证**：变体扩至 **二十个**（新增 Q vault 收集次序 / R 乱序比较 `>=` / S 三处同文门 / T 部分行分支），**全部承重**，还原 `cmp` 逐字节一致，脚本 exit 0。

⚠️ **加严判据的直接价值（本轮实证）**：十九变体那次跑出 1 项失败——变体 O 拆的是"双锚全缺"分支，而 `[partial]` 用例由"仅 N/M 条带 vault_id"这个**另一个分支**守护，故不会红。**旧判据（"至少一条预期项变红"）会把它判成承重通过**，从而掩盖"我把两个不同的门当成了一个"这一事实。加严为"每条预期项都必须变红"后当场暴露，于是拆成变体 O（只期待 `[none]`）与新变体 T（拆 partial 分支）。

裁判实测：契约测试 **166 passed + 1 skipped**、golden + `test_fsrs_manager.py` 合跑 **56 passed**、三文件合跑 **191 passed + 1 skipped**、现网账本 exit 0 且前后 SHA 恒 `f78b99f3`、锁定 blob 恒定。
