复核结论：两卡均未清零。当前 HEAD 为 `a94caa3d`，提交父链为 `9c366d27 → 4da0116d → a94caa3d`。

## CARD-G2-4 round-2

整改声明见[验收单 §七](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/验收单/UAT-CARD-G2-4-Lance旧表回退删除-2026-08-31.md:327>)。

1. BLOCKER-1 `file://` 双解释绕过 — `CONFIRMED-CLOSED`

   [归档器](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:94)拒绝 `://` 输入，并在 323–351 行将同一个 canonical `Path` 同时交给 live guard 与 `lancedb.connect`。  
   [回归锁](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:177)真实传入 `file://... --apply`，断言 `rc=1` 且 DB 树逐字节不变；有效。

2. BLOCKER-2 同库归档会被启动 schema repair 删除 — `CONFIRMED-CLOSED`

   [实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:280)导出 DB 树外 Parquet、回读核对，并在 331–340 行拒绝 DB 树内归档目录。  
   [回归锁](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:344)实际调用生产 `_cache_tables()`；正向对照表确被 schema repair 删除，而外置 Parquet 及摘要仍存活；有效。

3. BLOCKER-3 YAML/脚本 SHA 脱钩 — `CONFIRMED-CLOSED`

   [脚本常量](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/check_vault_doc_roles.py:98)为 `2a68d4cd…`，独立计算 YAML exact bytes 得到完全相同 SHA。  
   [回归锁](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_vault_doc_roles.py:227)同时锁当前 SHA、CLI 输出及篡改一字节必须退出 2；有效。

4. HIGH-1 弱摘要可把不同 schema 判同 — `STILL-OPEN`

   [当前摘要](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:236)只包含字段名、类型和 nullable，遗漏 `Schema.metadata` 与 `Field.metadata`；删除前对账在 290–295 行直接依赖该摘要。  
   最小反例：同一 `x:int64` 数据，仅 schema metadata 不同，结果 `schema.equals(check_metadata=True)=False`，但 `_arrow_digest` 完全相同。  
   [现有测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:131)只锁 `1` 与 `"1"`，未锁 round-1 明示的完整 schema/metadata。

5. HIGH-2 未复用应用 canonical vault-id — `CONFIRMED-CLOSED`

   [实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:115)强制导入应用 `sanitize_vault_id`，失败即拒绝；328–330 行使用 canonical 值判断单实例。  
   [回归锁](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:154)覆盖 `Default`、`DEFAULT`、带空白输入，均断言 canonical=`default`、pending 为空；有效。

6. HIGH-3 漏表及 unknown 被报 clean — `CONFIRMED-CLOSED`

   [表名契约](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:73)已纳入两张原漏表；139–152、270–274 行将未知表纳入 `unknown_bare` pending。  
   [回归锁](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:108)真实运行 `main()`，断言未知表进入 pending 且 dry-run `rc=2`；有效。

**BLOCKER/HIGH 清零：否**（HIGH-1 仍开）。

## CARD-G2-5 round-2

整改声明见[验收单 §七](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/验收单/UAT-CARD-G2-5-索引journal命名空间-2026-08-31.md:161>)。

1. HIGH-1 隔离件覆盖已有备份 — `CONFIRMED-CLOSED`

   [实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:115)以 `O_CREAT|O_EXCL` 原子抢占唯一名；198–220 行仅替换自身占位，失败时清占位、保留源文件。  
   [回归锁](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:261)预置备份并连续隔离三轮，断言每份历史内容均存活；能击中原同秒覆盖缺陷。结论限于原 finding，未扩展到断电/fsync 证明。

2. HIGH-2 旧测试会改名真实 journal — `CONFIRMED-CLOSED`

   两服务支持 `state_dir` 注入：[orchestrator](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:98)、[Lance service](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:54)。legacy 路径均由当前 `_pending_file.parent` 动态派生。  
   [测试辅助及目录断言](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:58)有效；round-1 点名的旧恢复入口另跑 `11 passed`，未触碰真实 `app/data`。

3. HIGH-3 长 Unicode key 导致 durable 写失败却返回成功 — `STILL-OPEN`

   字节预算部分已修：[fs_safe_key](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:56)会把长 key 压缩至安全 basename。  
   但原 finding 的失败反馈仍未修：[orchestrator](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:280)在 `_persist_sync()` 失败只记日志，仍无条件返回 `"accepted"`；[Lance service](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:410)同样吞持久化错误。  
   生产入口反例：令 `state_dir` 指向普通文件，实际得到 `status=accepted`、`journal_exists=False`。  
   [现有回归锁](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:288)只测 helper 和直接写文件，没有构造两个生产服务，也未断言 durable-write 失败必须返回失败；断言不足。

4. HIGH-4 “约 60 秒必收敛”失实 — `STILL-OPEN`

   当前文案已经纠正：[核心说明](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:153)、[迁移器](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/migrate_index_journals_g25.py:16)、[盘点文档](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/G2-5-后端全局状态文件盘点-2026-08-31.md:43>)均正确区分两条 journal。  
   但验收单整改表第 172 行的回归锁明确为 `—`，`backend/tests` 对该口径零命中。按本轮“每条必须有有效回归锁”的闭合标准，当前文本虽正确，证明义务仍未完成。

**BLOCKER/HIGH 清零：否**（HIGH-3、HIGH-4 仍开）。

验证结果：

- G2-4/G2-5 定向门及 SHA 契约：`32 passed`
- G2-5 round-1 点名旧恢复入口：`11 passed`
- 并行扩大 G2-4 套件：`134 passed`
- 未跑全量 CI、未访问现网数据、未修改工作树；既有未跟踪 round-2 文件保持原样。
- 本会话未提供 `graphiti-canvas`，故未执行 Graphiti 查询。
