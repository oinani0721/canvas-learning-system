> 批次: BATCH-2026-09-11-第十四批 · 车道 T1 · 卡 CARD-G2-9-F2 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F2-r2.md)"`
> 审查绑定: `08100483..ab249816`（该轮送审时的 HEAD；本卡末轮 r5 绑最终 HEAD `647ef77f`）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

**本轮不建议判定闭合：3 HIGH、2 MEDIUM 本卡发现，另有 1 MEDIUM 接口移交、1 LOW。BLOCKER：该级别无。**

已核对 `HEAD=ab249816`、分支 `card/t1-lance`，两个目标文件与绑定提交一致。以下基于源码和提交差异；未修改文件，未连接数据库或网络，未运行 pytest、canary 或数据库负控。

[HIGH] HIGH-1 仍未闭合，而且部分目录缺项会完全绕过新增降级告警。  
  `backend/lib/agentic_rag/clients/lancedb_client.py:922, 945, 950, 961, 1103`  
  复现思路：已有 `a_b_canvas_nodes`、没有对应指纹表；移走 `a_b` 目录但保留正常可枚举的根目录，V 只剩 `a`，该表重新归 `a`，且 `_vault_registry_degraded` 仍为 `False`。

具体边界如下：

- **根目录不可达或扫描抛错**：设置降级标志，但没有消费该标志来阻止删除。
- **单个目录移走、变隐藏或失去 `.obsidian/`**：正常扫描直接漏项，不设置降级。
- **YAML 正常声明不同 ID**：处理正确，与 `Settings.vault_id` 的显式配置优先级一致。
- **YAML 损坏、读失败或 ID 改名**：退回目录名或采用新 ID；旧 ID 的无指纹存量表失去保护，且可能静默。
- **尚无表的 vault**：只要目录满足候选规则，仍进入 V。
- **指纹来源列举失败**：只记 debug，返回空集。

因此，“登记移交＋日志”没有闭合删除面。较低成本的**局部闭合**是：来源明确失败时，在本文件内停止破坏性操作；这不需要限制可删除的逻辑表名，不会打红正常目录下的填充表正向对照。目录静默消失后的冷启动场景仍需额外归属证据。

[HIGH] 五秒 TTL 会继续使用已经失效的缺项集合，旧表即可触发，无需新建 vault 完成索引。  
  `backend/lib/agentic_rag/clients/lancedb_client.py:1035, 1040, 1056`  
  复现思路：同一连接在根目录短暂不可达时缓存 `V={a}`，随后目录恢复，原有 `a_b_canvas_nodes` 一直存在；五秒内删 `a`，缓存直接命中，仍会认领该旧表。

这与上一项不同：**来源已经恢复，保护仍未恢复**。连接 ID 没变，所以 HIGH-2 的连接键整改挡不住。作者“窗口内不可能已有表”的前提不成立；代码也没有保证索引至少耗时五秒。

[HIGH] 最长规则会让短 vault 丢失自己的指纹归属，造成删除内容后普通增量索引无法恢复。  
  `backend/lib/agentic_rag/clients/lancedb_client.py:1111, 1213, 1415, 1517, 2184, 2207`  
  复现思路：V 为 `{a, a_file}`，其中 `a_file` 可以只是空 vault；`a` 已有 `a_vault_notes` 和 `a_file_fingerprints`，删除 `a` 会删内容、留指纹，随后未修改文件的普通增量索引全部判为 unchanged，返回 0。

**这是相对 B14 的新增回归**：基线删除 `a` 会同时清掉内容和指纹，随后文件会被当作新文件重建。它不能用“长 vault 以前也能误删这张表”抵消。

“并入被询问 ID”只能保证新认领集合不超出旧前缀集合，不能保证真主人不失去自己的表；“少认领不会影响数据”的业务结论也不成立。较小的防护是检测到目标规范指纹名冲突时，在首次删除前整次拒绝，避免内容与指纹被拆开处理。

[MEDIUM] MEDIUM-5 的生产修复部分成立，但两处新增分页验证仍未覆盖声称的失效状态。  
  `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:473, 529, 675, 687`  
  复现思路：分别只把 `list_vault_tables` 或 `_fingerprint_table_exists` 退回默认十张枚举，当前相关门仍可通过。

原因分别是：

