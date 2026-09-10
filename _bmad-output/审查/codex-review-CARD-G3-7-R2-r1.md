> 批次: BATCH-2026-09-07-第十三批 · 车道 U9 · 卡 CARD-G3-7-R2 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-7-R2-r1.md)"`
> 审查绑定: `c480de1da6e42ec2a15c8352f1a1f800b7ea6651`（Codex 自行 `git rev-parse HEAD` 核对，见其正文首句）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `Reading additional input from stdin...` / `OpenAI Codex v0.153.3` / `--------`

---
复核对象：`HEAD c480de1da6e42ec2a15c8352f1a1f800b7ea6651`。全程只读，未运行测试、脚本或连接数据库。**发现 1 项 HIGH、3 项 MEDIUM、1 项 LOW；没有已核实的 BLOCKER。**

### HIGH

**1. census 的取数面不足以证明定义下的精确总数 `N=1`。**

[census:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:20) 纳入经公开 API 间接消费状态的文件，但其 `:44–46` 列出的全局检索串只有 `fsrs_card_states`、`_card_states`、`fsrs-state`。普通静态调用 `await svc.get_fsrs_state(id)`、`await svc.record_review_result(...)` 可以满足定义，却不含这些串；`review/record` 也只在 `:160` 对指定目录补扫。

因此，`:187` 的数字只能作为**所列证据发现并归类的消费方数量**，尚不能作为完整总数。§七没有披露这种普通静态调用漏面。**本次没有发现实际第二个消费方，不等于已证明实际 N 错误。**

排除所有权模块、纳入间接调用这两条规则，本身不会强制 N 恒为零或非零。但 `:32/:36` 的“去掉间接调用规则 ⇒ N 恒等于零”论证不成立：定义仍允许其他文件直接读 JSON，以及 HTTP 客户端。

### MEDIUM

**2. 写边界门会误拦正常读取，也会漏掉真实写入。**

[test_mastery_fsrs_projection_boundary.py:110](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:110) 固定把第二个位置参数当作 mode，`:168` 却将所有名为 `open` 的调用交给它：

| 调用形式 | 实际行为 | 检查结果 |
|---|---|---|
| `Path(p).open("w").close()` | 创建或截断文件 | **漏报**：只有一个参数，被当成默认只读 |
| `Path(p).open("r", -1)` | 只读；第二参数是 buffering | **误报**：非字符串参数被当成写 |
| `mode = "r"; open(p, mode)` | 正常只读 | **误报**：mode 不是字面量 |
| `Path(p).read_text().replace("\r\n", "\n")` | 读取并处理内存字符串 | **误报**：`:63/:172` 禁止任何名为 `replace` 的调用 |

此外，`:159–173` 只检查直接调用名，漏掉 `await asyncio.to_thread(Path(p).write_text, data)` 这种回调写法；真实持久化通道本身就在 [review_service.py:605](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:605) 使用同类形式。

若漏报的写入目标是节点 `.md`，文件名字面量门和只观察 review 投影路径的行为门也不能兜底。两个人工名单不相交，证明不了“所有合法读均放行”或“所有真实写均命中”。

**3. “幻影调用复活必红”仍是过强表述；这是保留下来的测试弱点。**

[test_review_service_fsrs.py:614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_review_service_fsrs.py:614) 用抛出 `AssertionError` 的函数替换 client getter，`:619–621` 只检查业务返回值。

若恢复的幻影调用被自己的 `except Exception` 吞掉，测试仍可能得到预期返回值。测试没有在调用结束后独立断言 getter 的调用次数为零。因此，“仍存在路径上的执行覆盖未变窄”可以成立，**“任何形式的幻影调用复活都必红”不成立**。这不是本卡改指方法所新增的覆盖退步。

**4. 文档把限定范围的检索写成了“全仓 0”。**

