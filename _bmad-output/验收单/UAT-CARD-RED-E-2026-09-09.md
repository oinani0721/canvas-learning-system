# UAT — CARD-RED-E（agent 模板恢复 6 + 新作 hint-generation + 假绿修 + 两表对齐 + 防删门）

> 批次：`BATCH-2026-09-07-第十三批 / CARD-RED-E`
> 车道：`card-u10-red-a`（分支 `card/u10-red-a`）
> 开工 HEAD：`0465a35c`（U10-A `CARD-HYGIENE-conftest` 末 commit）
> 日期：2026-09-09
> 裁判存档目录：`_bmad-output/审查/evidence-red-e/`

---

## 〇 本卡做了什么

一句话：把「AI 分级提示」这个功能从 **7 个月的静默降级** 里捞出来，并加上让它不会再无声消失的门。

- `.claude/agents/` 目录里只剩 **11** 份模板，而 smoke 测试期望 **18** 份。
- 缺的 7 份分两类：
  - **6 份被删**（commit `f425d7b7`，2026-03-30，message `ralph-loop: iteration 0`）→ 本卡从 `f425d7b7^` 逐份**逐字节**恢复；
  - **1 份 `hint-generation.md` 全史从未存在** → 本卡**新作**，标「真生产缺陷修复」。
- 生产影响链（实测在位）：`verification_service.py:3032` 调 `call_agent(AgentType.HINT_GENERATION, …)` → 模板不存在 → `gemini_client.py:227-228` 抛 `FileNotFoundError` → `agent_service.py:2816-2833` 转成 `AgentResult(success=False)` → `verification_service.py:3035` 条件为假 → **`:3060-3067` 落到写死兜底提示**。调用点自 `14f0412d`（2026-02-07）上线，**从未真正跑通过一次**，且不抛错、只留一行 `logger.warning`。

---

## 一 改动面（地盘门）

| 文件 | 改动 |
|---|---|
| `.claude/agents/canvas-orchestrator.md` | 新增（恢复，104719 B） |
| `.claude/agents/graphiti-memory-agent.md` | 新增（恢复，5584 B） |
| `.claude/agents/iteration-validator.md` | 新增（恢复，13690 B） |
| `.claude/agents/parallel-dev-orchestrator.md` | 新增（恢复，13392 B） |
| `.claude/agents/planning-orchestrator.md` | 新增（恢复，16492 B） |
| `.claude/agents/review-board-agent-selector.md` | 新增（恢复，7579 B） |
| `.claude/agents/hint-generation.md` | **新增（新作，5199 B）** |
| `backend/app/services/agent_service.py` | **仅 +1 行**：`:5724` 加 `"hint-generation",`（health 期望表 12 → 13） |
| `backend/tests/unit/test_agent_templates_smoke.py` | 假绿修 + 阈值 17→18 + 3 条新断言 + 2 处不实注释更正 |

地盘门存档：`evidence-red-e/scope-gate-20260909T120000.txt`
禁改清单（两个 conftest / `tests/support` / `lefthook.yml` / `.claude/hooks` / `.claude/settings*.json` / 根 `.gitignore` / `api/v1/system.py` / `agent_metrics.py` / `agent_memory_mapping.py` / `verification_service.py` / `gemini_client.py` / `test_agents_health.py`）逐一核查 **全空**。
`EXPECTED_AGENT_TEMPLATES` 18 项名单本身**未被改动**（`ast` 提取实测 `count=18`，diff 中无任何 `"*.md",` 行增删）。

---

## 二 「对齐」的定义（本卡裁定，已写成可执行断言）

两张表管的是不同的事，**本来就不该相等**：

| 表 | 位置 | 项数 | 管什么 |
|---|---|---|---|
| smoke 表 | `test_agent_templates_smoke.py::EXPECTED_AGENT_TEMPLATES` | 18 | 目录里必须有这些文件（防批量删除） |
| health 表 | `agent_service.py:5711-5725::expected_templates` | 13（本卡 12→13） | `/agents/health` 报不报 degraded，只盯 `AgentType` 里真会被 `call_agent` 加载的 |

差集恰 **5 份**：`graphiti-memory-agent` / `iteration-validator` / `parallel-dev-orchestrator` / `planning-orchestrator` / `review-board-agent-selector`。
原因：这 5 份**不是 `AgentType` 成员**，生产从不加载，但仍须留在目录里作删除告警面。

⛔ 明确没做的事：**没有**用「把期望表删到 11 项」这类改法求绿——那会把 `hint-generation` 这个真缺陷一起抹掉。

本卡把这条关系写成两条测试，让「两表为什么不等」成为可执行事实而不是注释：

- `test_health_expected_templates_equals_loadable_agent_types` —— 用 `ast` 从 `agent_service.__file__`（真正被 import 的那个文件，不是路径推算）取出 `expected_templates` 字面量，与 `AgentType` 去掉两个别名（`four-level` / `scoring`）后的值集比较。
- `test_smoke_table_minus_health_table_is_the_tripwire_only_set` —— 断言 `smoke − health` 恰是那 5 项，且 `health − smoke` 为空（health 盯的每一项都必须被 smoke 守住）。

---

## 三 DoD-3 · 4-A「Claude 已代验」（技术断言）

### 3.1 恢复逐字节对账（裁判 3）

存档：`evidence-red-e/restore-sha-20260909T000001.txt`

6 份逐份 `git show f425d7b7^:<path> | shasum -a 256` 与落盘 `shasum -a 256` **两列逐字节相同**，`wc -c` 与勘探六个字节数一一对上，`MISMATCH` 计数 = **0**。

| 模板 | 字节数 | sha256（前 16） |
|---|---|---|
| canvas-orchestrator | 104719 | `82080fd976499b84` |
| graphiti-memory-agent | 5584 | `814c82899bb81b11` |
| iteration-validator | 13690 | `f37033fb54e5a89c` |
| parallel-dev-orchestrator | 13392 | `76a67f32af0bbdaa` |
| planning-orchestrator | 16492 | `2306af6159221651` |
| review-board-agent-selector | 7579 | `744ce6f57b156f1f` |

内容**一字未改**，含 3 份无 YAML frontmatter 的（`iteration-validator` / `parallel-dev-orchestrator` / `planning-orchestrator`，首行是 `# <Title>`）——它们不在 `AgentType`、生产不加载，故意保持原样。

### 3.2 `hint-generation.md` 全史从未存在（新作依据）

开工原样复跑四条，全部空 / 全 0：

- `git log --all --diff-filter=A --oneline -- '.claude/agents/hint-generation.md'` → 空
- `git log --all --diff-filter=A --oneline -- '*hint-generation.md'` → 空
- `git log --all -S'hint-generation' --oneline -- .claude/agents/` → 空
- `git ls-tree --name-only <c> .claude/agents/ | grep -c hint` 在 `eb86275a` / `abf1d585^` / `f425d7b7^` / `HEAD` 四棵树 → **全 0**

⇒ 只能新作，不能「恢复」。（`f425d7b7^` 树恰 17 份 = 期望 18 − hint-generation，与勘探一致。）

### 3.3 模板真解析（裁判 5）

存档：`evidence-red-e/template-parse-20260909T000001.txt`，末行 `rc=0`

