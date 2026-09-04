# Codex 审查存档 — CARD-G2-4 Lance 旧表回退删除

> 批次: BATCH-2026-08-29-第七批 · 车道 V5
> 模型: `codex exec --sandbox read-only -m gpt-5.6-sol -c model_reasoning_effort="ultra"`
> 停轮规则 (第六批手册 §二): BLOCKER/HIGH → 再一轮; MEDIUM/LOW → 登记结案

---

## Round 1 (2026-08-31, 判 FAIL: 3 BLOCKER / 3 HIGH / 6 MEDIUM / 2 LOW)

> ⚠️ 审查期间工作区仍在改动 (我在等审查时补了 multimodal 守卫), Codex 明确声明
> 其结论基于最终稳定快照。教训: 发起审查后应冻结改动。

总评：**FAIL / BLOCKED，不可合并，更不可执行 `--apply`**。CARD-G2-4 的在线主链 `(a)–(d)`大体成立：B0.7 与 tier-2 裸表路径已删除，单实例窄映射保留，表缺失能在 supplementary 链路透出 `unavailable`。但归档器 `(e)` 存在两个可导致生产数据删除/归档副本消失的 BLOCKER；另有现有 SHA 契约红测。`136` 个定向测试全绿、grep gate `rc=0`，仍不足以推翻以下真库反例。

审查期间工作区发生过并发修改，新增了 `multimodal_store.py` 补丁、对应测试和 UAT；以下结论基于最终稳定快照。

## BLOCKER

1. **现网 `--apply` 拒绝闸可被 `file://` 双解释绕过。**  
   证据：[archive_legacy_lance_tables_g24.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:95)、[同文件:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:229)。  
   复现场景：临时“live”库写入裸 `vault_notes`，以 `file://<live-path>` 传入，并在 cwd 构造 `Path(uri)` 所见的诱饵目录。实测 `targets_live_store=False`、`main rc=0`，真实源表被 drop，只剩 archive。安全闸按普通路径解释，`lancedb.connect()` 却按 URI 解释。  
   修法：拒绝所有 scheme，或严格解析 `file://` 后只生成一次 canonical plain path，并把同一路径同时交给 guard 和 connect；`--apply` 最好要求正向证明“隔离副本”，而非 live denylist。

2. **归档副本会被正常客户端启动时再次删除，最终源表和归档表都消失。**  
   证据：[archive_legacy_lance_tables_g24.py:183](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:183)、[lancedb_client.py:927](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:927)、[同文件:3584](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:3584)。  
   复现场景：真临时库中归档一张缺 `doc_type` 的旧 `vault_notes`；归档后仅剩 `_g24archive__vault_notes__T`，随后运行真实 `LanceDBClient._cache_tables()`，表清单变为 `[]`。启动 schema repair 不认识 archive 前缀，直接 drop。现有 fixture 刻意带 `doc_type`，且未模拟重启。  
   修法：优先归档到 DB 外的 Arrow/Parquet + manifest；若必须同库保存，所有启动缓存/schema repair 必须排除 `ARCHIVE_PREFIX`，并新增真实重启生存测试。

3. **修改 `vault_doc_roles.yaml` 后未更新强制双文件指纹。**  
   证据：[vault_doc_roles.yaml:332](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/vault_doc_roles.yaml:332)、[check_vault_doc_roles.py:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/check_vault_doc_roles.py:98)。  
   复现场景：脚本常量仍是 `e5a02e…`，工作区 YAML 为 `2a68d4…`；`test_fingerprint_contract` 在 setup 直接报 `ConfigError`。  
   修法：按脚本命令刷新 `ROLES_SHA256`，并完整重跑 `test_vault_doc_roles.py`。

## HIGH

1. **hash/count 对账能把不同类型/schema 判成相同，再删除源表。**  
   证据：[archive_legacy_lance_tables_g24.py:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:134)、[同文件:196](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:196)。  
   复现场景：`{"x": 1}` 与 `{"x": "1"}` 的指纹实测完全相同，因为所有值先被 `str()`；apply 又不比较 schema。测试在 [test_archive...py:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:147) 复用同一弱 oracle，故会假绿。  
   修法：使用 Arrow schema、类型化值和 null bitmap 计算摘要；比较完整 schema/metadata，并用独立测试 oracle。