- drop 夹具只有十张自己的填充表 `a_00..a_09`，它们**全部在第一页**；页外唯一一张属于 `a_b`，本来就应保留。因此漏掉页外扫描，仍满足 `own_left` 为空、`dropped == 10`。
- 指纹读回发生在十张填充表删除之后，此时库里只剩指纹表，旧的默认分页也能找到它。

门③能锁住启动自愈的分页，不能替代对 `list_vault_tables` 的独立验证。`_all_names()` 自身显式使用 `limit=10_000`，断言读回没有默认十张问题。

[MEDIUM] 新增错误日志在 Loguru 分支下丢失实际 vault、表名、路径及异常参数。  
  `backend/lib/agentic_rag/clients/lancedb_client.py:51, 955, 971, 1128, 1267`  
  复现思路：启用 Loguru 后触发目录失败、命名碰撞或删除失败，消息中的 `%s/%r` 不会按 logging 风格插入位置参数。

`_last_drop_failures` 内保存的内容仍正确，但新增门没有检查日志内容。此项为静态格式契约判断；当前审查用虚拟环境未安装 Loguru，未完成动态验证。

[MEDIUM] 接口仍把“全部删除失败”描述成“没有表”，部分失败也不向调用方暴露——作为接口移交。  
  `backend/app/api/v1/endpoints/index.py:107`  
  复现思路：所有匹配表删除均抛异常，客户端返回 0，端点返回 404、文案为 `No tables found`；部分失败则返回 200，仅报告成功数。

仓内搜索未发现第三个生产消费方：只有该端点与 `g29_dual_vault_canary.py:783`。canary 的整数消费仍兼容，其“尝试数”注释已过时。按你的地盘边界，此项不升为本卡 HIGH。

[LOW] “固定字符串 grep 为 0”“helper 仅供幂等”及部分规则说明与绑定 HEAD 不符。  
  `backend/lib/agentic_rag/clients/lancedb_client.py:1075, 1111, 1179`  
  `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:44, 608`  
  复现思路：查固定子串 `startswith(f"{vid}_")`，当前命中第 1075 行，计数是 **1**；`_table_owner` 也在第 1111 行调用该 helper，而部分说明仍保留已经删除的 `t == v`。

**命名幂等与完整归属判定的区分成立**；最长匹配内部使用前缀判断也合理。失去证明力的是该字面 grep 判据，不能拿它证明归属闭合。

其余整改结论：

- **HIGH-2 原场景已闭合**：未连接时不缓存；首次连接或单次连接对象替换会重算。`id()` 在旧对象释放、多次替换后仍可能复用，但未确认实际生产重连链，不作为已复现 HIGH。
- **HIGH-3 已闭合**：删除 `name == vid` 不会使当前命名器生成的该 vault 真表无人认领；`a` 的逻辑表 `b` 生成 `a_b`，仍归 `a`。
- **HIGH-4 幂等回归已闭合**：存量已解析名不会新增双前缀。生产确有 `index_vault_notes:2109 → add_documents:2331 → resolve:4143` 的二次解析。`a` 传入 `a_b_*` 仍原样返回，属于基线既有行为；“不可解”过强，可以拒绝歧义访问，但不能将其再次算作本轮新增幂等回归。
- **default／三态保持**：`_owns_table:1197–1199` 保留既有分支，跳过候选 `"default"` 不会使裸表变全表或恒空。含下划线裸业务表原有的无人认领问题仍属既有边界。
- **指纹全量枚举生产改动正确**：影响 `_get_all_fingerprints`、`_update_fingerprint`、`_remove_fingerprint`，未发现新增功能回归；测试覆盖不足如上。

三段负控的**首个相关红点**可从断言顺序区分，但不能扩大解释为每层均已独立验证：

| 负控 | 源码推导的红点 | 证明边界 |
|---|---|---|
| 退回朴素前缀 | 前提门 `:614`；综合门通过集合前提后在 `:749` 红 | 综合门确实到达自愈消费路径 |
| V 置空／仅 active | 综合门 `:740` | 先被集合前提拦下，尚未执行后续删表场景；独立 cache/drop 门仍可检出后果 |
| 恢复吞异常＋返回尝试数 | 记账门 `:858`，得到 `3 != 2` | 首先验证返回数，尚未触达 `:863` 的失败账本断言 |

以上为负控定义与源码顺序的核对，未采信作者执行记录，也未声称本轮实际运行了这些负控。


