# 学习事件账 Schema v1 冻结契约（learning_events.jsonl）

> **来源卡**: BATCH-2026-08-28-第五批 / CARD-G3-1
> **真相源**: `backend/app/services/learning_event_log.py`（既有生产实现，EVENT_VERSION=1）。本文档把该实现的现实**逐字段契约化并冻结**——文档描述实现，实现不迁就文档；两者不一致时以代码 + 契约测试为准并修订本文档。
> **姊妹文档**: `docs/fsrs-truth-source-d0-revision.md`（D0 修订：frontmatter=current state，事件账=审计/幂等/重放）
> **裁判**: 契约测试 `backend/tests/regression/test_learning_events_schema_contract.py` + 校验脚本 `backend/scripts/validate_learning_events.py`
> **冻结日期**: 2026-08-28（现网账本 22 行快照全量核验通过）

## 一、冻结声明与版本策略

- 本契约冻结 **EVENT_VERSION = 1**（`learning_event_log.py:31`）的记录结构。这是对既有实现的**加性扩展式冻结，不是 supersede**：既有 9 类事件、既有 7 字段、既有幂等语义原样生效。
- **加性扩展（无需 bump version）**：payload 内新增键；EVENT_TYPES 白名单经对账评审后新增类型。
- **必须 bump EVENT_VERSION（v2）的变更**：删除/改名任一顶层字段；改变任一顶层字段类型或语义；改变 event_id 幂等语义；payload 从 object 改为其他类型。v2 出现前，读方必须容忍未知 event_version 行（前向兼容：跳过并告警，不炸）。
- 禁止第二套账本与未登记直写（D0 修订 T3 条款）。

## 二、账本文件契约

| 项 | 契约 |
|---|---|
| 位置 | `<vault 根>/learning_events.jsonl`（backend 侧由 `settings.CANVAS_BASE_PATH` 解析，`learning_event_log.py:52-56`；容器内默认 `/vaults/canvas-vault`） |
| 格式 | JSON Lines：每行一个独立 JSON object，UTF-8，`ensure_ascii=False` |
| 追加语义 | append-only；只追加不改写不删除；重放/重建工具只读 |
| 幂等 | 同一 `event_id` 全文件唯一；重放时已存在即跳过（`append_event`,:82-89；skill 写点同约定）。**实现语义如实登记**：写侧查重为 `json.dumps(event_id) in line` 的**子串匹配**（非解析后字段等值）——若某 event_id 的 JSON 串形恰好出现在任意行的 payload 文本中，后续同名追加会被误判已存在而跳过（保守方向：宁可漏记不重记，与"写失败不炸主链"同向）。校验器按字段等值判唯一，语义更严 |
| 并发 | backend 进程内 `threading.Lock`（:49）；跨进程无锁（G3-3 地盘，v1 如实登记） |
| 失败语义 | `append_event()` **永不抛异常**（:66-69, :103-105）。**折叠语义如实登记（Codex round-1 HIGH）**：返回值 `False` 把"幂等跳过"与"IO 失败"折叠为同一信号（区别只在日志），调用方无法机械区分。已知消费者偏离：`tips.py:572-578` 把任意 `False` 当 duplicate 处理并中止 callout 管道（`accepted=False`）——IO 失败会被误报为重复，**该写点上"不阻断主链"不成立**（登记 §九，修复属生产路径不在本卡）。G3-2 新写点**禁止**依赖此折叠布尔：必须沿用 skill 写点模式，先显式查重（duplicate 可区分）再追加（IO 失败单独可见） |
| 行格式变体（合法） | JSON 分隔符风格不冻结：现网存量同时存在紧凑（无空格）与 `json.dumps` 默认（`", "`/`": "` 带空格）两种行；当前 backend 与 skill 写点均产默认风格。逐行独立解析，不要求全文件风格一致 |
| 截断自愈（G3-2 契约） | 崩溃可能留下**无换行符结尾的截断尾行**；此时直接 append 会把新事件粘进坏行（连坐损坏——Codex round-1 HIGH）。G3-2 落实**追加前 LF 守卫**：append 前检查文件尾字节，非 `\n` 则先补写 `\n` 再追加（截断行自愈隔离为独立坏行）。校验器把坏行如实报 FAIL；重放工具跳过坏行并留痕 |

