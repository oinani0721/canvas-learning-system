总体裁定：**BLOCKED / FAIL**。当前 92 行的统计数字可复算且 ledger 一致，但生成器不满足强只读和精确快照绑定，不能直接交给 G4-10。

审查结论绑定当前字节：

- script：`87b6f612…0097d`
- report：`1e1ab071…f6d20`
- ledger：`c090ce35…9082`
- raw DLQ：`3b37460f…ba590`
- WT：`card/s5-census @ 37387a86`

## BLOCKER

1. **“只读契约”可被 `--out` 直接突破 — FAIL**

   [脚本:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:163) 接受任意输出路径，[脚本:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:281) 以 `"w"` 无条件截断，未做审查目录 allowlist、`samefile`、symlink 或数据目录隔离。

   静态反例：令 `X` 为 live DLQ，传入 `--dlq X --out X`；脚本先读入 X，随后会用 ledger 覆盖 X。`--out` 同样可指向 `qa_metrics.db` 或其他业务数据文件。报告的“0 写入”及 grep PASS（[报告:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:4)、[报告:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:93)）只能证明一次约定运行没有改业务数据，不能证明代码契约。

   SQLite 连接本身使用 `mode=ro` 且只执行 SELECT，这一子项 PASS；危险来自输出文件路径。

2. **ledger records 与头部源 SHA 不是同一快照 — FAIL**

   records 在[脚本:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:171)首次读取；头部 `dlq_file` 到[脚本:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:268)才重新读取，而 `describe_copy()` 又分别计算行数、SHA、mtime（[脚本:130](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:130)）。

   若 live DLQ 在两次读取间追加或改写，可产出“92 条 records + 93 行文件 SHA”，甚至头部自身的行数、SHA、mtime来自三个状态。G4-10 因而不能确信 stable key 绑定的是头部声明的 exact bytes。

3. **送审对象未冻结且审查期间实际漂移 — FAIL**

   首次观察到 script `591593af…`、report `f3ecf974…`；审查中分别变为当前 `87b6f612…`、`1e1ab071…`。三件 G4-9 交付物均为 untracked，报告所列 commit 不能标识其内容。

   旧证据仍称写入口位于 L291（[grep-selfattest:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-evidence/grep-selfattest.txt:21)），当前已在 L282，证明 evidence/ledger 不再绑定当前脚本。当前报告还在漂移中把错误的 `16/72` 修成了正确的 `22/66`；该旧错误不再算当前 finding，但漂移本身阻断验收。

## HIGH

1. **inline/SHA/anomaly 判定不 fail-closed — FAIL**

   [脚本:72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:72)存在三个可复现反例：

   - body=`"abc"`、声明长度=999、声明 SHA=`sha256("abc")` → 错判 `full_verified/pass`；
   - 200 字符 body、声明长度=201、声明 SHA 为空 → 错判 `truncated_prefix`；
   - 真正 `anomaly` 在[脚本:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:208)仍会被改判为 `approximate` 或 `unrecoverable`，basis 还会谎称“inline 截断”。

   另外，88 条记录的 SHA 只能证明 inline 不等于声明全文，不能证明这 200 字符确实是全文前缀。当前 92 行符合 `EpisodeTask.to_dict()` 生产不变量，所以当前 `4/88/0` 数字 PASS；通用判定逻辑仍 FAIL。

2. **request_id 不是可靠 provenance，缺失或碰撞会跨 session 误归因 — FAIL**

   [脚本:181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:181)用 `str(request_id)` 对整份历史文件分组：

   - 所有 missing/null 与字面 `"None"` 合组；
   - 数字 `123` 与字符串 `"123"` 合组；
   - 多个 token 仅按长度取一个，同长时静默取首项。

   生产字段本身可选（[episode_worker.py:88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/app/services/episode_worker.py:88)）；request ID 还可由客户端头指定，默认是可复用的 `str(id(request))`（[metrics.py:108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/app/middleware/metrics.py:108)）。

   当前数据 0 个缺失、25 组中未见 token 冲突，因此当前样本 PASS；未来增量会 fail-open 误归因。

3. **transcript 多命中/不可见被错误折叠进三态 — FAIL**

   [脚本:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:94)跨所有 project 目录做前缀 glob；一个或多个候选都算存在，不要求唯一、可读普通文件或内容关联。目录不存在、未挂载或无权限时则直接返回空，并在[脚本:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:217)裁为永久性的 `unrecoverable`，而诚实状态应是“未核验/当前源不可见”。

   真实入口只读复现：对当前 92 行传不存在的 transcripts 根，脚本退出 0 并输出 `byte_exact=4 / unrecoverable=88`。这会误导 G4-10 放弃仍可能存在的来源。

