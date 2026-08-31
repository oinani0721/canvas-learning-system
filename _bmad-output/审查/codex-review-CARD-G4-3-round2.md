# 裁定

**FAIL。需要再一轮。**

本轮结果：**BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 5**。原 BLOCKER-1 已闭合，但端到端观测 fail-open 仍有绕过。

取证截止为 `HEAD 9cf0fb85ed839bb7035d023534fca222a24d6968`；验收单最终观测 SHA-256 为 `b1fff9a2…f757f`。审计期间工作树被外部并发改写：验收单先是 67/69，后变成 70/72，又追加约束说明。以下结论基于最终观测字节，但本轮没有单一冻结快照。

## BLOCKER

### 原 BLOCKER-1：确认无问题，已闭合

三个生产 fallback 位于 [rag_service.py:197](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/rag_service.py:197>)、[rag_service.py:476](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/rag_service.py:476>)、[rag_service.py:495](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/rag_service.py:495>)；响应模型和映射分别在 [rag.py:124](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:124>)、[rag.py:296](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:296>)。

| fallback 键 | 端点处理 | 结果 |
|---|---|---|
| `messages` | 不读取 | 安全 |
| `results=[]` | 仅在缺少 `reranked_results` 时兜底 | 安全 |
| `reranked_results=[]` | 遍历并 `len()` | 安全 |
| `fused_results=[]` | 仅第一个 dict 有；不读取 | 安全 |
| `multimodal_results=[]` | 遍历 | 安全 |
| `quality_grade=None` | `result.get(...) or "low"` | 原 500 已闭合 |
| `result_count=0` | 忽略，由 `len(reranked)` 重算 | 安全 |
| `total_latency_ms=0.0` | 忽略，从扁平 latency 键重算 | 安全 |
| `latency_ms={}` | 不读取；扁平键缺失产生五个 `None`、总和 `0.0` | 安全 |
| `metadata={}` | 不读取；由扁平键构造默认 metadata | 安全 |
| `fallback_used/fallback_reason` | 不读取 | 安全 |
| `error` | 仅后两个 dict 有；不读取 | 安全 |
| `retrieval_status` | `"unavailable"` 命中枚举 | 安全 |
| `retrieval_status_reason` | 字符串进入 `Optional[str]` | 安全 |

没有发现第二个当前真实形状地雷。潜伏表达式是 `reranked_results` 和 `multimodal_results` 的 `.get(..., [])`：未来若键存在但值为 `None` 仍会炸；当前三个 fallback 和初始 state 均为 `[]`。可选防御为统一改成 `... or []`。

可复现结果：

- 两个新增文件：**70 passed（memory 44 / rag 26）**。
- `tests/api -k "memory or rag"`：**72 passed**。
- 在隔离副本把 [rag.py:343](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:343>) 回退为 `.get(k, "low")`：**4 failed**，包括真实 `ainvoke(None)`、initial state、两个 fallback reason。
- `TestRagRealFallbackEntrypoint` 确实走真实 `RAGService` 并断言 `ainvoke.await_count == 1`，不是假绿。

## HIGH

### HIGH-1：helper 内闭合，但四端点端到端 fail-open 仍未闭合

[decision_tracker.py:138-157](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/core/decision_tracker.py:138>) 本身确认无问题：同时令 `log_decision` 和备用 `logger.exception` 抛错，函数返回 `None`，不传播异常。

但存在以下真实绕过：

1. RAG fallback 的 warning 可把应有的 200/unavailable 升为 500：

   - [rag_service.py:326-333](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/rag_service.py:326>) 和 [rag_service.py:209](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/rag_service.py:209>)。
   - patch `rag_service.logger.warning` 抛错后，被 [rag_service.py:340-342](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/rag_service.py:340>) 包成：
     `RAGServiceError: RAG query execution failed: fallback warning sink failed`。

2. LangGraph 不可用路径仍直接调用原始 `log_decision`：

   - [rag_service.py:274-287](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/rag_service.py:274>)。
   - patch `app.services.rag_service.log_decision` 抛错后传播 `RuntimeError`，预期 503 被遮蔽为 500。

3. RAG 端点自身日志：

   - [rag.py:274-276](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:274>) 的 `logger.info` 在 `try` 前；抛错后服务根本不执行。
   - [rag.py:374-380](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:374>) 的 `logger.error` 可遮蔽原始 503/500。

4. Memory 端点在 `try` 前解析 vault：

   - 调用点 [memory.py:209-214](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/memory.py:209>)、[memory.py:396-401](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/memory.py:396>)。
   - [vault_scope.py:184-198](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/core/vault_scope.py:184>) 的 warning 抛错后，合法请求直接传播 `RuntimeError`。

