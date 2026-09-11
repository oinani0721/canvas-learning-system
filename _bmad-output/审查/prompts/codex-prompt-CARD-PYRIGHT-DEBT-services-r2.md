# 独立复核请求 — CARD-PYRIGHT-DEBT-services（阶段 1，round-2 · 整改复审）

## 一 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc`
分支 `card/u1-pyright-svc`，基线 `da690bf8`，本轮审 SHA **`958f20a3`**。

round-1 你判「本轮暂不通过」：BLOCKER=0 / HIGH=1 / MEDIUM=3 / LOW=3。**我采信了全部 6 条**，
本轮请复核整改本身。

### 请只读以下内容

1. `git diff 2fa89589 958f20a3 -- backend/app/services`
   —— 这是**本轮整改的全部改动**（4 个文件）。这是最重要的读取面。
2. `git diff da690bf8 958f20a3 -- backend/app/services`
   —— 本卡累计全部改动（53 文件，**366 insertions / 124 deletions**，实测于 `958f20a3`）。
3. `_bmad-output/审查/evidence-pyright-svc/r1-fix-verification-*.txt`（整改的运行期三态对照）
4. `_bmad-output/审查/evidence-pyright-svc/assert-except-audit-*.txt`（38 处 assert 的 except 覆盖审计）
5. `_bmad-output/审查/evidence-pyright-svc/counts-ast-*.txt`（用 AST 重数的口径修正）

---

## 二 逐条整改说明 —— 请独立核对每一条是否真的解决了问题

### HIGH（r1）：`batch_orchestrator.py` 两处 cast 掩盖 `CancelledError`

**我采信。** 已实证（Python 3.14.4，本机 venv）：
`issubclass(asyncio.CancelledError, Exception)` = **False**；
`gather(cancelled_task(), return_exceptions=True)` 返回 `[CancelledError('')]`；
`isinstance(r[0], Exception)` = **False** ⇒ 确实落进 `else` 分支；`r[0].success` 抛 `AttributeError`。

**整改**：撤掉两处 `cast`，改为 `# pyright: ignore[reportArgumentType]`
（第二处另加 `reportAttributeAccessIssue`），并把上面这段实证写进注释、登记 TAIL。
理由：修它要改 `isinstance` 的捕获面 = 运行期语义改动，不在这张纯类型卡范围。

**请核对**：① 换成 ignore 后是否还存在「声称类型正确」的成分？
② 注释描述的机制是否与你的实证一致？③ 这个「标注 + 移交」的处置边界是否恰当？

### MEDIUM（r1）：`error_extractor.py:255` assert 落在窄 except 内

**我采信。** 该方法的 except 是
`except json.JSONDecodeError` + `except (ImportError, ValueError, KeyError, AttributeError)`，
`AssertionError` 不在其中 ⇒ 原本被接住并返回 `[]` 的路径变成向外传播。

**整改**：改用 `cast(str, ...)`。三态实证（`r1-fix-verification-*.txt`）：

| 版本 | `content=None` 时 | 被该组 except 接住 |
|---|---|---|
| 基线（直接解引用） | `AttributeError` | 是 |
| round-1 的 assert | `AssertionError` | **否** |
| 整改后的 cast | `AttributeError` | 是 |

**我另外自查了同类的全部 38 处**（`assert-except-audit-*.txt`：按 AST 找出每个 assert 的最内层
`try`，判断其 handler 是否覆盖 `AssertionError`），**又找出你没点名的第 2 处**：
`intelligent_parallel_service.py:291`，其 try 只捕获
`(ConnectionError, RuntimeError, ValueError, asyncio.TimeoutError)`，同样吃不下 `AssertionError`。
已同法改为 `cast("BatchOrchestrator", ...)`。

**请核对**：① 这两处改后是否真的与基线同异常、同捕获路径？
② 那份 except 覆盖审计有没有漏掉别的 assert（例如落在嵌套 try、或 handler 写成 `except SomeAlias`）？
③ 「不在任何 try 内」的 25 处 assert，是否也需要同样对待？