## MEDIUM

1. **忽略生产实现支持的 `episode_body_full` — PARTIAL**

   `DeadLetterStore` 可保存 full body（[episode_worker.py:252](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/app/services/episode_worker.py:252)），但脚本完全不读取该字段。含可验证 full body、但无 transcript 的记录仍会被判 `unrecoverable`。当前 92 条该字段确为 0，因此不改变本次数字。

2. **未标识语义重复簇，G4-10 有盲目重放风险 — PARTIAL**

   独立复算 `{name, full_sha, group_id}`：6 个重复组覆盖 29 行，额外 occurrence 23 个；最大组为同一 session archive 16 行，但 `reference_time` 各不相同。ledger 未标识重复簇，也不携带 `reference_time`（[脚本:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/scripts/census_dead_letter_episodes.py:229)）。G4-10 不能仅按 SHA 去重，也不应无策略逐条重放。

3. **私有 transcript 绝对路径进入可交接 artifact — PARTIAL**

   ledger 如[ledger:150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json:150)保存用户名、project slug 和完整 session UUID；报告还要求逐条保留绝对路径（[报告:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:76)）。若提交或外发会泄露本机/session 元数据，应明确限定 private-only。

## LOW

1. **报告两处范围数字不精确 — FAIL（局部文档）**

   - [报告:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:38)写 `16954–20831` tokens；实际为 `16948–20831`，反例 raw line 50。
   - [报告:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:52)写声明长度 `217–8036`；实际为 `205–8036`，反例 raw line 34。

2. **“稳定键三列缺一不可”论证不成立 — PARTIAL**

   当前三元组确为 92/92 唯一，但 `line_no` 单独也是 92/92 唯一，`{sha256_prefix, request_id}` 同样是 92/92 唯一；单独 SHA prefix 为 69 个、request ID 为 25 个。[报告:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:80)的“三列缺一不可”过强。该键只能作为固定文件快照内的 occurrence key，不是跨重排或语义幂等键。

3. **schema 修复引用不完整 — PARTIAL**

   两条 schema 错误分别是 `LearningConcept.name` 和 `LearningTip.created_at`，但[报告:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:39)只展示前者。当前代码确实也已将后者改为 `tip_created_at`（[entity_types.py:254](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend/app/graphiti/entity_types.py:254)），所以“已修复”结论成立，但证据不完整。

4. **挂载当前事实 PASS，历史“从未生效”仅 PARTIAL**

   card/live 两份 compose exact-byte 相同；当前确有 `./backend:/app`，旧子挂载已删除（[docker-compose.yml:202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/docker-compose.yml:202)），与[报告:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md:28)相符。容器证据中的 92 行 SHA 也与 live 文件一致。  
   但 G4-9 自身证据包没有原始 `docker inspect`/`mountinfo`，不足以独立证明历史上“从不出现/一直被遮蔽”。

## 当前数字与边界核验

- raw：92/92 合法 JSON，SHA `3b37460f…ba590`。
- ledger：92 records；逐项字段/class/inline/session/recoverability 与 raw 独立复算 **0 mismatch**。
- class：`89 budget_400 / 2 schema / 1 group_id / 0 unexpected`。
- inline：`4 full_verified / 88 inferred truncated / 0 anomaly`。
- 当前三态：`4 byte_exact / 88 approximate / 0 unrecoverable`。
- 当前报告的 `22 session-archive + 44 qa + 22 distillation` 正确；LLM 非确定性、非逐字节、`approximate ≠ 已恢复` 的声明诚实。
- 7 个当前 transcript 候选均为单一常规文件，大小 90,584–723,950 bytes；仅核验路径/stat，未读取 transcript 内容。
- `qa_metrics.db`：只读复核为 1 张 `qa_error_logs` 表、0 行、无 request_id，查询前后 SHA 不变。
- 空文件：生成 0-record ledger、显式 class deviation，但退出 0，`PARTIAL`。
- 坏 JSON：在打开输出前异常中止，安全性 `PASS`、诊断性 `PARTIAL`。
- 缺 request_id：`FAIL`，见 HIGH-2。
- transcripts 目录不存在：`FAIL`，见 HIGH-3。

本轮审查未修改任何文件；未读取 transcript 内容，也未重新执行 Docker。建议 G4-10 **暂缓接单**，直至固定 exact bytes、修复两个 BLOCKER 代码不变量并重新生成同版 ledger/evidence/report。


