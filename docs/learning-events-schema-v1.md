# 学习事件账 Schema v1 冻结契约（learning_events.jsonl）

> **来源卡**: BATCH-2026-08-28-第五批 / CARD-G3-1
> **真相源**: `backend/app/services/learning_event_log.py`（既有生产实现，EVENT_VERSION=1）。本文档把该实现的现实**逐字段契约化并冻结**——文档描述实现，实现不迁就文档；两者不一致时以代码 + 契约测试为准并修订本文档。
> **姊妹文档**: `docs/fsrs-truth-source-d0-revision.md`（D0 修订：frontmatter=current state，事件账=审计/幂等/重放）
> **裁判**: 契约测试 `backend/tests/regression/test_learning_events_schema_contract.py` + 校验脚本 `backend/scripts/validate_learning_events.py`
> **冻结日期**: 2026-08-28（现网账本 22 行快照全量核验通过）

## 一、冻结声明与版本策略

- 本契约冻结 **EVENT_VERSION = 1**（`learning_event_log.py:31`）的记录结构。这是对既有实现的**加性扩展式冻结，不是 supersede**：既有 9 类事件、既有 7 字段、既有**幂等键语义**（`event_id` 全文件唯一）原样生效。⚠️ 幂等**键语义**不变，但其**判定方式**由本契约冻结为 parsed-field equality（§二 + §6.2 A4.5）——既有子串查重是实现缺陷而非另一种语义，修正它**不触发**下方的 v2 升版条款。
- **加性扩展（无需 bump version）**：payload 内新增键；EVENT_TYPES 白名单经对账评审后新增类型。
- **必须 bump EVENT_VERSION（v2）的变更**：删除/改名任一顶层字段；改变任一顶层字段类型或语义；改变 event_id 幂等语义；payload 从 object 改为其他类型。v2 出现前，读方必须容忍未知 event_version 行（前向兼容：跳过并告警，不炸）。
- 禁止第二套账本与未登记直写（D0 修订 T3 条款）。

## 二、账本文件契约

| 项 | 契约 |
|---|---|
| 位置 | `<vault 根>/learning_events.jsonl`（backend 侧由 `settings.CANVAS_BASE_PATH` 解析，`learning_event_log.py:52-56`；容器内默认 `/vaults/canvas-vault`） |
| 格式 | JSON Lines：每行一个独立 JSON object，UTF-8，`ensure_ascii=False` |
| 追加语义 | append-only；只追加不改写不删除；重放/重建工具只读 |
| 幂等 | **契约语义**：同一 `event_id` 全文件唯一；重放时已存在即跳过。**判定方式（§6.2 A4.5 冻结）= parsed-field equality**（逐行 `json.loads` 后比 `event_id` 字段）。<br>⚠️ **既有实现偏离（登记 §九，随 G3-2 修正）**：`append_event` 现用 `json.dumps(event_id) in line` 的**子串匹配**（`learning_event_log.py:86-88`）——若某 event_id 的 JSON 串形恰好出现在任意行的 payload 文本里，后续同名追加会被误判已存在而**零次落账**（丢一次真实事实）。这不是"更保守"，是**错误的查重实现**；契约以 parsed-field equality 为准 |
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
  - `vault_id`：非空 string——显式冗余 vault 归属，**必须等于账本同目录 `.canvas-config.yaml` 声明的 `vault_id`**（与文件位置隐含归属互证；防事件写错 vault 或账本被搬运后仍自称原 vault）。
    ⚠️ **绑定链路与可用范围（round-10/11 终局：与生产逐环节同源）**：
    - `payload.vault_id` 必须等于账本所在 vault 的**规范化 vault_id**——即生产 `Settings.vault_id` 的取值（`config.py:782-795`），完整链路是 **`yaml.safe_load` → `isinstance(str)` → `sanitize_vault_id()` → `!= "default"` 才采信**。
    - ⚠️ **事件里写的必须是规范化后的形式**：配置写 `"canvas-vault"` 时生产取值是 `canvas_vault`（连字符被 `sanitize_vault_id` 转下划线），事件若写原始连字符形式即判不一致。
    - **校验器复用同一实现**（PyYAML 解析 + import backend 的 `sanitize_vault_id` 本体），不自写副本——r5~r11 实证：手写 YAML 子集与手写 sanitize 副本都会与生产静默分叉（引号键、`0x10`、Unicode 转义键名、`team#1` → `team_1` …）。
    - **降级**：PyYAML 缺失或 backend 不可 import ⇒ **不绑定 + WARN**（少一层防护，安全方向），账本校验主体不受影响。
    - **安全性质（测试锁定）**：校验器绑定值要么等于真实生产入口取值，要么为 `None`——**绝不产生与生产不同的非 None 值**。生产在显式字段无效时会回退到目录名/环境推断，校验器不知运行时环境，对这类输入一律不绑定。
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
- **正常卡** = 持久化 tuple **完整、canonical、落在可调度域内，且 `W` 落在 review 域内**（round-8 HIGH#2：`fsrs_last_review` 是"上一次 review 的时刻"，与 `review_time` 同域，必须**严格小于** A7 的 review 域上界——否则不存在任何合法后继事件（后继须 `> W` 且同样严格小于该上界），`W` 恰为上界时 A3 的 `W+1s` 也立即越界；`fsrs_due` 是调度产物，适用更宽的一般时间戳上界）（round-5 HIGH#2 + round-6 HIGH#1 逐条收紧：bridge `review()` 消费**六字段**构造 `Card`，规则不精确会放过真实调用时抛 `AssertionError`/`ZeroDivisionError`/产生 NaN 的形状）。逐条：
  - `fsrs_last_review`：存在且可解析为 tz-aware 时刻（⇒ `W` = 该值）；
  - `fsrs_due`：存在且可解析为 tz-aware 时刻（**缺它 bridge 走 New 卡分支**，`fsrs_bridge.py:102`）；
  - `fsrs_state`：整数 ∈ {1,2,3}（`0` 属 legacy，走 bridge 的字段级迁移分支，不算"正常卡"）；
  - **按 state 的 canonical 形状**（round-6 四反例逐个封堵）：
    | state | `fsrs_step` | `fsrs_stability` / `fsrs_difficulty` | round-6 反例 |
    |---|---|---|---|
    | 1 Learning | **必须**存在且非负整数 | 要么**同时缺失**（首步未初始化），要么**同时为可调度域内正实数** | `state=1, step=0, S=D=0` 曾判正常 → 真实调用 `ZeroDivisionError` |
    | 2 Review | **必须缺失或 null** | **必须**同时存在且在可调度域内 | `state=2, step=0` 曾判正常 → 成功但持续写回**非 canonical** Review tuple |
    | 3 Relearning | **必须**存在且非负整数 | **必须**同时存在且在可调度域内 | `state=3` + 正常 S/D 但缺 step 曾判正常 → 真实 `review()` 抛 `AssertionError` |
  - **可调度数值域**（round-6 反例：正有限 `S=D=1e308` 曾判正常 → 调度产生 NaN 路径并失败）：
    - `fsrs_stability`：**有限正实数，上界 1e9 天**（≈274 万年）。⚠️ round-7 更正：早前把 `maximum_interval = 36500` 当上界是**错的**——FSRS 封顶的是 **interval** 不是 stability（实测连续 7 次 Easy 后 `S = 68949 > 36500`，会把合法卡误判 degraded）。⚠️ round-8 再收紧：但"任意有限正数"又过宽——`S = 1.797e308` 曾判 normal 而真实 bridge 抛 `OverflowError`。1e9 取的是**语义合理性上界**（方向 fail-closed）：技术可执行边界更高（实测 1e100 仍可执行，1.797e308 才溢出），但真实语义远低于此（Easy 链实测 7 万量级、`maximum_interval` 封顶 36500 天），超过 1e9 天必是数据损坏——故 1e9~1e100 区间**虽技术可执行仍判 degraded**，属有意的保守偏差（停下来要人工确认）而非误判；
    - `fsrs_difficulty` ∈ `[1, 10]`（FSRS 难度定义域，这条正确）；
    - 任一数值不得为 `NaN`/`±Inf`/空串/不可解析。
  - **整数字段用纯整数词法**（round-7）：`fsrs_state`/`fsrs_step` 必须是 int 或匹配 `^[+-]?\d+$` 的字符串。`1.0` 这类写法不受理——真实 bridge 执行 `int("1.0")` 实测抛 `ValueError`（`fsrs_bridge.py:106`）。
  - **重复 frontmatter 键的边界（round-7 如实收窄）**：`classify_card_state(fields: dict)` 接收的是**已解析且无重复键**的 dict——重复键信息在解析层即丢失，本函数无法机械判定。该条由 **frontmatter 解析层**负责（G3-2/G3-3 实现时须用保留重复键信息的解析器或在解析处 fail-closed）；本契约在此显式声明该责任边界，不再宣称由三态判别覆盖。
  - **可执行形式**：以上规则由 `backend/scripts/validate_learning_events.py::classify_card_state()` 机械实现（返回 `("new"|"normal"|"degraded", reason)`），G3-2/G3-3 直接复用同一函数，避免"文档一套、实现一套"。
