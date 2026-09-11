你是独立代码审查者，这是同一张卡的第三轮。仓库根目录：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance
（只读；不要连数据库，不要执行测试。）

## 〇 本轮最重要的一件事：请区分两类问题

第二轮你给出 HIGH-1：本卡的分页收口把「排在默认分页外的重叠 vault 表」从碰不到变成会删。
**作者复核后确认你是对的**，并据此更正了自己第一轮的说法。但该缺陷的**根治**需要拿到全部
vault 列表做最长前缀优先，涉及三处同口径，已明确移交下一张卡（`CARD-G2-9-F2`）。

所以本轮请把问题分成两类，分别回答：

- **A 类：已知且已登记移交的未闭合面本身。**（前缀重叠；以及本卡分页收口扩大了它的可达面）
  请**不要**再把「这个缺陷仍然存在」重复报告为 HIGH —— 那是已知的、故意保留的。
  请改为评估**处置是否恰当**：加的锁够不够、收窄后的声称还有没有宽于证据的地方、
  登记的信息够不够下一张卡接手。若你认为「保留并移交」这个决定本身不可接受，
  请明确说出来并给出理由（这条会原样转交给做合并裁定的人）。
- **B 类：除此之外的任何问题。** 正常按严重度报告。本轮结论请**明确给出 B 类的
  BLOCKER / HIGH 计数**（A 类不计入），因为流程规则是「最后一轮 B 类 BLOCKER=0、HIGH=0」。

## 一 背景 + 最小读取面

本轮 HEAD `0ec1f0c3`。上一轮绑 `9da89fdd`。

**本轮改动（两个文件）**：
1. `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`
   - 新增 `_assert_table_shape`：门的夹具前提改为从库里**读回** schema 与向量维度
   - 门⑤ 重写：参数化 `page-inner` / `page-outer` 两种形态；
     **前提全部移到不带 xfail 的独立用例** `test_prefix_overlap_premises_hold`
2. `backend/lib/agentic_rag/clients/lancedb_client.py`
   - 仅 `_owns_table` 的 docstring：更正措辞（单向认领 + 下划线边界）并补记
     「本卡的分页收口扩大了该缺陷的可达面」

**最小读取面**（按此顺序）：
- `git diff 9da89fdd 0ec1f0c3 -- . ':(exclude)_bmad-output'`（本轮增量）
- `git diff da690bf8 0ec1f0c3 -- . ':(exclude)_bmad-output'`（整卡全量）
- `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` 全文
- `backend/lib/agentic_rag/clients/lancedb_client.py` 的 `:830-905`、`:1000-1060`、`:3700-3760`
- `backend/scripts/g29_dual_vault_canary.py` 的 `:1240-1300`、`:1360-1460`
- 前两轮存档 `_bmad-output/审查/codex-review-CARD-G2-9-F1-r1.md` 与 `-r2.md`
- `_bmad-output/审查/evidence-g29f1/` 下：
  `g29f1-final-negctl-*.txt`（六段负控，**本轮起含变异体逐行 diff**）、
  `high1-r2-pagination-widens-overlap-*.txt`（你 r2 反例的实测）、
  `xfail-swallows-premise-*.txt` 与 `xfail-split-premise-fix-*.txt`（xfail 三态可区分性）、
  `dimcheck-callsites-*.txt`（AST 口径调用点全清单）、
  `connect-tmp-only-ast-*.txt`（connect 溯源，含验伪锚）、
  `canary-guard-ast-precise-*.txt`（守卫落点 AST 判据）
- 验收单 `_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md` **全文**
  （你 r2 提到「收窄的三处不在读取面」，本轮全文列入）

## 二 对第二轮每一条的处置（请独立核对）

| 你的条目 | 处置 |
|---|---|
| HIGH-1 分页收口扩大可达面 | 复核**成立**。门⑤ 参数化出 `[page-outer-10]` 专锁此面；**负控 6** 拆掉分页收口后该门 XPASS 报红 = 门内证明。声称三处收窄。按流程交由做合并裁定的人判断是否属阻断级，本车道不自判 |
| MEDIUM 「F2 修好后不会 XPASS，前提断言先失败」 | 已修：前提全部移出 xfail 用例 |
| MEDIUM 「夹具失败也记 XFAIL，不可区分」 | 已修：同上；三态可区分性有最小复现存档 |
| MEDIUM 「不能独立排除第三条调用路径」 | 补 AST 口径全清单：生产调用点恰 2 处（`_cache_tables` / `add_documents`），无第三条 |
| MEDIUM 「负控档案只有 sha，不能证明只改一层」 | harness 改为落档变异体与基线的逐行 diff；六段实测 1/1/1（第 3 段 2/2/2，它明确拆两处） |
| LOW-4 措辞失真 | 已改为「短 id **单向**认领长 id，需下划线边界（`ab_x` 不碰撞）」，有对撞实证 |
| LOW-5 文实不符 | 门⑤ 重写时该对照表已移除，docstring 同步 |
| LOW-6 / LOW-7 验收单措辞 | 已同步更正 |

## 三 请回答（按重要性排序）

1. **A 类处置**：门⑤ 那四条用例（两条前提门 + 两条缺陷锁）合起来，能不能做到：
   (a) 夹具坏 → 红；(b) 缺陷仍在 → xfail；(c) F2 修好 → 红并指向「该删标记了」？
   三者两两可区分吗？有没有第四种情形会被误判进上述某一类？
2. **A 类处置**：验收单里对「本卡扩大可达面」的描述，与代码实际行为是否一致？
   还有没有任何一处声称宽于证据？给做裁定的人的信息（触发条件、两个选项及代价）是否完整、准确？
3. **B 类**：`_assert_table_shape` 引入后，各门的前提是否可能**过严**（把正常夹具判成坏）？
4. **B 类**：门⑤ 的 `_overlap_fixture(db_path, filler)` 在 `page-outer` 形态下依赖
   「10 张填充表恰好占满默认分页」。这个前提有没有可能在别的 lancedb 版本上失效而**静默**通过？
5. **B 类**：整卡（`da690bf8` → `0ec1f0c3`）范围内，前三轮都没提到的问题。
6. **B 类**：六段负控里，有没有哪一段的变异 diff 与它声称拆的那一层**不符**？

## 四 输出格式

逐条给出：`[A|B] [BLOCKER|HIGH|MEDIUM|LOW]` + `file:line` + 一句话说明触发条件。
没有问题的维度请明确写「未发现问题」。
**最后必须单独给出一行：B 类 BLOCKER = N，B 类 HIGH = M。**

## 五 边界

- 只读审查。不要修改文件、执行测试或连接数据库、网络。
- 不评 `_check_and_fix_dimension_mismatch` 的 drop 条件设计本身（既有裁定）。
- 不评 `list_vault_tables:845` 的裸表口径本身是否合理（RAG-S1 H3 既有裁定）。
- 不评完整 canary 的端到端运行（本卡未跑，已登记移交）。
- 前缀重叠的**修法设计**不在本轮范围（属下一张卡）。
