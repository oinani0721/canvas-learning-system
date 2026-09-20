> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-PYRIGHT-TAIL-BEHAVIOR round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-TAIL-BEHAVIOR.md)"`
> 审查绑定: `3596e98b`（送审时 HEAD；正文首行自述绑定 `3596e98b0042c34acdf03ea90be2e8886d6f57f3`）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `4:OpenAI Codex v0.153.3` / `7:model: gpt-6-astra` / `11:reasoning effort: ultra`
> 结论: **BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 2** ⇒ 按协议 §1 合并门 + D-15，该轮通过。
> 本轮后仅有一个**纯 docstring** commit `5e8a76fd`（按 D-32 做「剥 docstring 后 AST 逐字相同」
> 自证，真代码零改动，不计入 D-15 轮次、不触发再审；证据
> `evidence-pyright-tail-behavior/d32-docstring-equivalence-*.txt`）。

---

复核绑定 **`3596e98b0042c34acdf03ea90be2e8886d6f57f3`**。在已核范围内：**BLOCKER 无；HIGH 无；MEDIUM 无；LOW 2 条。**

**LOW**

1. **[test_pyright_tail_behavior.py:242](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_pyright_tail_behavior.py:242)**，`test_resolved_path_is_actually_readable_by_neighbor_loader`：新增说明仍把旧行为概括为“任何”嵌套笔记目录信息丢失、正文“恒空”；同文件 `:203` 的“两者同域”和 [wikilink_graph_service.py:334](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/services/wikilink_graph_service.py:334) 的“嵌套目录信息全部丢失”也未同步收窄。  
   **对照输入：** 同时存在 `sub/note.md`、`sub2/note.md`，节点键为 `sub/note` 时，旧兜底 `f"{note_key}.md"` 已得到正确路径；这也与测试文件 `:205–208` 自己的说明一致。

2. **[batch_orchestrator.py:148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/services/batch_orchestrator.py:148)**，`_classify_gather_result`：新增可达性说明写错了方法名，实际超时入口是 `start_batch_session`，不是 `execute_batch`；“本仓唯一的取消源”也超出了本次证据范围。  
   **对照输入：** 沿实际 `start_batch_session:370` 的 `asyncio.wait_for` 检查调用链，找不到注释所指的 `execute_batch`。

其余问题的核对结果如下。

- **⓪ BaseException：没有证实新增吞掉 KeyboardInterrupt／SystemExit。** Python 3.14.4 的真实 gather 实验中，子任务抛出这两者会在到达结果循环前传播，最终从 `asyncio.run()` 抛出，因此也不能说改前会把它们 append 成业务结果。自定义 `BaseException` 则确实可进入结果列表：现状在节点层转换为失败节点、在组层转换为失败组；若两层都显式重抛，会最终越过会话层的 `except Exception`，无法正常完成失败聚合。这是错误处理策略差异，当前没有必须改为重抛的生产证据。

- **① 空模型配置：未发现窄 except 导致的现存失败路径。** 独立执行当前配置类源码，首次构造得到三个 `None` 字段，`get_scoring_model()` 返回 `None`，解析器回落到 `gemini/gemini-2.0-flash`。没有新增必填字段或校验器时，不能据此推导出 `ValidationError`。无参门确实覆盖了此前漏掉的延迟 import／取单例分支，但没有覆盖实际 LLM 请求及凭据传递。

- **② 参数验证顺序确实改变了错误优先级。** `""`、`None`、`"FOUR-LEVEL"` 都会让真实 `AgentType` 抛 `ValueError`，从而早返回 `failed`；它们不是漏过验证的输入。与依赖缺失同时存在时，原来的 `RuntimeError` 会被这条参数失败响应遮住；合法值仍检查依赖。**HTTP 404／422 的最终映射未核实**：指定最小面没有端点及请求模型正文，不能仅凭服务代码宣称 HTTP 语义未变。

- **③ 索引键规则成立，但集合不保证相等，也不保证严格包含。** 无重名用裸名，重名用去扩展名的相对路径；图还可能包含未解析链接目标。无额外目标时两集合可以相等。普通中文文件名可匹配；`[[with%20space]]` 对 `with space.md`、非 Markdown 目标 `[[data.txt]]` 会落入旧兜底。`_resolve_path` 本身也不校验输入一定来自图。这里仅确认边界，不评价键归一化方案。

- **④ 时间戳没有增加一段 LLM 等待时间。** 改前、改后都在 LLM 完成后构造实体；区别是旧参数被忽略后由模型生成时间，新代码保留调用方时间。只有构造顺序带来的微小时间差，没有固定的“晚多少”。未发现由此造成 Graphiti／复习排序回归的证据，也未扩大读取下游实现。

**新增门有判别力，但不能把通过范围扩大为完整运行期证明：**

| 门 | 能抓住 | 仍未覆盖 |
|---|---|---|
| gather AST 门 | `BaseException → Exception` | **负控输入：** 内存中交换两个分支体，原门仍通过；它不验证分支动作或真正所属循环。 |
| attach RHS 门 | `generate_hint = skip_question` | **负控输入：** 删除顶层挂载调用、删除副作用 import，或在赋值前加 `return`，四条 exam 门仍通过。 |
| TYPE_CHECKING 非 def 门 | 添加变量注解等非方法语句 | 新增未挂载模块级 helper 仍通过；这本身合理，ext 原来就有未挂载 helper。 |
| resolver → 下游读取门 | 嵌套路径可交给真实读取器 | **门未覆盖的路径：** `get_neighbors → NeighborNote.path`；用例直接调用 resolver，绕过了这段生产接线。 |
| 无参模型解析门 | 生产形态的配置 import／单例读取 | `_llm_classify_intent` 是否使用解析结果、凭据是否传递。 |

当前 exam 的副作用 import、顶层挂载调用和 11 条正确赋值都存在；上述负控证明的是**测试边界**，不是当前挂载故障。

其余 round-2 项：

- `manager._config = object()` 是对真实管理器做**非法状态注入**，没有 mock 被测方法。同步执行且 `finally` 恢复原配置，普通串行 pytest 未见持续污染路径；它不提供同进程并发线程隔离。
- retry warning 的“路径由参数推导、不保证存在”与分支一致，structlog 关键字字段合法，未发现新增失败面。但相邻注释的“没有任何写方／hasattr 恒 False／改前成功恒不可达”不能仅凭允许读取的枚举与签名完全证明；本轮不背书这些更强主张。
- `_generate_embedding` 与健康判断确实解耦；`search()`、`get_health_status()` 的 PREV／HEAD AST 均一致，“健康显示可用但搜索降级”的矛盾属于既有行为。
- **没有新增生产类型抑制。** 九文件保留 `pyright: ignore` 合计 **3**；新增有效 `type: ignore` 只有测试 `:367` 的故意旧参数用例。
- **“全仓再无引用”不成立。** 两个退役常量仍有历史文档提及；未找到可执行消费者。`multimodal_service` 内三个退役名称均无执行引用。修订后的“可执行引用与历史文档分开”口径基本准确；不能理解为全仓已无 `asyncio` 使用。

独立确认：六个纯格式文件 AST 全等、测试数量 **15 → 24**、三个声明零改动的文件确实零 diff。本轮没有修改文件或连接服务；未运行会写临时文件、可能触发联网导入的完整 pytest，也未复跑 pyright，因此不将作者的“24 passed／0 errors、80 warnings／五段负控还原”当成本轮实测。当前工作区有 **5 项未跟踪 `_bmad-output` 材料**，不等于当前 status 为零，也不反证作者当时的记录。
