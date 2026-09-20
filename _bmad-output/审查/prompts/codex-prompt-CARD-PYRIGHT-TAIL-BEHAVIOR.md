# 代码复核请求 — CARD-PYRIGHT-TAIL-BEHAVIOR（BATCH-2026-09-18-第十五批 · 车道 P8 · 第 2/3 张）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend`（分支 `card/p8-backend`）。
`PREV`（本卡开工时的 HEAD，即上一张卡 P8-A 的末 commit）= `2038278a`。本轮审查绑定 HEAD = `3596e98b`。

本卡把 census `_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md` §四 的七项「被 `# pyright: ignore`
掩盖的真缺陷」从「只标注」改成「真行为」，另加 §九.4 的 `TYPE_CHECKING` 声明一致性门。
`# pyright: ignore` 计数 11 → 3（保留 `learning_context_service.py` 的 `search_memories`、
`intelligent_parallel_service.py` 的 `hasattr` 守卫、`exam_service.py` 的副作用 import 三条）。

本卡有 **四个代码 commit**：
- `b8500c6e` `chore(format)` —— **纯格式**。六个 services 文件属主干既有 ruff 格式漂移集
  （`backend/app` 实测 141 文件 would reformat；`backend/ruff.toml` `line-length=120` 而代码按 88 列写），
  而 lefthook 的 `ruff format --check {staged_files}` 是整文件判定。为了让语义 commit 的审查面不含格式噪音，
  先把六个文件还原成 `PREV` 态、只跑 `ruff format` 单独提一个 commit。
  纯格式自证：逐文件 `ast.dump(ast.parse(PREV版)) == ast.dump(ast.parse(format后))` 六个全部 `True`。
- `2617a930` `fix(services)` —— **语义改动 + 新测试**（round-1 审的就是这个 HEAD）。
- `b46a280f` `fix(services)` —— 按 round-1 的 4 条 LOW + 内部对抗复核整改：四处说明改到如实 + 补 8 条门。
- `3596e98b` `fix(services)` —— 补下游端到端门 + 三处如实标注（本轮绑定的最终 HEAD）。
  只看本轮新增：`git --no-pager diff --no-color 2617a930 HEAD -- . ':(exclude)_bmad-output'`。

### 最小读取面（只读这些，不要扩大）

1. `git --no-pager diff --no-color 2038278a HEAD -- . ':(exclude)_bmad-output'`
   —— 本卡全部代码改动（含上面那个纯格式 commit，所以 diff 里会有大量纯换行位移；
   若要只看语义改动，读 `git --no-pager diff --no-color b8500c6e HEAD -- . ':(exclude)_bmad-output'`）。
2. `backend/app/services/agent_routing_engine.py` —— `_INTENT_FALLBACK_MODEL`(:207)、
   `_resolve_intent_model`(:210)、`AgentRoutingEngine._llm_classify_intent`(:560–603)
3. `backend/app/services/batch_orchestrator.py` —— `_classify_gather_result`(:131)、
   `_execute_all_groups`(:472–520)、`_execute_group`(:521–~620)、`NodeExecutionResult`/`GroupExecutionResult` 两个 dataclass
4. `backend/app/services/intelligent_parallel_service.py` —— `retry_single_node`(:558–~660)
5. `backend/app/services/multimodal_service.py` —— `search`(:1267–:1363)、`_generate_embedding`(:1364–~1395)
6. `backend/app/services/wikilink_graph_service.py` —— `_get_frontmatter`(:304)、`_resolve_path`(:313–~340)、
   以及 `build()` 里给 `self._vault` 赋值的那一段
7. `backend/app/services/error_classifier.py` —— `_build_misconception`(:70)、`ErrorClassifier.classify`(:189–~230)
8. `backend/app/services/exam_service.py` —— 顶层 `TYPE_CHECKING` import 块与 `class ExamService` 体内的
   `if TYPE_CHECKING:` 11 条方法声明（:42–:129 一带）+ 文件末尾的 `import app.services.exam_service_ext`
9. `backend/app/services/exam_service_ext.py` —— `attach_to_exam_service()` 及其 11 条 `ExamService.<name> = …` 赋值
10. `backend/app/core/litellm_config.py` —— `RuntimeModelConfigManager`(:103–:176)、`format_litellm_model`、`SystemModelConfig`/`ModelTaskConfig`
11. `backend/app/services/agent_service.py` —— `AgentType` 枚举(:139–:160)与 `call_agent` 的签名行
12. `backend/app/graphiti/entity_types.py` —— `Misconception`(:268–:296)、`ErrorType`、`RemedyStrategy`、`ERROR_TYPE_TO_REMEDY`
13. `backend/tests/unit/test_pyright_tail_behavior.py` —— 新增行为门，**全文**
14. `_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md` —— §四、§九
15. （**可选，不在本 worktree**）手册 §零.16 的绝对路径是
    `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md`；
    若只读沙箱读不到它，**直接跳过**——它唯一相关的结论是「T-new-7 默认不接通」，已在本 prompt ②.2 与 ⑤ 复述。