走**生产路径本体**：`GeminiClient()` 默认构造（`prompt_path` 取 `settings.AGENT_PROMPT_PATH`，实测解析到本树 `.claude/agents`）→ `load_prompt_template("hint-generation")` → `_parse_prompt_template`。**未自写任何正则复刻**，**未发出任何网络请求**。

- `name = hint-generation` ✅（`grep -c` = 1）
- `output_format` 非空，且 `json.loads` 通过，keys = `['hint_level', 'hint_text', 'reasoning']`
- `hint_text present: True` ✅（`grep -c` = 1）
- `hint_level present: True` ✅（`grep -c` = 1）
- `input_format` 非空，9 键 = `attempt_number / common_mistakes / concept / learning_history / question_text / related_concepts_graph / score_history / score_trend / user_answer`，与 `verification_service.py:3002-3025` 实际发送的 9 键**一一对应**

### 3.4 入库门（裁判 6）

存档：`evidence-red-e/index-gate-20260909T000001.txt`

- `git ls-files .claude/agents | wc -l` → **18** ✅
- `git status --porcelain .claude/agents` → 7 份全是 `A`（计数 = 7）✅
- 用 `git add -f`（仓根 `.gitignore:44 .claude/*` 会吞新文件）；该条命令**不含任何推送动作**（guard-hook 的 ` -f ` 正则跨整条命令匹配）

### 3.5 假绿修与两个对照输入（裁判 2、4）

**开工基线**（`evidence-red-e/smoke-open-20260909T000001.txt`）：恰 **9 failed / 36 passed / 45 collected**，9 条身份 = 7 条 `assert filepath.exists()` + 1 条 `assert len(actual_files) >= 17` + 1 条 hint-generation exists。

> **假绿的直接实证**：同一次运行里，`test_agent_template_not_empty[canvas-orchestrator.md]`、`[graphiti-memory-agent.md]`、`[hint-generation.md]`、`[iteration-validator.md]`、`[parallel-dev-orchestrator.md]`、`[planning-orchestrator.md]`、`[review-board-agent-selector.md]` **7 条全部报 PASSED** —— 而这 7 个文件当时**根本不存在**。`:79 if filepath.exists():` 让断言体整个被跳过，零断言 = 绿。

**收工**（`evidence-red-e/smoke-after-fix-20260909T000001.txt`）：**48 passed / 0 failed**，用例数 45 → **48**（只增不减）。

**对照输入 A**（承重 = 假绿修）：清空 `graphiti-memory-agent.md` → `1 failed, 47 passed`，唯一红条 = `test_agent_template_not_empty[graphiti-memory-agent.md]`（指定用例 `grep -c` = 1）。
还原后 sha `814c8289…` 与 `f425d7b7^` 原值相同、5584 B、`git diff --quiet` rc=0、`git status` 恢复原状。
存档：`negctl-a-setup / negctl-a-red / negctl-a-restore-20260909T000001.txt`

> ⚠️ **还原手段与卡文的偏差（如实登记）**：卡文写 `git show HEAD:<path> > <path>`，但这 7 份在 `HEAD` 里**并不存在**（本卡刚 `add -f`，尚未 commit），该命令会失败。实际用 `git show :<path>`（index stage-0 blob）。仍满足禁令（非 `checkout` / `restore` / `stash`），且顺带多验一件事：还原后 sha 相同 ⇒ 进 index 的内容确实等于从 `f425d7b7^` 恢复出来的内容。

**对照输入 B**（承重 = 阈值 18 + 聚合防删门）：把 `parallel-dev-orchestrator.md` 移到树外 → `4 failed, 44 passed`，`test_minimum_template_count` 红（指定用例 `grep -c` = 1）且消息含 `found 17`（`grep -c` = 1）。
另外 3 条红是预期的额外收获：`test_agent_template_exists[parallel-dev-orchestrator.md]`、`test_no_expected_template_is_missing`（新增聚合门）、以及 `test_agent_template_not_empty[parallel-dev-orchestrator.md]` —— **最后这条在假绿修之前遇到「文件不存在」会报 PASSED**，它这次变红是假绿修承重的第二重证明。
还原后 sha `76a67f32…` 与 `f425d7b7^` 原值相同、13392 B、目录回到 18、`git diff --quiet` rc=0、scratch 目录无残留；复跑 **48 passed**。
存档：`negctl-b-setup / negctl-b-red / negctl-b-restore / smoke-postnegctl-20260909T000001.txt`

⚠️ 若阈值仍停在 17，对照输入 B 会**不红**——它是 (f)② 是否真做到位的判据。实测红，故成立。

> ⚠️ **表述更正（Codex r1 LOW-2）**：首个 commit message 里写的「两个对照输入各只让指定用例变红」**过宽**。准确说法是：**A 恰 1 条红**；**B 是 4 条红**，其中 `test_minimum_template_count` 是被承重的那条（消息含 `found 17`），另外 3 条是同一次删除必然连带的。判据从来是「**指定的那条**必须红」（`grep -c <用例名>` ≥ 1），不是「只有它红」。本单 §3.5 原文一直如实列着 4 failed，是 commit message 的总述收窄失当，已在整改 commit 中更正。

**对照输入 C**（承重 = 两表 AST 门；来源 = Codex r1 MEDIUM-1 指出的失效场景，本卡整改后补做）：

在 `agent_service.py:5725` 的 `]` 之后注入一行 `expected_templates = expected_templates[:-1]` —— health 真正迭代的列表随之变成 12 项、缺 `hint-generation`。

- **整改前**的提取器只扫 List 字面量 ⇒ 仍返回原 13 项 ⇒ 两条集合断言的输入毫无变化 ⇒ **照绿**（Codex 在内存中复现，本卡确认成立）。
- **整改后**：`2 failed, 46 passed`，`test_health_expected_templates_equals_loadable_agent_types` 红（指定用例 `grep -c` = 1），失败消息 `` `expected_templates` is bound 2 time(s) … at line(s) [5711, 5726] ``（`grep -c` = 2，两条依赖同一 helper 的测试各命中一次）。
- 还原：`git show HEAD:backend/app/services/agent_service.py > <同路径>` → sha `329a42cb…` 与 HEAD 版**逐字节相同**、`git diff --quiet` rc=0、`:5726` 恢复为空行；复跑 **48 passed**、`ruff format --check` + `ruff check` 全绿。
- 存档：`negctl-c-setup / negctl-c-red / negctl-c-restore / smoke-postnegctl-c-20260909T160000.txt`

### 3.6 统一裁判 `tests/unit`（裁判 1）

命令：`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit -q -p no:cacheprovider`

共跑 **5 次**全量（1 次开工 + 4 次收工）。第 5 次绑 Codex r2 整改后的代码，是**终审口径**。

