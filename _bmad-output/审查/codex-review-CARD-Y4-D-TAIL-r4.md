> 批次: BATCH-2026-09-11-第十四批 · 车道 T10（card-t10-red） · 卡 CARD-Y4-D-TAIL round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-Y4-D-TAIL-r4.md)"`
> 审查绑定: `9b631648`（当轮 HEAD；本卡最终 HEAD 为 `b6858446`，本轮不绑合并态）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

仍有 **4 组 LOW 级覆盖声明不一致**，不能认定已全部清零。本轮仅作静态审查，未运行测试、负控、hook 或数据库操作。

BLOCKER: 无

HIGH: 无

MEDIUM: 无

LOW:

1. **文件头仍把无条件记录列为已验证。**  
   位置：[test_graphiti_json_dual_write.py:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_graphiti_json_dual_write.py:39)。r4 的函数 docstring 已准确限定为 True 侧，但文件头仍写 `records unconditionally [verified]`；False 侧仅验证返回 ID、旧客户端未调用。  
   **触发条件：**False 时跳过实际记录／入队、仍返回 ID，两条 flag 用例依然通过。

2. **fixture 说明仍混淆“使用真实实现”与“覆盖真实拒绝分支”。**  
   位置：[test_graphiti_json_dual_write.py:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_graphiti_json_dual_write.py:106)、[test_story_38_6_scoring_reliability.py:189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_38_6_scoring_reliability.py:189)。stub 不会阻止 `_enqueue_episode` 和 `EpisodeTask` 执行，这一更正正确；但将队列满／关闭分支列为 stub 会“拿掉”的覆盖仍过强：当前用例没有触发真实拒绝分支，失败场景直接替换了 `enqueue`。  
   **触发条件：**真实 `enqueue` 的 QueueFull／关闭处理发生回归，这些用例仍可通过。

3. **recovery 的文件保留声明超过内容断言能力，属于存量缺口。**  
   位置：[test_story_38_6_scoring_reliability.py:296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_38_6_scoring_reliability.py:296)、[同文件:302](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_38_6_scoring_reliability.py:302)。partial 只检查剩余一行，未确认留下的是失败条目；malformed 只检查返回计数，完全未检查坏行仍在文件中。  
   **触发条件：**误留成功条目、丢弃失败条目，或返回 `1/1` 却丢掉坏 JSON 行，对应用例仍通过。

4. **两个未标 xfail 的预算测试仍声称验证生产重试预算，实际比较本地旧常量，属于存量问题。**  
   位置：[test_story_38_6_scoring_reliability.py:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_38_6_scoring_reliability.py:68)、[同文件:463](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_38_6_scoring_reliability.py:463)。实际门槛分别为 **1.8 秒、4.5 秒**，不是注释中的 **13 秒、9 秒**，也没有绑定现行 worker 预算。  
   **触发条件：**外层 timeout 改为 10 秒，相关普通测试仍通过，但不满足声明中的至少 13 秒。

其余核对结论：

- **⓪ 删除覆盖：**三条 logging 均无等价覆盖。scenario 1 不检查 debug 与 episode_id；scenario 2/3 使用立即抛错，未覆盖慢下游及 warning 中的 `timeout`；scenario 3/4 不检查 warning 中的 `failed`。现有删除说明已承认“非等价”和日志／慢下游缺口，定性诚实。dataclass 的字段构造断言也未被完整接替，称为真实覆盖损失准确。
- **① 私有符号：**按命中行计数，确为 **13→0、4→1**。剩余一行仅为 xfail reason，无执行依赖；遵守禁改边界保留正确。新代码没有伪造已删 retry 属性。
- **② 用例账目：**确认 **7 条重写＋4 条删除**；现存为 **7＋18＝25 条**，没有额外删除或改名。四条恢复目标的可执行主体逐字相同，三个 xfail 标记源码完全相同。未运行测试，不能独立确认 PASS、11 条红或负控结果。
- **③ 恒真风险：**保留三条旧断言并明确披露失效范围，在本卡恢复原样的范围内可以接受，但不能计为相应语义覆盖。`group_id` 检查弱而非恒真；真实 `episodes_enqueued == 1` 在 `put_nowait` 成功后才成立，能区分尝试与接纳。
- **④ fixture：**基础 fixture 使用真 worker；partial 用例替换的是现存 `enqueue`，只证明两次尝试及模拟的 True／False 分流。实例为函数级，未见跨用例污染；`stop` 不在指定方法读取面内，因此未独立确认其内部是否依赖被替换的 `enqueue`。

B=0 H=0 M=0 L=4
