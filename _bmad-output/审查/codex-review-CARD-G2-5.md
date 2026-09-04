# Codex 审查存档 — CARD-G2-5 索引 journal 命名空间

> 批次: BATCH-2026-08-29-第七批 · 车道 V5
> 模型: `codex exec --sandbox read-only -m gpt-5.6-sol -c model_reasoning_effort="ultra"`
> 审查锚点: card/v5-lance @ 9c366d27（G2-4 已提交），只看相对 HEAD 的 diff 与未跟踪文件
> 停轮规则（第六批手册 §二）: BLOCKER/HIGH → 再一轮; MEDIUM/LOW → 登记结案

---

## Round 1（2026-08-31，判 FAIL: 0 BLOCKER / 4 HIGH / 6 MEDIUM / 2 LOW）

> 本轮全程冻结改动（G2-4 的教训），Codex 未再报告工作区并发修改。

总评：**CARD-G2-5 当前应判 FAIL，暂不建议合并**。审查锚点为 `card/v5-lance @ 9c366d27af0d`，仅检查相对 HEAD 的 diff 与未跟踪文件。结论为：**无 BLOCKER，4 项 HIGH、6 项 MEDIUM、2 项 LOW**；目标状态是 `(a) PARTIAL / (b) FAIL / (c) 受限 PASS / (d) PARTIAL / (e) FAIL`。正常、唯一且不过长的 vault key 下，A/B 隔离和原恢复算法成立；但隔离件可覆盖、Linux 长 Unicode key 会让持久化静默失效、旧测试会改真实运行状态，并且盘点与“60 秒收敛”结论存在实质错误。

## BLOCKER

核对过，未发现 BLOCKER。

## HIGH

### 1. 隔离件会覆盖已有时间戳备份，旧 delete 意图可不可逆丢失

- **结论**：不满足并发/幂等隔离要求。
- **证据**：[vault_state_paths.py:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:93) 只检查基础 `.pre-g25.bak`；存在时生成秒级时间戳，随后第 98 行直接 `Path.rename()`，不检查该时间戳目标。迁移器在 [migrate_index_journals_g25.py:113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/migrate_index_journals_g25.py:113) 只验证新源 hash，发现不了旧备份被覆盖。
- **复现场景**：临时目录预置基础备份和当前秒的时间戳备份，调用隔离后，实测时间戳文件从 `OLD-STAMPED` 被覆盖成 `NEW-DELETE`，源文件消失。当前工作区恰好同时存在 fixed legacy 和基础备份，下一次恢复必走该分支。
- **修法建议**：使用真正的 no-replace 发布与冲突重试；Linux 可用 `renameat2(RENAME_NOREPLACE)`，可移植方案需 `O_EXCL` 创建、同 FD hash 校验、`fsync` 文件和父目录后再删除源。随机后缀只能降低概率，不能替代 no-clobber。

### 2. 既有恢复测试会改名真实 `backend/app/data` journal

- **结论**：当前改动引入了测试对真实运行状态的写副作用。
- **证据**：新副作用位于 [vault_index_orchestrator.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:307) 和 [lancedb_index_service.py:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:211)。既有测试只改 `_pending_file`，未改新增的 `_legacy_pending_file`，例如 [test_rag_stage1_index_contracts.py:117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/regression/test_rag_stage1_index_contracts.py:117)、[test_story_38_1_ac3_startup_recovery.py:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_story_38_1_ac3_startup_recovery.py:42) 及两个 Story 38.7 integration 用例。
- **复现场景**：当前真实目录存在 10,435-byte 的 `vault_index_pending.jsonl`。在隔离副本运行 RAG-S1 恢复测试，测试 PASS，同时副本的真实 `app/data/vault_index_pending.jsonl` 被改名为时间戳备份；原工作区因此没有直接运行这些旧测试。
- **修法建议**：构造器注入统一 `state_dir`，让 working/legacy 两路径不可拆分；修齐所有调用 `recover*()` 的 fixture，并先断言两路径均位于 `tmp_path`。

