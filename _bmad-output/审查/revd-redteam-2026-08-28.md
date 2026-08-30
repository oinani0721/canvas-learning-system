# 红队对抗审查 — CARD-R-EVD manifest 校验器

> **批次**: BATCH-2026-08-28-第五批 / CARD-R-EVD
> **形态**: 5 条攻击轴并行 → 每条发现独立对抗复核（默认 refuted，须自行复跑）→ 3 个审计 critic
> **攻击目标**: 构造**能通过校验但在撒谎**的 manifest
> **被测版本**: Codex round-1 整改后（schema v1.0.0 + S1–S13 + A0–A3，111 测试绿）
> **规则**: 每条发现必须由攻击者亲自跑出 exit 0 才准上报；复核者默认判 refuted，且被告知「只利用 README 已声明的非目标不算发现」

## 结论摘要

红队在一份"Codex 两个 BLOCKER 已修、111 测试全绿"的校验器上，仍打出多条**未被声明为非目标**的真实漏洞。核心教训一致：**凡是由 manifest 作者自己填的"标准"，都不是标准**——`days_required` 自己填、skip 与否自己声明、evidence_level 与实际结果不挂钩。

## 已确认必修（多轴独立命中或本人复现）

| # | 级别 | 漏洞 | 谎言 | 处置 |
|---|---|---|---|---|
| R1 | BLOCKER | **`days_required` 由作者自填**：写 `days_required=1` + `days_completed=1` 即满足"14 天 dogfood 门" | 一天的窗口冒充 E5「可每天依赖的个人候选版本」 | schema 强制 `days_required ≥ 14`（§12.6 协议名即 14-day） |
| R2 | BLOCKER | **`activity_counts` 可以全零** | "14 天 dogfood 完成"而 0 次学习 session、0 次 ingest→board、0 次备份恢复 | 新增必填 `activity_minimums`：key 集须与 counts 相等、每项 ≥1、counts 逐项 ≥ minimums（§12.6「数值由用户运行前锁定、开始后不得下调」） |
| R3 | BLOCKER | **dogfood 起止日期从不解析**：`start_date` 到 `end_date` 只隔 2 天却报 `days_completed=14`；`start_date="banana"` 也过 | 2 天窗口认证 14 天 | schema 加日期正则；S11 解析并交叉核对：`end ≥ start` 且含首尾跨度 ≥ `days_completed` |
| R4 | BLOCKER | **`--require-complete` RC 门只查"文件在 + mode=live"**：10 条旅程跑在 10 个不同 commit、全部 E0、全部 `result=fail`，门返回零问题（**本人独立复现，问题数=0**） | 对外呈现为「J01–J10 全齐、RC 就绪」 | RC 门加三条：同一 `candidate.sha`、每份 `evidence_level ≥ E3`、每份 `result=pass`（§12.6「J01–J10 全部达到 E3」+ 同一 RC SHA） |
| R5 | BLOCKER | **skip/mock 是纯自陈布尔**：唯一"真实命令"写着 `SKIP_NEO4J=1 GRAPHITI_MOCK=1 pytest --ignore=…`，只要 `declared=false` 就能拿 E3 | "无 skip 黑盒 E2E" | 新增 S16：E3+ 时按已知开关模式扫 `commands[].cmd`，命中而未声明即红（**明确标注为启发式**，见 README 已知边界） |
| R6 | HIGH | **evidence_level 与 result/断言/回滚完全解耦**：全部断言 fail + 回滚 fail 的旅程可标 E4 并带用户签字 | "User-verified，用户可用" | 新增 S14：E3+ 必须 `result=pass`（"Verified" 蕴含通过） |
| R7 | HIGH | **SLO 未达标经 `result=partial` 洗白**：S9 的 waiver 要求只在 `result=pass` 时生效 | 每项 SLO 都没达标却无 waiver | S9 扩至"除 `result=fail` 外"，并强制 `known_limitations` 非空（§12.5「降级为限制」） |
| R8 | MEDIUM | **签字时间可早于旅程开始**：`signoff.at` 比执行窗口早 20 个月仍通过；签字人可以是模型自己 | "用户按真实场景完成 UAT" | 新增 S15：`signoff.at ≥ execution.finished_at`；`signoff.user` 不得等于 `environment.models[].name`（自签） |
| R9 | MEDIUM | **`expected_failure` 是无理由的万能牌**：三条命令全非零退出（含 exit 127 命令不存在），各挂一个 `expected_failure` 即可 `result=pass` | "全部命令跑通" | schema if/then：`expected_failure=true` 必须带 `note` |
| R10 | MEDIUM | **candidate.sha 可为 git null SHA（40 个 0）** | "clean RC SHA" | schema 正则排除全零；真实性不验（浅克隆场景，已写入已知边界） |
| R11 | LOW | **零耗时旅程**：`started_at == finished_at` 在 E5 通过 | 一条完整 bootstrap 旅程耗时 0 秒 | S2 扩展：E3+ 要求 `finished_at > started_at` 严格大于 |

