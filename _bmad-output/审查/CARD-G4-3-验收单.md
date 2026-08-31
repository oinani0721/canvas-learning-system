# 验收单 — CARD-G4-3 四态贯穿·API / trace 面

> **批次**: BATCH-2026-08-31-第七批 · 车道 V4
> **日期**: 2026-08-31
> **worktree**: `.claude/worktrees/card-v4-apistatus`（分支 `card/v4-apistatus`，**未 push**）
> **基线**: `9cf0fb85`
> **前置卡**: CARD-G4-2（服务层四态，第五批已合并）
> **附件**: `CARD-G4-3-状态词汇对齐登记.md`（完成条件 (d) 的登记产物）

---

## 一、这张卡给你带来什么（用户可感说明）

G4-2 让**服务层**学会了说「我坏了」而不是「没有数据」。但那句话说完就没人听——
到了 HTTP 响应这一层，端点在拼装返回值时把状态字段**挑拣掉了**。所以在
G4-2 之后、本卡之前，接口的表现和以前一模一样：

```
GET /api/v1/memory/concepts/逆否命题/history
→ 200 {"timeline": [], "total_reviews": 0}      ← 这是「没学过」还是「Neo4j 挂了」？
```

本卡把那句话接到出口。同一个请求现在长这样：

```
真的没学过：  200 {"timeline": [], ..., "retrieval_status": "empty",
                  "retrieval_status_reason": null}
Neo4j 挂了：  200 {"timeline": [], ..., "retrieval_status": "unavailable",
                  "retrieval_status_reason": "ConnectionRefusedError: bolt://..."}
```

**两个响应的 `timeline` 完全一样，区别全在新增的两个字段上。** 这就是这张卡的全部价值。

覆盖的四个接口：

| 接口 | 你会在哪儿碰到 |
|------|--------------|
| `GET /api/v1/memory/episodes` | 学习历史查询 |
| `GET /api/v1/memory/concepts/{id}/history` | 某个概念的得分时间线 |
| `GET /api/v1/memory/review-suggestions` | 复习建议（艾宾浩斯到期概念） |
| `POST /api/v1/rag/query` | RAG 智能检索 |

同时，**故障态会留下一条 trace 记录**（`log_decision`），事后可以按状态回查
「那天到底降级了多少次」。正常请求不落 trace，避免把日志淹掉。

### ⚠️ 一处需要你知道的契约变更（拍板项 1）

`GET /review-suggestions` 的返回值**从裸 JSON 数组换成了对象信封**：

```
以前： [ {concept: "逆否命题", ...}, ... ]
现在： { "items": [ {concept: "逆否命题", ...}, ... ],
        "retrieval_status": "ok", "retrieval_status_reason": null }
```

原因：JSON 顶层是数组时，**体内物理上没有地方放状态字段**——加性在这里做不到，
只能换信封。手册 §一 拍板项 1 的推荐是「换」，本卡按推荐执行。条目自身的字段
**一个字没动**。详见 §四。

### 这张卡不做什么

- **不做界面**。总账原卡文提到「Claudian 侧栏/总览页消费显示 + 浏览器走查截图」，
  但本批 `/goal` 的完成条件 (a)-(e) 里没有 UI 项，(d) 只要求「登记对齐计划不强改」。
  按 `/goal` 执行，**未写任何前端代码、未做浏览器走查**。UI 消费面仍是空白。
- **不统一另外四套状态词汇**（chat / MCP / board_manifest / memory health）。
  只登记，见附件。
- **不重新生成 `backend/openapi.json`**（D4 裁决点未批），漂移只登记，见 §六。

---

## 二、技术完成条件核对（AND）

| # | 条件 | 状态 | 证据 |
|---|------|------|------|
| **a** | `/memory/episodes` 与 `/concepts/{id}/history` 加性携带 `retrieval_status` + `retrieval_status_reason`（可选带默认，200 语义不变） | ✅ | `memory_schemas.py::LearningHistoryResponse` / `ConceptHistoryResponse` 各加 2 个 `Optional[...] = None` 字段；四态注入用例 8 条断言字段值 + 状态码恒 200 |
| **b** | `/review-suggestions` 按拍板项 1 换信封；零消费方 grep 证据入单；"加性"字面豁免显式记录 | ✅ | §四整节；`ReviewSuggestionsResponse` docstring 内亦写明「不是加性，是破坏性」 |
| **c** | `/rag/query` 纯透传 `CanvasRAGState.retrieval_status`；契约测试证明旧必填键全保留 | ✅ | `rag.py:298-311` 只做 `result.get()` 搬运；`TestRagAdditiveContract` 用旧 schema 的字段契约语义等价副本解析新响应，5 种状态全过 |
| **d** | chat degraded bool 与 MCP source_status **登记不强改**；trace 面 `log_decision` 与统一枚举对齐 | ✅ | 附件 `CARD-G4-3-状态词汇对齐登记.md`（5 套词汇清单 + 逐套可对齐性判定 + 3 张提名卡）；trace 单点 `decision_tracker.log_retrieval_status_decision` |
| **e** | API 注入测试三态断言字段值与状态码；既有套件零新增失败；openapi 漂移只登记 | ✅ | §三 + §五 comm 对账；§六 openapi 登记 |

---

## 三、改了什么（逐文件）

### 生产代码（4 个文件）

| 文件 | 改动 |
|------|------|
| `backend/app/models/memory_schemas.py` | `LearningHistoryResponse` / `ConceptHistoryResponse` 各 +2 可选字段；新增 `ReviewSuggestionsResponse` 信封模型；`__all__` 补一项；导入 `ServiceStatus` |
| `backend/app/api/v1/endpoints/memory.py` | 三端点透传状态 + 故障态落 trace；`/review-suggestions` 的 `response_model` 换信封、改调 `get_review_suggestions_with_status()` |
| `backend/app/api/v1/endpoints/rag.py` | `RAGQueryResponse` +2 可选字段；端点透传 + 故障态落 trace |
| `backend/app/core/decision_tracker.py` | 新增 `log_retrieval_status_decision()` —— trace 归一单点 |

**关键设计点 1：字段类型是 `Optional[ServiceStatus]` 而不是 `Optional[str]`。**
好处是 OpenAPI 里该字段自动带上值域约束，实查已确认：

```
$ python -c "... app.main.app.openapi() ..."
components.schemas.ServiceStatus =
  {"type": "string", "enum": ["ok", "empty", "degraded", "unavailable"], ...}
/api/v1/memory/review-suggestions 200 → $ref: #/components/schemas/ReviewSuggestionsResponse
/api/v1/memory/episodes           200 → $ref: #/components/schemas/LearningHistoryResponse
```

**代价（如实登记的行为变更）**：若服务层给出四态以外的值，响应校验失败 → 5xx，
而不是把「第五种状态」原样送给客户端。这是"值域由 schema 强制"的必然结果，
也是它的意义：词汇分裂当场暴露。已用
`test_out_of_domain_status_fails_loud_not_silently_passed_through` 把这个行为钉住。
**生产路径不受影响**——实查服务层全部赋值点只发四个合法 value 或 `None`：

| 出口 | 形态 |
|------|------|
| `memory_service.py:801/803/805`、`:892` | dict 键，写 `ServiceStatus.X.value` |
| `memory_service.py:1077/1086/1089`（review-suggestions） | `StatusedResult.unavailable()` / `.from_items()` —— 构造时**再过一次枚举校验** |
| `memory_service.py:2376/2377/2379/2382`、`:2467/2469/2470` | 同上（search / error-memories 族） |
| `rag_service.py:226/487/506` | `retrieval_status` 字面量 `"unavailable"`（对应的 `quality_grade: None` 在 216/481/500） |
| `lib/agentic_rag/nodes.py:572/576/579/582` | 四个字面量 |

> Codex round-1 LOW-3 指出我初版只列了 dict 出口、漏了整个 `StatusedResult` 族
> （其中 1077/1086/1089 正是本卡 `/review-suggestions` 走的那条）。补齐后结论不变
> 且更强：`StatusedResult` 的 `__post_init__` 本身就会把非法值挡在构造期。

**关键设计点 2：trace 归一收在一个函数里，因为这里有个会静默产生错值的坑。**
`log_decision` 内部做 `str(output)`，而 `ServiceStatus` 是 `class X(str, Enum)`
**不是** `StrEnum` —— `str(ServiceStatus.DEGRADED)` 得到的是
`'ServiceStatus.DEGRADED'` 而非 `'degraded'`。传错不报错，只会让 trace 里多出
一个不在统一值域内的字符串，使后续按状态聚合的查询全部落空。

这个坑是真实存在而非假想：`/review-suggestions` 路径拿到的
`StatusedResult.status` **就是枚举成员**，而另两条路径拿到的是 value 字符串——
同一个 trace 入口必须同时吃下两种形态。已用
`TestMemoryTraceEnumNormalization` 双形态钉住。

> 施工过程中的一次自我修正，如实记：初版把 trace 逻辑在 memory.py 和 rag.py
> **各写了一遍**，且 rag.py 那一份漏了枚举归一分支（服务层将来若改返回枚举，
> 那一处会静默写出 `'ServiceStatus.DEGRADED'`）。发现后抽成
> `decision_tracker.log_retrieval_status_decision` 单点，两端点共用。

### 测试（新增 2 文件 / 79 用例）