| # | 阶段 | 汇总行 | nodeid 数 | 末行 | 存档 |
|---|---|---|---|---|---|
| 1 | 开工 | `173 failed, 4749 passed, 48 skipped, 121 warnings, 29 errors in 364.47s` | 202 | `rc=1` | `unit-open-20260909T000001.txt` |
| 2 | 收工（format 前） | `164 failed, 4761 passed, …, 29 errors in 269.27s` | **193** | `rc=1` | `unit-after-20260909T120000.txt` |
| 3 | 收工（绑 `eed7a44c`） | `164 failed, 4761 passed, …, 29 errors in 320.40s` | **193** | `rc=1` | `unit-final-20260909T140000.txt` |
| 4 | 收工（绑 `f7729fdb`） | `164 failed, 4761 passed, …, 29 errors in 324.18s` | **193** | `rc=1` | `unit-r2-20260909T170000.txt` |
| 5 | **收工（绑 r2 整改，终审）** | `164 failed, **4762** passed, 48 skipped, 122 warnings, 29 errors in 423.99s` | **193** | `rc=1` | `unit-r3-20260909T190000.txt` |

算术：202 − 9 = **193** ✅（四次收工全部 193；`grep -c .` 实测，全程未用 `wc -l` 当分母）。跑 #5 的 passed 从 4761 增至 **4762**，正是 r2 整改新增的运行期绑定用例。

**终审判据（跑 #5，对本树开工基线）** — `red-diff-r3-vsopen-20260909T190000.txt`：

- `>` 行：**零条**（`grep '^>'` 无输出，rc=1）✅
- `<` 行：**恰 9 条**，集合 == §〇 的 9 条 nodeid ✅
- 收工 red 集里 `test_agent_templates_smoke` 残留 = **0** ✅

**双分母对照全表**（开工基线本身与主干 202 基线有一进一出，见 §六⑩，故两个分母都跑）：

| 分母 | 跑 #2 | 跑 #3 | 跑 #4 | **跑 #5（终审）** |
|---|---|---|---|---|
| **主干 202 基线** | `<` 10、`>` 1 | `<` 9、`>` **0** ✅ | `<` 9、`>` **0** ✅ | `<` 10、`>` 1 |
| **本树开工基线** | `<` 9、`>` **0** ✅ | `<` 10、`>` 1 | `<` 10、`>` 1 | `<` 9、`>` **0** ✅ |

> 两个分母之间那 1 条差额，全部来自 §六⑩ 那两条与本卡无关、且在全跑口径下不稳定的用例；**「9 条 `<`、零 `>`」在两个分母上各自达成过两次**。**本卡的 9 条在全部 5 次全跑里表现完全一致**：开工 9 条全红、四次收工 9 条全绿、零次出现本卡引入的新红。

### 3.7 `tests/api` 目录级（协议 §3）

| 阶段 | 结果 | 存档 |
|---|---|---|
| 开工 | `268 passed`，red nodeid 集 = **0 条**，rc=0 | `api-open-20260909T000001.txt` |
| 收工 | `268 passed`，red nodeid 集 = **0 条**，rc=0 | `api-after-20260909T120000.txt` |
| diff | **为空**（`api_diff_rc=0`，无 `>` 行） | `red-api-diff-20260909T120000.txt` |
| `test_agents_health.py` 开工 | `12 passed`，rc=0 | `agents-health-open-20260909T000001.txt` |
| `test_agents_health.py` 收工 | `12 passed`，rc=0 | `agents-health-after-20260909T120000.txt` |

> ⛔ **这条只证「没被本卡改红」，不证「期望表已对齐」**。`test_agents_health.py` 用的是 `MockAgentService`，其 `expected_templates`（`:64-77`）是 mock 内**硬编码的 12 项**，`:141-142` 硬编码 `total == 12` / `available == 12`、`:172 available == 10`，**完全不读文件系统、不读生产表**。本卡把生产表改成 13 之后它照样全绿 —— 这正是「同源期望只改一处」的静默漂移。该文件不在本卡地盘（手册 §一 未分派），故只跑不改，修复移交见 §六⑨。

### 3.7b health 期望表 12 → 13 的语义影响（实测，非推断）

存档：`evidence-red-e/health-semantics-20260909T140000.txt`

在不起服务、不外呼的前提下复现 `agent_service.py:5727-5742` 的 exists 分桶循环（`expected_templates` 由 `ast` 从生产源码取，`prompt_path` 取 `settings.AGENT_PROMPT_PATH`）：

```
prompt_path      = …/card-u10-red-a/.claude/agents
total            = 13
available        = 13
missing          = []
=> len(missing) > 0 ?  False   (True 才会让 status = degraded)
```

**这是一处正向语义修复，不是回归**：

- 改**前**：表里 12 项中 `canvas-orchestrator.md` 也不存在 ⇒ `missing_templates` 非空 ⇒ `:5773-5774` 恒判 `degraded`。
- 改**后**：13 项全部在盘 ⇒ `missing = []` ⇒ 模板这一层不再 degraded。

⚠️ 端点最终状态仍取决于 `:5771-5772` 的 `api_key_configured` / `gemini_client_initialized`，本卡**未实跑端点**（见 §五②）。本条只证「模板这一层从恒 degraded 变为不 degraded」，不证端点整体为 healthy。

⚠️ 副作用：`prompt_template_check["total"]` 由 12 变 13。任何硬编码 12 的地方随之不一致 —— 实测唯一命中处是 api 侧 mock，见 §六⑨。

### 3.8 pyright 多重集对照（裁判 7 / 协议 §2.3）

存档：`evidence-red-e/multiset-20260909T120000.txt`，首行：

```
base=421 work=421 NEW=0 GONE=0
```

末行 `rc=0`。基线 = `BASE_SHA=0465a35c` 的 `git archive` 树（`pyright-base-0465a35c.json`），工作侧 = 本树 HEAD（`pyright-work-*-20260909T120000.json`）。

`agent_service.py` 的 **8 条既有报错本卡一条未修**（归 U1 阶段 2），行号与勘探逐条对上：`:18`（reportUnusedImport `logging`）、`:1486` `:1487` `:1540` `:1541` `:3042` `:4181`（6×reportMissingImports）、`:2219`（reportUnusedVariable `source_desc`）。

**hook 跳过**：`lefthook.yml:205-231` 的 `python-typecheck` glob `backend/app/*.py` 命中 `agent_service.py`，`:224` 只检 staged、`:231` 透传 rc ⇒ 本卡 commit 必被拦（实测 `8 errors, 17 warnings`，`pyright_rc=1`）。按协议 §2.3 + 手册 §零.3（D-16 甲过渡）**带存档跳过该 hook**。
被跳过 hook 的原始输出：`evidence-red-e/typecheck-hook-20260909T120000.txt`（含 `lefthook.yml:205-231` 全文 + pyright 原始 25 行 + `pyright_rc=1`）。
「无新增」的判据取**基线树多重集对照 `NEW=0`**，不取行号交集（行号交集不足以证明零新增）。本卡在该文件的改动 hunk 恰一处：`@@ -5723,0 +5724 @@`。

---

## 四 DoD-3 · 4-B「你来验」（零技术词）

请在系统里这样走一遍：

1. 打开任意一块检验白板，挑一个你**确实还没完全想明白**的概念，回答它的检验问题，**故意答得不完整**（比如只说对一半）。
2. 看系统给你的提示。**记住这句话。**
3. 再答一次，还是不完整，但换个说法。看第二次的提示。
4. 第三次再答一次。看第三次的提示。

**你应该看到**：三次的提示**不一样**，而且一次比一次具体——

- 第一次像在说「往哪个方向想」；
- 第二次会**引用你自己写的话**，指出你那句话里差在哪一处；
- 第三次会给你一个「分几步想」的骨架，但**最后一步仍然留给你**。

