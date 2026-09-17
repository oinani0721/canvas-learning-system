# PYRIGHT-TAIL census —— U1/U2 清不掉的 pyright 存量逐条登记

> 卡：`CARD-PYRIGHT-TAIL`　批次：`[BATCH-2026-09-11-第十四批 / CARD-PYRIGHT-TAIL]`　车道：`card-t8-tools`（分支 `card/t8-tools`）
> 基准：`BASE_F` = `f493a4e170a88b5eb2c4af05b275055d005adfe9`（前一卡 T8-E `CARD-TOOLCHAIN-UNIFY` 末 commit）
> pyright 口径：`P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright`（实测 `1.1.411`），一律 `( cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' )`（R-B14-10；⛔ 禁 `| tail -1`）
> 常驻硬门实测：**改前 `0 errors, 81 warnings, 0 informations`　→　改后 `0 errors, 80 warnings, 0 informations`**（差额 1 = 本卡清掉的那条冗余 ignore）
> 全部 `file:line` 为本卡在 `BASE_F` 树上 `grep -n` / `sed -n` **实测**；与勘探稿/设计稿不符处已在「口径更正」节逐条列出。

---

## 一 列的定义（U1 §十六.2 第 3 条方法论回写落地）

U1 §十六.2 指出旧「死路径」定义把「无调用」与「无测试覆盖」混成一个「或·和」歧义判据。本表**拆成两列**，各自独立可判：

- **生产侧使用点**：在 `backend/app/**` 内该 TAIL 项被使用的次数。⛔ **口径不是单一的**，每个单元格必须自带口径标签，否则数字之间不可比（Codex round-1 MEDIUM-1 更正）：
  - `调用式` —— 用精确调用式（如 `.foo(`）计，已排除定义处；这是最强口径，本表只有 F-3 一行达到（实测 **0**）。
  - `混合命中` —— 裸名 / `import` 语句 / 注释三者的 `grep -rF` 合计命中数，**未拆分**。对「死 import」类项（T1 / T-new-3 / T-new-8）而言 `import` 本身就是使用点，拆不出「调用数」，故只能给混合数并在括号里注明构成。
  - `定性` —— 未取数，只给性质（如 T3 的「活端点内含死分支」）。这类单元格**没有数字**，本表不假装有。
- **测试覆盖**：在 `backend/tests/**` 内出现该符号的 `grep -rF` 命中数（同样是**混合命中**，不是「执行到缺陷行的用例数」）。⚠️ 命中 ≠ 覆盖到缺陷行——mock 掉被测对象的用例会命中符号却永不执行缺陷分支。部分行只写「有」= 定性未取数。
- ⛔ **本表没有任何一行是「双零」**（两列都实测为 0）。初版 §一 定义了「双零」这个词但表里无一行满足，容易让读者以为存在「已证死透」的条目——该词已作废，不再使用。
- ⛔ **上述任何一列为 0 都不等于「不可达」**：grep + AST 覆盖不到别名取用 / 回调注册 / 字符串反射 / 路由注入等动态路径，本表一律写「未发现直接生产调用 / 动态可达性未证」而非「零曝光」（M-2 裁定口径）。

**处置四档**：`本批改(T8-F)` / `本批其他卡` / `第十五批立卡` / `只登记`。

---

## 二 本批改 —— T8-F 本卡实改（5 个文件）