- **残缺卡 = 上述以外的一切组合**，一律 **fail-closed**（禁止自动重放，报 degraded 待修复）。显式列举（round-4/5 点名的灰区）：
  - 缺 `fsrs_last_review` 但有其他 `fsrs_*`；
  - **只有 `fsrs_last_review` 而缺 `fsrs_due`/`fsrs_state`**；
  - 三键齐全但 **`state=2/3` 缺 stability/difficulty**，或 **`state=1` 缺 step**（round-5 实测：真实 `review()` 抛 AssertionError）；
  - 任一数值字段为 `NaN`/`Inf`/空串/不可解析，或 `fsrs_state` 越界；
  - frontmatter 内该键**重复出现**（解析歧义，不可证）。
- **理由**：`W` 的可信前提是"当前 current state 与该水位线属同一次应用"。任何字段缺失或不可解析都意味着这个前提不可证——此时按 `-∞` 重放会二次推进，按该 `W` 前进又可能建立在错误状态上，唯一诚实处置是停下来。

**比较与排序语义（必须按绝对瞬间，不得按字符串）**：`W` 与 `review_time` 的所有比较（`>`、`≤`、相等）**以及 pending 集合的排序**，**必须先解析为 tz-aware datetime 再比**。理由：bridge 的 `_iso()` 把时刻 `astimezone(UTC)` 后写成 `...Z`（`fsrs_bridge.py:55-56`），而事件的 `review_time` 允许任意合法 offset——实测 `2026-08-01T18:00:00+08:00`（事件）与 `2026-08-01T10:00:00Z`（W）**是同一瞬间但字符串不同**。按字符串比较会把"已应用"判成 pending 并二次推进；**按字符串排序**会把 `10:00:02Z` 排在真实更早的 `18:00:01+08:00` 之前（round-5 反例），导致重放顺序错乱。

**整秒性判定同样按 UTC 归一化后计**：A5 要求的"整秒"在 UTC 归一化后保持（offset 只到分钟级；含秒的 offset 已被 §三 受理语法拒绝）。

**A7 时间上界，分两档（round-6 MEDIUM 提出，round-7 分档）**：
- **review 域上界（`review_time` 与 `fsrs_last_review` 共用，且须严格小于）**：两者必须 **< 9000-01-01T00:00:00Z**（该端点本身**不合法**）。
  - 基础理由：真实调度器会在复习时刻上叠加最长 `maximum_interval = 36500` 天（≈100 年）算出新 `due`，A3 的等时消解还要 `+1s`——`9999-12-31T23:59:59Z` 会让二者都抛 `OverflowError`。
  - **为什么是"严格小于"而非 `≤`（round-9 闭包 + round-10 文档对齐）**：`review_time` 会成为下一个 `W`，而 `W` 必须留出后继空间（后继须 `> W` 且仍在域内）。若端点取 `≤`，则 `review_time = 9000-01-01Z` 是合法输入却会写出一个**没有任何合法后继**的 `W` ⇒ 合法事件确定性制造残缺卡。两侧同界且同为排他，闭包才成立：**合法输入产出的状态必然合法**（实测最后合法秒 `8999-12-31T23:59:59Z` 经真实 bridge 产出 `due=9000-01-01T00:09:59Z`，分类 normal）。
- **一般时间戳上界**：`recorded_at`/`effective_at`/`fsrs_due` 等 ≤ **9500-01-01T00:00:00Z**（只拦 UTC 归一化本身会溢出的极端值）。⚠️ round-7 反例：若把 review 域的保守上界通用到所有字段，合法 review（如最后合法秒 `8999-12-31T23:59:59Z`）经调度产出的 `due`（实测 `9000-01-01T00:09:59Z`）会**反被判 degraded**。注：`review_time = 9000-01-01Z` 这个端点本身按 A7 就**不合法**（见上条排他上界），此处只是说明 due 需要更宽的域。
- 两档留出的余量（≈7000 年）远超任何真实用法，对现网零影响。校验器按字段分别强制。