| 文件 | 用例数 | 覆盖 |
|------|-------|------|
| `backend/tests/api/v1/endpoints/test_memory_four_state_api.py` | 49 | 三端点四态注入、透传纯度、不发明状态、200 语义、信封形状、条目契约不变、trace 归一（枚举/字符串双形态）、越界值 fail-loud、旧 schema 契约门、**required 集合机械门** |
| `backend/tests/api/v1/endpoints/test_rag_four_state_api.py` | 30 | 四态透传、null 不被归一、缺键容忍、unavailable 仍 200、值域、trace 三例、旧 schema 契约门、**required 集合机械门** |

**测试策略是「注入」而非「真弄挂 Neo4j」**：mock 服务层分别返回 ok/empty/degraded/
unavailable，断言 HTTP 响应字段逐字等于注入值。测的是"透传管道漏不漏水"，
真实故障注入是 G4-2 服务层卡的战场，本卡不重复。

**加性是怎么证的**：测试里重建了改动前模型的**语义等价副本**
（`LegacyLearningHistoryResponse` / `LegacyConceptHistoryResponse` /
`LegacyRAGQueryResponse` 等），用它 `model_validate()` 新端点的实际响应。
这比肉眼看 diff 强——diff 只能看出"加了字段"，看不出"某个旧字段的类型被顺手改窄了"。
副本对照 `git show HEAD:backend/app/models/memory_schemas.py` 与
`git show HEAD:backend/app/api/v1/endpoints/rag.py` **逐字段**抄写（字段名/必填性/
类型/默认值/`ge-le` 约束），省略不参与校验的 description 与 example ——
故称"语义等价"而非"源码逐字"（Codex round-1 LOW-1 措辞更正）。
两个**嵌套**副本（`LegacyConceptHistoryTimeline` / `LegacyMultimodalResultItem`）
原先因为所有用例都给空列表而**从未真正参与解析**，已补非空用例各一条。

**先红后绿实录**：实现前首跑新测试 = **32 failed / 17 passed**。
定稿后用**可复跑回放**重做（HEAD 生产代码 × 定稿测试）= **48 failed / 33 passed**，
存档 `evidence-g43/02-先红-定稿测试在HEAD代码上的回放.txt`。
那 30 条先绿的正是"旧契约别坏"的守门用例，它们在定稿后必须**仍绿**——
这一点比先红后绿更能抓住悄悄的类型收窄。定稿后 = **81 passed**。

**加性的第二道门（不依赖手抄副本）**：`TestMemorySchemaRequiredSetsFrozen` /
`TestRagSchemaRequiredSetFrozen` 直接比对模型 `model_json_schema()["required"]`
集合与改动前逐字相等的字面枚举。少一个 = 旧必填键被降级；多一个 = 新字段被写成
必填。这道门的期望值来自 `git show HEAD:...`，**独立于我手抄的 Legacy 副本**——
副本抄松了它照样能抓。

裁判命令实跑：
```
$ cd backend && caffeinate -i .venv/bin/pytest tests/api -q -k "memory or rag"
81 passed, 148 deselected, 11 warnings in 0.62s
```
（81 = 新增 79 + `tests/api` 内既有 2 条名字含 memory/rag 的用例）

### 变异验证：这些门是不是真的承重

写完门不等于门管用。14 个变异逐一施加（**串行**，每次改完复跑、还原后
`cmp` 逐字校验与备份相同）。

**可复跑**：`_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py`
（`cd backend && .venv/bin/python ../_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py`，
退出码 0 = 全部变异都被抓住）。输出存档
`evidence-g43/04-变异门验证-输出.txt`。脚本本身写了四条防自欺约束：串行、
`finally` 无条件还原 + `filecmp` 逐字校验、**锚点命中数必须恰为 1 否则当场炸**
（`str.replace` 不命中不报错，"变异没打上"与"门抓不住"在结果上同形）、
以及"全绿即失败"的判据方向。

| 变异 | 注入的缺陷 | 结果（收集数均 = 基线 81，且**含全部预期门**） |
|------|-----------|------|
| **M1** | `retrieval_status` 从可选改必填（破坏加性） | ✅ 3 条门变红 |
| **M2** | trace 去掉枚举归一 | ⚠️ **首版全绿 → 死门**，见下；补强后 ✅ 2 条 |
| **M3** | 端点在状态缺失时补 `"empty"`（发明状态） | ✅ 4 条 |
| **M4** | `/review-suggestions` 信封回退成裸 list | ✅ 8 条 |
| **M5** | `unavailable` 升成 503（破坏 200 语义不变） | ✅ 3 条 |
| **M6** | 端点用 `.get(k,"low")` 而非 `or "low"`（round-1 **BLOCKER-1** 本体） | ✅ 4 条 |
| **M7** | trace 落账去掉 fail-open（round-1 **HIGH-1** 本体） | ⚠️ **首版语法错误假杀**，见 §三之二·二；改合法块后 ✅ 7 条 |
| **M8** | 只删 fail-open 的**二级**兜底 | ✅ 3 条（round-2 点名缺口，旧门下全绿） |
| **M9** | helper 提前 return、根本不落账 | ✅ 12 条（同上） |
| **M10** | 把 `EMPTY` 加进落账集合 | ✅ 2 条 —— **round-3 实证的真存活变异**，补 ok/empty 参数化后才被杀 |
| **M11** | 信封的 `items` 键改名 | ✅ 7 条（round-3 点名缺口） |
| **M12** | `LearningHistoryResponse.retrieval_status` 退回裸 `str` | ✅ 2 条（round-3 缺口，OpenAPI 值域约束会消失） |
| **M12a** | `ConceptHistoryResponse.retrieval_status` 退回裸 `str` | ✅ 1 条 —— **round-4 实证的真存活变异**（值域门原先只查一个模型） |
| **M12b** | `ReviewSuggestionsResponse.retrieval_status` 退回裸 `str` | ✅ 1 条（同上） |

**判据（四次迭代后的最终版）**：一个变异算 kill 必须**五条同时成立** ——
①收集成功 ②收集数 == 基线（81）③`rc == 1`（是"有测试失败"而非语法/用法错）
④**零 pytest ERROR**（fixture/收集期崩溃不算"门抓住了"）
⑤**实际 FAILED ⊇ 该变异登记的预期 nodeid，精确到参数实例**。

第④⑤条是 round-3/4 补的关键：前几版只要求"有任意 FAILED"，于是**改一条无关测试的
断言**制造红灯也能判 ✓ —— 红灯与变异之间没有因果绑定。同输入双判据对照实测：

```
无关红灯（生产代码完全不变，只改一条测试断言）:
  judge_kill(旧口径, 无预期) -> (True,  '✓ 被抓住 (1 条门变红)')      ← 假杀
  judge_kill(新口径, 带预期) -> (False, '✗ 预期的门没变红: [...] —— 红的是别的测试')
```

脚本还在**第 1 秒**做全部锚点预校验（12 个变异的 patch 锚点必须各命中恰好 1 次）——
上一版 M10 的锚点是照"格式化前"的多行文本写的，而 `ruff format` 把它合成了一行，
脚本跑到第 10 个变异（约 18 分钟后）才炸。廉价检查要放在昂贵流程之前。

#### ⚠️ M2 抓出我自己写的一道死门（如实记）

M2 首次施加时**全部 61 条测试照样绿**。根因：

```python
# 原断言
assert spy.call_args.kwargs["output"] == "degraded"
```

`ServiceStatus` 是 `class X(str, Enum)`，所以
`ServiceStatus.DEGRADED == "degraded"` 为 **True** —— 这条断言对「传枚举」和
「传 value」**两种情况都成立**，根本看不见归一有没有做。同一份代码里我另写的
`assert "ServiceStatus" not in output` 也是瞎的（`in` 在 str 子类上是对 value
做子串匹配）。

实测确认坑本身是真的（Python 3.14.4）：

```
str(ServiceStatus.DEGRADED)  → 'ServiceStatus.DEGRADED'
ServiceStatus.DEGRADED == "degraded"  → True
```

即：**断言用的比较运算恒真，而 `log_decision` 内部用的 `str()` 会写出错值**——
两者看的不是同一个东西。

修法：新增 `_traced_output(spy)` 辅助函数，用 `str(...)` **复刻 `log_decision`
内部那一步**再断言。改后重跑 M2 → 2 条变红（`test_review_suggestions_unavailable_logs_decision`
与 `test_enum_valued_status_normalizes_in_trace_and_body`），门活了。

这道门为什么值得留：`/review-suggestions` 路径拿到的 `StatusedResult.status`
**就是枚举成员**，另两条路径拿到的是 value 字符串——归一不是防御未来，是当下
就在用。

### 测试断言适配（2 文件，因信封变更）

| 文件 | 改了什么 |
|------|---------|
| `tests/integration/test_memory_api.py`（仓库根） | `mock_memory_service` 补 `get_review_suggestions_with_status`；3 处 `isinstance(data, list)` 族断言改信封；1 处 call_args 目标改四态版方法 |
| `backend/tests/integration/test_memory_subject_filter.py` | 2 处结构断言改信封（`data["items"]`） |

**⚠️ 这两个文件在基线时就是全红的，我的修改并没有让它们转绿** —— 见 §五。

---

## 三之二、Codex round-1 对抗审查与整改（**裁定 FAIL → 已整改**）