2. **归档器未复用应用的 canonical vault-id，可能误删单实例正常裸表。**  
   证据：[archive_legacy_lance_tables_g24.py:90](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:90)、[app/config.py:765](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/config.py:765)、[同文件:1020](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/config.py:1020)。  
   复现场景：`ACTIVE_VAULT=Default` 经应用 sanitize 后是 `default`，但脚本按原字符串判 `single_vault=False`；实测 `--apply` 会归档并 drop 正常裸 `vault_notes`。  
   修法：调用同一 resolver/sanitizer；raw 与 canonical 不一致时 fail closed。覆盖大小写、空白、全角字符等测试。

3. **归档分类白名单漏掉实际受旧 B0.7 影响的生产表。**  
   证据：[archive_legacy_lance_tables_g24.py:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:63)、[tool_executor.py:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/tool_executor.py:114)。  
   复现场景：临时库只建裸 `canvas_explanations`、active vault=`v1`，实测分类为 `unknown`、`pending=[]`，工具错误地 exit 0。`edge_rationales` 也需单独裁定。  
   修法：从中央表名契约生成完整策略；无法确认归属的裸表应进入 `manual_pending` 并 exit 2，而非报 clean。

## MEDIUM

1. **`_is_table_absent` 只看目录前 10 张表。**  
   证据：[lancedb_client.py:794](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:794)。当前 LanceDB 0.30.2 的无参 `table_names()` 默认 `limit=10`。  
   复现场景：真库创建 `a00..a09` 和 `z_vault_notes`；完整目录含目标，但 `_is_table_absent("z_vault_notes")` 返回 `True`。若后页表存在但临时打不开，会被误诊为“未建表”。  
   修法：使用 `list_tables(limit=None)` 或完整分页；增加 11+ 表反例。该 API 同时已弃用，未来移除时当前 catch 会再次把诊断塌缩。

2. **所谓 vector-only 回退实际又运行一次 hybrid，测试是假绿。**  
   证据：[supplementary_search_service.py:874](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/supplementary_search_service.py:874)、[test_supplementary_search_service.py:1073](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_supplementary_search_service.py:1073)。  
   复现场景：使用生产默认签名，调用序列实测为 `["hybrid", "hybrid"]`；第二次没有 `query_type="vector"`。fake 用 `kwargs.get()`，错误地把缺参当成 vector。  
   修法：第二次显式传 `query_type="vector"`，测试严格断言第二次值。

3. **并发新增的 MultimodalStore 修补在生产客户端上不可达。**  
   证据：[multimodal_store.py:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/lib/agentic_rag/storage/multimodal_store.py:211)、[同文件:248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/lib/agentic_rag/storage/multimodal_store.py:248)、[test_g24...py:289](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g24_lance_legacy_table_removal.py:289)。  
   复现场景：生产 `LanceDBClient.search()` 不接受 `query_vector/filter/limit`；真客户端调用 `store.get()` 得到 `TypeError: unexpected keyword argument 'query_vector'`，根本到不了 `TableMissingError` catch。fake 的 `search(**kwargs)` 掩盖了签名错位。  
   修法：建立明确适配层，并用真实 client/生产签名测试。

4. **typed missing 仍会在其它生产 wrapper 中重新变回健康空。**  
   证据：[lancedb_client.py:3784](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:3784)、[nodes.py:364](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/lib/agentic_rag/nodes.py:364)、[vault_notes_retriever.py:245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/lib/agentic_rag/retrievers/vault_notes_retriever.py:245)。  
   复现场景：真实空临时库调用 `search_multiple_tables(["canvas_nodes"])` 返回 `[]`，未向 `nodes.py` 的 outer catch 传播，因而不会写 `channel_errors`。VaultNotesService 同样 broad-catch 后返回 `[]`。  
   修法：记录每表成功/失败；无一成功且出现 `TableMissingError` 时重新抛出，有部分成功则显式 degraded。

