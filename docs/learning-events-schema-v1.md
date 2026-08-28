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
  - **降级绕过封堵（Codex round-3 HIGH）**：`schema_ext` 出现但值不是 `"review/1"`（如 `"review/01"`、非字符串）= **违规**，不得静默降级为历史行；复习事件 payload **带扩展键却无 marker** 同样违规（历史行 payload 只有 `grade_norm`/`exam_board`/`attempt_count`，不含扩展键，故对存量零误报）。
- **挂载点限定**：`review/1` 只许挂在 `answer_scored` / `answer_abandoned` 上（挂到 `session_archived` 等 = 违规）。
- **扩展必填键**（`schema_ext == "review/1"` 时 REQUIRED，类型与语义由校验器强制）：
  - `vault_id`：非空 string——显式冗余 vault 归属，**必须等于账本同目录 `.canvas-config.yaml` 声明的 `vault_id`**（与文件位置隐含归属互证；防事件写错 vault 或账本被搬运后仍自称原 vault）。校验器找不到该配置文件时降级为 WARN（保持对任意 vault 独立可跑）。
  - `concept_id`：非空 string，且**必须等于顶层 `node_id`**——映射关系 = `node_id` 承载 concept_id
  - `rating`：int 且 ∈ {1,2,3,4}（FSRS Rating；bool 伪装 int 判违规）
  - `grade_norm`：数值且 ∈ [0,1]（既有 quiz-answer 写点已产此键）
  - **评分自洽（Codex round-3 HIGH）**：`answer_scored` 的 `rating` 必须等于 `rating_from_grade(grade_norm)`（`fsrs_bridge.rating_from_grade` 口径：`grade = 1 + 3·gn` 就近落四档、越界钳制）；`answer_abandoned` 的 `rating` **恒为 1**（[Decision-FSRS-1] 弃答一票否决 Again）。
  - `review_time`：本次复习业务时刻（§三受理语法，tz-aware，**必须整秒**见 §6.2 A5）；与顶层 `effective_at` **同一瞬间**（按绝对时刻比较——`Z` 与 `+00:00` 是同一瞬间的两种写法，不按原字符串比）
  - `fsrs_library_version` + `fsrs_params_hash`：产生本次调度结果的库版本与参数指纹。**非降级时必须与 G3-4 `backend/tests/regression/fsrs_golden_manifest.json` 的 `library_version` / `params_hash` 真值相等**（Codex round-3 HIGH：只验形状时 `999.999` + 全零 hash 可蒙混）；校验器找不到该 manifest（脚本被拷到别处独立运行）时降级为形状校验并输出 WARN。
  - **降级口径（诚实声明）**：fsrs 库不可用而评分链仍降级运行时，两键填 `"degraded:<原因>"` 哨兵（如 `degraded:fsrs-import-failed`）——禁止编造 hash、禁止留空、禁止省键；两键的 degraded 状态必须**成对**，原因非空。

### 6.2 写序与崩溃恢复状态机（G3-2 落实；Codex round-1 BLOCKER + round-2 交错窗口整改）

**水位线定义（字段名以真实实现为准）**：`W(node)` = 该节点 frontmatter 的 **`fsrs_last_review`**（`canvas-vault/.claude/scripts/fsrs_bridge.py:44-46` FIELD_ORDER 真相源；写出格式 `%Y-%m-%dT%H:%M:%SZ`，**秒级精度**）。

