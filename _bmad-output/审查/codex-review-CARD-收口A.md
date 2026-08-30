# CARD-收口A 交付物规范符合性复核

## 结论

**需再一轮。**

本卡代码、CI 最终脚本和合并后测试目前均可复现为绿，但交付物存在 **4 条 HIGH 级“自述与事实不一致”**。按验收单头部规则，`HIGH > 0` 必须再开一轮，不能验收。

本轮定位并检查了六个 `CARD-收口A` 提交：

```text
fe60b3f8  S3 CI 接入及 round-23
9e24ef40  G5-9 首轮整改（含误提交的拼接报告）
4748bad2  S3 合并 trunk
06dc6955  碰撞恢复及并行复核处置
c0912962  S6 合并 trunk
7802d67c  最终验收单、证据与维护卡 B
```

> 重要区分：**S3/S6 当前代码判据可合并，不等于 CARD-收口A 的交付物可验收。**

## HIGH 发现

### HIGH-1 — 明确必交的 G5-4 定向复核 ③b 未产出，验收单还将其漏出完成条件表

第六批手册明确要求再做一轮 G5-4 定向 Codex 并保存非空存档，见[第六批开跑手册:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/implementation-artifacts/goal-cards/2026-08-29-第六批开跑手册-6车道7卡.md:63)。该要求是主干 `a9c8b97c` 新增的，本卡最终文档和两次合并均已承认并使用该主干，不能以“开工时没有”为由排除。

但[验收单完成条件表:33-39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/验收单/UAT-CARD-收口A-S3S6四项收口与两分支合并准备-2026-08-30.md:33)只列 ①②③④⑤，完全没有 ③b；六个本卡提交也未新增 G5-4 报告。

```bash
git -c core.quotePath=false ls-tree -r --name-only HEAD |
  rg 'codex-review-CARD-G5-4(\.md|-round[2-5]\.md)$' |
  wc -l
# 5

git log --oneline 4717a2cd..c0912962 -- \
  '_bmad-output/审查/*G5-4*'
# 无输出
```

现有 5 份仅为 base、round2–round5。既有 `round6-终裁复核-处置.md` 是 workflow 终裁，不是新一轮定向 Codex，且在本卡前已经存在。

因此，“G5-4 实存 5 轮”的历史计数正确，但不能替代 ③b 的新交付要求。

### HIGH-2 — 并行 G5-9 报告仍至少残留 1 BLOCKER / 1 HIGH，却以“升级用户”代替下一轮

停轮规则确实位于验收单第一个实体章节头部，见[验收单:9-11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/验收单/UAT-CARD-收口A-S3S6四项收口与两分支合并准备-2026-08-30.md:9)。结构位置合规。

但并行完整复核的正式裁决是 **BLOCKER 2 / HIGH 4 / MEDIUM 5 / LOW 1**，见[并行报告:19-22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/codex-review-CARD-G5-9-主session独立复核-2026-08-30.md:19)。合并处置后：

- B2 仍标为 `BLOCKER，部分处置 + 升级用户`，见[处置表:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/codex-review-CARD-G5-9-两份复核合并处置.md:47)。
- H6 仍标为 `HIGH，升级用户裁决`，见[处置表:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/codex-review-CARD-G5-9-两份复核合并处置.md:52)。
- 已提交产物中没有用户重分级或关闭裁决，也没有后续完整复核清零。

验收单自己在[306-310 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/验收单/UAT-CARD-收口A-S3S6四项收口与两分支合并准备-2026-08-30.md:306)承认“按停轮规则本应再一轮”，随后又在[312 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/验收单/UAT-CARD-收口A-S3S6四项收口与两分支合并准备-2026-08-30.md:312)重申“HIGH>0 不开轮是违规”，构成直接自相矛盾。

两项升级理由本身不是捏造：

- B2：近几批 125 个提交中，113 个标题使用 `BATCH/CARD`；仅 3 个含 `PLAN-`，均为计划文档型 `PLAN-CLS-PRODUCTIVITY...`，数字型 `PLAN-[0-9]+` 为 0。与此同时根规则仍要求 `commit 含 PLAN-NNN`，见[CLAUDE.md:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/CLAUDE.md:13)，而总账又规定“commit 带批次标记”，见[总账:471](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:471)。**规则与批次实践冲突的论证成立。**
- H6：同一总账第 471 行确实明确把 G5-9 frontmatter 兼容形状列为“需用户拍板”。

