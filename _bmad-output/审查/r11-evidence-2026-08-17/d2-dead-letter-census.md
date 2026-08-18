# D-2 死信队列重数盘点（只读）

> **批次**：R11-BATCH2-2026-08-17 · T5
> **性质**：只读盘点，本项不改任何代码
> **数据源**：`backend/data/dead_letter_episodes.jsonl`（92 行 / 99915 B / mtime 2026-08-11 22:01:25）

---

## 0. 先纠正一处历史记忆

旧记忆记载「live 是 `WT/data/` 那 1 条、`WT/backend/data/` 92 条是陈旧文件」。**实测相反**：

| 路径 | 行数 | mtime | 容器可见性 |
|---|---:|---|---|
| `worktree/backend/data/dead_letter_episodes.jsonl` | **92** | 2026-08-11 | ✅ 容器 `/app/data` 呈现的就是这份 |
| `worktree/data/dead_letter_episodes.jsonl` | 1 | 2026-07-13 | ❌ 被父挂载遮蔽，容器看不见 |

容器 `/app/data` 经由 `./backend:/app` 解析到 `backend/data/`（详见同批 T1 的 compose 地雷分析）。**92 行那份才是 live 面。**

---

## 1. 重数结果

- **总量 92 条**，全部可 JSON 解析（0 条损坏）
- **时间跨度**：`failed_at` 2026-05-14 → 2026-08-11（约 3 个月）
- **retry_count 全部 = 3** —— 无一例外都重试到上限才落死信

### 按日分布（爆发式，非均匀）

| 日期 | 条数 | 占比 |
|---|---:|---:|
| 2026-05-14 | 3 | 3% |
| 2026-08-08 | 8 | 9% |
| **2026-08-09** | **48** | **52%** |
| 2026-08-10 | 25 | 27% |
| 2026-08-11 | 8 | 9% |

**89 条（97%）集中在 8/08–8/11 四天**，其余 3 条是 5 月的孤立事件。这不是长期渗漏，是一次持续四天的集中故障。

### 按来源分布

| source_description | 条数 | 内容性质 |
|---|---:|---|
| `canvas_learning:qa_highlight` | 45 | 问答高亮（学习记忆） |
| `canvas_learning:conversation_distillation` | 22 | 对话蒸馏摘要 |
| `conversation-archive` | 22 | 会话归档 |
| `callout-annotation-record` | 3 | 批注记录 |

**丢失的全部是学习记忆类内容**，无系统/运维类 episode。

### 按 group_id 分布

| group_id | 条数 |
|---|---:|
| `vault:canvas_vault` | 89 |
| `vault:default` | 3 |

---

## 2. 根因（三类，高度集中）

### ① `exceed_context_size_error` — 89 条（97%）

```
Error code: 400 - {'error': {'code': 400,
  'message': 'request (16998 tokens) exceeds the available context size (16384 tokens), try increasing it',
  'type': 'exceed_context_size_error', ...
```

本地 LLM 的 **`n_ctx = 16384`**，而 Graphiti 结构化抽取请求达 **16998 tokens**——超出约 614 tokens（3.7%）。

触发条件可从 `episode_body_length` 看清：

| 统计量 | 值 |
|---|---:|
| min | 131 |
| 中位 | 341 |
| **max** | **8036** |
| \>200 字符的条数 | 88 |

**后 10 条声明长度全部等于 8036** —— 存在一批体量整齐的大 episode。8036 字符的正文，叠加 Graphiti 的 entity/edge 类型定义模板与抽取指令，就把 16384 的窗口撑爆。

⚠️ **`n_ctx` 配置不在仓库内**（本次全仓 grep 零命中），位于本地模型启动脚本 / launchd 配置中 —— 属 D-2 修复本体，本批不动。

### ② `EntityTypeValidationError` — 2 条

```
name cannot be used as an attribute for LearningConcept as it is a protected attribute name
created_at cannot be used as an attribute for LearningTip as it is a protected attribute name
```

自定义实体类型的属性名与 Graphiti 保留字冲突。属 schema 定义缺陷，与上下文长度无关。

### ③ `GroupIdValidationError` — 1 条 ⚠️ 值得单独标记

```
group_id "vault:default" must contain only alphanumeric characters ...
```

**这与项目已定的 group_id 物理格式规约直接冲突**：Neo4j 物理 group_id 应统一为 `vault__x` 双下划线形式，所有 Cypher 绑定必须经 `to_physical_group_id()` 转换。此处 `vault:default` 带冒号直接送到了 Graphiti，说明**存在一条未过转换函数的写入路径**。

虽然只有 1 条，但它暴露的是**契约旁路**而非偶发错误 —— 建议单独立项核查，不要淹没在 n_ctx 议题里。

---

## 3. 正文完整性与可重放性

### 关键澄清：正文缺失是设计，不是缺陷

`DeadLetterStore` 的 docstring（`episode_worker.py:200-224`）明确记载这是 **audit-2026-04-07/p1-1 的隐私改写**，防的是 CWE-532：

> 此前每次失败都存完整 `episode_body` 明文 —— 意味着 LLM 看到的一切内容（PII、学生答案、含指令的系统提示、偶发泄漏的凭证）被永久归档；叠加该文件在某些失败模式下会被提交进 git，构成 CWE-532 向量。

现行契约：

