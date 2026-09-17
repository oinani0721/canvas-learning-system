> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE-r2.md)"`
> 审查绑定: `d9fa07742177b506312bea2874591ed31b38946b`（该轮 HEAD；本轮报 HIGH 1，按 D-15 整改为 `d90f5a67` 后另送 round-3）
> 会话头自证（抄 .stderr 第 2 / 5 / 9 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**本轮不能签署通过：发现新增 HIGH，round-1 ②也仅部分修复。** 审查绑定 `d9fa07742177b506312bea2874591ed31b38946b`；未改文件、未连接数据库、未运行会触发连接的测试。以下区分实际内存复现与静态结论。

1. **HIGH — 测试的现网端口保护可绕过。**  
   [test_neo4j_replay_wire_t6b.py:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:62)、`:74`、`:277`。两处保护只检查字符串 `":7691"`。**未被拦下的输入**：`NEO4J_TEST_URI=bolt://127.0.0.1:07691`。已用工作树实际安装的 Neo4j **6.1.0** 解析器确认：检查放行，但驱动解析后的端口是 **7691**。测试收集阶段随后调用 `verify_connectivity()`；凭证有效时还会执行夹具清理。  
   **复现思路：**仅调用 URI／地址解析器，对比字符串检查与解析端口即可，无须连接数据库。

2. **MEDIUM — 空异常文本仍被启动摘要误判为成功。**  
   [main.py:428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:428)；生产方为 `fallback_sync_service.py:83、90、100`。`v.get("error")` 会漏掉 `""` 和 `None`。三个生产分支正常不会生成 `None`，但捕获集中的 `RuntimeError()`、`OSError()`、`ConnectionError()`、`TimeoutError()` 均实测得到 `str(e)==""`。  
   **复现思路：**负控输入令子同步抛无参数 `TimeoutError()`，所得 `error=""` 使 `_failed=[]`，继续输出 `:435` 的成功摘要；对照输入 `RuntimeError("failure")` 则正确进入错误摘要。应识别 `error` 字段是否存在。

3. **MEDIUM — round-1 ⓪仍是未关闭的验收缺口。**  
   [test_neo4j_replay_wire_t6b.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:186)、`:197`、`:224`。客户端预先初始化、生产单例被替换、lifespan 不执行，启动接线与真实工厂装配仍是**门未覆盖的路径**。  
   **复现思路：**负控输入摘掉 `main.py:416` 的启动调用，当前测试仍不会检查到。禁止触碰现网和 live vault，足以支持“不直接运行现有 lifespan”；登记限制不能证明这些路径通过。另，`:392` 回填抛异常会直接跳过回灌，此路径也仍在。

4. **MEDIUM — 清理查询会删除其他测试的数据。**  
   [test_neo4j_replay_wire_t6b.py:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:112)、`:200`、`:205`。兜底查询删除所有无邻居的 `scoring` Episode，没有门前缀或本次运行身份约束；即使连接正确的共享测试库，也会发生越界清理。  
   **复现思路：**对照输入为其他测试留下的无边 `(:Episode {type:"scoring", id:"othergate"})`，该查询同样匹配并删除它。这是源码结论，本轮未执行删除。

5. **LOW — 非 UTF-8 已修复，但 JSON 计数仍有异常遗漏。**  
   [fallback_sync_service.py:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:175)、`:176`。**负控输入** `'[' + '1'*5000 + ']'` 在工作树 Python **3.14.4** 默认整数位数限制下抛普通 `ValueError`，不属于当前捕获集，最终被 `main.py:458` 误记成回填失败；对照输入 `[1]` 正常。已实际复现。[Python 整数转换限制](https://docs.python.org/3.13/library/stdtypes.html#integer-string-conversion-length-limitation)

   捕获边界还需区分版本：深嵌套 JSON 在实测 Python 3.11 会抛 `RecursionError`，同一输入在本机 3.14 通过；`Path.exists()` 又位于两个 `try` 外，3.13 可传播权限类 `OSError`，3.14 则改为抑制这些错误并返回 `False`。[Python 路径查询变更](https://docs.python.org/3.14/library/pathlib.html#querying-file-type-and-status)  
   `MemoryError` 理论上也可能发生，但不另列为要求吞掉的缺陷。

6. **LOW — 端点公开描述仍与本卡声明的 learning 链口径冲突。**  
   [traces.py:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:89) 宣称条目回灌后移除、第二次 `recovered=0`；`fallback_sync_service.py:120` 却明确声明 `learning_memories` 不轮转。此处计的是已确认的文档冲突。  
   **复现思路：**对照输入只保留一条有效 learning 记录，连续调用两次核对该链计数；若⑤(b)所述全量重放成立，就不能承诺第二次归零。这与刻意暂不再生 `backend/openapi.json` 无关。

其余问题的结论如下：

- **整改①解决了原问题，不因“未来结构变化会红”而判缺陷。**  
  [test_neo4j_replay_wire_t6b.py:363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:363) 确实挡住首轮 `Episode=2`、第二轮仍为 `2` 的负控输入。它同时锁定当前评分输入的图结构；有意改变结构时，应同步审查期望值。  
  但 `:237、245` 只计前缀节点及经 `SCORED` 连到前缀 Node 的 Episode。游离 Episode、连错 Node 的 Episode、无前缀节点及其他重复关系都是**门未覆盖的路径**；此外 `labels(n)[0]` 只取一个标签，`count(e)` 没有去重。计数相同只能证明这个查询范围内相同，不能证明全图没有重复。

- **整改③可以接受；整改④的原非法 UTF-8 问题已解决。**  
  [traces.py:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:124) 已如实披露异常文本，`:96` 确实接入原鉴权依赖。有效内部权限请求遇到含路径的异常仍会收到路径，但当前没有证明未鉴权请求能取得这些内容，也没有接受任意文件路径的端点参数。按“原样返回 stats”的要求，不必仅因该行为重新判缺陷。两个计数 helper 对非法 UTF-8 的负控均已确认 warning 后返回零。

- **`pending_total` 的排除理由成立，但只能解释为两条队列的计数。**  
  [fallback_sync_service.py:146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:146) 与 `main.py:451–455` 已明确单列 learning 记录。长期保留的记录总数不能直接当作未同步数；同样，排除它也不能证明 learning 链没有未同步记录。因此不另计“漏加”缺陷。

- **⑤只能核逻辑，尚未独立核实实现。** 追加读取未获确认，相关消费者及重放实现仍在允许片段之外。  
  **(a)** 若条目确实缺少消费者要求的字段、失败后原样留存且没有其他消费者，则“当前接线下持续 pending”成立；“零调用方”本轮未独立证明。  
  **(b)** 不调用 `record_score_history` 排除了那条 `CREATE Episode` 路径；但仅有 `MERGE + SET` 尚不足以证明幂等，还需确认 MERGE 身份键稳定、SET 不改变身份及没有其他创建路径。即使节点数量不增长，也不能直接推成属性状态完全不变。

**计数汇总：BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 2。** MEDIUM 包含保留的 round-1 ⓪验收缺口；⑤未核实的行为不计入。