因此，**升级用户是正当的阻塞处置，但不是清零裁决**。正确状态应是“等待用户裁定，裁定后再做有效复核”，不能直接结案。

### HIGH-3 — 验收单把旧勘探表写成“与实际合并完全一致”

[验收单:350-355](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/验收单/UAT-CARD-收口A-S3S6四项收口与两分支合并准备-2026-08-30.md:350)称：

- `merge-tree` 与实际合并完全一致；
- S3/S6 自 base 改动为 75/40；
- S6 实际冲突为 0。

实际为：

```bash
git diff --name-only 37387a86..4748bad2^1 | wc -l
# 82

git diff --name-only 37387a86..c0912962^1 | wc -l
# 48

git merge-tree 37387a86 06dc6955 a9c8b97c
# CURRENT_TASK.md: changed in both，并出现冲突标记
```

75/40/零冲突只对应早期 tips `9014f313`、`4717a2cd` 与旧 trunk `2164b498`。同一验收单在[373-381 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/验收单/UAT-CARD-收口A-S3S6四项收口与两分支合并准备-2026-08-30.md:373)和[387-390 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/验收单/UAT-CARD-收口A-S3S6四项收口与两分支合并准备-2026-08-30.md:387)又正确写成 S6 实际有 1 处冲突，属于同文事实冲突。

### HIGH-4 — S3 的 Clear Context 恢复锚点写错实际合入主干

[S3 `CURRENT_TASK.md:5`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:5)写的是“已合并主干 `2164b498`”，实际合并提交第二父为：

```bash
git rev-parse 4748bad2^2
# a9c8b97ccc33f50c8255cac7fb6b53d9945b84e6
```

该文件[17-18 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:17)又称冲突已逐处人工解决。Reflog 中最初 merge 提交 `5d83205b` 后仅 amend 为 `4748bad2`；两者 tree 完全相同：

```bash
git diff --exit-code 5d83205b^{tree} 4748bad2^{tree}
# exit 0
```

即提交信息后来改成了 `a9c8b97c`，恢复锚点正文仍遗留旧 SHA。这不是普通措辞问题，而是恢复上下文的事实锚点错误。

## MEDIUM / LOW 发现

### MEDIUM-1 — “完全复刻 workflow env”不实

[ci-equivalence.md:3-5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/closeout-a-evidence/ci-equivalence.md:3)称完全复刻 env，但 runner 在本地 `backend/` 下运行，存在 ignored `.env`；应用会加载它，见[`app/__init__.py:10-16`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/__init__.py:10)，根 conftest 又会导入 Settings/app，见[`tests/conftest.py:21-23`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/conftest.py:21)。

不输出值、只做哈希对照时，本地与“无 `.env` 的 CI”模拟有 6 个 Settings 字段不同。此外：

```bash
backend/.venv/bin/python -m pip check
# moviepy 2.2.1 requires pillow<12.0, but pillow 12.3.0 is installed
```

因此可证明“本地跑过”，不能称“进程环境完全等价”。未发现这会真实导致 CI 变红，故不升 HIGH。

### MEDIUM-2 — `303+213=516` 不能证明“零交叉污染”，且 runner 与 workflow 顺序不同

[ci-equivalence.md:19-24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/closeout-a-evidence/ci-equivalence.md:19)用通过数相加证明“无共享 fixture / ContextVar 泄漏”，这个推理过强。

集合相同，但顺序不同：

- runner：15 个旧文件全部结束后，再跑 2 个新文件，见[runner:11-30](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/closeout-a-evidence/ci-equivalence-runner.sh:11)。
- workflow：2 个新文件位于最后两个旧 unit 文件之前，见[`test.yml:138-141`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/.github/workflows/test.yml:138)。

相同计数只能证明该次顺序没有失败，不能逻辑证明无全局状态污染。当前按最终 workflow 顺序独立复跑 517+1 通过，所以这是论证口径问题，不是流水线破坏。

### MEDIUM-3 — “S6 只依赖 stdlib + pytest、与后端服务完全绝缘”不实

相关自述见[merge-readiness.md:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/审查/closeout-a-evidence/merge-readiness.md:100)和[149-150 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/审查/closeout-a-evidence/merge-readiness.md:149)。

实际依赖包括：