| 编号 | 文件:行（实测） | 性质 | 生产侧使用点（口径） | 测试覆盖（混合命中） | 处置 |
|---|---|---|---|---|---|
| F-1 | `pyrightconfig.json:4`（`include` 的 `"src"` 条目）+ `:48` 旧注释 | 死配置：`git ls-files src` = **0**，该 include 项匹配 0 文件 | — | — | **本批改(T8-F)** ✅ 已删 `include` 里的 src 条目 + `:48` 注释改为「已清除」。移除后 pyright 分析文件数**实测不变**（受控两跑 `filesAnalyzed` 均 **305**，含控制组，见 §十.2）⇒ `app` 仍 0 errors |
| F-2 | `backend/app/dependencies.py:1035`（行尾 `# pyright: ignore[reportArgumentType]`）+ `:1031-1033` 陈旧注释块 | 冗余 ignore：U1 已把 `canvas_service.py:69` 改成 `canvas_base_path: Optional[str] = None`，该 ignore 随即被 pyright 自曝 | — | — | **本批改(T8-F)** ✅ 先红自证 `:1035:63 - warning: Unnecessary "# pyright: ignore" rule: "reportArgumentType" (reportUnnecessaryTypeIgnoreComment)` = 1 → 删后 = 0，`app` warnings 81→80 |
| F-3 | `backend/app/services/review_service.py:1240` 与 `:2135-2136` | 注释过宽断言（U1 §二十.2 M-2）：原写「生产零调用方」「传递性零曝光」 `调用式` **0** —— `.generate_verification_canvas(` 在 `backend/app` 的唯二命中是 `dependencies.py:301` 的 docstring 示例块 + 本条注释自身 | `backend/tests` 命中 **15**（全为 mock 用例） | **本批改(T8-F)** ✅ 改为「未发现直接生产调用(grep + AST 口径), 动态可达性未证」/「传递性曝光面同样未证(不等于零曝光)」 |
| F-4 | `backend/app/services/canvas_service.py:341` | 注释断言不成立（U1 §二十.2 L-1）：原写「落地路径逐字不变」 | `_trigger_memory_event(:264)` 在 `_memory_client is None` 时提前 return ⇒ `:342` 的 assert 生产不可达 | — | **本批改(T8-F)** ✅ 改为「走同一 fallback 分支; 但 assert 无消息 ⇒ `f"...: {e}"` 的原因文本会变空, 非逐字不变(生产不可达, 仅影响日志文本)」 |
| F-5 | `backend/app/services/exam_service.py:80-82`（改后 `:80-85`） | 注释挂载点不精确（U2 r3 L1）：原写「由 exam_service_ext.py **模块顶层的猴子补丁挂载**」 | 实测赋值在 `exam_service_ext.py` 的 `attach_to_exam_service()` **函数体内**（`:956-966`，def `:932`），由该模块顶层 `:970` 的调用执行 | — | **本批改(T8-F)** ✅ 改为函数体内 + 顶层调用的准确表述，并附一句 D-29 crossover 说明 |
| F-6 | `backend/app/services/multimodal_service.py:310` `img.thumbnail((100, 100), Image.Resampling.LANCZOS)` | L-3：commit message 里「Pillow 9.1 起弃用」的说法应更正（Pillow 9.4 已**撤销** `Image.LANCZOS` 的弃用，本次替换是为对齐 type stub 的等值替换） `混合命中` **1**（该行本身） | **0** | **只登记（本卡零代码改动）**：该行**无代码注释可改**（`:318-319` 只是 "Pillow not installed" 日志串），commit message 是不可变历史 ⇒ 仅在本 census 更正事实，**不改任何代码行** |

> **非注释行改动的完整清单（⛔ 取值面必须写明，Codex round-1 LOW-1 更正）**：跨全部 5 个文件的 `diff -U0` 里，非注释 `+`/`-` 行共 **3** 行 —— ① `dependencies.py` 的 `canvas_base_path=canvas_base_path,` 一删一增（`-` 带行尾 ignore / `+` 不带，代码本体逐字相同，计 2 行）；② `pyrightconfig.json` 里被删掉的那一行 include 条目（JSON 数据行，计 1 行，即本卡 F-1 的正题）。
> 卡文 §二 step 10 的机械判据把取值面**限定在 4 个 `.py` 文件**（pathspec 不含 `pyrightconfig.json`），在那个面上是 **恰 2 行** —— 两个数字都对，差别只在取值面。本 census 初版把「全部 +/- 行均为注释行」写在 F-1~F-5 的标题下却用了 4 文件面的数字，是**取值面与主张不一致**，已更正。三个 `services` 文件与 `exam_service.py` 的改动确实 **100% 是 `#` 注释行**。满足裁定 **R-B14-4** 的附加约束「只准增删 `# pyright: ignore[...]` 注解与注释行，禁改任何语义行」。机械自证见验收单 step 10。

---

## 三 本批其他卡接手（本卡只注明归属，一行不改）