审查存档：`_bmad-output/审查/codex-review-CARD-G4-3.md`
（`codex exec --sandbox read-only -m gpt-5.6-sol -c model_reasoning_effort="ultra"`）。

裁定 **FAIL / 不可验收**：BLOCKER ×1 · HIGH ×1 · MEDIUM ×2 · LOW ×4，
硬边界无违规、8 项"确认无问题"。逐条独立复现后整改如下 —— **8 条全部认领，零争辩**。

### BLOCKER-1（已修）：真实 `/rag/query` 的 unavailable 路径返回 500，我的测试是假绿

- **我自己复现确认**：`patch("app.services.rag_service.canvas_agentic_rag").ainvoke = AsyncMock(return_value=None)`
  → 真实 `RAGService.query` 走 `_get_fallback_result` → **HTTP 500**，`ainvoke_calls=1`。
- **根因**：三个 fallback 出口（`quality_grade` 分别在 `rag_service.py:216/481/500`）都显式写
  `"quality_grade": None`，而端点用的是 `result.get("quality_grade", "low")` ——
  `.get` 的默认值**只在键缺失时生效**，键存在且为 `None` 时原样返回 `None`
  → 撞 `quality_grade: str` 响应模型 → 500。
- **为什么我的测试没抓住**：新增用例的 `_state()` 对所有状态**固定伪造**
  `quality_grade="high"`。合成 fixture 与生产形状之间的这条缝，就是假绿的藏身处。
  `test_unavailable_still_returns_200` 在合成 state 上成立、在真实入口上是 500 ——
  **本卡「unavailable 仍 200」的判据此前根本不成立**。
- **修法**（端点一行，守硬边界不碰服务层）：`result.get("quality_grade") or "low"`。
  修后同一复现 → **200 + `retrieval_status="unavailable"` + reason 完整**。
- **补门**：`TestRagRealFallbackEntrypoint` —— 走**真实** `RAGService`，断言
  `ainvoke` 确被调用（防止门本身没测到东西）；另加一条**形状哨兵**锁住服务层
  仍发 `quality_grade=None`（服务层哪天改了，哨兵变红提醒重新评估端点兜底，
  而不是让它悄悄变成没人知道还需不需要的死代码）。

### HIGH-1（**部分闭合** — 本卡射程内已修，射程外如实登记移交）：trace 落账异常把本该 200 的响应升成 500，还谎报原因

- **我自己复现确认**：`patch("app.core.decision_tracker.log_decision", side_effect=RuntimeError(...))`
  → `/memory/episodes` 返回 **500**，且 detail 是
  `"Failed to query learning history: trace sink failed"` —— **查询其实成功了**，
  错误信息在说谎（比 Codex 描述的更糟，它只说了 500）。
- **根因**：`log_retrieval_status_decision()` 在四个端点的 `return` 之前被同步调用，
  而那些调用点都裹在 `try/except Exception → HTTP 500` 里；观测面异常直接被当成
  业务失败。
- **我的自相矛盾**：`decision_tracker.py` 的注释里我**写着**"观测代码不该成为新的
  失败源"，但代码没实现它。注释在描述一个我没做的设计。
- **修法**：`log_retrieval_status_decision()` 内 fail-open + 降级到本模块 logger，
  并给 logger 本身再套一层兜底（日志后端坏掉时 `logger.exception` 同样会抛）。
- **补门**：memory ×3（episodes / concept-history / review-suggestions）+ rag ×1，
  断言落账抛错时仍 200 且状态字段不变。
- **射程核实（AST 实扫，不是估计）**：本卡四个端点的 `try` 体内，观测类调用
  **只有** `log_retrieval_status_decision` 一处 —— 即 fail-open 加在这里就覆盖了
  本卡引入的全部风险面。另有 5 处 `logger.info/warning` 位于 `try` 内，但都在
  **我没碰的端点**（`create_learning_episode` / `extract_conversation_learning` /
  `archive_session` / `update_rag_config`），属同型存量债，本卡不扩范围收，
  登记在 §十。
- **fail-open 会不会吞掉真 bug**：会，这是代价。`input_summary` 不可序列化这类
  程序错误从此只进 logger 不进响应。取舍理由：观测故障让**业务响应**变 500 且
  谎报原因，比观测静音更坏。降级路径写了 `logger.exception`（带栈），不是静默
  `pass`；只有 logger 本身也坏掉时才完全静音（那一层由 M8 变异锁住）。

#### ⚠️ 射程收窄声明（Codex round-2 判 HIGH-1 为 PARTIAL，我认这个判定）

round-2 用「整个四端点观测故障不得改变结果」的口径衡量，本卡**没有**做到。
Codex 实证的绕过点我逐条核过，全部属实。

> ⚠️ **round-3 又推翻了我这里的一句话**：我原先写「**全部**在硬边界之外」——
> 不成立。`rag.py:274` 的入口 `logger.info` 在主 `try` **之外**，它抛错会让请求
> 直接 500 且 `rag_service.query` **一次都没被调用**，而 `rag.py` **正是本卡
> 已修改的文件**，推不给"服务层硬边界外"。我自己复现确认后已修（加 fail-open），
> 并补门 `test_entry_logger_failure_does_not_break_response`
> （断言 200 **且** `query.await_count == 1`）。
>
> 教训与本卡 BLOCKER-1 同源：**"全部/唯一"这类全称断言，我这一轮说错了三次**
> （全部绕过点在边界外 / 唯一一颗 quality_grade 地雷 / 清单 13 项）。
> 全称断言需要穷举证据，而我给的是抽样。

修完 `rag.py:274` 后，**仍未闭合**的绕过点（round-3 又补了 5 处，我逐条复现属实）：

| 绕过点 | 位置 | 为什么本卡不修 |
|--------|------|--------------|
| RAG fallback 的 `logger.warning` | `rag_service.py:209`、`:326-333` | 服务层实现，卡文硬边界「不碰 rag_service」 |
| LangGraph 不可用路径直接调原始 `log_decision` | `rag_service.py:274-287` | 同上（抛错会把预期 503 遮成 500） |
| RAG 端点 `logger.error` 遮蔽原始 503/500 | `rag.py:374-380` | 在 `except` 块内，属既有异常处理，非本卡引入 |
| vault resolver 的 warning | `vault_scope.py:184-198`（经 `memory.py:209/396` 触发） | `vault_scope.py` 是 G2-2/G4-1a 的地盘 |
| memory 服务层 debug/warning/error | `memory_service.py:665-682 / 843-850 / 1080-1089` | 硬边界「不碰 memory_service」 |
| RAGService 初始化日志 | `rag_service.py:194`、`:289-290` | 服务层 |
| memory 服务层 failed-score warning | `memory_service.py:748` → `:2753` | 服务层（Neo4j 已成功调用一次，日志失败仍升 500） |
| LangGraph 节点 debug sink | `lib/agentic_rag/nodes.py:1873` | lib 层，硬边界明列 |
| vault resolver debug | `vault_scope.py:133`（除 :184-198 外的第二处） | G2-2/G4-1a 地盘 |
| Neo4j client 日志 | `neo4j_client.py:746` —— 抛错会把健康的 `ok/timeline=1` **改写成** `unavailable/timeline=0` | client 层 |

**因此本卡的准确宣称是**（第三次收窄，前两次都说宽了）：

> *本卡在**自己修改的两个端点文件内**把观测面与业务面隔开了两处：
> `log_retrieval_status_decision`（helper 双层兜底）与 `rag.py:274` 的入口日志。
> **端到端 fail-open 未闭合** —— 至少还有 11 处绕过点分布在 service / lib /
> client / vault resolver / DI 初始化层，全部在本卡硬边界之外。
> 本卡**不宣称**已列全，因为这类点只能靠逐个注入实证发现，我和 Codex 各找到一批，
> 不排除还有第 12 处。*

移交提名 **CARD-OBS-nothrow-logging**，范围按 round-3 建议扩为：
**endpoint + 依赖初始化 + service recovery + vault/client + LangGraph nodes/retrievers**
（原先只写"允许触及 service 层"，覆盖不了后四类）。
本卡测试类 docstring 已写明"本组门不宣称端到端 fail-open 已闭合"。

### MEDIUM-1（已修）：「零消费方」结论说过头 + 证据路径不可复现

见 §四 —— 结论收窄为"活跃源码零消费方"，登记 `_archive` 中 1 个期望裸数组的
tracked 客户端，并把仓外消费面显式标为 UNVERIFIABLE；证据文件重做为
`evidence-g43/01-review-suggestions-消费方证据.txt`（A–E 五组，每组带可粘贴复跑的命令）。

### MEDIUM-2（已修）：59 条失败的根因表两次都错

见 §五 —— 第三版按 `re.split` 切块，块数与 `FAILED` 行数严格相等（59），
逐块归类零遗漏，并把"块数 == FAILED 行数"这道自检写进流程。

### LOW-1 ~ LOW-4（已处置）

