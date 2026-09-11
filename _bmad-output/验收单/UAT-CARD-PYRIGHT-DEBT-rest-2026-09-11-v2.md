# UAT — CARD-PYRIGHT-DEBT-rest v2（阶段 2）

> 批次: BATCH-2026-09-07-第十三批 · 车道 U2 (`card-u2-pyright-rest`)
> v1 = 阶段 1（`_bmad-output/验收单/UAT-CARD-PYRIGHT-DEBT-rest-2026-09-08.md`），本文覆盖阶段 2。
> ✅ **已提交**（用户 2026-09-11 当次批准带存档的 `LEFTHOOK_EXCLUDE`）。

## 〇 提交结构

| commit | 内容 | 门 |
|---|---|---|
| `dd2cede9` | `Merge commit '286178d8' into card/u2-pyright-rest` —— **纯 merge，零本卡代码** | 两门带存档排除（红因 100% 非本卡，见判据 12/12b） |
| `9c2ee90b` | 阶段 2 三文件 + `openapi.json` 时间戳 —— **车道 tip / 终审绑定 SHA** | `python-typecheck` ✔️ **自己就绿**；只排除 `python-lint` |

- 基线（阶段 2 起点）= `286178d8`（主干候选树）
- 工作树干净，代码树未跟踪文件 0
- `openapi.json` 在 `9c2ee90b` 里只改了 **2 行**（`x-generated-at`），坐实模型改写零形状变化
- **地盘判据 §二.10（`--no-merges`）现已可用**，输出恰为一个 `services/exam_service.py` = D-29 授权的单文件 crossover（口径冲突见 §五.6，待主 session 正式改判据写法）

## 一 本卡阶段 2 改了什么（恰好 3 个文件）

| 文件 | 改动性质 | 消错 |
|---|---|---|
| `api/v1/endpoints/review.py` | 4 处 `# pyright: ignore` + 理由注释；1 处海象提取 | 7 |
| `api/v1/system.py` | `status_map` 标 `Literal`、`JSONResponse` 返回 ignore、14 处 `Field(0,…)`→`Field(default=0,…)` | 4 |
| `services/exam_service.py` | **D-29 单文件 crossover**：整文件取自 `card/u1-pyright-svc`，本卡一个字未改 | `exam.py` 10 + services 侧连带 13 |

## 二 DoD-3 / 4-A：Claude 已代验

> 证据目录 `_bmad-output/审查/evidence-pyright-rest/`。**带 `⛔ SUPERSEDED` 首行的存档不得引用**（共 8 份，见 §六.3）。

