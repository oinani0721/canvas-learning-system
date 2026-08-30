# Release 旅程证据目录规范（A06 轻量版）

> **卡**: BATCH-2026-08-28-第五批 / CARD-R-EVD
> **上游真相源**: 生产力化长期 Goal 计划书 §12.4 A06（L569）+ §12.5（E0-E5 等级、SLO 锁版、降级规则）+ §12.6（L596 manifest 必含字段、J01–J10、14 天 dogfood）
> **schema**: [`manifest.schema.json`](manifest.schema.json)（v1.0.0，JSON Schema draft 2020-12）
> **校验器**: `backend/scripts/validate_release_manifest.py`
> **裁判**: `backend/tests/unit/test_validate_release_manifest.py`（168 测试；对校验器 77 条规则做过逐条变异测试，删任一条都会让套件变红）

## 这是什么

J01–J10 十条真实用户旅程（计划书 §12.6）跑完之后，证据不能只是聊天记录里的一句"跑过了"。本目录规定：每条旅程的每次证据留存长什么样、放哪儿、以及**机器怎么判断它有没有自相矛盾**。

一句话边界：**校验器只裁决 manifest 自身的机械自洽**——字段齐不齐、格式对不对、跨字段矛不矛盾、（可选）artifact checksum 和磁盘对不对得上。它**不裁决旅程真的跑过、断言真的成立**。E 级真伪由 G1-3 能力证据台账与 G1-6 逐声明审计链负责；本器唯一能挡的，是"manifest 自己就说不圆"的那类失实（带着 skip 声明标 E3、断言 fail 了整体还写 pass、回滚失败却宣称通过、E5 没跑够 dogfood）。

**schema 与校验器是一个整体**：只读 schema 会高估宽松度——大量约束（等级联动、SLO 达标、provenance 与等级的关系、dogfood 窗口自洽、路径越界）在语义层 S1–S17 与产物层 A0–A3 实施。

这套规则经过一轮 Codex 静态审查（2 BLOCKER + 4 HIGH + 3 MEDIUM）和一轮 5 轴红队实测对抗（24 条经独立复核确认的绕过），核心教训写在这里免得后人重犯：**凡是由 manifest 作者自己填的"标准"都不是标准**。第一版里 dogfood 的天数下限、skip 与否、SLO 达没达标，全是作者自报，于是 `days_required=1` 就能满足"14 天门"、命令行写满 `GRAPHITI_MOCK=1` 也能声明"零 mock"。现在这些要么钉死下限，要么与其他字段交叉核对。

## 目录结构

```
docs/release-evidence/
├── README.md                  ← 本文件
├── manifest.schema.json       ← 结构契约（改它必须同步校验器里的 SHA 常量）
└── <rc>/                      ← 一个 release candidate 一个目录
    └── journeys/
        ├── J01/
        │   ├── manifest.json  ← 必需，本规范的核心
        │   └── *.txt / *.log  ← 证据产物（脱敏后），checksum 记在 manifest 里
        └── J08/
            └── manifest.json
```

- `<rc>` 目录名 = manifest 里的 `rc` 字段（S6 规则强制一致）；
- `Jxx` 目录名 = manifest 里的 `journey_id`（同上）；
- 现有示例：[`example-backfill-d5/journeys/J08/`](example-backfill-d5/journeys/J08/)——用已归档的 CARD-D5 board-recap 盲测证据回填的**格式演示件**。它自陈 `provenance.mode = reconstructed`，因此被 S10/S13 锁死在 E2、禁止签字、且不计入任何 RC 完整性门。

## 新增一条 Jxx 证据的三步操作

**第 1 步 · 建目录、放产物**

```bash
mkdir -p docs/release-evidence/<rc>/journeys/J07
# 把脱敏后的日志/输出/hash 清单放进去，然后取 checksum：
shasum -a 256 docs/release-evidence/<rc>/journeys/J07/*
wc -c docs/release-evidence/<rc>/journeys/J07/*
```