### 3. Linux/Docker 下长 Unicode vault key 会让 durable 写入失败，但调用方仍收到成功

- **结论**：支持的生产平台存在静默丢失 pending 意图的条件性缺陷。
- **证据**：[config.py:1017](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/config.py:1017) 与第 1046 行按“字符数”截到 200；[vault_state_paths.py:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:63) 不限制最终 basename 字节数。仓库使用 [Dockerfile:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/Dockerfile:5) 的 Linux slim 镜像。orchestrator 在 [vault_index_orchestrator.py:289](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:289) 吞掉持久化错误，但 `enqueue()` 仍返回 `accepted`；LanceDB 在第 413–419 行同型。
- **复现场景**：200 个 CJK 字符产生的 `vault_index_pending__<key>.jsonl` 是 **627 UTF-8 bytes**，超过 ext4/overlayfs 常见 255-byte `NAME_MAX`，写入报 `ENAMETOOLONG`。macOS/APFS 本机可创建，因此这是明确的 Linux/Docker 条件性失败。
- **修法建议**：对完整 basename 和 `.tmp` 名按 UTF-8 字节预算；采用短可读前缀加稳定 digest，并对 ASCII、CJK、组合字符、emoji 做 Linux 门测试。持久化失败必须向调用者返回失败状态。

### 4. “约 60 秒必收敛”的告警与盘点结论不实

- **结论**：旧 journal 被隔离后的语义损失可能永久存在，而非统一的 60 秒窗口。
- **证据**：失实声明出现在 [vault_state_paths.py:81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:81)、[migrate_index_journals_g25.py:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/migrate_index_journals_g25.py:16) 和 [盘点文档:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/G2-5-后端全局状态文件盘点-2026-08-31.md:43)。LanceDB journal 在 [lancedb_index_service.py:398](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:398) 只保存 `canvas_name`，不存在周期反熵；RAG 扫描只处理当前部署 vault。
- **复现场景**：A 的旧 LanceDB 失败项在 B 下被隔离，之后该 Canvas 不再变化，则没有入口重新索引。A 的 delete 在 B 下隔离时，B 的扫描也不可能清理 A 的表；只有未来重新启动 A 且 orchestrator 健康时才可能收敛。
- **修法建议**：区分两种 journal。RAG 只能承诺“所属 vault 再次启动且扫描健康后收敛”；LanceDB 应明确要求 Ops 判归属或对已知 vault 做安全全量重建。

## MEDIUM

### 5. 隔离仅在 `recover*()` 懒触发

- **结论**：严格的“升级后旧件已隔离”条件未做到。
- **证据**：两处 persist 均不会先隔离；隔离只在上述 `recover()`/`recover_pending()` 中执行。
- **复现场景**：服务被禁用，或直接实例化后未调用 recover 就先 persist，新 namespaced 文件会生成，但旧 fixed journal 原地保留、无 warning；旧版本回滚仍可能加载它。
- **修法建议**：把隔离放进独立于 feature flag 的统一启动迁移阶段，或把迁移器 `--apply` 设为升级硬门。正常 lifespan 的当前顺序已核对正确。

### 6. CARD-G2-5 行为测试有三个可机械证明的“死门”

- **结论**：`10 passed` 不能证明部署 key、Lance runtime 隔离及真实恢复均成立。
- **证据**：
  - [test_g25_journal_namespace.py:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:98) 只在 hostile ContextVar 下测 helper，不实例化两个服务；
  - 第 180 行只测试 orchestrator 的 legacy 入口；
  - 第 165 行的 Lance A 恢复只检查返回计数，没有断言 `_do_index_with_retry` 的调用和 journal 消费。
- **复现场景**：在隔离副本中：

  1. 将两个服务改为从 `current_vault_id()` 取 ContextVar，仍 `10 passed`；
  2. 删除 LanceDB runtime quarantine，仍 `10 passed`；
  3. 不索引、只删除文件并返回 `recovered=1`，仍 `10 passed`。