| # | 内容 | 处置 |
|---|------|------|
| LOW-1 | "逐字副本"措辞过头；两个嵌套 Legacy 模型因全用空列表而从未参与解析 | 措辞改"语义等价副本"；补非空 timeline / 非空 multimodal 各一条用例，嵌套模型现在真正参与校验 |
| LOW-2 | 登记文档写"3 个端点"（实为 4）、引用已删除的 `memory.py::_trace_retrieval_status`、`log_decision` 调用数写 20/18 | 全部更正；调用数改用 **AST 实数**（19 个 Call 节点 / 状态类 2 / 业务类 17），初版的 20 是把 `grep -c` 的行数当调用数 |
| LOW-3 | "服务层全部赋值点"漏了整个 `StatusedResult` 族（含 review-suggestions 走的 1077/1086/1089）；`LearningMemoryClient` 被我说成"Neo4j 直连" | 补齐出口表；客户端更正为**本地 JSON 文件存储**（它只是恰好定义在 `neo4j_edge_client.py` 里，我被文件名误导） |
| LOW-4 | 改动清单漏了 `evidence-g43/`；变异脚本原地改工作树源码 | 清单补齐（见 §三之三）；变异脚本的原地修改风险**如实登记不改造**：脚本已有 `finally` 无条件还原 + `filecmp` 逐字校验，但**进程被强杀时无法保证**，且与并发编辑不兼容 —— 迁到临时 worktree 是更稳的做法，登记为后续改进，不在本卡范围 |

### 本轮整改**未采纳**的部分：无

8 条全部采纳。整改后 `tests/api -k "memory or rag"` = **81 passed**，
变异门扩到 **14 个全部被抓**（M6/M7 锁 round-1 BLOCKER/HIGH 的缺陷本体，
M8/M9 堵 round-2 缺口，M10/M11/M12 堵 round-3 缺口，M12a/M12b 堵 round-4 缺口——
其中 **M10 与 M12a/M12b 都是被审查实证过的"真存活"变异**）。

### 顺着 BLOCKER-1 自己往下挖的一步（不在 Codex 清单内）

Codex 让我找"第二颗同型地雷"。逐字段对照 `_get_fallback_result` 与
`create_initial_state()` 的每一个键之后，结论是 **`quality_grade` 是唯一一颗**
（`latency_*` 全 None 但字段是 `Optional[float]`；`query_rewritten=False` /
`rewrite_count=0` 非 None；`reranked_results`/`multimodal_results` 初值是 `[]`）。

但"逐字段人眼比对"这个方法本身查不出**将来**新加的第二颗。所以我换了个思路加了
一道机械门 `TestRagProductionStateShapesAllReturn200`：**不比对字段，直接把生产
真实产出的 state 形态整个喂给端点**，让 pydantic 自己去炸 ——
`create_initial_state()`（图早退形态）与 `_get_fallback_result()`（两种 reason）
共 3 条，断言恒 200。

这道门顺带证实了一件比 Codex 说的更严重的事：`create_initial_state()` 里
**`"quality_grade": None`（state.py:243）** —— 也就是说这颗地雷**不止在 fallback
路径上**，任何"图跑了但没设 quality_grade"的成功/早退路径同样会 500。
回退 BLOCKER 修复后本门 3 条 + 真实入口 1 条共 **4 条变红**，确认承重。

### 施工过程中我自己的一次操作失误（如实记）

补 LOW-1 时把 `ruff format` 传成了**整个目录** `tests/api/v1/endpoints/`，
连带重格式化了 5 个与本卡无关的既有测试文件（`test_agents_dedup.py` /
`test_agents_encoding.py` / `test_agents_learning_event.py` /
`test_fsrs_state_api.py` / `test_metadata_subject_mapping.py`）。
发现后按 `git show HEAD:<path>` 字节还原，`git status` 复核确认工作树只剩本卡文件。
教训：格式化命令必须指名到文件，不能给目录 —— 目录参数会把"存量漂移"一并改掉，
产生与本卡无关的大 diff。

---

## 三之二·二、Codex round-2 复核与整改（裁定 **FAIL / 需再一轮**）

审查存档：`_bmad-output/审查/codex-review-CARD-G4-3-round2.md`。
裁定 **BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 5**；原 BLOCKER-1 判**已闭合**，
硬边界与 5 个误格式化文件的还原经 `git hash-object` 逐字节比对**确认无问题**。

### ⚠️ MEDIUM-1：M7 是**语法错误假杀** —— 我这一轮最严重的错

- **Codex 的指控**：M7 把 `try:` 换成 `if True:` 却留着后面的 `except`，
  变异体是 **SyntaxError**；pytest 连收集都没完成，一条 FAILED 都没有，
  却因为 `rc != 0` 被我的 runner 记成「✓ 被抓住」。
- **我自己复现确认**：`compile()` 直接报 `invalid syntax @L145`；
  翻回上一版存档，M7 那一栏**确实一条 FAILED nodeid 都没有**（空行）。
- **根因不在 M7，在判据**：`rc != 0` 把「测试根本没跑起来」和「测试抓住了缺陷」
  归成了同一类。这正是我记忆里那条教训（*把「没有发生」当「验证通过」*）的
  原样重演。
- **修法（根因级）**：
  1. M7 改成**语法合法**的完整块替换（同批删掉配套 `except` 块）；
  2. runner 的 kill 判据换成**三条 AND**：收集成功 + **收集数与基线相等** +
     **至少一条具名 FAILED nodeid**；
  3. 补 Codex 点名的两个缺口：**M8**（只删 fail-open 的二级兜底）、
     **M9**（helper 提前 return 根本不落账）—— 这两个在旧门下都是全绿。
- **判据本身也验伪了**：注入一个真语法错误后，`judge_kill` 明确返回
  `✗ 收集失败（语法/导入错误）—— 这不是门抓住了，是测试没跑起来`（旧版会记 ✓）。

### 😑 我在修这道判据时**又造了一道死门**（如实记）

新加的「收集数不变」检查第一版写成 `PYTEST + ["--collect-only", "-q"]`，
而 `PYTEST` 里**已经有一个 `-q`** —— 变成 `-q -q`，pytest 把收集清单整个抑制掉，
函数恒返回 0，于是「收集数不变」退化成 `0 == 0` 的**恒真检查**。
首跑打出 `collected=0` 才发现。实测：单 `-q` → 75 条，双 `-q` → 0 条。

教训（已写进脚本注释）：**每加一道检查，就新增一条"它自己失败时"的路径；
新检查装上后必须先验伪一次，不能装上就信。**

### LOW-3：fail-open 门断言太弱（已补强）

Codex 指出前版只断言 200、不查 reason、更不查落账是否真的被调用 ——
于是「helper 提前 return 什么都不做」这种退化照样全绿。现改为：
精确 status **与** reason + `spy.call_count == 1` + **双 patch 变体**
（`log_decision` 与 `logger.exception` 同时抛错），memory ×2 参数化 + rag ×1。
M8/M9 正是这两条断言的对应变异，现在都能被杀。

### LOW-1：形状哨兵方向反了（已按建议改）

`test_query_with_fallback_exception_exit_keeps_none_quality_grade` 原先强制
服务层**继续**发 `quality_grade=None` —— 上游哪天合法改进成 `"low"`，这条门会
把改进判成回归。**一条在别人变好时变红的门是噪音**，Codex 说得对。
改为只锁本出口的四态语义；端点 `or "low"` 防御的价值由
`TestRagProductionStateShapesAllReturn200` 直接证明，不需要靠冻结上游缺陷。

### MEDIUM-2/3、LOW-4/5（已处置）

| # | 内容 | 处置 |
|---|------|------|
| MEDIUM-2 | 证据跨快照：`04` 输出仍写 67 passed、验收单称 361 collected 而当前是 372、M4/M5 的条数与存档对不上 | **所有证据在改动定稿后统一重生成**，并落 §三之四 的 SHA-256 冻结清单；审计期间不再编辑 |
| MEDIUM-3 | 消费方证据 E 组没有命令、且引用了已被我改名删掉的旧文件 | 证据文件整体重做：改用 **`git grep`** 限定 tracked 文件，A–E 每组都带可粘贴命令，E 组 9 条命中**逐条定性**（含 `.hypothesis` 缓存与 `.gdr` 打包产物） |
| LOW-4 | 「字面副本 / 逐字忠实」措辞仍在 6 处 | 全部改为**「字段契约语义等价副本」** |
| LOW-5 | `rag_service` 行号写成 222/481/500（实为 `quality_grade` 216/481/500、`retrieval_status` 226/487/506）；ImportError 第三条是 `_fuse_weighted_multi_source`；`LearningMemoryClient` 写入是 :817-824 原子写；改动清单 12 项实为 13、evidence 6 个实为 7+1 | 逐条按实查更正（含代码注释里的行号） |

### 本轮**未采纳**的部分

无。9 条全部认领。其中 HIGH-1 采纳为「**收窄宣称 + 登记移交**」而非在本卡内修 ——
因为除 `rag.py` 内那一处外，其余绕过点都在硬边界外，越界修比不修更坏。

---

## 三之二·三、Codex round-3 复核与整改（裁定 **FAIL / 需再一轮**）

审查存档：`_bmad-output/审查/codex-review-CARD-G4-3-round3.md`。
裁定 **BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 4**。

**冻结首门通过**：7 项 evidence 的 SHA-256 逐字匹配；M7/M8/M9 独立重放真杀；
数字对账除"改动清单 14 项"外全部一致；硬边界 11 个文件逐字节等于 HEAD。

### HIGH-1（再次收窄）：我说"全部绕过点在硬边界外"，又说错了