| 编号 | 文件 | 性质 | 处置 |
|---|---|---|---|
| T-new-4 | `backend/app/core/background_task_manager.py`（`TASK_CLEANUP`） | 行为面 | **本批其他卡 → T5-A** |
| T-EDGES | `backend/app/api/v1/endpoints/edges.py` | 行为面 | **本批其他卡 → T5-B** |
| T-SWITCHVAULT | `backend/app/mcp/infra_tools.py` | 行为面 | **本批其他卡 → T5-C** |
| T-UNREACH | `backend/app/api/v1/endpoints/boards.py` / `board_manifest_tools.py` | 死分支 | **本批其他卡 → T5-E**（已于 2026-09-17 收官，终审 `802f05ca`） |

---

## 四 第十五批立卡（行为变化项，D-35：本卡只登记不改）

| 编号 | 文件:行（实测） | 性质 | 生产侧使用点（口径） | 测试覆盖（混合命中） | 处置 |
|---|---|---|---|---|---|
| T1 | `backend/app/services/rollback_service.py:124` / `:298` / `:361`（三处 `# pyright: ignore[reportMissingImports]`，注释 `:121`/`:295`/`:358`） | `from src.rollback import ...`；`git ls-files src` = **0** ⇒ 运行期恒 `ImportError`、端点恒 503 `混合命中` **4**（3 个 `import` + 1 条注释；死 import 类，拆不出「调用数」） | **0** | **第十五批立卡 `CARD-T1-ROLLBACK-RETIRE`**：保留（补实现）还是退役（删端点）= 产品裁定 |
| T3 | `backend/app/api/v1/endpoints/review.py:255`（死 import）+ `:191` / `:427`（`GeminiClient(model=)` 的 `# pyright: ignore[reportCallIssue]`） | 活/死混合面：注释 `:248` 明写「单修本行会激活死码, 随即撞该函数里 `GeminiClient(model=)` 的 TypeError」 `定性`：活端点内含死分支，未取数 | `定性`：有端点级用例，但不覆盖死分支 | **第十五批立卡 `CARD-T3-REVIEW-DEADCODE`**：修 = 激活死码 + 改行为 |
| T-new-1 | `backend/app/services/wikilink_graph_service.py:325`（注释 `:321-322`） | `self._vault.get_source_path(...)` 恒 `AttributeError`，被 `except Exception` 静默降级 `混合命中` **2**（1 调用 + 1 注释） | **1** | **第十五批立卡**（行为变化：补真实取路径 = 改降级行为） |
| T-new-2 | `backend/app/services/error_classifier.py:202`（`created_at=` 的 `# pyright: ignore[reportCallIssue]`，注释 `:197-201`） | `Misconception` 在 P0-4 已把字段改名 `misconception_created_at`，本处仍传旧名；pydantic `extra='ignore'` ⇒ 传入值被**静默丢弃**、回落 `default_factory` `混合命中` **1** | `定性`：有 | **第十五批立卡**（改参数名 = 行为变化，D-35） |
| T-new-3 | `backend/app/services/agent_routing_engine.py:559`（注释 `:555-556`） | `from app.core.litellm_config import get_litellm_config` 恒 `ImportError` ⇒ 降级写死模型 `混合命中` **3**（import + 调用 + 注释，无定义处） | **0** | **第十五批立卡**（补实现 = 改选模型行为） |
| T-new-5 | `backend/app/services/batch_orchestrator.py:506` 与 `:569`（两处 `# pyright: ignore[reportArgumentType]`） | `CancelledError` 被当业务结果追加进结果列表 `混合命中` **2** | `定性`：有 | **第十五批立卡**（改 = 改失败语义） |
| T-new-6 | `backend/app/services/intelligent_parallel_service.py:652`（注释 `:647`；同族 `:659`） | `agent_type=` 传 str 未转换 `混合命中` **1** | `定性`：有 | **第十五批立卡**（加转换 = 行为变化） |
| T-new-7 | `backend/app/services/learning_context_service.py:205`（`# pyright: ignore[reportCallIssue]`，注释 `:199`） | ⛔ **活路径**：`search_memories(node_id=..., limit=...)` 缺必填 `query` ⇒ 恒 `TypeError`，被 `except` 接住只记 debug ⇒ **该数据源从未供过数据** `定性`：**活路径** —— `exam_quick.py:116` → `_fetch_tips_and_errors(:121)` → 本行；另 `learning_context_service.py:320` 亦入 | **2** | **第十五批立卡（优先级最高）**：补 `query=` = 改出题输入 ⇒ 须产品裁定 |
| T-new-8 | `backend/app/services/multimodal_service.py:1427`（`# pyright: ignore[reportMissingImports]`，注释 `:1424`） | `from agentic_rag.embedding.embedding_service import ...`；`backend/lib/agentic_rag/` 下无 `embedding` 子包（`extraPaths` 也解不了）⇒ 运行期恒走 `except ImportError`、**向量搜索永久关闭恒降级文本搜索** `混合命中` **1**（死 import 本身） | **0** | **第十五批立卡**（退役该分支或补实现；G-PIPE 同族） |
| T14 | `backend/app/clients/provider_factory.py:260` / `:265`（注释 `:256-259`） | `config.py` 无 `OPENAI_API_KEY` 字段 + `extra="ignore"` ⇒ `hasattr` 恒 False、**openai 分支恒不激活** `混合命中` **7**（含 `:210` 的 `getattr` 默认空串路径） | **3** | **第十五批立卡**（加字段 = 行为变化，D-35） |

