> 批次: BATCH-2026-09-11-第十四批 · 车道 T10（card-t10-red） · 卡 CARD-Y4-D-TAIL round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-Y4-D-TAIL.md)"`
> 审查绑定: `c1fab4cd`（当轮 HEAD；本卡最终 HEAD 为 `b6858446`，本轮不绑合并态）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

仅做静态审查；未运行测试、hook 或数据库，因此不确认作者自述的 PASS 和负控实测结果。

**BLOCKER: 无**

**HIGH: 无**

**MEDIUM**

- [test_graphiti_json_dual_write.py:374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_graphiti_json_dual_write.py:374)：三条 logging 用例均没有逐断言等价覆盖——success 的 `debug` 调用及 `episode_id` 关联、failure 的 `warning/failed` 未被替代，timeout 更额外失去了慢下游输入，因为 scenario 2/3 都立即抛出 `RuntimeError`；作者承认观测面不同是诚实的，但“等价／更强”及第 181 行的非阻塞覆盖归属仍不成立。  
  **触发条件：** 日志及事件标识关联消失，或调用方改为等待 worker 完成、真实下游迟迟不返回时，所引用的立即成功／立即失败测试仍可能全部通过。

**LOW**

- [test_story_38_6_scoring_reliability.py:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_38_6_scoring_reliability.py:212)：处置数量自述不准确，实际是 **4 条入队重写＋3 条 recovery 重写＋3 条 logging 删除＋1 条 dataclass 删除**，不是“4＋4＋3”；该处 docstring 所称旧测试曾挂载私有助手也不准确，旧版只有 partial 用例这样做。  
  **触发条件：** 按作者分类核销 11 条红例时，会错计 recovery 数量并漏列 dataclass 删除；源码中实际有 **7 条**新增依赖 `ready_worker` 的用例，“6 条负控”是否覆盖完整也无法据此确认。

其余核对结果：

- **用例去向完整。** 两文件分别为 **11→7、18→18** 条，没有额外删除、改名或隐蔽改成恒真断言；4 条恢复目标的执行体未变。恢复类外的 14 条用例也未改，其中包含原有 3 个 xfail。
- **废弃引用处理正确。** 引用行数确为 **13→0、4→1**；剩余一处仅在 xfail reason 中，不构成运行依赖。三个标记内容未变，行号确为 **38／51／79**，保留禁改文本合理。
- **保留旧三条用例可作为历史恢复记录，但不能算功能覆盖恢复。** docstring 披露必要，却不能使断言重新有效；应补充当前管线的有效测试。两个计时断言并非数学上的恒真，但没有施加真实下游延迟；旧客户端的 `assert_not_called()` 则与 flag 无关。
- **新断言并非整体恒真。** `group_id` 检查只能保证非空字符串，错误的非空分组仍会通过；spy 在真正入队前记录，因此数量断言证明“尝试入队”，不能单独证明接纳。相较之下，真实 `enqueue` 在成功入队后同步增加计数，`episodes_enqueued == 1` 是有效断言。
- **fixture 没有整体替换被测层。** readiness 检查和 `EpisodeTask` 创建仍走生产代码；partial 用例明确额外替换了真实存在的 `enqueue`，不存在幽灵属性，函数签名也正确。赋值会持续到 teardown，但 fixture 为函数作用域；`stop` 不在允许读取的方法内，故不能确认其内部依赖，也没有依据报告确定的 teardown 故障。
- **dataclass 删除的“非等价覆盖损失”定性准确。** 原测试实际验证旧客户端收到的字段映射，没有验证 dataclass 类型；新断言没有完整接替 canvas、agent feedback、timestamp 等检查。其他调用方和全仓覆盖状况超出读取范围，未确认。

B=0 H=0 M=1 L=1
