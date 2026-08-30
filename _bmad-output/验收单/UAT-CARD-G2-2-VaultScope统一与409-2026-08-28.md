# 验收单 — CARD-G2-2 唯一 VaultScope resolver + 409 fail-closed

> **批次**: BATCH-2026-08-28-第五批 · 车道 S1 第一卡
> **日期**: 2026-08-28
> **worktree**: `.claude/worktrees/card-s1-scope`（未 push）

## 一、这张卡给你带来什么（用户可感说明）

### 409 行为 — 「防串库保险丝」现在全面生效

以前的问题：后端有 **8 套各自为政**的「判断请求属于哪个 vault」的代码
（11 个 endpoint 共享一套 + 5 个文件各自复制一套 + tips/boards 又各有私有版本）。
它们的兜底行为分裂成 4 种——最危险的一种是：请求带了 vault A 的名字，
但后端进程当前挂载的是 vault B 时，部分接口会**静默把 A 的数据操作套到 B 的作用域上**，
这就是跨 vault 串库暗坑（你的 CS61B 批注可能落进数学 vault 的桶里）。

现在的行为：**只要请求显式声明了 vault，而它和后端当前挂载的 vault 不一致，
后端立刻拒绝并返回 409 错误**，错误信息同时写明「你请求的 vault」和「当前挂载的 vault」，
例如：

```
409: vault 未激活: cs_61b (当前挂载: 数学) — 请求 vault 与进程 active vault 不一致,
拒绝静默改写作用域 (CARD-G2-2 fail-closed)
```

你在什么场景会看到它：Obsidian 插件/skill 的 curl 指向了错误的后端实例
（比如双树拓扑下 A vault 的插件打到了 B vault 的后端）。以前这种错配**静默吞掉、
数据落错桶、几周后才发现**；现在当场报 409，错误里直接告诉你两边各是谁。

### 409 的「假警报」防线（Codex 审查后加固）

后端识别 vault 身份有两套说法：`.canvas-config.yaml` 里的**稳定 ID**，和 vault
**目录名**。插件、SessionEnd hook、exam skill 发来的往往是目录名或显示名。
如果只拿稳定 ID 做比较，「稳定 ID ≠ 目录名」的合法配置会让**每一个正常请求都 409**
——等于全站瘫痪。

现在的判定用**别名集合**：稳定 ID、`ACTIVE_VAULT` 环境变量、实际挂载目录名，
三者任一命中即放行，并统一归一到稳定 ID（防止同一 vault 因入口不同分裂成两个数据桶）。
真正指向另一个 vault 的请求三项都不命中，仍然 409——保险丝没有被削弱。

### 两个例外（设计内，不是 bug）

1. **Claude Code 对话 hook**：hook 请求从工作目录推导 vault，你在 A vault 目录里
   开对话而后端挂载 B 是合法场景（推导优先，不 409）——已在代码里显式建模+文档化。
2. **旧版插件的 deprecated group_id 参数**：仍走兼容归一化路径（带 warning 日志），
   不做 409——强行检查会把兼容层整个杀死，该面收敛归后续 G2-4/G4 卡。

### 「不传 vault」的行为也统一了

以前 5 个克隆里有 3 个在请求不带 vault 时落 `vault:default` 污染桶（写进去的数据
任何 vault 都查不到）。现在统一为：**推导当前挂载的 vault**，写读恒同命名空间。

## 二、技术完成条件核对（AND）

| # | 条件 | 结果 |
|---|------|------|
| (a) | 新建 `backend/app/core/vault_scope.py`：单点解析 + 409 + 双缺失推导 active vault + hook 例外文档化 + `current_group_id()` 统一读取口 | ✅ 253 行新模块，5 条契约全在模块 docstring |
| (b) | 收敛面：共享 resolver re-export 化；exam/metadata/memory/errors/exam_sessions 5 克隆删除；tips 私有 helper、boards 手写 409、subjects/chat/inheritance/context/profile/mastery 全改调 | ✅ `_vault_id_resolver` 现为纯 re-export（mastery alias `is` 同一性测试保持绿） |
| (c) | service 层 ContextVar→DEFAULT_GROUP_ID 兜底统一替换（agent_service×3 / conversation_archive×5 / inheritance / error_writer / learning_context / react_agent / event_handlers / memory_service×3） | ✅ 全部改经 `current_group_id()` |
| (d) | grep 判据：endpoint 层+memory_service 0 直读 DEFAULT_GROUP_ID、0 直调 get_current_vault_id（豁免：review.py=D3/D4 合并后 micro-patch 移交、main.py startup、archive_scheduler、relationship_sync、graphiti_memory_reader/exam_service_ext/mastery_store=G2-4/G4 消费链） | ✅ 见 §三 grep 复核命令 |
| (e) | `test_vault_scope_409.py` 全绿（Codex 整改后扩至 **37 条**：五端点基线 + 13 条整改面覆盖 + 3 条别名容忍）；C6 契约反转 8 条全绿；wave5 两文件断言翻新 64 条全绿；裁判命令 `-k "vault_scope or contextvar or wave5_stageb"` 0 fail；全量收集 3967 条无 Interrupted | ✅ |

### review.py 移交条款（卡文明示）

`review.py:34-58` 本地克隆与 `review_service.py:615-625` 的 DEFAULT_GROUP_ID 清零
属 in-flight D3+D4 锁定文件，按 F4 双门决议拆为「L1 收尾 micro-patch」，
**D3+D4 合并后经合并队列 rebase 落地**，本卡不触碰。
`exam_service.py`/`verification_service.py` 全批禁改（G5-12 地盘），未触碰。