**A6 调度器入参必须是 UTC（round-5 HIGH#1，端到端条款）**：传给 fsrs `Scheduler.review_card()` 的 `review_datetime` **必须 tz-aware 且 tzinfo 恰为 UTC**——库对此硬校验（`scheduler.py:256-260` 抛 `ValueError: datetime must be timezone-aware and set to UTC`）。因此 G3-2 写路径必须满足：**事件 `payload.review_time`、传入调度器的时刻、写出的 `W` 三者是同一瞬间，且入库/入调度器前统一 `astimezone(UTC)`**。
> ⚠️ **移交（bridge 实现缺陷，本卡不改生产代码）**：`fsrs_bridge.py:50 _aware()` 只补 tzinfo 不做 `astimezone(UTC)`——把校验器判定合法的 `12:00:00+08:00` 传给真实库会**抛 ValueError**（round-5 只读复算实测）；该函数同时把 naive 串静默当 UTC、并在 `_iso()` 截掉小数秒。三项均属 bridge 侧修复，随 **G3-2** 接入时一并处置（登记于 §九）。

**pending 集合**：账本中该节点全部满足以下全部条件的事件：`schema_ext == "review/1"`、**未标 `out_of_order`**、且 `payload.review_time > W`（按绝对瞬间比较）；按 `(review_time, 账本行序)` 升序。

五条硬约束，G3-2 必须同时实现（缺一则 exactly-once 不成立）：

- **A1 write-ahead**：先追加事件再更新 frontmatter。当前现实为 frontmatter 先写、事件后补，差异已在 D0 修订 §四登记。
- **A2 恢复先于新写（消灭交错窗口）**：任何复习写点在**追加新事件之前**，必须先把该节点的 pending 集合按序重放至空。
  - **为什么必要**（round-2 反例）：若允许"E1@t1 落账未应用时 E2@t2 直接从旧状态推进到 t2"，则水位线抬到 t2 后 E1 满足 `t1 ≤ W` 被误判已应用，**E1 对 current state 的贡献永久丢失**。A2 使**单写者下**任意时刻至多只有最后一次追加的事件处于 pending，该交错窗口不会出现。**并发下 A2 本身不够**——见 A4。
  - 崩溃窗口全覆盖：①事件已落账、frontmatter 未推进 → 下次写入前 A2 重放恢复；②两者都完成 → `review_time ≤ W`，不推进（幂等）；③追加即崩（事件未落账）→ 账本与 frontmatter 一致，本次评分丢失属用户可感知重试面，非账本不一致。
- **A3 严格递增（等时唯一口径：写侧推进，禁止拒绝）**：写侧必须保证同节点新事件 `review_time` **严格大于** `W`（按绝对瞬间比较）——若计算值 ≤ `W`（秒级精度下等时是常见情形），**推进到 `W + 1s` 后再写**，不得以原值写入。
  - ⚠️ **口径统一（round-4 指出的自相矛盾）**：早前移交条款里的"等时**拒绝**"作废。唯一口径是**推进**（`W + 1s`）——拒绝会丢掉一次真实评分，与"事件账是完整审计"冲突。G3-3 的职责是在**并发面强制**该规则（见 A4），而非另立拒绝策略。
