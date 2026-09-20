**结论：整改部分有效，但尚不能判为完成。未发现 BLOCKER；仍有 HIGH 级未被拦下的输入。**

审查绑定 `ed5b3a85461812934befa05eb13a0377f45f3299`。全程只读，未连接数据库或服务；负控通过内存与标准输入运行，未修改文件。

先给最重要的五行反查结果：**五处入口行号均准确，证据正文两行通过、三行存在出入。**

| 台账行 | 入口核对 | 证据正文结论 |
|---|---|---|
| CAP-INDEX-DEL-04 | `index.py:90–91` 确为删除路由及函数 | **PARTIAL**：503／404 限制属实，但所引测试没有测试删除端点。 |
| CAP-TZ-SRC-07 | `scripts/local_tz.py:1` 确为两副本说明 | **PARTIAL**：两副本属实，E1 有测试；“逐字对照门锁定”漏记常量不受检查。 |
| CAP-NEO4J-REPLAY-10 | `fallback_sync_service.py:599` 确为回灌函数 | **PARTIAL**：无 overflow 回灌方属实；“不走保留策略、30 天后删除”错误。 |
| CAP-EDGE-RAT-15 | `edges.py:254` 确为 `_write_lancedb` | **PASS**：`:309` 将 async `add_documents` 交给 `to_thread`，得到未 await 的 coroutine；存档 `lancedb-never-writes-probe-20260915T183820.txt:13–29` 明确支持“函数体未执行”。E1＋`implemented-unverified` 如实。 |
| CAP-MCP-QUAR-16 | `server.py:353` 确为 14 工具清单 | **PASS**：`:384–405` 注册 410 并隐藏 schema；隔离测试核查响应及工具集合，实现仍保留。JSON-RPC 部分属于源码／构造面证据，本轮未实跑。 |

以下发现按级别排列。

1. **HIGH — 第二张能力表完全不受检查，当前树即可让无 manifest 的 E5 整体 PASS。**  
   [ledger_lint.py:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:143) 遇到首张表后的非表格行就停止解析，而 `:240` 只要求至少 15 行。负控输入保留前 15 行，将其余行放入第二张合法 Markdown 表，并把 CAP-MCP-QUAR-16 改成无 manifest 的 E5，实际得到 **`rows=15`、`L3 PASS (0 rows)`、`LINT: PASS`**。这直接突破了“没有 live manifest 就无法出现 E3+”的声明。

2. **HIGH — L11 没有把“核验 SHA”绑定到主干，未合分支可自证通过。**  
   [ledger_lint.py:263](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:263) 只核它是 commit，`:347` 再检查证据是否为这个自填 SHA 的祖先。负控输入将部署行证据改为 `79134975`、核验 SHA 改为 `7e1d6b53`，**L9／L11／L12 及整体均 PASS**；但 `79134975` 不是审查绑定 SHA 的祖先。因此该门只能证明“两提交有祖先关系”，不能独立证明“能力已在主干”。

3. **MEDIUM — Neo4j 行混淆了 `.overflow.` 与 `.synced.` 的删除规则。**  
   [capability-ledger.md:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:69) 引用的 `failed_writes_constants.py:104` 实际描述旧游标缺陷把记录误标 `.synced.` 的历史负控输入。当前 overflow 由 `failure_counters.py:153–174` **按文件数量删最老档案**；30 天清理只适用于 `fallback_sync_service.py:931–952` 的 `.synced.`。同表 `:70` 的“丢的是最新而非最旧”也过度概括：原文只证明本批记录可能随最老归档一起被删。

4. **MEDIUM — 时区行把对照门的覆盖范围写宽了。**  
   [capability-ledger.md:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:66) 称副本靠逐字对照门锁定，但测试 `test_g6_9c_single_tz_source.py:91–132` 只比较列举的函数／类，不检查模块常量。验收单 `UAT-CARD-G6-9c-2026-09-08.md:280–283` 已记录未被拦下的输入：单份副本常量减一秒，两道对照门和 54 个参数格仍绿，两副本却相差一小时。该已知限制没有如实回填。

5. **MEDIUM — 索引删除行的测试证据与能力不对应。**  
   [capability-ledger.md:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:63) 引用 `test_lancedb_vault_isolation.py`，但该文件正文只测试表名与作用域解析，没有 `delete_vault_index`、`drop_vault_tables` 或 DELETE 请求。三态限制有源码支持，**该行 E1 所需的对应测试链则未由所列证据建立**。

