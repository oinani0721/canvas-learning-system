# 独立复核请求 — CARD-PYRIGHT-DEBT-services（阶段 1，round-1）

## 一 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc`
分支 `card/u1-pyright-svc`，基线 `da690bf8`。

这是一张**纯类型债清理卡**：把 `backend/app/services/**` 的 pyright（1.1.411，`typeCheckingMode: basic`，
`pythonVersion: 3.11`）存量错误清零。**明确约束：不得改运行期语义。**

阶段 1 的范围是 54 个「非共享」文件（另 10 个文件由别的车道并行改动，阶段 2 才动；另有 18 条错误
要等另一张卡的 `extraPaths` 配置合入后才能判，本轮不碰）。

### 请只读以下内容（不要遍历整个仓库）

1. `git diff da690bf8 2fa89589 -- backend/app/services`
   —— 这是本卡的**全部**代码改动（53 个文件，351 insertions / 123 deletions）。
2. `_bmad-output/验收单/UAT-CARD-PYRIGHT-DEBT-services-2026-09-08.md` 的 **§六 ignore 清单**与 **§七 修复手法口径**。
3. `_bmad-output/审查/evidence-pyright-svc/multiset-da690bf8-vs-work-*.txt` 的**末行**。
4. `_bmad-output/审查/evidence-pyright-svc/rule-dist-base-20260908T064241.txt`（开工时的错误分布）。

补充说明：`backend/app/api/v1/endpoints/exam.py` 的 10 条错误也被本卡消掉了，但**该文件一个字符都没改**
（做法见下方第二节第 3 条）。如需确认，可只读该文件与 `backend/app/services/exam_service.py` 的 diff。

---

## 二 作者自述 —— 以下每一条都请你独立核对，不要采信我的说法

1. **死 import 删除（50 行，覆盖 53 条诊断）**
   我的主张：这些 import 在本模块内确实未被使用，且不存在字符串级/动态使用（`getattr` / `importlib` /
   `globals()`），也没有别的模块从这些 services 文件「借道」import 它们。
   请核对：有没有哪一个删除会让某处运行期 `NameError` / `AttributeError`，
   或让某个模块的公开属性面发生外部可见的变化。
   特别请看：`memory_service.py` 删掉的 `import neo4j.exceptions`（它有一段解释历史事故的注释）、
   `rag_service.py` 从 `try: from agentic_rag import (...)` 块里删掉的 `CanvasRAGConfig`。

2. **`assert x is not None`（38 处）**
   我的口径是：**只加在「原代码遇 None 也会崩」的位置**，把静默的 `AttributeError` / `TypeError`
   换成 `AssertionError`；**不允许**加 `if x is None: return ...` 这类改控制流的早退。
   请核对：有没有哪一处 assert 实际上落在「原代码遇 None 会正常走下去」的位置 —— 那就是我改了语义。
   我自己已知有 3 处的下一条语句不是直接解引用，理由分别写在同行注释里
   （`graphiti_belief_service.py` 两处、`wikilink_graph_service.py` 一处），请重点看这 3 处。

3. **`if TYPE_CHECKING:` 方法声明（`exam_service.py`）**
   `exam_service_ext.py` 在模块顶层用 `ExamService.<name> = <fn>` 挂了 11 个方法（猴子补丁）。
   我在 `class ExamService` 体内加了一个 `if TYPE_CHECKING:` 块声明这 11 个签名。
   我的主张：① 签名与 `exam_service_ext.py` 的 `def` **逐字一致**；② 运行期该块不执行，零行为变化；
   ③ 这同时消掉了 ext 侧 11 条 `Cannot assign to attribute` 与 `api/v1/endpoints/exam.py` 的 10 条
   `Cannot access attribute`。请逐条核对签名是否真的一致（参数名、默认值、`async`、返回类型）。

4. **`cast(...)` 窄化（23 处）**
   只用于联合类型：litellm 的 `ModelResponse | CustomStreamWrapper`、
   `asyncio.gather(return_exceptions=True)` 的 `T | BaseException`、`str → Literal/Enum`。
   请核对：有没有哪一个 `cast` 把一个**真实的**类型错误盖住了 —— 即运行期该值确实可能是 cast 目标之外的类型。
   litellm 那 12 处我的依据是「这些调用点都没有传 `stream=True`」，请核对该依据是否成立。

5. **多重集对照 `NEW=0`**
   我用 `git archive da690bf8` 建基线树，两边跑 `pyright backend/app --outputjson`，
   以 `(相对路径, rule, message)` 为键做多重集差集，结果 `base=421 work=242 NEW=0 GONE=179`。
   请核对这个判据是否足以支撑「本卡没有把任何地方弄红」。
   已知盲区（我已如实登记）：键不含行号，所以「同文件同 rule 同消息换一行再犯」看不见。

6. **注解收紧（6 处）**
   把 `object` 改成真实类型（`Neo4jClient` / `AsyncDriver`）、给默认值为 `None` 的参数补 `Optional`。
   请核对：每一处收紧之前，调用方实际传入的值是否都满足新注解 —— 收紧类型可能让某个调用方从此不成立。

---

## 三 请按重要性排序回答以下问题

1. 有没有哪一处 `cast` 把一个真实的类型错误盖住了？
2. 有没有哪一处 `assert x is not None` 落在「原代码遇 None 不会崩」的位置（= 改了语义）？
3. `exam_service.py` 的 `TYPE_CHECKING` 方法声明与 `exam_service_ext.py` 的定义是否逐字同签名？
   有没有可能与测试里对 `exam_service_ext` 的 monkeypatch 站点冲突？
   （我实测：`grep -rln exam_service_ext backend/tests` = 3 个文件，其中
   `patch("app.services.exam_service_ext...` 的站点数 = 0。）
4. 12 条 `# pyright: ignore[...]` 中，有哪一条的理由**不成立**，或者本可以用真正的类型修复代替？
5. 删掉的 50 行 import 中，有没有哪一行其实有副作用（子模块注册、装饰器注册、`__init__` 执行等）？
6. 本卡把 4 个既有真缺陷标成了 ignore 并登记移交（`get_litellm_config` 不存在、
   `Settings.TASK_CLEANUP_INTERVAL_SECONDS` 不存在、`Misconception.created_at` 改名遗漏、
   obsidiantools `Vault.get_source_path` 不存在）。请判断：这个「只标注不修」的处置是否恰当，
   有没有哪一条其实应该在本卡就修掉。

---

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` 与一句话说明为什么它是那个级别。
如果某一节你核对后认为没有问题，请明确写「该节无发现」，不要省略。

---

## 五 边界

- **只读**，不要修改任何文件。
- 不要连接任何数据库（本卡零数据库改动）。
- 不要运行 `tests/integration` 或 `tests/e2e`。
- 以下两处**不在本卡范围**，请不要作为本卡的问题提出：
  - `backend/app/api/v1/endpoints/review.py:1543 / :1560 / :1561`（对 dict 取属性，是 api 侧既有缺陷，归另一张卡）
  - `backend/app/services/review_service.py:1809-1813`（`EdgeRelationship` 签名不匹配，属共享文件，阶段 2 处理）
- `backend/app/services/` 下的 10 个「共享文件」（`review_service.py` / `mastery_engine.py` /
  `mastery_store.py` / `multimodal_service.py` / `difficulty_matcher.py` / `canvas_service.py` /
  `calibration_tracker.py` / `event_bus.py` / `mastery_fusion.py` / `agent_service.py`）
  在阶段 1 **禁止改动**，它们仍有 60 条错误 —— 这是预期状态，不是本卡的遗漏。
