# Story 3.13: Prompt 注入防护与输出安全检查

Status: ready-for-dev

## Story

As a 系统,
I want 对话输入有 Prompt 注入检测，LLM 输出有安全检查，
So that 恶意输入不能操纵 AI 行为，AI 输出不包含有害内容。

## Acceptance Criteria

1. **AC-1: System/User 结构隔离（Layer 0 — 后端算法权威）**
   - **Given** 任何通过后端发送给 LLM 的调用
   - **When** 构造 prompt messages
   - **Then** system prompt 和 user message 严格隔离（PromptTemplate.build 强制 system/user 分离）
   - **And** user input 永远不进入 system message
   - **And** system message 包含 SYSTEM_BOUNDARY_MARKER，PromptTemplate.validate_messages 在每次 LLM 调用前验证消息格式
   - **And** 验证失败的请求拒绝发送，返回 400 错误

2. **AC-2: 输入注入检测（heuristic rule engine）**
   - **Given** 用户在对话中输入内容
   - **When** 内容发送给 LLM 之前
   - **Then** check_input() 检测已知注入模式（role override、encoding bypass、delimiter manipulation、multilingual variants including Chinese）
   - **And** risk_score >= INJECTION_THRESHOLD（默认 0.7）的输入被阻断
   - **And** 被阻断的输入返回安全降级回答（"检测到异常输入，请重新表述您的问题"）
   - **And** 结构化日志记录检测结果（risk_score, matched_patterns, input_preview, latency_ms）

3. **AC-3: 编码绕过防御**
   - **Given** 用户输入包含编码过的注入尝试
   - **When** 输入进入检测引擎
   - **Then** 自动尝试 Base64 / Hex / ROT13 解码后再次扫描注入模式
   - **And** 编码绕过检测结果标记为 `encoding_bypass:{encoding_type}:{pattern_label}`

4. **AC-4: LLM 输出安全检查（Layer 5 — 结构化输出引导）**
   - **Given** LLM 返回了生成内容
   - **When** 内容返回给前端之前
   - **Then** check_output() 检测以下安全违规：
     - system prompt 泄漏（boundary marker 出现、自我披露模式、verbatim content 泄漏）
     - 危险代码执行指令（exec/eval/subprocess/curl|bash）
     - XSS 脚本注入（`<script>` 标签）
   - **And** 检测到违规时，输出经过 sanitize 处理后再返回前端
   - **And** 危险内容前置 `[Safety Notice]` 标记

5. **AC-5: 集成到所有 LLM 调用路径**
   - **Given** 后端有多条 LLM 调用路径（AgentService.call_agent、AgentService.call_agent_with_images、GeminiClient.call_agent、ClaudeClient.call_agent、AutoScorer、VerificationService）
   - **When** 任何路径发起 LLM 调用
   - **Then** 输入侧 check_input() 在 prompt 构造前执行
   - **And** 输出侧 check_output() 在结果返回前执行
   - **And** 安全检查不阻塞主请求（P95 延迟增加 < 5ms）

6. **AC-6: 日志与监控**
   - **Given** 检测到注入尝试或输出安全违规
   - **When** 事件发生时
   - **Then** 通过 structlog 发射结构化日志事件（injection_detection / output_safety_violation）
   - **And** 日志包含：check_type、risk_score、is_blocked、matched_patterns、input_length、latency_ms
   - **And** 日志不记录完整用户输入（仅 preview 前 100 字符）以保护隐私

7. **AC-7: 可配置的开关与阈值**
   - **Given** 运维需要调整安全策略
   - **When** 通过环境变量配置
   - **Then** INJECTION_GUARD_ENABLED 控制开关（默认 true）
   - **And** INJECTION_THRESHOLD 控制阻断阈值（默认 0.7）
   - **And** 关闭 guard 时所有输入放行，check_input() 返回 risk_score=0.0

## Tasks / Subtasks