---

## 五 只登记（类型例外 / 非本卡面）

| 编号 | 位置（实测） | 性质 | 处置 |
|---|---|---|---|
| T6 | `backend/app/core/exception_handlers.py:309-311`（`cast(ExceptionHandler, ...)` ×3，注释 `:306-308`） | starlette stub 逆变导致的类型层 cast，**零行为** | **只登记·类型例外**（R-10 接受 C-6） |
| T8 | `backend/app/clients/neo4j_client.py:616`（`cast(LiteralString, query)`，注释 `:613`） | 防 f-string 注入的类型层 cast，**零行为** | **只登记·类型例外**（R-10 接受 C-6） |
| T10 | `backend/lib/**`（`pyrightconfig.json` 的 `extraPaths: ["backend/lib"]`）—— `LanceDBClient` 无 `delete` / `upsert` / `get_db` | lib 侧存量，不在 `include` 的 `backend/app` 面 | **只登记**（本卡未重测；lib 侧收敛另立卡） |
| T11 | `backend/tests/**` 与仓根 `tests/**` 的 pyright 存量（U2 §五 登记口径：`backend/tests` 1350 错 / 仓根 `tests/` 168 错） | 测试面存量 | **只登记**：⛔ **本卡未在本批重测**，沿用 U2 口径；`"$P" tests` 不是本卡硬门 |
| T-GATE-GAP | 方法论（U2 §五） | 「绑定位置改变语义不在任何自动门覆盖面」= 门设计面 | **只登记** → 归协议 / T8-G / 第十五批 |

---

## 六 本卡新发现（登记，不改 —— 不在卡文 §〇 授权的三处之列）

| 编号 | 位置（实测） | 性质 | 为什么本卡不改 | 处置 |
|---|---|---|---|---|
| **T-new-9** | `backend/app/services/exam_service.py:553-556`（改后 `:556-559`）：「作用是执行 exam_service_ext **模块顶层的** `ExamService.<name> = <fn>` 猴子补丁挂载」 | 与 F-5 **同型**的不精确措辞（赋值实际在 `attach_to_exam_service()` 函数体内）。因原串被换行切断，`grep -cF '模块顶层的猴子补丁挂载'` 命中不到它（改前该判据 = 1，只命中 `:80`） | 卡文 §三 明列 `exam_service.py`「**只改 `:80-81`**」，且 §三 禁改 `:556` 副作用 import 一带 ⇒ 改它属越界 | **只登记** → 建议并入第十五批「注释措辞收敛」卡，或由主 session 补裁扩面 |
| **T-new-10** | 注释/文档里的 `file:line` 引用**成批漂移**（U1/U2 阶段 2 合入后）：`review_service.py:1238` 写 `canvas_service.py:616` → 实测 `read_canvas` 在 **:620**；`:1239` 写「首个 try 在 `:1249` 之后」→ 实测首个 `try:` 在 **:1255**；`:2139` 写「只留 2138 或只留 2141」→ 实测 4 个 kwarg ignore 在 **:2142-2145**；`question_generator.py:208` 写 `canvas_service.py:598` → 实测 `asyncio.Semaphore` 在 **:567**；`docs/stories/33.9.story.md:30` 写 `dependencies.py:1064-1127` → 该符号**已整段删除**；`docs/.../14-scheme-a-implementation-prd.md:1917` 写 `exam_service.py:69-83` = `create_session` → 实测 `:69-83` 是类文档串 + `TYPE_CHECKING` 块 | 这些引用**没有任何自动门**看守（T-GATE-GAP 同族）：合并一次就集体失实，而所有判据都绿 | ① `question_generator.py` 不在本卡地盘；② `:1238`/`:1239`/`:2139` 不在卡文授权的两处（`:1240`/`:2135`）之列；③ PRD 是只读锚定文档 | **只登记** → 建议第十五批立 `CARD-COMMENT-LINEREF-GATE`（门设计面，可做成「注释里的 `file.py:NNN` 必须能解析到同名符号」的静态门） |