**水位线三态（Codex round-3 HIGH + round-4 HIGH#2 收紧）**：判别按**完整 FSRS tuple 的可解析性**，不只看单键存在性。
- **真新卡** = 节点 frontmatter **不含任何 `fsrs_*` 字段** ⇒ `W = -∞`，全部事件 pending（合法首事件路径）。
- **正常卡** = **同时**满足：含 `fsrs_last_review` 且值可解析为 tz-aware 时刻；含 `fsrs_due` 且可解析；含 `fsrs_state` 且 ∈ {1,2,3}（`fsrs_bridge.py:44-46` FIELD_ORDER 的必备三项）⇒ `W` = `fsrs_last_review`。
- **残缺卡 = 上述两者以外的一切组合**，一律 **fail-closed**（禁止自动重放，报 degraded 待修复）。显式列举（round-4 点名的灰区）：
  - 缺 `fsrs_last_review` 但有其他 `fsrs_*`（原残缺卡）；
  - **只有 `fsrs_last_review` 而缺 `fsrs_due`/`fsrs_state`**——bridge 在无 `fsrs_due` 时按 New 卡处理（`fsrs_bridge.py:102`），与"正常卡"语义冲突；
  - `fsrs_due` + `fsrs_last_review` 但缺 `fsrs_state`；
  - 任一必备键值为空串 / 不可解析 / `fsrs_state` 越界。
- **理由**：`W` 的可信前提是"当前 current state 与该水位线属同一次应用"。任何字段缺失或不可解析都意味着这个前提不可证——此时按 `-∞` 重放会二次推进，按该 `W` 前进又可能建立在错误状态上，唯一诚实处置是停下来。

**比较语义（必须按绝对瞬间，不得按字符串）**：`W` 与 `review_time` 的所有比较（`>`、`≤`、相等）**必须先解析为 tz-aware datetime 再比**。理由：bridge 的 `_iso()` 把时刻 `astimezone(UTC)` 后写成 `...Z`（`fsrs_bridge.py:55-56`），而事件的 `review_time` 允许任意合法 offset——实测 `2026-08-01T18:00:00+08:00`（事件）与 `2026-08-01T10:00:00Z`（W）**是同一瞬间但字符串不同**。按字符串比较会把"已应用"判成 pending 并二次推进。

**整秒性判定同样按 UTC 归一化后计**：A5 要求的"整秒"在 UTC 归一化后保持（offset 只到分钟级；含秒的 offset 已被 §三 受理语法拒绝）。

**pending 集合**：账本中该节点全部满足以下全部条件的事件：`schema_ext == "review/1"`、**未标 `out_of_order`**、且 `payload.review_time > W`（按绝对瞬间比较）；按 `(review_time, 账本行序)` 升序。

五条硬约束，G3-2 必须同时实现（缺一则 exactly-once 不成立）：

- **A1 write-ahead**：先追加事件再更新 frontmatter。当前现实为 frontmatter 先写、事件后补，差异已在 D0 修订 §四登记。
- **A2 恢复先于新写（消灭交错窗口）**：任何复习写点在**追加新事件之前**，必须先把该节点的 pending 集合按序重放至空。
  - **为什么必要**（round-2 反例）：若允许"E1@t1 落账未应用时 E2@t2 直接从旧状态推进到 t2"，则水位线抬到 t2 后 E1 满足 `t1 ≤ W` 被误判已应用，**E1 对 current state 的贡献永久丢失**。A2 使**单写者下**任意时刻至多只有最后一次追加的事件处于 pending，该交错窗口不会出现。**并发下 A2 本身不够**——见 A4。
  - 崩溃窗口全覆盖：①事件已落账、frontmatter 未推进 → 下次写入前 A2 重放恢复；②两者都完成 → `review_time ≤ W`，不推进（幂等）；③追加即崩（事件未落账）→ 账本与 frontmatter 一致，本次评分丢失属用户可感知重试面，非账本不一致。
- **A3 严格递增（等时唯一口径：写侧推进，禁止拒绝）**：写侧必须保证同节点新事件 `review_time` **严格大于** `W`（按绝对瞬间比较）——若计算值 ≤ `W`（秒级精度下等时是常见情形），**推进到 `W + 1s` 后再写**，不得以原值写入。
  - ⚠️ **口径统一（round-4 指出的自相矛盾）**：早前移交条款里的"等时**拒绝**"作废。唯一口径是**推进**（`W + 1s`）——拒绝会丢掉一次真实评分，与"事件账是完整审计"冲突。G3-3 的职责是在**并发面强制**该规则（见 A4），而非另立拒绝策略。
