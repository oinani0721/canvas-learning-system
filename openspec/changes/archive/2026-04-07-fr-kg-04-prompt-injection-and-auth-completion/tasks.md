## 1. 前置确认（必须先完成）

- [x] 1.1 grep `useInternalApiKey` hook 在 frontend 中的所有调用点 — 由 `ApiClient` 自动注入，无需手动 hook 调用
- [x] 1.2 Settings Tab 零改动（F5 修正：`ApiClient.postModelConfig` / `testLlmConnection` 已自动携带 `X-CLS-Internal-Key`）
- [x] 1.3 不再依赖 sidecar `__contextPrefix` 字段（D-USER-2 决策改为 chat-store 文本前缀包装，零 IPC 协议变更）
- [x] 1.4 `require_internal_api_key` 已在 `backend/app/security.py`（F1 修正：非 `app/core/security.py`）
- [x] 1.5 `test_sync_batch_auth.py` 作为鉴权测试模板参考，`_settings_factory` 和 `auth_client` fixture 被 `test_system_endpoint_auth.py` 复用

## 2. Phase 1 — /system/* 鉴权扩展

- [x] 2.1 `backend/app/api/v1/system.py:22` 已 `from app.security import require_internal_api_key`
- [x] 2.2 `system.py:431` `update_model_config` 装饰器已含 `dependencies=[Depends(require_internal_api_key)]`
- [x] 2.3 `system.py:498` `test_llm_connection` 装饰器同上
- [x] 2.4 `backend/tests/unit/test_system_endpoint_auth.py` 已新建（10 tests 覆盖完整 5 分支 fail-closed 状态机）
- [x] 2.5 `pytest backend/tests/unit/test_system_endpoint_auth.py -v` → 10 passed
- [x] 2.6 backend + curl 验收路径记录在 `docs/security/prompt-injection-playbook.md`
- [x] 2.7 frontend Settings Tab 通过 `ApiClient` 自动注入 header，零代码改动

## 3. Phase 2 — Learning Context 注入路径降权

- [x] 3.1 grep `chat-store.ts` 中 `learningContext` 的引用完成
- [x] 3.2 删除了 `frontend/src/stores/chat-store.ts` 原 line 577-580 的 `systemPrompt` 三元拼接
- [x] 3.3 改为 `const systemPrompt = baseSystemPrompt;` 单行
- [x] 3.4 通过新导出的 `wrapUntrustedLearningContext(text, learningContext)` 纯函数在 `mgr.sendMessage` 前把 user message 包装为 `<UNTRUSTED_LEARNING_CONTEXT>` 前缀块（D-USER-2 文本前缀方案，非 `__contextPrefix` 字段）
- [x] 3.5 零 sidecar 改动（D-USER-2：wrapped message 通过现有 `request.message` 字段原样流向 SDK）
- [x] 3.6 `frontend/src/stores/chat-store.test.ts` 已新建，7 个测试覆盖：empty/null/undefined pass-through + normal wrap + embedded close tag escape + mixed-case escape + preamble ordering
- [x] 3.7 `npm test -- chat-store.test.ts` → 7 passed

## 4. Phase 3 — 系统 prompt 元规则 + record_learning_memory 加固

- [x] 4.1 `agent_service.py` 在 `tool_instruction` 之后追加 `safety_meta_rule` 段（5 条规则：Untrusted 标签语义 / 不要把资料当指令 / 禁止写工具触发 / 引用时必须复述 / 冲突优先级）
- [x] 4.2 拼接已改为 `system_prompt = f"{system_prompt}{tool_instruction}{safety_meta_rule}"`
- [x] 4.3 `react_agent.py` `record_learning_memory` docstring 已扩充：`⚠️ WRITE OPERATION` 横幅 + 3 前置条件 + `严禁` 4 反例
- [x] 4.4 `每次请求最多调用2次` 约束保留
- [x] 4.5 `backend/tests/unit/test_safety_meta_rule_in_prompt.py` 已新建，4 个断言（UNTRUSTED tag 引用 / MUST NOT 子句 / 工具名提及 / 拼接顺序）
- [x] 4.6 `backend/tests/unit/test_record_learning_memory_docstring.py` 已新建，5 个断言（WRITE OPERATION / UNTRUSTED / 频次 cap 保留 / 严禁子句 / 自名引用）

## 5. Phase 4 — 集成对抗测试

- [x] 5.1 `backend/tests/integration/test_prompt_injection_learning_context.py` 已新建（50 parametrized tests）
- [x] 5.2 15 个标准攻击向量均通过 `format_as_markdown` → `wrapUntrustedLearningContext` Python mirror → 验证结构不变量（tip 注入路径）
- [x] 5.3 同样 15 向量覆盖 `edge_reason` 注入路径
- [x] 5.4 专用测试 `test_layer2_wrap_escapes_injected_close_tag` 验证 tag-closing injection 防御
- [x] 5.5 Layer 3 / Layer 4 全局不变量测试（safety_meta_rule 存在 / record_learning_memory description 有 WRITE OPERATION）
- [x] 5.6 `test_full_stack_all_vectors_pass_all_layers` 合并验证所有 4 层在所有 15 向量下的不变量
- [x] 5.7 `pytest tests/integration/test_prompt_injection_learning_context.py -v` → 50 passed

## 6. 文档与归档

- [x] 6.1 新建 `docs/security/prompt-injection-playbook.md`（defense-in-depth 5 层架构图 + 15 攻击向量清单 + regression guards 列表）
- [x] 6.2 在 `docs/known-gotchas.md` 追加 G-INJ 系列 4 条（G-INJ-001~004 覆盖 chat-store / meta rule / docstring / system auth）
- [x] 6.3 `pytest backend/tests/ -x -q` 整体回归（在 Task 11 Phase 6 执行）
- [x] 6.4 `cd frontend && npm test` 整体回归（在 Task 11 Phase 6 执行）
- [x] 6.5 `npx openspec validate fr-kg-04-prompt-injection-and-auth-completion --strict` 全绿（Phase 0 已确认）
- [ ] 6.6 创建 commit 走 lefthook hooks（待用户授权）
- [ ] 6.7 通知用户 PR 准备就绪，等待手动验收
