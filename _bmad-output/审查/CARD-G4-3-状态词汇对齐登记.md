# CARD-G4-3 附件 — 全后端状态词汇盘点与对齐计划（**只登记，不强改**）

> **批次**: BATCH-2026-08-31-第七批 · 车道 V4
> **日期**: 2026-08-31
> **卡文依据**: 完成条件 (d)「chat enrich 链的 degraded bool 与 MCP source_status 三态
> **登记对齐计划不强改**（另立卡候选，防蔓延）」
> **手册依据**: §二 G4-3「已有三套不齐的词汇（chat degraded bool / MCP source_status
> 三态 / memory health 三态）——本卡只对齐主链四态」

---

## 〇、为什么是「登记」而不是「顺手统一」

把这几套词汇一次性改成四态，需要动 `chat.py`（G4-4 战场的同一文件）、
MCP 工具契约（对外协议）、`board_manifest`（D1/A2 总览页与 recap skill 的
既有消费方）。任何一处的值域变更都会**穿透到已有消费方**，而本卡的硬边界写
得很清楚：只透传、不碰服务层、不碰 G4-4 战场。

所以本文件只做三件事：**列清单 → 判可对齐性 → 提名 owner 卡**。
一行生产代码都没有因本文件而改动。

---

## 一、清单：目前后端一共有 5 套状态词汇

| # | 词汇 | 定义位置 | 值域 | 消费面 |
|---|------|---------|------|--------|
| 1 | **ServiceStatus（统一四态）** | `backend/app/models/service_status.py:39` | `ok` / `empty` / `degraded` / `unavailable` | G4-2 服务层读路径、`CanvasRAGState`、**本卡新接入的 4 个 API 端点** |
| 2 | **chat enrich 降级布尔** | `backend/app/api/v1/endpoints/chat.py:237-238`、`:250-258` | `degraded: bool` + `degraded_reason: str\|None`；另有 `supplementary_degraded: bool` + `supplementary_reason` | `/chat` 响应、prompt 内的 `degraded` XML 标注（`chat.py:830-859`） |
| 3 | **MCP note_search 三态** | `backend/app/mcp/tools/note_search_tools.py:124` | `ok_nonempty` / `ok_empty` / `error` | MCP 工具对外协议（`app/mcp/server.py:218` 文档串） |
| 4 | **board_manifest 信封三态** | `backend/app/models/board_manifest.py:204` | `ok` / `snapshot` / `error`（另有独立的 `degraded: bool` + `degraded_reason`） | `/boards` 端点、D1 总览页、board-recap skill |
| 5 | **memory health 层级二态 / 整体三态** | `backend/app/models/memory_schemas.py:285-297` | Layer: `ok` / `error`；Overall: `healthy` / `degraded` / `unhealthy` | `/memory/health` 端点 |

---

## 二、逐套判可对齐性

### #2 chat enrich 降级布尔 → 四态

**结论：可对齐，但必须与 G4-4 同批做。**

- **语义映射是完备的**：`degraded=False` 且有邻居 → `ok`；`degraded=False` 且
  `neighbors_count==0` → `empty`；`degraded=True` 且仍有当前笔记内容 → `degraded`；
  两者皆失且无内容 → `unavailable`。
- **但布尔比四态少一格**：`degraded=False` 无法区分 `ok` 与 `empty`。这正是
  「bool 装不下四态」的根因——它把「空」和「好」压成同一个值。
- **阻塞点**：`chat.py` 是 G4-3 与 G4-4 的**共同战场**（手册 §二 明写「与 G4-4
  强冲突（rag/chat/agents 同文件）」）。本卡碰它必然产生合并冲突。
- **另一条隐性依赖**：`chat.py:839` 把 `degraded="true"` 直接写进**发给模型的
  prompt XML**。改成四态等于改 prompt 契约，需要一并核对模型是否按新值域行事——
  这是行为面而非纯 schema 面的变更，不该藏在一张透传卡里。

### #3 MCP source_status 三态 → 四态

**结论：可对齐，且映射是无损的；但属对外协议变更。**

- `ok_nonempty` → `ok`；`ok_empty` → `empty`；`error` → `unavailable`。
  三个值一一对上，**零语义损失**。
- 缺 `degraded` 一格：MCP 工具当前没有「部分源失败但仍有结果」的表达（
  `note_search_tools.py:190/216` 的注释显示它刻意让基础设施失败**抛出**而不是
  伪装空结果——方向与四态一致，只是词不同）。
- **阻塞点**：`source_status` 是 MCP 工具的**对外契约**，消费方在 Claude Code /
  Claudian 侧，不在本仓 grep 射程内。改值域需要先盘清外部消费面，本卡无从证明
  「零消费方」。

### #4 board_manifest 三态 → 四态

**结论：不宜简单对齐——它表达的是**另一个维度**。**

