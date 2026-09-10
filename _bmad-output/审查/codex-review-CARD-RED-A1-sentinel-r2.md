> 批次: BATCH-2026-09-07-第十三批 · 车道 card-u10-red-a · 卡 CARD-RED-A1-sentinel round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-A1-sentinel-r2.md)"`
> 审查绑定: `0acea4e3..e74757c5`（阶段一，**未** merge 候选树；审时 HEAD，工作树代码面干净）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> ⚠️ 字面第一行是 `Reading additional input from stdin...`；真正的会话头为
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a085c5-f00f-7b43-a2d6-43079626c55f`

---

**BLOCKER 0 / HIGH 0。** 本轮绑定 `0acea4e3..e74757c5564c4eb6139c7291ae59ca6d75f68dc8`。整改未引入已证实的生产功能缺陷；保留两项 MEDIUM 未闭合项，另有三项 LOW。

1. **MEDIUM｜M1 的新表述准确，移交符合地盘约束，但契约缺陷仍未修复。**

   [openapi.json:28662](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/openapi.json:28662) 引用 `APIKeyHeader`，而 `:15737` 的组件只定义 `InternalApiKey`。

   独立重算确认：悬空 operation **17→31**，其中 `/system/*` **2→16**；新增的 14 个确实从有效全局声明变成了无效局部声明。按本卡限定的修改面，带数字移交恰当，但应继续标为未解决，不能视为仅有文案问题。

2. **MEDIUM｜M2 正确撤回了装机验收通过，但新描述仍不是完整配置矩阵。**

   [验收单:383](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-sentinel-2026-09-09.md:383) 按配置区分提示、明确未验收，方向正确。不过“会被挡住并显示提示”仍有前提：

   - 后端已配置 key、请求缺头：403。
   - 后端空 key：鉴权层通常返回 503。
   - DEBUG、显式 bypass、loopback 同时成立：可以放行。
   - 非本地配置还可能在 Settings 校验时拒绝启动，根本没有 HTTP 响应。

   依据为 [security.py:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/security.py:96)、`:110`、`:144` 和 `config.py:295`。实际页面表现及密钥配置流程仍未验证；没有发现可坐实的现役插件启动死锁。

3. **LOW｜负控 B 正常运行恢复干净，但新增“恢复自证”可以对空观测误报 PASS。**

   [status_conformance_probe.py:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-sentinel/status_conformance_probe.py:184) 只检查恢复观测中有没有未声明码；`restored=[]` 同样得到 `True`，随后 `:187` 可以合成最终 PASS。

   已用真实 `main()`／`_observe()` 做受控反例：仅在恢复后从实际 schema 删除全部 `/system/*` paths，仍得到：

   ```text
   还原自证 ... True
   VERDICT=PASS
   RESTORED_SYSTEM_PATHS=[]
   ```

   因此“恢复后再次全绿”**单独不足以证明完整恢复**。应比较恢复前后的 operation 键集、状态码及声明；`:179` 的负控 B 也只比较数量，未绑定相同键集。

   **本次正常恢复没有失败。** 独立复跑确认：路由声明内容、字典及内层对象身份、键顺序、完整 OpenAPI 内容、依赖覆盖和 lifespan 均恢复，连接尝试为 0。缓存对象经过失效重建，身份改变符合当前实现。

4. **LOW｜hunk 多重集能识别重复新增，但仍可能漏掉位置迁移或旧新抵消。**

   [格式存档:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-sentinel/ruff-format-hunk-multiset-20260909T183436.txt:4) 的“新增违规必然出现新内容”过强；实际比较的是带符号行多重集，丢失了位置、上下文和 hunk 边界。

   **单纯增加与存量重复的违规不会漏**，因为次数增加。但把旧位置的 `return [1,2]` 修好，同时在新位置引入同样违规，两侧多重集仍完全相同。当前 Ruff 的内存反例已复现这一点。

   **本卡实际整改成立。** 独立重算得到 **97/122/84/0/0/0/0**，并进一步核对 formatter 修改位置与本卡新增行无交集；未发现上述抵消。验收单 `:475` 的“逐 hunk 比”应改成准确的“带符号行内容多重集比较”。

5. **LOW｜整改表已经改正，验收单旧正文仍重复被否定的事实。**

   同一份验收单仍有：

   - [`:123`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-sentinel-2026-09-09.md:123)：仍称“进程终态……逐项相同”。
   - [`:200`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-sentinel-2026-09-09.md:200)：仍用检查名出现 0 次推导“两个码都声明到位”。
   - [`:501`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-sentinel-2026-09-09.md:501)：仍笼统称首次装机相关端点“现在会 403”。

   所以 **L3／L4②／M2 的文档整改尚未全文完成**。探针 `:16–17` 的新超时措辞本身成立，没有继续声称检查未执行。

两个 fixture 的新 docstring **通过复核**：[test_mock_degradation_transparency.py:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_mock_degradation_transparency.py:43) 和 [test_review_mode_support.py:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_review_mode_support.py:34) 限定为连接控制状态，符合当前路径。`431/467/534/554` 引用仍准确；`554` 是初始化判定，实际调用在 `555`。时间戳只被写入或展示，不参与再次连接判定。这支持**同一实例**不把首次连接推给后续调用，不能外推所有实例或任意测试顺序。

冷首触候选 **确实成立，属于既有隔离边界**：[test_verification_service_activation.py:221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_verification_service_activation.py:221) 经真实 VerificationService、`get_mastery_store()`、`MasteryStore.get_concept()` 到达冷单例的 driver 初始化。当前 `default` 分组能转换为 `vault__default`，不会提前阻断。动态验证使用原测试体与原 fixture，在 driver 初始化入口记录后停止，确认可达而未拨号；相关路径在 `U0..HEAD` 无改动，没有依据要求本卡越界修复。

存档核对结果一致：unit 为 **120 failed / 4810 passed / 48 skipped / 29 errors**，149 条红与整改前完全相同；相对 202 基线减 **53**、新增 **0**，相对开工减 **12**、新增 **0**。五文件双序各 **72 passed、零哨兵**；API **268 passed、端口总账 0**；探针 v2 及 Ruff 结果均独立复现。

本轮全程只读，未重跑全量 pytest；上述套件结论来自原始存档重算。审查期间 r1 报告被外部补入说明头，代码、验收单及证据文件仍与绑定 HEAD 一致。