- **A4 临界区与并发协议（round-3 BLOCKER + round-4 BLOCKER 收紧）**：**"读 W → 判三态 → 扫描 pending → 重放 → 计算新状态 → durable append 新事件 → apply → 原子发布 frontmatter → 释放"整段必须在 per-node 真互斥内完成**。以下四条是并发正确性的最小充分集，缺一不可：
  - **A4.1 真互斥而非乐观 CAS**：必须是**独占的 per-node 排他锁**（文件锁 / 目录锁），持有期覆盖到**发布之后**。乐观 CAS 不满足——round-4 反例：两写者可在同一秒各自 durable append，胜者发布 `W = t1` 后，败者事件因 `review_time == W`（等时）**永久不进 pending**，该次评分静默丢失。A3 的"推进到 W+1s"只有在锁内读到最新 `W` 才有意义。
  - **A4.2 应用游标与折叠基线**：重放的基线**恒为当前 frontmatter 的 current state**（不是账本起点、不是缓存副本）；游标 = 本次锁内读到的 `W`。若实现选择"从头折叠全账本"，其结果必须与"从 `W` 起增量重放"一致——两者不一致即视为实现缺陷。
  - **A4.3 账本耐久先于发布**：新事件必须**先 durable 落盘（write + flush + fsync 到账本文件）**，再 apply 并发布 frontmatter。顺序颠倒会让"frontmatter 已推进但账本无该事件"——这是审计断链，且下次恢复无法察觉。
  - **A4.4 原子发布**：frontmatter 六字段（`fsrs_bridge.py:44-46` FIELD_ORDER）与 `fsrs_last_review` 必须在**同一次原子替换**中落盘（`os.replace`，现有 bridge 已是该写法），杜绝"部分字段已更新、W 未更新"的半态——半态会被三态判别识别为**残缺卡**并 fail-closed（正确的降级方向）。
  - ⚠️ **移交条款（G3-3，三项必补）**：①per-node **排他锁**（不是 CAS 比较）覆盖 A4 全序列；②冲突写者在锁内**重读 W 并按 A3 推进时刻**后重算（不得在陈旧状态上重试）；③账本 append 的 fsync 耐久。G3-3 卡面当前只写"比较 last_review/revision 后写"，三项均不在其中，实施时须补。本卡只冻结契约，不实现。
- **A5 整秒精度（Codex round-3 BLOCKER：小数秒二次推进）**：`review_time` **必须为整秒**（无小数秒段）。因为 `W` 只有秒级精度，`10:00:00.5 > 10:00:00` 恒成立——同一事件重放会被判 pending 并**二次推进**（实测：首次应用后 Learning/due 10:10，重放同一事件推进为 Review/due +2d）。校验器对 `schema_ext=review/1` 行机械强制整秒。