### MEDIUM（r1）：`intelligent_parallel_service.py:649` 的 `cast("AgentType", agent_type)`

**我采信。**「`AgentType` 继承 `str`」确实不能反向证明任意字符串是 `AgentType` 实例。
**整改**：撤掉 cast，改 `# pyright: ignore[reportArgumentType]` + 写明「形参是 `str`、未做转换、
是否兼容取决于 `call_agent` 实现」+ TAIL 登记。

### MEDIUM（r1）：`frontmatter_signals` / `targeting_material_service` 的 `dict[str, Any]`

**我采信你的定性**：YAML 值可以是标量（`tips: 1`），循环仍会 `TypeError`，
类型放宽把诊断消掉了而不是修好了。**本轮未改代码**，只在验收单登记为「已知未修的类型放宽」。
**请判断**：这个处置是否可接受，还是应当在本卡就改成显式的 `isinstance` 判定（那会加分支 = 语义改动）。

### LOW（r1）：`rag_service` 模块属性面变化 / `graphiti_belief_service:298` 注释

- 属性面：**采信**，已登记；全仓无外部消费者（`grep` 仅命中 docstring 与该文件自身的 placeholder）。
- 注释：**采信**。「返回 None 时排序同样 TypeError」确实不普遍成立（单元素 `sort` 不比较键）。
  已改写为真实依据「`e.valid_at or e.created_at` 恒非 None ⇒ `_to_aware_utc` 的 None 分支不可达」。

### LOW（r1）：数量口径

**你是对的，我的文本 grep 把注释也数进去了。** 用 AST 重数（`counts-ast-*.txt`），当前 `958f20a3`：

| 项 | round-1 我写的 | AST 实测（958f20a3） |
|---|---|---|
| `cast` 调用 | 23（文本匹配） | **14** = 12 `ModelResponse` + 1 `str` + 1 `BatchOrchestrator` |
| 新增 `TYPE_CHECKING` 块的文件 | 5 | **11** |
| `assert x is not None` | 38 | **36**（整改撤掉 2 处） |
| `# pyright: ignore[...]` | 12 | **16**（整改新增 4 处） |
| diff | 351/123 | **366 insertions / 124 deletions** |

验收单已按此更正。

---

## 三 请按重要性排序回答

1. 整改后的 `batch_orchestrator` 两处，是否仍以任何形式掩盖 `CancelledError`？
2. 两处 `assert → cast` 的替换，是否真的恢复了与基线一致的异常传播路径？
3. 我的 except 覆盖审计（AST 找最内层 try + 判 handler）有没有方法学漏洞？
   「不在任何 try 内」的 25 处 assert 是否也改变了调用方可观察的行为？
4. 整改是否引入了任何新的问题（含新的死 import、新的类型放宽、注释与实际不符）？
5. round-1 里我未改的两项（YAML `Any`、`rag_service` 属性面），登记而不修是否恰当？

---

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` 与一句话定级理由。
每一节若核对后无问题，请明确写「该节无发现」。
最后请给出一句总判：本轮 BLOCKER 与 HIGH 是否均为 0。

---

## 五 边界

- **只读**，不要修改任何文件；不要连数据库；不要跑 `tests/integration` / `tests/e2e`。
- 不在本卡范围（请勿作为本卡问题提出）：
  - `backend/app/api/v1/endpoints/review.py:1543 / :1560 / :1561`（api 侧既有缺陷，归另一张卡）
  - `backend/app/services/review_service.py:1809-1813`（共享文件，阶段 2 处理）
- 10 个「共享文件」（`review_service.py` / `mastery_engine.py` / `mastery_store.py` /
  `multimodal_service.py` / `difficulty_matcher.py` / `canvas_service.py` / `calibration_tracker.py` /
  `event_bus.py` / `mastery_fusion.py` / `agent_service.py`）阶段 1 禁改，仍有 60 条错误 = 预期状态。
- 另有 18 条错误要等另一张卡的 `extraPaths` 配置合入后才判，本轮不碰。
