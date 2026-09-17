> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-E (card-t5-bugs) · 卡 CARD-T-UNREACH round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-T-UNREACH.md)"`
> 审查绑定: `802f05ca352afc3d432b1511f7e2e38869f19eb3`（= 送审时的 HEAD = 本卡最终代码 HEAD；Codex 本轮自述「审查绑定 802f05c；指定文件与工作区一致」）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`

---

本卡未发现需要修复的缺陷。审查绑定 `802f05c`；指定文件与工作区一致，给定 diff 范围内确实只改三个文件。

- **BLOCKER：无**
- **HIGH：无**
- **MEDIUM：无**
- **LOW：无**

按问题顺序核对：

0. **500 语义正确。** [boards.py:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/boards.py:87)：负控输入为 service 返回缺必填字段的数据，失败发生在服务端输出投影，归为 500 合理；**调用方是否依赖旧 422 未核实**，允许读取的文件不包含调用方实现。

1. **MCP 输出契约保持。** [board_manifest_tools.py:70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/board_manifest_tools.py:70)：同一负控仍返回 `ok=False、manifest=None`，按 `ok` 降级的消费者不受文案变化影响；但这不能独立证明 HTTP 侧「curl 失败→Grep」实际执行，当前只有注释声明。

2. **指定三处均未被遮蔽。** [board_manifest_service.py:1029](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/board_manifest_service.py:1029)、[同文件:1069](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/board_manifest_service.py:1069)、[canvas_service.py:701](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/services/canvas_service.py:701)：各自都是所属 `try` 的唯一 handler，不存在前置宽异常截走输入；这不构成全仓 census 证明。

3. **KeyError 对照语义保持。** [boards.py:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/boards.py:94)、[board_manifest_tools.py:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/board_manifest_tools.py:73)：对照输入 `KeyError("no such board")` 仍进入原分支，HTTP 404 与 MCP detail 提取逻辑均未改变；普通 `ValueError` 分支也保持原行为。

4. **patch 目标正确，未发现实际泄漏。** [测试文件:70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_board_manifest_unreach_t5e.py:70)：函数内 import 应 patch 源模块，`serve_manifest` 应 patch 消费模块，monkeypatch 会在测试结束恢复；但 [:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_board_manifest_unreach_t5e.py:74) 的 `asyncio.run` 不恢复调用前预设的 current loop，因此依赖共享 loop 的其它测试属于未覆盖路径，不能声称全进程隔离已获证明。

5. **删除 ignore 合理。** [boards.py:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/boards.py:87)、[board_manifest_tools.py:67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/board_manifest_tools.py:67)：分支恢复可达后，删除针对 `reportUnusedExcept` 的抑制没有引入新诊断的代码依据；任意版本、配置下的结果以及 `0 errors / 81 warnings` 均未实测确认。

6. **当前 AST 门没有空跑假绿。** [测试文件:120](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_board_manifest_unreach_t5e.py:120)：`checked == 1` 拦住零匹配路径，纯内存负控恢复旧顺序后两处均断言失败；在前面新增 `except Exception` 是相对顺序门的盲区，但若它吞掉异常并改变结果，[:127–143 的行为门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_board_manifest_unreach_t5e.py:127) 会失败，不能据此判定整套测试假绿。

没有运行 pytest、pyright、项目导入、服务或数据库操作，也没有修改文件。源码支持真实 `model_validate` 失败及 11 个展开用例，但作者所述历史红绿结果、运行时负控和前后哈希一致性仍未独立验证。

**计数：BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 0。**