- [`test_g5_9_recap_exam.py:202-216`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:202)导入并调用 `app.services.board_manifest_service.scan_vault`。
- [`test_recap_scan_signals.py:384-396`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/test_recap_scan_signals.py:384)使用 `build_manifest`，后续还使用 `_node_role` 和 PyYAML。
- 根 conftest 无条件导入后端配置和 `app.main`。

不过实际合并目标未改相关 service/vault，160 项也已通过；“可合并”结论仍有实跑支撑，只是“天然绝缘”的理由不成立。

### MEDIUM-4 — 维护卡 B 的数字旁证有两处误计

[维护卡 B:20-22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/implementation-artifacts/goal-cards/2026-08-29-维护卡B-board-recap-verifier收紧.md:20)称 round-5 有 3 个误伤，原处置表实际有 4 个不同输入：`统计口径尚未一致`、`说明十分清楚`、`口径一致`、`legitimate-nested-list`。

[维护卡 B:109-116](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/implementation-artifacts/goal-cards/2026-08-29-维护卡B-board-recap-verifier收紧.md:109)又称代码中有“5 种合法用法”；当前 [`recap_scan.py:1337-1358`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1337)实际编号为 ①–⑦，第⑦还包含两个正则，即 7 个类别、8 个模式。

这不推翻移交正当性，但使“5/8 数字吻合”的旁证不可靠。

### MEDIUM-5 — 碰撞后的命名和“逐文件预检”仍没有形成可验证控制

恢复后的两份文件当前名称不同，但 T2 报告仍使用通用名 `codex-review-CARD-G5-9.md`，没有采用其自己建议的 `-T2车道` 后缀，也没有可执行的 `test -e` 防重名门，见[报告:29-31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/codex-review-CARD-G5-9.md:29)。因此只能避免本次两份文件重名，不能保证下次不再碰撞。

[验收单:228-230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/验收单/UAT-CARD-收口A-S3S6四项收口与两分支合并准备-2026-08-30.md:228)称后续两个提交均先逐文件核对字节数、行数和编码。当前内容确实可解码，`c0912962` 也记录过 38 个主干 blob 的字节比对；但 `c0912962`、`7802d67c` 均没有保存“所有文件、行数、字节数、编码、核对发生在 commit 前”的逐文件 receipt。故该历史流程声明**无法独立证实**。

### LOW-1 — merge-base 证据使用可变分支名，原命令现已不能原样复现

[merge-readiness.md:35-38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/审查/closeout-a-evidence/merge-readiness.md:35)记录的分支名命令现在会返回 `a9c8b97c`，不再返回 `37387a86`。

固定实际 merge parents 后可复现：

```bash
git merge-base 4748bad2^1 4748bad2^2
git merge-base c0912962^1 c0912962^2
# 均为 37387a8662e9dd646fad5628841679d777cb7eae
```

历史结论成立，问题只是证据用了可变 ref。

## 其余逐项复核结果

### 一、停轮和历史轮次

| 对象 | 正式残留计数 | 本卡动作 | 判定 |
|---|---:|---|---|
| G3-1 round-23 | 0 / 0 / 2 / 8 | 登记 M/L，不开新轮 | 合规 |
| G5-9 本车道 round-1 | 0 / 4 / 8 / 2 | 整改并尝试 round-2 | 该步合规 |
| G5-9 round-2 | 无有效终稿，不能计数 | 未形成清零裁决 | 不可作为停轮依据 |
| G5-9 并行完整报告 | 2 / 4 / 5 / 1 | 处置后至少仍有 1B/1H，未再审 | 违规 |
| G5-4 round-5 | 没有规范四级残留清单 | 上游另要求 ③b | ③b 未完成 |

G3-1 round-23 的计数见[报告:162-177](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/codex-review-CARD-G3-1-round23-2026-08-29.md:162)；G5-9 本车道计数见[报告:228-235](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/codex-review-CARD-G5-9.md:228)。

MEDIUM/LOW 均有登记：本车道见[`round1-处置.md:45-61`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/codex-review-CARD-G5-9-round1-处置.md:45)，并行报告见[合并处置:53-58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/codex-review-CARD-G5-9-两份复核合并处置.md:53)。未发现静默省略。

历史存档实数：

```text
G3-1：本卡前 22 份；加入 round-23 后当前 23 份。
G5-4：当前 5 份 Codex 报告。
```

因此验收单对手册 `19/6` 的更正本身属实。

### 二、CI 改动、本地验证与 shell 语义

