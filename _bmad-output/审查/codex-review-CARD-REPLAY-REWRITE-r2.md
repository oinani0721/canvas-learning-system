> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p2-outbox · 卡 CARD-REPLAY-REWRITE round-2
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-REPLAY-REWRITE-r2.md)" > _bmad-output/审查/codex-review-CARD-REPLAY-REWRITE-r2.md 2> _bmad-output/审查/codex-review-CARD-REPLAY-REWRITE-r2.stderr </dev/null`
> 审查绑定: `47ebbc21`（= 最终代码 HEAD；`git --no-pager diff --stat --no-color 47ebbc21 HEAD -- . ':(exclude)_bmad-output'` = 空）
> 会话头自证（抄 `.stderr`，行号括注；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: glm-5.3`（第 5 行） / `reasoning effort: max`（第 9 行）

---

# Round-2 复核结论

**绑定确认**：本地 `HEAD = 47ebbc215174704041da7e96fac5b7e40279c57e`；代码树无 dirty/untracked 代码改动，仅审查文档类 untracked 文件。累计 diff 为 9 个代码/测试文件，`3d0c4fce → 47ebbc21` 整改 delta 为 3 文件，与卡面一致。

**总裁定**：在**明确限定的单进程、单 uvicorn 部署模型**下，r1 的两个 HIGH 不再构成当前合入阻断：HIGH-1 已实质修复；HIGH-2 可降级为已登记部署边界。四件主事——稳定身份、来源 vault、二次写成功条件、身份日志崩溃恢复——在正常 v2 写侧输入下成立。

但我不建议把结论写成“确定性坏输入都不会阻断整代”：**timestamp 与可 `int()` 但不可安全作为 Neo4j 整数的 score 仍有同类残余缺口**。本轮发现 **0 BLOCKER / 0 HIGH / 2 MEDIUM / 2 LOW**。

本轮未运行测试、服务或数据库连接；结论来自只读 diff、源码、测试与裁定文档核对。

---

## 发现清单

```text
[MEDIUM] backend/app/services/fallback_sync_service.py:926 — timestamp 只做 truthy/fallback，没有在图写入前验证可解析，坏 timestamp 仍可逃出窄异常捕获并阻断整代。
  复现思路：未被拦下的输入 — 构造 concept/vault/score 均有效但 timestamp={"x":1}、123 或 "not-a-date" 的条目；:932 直接送 datetime($ts)，驱动参数错误/Neo4jError/ValueError 不属于 :1001-1003 或 :512 的三类捕获，后续 good 条目无法 finalize；对照 ISO timestamp 主路径仍绿。
```

```text
[MEDIUM] backend/app/services/fallback_sync_service.py:903 — score 预验只证明 Python int(score) 不抛，未规范化/约束类型与 Neo4j 64 位整数范围，LEARNED 与 Episode 仍可分叉或继续阻断。
  复现思路：未被拦下的输入 — score=10**1000 会通过 int(score) 但可能在驱动打包处抛非捕获异常；score="80" 或 80.5 会在第一次 LEARNED 写原值、二次 Episode 写 int 值，造成图内类型/数值不一致；现有 test_unconvertible_score... 只覆盖 "not-a-number"，对照 score=80 仍绿。
```

```text
[LOW] backend/app/services/fallback_sync_service.py:929 — 缺 timestamp+score 的条目虽不再确认，但仍先执行 no-ts LEARNED 写入再 return False，空图分支会每轮重复写未确认分数。
  复现思路：门未覆盖的路径 — 空图上放入 no-ts score=10 条目，:930 先写 r.score，:936-944 再整条留待；现有 integration gate 先用 t1 制造图上 timestamp，unit 替身又未断言 run_query==0，因此“空图 + no-ts 仍发生第一次图写”没有任何门经过。
```

```text
[LOW] backend/app/services/fallback_sync_service.py:589 — overflow 全确认后先 rotate 成 .synced 再清身份日志，崩在两者之间会让该代 key 永久残留。
  复现思路：未被拦下的输入 — 在 :586 rotate 成功后、:589 clear 前注入崩溃，或让 _clear_confirmed_ids 抛 OSError；下一轮 overflow_siblings 不再扫描 .synced 文件，因此该 generation key 不会被清掉；数据不会重放/丢失，但身份日志会累积并污染审计状态。
