> 批次: BATCH-2026-09-07-第十三批 · 车道 U10（card-u10-red-a） · 卡 CARD-RED-A1-auth round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-A1-auth-r2.md)"`
> 审查绑定: `7004a365..faeda37f`（已提交 HEAD，非工作区）
> 会话头自证（抄 .stderr 的 workdir / model / provider / reasoning effort 行，stderr 本身不入库）:
> `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
> `model: gpt-6-astra`
> `provider: openai`
> `reasoning effort: ultra`

---

本轮结论：**BLOCKER=0 / HIGH=0 / MEDIUM=2 / LOW=2。五条整改尚未完全闭合，剩余问题均为说明准确性。**

审查绑定 `7004a365..faeda37f`，已确认 HEAD 及父提交。全程只读，未重跑 pytest；以下依据提交内容和已提交存档。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM**

1. **移交理由仍有旧结论残留，且新理由夹带过强的必要性判断。**

   位置：[UAT:243](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-auth-2026-09-09.md:243)、[second-layer:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/second-layer-20260909T134842.txt:82)。

   UAT:244 仍称五条“断言过期了”，:264 仍写“判契约演进移交”，与其 :108–115 已更正的“未证明断言错误、按分工移交”直接冲突。

   second-layer:82–84 又写“要修需逐用例改用例代码”。五条输入不同，只能证明不能共用一个固定 `return_value`，不能推出必须修改用例体；函数级 fixture 可以按用例配置前提。

   **建议：**统一为“需要按用例适配 active-vault 前提，本卡按分工移交”。移交决定可以成立，但不能继续以断言过期或必须改用例代码为依据。

2. **UAT 将 enrich-context 的覆盖缺口扩大成了全仓 vault 拒绝行为无覆盖。**

   位置：[UAT:250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-auth-2026-09-09.md:250)。

   此处省略端点限定，声称全仓没有验证“请求 vault 与 active vault 不一致时会被拒”的测试，并归因于 round-1 实证。两处 fixture 的新说明则明确限定为 **enrich-context**。

   指定存档中，[unit-open:2765](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/unit-open-20260909T132605.txt:2765) 已记录 `test_sync_batch_mismatch_409` 的运行；开工、收工日志 :279–280 均显示 `test_vault_scope_409.py` 通过。虽然本轮未越界读取其断言，但不能据此宣称全仓没有这类覆盖。

   **建议：**补回 enrich-context 端点限定；不要将局部覆盖缺口推广为整个 vault 拒绝机制无覆盖。

**LOW**

1. **重新分类仍漏分短 prompt 的提前返回路径。**

   位置：[second-layer:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/second-layer-20260909T134842.txt:21)。

   表中把三个 RAG hook 用例全部归入“确实进了业务处理”。但 [test_chat_endpoint.py:452](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_chat_endpoint.py:452) 明确测试短 prompt 提前返回：发送 `"hi"`，断言 HTTP 200 且 `captured_lazy` 未调用。

   **建议：**按表自身标准，将该用例归入第 (ii) 类；第 (iii) 类保留另外两个 hook 用例和六个 sync 用例。这是预期的提前返回覆盖，不是假绿。顺便更新 POST 行号为当前 :434/:463/:485。

2. **fixture 说明中的“每条／全文件”仍超出实际覆盖范围。**

   位置与依据：

   - [test_chat_endpoint.py:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_chat_endpoint.py:24) 称所有请求携带同一 `vault_id`，但 :434、:463、:485 的三个 hook 请求没有该字段。
   - [test_study_question_deep_mode.py:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_study_question_deep_mode.py:42) 称不配 active vault“每条断言都会变成 409”，但非法 mode 用例在 :120 验证的是先行的 Pydantic 422。
   - [test_enrich_context_vault_isolation.py:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_enrich_context_vault_isolation.py:35) 称本文件每条断言原先均停在鉴权；实际 :173 的并发测试不请求 client、不走 HTTP，开工已绿。

   **建议：**分别限定为“本文件的 enrich-context 请求”“七条有效输入的正向请求”“本文件使用 client 的 HTTP 用例”。

原 LOW-2 的“可发现范围＋显式导入”、原 LOW-3 的“鉴权相关字段一致”已准确落实。两处 fixture 新增的“本桩不证明不一致时会拒绝”也符合代码；匹配 active vault 后，真实隔离判定仍执行。

总评：**解除鉴权阻挡、恢复 32 条测试执行的目标成立；“37 条业务断言全部跑到业务层”仍不成立。** 五条仍在 409 处失败，输入校验和提前返回用例也有各自正确的停止位置。覆盖还原、实例头、17 条 active-vault 桩及 sync 异常分类的 round-1 结论未被动摇；AST 比较确认四文件断言未变。未发现新增业务未执行却误绿，或将运行问题转嫁给其它测试。memory 桩仍只提供成功返回空历史记录，不证明历史服务异常降级分支。