## 三、验收步骤（可复核）

```bash
cd .claude/worktrees/card-s1-scope/backend

# 1. 裁判命令
.venv/bin/pytest tests/unit -q -k "vault_scope or contextvar or wave5_stageb"
# 预期: 0 failed (Codex 整改后 test_vault_scope_409.py 共 37 条)

# 2. grep 判据（应只剩豁免清单内文件/注释行）
rg -n "DEFAULT_GROUP_ID" app/api/v1/endpoints/ --glob '!review.py' | rg -v "^\S+:\d+:\s*#|docstring|推导|污染桶"
rg -n "get_current_vault_id" app/api/v1/endpoints/ --glob '!review.py'   # 应为空
rg -n "DEFAULT_GROUP_ID|get_current_vault_id" app/services/memory_service.py  # 应为空

# 3. 手动感受 409（可选，需 backend 起在任一 vault 上）
curl -s -X POST http://localhost:8011/api/v1/boards/manifest \
  -H 'Content-Type: application/json' -H "X-CLS-Internal-Key: $KEY" \
  -d '{"vault_id": "不存在的vault", "board_id": "x"}' | head -3
# 预期: 409 + 两侧 vault 名称
```

## 四、409 爆炸半径：存量测试逐一修（卡文预算内主要工作量）

409 fail-closed 生效后，凡是「请求某 vault 但进程 active vault 是另一个」的
存量测试都会红。逐一核实并翻新：

| 测试文件 | 现象 | 处置 |
|---|---|---|
| `test_wave5_stageb_*.py`（2 文件 18 条） | `vault_id="cs_61b"` vs active `canvas_vault` → 409 | 用 `patch("app.config.get_current_vault_id")` 把目标 vault 声明为激活态；双缺失断言由 `DEFAULT_GROUP_ID` 翻新为「推导 active vault」 |
| `test_subjects_group_isolation.py`（5 条） | 同上（`vault_a` / `vault_b`） | 新增 `_activate_vault()` helper；双 vault 隔离用例改为「两次请求各在自己 vault 激活的进程里发出」——409 门下这才是合法形态 |
| `test_story_2_3_error_reminders.py`（4 条） | mock 打在旧 `search_memories`，而 `search_error_memories` 内部已改调状态方法 | mock 目标同步到 `search_memories_with_status`，返回值包 `StatusedResult`；数据意图不变 |
| `test_react_agent.py`（1 条） | 断言 fallback 落 `DEFAULT_GROUP_ID` | 翻新为断言推导 active vault（原 warning 随兜底退役一并取消） |

**基线对照口径**：本卡触及的每个文件都与 HEAD 基线 worktree 跑同一 venv 做
`comm` 双向集合对比，确认**零新增失败**。全量套件的既有失败（基线 223 failed
+ 38 errors）不在本卡范围。

## 五、测试翻新说明（诚实记录）

- `test_react_agent.py` 两条、`test_lancedb_vault_isolation.py` 一条为**基线即红**的
  陈旧断言（punycode 物理格式硬编码 / reload_settings 被 .canvas-config.yaml 优先级
  短路），翻新为按契约函数计算期望值 / patch 正确层——测试意图保持不变。
- C6 `test_memory_service_contextvar_leak.py` 按其 docstring :36-41 预告完成契约反转：
  「进程级单 active vault、无视 ContextVar」→「per-request VaultScope 优先、
  无请求作用域回落 active vault」。安全依据：409 门保证请求路径二者一致，
  唯 hook-cwd 合法例外正是需要 per-request 优先的场景。

## 六、Codex 审查

- **round-1 存档**：`_bmad-output/审查/codex-review-CARD-G2-2.md` —— 裁定 FAIL，
  6 BLOCKER + 5 HIGH + 3 MEDIUM。
- **整改记录**：`_bmad-output/审查/codex-review-CARD-G2-2-round1-整改记录.md` ——
  逐条处置表 + 移交条款。

审查抓到的**真实失守面**（首轮我确实漏了，值得记录）：

1. `chat.py` 的 `/enrich-context` 与 `/post-turn-extract` 是第 9、10 份克隆，
   完全绕过 409（前者可读异 vault 记忆，后者可向异 vault 写错误记录）；
2. `tips.py` 四个端点把 409 吞成 200 空列表 / 500，且 **callout-direct 先写幂等键
   再 409** —— 客户端纠正 vault 后重试被判 duplicate，批注永久丢失；
3. `/archive/session` 的 409 被吞成 200 `status=error`，而 SessionEnd hook 把任意
   2xx 当成功 → 删除重试机会并丢整段会话存档；
4. `extract-conversation` 的 canvas_path 分支用 legacy `build_group_id(subject, canvas)`
   （无 vault 段），多 vault 塌进同一桶；
5. 稳定 ID vs 目录名的误 409 风险（见上）。

以上全部已修并有测试锁定（`TestCodexRound1RectifiedEndpoints` 13 条 +
`TestVaultAliasTolerance` 3 条）。读侧全组查询封堵（BLOCKER-5 主体、HIGH-7）
经核属 **CARD-G4-1 明文范围**（总账 v2 逐字点名 `memory_service.py:593/905`），
按铁律不越界，已写移交条款。