```

---

## ⓪ 确认日志与文件写回之间任一崩溃点是否幂等

**单进程主路径：PASS。**

| 崩溃点 | 重启结果 |
|---|---|
| LEARNED 已写、Episode 未开始 | 重放两次写；LEARNED MERGE，Episode 按 `(record_id, group_id)` MERGE，不重 |
| Episode 已写、身份日志未落 | 重放；同上，Episode 不重 |
| 身份日志 atomic replace 中途崩 | 只见旧/新日志之一；新则跳过，旧则幂等重放 |
| 身份日志已落、代际文件未 rewrite | 重启加载 confirmed IDs，跳过已确认，继续未确认 |
| active rewrite atomic replace 中途崩 | 旧文件则下轮再剔除；新文件则 confirmed 日志继续保护 |
| rewrite 后追加新死信 | finalize 前重新读当前文件并按身份过滤，新 record_id 会保留 |
| 空 rewrite 后 rotate、clear 前崩 | 文件已不在，数据已确认；主要是日志残留问题 |
| overflow 处理中被 prune | finalize 锁下复查 FileNotFound，不把旧快照写回、不复活 |

关键实现：`_persist_confirmed_ids` 在每条成功后落盘（`:515-520`），active finalize 重新读当前文件并调用 `_filter_confirmed_lines`（`:523-555`, `:598-617`），Episode 幂等键在 `neo4j_client.py:1871-1882`。

限定：该结论**不覆盖多进程**；也不覆盖同一 record_id 后续 payload 被人为改变的异常输入。

---

## ① legacy 内容哈希是否可接受

**结论：legacy-only 可接受；不能扩大为 v2 正常兜底。**

- 无 `record_id` 的历史行没有可区分“重复落盘”与“两次独立事件”的身份；`sha256(canonical JSON)` 只能给出保守合并（`:129-142`）。
- 后果仍是不可逆少记一次 Episode，尤其两条语义独立但逐字相同的 legacy 事件。
- v2 正常写侧 `serialize_failed_write → stamp_failed_write_identity` 总会生成 uuid（`failed_writes_constants.py:518-555`），因此该取舍不应影响新数据。
- 若看到 `schema_version=2` 但缺 `record_id`，应视为异常/损坏 v2，而不是把内容哈希说成 v2 正常身份策略。

---

## ② 缺 vault 的 90 条历史条目产品后果

**结论：安全优先，代价是恢复可用性归零，直到显式归属或迁移。**

- 无 `group_id`/`vault_id` 且未设 env 时，`_resolve_entry_source` 返回 `quarantined`，不写图、留文件、计 pending（`:627-645`）。
- 这避免了 G2-2 的错 vault 写入，但卡面所述 90 条历史会持续占用 pending/quarantined 状态。
- `CLS_REPLAY_LEGACY_NOSCOPE_VAULT` 是**全局归属开关**，只在操作者能证明这批 no-scope 条目全部属于同一 vault 时安全；若历史混合来源，一键 env 会把全部写成同一 vault。
- 有 `vault_id` 但无 canvas/path 的条目走 `unresolvable`，不计 `quarantined`；排查报表不要把这两类混为一谈。

---

## ③ overflow 是否会重放已确认 record_id，幂等兜底是否足够

**串行单进程：PASS。**

- confirmation log 按代际文件名分 key；active 超时轮转后，旧内容以下一轮 `.overflow.*` 身份再次出现时可能重放。
- 对同一 `(record_id, group_id)`，Episode MERGE 防重，LEARNED MERGE 防边重复，因此冗余重放不产生重复图对象。
- 同一 record_id 出现在多个代际、同 group：第二次 replay 与第一次图结果幂等。
- 同一 record_id 但不同 group：会按 group 复合键成为不同 Episode，这是当前身份键设计的一部分。
- 该兜底依赖 record_id 稳定且 payload 不变；多进程并发 MERGE/finalize 仍不受保护。

---

## ④ 多进程与进程内锁定级

**结论：在当前单容器、单 uvicorn 部署模型下，HIGH-2 可重分类为 LOW / 登记边界；不是“已修复多进程”。**

依据：

- `backend/Dockerfile:28` 无 `--workers`。
- 卡面提交的 `docker top` 证据显示当前恰 1 个 uvicorn 进程；本轮未重新运行 docker 命令。
- `_sync_all_lock` docstring 明确登记“进程内；多 worker / 多进程未覆盖”（`fallback_sync_service.py:90-105`）。

仍需保持禁用的部署形态：

- `uvicorn --workers`
- backend 与 sidecar/脚本同时执行 replay
- 两个容器共享同一 `backend/data`
- 未来运维改命令但无文件锁

原因是 `threading.Lock`/`asyncio.Lock`、固定 `.tmp`、确认日志 read-modify-write 都没有跨进程互斥；并发 MERGE 也没有数据库唯一约束兜底。

---

## ⑤ pyright 0 是否靠 ignore 掩盖

**未发现本卡新增 `# pyright: ignore`。**

抽查结果：

- `fallback_sync_service.py` / `failed_writes_constants.py` / `neo4j_client.py` / `agent_service.py` / 两份新测试：0
- `memory_service.py`：2，均为既有，不在本卡 diff 中
- cumulative diff 中无 `pyright: ignore` 行增删

本轮没有重跑 pyright，因此只核对“零新增 ignore”，不重新证明 `0 errors / 82 warnings`。

---

## r1 处置复核

| # | r1 发现 | Round-2 结论 |
|---|---|---|
| 1 | HIGH-1：缺 ts+score 跳过二次写仍确认 | **修复成立**。`:936-944` 在二次写前返回 False，不确认；unit `:439-451` 与真库 gate `:499-507` 检查 Episode 0 / pending 1 / 文件保留。残余 LOW：第一次 LEARNED 写仍会发生。 |
| 2 | HIGH-2：多进程无互斥 | **降级成立**，但仅限当前单进程部署不变量；分类为 LOW/登记边界，不是并发安全性修复。 |
| 3 | MEDIUM-1：overflow unknown 被算术吞掉 | **修复成立**。任一代 unknown 使顶层 `pending=-1 + error`（`:371-423`），测试 `:471-490` 覆盖 chmod unreadable overflow。 |
| 4 | MEDIUM-2：坏 score 中断整代 | **对 r1 指定输入修复成立**：`"not-a-number"`/NaN/inf 在图写前拒绝（`:898-910`），好条继续（`:455-467`）。但同族残余 MEDIUM：巨大 int、字符串数字、浮点小数仍未闭环。 |
| 5 | LOW：legacy hash 合并 | **接受为 legacy-only 取舍**；v2 正常 writer 必带 uuid record_id。 |

**建议**：不以 r1 HIGH 阻断当前单进程合入；但两条 MEDIUM 应在关闭“确定性坏输入不阻断”这句验收表述前修复或明确缩小输入契约。