- `fe60b3f8` 对 `.github/workflows/test.yml` 是 **+10/-0**：8 行续写既有注释项、2 行加入测试清单，见[`test.yml:100`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/.github/workflows/test.yml:100)和[`test.yml:138`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/.github/workflows/test.yml:138)。
- 未改 flags、env、timeout、其他 job；本卡净增量没有改其他 workflow。
- 三份 JUnit 实物仍在，结果为 `303 passed`、`516 passed + 1 skipped`、`213 passed + 1 skipped`，与[ci-equivalence.md:8-16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/closeout-a-evidence/ci-equivalence.md:8)一致。不是只写了自述。
- `--junitxml` 落 scratchpad和本地 Python 3.14.4 均诚实披露。它们足以支持“本机确实跑过”，但不足以证明 CI 3.11/3.12 的真实执行；实际也未远端触发 CI。
- 最终 `Run tests` 脚本独立替换 pytest 为 `printf` 后：**exit 0、17 个 `.py`、尾部 flags 全部到达**。
- 重构文档所述错误形态后：YAML 可解析，但 shell **exit 127，只到达 13 个 `.py`**。论断成立；最终版本无此问题。精确的历史第一版 blob 未留存，只能验证所描述形态的 shell 行为。

`ci-preflight.md` 四项结论均基本属实，见[表格:6-11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/closeout-a-evidence/ci-preflight.md:6)：

- `fsrs==6.3.1` 已钉版。
- `fsrs_bridge.py` 以及 `.claude/skills` 下实际使用的文件均 tracked；Git 本身不跟踪目录，只跟踪其内容。
- 唯一 skipped 自带 `Path.is_file()` 守卫；CI checkout 没有 `learning_events.jsonl` 时会 skip，不会变红。
- backend paths 和 trunk branch trigger 均覆盖；`card/*` push 不触发也已如实声明。

### 三、合并准备

- `37387a86` 可由固定 merge parents 重现。
- 主仓陷阱也可重现：错误来自把对照 ref 换成 `main`/裸 `HEAD`，不是物理 cwd 本身。文档[59-61 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/审查/closeout-a-evidence/merge-readiness.md:59)对此限定准确。
- 主干确实由 `2164b498` 前进到 `a9c8b97c`；锁定 blob、unit conftest、canvas-vault 的复算均支持文首更正。两条旧结论也已在原表[97-98 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-closeout/_bmad-output/审查/closeout-a-evidence/merge-readiness.md:97)就地标注被推翻。
- 独立按当前合并后工作树重跑：
  - S3 三文件：**219 passed + 1 skipped**
  - S3 workflow 17 文件：**517 passed + 1 skipped**
  - S6 两文件：**160 passed**
- 因此当前代码“可合并”并非只凭文件不重叠；另查 blob、conftest、vault、依赖面并做了实跑。只是 S6 “完全绝缘”理由过强，见 MEDIUM-3。
- `-X ours/theirs` 是 Git 对象库无法证明的命令行负事实。S3 的合并结果不同于两侧 blob，支持人工编辑；S6 结果与 ours 相同，无法区分人工选 ours 还是策略选项。未发现使用 `-X` 的证据，但也不能独立证明绝未使用。

### 四、维护卡 B

移交理由成立，不属于“回避难做部分”：

- 上游手册本身明确写 ④ 不在本卡，移交维护卡 B，见[手册:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/implementation-artifacts/goal-cards/2026-08-29-第六批开跑手册-6车道7卡.md:65)。
- `_verify_numbers` 当前确是闭世界枚举，收紧裸数字与避免合法语料误杀是双向设计问题。
- 独立全域检索没有找到上游“8 类探针”清单；唯一命中是手册自己的那句话。维护卡把“4+4=8”明确标成推导，而不是出处，这部分诚实。

数字误计见 MEDIUM-4。

### 五、硬边界

| 边界 | 结果 |
|---|---|
| `.github/workflows/` | 本卡自有改动只有 `test.yml`；最终出现的 `plugin-ci.yml`、`release-evidence.yml` 来自主干合并，不是本卡夹带 |
| `recap_scan.py` | `4717a2cd`、`9e24ef40`、`06dc6955`、`c0912962` blob 均为 `7d2da68c…`，verifier 逻辑零改动 |
| live vault | 本卡提交窗口 13:00–14:27，12:30–15:00 内未发现文件 mtime 变化；未发现可归因于本卡的写痕 |