- **Codex 的反例**：`rag.py:274` 的入口 `logger.info` 在主 `try` **之外**，
  patch 后 HTTP 500 且 `service.await_count == 0` —— 而 `rag.py` **正是本卡
  已修改的文件**，推不给"服务层硬边界外"。
- **我复现确认**（整改前 500 + 服务零调用 → 整改后 200 + `await_count == 1`），
  已加 fail-open 并补门 `test_entry_logger_failure_does_not_break_response`。
- Codex 另补 5 处绕过点（`rag_service.py:194/289-290`、`memory_service.py:748→2753`、
  `nodes.py:1873`、`vault_scope.py:133`、`neo4j_client.py:746` —— 最后这个尤其恶劣：
  日志抛错会把健康的 `ok/timeline=1` **改写成** `unavailable/timeline=0`）。
  全部在硬边界外，已并入 §三之二 的移交表，移交范围按建议扩为
  **endpoint + 依赖初始化 + service recovery + vault/client + LangGraph nodes**。
- **宣称第三次收窄**，并明说"**不宣称已列全**"——这类点只能靠逐个注入发现。

### HIGH-2（如实登记）：我说"不连任何数据库"，失实

详见新增的 **§七之二**。要点：**裁判命令干净**（实测 0 连接、运行时文件 SHA 不变），
但 **comm 全量命令**里的存量文件 `test_metadata_subject_mapping.py:61` 会启真实
lifespan → 连 `bolt://localhost:7691` + 幂等 DDL + 写两个 git-ignored 运行时文件。
我为做对账**跑了 4 次**。已如实登记 + 提名 `CARD-TEST-isolate-lifespan`。

根因是**射程偷换**：我写的 77 个用例确实全 mock，但我把"我这部分的性质"
当成了"整条命令的性质"。

### MEDIUM-1：`judge_kill` 仍能被无关红灯骗（第三版判据）

Codex 实证：**只改一条测试断言、生产代码完全不变** → `1 failed / collected=75`
→ 旧判据仍判 ✓。根因是前两版只要求"有任意 FAILED"，红灯与变异**没有因果绑定**。

修法：每个变异登记**预期该杀死的 nodeid**，实际 FAILED 必须覆盖它；再加 `rc == 1`
（排除语法/用法错）。同输入双判据对照已验伪（见 §三 变异表下方）。

### MEDIUM-2：`EMPTY` 是**真存活**变异（最有价值的一条）

把 `EMPTY` 加进 `_TRACEABLE_FAULT_STATES` → **75 passed 全绿**。根因：
`test_healthy_states_do_not_spam_trace` 的 docstring 写着"ok/empty"，
**实际只注入了 ok**。文档说覆盖了、代码没覆盖 —— 这是最难发现的那类空洞。
已两侧参数化 `ok/empty`，并补 M10/M11/M12 三个变异。

### MEDIUM-3 / LOW-1~4

| # | 内容 | 处置 |
|---|------|------|
| MEDIUM-3 | 消费方证据自相矛盾：C 组明明有 1 条命中，结论却写"A/B/C 三组零命中"；E 组实为 10 条却写 9 | 按实数更正 + 加"6 行合计 10 条"的自检行 |
| LOW-1 | `04` 输出用 `tail[-8:]` 截断，M9 的 12 条只存了 7 条 | 去掉截断，完整输出 |
| LOW-2 | 改动清单写 14，实为 15 | 按实数更正，并注明"这个数字会变，以实跑为准" |
| LOW-3 | 冻结清单只绑 evidence，证明不了「代码—测试—证据—声明」同源 | 扩到 **19 个文件 5 组**；验收单自身刻意排除（它还要追加整改记录） |
| LOW-4 | `memory_schemas.py:563` 仍写 `LearningMemoryClient` 走 Neo4j 直连；rag 测试函数名 `keeps_none_quality_grade` 与放宽后的断言不符 | 两处均更正 |

### 本轮**未采纳**：无。9 条全部认领。

### 这一轮我自己犯的两个错（如实记）

1. **M10 锚点照着"格式化前"的多行文本写**，而 `ruff format` 把它合成一行 →
   脚本跑到第 10 个变异（约 18 分钟后）才 `AssertionError` 中止。
   已把**全部锚点预校验提到第 1 秒**（纯字符串比对，一秒完成）——
   廉价检查要放在昂贵流程之前。
2. **又一次在变异脚本运行期间编辑被变异的文件**（`memory_schemas.py`），
   restore 有覆盖我编辑的风险。这次靠跑完后 `grep` 特征串确认 4 处编辑全部幸存；
   但正确做法是**等它跑完再改**。同一失效模式本卡犯了两次。

---

## 三之二·四、Codex round-4 复核与整改（裁定 **FAIL / 需再一轮**）

审查存档：`_bmad-output/审查/codex-review-CARD-G4-3-round4.md`。
裁定 **BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 2**。

**大面确认无问题**：冻结 19 项 `mismatch=0`；M10/M11/M12 独立重放真杀；
12 变异 18 个锚点全命中；`rag.py` 新 try/except 只包入口日志、不吞业务错误；
硬边界 11 文件逐字节等于 HEAD；裁判命令 `PORT7691_SOCKET_CALLS=0` + 两个运行时
文件 SHA 前后一致。

### HIGH-1：§十 又冒出"全部/全在"的全称（我 round-3 漏改的旧文本）

Codex 找到**第 12 处**观测旁路：`rag.py:419` `/weak-concepts` 的入口
`logger.info`（patch 后 500 且 `await_count=0`）与 `:441` 的 `logger.error`
（把结构化 503 遮成裸 500）。二者是 HEAD 存量、不在本卡四个主端点，
**可移交不强修**；但我在 §十 写的"**全部**绕过点""**全在**硬边界外"
与前文"不宣称列全"自相矛盾 —— 那是 round-3 改写时漏掉的两句旧文本。

已删全称，并把 `rag.py:419/441` 显式并入移交表；移交范围再扩一项
**except 分支日志**（`memory.py:268/323/436` 会把结构化 500 detail 遮成裸
`Internal Server Error`，LOW-1）。

### MEDIUM-2：M12 的两个同型点**真存活**（本轮最实的一条）

三个模型都有 `retrieval_status` 字段（`memory_schemas.py:160/247/580`），
但我的值域门只检查 `LearningHistoryResponse` 一个。Codex 把另两个改回
`Optional[str]` → **79 passed 全绿**。

已把值域门参数化到三个模型，并补 **M12a/M12b** 两个变异。实测：改动前两变体
全绿，改动后各杀 1 条预期门。

> 这与 round-3 的 M10（docstring 写 ok/empty 但只注入 ok）是同一种病：
> **"检查了一个" ≠ "检查了这个不变量"**。同型点必须逐个上门。

### MEDIUM-1：`judge_kill` 子串匹配仍可假杀 → 收紧后连暴三个解析 bug

Codex 实证：预期 `…test_healthy_states_do_not_spam_trace` 时，只有 `[ok]`
参数失败也判 ✓ —— 但该变异真正该杀的是 `[empty]`。已改为**精确到参数实例**
（预期串须是某条 nodeid 的完整 `::` 后缀）+ **ERROR 拒绝判杀**。

**收紧之后，连续暴露我自己的三个解析 bug（全是假阴）**，如实记：

| # | bug | 症状 |
|---|-----|------|
| 1 | `_tail()` 两边都 `split("::", 1)`，而 nodeid 是 3 段、预期串是 2 段 | 两边不同形 → **14/14 全判死门** |
| 2 | `startswith("ERROR ")` 把**日志输出行**（`ERROR    app.api…:memory.py:268 …`）当成 pytest ERROR nodeid | M1/M4/M5/M7/M8 被判"环境炸了" |
| 3 | FAILED 行用 `split(" ")[0]` 提取 nodeid，而 parametrize id 里**含空格**（`…-unavailable-neo4j down]`） | nodeid 被砍成两截 → M7/M8/M9 判"预期门没红"，而它们**明明红了** |

三个都只在判据收紧后才暴露 —— 宽松判据下"有任意 FAILED 就算过"，
nodeid 解析对不对根本不被检验。**判据一严，解析质量才第一次被考。**

另：bug ③ 正是 Codex round-4 顺带提到的"exact nodeid 被空格截断"，
我当时没验就放过了，结果它就是下一个绊倒我的东西。

**最终结果**：14 个变异**全部被抓且含全部预期门**（含 M12a/M12b）。

### MEDIUM-3 / MEDIUM-4 / LOW-2

| # | 内容 | 处置 |
|---|------|------|
| MEDIUM-3 | §七之二 是旧快照：写 75 passed / 新增 73 / pending 14,449 B，实为 81 / 79 / 14,020 B | 数字更新；**字节数不再写死**（活文件，写死必过期）；"跑了 4 次"改成"**至少 4 次**（无独立证据）" |
| MEDIUM-4 | 冻结清单排除验收单 → "证据—声明同一快照"没被证明 | 认同。改为：**施工期排除是脚手架，终验清单不排除** —— 验收单定稿后重新生成清单并纳入，由 commit 锚定 |
| LOW-2 | 写"19 文件 5 组"，实为 6 组 | 按实数改 6 组 |

### 本轮**未采纳**：无。7 条全部认领。

---

## 三之三、完整改动清单（`git status` 逐条，含证据目录）