| 字段 | 是否留存 | 说明 |
|---|---|---|
| `episode_body_sha256` | **92/92 有** | 对**完整正文**计算，供重放时校验一致性而不暴露内容 |
| `episode_body_length` | 92/92 有 | 完整正文的原始长度 |
| `episode_body` | 92/92 有，但**截断至 200 字符** | 来自 `EpisodeTask.to_dict()`（`:108` 注释写明 `truncate for logging`） |
| `episode_body_full` | **0/92** | 仅当 env `DEAD_LETTER_STORE_FULL_BODY=true` 才写；容器实测该 env **未设置** |

> 📌 若直接拿 200 字符的 `episode_body` 去比对 `episode_body_sha256`，会看到「88 条校验失败、4 条通过」——那是**预期行为**（通过的 4 条只是原文本身 ≤200 字符），不是数据损坏。初次分析时我曾据此误判为「正文被截断导致无法重放」，此处更正。

### 重放所需字段齐备度

| 字段 | 齐备度 | 重放用途 |
|---|---:|---|
| `name` | 92/92 | 定位原始条目 |
| `source_description` | 92/92 | 判定来源管道 |
| `reference_time` | 92/92 | 时间锚点 |
| `group_id` | 92/92 | 目标图分区 |
| `request_id` | 92/92 | 经 traces 端点回溯完整链路 |
| `entity_type_names` | **70/92** | 抽取 schema |
| `edge_type_names` | **70/92** | 抽取 schema |
| 完整正文 | **0/92** | ⛔ 必须从原始来源重取 |

**结论**：死信记录本身**不足以独立重放**，但足以**定位并重建** —— 凭 `name` + `source_description` + `request_id` 回到原始 vault 笔记/会话取正文，再用 `sha256` 校验取到的内容与当初失败的是否同一份。22 条缺 `entity_type_names`/`edge_type_names` 的需额外确定 schema。

---

## 4. 生产者 / 消费者拓扑

### 生产者（唯一）

- `app/services/episode_worker.py:641 / 655 / 658` → `self._dead_letter.store(task, error)`
- 存储实现：`DeadLetterStore`（`:200-265`），同步 append JSONL
- 另有 `app/core/failure_counters.py:73` 的 `write_dead_letter()`（独立通道，未写入本文件）

### 消费者（**无 replay，仅只读分析**）

| 消费方 | 用途 | 是否重放 |
|---|---|---|
| `app/api/v1/endpoints/traces.py:23` | `GET /api/v1/traces/{request_id}` 按 request_id 聚合时间线 | ❌ 只读查询 |
| `backend/scripts/generate_regression_tests.py:156` | 读死信生成回归测试 | ❌ 只读分析 |

**全仓 grep `replay` / `重放` / `reprocess` / `requeue` 与 dead_letter 的交集：零命中。**「replay」一词只出现在 `DeadLetterStore` 的 docstring 里，描述的是**设计意图**而非既有实现。

> **这是本次盘点最重要的发现**：92 条死信处于**永久搁浅**状态 —— 有完善的入队、重试、隔离、隐私保护和可观测性，但**没有任何出口**。写进去就再也没有代码会把它们取出来。

---

## 5. 对 D-2 优先级的建议

### 建议：**维持 D-2 现有优先级，但拆成三个独立子项**，其中一项应提前

当前 D-2 被当作单一议题（「n_ctx 不够」），但盘点显示它实际是三件事，紧迫度不同：

| 子项 | 覆盖 | 建议优先级 | 理由 |
|---|---:|---|---|
| **D-2a** 调大 `n_ctx` / 对超长 episode 做分片 | 89 条 | **维持原优先级** | 根因明确、修复点单一（仓外配置）。但注意：单纯调大 n_ctx 只是把阈值上移，8036 字符那批仍可能在更大内容下复现 —— 分片或预截断才是治本 |
| **D-2b** 建 replay consumer | 92 条 | **维持** | 没有它，D-2a 修好后这 92 条仍然躺着不动。但它依赖 D-2a 先修好（否则重放照样撞墙） |
| **D-2c** `vault:default` 未过 `to_physical_group_id()` | 1 条 | **建议提前，独立立项** | 数量最少但性质最重：这是 group_id 物理格式契约的旁路。1 条是症状，旁路本身可能影响所有经该路径的写入 —— 且与既有的 vault 隔离工作直接相关 |

### 不建议升级 D-2 整体优先级的理由

1. **不在扩大**：89 条集中在 8/08–8/11 四天，8/11 后 7 天无新增。这是已停止的历史故障，不是持续渗漏
2. **无数据丢失风险**：死信是**旁路归档**，原始内容仍在 vault 笔记与会话记录里；丢的是「进图谱」这一步，不是内容本身
3. **影响面已知且有界**：92 条全是学习记忆类（问答高亮/对话蒸馏/归档），不涉及系统状态或用户数据完整性

### 但有一条需要尽快确认

**8/11 之后为何不再新增？** 存在两种可能，含义截然不同：

- ✅ 触发条件消失（那批 8036 字符的大内容处理完了）→ 现状可接受
- ⚠️ **写入通道本身已停摆**（根本没有新 episode 在尝试写入）→ 那是更严重的问题，且会被"死信不再增长"这个表象掩盖

建议在 D-2 开工前先跑一次「近 7 天成功写入的 episode 计数」来区分这两种情况。本批为只读盘点，未执行该查询。

---

## 附：本盘点未做的事

- 未修改任何代码
- 未清空或归档死信文件
- 未查 `n_ctx` 实际配置值（在仓外的本地模型启动脚本 / launchd 中）
- 未验证「重放是否真能成功」（需要 D-2a 先修）