> 本卡对自己动过的两处**主动做了收敛**：`review_service.py:2135` 原写 `generate_verification_canvas(:1371)`（实测 def 在 `:1197`、调用在 `:1377`，两头都不是 1371）⇒ 改写该行时**去掉了这个已失实的数字**、改用符号名 `generate_verification_canvas()`；`canvas_service.py` 与 `review_service.py` 的改动均**逐行等量替换**（`numstat` 实测 `1 1` 与 `3 3`）以**不让本卡自己制造新的行号漂移**（`canvas_service.py` 的 `read_canvas` 仍在 `:620`、`asyncio.Semaphore` 仍在 `:567`，实测复核过）。

---

## 七 U1 §十六.2 三条方法论回写 —— 本批落地口径

| # | U1 原始发现 | 本批落地 |
|---|---|---|
| 1 | `PHASE0_PENDING` 启发式（`"missing for parameter" in message`）会把**真缺陷**误豁免 | **本批不再使用该过滤器**。pyright 判据一律 `( cd backend && "$P" app 2>&1 \| grep -E '^[0-9]+ errors?, ' )` 全量、无豁免（本卡 (b)/(k) 即此形态） |
| 2 | 用 `\| tail -1` 取汇总行会取到升级提示行（pyright 1.1.411 末行是 `v1.1.411 -> v1.1.414`） | **⛔ 禁 `\| tail -1`**，一律 `grep -E '^[0-9]+ errors?, '` 锚汇总行本身（结构锚，不是位置锚） |
| 3 | 「死路径」定义里「无调用」与「无测试覆盖」的「或·和」歧义 | 本 census **拆两列**（§一），并显式声明两列都不蕴含「不可达」（动态可达性未证） |

> 三条的**协议层**回写（写进 `card-batch-protocol.md`）不在本卡面 ⇒ 归 **T8-G / 第十五批**。

---

## 八 口径更正（勘探/设计稿 → 本卡实测）

| 项 | 勘探/设计稿 | 本卡实测 |
|---|---|---|
| `dependencies.py` 冗余 ignore | `:1032` | **`:1035`**（注释块 `:1031-1033`） |
| `review_service.py` 第二处注释 | `:2136` | **`:2135`** |
| `exam_service_ext.py` 赋值 / 调用 | 赋值 `:947-957` / 调用 `:961` | **赋值 `:956-966` / 调用 `:970`**（def `:932`） |
| `provider_factory.py` | 裸名「`:256/:261`」 | 路径 **`backend/app/clients/provider_factory.py`**，ignore 在 **`:260` / `:265`** |
| `review.py` GeminiClient ignore | `:238` | **`:191` / `:427`**（死 import 在 `:255`） |
| pyright 基线 | `recon_C §8` 的 420 errors（`286178d8`，U1/U2 阶段 2 未合） | **`B14_BASE` = 0 errors, 81 warnings**（U1 `622f3a5d` + U2 `b4705dde` 合入后） |
| `grep -cF '"src"' pyrightconfig.json` 改前值 | 卡文早期写 1 | **实测 2**（`:4` include 条目 + `:48` 旧注释里逐字引用），承重判据改用 include 面 `sed -n '/"include"/,/]/p' \| grep -cF` = 1（对行号漂移免疫） |
| git pathspec | `'backend/app/**/*.py'` | **实测对顶层 `backend/app/*.py` 零覆盖**（git 的 `*` 跨 `/`），一律写 `'backend/app/*.py'` |

---

## 九 本卡未证明什么

