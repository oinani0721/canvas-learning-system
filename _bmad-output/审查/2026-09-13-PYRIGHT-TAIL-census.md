# PYRIGHT-TAIL census —— U1/U2 清不掉的 pyright 存量逐条登记

> 卡：`CARD-PYRIGHT-TAIL`　批次：`[BATCH-2026-09-11-第十四批 / CARD-PYRIGHT-TAIL]`　车道：`card-t8-tools`（分支 `card/t8-tools`）
> 基准：`BASE_F` = `f493a4e170a88b5eb2c4af05b275055d005adfe9`（前一卡 T8-E `CARD-TOOLCHAIN-UNIFY` 末 commit）
> pyright 口径：`P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright`（实测 `1.1.411`），一律 `( cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' )`（R-B14-10；⛔ 禁 `| tail -1`）
> 常驻硬门实测：**改前 `0 errors, 81 warnings, 0 informations`　→　改后 `0 errors, 80 warnings, 0 informations`**（差额 1 = 本卡清掉的那条冗余 ignore）
> 全部 `file:line` 为本卡在 `BASE_F` 树上 `grep -n` / `sed -n` **实测**；与勘探稿/设计稿不符处已在「口径更正」节逐条列出。

---

## 一 列的定义（U1 §十六.2 第 3 条方法论回写落地）

U1 §十六.2 指出旧「死路径」定义把「无调用」与「无测试覆盖」混成一个「或·和」歧义判据。本表**拆成两列**，各自独立可判：

- **生产调用方**：在 `backend/app/**` 内，除定义处与注释外，该符号被**实际调用**的次数（用精确调用式如 `.foo(` 计，不用裸名计；裸名会把 docstring/同名端点自建实现算进来）。
- **测试覆盖**：在 `backend/tests/**` 内出现该符号的命中数。⚠️ 命中 ≠ 覆盖到该缺陷行——mock 掉被测对象的测试会命中符号却永不执行缺陷分支（本表在备注里如实标注）。
- 两列都为 0 ⇒ 「双零」；只有生产调用方为 0 ⇒ 「生产未发现直接调用」。⛔ **两者都不等于「不可达」**：grep + AST 覆盖不到别名取用 / 回调注册 / 字符串反射 / 路由注入等动态路径，本表一律写「动态可达性未证」而非「零曝光」（M-2 裁定口径）。

**处置四档**：`本批改(T8-F)` / `本批其他卡` / `第十五批立卡` / `只登记`。

---

## 二 本批改 —— T8-F 本卡实改（5 个文件）

