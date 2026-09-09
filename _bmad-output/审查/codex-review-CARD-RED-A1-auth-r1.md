> 批次: BATCH-2026-09-07-第十三批 · 车道 U10（card-u10-red-a） · 卡 CARD-RED-A1-auth round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-A1-auth.md)"`
> 审查绑定: `7004a365..工作区`（改动当时未提交，审的是工作树；HEAD 仍为 7004a365。⚠️ 不绑合并态）
> 会话头自证（抄 .stderr 的 model / provider / reasoning effort 行，stderr 本身不入库）:
> `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
> `model: gpt-6-astra`
> `provider: openai`
> `reasoning effort: ultra`

---

结论：**未发现 BLOCKER/HIGH；fixture 修复有效，但五条用例的移交理由不足，若干新增说明需要纠正。** 本次只读审查了当前工作树相对 `7004a365` 的差异、新 fixture 和指定证据；未重跑 pytest。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM**

1. **五条用例“契约已过期、必须改断言才能修”的判断不成立。**

   位置：[second-layer-20260909T134842.txt:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/second-layer-20260909T134842.txt:63)。

   §A:63–74 将设置 active vault 等同于“关掉隔离”，并把 `status_code == 200` 解释成“任意 vault 都应被接受”。实际五条验证的是 ContextVar 注入、中文保留、subject 可选、路径字符净化和 emoji 剥离；没有明确安排“请求属于另一个 vault”的前提。

   [vault_scope.py:160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/core/vault_scope.py:160) 仍真实执行 `requested not in active_vault_aliases()`。为正向测试配置匹配的 active vault，不会删除这条判定。“需要逐例设置前提”也不等于违反“禁止改断言”。

   **建议：重新确认移交分类。** 可以出于分工移交，但目前只能说测试前提尚未适配，不能声称已经证明五条断言错误、必须重写或本卡无法修复。

2. **新增说明把尚不存在的 409 覆盖当作已有保障。**

   位置：[test_chat_endpoint.py:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_chat_endpoint.py:43)、[test_study_question_deep_mode.py:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_study_question_deep_mode.py:43)。

   两处声称“vault 一致性判定本身由 `test_enrich_context_vault_isolation.py` 负责”。该文件实际没有任何 **409 断言**：五条正向测试被 409 阻断，两条验证 422，一条直接验证 ContextVar 并发隔离。因此，不能用它证明“请求 vault 与 active vault 不一致时会拒绝”的回归覆盖。

   **建议：删除这项覆盖保证，或引用真正验证 409 的测试。** 这不否定当前两处 active-vault 桩，但必须准确说明它们不证明哪些安全性质。

**LOW**

1. **第二层分类表误述请求路径。**

   位置：[second-layer-20260909T134842.txt:17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/second-layer-20260909T134842.txt:17)。

   “非 HTTP 的 rag_enrich_hook 单元”不实：三条都在 `test_chat_endpoint.py:429、458、480` 使用 `client.post("/api/v1/chat/rag/enrich-hook", ...)`。同段把六条 sync 也归为“本就不进业务层”，但它们确实进入端点异常分类。

   **建议：区分输入校验、端点提前返回和端点业务处理。** 转绿数量没有因此失效，错误在分类说明。

2. **把 conftest 中的 fixture 可发现性写成自动执行。**

   位置：[authed_client.py:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/support/authed_client.py:19)。

   独立命名、非 `autouse` 的 `authed_client` 即使定义在 conftest，也仍需测试或其它 fixture 请求才执行；不会自动给所有测试加 key。

   **建议：保留当前 opt-in 实现，把理由改为“限制可发现范围、要求显式导入”。**

3. **“Settings 逐字等价”不实。**

   位置：[test_sync_exception_classification.py:57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_sync_exception_classification.py:57)。

   `_dev_settings()` 的 `PROJECT_NAME="Test"`、单来源 `CORS_ORIGINS`，与 `authed_client.py:76、80` 不同。鉴权所需 key 和 DEBUG 相同，不代表整份设置相同。

   **建议：改为“鉴权相关字段一致”。**

对其余关键问题，核对结果如下：

- **覆盖不会按当前 fixture 生命周期泄漏。** [authed_client.py:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/support/authed_client.py:107) 保存进入前的值，退出只删除或恢复 `get_settings`。function-scope autouse `isolate_dependency_overrides` 先快照，最后恢复整表。用例再次替换同键后，teardown 回收这次临时替换是正确行为；不应把用例设置留给下一个测试。没有发现需要改成“仅当当前值仍是本 fixture 的值才恢复”的理由。

- **现有 HTTP 请求都使用这个 client。** 四文件没有另建客户端或逐请求 `headers=`。实例头能覆盖现有路径。HTTPX 的请求头按名称合并：增加其它头不会删除鉴权头，显式提供同名鉴权头则会覆盖它。不能把实例默认头理解为不可覆盖保证；本次未运行额外的 headers 探针。

- **chat 的 10 条和 deep 的 7 条 active-vault 桩合理。** 这些 enrich-context 请求确实使用相同常量，原有断言验证组装、图降级、预算及检索参数。桩改变的是 active-vault 输入，真实 resolver 仍执行；没有发现因此掩盖了这 17 条原本验证的跨 vault 行为。

- **sync 两桩没有替换异常分类路径。** schema gate 和 vault 解析位于 `sync.py:107–118`；被测调用仍在 `:138`。registry 的 autouse no-op 也与作者声明一致。更直接的证据是 [four-after 日志:336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/four-after-20260909T135007.txt:336)：三种基础设施异常留下对应分类日志，后续三种逻辑异常的 traceback 明确经过 `process_sync_batch()` 和测试里的 `raiser`，不是鉴权 503 偶然匹配。

- **未发现本卡新增的“业务未执行却误绿”。** memory 桩走的是“成功返回空历史记录”，原有图降级和 mode 参数断言仍在执行。它不验证历史记忆服务的异常降级分支；“空列表相同”不能当作异常路径覆盖证明。五条 422、一个空 node_path 的 400 本来就验证拒绝行为，停在校验处符合意图。所引用的 `chat.py:341/:354`、assembler `:473` 及 schema gate 内部实现超出指定读取范围，本次没有替这些事实声明背书。

独立重算原始 nodeid 后，**37＝32 转绿＋5 仍红**成立；目录级红集从 193 降到 161，新增红 nodeid 为零。AST 比较也确认四文件的 `assert` 和断言方法调用未变；未改生产代码、两个 conftest、W4，也未新增 skip/xfail。

总评：这套改动达成了**解除鉴权阻挡并恢复 32 条测试执行**的目标，没有发现通过放宽鉴权或吞掉被测业务来求绿。但“让 37 条业务断言全部跑到业务层”尚未达成：五条仍在 409 后失败，另有输入校验测试本就不应进入下游。当前主要问题是把五条未解决的测试前提问题过早归为契约债，移交依据需要重新核定。