1. 未证明被判「第十五批立卡」的 T-new-1/2/3/5/6/7/8、T1、T3、T14 的**具体修法正确**——本卡只登记处置，一行代码不改。
2. 未重测 **T11**（`backend/tests` + 仓根 `tests/` 的 pyright 存量），沿用 U2 §五登记口径；本批**未跑** `"$P" tests`。
3. ~~未证明删 `dependencies.py:1035` 的 ignore 后在其他 include 面无连带 error~~ —— **已于 Codex round-1 后实测关闭（仅限 include 面）**：全 include 面（305 文件）上 BASE_F 版 `165 errors, 82 warnings` vs 本卡版 `165 errors, 81 warnings`，**errors 一条未增**（见 §十.3）。⛔ **仍未证明**的是 `backend/tests`（509 个 `.py`）——实测它**根本不在 `pyrightconfig.json` 的 include 面内**（`include` 的 `tests` 相对仓根解析 = 仓根 `tests/` 的 41 个文件；`305 − 264 = 41` 恰好对上），这一面本卡既没测、也不在该配置的覆盖范围。
4. 未证明 `exam_service.py` 的 `if TYPE_CHECKING` 块内 11 个方法声明与 `exam_service_ext.py` 的真实 `def` **逐字签名一致**（那是 U1 面；本卡只改挂载点措辞）。
5. census 的「生产调用方 = 0」基于 **grep + AST 口径**，覆盖不到别名取用 / 回调注册 / 字符串反射 / 路由注入等动态可达路径 ⇒ 一律只能说「未发现直接生产调用」，**不能说「零曝光」**。
6. 未证明 F-6（`multimodal_service.py` Pillow）的 **commit message 历史更正**对任何读者已生效——commit message 不可变，本卡只在本 census 登记事实。
7. 未证明 `pyrightconfig.json` 的 `exclude` / `extraPaths` / 各 `report*` 键里**没有别的死枝**——本卡只清 `include` 的一处，其余配置面未逐键复核。
8. 未证明「测试覆盖」列的命中数等于**真覆盖到缺陷行**——`generate_verification_canvas` 的 15 处 tests 命中全为 mock 用例，是否执行到 `:1243` 的 `get_canvas` 崩溃行未逐条验。

---

## 十 Codex round-1 之后的复核与实测（本节全部为 `_bmad-output` 改动，不动代码 ⇒ 终审绑定 `bcd487db` 不破）

Codex（`gpt-6-astra` · `ultra`）round-1 绑定 `bcd487db`：**BLOCKER 0 / HIGH 0** / MEDIUM 3 / LOW 1。按协议 §1，MEDIUM / LOW **登记不阻断**。逐条处置如下。

### 十.1 LOW-1（census 的非注释行计数）—— ✅ 采纳并更正

Codex 指出全 diff 的非注释增删行是 **3** 行而非 2 行（多出 `pyrightconfig.json` 里被删的那行 include 条目）。**复核属实**：本 census 初版把「4 个 `.py` 文件面」的数字（恰 2）写在了「F-1~F-5」这个更宽的标题下 —— 是**取值面与主张不一致**，不是数字算错。§二 末尾已改为完整清单并写明两个取值面各自的数字。

### 十.2 MEDIUM-3（`git ls-files` 不足以证明分析文件集不变）—— ✅ 采纳，并用直接实测关闭

Codex 说得对：`git ls-files src` = 0 只覆盖**受跟踪**文件，证不了未跟踪/被忽略的目录不存在，更证不了 pyright 的分析文件集不变。本卡补了三层证据：

1. **文件系统层**：`ls -d ./src` rc=**1**（仓根该目录根本不存在）；验伪锚 `ls -d ./backend` rc=**0**（证该判据非恒 1）。深度 ≤2 的同名目录只有 `./frontend/src`（前端 TS 目录），而 pyright 的 `include` **相对配置文件所在目录（仓根）解析**，取不到它。
2. **受控两跑**（用本卡 (h) 同款安全模式：临时改配置 → 跑 → `git show HEAD:` + `cp` 还原，⛔ 禁 `git checkout` / `git stash`；还原后 `shasum` 逐字相同、`git status --porcelain -uno` = 0）：

   | 配置 | include | `filesAnalyzed` | 汇总行 |
   |---|---|---|---|
   | 本卡版 | `["backend/app","tests"]` | **305** | `165 errors, 81 warnings` |
   | BASE_F 等价 | `["backend/app","src","tests"]` | **305** | `165 errors, 81 warnings` |

   ⇒ `src` 条目贡献 **0** 个文件。
