> 批次: BATCH-2026-09-07-第十三批 · 车道 U10（card-u10-red-a） · 卡 CARD-RED-A2 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-A2.md)"`
> 审查绑定: `052a9289..fe3787ce`（该轮送审时 HEAD = 绑定区间右端，复核结束时未漂移）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**结论：本卡测试修复成立，未发现 BLOCKER / HIGH。** 有一项 MEDIUM 级论证错误需要纠正：“任何经过 Pydantic 校验的 Settings 都无法到达 Branch 1”不成立。

审查绑定为 `052a9289..fe3787ce`，当前 HEAD 和两文件字节均已对账。全程只读；独立执行了配置、鉴权及日志捕获的内存验证，17 条和目录级结果则来自存档复核，没有重新运行整套 pytest。

1. **MEDIUM — Branch 1 并非在真实配置路径上完全不可达。**

   [config.py:295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/config.py:295) 检查原始 key 的真假值；[security.py:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/security.py:91) 先做 `.strip()`。独立实测：

   ```python
   Settings(
       _env_file=None,
       DEBUG=False,
       INTERNAL_API_KEY="   ",
       NEO4J_ENABLED=False,
   )
   ```

   在隔离环境下通过全部校验；传给当前真实鉴权函数后，返回 **503、精确 detail，并记录 `auth_fail_closed`**。这是“任何已验证 Settings 都不可达”的直接反证。

   对**精确空串 `""`**，正常启动确实会先失败：[config.py:966](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/config.py:966) 在模块导入时就调用 `get_settings()` 创建配置。因此，本卡三条证明的是：**非法配置若抵达鉴权依赖，最后一道防线仍拒绝请求**，不能证明“漏配 key 的正常部署成功启动后返回 503”。

   两层防御仍有各自价值，没有依据删除 Branch 1 或放宽配置校验。全空白 key 可作为额外真实构造用例，不能替换这三条精确空串负控。

2. **LOW — `model_construct` 确实引入其他配置偏差，但未导致当前三条测错分支。**

   位置：[test_sync_batch_auth.py:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_sync_batch_auth.py:98)、[test_system_endpoint_auth.py:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_system_endpoint_auth.py:91)。

   独立遍历全部 **77 个字段**：清空环境、禁用 `.env` 后，与相同参数但 `DEBUG=True` 的合法 `Settings` 比较，只有 `DEBUG` 不同，未发现跳过其他 validator 导致默认值额外变形。

   但对象同时带有 `NEO4J_ENABLED=True`、`NEO4J_PASSWORD=""`，还违反了 [config.py:288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/config.py:288) 的另一条生产不变量。它也没有保留真实环境对其他字段的覆盖值，所以不能宣称整个对象等同真实生产配置。

   **这不影响当前分支结论**：Branch 1 只读取 key 和 DEBUG，随后立即抛异常。更小的故障注入方式是：先正常创建合法开发态配置，保持 key 为空、显式关闭 Neo4j，再用 `model_copy(update={"DEBUG": False})`。其余字段先经过校验，仅最终更新绕过校验；仍不能将它称为正常启动路径。[Pydantic 文档](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_copy)

3. **LOW — caplog 当前承重，但裸子串不足以唯一绑定当前 HTTP 请求。**

   位置：[test_sync_batch_auth.py:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_sync_batch_auth.py:171)、[test_system_endpoint_auth.py:155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_system_endpoint_auth.py:155)，以及同文件第 210 行。

   两段专项负控成立：①捕到 Branch 1，错误 token 断言失败；②捕到 Branch 2，原 token 断言失败。结合正常运行的 17 PASSED，足以证明**本次环境中非恒真、非恒假，而且能独立分辨这两个分支**。

   缺少的反例有两类：

   - 保留 Branch 1 的 503/detail，仅移除其日志事件，保持测试断言不变。
   - Branch 1 事件缺失，但同一测试调用阶段的其他事件发出了匹配 token。

   第二类已有具体碰撞：[security.py:220](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/security.py:220) 的 **`ws_auth_fail_closed` 也包含 `auth_fail_closed`**。纯内存验证确认，它以及其他 logger 输出的同名 token 都能满足当前断言。尚无证据表明当前三条已经受到这种污染。

   更稳的测试侧判据是请求前清空捕获，检查 `caplog.records`，同时限定：

   `name == "app.security"`、`funcName == "require_internal_api_key"`、`levelno == ERROR`、完整标记 `"(auth_fail_closed)"`。

   `at_level(..., logger=...)` 调整级别，并不筛选日志来源。`security.py` 本来就是 stdlib logger，structlog 桥接不是捕获该事件的必要条件；[conftest.py:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/conftest.py:61) 设置 root propagation，也不能修复子 logger 的 `propagate=False` 或 `disabled=True`。当前存档已经证明当时捕获链正常。[pytest 日志文档](https://docs.pytest.org/en/stable/how-to/logging.html#caplog-fixture)

4. **LOW — 精确 detail 耦合文案，但文案漂移会显式打红。**

   位置：[test_sync_batch_auth.py:170](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_sync_batch_auth.py:170)、[test_system_endpoint_auth.py:154](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_system_endpoint_auth.py:154)，以及同文件第 209 行。

   Branch 2 以前者整句为前缀的事实成立，当前精确等值确实能够分层。生产 detail 改一个字会产生 `AssertionError`，**不会静默通过**。可把上述限定来源的日志事件作为主要层身份判据，精确 detail 作为额外响应契约；现有日志标记仍是字符串，尚非正式结构化事件码。

5. **LOW — 两处自述超过了实际证据粒度，主体结论不受影响。**

   - [test_system_endpoint_auth.py:204](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_system_endpoint_auth.py:204) 对应的 test-llm 用例，基线原本只有状态码断言，没有模糊 detail。因此“三条原有两项断言均通过”不准确。AST 对比确认：**全部既有断言均保留**，三条分别从 `2→4、2→4、1→3` 项。
   - [caplog 存档:12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a2/negctl-caplog-20260909T200502.txt:12) 中，①还原只保存了 `diff-quiet-rc=0`，没有该次还原后的 SHA 输出；②保存了 SHA 和 diffquiet。最终字节已独立对上 `fe3787ce`，但不能说存档完整展示了每一次 SHA 对账。

其余核心自述核对成立：生产代码零改动、仅目标档位切换构造方式、四段负控失败身份吻合、两文件 17 PASSED。原始目录日志重新提取 nodeid 后，确为 **120 failed → 117 failed，仅删除目标三条、无新增**；29 errors 保持不变。这支持本卡净修复三条，不代表目录全绿。