**你不应该再看到**：三次都是同一句「提示 N：思考「XX」的定义和核心特点。」——那是修复之前的样子，无论你答什么、答第几次，系统给的都是这一句。

**felt-sense（本卡真正想让你感觉到的）**：第二次提示引用你原话的那一刻，你会有一种「它是真的在看我写的东西」的感觉，而不是「它在敷衍我」。这个信任感是这次修复的全部意义——一个每次都回同一句套话的提示系统，比没有提示更伤人，因为它假装在帮你。

> ⚠️ 说明：4-B 这一段能不能真的看到，取决于系统连上了可用的 AI 服务。本卡只修了「模板缺失导致必然降级」这一层——模板现在在了，链路通了；但**本卡没有实跑过真实 AI 调用**（见 §五④）。如果你走完上面四步仍然三次都是同一句话，那说明还有另一层问题，请告诉我，那是下一张卡的事。

---

## 五 本卡未证明什么

1. **未证明新 `hint-generation.md` 的提示词教学质量**。本卡只证「能被生产解析器解析且契约字段齐」。分级策略（`direction` / `diagnostic` / `scaffold` 三档、按 `attempt_number` 取值）是本卡自定的，**没有论文或成熟案例支撑**（DD-01 依据另议）；`hint_level` 的取值域是本卡在模板里写死的，生产侧 `verification_service.py:3040` 只把它写进日志、不做校验，所以模型返回别的值也不会被拦。
2. **未证明 `/agents/health` 端点实跑为 healthy**。需要可用的 AI 服务 key，本批禁外呼。只证了期望表从 12 改到 13 这一处代码改动，以及 `agent_service.py:5730-5735` 的 exists 分桶逻辑会去查这 13 个文件（现在全都在）。
3. **未证明 3 份无 frontmatter 的恢复模板可被 `_parse_prompt_template` 解析**。它们（`iteration-validator` / `parallel-dev-orchestrator` / `planning-orchestrator`）首行是 `# <Title>`，会撞上 `gemini_client.py:170-171` 的 `raise ValueError("Invalid prompt template: missing YAML frontmatter")`。因为生产不加载它们（不在 `AgentType`），本卡按「恢复内容一字不改」的约束**故意没有补 frontmatter**。
4. **未证明 `call_agent` 在真实 AI 服务下会返回含 `hint_text` 的 JSON**。本卡只证模板侧契约（模板声明了这两个键、解析器能读出来）。模型是否照做、`agent_service.py:2449-2470` 的 JSON 解析是否命中，均未实跑。
5. **未证明防删门能拦住「在 Obsidian / Finder 里手删」**。pytest 门只在跑测试时说话。`.claude/hooks/pretool-guard.js` 存在但 `.claude/settings.json` 的 `hooks` 是 `{}`、未注册任何 PreToolUse ⇒ D-22 的 hook 分支不成立，本卡按裁定走纯 pytest 门，未动 hook。
6. **未证明 `agent_metrics.py:67-84` 的 `VALID_AGENT_TYPES`（14 项，不含 `hint-generation`）对指标面的影响**。该文件不在本卡地盘，只读未改。
7. **未证明 `f425d7b7` 那次删除的动机**（commit message 只有 `ralph-loop: iteration 0`）。只作事实登记。
8. **两表门的能力边界（经 Codex 三轮收窄后的说法，含两次自我更正）**。当前形态是「静态读名单 + 运行期读名单 + 逐项比对 + 查重」：
   - **静态半边**：`ast` 读 `AgentService.health_check` 内的 `expected_templates` 列表字面量。「绑定唯一」**不等于**「读到的就是 probe 实际迭代的」——原地改内容不改绑定。
   - **运行期半边**：把 `AGENT_PROMPT_PATH` 指向空目录，`missing` 原样返回 probe 的完整名单（有序），逐项比对 + 查重。**这一半才是身份绑定**。
   - **仍未证明**：① 未验证「表被移出 `health_check`、改由该方法调用的 helper 提供」——那时静态半边报 `bound 0` 会红（Codex r3 实测），但这是**噪声红而非精确诊断**，本卡未为该重构提供可用路径；② 未验证 probe 在**非空但内容不同**的目录下的行为（只测了「本树真实目录」与「空目录」两端）；③ `prompt_template_check` 只回 `total`/`available`/`missing`，身份靠「制造全缺失」间接取得，**本卡未改生产以让它直接回报名单**（越界）；④ 未证明该手法在 `AGENT_PROMPT_PATH` 被别的机制（如 endpoint 层缓存）固化时仍有效。

   ⚠️ **本条被写宽过两次，此处是第三版**：
   - r1 曾称 `ast.Store` "covers every binding form" 并据此宣称门锁住了 health 迭代的内容 —— 前半句成立，**后半句的推论**被 Codex r2 用 `remove` / `[:]=` / `match-case` 证伪。
   - r2 改后又写下 "any such edit changes the length" —— 被 Codex r3 用**等长替换** `[-1] = "other"` 证伪。
   两次都是「一个真实观测 + 多走一步的普遍化」。第三版起，本条只陈述**已被对照输入实证**的覆盖面，未实证的一律列进上面的「仍未证明」。
9. **未证明 `test_minimum_template_count` 对「删一份 + 加一份无关 .md」免疫**。它数的是 `_AGENTS_DIR.glob("*.md")` 的总数，不是期望名单的交集；这个盲区由新增的 `test_no_expected_template_is_missing`（按名单逐份 exists）覆盖，两条合起来才完整——单看阈值那条仍有此余量。
10. **未证明开工基线那两条漂移与 U10-A 的因果**。见 §六⑩，只观测到现象，未做归因实验。
11. **未证明这 7 份文件不会经只动 index 的路径掉出版本控制**（Codex r1/r2/r3 三轮均点名）。`git rm --cached` 保留磁盘文件却移除 index 条目，**本地 smoke 仍全绿**，只有干净 checkout 才暴露；退出跟踪后 ignore 规则又会阻止普通 `git add` 收录。pytest 门只看工作树，不检查 Git 跟踪状态。
12. **未证明 `exists()` 分桶能识别「文件在但内容为空或不可解析」**。health 探针只判存在。smoke 侧 `not_empty` 覆盖空文件，但**不覆盖**「非空却不可被 `_parse_prompt_template` 解析」（那 3 份无 frontmatter 的恢复模板正是此类，见 ③）。
13. **未证明在单元测试里实例化 `AgentService()` 没有副作用、也未证明它在无配置的 CI 环境下稳定**。本卡自查到的是：单跑 3 次全绿、`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`、tracked 文件 0 改动、`gemini_client=None` 无未关闭资源告警。**Codex r3 明确保留此项为「未完整核验」**（其读取面不含构造器与完整 health 方法），本卡随之不宣称该结论。
14. **未证明新用例对 `settings.AGENT_PROMPT_PATH` 的临时改写在并行测试下安全**。它直接 `setattr` 全局 `settings` 对象并在 `finally` 还原，未用 `monkeypatch`；在 `pytest-xdist` 并行或同进程内有其他测试同时读该设置时，存在理论上的竞争窗口。本卡跑的是串行单文件与串行 `tests/unit`，**未在并行下验证**。