| 编号 | 文件:行（实测） | 性质 | 生产调用方 | 测试覆盖 | 处置 |
|---|---|---|---|---|---|
| F-1 | `pyrightconfig.json:4`（`include` 的 `"src"` 条目）+ `:48` 旧注释 | 死配置：`git ls-files src` = **0**，该 include 项匹配 0 文件 | — | — | **本批改(T8-F)** ✅ 已删 `include` 里的 src 条目 + `:48` 注释改为「已清除」。移除后 pyright 分析文件数不变 ⇒ `app` 仍 0 errors |
| F-2 | `backend/app/dependencies.py:1035`（行尾 `# pyright: ignore[reportArgumentType]`）+ `:1031-1033` 陈旧注释块 | 冗余 ignore：U1 已把 `canvas_service.py:69` 改成 `canvas_base_path: Optional[str] = None`，该 ignore 随即被 pyright 自曝 | — | — | **本批改(T8-F)** ✅ 先红自证 `:1035:63 - warning: Unnecessary "# pyright: ignore" rule: "reportArgumentType" (reportUnnecessaryTypeIgnoreComment)` = 1 → 删后 = 0，`app` warnings 81→80 |
| F-3 | `backend/app/services/review_service.py:1240` 与 `:2135-2136` | 注释过宽断言（U1 §二十.2 M-2）：原写「生产零调用方」「传递性零曝光」 | `.generate_verification_canvas(` 在 `backend/app` 实测 **0 个真实调用点**（唯二命中：`dependencies.py:301` 的 docstring 示例块 + 本条注释自身） | `backend/tests` 命中 **15**（全为 mock 用例） | **本批改(T8-F)** ✅ 改为「未发现直接生产调用(grep + AST 口径), 动态可达性未证」/「传递性曝光面同样未证(不等于零曝光)」 |
| F-4 | `backend/app/services/canvas_service.py:341` | 注释断言不成立（U1 §二十.2 L-1）：原写「落地路径逐字不变」 | `_trigger_memory_event(:264)` 在 `_memory_client is None` 时提前 return ⇒ `:342` 的 assert 生产不可达 | — | **本批改(T8-F)** ✅ 改为「走同一 fallback 分支; 但 assert 无消息 ⇒ `f"...: {e}"` 的原因文本会变空, 非逐字不变(生产不可达, 仅影响日志文本)」 |
| F-5 | `backend/app/services/exam_service.py:80-82`（改后 `:80-85`） | 注释挂载点不精确（U2 r3 L1）：原写「由 exam_service_ext.py **模块顶层的猴子补丁挂载**」 | 实测赋值在 `exam_service_ext.py` 的 `attach_to_exam_service()` **函数体内**（`:956-966`，def `:932`），由该模块顶层 `:970` 的调用执行 | — | **本批改(T8-F)** ✅ 改为函数体内 + 顶层调用的准确表述，并附一句 D-29 crossover 说明 |
| F-6 | `backend/app/services/multimodal_service.py:310` `img.thumbnail((100, 100), Image.Resampling.LANCZOS)` | L-3：commit message 里「Pillow 9.1 起弃用」的说法应更正（Pillow 9.4 已**撤销** `Image.LANCZOS` 的弃用，本次替换是为对齐 type stub 的等值替换） | 1（该行本身） | 0 | **只登记（本卡零代码改动）**：该行**无代码注释可改**（`:318-319` 只是 "Pillow not installed" 日志串），commit message 是不可变历史 ⇒ 仅在本 census 更正事实，**不改任何代码行** |

> F-1~F-5 的全部 `+`/`-` 行均为 `#` / `//` 注释行，**唯一**的非注释行改动是 `dependencies.py` 的 `canvas_base_path=canvas_base_path,`（`-` 带行尾 ignore / `+` 不带，代码本体逐字相同）—— 满足裁定 **R-B14-4** 的附加约束「只准增删 `# pyright: ignore[...]` 注解与注释行，禁改任何语义行」。机械自证见验收单 step 10。

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

