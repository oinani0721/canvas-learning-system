# UAT — CARD-R-EVD Release 证据目录与 manifest 规范

> **批次**: BATCH-2026-08-28-第五批 / CARD-R-EVD（车道 S8，DEBT-5 之后第二卡）
> **worktree**: `.claude/worktrees/card-s8-ci`（分支 `card/s8-ci`）
> **卡定义**: 总账 v2 §R-EVD（4h · wave 1 · 发布必需），锚点计划书 §12.4 A06 / §12.6 L596
> **执行日**: 2026-08-28

## 一句话

把"发布前每条用户旅程的证据长什么样"从一句口头约定变成**机器能判的契约**：JSON Schema 定字段、校验器查自洽（S1–S17 + A0–A3）、CI 自动跑、并用已归档的 D5 盲测证据回填了一份示例。本卡不跑任何旅程——只做规范、校验器、样例。

## 用户视角：这东西将来怎么帮到你

发布那天你会面对十条旅程的一堆日志和截图。没有本卡，你只能靠"当时好像跑过"来决定 README 能写什么；有了本卡，每条旅程有一份可机读的 manifest，而且机器会拒绝下面这些自欺：

- 断言里有 fail，整体却写"通过"；
- 回滚失败了，整体还写"通过"；
- 带着 mock 声明却标 E3（"参考环境已验证"）；
- 标 E4/E5 却没有你的签字，或者签字只有一个 "approved" 字样、没有人名和时间；
- 标 E5 却没跑满 14 天 dogfood，或 dogfood 跑的是另一个 SHA；
- SLO 没达标却判 pass 且没有你的书面接受；
- 事后补写的记述冒充当场实录。

**你需要做的**：暂时什么都不用做。本卡没有任何界面、没有部署、不碰 live vault。真正需要你的时刻在未来——RC 冻结后每条旅程的 manifest 会来找你签字（`signoff` 字段），以及 SLO 阈值由 CARD-R-SLO 请你锁版。

## Claude 已代跑的技术验证

| 判据（卡定义要求） | 结果 |
|---|---|
| (a) schema 定版 + 目录规范文档 | ✅ `docs/release-evidence/manifest.schema.json` v1.0.0（draft 2020-12）+ `docs/release-evidence/README.md`（含与 L596 逐行裁剪对照 + 三步操作） |
| (b) 校验脚本 + 单测 | ✅ `backend/scripts/validate_release_manifest.py` + `backend/tests/unit/test_validate_release_manifest.py`（**168 测试**） |
| (c) 示例 manifest（D5 证据回填） | ✅ `docs/release-evidence/example-backfill-d5/journeys/J08/manifest.json` |
| (d-1) 校验脚本对示例 exit 0 | ✅ `--all` exit 0（artifact checksum 与磁盘逐字节比对，默认开启） |
| (d-2) 对畸形 fixture exit 1 | ✅ 结构层（脏树/缩写 SHA/路径穿越）与语义层（空心 E5：S2/S3/S9/S11/S12 逐条点名）各有复现 |
| (d-3) pytest 新测试全绿 | ✅ 168 passed（backend venv + CI 等价干净 venv 双跑） |
| CI 环境自足（readme-claims 首跑教训） | ✅ 在**只装 `jsonschema`+`pytest` 的干净 venv、python 3.9.6**（比 CI 的 3.12 更老）上复跑全绿 |
| 硬边界 `test.yml` / `readme-claims.yml` 零改动 | ✅ Codex 双轮复核 HEAD 与 index blob 相同 |
| 硬边界 `backend/.gitignore` 禁改（S4 独占） | ✅ 零接触 |
| Codex 对抗审查 | round-1: 2 BLOCKER + 4 HIGH + 3 MEDIUM → 全部整改；存档 `_bmad-output/审查/codex-review-CARD-R-EVD-rounds.md` |
| 红队对抗（5 轴 + 独立复核 + 3 审计） | 67 agent / 5.27M tokens；**24 条确认绕过全部整改**、35 条驳回；存档 `_bmad-output/审查/revd-redteam-2026-08-28.md` |
| **变异测试** | ✅ **77/77 规则被杀死（存活 0）**——逐条删除校验器规则后套件必红，不存在假绿 |