- **A4 临界区与并发协议（round-3 BLOCKER + round-4 BLOCKER 收紧）**：**"读 W → 判三态 → 扫描 pending → 重放 → 计算新状态 → durable append 新事件 → apply → 原子发布 frontmatter → 释放"整段必须在 per-node 真互斥内完成**。以下四条是并发正确性的最小充分集，缺一不可：
  - **A4.1 真互斥 + 稳定锁身份**：必须是**独占的 per-node 排他锁**，持有期覆盖到**发布之后**。两点缺一不可：
    - **不是乐观 CAS**——round-4 反例：两写者可在同一秒各自 durable append，胜者发布 `W = t1` 后，败者事件因 `review_time == W`（等时）**永久不进 pending**，该次评分静默丢失。CAS 只能检测"值被改过"，无法阻止已发生的 append 副作用。
    - **锁对象必须是不会被 `os.replace` 顶替的实体**（round-5 反例）：若对节点文件本身加锁，`A 锁旧 inode → replace → C 锁新 inode → B 获得旧 inode 锁` 会让 B/C 同时自认排他。冻结为：**per-node sidecar 锁文件或锁目录**（如 `<vault>/.locks/<key>.lock`），`key = 规范化({vault_id, node_id})`（NFC 归一 + 路径安全转义，保证同一节点恒得同一 key）。
    - **接管必须带 fencing，不得只靠超时（round-6 BLOCKER 分项）**：`pid + 时间戳 + 超时接管` **不充分**——反例：A 因 STW/换页暂停超过超时，B 接管并发布，A 恢复后仍会发布基于旧状态的结果（双持 + 状态回退）。冻结为两条同时成立：
      ① **fencing epoch**：锁文件内记单调递增的 `epoch`（每次成功获取 +1）与持有者身份；持有者在**发布前（写 temp 之后、`os.replace` 之前）必须重读锁文件确认 `epoch` 与身份仍是自己**，否则**放弃本次发布**（已 durable 的事件留在账本里，由下一次带锁的 A2 重放消化——这正是 write-ahead 的价值）。
      ② **接管必须是 conditional takeover（CAS），死亡证明须与观察值原子绑定（round-7 BLOCKER 分项）**：
        - 死亡证明本身：`pid` 不存在，或 `pid` 存在但**进程启动时间与锁记录不符**（pid 复用检测）；二者都无法证明时**不得接管**，如实报 degraded 待人工处置；
        - **绑定方式**：接管写入必须是"**当且仅当锁内容仍等于观察到的 `{epoch, owner}` 时，原子替换为 `{epoch+1, self}`**"。⚠️ round-7 反例：B 与 C 同时读到 `{7, A(已死)}` 并各自证明 A 已死，B 接管为 `{8, B}` 后，C 仍凭**陈旧证明**覆盖新 owner ⇒ 双持。CAS 让 C 的写入因观察值已变而失败，须重新观察。
  - **A4.2 唯一折叠基线（round-5：原措辞自相矛盾，此处收敛）**：在线写路径的基线**恒为当前 frontmatter 的 current state**，游标 = 本次锁内读到的 `W`，只做 **pending 增量重放**。"从账本起点全量折叠"**仅作离线对账/审计手段**，禁止出现在在线写路径——两者在"事件账不完整（历史行无 review/1 扩展）"的现实下**并不等价**，把全量折叠当在线基线会重复应用已在 state 里的事件。
  - **A4.3 耐久序列（round-5 补全，参照仓内已有正确模式 `canvas-vault/.claude/scripts/sync_board_concepts.py:583`）**：
    - 账本追加：`write` → `flush` → `fsync(账本 fd)`；**账本文件首次创建时还须 `fsync(父目录 fd)`**（否则崩溃后目录项可能不存在）；
    - 顺序：账本 durable **先于** apply 与 frontmatter 发布。顺序颠倒会造成"frontmatter 已推进但账本无该事件"的审计断链，且下次恢复无法察觉。
  - **A4.4 原子发布（round-5 补全 fsync）**：frontmatter 六字段（`fsrs_bridge.py:44-46` FIELD_ORDER）与 `fsrs_last_review` 必须在**同一次原子替换**中落盘：`写 temp` → `flush` → `fsync(temp fd)` → `os.replace` → **`fsync(父目录 fd)`**。杜绝"部分字段已更新、W 未更新"的半态——半态会被三态判别识别为**残缺卡**并 fail-closed（正确的降级方向）。
  - **A4.5 账本追加的原子性与查重同域（round-5 新增，round-6 三项收紧）**：
    - **查重与追加同锁**：`event_id` 的查重与追加必须在同一把锁内（查重通过后到写入之间不得释放锁），否则两写者可各自查重通过再双写同一 `event_id`。账本是 **per-vault 共享文件**（非 per-node），故该锁粒度为 **per-vault 账本锁**，与 A4.1 的 per-node 锁是两把不同的锁（获取顺序全局固定：**先 node 锁后账本锁**，防死锁）。
    - **查重必须是 parsed-field equality（round-6 BLOCKER 分项）**：逐行 `json.loads` 后比较 `record["event_id"]` 字段是否相等；**禁止子串匹配**。既有 `append_event` 用的是子串查重（`learning_event_log.py:86-88`，§二已如实登记）——当任一历史行的 payload 文本里恰好含有新 `event_id` 的 JSON 串形时，新事件会被**误判 duplicate 而零次落账**（丢一次真实评分）。⚠️ 澄清：这**不是改变幂等语义**（幂等键仍是 `event_id` 唯一，不触发 §一的 v2 升版条款），而是**修正查重实现的正确性**——子串匹配从来就不是"字段相等"的正确实现。既有实现的偏离登记在 §九，随 G3-2 修正。
    - **写入必须验证完整落盘（round-6 BLOCKER 分项）**：`O_APPEND` 对**普通文件**不提供 `PIPE_BUF` 级原子性保证（该保证只对管道成立），普通文件 `write` 仍可能**短写**。因此：单行须一次 `write` 提交，并**检查返回字节数等于期望长度**；短写时按 §二"截断自愈"处理（下次追加前 LF 守卫），并在重启恢复流程中把不可解析的尾行如实报为损坏行（校验器已实现该判定）。
    - **duplicate 命中后的状态推进门（round-6 BLOCKER 分项，round-7 扩等价面）**：查重命中同一 `event_id` 时，按**语义 envelope 的 canonical 形式**分流。envelope = `{event_version, event_type, node_id, effective_at, payload}` 的 `json.dumps(..., sort_keys=True, separators=(",",":"))`——**显式排除 `recorded_at`**（重试时自然变化，不构成事实差异）。
      ⚠️ round-7 反例：只比 `payload` 时，两条同 `event_id`、同 payload、`event_type` 分别为 `answer_scored`/`answer_abandoned` 的记录会被误判 no-op（两者是**相反的事实**：答对 vs 弃答）。
      ⚠️ **适用范围（round-8 MEDIUM）**：envelope 冲突门**只约束 `schema_ext=review/1` 的复习写路径**（G3-2 地盘）。通用 `append_event()` 在调用方省略 `effective_at` 时每次以新 `now` 填充（5 个 backend 调用点中 4 个省略），若全局套用 envelope 门，**合法重试会因 `effective_at` 天然不同而被误判冲突**——非扩展行沿用既有语义：同 `event_id` 即幂等跳过，不做 envelope 比较。
      ⚠️ **已知保守误拒**：canonical 比较基于 JSON 文本，同一瞬间的 `Z` 与 `+00:00` 两种写法会被判为不同 ⇒ 误报冲突。因写点内部时刻表示统一（同一实现产出同一格式），现实中不触发；若未来出现跨写点重试，须在比较前对时间字段做瞬间归一化。
      ① **同 ID 同 canonical envelope** ⇒ 视为重放/恢复，**no-op**（不再落账、**绝不再次 apply**；若 frontmatter 尚未推进则按 A2 走 pending 重放路径恢复）；
      ② **同 ID 不同 canonical envelope** ⇒ **冲突，fail-closed**（拒绝写入并如实报错——同一幂等键承载了两份不同事实，属上游 bug，不得由工具静默选边）；
      ③ 任何情况下 duplicate 都**不得触发第二次 apply**。
  - ⚠️ **移交条款（G3-3，五项必补）**：①per-node **排他 sidecar 锁**（非 CAS、非节点文件本身）覆盖 A4 全序列 + 崩溃回收；②**per-vault 账本锁**内完成 event_id 查重与 `O_APPEND` 单次写；③冲突写者在锁内**重读 W 并按 A3 推进时刻**后重算（不得在陈旧状态上重试）；④账本与 frontmatter 的**完整 fsync 序列**（含父目录）；⑤只做 pending 增量重放，不把全量折叠当在线基线。
    G3-3 卡面（编排 worktree 的总账文件）当前仍只写"比较 last_review/revision 后写"，**五项均不在其中**——卡面更新属编排者动作，本卡无权改他人卡面，故在此与 CURRENT_TASK 双处登记。本卡只冻结契约，不实现。
- **A5 整秒精度（Codex round-3 BLOCKER：小数秒二次推进）**：`review_time` **必须为整秒**（无小数秒段）。因为 `W` 只有秒级精度，`10:00:00.5 > 10:00:00` 恒成立——同一事件重放会被判 pending 并**二次推进**（实测：首次应用后 Learning/due 10:10，重放同一事件推进为 Review/due +2d）。校验器对 `schema_ext=review/1` 行机械强制整秒。