5. Memory 服务状态生产路径：

   - history：[memory_service.py:665-682](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/memory_service.py:665>)
   - concept：[memory_service.py:843-850](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/memory_service.py:843>)
   - suggestions：[memory_service.py:1080-1089](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/memory_service.py:1080>)

   分别 patch 对应 `debug/warning/error` 后，可得到 500，或把成功 history 污染成 degraded。

这些是 HEAD 已有路径，不是整改新引入；但按本轮明确要求的“整个四端点观测故障不得改变结果”口径，HIGH-1 只能判 **PARTIAL/FAIL**。

建议：另立允许触及 service 层的窄卡，统一使用 no-throw logging adapter，并覆盖上述真实入口；仅修 `log_retrieval_status_decision` 不足以宣称端到端 fail-open。

## MEDIUM

### 1. M7 是语法错误假杀；“7 个变异全被对应门杀死”不成立

[M7:125-133](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py:125>) 把 `try:` 替换为 `if True:`，却保留后面的 `except`。只读 `compile()` 复现：

```text
anchor_count 1
decision_tracker.py:145
    except Exception:
    ^^^^^^
SyntaxError: invalid syntax
```

脚本在 [151-158](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py:151>)、[190-197](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py:190>) 只以 `rc != 0` 判 kill，故把 collection/SyntaxError 算成测试门命中。存档 [04 输出:49-52](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/04-变异门验证-输出.txt:49>) 的 M7 恰好没有任何 FAILED nodeid。

逐项裁定：

- M1、M2、M3、M4：有效。
- M5：部分有效；只打 review-suggestions，且 503 在广义 catch 内最终成 500。
- M6：有效，当前合法回退为 4 failed。
- M7：无效，语法错误。

我另做语法有效的 HIGH-1 回退，四条 fail-open 测试全部变红，说明测试本身能杀核心回退；假的是 M7 证据。

明显缺口：

- 只删除 `logger.exception` 的二级保护，四条测试仍 **4 passed**。
- helper 提前 `return None`、完全不调用落账，四条测试仍 **4 passed**。
- 未覆盖 service/raw `log_decision`、resolver、端点入口日志绕过。

建议：M7 改为合法完整块替换；runner 必须校验收集成功、收集数不变和预期 FAILED nodeid，不能接受任意非零退出码。

### 2. 测试与文档证据跨快照

当前 [验收单:139-177](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:139>) 的 **70/72** 与我当前实跑一致；题面中的 **67/69 已过期**。

但证据仍不一致：

- [04 输出:5-6](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/04-变异门验证-输出.txt:5>) 和 `:66-67` 仍是 67 passed；M6 仍只记录 1 failed。
- [验收单:460-475](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:460>) 把 361 collected 称为“最终代码态”；当前同一选择集 `--collect-only` 是 **372**。
- 验收单写 M4=7、M5=2；存档汇总实际为 M4=8、M5=3。
- 审计期间验收单至少两次被外部改写，本审阅者未写工作树。

建议：停止并发编辑，保存 exact-bytes manifest，再重生成 current-state 裁判、comm 和 mutation 输出。

### 3. 原 MEDIUM-1：核心结论正确，证据 A–E 仍未完全闭合

确认无问题：

- 活跃生产源码独立 `rg` 为 0。
- [ApiClient.ts:1413](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_archive/canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts:1413>) 是 tracked 归档客户端，签名期待裸数组。
- 仓外消费面标 `UNVERIFIABLE` 正确。

未闭合：

- [消费方证据:31-32](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/01-review-suggestions-消费方证据.txt:31>) 的 E 组没有命令，直接进入输出，与“每组带命令”矛盾。
- E 输出引用已不存在的 `01-review-suggestions-零消费方-grep.txt`，不能从当前快照复现。

建议：用 `git grep` 限定 tracked 文件，补出 E 的完整命令和排除规则，从冻结快照重新生成。

### 原 MEDIUM-2：确认无问题

两份 59-nodeid 清单 SHA-256 完全相同。独立重放得到 `59 failed`，分类精确为：

| 根因 | 数量 | nodeid 行 |
|---|---:|---|
| 鉴权 | 46 | 1–21、24–48 |
| mock 签名陈旧 | 7 | 49–55 |
| ImportError | 3 | 56–58 |
| 陈旧 group_id | 1 | 22 |
| mock 抛错逸出 | 1 | 23 |
| coroutine 未 await | 1 | 59 |

复现入口是 [失败清单](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/03-基线失败清单-59条.txt:1>)：

```bash
cd backend
xargs .venv/bin/pytest --tb=short -q \
  -p no:cacheprovider --override-ini=addopts= \
  < ../_bmad-output/审查/evidence-g43/03-基线失败清单-59条.txt
```

