你是本仓的独立审查者。只读，不改任何文件，不连任何数据库或服务。

## ① 背景与最小读取面（请只读这些，不要扩面）

仓库根: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs
卡: CARD-G1-3 [BATCH-2026-09-18-第十五批]。审查绑定: 35b919fe（基线 9c4e7e82）。

本卡是**零代码卡**：只新增一份 markdown 台账 + 给一份 README 加两处反链 + 在 `_bmad-output/` 下放一个 lint 脚本与一个 patch。请读：

1. 本卡代码树 diff（恰 2 文件）:
   `git --no-pager diff --no-color 9c4e7e82 35b919fe -- . ':(exclude)_bmad-output'`
2. `docs/release-evidence/capability-ledger.md` —— 全文（本卡主产物）
3. `docs/release-evidence/README.md` 的 1-16 行与 81-99 行
4. 计划书 `_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md` 的 567 行与 579-592 行（A04 定义 + §12.5 E0–E5 + 降级规则）
5. `docs/release-evidence/manifest.schema.json` 的 713-722 行（evidence_level 枚举）
6. `backend/scripts/validate_release_manifest.py` 的 76-78 行（_E3_PLUS / _RECONSTRUCTED_MAX）
7. `.claude/rules/card-batch-protocol.md` 的 90-96 行（§5 排批；本卡 patch 的落点在其末行之后）
8. `_bmad-output/审查/evidence-g13/protocol-ledger-row.patch` —— 全文
9. `_bmad-output/审查/evidence-g13/ledger_lint.py` —— 全文（承重门 L1–L11）
10. 承重存档（全部在 `_bmad-output/审查/evidence-g13/`）:
    - `ledger-lint-close-*.txt`（收工门）
    - `negctl-1-L4-*.txt` / `negctl-2-L3-*.txt` / `negctl-3-L3-*.txt` / `negctl-4-L1-*.txt` / `negctl-5-L11-*.txt`（五段负控）
    - `negctl-origin-sha-*.txt`（原件跑前跑后 sha）
    - `entry-lineno-crosscheck-*.txt`（入口行号逐条反查）
    - `patch-dryrun-*.txt` / `patch-applied-verify-*.txt`
    - `structural-close-*.txt` / `na-judges-pyright-openapi-ruff-*.txt`
11. 供抽查回填面: `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md` 的 148-268 行

## ② 作者自述（请独立核对，不要采信）

作者声称：(1) 台账 21 行，每行有入口 / E 级 / 状态 / uat / 证据 / 已知限制 / 来源卡 / 核验 SHA；(2) E3 及以上行数为 0，且这一点被承重门 L3 锁死而不是靠自律；(3) 每条证据路径在树内真实存在，每个 8 位 SHA 都是核验 SHA 9c4e7e82 的祖先；(4) README 只动了两处（头部加一行 + 原有那句加链接），协议文件一字未直改、只出 patch；(5) 五段负控各自红在指定判据上，且原件逐字未动。

## ③ 请按重要性排序回答下面的问题

**⓪ 随机抽 5 行做反查（最重要）**：从台账里任选 5 行，逐行核 —— 入口的 `file:line` 在 9c4e7e82 上是否真指向它声称的那个符号或段落；证据列指到的文件**内容是否真支撑该行的 E 级与限制描述**（不是「文件存在」，而是「文件确实说了这件事」）。任何一行对不上，请指出行 id 与具体出入。

① 已知有问题的能力是否被如实写成限制、而不是被描述成可用？请特别核这几行：边理由向量化写入（声称从不真写）、索引删除端点（声称三态未对齐）、时区来源（声称是两份副本而非单一模块）、MCP 写侧工具隔离（声称 410 未物理删除）、Neo4j 失败写回灌（声称轮转出去的记录无回灌方）。

② 「用户 UAT 勾选不升 E4」与总账旧口径的冲突，是否被如实标注为待裁，而不是悄悄二选一？

③ 承重门 L3 的覆盖是否完整：负控②测的是「E3 但证据里没有 manifest」，负控③测的是「有 manifest 但 mode 不是 live」。**还有哪些输入是 L3 未覆盖的路径**？例如证据里同时有多个 manifest、manifest 存在但字段缺失、journeys 目录名带特殊字符等。

④ L11（证据 SHA 必须是核验 SHA 的祖先）的口径是否站得住：它对 `merged-squash/*` tag 豁免，理由写在脚本头部（squash 合并使原分支恒非主干祖先）。这个豁免是否留下了**未被拦下的输入**？

⑤ patch 的措辞是否与协议 §5 里「台账只主 session 改」同口径？它能否干净套到协议文件末尾？与 P8 CARD-G1-1 的同段 patch 顺序套用是否会冲突？

⑥ README 新增的那一行、以及台账全文，是否含计划书 §12.7 在证据达到 E3/E4/E5 前禁止的那类声明（production-ready、任意 vault 一键可用、完整 multi-vault safe 等）？

⑦ 承重门自身是否有假绿面：哪条判据可能在「其实没检查到任何对象」的情况下打印 PASS？脚本打印的 `L4 checked=` / `L11 checked=` 计数是否足以排除这种情况？

## ④ 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给 `file:line` + 一句话说明如何观察到该问题。描述问题时请用「负控输入」「对照输入」「未被拦下的输入」「门未覆盖的路径」这类措辞。

## ⑤ 边界

只读审查。不评 CARD-R-RC（rc 骨架）、CARD-R-SLO（SLO 阈值）、G1-6（逐声明审计链）三张卡的面；不评 G8-9 底账内容本身的正误（台账只引用它的小节编号）；不要求本卡去修台账之外的任何文件。