- **修法建议**：在 hostile ContextVar 存续期间构造两个服务；补 Lance legacy 真实入口测试；断言 Lance 恢复函数调用参数、次数及文件删除。

### 7. 迁移 census 漏掉旧 `.jsonl.tmp`

- **结论**：dry-run 可对真实 crash residue 误报 clean。
- **证据**：[migrate_index_journals_g25.py:72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/migrate_index_journals_g25.py:72) 只识别 canonical `.jsonl`；[vault_index_orchestrator.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/vault_index_orchestrator.py:291) 确实会产生 `vault_index_pending.jsonl.tmp`，而 `.gitignore` 又会隐藏它。
- **复现场景**：目录仅留下含 delete 的旧 `vault_index_pending.jsonl.tmp`，dry-run 返回 0，apply 也不报告或隔离。
- **修法建议**：把 legacy/namespaced tmp 单列为 crash residue；旧无维度 tmp 改名隔离、不加载，并加入报告和测试。

### 8. §三不是完整的后端全局文件盘点

- **结论**：目标 `(e)` 未完成。
- **证据**：[盘点文档:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/G2-5-后端全局状态文件盘点-2026-08-31.md:63) 宣称逐一裁定，但至少漏掉：
  - [guardian.py:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/audit/guardian.py:28) 的 `backend/logs/audit.jsonl`；
  - [memory_system_logger.py:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/memory_system_logger.py:34) 的 `memory-system-*.log`；
  - [notification_channels.py:119](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/notification_channels.py:119) 的 `logs/alerts.log`；
  - 可写的 `rag_config.yaml` 与 `subject_mapping.yaml`。
- **复现场景**：按所有固定路径和写 API 做 `rg`，上述写入方均存在，但表中没有对应 A/B/C 裁定。
- **修法建议**：从所有 `open(...,"a"/"w")`、`write_text`、SQLite connect 和默认路径机械生成 census；配置可以判 B，日志也可以判 B，但必须逐项说明敏感字段、vault 标识、访问和保留策略。

### 9. `bug_log` 与 `dead_letter_episodes` 的 B 豁免理由不成立

- **结论**：把含 vault 用户数据的全局文件说成“与 vault 无关/纯观测件”不诚实。
- **证据**：[盘点文档:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/G2-5-后端全局状态文件盘点-2026-08-31.md:87) 至 88 行。`bug_log` 在 [bug_tracker.py:138](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/bug_tracker.py:138) 持久化 `request_params`，异常处理器还会放入 query/body；episode dead-letter 的 [EpisodeTask.to_dict():105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/episode_worker.py:105) 始终保存正文前 200 字符，且可选保存完整正文。
- **复现场景**：vault A 请求体含路径或节点内容并触发 500/episode 失败，数据进入全局文件；切到 B 后文件仍存在，trace 读取也没有 vault 过滤。
- **修法建议**：至少改判 C；若坚持集中日志 B 豁免，必须增加 vault_id、脱敏、访问控制、保留期及跨 vault 查询规则，不能继续写“与 vault 数据无关”。

### 10. 盘点含多个可复现事实错误

- **结论**：当前盘点不能作为清理或排卡依据。
- **证据**：
  - [盘点文档:92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/审查/G2-5-后端全局状态文件盘点-2026-08-31.md:92) 将 28KB `review_data.db` 称为现网文件；当前仓库唯一命中是 28,672-byte 的 `backend/tests/integration/data/review_data.db` 测试夹具，当前容器 `/app/data` 无该文件；
  - 第 75 行把 outbox 放在 `backend/app/data`，实际由 [event_bus.py:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/event_bus.py:47) 写到 `backend/data/outbox`；
  - 第 104 行称 C=9，逐行机械计数实际为 C=10。