| # | 判据 | 结果 | 证据 |
|---|---|---|---|
| 1 | merge 零新增（⊆ 两父并集） | parent1=232 parent2=420 merged=231 **NEW_vs_UNION=0** | `merge-union-multiset-20260911T083413.txt` |
| 2 | **主判据**：rest 面归 0 | 总 197，**rest=0**，services=197 | `pyright-app-phase2-final2-*.json` |
| 3 | 零新增 error（基线=merge 点 231） | **NEW=0**，GONE=34 | `multiset-err-and-warn-*.txt` |
| 3b | 零新增 **warning**（原为盲区，本轮补） | 80→80，**NEW=0 GONE=0**；锚：error/warning 键集交集=0 | 同上 |
| 4 | 分包 pyright（**15 个子包 + 根 .py 全覆盖**，清单由 `find` 推导不手抄） | 每个包 error=0，唯 `services` 197 | `per-pkg-complete-*.txt` |
| 4b | 完整性锚 | ①诊断里的包全在文件系统清单内（空差集）②分包求和 197 == 全量 197 | 同上 |
| 5 | AST 位置默认 | 本树 **0**；锚：同脚本在纯净主干 **366 处 / 27 文件** | `field-positional-phase2-*.txt` |
| 6 | openapi 零漂移 + required 差集 0 | diff-rc=0；required 差异 schema 数 0 | `openapi-phase2-*.txt` |
| 6b | ⚠️ **判据 6 对 `system.py` 那 4 个模型是空判据** | 它们不进 schema（`grep -c LLMStatsSummary backend/openapi.json` = 0），故另用判据 7 补位 | 同上 |
| 7 | `system.py` 模型语义等价（补 6b 盲区） | 8 个模型 json_schema + field defaults **全同**；锚A `Field(0)` vs `Field(default=1)`=False，对照B `Field(0)` vs `Field(default=0)`=True | `system-model-schema-equiv-v2-*.txt` |
| 8 | ruff check（3 改动文件） | `All checks passed!` rc=0 | `ruff-judge-v2-*.txt` §1 |
| 9 | ruff format 状态（**3 文件全覆盖**） | `review.py` clean→**clean**；`system.py`/`exam_service.py` DIRTY→DIRTY | `ruff-judge-v2-*.txt` §2 |
| 9b | hunk 级：本卡新增的格式偏差 | 三文件**改后独有均 = 0**；锚：塞一条超长行 → 判据报出 3 行 | `ruff-judge-v2-*.txt` §3-4 |
| 10 | 地盘（**两套独立机制互证**） | `git diff` 口径与逐文件 sha 口径**都是同样 3 个文件**；锚：临时改一个未碰过的文件 → 两口径都报出，还原逐字节一致 | `scope-lint-judge-v2-*.txt` §A |
| 10b | 禁写面 / D-29 授权面 / 未跟踪残留 | `lefthook.yml`+`backend/lib`+`pyrightconfig.json` 改动 **0**；`services` 改动 **1** 且恰为 `exam_service.py`；代码树未跟踪文件 **0** | 同上 §A5 |
| 11 | merge 冲突面（`openapi.json`）处置 | 取主干版 + 合并后代码重生成逐字节相同（剔时间戳）；锚：含时间戳时 rc=1 | `openapi-mergecheck-20260911T082744.txt` |
| 12 | lefthook 两门红 = 主干既有（补丁生效后重跑） | 面 95 个 .py：dirty 39 / clean 56；39 个在纯净主干上**同样 dirty** ⇒ **本卡引入 0** | `scope-lint-judge-v2-*.txt` §B |
| 12b | **逐文件归因**：`python-typecheck` 红 = 5 个 services 文件 28 条（`review_service` 14 / `multimodal_service` 6 / `mastery_engine` 5 / `agent_service` 2 / `mastery_store` 1）；本卡面贡献 **0**，`system.py` 与 `exam_service.py` 各 **0** | 见 `hook-redness-attribution-*.txt`；`9c2ee90b` 提交时 `python-typecheck` 实测 ✔️ 绿 |
| 13 | **运行期回归**：`tests/unit` + `tests/api` | 见 §三（四轮对照） | `unit-4run-attribution-*.txt` |
| 14 | 注释修订后运行期不变 | 两文件 **AST 逐节点全同**；锚A 改一个标识符→AST 变；锚B 只加注释→AST 不变 | `ast-identity-commentfix-20260911T0916*.txt` |

## 三 运行期回归：一条新红的四轮定性

`tests/unit` 开工/收工两轮出现 1 条差异，用 **2×2 设计**（代码 {基线, 阶段2} × 轮次）定性：

| 轮次 | 代码态 | 末行 | nodeid | 现网 Neo4j 连接尝试 |
|---|---|---|---|---|
| run1 | 基线 | 36 failed / 5188 passed / 29 errors / 393.62s | 65 | **0** |
| run2 | 阶段 2 | 37 failed / 5187 passed / 29 errors / 449.24s | 66 | **1** |
| run3 | 基线（同样累积状态） | 36 failed / 5188 passed / 29 errors / 333.73s | 65 | **0** |
| run4 | 阶段 2（复跑） | 36 failed / 5188 passed / 29 errors | 65 | **0** |