3. ⛔ **控制组**（否则「两侧都是 305」也可能只说明配置压根没被读）：临时把 `tests` 也去掉 → `filesAnalyzed` = **264** ≠ 305 ⇒ `include` 数组**确实驱动**分析集，上表的「相同」是真结论。

> ⛔ **作废声明**：本项第一次尝试是在 scratchpad 里造两份 `include` 用**绝对路径**的探针配置，两侧 `filesAnalyzed` 都得 **0**。那**不是**「没变化」而是**没跑成** —— pyright 明确报 `Ignoring path "..." because it is not relative`，绝对路径被整条忽略。该次结果已作废、不作任何依据。（顺带实证了 pyright 这些路径数组只接受相对路径，也就坐实了第 1 点里「`include` 相对仓根解析」这个前提。）

### 十.3 Codex 问题①（删 ignore 后别处会不会新冒 error）—— ✅ 在 include 面上实测关闭，`backend/tests` 如实留空

同款安全模式，只把 `dependencies.py` 在 BASE_F 版与本卡版之间切换，跑**不带 path 参数**的全 include 面：

| `dependencies.py` 版本 | 全 include 面（305 文件）汇总 |
|---|---|
| BASE_F（ignore 还在） | **`165 errors, 82 warnings`** |
| 本卡版（ignore 已删） | **`165 errors, 81 warnings`** |

⇒ **errors 一条未增**（165 → 165），warnings 恰少 1 = 被清的那条冗余 ignore。还原后 `shasum` 与 `HEAD` 版一致、工作树干净。

⛔ 取值面必须写明：`pyrightconfig.json` 的 `include` 里那个 `tests` 是**仓根 `tests/`**（41 个 `.py`），**`backend/tests`（509 个 `.py`）根本不在 include 面内**。所以本条关闭的是「include 面无新 error」；`backend/tests` 那一面本卡**既没测、也不在该配置的覆盖范围**——它只有在有人把路径显式传给 pyright 时才会被分析。该项留在 §九。

### 十.4 MEDIUM-2（新注释仍有超出证据的结论）—— ⚠️ **登记不改**

Codex 指出两处：`exam_service.py` 的「文件内无读 logging 代码 ⇒ 无业务回归」，以及 `canvas_service.py:341` 的「生产不可达」未限定到所述的上游 guard 调用链。**这个批评在类型上成立** —— 「文件内没有读 X」推不出「无业务回归」（模块外仍可能有属性消费者）；「生产不可达」也该写成「经所述上游调用链不可达，动态入口未证」。

**本卡不改，理由三条**：

1. 这两段措辞是**卡文 §一(e) 逐字规定的新措辞**（分别源自 U2 r3 L1 与 U1 §二十.2 L-1 的裁定原文），不是本车道自拟；改它等于偏离卡文规定的交付内容。
2. 协议 §1 对 **MEDIUM 是「登记不阻断」**，且 D-15 已在 round-1 达成（绑最终 HEAD 且 B/H = 0）。改代码注释会打破 `bcd487db` 的字节级绑定 = 自己给自己制造一次额外轮次。
3. 这恰好就是本 census §六 T-new-9 / T-new-10 想说的同一件事：**注释里的断言强度本身缺一道门**。合适的落点是第十五批的措辞收敛卡 + 门设计，不是在本卡里再手改两行。

⇒ 登记进台账，并请主 session 在下一张同族卡的卡文里把这两句的**规定措辞**一并收紧（源头在裁定原文，不在车道）。

### 十.5 Codex 对其余问题的裁定（摘录，供主 session 复核）

- **⓪ 活路径延期**：未发现「本批必须修却漏修」的证据；T-new-7 的延期依据是行为变化需裁定，不是误判为死路径。两列零计数本身也不能排除别名 / 回调 / 反射 / 路由注入。
- **① ignore 与门覆盖**：逐条比对留存日志后，除正常行号移动外**唯一消失的诊断就是目标冗余 ignore**；确为 `0 errors／81 warnings → 0 errors／80 warnings`。
- **④ T-new-9 / T-new-10 登记不改**：按 census 引述的行级授权，理由成立；但原卡 §〇/§三 不在允许读取面内，故授权条款本身未获独立确认。
- **⑤ 等量替换**：**属实** —— `canvas_service.py` = 1/1、`review_service.py` = 3/3，且各差异块分别等量，确实没有移动这两个文件其余内容的行号。