产物必须脱敏：不含 secret、不含用户绝对路径、不含私人笔记正文。原样收录时把 `redacted` 填 `false`（意思是"我确认过它本来就不含敏感内容"），做过脱敏则填 `true` 并在 `redaction_note` 说明删了什么。至少要有一件产物——零产物的"证据"不是证据。

**第 2 步 · 写 manifest.json**

拷贝示例件当骨架，逐字段替换。填写时的五条硬性提醒：

- `candidate.sha` 要**完整 40 位**，且必须是**执行期 checkout 的那个 commit**。事后把"归档证据的那个提交"填进来是最常见的错误——它在执行时还不存在（示例件的 `notes` 记录了本卡自己踩的这一脚）。`candidate.dirty`：发布证据必须是 `false`（脏树上跑出来的东西不成立）；只有 `mode=reconstructed` 且 ≤E2 的回填件才允许如实写 `true`——代价是它永远升不到 E3+，这正是应有的代价（S17）。
- `provenance.mode` 二选一：`live`（执行期实录，`unproven_fields` 必须为空）或 `reconstructed`（事后回填，必须给 `reconstructed_from` 并逐条列出无证据支撑的字段）。回填件最高 E2、不能签字、不计入 RC 门。
- 有 skip 或 mock 就在 `execution.skips_or_mocks` 里**逐条列出来**。E3 及以上不允许存在任何 skip/mock（§12.5）。
- 时间戳必须带时区偏移（`+08:00` / `Z`）。本仓有过 UTC/沪时混算导致误诊的教训（`docs/known-gotchas.md`）。注意 JSON Schema 的 `format: date-time` 默认只是注解不校验，真正把关的是校验器的 S2。
- `slo.measurements` 逐项写阈值与实测。E3 及以上必须有 revision 且至少一条实测；未达标而整体仍判 `pass` 时，必须附用户 `waiver`（§12.5：未达标只能判失败，或经用户事前/书面接受后降级为限制）。

**第 3 步 · 跑校验**

```bash
# 单份（产物 checksum 默认会真验）
backend/.venv/bin/python backend/scripts/validate_release_manifest.py \
    docs/release-evidence/<rc>/journeys/J07/manifest.json

# 全量
backend/.venv/bin/python backend/scripts/validate_release_manifest.py --all

# RC 发布门：断言某个 rc 下 J01–J10 齐全、全为 live 实录、同一候选 SHA、全部 E3+ 且通过
backend/.venv/bin/python backend/scripts/validate_release_manifest.py --require-complete <rc>
```

退出码：`0` 通过 · `1` 内容不合格 · `2` 配置/环境错。分档口径：**单份文件的任何问题都是 `1`**——包括 JSON 语法错、文件不存在、编码错、顶层不是对象——校验器会把它记成 `[load]` 一条并**继续校验后面的文件**（早先一个手抖的逗号会中断整批，还被报成"环境错误"，把后面所有违规一起藏起来）。`2` 只留给真正的环境问题：schema 指纹不符、缺 `jsonschema` 依赖、证据根目录不存在。

产物 checksum 真验**默认开启**；`--skip-artifact-verify` 是显式弃权，弃权时输出会打一行 `⚠️ 已弃权`。

CI 侧由 `.github/workflows/release-evidence.yml` 在证据目录/校验器/schema 变更时自动跑 `--all` + 裁判测试。**注意 CI 的这道门只证明"已入库的 manifest 都自洽"，不证明"某个 RC 的证据齐了"**——后者要显式跑 `--require-complete`，发布前由人执行。

## 字段速查