- `run1 → run3` 差集 **空**（diff-rc=0）⇒ 排除「跑第二轮 / `backend/data/` 累积状态」
- `run1 → run4` 差集 **空**（diff-rc=0）⇒ **基线代码与阶段 2 代码的 nodeid 集合逐条相同**，本卡判据（只允许 `<`）达成
- run2 的那条 `test_candidate_service.py::test_accept_candidate_already_accepted_returns_422` 是 **W4 哨兵**（该用例期间有 1 次到现网 Neo4j 的连接尝试被拦下并转成失败），**不随代码复现** ⇒ 归偶发。同型哨兵在本项目非首次（第十二批集成期 `evidence-b12-integ/dir-tests-unit-20260906T203713.txt:1454` 等多处）。
- `tests/api`：268 passed，连接尝试 0。
- 调查全文 `evidence-pyright-rest/w4-sentinel-investigation-20260911.md`（含一条**不成立的旁证**的如实记录，标明不得引用）。

## 四 运行期语义零变化的逐点证明（可证，非「大概」）

1. **海象改写**：`difficulty_map` 的唯一键填充处在 `_get_difficulty_data` 内，形如 `if nid and diff is not None: difficulty_map[nid] = diff` ⇒ **None 与空串永不入键集** ⇒ 原式 `None in dict` 恒 False，与新式 `is not None` 同落 False 分支。`dict.get` 无副作用 ⇒ 求值 2→1 等价。该行最近一次改动是 `95d8cb1a`（2026-07-30 FSRS-V2），非本批热点行。
   ⚠️ 已知副作用（无害，已写进行内注释）：推导式里的海象会把 `nid` 绑到外层函数作用域；`generate_verification_canvas` 内无同名局部变量（全文件 `nid` 只出现在本处与 `_get_difficulty_data`）。
2. **`Field(0,…)`→`Field(default=0,…)`**：pydantic v2 下第一个位置实参即 `default`；判据 7 的对照 B 实测判为严格相同。
3. **`status_map` 注解**：只加注解，取值字典逐字未变。
4. **crossover 的 `if TYPE_CHECKING:` 块**：运行期 `TYPE_CHECKING` 为 False，块不执行。删掉的 `import logging` 在该模块 `grep -c 'logging\.'` = **0**（它用 structlog）。末尾的副作用 import 经 `git show` 两版对照**只加了注释**，行为不变。
5. **注释修订**：判据 14 的 AST 逐节点比对证明运行期字节等价。

## 五 本卡未证明什么

1. **未证明**本树全量 `pyright app` 归 0——`services/` 残余 197 条是 U1-A 面。清单：`services-residual-20260911T084046.txt`。
2. **未证明**这 197 条会被 U1-A 清掉，也**未证明**集成候选树上全量归 0（那是主 session 的合入门）。
3. **未证明** anthropic / litellm / neo4j / gemini 真调用路径行为不变——类型层窄化未跑真 API。
4. `review.py` 三个真 bug **未修**，只加 ignore 并登记移交：`GeminiClient(model=…)`（该类无此形参，出现在 `_get_or_create_verification_service` 与 `_generate_ai_questions` 两处）、死 import `app.core.config`、`get_session_progress` 里把 dict 当 dataclass 用。
5. **未证明** crossover 的 11 个 `TYPE_CHECKING` 方法声明与 `exam_service_ext.py` 的真实 `def` 逐字一致——该证明属 U1-A 的面。对抗审查就此单设视角，产出见 §六.2。
6. **未跑** `tests/integration` / `tests/e2e`；未起后端做运行期验证。
7. 多重集键**不含行号**（既有盲区）：同文件同 rule 同消息但行号漂移的回归看不见。
8. `openapi` 判据对 `system.py` 那 4 个模型是空判据（已声明并用判据 7 补位）。
9. Codex **round-3 已完成**，绑最终 HEAD `9c2ee90b`（prompt `prompts/codex-prompt-CARD-PYRIGHT-DEBT-rest-r3.md`，最小读取面 = `git diff 286178d8 9c2ee90b -- <本卡 3 文件>`）。存档 `codex-review-CARD-PYRIGHT-DEBT-rest-r3.md`。轮次 3/5，**BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 4**，满足合并门。逐条见 §六.5。
10. **未证明** run2 那次哨兵触发的确切机制——只证明了它不随代码复现（四轮 2×2）。真因（进程内 MemoryService 单例惰性初始化的时序）未定位，归测试隔离面。

