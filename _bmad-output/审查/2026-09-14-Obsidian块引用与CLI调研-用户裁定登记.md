# Obsidian 块引用 / CLI 调研 — 用户裁定登记（2026-09-13 ～ 2026-09-14）

> 来源研究：`_bmad-output/研究/2026-09-12-Obsidian原生块引用与CLI-对原白板节点批注关系梳理的收益评估.md`（§10.2 决定表）
> ⚠️ graphiti-canvas MCP 在本 session 全程连接失败，`[Decision-Review]` 未写入图；本文件为一手登记，MCP 恢复后按本文补 `add_memory`（PENDING）。
> 用户 = 甲方（CLAUDE.md 铁律 4）；以下均为用户在对话中的原话裁定，主 session 只转录不代裁。

| # | 决定 | 用户裁定 | 日期 | 执行状态 |
|---|---|---|---|---|
| D-A | 「批注埋原生 `^cb-xxx` 块 id」：维持 2026-06-13 延后，还是现在做？ | **维持延后**（原话「D-A延后」） | 2026-09-13 | 不排卡 (d)；D-B / D-C / D-D 随之不触发。性质 = 对 06-13「待 ChatGPT 审查」提案的**首次用户明确裁定** |
| D-E | 是否开 CLI 跑零代码只读探针卡 (a) | **执行**（原话「D-E 请你执行 CIL 跑探针」） | 2026-09-13 | ✅ 完成：33 条只读命令、零写入；证据 `_bmad-output/审查/evidence-cli-probe/INDEX-20260913.md`；结论写入研究文档 §11。裁决不变：收益不明显 |
| D-F | 退役 `react_agent` 三个 Obsidian CLI 工具（方案 A） | **补充到分 goal 治理**（原话「先 D-F 和 D-G 我们先一起补充到分 goal 治理那里」） | 2026-09-14 | ✅ 已登记台账 §一.b「2026-09-14 调研派生待排卡」→ REACT-CLI-DEMOTE，第十五批排批处置 |
| D-G | 修 obsidiantools absolute 链接下入/出边分裂 | **补充到分 goal 治理**（同上） | 2026-09-14 | ✅ 已登记台账 §一.b → WLGRAPH-KEY-NORM |
| D-H | 修正「pretool-guard.js 强制阻断」失实承诺 + 补路径级守卫 | **先做**（原话「D-H 先做」） | 2026-09-14 | ✅ 完成：守卫脚本 + 单测（7/7）+ 真实载荷（10/10）落地；用户 2026-09-14 裁「**用户级 `~/.claude/settings.json`**」（D-36 同意），已加两条 PreToolUse（Bash 追加 / `Edit\|Write\|MultiEdit\|NotebookEdit` 新增），备份 `~/.claude/settings.json.bak-20260914T155608`；接线后同会话发现粗版守卫把「命令文本提到 PRD + 含 touch/cp 一词」当写（误拦了主 session 自己的通告命令）→ 当场收窄为**按命令段解析写目标**（重定向目标 / cp·mv·rsync 目的参数 / tee 参数 / 就地命令 + 保护路径），源为保护路径的 `cp <PRD> /dev/null` 放行；单测 8/8（`evidence-dh-guard/unit-test-r3-*.txt`），重装副本 sha256 `c05f03d1…` 与源码一致；协议 §2.3 批级通告已写第十四批手册 §零 第 17 条并 SendMessage 通知 batch-14 主会话；CLAUDE.md 两处改为实话；证据 `_bmad-output/审查/evidence-dh-guard/`。**本会话实测立即生效**：接线后主 session 一条无害的 `cp "<PRD>" /dev/null` 被 R1 真实拦下（`evidence-dh-guard/live-session-block-20260914T1602.md`） |
| D-36（既往） | pretool-guard 接线需用户同意改 settings | 第十四批手册 §四.4 原文 | 2026-09-11 | 本次 D-H 接线动作以此为准，等待用户裁 |

## 附：提交归属（2026-09-14 16:10，与 batch-14 主会话 SendMessage 商定）

- 本会话（bmad-output-08）在 feature 主干树的全部产出**不另行 commit**，由 batch-14 主会话随其下一个 docs commit 统一入库；hook 源码与测试被 `.gitignore:44` `.claude/*` 忽略，需 `git add -f`（既有 6 个 hook 亦如此）。
- 对方已核：`~/.claude/settings.json` 两处接线；R2 用 realpath + isInside 判 live 路径，车道树里的 `canvas-vault/` 副本不在其内，车道改自己树的 SKILL.md 不会被误拦；手册 §一.1 已补第 9 条「遇 `[readonly-path-guard R…]` 拦截即停下报主 session，不得绕过、不得请求旁路」。
- 主仓 `CLAUDE.md:101` 的同句失实承诺随合并跟进，本会话未动主仓工作树。

## 附：与 CLAUDE.md 铁律的对照

- 铁律 2「决策必须 `[Decision-Review]` PENDING，独立验证」：本文即 PENDING 登记；独立验证 = 研究文档 §8 的 12 主张 × 3 路对抗核验（37 agent，0 失败）+ §11 探针实测。
- 铁律 4「技术决策先深度澄清，用户是甲方」：三次对话逐条解释（D-A/D-E；D-F/D-G/D-H），用户逐条裁定，无代裁。