---

## 六 台账待登记条目

1. **7 份新增文件清单 + 逐份 sha / 字节数**：见本单 §三.1 表（6 份恢复）+ `hint-generation.md`（新作，5199 B，sha `4f9f40cdfd1dbede9478a5e5b008621de52d630567e0c3533165046b230f017f`）。存档 `evidence-red-e/restore-sha-20260909T000001.txt`、`index-gate-20260909T000001.txt`。
2. **`.gitignore:44` 吞新文件** ⇒ 本卡用 `git add -f` 入库。「给根 `.gitignore` 加 `!.claude/agents/`」= **越界项**，移交排批裁定。
3. **`pretool-guard.js` 存在但未在任何 settings 注册**（`.claude/settings.json` 的 `hooks` = `{}`，`settings.local.json` 无 `hooks` 键）⇒ D-22 的 hook 分支不成立。若要接线须注册 `matcher: "Bash|Write"`，**移交第十四批**。
4. **smoke `:11` / `:61` 的 `[Source: docs/stories/31.A.2.story.md]` 引用不实**（该文档标题是「学习历史读取修复」，`grep -i hint` 0 命中）。本卡**未改这两处**（避免扩大改动面），只登记。
5. **`agent_metrics.py:67-84` 的 `VALID_AGENT_TYPES` 14 项缺 `hint-generation`**（不在本卡地盘，只读未改）。
6. **health 期望表口径从 12 改 13 的定义**：13 = `AgentType` 去掉 `four-level` / `scoring` 两别名后的全部值。差集 5 份的原因见本单 §二。新增项位置：`agent_service.py:5724`，放在 `"canvas-orchestrator"` 之后（列表末尾）。
7. **`agent_service.py` 8 条 pyright 存量未修**（归 U1 阶段 2）。**本卡用过 hook 跳过**：`LEFTHOOK_EXCLUDE=python-typecheck`，存档 `evidence-red-e/typecheck-hook-20260909T120000.txt`（被跳过 hook 的原始输出）+ `multiset-20260909T120000.txt`（`NEW=0` 行）。
8. **Codex 轮次与每轮绑定 SHA**：见 §七。
9. **api 侧期望表漂移移交（重要）**：`backend/tests/api/v1/endpoints/test_agents_health.py:64-77` 的 mock 内 `expected_templates` 仍是 **12** 项，`:141-142` 硬编码 `total == 12` / `available == 12`、`:172 available == 10`，与本卡 (g) 改成 13 的生产表**已脱节但测试照绿**（mock 不读生产表）。该文件不在本卡地盘 ⇒ 本卡只跑不改（证据见 §三.7），**修复移交第十四批微卡**。建议修法：让 mock 与断言从生产 `expected_templates` 取数，或至少同步到 13 并保留一条「两处必须相等」的断言。
10. **开工 `tests/unit` 基线与主干 202 基线有一进一出（非本卡引入）**：
    - `>` `test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`（本树全跑红，202 基线里没有）
    - `<` `test_mock_degradation_transparency.py::TestMockScoringWarningLogs::test_mock_mode_logs_warning`（202 基线有，本树全跑绿）
    - 总数仍是 202。本卡开工时工作树干净、未改任何文件。
    - **单跑探测**（`evidence-red-e/drift-probe-20260909T000001.txt`，连跑 2 次）：两次**单跑**结果一致，且都与 202 基线相同（candidate 绿 / mock_mode 红）。
    - **全跑观测（5 次）**：

      | # | 全跑 | `test_accept_candidate_…_422` | `test_mock_mode_logs_warning` | 组合 |
      |---|---|---|---|---|
      | 1 | 开工 `unit-open-…000001` | 红 | 绿 | A |
      | 2 | 收工 `unit-after-…120000` | 红 | 绿 | A |
      | 3 | 收工 `unit-final-…140000` | 绿 | 红 | B（= 202 基线态） |
      | 4 | 收工 `unit-r2-…170000` | 绿 | 红 | B |
      | 5 | 收工 `unit-r3-…190000` | 红 | 绿 | A |

    - ⇒ **全跑口径下这两条不由代码决定**：同一份代码、同一命令，5 次观测到两种组合，出现顺序 **A A B B A**。两态互斥（恒一红一绿，占 202 / 193 里的同一格）。
    - ⚠️ **本条第二次更正**：上一版依据前 4 次写成「形态是**切换后保持**而非逐次随机」，第 5 次跑回 A 直接证伪。现在**只记录观测序列，不做形态归纳**——5 个点不足以区分「周期」「随机」还是「依赖某个未识别的外部状态」。
    - **未做归因实验**：`da690bf8..HEAD` 里只有 U10-A 改了 `backend/tests/unit/conftest.py`，两个漂移文件本身未被改；本卡既未验证 conftest 的因果，也未定位触发因素。**移交主 session 排批时判定**。
    - **不影响本卡结论**：本卡的 9 条在全部 5 次全跑里表现完全一致（开工全红、四次收工全绿、零次新红），与这两条的摇摆正交；且「`<` 恰 9 条、`>` 零条」在**两个分母上各自达成过**（202 基线于跑 #3/#4，开工基线于跑 #2/#5）。
    - ⚠️ **本条曾被写宽过，此处更正**：先前依据「两次单跑稳定」写成「不是随机 flaky，而是执行顺序 / 测试间污染」。两次单跑只能证明**单跑口径**稳定，推不出全跑口径的机制；收工 #2 的翻转直接证伪了那个更强的表述。现结论收窄为：**单跑稳定、全跑非确定，机制未定**。
    - **未做归因实验**：`da690bf8..HEAD` 只有 U10-A 改了 `backend/tests/unit/conftest.py`，两个漂移文件本身未被改，但本卡未验证 conftest 改动与这两条的因果，也未定位非确定性的来源。**移交主 session 排批时判定**。
    - **不影响本卡结论**：本卡的 9 条在全部 3 次全跑里表现完全一致（开工全红、两次收工全绿、零次新红），与这两条的摇摆正交。