## 六 对抗审查

### 6.1 规模与口径

内部对抗审查以 Workflow 形式跑完并**全程落盘**（协议 §1「要算数就落盘」）：5 个独立视角产出发现 → 每条发现由 **3 个不同视角的反驳者**独立尝试证伪，≥2 票反驳即判死。
- 80 个 agent / 1393 次工具调用 / 21.8 分钟
- **25 条发现**，其中 19 票 STANDS / 5 票 REFUTED
- journal（逐 agent 返回值）：`~/.claude/projects/…/subagents/workflows/wf_9eca0d88-65c/journal.jsonl`

### 6.2 已按发现整改（本轮）

| 发现 | 处置 |
|---|---|
| `system.py` ignore 首要理由「另一个返回点返回的是 dict」是编造的（该函数只有 1 个 return） | **已改写注释**。核实后保留 `-> dict` + ignore 的决定仍成立，真理由是另两条：FastAPI 用返回注解推 response_model（openapi 里该路径 200 响应确有 schema）、`infra_tools.py` 调用点靠该注解保住其防御分支 |
| 本卡注释里 4+ 处自引行号被本卡自己插入的注释行顶走 | **已全部改用符号名**（项目既有教训「同改动面内引用一律用符号名」） |
| 「无条件 500」与 `_generate_ai_questions` 的两道早返回矛盾 | **已改为**「AI_API_KEY 非空且有待复习节点时才 500」 |
| 海象等价性论证漏了 `nid` 作用域外泄与「无 None 键」的依据 | **已补进行内注释**（两条都写明，含全文件 `nid` 出现处的核查结论） |
| `patch` 残留 `backend/app/api/v1/system.py.orig` 未被 gitignore 覆盖 | **已移出代码树**（`git add -A` 不会再带入；未跟踪文件复查 = 0） |
| 分包判据漏 7 个包且无锚 | **已重写**：清单由 `find` 推导 + 两条完整性锚（判据 4/4b） |
| 地盘判据的锚是同义反复 | **已重写**：两套独立机制互证 + 改一个未碰过的文件做真锚（判据 10） |
| lefthook 基线判据跑在补丁之前 | **已在补丁生效后重跑**（判据 12） |
| ruff hunk 判据只覆盖 2/3 文件、跳过唯一翻转的 `review.py`；且「已修正为 clean」是自述 | **已重写**：三文件全覆盖 + 超长行变异锚 + 实测落盘（判据 9/9b） |
| 多重集只统计 error、warning 面无判据 | **已补** warning 多重集（判据 3b） |
| 被推翻/过时的存档没有作废标记 | **已给 8 份打 `⛔ SUPERSEDED` 首行**并写明后继文件 |

### 6.3 已证伪 / 不予采纳

- **「D-29 地盘判据自述口径矛盾：services 面应为 7 而非 1」** — 实测 `git diff 286178d8 -- backend/app/services` 就是 1 个文件。**证伪**。
- **一条 BLOCKER「3 个文件已全部回退成主干原样、交付物不在树上」** — 该 agent 恰好在本 session 跑**还原→对照→复原**实验的窗口内读到中间态。属**并发读取污染**（项目既有教训「⛔ 并发 agent 写入毒化变异基线」的同族）。**不予采纳**，但登记为方法论教训：审查对象必须在审查期间冻结。
- **一条 HIGH「运行期判据出了新红、控制组前提不成立、结论没进验收单」** — 该发现在 run3/run4 之前成立；现已由 §三 的四轮 2×2 定性并写入本验收单。**已消解**。

### 6.4 移交给 U1 / 主 session（本卡不改）

