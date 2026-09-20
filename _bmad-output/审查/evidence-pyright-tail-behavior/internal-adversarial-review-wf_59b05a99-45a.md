# 内部对抗复核存档 — CARD-PYRIGHT-TAIL-BEHAVIOR

> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-PYRIGHT-TAIL-BEHAVIOR
> 形态: Claude Code `Workflow` 多 agent 编排（**不是** Codex；不替代协议 §2 的 Codex 轮次）
> run id: `wf_59b05a99-45a` · agents: 96（0 error / 0 skipped / 0 empty）· tool_uses: 1488
> journal（逐 agent 返回值，本存档的真相源）:
>   `~/.claude/projects/-Users-Heishing-…-card-p8-backend/fdb9cfbf-…/subagents/workflows/wf_59b05a99-45a/journal.jsonl`
> 结构: 8 个只读维度并行 find → 每条发现由 **3 个不同视角**的反驳者独立裁决
>       （举反例 / 是否已被现有门覆盖 / 根因是否越界），**2 票以上反驳即判死** → 完整性批评者收口
> 审查绑定: `2617a930`（= Codex r1 同一 HEAD）
> ⚠️ 协议 §1「不入库的复核不作依据」——本存档即为入库形态；其结论在验收单中标注为
>   「内部对抗复核」，与 Codex 存档分列，不混记为 Codex 轮次。

---

## 汇总：29 条发现 → 存活 15 / 被反驳 14

## 一 存活（3 视角裁决后 refuted < 2）

### 1. [MEDIUM] `backend/app/services/batch_orchestrator.py` :: `_execute_all_groups` (:513)

- 维度: `cancel-semantics` · 反驳票: **1/3**
- 主张: group 级失败/取消分支构造的 `GroupExecutionResult` 只填 `failed_count=len(groups[i].node_ids)`，`node_results` 留空 default_factory=[]，于是 `_aggregate_results`（1097 行 `for nr in gr.node_results`）产出 `errors: []`，API 响应对该组给出「total_nodes=N、completed_nodes=0、errors 为空数组」——取消/失败原因只进了 502-507 行的日志，一个字都没到调用方；node 级分支（569-577）则把 `error_message` 写进了 NodeExecutionResult。
- 复现思路: 对照输入：同一个失败在两层的可观测性不同——让 `_execute_group` 抛出（既有 `test_execute_all_groups_handles_group_exception` 就是这个形态），`_aggregate_results` 返回的 `groups[i]` 是 `{"total_nodes": N, "completed_nodes": 0, "errors": [], "results": []}`，而顶层 `failed_nodes` 却是 N；改为让同样的异常发生在 node 层，`errors` 里就有 N 条带 error_message 的条目。
- 三视角裁决:
  - `counterexample` → **反驳**：可以举出具体调用序列证明「API 响应对该组给出 errors 空数组」不会发生——发现的机制描述对，但它主张的可观测后果在生产接线上不成立，且该分支不是本卡引入的。