**三态语义（消解"已应用 vs 迟到乱序"歧义）**：`review_time ≤ W` 的事件**一律不推进 current state**——无论它是"已应用"还是"迟到的乱序事件"，对 current state 的动作**完全相同**，因此该歧义对 exactly-once 无影响。二者的区分只用于**账本标注**：
- **乱序判据统一为 G3-3 卡面口径**（`review_time 早于已应用的最新事件`，即 `review_time ≤ W`，按绝对瞬间比较），标 `out_of_order`；本文档 pending 集合定义已显式**排除已标 out_of_order 的行**，两处口径自洽。
- **`out_of_order` 字段冻结（round-4 HIGH#3，round-17 补语义门）**：位置 = `payload.out_of_order`；类型 = **布尔 `true`**（唯一合法值）；**未标 = 不写该键**（禁止写 `false`、字符串 `"true"`、对象或任何其他形态——它们既非"已标"也非"未标"，会让 pending 排除条件产生歧义）。校验器机械强制该形态。
  ⚠️ **形态合法 ≠ 语义为真（round-17 Codex HIGH）**：proof 的 scanner 排除标了 `out_of_order` 的行，于是"标记本身"成了把事件移出适用集的手段。若某行标了该键、其 `review_time` 却**晚于此前所有适用事件**，它就是**被伪装成乱序的真实后继**——排除它即绕过尾部覆盖门。故 proof 侧额外强制：标记行的 `review_time` 必须**不晚于**此前适用事件的最大时刻（即符合本条乱序定义 `review_time ≤ W`）；不符者**报违规且仍计入适用集**。