| 状态 | 路径 |
|------|------|
| M | `backend/app/models/memory_schemas.py` |
| M | `backend/app/api/v1/endpoints/memory.py` |
| M | `backend/app/api/v1/endpoints/rag.py` |
| M | `backend/app/core/decision_tracker.py` |
| M | `backend/tests/integration/test_memory_subject_filter.py`（断言适配） |
| M | `tests/integration/test_memory_api.py`（断言适配，仓库根 `tests/`） |
| ?? | `backend/tests/api/v1/endpoints/test_memory_four_state_api.py` |
| ?? | `backend/tests/api/v1/endpoints/test_rag_four_state_api.py` |
| ?? | `_bmad-output/审查/CARD-G4-3-验收单.md`（本文件） |
| ?? | `_bmad-output/审查/CARD-G4-3-状态词汇对齐登记.md` |
| ?? | `_bmad-output/审查/codex-review-CARD-G4-3.md` |
| ?? | `_bmad-output/审查/evidence-g43/`（6 个证据文件 + 变异脚本） |

| ?? | `_bmad-output/审查/codex-review-CARD-G4-3-round2.md` |
| ?? | `_bmad-output/审查/codex-review-CARD-G4-3-round3.md` |
| ?? | `_bmad-output/审查/CARD-G4-3-证据冻结清单.txt` |

共 **15 项**（`git status --short | wc -l` 实数，2026-08-31 11:45）；
`evidence-g43/` 内为 **6 个 txt + 1 个脚本**（`01/02/03/04/05/06` +
`mutation_gate_check_g43.py`）。

> ⚠️ 这个数字会随每一轮审查存档增加而变（round-1 时 12、round-2 时 13、
> round-3 时 14、本次 15）。**读者请以 `git status --short | wc -l` 的实跑为准**，
> 不要以本行为准 —— 我已经在这一栏错过三次，根因是"手写一个会变的数字"。
> **这一栏我错了三次**（如实记）：round-1 LOW-4 指出漏了证据目录与审查文件；
> round-2 LOW-5 指出漏了 round2 审查文件、且 evidence 数写错；改完之后我又把
> 总数写成 13（当时确实是 13，但随后新增了证据冻结清单，没同步）。
> 现在的数字来自 `git status --short | wc -l` 与 `ls evidence-g43 | wc -l` 的**实跑**，
> 不是我数的。教训：**清单类数字必须由命令产出，不能手写**。

---

## 三之四、证据冻结清单（SHA-256）

Codex round-2 MEDIUM-2 的核心指控是「证据跨快照」—— 我一边改一边生成证据，
于是文档里的数字和证据文件里的数字对不上。处置：**改动定稿后一次性重生成全部
证据**，并落下面这份哈希清单。清单生成之后不再编辑任何证据文件。

全文：`_bmad-output/审查/CARD-G4-3-证据冻结清单.txt`

**round-3 LOW-3 整改**：前版只绑 evidence 的 7 个文件，无法证明「代码—测试—
证据—声明」出自同一快照。现已扩到 **6 个 artifact 分组**：生产代码 4 + 新增测试 2
+ 断言适配 2 + 登记文档 1 + 审查存档 N + 证据 7。
（Codex round-4 LOW-2 指出我写"5 组"是数错了，实为 6 组。）

> **验收单自身（本文件）在施工期不在清单内** —— 它要在清单生成后继续追加
> 「round-N 整改记录」，绑进来只会让哈希在下一次编辑时立即失效。
>
> ⚠️ **但 round-4 MEDIUM-4 指出这个例外不能作为终验形态**，我认这个判定：
> 验收单正是**主要声明载体**，把它排除在外，"证据—声明同一快照"就没被证明。
> **收尾时的做法**（本卡采用）：验收单定稿 → **重新生成清单并把验收单纳入**
> → 清单与最终 commit 一起提交，由 commit hash 锚定。
> 即：施工期排除是脚手架，**终验清单不排除**。

| 文件 | 内容 | 对应验收单的数字 |
|------|------|----------------|
| `01-review-suggestions-消费方证据.txt` | `git grep` A–E 五组 + E 组 9 条逐条定性 | §四「活跃源码零消费方 / 归档 1 个 / 仓外 UNVERIFIABLE」 |
| `02-先红-定稿测试在HEAD代码上的回放.txt` | 定稿测试 × HEAD 生产代码 → **48 failed / 33 passed** | §三「先红后绿」 |
| `03-基线失败清单-59条.txt` | 基线 FAILED nodeid 排序清单 | §五 |
| `04-变异门验证-输出.txt` | **14 变异** × **五条 AND 判据（收集成功 / 收集数 == 基线 / rc==1 / 零 ERROR / 实际 FAILED ⊇ 预期 nodeid 精确到参数实例）** | §三「变异验证」 |
| `05-最终失败清单-59条.txt` | 定稿 FAILED nodeid 排序清单 | §五 |
| `06-comm对账.txt` | 双向差集 + 两清单 SHA | §五 |
| `mutation_gate_check_g43.py` | 可复跑变异脚本（含加固后的 `judge_kill`） | §三 |

**其中最强的一条**：`03` 与 `05` 的 SHA-256 **完全相同**
（`6a109e8e32832cca9996686332eb5b8650dae13d15fa6681276dc6aefeb8c6b7`）——
两份失败清单**逐字节同一**，比"comm 输出为空"更硬（comm 空只证明差集为空，
SHA 相同直接证明文件同一）。

### 先红后绿的做法（round-2 后重做）

前版的"先红"是"实现前跑一次"的历史记录，无法复现。现在改为**可复跑的回放**：
用 `git show HEAD:<4 个生产文件>` 覆盖工作树 → 跑裁判命令 → `finally` 还原。

结果：**48 failed / 33 passed**。那 33 条先绿的正是"旧契约别坏"的守门用例
（Legacy 副本解析、required 集合、条目字段等）—— 它们在 HEAD 上就该绿，
在定稿后也必须仍绿；**它们变红才是真正的坏消息**。

---

## 四、拍板项 1 的选择记录与"加性"字面豁免

### 选择：**换信封**（按手册 §一「不拍按推荐」+ 推荐「换」执行）

手册 §一 三个待拍板项写明「**不拍按推荐**」，拍板项 1 的推荐是「换」；
本批 `/goal` 完成条件 (b) 亦写「默认换信封结构」。截至本卡收尾，
**用户未就此项下达与推荐相反的裁定**，故按推荐默认执行。

**若用户在早间验收决定回退**：撤回 `ReviewSuggestionsResponse`、把
`response_model` 改回 `List[ReviewSuggestionResponse]`、端点返回 `result.items`，
并撤回本节的豁免记录与 §三 的两处测试断言适配。
`test_review_suggestions_envelope_is_declared_breaking_not_additive` 会在回退后
变红，是刻意留的哨兵。

### "加性"字面豁免的显式记录

本卡的铁律是**加性**（旧必填键全保留、200 语义不变）。`/review-suggestions`
**不满足这条铁律**，是本卡唯一的破坏性变更：

- JSON 顶层是数组时，体内**物理上**没有位置承载 `retrieval_status`——
  不是"懒得做加性"，是加性在此不可能。
- 备选方案（放 HTTP 响应头）会让状态脱离响应体、无法进 OpenAPI 值域约束、
  与另外三个端点的字段名不一致，等于制造第二套词汇——与本卡目的相反。

**这一处在文档、代码 docstring、端点 description、测试用例四处都被明确标注为
"破坏性"，不使用"加性"措辞掩盖。**

### 消费方 grep 证据（可复现，含每条的完整命令）

命令与完整输出：`evidence-g43/01-review-suggestions-消费方证据.txt`（A–E 五组，
每组都写了可直接粘贴复跑的命令行）。

| 组 | 面 | 结果 |
|---|-----|------|
| **A** | 活跃前端/插件/sidecar（`*.ts *.tsx *.js *.jsx *.vue *.svelte *.html`，排除 `node_modules` 与 `_archive`） | **零命中** |
| **B** | `frontend/` 与 `canvas-vault/` 两棵活跃树（任意扩展名） | **零命中** |
| **C** | backend 活跃 Python 客户端/脚本 | 仅命中本卡新增的 `memory_schemas.py:553` docstring |
| **D** | **`_archive/` 归档面** | ⚠️ **有真实消费方**，见下 |
| **E** | 全仓兜底（去 node_modules/.venv/docs/_bmad/_plans/.md/测试/归档） | 仅端点自身 + 服务层 docstring + `backend/openapi.json:5282`（生成快照，§六 只登记不修） |

### ⚠️ 结论收窄（Codex round-1 MEDIUM-1，我的初版结论说过头了）

初版写的是「**零生产消费方**」。实测有一个反例，必须收窄：

**`_archive/canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts:1413`**
是 **git tracked** 的真实 HTTP 客户端：

```ts
async getReviewSuggestions(query): Promise<MemoryReviewSuggestionItem[]>
  → this.request<MemoryReviewSuggestionItem[]>('GET', `/memory/review-suggestions?...`)
```

它**期望裸数组**，信封化会破坏它。性质判定：该插件属 Tauri 时期已淘汰产物
（归于 `_archive/`，不在活跃构建链，无运行时消费），但**它是代码不是文档**，
初版 grep 把 `_archive` 一并排除掉了，属于我把证据范围划得对自己有利。