行号仅供定位；本卡自己加了注释与 docstring，请以**符号名**为准。

## ② 作者自述（请独立核对，不要采信）

1. 七项**每项只去掉本项对应的那一条** `# pyright: ignore`；改后九文件计数实测
   `1/0/0/0/1/0/0/1/0`（顺序：learning_context / error_classifier / agent_routing_engine /
   batch_orchestrator / intelligent_parallel_service / multimodal_service / wikilink_graph_service /
   exam_service / exam_service_ext），**合计 3**。
   ⚠️ 卡文 §一(f) 写「合计 4」但只列了 3 条保留项，是卡文自身的算术错误；
   commit `2617a930` 的 body 沿用了那个错数字，已在 `b46a280f` 的 body 与验收单里更正（不 amend，避免破坏 r1 绑定）。
2. `backend/app/services/learning_context_service.py`（T-new-7）与 `backend/app/services/exam_service_ext.py`
   **零改动**；`backend/app/services/exam_service.py` 也零改动（AST 一致性实测 11/11 相等，无需对齐）。
3. `pyright app` 改前 / 改后都是 `0 errors`（80 warnings，两次同数），未靠新增 `# pyright: ignore` 掩盖。
4. 新行为门 **24** 条用例全部用真对象：真 `asyncio.CancelledError` + 真 `asyncio.gather(return_exceptions=True)`、
   真 obsidiantools `Vault(tmp_path).connect()`（经 `WikilinkGraphService.build()` 真路径）、
   真 `RuntimeModelConfigManager` 单例、真 `AgentType` 枚举、真 `Misconception` 模型、
   真 `IntelligentParallelService()` / `MultimodalService()` 默认实例；**零 mock、零 monkeypatch、零连库**。
5. T-new-8 只**退役**死 import 与其后不可达的重试循环，不补实现；用户可见行为不变
   （`search()` 仍回落文本搜索、`search_mode="text"`），日志仍含「降级为文本搜索」子串，
   既有 `tests/unit/test_multimodal_fixes.py` 的两条相关用例收工仍 passed。
6. 负控**五段**各自红在**指定断言**上，还原后 `shasum -a 256` 跑前跑后逐字同、`git status --porcelain` 为 0。
   其中后两段专门证明旧门的盲区：把 `isinstance(result, BaseException)` 改回 `Exception` 时其余 22 条全绿
   （含 `_classify_gather_result` 的三条纯函数断言），只有新增的 AST 门红；把
   `ExamService.generate_hint` 挂成 `skip_question` 时旧两条 AST 门全绿，只有新增的挂载门红。

## ③ 请按重要性排序回答的问题

0. `_classify_gather_result` 把 `KeyboardInterrupt` / `SystemExit` 也归成 `"failed"`
   （`isinstance(result, BaseException)` 这一支）。对照输入：一个在 `gather` 里抛 `KeyboardInterrupt`
   的子任务。这是否构成**新的**静默？还是相对改前（它们会落进 `else` 分支被当业务结果 append）
   属于收紧？是否应只收 `CancelledError` + `Exception`，把其余 `BaseException` 重新抛出？
   请指出这个选择在 `_execute_all_groups` / `_execute_group` 的调用点上会导致什么可观察差异。
1. T-new-3 把 `except Exception` 收窄成 `except (ImportError, AttributeError, RuntimeError)` 之后，
   对照输入：一个**完全没有配置过模型**的进程。`_resolve_intent_model` 是否可能抛出未被接住的异常，
   让 `_llm_classify_intent` 整段失败而不是降级？`RuntimeModelConfigManager` 是单例（`__new__` 持有
   `_instance`），首次实例化时 `SystemModelConfig()` 的求值是否有失败路径？
2. T-new-6 的早返回放在 `self._agent_service is None` 检查**之前**。未被拦下的输入：
   `agent_type=""`（空串）、`agent_type=None`、大小写不同的取值。这是否改变了端点
   `api/v1/endpoints/intelligent_parallel.py` 的 404/422 语义，或把「依赖未注入」这类配置断裂
   伪装成了「请求参数错」？
3. T-new-1 改用 `md_file_index.get(note_key)`。门未覆盖的路径：vault 里存在**非 .md** 的笔记、
   带 URL 编码或非 ASCII 文件名的笔记、`note_key` 来自 `_resolve_path` 以外调用点的情形。
   `md_file_index` 的键与图节点名是否在**所有**情况下同域？作者实测「无重名时是裸文件名、
   重名时自动改用去扩展名的相对路径，图节点名同步跟随」——请独立验证这条实测，并指出它不成立的输入。
