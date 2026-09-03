结论：**HIGH-4 e③ 仍开；HIGH-3 的原高危竞态已关闭，但有 MEDIUM 残余。**

验证命令实跑结果：`27 passed, 10 warnings in 1.73s`。这只证明定向套件，不代表全量 CI；未重演变异、未修改工作区。

## 逐条判决

1. **HIGH-4 e③ — STILL-OPEN**

   - 三段真实文本当前均正确：quarantine docstring 明确限定当前 vault、Lance 无周期反熵，[vault_state_paths.py:153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:153)、[vault_state_paths.py:161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:161)；migrator 同样正确，[migrate_index_journals_g25.py:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/migrate_index_journals_g25.py:16)、[migrate_index_journals_g25.py:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/migrate_index_journals_g25.py:22)；实际 warning 也含两项限定，[vault_state_paths.py:225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/core/vault_state_paths.py:225)。
   - §9.6 的三项堵口已经实现，九条现有篡改门也全部拒绝，[验收单:424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/验收单/UAT-CARD-G2-5-索引journal命名空间-2026-08-31.md:424)、[test_g25_journal_namespace.py:983](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:983)。
   - 但 helper 只显式要求「只覆盖当前部署」，[test_g25_journal_namespace.py:916](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:916)；「没有周期反熵」仅通过 `finditer` 检查命中后的句子，[test_g25_journal_namespace.py:919](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:919)。当第二短语完全缺失时循环零次，仍会放行。
   - 所谓“缺另一短语”门实际保留了「没有周期反熵」、缺的是第一短语，因此被第 916 行拒绝，没有测试相反方向，[test_g25_journal_namespace.py:987](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:987)。
   - 其他仍可能误放的文本形态包括：把限定短语置于否定或引用语境；使用未枚举的反问词；用未被三支正则覆盖的时间、同步或必然性近义表达；把引用/否定标记与活断言放入相邻窗口但分属不同语义。有限子串和窗口共现不能证明语法极性。
   - 因此：**当前文本正确、九样本全拒绝，但防篡改门本身仍有确定性死门，不能确认 HIGH-4 关闭。**

2. **HIGH-3 — CONFIRMED-CLOSED（原高危主路径）**

   - 普通不同文本的并发 append 已在锁内重读、合并后才 rewrite/unlink，[lancedb_index_service.py:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:268)、[lancedb_index_service.py:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:281)、[lancedb_index_service.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:291)。
   - B1 使用真实 `_persist_pending` 追加不同的 `canvas-new`，并断言新条目和失败条目保留、成功条目消费，[test_g25_journal_namespace.py:754](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:754)、[test_g25_journal_namespace.py:768](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:768)。
   - **MEDIUM 残余：相同行 multiplicity。** `orig_lines` 被压成集合，[lancedb_index_service.py:245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:245)，锁内所有与旧行逐字相同的 occurrence 都被视作残影，[lancedb_index_service.py:285](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:285)。
   - 有害触发还需同时满足：新 append 与旧行字节完全相同；发生在旧 recovery 已无法覆盖新变化的时序；旧项恢复成功；新 occurrence 不是已被成功重建吸收的冗余信号。正常含新时间戳的写入下概率很低，但本次范围内没有“字节必唯一”或“相同记录必可幂等合并”的不变量，因此不能降为纯理论问题。该残余不足以维持原 HIGH，登记 MEDIUM。

3. **e① / B4 — CONFIRMED-CLOSED**

   真跑 `_scan_loop` 并要求 `reconcile` 至少调用两次，空壳变异会红，[test_g25_journal_namespace.py:837](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:837)、[test_g25_journal_namespace.py:847](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:847)。

   但扫描根仍仅靠源码出现 `self.vault_path`，默认周期也只锁声明值，[test_g25_journal_namespace.py:815](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:815)、[test_g25_journal_namespace.py:817](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:817)。注释、文档串或死代码可满足前者；行为探针也未证明 loop 实际使用配置周期。记 MEDIUM 证明缺口，不等同于已证实生产行为错误。

4. **e② — CONFIRMED-CLOSED（已知 0.20s 绕过）**

   recover 后确认隔离件存在、调度表为空，观察 1 秒索引调用仍为零；正向调度恰调用一次，[test_g25_journal_namespace.py:881](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:881)、[test_g25_journal_namespace.py:885](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:885)、[test_g25_journal_namespace.py:896](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:896)。超过 1 秒或其他载体仍只是已披露限制，[验收单:406](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/验收单/UAT-CARD-G2-5-索引journal命名空间-2026-08-31.md:406)。

5. **d② / B2 — CONFIRMED-CLOSED**

   upsert 后以 delete 触发 coalesce 写失败，断言返回 `persist_failed` 且内存 op 仍为 delete，[test_g25_journal_namespace.py:554](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:554)、[test_g25_journal_namespace.py:558](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:558)、[test_g25_journal_namespace.py:561](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:561)。

6. **d③ / B3 — CONFIRMED-CLOSED**

   503、七字段精确集合、聚合计数和逐路径状态均已锁住，[test_g25_journal_namespace.py:590](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:590)、[test_g25_journal_namespace.py:595](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:595)、[test_g25_journal_namespace.py:604](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:604)。

   新 MEDIUM 缺口：负例中两个路径全部失败，未锁“部分成功、部分失败时仍须 503”的更宽合同。

7. **d⑥ / B5、M4 — CONFIRMED-CLOSED**

   坏目录失败、不留已检查残片、失败传播和原 journal 字节不变均有断言；好目录还要求 journal 真正收缩，[test_g25_journal_namespace.py:668](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:668)、[test_g25_journal_namespace.py:699](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:699)、[test_g25_journal_namespace.py:723](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:723)。

   新 MEDIUM 缺口：验收单称“内容逐键断言”，[验收单:383](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/_bmad-output/验收单/UAT-CARD-G2-5-索引journal命名空间-2026-08-31.md:383)，实际只比较 `canvas_name`，[test_g25_journal_namespace.py:725](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:725)；其他字段丢失或改变仍可能全绿。

## 新问题分级

- **BLOCKER：无。**
- **HIGH：1**
  - e③ 未要求「没有周期反熵」至少出现一次，现有缺短语门测错方向；HIGH-4 继续开放。
- **MEDIUM：6**
  - 相同字节并发 append 的 occurrence/时序未证明安全。
  - 锁内重读异常被当作空集合，随后仍可能覆盖或删除未知 journal，且不置 `persist_failed`，[lancedb_index_service.py:280](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:280)。
  - 已保留的并发 `fresh` 未计入返回的 `pending`，[lancedb_index_service.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:291)、[lancedb_index_service.py:303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/app/services/lancedb_index_service.py:303)。
  - e① 扫描根和周期仍是源码/声明级绑定。
  - d③ 缺混合成功失败场景。
  - d⑥ “逐键断言”与实际断言不符。
- **LOW：1**
  - e③ 测试说明仍写“篡改门×4”，实际为九条，[test_g25_journal_namespace.py:951](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_g25_journal_namespace.py:951)。

BLOCKER/HIGH 清零：否