- `source_status` 的 `ok`/`snapshot`/`error` 回答的是「**数据从哪来**」（live /
  快照回退 / 取不到），而四态回答的是「**结果可不可信**」。
- 证据：该信封**同时**已有独立的 `degraded: bool` + `degraded_reason`
  （`board_manifest.py:207-208`）——即它自己就把「来源」和「可信度」拆成了两个字段。
- 因此正确做法是把它的 `degraded` 布尔升成四态、**保留** `source_status` 作为来源
  维度，而不是把两者揉成一个。这也是本卡不动它的原因：揉错了会丢信息。

### #5 memory health 二/三态 → 四态

**结论：不对齐，且建议永久保持独立。**

- `/memory/health` 回答的是「**这个子系统现在健康吗**」（liveness/readiness 语义），
  四态回答的是「**这一次检索的结果可不可信**」。前者是**组件**属性，后者是**单次
  调用**属性。
- 具体反例：Neo4j 健康（`LayerStatus.ok`）但**这一次**查询超时 → 健康面 `ok`、
  检索面 `unavailable`。二者本就应当能各自取值，合并会丢掉这个区分。
- `OverallStatus` 的 `healthy/degraded/unhealthy` 是运维监控界的通行词汇，与
  Prometheus/告警侧对接，改名的收益为负。

---

## 三、对齐计划（提名，待用户裁决）

| 提名卡 | 范围 | 前置依赖 | 建议时机 |
|--------|------|---------|---------|
| **CARD-G4-3b**（提名）| #2 chat enrich 降级布尔 → 四态；含 prompt XML 值域同步与行为核对 | **必须**在 G4-4 之后或与之同车道（同文件硬冲突） | G4-4 落地后的下一批 |
| **CARD-G4-3c**（提名）| #3 MCP `source_status` → 四态；先做外部消费面盘点再改值域 | 需先有 MCP 工具消费面台账（可并入 DEBT 系列的资产盘点） | 消费面盘清后 |
| **CARD-G4-3d**（提名）| #4 `board_manifest` 的 `degraded: bool` → 四态，**保留** `source_status` 来源维度不动 | D1 总览页与 board-recap 的金样回归必须同批跑 | 独立小卡即可 |
| —— | #5 memory health **不改**，本文件即为其「已裁定保持独立」的记录 | —— | —— |

**防蔓延声明**：以上三张提名卡都**不在**本卡范围内，本卡未为它们写任何代码、
未改任何值域、未新建任何兼容层。若后续有人宣称「四态已全后端统一」，本文件即为
反证——统一的只有主检索链（memory 三端点 + rag/query 共 4 个端点 + 服务层），其余四套仍各行其是。

---

## 四、本卡实际对齐了什么（可核查）

| 面 | 对齐动作 | 位置 |
|----|---------|------|
| API 响应 | `LearningHistoryResponse` / `ConceptHistoryResponse` / `ReviewSuggestionsResponse` / `RAGQueryResponse` 四个模型的 `retrieval_status` 字段**类型即 `ServiceStatus` 枚举**（不是裸 str），OpenAPI 因此带上 `enum: [ok, empty, degraded, unavailable]` 值域约束 | `memory_schemas.py`、`rag.py` |
| trace | `log_decision(output=...)` 在 4 个端点上统一传枚举 **`.value`**（归一收在单点，端点不各写一遍） | `decision_tracker.py::log_retrieval_status_decision`，由 `memory.py` ×3 + `rag.py` ×1 调用 |

`ServiceStatus` 已确认出现在生成的 OpenAPI `components.schemas` 中，值域四项齐全
（实查记录见验收单 §三）。

### trace 面对齐的**完整射程**（实查，非估计）

全仓 `log_decision(` 的 **Call 节点** 共 **19 个**（`app/` + `lib/`，AST 实数；
不是 `grep -c` 的命中行数——我初版写 20 就是把行数当调用数）。逐一核过 `output=`
实参后，**输出状态类语义的只有 2 个**：

| 位置 | output | 处置 |
|------|--------|------|
| `app/services/rag_service.py:278` | `ServiceStatus.UNAVAILABLE.value` | G4-2 已对齐，本卡未动 |
| `app/core/decision_tracker.py:139`（本卡新增单点） | `normalized`（四态枚举归一后的 value），由 `memory.py` ×3 + `rag.py` ×1 共 4 个端点调用 | 本卡落地 |

其余 **17 个**的 `output` 是业务值（episode_id、`"skipped_duplicate"`、mastery 等级、
agent 名等），**与四态无关，不属对齐射程**。即：trace 面的四态对齐在本卡后
**已完整**，没有"漏网的第 20 个"。这一条是为了防止后续出现「trace 也统一了吗」
的含糊宣称——答案是：状态类 output 全部统一，业务类 output 本来就不该统一。
