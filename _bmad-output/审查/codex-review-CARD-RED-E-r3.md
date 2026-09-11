> 批次: BATCH-2026-09-07-第十三批 · 车道 U10 · 卡 CARD-RED-E round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-E-r3.md)"`
> 审查绑定: `49994317`（Codex 自述绑定 `49994317d89fbdf4b1ef2ae981305dac89e0d3cb`，与当时 HEAD 一致）
> 会话头自证（`.stderr` 的 :4 / :7 / :10 / :11，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `sandbox: read-only` / `reasoning effort: ultra`
>
> ⚠️ 抄的不是字面前三行：codex 0.153.3 本次把 stdin 提示与一条 `codex_models_manager` 刷新超时 ERROR
> 打在会话头之前，`model:` 落在 :7。协议 §2.1 的「前三行」是位置判据，此处按其实质（含 model 行的会话头）
> 抄录并标注实际行号。
> ✅ 本文件正文是原始落盘 stdout，未经任何处理（首部为以上 blockquote 追加，正文一字未改）。

---

审查绑定 **`49994317d89fbdf4b1ef2ae981305dac89e0d3cb`**。六份恢复文件的字节一致性已独立核实；发现 **1 个 MEDIUM 门缺口**。构造器副作用受读取范围限制，尚不能完整核验。

**BLOCKER：该档 0 条。**

**HIGH：该档 0 条。**

**MEDIUM：1 条。**

**M-1：新增运行期测试仍只绑定数量，等长替换可以让 `hint-generation` 脱离实际监控而全部断言保持绿色。**

定位：

- [test_agent_templates_smoke.py:227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_agent_templates_smoke.py:227)：仅断言 `total == len(names)`、`missing == []`、`available == len(names)`。
- [agent_service.py:5731](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/services/agent_service.py:5731)：按实际列表分桶，但只返回可用项数量。
- [test_agent_templates_smoke.py:213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_agent_templates_smoke.py:213)：声称 “any such edit changes the length”，范围过宽。

在列表定义之后，仅在内存中注入：

```python
expected_templates[-1] = "graphiti-memory-agent"
```

使用当前生产分桶代码、本树真实模板目录、当前静态提取函数和三条原始运行期断言，实测：

```text
静态名单：13 项，包含 hint-generation
实际名单：13 个不同成员，不包含 hint-generation
报告：total=13，available=13，missing=[]
三条运行期断言：全部 PASS
```

静态名单与基线逐项相同，因此两条集合断言也不会改变结果。换成已存在的 `"scoring-agent"` 同样通过，此时实际只有 **12 个不同成员**。

这不是当前生产列表已经错误，而是本轮新增门仍会放过其声称防止的名单漂移。D 的三种负控都缩短了列表，不能证明等长修改也被覆盖。

建议保留纯 pytest 方案，增加**真实空临时目录下的探测**，将返回的完整 `missing` 名单与静态名单逐项比较，并校验重复项；这样才能利用返回字段核对成员身份。本次复现执行的是生产分桶片段及原始断言，未执行完整服务入口或整套 pytest。

**LOW：该档 0 条。**

其余重点核查结果如下。

1. **新模板的字段层级正确，但解析成功不等于模型输出已受结构校验。**  
   [hint-generation.md:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/.claude/agents/hint-generation.md:48) 的标题、换行、代码围栏精确匹配 [gemini_client.py:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/clients/gemini_client.py:193) 的正则。解析器先得到 `output_format` **字符串**，对其 `json.loads` 后得到根级 `hint_text`、`hint_level`、`reasoning`，没有 `data` 包装层。模板要求只输出该 JSON 对象，与 [agent_service.py:2466](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/services/agent_service.py:2466) 的 `result.update(parsed)` 和 [verification_service.py:3036](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/services/verification_service.py:3036) 的读取路径兼容。证据支持格式契约一致，尚未证明真实 AI 调用成功或模型始终遵从。