一、对照输入（真实调用序列）：`_aggregate_results` 的返回值在生产里没有任何消费方。
- 起批：`backend/app/api/v1/endpoints/intelligent_parallel.py:317` 调的是 **service** 的 `start_batch_session`，返回 `SessionResponse(session_id, status=pending)`（`intelligent_parallel_service.py:245-252`），不是编排器的聚合字典。
- 编排器的 `start_batch_session`（`batch_orchestrator.py:28
  - `already-covered` → **支持**：代码核实全部属实，且现有门/测试/类型检查都没覆盖这条场景。

代码事实（backend/app/services/batch_orchestrator.py）：
1. `_execute_all_groups` 的失败/取消分支（约 :500-513）只填 `group_id/agent_type/status="failed"/failed_count=len(groups[i].node_ids)`，`node_results` 落到 dataclass 的 `field(default_factory=list)`（:112）。异常文本只进 :502/:507 两行 `logger.error`。
2. `_aggregate_results`（:1093-1112）的 `results_list`/`errors_list` 完全由 `for nr in gr.node_resu
  - `scope-boundary` → **支持**：不越界，发现成立。整条因果链都在 backend/app/services/batch_orchestrator.py 内，该文件不在硬边界清单里，且本卡已经在改它。逐点核实：(1) NodeExecutionResult(:91) 与 GroupExecutionResult(:106) 两个 dataclass 定义在 batch_orchestrator.py 本体，不在 backend/app/models/**，node_results 的 field(default_factory=list) 也在这里；(2) group 级失败/取消分支 :505-512 确实只填 group_id/agent_type/status="failed"/failed_count=len(groups[i].node_ids)，node_results 留默认空表；(3) _aggregate

### 2. [HIGH] `backend/app/services/intelligent_parallel_service.py` :: `IntelligentParallelService.retry_single_node` (:634)

- 维度: `agenttype-early-return` · 反驳票: **0/3**
- 主张: 本卡把恒失败的 call_agent 修通后，成功分支首次在生产可达，而该分支返回的 file_path 是凭 canvas_path/node_id/agent_type 拼出来的字符串——AgentResult 没有 file_path 字段（hasattr 恒 False），call_agent 也不写任何文件，agent 的回答（result.result/result.data）被整个丢弃 ⇒ POST /canvas/single-agent 现在会返回 200 + status=success + 一条指向不存在文件的路径。
- 复现思路: 门未覆盖的路径：唯一覆盖成功分支的 test_intelligent_parallel_endpoints.py::test_retry_single_node_delegates_to_agent_service 用的是 conftest.py:1024-1030 的 MagicMock（file_path=None，正好落进拼接分支），只断言 status==success，没有任何判据检查该路径下文件是否真存在；真 AgentService 的成功分支改前抛 AttributeError 恒不可达，因此本卡打通它时无门看管。
- 三视角裁决:
  - `counterexample` → **支持**：发现成立，举不出反例。逐链核实：(1) AgentResult 是 @dataclass（agent_service.py:162-181），字段无 file_path，全文件无 __getattr__ ⇒ hasattr 对真实结果恒 False；(2) 改前不可达已证：SingleAgentRequest.agent_type 是裸 str（intelligent_parallel_models.py:224），端点原样下传（intelligent_parallel.py:567-571），裸 str 进 _call_gemini_api 后第一处无条件使用就是 agent_type.value（agent_service.py:2418，还有 2421/2435/2437）⇒ AttributeError 被 call_agent 的兜底 except Exception 吞成 su
  - `already-covered` → **支持**：发现成立，未被任何现有门覆盖。逐条核实：(1) 可达性变化属实——改前 retry_single_node 把裸 str 传给 call_agent，_call_gemini_api 第一条日志就取 agent_type.value（agent_service.py:~2415），其 except Exception 处理器本身又取 .value（~2882），AttributeError 逸出 call_agent 落进 retry_single_node 的 except ⇒ 恒 failed；生产 DI 注入的是真 AgentService（dependencies.py:1046 → intelligent_parallel.py:167），本卡传枚举后成功分支首次可达。(2) 路径确系凭空拼接——AgentResult（agent_service.py:163-181）无 fil
  - `scope-boundary` → **支持**：根因在界内，不是越界。谎报路径的构造点是 backend/app/services/intelligent_parallel_service.py:626-635（本卡已改的文件，不在硬边界清单）；诚实修法完全在界内：SingleAgentResponse.file_path 本就是 Optional[str]=None（models/intelligent_parallel_models.py:464-468），端点只是原样透传（api/v1/endpoints/intelligent_parallel.py:567），所以成功分支返回 file_path=None（或返回带原因的 failed）不需要动 models/**、api/** 或 agent_service.py。只有「真去生成文件」才需要 agent_service.py——但那是未实现的功能，不是本缺陷；缺陷是服务层报出

### 3. [HIGH] `backend/app/services/agent_routing_engine.py` :: `AgentRoutingEngine._llm_classify_intent` (:578)

- 维度: `intent-model-resolve` · 反驳票: **0/3**
- 主张: `_resolve_intent_model()` 让 model 跟随运行期配置了，但同一处 `litellm.acompletion` 仍然只传 model、不传 api_key；面板配的 key 只活在 `RuntimeModelConfigManager` 内存里（litellm_config.py 全文无 os.environ 导出、全仓无 litellm.api_key 赋值），于是模型一旦切到 env 里没有 key 的那个 provider，调用必抛 AuthenticationError，被外层 `except Exception: logger.debug("LLM intent classification failed")` 吞掉 → `_llm_classify_intent` 返回 None，语义路由静默关闭；仓内另两个同源消费方 suggestions.py:185-200 与 conversation_distiller.py:303-316 都是 model 与 `get_*_api_key()` 成对取的，本处只取了一半。修复只需在本文件调用点补 `get_scoring_api_key()`（litellm_config.py:165 已存在），不触碰硬边界文件。
- 复现思路: 对照输入：一个只通过 POST /api/v1/system/config 配了 scoring={provider:"anthropic", model_name:"claude-…", api_key:"sk-ant-…"}、env 里只有 GEMINI_API_KEY 的进程 —— 在 b8500c6e 上走写死的 gemini/gemini-2.0-flash 分类成功，在 2617a930 上 model 变成 anthropic/… 而 api_key 缺席，每个低置信节点都退回正则结果，日志只有一条 debug。
- 三视角裁决:
  - `counterexample` → **支持**：发现成立——五条反驳路径全部走不通，举不出让该问题不发生的输入。

1) 「面板 key 经 env 到达 litellm」不成立：`RuntimeModelConfigManager`（litellm_config.py:103-173）全无 os.environ 写入；backend/app 内唯一的 `os.environ[...]` 赋值是 config.py:1063 的 reload_settings（无关）；`POST /api/v1/system/config`（system.py:853-854）只做 `mgr.update(sys_config)`；load_dotenv（app/__init__.py:16、main.py:26）只灌 .env，从不灌面板 key。
2) 「全局 litellm key」不成立：`grep -rn "litellm.api_key\|
  - `already-covered` → **支持**：核实成立，且现有门/测试/类型检查均未覆盖。实证：(1) agent_routing_engine.py:578-585 的 acompletion 只传 model/messages/temperature/max_tokens，全文件 grep api_key 零命中；(2) model 已改为 _resolve_intent_model()（:210-238）→ RuntimeModelConfigManager.get_scoring_model()，即面板推送的 provider；(3) litellm_config.py 自身 docstring 写明 key 只在内存（Task 9.5），文件内无 os.environ 写入，POST /api/v1/system/config（system.py:817-853）只做 mgr.update()；app/ 下仅有的 env 写
  - `scope-boundary` → **支持**：根因在界内，不越界。缺陷点是 backend/app/services/agent_routing_engine.py:578 的 litellm.acompletion 调用只传 model 不传 api_key；该文件不在本卡硬边界清单里（清单列的是 agent_service.py，不是 agent_routing_engine.py）。修复是同文件内的调用点补参，所需的 get_scoring_api_key() 已存在于 litellm_config.py:165 —— 只需调用，不需要改动它，读取边界文件不算越界。实测核实：(1) grep api_key 在 agent_routing_engine.py 零命中；(2) litellm_config.py 全文无 environ，POST /api/v1/system/config（api/v1/system.py:819-

### 4. [MEDIUM] `backend/tests/unit/test_pyright_tail_behavior.py` :: `test_resolve_intent_model_uses_configured_scoring_model` (:67)

- 维度: `intent-model-resolve` · 反驳票: **0/3**
- 主张: 两条意图模型门（:67 / :82）都显式把 config 传进去，生产路径 `_resolve_intent_model()`（config=None → 函数内延迟 import `get_runtime_model_config` → 取单例）与 `except (ImportError, AttributeError, RuntimeError)` 的 warning 降级分支零覆盖；而本卡修的 T-new-3 正是「import 了一个不存在的名字 ⇒ 恒降级」这一类缺陷 —— 它恰好落在门覆盖不到的那一段。同理也没有任何断言把 :575 的 `model = _resolve_intent_model()` 这条接线钉住。
- 复现思路: 门未覆盖的路径：把 :229 的 `get_runtime_model_config` 改回任意不存在的名字（或把 :575 改回字面量 `_INTENT_FALLBACK_MODEL`），`test_resolve_intent_model_uses_configured_scoring_model` 与 `test_resolve_intent_model_falls_back_without_config` 仍然全绿，缺陷原样复活。
- 三视角裁决:
  - `counterexample` → **支持**：发现成立，举不出反例。核实：(1) agent_routing_engine.py:228-231 的 `from app.core.litellm_config import get_runtime_model_config` 写在 `if config is None:` 块体内，而 test_pyright_tail_behavior.py:67 与 :82 两条门都显式传 config ⇒ 该 import 语句在门里从不执行，把 :229 换成不存在的名字两门照绿（未被拦下的输入）。(2) 全仓 grep（backend/ 全量 --include='*.py'）显示 `_resolve_intent_model` / `_llm_classify_intent` / `_INTENT_FALLBACK_MODEL` 只出现在生产文件 + 本测试文件；既有 tests/unit/
  - `already-covered` → **支持**：不 refute，但降级为 LOW。\n\n核实为真的部分：`test_pyright_tail_behavior.py:67` / `:82` 两条门都显式传 config，`_resolve_intent_model` 的 `config is None` 分支（agent_routing_engine.py:228-231 延迟 import `get_runtime_model_config` + 取单例）与 `except (ImportError, AttributeError, RuntimeError)` 的 warning 降级分支确实零覆盖；全仓 grep（`_llm_classify_intent` / `_resolve_intent_model`）显示除本新文件外无任何测试触及意图模型路径，既有 `tests/unit/test_agent_routing_eng
  - `scope-boundary` → **支持**：根因在界内，无法以「越界」驳回，发现本身经代码核实成立。\n\n核实：(1) agent_routing_engine.py:228-231 的 `config is None` 分支（延迟 import `get_runtime_model_config`）与 :233 的 `except (ImportError, AttributeError, RuntimeError)` warning 降级分支，确实被两条门绕开——:67/:82 都显式传 `runtime_model_config`。(2) 全 backend `*.py` grep：`_llm_classify_intent` 零测试引用，:575 `model = _resolve_intent_model()` 这条接线无任何断言。\n\n界内判定（我的视角）：缺口落在 agent_routing_engine.py（本

### 5. [MEDIUM] `backend/app/services/wikilink_graph_service.py` :: `_resolve_path` (:319)

- 维度: `wikilink-path-resolve` · 反驳票: **1/3**
- 主张: 新 docstring 断言「图节点名与 obsidiantools md_file_index 同域、不存在歧义」为假：obsidiantools 的图节点 = md_file_index 键 ∪ 正文 wikilink 文本（api.py:774 `__get_graph_data_dict` 返回 `_wikilinks_index`，api.py:526 `nx.MultiDiGraph(graph_data_dict)` 把值里的目标串也建成节点），后者含不存在笔记和带目录前缀的写法；同文件 157-161 行的既有注释（以及整套 basename fallback）说的正是同一件事，与该 docstring 直接冲突。在 docstring 自己举的重名场景下，一条裸 `[[note]]` 产生图节点 `note`，它不在 md_file_index（键被 obsidiantools 改成了 `sub/note`/`sub2/note`）⇒ `_resolve_path` 回落出一个不存在的 `note.md`。
- 复现思路: 门未覆盖的路径：在 test_resolve_path_disambiguates_duplicate_basenames 的 vault 里给 top.md 加一行 [[note]]，图里即多出节点 `note`，_resolve_path("note") 返回不存在的 `note.md`，而现有三条用例都没有任何指向重名 basename 的 wikilink。
- 三视角裁决:
  - `counterexample` → **支持**：发现的事实主张成立，我举不出反例。

库侧实证（/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/obsidiantools/api.py）：
- `__get_graph_data_dict`（api.py:734-762）在 attachments=False 时直接 `return self._wikilinks_index`；`connect()`（api.py:524-526）`G = nx.MultiDiGraph(graph_data_dict)` ⇒ 图节点 = 字典键（md_file_index 键）∪ 字典值（正文 wikilink 文本）。
- 值侧无任何归一化：
  - `already-covered` → **反驳**：前提属实但结论站不住：已被现有门覆盖，且不是本卡引入的行为。(1) 事实核对：obsidiantools api.py:526 `nx.MultiDiGraph(graph_data_dict)` + api.py:760 返回 `_wikilinks_index`，节点集确为 md_file_index 键 ∪ 正文 wikilink 目标串；包自身也有 `_get_nonexistent_notes`(api.py:1360-1368) 专门表达这个差集。所以"图节点 ⊋ md_file_index 键"成立。(2) 但该路径正是 `_resolve_path`(wikilink_graph_service.py:319) 显式处理并在自己 docstring 第三段写明的兜底："索引里查不到时仍回落 f\"{note_key}.md\"，与旧行为一致"。(3) 该兜底已有门：back
  - `scope-boundary` → **支持**：根因不越界，发现成立。

【边界轴裁定】问题落点是 backend/app/services/wikilink_graph_service.py:313-326 的新 docstring —— 由本卡 commit 2617a930 亲手写入，在本卡亲手重写的 _resolve_path 上。该文件不在硬边界清单（models/** · graphiti/entity_types.py · core/litellm_config.py · services/agent_service.py · api/** · services/learning_context_service.py · services/exam_service*.py）内，因果链上也没有任何一环经过边界内文件。本卡完全有权也有责任改。判「越界，需另立卡」不成立。

【逐条核实（不采信主张，自读随包 obsidianto

### 6. [MEDIUM] `backend/tests/unit/test_pyright_tail_behavior.py` :: `test_build_misconception_preserves_caller_timestamp` (:200)

- 维度: `misconception-build` · 反驳票: **1/3**
- 主张: T-new-2 的行为门只打在新抽出的 `_build_misconception` 上，没有任何一条断言把 `ErrorClassifier.classify()` 这个唯一调用点绑到该 helper，于是被修复的那一行（error_classifier.py:214-224）处于无人看管状态。
- 复现思路: 门未覆盖的路径：把 error_classifier.py:214-224 改回旧形态 `Misconception(..., created_at=datetime.now(timezone.utc).isoformat())  # pyright: ignore[reportCallIssue]`（`_build_misconception` 保留为未被调用的死函数），本卡两条新用例 test_build_misconception_preserves_caller_timestamp / test_legacy_created_at_kwarg_is_silently_dropped_by_model 仍全绿，既有的 test_error_classification_mapping.py::test_classify_legacy_method_still_works（唯一调 classify() 的用例，只断言 error_type / remedy_strategy）也仍全绿，pyright 也因 ignore 注释恢复而归 0 —— 即本卡声称锁住的缺陷可以整体回滚而不被任何判据拦下；补一条断言 `(await ErrorClassifier().classify(...)).misconception.misconception_created_at` 落在调用前后墙钟区间内即可堵上。
- 三视角裁决:
  - `counterexample` → **支持**：核心主张经实测成立，我举不出反例。(1) `grep -rn "_build_misconception" backend --include="*.py"` 只有三处：定义 error_classifier.py:70、唯一调用 :214、测试里的直接 import :203——无任何结构门/替身/AST 断言把 classify() 绑到 helper。(2) 唯一调 classify() 的 test_error_classification_mapping.py:305-320 只断言 error_type / remedy_strategy / misconception.error_type；`misconception_created_at` 全仓只出现在本卡两条新断言里，都打在 helper 或模型上，从不打在 classify() 的返回值上。(3) pyright 门也
  - `already-covered` → **反驳**：实读三处后判定站不住（两条独立理由，第一条是决定性的）。

**1. 该发现自己给出的"堵上"方案是无判别力的空门（决定性）。**
`backend/app/graphiti/entity_types.py:290-293`：`misconception_created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), ...)`。
即旧形态（`created_at=` 被 pydantic `extra='ignore'` 丢弃）下该字段回落的值**也是构造那一刻的 now**；新形态（`error_classifier.py:214-224`）传入的值是构造前一行取的 now。两者都必然落在"调用前墙钟 ≤ x ≤ 调用后墙钟"区间内。所以发现里提议的断言 `(await Er
  - `scope-boundary` → **支持**：从「根因是否越界」这一角度看，这条发现**不越界**，因此不该以越界为由驳回。

核实到的事实（只读核对，未改任何文件）：
1. `backend/app/services/error_classifier.py:214` 是 `_build_misconception` 的唯一生产调用点；`grep -rn "_build_misconception" backend --include='*.py'` 只有三处：定义 (:70)、该调用点 (:214)、以及本卡新测试 (`backend/tests/unit/test_pyright_tail_behavior.py:203/206`)。
2. `grep -rn "\.classify(" backend --include='*.py' | grep -v "classify_with\|_llm_classify"` 全仓只命中

### 7. [HIGH] `backend/tests/unit/test_pyright_tail_behavior.py` :: `test_classify_gather_result_separates_cancellation_from_failure` (:248)

- 维度: `gate-quality` · 反驳票: **1/3**
- 主张: T-new-5 的真修复是 batch_orchestrator.py:502 与 :567 两处 `isinstance(result, Exception)` → `isinstance(result, BaseException)`；新门只打在纯函数 `_classify_gather_result` 上，而该函数的返回值在两个调用点只用于选日志文案（`kind == "cancelled"` 仅决定 logger.error/warning 的措辞），对 append 什么、failed_count 怎么加毫无影响。被修的那两行分支条件没有任何门。
- 复现思路: 负控输入：把 :502 与 :567 两处改回 `isinstance(result, Exception)`（缺陷原样复发，CancelledError 重新被 append 进结果列表并在 :581 `result.success` 抛 AttributeError），本文件 3 条 T-new-5 门 + 既有 tests/unit/test_batch_orchestrator.py:900 全绿。
- 三视角裁决:
  - `counterexample` → **支持**：无法举出任何能区分「修复态」与「把 :502/:567 改回 isinstance(result, Exception)」的输入。逐条核实：(1) batch_orchestrator.py 两处调用点里 kind 只进 logger.error/logger.warning 的措辞，append 与 failed_count 不受 kind 影响 —— 真修复是分支条件本身；(2) 本文件三条 T-new-5 门：:226 只断言 asyncio 自身语义、不 import 生产符号，:248/:257 直接调模块级纯函数 _classify_gather_result，调用点回退不改这个函数 ⇒ 三条恒绿；(3) tests/unit/test_batch_orchestrator.py:900 抛的是 raise Exception("Group execution failed")
  - `already-covered` → **反驳**：发现的事实描述基本准确（`_classify_gather_result` 的返回值在 :502/:567 两处确实只决定 logger 措辞，不影响 append 什么与 failed_count；三条 T-new-5 门确实只打在纯函数与 asyncio 语义上；卡自己的 negctl-1 也只变异了纯函数本身），但它的核心主张「被修的那两行分支条件没有任何门」与它给出的负控预期「全绿」都不成立——被漏算的门是**类型检查**。

证据链：
1. `pyrightconfig.json` 是 `typeCheckingMode: "basic"`，`reportArgumentType` / `reportAttributeAccessIssue` 均为 error 级；`reportUnnecessaryTypeIgnoreComment` 为 `"warning"`。
2. 改前（
  - `scope-boundary` → **支持**：发现成立，且根因不越界。(1) 实测核实：batch_orchestrator.py:502/:567 的 `isinstance(result, BaseException)` 是本卡的真行为改动，但 `_classify_gather_result` 的返回值在两处只用于选日志文案——:502 处 kind 仅决定两条 logger.error 的措辞，append 的 GroupExecutionResult 两支完全相同；:567 处 node_results.append 与 failed_count += 1 都在 kind 判断之前、与 kind 无关，kind 只额外触发一条 logger.warning。(2) grep 实测 test_pyright_tail_behavior.py 中 `_execute_all_groups` / `_execute_group` 

### 8. [MEDIUM] `backend/tests/unit/test_pyright_tail_behavior.py` :: `test_resolve_intent_model_falls_back_without_config` (:82)

- 维度: `gate-quality` · 反驳票: **0/3**
- 主张: 断言把函数输出与函数自己的常量 `_INTENT_FALLBACK_MODEL` 相比（两值同源），锁不住卡文声称的「与改前的可见行为一致」—— 改前写死的是字面量 `gemini/gemini-2.0-flash`，全仓没有任何断言把该常量钉在这个值上。同型问题在 :69：`assert resolved == format_litellm_model("anthropic", "claude-sonnet-5")` 两侧都出自同一个 `format_litellm_model`，格式化写错时两侧同时错、门照样绿。
- 复现思路: 对照输入：把 agent_routing_engine.py:207 的 `_INTENT_FALLBACK_MODEL` 改成 `"x/y"`（意图分类回落到一个不存在的模型），本文件全绿。
- 三视角裁决:
  - `counterexample` → **支持**：发现成立，举不出反例。逐条核实：(1) `backend/app/services/agent_routing_engine.py:207` 的 `_INTENT_FALLBACK_MODEL = "gemini/gemini-2.0-flash"` 与改前 `except` 分支里被删掉的同一字面量逐字相同（`git diff b8500c6e 2617a930` 中 `-            model = "gemini/gemini-2.0-flash"`），所以用例 docstring 主张的「与改前的可见行为一致」指的就是这个串。(2) 全仓 grep `_INTENT_FALLBACK_MODEL` 只有 6 处生产引用（207/221/236/239/242/243）+ 测试的 2 处（:76 import、:82 断言），没有任何一处把它钉在字面量上；字面量在测试文件里
  - `already-covered` → **支持**：不 refute，但降级到 LOW，且发现的第二半（:69）不成立。\n\n实测核对（只读）：\n1) `_INTENT_FALLBACK_MODEL` 全仓引用面 = 定义行 `backend/app/services/agent_routing_engine.py:207` + `_resolve_intent_model` 内部三处（:236/:239/:242）+ 本测试文件的 import/assert（:76/:82）。`backend/tests/` 里对字面量 `gemini/gemini-2.0-flash` 的断言 = **0 条**（测试文件里唯一出现在 :54 的 docstring 注释，不是断言）；`test_agent_routing_engine.py`（579 行）零 model 断言。pyright 看不见 str→str 的值改动，backend/**
  - `scope-boundary` → **支持**：根因不越界，发现（:82 半）成立，但严重度偏高。

1) 越界判定 = 否。同源断言在 `backend/tests/unit/test_pyright_tail_behavior.py:82`，该文件由本卡 commit 2617a930 新建；常量在 `backend/app/services/agent_routing_engine.py:207`。硬边界清单点名的是 `backend/app/services/agent_service.py`，与 `agent_routing_engine.py` 是**两个不同文件**，后者正是本卡合法改动的六个 services 之一。修法 = 在本卡自己的测试文件里加一行 `assert _INTENT_FALLBACK_MODEL == "gemini/gemini-2.0-flash"`，不触任何边界文件。故不能以「越界」驳回。

2

### 9. [LOW] `backend/tests/unit/test_pyright_tail_behavior.py` :: `test_generate_embedding_reports_missing_service_without_import_error` (:312)

- 维度: `gate-quality` · 反驳票: **0/3**
- 主张: 这条门的 3 条断言里有 2 条改前改后都真：`vector is None`（旧代码 ImportError 分支同样 return None）和「降级为文本搜索」（旧日志文案里也有这 6 个字）。唯一有判别力的是 `not any("ImportError" in m ...)` —— 全部判别力压在旧日志里那个英文单词字面量上，把旧文案换个说法（如「embedding 服务缺席」）再还原死 import，门就绿了。
- 复现思路: 对照输入：还原 multimodal_service.py 的死 import 与重试循环，但把 warning 文案改成不含 ImportError 字样，三条断言全过。
- 三视角裁决:
  - `counterexample` → **支持**：发现成立，举不出反例。逐条核实（`git diff b8500c6e 2617a930 -- backend/app/services/multimodal_service.py` + `backend/tests/unit/test_pyright_tail_behavior.py:312-325`）：

1. `assert vector is None` 非判别性 — 旧代码 `except ImportError:` 分支同样 `return None`，且其下的重试循环因 except 直接 return 而不可达，两侧都只走「一条 warning + None」。
2. `assert any("降级为文本搜索" in m)` 非判别性 — 旧文案 `"向量搜索不可用（embedding service ImportError），降级为文本搜索"` 字面含这 6 个字。这条还与
  - `already-covered` → **支持**：发现成立，未被任何现有门覆盖。代码核实：改前 `except ImportError:` 分支就是 `logger.warning("向量搜索不可用（embedding service ImportError），降级为文本搜索"); return None` —— 故 `vector is None` 与 `any("降级为文本搜索" in m)` 两条断言改前改后皆真，判别力确实全压在 `not any("ImportError" in m)` 这一个英文字面量上，主张的算术完全正确。

三条覆盖候选逐一排除：
(1) 类型检查不覆盖——这是决定性的。旧死 import 行自带 `# pyright: ignore[reportMissingImports]`，正是 PYRIGHT-TAIL 卡的立卡前提（「被 pyright: ignore 掩盖的真缺陷」），即改前树在带着这个死 im
  - `scope-boundary` → **支持**：按我的裁决视角（根因是否落在本卡硬边界之外）：**不越界，因此不能以「越界」为由驳回**。

根因位置逐条核过：
1. 门本身在 `backend/tests/unit/test_pyright_tail_behavior.py:312`（本卡新增文件，411 行全是本卡的）。
2. 被测生产面在 `backend/app/services/multimodal_service.py::_generate_embedding`（本卡已改，见 `git diff b8500c6e 2617a930` 该文件 65 行改动）。
两者都**不在**硬边界清单（models/** · graphiti/entity_types.py · core/litellm_config.py · agent_service.py · api/** · learning_context_service.py 

### 10. [LOW] `backend/tests/unit/test_pyright_tail_behavior.py` :: `runtime_model_config` (:47)

- 维度: `gate-quality` · 反驳票: **1/3**
- 主张: `manager.update(original if original is not None else SystemModelConfig())` 的 else 分支是死代码：`RuntimeModelConfigManager.__new__`（litellm_config.py:115-119）在建单例时就把 `_config` 设成 `SystemModelConfig()`，property `config`（:135-137）恒非 None。更实质的是这个 fixture 为了「隔离进程级单例」真去改了全局单例，但两条用例都把 config 显式传参、没有任何断言依赖单例本身 —— 承担了污染风险却换不到覆盖面（正是 finding 1 的根因）。
- 复现思路: 门未覆盖的路径：把 fixture 改成不返回 manager、用例改调无参 `_resolve_intent_model()`，才会真正走到单例路径；当前写法下删掉 fixture 的 update 语义也不影响任何断言。
- 三视角裁决:
  - `counterexample` → **支持**：成立，无法反证。(1) 死分支：`litellm_config.py:115-119` 的 `__new__` 建单例时即置 `_config = SystemModelConfig()`；唯一另一个写者 `update()`(:127-133) 立刻解引用 `self._config.chat`，传 None 会当场崩而不会留下 None 状态；全仓 grep 无 `RuntimeModelConfigManager` 的 reset_instance / `_config = None`，唯一生产写点 `system.py:854` 传真对象，`test_system_endpoint_auth.py:139` 只 patch 函数不碰单例。举不出让 `original is None` 的调用序列 ⇒ `else SystemModelConfig()` 确为不可达。(2) 覆盖面主
  - `already-covered` → **反驳**：三条子主张逐条核过，没有一条构成缺陷。

(1)「else 分支是死代码」—— 事实成立但无失败场景。litellm_config.py:115-119 `__new__` 建单例时置 `_config = SystemModelConfig()`，property `config`(:135-137) 声明 `-> SystemModelConfig`（非 Optional），全仓 grep 无任何 `_config = None` 赋值点，故 `original is not None` 恒真。但这是 test-only teardown 里的一个防御表达式：有它没它 fixture 都把同一个对象还原回去，`manager.update(original)` 行为逐字节相同。举不出「什么输入 → 什么错误输出」，这是风格 nit，不是缺陷。另注：pyrightconfig.json 
  - `scope-boundary` → **支持**：根因不越界，发现成立，维持 LOW。(1) 死分支已核实：litellm_config.py:115-119 的 __new__ 在建单例时即置 _config = SystemModelConfig()，config property (:135-137) 标注为 -> SystemModelConfig 非 Optional；对 backend/app + backend/tests 全仓 grep，无 `_config = None`、无 `update(None)`、无 `RuntimeModelConfigManager._instance = None` 重置站点 ⇒ original 恒非 None ⇒ test_pyright_tail_behavior.py:47 的 `else SystemModelConfig()` 不可达。(2) 更实质的那半也成立：两条用例 (:

### 11. [HIGH] `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_pyright_tail_behavior.py` :: `_attached_names` (:385)

- 维度: `ast-gate-blindspots` · 反驳票: **0/3**
- 主张: 门只取赋值语句的左侧 target.attr，从不看 stmt.value，因此「挂了名字但挂错函数」这一类错误两条 test_type_checking_* 全绿——而这恰是门自称要锁的「ext 是运行期真相」。
- 复现思路: 负控输入：把 exam_service_ext.py:960 改成 `ExamService.resume_exam = pause_exam`（复制粘贴典型错法），declared 名集合与 attached 名集合仍完全相等，test 1 仍拿 declared['resume_exam'] 去比 ext 里那个未被挂载的 resume_exam def，两条门都不红，运行期 resume 却执行 pause。
- 三视角裁决:
  - `counterexample` → **支持**：发现成立，且我举不出任何反例。逐条核实：(1) test_pyright_tail_behavior.py:379-385 的 _attached_names() 只遍历 stmt.targets 取 target.attr，全程不读 stmt.value——代码原文即 `names.add(target.attr)`；(2) _ext_signatures()(:355-366) 按 def 自身 fn.name 建键，与 attach 实际绑定的值无任何关联。把 exam_service_ext.py:960 改成 `ExamService.resume_exam = pause_exam` 后：attached 名集合仍是原 11 个左值名（targets 未动）⇒ test_type_checking_declaration_names_match_attach_assignmen
  - `already-covered` → **支持**：发现属实，未被任何现有门覆盖。实证：(1) test_pyright_tail_behavior.py:369-386 的 _attached_names 只取 ast.Assign 的 target.attr，全函数不读 stmt.value；_ext_signatures(:355)/_declared_signatures(:337) 同样纯按名字建映射。负控输入 `ExamService.resume_exam = pause_exam`（exam_service_ext.py:960）下三个 helper 输出逐字不变 ⇒ 两条 test_type_checking_* 全绿，主张成立。(2) pyright 覆盖不到：exam_service.py:98/:100 与 exam_service_ext.py:540/:545 的 pause_exam / resume_exam
  - `scope-boundary` → **支持**：按我的裁决轴（根因是否越界）：**不越界，本卡可修且应修**。

1) 技术主张属实（逐条核过，非采信）。`backend/tests/unit/test_pyright_tail_behavior.py:368-383` 的 `_attached_names()` 只遍历 `stmt.targets`，取 `ast.Attribute.attr`（`target.value.id == "ExamService"`），**全程不读 `stmt.value`**。两条门因此都看不见绑定身份：
   - `test_type_checking_declarations_match_ext_signatures`（:388）比的是 `_declared_signatures()`（解析 `backend/app/services/exam_service.py` 的 `if TYPE_CHEC

### 12. [MEDIUM] `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_pyright_tail_behavior.py` :: `_declared_signatures` (:346)

- 维度: `ast-gate-blindspots` · 反驳票: **0/3**
- 主张: TYPE_CHECKING 块内只收 FunctionDef/AsyncFunctionDef，非 def 语句（变量注解 / 赋值）被静默丢弃，且 len(declared)==11 这条计数判据也只数 def，看不见它们。
- 复现思路: 负控输入：在 exam_service.py:79 的 `if TYPE_CHECKING:` 块里加一行 `archive_exam: Callable[..., None]`——pyright 从此认为 ExamService 有这个属性、调用点不再报 attribute-unknown，但 declared 仍是 11 个名、declared==attached 仍成立，两条门全绿，运行期 `svc.archive_exam` 直接 AttributeError。
- 三视角裁决:
  - `counterexample` → **支持**：发现成立，无法构造反例。核实：test_pyright_tail_behavior.py:345-346 的循环只收 FunctionDef/AsyncFunctionDef，无 else、无「意外语句」断言，AnnAssign/Assign 被静默丢弃 ⇒ 既不进 declared，也不影响 len(declared)==11(:398) 和 declared==attached(:406-410)。四条反驳路径全部失败：(1) grep -rn TYPE_CHECKING backend/tests/ 只命中本文件 + 无关的 support/lifespan.py，grep attach_to_exam_service 只有定义与 exam_service_ext.py:970 的自动调用，无第二道门比对运行期属性；(2) 根 pyrightconfig.json 为 typeChe
  - `already-covered` → **支持**：发现成立，未被任何现有门覆盖。逐条核实：(1) test_pyright_tail_behavior.py:350 的内层循环只收 `isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))`，AnnAssign/Assign 无 else 无 raise 直接落空；(2) 两条门共用该 helper——`len(declared)==11`(:398) 数的是 def 字典，`set(_declared_signatures())`(:406) 是同一字典的键，都看不见非 def 声明；(3) 门未覆盖的路径恰好是危险方向：新增一条 AnnAssign 后 len 仍 11、declared==attached 仍成立，而反方向(挂载未声明)会触发——即第二条门声称要挡的「声明但未挂载 ⇒ 运行期 AttributeError」正是漏
  - `scope-boundary` → **支持**：根因在界内，不属越界。核实过程：(1) 主张属实——backend/tests/unit/test_pyright_tail_behavior.py::_declared_signatures 的 `for fn in node.body: if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))` 确实只收 def，AnnAssign/Assign 被静默丢弃；`len(declared) == 11` 数的是过滤后的残留，同样看不见它们；`_attached_names()` 读的是另一个文件（exam_service_ext.py 的 attach 赋值），所以 declared==attached 也照样成立。三条判据全绿。pyright 把 `if TYPE_CHECKING:` 视为真分支，类体内的 AnnAssign

### 13. [MEDIUM] `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_pyright_tail_behavior.py` :: `_attached_names` (:376)

- 维度: `ast-gate-blindspots` · 反驳票: **0/3**
- 主张: _attached_names 用 ast.walk 递归整个 attach_to_exam_service 子树，而 _declared_signatures/_ext_signatures 用非递归的 cls.body/tree.body——这个不对称让「条件分支里的」或「嵌套 def 里从不执行的」挂载语句也被算成已挂载。
- 复现思路: 门未覆盖的路径：把 exam_service_ext.py:962 的 `ExamService.get_cognitive_load_message = get_cognitive_load_message` 包进 `if os.getenv("ENABLE_COGLOAD"):`（或塞进 attach 体内一个从不调用的嵌套 def），ast.walk 照样命中该 Assign，declared==attached 成立、门绿，而真实进程按环境变量缺省不挂载该方法。
- 三视角裁决:
  - `counterexample` → **支持**：发现成立，举不出反例。核实结果：(1) 不对称属实——`_declared_signatures` 走 tree.body→cls.body→node.body 三层显式非递归，`_ext_signatures` 只走 tree.body，唯独 `_attached_names`(:376) 用 ast.walk(fn) 递归全子树，会命中 if/for/with 块内以及嵌套 def 内的 Assign。(2) 方向是 fail-open：def 若挪进条件块，`_ext_signatures` 漏掉它会让签名门直接红（fail-closed，安全）；只有 `_attached_names` 把「从不执行的赋值」算成已挂载，使 declared==attached 绿而运行期 ExamService 上没有该属性。docstring(:405) 声称测的是「真正挂上去的名字集合」，判据取
  - `already-covered` → **支持**：发现成立，且现有门/测试/pyright 均未覆盖它描述的场景，但应降为 LOW（当前无假绿，属潜在门强度缺口）。

【事实核实】test_pyright_tail_behavior.py:376 确为 `for stmt in ast.walk(fn)`（递归整棵 attach_to_exam_service 子树），而 _ext_signatures 用 `tree.body`、_declared_signatures 用 `cls.body` + 一层 `node.body`，均非递归。不对称属实。

【当前无假绿】AST 实测 exam_service_ext.py:932-966 的 attach_to_exam_service 直接子节点为 ['Expr','ImportFrom', Assign×11]，ast.walk 的 Assign 数 = 11 = fn.body 的
  - `scope-boundary` → **支持**：根因不越界，但发现被高估，建议降到 LOW。

(1) 越界判定 = 否。不对称完全落在本卡自己的新文件里：`backend/tests/unit/test_pyright_tail_behavior.py:376` 用 `for stmt in ast.walk(fn)` 递归整棵 attach 子树，而 `:339/:342/:345`（tree.body → cls.body → node.body）与 `:364`（tree.body）都是非递归。修法是把 `ast.walk(fn)` 换成 `fn.body`（或两者都取并断言相等），一行，全在 `tests/unit/**`——不在硬边界清单内。实测本卡确实没碰边界文件：`git --no-pager diff --no-color --stat b8500c6e 2617a930 -- backend/app/services

### 14. [MEDIUM] `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_pyright_tail_behavior.py` :: `_declared_signatures` (:347)

- 维度: `ast-gate-blindspots` · 反驳票: **0/3**
- 主张: 比较元组只含 (is_async, ast.unparse(args), ast.unparse(returns))，装饰器列表 fn.decorator_list 完全不进比较，于是 ext 侧加装饰器改变绑定语义时门看不出差异。
- 复现思路: 负控输入：给 exam_service_ext.py:592 的 get_cognitive_load_message 加 `@staticmethod`（或任一 functools 包装器），args/returns 文本一字不变、is_async 不变 ⇒ test 1 的 mismatch 仍为空、门绿，运行期 `svc.get_cognitive_load_message(5)` 却因不再传 self 而 TypeError。
- 三视角裁决:
  - `counterexample` → **支持**：发现成立，举不出反例。实测三点：(1) test_pyright_tail_behavior.py:347-351 与 :359-365 的比较元组确为 (is_async, ast.unparse(args), ast.unparse(returns)) 三元，decorator_list 不在内；全文件 grep 'decorator|staticmethod|classmethod|lru_cache|functools' rc=1 零命中，无补偿判据。(2) 负控可行：exam_service_ext.py:592 加 @staticmethod 后 args/returns/is_async 文本一字不变 ⇒ test 1 的 mismatch 恒空、门绿；而 attach_to_exam_service():962 是裸赋值 ExamService.get_cognitive_
  - `already-covered` → **支持**：发现成立（未被任何现有门覆盖），但严重度应降。

一、机制核实（代码位置确凿）
- `backend/tests/unit/test_pyright_tail_behavior.py:347-351`（`_declared_signatures`）与 `:359-363`（`_ext_signatures`）的比较元组确实只有 `(isinstance(fn, ast.AsyncFunctionDef), ast.unparse(fn.args), ast.unparse(fn.returns))`，`fn.decorator_list` 不进比较；`_attached_names`（:369-386）只收 `ExamService.<name> = ...` 的属性名，也不看 RHS 形态。装饰器加在 ext 侧时三个提取器输出全不变 ⇒ `test_type_checking_decl
  - `scope-boundary` → **支持**：发现成立，且根因未越界。(1) 实测 `_declared_signatures` (:347) 与 `_ext_signatures` (:366) 的比较元组确为 `(is_async, ast.unparse(fn.args), ast.unparse(fn.returns))`，`fn.decorator_list` 两侧均不进比较。(2) 负控成立：给 exam_service_ext.py:592 `get_cognitive_load_message` 加 `@staticmethod`，args/returns 文本与 is_async 一字不变 ⇒ test 1 的 mismatch 仍为 {} 门绿；运行期 attach_to_exam_service() (:962) 把 staticmethod 对象挂到类上，唯一生产调用方 backend/app/api/v1/e

### 15. [LOW] `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_pyright_tail_behavior.py` :: `test_type_checking_declaration_names_match_attach_assignments` (:404)

- 维度: `ast-gate-blindspots` · 反驳票: **1/3**
- 主张: 门只判 declared 与 attached 两个集合相等，对「ext 里新增了以 self 为首参的模块级 def、但既没声明也没挂载」这一情形两侧同时为空缺 ⇒ 相等成立 ⇒ 门全盲（反向的「挂了没声明」「声明了没挂」才会红）。
- 复现思路: 门未覆盖的路径：在 exam_service_ext.py 顶层加 `async def archive_exam(self, exam_id: str) -> None: ...` 而不改 attach、不改 TYPE_CHECKING 块，两条门均绿；该缺口目前只靠调用点的 pyright attribute-unknown 兜底，本文件的行为门不提供任何覆盖。
- 三视角裁决:
  - `counterexample` → **支持**：无法举出反例，发现成立。实测核实：(1) test_pyright_tail_behavior.py:404 的判据是 declared == attached，declared 只来自 exam_service.py 的 TYPE_CHECKING 块、attached 只来自 attach_to_exam_service 体内赋值；(2) 另一条 :389 只按 declared.items() 单向遍历 + len(declared)==11，_ext_signatures() 仅通过 ext.get(k) 被反查，从不枚举 ext 自身新增项。故「ext 新增 self 首参顶层 def，既不声明也不挂载」对两个集合与那个计数都无影响，两条门均绿——主张的「两侧同时为空缺 ⇒ 相等成立」属实。当前存量不受影响（AST 普查：ext 15 个顶层 def，11 个 self 首参全部
  - `already-covered` → **反驳**：机制描述属实（两侧同时缺位 ⇒ 集合相等 ⇒ 门不红），但这条发现站不住，三点：

(1) 有害形态已被现有强制门覆盖。`pyrightconfig.json` 是 `typeCheckingMode: "basic"`（`reportAttributeAccessIssue` 未被覆写 = error）、`include: ["backend/app", "tests"]`。`backend/app/services/exam_service.py:86-87` 的注释本身就写明这 11 条 TYPE_CHECKING 声明存在的目的是「消掉 api/v1/endpoints/exam.py 的 attribute-unknown」，而调用点确实是实例属性访问：`backend/app/api/v1/endpoints/exam.py:245 svc.generate_hint(...)
  - `scope-boundary` → **支持**：根因不越界，发现成立。实测三点：(1) :404 门只断言 declared==attached，ext 侧「既没声明也没挂载」在两集合同时缺席⇒相等成立，确实全盲；:389 门迭代 declared.items() 且 assert len(declared)==11 锁的是声明侧数量，新增未声明的 ext def 同样不红 —— 两条门都不消费「ext 有而两侧都没有」的差集，尽管 _ext_signatures() helper 已把全部 14 个模块级 def 抽出来了。(2) 发现里说的「靠调用点 pyright 兜底」只兜住一半：ext 的 def 全部是 self 无注解，ext 内部的 self.<name>(...) 调用（exam_service_ext.py:542、:547 实例）在 pyright 下是 Unknown 上的属性访问不报错，只有 api/v1/en

## 二 被反驳（≥2 票判死，登记备查）

1. [HIGH] `batch_orchestrator.py::_execute_all_groups / _execute_group` — 2/3 票反驳
   - 主张: 本卡唯一的语义改动（502、567 两处 `isinstance(result, Exception)` → `isinstance(result, BaseException)`，以及 574 行 `str(result) or type(result).__name__` 回落）没有任何测试覆盖，而 131 行 `_classify_gather_result` 的 docstring（138-139 行）把 `test_gather_return_exceptions_surfaces_cancellation_as_non_exception` 称作「回归门」，该测试（tests/un
   - 反驳（`counterexample`）: 裁定：refuted=true（HIGH 不成立；残余面已按协议登记，且发现自述的负控本身不成立）。

**1. 发现提出的负控在本仓是红的，不是「变异存活」。**
`2617a930` 在改 isinstance 的同时**删掉了三个 `# pyright: ignore`**（原 :482 `reportArgumentType`、:540 `reportArgumentType`、:541 `reportAttributeAccessIssue`，见 diff）。`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/
   - 反驳（`already-covered`）: 这条 HIGH 站不住：它声称的负控恰好被本仓的**强制类型门**拦下，而它没跑那道门。

1. **负控「把 502/567 改回 `isinstance(result, Exception)`」会让 `pyright app` 变红，不是「变异存活」。** 仓内直接证据在被删的那三行注释里：改前 `backend/app/services/batch_orchestrator.py` 的 else 分支就是 `processed_results.append(result)  # pyright: ignore[reportArgumentType]`、`node_results.appe

2. [LOW] `batch_orchestrator.py::_execute_group` — 2/3 票反驳
   - 主张: 同一「节点被取消」状态在同一文件里产出两套互不相同的字符串：gather 取消走 574/575 行得到 `error_message="CancelledError"` + `error_type="CancelledError"`，而 `_execute_node_with_semaphore` 的 `_cancel_requested` 预检（655-656 行）得到 `error_message="Cancelled"` + `error_type="CancellationError"`；`error_message` 会经 `_aggregate_results` 的 `error
   - 反驳（`counterexample`）: 发现站不住脚，三点各自独立足以否定：

(1) 复现思路描述的「对照输入」在仓内不可构造。`cancel_session()`（batch_orchestrator.py:1189）只写 `self._cancel_requested[session_id] = True`，从不 cancel 任何 task。全仓唯一的取消源是 :351 的 `asyncio.wait_for(self._execute_all_groups(...), timeout=timeout)`，它取消整个 `_execute_all_groups` task —— 这会让外层 gather(:495) 进入 `_
   - 反驳（`already-covered`）: 不成立（无可证消费面 + 复现路径不存在）。核实：(1) `NodeExecutionResult.error_type` 全仓零读取——只在 :575/:656/:853 写，`grep -rn error_type backend/app` 其余命中全在 middleware/main.py 的无关字段，故「error_type 两套取值」不可观测；(2) `_aggregate_results` :1107-1112 只把 node_id + error_message 放进 errors_list，而 `grep -rn error_message frontend/src` 0 命中

3. [LOW] `batch_orchestrator.py::_classify_gather_result` — 2/3 票反驳
   - 主张: `_classify_gather_result` 的返回值在生产路径上只用于挑日志文案：两个调用点（503、568）都写在 `if isinstance(result, BaseException):` 内部，所以 157 行的 `return "ok"` 在生产恒不可达，只有 `test_classify_gather_result_treats_real_result_as_ok` 能走到；而 `"cancelled"` 与 `"failed"` 在 `GroupExecutionResult.status`（恒 "failed"）、`NodeExecutionResult.error_
   - 反驳（`already-covered`）: 事实核对通过，但三条都不构成缺陷：

1) 「`return "ok"` 生产恒不可达 = 死分支」被现有类型检查覆盖且**要求**。函数签名是 `-> Literal["ok","failed","cancelled"]`（batch_orchestrator.py:131）；去掉 :157 的 `return "ok"` 后函数末尾隐式返回 `None`，pyright 报 `reportReturnType`，而本批候选树合入门是 `pyright app` = 0 errors。也就是说这个分支不是可删的死码，而是全函数（total function）契约的必要出口，并由 `test_
   - 反驳（`scope-boundary`）: 发现的五条事实全部核实为真（:131 定义、:157 的 "ok" 在两个调用点 :503/:568 恒不可达、status 硬编码 "failed"、error_type 不经本函数、final_status :365-383 只看 _cancel_requested 与计数且本卡未改），但它不构成本卡缺陷，理由有二。(1) 无行为后果且语义上本就该如此：用户发起的取消走 :650-657 的 _cancel_requested 标志、返回正常 NodeExecutionResult(error_type="CancellationError")，根本不产生 CancelledError；w

4. [MEDIUM] `intelligent_parallel_service.py::IntelligentParallelService.retry_single_node` — 3/3 票反驳
   - 主张: 同一条新可达路径上 result.success 被无条件当作「已生成」：agent_service.py:2739-2751 在 check_input 判定输入被注入检测拦截时返回 success=True（result={"response": SAFETY_BLOCK_INPUT_MESSAGE}），于是被安全拦下的节点重试也会报 status=success 并附上拼接的 file_path（该分支改前同样因 2741 行 agent_type.value 对裸 str 抛 AttributeError 而不可达）。返回 success=True 的那一侧在 agent_servic
   - 反驳（`counterexample`）: 裁定 refuted=true（根因越界 + 非本卡可隔离的缺陷），但如实说明：我举不出"安全拦截时不报 success"的反例——拦截路径确实会走成 status=success。推翻的是它的归属与可修性，不是它的可达性。

核实到的事实（均为只读实测）：

1. 根因在硬边界文件内。success=True 由 backend/app/services/agent_service.py:2745-2751 产出（`AgentResult(success=True, result={"response": SAFETY_BLOCK_INPUT_MESSAGE})`），agent_servic
   - 反驳（`already-covered`）: 事实部分属实，但站不住的是「这是本卡应记的缺陷」这一主张。逐条核实：

1) 事实核对（全部属实）：agent_service.py:2737-2752 在 check_input 判定 is_blocked 时确实 `return AgentResult(success=True, result={"response": SAFETY_BLOCK_INPUT_MESSAGE})`；AgentType 是 `str, Enum`（agent_service.py:139），裸 str 无 `.value`，故改前 2741 行 f-string 里的 `agent_type.value` 必抛
   - 反驳（`scope-boundary`）: 根因越界，应登记另立卡，不作本卡缺陷。

1) 根因位置在硬边界文件内，且无本卡可用的替代判据。`success=True` + `result={"response": SAFETY_BLOCK_INPUT_MESSAGE}` 的决定在 backend/app/services/agent_service.py:2737-2751（该文件在本卡硬边界清单内），同一约定还重复在 clients/claude_client.py:232-236,481-484 与 clients/gemini_client.py:414-418,718-721,814-818（本卡也未改）。关键是 AgentR

5. [LOW] `wikilink_graph_service.py::_resolve_path` — 3/3 票反驳
   - 主张: 守卫覆盖面比改前小：旧实现把 `str(source)` 一并放在 `except Exception` 内，新实现只把索引查找包进 try，`Path(source).as_posix()` 落在 try 之外且异常元组不含 ValueError；索引值若不是 path-like，`Path(source)` 抛出的 TypeError 会逃出 `_resolve_path` 并穿过 `get_neighbors` 冒泡（改前这一路是静默回落）。obsidiantools 对 `md_file_index` 提供公开 setter（api.py:199-201），但全仓无非-Vault 赋值
   - 反驳（`counterexample`）: 不成立。（1）可达性：`_vault` 全仓仅两处赋值（wikilink_graph_service.py:40 `None`、:79 `Vault(Path(vault_path)).connect()`），无第三处；`md_file_index` 在 backend/app+tests+scripts 只有 3 处命中（服务自身 :317 docstring、:331 调用点、test_pyright_tail_behavior.py:137 docstring），obsidiantools 的公开 setter（api.py:199-201）零调用；真 Vault 的索引值确证为 Pat
   - 反驳（`already-covered`）: 站不住（已被现有门覆盖 + 前提不成立）。① 类型门已覆盖：obsidiantools api.py:194-196 声明 `md_file_index -> dict[str, Path]`，`connect()`(api.py:463 `return self`) 使 `self._vault` 推断为 `Vault | None` —— 这一点由本卡删掉的那条 `# pyright: ignore[reportAttributeAccessIssue]` 反证（receiver 若是 Any，pyright 根本不会报 attribute access 错）。因此 wikilink_gr
   - 反驳（`scope-boundary`）: 驳回，但**不是**以越界为由——越界主张本身站不住脚，需先澄清：wikilink_graph_service.py 不在本卡硬边界清单内（清单中的 services 仅 agent_service / learning_context_service / exam_service*），且发现引用的「api.py:199-201」实为 backend/.venv/lib/python3.14/site-packages/obsidiantools/api.py（第三方库），与 backend/app/api/** 无关，属路径混淆。若真是缺陷，本卡可原地一行修好。

驳回理由在实质面：(1) 

6. [LOW] `wikilink_graph_service.py::_resolve_path` — 3/3 票反驳
   - 主张: except 分支静默、零日志，复刻了本卡要修的那个缺陷机理：原缺陷正是「`get_source_path` 不存在 ⇒ AttributeError 被静默吞 ⇒ 函数常年退化成扁平 `<key>.md` 且无人察觉」，新实现对同一次属性访问仍然静默吞 AttributeError（同文件 `_resolve_vault_path` 479-485 行在异常时会 `logger.warning`，此处没有）。上游一旦改名或换实现，函数会再次悄悄退回恒回落状态，外部没有任何可观测信号。
   - 反驳（`counterexample`）: 裁决：不成立（refuted）。逐条核实后，这条发现的两个支柱主张（「同一机理被复刻」「外部无任何可观测信号」）都被具体调用序列推翻。

【1】该 except 分支在当前依赖下没有输入能触达（不是「未被拦下的输入」，是不存在的输入）
- backend/.venv/.../obsidiantools/api.py:195-201 —— `md_file_index` 是**带 getter+setter 的公开 property**，其后备字段 `self._md_file_index` 在 `Vault.__init__` 第 141 行就赋好（不在 `connect()` 里），且被列在
   - 反驳（`already-covered`）: 站不住：该场景已被现有类型门 + 新增行为门双重覆盖，且发现对旧缺陷机理的归因不实。

(1) 类型门覆盖「上游改名」。wikilink_graph_service.py:40 `self._vault = None` 与 :79 `self._vault = vault`（vault 来自 `Vault(Path(...)).connect()`，obsidiantools/api.py:463 的 connect 虽无注解但 `return self` ⇒ 推断为 Vault），故 pyright 推断声明类型为 `Vault | None`，被 :328 的 `is None` 守卫窄化
   - 反驳（`scope-boundary`）: 不越界，但发现的核心主张被代码证伪 → refuted。

(1) 越界判定：否。`backend/app/services/wikilink_graph_service.py` 不在本卡硬边界清单（models/** · entity_types.py · litellm_config.py · agent_service.py · api/** · learning_context_service.py · exam_service*）内；:332 的 except 分支就在本卡已改的文件里，补一行 logger.warning 是纯 in-file 改动。不能以「越界」驳回。

(2) 

7. [LOW] `error_classifier.py::ErrorClassifier.classify_with_pedagogy` — 2/3 票反驳
   - 主张: `classify_with_pedagogy` 声明并在 docstring 中承诺 `node_id`（"Canvas 节点 ID (写入 frontmatter / Graphiti 用)"）和 `session_id`（"对话 session ID"）两个参数，但函数体（行 259-272）从未引用它们，返回的 `ClassifiedError` 模型也没有对应字段 —— 参数被静默吞掉，属 DD-13 名实不一致；与本卡修的 `created_at=` 静默丢弃是同一族形态（只是这次不是 pydantic extra='ignore'，而是形参根本没用）。
   - 反驳（`counterexample`）: 事实属实但不构成本卡缺陷。核实：error_classifier.py:233-272 的 classify_with_pedagogy 确实只用 error_description/context/sub_tags，ClassifiedError(:144-166) 无 node_id/session_id 字段。但三点使其站不住脚：(1) 该函数**不在本卡 diff 面内**——git diff b8500c6e 2617a930 -- backend/app/services/error_classifier.py 只新增 _build_misconception() 并改写 clas
   - 反驳（`already-covered`）: 事实核对属实但不构成缺陷。(1) 不在本卡改动面：`git diff b8500c6e 2617a930 -- backend/app/services/error_classifier.py` 只改了 `classify()` 与新增的 `_build_misconception()`；`classify_with_pedagogy`(:233) 是未改动的既有代码，且从未带 `# pyright: ignore`，不属本卡「七项被 ignore 掩盖的缺陷」。(2) 无任何输入产生错误行为：`ClassifiedError`(:144-165) 按设计就是纯分类裁决，node/sessio

8. [MEDIUM] `multimodal_service.py::MultimodalService.get_health_status` — 2/3 票反驳
   - 主张: 本卡把 `_generate_embedding` 固化成「恒返回 None」之后，同文件 `get_health_status` 仍按 `has_store and lancedb_connected` 报 `vector_search_available=True` / `capability_level="full"`，健康端点对外宣称的能力代码永远交付不了（改前是运行期 ImportError 造成的同一结果，本卡把它变成了静态可证的恒真，却没有同步修正或登记这处名实不符）。
   - 反驳（`counterexample`）: 【对照输入即可推翻「本卡造成」这一部分，剩余部分落在越界/已登记面】

事实核查（都在代码里）：
1. 主张的技术事实成立但**与本卡无关**。`git --no-pager diff --no-color b8500c6e 2617a930 -- backend/app/services/multimodal_service.py` 全文只有三处：删 `import asyncio`、L111-115 常量注释、`_generate_embedding`（L1364-1394）。`get_health_status`（L1006-1063，含 L1051 `vector_search_ava
   - 反驳（`already-covered`）: 我按「现有门/测试是否已覆盖」这个角度查了，结论是**没有任何门覆盖**：test_multimodal_fixes.py:429-451 不是门而是把 full 锁死；test_multimodal.py:93-124 只手工构造响应模型、从不调 get_health_status；本卡新测 test_pyright_tail_behavior.py:308-319 只测 _generate_embedding；pyright 看不到这类语义错配。发现里的事实也全部核实为真（:1049-1052 只看 has_store and lancedb_connected；models/multim

9. [LOW] `multimodal_service.py::MultimodalService.search` — 2/3 票反驳
   - 主张: 退役只做了一半：`_generate_embedding` 现在无分支地 `return None`（全仓无 MultimodalService 子类、无对该方法的 monkeypatch，已 grep 确认），于是 search() 的 :1296 `if query_vector:` 整段（:1296-:1321）成为静态不可达死代码——其中包含全仓唯一的 `multimodal_store.search()` 调用点、唯一的 `query_processed=True` 与唯一的 `search_mode="vector"` 产出点；:1323 的 `except Exception` 
   - 反驳（`already-covered`）: 站不住，三条独立理由：

(1) 不是本 commit 引入的。改前 `git show b8500c6e:backend/app/services/multimodal_service.py` 的 `_generate_embedding` 开头就是 `try: from agentic_rag.embedding.embedding_service import get_embedding_service` / `except ImportError: ... return None`。我实测 `ls backend/lib/agentic_rag/` 无 `embedding` 子包、`
   - 反驳（`scope-boundary`）: 按我的裁决轴先给诚实结论：**根因并不越界**。`backend/app/services/multimodal_service.py` 不在本卡硬边界清单；补实现要动的 `app/graphiti/embedder_factory.py`（不是被禁的 `entity_types.py`）与 `backend/lib/agentic_rag/storage/multimodal_store.py` 同样不在清单。所以不能用「越界，需另立卡」这个理由。

但这条发现仍应 refuted，理由是「不成立（非本卡引入）+ 已被覆盖」三点，均在代码里核实过：

1. 死代码先于本卡存在，本卡未引入。`

10. [LOW] `multimodal_service.py::EMBEDDING_RETRY_DELAY / EMBEDDING_MAX_RETRIES 退役注释块` — 3/3 票反驳
   - 主张: 注释断言「全仓再无引用」，但 docs/stories/36.13.story.md:46 仍以 `| multimodal_service.py:1388 | 嵌入重试 | EMBEDDING_RETRY_DELAY | ✅ 常量 |` 把它登记为在用常量。代码面（backend/app、backend/tests、backend/scripts、backend/lib、frontend、sidecar）确实零引用、`import asyncio` 也确实全文件零残留（已独立 grep 含 getattr/importlib/star-import/patch 目标），但 docs/ 这条盘
   - 反驳（`counterexample`）: 发现的 grep 事实为真（docs/stories/36.13.story.md:46 确有 1 条命中），但由此推出「注释失实 / 会误导第十六批」不成立。

1) 对照输入（决定性）：该表位于 `### 代码现实检查 (2026-02-10 验证)` 标题下，所在 story `## Status` = `Done`，Change Log 止于 2026-02-11 —— 是冻结的「before」快照，不是在用清单。把发现自己的判据套到它上面三行的兄弟行：`| review_service.py:368 | "Simulate work" | 0.2s | 🔴 应删除 |` —— 该 s
   - 反驳（`already-covered`）: 站不住。(1) 注释主张的是**代码引用面**，而该面确实为 0 —— 全仓（排除 _bmad-output/.git/node_modules）仅 1 条命中，且是一个 markdown 表格单元格，不是符号引用；`import asyncio` 也确已全清。(2) 关键证伪：那条 doc 行在**本卡动手之前就已经失实**。`docs/stories/36.13.story.md:46` 锚的是 `multimodal_service.py:1388`，而在 b8500c6e（本卡语义改动前）`await asyncio.sleep(EMBEDDING_RETRY_DELAY)` 实际在 
   - 反驳（`scope-boundary`）: 【先答我的分派角度：不越界，但据此不能判缺陷】docs/stories/36.13.story.md 不在本卡硬边界清单（models/** · entity_types.py · litellm_config.py · agent_service.py · api/** · learning_context_service.py · exam_service*.py）之内，所以这条**不能**按「根因越界」驳回。我改为按「不成立」驳回，依据是实测：

1. 事实核对（我自己跑的，不采信主张）：`grep -rn -e EMBEDDING_RETRY_DELAY -e EMBEDDING_MA

11. [HIGH] `test_pyright_tail_behavior.py::test_resolve_intent_model_uses_configured_scoring_model` — 2/3 票反驳
   - 主张: 两条 T-new-3 门都显式传 config 入参，生产唯一调用形态 `_resolve_intent_model()`（agent_routing_engine.py:575 无参调用）的 `config is None` 分支零覆盖 —— 而本卡要修的那个失效模式恰恰全在该分支里：`agent_routing_engine.py:229` 的 `from app.core.litellm_config import get_runtime_model_config` 仍被 `except (ImportError, AttributeError, RuntimeError)` 吞掉并静默
   - 反驳（`counterexample`）: 发现的复现思路本身可被证伪，且「失效模式全在未覆盖分支里」的主张不成立。

(a) 提出的负控输入（把 agent_routing_engine.py:229 的 import 名改成不存在的符号）**不是**「全仓门全绿」：pyright 恰恰对这一行报 reportAttributeAccessIssue——改前代码必须在该行挂 `# pyright: ignore[reportAttributeAccessIssue]` 才过得去（diff 里原样可见），这就是它当初进 PYRIGHT-TAIL 的原因。而 pyright 0 errors 是两道硬门：lefthook `python-
   - 反驳（`already-covered`）: 场景已被 pyright 门覆盖，发现的复现思路自身不成立。

1) 复现思路claim「把 agent_routing_engine.py:229 导入名改成不存在的符号 ⇒ 全仓其它门全绿」为假。仓内直接反证：改前的同一行（`git show b8500c6e:backend/app/services/agent_routing_engine.py` L531）是 `from app.core.litellm_config import get_litellm_config  # pyright: ignore[reportAttributeAccessIssue]` —— 原缺陷之所以能

12. [MEDIUM] `test_pyright_tail_behavior.py::test_gather_return_exceptions_surfaces_cancellation_as_non_exception` — 3/3 票反驳
   - 主张: 作者只标注了 3 条「无判别力」用例，实际至少漏标 2 条：本条只断言 CPython 自身语义（CancelledError 继承关系 + gather 的收敛行为），不引用 batch_orchestrator 任何符号；`test_agent_type_accepts_alias_values_and_rejects_unknown`（:274）只断言 `app/services/agent_service.py` 的 AgentType 枚举本身，而该文件在本卡硬边界内、一行未改。后者的 docstring 还写着「转换是有判别力的」，与事实相反 —— 它测的不是本卡加的那段转换。
   - 反驳（`counterexample`）: 发现的锚点主张（:226 漏标）在锚点本身即被证伪，且「至少漏标 2 条」的计数不成立（实为 1 条）。

对照输入（不需要跑任何东西，直接读锚点）：
1. `backend/tests/unit/test_pyright_tail_behavior.py:231-234` 的 docstring 原文就是「这条不依赖本卡任何新符号——它证明既有两处 `isinstance(result, Exception)` 分支筛不掉取消,缺陷输入面不是假想出来的」。这正是发现声称被隐瞒的那条性质，逐字写在发现指定的行上。
2. `_bmad-output/验收单/UAT-CARD-PYRIGHT-TA
   - 反驳（`already-covered`）: 发现的主体主张与事实不符。(1) `test_gather_return_exceptions_surfaces_cancellation_as_non_exception`（test_pyright_tail_behavior.py:226）并非漏标——它在自己的 docstring（:230「这条不依赖本卡任何新符号」）和 UAT 判别力表（UAT-CARD-PYRIGHT-TAIL-BEHAVIOR-2026-09-18.md:160「不依赖本卡任何新符号，证明缺陷输入面真实存在」）里各标注一次；该表共 4 行显式条目 + 「其余」，不是发现说的「只标注了 3 条」。(2) `test_
   - 反驳（`scope-boundary`）: 越界辩护不成立，但发现本身按其主张站不住。(1) 边界：根因不在硬边界外。没有任何一处需要改 agent_service.py —— `git diff b8500c6e 2617a930 -- backend/app/services/agent_service.py backend/app/api backend/app/models` 为空；测试**读**边界文件不是越界，边界禁的是**改**。要改的只有本卡自己的 UAT 标注表 / 自己新增的测试文件，都在本卡地盘内。所以不能用「越界」驳回。(2) 主张 A 直接被事实推翻：:226 被标注了**两次** —— 用例自身 docstr

13. [MEDIUM] `test_pyright_tail_behavior.py::test_build_misconception_preserves_caller_timestamp` — 2/3 票反驳
   - 主张: T-new-2 的缺陷行是 `error_classifier.py:211-223` 的 `classify()` 用错 kwarg 名，修复是改调 `_build_misconception`；门只打在新抽出的 helper 上，`classify()` 这条真调用路径没有任何门，且由于两边写的都是 now()，还原后运行期无可观测差异 ⇒ 行为门原理上抓不到，需要 AST/grep 门（断言 classify 体内不出现 `created_at=` 这个 kwarg）才锁得住。
   - 反驳（`counterexample`）: 站不住脚，两点均在代码里可指位置。

(1) 负控被一道硬门抓得到，只是不是行为门。census `_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md:61` 记的就是这条表达式上原带 `# pyright: ignore[reportCallIssue]` —— 即 pyright 对 `Misconception(..., created_at=...)` 实际报错（pydantic v2 dataclass_transform 合成的 `__init__` 无 `created_at` 形参）。`pyrightconfig.json` 的 
   - 反驳（`already-covered`）: 已被 pyright 门覆盖，发现的核心主张（classify() 这条路径「没有任何门」）不成立。

证据链：
1) backend/app/services/error_classifier.py 落在 pyright 强制面内。仓根 pyrightconfig.json：include=["backend/app","tests"]、typeCheckingMode="basic"（basic 下 reportCallIssue 为 error 级）。lefthook.yml:206-231 的 python-typecheck 块 glob="backend/app/*.py"（单星跨

14. [LOW] `test_pyright_tail_behavior.py::_declared_signatures` — 2/3 票反驳
   - 主张: 门比的是 ast.unparse 的文本，而注解/默认值里的名字是在两个不同模块的命名空间里各自解析的，存在「文本相同、绑定不同」的静默通过面（反向的「文本不同、语义相同」如 Optional[str] 与 str | None 只会造成响亮误报，危害较小）。
   - 反驳（`already-covered`）: 已被现有的 pyright 硬门覆盖，发现自带的复现路径跑不通。

核实过程：
1. 门的对象：backend/app/services/exam_service.py:79-125 的 `if TYPE_CHECKING:` 块（11 条声明）↔ backend/app/services/exam_service_ext.py 的模块顶层 def（:58/:272/:475/:743…）。真正的运行期挂载在 exam_service_ext.py::attach_to_exam_service() :956-966（`ExamService.<name> = <fn>`），由 :970 顶层
   - 反驳（`scope-boundary`）: 已被覆盖（不按「越界」refute——门洞本身在测试文件内，属本卡地盘）。发现的前提事实成立：test_pyright_tail_behavior.py:336-372 的 _declared_signatures/_ext_signatures 确实只比 ast.unparse 文本，不解析 import。但它点名的复现场景（把 exam_service_ext.py:36 的 HintResponse 换成另一模块导入 / ext 内重定义同名类）**不是静默通过面**，而是被另一道现成的门当场拦下：

1. exam_service_ext.py:956-966 的 attach_to_

## 三 完整性批评者（还有什么没查）

## (a) 一个维度都没覆盖到的面

**A1 — `_resolve_path` 的下游消费链（本卡最大的用户可见变化，8 个维度零提及）**

`wikilink_graph_service.py:209` → `wikilink_context_service.py:480 n_text = _read_neighbor_md(n.path, vault_root)` → `:315 _resolve_vault_md_path`，后者用 `Path(vault)/raw` + `.resolve(strict=True)`。

改前，凡**不在 vault 根目录**的笔记，`n.path` 是扁平 `X.md`（本卡自己的门 `test_resolve_path_returns_vault_relative_path_for_nested_note` 就证明了改前返回 `note.md`），`vault/X.md` 不存在 ⇒ `strict=True` 抛 OSError ⇒ 被 `:339 except (OSError, ValueError)` 吞 ⇒ 返回 None ⇒ `content_summary` / `callouts` **恒空**。改后第一次解析成真实路径 ⇒ 邻居正文与 callout 首次真正进入 LLM 提示（`chat_context_assembler.py:295-320` 把它们渲进 `<neighbor>` 块）。

门未覆盖的路径：全仓没有一条测试走「真 graph → 真文件」这条链。`tests/unit/test_wikilink_context_service.py:111-150` 全部用 `MagicMock()` 图服务——`getattr(service,"_vault_path")` 拿到的是 MagicMock，经 `__fspath__` 变成 `Path('')`，邻居文件恒不存在，所以 `assert n.content_summary is None`（:150）在本卡改前改后都绿、与改动无关。本卡新增的门只断言 `_resolve_path` 的**返回字符串**，没有一条断言下游。

commit body 与验收单只写「邻居卡片 path 恒扁平化」，从头到尾没有一句说「邻居正文/callout 从恒空变成有内容」；§六「本卡未证明什么」10 条里也没有这条。

**A2 — 两处 `BaseException` 分支里「cancelled」子分支在生产的可达性，无人论证**

我核了 CPython 3.14.4 `asyncio/tasks.py:751-766`（`_GatheringFuture.cancel` 置 `_cancel_requested`）与 `:858-864`（`if outer._cancel_requested: outer.set_exception(exc)`）：`return_exceptions=True` 下只要 **gather 自身**被取消，就**不返回结果列表**，直接抛 CancelledError。

而本仓唯一的取消源是 `batch_orchestrator.py:351` 的 `asyncio.wait_for(self._execute_all_groups(...), timeout=timeout)`——取消的正是外层；`batch_orchestrator.py` 全文件 `grep '\.cancel()'` **零命中**；`self._cancel_requested`（`:653`）是协作式布尔标志，不调 `Task.cancel()`。⇒ CancelledError 只有在**子任务自己**以 CancelledError 收尾（下游库把取消漏出来）时才会进 results 列表。

这条前提既没被卡的证据体系检查过，也不在 §六。§六.1 只说「没在真实并发路径上触发过」，没说「我不知道它是否可触发」。（顺带：commit body 称改前「取消被当业务结果 append，随后 `result.success` 抛 AttributeError」——在 **group** 级 `_execute_all_groups` 里根本没有 `.success` 访问，改前的 AttributeError 会晚到 `start_batch_session:460 sum(r.failed_count for r in results)` 才发生。）

**A3 — `b8500c6e` 纯格式 commit 与 pragma 注释的交互（此前无人核，我核了，结论是干净的）**

AST 等价证明不覆盖注释，而 `# pyright: ignore` / `# noqa` 是 lefthook 两道门的承重注释。实测 `git --no-pager diff --no-color b8500c6e^ b8500c6e -- backend/app | grep -E '^[-+].*(pyright: ignore|noqa|type: ignore)'` **零命中** ⇒ 没有 pragma 被 format 合并或挪离其目标行。该面无问题，但属于此前没有任何维度验过的面。

---

## (b) 反驳者搞错了的

**B1 — 「EMBEDDING 常量退役注释称『全仓再无引用』失实」（被 3/3 反驳）成立**

`multimodal_service.py:115` 至今原文是「全仓再无引用」。更关键的是：**卡方自己已经书面接受了这条**——验收单 §四 LOW-3 写「接受。我的 grep 面是 `backend --include='*.py'`，写结论时却说了『全仓』——判据面 ≠ 主张面」，处置写明「改为『全仓**可执行代码**再无引用；文档中仍有历史提及』」。HEAD 上一字未改。这不是「还没人发现」，是**已承认、未执行**。

**B2 — 「`get_health_status` 名实不符」（被 2/3 反驳）成立**

`multimodal_service.py:1050-1052`：`vector_search_available = has_store and lancedb_connected` / `capability_level = "full" if vector_search_available else "degraded"`，与 `_generate_embedding` 完全解耦。本卡在同一文件 `:1367` 写下「本方法当前**恒返回 None**」，于是「向量检索可用」从"运行期 ImportError 导致的事实上不可用"升级为**静态可证的假**。

对照输入：注入 `multimodal_store` 且其 `health_check()` 返回 `{"lancedb": True}` ⇒ 健康端点返回 `vector_search_available=True` / `capability_level="full"`；同一进程里 `search()` 的 `:1296 if query_vector:` 永不为真、`search_mode` 恒 `"text"`。验收单 §六 为 T-new-8 登记了 4 条「未证明」，**没有**这一条。

**B3 — 「漏标无判别力用例」（被 3/3 反驳）有一半是对的**

`tests/unit/test_pyright_tail_behavior.py:274 test_agent_type_accepts_alias_values_and_rejects_unknown` 只断言 `app/services/agent_service.py` 的 `AgentType` 枚举——硬边界文件、本卡零改动——改前改后都绿，它**不在**验收单 (b) 列出的 9 条先红里。而验收单 §三(g) 判别力表最后一行写「其余 | **有判别力**（见 (b) 先红红因）」。15 条里 green-before 共 6 条，表里显式标了 3 条、§三(b) 另认了 2 条 AST 门，唯独这条落进「其余=有判别力」，与事实相反；该用例自己的 docstring 还写着「(转换是有判别力的)」。

（另：被 2/3 反驳的「`_classify_gather_result` docstring 把 `test_gather_return_exceptions_...` 称作『回归门』」也该翻案——`batch_orchestrator.py:138` 写「见回归门」，而验收单 §三(g) 自己把它定性为「证明缺陷输入面真实存在」、§六.1 承认接线无运行期门。同一卡内两处自相矛盾。存活 finding #7 已覆盖实质，此处只作补记。）

---

## (c) 声称验证了但实际没有

**C1 — §三(m) 与 §六.10 称「已改写注释措辞使 (m) 判据真正无命中」「并加了一条门」，两件事在 HEAD 上都不存在**

我按验收单原文的判据跑了一遍：

```
git --no-pager diff --no-color --name-only 2038278a HEAD -- . ':(exclude)_bmad-output' \
  | xargs grep -n -e fsrs_bridge -e decay_beta -e 7691 -e 7687
→ backend/tests/unit/test_pyright_tail_behavior.py:14
```

该行原文仍是 `#   零连库(7691/7687/7692 均不触)、零网络、零 live vault 读写;落盘只用 tmp_path。`——端口字面量在，「零网络」也在（§四 LOW-4 承诺改成「零主动网络调用；import 链会触发 LiteLLM 价格表拉取」，同样未落地）。工作树 `git status --porcelain` 只有 4 个未跟踪的 `_bmad-output` 条目，跟踪文件 == HEAD，不存在「改了还没提交」。

**C2 — §四 LOW 表四条处置 + 问题 1 处置，全部未落地**

| 承诺 | HEAD 实况 |
|---|---|
| LOW-1a 改写 `_classify_gather_result` docstring | `batch_orchestrator.py:147` 仍写「`KeyboardInterrupt` / `SystemExit` 同样落 `"failed"`。这比改前**收紧**」——正是 Codex 实测证伪的那句 |
| LOW-2 改写 `_resolve_path` docstring | `wikilink_graph_service.py:319` 仍写「两者同域, 不存在歧义」 |
| LOW-2 「把该反例做成常驻门」 | 不存在。`test_resolve_path_disambiguates_duplicate_basenames`（:134）建的 4 个 md **一个 wikilink 都没写**，图里不可能出现索引外节点，重名 ∧ 裸名 `[[note]]` 这个反例既没测也没记 |
| LOW-3 | 见 B1 |
| LOW-4 | 见 C1 |
| 问题 1「在 docstring 里如实写明这条边界」 | `_resolve_intent_model` 的 Notes（`agent_routing_engine.py:222-224`）只写「记 warning 再回落」，没有「非 (ImportError, AttributeError, RuntimeError) 的异常会从 `:575` 外溢（该调用在 `:577` 的 try **之外**）」 |

⇒ 存活 finding #5（wikilink docstring 为假）不是新发现，是**已被 Codex r1 抓到、卡方书面接受、处置未执行**。

**C3 — 验收单内部数字自相矛盾，且未按 §四 的自我更正回填**

§四（line 308-312）自行更正为「ignore 计数是 **11 → 3**，不是 11 → 4；卡文列了 3 条却写 4」，但 §三(f) 表（line 119）和 §五 DoD 表（line 342）仍写「→ 4 ✓」。我独立数了：`backend/app` 下含 `pyright: ignore` 的行，`b8500c6e` = 53，HEAD = 45（删 8，与 diff 里删掉的 8 处逐一对上）；census 面保留的正是 3 条——`learning_context_service.py:205` / `intelligent_parallel_service.py:629` / `exam_service.py:559`。即 11→3 正确，两张表未同步。

**C4 — 承重字段仍是 `<待填>`，且 D-15 末轮未跑**

§〇「最终代码 SHA / commit 数 / Codex 轮次 / evidence 档数」、§三(g) 收集条数与 tail-green 档名、§三(h) pyright-after 档名、§三(i) `tests/unit` 与 `tests/regression` 收工行、§三(l) 验伪锚、§三(o) ruff F821 验伪锚、§四 r2 整节。

磁盘上这些档**是有的**（`tail-green-20260918T200726.txt` 末行 `15 passed, 10 warnings`、`pyright-after-20260918T200726.txt`、`unit-close-20260918T202616.txt`、`regression-close-20260918T201222.txt`），所以是登记缺口不是没跑；但按协议 §5「验收单只**引用**路径与末行，不自述数字」，现在这些行既没路径也没数字，而 D-15 要求的末轮（绑最终 HEAD 的 r2）确实还没跑。

---

## (d) 跨文件交互效应

**D1 — 见 A1。**补一条被 A1 连带作废的既有「门」：

`tests/unit/test_security_p0_vulnerabilities.py:190-199 test_obsidiantools_currently_returns_relative_paths_only` 的 docstring 把「`_resolve_path()` 返回 `f"{note_key}.md"`，**永远是相对路径** ⇒ 当前实现 SAFE by accident」当作现实依据。本卡把返回值换成 `md_file_index` 取出的值（`Path(source).as_posix()`），这条依据已作废。

行为上**仍然安全**（我核了 obsidiantools `api.py:1074-1114 __get_relpaths_by_name` 的值来自 `get_md_relpaths_matching_subdirs(self._dirpath)`，恒是 vault 内相对路径；且 `_resolve_vault_md_path:324-330` 有 `resolve(strict=True)` + `relative_to(root)` + 后缀检查）。问题是这条测试的**正文是模拟的**——它自己拼 `PathlibPath(note_key + ".md")`，从不调 `_resolve_path`——所以改前改后都绿，锁不住任何东西。未被拦下的输入：obsidiantools `api.py:199-201` 给 `md_file_index` 提供了公开 setter，若将来有人赋一个非 vault 内的值，这条「门」不会红（真正拦住的是 `_resolve_vault_md_path`，而那是另一份测试）。

**D2 — `AgentType` 硬化成入参校验后，仓内两套 agent 名单的不一致被带到了 API 边界**

`app/core/agent_memory_mapping.py:43-63` 的 `AGENT_MEMORY_MAPPING` 里有两个名字不在 `AgentType` 枚举（`agent_service.py:145-159`）内：`review-board-agent-selector` / `graphiti-memory-agent`。`POST /canvas/single-agent` 的 `agent_type` 形参类型是裸 `str`（`app/models/intelligent_parallel_models.py:169/225/373/541`），所以这两个值能到 `retry_single_node`，现在会当场返回 `failed + "unknown agent_type: …"`。

**不是回归**（改前裸 str 一样在 `call_agent` 处失败），但「合法 agent 名字集合」在本仓有两套，而本卡把其中一套变成了端点的硬校验。§六.7 只登记了「未核前端传值集合」，没登记仓内这两套名单本身不一致。

**D3 — 排除性结论（核过，无问题）**：全仓 `Misconception(` 构造点只有 `error_classifier.py:89`（即新抽出的 `_build_misconception`），`classify_with_pedagogy`（:259-272）不建实体 ⇒ 不存在第二处同型的 `created_at=` 静默丢值。`_generate_embedding` 的调用点也只有 `:1294` 一处（`search()`），不存在第二条索引侧管道被本卡连带改掉。
