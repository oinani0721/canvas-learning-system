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
| 契约测试 `backend/tests/regression/test_learning_events_schema_contract.py` | **50 passed + 1 skipped**（本文件单跑口径，八轮整改后；skip = 仓内 vault 根无账本的 worktree 环境，主仓自动生效。与 golden 门 + 既有账本测试合跑 = **69 passed + 1 skipped**） |
| **真实 producer 执行**（Codex 一轮 HIGH 整改） | vault 三 skill 写点的 python 代码**从 SKILL.md 逐字提取执行**（ai-linked-doc 单行模板 / start-exam-board PYEOF 块 / quiz-answer 评分链账本段；仅路径常量重定向 tmp fixture），产物过校验器 + 幂等重放断言；backend 侧按 5 调用点实参形状经真实 `append_event` 写入后全过 |
| 既有账本回归 `test_learning_event_log.py` | 6 passed（零改动） |
| 校验脚本 vs 三 fixture | 合法 → exit 0 / 缺字段 → exit 1（点名 `effective_at`）/ 重复 event_id → exit 1（点名首见行号）（存证 `审查/g3-1-evidence/g3-1-fixture-validation.txt`） |
| 校验脚本 vs **现网账本**（当前 23 行，用户仍在产生新事件） | **exit 0** 零 WARN 零 FAIL，且 sha256 运行前后一致（只读证明；存证按每轮整改重生成，含 HEAD/validator SHA/完整命令） |
| 现网写点 0 误报 | 按 8 个写点 1:1 建模的 `real_shapes.jsonl`（含 Z 后缀时间戳/紧凑分隔符/中文 event_id）全过 |
| 边界判定 | 截断行如实报 FAIL / 未知顶层字段拒绝 / naive 时间戳拒绝 / **NaN·Infinity 非标准常量拒绝（RFC 8259 严格）** / **行内重复键拒绝（json.loads 静默取后者的歧义面）** / 未知 event_version 走 WARN 前向兼容通道不误杀 |
| 漂移锁 | EVENT_VERSION=1、9 类白名单、7 键形状、校验器复制份 == 真相源（四路契约测试）+ **`rating_from_grade` 与 `fsrs_bridge` 逐档等价**（千点网格 + 三档分界两侧）+ **W 与 review_time 的瞬间等价关系**（bridge `_iso` 写出格式改变即红）+ **`.canvas-config.yaml` 解析 21 形态矩阵**（极简可证策略；含 round-5/6/7/8 全部错绑反例） |
| 铁律遵守 | `learning_event_log.py` **零改动**；git diff 只含新增文件 + CLAUDE.md/architecture.md 引用行 + CURRENT_TASK；未新建任何第二套账本 |
| ruff | 本卡交付文件 All checks passed（`backend/scripts/` + 契约测试；**范围声明**：仓库其余既有告警不在本卡范围） |

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

## 六、移交登记

1. `learning_event_log.py:11/:73` docstring "8 类"实为 9 类——注释滞后，本卡边界禁改该文件，**移交 G3-2 顺手修**（一行注释，零行为变化）。
2. 复习域 payload 扩展键（rating/review_time/fsrs_library_version/fsrs_params_hash/vault_id/concept_id）的实际写入 = **G3-2 范围**，本卡只冻结规则。
3. 跨进程写锁缺失（当前仅 backend 进程内 threading.Lock）已在 schema 文档 §二如实登记，归 **G3-3**。