**三态语义（消解"已应用 vs 迟到乱序"歧义）**：`review_time ≤ W` 的事件**一律不推进 current state**——无论它是"已应用"还是"迟到的乱序事件"，对 current state 的动作**完全相同**，因此该歧义对 exactly-once 无影响。二者的区分只用于**账本标注**：
- **乱序判据统一为 G3-3 卡面口径**（`review_time 早于已应用的最新事件`，即 `review_time ≤ W`，按绝对瞬间比较），标 `out_of_order`；本文档 pending 集合定义已显式**排除已标 out_of_order 的行**，两处口径自洽。
- **`out_of_order` 字段冻结（round-4 HIGH#3）**：位置 = `payload.out_of_order`；类型 = **布尔 `true`**（唯一合法值）；**未标 = 不写该键**（禁止写 `false`、字符串 `"true"`、对象或任何其他形态——它们既非"已标"也非"未标"，会让 pending 排除条件产生歧义）。校验器机械强制该形态。
- **迟到事件的入账通道**：A3 的"严格大于 W"只约束**在线评分**（正常复习写入）。补录/迟到事件走**账本补录通道**：以原始 `review_time` 入账 + 标 `payload.out_of_order = true`，**不进 pending、不推进 current state**——因此与 A3 无冲突。
- **degraded pending 处置（round-4 HIGH#3）**：当节点落入**残缺卡**（三态 fail-closed）时，该节点的 pending 集合**整体冻结**——不重放、不追加新在线事件（新评分应向用户如实报错而非静默丢弃），直到水位线被修复。修复后按 A2 正常重放，pending 中的事件**不因这段冻结期而失效**（它们仍在账本里，`review_time > W` 依旧成立）。禁止"跳过残缺节点继续写新事件"——那会在错误基线上叠加，且让后续恢复无法判别。

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
- **判定规则**（每行）: **严格 JSON** 可解析（RFC 8259——拒 `NaN`/`Infinity` 非标准常量、拒对象内重复键；写侧 `json.dumps(dict)` 不可能产出两者，合法数据零误报）；非法 UTF-8 字节序列 = 该行违规（逐行独立解码，不中断其余行）；**前向兼容分流**：`event_version` 为 int 且 ≠1 的行**只 WARN 并完全跳过 v1 形状校验**（Codex round-1：原"WARN+形状 FAIL 双发"违反前向兼容，已修）；v1 行：顶层键**恰好** 7 键、各字段类型/约束按 §三、`event_type` ∈ 白名单、时间戳按 §三受理语法且 tz-aware；payload 含 `schema_ext: "review/1"` 时强制 §6.1 全部扩展键类型与**语义绑定**（挂载点 / concept_id==node_id / review_time 整秒且与 effective_at 同瞬间 / rating-grade_norm 自洽 / 弃答 rating=1 / 库指纹与 golden manifest 真值相等）；`schema_ext` 值非法或复习事件带扩展键却无 marker = 违规（防降级绕过）。深层嵌套（RecursionError）与超长整数（解析限额）均单行判违规、不中断其余行。**文件级**: `event_id` 全文件唯一（跨版本行也登记——幂等键语义跨版本恒定）。无标记历史行的 payload 键集不做 FAIL 判定（§6.3）。
- **exit code**: `0` = 全部通过；`1` = 存在违规（逐行报告）；`2` = 用法/IO 错误。输出确定性排序，可入 CI。

## 九、已知差异登记（不改代码本体，如实记录）

| 差异 | 位置 | 说明 |
|---|---|---|
| docstring/注释写"8 类"，实际白名单 9 类 | `learning_event_log.py:11`（"限 8 类核心动作"）、:73（"8 类白名单"） | `callout_ingested` 2026-07-23 入集后注释未同步。本卡边界不动该文件；移交 G3-2 顺手修注释（一行，无行为变化） |
| v2 卡"backend 4 写点"计数 | 总账 v2 G3-1 档案节 | 实为 5 调用点，见 §五勘误 |
| **tips 写点把 IO 失败误报为 duplicate 并中止管道**（Codex round-1 HIGH） | `tips.py:572-578` | `append_event` 返回 `False` 折叠两义（§二），tips 消费者按 duplicate 分支返回 `accepted=False`——IO 失败时 callout 被错误拒收且"不阻断主链"不成立。生产路径修复不在本卡；**移交独立 micro-patch**（⚠️ G3-7 卡面只含 `/review/record`、`/fsrs-state`、mastery grade 三条路径，**不含 tips**——不可默认由其顺带收，Codex round-2 指出） |
| **tips 入口可产出 naive `effective_at`**（Codex round-1 HIGH） | `tips.py:510`（`CalloutDirectRequest.added_at` 接受 naive datetime）→ `:570` `isoformat()` 落账 | 违反 §三 tz-aware 契约的**潜在 producer 缺陷**（现网 22 行未命中——实际调用方都传了 tz-aware）。校验器会如实抓出此类行。生产路径修复不在本卡；**移交独立 micro-patch**（与上条同 owner），修法 = schema 层 `AwareDatetime` 或入口归一化 UTC |