5. **dry-run 与多表 apply 的安全骨架不完整。**  
   证据：[archive_legacy_lance_tables_g24.py:260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:260)、[同文件:266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:266)。  
   复现场景一：`--out <db-root>/evidence.json` 时 dry-run `rc=2`，但 DB 树已新增文件。复现场景二：多张裸表逐张复制后立即 drop；第一张成功、第二张失败会留下部分执行且可能没有完整报告。  
   修法：拒绝 out 位于 DB 树内；apply 改为“两阶段全部复制/核对成功后统一 drop”，或提供 journal/resume。

6. **grep gate 的自检仍不能阻止 fail-open。**  
   证据：[g24_grep_gate.sh:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/g24_grep_gate.sh:47)、[同文件:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/g24_grep_gate.sh:97)。  
   复现场景：真实扫描路径不存在/无权限时 stderr 与 rc 被丢弃，空输出仍判 0 命中；G2 只抓精确双引号，单引号、空白或变量调用可绕过；G3 用“行号大于 class 起点”冒充类范围。首次受限运行中 `mktemp` 失败后脚本还尝试写 `/control.txt`，也证明失败处理不完整。  
   修法：目标逐一验证存在/可读，grep `rc>1` 判红；用 AST 检查调用；`mktemp` 失败立即退出并用 trap 清理。

## LOW

1. **React agent 的缺表诊断退化。** [react_agent.py:99](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/react_agent.py:99) 会把 `TableMissingError` 当普通 RuntimeError，再查同一缺失表一次，最终返回 generic `[Error]`，原本的“尚未索引”提示不可达。建议 typed catch 先行并直接提示建索引。

2. **旧名/旧字段未完全清理。** [chat.py:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/api/v1/endpoints/chat.py:74)、[note_search_tools.py:189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/mcp/tools/note_search_tools.py:189)、[同文件:286](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/mcp/tools/note_search_tools.py:286) 仍引用 `_two_tier_search` / `is_legacy_fallback`。无当前生产者，但不满足“清干净”和 DD-13 文意一致。

## 已核对、未发现问题

- `(a)` B0.7 条件回退已真正删除；`default`/空字符串仍返回裸表，真实读写正向对照通过，未发现单实例主路径回归。
- `(b)` `search()` 中 `TableMissingError` 位于 catch-all 前并能穿透 `enable_fallback`；普通异常仍返回 `[]`。但分页和 wrapper 再吞问题见上，故整体为 **PARTIAL**。
- `(c)` `search_supplementary` 的捕获顺序正确，返回 `degraded=True`、`status=unavailable`、非空且带表名的 reason，并复用了 `ServiceStatus`。
- `(d)` supplementary 的 tier-2 直开分支和 env helper 已删除，函数已改名；把旧 env 设为 true 也不会访问 `client._db`。生产代码/配置未发现该 env 残留；仅有上述 stale 注释/字段和 grep gate 强度问题。
- `(e)` 普通 dry-run（out 不落入 DB）当前只调用读 API；精确 `/lancedb`、当前 `LANCEDB_DATA_PATH`、稳定相对路径和稳定 symlink 能被拒绝。但 URI/别名、归档生存性和弱对账使本项 **FAIL**。
- `note_search_tools` 能把 supplementary unavailable 转成 `source_status=error`；tool executor、agent graph、cross-canvas 与 multimodal retriever未发现新增未捕获异常。
- 最终验证：六个定向套件 `136 passed`；grep gate `rc=0`；`git diff --check` 通过。`test_lancedb_vault_isolation.py` 的钉死用例 `:23/:35` 通过；全文件仍有 3 个配置耦合失败，未落在本卡改动 hunk。
- 限制：当前环境未提供 `graphiti-canvas`，故未执行仓库规定的 Graphiti 查询；本审查未访问或修改现网数据，也未修代码。