## 复核判为「非发现」的（诚实记录）

复核者被要求默认 refuted，并对照 README 的「已知边界」判断是否只是利用了已声明的非目标。以下被判 NOT-A-FINDING：

- **零字节产物满足"至少一件产物"**：复现属实（exit 0），但判为"declared non-goal 且该角度不承重"——不过本次仍做了收窄：断言引用的产物必须非空（S12 扩展），单纯挂在清单里的空文件仍允许。
- **`repo://README.md` 冒充旅程产物**：复现属实，checksum 也是真的；校验器无从知道产物是否本次旅程产生。**保留为已知边界并写入 README**。
- **`expected_failure` 的宪章问题**：复核认为属 S7 设计范围内——但"无理由"这一点仍被采纳为 R9（要求 note）。
- **waiver 事后补开**：复核指出 §12.5 L592 原文允许"事前**或书面**接受"，被禁的是改阈值而非接受未达标。**采纳复核意见**，不加时序约束，改为强制 `known_limitations` 落账（R7），并把这一判断写入 README 已知边界。
- **`started_at == finished_at`**：复核认为 S2 边界正确（未倒挂）。**部分采纳**——仅在 E3+ 上加严（R11）。

## 规模与结论

workflow 实跑：**67 个 agent / 932 次工具调用 / 5.27M subagent tokens / 31 分钟**。5 条攻击轴共提出若干绕过，经每条独立对抗复核（复核者默认判 refuted，须自行复跑，且被告知"只利用 README 已声明的非目标不算发现"）后：**24 条确认、35 条驳回**。

确认的 24 条全部已整改并各有回归测试（`test_redteam_*` 系列）。驳回的 35 条按复核意见处理：属"已声明非目标"的写入 README 已知边界，不做假修。

## 审计 critic 结论（3 个）

### 1. 测试质量 critic —— 做了真变异测试，抓到假绿

该 critic 把校验器复制到 scratchpad，**逐条删除规则**再跑仓内测试，发现 **45 条子规则中 7 条删掉后测试仍全绿**（= 零覆盖），并抓到三处"因为错误的理由而通过"：

- `test_a0_symlink_artifact_rejected` 断言 `"symlink" in p`，而 pytest 的 tmp_path 目录名里就带测试函数名 `…symlink…`——**报错消息里的路径**就满足了它。把整条 symlink 规则删掉，测试照样绿。
- `test_s8_rollback_self_contradiction_fails[rollback0]` 只断言 `"S8" in codes`，实际是被另一条 S8 规则（"not_applicable 必须给 reason"）顺手满足的。
- `test_codex_round1_blocker1_repo_path_traversal` 的 `any("path" in p)` 被 schema 报错里的 JSON 指针 `artifacts/0/path` 满足——这条自称覆盖 BLOCKER-1 的测试**从未触达 A0 那层防御深度**。

**整改**：三处断言逐条钉死到只可能来自校验器的中文措辞或具体消息；symlink 测试改为把目标放在 manifest 目录**内部**（否则 containment 规则先开火，symlink 分支根本执行不到）。随后我自建 harness 做了**全量变异测试**：77 条规则逐条删除、每次重跑全套件，补齐 9 处缺口后达到 **77/77 全部被杀死，存活 0**。

期间还发现测试自身的一个后门：`test_mutation_a1_unreadable_artifact_reported` 写的是"problems 为空就 skip"，而规则删掉后 problems 恰好为空 → 测试自己跳过 → 变异体存活。skip 的判据必须来自环境探测，不能来自被测物的输出。