**per-vault 命名空间**：账本归属 vault 由**文件物理位置**决定（vault 根目录下），无需记录 vault_id 字段。与 CARD-C1a vault_key 约定（唯一定义点 `scripts/send_bark.py::vault_key()`，vault 目录名 → 文件名/通知 id 安全 key）的对应关系：**账本所在 vault 根的目录名，经 `vault_key()` 即得该 vault 在 state 文件/推送锁/通知 id 域的命名空间 key**。两套命名空间同源（vault 目录名），不需要映射表。

## 三、顶层字段契约（恰好 7 键，冻结）

每行 JSON object **必须且只许**含以下 7 个顶层键（现网 22 行 100% 符合）：

| 字段 | 类型 | 约束 | 语义 |
|---|---|---|---|
| `event_id` | string | 非空；全文件唯一（幂等键）；调用方构造稳定值 | 幂等键。构造规则见 §四逐类契约（`前缀:业务id` 惯例） |
| `event_version` | int | 恒为 `1`（本契约冻结版本） | schema 版本 |
| `event_type` | string | 必须 ∈ EVENT_TYPES 白名单（9 类，见 §四）；未知类型写入侧直接拒绝 | 事件类别 |
| `node_id` | string | 可为空串（如 skill 写点缺节点语境时）；通常为节点名（文件 basename 去扩展名） | 事件关联的知识节点。**复习域语境下 node_id 即 concept_id**（见 §六） |
| `recorded_at` | string | 扩展格式 ISO-8601 datetime，**必须 timezone-aware**。受理语法：`YYYY-MM-DD` + 分隔符（限 `T`/`t`/空格）+ `HH:MM[:SS[.f…]]` + 时区（`Z` 或 `±HH:MM`）。序数日期等其他 ISO 变体**不受理**（现网写点从不产出；`fromisoformat` 会接受任意单字符分隔符，校验器已显式收紧——Codex round-1） | 记录落盘时刻 |
| `effective_at` | string | 同 `recorded_at` 语法；缺省 = recorded_at | 业务生效时刻（补录历史事件时与 recorded_at 分离） |
| `payload` | object | JSON object（可为 `{}`）；键集按 event_type 见 §四，只许加性扩展 | 事件明细 |

## 四、EVENT_TYPES 白名单逐类契约（9 类，冻结于 `learning_event_log.py:35-47`）

| event_type | event_id 构造 | payload 已知键（v1 现实，informative） | 写点 |
|---|---|---|---|
| `node_derived` | `derive:<新节点名>` | `{}` | vault skill `ai-linked-doc/SKILL.md:189`（静态 python 单行） |
| `exam_created` | `exam:<检验白板 basename>` | `exam_board` | vault skill `start-exam-board/SKILL.md` Step 6.5（:424-446 静态 python） |
| `answer_scored` | `quiz:<eid>` | `grade_norm`, `exam_board`, `attempt_count` | vault skill `quiz-answer/SKILL.md` 评分链（:324-341 静态 python） |
| `answer_abandoned` | `quiz:<eid>` | 同 `answer_scored` | 同上（`abandoned` 分支，:325） |
| `candidate_created` | `cand:<candidate_id>` | `source`, `description`(≤200 字符) | backend `app/services/conversation_distiller.py:445` |
| `candidate_accepted` | `accept:<candidate_id>` | `edited` | backend `app/api/v1/endpoints/errors.py:198` |
| `candidate_disputed` | `dispute:<candidate_id>` | `dispute_reason`(≤300 字符) | backend `app/api/v1/endpoints/errors.py:259` |
| `session_archived` | `archive:<session_id>` | `tips`, `errors`, `group_id` | backend `app/api/v1/endpoints/memory.py:815`（import :813） |
| `callout_ingested` | `callout:<callout_id>` | `callout_type`, `text`(≤200 字符) | backend `app/api/v1/endpoints/tips.py:565`（import :554）；`effective_at`=批注原始时间 |