[docs/fsrs-truth-source-d0-revision.md:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/docs/fsrs-truth-source-d0-revision.md:68) 写 `_legacy_card_states` / `is_uuid_v4`“全仓 0”，但 [主 spec:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/openspec/specs/concept-identity/spec.md:8)、`:10` 就包含这些标识符。

census `:200–201` 所列范围实际是 `backend/app`，历史检索进一步限于 `review_service.py`。这里应保留原来的范围限定；本次材料也不足以独立确认“整个历史从未实现”。

### LOW

**5. 新说明仍有过期判据和错误行号。**

- [边界测试:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:8) 仍描述“engine 恰好 1 条、store 0”的计数门，实际 `:260–293` 已改为可执行引用检查，并要求两模块保留说明文字。
- [mastery_engine.py:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/mastery_engine.py:297) 新列的读方行号仍不准确：`:342/:349/:352` 落在说明文字，`:667/:669` 是分隔注释；当前实际读取在 `:353/:360/:363` 和 `:678/:680`。

### 未核实

- **删除方法是否打断动态调用链：未核实。** 若存在 `getattr(svc, "save_card_state")` 派发且没有兼容入口，删除可能断链。指定材料没有证明此类调用不存在；[census:214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:214) 也明确承认这一边界。不能据此反推已经发生线上故障。
- **N1/N2 是否真正命中点名断言：未核实。** 两份 `negctl-N1N2-*.txt` 实际都是摘要，缺少注入源码、匹配实现和 pytest 的 `^E` 原始正文。最新日志 [103941.txt:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/negctl-N1N2-20260908T103941.txt:8)、`:16/:18` 只是宣告 KILLED。N1 函数内确实只有 `:192` 一道断言；N2 行为门最终断言 `:378` 前另有 `:351/:352/:361/:371` 的前提断言。同 nodeid 不足以定位失败层，缺少正文也不能证明实际发生了误杀或非法语法输入。
- **行为门无条件“跑到底”的证明：未完全核实。** 测试 `:371` 检查结果非 None，但没有先断言初值为 None；`ConceptState` 默认值不在许可读取面内。CI 是否禁止该门被 skip，也未核实。
- **OpenSpec 工具拒绝与正式移交是否完成：未核实。** 指定文件能确认 spec 尚未修改，不能确认移交闭环。

### 已核实成立的部分

1. **两条改指测试保留了现存路径的对应覆盖与失败返回语义。** 基线包装只是传入同一 `pending`、记录日志并返回 `_save_card_states` 的结果。新版 [测试:619](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_review_service_fsrs.py:619) 仍执行被包装者，`:620–621` 保留读取命中／未命中断言；`:635–637` 使用同一失败路径并断言 `False`。没有发现仍存在的原路径因改指而失去覆盖。

2. **patch 正控能阻止“落点完全未生效却继续通过”。** [行为门:349](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:349) 经真实 `_save_card_states` 写入，再检查目标出现；生产写通道确实动态读取 `_CARD_STATES_FILE`。

3. **FSRS 不可用时是明确跳过。** 行为门 `:340–345` 调用 `pytest.skip`，并非最终断言通过；正控和结果检查也都不会执行。因此，不能把包含此 skip 的整体成功退出当成行为边界已验证。

4. **主 spec 与基线逐字相同。** 两版本 Git blob 均为 `bec8896f3d8e76d39c276c200d005ca4b824320b`；[spec:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/openspec/specs/concept-identity/spec.md:14)、`:35/:39` 仍引用退役方法。这部分仍悬空。

5. **文档没有把 TOCTOU、mastery 漂移登记成已解决。** [D0 文档:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/docs/fsrs-truth-source-d0-revision.md:66)、`:67/:83` 明确保留限制；[known-gotchas.md:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/docs/known-gotchas.md:139) 仍标“部分修复／未修”。④ 行和 G-FAKE-007 的“已退役”指方法删除，没有明确宣称 spec 或三份状态已收敛。