live vault 原本存在大量 dirty/untracked 内容，且没有开工前完整 manifest，因此只能证明“未发现可归因写痕”，不能数学证明绝对零写入。

### 六、跨 session 文件碰撞

两份报告的正文 payload 均完整恢复；恢复文件额外增加了事故来源头部，但来源正文未删改。

```bash
cmp -s \
  <(tail -n +19 codex-review-CARD-G5-9-主session独立复核-2026-08-30.md) \
  <(git show 9e24ef40:_bmad-output/审查/codex-review-CARD-G5-9.md | head -c 9890)
# exit 0
# sha256 4ba556ab7c59c5a6463e6dc1ad38f32742e296aa821994dc72e59084221009b7

cmp -s \
  <(tail -n +58 codex-review-CARD-G5-9.md) \
  <(sed -n '4272,4449p' g5-9-evidence/codex-round1-transcript.txt)
# exit 0
# sha256 65a104a9653b213db5c060dabd6811d76f30f04d5aec708f09b8fd7686439e9a
```

`06dc6955` 的提交信息明确写出了：

- 两个 fd/offset 拼接；
- 损坏文件被 `git add -A` 提交进 `9e24ef40`；
- `9e24ef40` 的提交信息与内容不符；
- 两份恢复来源及字节边界。

描述准确，没有淡化事故。命名和后续预检问题见 MEDIUM-5。

### 七、G5-9 二段整改与 10 个负验证

`_open_exam_dirfd()` 的窄口径声明成立：

- [`recap_exam_build.py:293-325`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:293)打开并校验目录 fd。
- 成功锚定后，[`_atomic_write():352-429`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:352)的创建、link、回读、unlink、fsync 均使用 basename + `dir_fd`。
- `_prepare` 在锚定前仍有 mkdir、probe 和目录打开时的路径解析，undo 也是另一套按路径流程；这些不应被扩写成“整个程序从此完全不解析路径”。

undo 对 leaf symlink 的处理见[`recap_exam_build.py:674-680`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:674)：

- 它确实会拒绝 vault 内合法组织用途的 alias 路径；
- 若产品未来承诺“可通过 alias undo”，这属于功能收缩；
- 当前契约只承诺回退回执中的 `created_path`，直接使用 referent 路径仍可工作，因此未发现对现有承诺的违规；
- 拒绝理由明确说明“避免移走 referent 并留下死链”。

负验证在完整隔离临时副本中独立重跑，未修改三个工作树或 live vault：

```text
baseline：55 passed
A/B/C/D/E/F/G/H/I/J：10/10 均非零退出、对应门变红
还原后：55 passed
源文件 SHA 前后：
516ef31ff026af112394ae347ca066817b0f46f6712a05aab60b0b03efc13752
RESULT: PASS
```

脚本的逐变体 `finally` 恢复和 SHA 核对见[`round1-high-negverify.py:252-305`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:252)。

静态核查未发现仍“只改一层而因别的原因变红”的变体：

- D 同时关闭 prepare 守卫、symlink probe、dirfd 三项校验。
- I 同时关闭 dirfd 三项校验，并把 open/link/read 三个操作退回路径调用。
- 其余变体对应单一且唯一的形状校验、发布字节、并发删除、留痕回读、leaf symlink、unlink 前 identity 性质。

文档所称 D/I 首次只弱化一层而误判“不承重”的事故属实；最终脚本已经修正。

## 未能完全验证的部分

- Git 对象和 reflog不保存完整 merge 命令行，无法绝对证明没有用过 `-X ours/theirs`。
- 合并后历史三次 pytest 没有持久化 stdout/JUnit；本轮当前状态独立复跑结果吻合，但不能证明历史时刻的进程事件。
- 第一版错误 YAML/shell 脚本没有保存精确 blob，只能复现其所述 shell 形态。
- live vault 没有开工前完整 manifest，无法证明绝对零写入，只能确认无可归因痕迹。
- 审计期间另一 session 在 T2 工作树新增了未跟踪的 `closeout-a-evidence/移交与裁决清单.md`。该文件不是六个 `CARD-收口A` 提交的一部分，本轮未读取、未触碰、未纳入结论。

## 残留清单

| 级别 | 数量 |
|---|---:|
| BLOCKER | **0** |
| HIGH | **4** |
| MEDIUM | **5** |
| LOW | **1** |

按本卡头部停轮规则：**HIGH 4 > 0，CARD-收口A 必须再开一轮，当前不可验收。**