4. T-new-2 抽出 `_build_misconception` 之后，`classify()` 里那个时间戳仍是「建实体那一刻」吗？
   LLM 调用在它之前完成，这会让时间戳比改前晚多少？对下游（Graphiti 写入 / 复习排序）是否有影响？
5. AST 一致性门只比 `ast.unparse` 的文本。负控输入：在 `exam_service.py` 的 `if TYPE_CHECKING:`
   块里加一条**非 def** 语句（如一个变量注解），或在 `exam_service_ext.py` 里加一个新的模块级 def
   而不在 `attach_to_exam_service()` 里挂载。这两种情况门会不会静默跳过？
   门是否证明了这 11 个方法在**运行期**真的挂载成功？
6. `pyright app` = 0 是否靠新增 `# pyright: ignore` 或 `# type: ignore` 掩盖？
   本卡新增的 `# type: ignore[call-arg]` 只有测试文件里故意传旧 kwarg 的那一处，请核实。
7. `multimodal_service.py` 里随重试循环一并删掉了 `import asyncio`、`EMBEDDING_MAX_RETRIES`、
   `EMBEDDING_RETRY_DELAY`。请核实这三者在全仓确实再无引用（包括测试、脚本、文档里的 import）。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：
- `file:line`（用符号名辅助定位）
- 一句话说明缺陷是什么
- 一句复现思路，措辞请用 **负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径** 这四类之一

没有发现的级别请显式写「无」。

## ⑤ 边界

- 只读复核，不要修改任何文件，不要连接任何数据库或网络服务。
- 不要评价 T-new-7（`learning_context_service.py` 的 `search_memories` 补 `query=`）**是否应该接通**
  ——那是已裁定的产品口径（默认不接通），本卡按裁定零改动。
- 不要评价 T-new-8 的**补实现方案**（768 维断言 vs `embedder_factory` 的 1024 维）——已登记第十六批。
- 不要评价 `wikilink_graph_service.py` 的键归一化（D-G WLGRAPH-KEY-NORM，待裁定，不在本卡）。
- 不要评价主干既有的 ruff 格式漂移本身（D-40，第十五批末位由主 session 整仓处理）。
- `backend/app/models/**`、`backend/app/graphiti/entity_types.py`、`backend/app/core/litellm_config.py`、
  `backend/app/services/agent_service.py`、`backend/app/api/**` 本卡**不得改动**，
  若你认为缺陷根因在这些文件里，请指出但标注为「越界，需另立卡」。

---

## ⑥ round-2 增补（本轮为第 2 轮，绑最终 HEAD `3596e98b`）

round-1 判定 BLOCKER/HIGH/MEDIUM 全 0、LOW 4 条。那 4 条 LOW（以及一次内部多 agent
对抗复核的存活发现）已在 `b46a280f` 与 `3596e98b` 两个 commit 里整改。本轮请重点核：

1. **四处「说明改到如实」是否真的如实了**，有没有把一个过强的说法换成另一个过强的说法：
   `_classify_gather_result` 的 KeyboardInterrupt 段与新增的可达性段、
   `_resolve_path` 的「图节点是索引键的真超集」段、常量退役注释的引用面、
   新门文件头的「零网络」收窄。
2. **新增的 9 条门是否真有判别力**（15 → 24）。特别是：
   - `test_gather_result_loops_screen_on_baseexception_not_exception`（AST 口径锁两处 isinstance）
   - `test_attach_bindings_point_at_the_same_named_function`（锁挂载右侧）
   - `test_resolved_path_is_actually_readable_by_neighbor_loader`（端到端喂给真下游）
   - `test_resolve_intent_model_reads_singleton_when_called_without_config`（生产无参形态）
   这些门自己有没有新的静默通过面？门未覆盖的路径是什么？
3. `test_resolve_intent_model_falls_back_when_config_lookup_raises` 里把
   `manager._config = object()` 再还原 —— 这算不算 mock？它对同进程其它用例有没有污染风险？
4. `retry_single_node` 成功分支新加的那条 warning：措辞是否与实际情况相符
   （`file_path` 确实是推导的、确实无写方）？加日志有没有引入新的失败面？
5. `_generate_embedding` docstring 里关于 `get_health_status` 不一致的描述是否准确
   （`vector_search_available = has_store and lancedb_connected` 确实与本方法解耦？
   「改前就存在、本卡未引入」这个归属判断对不对）？
6. 仍然 ⛔ 不得改动任何文件；仍然不评价 T-new-7 是否该接通、T-new-8 补实现方案、
   D-G 键归一化、主干既有 ruff 漂移。