| 字段 | 说明 |
|---|---|
| `schema_version` | 本 manifest 遵循的 schema 版本；major 不被校验器支持时直接 S1 打红，不做尽力而为解析 |
| `journey_id` / `journey_title` / `rc` | 身份，与目录结构强一致（S6） |
| `provenance` | `mode`(live·reconstructed) / `reconstructed_from` / `unproven_fields[]` —— manifest 自身的出处 |
| `candidate` | `sha`（满 40 位、非全零、执行期 HEAD）/ `branch` / `dirty`（发布证据须 false，见 S17）/ `worktree` |
| `environment` | `host_os` / `runtimes` / `models`（无模型参与给空数组）/ `index_sha`（不涉索引须显式 `null` + `index_sha_null_reason`）/ `services` |
| `execution` | `started_at` / `finished_at`（带时区）/ `operator` / `commands`（真实命令，非零退出须标 `expected_failure`）/ `skips_or_mocks` |
| `assertions` | 逐条 `id` / `statement` / `method`（怎么验的）/ `result`(pass·fail·not_run) / `evidence`（须逐字等于某个 artifact 路径） |
| `rollback` | `performed` / `method` / `result`(pass·fail·not_applicable) / `reason` |
| `artifacts` | 至少一件。`path`（相对本目录，或 `repo://` 相对仓库根）/ `sha256` / `bytes` / `redacted` |
| `slo` | `manifest_revision`（引用 R-SLO 锁版件）+ `measurements[]`（metric/threshold/measured/method/meets/waiver） |
| `release_gates` | **仅 E5**：`dogfood`（协议版本/RC SHA/起止/天数/活动量）+ `recovery_drill` |
| `signoff` | `status`(pending·approved·rejected)；approved 时**必须**同时有 `user` 与 `at` |
| `evidence_level` | E0–E5（§12.5）。文件名含 e2e、CI 绿、fixture 都**不**自动升级 |
| `result` | 整体判定 pass·fail·partial；任一断言非 pass、或回滚 fail 时不得写 pass |

## 语义与产物规则（校验器实施，schema 表达不了的部分）

| ID | 规则 | 依据 |
|---|---|---|
| S1 | `schema_version` major 必须被校验器支持 | 防跨版本尽力而为解析 |
| S2 | 所有时间戳必须带时区（含 `signoff.at`、`waiver.at`、`recovery_drill.at`）；`finished_at ≥ started_at` | known-gotchas 时区教训；`format` 默认不校验 |
| S3 | 任一断言非 pass、或 `rollback.result=fail` → `result` 不得为 pass | 防"整体绿、细项红" |
| S4 | skip 声明自洽；E3+ 不得有任何 skip/mock | §12.5「无 skip 黑盒 E2E」 |
| S5 | E4/E5 必须 `signoff.status = approved`（schema 另强制 approved 带 user+at） | §12.5 E4 = User-verified |
| S6 | `journey_id` / `rc` 与目录名一致，且在 `<rc>/journeys/<Jxx>/` 下 | 防证据错位归档 |
| S7 | 命令非零退出必须显式标 `expected_failure` | 防失败命令混进"跑通了" |
| S8 | `index_sha=null` 须给理由；artifact 路径不得重复；rollback 各字段自洽 | 防省略字段冒充"无关" |
| S9 | E3+ 必须有 SLO revision **且**至少一条阈值/实测；未达标而未判 `fail` 须有用户 waiver **且**写进 `known_limitations`；waiver 的 `accepted_by` 不得是执行者本人；阈值与实测能解析成同单位数字时做尽力而为的数值交叉核对 | §12.5 L592 |
| S10 | 回填件（reconstructed）最高 E2、不得签字、必须列出 `unproven_fields`；实录（live）不得有 `unproven_fields`、也不得带 `reconstructed_from` | 防事后重建冒充实跑证据 |
| S11 | E5 必须有 `release_gates`：dogfood 实跑 ≥14 天（下限钉死在校验器里，**不由 `days_required` 自报**）、零漏日、起止日期能解析且窗口装得下所报天数、窗口不在未来、`activity_counts` 与 `activity_minimums` 项目一致且逐项达标、`rc_sha` 与 candidate 一致、恢复演练 pass；低等级不得挂 `release_gates` | §12.5 E5 + §12.6 14-day dogfood protocol |
| S12 | `assertions[].evidence` 必须解析到已登记 artifact，且该产物非空 | 防悬空引用与空文件充数 |
| S13 | E3+ 必须 `provenance.mode = live` | §12.5 E3 = clean RC 上实跑 |
| S14 | E3+ 必须 `result = pass` | "Verified" 蕴含通过——一条没跑通的旅程不构成验证 |
| S15 | `signoff.user` 不得等于 `execution.operator`，也不得是本次用到的模型名 | E4 = 用户验收，执行者与模型不能自签 |
| S16 | E3+ 且声明零 skip 时，扫命令/注记/断言方法里的 mock/skip 痕迹（启发式） | 防"命令里明写 mock、声明里说没有" |
| S17 | `dirty=true` 只允许出现在 `mode=reconstructed` 且 ≤E2 的回填件里 | L596 要求发布证据 dirty=false；但 schema 若写死 `const false`，一份诚实回填就只能在这里说假话 |
| A0 | artifact 路径不得绝对/`..` 上跳/含控制字符/含 symlink/解析后越界；`repo://` 不得指向证据树内部（默认档也检查，越界条目绝不会被读取） | 无约束即任意文件读取 + hash oracle。控制字符单列是因为 schema 正则的 `.*` 不跨行——`ok.txt\n../../etc/passwd` 能过正则，靠 A0 兜住；`repo://` 指向别的 RC 会让一份产物同时给多个 RC 背书 |
| A1–A3 | artifact 存在、sha256 与 bytes 与磁盘一致（**默认开启**）；`repo://` 目标不符时只报不符、不回显实际摘要与字节数 | checksum 不是抄上去就算；回显会把 CI 日志变成任意仓内文件的 hash/size oracle |

