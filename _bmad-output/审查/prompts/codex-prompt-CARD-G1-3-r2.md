你是本仓的独立审查者。只读，不改任何文件，不连任何数据库或服务。

**先看这条**：本轮**不要向我提问**。凡是完成下面任务所需的文件，你可以直接读——包括台账里引用到的任何源码、测试、验收单、存档、以及协议与计划书的其他段落。下面的「起点读取面」是**起点**不是上限；⓪ 那一项本来就要求你核对源码与证据正文，请直接读。若某项确实无法核实，就在报告里标注「未核实」并说明原因，不要停下来等我批准。

## ① 背景与起点读取面

仓库根: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs
卡: CARD-G1-3 [BATCH-2026-09-18-第十五批]。审查绑定: **ed5b3a85**（基线 9c4e7e82，两个 commit：35b919fe、ed5b3a85）。

本卡是零代码卡：新增一份 markdown 台账 + 给一份 README 加两处反链 + 在 `_bmad-output/` 下放 lint 脚本与 patch。起点：

1. `git --no-pager diff --no-color 9c4e7e82 ed5b3a85 -- . ':(exclude)_bmad-output'`（恰 2 文件）
2. `docs/release-evidence/capability-ledger.md` 全文
3. `docs/release-evidence/README.md`
4. 计划书 `_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md` 的 567 行、579-592 行、以及 §12.7（含 633 行那条禁夸大清单）
5. `docs/release-evidence/manifest.schema.json` 713-722 行；`backend/scripts/validate_release_manifest.py` 76-78 行
6. `.claude/rules/card-batch-protocol.md` §5（本树 90-96 行）
7. `_bmad-output/审查/evidence-g13/` 全目录：`ledger_lint.py`、`l3_semantics_control.py`、`protocol-ledger-row.patch`、以及全部 `*.txt` 存档
8. `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md` 148-268 行（回填面抽查用）
9. 旧总账 `_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md` 242 行

## ② 上一轮的两条发现已整改（请核对整改是否到位，别默认它对）

第一轮你指出：L3 遇到第一份满足两个字段的 manifest 就放行；L11 核祖先关系但不核 SHA、tag 与该能力是否对应。本轮据此改了：

- **L3 改为全称判据**：证据里引用到的每一份 journey manifest 都要合格，且至少一份。因为树内没有任何合格的 live manifest，这个输入在真树上造不出来，所以另附 `l3_semantics_control.py` 做语义对照（临时目录造两份 manifest，旧实现与新实现各判一遍）。
- **新增 L12**：证据 SHA 必须真改动过本行入口列里的文件（`git show --name-only` 取交集）。

请核：这两条整改是否真的堵住了你指出的路径？有没有引入新的未被拦下的输入？对照实验的结论是否被它自己的输出支持？

## ③ 作者自述（请独立核对，不要采信）

台账 21 行，每行有入口 / E 级 / 状态 / uat / 证据 / 已知限制 / 来源卡 / 核验 SHA；E3 及以上为 0 且被 L3 锁死；每条证据路径真实存在、每个 8 位 SHA 都是核验 SHA 的祖先且改动过本行入口；README 只动两处；协议一字未直改、只出 patch；六段负控各自红在指定判据且原件逐字未动。

## ④ 请按重要性排序回答

**⓪ 抽 5 行反查（最重要，请直接读源码与证据正文）**：任选 5 行，逐行核 —— 入口 `file:line` 在 `ed5b3a85` 上是否真指向它声称的符号或段落；证据列指到的文件**内容是否真支撑该行的 E 级与限制描述**（不是「文件存在」，而是「文件确实说了这件事」）。对不上的请指出行 id 与具体出入。

① 已知有问题的能力是否被如实写成限制而非可用？请特别核：边理由向量化写入（声称从不真写，涉及 `edges.py:309` 与 `lancedb_client.py:4344`）、索引删除端点（声称三态未对齐）、时区来源（声称是两份副本而非单一模块）、MCP 写侧工具隔离（声称 410 未物理删除）、Neo4j 失败写回灌（声称轮转出去的记录无回灌方）。

② 「用户 UAT 勾选不升 E4」与旧总账 242 行口径的冲突，是否被如实标注为待裁，而不是悄悄二选一？

③ L3 / L11 / L12 三条门**还有哪些未覆盖的路径**？例如证据里 journey 路径大小写或目录名异常、manifest 字段缺失而非取值不对、SHA 改动的文件与入口只是路径前缀相同、tag 被豁免祖先核所留下的口子。

④ patch 的措辞是否与协议 §5 里「台账只主 session 改」同口径？能否干净套到协议末尾？与 P8 CARD-G1-1 的同段 patch 顺序套用会不会冲突（若该 patch 在树内可读，请一并核）。

⑤ 台账全文与 README 新增行，是否含计划书 §12.7 在证据达到 E3/E4/E5 前禁止的那类声明？

⑥ 承重门自身还有没有假绿面：哪条判据可能在「其实没检查到任何对象」时打印 PASS？脚本打印的 `L4 checked=` / `L11 checked=` / `L12 checked=` 计数是否足以排除这种情况？六段负控里，有没有哪一段其实是红在别的原因上？

⑦ 台账的覆盖面：对照未合卡追踪台账 §二，21 行是否漏掉了明显该入账的已合能力？作者已在验收单列了一份遗漏清单，请核它是否诚实（有没有把该入账的说成不该入账）。

## ⑤ 输出格式

BLOCKER / HIGH / MEDIUM / LOW 分级，每条给 `file:line` + 一句话说明如何观察到。描述时请用「负控输入」「对照输入」「未被拦下的输入」「门未覆盖的路径」这类措辞。

## ⑥ 边界

只读。不评 CARD-R-RC、CARD-R-SLO、G1-6 三张卡的面；不评 G8-9 底账内容本身的正误；不要求本卡去修台账之外的文件。
