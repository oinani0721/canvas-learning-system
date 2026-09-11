# 独立复核请求 — CARD-PYRIGHT-DEBT-services 阶段 2（末轮，绑最终 HEAD）

## 一 背景与最小读取面（请只读以下内容，勿全仓漫游）

本卡把 `backend/app/services/**` 的 pyright 存量错误清零。阶段 1（已审 4 轮，r4 达 B0/H0/M0）
清 54 个非共享文件；**阶段 2（本轮唯一审查对象）** 在合入主干候选树 `286178d8` 后清 10 个共享文件。

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc`

请读（且仅读）：

1. 本轮改动全文：
   `git diff 286178d8 ccd2a4d1 -- backend/app/services`
2. 证据目录中的这几份（路径相对仓根）：
   - `_bmad-output/审查/evidence-pyright-svc/phase0-merge-whatif-final-*.txt`（何若实测：合 U2 阶段 0 后 services=0）
   - `_bmad-output/审查/evidence-pyright-svc/multiset-286178d8-vs-*.txt`（多重集 NEW 判据末行）
   - `_bmad-output/审查/evidence-pyright-svc/rule-dist-phase2-base-20260911T083206.txt`（开工按 rule/文件分布）
   - `_bmad-output/审查/evidence-pyright-svc/format-drift-phase2-*.txt`（format 漂移身份口径双向差集）
   - `_bmad-output/审查/evidence-pyright-svc/lefthook-blocked-raw-phase2*.txt`（被跳过的两道 hook 的原始输出）
   - `_bmad-output/审查/evidence-pyright-svc/ignore-necessity-phase2-final-*.txt`（ignore 承重门 8/8）
   - `_bmad-output/审查/evidence-pyright-svc/negctl-phase2-*.txt`（负控 3/3，含跑前/还原后 sha256）
   - `_bmad-output/审查/evidence-pyright-svc/scope-phase2-*.txt`（地盘：63 文件全在 services/，禁改面空）
   - `_bmad-output/审查/evidence-pyright-svc/unit-nodeid-diff-phase2-*.txt` 与 `unit-clean-baseline-568de82a-*.txt`（tests 差集）
   - `_bmad-output/审查/evidence-pyright-svc/baseline-contamination-corroboration-*.txt`（开工基线污染的旁证）
3. 验收单 `_bmad-output/验收单/UAT-CARD-PYRIGHT-DEBT-services-2026-09-08.md`（v2，§十一 起为阶段 2）
4. 为核对签名/定义可按需点读：`backend/app/clients/neo4j_learning_base.py`、
   `backend/app/clients/neo4j_edge_client.py`、`backend/app/services/canvas_service.py`。

## 二 作者自述，请独立核对（不要采信我的结论，请自己验）

1. **本卡只做类型层，零语义改动**。10 个共享文件此前由 U9/U10-B/U11-C 改过判定逻辑，
   本卡声称只叠注解/窄化/删死 import/加 `_` 前缀，未动任何判定行与控制流。
2. **未使用变量一律 `_` 前缀重命名而非删除**（7 处）。自述理由：删除只对纯右值安全，
   逐处判断 7 次、判错一次即行为变化；重命名对全部 7 处都是零行为变化。
3. **10 条 `import logging` 系真死 import**：自述已逐文件确认其余 `logging` 字面量都在注释/docstring 内。
4. **`CardState` 从 import 与 except 兜底两侧一并移除**：自述全仓无人从 `review_service` 导入或 patch 它。
5. **`Image.LANCZOS` → `Image.Resampling.LANCZOS`**：自述 Pillow 12 运行期实测 `==` 为 True
   （前者是裸 int 1，后者是 IntEnum 成员），stub 已删模块级常量，故此为官方迁移路径，而非用注解回避 stub 给出的弃用信号。
6. **litellm 窄化照抄阶段 1 先例用 `cast` 而非 `assert`**：自述理由是该处 except 把 `{e}` 写进日志，
   `AssertionError` 的空消息会吃掉原因（error_classifier.py 的既有注释记载了同一校正）。
7. **`canvas_service` 的 `assert self._memory_client is not None` 是真不变量**：
   自述唯一调用链 `_trigger_memory_event`(:264) 在 None 时提前 return。
8. **三条真缺陷只加行级 ignore、不改语义**（`review_service:1243` get_canvas、
   `review_service:2141-2144` EdgeRelationship、`learning_context_service:205` search_memories 缺 query）。
   自述前两条所在方法 `generate_verification_canvas` **生产零调用方**，第三条在活路径上但功能一直空转。
9. **多重集对照 NEW=0**（基线 = `286178d8` 的 `git archive` 树，键 = 路径+rule+消息，不含行号）。

## 三 请按重要性排序回答这些问题

1. 有没有哪个 `cast` 把**真类型错误**盖住了（即：该处运行期确实可能是另一个类型，
   cast 让 pyright 不再报，而缺陷仍在）？特别看 `cast(Any, ...)` 与 `cast(str, ...)` 两类。
2. `assert x is not None` 是否落在**原代码遇 None 也会崩**的位置？若该处原本被某个 except 静默吞掉，
   而 assert 改变了可观察行为（异常类型/消息/日志内容），请指出。
3. 8 条新增 `# pyright: ignore[...]` 每一条的**理由是否成立**？（它们已过承重门：逐条摘掉后 pyright 在同行重报同 rule，8/8 承重）是否有哪条其实能真正修掉而不必 ignore？
   是否有哪条 ignore 的 rule 名过宽、顺带盖住了同行的别的问题？
4. 三条"真缺陷不改"的**死活路径判定是否可靠**？我判 `generate_verification_canvas` 生产零调用方的依据是
   「全仓唯一 `.generate_verification_canvas(` 出现在 `dependencies.py:301` 的 docstring 示例块内」——
   这个判据有没有漏掉别的到达方式（动态派发、字符串反射、路由表、后台任务、CLI）？
5. `_` 前缀重命名的 7 处里，有没有哪一处其实**被同作用域别处读到**（含闭包、locals()、f-string、eval）？
6. 阶段 2 共享文件的改动是否真的只在类型层？有没有哪一 hunk 实际改了判定或控制流？
7. `EdgeRelationship(` 那一行我**删掉**了原本挂着的 ignore，依据是「`Arguments missing` 诊断的 range
   跨整个调用表达式，range 内任一行的 ignore 都会连带压住它」（三组对照实测见验收单 §十四.7）。
   这个依据成立吗？删掉之后是否存在某种 pyright 配置/版本下该诊断会重新冒出来的情形？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 四级分组，每条写明 `file:line` 与一句话结论 + 一句话依据。
若某级为空请显式写「（无）」。最后给一段总评。

## 五 边界

- 只读复核，请勿修改任何文件；请勿连接数据库；请勿运行 `tests/integration` 或 `tests/e2e`。
- **不在本卡范围**：`backend/app/{api,clients,mcp,core,middleware}/**`、`pyrightconfig.json`、
  `backend/app/models/**`（均属并行车道 U2 的地盘）；`backend/tests/**` 的存量红。
- 本树**没有** `extraPaths`（那是 U2 阶段 0 的唯一写者，尚未合入本树）。因此 `pyright app/services`
  在本树仍有 35 条残余（23 条 `agentic_rag`/`memory.temporal` 解析不到 + 12 条 pydantic 位置默认假阳）。
  **这 35 条是预期而非缺陷**，请勿作为发现提出；判据见何若实测存档（合阶段 0 后 = 0 errors）。