新增类型流程（T4）：白名单对账评审（记录追加到本文档 §七）→ `EVENT_TYPES` 加性入集 → 本表补行 → 契约测试冻结集合同步更新（测试红即漏改）。

## 五、写点普查（2026-08-28 逐点核对现行号）

**backend（经 `append_event()`，5 个调用点 / 4 文件）**：

1. `backend/app/api/v1/endpoints/tips.py:565` — `callout_ingested`
2. `backend/app/api/v1/endpoints/memory.py:815` — `session_archived`（import 在 :813）
3. `backend/app/api/v1/endpoints/errors.py:198` — `candidate_accepted`
4. `backend/app/api/v1/endpoints/errors.py:259` — `candidate_disputed`
5. `backend/app/services/conversation_distiller.py:445` — `candidate_created`

**vault（skill 静态 python 直写同一文件、同 schema、同幂等约定，3 个写点）**：

6. `canvas-vault/.claude/skills/quiz-answer/SKILL.md:324-341` — `answer_scored` / `answer_abandoned`
7. `canvas-vault/.claude/skills/start-exam-board/SKILL.md:424-446` — `exam_created`
8. `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md:189` — `node_derived`

**计数勘误（如实记录）**：总账 v2 G3-1 档案节写"backend 4 写点 + vault 3 个 skill 静态写点"（=7）；开跑手册 §二写"5 后端写点 + 3 skill 写点"。逐点实查结果为 **backend 5 调用点（errors.py 含 2 个）+ vault 3 = 8 写点**；v2 卡的"4"为文件粒度或批次3' 初始接入数的沿写。本文档以调用点粒度 8 为准。

**同名陷阱（防混淆）**：`MemoryService.record_learning_event()` / `unified_learning_event.py`（LearningEvent → Graphiti episode / Neo4j 管道）与本账本**无关**——它们不写 `learning_events.jsonl`。全仓 `learning_events.jsonl` 写点即上表 8 处（2026-08-28 grep 全仓核验）。

## 六、复习域扩展规则（G3-2 预备，本卡只定契约不动写路径）

G3-2 把复习评分写路径接入账本时，按以下**加性**规则执行：

### 6.1 事件形状

- **不新增 event_type**：沿用既有 `answer_scored` / `answer_abandoned`（白名单不变，见 §七评审记录）。
- **机械可判别标记（Codex round-1 HIGH）**：扩展行 payload **必须**含 `"schema_ext": "review/1"`。这是历史行与新契约行的唯一机械分界——校验器对含此标记的行强制以下键与类型，对无标记行（全部历史行）零追溯零误报。
- **扩展必填键**（`schema_ext == "review/1"` 时 REQUIRED，类型由校验器强制）：
  - `vault_id`：非空 string——显式冗余 vault 归属（与文件位置隐含归属互证）
  - `concept_id`：非空 string——映射关系 = 顶层 `node_id` 承载 concept_id（节点名），payload 内显式重申
  - `rating`：int 且 ∈ {1,2,3,4}（FSRS Rating；bool 伪装 int 判违规）
  - `review_time`：本次复习业务时刻（§三受理语法，tz-aware；与 `effective_at` 一致）
  - `fsrs_library_version` + `fsrs_params_hash`：产生本次调度结果的库版本与参数指纹。**口径 = G3-4 `backend/tests/regression/fsrs_golden_manifest.json` 的 `library_version` / `params_hash`（sha256 canonical scheduler_config）**——同分支交付，形式依赖已闭合。
  - **降级口径（诚实声明，Codex round-1 HIGH）**：fsrs 库不可用而评分链仍降级运行时，两键填 `"degraded:<原因>"` 哨兵（如 `degraded:fsrs-import-failed`）——禁止编造 hash、禁止留空、禁止省键。校验器接受该哨兵形态。