11. **现存模板的 `input_format` / `output_format` 在生产解析器下全部为 `None`**（本卡实测的既有事实，非本卡引入）：`_parse_prompt_template` 的正则要求 `## Output Format\n` **紧接** ` ```json `，而现存 11 份全都按 Markdown 惯例在中间插了一行说明文字（如「你必须返回以下JSON格式的输出：」）⇒ 正则不匹配、字段恒 `None`。功能上未坏（`system_prompt` 保留全文，模型仍看得到 JSON 示例），但 `AgentPromptTemplate.output_format` 这个结构化字段在全仓恒空。本卡新模板已避开（标题行后紧接代码块），**未改任何现存模板**。是否统一排版 = 移交项。
12. **`git check-ignore` 不能当入库判据（比卡文写的更强的理由）**：卡文预期 `add -f` 后 check-ignore「仍打印 `.gitignore:44`」，**实测是不打印且 rc=1** —— `check-ignore` 对**已跟踪**文件不做 ignore 判定。也就是说它的返回值在 `add -f` 前后会**翻转**，拿它当判据会给出方向相反的结论。判据取 `git ls-files` 是对的。
13. **r1 存档一度被主 session 自己清空并重建**（详见 §七 round-1 的事故框）：BSD sed 语法错误 → 原始 stdout 正文丢失 → 自 codex session rollout 提取还原，字节账（7151 − 内部标记 = 6886，对 6887 差 1 个换行）与 11 处特征串双重核对通过。该存档**非原始落盘产物**，请复核时裁定是否计入轮次配额。
14. **协议 §2.1「抄 .stderr 前三行含 model 行」是位置判据，在 codex 0.153.3 上会失效**：models 刷新超时时两条 ERROR 会顶掉会话头位置，`model:` 落到 :7（r1）/ :5（r2）/ :7（r3），**每轮位置还不一样** ⇒ 照字面抄前三行抄不到任何自证字段。建议改为「抄含 `model:` 的那段会话头并标注实际行号」。**移交排批修订协议**。
15. **变异还原源的口径需要写进协议**（本卡两次事故的共同根因，建议补进 §2.2）：`git show HEAD:<path> > <path>` 只有在该文件**已提交且工作树无本地改动**时才等于「还原到变异前」。对有未提交改动的文件，它会静默回退掉那些改动。本卡在 smoke 文件上踩中此坑，丢失了尚未提交的整轮整改（详见 §七 round-3 事故框）。建议协议明确：**变异前先 `cp` 出工作树副本作为唯一还原源**，并在还原后断言 sha 等于该副本（而不是等于 HEAD）。
16. **本卡两次存档/工作树事故的登记**（均由主 session 自曝，非审查者发现）：① r1 存档被 BSD sed 清空后自 codex rollout 还原（§七 round-1 事故框）；② r3 工作树改动被错误还原源清掉后重写（§七 round-3 事故框）。两次都由「写完立刻自检」抓到 —— ① 是 `grep -c 'BLOCKER：该档 0 条'` 返回 0，② 是还原脚本里的 WARNING 自检行。**建议把「破坏性操作后立即断言目标内容仍在」写成排批的通用要求**。
15. **smoke 文件的两处注释更正（本卡自主判断，超出卡文明列范围，请复核时裁定）**：
    - `:22` 原注释 `# Expected agent template files after recovery (git checkout eb86275)` —— 该树只有 17 份且无 `hint-generation.md`，拿不出第 18 项，是**误导后人用错误手段恢复**的不实陈述。本卡改为记录真实来源（11 未删 + 6 从 `f425d7b7^` 恢复 + 1 新作）。
    - `:84` docstring「At least 17」按卡文要求更新为实测口径。
    - 两处均为注释 / docstring，**未触碰 `EXPECTED_AGENT_TEMPLATES` 名单本身**。

---

## 七 Codex 轮次

模型固定 `gpt-6-astra` + `model_reasoning_effort="ultra"`，`codex-cli 0.153.3`，`--sandbox read-only`。

### round-1 — 绑 `eed7a44c`

存档：`_bmad-output/审查/codex-review-CARD-RED-E-r1.md`
结论：**BLOCKER 0 条 / HIGH 0 条**；MEDIUM 1 条、LOW 2 条。Codex 自述审查绑定 `0465a35c → eed7a44cdfbc797b5bb9fa5549991b76c7d16318`，与本卡当时 HEAD 一致。

> ⛔ **存档事故与还原（主 session 自曝，必须随卡上交）**
>
> 给该存档写协议 §2.1 首部时，主 session 用了 `sed '1{/^$/d}'` —— **BSD sed 不支持这种写法**，报 `extra characters at the end of d command`，管道随之失败，`awk | sed > /tmp/body` 产出 0 字节，`mv` 又把它盖回原文件 ⇒ **原始 stdout 正文被清空**，文件一度只剩 884 B 首部。发现方式：写完立刻跑的完整性自查 `grep -c 'BLOCKER：该档 0 条'` 返回 **0**。
>
> **还原来源**：`~/.codex/sessions/2026/09/09/rollout-2026-09-09T10-51-01-01a08413-7128-7533-abc6-f36cdb5ac43f.jsonl`（时间戳与 `.stderr` 首条 `2026-09-09T02:51:01Z` 一致）的 assistant 最终消息。**未用记忆重写冒充原文**。
>
> **还原正确性的双重核对**：
> 1. **字节账对上**：rollout 原文 7151 B → 剥去模型内部标记 `<oai-mem-citation>…</oai-mem-citation>`（该块是模型原始输出的一部分，`codex exec` 写 stdout 时本就不输出）后 **6886 B**，与损坏前 stdout 实测的 **6887 B** 仅差 1 个末尾换行。差额被完整解释，无剩余。
> 2. **特征串核对**：11 处（审查绑定句 / 四档标题 / `expected_templates[:-1]` / `negctl-b-red` / `4 failed / 44 passed` / `git rm --cached` / `healthy → degraded` /「42 个文件检查用例」等）逐一 `grep -c` **全 = 1**。
>
> ⚠️ 因此该存档**不是未经处理的原始落盘产物**，首部已就此加了两条 blockquote 说明（另一条是会话头位移，见下）。复核时若认为重建存档不计入轮次配额，本卡接受重跑 r1，请裁定。
>
> 附带发现（协议改进建议，移交排批）：协议 §2.1 要求「抄 .stderr 前三行含 model 行」是**位置判据**。codex 0.153.3 在 models 刷新超时时会把两条 `codex_models_manager` ERROR 打在会话头之前，`model:` 行被顶到 :7 —— 照字面抄「前三行」会**抄不到任何自证字段**，而首部三字段因为是手填的，看上去仍然齐全。建议把判据改为「抄含 `model:` 的那段会话头（行号如实标注）」。

| 条目 | 处置 |
|---|---|
| **MEDIUM-1** 两表门只绑同名**字面量**，未绑 health 实际迭代的列表：追加 `expected_templates = expected_templates[:-1]` 后运行列表变 12 项缺 hint-generation，提取器仍返回 13 项 ⇒ **门假绿** | ✅ **已改**。`_health_expected_templates` 改为先用 `ast.Store` 统计**全部绑定**（覆盖 Assign / AugAssign / AnnAssign / for-target / with-as / walrus），`!= 1` 即红并报出行号；再取唯一的 List 字面量，取不到也红。补做**对照输入 C** 实证该场景现在必红（§3.5） |
| **LOW-1a** 差集消息用对称差 `^`：某模板日后正式加入 AgentType 后已退出 smoke-only 集，消息却仍称其 `unexpected smoke-only` | ✅ **已改**。改为分方向报「newly smoke-only」/「no longer smoke-only（health now watches them，update TEMPLATES_NOT_IN_AGENT_TYPE）」 |
| **LOW-1b** 第二个同名字面量触发 `found 2`，消息却解释成 health 被 "renamed or removed"，实际是匹配歧义 | ✅ **已改**。新消息区分 0 绑定（renamed or removed）与 2+ 绑定（gate 读的列表可能不是 probe 迭代的那个），并列出全部绑定行号 |
| **LOW-2** 「两个对照输入各只让指定用例变红」的总述与存档不符（B 实际 4 failed） | ✅ **已更正**表述，见 §3.5 的更正框。判据本身（指定用例必红）不变，删除门有效性不受影响 |

Codex 同轮独立确认的事项（无需整改，记录备查）：