## 做了什么

### 1. `manifest.schema.json`（结构契约）

L596 要求的字段全部落地：candidate SHA（满 40 位、非全零）、`dirty`（发布证据须 false，由 S17 把关——见下方自我纠错）、环境/模型/index SHA、真实命令、skip/mock 声明、起止时间、断言、回滚、脱敏 artifact checksum（**至少一件**）、用户签字（approved 必带 user+at）。另加三块 L596 之外但同为上游要求的：`provenance`（manifest 自身出处）、`slo`（阈值+实测，§12.5 L592）、`release_gates`（E5 的 14 天 dogfood + 恢复演练，§12.5/§12.6）。

### 2. `validate_release_manifest.py`（三层校验，S1–S17 + A0–A3）

- **结构层** jsonschema；
- **语义层 S1–S17**：版本、时区与时序（含签字不得早于收工、事件不得在未来）、断言/回滚与整体判定不矛盾、skip 与等级联动、签字与等级联动、目录一致性、退出码与 `expected_failure` 自洽、字段自洽（产物元数据算术、路径别名去重）、SLO 阈值实测与 waiver（含数值交叉核对、执行者不得自开免责）、provenance 与等级联动、E5 硬门（14 天下限钉死、窗口日期交叉核对、活动量逐项达标）、evidence 解析且非空、E3+ 必须 live 且必须 pass、签字身份（执行者/模型不得自签）、mock/skip 文本痕迹启发式、脏树只允许出现在低等级回填件；
- **产物层 A0–A3**：路径安全（绝对/`..`/控制字符/symlink/越界/`repo://` 指向证据树全拒）+ 存在性 + checksum + 字节数，**默认开启**。

配置面沿用 G1-5 的**双文件指纹契约**：schema 全文 SHA-256 钉在脚本常量里，schema 单边放水 = exit 2 拿不到绿。退出码三档：0 通过 / 1 内容不合格（单份文件的问题不再中断整批）/ 2 真环境错。

### 3. 示例 manifest（D5 回填）

数据取自已归档的 CARD-D5 board-recap 盲测（`_bmad-output/审查/d5-evidence-2026-08-27/`）。它演示的不只是"字段怎么填"，更是**一个不完美的真实状态怎么如实表达**：J08 只覆盖 recap 半程（三段能力当时未实现）→ `result: partial`、两条 skip 声明、六条断言里一条 `not_run`、`signoff: pending`、`evidence_level: E2`。

### 4. CI 门 `.github/workflows/release-evidence.yml`

独立 workflow（`test.yml` 零改动），paths 限证据目录/校验器/schema/裁判测试，只装 `jsonschema`+`pytest`，跑 `--all` + 裁判测试。

## RC 发布门（新增）

`--require-complete <rc>` 是发布前由人跑的门，断言该 RC 下 J01–J10 齐全、**全为 live 实录、跑在同一个候选 SHA 上、全部 E3+ 且全部 result=pass**。CI 的 `--all` 只证明"已入库的 manifest 都自洽"，证明不了"这个 RC 的证据齐了"——这两件事被红队打穿过一次（十条旅程跑在十个不同 commit、全部 E0、全部 fail，旧版 RC 门返回零问题）。

## 过程中的两次自我纠错（值得记录）

首版示例 manifest 我把 `candidate.sha` 填成了 `c823a35f`——**那是把 D5 证据归档进仓的那个提交**，时间 06:21:32，晚于我自己写的 `finished_at` 06:20。也就是说，我声称"在这个 commit 上跑出了这些证据"，而这个 commit 是证据产生之后才存在的。同时我还写进了结案报告根本没记录的 OS 版本、Python 版本、精确命令与退出码。

Codex round-1 的 HIGH 逐条点破。整改：改用执行窗口前的最后一个提交 `91383b1f`，并新增 `provenance` 机制——`mode: reconstructed` + `reconstructed_from` + `unproven_fields`（9 条，逐条说明哪个字段没有原始证据、依据什么推断）。校验器的 S10/S13 把回填件锁死在 E2、禁止签字、不计入 RC 完整性门。