- **迟到事件的入账通道**：A3 的"严格大于 W"只约束**在线评分**（正常复习写入）。补录/迟到事件走**账本补录通道**：以原始 `review_time` 入账 + 标 `payload.out_of_order = true`，**不进 pending、不推进 current state**——因此与 A3 无冲突。
- **degraded pending 处置（round-4 HIGH#3 + round-5 HIGH#3 解冻边界）**：当节点落入**残缺卡**（三态 fail-closed）时，该节点的 pending 集合**整体冻结**——不重放、不追加新在线事件（新评分应向用户如实报错而非静默丢弃）。禁止"跳过残缺节点继续写新事件"——那会在错误基线上叠加。
  - **解冻的唯一合法条件（round-5 提出，round-6 机械化）**：修复必须**把六字段与 `W` 原子重建到同一个可证明的账本边界**上——选定账本中某个事件 `E`，从**可证明起点**折叠到 `E` 为止，把结果的六字段与 `W = E.review_time` 在**同一次原子替换**中写入。三项必须机械确定：
    - **`E` 的选取与层级作用域（round-11 修正尾部逃逸，round-13 冻结作用域）**：
      - **最外层（top-level）proof**：`E` 必须是该节点在账本中**行号最大的适用事件**（`schema_ext=review/1`、未标 `out_of_order`），且 **`cursor_line` 之后不得再存在该节点的任何适用事件**——保证重建覆盖到账本末尾。
      - **`ancestor_proof`（中间层）：不受"其后无适用事件"约束**。⚠️ round-13 指出的歧义：若把该尾部约束**递归**施于 ancestor，则正常链 `L1=t1、L2=t2` 中的 ancestor（`cursor_line=1`）会因 L2 存在而失效，任何多层链都无法成立；只施于最外层则是原意。现明确冻结为**仅最外层**——ancestor 的职责是提供一个**中间快照**，本就不必覆盖到末尾，它只需满足：区间定义、层内单调、跨层单调、三条等式、链终止与防循环。
      - 两个 verifier 因此不会给出相反结果。
      - 📌 **可执行的单一事实（round-14，round-15 补真实绑定）**：以上分层语义已落成参考实现 `backend/scripts/validate_learning_events.py::verify_degraded_proof(proof, applicable, *, ledger_path=None)`——作用域由**内部**递归参数 `is_top_level` 承载（递归固定传 `False`），round-15 起**已移出公开签名**（公开可写等于给调用方一个关掉尾部门的开关）。行为门见 `test_learning_events_schema_contract.py::test_normal_two_layer_chain_is_provable`（正常两层链必须 PASS）与 `::test_layered_split_cannot_bypass_monotonicity`（分层绕过必须 FAIL）。
        **传 `ledger_path` = 账本直读模式**：verifier 用 `scan_ledger_bytes()` 在**单一字节快照**上抽取适用事件、该节点全部事件行、无扩展历史行、degraded 哨兵行与 vault_id 集合，并用 `ledger_prefix()` 复算 `ledger_prefix_sha256` 与 `prefix_ends_without_lf`，忽略调用方传入的 `applicable`。**生产接入必须传 `ledger_path`**——否则 `applicable` 是信任边界，调用方抽取不全会让最外层尾部门真空通过（round-14 Codex HIGH 实证）。
        ⚠️ **verifier 不做的六件事**（round-17 落定；与 `validate_learning_events.py` 的模块头注释、`verify_degraded_proof` docstring **逐字同文**）：
        ① 不复算 FSRS 折叠 —— canonical reducer 的精度常量属 G3-2, 需真实 fsrs;
        ② 不复算 `result_hash` —— 它是折叠产物的 hash, 同样依赖 reducer;
        ③ 不传 `ledger_path` 时不复算 `ledger_prefix_sha256`、不自行抽取事件 —— 此时 `applicable` 是信任边界, 其完整性由调用方保证 (抽取不全会让尾部门真空通过); 传 `ledger_path` 后 verifier 自行抽取并复算, 但这不等于消除全部信任 (见 ⑤);
        ④ 不把 genesis 原文与真实节点文件的字节比对 —— 只验其与自报 hash 自洽、且顶层无 `fsrs_*` 键; 节点文件路径不在 proof 内, 该绑定须由调用方另行完成;
        ⑤ 不做完整记录级 schema 校验 —— scanner 只校验 proof 依赖的字段 (node_id / schema_ext / out_of_order / review_time / event_id / 算法身份 / vault_id); proof 校验以「该账本已通过主体校验」为前置条件;
        ⑥ 传 `ledger_path` 时读的是调用瞬间的快照 —— 之后的并发追加不在判定内 (调用方须在持有账本锁时校验)。
        📌 **proof 侧的强依赖（与账本主体校验不同口径）**：账本校验主体是 stdlib-only，但 **proof 侧强制要求 PyYAML**（genesis 顶层键判定）**与同仓 G3-4 golden manifest**（算法身份同源，且其 `scheduler_config` 须完整含六键）。任一不可达或残缺 ⇒ **fail-closed 报违规**，不降级放行——降级会让"合法形状版本 + 任意 hash + 残缺配置"直接通过（round-16/17 实证）。
        📌 **`scheduler_config` 的类型冻结**：proof 的该字段必须与 manifest 的 **canonical JSON 文本逐字相同**（`json.dumps(sort_keys=True, separators=(",",":"))`）。这一并冻结了各键的 JSON 类型——`enable_fuzzing` 是 `false` 不是 `0`、`learning_steps_minutes` 是整数数组不是布尔数组、`maximum_interval` 是 `36500` 不是 `36500.0`。Python 的 `==` 对前两组判等（`0 == False`、`True == 1`），故**不得用 `==` 比较**。
        返回空违规 = "已判门内无歧义，可交付 reducer 复算"，**不等于** proof 成立。
      ⚠️ round-11 反例：若按 `(review_time, 行号)` 复合序取最大，当 `L1=t2`、`L2=t1`（两行都未标乱序）时 E=L1，区间只含 L1，单调门真空通过，**L2 完全逃逸未被覆盖**。改用行号口径后，E=L2，L1 与 L2 同在区间内，单调门会因 `t2 > t1` 而判该区间不自洽 ⇒ 正确地报"不可证明"。
    - **canonical reducer（round-6 实测的舍入歧义）**：折叠必须**逐事件按生产持久化精度舍入后再进下一步**（与 bridge 的写-读循环一致），**不得**在内存中连续折叠、只在末尾舍入。实测差异：三次 Good 后 `stability` = **10.9711**（逐步舍入）vs **10.9710**（末尾舍入）——两者都满足"折叠到 E"的粗描述，故边界必须唯一化。舍入精度以 bridge 写出 frontmatter 时的实际精度为准（G3-2 落地时把该常量与本条一并锁进测试）。
    - **proof schema（round-8 HIGH#4 机械化——此前只是清单，两个不同起点可满足同一清单却折出不同结果）**。proof 是一个 JSON object，字段与语义如下，缺任一项或任一项不满足约束即**不可证明**：

      | 字段 | 内容与约束 |
      |---|---|
      | `vault_id` / `node_id` | 本次重建的目标节点身份 |
      | `ledger_prefix_sha256` | 账本文件**从第 0 字节起、到 E 所在行的终止 LF（含该 LF）为止**的字节序列的 sha256。若 E 是文件最后一行且无终止 LF，则到文件末字节为止，并置 `prefix_ends_without_lf: true` |
      | `cursor_line` | E 的 1-based 行号（与 `ledger_prefix_sha256` 的截断点必须一致） |
      | `event_id` / `review_time` | E 的幂等键与业务时刻（`review_time` 即重建后写入的 `W`） |
      | `fsrs_library_version` / `fsrs_params_hash` / `scheduler_config` | 复算所用的算法身份与完整配置（须与 G3-4 golden manifest 同源；`degraded:*` 哨兵不合格） |
      | `reducer` | canonical reducer 标识与其精度常量（见上一条；G3-2 落地时冻结具体值） |
      | `origin` | 起点，二选一：`{"kind": "new_card", "genesis_evidence": {...}}`（真新卡，链终止于此；折叠区间左端点 = `genesis_evidence.first_event_line - 1`，见下方 genesis 锚——round-11 修正原「取 0」与后文冲突）或 `{"kind": "snapshot", "state": {...}, "snapshot_hash": "...", "ancestor_proof": {...}}`（三条等式约束见下） |
      | `result_hash` | 重建出的**状态对象**（键集按下方"状态对象的唯一形状"——Learning/Relearning 六键、**Review 五键**）的 canonical JSON 的 UTF-8 字节 sha256——供他人独立复算比对 |

    - **状态对象的唯一形状（round-9 HIGH#3，round-10 补值类型）**：proof 里出现的每个"状态"（`origin.snapshot.state`、`result` 等）都是**恰含 `fsrs_bridge.py:44-46` FIELD_ORDER 中「适用于该 `fsrs_state` 的键」的 JSON object**：

      | `fsrs_state` | 键集 |
      |---|---|
      | 1 Learning / 3 Relearning | 六键：`fsrs_due` / `fsrs_state` / `fsrs_step` / `fsrs_stability` / `fsrs_difficulty` / `fsrs_last_review` |
      | 2 Review | **五键**：同上但**省略 `fsrs_step`**（与 §三态表的 canonical 形状一致——Review 态带 step 即非 canonical） |

      （r11/r12 修正：早前几处混写"固定六键"，与 Review 省略 step 冲突；现全文以本表为准。）
      **值类型必须归一化后再序列化（round-10 HIGH）**——否则 `{"fsrs_state": 2, "fsrs_stability": 10}` 与 `{"fsrs_state": "2", "fsrs_stability": 10.0}` 都能通过三态判别却产生**不同 hash**，proof 失去唯一性：

      | 键 | canonical 类型 |
      |---|---|
      | `fsrs_due` / `fsrs_last_review` | JSON string，**UTC 整秒 `Z` 形式**（`%Y-%m-%dT%H:%M:%SZ`，与 `fsrs_bridge._iso()` 写出格式一致） |
      | `fsrs_state` | JSON number（整数），取值 1/2/3——不得为字符串 |
      | `fsrs_step` | JSON number（非负整数）**或该键省略**（Review 态省略，见三态表）——不得为 `null`、不得为字符串 |
      | `fsrs_stability` / `fsrs_difficulty` | JSON number（**float**，即使整数值也序列化为 `10.0` 而非 `10`）——不得为字符串 |
      ⚠️ **不再单列 `W`**——`W` 就是该对象里的 `fsrs_last_review`（round-9 指出："six_fields + W"的写法会让同一信息有两处表示，可不一致）。凡文中说"六字段与 `W`"，均指该单一对象。
      `result_hash` / `snapshot_hash` = 该对象的 `json.dumps(..., sort_keys=True, ensure_ascii=False, separators=(",",":"))` 的 **UTF-8 字节** 的 sha256（编码与分隔符一并冻结）。
    - **`origin.kind == "snapshot"` 的绑定（round-8 提出，round-9 加等式约束）**：必须含 `{state, snapshot_hash, ancestor_proof}`，且**以下三条等式全部成立**，否则不可证明：
      1. `snapshot_hash == sha256(canonical(state))`（自洽）；
      2. `snapshot_hash == ancestor_proof.result_hash`（该快照必须**正是**祖先 proof 的产出，而非另一份同形对象）；
      3. `state.fsrs_last_review == ancestor_proof.review_time`（祖先折叠到的事件时刻，即为该快照的水位线）。
    - **折叠区间与折叠顺序（round-9 HIGH#3，round-10 补顺序与单调性）**：
      - **区间**：账本中该节点、`schema_ext=review/1`、未标 `out_of_order`、且**行号**落在 `(ancestor_proof.cursor_line, cursor_line]` 内的全部事件——**左开右闭、按行号界定**（不用时刻界定，因同瞬间不同行会有两种解释）。`origin.kind == "new_card"` 时左端点 = `genesis_evidence.first_event_line - 1`。
      - **顺序**：按**行号升序**折叠（账本的物理追加序即因果序——A2 保证写入时状态已是最新）。
      - **单调性硬门（round-10）**：区间内的 `review_time` 必须**随行号严格递增**。若出现"行号递增而 `review_time` 不增"的行，说明该行是迟到/乱序事件却**未标 `out_of_order`** ⇒ 账本自身不自洽，**proof 不可证明**（须先由人工裁定该行的归属，而非由工具选一种顺序）。这消除了"按行号折"与"按时刻折"两种解释的分歧——两者在通过该门的区间上必然一致。
    - **`origin.kind == "new_card"` 的 genesis 锚（round-10 HIGH）**：`new_card` 不能只是自报——同一份账本在"此前是真新卡"与"此前已有未入账的 Review 状态"两个世界里会折出不同结果（Learning vs Review），proof 必须能区分。因此该分支**必须附** `genesis_evidence`：
      - `node_frontmatter_hash`：重建时刻该节点 frontmatter 的 sha256。**字节域冻结**：从文件首个 `---` 行的**下一字节**起，到闭合 `---` 行的**前一字节**为止（不含两条 `---` 行本身及其换行），按 UTF-8 原始字节计算；此刻该 frontmatter **不含任何 `fsrs_` 前缀字段**（三态判别为 `new`）。为便于复验，proof 须同时携带该 frontmatter 的**原文**（`node_frontmatter_text`）；
      - `first_event_line`：该节点在账本中最早一条事件的行号，且 `first_event_line > 0`；折叠区间左端点即取 `first_event_line - 1`（而非笼统的 0），使区间起点也可核验；
      - 三者缺一 ⇒ 不可证明，必须改走 `snapshot` 分支或人工裁定。
      - ⚠️ **证明强度的诚实上限（round-11）**：`genesis_evidence` 证明的是"**重建时刻**该节点无任何 FSRS 状态"，**不能**证明"历史上从未存在过未入账的 Review 状态"（例如状态曾被手工删除）。因此 `new_card` 分支只在该节点**账本历史完整**（其全部复习事件都带 `review/1`）时可用；若存在无扩展的旧行，则该节点属 §"不可证明时必须继续冻结"，须人工裁定——工具不得自行采信 `new_card`。
    - **链的终止与防循环（round-8，round-15 补深度上限）**：`ancestor_proof` 链必须**终止于 `origin.kind == "new_card"`**；链上每一层的 `(vault_id, node_id)` 必须相同，且 `cursor_line` 必须**严格递减**（保证有限步终止、不可自引用）。任一条不满足 ⇒ 不可证明。
      **深度上限 = 128 层**（`validate_learning_events.py::PROOF_MAX_DEPTH`）。⚠️ round-14 Codex LOW：此前实现私设 64 层却未成文，会**误拒合法的长链**。现明确：该上限是针对畸形/自引用输入的防御性保险，不是语义约束——严格递减本已保证有限步；单节点的解冻链层数等于历史上的重建次数，128 已极为宽裕。超限时报违规而非静默截断。
      ⚠️ **round-15 自查（上限取值有硬约束）**：该值**必须远低于实现语言的递归上限**。一度改取 1024 > Python 默认的 `sys.getrecursionlimit()`（1000），结果深度约 985 起的链在递归中抛**未捕获的 RecursionError**——工具崩溃而非报违规，比原来的"误拒长链"更坏。校验器另在公开入口捕获 `RecursionError` 转为违规作纵深防御（调用方栈深不可知）。
    - **跨层单调门（round-12 HIGH：分层可绕过层内单调性）**：`ancestor_proof.review_time`（即 ancestor 折叠到的时刻，也是 snapshot 的 `W`）必须 **严格小于本层折叠区间中首个事件的 `review_time`**。
      ⚠️ round-12 反例：`L1=t2、L2=t1`（`t2 > t1`，两行均未标 `out_of_order`）时，可拆成 ancestor 区间 `(0,1]` 与本层区间 `(1,2]`——两个**单事件区间**的层内单调门都**真空通过**，全链非单调却蒙混过关。加上本条后：ancestor 的 `W = t2` 不小于本层首事件的 `t1` ⇒ 正确判**不可证明**。
      该条不会误伤正常链：真实追加序下时刻本就随行号递增，跨层边界自然满足严格小于。
    - **`prefix_ends_without_lf` 的取值规则（round-9）**：类型为 boolean。E 所在行**有**终止 LF 时该键**必须省略**（不得写 `false`）；**无**终止 LF（E 是文件末行且文件不以 LF 结尾）时**必须**写 `true`。这样"省略"与"false"不并存，比较无歧义。
    - **`degraded:*` 哨兵行不参与自动证明链**：其 `fsrs_library_version`/`params_hash` 是哨兵而非算法身份，无法确定性复算——含此类事件的区间必须由人工裁定。
  - **为什么必须如此**（round-5 两反例）：若 state 已含 `E2` 而水位线被随手修成 `W = t1` ⇒ `E2` 会被二次应用；若 state 仅含 `E1` 而 `W` 被修成 `t2` ⇒ `E2` 永久遗漏。两种错误都源于"state 与 W 不同源"。
  - **不可证明时必须继续冻结**：当账本缺少覆盖该节点的完整 review/1 事件序列（例如该节点的历史全是无扩展的旧行），**无法**重建可证明同源的 state+W ⇒ 该节点保持冻结并向用户如实报告，由人工裁定（例如接受"以当前 frontmatter 为准、把 `W` 设为账本中该节点最大 `review_time`"这一有损但显式的决策）。**禁止工具自动做该有损决策**。
  - 冻结期间账本中的 pending 事件**不因冻结而失效**（它们仍在账本里，解冻后按上述边界一并计入）。

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