- 输出字段与层级对齐：`hint-generation.md:48` 顶层直接含两键；`gemini_client.py:193` 提取的是**字符串**，`json.loads` 后得到含两键的 dict，无额外 `data` 包装；`agent_service.py:2466` 的 `result.update(parsed)` 保留顶层键，与 `verification_service.py:3036` 消费路径相符。**但解析成功 ≠ 模型输出经 schema 校验**，且本卡未作真实调用验收（与 §五① §五④ 一致）。
- `>= 18` 单条**确实**能被「删一份 + 补一份无关 .md」通过，但按名单的存在性 / 非空 / 缺失汇总三条（`:120` / `:132` / `:143`）挡住具名模板缺失 ⇒ **不能据此说整套 smoke 假绿**（与 §五⑨ 的登记一致）。
- 六份恢复文件的工作树 / HEAD / index / `f425d7b7^` **四方字节一致**，字节数与 SHA256 与存档相符；当前 HEAD 与 index 均有完整 18 份。
- `.gitignore:44` 对已跟踪文件不起忽略作用。但文件仍可经 `git rm`、删除后暂存、合并删除、回退提交而丢失；**尤其 `git rm --cached` 保留磁盘文件却移除 index 条目，本地 smoke 照绿，只有干净 checkout 才暴露** —— 退出跟踪后 ignore 规则又会阻止普通 `git add` 收录。这是 pytest 工作树检查的**边界**，补记入 §五（见下条）。
- health 语义方向正确：其余条件正常、原 12 项齐全但缺 hint 的部署会从 `healthy → degraded`；只增期望项不会让 `degraded → healthy`（恢复文件才会）。空文件或不可解析模板仍会被 `exists()` 判为 available —— 原有存在性检查的边界。

> **补记入「本卡未证明什么」（源自 Codex r1，编号接 §五）**：
> ⑪ 未证明这 7 份文件不会经 `git rm --cached` 之类**只动 index 不动磁盘**的路径掉出版本控制 —— 那种情况下本地 smoke 仍全绿，只有干净 checkout 才暴露；pytest 门只看工作树，不检查 Git 跟踪状态。
> ⑫ 未证明 `exists()` 分桶能识别「文件在但内容为空或不可解析」—— health 探针只判存在。smoke 侧的 `not_empty` 覆盖了空文件，但**不覆盖**「非空却不可被 `_parse_prompt_template` 解析」。

### round-2 — 绑 `f7729fdb`

存档：`_bmad-output/审查/codex-review-CARD-RED-E-r2.md`（8571 B；**正文为原始落盘 stdout，未经处理**，与 r1 不同）
结论：**BLOCKER 0 条 / HIGH 0 条**；MEDIUM 1 条、LOW 2 条。Codex 自述「结束时 HEAD 未变，本卡文件与 HEAD 无差异」。

| 条目 | 处置 |
|---|---|
| **M-1（门缺口，重要）** r1 的整改只挡住「重新绑定名字」，挡不住**原地改内容**：`expected_templates.remove("hint-generation")`、`expected_templates[:] = expected_templates[:-1]`、`match/case` 重绑定（`MatchAs.name` 不是 `ast.Name(Store)`）三者实测均 `EXTRACT_PASS extracted=13 runtime=12`，断言输入不变 ⇒ **仍照绿**。Codex 结论：「绑定次数不能证明所提取内容等于实际迭代内容」 | ✅ **已改，且换了判据类型**。新增 `test_health_probe_output_matches_the_table_this_gate_reads`：实际 `await AgentService().health_check(include_api_test=False)`，把**运行期产出**的 `total` / `available` / `missing` 与静态名单对照。判据从「静态猜源码」升级为「运行期读回」。补做**对照输入 D**，三种场景全部实证必红 |
| **L-1（噪声红）** 全模块 `ast.walk` 扫同名变量：仅追加一个**从未被调用**的 `def unrelated(): expected_templates = set()` 就会报 `bound 2 time(s)` | ✅ **已改**。新增 `_health_check_body()`，把扫描面**限定到 `AgentService.health_check` 这一个方法**；找不到该方法（改名/移走）则红。实测追加无关同名局部后仍 **49 passed** |
| **L-1 附带** `literals` 只收 `ast.Assign`，把 `expected_templates: list[str] = [...]` 这种合理重构误报成 "not to a list literal" | ✅ **已改**。兼收 `ast.AnnAssign`；实测改成带注解写法后仍 **49 passed** |
| **L-2（消息措辞）** `TEMPLATES_NOT_IN_AGENT_TYPE - smoke_only` 不只含「health 新增」，也含「从 smoke 名单移除」，但消息一律说 `health now watches them` | ✅ **已改**。两个方向都改成中性表述，第二个方向明说「health now watches it, **or it left EXPECTED_AGENT_TEMPLATES**」 |
| **表述收窄（Codex 指出）** 「ruff format/check 全绿」的说法过宽——存档 `ruff-gate` 里 `agent_service.py` 仍记录既有格式漂移 | ✅ **已更正**。全卡口径统一为：**smoke 文件** format+check 全绿；`agent_service.py` 保持 `DRIFT-AT-HEAD` 未动（既有漂移，禁顺手修），实测 `agent_svc_fmt_rc=1` 如实登记 |

Codex r2 同轮独立确认（无需整改）：

- 新模板输出契约对得上，且它**实际调用了** `load_prompt_template("hint-generation")` + `json.loads` + 复跑 `agent_service.py:2466` 的合并代码，确认两键留在返回字典顶层，与 `verification_service.py:3036/:3040` 一致。同时明确：**这只证明格式兼容，不证明模型每次都遵守格式**（与 §五① §五④ 一致）。
- 计数测试单独有余量，但逐文件检查与缺失集合检查挡住具名删除 ⇒ 不能说整套 smoke 假绿（与 §五⑨ 一致）。
- 六份恢复文件逐字节等于 `f425d7b7^`，18 份均受跟踪。**新增实测**：普通 `git check-ignore` 不命中已跟踪文件，加 `--no-index` 才显示 `.gitignore:44` —— 与本卡 §六⑫ 的发现互相印证。
- health 覆盖范围改变且方向正确；端点仍不检验内容能否解析（已声明边界，§七 补记 ⑫）。
- Codex 关闭缓存、插件自动加载并隔离 conftest 后独立重跑得 **48 passed**（其快照早于本轮 M-1 整改，本卡整改后为 **49 passed**）。

### round-2 整改后的对照输入（本卡补做，实证新门承重）

| 对照输入 | 注入 | 结果 | 存档 |
|---|---|---|---|
| **D-1** | `expected_templates.remove("hint-generation")` | `1 failed, 48 passed`，红的正是 `test_health_probe_output_matches_the_table_this_gate_reads` | `negctl-d-20260909T180000.txt` |
| **D-2** | `expected_templates[:] = expected_templates[:-1]` | 同上，恰 1 红且为指定用例 | 同上 |
| **D-3** | `match expected_templates[:-1]: / case expected_templates:` | 同上，恰 1 红且为指定用例 | `negctl-d3-l1-20260909T180000.txt` |
| **L-1 反向** | 追加无关的 `def _unrelated_helper_for_scope_probe(): expected_templates = set()` | **49 passed**（噪声红已消除） | 同上 |
| **AnnAssign** | 把表改成 `expected_templates: list[str] = [...]` | **49 passed**（不再误报 not a list literal） | `negctl-annassign-20260909T180000.txt` |