这条教训被固化成两处机械回归：`test_repo_example_candidate_sha_is_not_the_archiving_commit`（钉死不得再用归档提交）与 `test_repo_example_is_declared_reconstructed`（钉死示例必须自陈回填）。

**第二次**：改完之后我以为示例已经诚实了。红队的保真度审计逐条核对归档与 git 事实，又报出 **11 处 overclaim**——最重的一条是断言 D5-4 写「无 vault 内容写入」，而 `canvas-vault/CLAUDE.md` 与 `Dashboard.md` 确实在执行窗口内（06:19:25）被写并随 c823a35f 提交，D5 结案报告自己的判据行还记着这次改动。另外「18 项机械裁判」实测是 16 项、命令表里的脚本路径从未存在、`candidate.branch` 是个不存在的 ref。

其中最有价值的一条是 O4：`candidate.dirty: false` **不是"未经证明"而是"可被证伪"**——执行结束时那两个文件已改且未提交。而 schema 当时把 `dirty` 写死成 `const: false`，**唯一合规的写法就是假话**。整改是放开 schema 并新增 S17：发布证据（live / E3+）仍必须 false，但 ≤E2 的回填件可以如实写 true，代价是它永远升不到 E3+。**约束的设计必须给真话留出口**——这是本卡最该记住的一条。

反向的一条：`candidate.sha` 我原本降格为「最合理推断」，实际上主仓 reflog 直接证明了 HEAD 自 05:30:04 起就是 `91383b1f`、到 06:21:32 才变，完整覆盖执行窗口。已提升为实证并移出 `unproven_fields`。

## 已知边界（诚实声明）

以下几条是**红队实测确认能绕过**的，机械门管不了（README「已知边界」有完整版）：

- 校验器判的是 manifest 的**自洽**，不是事实。一份处处自洽但内容编造的 manifest 它拦不住——那归 G1-6 逐声明审计链。
- 产物可以是与本旅程无关的既有文件；必含字段可以用 1 字符占位符满足；§12.6 每条旅程的「关键硬断言」没有逐旅程落地；`candidate.sha` 只验格式不验它是本仓真实提交。
- S16 的 mock/skip 扫描是启发式，换个措辞就能躲开；SLO 的数值交叉核对只在阈值与实测能解析成同单位数字时才开火。
- CI 的 `--all` 只证明"已入库的 manifest 都自洽"，**不**证明"某个 RC 的证据齐了"；后者要人显式跑 `--require-complete <rc>`（CI 无从知道当前该验哪个 rc）。
- 本卡不跑任何旅程，不产生任何真实 RC 证据。仓内唯一的 manifest 是格式演示件。

## ⛔ 待用户裁决 / 交接（3 项）

1. **`jsonschema` 未在 `backend/requirements.txt` 显式声明**（现为传递依赖，venv 内实测 4.26.0）。校验器缺它时退出 2 报错、不降级放行；CI 显式安装。本卡开跑期间 CARD-DEBT-9 正重建 venv 并独占该文件族，故**不代改**——建议 DEBT-9 合并后补一行。
2. **DEBT-7（required checks 启用）**：`release-evidence.yml` 与 `plugin-ci.yml` 都用 `paths` 过滤，设为全局 required check 会让被跳过的 PR 永远 Pending（GitHub 官方行为）。两个 workflow 头部都写了交接注记。
3. **SLO schema 的 owner 边界**：本卡只定义 J manifest 里"引用哪个 revision + 实测多少 + 达没达标"的记录形状，**阈值定多少**归 CARD-R-SLO 锁版。若 R-SLO 最终选了不同的字段形状，本 schema 的 `slo.measurements` 需按其对齐（届时升 schema 版本 + 重钉指纹）。

## 遗留

- **CI 首跑验证**：本卡按纪律不 push。push 后需确认 `Release Evidence Check` 真绿。
- 本卡新增的两个 workflow（`plugin-ci.yml`、`release-evidence.yml`）都是本车道独占 `.github/workflows/` 的产物，与 DEBT-4/DEBT-7 的后续改动需按 wave 错开。