- **定位**: 确定性校验器。**账本校验主体 stdlib-only**，可独立对任意 vault 的 jsonl 执行；**vault_id 绑定层**需 PyYAML + 可 import 的 backend `app.config`（必须与生产 `Settings.vault_id` 逐环节同源，见 §6.1），不可达时降级为不绑定 + WARN，主体不受影响。白名单在脚本内复制一份，由契约测试与 `learning_event_log.EVENT_TYPES` 锁死同步（漂移即红）。
- **用法**: `python3 backend/scripts/validate_learning_events.py <learning_events.jsonl 路径>`
- **判定规则**（每行）: **严格 JSON** 可解析（RFC 8259——拒 `NaN`/`Infinity` 非标准常量、拒对象内重复键；写侧 `json.dumps(dict)` 不可能产出两者，合法数据零误报）；非法 UTF-8 字节序列 = 该行违规（逐行独立解码，不中断其余行）；**前向兼容分流**：`event_version` 为 int 且 ≠1 的行**只 WARN 并完全跳过 v1 形状校验**（Codex round-1：原"WARN+形状 FAIL 双发"违反前向兼容，已修）；v1 行：顶层键**恰好** 7 键、各字段类型/约束按 §三、`event_type` ∈ 白名单、时间戳按 §三受理语法且 tz-aware；payload 含 `schema_ext: "review/1"` 时强制 §6.1 全部扩展键类型与**语义绑定**（挂载点 / concept_id==node_id / review_time 整秒且与 effective_at 同瞬间 / rating-grade_norm 自洽 / 弃答 rating=1 / 库指纹与 golden manifest 真值相等）；`schema_ext` 值非法或复习事件带扩展键却无 marker = 违规（防降级绕过）。深层嵌套（RecursionError）与超长整数（解析限额）均单行判违规、不中断其余行。**文件级**: `event_id` 全文件唯一（跨版本行也登记——幂等键语义跨版本恒定）。无标记历史行的 payload 键集不做 FAIL 判定（§6.3）。
- **exit code**: `0` = 全部通过；`1` = 存在违规（逐行报告）；`2` = 用法/IO 错误。输出确定性排序，可入 CI。