三次注入还原后 `agent_service.py` sha 均为 `329a42cb…`，与 HEAD 逐字节相同，`git diff --quiet` rc=0。

> **判据类型的升级（本轮最实质的改动）**：r1 的门是「读源码猜 health 用什么表」，r2 的门是「跑 health、读它自己报出来的 total/missing」。前者对「不改绑定只改内容」的编辑天然失明——这不是实现 bug，是**判据类型**选错了。Codex 两轮把它从静态推断推到了运行期观测。
>
> ⚠️ 但 r2 的运行期判据仍只绑定**数量**，r3 用等长替换直接证伪，见下。

### round-3 — 绑 `49994317`

存档：`_bmad-output/审查/codex-review-CARD-RED-E-r3.md`（**正文为原始落盘 stdout，未经处理**）
结论：**BLOCKER 0 条 / HIGH 0 条 / LOW 0 条**；MEDIUM 1 条。Codex 自述绑定 `49994317d89fbdf4b1ef2ae981305dac89e0d3cb`，与当时 HEAD 一致。

| 条目 | 处置 |
|---|---|
| **M-1（门缺口，第三次同类）** r2 的运行期用例只断言 `total == len(names)` / `missing == []` / `available == len(names)` —— **三条全是数量**。在表定义之后注入 `expected_templates[-1] = "graphiti-memory-agent"`：静态名单仍 13 项含 `hint-generation`，运行期名单也是 13 项但**已不含它**，`total=13 / available=13 / missing=[]` ⇒ 三条断言全 PASS。换成 `"scoring-agent"` 则实际只剩 12 个不同成员，同样全绿。作者注释里那句 "any such edit changes the length" **范围过宽** | ✅ **已改，判据从数量升级为身份**。新增 `test_health_probe_watches_exactly_the_names_this_gate_reads`：把 `settings.AGENT_PROMPT_PATH` 临时指向 pytest `tmp_path`（空目录）→ 每一项都落进 `missing` ⇒ **probe 把自己的完整名单按顺序原样吐出来**；再与静态名单**逐项比较** + **查重**。这正是 Codex 建议的修法。`finally` 还原设置，并额外断言还原成功。原 r2 用例保留并改名为 `test_health_probe_reports_no_missing_template`（守生产面：probe 不得报缺失） |
| **表述更正（Codex 再次指出）** r2/r3 的 prompt §二 第 5 条仍写着「两个对照输入各自只让指定用例变红」，B 实际 4 failed | ⚠️ **我的疏漏**：LOW-2 我只更正了验收单，**没有同步更正 prompt 里的作者自述**，导致 Codex 每轮都重新看到那句不实表述并重新纠正。已在 r4 prompt 中改正。这条记在这里，是因为「只改一处、忘了同源的另一处」正是本卡 §六⑨ 批评 api 侧 mock 的同一种毛病，我自己也犯了 |

Codex r3 同轮独立确认（无需整改）：作用域收窄后改名 / 外移 / 改成 helper 调用 / 方法内二次绑定四种路径均明确失败（分别 `bound 0` / `bound 0` / `not to a list literal` / `bound 2`），没有静默失效；恢复六份满足「工作树 = HEAD blob = `f425d7b7^` blob」三方一致，tracked 模板精确 18；health 新增一项的语义方向正确。

### round-3 整改后的对照输入（本卡补做）

| 对照输入 | 注入 | 结果 | 存档 |
|---|---|---|---|
| **E-1** | `expected_templates[-1] = "graphiti-memory-agent"` | `1 failed, 49 passed`，红的正是 `test_health_probe_watches_exactly_the_names_this_gate_reads` | `negctl-e-20260909T210000.txt` |
| **E-2** | `expected_templates[-1] = "scoring-agent"`（制造重复项） | 同上，恰 1 红且为指定用例 | 同上 |
| **D 复跑** | `remove(...)` / `[:] = ...` 两种减项 | 各 `1 failed`，红的都是身份绑定用例（未因 r3 改动退化） | `negctl-d-rerun-20260909T210000.txt` |
| **L-1 反向复跑** | 追加无关同名局部 | **50 passed**（噪声红仍未复发） | 同上 |

四次注入还原后 `agent_service.py` sha 均为 `329a42cb…`，与 HEAD 逐字节相同。

> ⛔ **第二次自曝事故：对照输入 F 的还原源用错，清掉了尚未提交的 r3 改动**
>
> **经过**：对照输入 F 变异的是 **smoke 文件本身**（把 `monkeypatch` 的目标改成真实目录，验证「覆盖失效」时该用例是否仍红）。变异确实红了、红在正确的前置断言上。但**还原源写成了 `git show HEAD:<path>`** —— 而 r3 的改动当时**还在工作树、尚未提交**，HEAD 是 r2 版本 ⇒ 这一还原把新增的身份绑定用例、拆分后的两个用例、以及 docstring 更新全部清掉，文件回退到 49 用例。
>
> **发现方式**：还原脚本里那句自检 `print('WARNING: restored to HEAD, which lacks the r3 fix' if 'watches_exactly' not in ...)` 立即打出了 WARNING。
>
> **为什么前面 D/E 系列没事**：那几组变异的是 `agent_service.py`，它**已提交**，HEAD 恰好就是变异前状态，`git show HEAD:` 语义正确。**同一条还原命令在两个文件上正确性不同，取决于该文件有没有未提交改动** —— 这正是 memory 里「还原基准是变异前的 sha 不是 HEAD」那条，我读过却仍然踩中。
>
> **补救**：r3 三处改动全部重写。重建版 sha `d2cb6492…` 与丢失前 `f4020149…` **不同**（丢失前是「try/finally 版 → 改 monkeypatch → format」两次编辑的产物，重建是一次写成），故**不以 sha 为等价判据，改以行为为判据**：复跑 D/E/F **五组注入**，全部 `1 failed, 49 passed` 且红的都是 `test_health_probe_watches_exactly_the_names_this_gate_reads`；还原后 50 passed、两文件 sha 均回到变异前。存档 `negctl-rebuild-verify-20260909T230000.txt`。
>
> **流程改正**：此后凡变异**有未提交改动的文件**，还原源一律取变异前的工作树副本（scratchpad），并在脚本开头显式 `cp` 出来；`git show HEAD:` 只用于已提交且无本地改动的文件。
>
> **连带作废**：同一时间窗内在后台跑的 `unit-r4-20260909T220000.txt`（`164 failed, 4763 passed`）测的是损坏中间态，**已改名 `VOID-` 并在文件内追加作废声明，不作为任何判据**。重跑见 `unit-r5-*.txt`。

**r3 关注点 (a) 的自查**（存档 `selfcheck-r3a-20260909T200000.txt`）：单跑 3 次全绿；`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`（新用例不碰 Neo4j）；tracked 文件 0 改动；`gemini_client=None` 且无未关闭资源告警。⚠️ Codex 明确保留 (a) 为「未完整核验」——它的读取面不含构造器与完整 health 方法，故**不授予**「无副作用 / CI 无配置稳定」结论；本卡也不宣称，见 §五⑬。