2. **`>= 18` 单独仍有余量，完整 smoke 门能挡住“删期望文件、补无关文件”。**  
   [smoke.py:199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_agent_templates_smoke.py:199) 统计全部 `.md`，补一个无关文件确实能保住数量测试。但 `:163`、`:175`、`:186` 按期望文件名检查存在性，仍会失败。因此数量断言不是身份保证，组合门才提供删除告警。  
   另需纠正作者自述的小标题：负控 B 实际是 **4 failed**，包括存在性、非空、汇总缺失和数量检查；“数量检查红且含 found 17”属实，“仅指定用例红”不属实。见 [negctl-b-red:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-e/negctl-b-red-20260909T000001.txt:80)。

3. **作用域收窄后，普通改名、外移和 helper 重构会明确失败。**  
   对当前提取器的内存验证结果：变量改名或移到方法外直接使用 → `bound 0`；改为 `expected_templates = helper()` → `not to a list literal`；方法内第二次绑定 → `bound 2`。这些路径没有静默失效。AgentType 增删后的差集消息也能指出具体方向。  
   但 [smoke.py:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_agent_templates_smoke.py:114) 仍使用递归 `ast.walk(fn)`，方法内部未调用的嵌套函数若有同名局部，仍可能噪声红。保留旧字面量、另让 helper 改写实际成员的情况，则仍受 M-1 的身份缺口影响。

4. **入库和恢复核对通过，pytest 不保护 Git index。**  
   六份文件均满足“当前工作树 = HEAD blob = `f425d7b7^` blob”，字节数和 [restore-sha:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-e/restore-sha-20260909T000001.txt:6) 开始的记录一致；当前 tracked 模板精确为 18。  
   `.gitignore` 不会自动取消已跟踪文件。后续 `git rm`、普通删除再 `git add -u`、恢复到不含这些文件的版本，都可能造成删除；`git rm --cached` 则可只移除跟踪而保留磁盘文件，使本地 pytest 继续通过。后者是作者已经承认的边界。另，“hint 历史新增记录为空”仅适用于本卡之前；当前历史已有本卡 `eed7a44c` 的新增记录。

5. **health 新增一项会有意收紧健康判定。**  
   根据 [agent_service.py:5771](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/services/agent_service.py:5771)：客户端与密钥正常、原 12 项齐全但缺 hint 的部署，会从 `healthy` 变为 `degraded`；13 项齐全则保持 `healthy`。只增加这一项不会让原先的 `degraded` 反向变为 `healthy`；客户端或密钥不满足时仍优先返回 `unhealthy`。这是新增监控的预期语义。未更新的 API mock 测试不能证明真实生产表仍是 12 项。

6. **构造器隔离性和验收措辞还有明确的证据边界。**  
   `include_api_test=False` 确实跳过 [agent_service.py:5746](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/services/agent_service.py:5746) 的 AI ping 分支，但不足以证明整个 `AgentService()` 生命周期没有缓存、全局状态或其他副作用。运行期探测还读取 `settings.AGENT_PROMPT_PATH`，而文件 smoke 使用仓根推导的 `_AGENTS_DIR`，两者不是同一配置来源。  
   你指定的读取范围没有覆盖构造器、完整 health 方法和路径配置定义；定点扩展请求尚未获得答复，因此 **(a) 保留为未完整核验，不判定存在缺陷，也不授予“无副作用／CI 无配置稳定”结论**。验收单 Markdown 同样不在允许范围内；允许读取的代码中，M-1 已足以证明“实际名单已绑定”的说法过宽。

总评：**恢复字节与新模板格式契约通过；完整 smoke 组合能发现期望文件被删除或清空，round-3 也挡住了已列举的三种减项输入。但实际 health 名单绑定仍为 PARTIAL，等长替换可以假绿。** 本卡可以声称修复了缺文件及指定回归场景，尚不能声称名单一致性已完全锁住，也不能据现有证据宣告端到端 AI 提示和构造器隔离性验收完成。


