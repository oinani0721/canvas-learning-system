> 批次: BATCH-2026-09-11-第十四批 · 车道 T10（card-t10-red） · 卡 CARD-Y4-D-TAIL round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-Y4-D-TAIL-r2.md)"`
> 审查绑定: `f6f00bb5`（当轮 HEAD；本卡最终 HEAD 为 `b6858446`，本轮不绑合并态）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

只读静态复核完成，未运行测试、hook 或连接数据库。**新增 `episodes_enqueued == 1` 确实增强了断言**；本轮剩余问题均为 LOW。

**BLOCKER: 无**

**HIGH: 无**

**MEDIUM: 无**

**LOW:**

1. [test_graphiti_json_dual_write.py:400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_graphiti_json_dual_write.py:400)：temporal 用例声称任务到达队列，但 `:427` 只检查了委派前记录的任务，没有固定“队列接纳”的保证。  
   **触发条件：**worker 仍 ready、实际 `enqueue` 返回 False 时，任务数量和字段断言仍全部通过；这属于证明范围不足，并非恒真断言。

2. [test_graphiti_json_dual_write.py:378](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_graphiti_json_dual_write.py:378)：删除说明仍写“等价覆盖逐条归属如下”，与 `:388` 更正后的“邻近场景，非等价覆盖”直接矛盾。  
   **触发条件：**依据前一句判断日志覆盖已被接替时，scenario 1–4 即使没有相关日志也能通过。

3. [test_graphiti_json_dual_write.py:260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_graphiti_json_dual_write.py:260)：仍称用例“证明调用方不被下游拖住”，文件头 `:38/:40` 也保留对应覆盖声明，与新增的“未施加真实下游延迟”说明不一致。  
   **触发条件：**现行下游发生阻塞，而测试延迟仍挂在无人调用的旧客户端上时，这些断言不能验证慢下游隔离。

4. [test_story_38_6_scoring_reliability.py:201](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_38_6_scoring_reliability.py:201)：作者“4 条双写重写＋4 条 recovery 重写＋3 条删除”的分拆不准确，实际为 **4＋3 条重写、4 条删除**。  
   **触发条件：**按 nodeid 核对处置清单时，`test_recover_no_file` 完全原样，dataclass 用例则是已明确披露的第 4 条删除。

其余重点核对结果：

- **⓪ 删除覆盖：**三条 logging 均无等价覆盖。success 缺 debug 调用及 episode_id 日志关联；failure 缺 warning 调用及 `"failed"` 文案；timeout 缺慢下游输入、warning 调用及 `"timeout"` 文案。r2 对主要缺口的披露属实，只是 timeout 日志断言没有逐项展开。dataclass 用例删除属于字段构造覆盖损失，新断言没有完整接替，作者的“非等价覆盖”定性合理。
- **① 符号与 xfail：**新代码未复活已删私有助手；`flaky_enqueue` 替换的是现存方法。旧符号按匹配行数确为 **13→0、4→1**，唯一残留在 xfail reason 中；三个标记内容未改，保留该文本符合给定禁改边界。
- **② 用例完整性：**双写文件 **11→7**，scoring 文件 **18→18**；没有未披露的删除、改名或新增 skip。四条恢复目标执行体均未改。`ready_worker` 依赖确为 **7 条**；PASS、既有红和补跑负控的实测结果，本轮未验证。
- **③ 断言强度：**真实 `enqueue` 在 `put_nowait()` 成功后才增加计数，故新指标断言能排除“spy 记录了尝试，但队列拒绝”的情况；它不证明后台处理完成。`group_id` 仅检查非空字符串，新增注释准确承认了限制。三条历史弱覆盖用例保留原体并披露限制，在本卡恢复原样的范围内可以接受，但不能算对应业务语义已获验证。
- **④ fixture：**真实 worker、`is_ready` 和 `EpisodeTask` 创建路径均保留。partial 用例明确替换最终入队结果，其 True 分支没有实际入队；替换限于本用例实例。**`stop()` 实现不在限定读取面内，因此不能确认 teardown 内部是否受影响。**

“全仓无相关用例”和其他生产文件中的活跃消费者声明超出读取面，未独立确认。

B=0 H=0 M=0 L=4