小的文案误差：三条 ImportError 中前两条是 `_fuse_rrf_multi_source`，第三条是 `_fuse_weighted_multi_source`；[验收单:489](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:489>) 把三条都写成前者。分类数量不受影响。

## LOW

### 1. 形状哨兵方向反了

[test_rag_four_state_api.py:370-393](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:370>) 强制服务层继续发 `quality_grade=None`。未来服务层合法改进为 `"low"` 时，它会把改进判成回归。

建议删除精确 `is None`，保留 unavailable/reason、端点 200 和 HTTP `quality_grade=="low"`。端点防御不需要靠冻结上游缺陷证明其存在价值。

### 2. 广义 fail-open 会吞程序错误

[decision_tracker.py:138-157](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/core/decision_tracker.py:138>) 捕获所有 `Exception`。循环引用的 `input_summary` 会令 `json.dumps` 抛 `ValueError`，helper 返回 `None`。

正常 logger 可用时会记录 traceback，并非必然“永久静音”；logger 同时失效时才会完全静音。当前四个调用点只传字符串、整数和 `None`，没有现实触发器。另因归一逻辑 [114-126](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/core/decision_tracker.py:114>) 在 `try` 外，helper 也并非结构性绝不抛。

建议把纯数据构造与 sink emission 分离；生产 sink fail-open，同时提供失败计数/健康指标或测试环境 strict 模式。

### 3. 四条 fail-open 测试断言不够强

- [memory test:677-678](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_memory_four_state_api.py:677>) 只断言状态属于二元集合，episodes/concept 状态互换仍绿，且不检查 reason。
- [memory test:689-690](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_memory_four_state_api.py:689>) 不检查 reason。
- 只有 [RAG test:415-418](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:415>) 精确锁住 status/reason。
- 四条均未断言 `log_decision` 确实被调用。

建议参数化精确 expected status/reason，并断言落账 patch 的 `call_count == 1`；另补双重 patch `log_decision + logger.exception`。

### 4. 原 LOW-1：功能闭合，措辞未闭合

两个嵌套模型确实参与了非空解析，确认无问题：

- [memory test:441-469](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_memory_four_state_api.py:441>)
- [RAG test:262-285](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:262>)

但旧措辞仍在：

- memory test `:370/:384/:409`：“字面副本”
- [RAG test:234-239](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:234>)：“字面副本/逐字忠实”
- 验收单 `:77` 仍写“字面副本”

建议统一为“字段契约语义等价副本”。

### 5. 原 LOW-2/3/4 的残余

- **LOW-2 确认无问题**：AST 独立遍历 `backend/app` 与 `backend/lib` 得到 `log_decision` **19 Call / 状态类 2 / 业务类 17**；登记文档 [118-129](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-状态词汇对齐登记.md:118>) 正确，四端点和符号名也正确。
- **LOW-3 实质确认**：列出的三个 `StatusedResult` 族出口都存在；`LearningMemoryClient` 的确是本地 JSON 客户端。但验收单 `:116` 把状态行写成 `222/481/500`，实际是 `226/487/506`；三个 `quality_grade=None` 实际为 `216/481/500`。JSON 读取在 `766-796`，写入是 `817-824` 的原子写入，不是该范围内的直接 `open`。
- **LOW-4 部分闭合**：原地变异风险已如实登记，确认无问题。但 [改动清单:354-371](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:354>) 写 12 项，当前 `git status --short` 是 **13 项**，漏了 0-byte 的 `codex-review-CARD-G4-3-round2.md`。证据目录实际是 **7 个 txt + 1 个脚本**，不是“6 个证据文件 + 脚本”。

## 硬边界与误格式化核验

确认无问题。以下全部满足：

```text
git rev-parse HEAD:<path> == git hash-object <path>
```

误格式化后还原的 5 个测试逐字节等于 HEAD：

- `test_agents_dedup.py`
- `test_agents_encoding.py`
- `test_agents_learning_event.py`
- `test_fsrs_state_api.py`
- `test_metadata_subject_mapping.py`

硬边界 6 文件也逐字节等于 HEAD：

- `backend/app/services/rag_service.py`
- `backend/app/services/memory_service.py`
- `backend/app/api/v1/endpoints/chat.py`
- `backend/app/api/v1/endpoints/agents.py`
- `backend/lib/agentic_rag/nodes.py`
- `backend/openapi.json`

本轮没有新硬边界违规。

再次复核前至少需要：冻结 exact bytes、处理 HIGH 的真实日志绕过、修成合法 M7 并加强 runner、移除反向形状哨兵、重生成 mutation/comm/current-test 证据。当前会话未暴露 `graphiti-canvas` 搜索工具，因此未执行 AGENTS.md 指定的 Graphiti 查询；本裁定不依赖该查询。