- [ ] **Task 1: 将 prompt_injection_guard.py 集成到 AgentService（核心集成）** (AC: #1, #2, #4, #5)
  - [ ] 1.1 在 `agent_service.py` 的 `call_agent()` 方法中，调用 LLM 前执行 `check_input(prompt)`
  - [ ] 1.2 如果 `is_blocked=True`，直接返回安全降级回答，不调用 LLM
  - [ ] 1.3 LLM 返回后，执行 `check_output(response_text, system_prompt)` 安全检查
  - [ ] 1.4 如果 `is_safe=False`，使用 `sanitized_output` 替代原始输出
  - [ ] 1.5 在 `call_agent_with_images()` 中同样集成输入/输出安全检查
  - [ ] 1.6 在 `call_agents_batch()` 中对每个请求独立执行安全检查

- [ ] **Task 2: 集成到 GeminiClient / ClaudeClient（LLM 客户端层）** (AC: #1, #5)
  - [ ] 2.1 在 `GeminiClient.call_agent()` 中使用 `PromptTemplate.build()` 构造消息（替代直接拼接）
  - [ ] 2.2 在发送前调用 `PromptTemplate.validate_messages()` 验证消息格式
  - [ ] 2.3 在 `ClaudeClient.call_agent()` 中同样使用 `PromptTemplate.build()` 构造消息
  - [ ] 2.4 验证失败时 raise ValueError 并记录日志，不发送请求

- [ ] **Task 3: 集成到 AutoScorer 和 VerificationService** (AC: #5)
  - [ ] 3.1 在 `AutoScorer.evaluate()` 的两阶段调用前后添加安全检查
  - [ ] 3.2 在 `VerificationService._call_gemini_for_question()` 前添加输入检查
  - [ ] 3.3 在 `VerificationService.generate_question_with_rag()` 输出侧添加输出检查
  - [ ] 3.4 在 `VerificationService.generate_hint_with_rag()` 输出侧添加输出检查

- [ ] **Task 4: 集成到 MCP exam_tools** (AC: #5)
  - [ ] 4.1 在 `mcp/tools/exam_tools.py` 的 `generate_question()` 添加输入/输出安全检查
  - [ ] 4.2 在 exam tools 的 `score_answer()` 对用户答案输入执行注入检测
  - [ ] 4.3 确保安全检查不影响 pipeline_token 流程（检查在 token 生成/验证之前执行）

- [ ] **Task 5: WebSocket 对话路径集成** (AC: #2, #5)
  - [ ] 5.1 在 WebSocket 消息处理（`endpoints/websocket.py`）中添加输入注入检测
  - [ ] 5.2 WebSocket 被阻断时，发送安全降级消息（type: "safety_block", 含 risk_score）
  - [ ] 5.3 输出安全检查在 WebSocket 响应流式传输结束后执行（完整内容检查）

- [ ] **Task 6: 安全降级回答模板** (AC: #2)
  - [ ] 6.1 创建中文安全降级回答模板：
    - 注入被阻断：`"检测到异常输入模式，请重新表述您的问题。如果这是正常学习内容，请尝试用不同的方式提问。"`
    - 输出不安全：`"[安全提示] AI 输出中检测到潜在不安全内容，已过滤处理。"`
  - [ ] 6.2 降级回答包含 `safety_metadata` 字段（risk_score、matched_patterns 摘要、timestamp）

- [ ] **Task 7: 测试** (AC: #1-#7)
  - [ ] 7.1 单元测试：check_input() 对各类注入模式的检测率（目标：覆盖 OWASP LLM Top 10 2025 的 LLM01 常见攻击向量）
  - [ ] 7.2 单元测试：check_output() 对 system prompt 泄漏、危险代码的检测
  - [ ] 7.3 单元测试：编码绕过检测（Base64 / Hex / ROT13 编码的注入）
  - [ ] 7.4 单元测试：中文注入模式检测
  - [ ] 7.5 集成测试：完整调用链中安全检查的端到端工作
  - [ ] 7.6 性能测试：check_input + check_output 联合延迟 < 5ms（P95）
  - [ ] 7.7 测试 INJECTION_GUARD_ENABLED=false 时所有检查被旁路

## Dev Notes

### 6-Layer Agent Defense Architecture Context

This story implements **Layer 0** and **Layer 5** of the 6-layer Agent behavior constraint defense architecture:

| Layer | Mechanism | Constraint Strength | This Story |
|-------|-----------|-------------------|------------|
| Layer 0 | 后端算法权威（不可绕过） | Hard | **YES** — PromptTemplate structural isolation, server-side enforcement |
| Layer 1 | 密码学令牌管道（跳步拒绝） | Hard | No — implemented in Story 3.2 (pipeline_token.py) |
| Layer 2 | CLAUDE.md/AGENTS.md | Advisory ~80% | No — prompt-level, not code |
| Layer 3 | Claude Code Hooks | Deterministic, Claude Code only | No — client-side hooks |
| Layer 4 | 后端审计守护（异步检测） | Hard | No — implemented in Story 3.2 (guardian.py) |
| Layer 5 | 结构化输出 | Guiding ~90% | **YES** — output safety check, sanitization |

**Layer 0 implementation in this story:**
- `PromptTemplate.build()` enforces structural isolation between system and user messages
- `PromptTemplate.validate_messages()` validates message format before every LLM call
- `SYSTEM_BOUNDARY_MARKER` prevents system prompt leakage
- This is a **hard** constraint — the server controls message construction, users cannot bypass it

**Layer 5 implementation in this story:**
- `check_output()` validates LLM output for safety violations
- Output sanitization removes system prompt leaks and dangerous code
- Structured output format (JSON schema enforcement in AutoSCORE) is a complementary mechanism already in Story 6.4
- This is a **guiding** constraint — reduces attack surface but LLMs may still produce unexpected output

### Existing Security Code

The module `backend/app/middleware/prompt_injection_guard.py` is **already fully implemented** but **not integrated anywhere** in the codebase. Key findings:

- `PromptTemplate` class: builds system/user isolated messages
- `check_input()`: heuristic rule engine with 25+ patterns (English + Chinese + delimiter + indirect injection + encoding bypass)
- `check_output()`: system prompt leak detection + dangerous code detection + XSS filtering
- `InjectionCheckResult` / `OutputCheckResult`: well-defined result dataclasses
- Structured logging via structlog already configured
- Environment variable controls already in place (INJECTION_GUARD_ENABLED, INJECTION_THRESHOLD)

**Integration gap:** No file in `backend/app/` imports `prompt_injection_guard`. The guard exists but is dead code. This story's primary work is integration, not new module development.

### Architecture Compliance

- **FR-QA-05**: Prompt 注入防护 + LLM 输出安全检查 — this story is the direct implementation
- **NFR-SEC-06**: Prompt 注入防护 — security requirement fulfilled by this story
- **NFR-SEC-07**: 6 层 Agent 行为约束防御架构 — Layer 0 and Layer 5 portions
- **OWASP LLM Top 10 2025 LLM01**: Prompt Injection (ranked #1 risk) — the guard module references OWASP Prompt Injection Prevention Cheat Sheet

### Integration Points (All LLM Call Paths)

| Call Path | File | Method | Integration Location |
|-----------|------|--------|---------------------|
| Node dialogue | agent_service.py | `call_agent()` | Before LLM call + after response |
| Image dialogue | agent_service.py | `call_agent_with_images()` | Before LLM call + after response |
| Batch calls | agent_service.py | `call_agents_batch()` | Per-request check |
| Gemini direct | gemini_client.py | `call_agent()` | Message construction |
| Claude direct | claude_client.py | `call_agent()` | Message construction |
| AutoSCORE | autoscore.py | `evaluate()` | Both stages |
| Verification | verification_service.py | `_call_gemini_for_question()` | Before call + after response |
| Exam tools | mcp/tools/exam_tools.py | `generate_question()` / `score_answer()` | MCP tool input/output |
| WebSocket | endpoints/websocket.py | message handler | Stream completion check |

### Performance Constraints

- check_input() is regex-based heuristic — measured at < 1ms for typical inputs in the module's own timing
- check_output() includes substring scanning for system prompt leak — should be < 2ms for outputs up to 4K tokens
- Combined P95 target: < 5ms (well within the architecture's requirements)

### References

- [OWASP LLM Top 10 2025 — LLM01 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [OWASP Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- Architecture: `_bmad-output/planning-artifacts/architecture.md` — Authentication & Security section (6-layer defense table)
- Existing module: `backend/app/middleware/prompt_injection_guard.py` — fully implemented, needs integration
- Related: Story 3.2 (pipeline_token.py — Layer 1, guardian.py — Layer 4)
- Related: Story 6.4 (AutoSCORE structured output — complementary Layer 5 mechanism)

## Dev Agent Record

### Agent Model Used
<!-- To be filled by implementing agent -->

### Debug Log References
<!-- To be filled during implementation -->

### Completion Notes List
<!-- To be filled during implementation -->

### File List
- `backend/app/middleware/prompt_injection_guard.py` — existing module (PromptTemplate, check_input, check_output)
- `backend/app/services/agent_service.py` — primary integration target (call_agent, call_agent_with_images, call_agents_batch)
- `backend/app/clients/gemini_client.py` — LLM client integration (call_agent, call_agent_with_images)
- `backend/app/clients/claude_client.py` — LLM client integration (call_agent, call_agent_with_images)
- `backend/app/services/autoscore.py` — AutoSCORE integration (evaluate)
- `backend/app/services/verification_service.py` — verification integration (_call_gemini_for_question, generate_question_with_rag, generate_hint_with_rag)
- `backend/app/mcp/tools/exam_tools.py` — MCP exam tools integration (generate_question, score_answer)
- `backend/app/api/v1/endpoints/websocket.py` — WebSocket integration
- `backend/app/audit/guardian.py` — related Layer 4 (already implemented in Story 3.2)
- `backend/app/mcp/pipeline_token.py` — related Layer 1 (already implemented in Story 3.2)
- `backend/tests/test_prompt_injection_guard.py` — new test file