装载期还有两道：重复 JSON key 直接拒收（标准库会静默取后值，`{"dirty":true,"dirty":false}` 可骗过一切校验）；顶层非对象按内容不合格（退出 1）而非环境错。

## 与计划书 L596 的对照（裁剪记录）

简化路线要求轻量落地，以下是**逐项交代**——哪些原样保留、哪些加严、哪些裁剪了、为什么。

| L596 原文要求 | 本版处置 | 说明 |
|---|---|---|
| candidate SHA | ✅ 原样（加严） | 强制满 40 位；文档与示例都点名"别填归档提交" |
| `dirty=false` | ⚠️ 改由语义层强制 | 早先 schema 写死 `const: false`，结果**逼得一份诚实回填只能在这里写假话**（D5 执行期工作树确实是脏的）。现放开为 boolean，由 S17 把住发布线：live 与 E3+ 必须 false，≤E2 的回填件可以说真话 |
| 环境 | ✅ 原样 | `host_os` + `runtimes` + `services` |
| 模型 | ✅ 原样 | `models[]`，含 role/name/version/endpoint |
| index SHA | ⚠️ 收窄 | 必需字段，但允许显式 `null` + 必填理由。**裁剪理由**：J06/J07/J08 等旅程本就不经检索索引，强填一个假 SHA 比诚实写 null 更糟 |
| 真实命令 | ✅ 原样（加严） | 至少一条，含 cwd 与 exit_code；非零退出须标 `expected_failure` |
| skip/mock 声明 | ✅ 原样（加严） | 结构化为 `{declared, items[{what, why}]}`，并由 S4 与 E 级联动 |
| 起止时间 | ✅ 原样（加严） | 强制带时区 + 先后顺序，且手验（不依赖 `format` 注解） |
| 断言 | ✅ 原样（加严） | 逐条含 method 与 result；`evidence` 必须解析到 artifact（S12） |
| 回滚 | ✅ 原样（加严） | 不适用时须 `not_applicable` + reason；`fail` 时整体不得 pass（S3） |
| 脱敏 artifact checksum | ✅ 原样（加严） | **至少一件**（`minItems: 1`，防零产物真空通过）；路径受 A0 安全约束；checksum **默认**重算比对（`--skip-artifact-verify` 才弃权）|
| 用户签字 | ✅ 原样（加严） | approved 必须同时有 `user` 与 `at`，且 `at` 须为带时区的合法时间——**光一个 approved 字符串不算签字** |

**§12.5 / §12.6 的额外硬门（L596 之外，但同为上游要求）**：SLO 阈值与实测（S9）、E5 的 14 天 dogfood 与恢复演练（S11）、E3+ 必须 live 实录（S13）均已落地为机械规则。

**主动裁剪掉的（不在本版）**：

