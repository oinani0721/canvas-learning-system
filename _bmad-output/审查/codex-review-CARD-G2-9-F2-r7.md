> 批次: BATCH-2026-09-11-第十四批 · 车道 T1 · 卡 CARD-G2-9-F2 round-7
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F2-r7.md)"`
> 审查绑定: `08100483..64b1848f`（= 本卡最终**代码语义** HEAD；其后只有 `9e2b1443` 一笔 D-32 纯 docstring 尾巴，AST 等价证据见 evidence-g29f2/d32-ast-equivalence-*.txt。主 session 2026-09-14 在 D-15 上限之外授权本轮，专修 r6-MEDIUM-2）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

**结论：本轮增量可接受，r6-MEDIUM-2 已闭合；未发现本轮新增回归。**  
绑定 `08100483..64b1848f`，复核结束时 HEAD 仍为 `64b1848f`，两个审查文件与提交一致。

本次仅做静态审查和提取生产代码后的内存求值；未修改文件、未连接数据库或网络，未运行 pytest 或负控。

## 发现

**BLOCKER：该级别无。HIGH：无本卡新增回归；以下既有边界仍存在。**

### [HIGH] V 缺项且余名恰为规范逻辑名时，两条破坏性路径仍可能误删——与 B14_BASE 同态

定位：[lancedb_client.py:1422](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1422)、[lancedb_client.py:1571](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1571)。

复现思路：真实 vault `a_canvas` 留有逻辑表 `nodes`，物理名为 `a_canvas_nodes`；其目录不可发现且无指纹表，V 只剩 `a`。此表被判给 `a`，余名 `canvas_nodes` 又属于规范逻辑名，因此通过模糊名保护，可被 `drop_vault_tables("a")` 删除，存在漂移时也会进入自愈。

**归类：已登记移交的既有 HIGH，不是 F2 回归。** 基线同样按 `a_` 认领并处理此表。r4-H1/r5-HIGH-1 对 `a_b_canvas_nodes` 这一形态已闭合，但不能宣称解决所有缺项 V。

### [MEDIUM] 本 vault 的历史自定义表仍被跳过自愈，并可能阻止整次删除——本卡可用性回归，已登记移交

定位：[lancedb_client.py:1422](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1422)、[lancedb_client.py:1571](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1571)。

复现思路：V 完整且只有 `a`，本方历史表为 `a_old_index`，当前配置未包含 `old_index`；自愈持续跳过它，删索引则整次返回 0。

这确认 r6-MEDIUM-1 仍在。仅凭现有表名，无法同时保证“恢复所有历史表”和“拒绝所有未发现 vault 的表”；需要经过确认的归属清单或表级元数据，不能直接放宽此条件。

### [MEDIUM] 全部删除失败或安全拒绝，被 HTTP 消费方统一报告成“没有表”——端点契约移交建议

定位：[lancedb_client.py:1368](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1368)、[index.py:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/app/api/v1/endpoints/index.py:107)。

复现思路：库中已有表，但所有删除均抛错，或触发整次拒绝；客户端返回 0，端点返回 `404 / No tables found`，没有消费 `_last_drop_failures` 或 `_last_drop_refusal`。

这是可观察的契约变化。部分失败仍返回 200，但计数已反映成功调用数。按本卡边界，移交端点区分“不存在、失败、拒绝”，不列为本卡阻断。

### [LOW] “前提门与隔离门一起红”的说明已过期，断言本身仍有效

定位：[test_lancedb_cross_vault_drop_g29f1.py:591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:591)。

复现思路：退回朴素前缀后，前提门在 618 行失败；模糊名保护仍保住 `a_b_canvas_nodes`，自愈隔离断言可以继续通过。

**确认属于文案问题。** 但报告必须按实际红点解释负控，不能继续把它说成跨 vault 删除已经发生。

### [LOW] “不减少自己的认领”及“default 零跨 vault 暴露面”的绝对表述超出代码保证

定位：[lancedb_client.py:1185](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1185)、[lancedb_client.py:1151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1151)。

复现思路：V 包含 `a_vault` 时，`a` 拼出的 `a_vault_notes` 被归给 `a_vault`；另外，vault `file` 的自定义逻辑名 `fingerprints` 会拼成 `file_fingerprints`，仍命中 default 的精确例外。