### 6.2 写序与崩溃恢复状态机（G3-2 落实；Codex round-1 BLOCKER + round-2 交错窗口整改）

**水位线定义（字段名以真实实现为准）**：`W(node)` = 该节点 frontmatter 的 **`fsrs_last_review`**（`canvas-vault/.claude/scripts/fsrs_bridge.py:44-46` FIELD_ORDER 真相源；写出格式 `%Y-%m-%dT%H:%M:%SZ`，**秒级精度**）。**键缺失（新卡从未复习）⇒ `W = -∞`**（该节点全部事件均为 pending）。

**pending 集合**：账本中该节点全部 `payload.review_time > W` 的 `schema_ext=review/1` 事件，按 `(review_time, 账本行序)` 升序。

三条硬约束，G3-2 必须同时实现（缺一则 exactly-once 不成立）：

- **A1 write-ahead**：先追加事件再更新 frontmatter。当前现实为 frontmatter 先写、事件后补，差异已在 D0 修订 §四登记。
- **A2 恢复先于新写（消灭交错窗口）**：任何复习写点在**追加新事件之前**，必须先把该节点的 pending 集合按序重放至空。
  - **为什么必要**（round-2 反例）：若允许"E1@t1 落账未应用时 E2@t2 直接从旧状态推进到 t2"，则水位线抬到 t2 后 E1 满足 `t1 ≤ W` 被误判已应用，**E1 对 current state 的贡献永久丢失**。A2 使任意时刻**至多只有最后一次追加的事件**可能处于 pending，该交错窗口在构造上不可能出现。
  - 崩溃窗口全覆盖：①事件已落账、frontmatter 未推进 → 下次写入前 A2 重放恢复；②两者都完成 → `review_time ≤ W`，不推进（幂等）；③追加即崩（事件未落账）→ 账本与 frontmatter 一致，本次评分丢失属用户可感知重试面，非账本不一致。
- **A3 严格递增 + 等时消解**：写侧必须保证同节点新事件 `review_time` **严格大于** `W`（秒级精度下若计算值等于 `W`，推进到 `W + 1s` 后再写）。这使 `>` 比较在秒级时间戳下无歧义。并发下的强制（两进程同时通过 A3 检查）归 **G3-3 per-node CAS**——⚠️ **移交条款**：G3-3 卡面当前未定义"等时拒绝/复合排序"，实施时须补此项，否则 A3 在并发面失去强制。

**三态语义（消解"已应用 vs 迟到乱序"歧义）**：`review_time ≤ W` 的事件**一律不推进 current state**——无论它是"已应用"还是"迟到的乱序事件"，对 current state 的动作**完全相同**，因此该歧义对 exactly-once 无影响。二者的区分只用于**账本标注**（G3-3 的 `out_of_order` 标记），其判据是**事件到达序**（追加时该事件 `review_time` 是否小于当时账本内该节点的最大 `review_time`），不是水位线。

- **duplicate 与 IO 失败必须可区分**（§二折叠语义）：G3-2 写点先显式查重再追加，禁止依赖 `append_event` 的折叠布尔。
- **截断尾行 LF 守卫**：见 §二"截断自愈"行。

### 6.3 历史兼容

- 历史行（无 `schema_ext` 标记的 `answer_scored`/`answer_abandoned`）**永久合法**——校验器不以扩展键缺失判 FAIL（防对现网账本误报）。历史行不参与 6.2 水位线重放（无 `review_time`，视为已应用）。

## 七、白名单对账评审记录

