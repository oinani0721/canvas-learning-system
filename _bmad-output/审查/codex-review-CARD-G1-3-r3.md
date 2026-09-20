**结论：BLOCKER 0 / HIGH 1 / MEDIUM 8 / LOW 1。整改部分有效，尚不能判为完成。**

审查绑定 `bba951951e44597c08fc284c9ac3ac66896d4c8b`。全程只读，未连接数据库或服务。结束时 HEAD、受版本控制文件均未变化。

1. **HIGH — L13 仍未封住第二张能力表不受检查的路径。**  
   [ledger_lint.py:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:193) 要求行首尾都有 `|`，`:196` 又只收恰好 11 列。负控输入保留前 15 行，将后六行改为无 manifest 的 E5，再分别放入 **12 列表、10 列表、省略外侧竖线的 11 列表、HTML 表**；四种均得到 **`rows=15`、`L3 (0 rows)`、`L13 PASS`、`LINT: PASS`、rc=0**。原来的具体写法已堵，原 HIGH-1 所指路径尚未整体封闭。

2. **MEDIUM — L9 依赖可信的外部基准，仍不能独立证明“已在主干”。**  
   [ledger_lint.py:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:269) 默认 `HEAD`，`:285` 只确认引用可解析为 commit。固定 `--trunk=bba95195` 时，`7e1d6b53 / 79134975` 原负控输入确实只红 L9；但把该部署行组成 15 个唯一 id 的对照输入，传入 **`--trunk=7e1d6b53` 后整体 PASS**。  
   **原路径在可信 trunk 下已堵**；剩余问题是主干身份由调用方保证，默认工作树 HEAD 不能提供这个保证。这不等于固定可信 trunk 后仍有未被拦下的输入。

3. **MEDIUM — M-6 只部分修复，L3 仍漏掉同一文件的其他路径写法。**  
   [ledger_lint.py:250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:250) 只做 `normpath`，随后要求字符串以 `docs/release-evidence/` 开头。同一 reconstructed manifest 使用**绝对路径**或 `../card-p10-docs/docs/release-evidence/…/manifest.json` 时，均真实存在、被 L4 识别为路径，但 `find_manifest_refs()` 返回空列表。  
   这是正式发现函数中仍未覆盖的路径；**本树没有真实 live manifest，未声称完成“混入真实 live 后整门 PASS”的验证。**

4. **MEDIUM — M-7 登记了限制，但两条旧路径仍未修。**  
   [ledger_lint.py:454](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:454) 仍把 `⇩` 后的依赖纳入入口集合；索引删除行证据改为 `8f3ee155`，仅命中 LanceDB 依赖文件，整体仍 PASS。另将部署行 tag 换成 `merged-squash/card/t5-bugs-CARD-T-SWITCHVAULT`，也整体 PASS，因为 `:415` 只查 tag 存在。新增 `58164977` 存档确实证明“顺带碰过入口文件也能通过”，**属于限制自证，不是修复**。

5. **MEDIUM — M-9 的验收单仍未交付，不能以具体路径替代存在性。**  
   [capability-ledger.md:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:40) 与 `:87` 引用的 `UAT-CARD-G1-3-2026-09-18.md`，在绑定提交和当前工作树均不存在；`git cat-file -e` 返回 128。`structural-close-20260918T174957.txt:16` 仅凭“具体路径引用=2”写“M-9 已修”，证据不足。三项能力仍没有独立入账；**遗漏分类未核实，原因是验收单缺失**。下一 commit 的交付不能计入本轮绑定。

6. **MEDIUM — 复习总览行把显式降级写成了空视图／恒空。**  
   [capability-ledger.md:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:69) 的描述与 `review_overview.py:770–775、1714–1724` 不符：页面明确区分“过期投影／无投影／投影损坏”，并显示具体提示；已有投影停更时，`:1097–1098` 保留数据并标 `stale`，不必然恒空。所引测试也断言这些降级提示。

7. **MEDIUM — clear-inbox 行将局部“不建议删”泛化为整个引擎的限制。**  
   [capability-ledger.md:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:73) 写“刻意不产出建议删”，但 `inbox_preview.py:1766–1773、1826` 的 C3/C4 实际返回删除提名，测试 `test_g5_6_clear_inbox.py:279–285、309–310` 明确断言“建议删”。原文“不建议删”只限定批内重复、正本不可判的情形。另 `inbox_preview.py:2445` **默认就输出到 `<vault>/outputs`**，并非只有误指定到 vault 内才写入。

8. **MEDIUM — Skill 可移植性行把已覆盖的路径写成门未覆盖的路径。**  
   [capability-ledger.md:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:74) 称新增 skill 不登记就不扫描，但 `skill_portability_lint.py:2335–2343` 枚举实际目录、报告集合漂移并继续检查；`:897–915` 还解析 fenced Python/shell 并扫描裸 token，因此也不是“只查 frontmatter 与反引号 span”。