**准确表述**：*当前仓内**活跃**生产源码消费方为 0；归档树中存在 1 个期望裸数组的
客户端，若将来复活需同步改为读 `items`；**仓外**（Claude Code / Claudian /
用户本地脚本）消费方 **UNVERIFIABLE**，本卡无从证明。*

**补充核实**：`LearningMemoryClient`（`backend/app/clients/neo4j_edge_client.py:755`）
是**本地 JSON 文件存储客户端**（`storage_path`；读在 :766-796，写是 :817-824 的原子写入），**不是**我初版写的"Neo4j 直连"——它只是恰好定义在
`neo4j_edge_client.py` 里，被文件名误导。无论如何它**不走 HTTP**，不消费本端点
—— 结论不变，措辞已更正（Codex round-1 LOW-3）。

### ⚠️ 手册"零消费方"未涵盖的一项：测试侧有 6 处结构断言

手册 §一 的「实测零消费方」指的是**生产**消费方，这一点我复核成立。但换信封
**确实**打破了 6 处既有测试断言（3 个断言点在根 `tests/integration/test_memory_api.py`，
3 个在 `backend/tests/integration/test_memory_subject_filter.py`），已随本卡同批改写。
如实记录，不当作"零代价"。

---

## 五、既有套件 comm 对账

**口径**：同一条 pytest 命令，改动前后各跑一次，比对 `FAILED` 集合。
选择集覆盖本卡可能波及的全部面：`tests/api` 全目录 + 两个 memory/rag 集成文件 +
G4-2 的四态单测 + 根 `tests/integration/test_memory_api.py`。

```
cd backend && caffeinate -i .venv/bin/pytest \
  tests/api \
  tests/integration/test_memory_subject_filter.py \
  tests/integration/test_rag_multimodal_api.py \
  tests/unit/test_four_state_injection.py \
  tests/unit/test_service_status_contract.py \
  tests/unit/test_rag_multimodal_integration.py \
  ../tests/integration/test_memory_api.py \
  -q -p no:cacheprovider --override-ini="addopts="
```

| | 结果 | 收集总数 | 耗时 |
|---|------|---------|------|
| **基线（HEAD 9cf0fb85 代码态）** | **59 failed / 243 passed** | 302 | 1053s |
| **定稿（round-1/2/3/4 全部整改后）** | **59 failed / 322 passed** | 381 | 1752s |

**结论：新增失败 = 0。** 通过数 243 → 322，增量 **+79 恰等于本卡新增用例数**；
收集总数 302 → 381，差值同为 79 —— 这也**反证**定稿那一跑收的是最终版测试
文件（而不是中途某个旧版本）。

> Codex round-2 MEDIUM-2 指出前几版证据「跨快照」（`04` 输出还写着 67 passed、
> 验收单称 361 collected 而当时已是 372）。原因是我一边改一边生成证据。
> 现在的做法：**改动定稿后，所有证据一次性重生成**，并落 §三之四 的 SHA-256
> 冻结清单，让"文档数字"与"证据文件"能被逐条对上。

**基线 59 条失败的归因（实查）**。按文件分布：
`test_memory_subject_filter.py` 25 · 根 `test_memory_api.py` 21 ·
`test_rag_multimodal_api.py` 7 · `test_rag_multimodal_integration.py` 4 ·
`test_recommend_action.py` 1 · `test_metadata_subject_mapping.py` 1。

按根因分类（**59 个失败块逐个归类，零未归类**；分类脚本按 `^_+ (.+?) _+$`
切块后逐块正则匹配，合计校验 = 59）：

| 类别 | 条数 | 根因 |
|------|------|------|
| **鉴权** | **46** | `require_internal_api_key`（ChatGPT-DR P0-3 加固）在这些老测试里从未被满足 → `403` / `503` / 响应体 `{"detail": "Internal API key not configured..."}` |
| mock 签名陈旧 | 7 | `mock_query() got an unexpected keyword argument 'subject_id'` —— 测试的假 service 签名没跟上真实 `RAGService.query` |
| 幽灵包私有符号 | 3 | `ImportError: cannot import name` —— 前两条是 `_fuse_rrf_multi_source`，第三条是 `_fuse_weighted_multi_source`（`agentic_rag.nodes` 是 re-export 壳，私有 helper 在 `_nodes_impl`） |
| 陈旧 group_id 期望 | 1 | `test_metadata_group_id_format` 期望 `math54:线性代数`，实际已是 vault 作用域格式 `vault:canvas_vault:math54:线性代数` |
| mock 主动抛错逸出 | 1 | 测试注入的 `Mock history query error` 未被吞 |
| coroutine 未 await | 1 | `TypeError` |
| **合计** | **59** | 与 `FAILED` 行数逐条对上 |

> **两次自我更正，如实记**（都是我的分类脚本写错，不是数据变了）：
> 1. 初稿写「59 条**全部**是 403/503/500」——不成立。第一版正则只抓状态码
>    数字，把响应体写着 `Internal API key not configured`、断言里却没打状态码
>    的 2 条误判成"非鉴权"。
> 2. 第二版写「解析出 50 个块，41 auth / 5 RAG 服务未就绪」——**块数本身就是
>    错的**。我用了个有状态的切块循环，丢了 9 块；换成 `re.split` 后实际是
>    59 块，与 `FAILED` 行数严格相等。而且那 5 条根本不是"服务未就绪"，是
>    mock 签名陈旧（共 7 条）。
>
> 教训同型：两次都是**把脚本的输出当成事实**，而没有先验证脚本自身的完备性
> （块数 == FAILED 行数 这个校验，第三版才加上）。上表的"合计=59、零未归类"
> 就是补上的那道自检。

**判据归属声明**：以上分类是辅助说明。验收判据是下方 FAILED 测试 id 集合的
comm 差集，与分类是否精确无关。

**⚠️ 由此得出一条必须写清楚的事实**：我在 §三 改了断言的那两个文件
（`test_memory_api.py` / `test_memory_subject_filter.py`）**在基线时就已经
全红**（21 + 25 = 46 条，全部落在鉴权类里）。我的断言修改让它们的**契约期望**与新
响应形状一致了，但它们**仍然是红的**，因为红的原因是鉴权而不是响应形状。

换句话说：**这两个文件不能作为"信封改对了"的证据**。信封的正确性由新增的
`tests/api/v1/endpoints/test_memory_four_state_api.py`（显式 override 鉴权依赖）
证明。这两个文件的修改属于"不让它们在鉴权修好之后立刻因为形状再红一次"的预置。

这也解释了新测试为什么要 `app.dependency_overrides[require_internal_api_key]`——
不是为了绕过安全检查，而是让失败信号只可能来自四态字段本身。

### comm 差集（判据本体）

把两次 `FAILED` 行提取成排序后的测试 id 集合逐行比对：

```
$ comm -23 baseline-failures.txt after-failures.txt   # 仅基线有 = 本卡修好的
(空)
$ comm -13 baseline-failures.txt after-failures.txt   # 仅变更后有 = 新增失败
(空)
```

**两个方向都为空 —— 失败集合逐条相同，零新增失败，也零意外修复。**

零意外修复这一条同样重要：它印证了 §五 上文那个不好看的事实 —— 我改了断言的
两个测试文件仍然全红（鉴权），我的修改**没有**把它们变绿，验收单不能把它们
算作本卡的战果。

证据存档：`evidence-g43/03-基线失败清单-59条.txt` /
`evidence-g43/05-最终失败清单-59条.txt` / `evidence-g43/06-comm对账.txt`。

**两份清单的 SHA-256 完全相同**（`6a109e8e…c6b7`）—— 这比"comm 输出为空"更强：
comm 为空只说明差集空，SHA 相同直接说明**两份文件逐字节同一**。

---

## 六、openapi 漂移登记（只登记，不修）

卡文：「openapi 漂移只登记不吞收债卡（D4 裁决点未批）」。本卡**未重新生成**
`backend/openapi.json`。登记两条事实：

1. **快照已陈旧 5 个月**：`backend/openapi.json` 的
   `info["x-generated-at"] = "2026-03-31T12:55:27Z"`。其
   `/api/v1/memory/review-suggestions` 的 200 schema 仍是
   `{"type": "array", "items": {"$ref": ".../ReviewSuggestionResponse"}}`，
   与本卡后的实际实现（`$ref: .../ReviewSuggestionsResponse` 信封）不一致。
   本卡新增的 4 处 `retrieval_status` 字段同样不在快照里。

2. **漂移门本身是坏的（本卡顺手发现，未修）**：
   `.github/workflows/api-spec-sync.yml` 的漂移比对逻辑是
   `if [ -f "openapi.json" ]`（第 82、175、405 行），检查的是**仓库根**的
   `openapi.json`——而该文件实际在 `backend/openapi.json`，仓库根**不存在**
   同名文件（已实查：`ls openapi.json` → No such file）。因此该 workflow 的
   drift 检测恒走 `else` 分支（"No existing openapi.json found" → `changed=true`），
   **从未真正比对过任何东西**。

   → 建议登记为独立收债卡（提名 **CARD-DEBT-openapi-sync**）：先修 workflow 的
   路径，再决定 `backend/openapi.json` 是重新生成还是退役。**不在本卡范围**，
   本卡未改该 workflow 一行。

3. 对本分支的实际影响：**无**。该 workflow 只在 `pull_request` 与 `push` 到
   `main`/`clean-release` 时触发，本卡不 push。

