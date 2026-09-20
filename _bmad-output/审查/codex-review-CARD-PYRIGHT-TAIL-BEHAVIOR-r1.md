> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-PYRIGHT-TAIL-BEHAVIOR round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-TAIL-BEHAVIOR.md)"`
> 审查绑定: `2617a930`（本轮送审时的 HEAD；正文首行自述绑定 `2617a930fdc62fc487c0bd5c26423ac992a5af07`）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `4:OpenAI Codex v0.153.3` / `7:model: gpt-6-astra` / `11:reasoning effort: ultra`
> 备注: 本轮之前有一次同 prompt 的调用因 `You've hit your usage limit` 返回 0 字节（rc=1），
> 按协议「0 字节存档不入 commit」已移出仓库、且该次不计入轮次配额；配额随后恢复，本轮为首个有效轮次。

---

复核绑定 `2617a930fdc62fc487c0bd5c26423ac992a5af07`。在限定读取面内，未确认新增的运行期阻断缺陷；发现以下说明及证据口径问题。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM：无。**

**LOW：**

1. [batch_orchestrator.py:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/services/batch_orchestrator.py:147)（`_classify_gather_result`）：关于真实 `KeyboardInterrupt/SystemExit` 会成为 gather 结果项的解释不成立；此外，外层 `GroupExecutionResult` 没有注释声称的 `error_type` 字段。  
   **对照输入**：子协程真正 `raise KeyboardInterrupt()`；本机 Python 3.14.4 实测 gather 未返回结果列表，`asyncio.run()` 边界抛出原异常。

2. [wikilink_graph_service.py:316](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/services/wikilink_graph_service.py:316)（`_resolve_path`）：新增“所有图节点与索引恒同域、无歧义”的说明过强，重名测试没有验证正文链接目标。  
   **门未覆盖的路径**：同时存在 `sub/note.md`、`sub2/note.md`，另一个文件链接 `[[note]]`；图会额外出现索引中没有的 `note`，最终仍回落 `note.md`。这是既有匹配边界，本卡新增问题是说明失实，不要求处理归一化。

3. [multimodal_service.py:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/services/multimodal_service.py:114)：注释“全仓再无引用”不准确，文档仍保留两个常量的引用。  
   **对照输入**：全仓检索常量名，命中 `.gdr/prd-backend-pack.md:29616–29617` 和 `docs/stories/36.13.story.md:46`；未检出可执行代码对这两个常量的引用。

4. [test_pyright_tail_behavior.py:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_pyright_tail_behavior.py:14)：测试文件自身不足以保证“零网络”，服务导入存在依赖自动联网行为。  
   **对照输入**：新进程导入 `IntelligentParallelService`，本次实际触发 LiteLLM 获取远端价格表；请求因沙箱 DNS 限制失败后回落本地。这是联网尝试，不能记为“零网络”。

对应问题的结论：

0. **真实 KeyboardInterrupt 输入：既不是新增静默，也不是注释所称的收紧。** 改前、改后都到不了两个结果处理循环。对于真正进入结果列表的普通／自定义 `BaseException`，本卡确实改成继续处理：内层生成失败节点并广播组完成，外层生成失败组。建议明确只接收 `CancelledError + Exception`，其余重新抛出；若采用此策略，**两个调用点都必须处理**，否则内层重抛后仍可能被外层 gather 收集并转换。

1. **完全未配置模型不会触发所述初始化失败。** `SystemModelConfig` 三个字段均默认 `None`；新进程、真单例的独立检查返回既有 fallback。`:575` 确实位于后面的 `try` 外，其他来源的 `ValueError/TypeError` 可以外溢，但当前空配置不是触发条件。

2. **空串、`None`、大小写不同的 `"FOUR-LEVEL"` 都被拦下**，返回 `failed/unknown agent_type`；合法 `"four-level"` 加未注入依赖仍抛 `RuntimeError`。无效参数确实会遮住同时存在的依赖缺失或节点读取错误，这是新增的校验优先级。**404/422 是否改变未确认**：端点处理代码未列入允许读取面，服务返回值不能直接证明 HTTP 状态。

3. **文件索引命名规则成立，所有图节点同域不成立。** 已安装依赖实现及内存实验确认：非 ASCII 精确同名可以匹配；URL 编码链接不会自动解码；`.txt/.pdf` 等链接目标可以进入图，却不在 Markdown 索引中。未知键或外部直接传入的键也没有同域保证。这些输入继续走既有兜底。

4. **时间戳没有因 LLM 调用而新增延迟。** 改前、改后均在 LLM 返回之后取时间；改前真正保存的是模型初始化期间的 `default_factory` 时间，改后保存 helper 调用前的显式时间，正常顺序下反而略早。差异仅在本地构造步骤之间，没有 LLM 耗时级偏移；本次未验证下游排序。

5. **两种 AST 负控都会通过，已在内存中验证。** 非 `def` 语句被忽略；新增未挂载模块函数不参与声明集合比较——扩展模块本来就允许 helper。当前两道静态门 **11/11 通过**，但不证明运行期挂载：删除自动挂载调用、改变赋值右侧，门仍可能通过。当前源码未发现这些错误，不能把证明边界当成已经挂错。

6. **没有新增生产侧 ignore 掩盖。** 九文件实际为 **11 → 3**，不是 4；顺序确为 `1/0/0/0/1/0/0/1/0`。本卡删除了八处，其中 batch 文件三处；唯一新增有效 `type: ignore` 是测试 `:194` 的旧参数负控。本次未重跑 `pyright app`，不独立背书“0 errors、80 warnings”。

7. **删除的三个名称在 multimodal_service 本文件中均无剩余引用**，也未检出从该模块导入它们的具名或星号 import；全仓文档引用见 LOW-3。`search()` 的文本降级及日志子串保留，未重跑既有两条测试。

六文件格式 commit 的 AST 等价已独立确认；`learning_context_service.py`、`exam_service.py`、`exam_service_ext.py` 与 PREV 字节一致。未修改仓库，未连接数据库；一次导入触发的联网尝试已阻断。完整 15 条测试及作者历史负控哈希未复跑；当前另有四项未跟踪审查材料，不能把历史“status 为 0”当作当前状态。