9. **MEDIUM — L13 新增了代码块示例的假红。**  
   [ledger_lint.py:189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:189) 不识别代码块边界。对照输入保留原台账，追加 fenced `text` 代码块中的 11 列示例表，**仅 L13 红两行，整体 rc=1**。当前台账实际只有 2 列规则表和 11 列能力表，原件未被误伤；3 列表同样不命中该条件。假红发生在合法的同列数示例或说明表。

10. **LOW — 原件哈希存档既不能证明全过程未触碰，也未绑定定稿字节。**  
    [negctl-origin-sha-20260918T174741.txt:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/negctl-origin-sha-20260918T174741.txt:2) 只比较前后两个时刻，不能排除中间修改后恢复，`:4` 的“原件未被负控触碰”超出证据范围。此外存档为 `0a97caac…`，绑定提交及当前台账实际为 `1f971806…`，不是同一份字节内容。

其余整改逐项核对结果：

| 整改 | 结论 |
|---|---|
| **M-3 overflow／synced** | **到位。** `failure_counters.py:153–174` 按数量删除最老 overflow；`fallback_sync_service.py:931–952` 按 30 天清理 synced。新记录随最老归档被删的例子对应 `failed_writes_constants.py:227–230`，改写没有继续泛化。 |
| **M-4 时区对照门** | **到位。** `test_g6_9c_single_tz_source.py:91–132` 比较列举的函数和类，不含模块常量；所引 UAT 第⑱条确实记录了两门及 54 参数格仍绿的对照结果。 |
| **M-5 索引删除测试** | **E1 对应性已补齐。** 第一份测试真实调用删除端点并验证成功／404／503，但 `drop_vault_tables` 是 `MagicMock`；第二份在 `test_lancedb_cross_vault_drop_g29f1.py:676、864` 调用真实删表实现。因此“两份都真调删表”的括注应区分这两层。 |
| **M-8 L4** | **原负控输入已堵。** 逐行计数及证据路径非空检查已加入；但仍只保证存在路径，`./` 加有效 SHA 也能整体 PASS，不能读成核实了具体证据文件或正文。 |
| **L-10 语义对照措辞** | **到位。** `l3_semantics_control.py:99–102` 明说没有调用正式 L3，仅支持给定 hits 的存在／全称判据对照。 |
| **L-11 patch 兼容性** | **措辞整改到位。** `protocol-ledger-row.patch:7–9` 已标“未核实”。本 patch 单独 `git apply --check` 通过；两 patch 串联兼容性仍未核实。 |

本轮另抽的五行均与 r2 不同：

| 台账行 | 入口反查 | E 级与证据正文 |
|---|---|---|
| CAP-FSRS-SOT-05 | `review_service.py:129` 是 reader 段标题，实际函数在 `:223` | **PASS**：真相源测试及 g37r2 存档支持 E1；投影与 frontmatter 边界吻合。 |
| CAP-QUIZ-CAS-06 | `quiz-answer/SKILL.md:76` 确为两阶段规则 | **PASS**：pending 续跑、成功才 done、本地 Beta 的正文及 UAT 支持 E1；后端死锁的当前运行状态未连接服务复验。 |
| CAP-REVIEW-OV-08 | `review_overview.py:1185` 确为聚合入口 | **PARTIAL**：E1 有据，限制描述存在第 6 条问题。 |
| CAP-INBOX-PREV-12 | `inbox_preview.py:2099` 确为 `build_preview` | **PARTIAL**：E1 有据，限制描述存在第 7 条问题。 |
| CAP-SKILL-PORT-13 | `skill_portability_lint.py:86` 是常量，实际判据入口从 `:2331` 起 | **PARTIAL**：测试及 555 passed 存档支持 E1，限制描述存在第 8 条问题，入口行号也宜收紧。 |

这五份入口文件在 `bba95195` 与 `9c4e7e82` 内容相同，其最后改动 SHA 与台账填写值一致。

**十段负控没有发现红在别的原因上。** 独立复算正式门，十段依次仅红 **L4、L3、L3、L1、L11、L12、L13、L9、L3、L4**，全部 rc=1；原件对照输入 PASS。但这只能证明这十个输入，不能覆盖上述新增输入。

**未发现台账新增 §12.7 禁止的产品升级声明。** 当前仍为 16 行 E1、5 行 E2、E3+ 为 0；README 仅增加反链。主要未闭合项是门的覆盖边界、缺失验收单，以及三行与源码不符的限制描述。未跟踪的 `l13-false-positive-scan-*.txt` 未计入 `bba95195` 已交付证据。