### 2. 文档诚实性 critic

逐行比对 README 与代码实际行为。整改后 README 的规则表已扩到 S1–S17 + A0–A3 并逐条与代码对齐；`dirty` 一行从"schema const false"改为如实记录"改由语义层强制，且说明为什么不能写死"；退出码分档、产物默认真验、CI 门的覆盖边界均已重写。

### 3. 示例保真度 critic —— 最重的一个

逐条核对示例 manifest 与 D5 归档 + git 事实，报出 **11 处 overclaim + 1 处 underclaim**。我逐条独立复核（reflog、mtime、文件计数、脚本位置、裁判项数）后确认全部属实，并全部改正：

| 编号 | 问题 | 改正 |
|---|---|---|
| O1 | 断言 D5-4 称「无 vault 内容写入」——**事实相反**：CLAUDE.md 与 Dashboard.md 于 06:19:25（执行窗口内）被写并随 c823a35f 提交 | 断言改写为真实写侧足迹，并注明所引 after-check.txt 结构上支撑不了更宽的主张 |
| O2 | 命令表里的裁判脚本路径 `.claude/skills/board-recap/scripts/check_report_sections.py` **从未存在**（真实位置在 CARD-C5 证据目录），且该脚本只吃单文件不吃 glob | 路径与调用形态双改，note 里点明 |
| O3 | 「18 项机械裁判」——实测 manifest 模式下恰好 **16 项**，源码上限 17，18 不可达 | 改为 16 并注明来源 |
| O4 | `candidate.dirty: false` **不是"未证明"而是"可证伪"**——schema 的 `const: false` 逼着这份诚实回填写下假话 | schema 放开为 boolean + 新增 S17 把住发布线；示例改为 `dirty: true` 并写进 known_limitations |
| O5 | `candidate.branch: feature/obsidian-hybrid-dev` **是不存在的 ref**（真名 `worktree-feature-obsidian-hybrid-dev`） | 改为实测值 |
| O6 | `cwd: canvas-vault` 实指**主仓** vault（30 个 md），而非 candidate.worktree 下那份陈旧副本（15 个 md，不含被测文件） | 每条命令的 cwd 显式标注，并列入 unproven_fields |
| O7 | `finished_at` 取自结案报告落盘时刻（收尾文档），非执行边界；最后一份执行产物落盘于 06:18:39 | 列入 unproven_fields 并说明 |
| O8 | `environment.services` 写「本地 FastAPI 端点」——skill 源码里**没有任何 HTTP 调用**，数据面是 MCP 工具 | 改为 MCP 工具并列入 unproven_fields |
| O9 | 命令表覆盖不全：D5-3 依赖的 `--verify` 调用与 MCP 取数调用都不在表里 | 在 unproven_fields 中显式声明不完整 |
| O10 | `rollback.reason` 称「零 vault 写侧」，与 O1 冲突 | 改写 |
| O11 | `reconstructed_from` 说的 mtime 推导在本仓不可复现（本仓副本 mtime 已是 checkout 时刻） | 改为指名 feature worktree 的确切路径 |
| **underclaim** | `candidate.sha` 被降格为「最合理推断」——其实**有直接证明**：主仓 reflog 显示 HEAD 自 05:30:04 起为 91383b1f、至 06:21:32 才变，完整覆盖执行窗口 | 提升为 reflog 实证并移出 unproven_fields |

两条教训固化为回归测试：`test_repo_example_candidate_sha_is_not_the_archiving_commit`、`test_repo_example_declares_dirty_truthfully`。

## 元教训

这一轮最值得记的不是任何单条漏洞，而是三件事：

1. **凡是由被审对象自己填的"标准"都不是标准**——`days_required` 自填、skip 自陈、`meets` 自判，三处都被打穿。
2. **"我已经很诚实了"不是诚实**——示例 manifest 我是奔着"如实回填"写的，仍有 11 处 overclaim，其中一处（D5-4）与归档白纸黑字相反。诚实需要逐条核对事实，不是端正态度。
3. **schema 可以逼人说谎**——`dirty: const false` 是善意的硬要求，但它让唯一合规的写法变成假话。约束的设计必须给真话留出口。
