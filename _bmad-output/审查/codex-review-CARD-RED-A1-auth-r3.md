> 批次: BATCH-2026-09-07-第十三批 · 车道 U10（card-u10-red-a） · 卡 CARD-RED-A1-auth round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-A1-auth-r3.md)"`
> 审查绑定: `7004a365..bcbe2741`（Codex 正文首段自陈：审查期间工作区另有未提交改动，本轮只评价该提交）
> 会话头自证（抄 .stderr 的 workdir / model / provider / reasoning effort 行，stderr 本身不入库）:
> `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
> `model: gpt-6-astra`
> `provider: openai`
> `reasoning effort: ultra`

---

本轮绑定 **`7004a365..bcbe2741`**。全程只读，未重跑 pytest。审查期间工作区出现了额外未提交修改；以下结论只评价指定提交。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM：无。**

**LOW：2 条。**

1. **chat 的校验用例仍少算一条。**

   位置：[test_chat_endpoint.py:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_chat_endpoint.py:46)。

   新说明写“`:131/:140` 那两条在 Pydantic / 入参校验就返回的用例”，实际有 **3 条用例、4 次 POST**：

   | 用例 | 定义行 | 实际断言 |
   |---|---:|---|
   | `test_enrich_context_empty_node_path_rejected` | 163 | 400 |
   | `test_enrich_context_max_hops_validation` | 172 | 两次 422 |
   | `test_enrich_context_rejects_invalid_mode` | 350 | 422 |

   `:131/:140` 实际分别是 happy-path 的断言和 degraded 测试的数据。正确计数为 **16 = 10 条 enrich-context 正向 + 3 条校验 + 3 条 rag hook**。

   **建议：**补上非法 mode 用例，改成“三条”，并使用测试名称定位，区分用例数与请求次数。

2. **更新后的行号仍有漂移，短 prompt 的 POST 还对应错了用例。**

   位置：[chat:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_chat_endpoint.py:24)、[study:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_study_question_deep_mode.py:42)、[isolation:37](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_enrich_context_vault_isolation.py:37)、[second-layer:23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/second-layer-20260909T134842.txt:23)、[UAT:241](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-auth-2026-09-09.md:241)。

   最终 HEAD 的准确位置为：

   | 对象 | 定义行 | POST 行 |
   |---|---:|---:|
   | chat `uses_lazy_init` | 432 | **443** |
   | chat `short_prompt_skips_lazy_init` | 461 | **472** |
   | chat `lazy_init_returns_none_injects_degraded_marker` | 481 | **494** |
   | study 非法 mode | **121** | 123 |
   | isolation 并发测试 | **175** | 无 |

   现写的 `:434/:463/:485` 全是 `AsyncMock` 导入；study 的 `:114` 是有效 deep 请求；isolation 的 `:173` 是空行。`second-layer:23` 将短 prompt 的 POST 写为 `:434`，另外两条业务处理 POST 应是 **`:443/:494`**。

   **建议：**按最终提交逐项更新，并让 `second-layer`、fixture 说明和 UAT 使用同一映射。短 prompt 改归第 (ii) 类的分类本身正确。

两条 MEDIUM 的整改均已落实：

- **“另有 409 覆盖且绿”准确。** [test_vault_scope_409.py:333](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_vault_scope_409.py:333) 确实发送异 vault payload 并断言 409。[开工日志:279](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/unit-open-20260909T132605.txt:279) 与[收工日志:279](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/unit-after-20260909T134347.txt:279) 均记录该文件全部通过，证据不止是红集缺席。“一直绿”应限定理解为**这两次存档均通过**。
- **“同一组桩”准确。** 该文件 `:360–367` 与本卡两处 fixture 的 patch 目标、accessor 的 `AsyncMock` 返回方式，以及 `search_error_memories` 返回 `[]` 的行为一致。
- **移交理由已收窄为分工。** 当前说明承认 function-scope fixture 可以按用例适配前提，已删除“断言过期”“判契约演进”的当前结论。
- **其余计数正确：**study 为七条有效正向加一条非法 mode；isolation 为七条 HTTP 加一条并发测试；rag hook 确为三条。

总评：**解除鉴权阻挡、让 32 条测试恢复通过的目标成立；“37 条业务断言全部跑到业务层”仍不成立。** 五条仍停于 409，校验及提前返回用例也有各自预期的停止位置。未发现新增假绿或把运行问题转嫁给其它测试。round-2 至本轮五个 Python 文件去掉 docstring 后的可执行 AST 一致，既有覆盖还原、请求头、active-vault 桩和 sync 异常分类结论未被动摇；memory 桩仍只证明空历史结果路径，不证明历史服务异常降级分支。