| 日期 | 评审 | 结论 |
|---|---|---|
| 2026-07-23 | `callout_ingested` 加入白名单（燃料策略对账批次5' 方案评审） | 通过，第 9 类（`learning_event_log.py:33-34` 注记） |
| 2026-08-28 | G3-1 冻结评审：复习域是否需要新 event_type？ | **否**——`answer_scored`/`answer_abandoned`/`exam_created` 已覆盖复习动作语义；G3-2 走 payload 加性键（§六），EVENT_TYPES 白名单 9 类不变。若未来出现无法归入现有 9 类的复习动作（如调度重算、休眠/恢复），须新开评审行再入集 |

## 八、校验脚本契约（`backend/scripts/validate_learning_events.py`）

- **定位**: 确定性、stdlib-only、可独立对任意 vault 的账本文件执行（不依赖 backend 运行环境）。白名单在脚本内复制一份，由契约测试与 `learning_event_log.EVENT_TYPES` 锁死同步（漂移即红）。
- **用法**: `python3 backend/scripts/validate_learning_events.py <learning_events.jsonl 路径>`
- **判定规则**（每行）: **严格 JSON** 可解析（RFC 8259——拒 `NaN`/`Infinity` 非标准常量、拒对象内重复键；写侧 `json.dumps(dict)` 不可能产出两者，合法数据零误报）；非法 UTF-8 字节序列 = 该行违规（逐行独立解码，不中断其余行）；**前向兼容分流**：`event_version` 为 int 且 ≠1 的行**只 WARN 并完全跳过 v1 形状校验**（Codex round-1：原"WARN+形状 FAIL 双发"违反前向兼容，已修）；v1 行：顶层键**恰好** 7 键、各字段类型/约束按 §三、`event_type` ∈ 白名单、时间戳按 §三受理语法且 tz-aware；payload 含 `schema_ext: "review/1"` 时强制 §6.1 扩展键类型。**文件级**: `event_id` 全文件唯一（跨版本行也登记——幂等键语义跨版本恒定）。无标记历史行的 payload 键集不做 FAIL 判定（§6.3）。
- **exit code**: `0` = 全部通过；`1` = 存在违规（逐行报告）；`2` = 用法/IO 错误。输出确定性排序，可入 CI。

## 九、已知差异登记（不改代码本体，如实记录）

| 差异 | 位置 | 说明 |
|---|---|---|
| docstring/注释写"8 类"，实际白名单 9 类 | `learning_event_log.py:11`（"限 8 类核心动作"）、:73（"8 类白名单"） | `callout_ingested` 2026-07-23 入集后注释未同步。本卡边界不动该文件；移交 G3-2 顺手修注释（一行，无行为变化） |
| v2 卡"backend 4 写点"计数 | 总账 v2 G3-1 档案节 | 实为 5 调用点，见 §五勘误 |
| **tips 写点把 IO 失败误报为 duplicate 并中止管道**（Codex round-1 HIGH） | `tips.py:572-578` | `append_event` 返回 `False` 折叠两义（§二），tips 消费者按 duplicate 分支返回 `accepted=False`——IO 失败时 callout 被错误拒收且"不阻断主链"不成立。生产路径修复不在本卡；**移交独立 micro-patch**（⚠️ G3-7 卡面只含 `/review/record`、`/fsrs-state`、mastery grade 三条路径，**不含 tips**——不可默认由其顺带收，Codex round-2 指出） |
| **tips 入口可产出 naive `effective_at`**（Codex round-1 HIGH） | `tips.py:510`（`CalloutDirectRequest.added_at` 接受 naive datetime）→ `:570` `isoformat()` 落账 | 违反 §三 tz-aware 契约的**潜在 producer 缺陷**（现网 22 行未命中——实际调用方都传了 tz-aware）。校验器会如实抓出此类行。生产路径修复不在本卡；**移交独立 micro-patch**（与上条同 owner），修法 = schema 层 `AwareDatetime` 或入口归一化 UTC |