- `exam_service.py` 的 `if TYPE_CHECKING` 注释把挂载点说成「模块顶层的 `ExamService.<name> = <fn>`」，实测赋值在 `attach_to_exam_service()` 函数体内（`exam_service_ext.py:947-957`），由模块顶层的 `attach_to_exam_service()` 调用（:961）执行。要害判断（副作用 import 触发挂载）**正确**，措辞不精确。D-29 规定本卡不改该文件，**交 U1**。

## 七 4-B：你来验（零技术词）

1. 照常打开一张原白板 → **我看到**它和昨天一样打开，没有多出红字 → **我感觉**没被动过。
2. 跑一次索引 → **我看到**节点照常出现、数量和之前对得上 → **我感觉**踏实。
3. 看一眼今天的复习建议 → **我看到**该到期的还在、不该出现的没冒出来 → **我感觉**它还是那个熟悉的清单。
4. 开一次检验白板做两题 → **我看到**出题、提示、判分都照常走完 → **我感觉**流畅，没有卡顿也没有莫名其妙的报错。

这次改的全是「写给机器看的类型标注和注释」，不是你会看见的任何东西。**如果你感觉「跟没改一样」，那就是对的**；只要有任何一处和昨天不同，就是我错了，请在下面批注。

## 八 批注区

> [!question]+ 你的提问
>

> [!error]+ 你发现的问题
>

### 6.5 Codex round-3（绑最终 HEAD `9c2ee90b`）

**BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 4** —— 满足协议 §1 合并门（末轮绑最终 HEAD 且 B/H 皆 0）。
存档 `_bmad-output/审查/codex-review-CARD-PYRIGHT-DEBT-rest-r3.md`（§2.1 六行首部已补，含一处偏离说明）。
⛔ 主 session 已下**代码冻结令**（`9c2ee90b` 之后不得改任何代码文件），故以下 4 条 LOW **全部登记不修**。

| # | Codex LOW | 我的独立核验 | 处置 |
|---|---|---|---|
| L1 | `exam_service.py:25` 模块命名空间确有变化（`logging` 属性消失、新增 `TYPE_CHECKING=False`），隔离执行可区分两版 | **属实**。但文件内无读取 `logging` 的代码，无业务回归 | 该文件是 D-29 crossover，本卡一字不改 → **移交 U1** |
| L2 | `review.py` 注释「`AI_API_KEY` 非空时必进 ⇒ 5 个端点全 500」断言过强 | **属实**：`_get_or_create_verification_service` 开头有 `if _verification_service_instance is not None: return`，只有**首次**调用才会进 Gemini 构造块 | 登记；下卡改注释时收窄为「单例首次创建时」 |
| L3 | `review.py:1595/1596` 行尾 `# 同 :1543` 仍是失效引用（`:1543` 是 docstring，真理由在 `:1573-1578`） | **属实**。我改了注释**块**却漏了这两行的**行尾标签** ⇒ 本验收单原先「已全部改用符号名」**不实**，此处更正 | 登记；下卡一并改成符号名 |
| L4 | `Field` 改写应为 **14** 处不是 13（四个模型 7+3+3+1） | **属实**：`git diff` 新增 `Field(default=` 行数实测 14 | **本文已更正为 14** |

**Codex 另两点澄清（非 LOW，一并记录）**
- 「rest 面归 0」**特指 error**；非 services 仍有 **33 warnings**（本卡已用判据 3b 证明 warning 零新增，但不是归 0）。
- 我概括的「ignore 压的全是别卡真 bug」**不够准确**：`system.py` 那条是「返回注解与实际对象冲突」，`exam_service.py` 那条是「保留副作用 import」，都不是 bug。
- 海象改写「对任意 Python 输入等价」**不成立**（Codex 给出纯内存反例：`difficulty_map={None: mastered}`、或自定义 `get()` 二次返回不同值）；**在本代码的实际输入路径上等价**成立——节点由 `json.load` 生成、键填充处排除 `None`、过滤内部无 `await`。本验收单 §四.1 的表述即为后者，与 Codex 结论一致。