| 编号 | 文件:行（实测） | 性质 | 生产调用方 | 测试覆盖 | 处置 |
|---|---|---|---|---|---|
| T1 | `backend/app/services/rollback_service.py:124` / `:298` / `:361`（三处 `# pyright: ignore[reportMissingImports]`，注释 `:121`/`:295`/`:358`） | `from src.rollback import ...`；`git ls-files src` = **0** ⇒ 运行期恒 `ImportError`、端点恒 503 | `from src.rollback` 在 `backend/app` 命中 **4**（3 个 import + 1 条注释），无任何可成功的导入 | **0** | **第十五批立卡 `CARD-T1-ROLLBACK-RETIRE`**：保留（补实现）还是退役（删端点）= 产品裁定 |
| T3 | `backend/app/api/v1/endpoints/review.py:255`（死 import）+ `:191` / `:427`（`GeminiClient(model=)` 的 `# pyright: ignore[reportCallIssue]`） | 活/死混合面：注释 `:248` 明写「单修本行会激活死码, 随即撞该函数里 `GeminiClient(model=)` 的 TypeError」 | 混合（活端点内含死分支） | 有（端点级用例，但不覆盖死分支） | **第十五批立卡 `CARD-T3-REVIEW-DEADCODE`**：修 = 激活死码 + 改行为 |
| T-new-1 | `backend/app/services/wikilink_graph_service.py:325`（注释 `:321-322`） | `self._vault.get_source_path(...)` 恒 `AttributeError`，被 `except Exception` 静默降级 | `get_source_path` 在 `backend/app` 命中 **2**（1 调用 + 1 注释） | **1** | **第十五批立卡**（行为变化：补真实取路径 = 改降级行为） |
| T-new-2 | `backend/app/services/error_classifier.py:202`（`created_at=` 的 `# pyright: ignore[reportCallIssue]`，注释 `:197-201`） | `Misconception` 在 P0-4 已把字段改名 `misconception_created_at`，本处仍传旧名；pydantic `extra='ignore'` ⇒ 传入值被**静默丢弃**、回落 `default_factory` | 1 | 有 | **第十五批立卡**（改参数名 = 行为变化，D-35） |
| T-new-3 | `backend/app/services/agent_routing_engine.py:559`（注释 `:555-556`） | `from app.core.litellm_config import get_litellm_config` 恒 `ImportError` ⇒ 降级写死模型 | `get_litellm_config` 在 `backend/app` 命中 **3**（import + 调用 + 注释），无定义处 | **0** | **第十五批立卡**（补实现 = 改选模型行为） |
| T-new-5 | `backend/app/services/batch_orchestrator.py:506` 与 `:569`（两处 `# pyright: ignore[reportArgumentType]`） | `CancelledError` 被当业务结果追加进结果列表 | 2 | 有 | **第十五批立卡**（改 = 改失败语义） |
| T-new-6 | `backend/app/services/intelligent_parallel_service.py:652`（注释 `:647`；同族 `:659`） | `agent_type=` 传 str 未转换 | 1 | 有 | **第十五批立卡**（加转换 = 行为变化） |
| T-new-7 | `backend/app/services/learning_context_service.py:205`（`# pyright: ignore[reportCallIssue]`，注释 `:199`） | ⛔ **活路径**：`search_memories(node_id=..., limit=...)` 缺必填 `query` ⇒ 恒 `TypeError`，被 `except` 接住只记 debug ⇒ **该数据源从未供过数据** | **活**：`exam_quick.py:116` → `_fetch_tips_and_errors(:121)` → 本行；另 `learning_context_service.py:320` 亦入 | **2** | **第十五批立卡（优先级最高）**：补 `query=` = 改出题输入 ⇒ 须产品裁定 |
| T-new-8 | `backend/app/services/multimodal_service.py:1427`（`# pyright: ignore[reportMissingImports]`，注释 `:1424`） | `from agentic_rag.embedding.embedding_service import ...`；`backend/lib/agentic_rag/` 下无 `embedding` 子包（`extraPaths` 也解不了）⇒ 运行期恒走 `except ImportError`、**向量搜索永久关闭恒降级文本搜索** | 1 | **0** | **第十五批立卡**（退役该分支或补实现；G-PIPE 同族） |
| T14 | `backend/app/clients/provider_factory.py:260` / `:265`（注释 `:256-259`） | `config.py` 无 `OPENAI_API_KEY` 字段 + `extra="ignore"` ⇒ `hasattr` 恒 False、**openai 分支恒不激活** | `OPENAI_API_KEY` 在 `backend/app` 命中 **7**（含 `:210` 的 `getattr` 默认空串路径） | **3** | **第十五批立卡**（加字段 = 行为变化，D-35） |

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
3. 未证明删 `dependencies.py:1035` 的 ignore 后在 `backend/tests` 或其他 include 面**无连带 error**——本卡硬门只看 `app` 全量。
4. 未证明 `exam_service.py` 的 `if TYPE_CHECKING` 块内 11 个方法声明与 `exam_service_ext.py` 的真实 `def` **逐字签名一致**（那是 U1 面；本卡只改挂载点措辞）。
5. census 的「生产调用方 = 0」基于 **grep + AST 口径**，覆盖不到别名取用 / 回调注册 / 字符串反射 / 路由注入等动态可达路径 ⇒ 一律只能说「未发现直接生产调用」，**不能说「零曝光」**。
6. 未证明 F-6（`multimodal_service.py` Pillow）的 **commit message 历史更正**对任何读者已生效——commit message 不可变，本卡只在本 census 登记事实。
7. 未证明 `pyrightconfig.json` 的 `exclude` / `extraPaths` / 各 `report*` 键里**没有别的死枝**——本卡只清 `include` 的一处，其余配置面未逐键复核。
8. 未证明「测试覆盖」列的命中数等于**真覆盖到缺陷行**——`generate_verification_canvas` 的 15 处 tests 命中全为 mock 用例，是否执行到 `:1243` 的 `get_canvas` 崩溃行未逐条验。