## 九、已知差异登记（不改代码本体，如实记录）

| 差异 | 位置 | 说明 |
|---|---|---|
| **查重用子串匹配而非字段等值**（Codex round-6/7 BLOCKER 分项） | `learning_event_log.py:86-88`（`json.dumps(event_id) in line`） | 若某 `event_id` 的 JSON 串形恰好出现在任意历史行的 payload 文本里，新事件会被误判 duplicate 而**零次落账**（丢一次真实事实）。契约（§二 + §6.2 A4.5）已冻结为 **parsed-field equality**；这是**修正错误实现**而非改幂等语义，不触发 §一的 v2 升版条款。**移交 G3-2**（其新写点必须用 parsed 查重；既有 `append_event` 本体的修正随之进行） |
| **bridge 时间口径三项**（Codex round-5 HIGH#1） | `fsrs_bridge.py:50 _aware()` / `:55 _iso()` | ①`_aware()` 只补 tzinfo 不做 `astimezone(UTC)`——把校验器判定合法的 `12:00:00+08:00` 传给真实库会抛 `ValueError: datetime must be timezone-aware and set to UTC`（round-5 只读复算实测）；②naive 串被静默当 UTC；③`_iso()` 截掉小数秒。契约 A6 已冻结"三者同一瞬间且统一 UTC"；**移交 G3-2**（接入复习写路径时一并修） |
| docstring/注释写"8 类"，实际白名单 9 类 | `learning_event_log.py:11`（"限 8 类核心动作"）、:73（"8 类白名单"） | `callout_ingested` 2026-07-23 入集后注释未同步。本卡边界不动该文件；移交 G3-2 顺手修注释（一行，无行为变化） |
| **Review 态 `fsrs_step: null` 的文本解析偏差**（Codex round-8） | `fsrs_bridge.py:117`（`int(step) if step not in (None, "") else None`） | 契约允许 Review 卡不带 `fsrs_step`（或写 null）。但 bridge 从 frontmatter **文本**解析时，YAML 的 `null` 会成为字符串 `"null"`，不落在 `(None, "")` 判空集合里 ⇒ `int("null")` 抛错。**移交 G3-2/G3-3**：写侧应**省略该键**而非写 null，或读侧把 `"null"`/`"~"` 一并归空 |
| **canonical reducer 的精度常量与序列化 bytes 未冻结**（Codex round-7 HIGH 部分） | §6.2 degraded 解冻条款 | 本卡已冻结**方向**（逐事件持久化舍入，禁末尾舍入；实测差异 10.9711 vs 10.9710 在案），但"精度常量、`round` tie 语义、序列化规则、bridge blob hash"依赖 G3-2 落地时的真实写出实现——**移交 G3-2**：实现落地时把这些常量与 blob hash 一并锁进测试，届时本条方可闭合 |
| v2 卡"backend 4 写点"计数 | 总账 v2 G3-1 档案节 | 实为 5 调用点，见 §五勘误 |
| **tips 写点把 IO 失败误报为 duplicate 并中止管道**（Codex round-1 HIGH） | `tips.py:572-578` | `append_event` 返回 `False` 折叠两义（§二），tips 消费者按 duplicate 分支返回 `accepted=False`——IO 失败时 callout 被错误拒收且"不阻断主链"不成立。生产路径修复不在本卡；**移交独立 micro-patch**（⚠️ G3-7 卡面只含 `/review/record`、`/fsrs-state`、mastery grade 三条路径，**不含 tips**——不可默认由其顺带收，Codex round-2 指出） |
| **tips 入口可产出 naive `effective_at`**（Codex round-1 HIGH） | `tips.py:510`（`CalloutDirectRequest.added_at` 接受 naive datetime）→ `:570` `isoformat()` 落账 | 违反 §三 tz-aware 契约的**潜在 producer 缺陷**（现网 22 行未命中——实际调用方都传了 tz-aware）。校验器会如实抓出此类行。生产路径修复不在本卡；**移交独立 micro-patch**（与上条同 owner），修法 = schema 层 `AwareDatetime` 或入口归一化 UTC |