1. **Phase 0G 的两级 receipt 链 / boundary receipt 仪式** —— 按已改道的简化路线（总账 v2 R-EVD 卡文：「治理按已改道决策走轻量存档，不引入 Phase 0G receipt 链」）。证据的可信度靠 checksum + git 历史 + 用户签字位，不靠额外的仪式性收据文件。
2. **多签 / 审批工作流** —— `signoff` 只有单个用户签字位。个人产品，甲方就一个人。
3. **自动采集器** —— 本卡只做规范 + 校验器 + 样例，不做"跑完旅程自动生成 manifest"的工具。旅程本体的执行归各 J 卡（G2-11 / G5-11 / R-J0x）。
4. **SLO 阈值本体的定义** —— 本 schema 记录"引用哪个 revision + 本旅程实测多少 + 达没达标"，但**阈值本身定多少**由 CARD-R-SLO 锁版，各卡复用不另造格式（总账 v2 R-SLO 的 owner 裁定）。注意这不同于"不记录阈值"——L592 要求 J manifest 记阈值与实测，本版 S9 是强制的。

## 已知边界（诚实声明）

以下几条是**红队实测确认能绕过**的（`_bmad-output/审查/revd-redteam-2026-08-28.md`），写在这里以免有人以为"过了校验就等于证据成立"：

- 校验器判的是 manifest 的自洽，不是事实。有人可以写一份处处自洽但内容编造的 manifest——那属于 G1-6 逐声明审计链的地盘，不是机械门能挡的。
- 产物真验只覆盖 manifest 里列了的产物；旅程跑出来但没写进 manifest 的东西，它看不见。
- **产物可以是与本旅程无关的既有文件**：`artifacts` 只验路径安全与 checksum 一致，无从知道那份文件是不是这次旅程产生的。把 `repo://README.md` 登记成 J01 的证据，checksum 真验照样绿。
- **必含字段可以用 1 字符占位符满足**：`host_os: "x"`、`operator: "x"`、`method: "x"` 都合法。字段在场是机械门能保证的上限，字段有意义不是。
- **§12.6 每条旅程的"关键硬断言"没有落地**：校验器不知道 J01 必须验 preflight→安装→activate→rollback 全链，只知道"至少有一条断言"。`journey_id` 目前只用于目录一致性。逐旅程断言清单如要机械化，需要一份 per-journey 规格表（本卡未做，属后续卡）。
- **`candidate.sha` 只验格式不验存在**：40 位 hex 即可（全零 null SHA 已单独拒绝），校验器不去 `git cat-file` 确认它是本仓真实提交——RC 可能来自浅克隆或尚未推送的分支。
- **SLO waiver 的时间不受约束**：§12.5 明确允许"经用户事前**或书面**接受后降级为限制"，所以事后补开的 waiver 本身不违规；机械门只要求它有签署人、有时间，并强制把这次未达标写进 `known_limitations`。真正被禁的"看完结果再降低门槛"是改阈值，而阈值来自 R-SLO 锁版件、不在本 manifest 里定义。
- **skip/mock 的命令扫描是启发式**：S16 只按已知开关模式（`*_MOCK=1` / `SKIP_*=1` / `--ignore=` / `-m "not ..."` 等）在 E3+ 上报警，换个措辞就能躲开。它拦的是"命令里明摆着写了 mock 却声明零 mock"这种自相矛盾，不是所有 mock。
- SLO 的 `threshold` / `measured` 是自由文本（如 `"≤ 2.5s"` / `"1.8s"`），校验器**不做数值比较**，`meets` 由填写者判定。机械门只保证"阈值、实测、达标结论、采集方法四者都在场，且未达标时不能悄悄判 pass"。数值口径的正确性归 R-SLO 与审计链。
- `jsonschema` 目前不在 `backend/requirements.txt` 里（现为传递依赖，venv 内实测 4.26.0）。校验器缺它时**退出 2 报错，不降级放行**；CI workflow 显式安装。**交接项**：requirements.txt 该显式声明它——本卡开跑期间 CARD-DEBT-9 正在重建 venv 并独占该文件族，故不代改。