- **复现场景**：`find backend -name review_data.db` 仅返回测试夹具；按三张表逐行计数即可复现。
- **修法建议**：删除/纠正 `review_data.db` 生产结论，记录容器身份与证据时间；路径和合计由脚本机械生成。

## LOW

### 11. 新测试没有锁生产目录计算

- **结论**：测试只锁 basename，确实绕过了 production parent。
- **证据**：[test_g25_journal_namespace.py:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:63) 至 77 行无条件替换 parent。
- **复现场景**：把两个服务的 `_data_dir` 改为 `/definitely-wrong-production-state-dir`，CARD-G2-5 仍 `10 passed`。
- **修法建议**：替换前先断言原 parent 精确等于模块相邻的 `app/data`；更好的是构造器显式注入 `state_dir`。

### 12. census 匹配过宽，stat 异常也可能静默

- **结论**：异常文件可被错误标成 clean/quarantined，路径不可 stat 时也没有要求的 Ops warning。
- **证据**：[migrate_index_journals_g25.py:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/migrate_index_journals_g25.py:69) 把任意含 `.pre-g25.bak` 的文件归为隔离件，并接受空 key 的 `vault_index_pending__.jsonl`；[vault_state_paths.py:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:87) 把 stat `OSError` 当不存在且不告警。
- **复现场景**：放入 `unrelated.pre-g25.bak` 或空 key 文件，报告仍视作合法类别。
- **修法建议**：限定两个 stem、严格验证非空 canonical key，并把异常项单列；只对 `FileNotFoundError` 返回 None，其他 `OSError` 必须 warning/error。

## 核对过，未发现问题

- `(a)` 正常路径确实从 `get_settings().vault_id` 取部署身份，不读 per-request ContextVar；两个服务当前实现均调用该 helper。
- `sanitize_vault_id` 不会产出路径分隔符或 `__`。`CS 61B` 与 `cs-61b` 会碰撞为 `cs_61b`，共享 journal 的后果已在 [vault_state_paths.py:45](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:45) 和 UAT 中诚实登记。按“`settings.vault_id` 即逻辑身份”的卡文不另判新缺陷；若要求不同物理目录无条件隔离，则该残余应升级为 HIGH。
- 成功隔离路径会 rename、warning 且不加载；普通 rename 失败会保留源并继续拒绝加载。目标与源同目录，正常路径不存在跨设备 rename。
- 正常 production 时序正确：LanceDB 在 lifespan 开放请求前恢复；orchestrator `start()` 先 recover 再启动 worker。
- A 写两条 delete → B `recover()==0` → A 字节不变 → A `recover()==2` 已通过；LanceDB A/B 同型通过。CARD-G2-5 目标测试为 **10 passed**。
- Story 38.1 在隔离副本中 8 unit + 2 integration 为 **10 passed**；RAG-S1 `in_flight → pending` 为 **1 passed**。除 namespace/quarantine 前置动作外，两套恢复算法未改，未发现 namespaced journal 的既有语义回归。
- 默认迁移 dry-run 实跑为 `pending=1 / exit 2`，无 `--out` 时零写入；真实 journal 的大小、mtime、SHA 及 `git status` 前后不变。
- `.gitignore` 覆盖实际 canonical、新 namespaced、RAG `.jsonl.tmp`、基础及时间戳备份；LanceDB 当前实现不生成 `.tmp`。
- 全仓生产调用点扫描未发现其他 endpoint/service 继续把旧 fixed 文件名作为工作 journal 读写。
- 盘点中以下裁定独立抽查正确：`canvas_events_fallback.json` 为 C、`qa_metrics.db` 为 C、`learning_events.jsonl` 天然随 vault 为 B、board manifest 天然随 vault 为 B、`reference_priority.json` 为配置 B。
- 全量 CI 未运行：直接跑部分既有 recovery 测试会触发 HIGH-2 的真实状态改名。本轮未读取真实 journal 正文，也未修改工作区。