能够证明的是：**同一调用 vault 的新认领集合不超过基线集合**；不能据此证明真实属于它的表全部保留认领。裸指纹重名也是基线已有的数据丢失边界，不是本轮新增 HIGH。

## ⓪ V 完整性与 TTL

| 情形 | 当前落点 |
|---|---|
| 非隐藏目录、含 `.obsidian/`，尚无任何表 | 目录来源即可纳入 V，不依赖指纹表 |
| YAML 声明不同 id，且成功读取 | 优先采用经 sanitize 的显式 id，与 `Settings.vault_id` 的 YAML 分支一致 |
| 目录移走、标记目录消失、变隐藏，或 YAML 读取失败后退回目录名 | 可能缺少真实 id，**不一定置降级**；有指纹表可补，没有则依赖模糊名保护 |
| `VAULTS_ROOT` 不是目录，或枚举抛出被捕获的异常 | 置降级；非 default 删除整次拒绝，自愈跳过 |
| 指纹表枚举抛错 | 同样置降级；没有指纹表本身则不算失败 |

因此，“主来源失败均可观测”也不能覆盖所有局部缺项：YAML 异常被吞后回退、正常扫描得到空目录等，都可能留下不完整 V。

**TTL 整改有效：** 两条破坏性路径入口强刷，并在流程内固定同一份 V；r4-H2 的降级自愈保护和 r4-H3 的流程中途 TTL 重算问题已闭合。普通读侧仍可使用五秒缓存。

“五秒内不可能有表”的理由不成立：旧 vault 目录恢复、已有表目录重新可见均无需等待索引。固定 V 也不等于目录发现与其他进程建表之间具有事务隔离。

## ① default 三态与本轮新门

**本轮重点三项均通过代码核验：**

- `bool(vault_id) and vault_id != "default"` 恰是 `_owns_table` 裸表分支条件的否定。
- drop 两处使用同一个显式参数；自愈两处使用预先求出的同一个 `owner_vault`。没有 `_UNSET` 未解析就直接进入 helper 的生产调用。
- 新 drop 门在 **1464** 行要求全集恰剩 `b_canvas_nodes`；新自愈门在 **1491、1494** 行分别要求自己的漂移表消失、他库漂移表保留。

default 没有变成全表可见或恒空。`_table_owner` 返回 `None` 不影响裸表分支，因为该分支不调用它。历史 `default_canvas_nodes` 仍不被 default 认领，但**基线也如此**。

## ② 命名与 ③ 分页覆盖

`resolve_table_name` 当前仍使用纯前缀幂等守卫，题干“改成归属判定”已不是现状。生产确有二次解析：`index_vault_notes → add_documents → resolve_table_name`。当前实现没有该双前缀回归；归属自检只告警，不改名。

测试读回使用显式 `limit=10_000`，本文件夹具不会落入默认十张盲区。页外删除门还检查自己的 12 张填充表全部删除；指纹存在性另有独立页外门。双向门同时检查本方漂移表被处理、本方删除计数和他方表保留，能够排除“操作完全没执行”的假隔离。

## ④ 负控的实际红点

以下是**按题述变异的静态推导，不是负控重跑结果**：

| 负控 | 实际首先验证到的层次 |
|---|---|
| 恢复朴素前缀 | 前提门 **618** 红；双向门 **783** 红于“自己的表没删”。自愈 overlap 隔离门可以仍绿 |
| V 打空／仅含 active | 双向门先在 **744** 的成员前提红，尚未执行四个隔离场景 |
| 恢复尝试数并吞异常 | 记账门先在 **862** 红：得到 3，预期 2；尚未到 **867** 的失败列表断言 |
| NC19：helper 恒 True | default drop 门 **1459** 红于出现拒绝记录 |
| NC20：自愈 `scoped` 恒 True | default heal 门 **1491** 红于自己的 `notes` 未处理 |

三类变异可以通过红点组合区分，但“全部直接打中各自声称的隔离／记账层”不成立。当前错误日志调用确实存在，记账门没有单独锁住日志输出。

## ⑤ 消费方与计数边界

静态检索未发现额外生产消费方，仍只有 `endpoints/index.py` 和 `g29_dual_vault_canary.py`。

“实删数”的精确定义是**未抛异常的 `drop_table` 调用数**：由于使用 `ignore_missing=True`，表若已被并发删除，本次仍可能计数。因此它比原来的尝试数准确，但不是数据库层证明的“由本次实际删除数”。