6. **MEDIUM — L3 的全称判据只覆盖正则命中的路径。**  
   [ledger_lint.py:60](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:60) 与 `:285` 没有先规范化、枚举全部 manifest 引用。本轮确认已有 reconstructed 文件以下三种写法均真实存在，却全部产生空命中：
   - `…/journeys/./J08/manifest.json`
   - `…/Journeys/J08/manifest.json`
   - `…/journeys/j08/manifest.json`

   当同一行另有一份正常路径的合格 live manifest 时，上述不合格引用就不进入全称检查；这是**门未覆盖的路径**，本轮未假称已在真树完成含 live 的整门复现。  
   字段缺失方面，`:304–306` 会拒绝缺少 `mode` 或 `dirty`；但只有这两个字段、缺少 SHA／执行／断言／产物等字段的对象仍满足 L3。错误字段类型还可能直接抛 `AttributeError`，并非受控诊断。

7. **MEDIUM — L12 堵住完全无关文件的 SHA，但没有堵住能力错配及 tag 错配。**  
   [ledger_lint.py:363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:363) 把 `⇩` 后的降级触发面也算作入口。负控输入将索引删除行的证据 SHA 换成仅修改 LanceDB 依赖文件的 `8f3ee155`，整体仍 PASS，不能据此证明删除端点对应性。另将部署行 tag 换为已有的 `merged-squash/card/t5-bugs-CARD-T-SWITCHVAULT`，整体同样 PASS；tag 只检查存在，没有与来源卡或证据 SHA 关联。  
   **路径前缀相同这一条已堵住**：`:374` 使用完整路径集合求交，不使用前缀匹配。

8. **MEDIUM — L4 总计数不能证明每行检查过证据文件。**  
   [ledger_lint.py:319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:319) 合并统计入口与证据对象。负控输入删除 CAP-DEPLOY-01 的全部证据文件及 tag，只保留 `8eeaa899`，仍得到 **整体 PASS，paths=114、L11=22、L12=22**。这些非零总数掩盖了该行“证据文件检查数为零”；L11／L12 有逐行非空保护，但不能替代文件证据检查。

9. **MEDIUM — 声称已登记的遗漏清单与待裁验收单未交付。**  
   [capability-ledger.md:85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:85) 和 `:40` 均援引“本卡验收单”，但绑定提交及本树文件枚举都没有 G1-3 验收单。因此作者所称遗漏分类是否诚实，结论为 **未核实：清单缺失**。对照完整追踪台账 §二，至少以下已合能力没有独立入账：
   - 板级 snooze／unsnooze：追踪台账 `:139`，真实入口 `review_overview.py:3301、3390`。
   - 交互复习壳自动刷新／重建反馈：追踪台账 `:171、180、191`，对应 UAT `:35–48`。
   - board-recap：追踪台账 `:182`，对应 Skill、收集器及 UAT 正文均存在。

   台账已承认“不保证无遗漏”，这一点诚实；但不能据此认定缺失的遗漏清单已经正确分类。

10. **LOW — L3 对照实验的最后一句超出输出能证明的范围。**  
    [l3_semantics_control.py:99](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/l3_semantics_control.py:99) 将 A／D 两例结论相同扩大为“没有改变其它输入”。独立复算确实得到 A=`PASS/PASS`、B／C=`PASS/FAIL`、D=`FAIL/FAIL`，**足以支持原先那条存在判据缺陷已改正**；但实验直接接收预先提取的 `hits`，没有调用正式 L3，不能证明路径发现、schema 或其他输入均正确。

11. **LOW — 与 P8 patch“不冲突”的声明尚无证据。**  
    [protocol-ledger-row.patch:7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/protocol-ledger-row.patch:7) 声称两者各加一行、不冲突；但本树及绑定提交均未找到 P8 CARD-G1-1 patch，存档也未执行两 patch 顺序套用。该项应标 **未核实**，不能断言兼容，也不能反向断言必冲突。

其余要求的核对结果：

- **六段已有负控均成立**：独立复现后分别仅 L4／L3／L3／L1／L11／L12 失败，没有红在其他判据上。
- **原件最终字节一致**：台账 SHA256 与前后存档一致；这证明前后相同，不能证明历史执行中从未修改后恢复。
- **UAT 冲突已如实写成待裁**：台账 `:40` 明列旧总账 `:242` 与计划书 `:587` 的差异，明示保守默认，没有悄悄二选一；问题仅在声称另有验收单登记。
- **协议 patch 本身通过**：`:17` 明确车道写待登记行、主 session 落表，与协议 §5 一致；本轮 `git apply --check` 返回 0，协议原文件 diff 为空。
- **未发现 §12.7 禁止的产品升级声明**：README 确实只有两处反链改动；台账实际为 16 行 E1、5 行 E2、E3+ 为 0。
- **存档不能读成全套绿**：unit 开收工均为 32 failed、5731 passed、44 skipped、13 xfailed，失败集合未增加；manifest 套件 168 passed，全量校验仍只覆盖一份 reconstructed 示例。

本轮结束时 HEAD 与受版本控制文件均未变化。审查期间出现的两份未跟踪补充存档，没有计入 `ed5b3a85` 的已交付证据。