---

## 七、硬边界遵守声明

| 边界 | 遵守情况 |
|------|---------|
| 不碰 `rag_service.py` / `memory_service.py` 服务层实现（只透传） | ✅ 两文件 `git diff` 为空。端点从 `get_review_suggestions()` 换成 `get_review_suggestions_with_status()` 属**换调用点**，两个方法均为 G4-2 已存在的公开方法，未新增/修改任何服务层代码 |
| 不碰 G4-4 战场的请求侧 scope 逻辑 | ✅ `chat.py` / `agents.py` 未改；`memory.py` 里 `_resolve_vault_group_id(...)` 调用点一行未动 |
| 不重新生成 `backend/openapi.json` | ✅ 未改，见 §六 |
| commitlint header ≤100 / body 行 ≤100 | 见 §八 |
| 不 push | ✅ |
| live vault 与 Neo4j 7691 只读 | ⚠️ **部分守住，一处越界，如实登记** —— 见 §七之二 |
| `exam_service` / `verification_service` 禁改 | ✅ 未触及 |

### 七之二、⚠️ 数据库副作用的如实登记（Codex round-3 HIGH-2）

我原先在这一栏写的是「本卡全程零数据库写；测试全部为进程内 mock，不连任何
数据库」。**这句话是错的**，Codex round-3 实证推翻。逐条厘清：

#### 裁判命令 —— 干净（实测）

```
$ cd backend && caffeinate -i .venv/bin/pytest tests/api -q -k "memory or rag"
81 passed …
PORT7691_SOCKET_CALLS = 0          ← Codex round-4 独立复跑（socket 层计数）
data/bug_log.jsonl                     SHA 前后一致 ✓
app/data/vault_index_pending.jsonl     SHA 前后一致 ✓
```

本卡**新增的 79 个用例**全部是进程内 mock + 裸 `FastAPI()` 挂 router
（不走 `app.main`，因此不触发 lifespan），这部分声明成立。

#### comm 全量命令 —— **有副作用，越界了**

`§五` 的 comm 对账命令包含 `tests/api` 整个目录，其中
`test_metadata_subject_mapping.py:57-61` 用的是
`from app.main import app` + `with TestClient(app)` —— **会启动真实 lifespan**：

- `main.py:159` 预热真实 `MemoryService` → 连 `bolt://localhost:7691`
- `memory_service.py:287` 执行真实 DDL（`CREATE FULLTEXT INDEX … IF NOT EXISTS`）
- 副作用落到两个 **git-ignored** 的运行时文件：
  `backend/app/data/vault_index_pending.jsonl`、`backend/data/bug_log.jsonl`
  （⚠️ 不在此写具体字节数 —— 它们是活文件，写死一个数字下一次就过期；
  round-4 就抓到我写的 14,449 B 已变成 14,020 B）

**跑了几次**：我登记为「**至少 4 次**」。这个数字来自我自己的回溯，
**没有独立证据**（未留逐次记录）—— Codex round-4 指出 exact 4 不可独立证明，
这个更正是对的。

**性质判定**：
- 这个测试文件是**存量**（HEAD 就是这样，本卡未改，`git hash-object` 已验与 HEAD 同）；
- DDL 是 `IF NOT EXISTS`，索引已存在 → **本次无 schema 变更**；
- 但卡文硬边界写的是「live vault 与 Neo4j 7691 **只读**」，而我为了做 comm 对账
  **跑了 4 次**这条命令 —— 即便每次都是幂等 DDL，**"我不知道它会连库"本身就是问题**，
  这条边界我是撞过去的，不是守住的。

**我没有做的事（避免二次伤害）**：未删除新生成的 pending 文件、未回滚
`bug_log.jsonl`（无前像可回滚）。两文件均 git-ignored，不进本卡提交。

**移交**：提名 **CARD-TEST-isolate-lifespan** —— 给 `tests/api` 下用
`app.main.app` 的测试补 lifespan 隔离（`transport=ASGITransport` 或
override 掉预热依赖），并在 CI 加"跑完比对运行时文件 SHA"的门。
本卡不改该文件（存量、非本卡战场）。

**教训**：我把"我写的测试是 mock 的"直接推广成了"这条命令不连数据库" ——
命令里还有别人的测试。**声明的射程必须等于命令的射程，不是我写的那部分的射程。**

### 与 V1 车道（G4-1b）的合并顺序

手册 §四：「V1 与 V4 同触 `endpoints/memory.py`——合并顺序 V1 先 V4 后，
V4 开工前 grep 确认」。开工前已确认本 worktree 基线 = `9cf0fb85`，与 V1 同源。

本卡在 `memory.py` 的触点（供合并时对照）：

| 位置 | 本卡改动 |
|------|---------|
| 顶部 import 块 | +`log_retrieval_status_decision`、+`ReviewSuggestionsResponse` |
| `MemoryServiceDep` 之后 | +一段说明性注释块（无代码） |
| `get_learning_history` 的 `return` 前 | +取状态 +落 trace +2 个 kwarg |
| `get_concept_history` 的 `return` 前 | +落 trace（`ConceptHistoryResponse(**result)` 本身未改） |
| `get_review_suggestions` 装饰器/签名/函数体 | `response_model`、返回注解、调用方法、返回结构 |

G4-1b 的触点按其卡文是 `memory.py:260` 端点（`get_concept_history` 加
vault_id/subject_id/group_id 参数）。与本卡的重叠面在
`get_concept_history` 函数内：**G4-1b 改参数列表，本卡在函数体 return 前插入
trace 调用**，两者不在同一行，预期为可自动合并的相邻改动。合并后建议复跑
`pytest tests/api -k "memory or rag"`。

---

## 八、提交

```
commit: feat(api): 四态贯穿 API/trace 面 [BATCH-2026-08-31-第七批 / CARD-G4-3]
```
未 push。

---

## 九、格式门说明

`ruff check` 全绿。`ruff format --check` 逐文件对照 HEAD 基线：

| 文件 | HEAD | 现在 | 处置 |
|------|------|------|------|
| `memory_schemas.py` / `memory.py` / `rag.py` / `test_memory_subject_filter.py` / 根 `test_memory_api.py` | DRIFT | DRIFT | **存量漂移，不动**（格式化会产生与本卡无关的大 diff，违反「禁止一次修复混合多个不相关变更」） |
| `decision_tracker.py` | **clean** | 曾 DRIFT | 我引入的 → **已正式 `ruff format`** |
| 两个新测试文件 | 新增 | — | 已 `ruff format` |

判据来源：`git show HEAD:<path> | ruff format --check --stdin-filename <path> -`
（缺 `--stdin-filename` 会拿到假判定）。

---

## 十、遗留与移交

| 项 | 去向 |
|----|------|
| chat enrich degraded bool 四态化 | 提名 **CARD-G4-3b**，必须在 G4-4 之后（同文件硬冲突）——见附件 |
| MCP `source_status` 四态化 | 提名 **CARD-G4-3c**，需先盘清仓外消费面——见附件 |
| `board_manifest` 的 `degraded` 四态化（保留 `source_status` 来源维度） | 提名 **CARD-G4-3d**——见附件 |
| memory health 二/三态 | **裁定保持独立**，不对齐（组件健康 ≠ 单次调用可信度）——见附件 |
| `openapi.json` 陈旧 + drift 门路径写错 | 提名 **CARD-DEBT-openapi-sync**——见 §六 |
| 四态的 **UI 消费面**（Claudian 侧栏 / 总览页徽标 + 浏览器走查截图） | **本卡未做**（`/goal` 完成条件未含），总账原卡文有此项，需用户裁定是否另立卡 |
| 根 `tests/integration/test_memory_api.py` 与 `test_memory_subject_filter.py` 的鉴权全红（46 条） | **存量债，非本卡引入**。需要一张卡给这两个文件补 `require_internal_api_key` 的 dependency override 或 API key header |
| 观测故障能升成 5xx 的**已知**绕过点（**不宣称列全**）：`rag_service.py:194/209/274-287/289-290/326-333`、`rag.py:374-380`、**`rag.py:419` 与 `:441`（`/weak-concepts` 端点，本卡未碰的存量）**、`vault_scope.py:133/184-198`、`memory_service.py:665-682/748→2753/843-850/1080-1089`、`neo4j_client.py:746`、`lib/agentic_rag/nodes.py:1873`，以及 `memory.py:268/323/436` 的 except 日志（不会把成功变 500，但会把结构化 detail 遮成裸 `Internal Server Error`） | **同型存量债**。提名 **CARD-OBS-nothrow-logging**，范围：**endpoint + 依赖初始化 + service recovery + vault/client + LangGraph nodes + except 分支日志**。本卡只修自己引入/自己文件内的两处（`log_retrieval_status_decision`、`rag.py:274`），其余**移交不修**。⚠️ 本行**刻意不写"全部"** —— round-1/2/3/4 每轮都又找出新的，这类点只能靠逐个注入实证发现 |
| 变异脚本 `mutation_gate_check_g43.py` **原地改工作树源码**再还原 | 已有 `finally` + `filecmp` 逐字校验，但**进程被强杀时无法保证**，且与并发编辑不兼容。更稳的做法是在 `git archive` 出来的临时 worktree 里跑。登记为后续改进（Codex round-1 LOW-4），不在本卡范围 |
