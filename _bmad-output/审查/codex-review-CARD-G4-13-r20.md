> **存档首部（协议 §2.4.1）**
> - 模型：`glm-5.3`（ZAI profile；D-43 换模型）—— `.stderr:5`
> - reasoning_effort：`max` —— `.stderr:9`
> - codex：`OpenAI Codex v0.153.3` —— `.stderr:2`
> - 附加自证：`provider: ZAI`（`.stderr:6`）· `sandbox: read-only`（`:8`）· `session id: 01a0c190-b1b6-7d00-9e63-79852d81bb7d`（`:11`）
> - 命令：`source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G4-13-r20.md)"`
>   （rc=0；stdout > `.md`、日志 > `.stderr`（gitignore，不入库））；**绑定 `64f109bb`（最终 HEAD）**
> - 结论：**B=0 / H=0 / M=0 / L=0**（复核者对被审文件 `git diff --quiet HEAD` rc=0 自证）

---

# CARD-G4-13 r20 终轮复核（只读）

## 0. HEAD / 车道绑定

- 车道：`card/p9-testinfra`
- 当前 HEAD：`64f109bbecb29b0dc94fe433962161337d216516`
- 父提交：`4a24d9482793cd8cd5620eef107ede66aca8168f`
- 本轮复核目标文件 worktree 与 HEAD 完全一致（`git diff --quiet HEAD -- <目标文件>` rc=0）。
- checkout 中仍有本轮审查产物 untracked：`r20` prompt/empty review、`r25-freeze-all-103-*`、`r25-jev-review-*`；它们不影响 HEAD 中的目标金集/manifest/checklist，但说明 `r25-freeze-all-103` 与 Jev 证据不是最终 commit 内证据。对此我没有依赖它们作唯一结论，而是直接重算 Git diff。
- 未改文件、未连 7691/7687/8011、未跑两 runner 非 shadow 模式；只实际重跑了只读 CLI `verify`，rc=0。

---

## ⓪ 裁决完整性 — PASS

独立解析勾选清单与两份主金集后：

- 清单：
  - `<!-- gsid:... -->` = 103 个，唯一 103 个。
  - 每个条目下三选一 checkbox 齐全，且恰好 1 个 `[x]`，无 0/2 勾。
  - 清单 ID 序列与 vault+memory 主集 103 条 ID 完全同序。
  - 分布：relevant 64 / ambiguous 39 / irrelevant 0。
  - 清单 SHA256 实算：`d73430f2ee444590915131bf57abc1e54bb4600ac6c51c86b7aa7a2ff0f8bb92`，与 `_bmad-output/审查/evidence-g413/r25-sync-checklist-20260920T181512.txt:1-4` 一致。
- YAML：
  - vault 75 条：relevant 45 / ambiguous 30 / pending 0。
  - memory 28 条：relevant 19 / ambiguous 9 / pending 0。
  - 103 条 `user_verdict` 与清单逐条一致，错配 0。
  - 103 条 `verdict_by` 全为 `Heishing`，`verdict_at` 全为 `2026-09-21T01:15:12Z`。
  - 代表性落盘形态：`backend/tests/regression/vault_gold_set.yaml:44-54`、`backend/tests/regression/memory_gold_set.yaml:37-46`。
- 逐行 diff：
  - vault：225 行变化，75 条 × 恰 3 行。
  - memory：84 行变化，28 条 × 恰 3 行。
  - 变化行 key 集合只含 `user_verdict` / `verdict_by` / `verdict_at`。
  - 除三字段外的解析层逐键差异 = 0。
  - 两份 shadow 文件与父提交 byte-for-byte 相同；vault shadow 仍为 2 条 pending（`backend/tests/regression/vault_gold_set_shadow.yaml:14-35`）。

结论：103/103 回写与用户勾选清单完全一致；未发现任何非三字段内容被本 commit 动过；shadow 未触碰。

---

## ① 冻结完整性与 verify 语义 — PASS

### 实际冻结状态

Manifest 终态：

- revision 3、frozen true：`backend/tests/regression/gold_set_manifest.yaml:8-11`
- vault hash/count/verdict_counts：`:13-35`
- memory hash/count/verdict_counts：`:36-56`
- shadow hash/count/pending：`:57-82`
- totals 103 / attack 20 / registered 105：`:83-86`
- approved + signer + time + checklist：`:87-91`
- revision 1→2→3 history：`:92-101`

独立实算：

- 四份金集 SHA256 均与 manifest 一致。
- `verify` 实跑输出四行 OK，rc=0。
- revision 链：
  - 父提交 revision 2，adjudication 为 pending，history 有 1、2。
  - HEAD revision 3，revision 3 新增用户裁定理由。
  - 父 revision 2 未曾 approved，因此 revision 3 history 没有 `prev_adjudication` 是正确行为；代码只在旧状态 approved 时留痕：`backend/scripts/gold_set_manifest_tool.py:209-215`。
- 既有 83 条对 `9c4e7e82`：
  - vault 58 条、10 个 FROZEN_KEYS 差异 0。
  - memory 25 条、10 个 FROZEN_KEYS 差异 0。
  - 与 `_bmad-output/审查/evidence-g413/r25-freeze-and-gates-20260920T181543.txt:1-4` 一致。
- 12 个判分函数 AST 独立比较结果全部 same=True：
  - vault：`norm_text`、`material_text`、`grade_of`、`is_contaminated`、`forbidden_violations`、`ndcg_at_k`、`compare_with_baseline`
  - memory：`norm_text`、`result_text`、`is_relevant`、`is_leaked`、`compare_with_baseline`

### 回写路径自身

`apply-verdicts` 的 intended path 没有“顺手改内容仍 verify 绿”的通道：

- 定位来自 PyYAML node line，不用文本启发式：`backend/scripts/gold_set_manifest_tool.py:980-987`
- 只接受唯一 queries sequence、唯一 id、唯一三标注键：`:1002-1024`
- 只规划三字段规范行：`:1035-1071`
- 写前读回三字段校验：`:1082-1102`
- 写前全文档不变量：除目标三字段外解析结果必须全等，否则整批放弃：`:1103-1117`
- 回写后 manifest 仍是旧 hash，所以 verify 应 rc=1，必须显式 `build --bump-revision` 升版； rehearsal 证据也记录了该负控：`_bmad-output/审查/evidence-g413/r25-user-marks-rehearsal-20260920T181454.txt:7-10`

### 三态语义

- CLI `verify_all` 明确 0=全符、1=内容不符、2=环境/输入错：`backend/scripts/gold_set_manifest_tool.py:267-277`
- SHA 不符归 rc=1：`:321-336`
- shape/field 问题 fail-closed：`:338-365`
- totals 与 approved 签名形状复核：`:374-401`
- runner 侧 `verify_gold_set_file` 是 bool 压缩，false 由 runner 呈现 rc=2；工具自己明确说明这不是 CLI rc 一一对应，而靠文案区分：`:467-480`

结论：本次实际 revision/hash/counts/内容冻结链自洽；intended 回写路径下未构造出“只经 apply → build → approve 且内容被悄悄改仍 rc=0”的输入。

---

## ② 签字语义 — PASS（工作流签字）；身份属性不可由仓内文件密码学证明

Manifest 已记录：

- `status: approved`
- `signed_by: Heishing`
- `signed_at`
- `checklist_path`

位置：`backend/tests/regression/gold_set_manifest.yaml:87-91`。

`approve` 的正常路径具备以下门槛：

- signer 非空、时间可解析、checklist 必须存在：`backend/scripts/gold_set_manifest_tool.py:723-754`
- 先 `verify_all` rc=0：`:760-765`
- manifest registry 必须恰好等于四份金集：`:767-779`
- 已 approved 不许静默覆签：`:781-788`
- 两个主集不得有任何 pending：`:790-805`
- 新 manifest 写入前再 verify，原子替换：`:807-843`
- `build --bump-revision` 会把 approved 重置 pending；若旧版 approved，则旧签字入 `revision_history[].prev_adjudication`：`:209-215`、`:224-257`

因此正常 `approve` / build 后重签路径不能在主集仍有 pending 时签出 approved。

边界说明：`signed_by` 是 CLI 提供的属性字符串，`checklist_path` 只验存在，不哈希绑定清单内容；Git commit 也没有 GPG/平台级身份签名。所以“Heishing 本人确实勾选”这件事的最终依据是任务书给定的用户裁定事实、清单 SHA 同步证据、以及 103 条逐条一致，而不是 manifest 自身的密码学证明。未发现 AI 代填的读证据；但也无法从仓内文件 alone 证明物理操作者身份。

---

## ③ 门与测试判别力 — PASS

### 6 个状态无关化测试仍真判别

辅助函数 `_pick_other_verdict()` 会选择与当前 verdict 不同的值，避免 adjudicated 状态下回写变成空操作：`backend/tests/regression/test_gold_set_manifest_g413.py:100-107`。`_mark()` 找不到目标复选框会直接 AssertionError，不静默通过：`:110-118`。

六个改动点均保留了实质断言：

1. roundtrip：只改目标三行、key 集合必须恰为三标注字段、分节注释保留：`:464-519`
2. anchor loss：锚丢失时 changed=[]、problems 非空、原字节不变：`:522-558`
3. checkbox edge：大写 `[X]` 可识别，坏 verdict anchor 不写并报 problem：`:561-598`
4. CRLF：字节级行尾保留，仍恰 3 行变化：`:815-844`
5. block boundary / embedded anchor：勾选不跨块、不夺权：`:941-973`
6. missing trailing newline：不补尾换行，仍恰 3 行变化：`:1080-1104`

这不是把断言放宽成恒真；它把“旧世界默认 pending”的假设替换为“与当前值不同”的对照假设。

### 103 条全量覆盖

- 行为门自身的 synthetic roundtrip 断言主要打单条/少量条目，不等于自动断言 103 条全量。
- 但全量证据存在：`r25-user-marks-rehearsal` 记录 103 picks、103 changed、225/84/0/0 行、值对账 0、回写后 verify rc=1：`_bmad-output/审查/evidence-g413/r25-user-marks-rehearsal-20260920T181454.txt:1-13`
- 本轮我又直接对父提交→HEAD 做 Git 全量 line/semantic diff，确认 103 条每条恰 3 行且非标注差异 0；因此全量覆盖不只靠样本测试。

### 测试证据

- 初测暴露 6 个状态依赖失败：`r25-freeze-and-gates:6-8`
- 状态无关化后 g413 行为门 90 passed：`r25-gate-stateagnostic:54-56`
- 点名套件 47 passed：`r25-freeze-and-gates:10-12`
- 目录级 regression：2003 passed / 6 skipped / 1 xfailed，红 0：`r25-regression-after-verdicts:180-182`
- 这些测试未在本轮重跑；本轮核验的是最终文件与 HEAD 一致、证据内容与目标一致，并只读重跑 `verify`。

---

## ④ 发现清单

- **BLOCKER**：未发现。
- **HIGH**：未发现。
- **MEDIUM**：未发现。
- **LOW**：未发现（按“当前终态 + 授权 apply/build/approve 路径”口径）。

### 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖路径

- **未被工具防住的离线输入**：如果攻击者同时手改金集 YAML 与 manifest 中的 SHA，`verify` 会把新内容视为登记内容；更广地，`verify_all` 不重算 `by_class` / `verdict_counts` / revision_history。也可以直接手改 manifest 为 approved+签名而绕过 `approve`。这些都需要绕过“不要手改 manifest”的使用契约，不是 `apply → build → approve` 正常链路；本轮通过父→HEAD Git diff、清单逐条对账和 hash 实算排除了当前终态发生该情况。
- **对照输入**：四份文件当前 SHA 全部匹配；两 shadow 与父提交完全相同；既有 83 条 10 keys 对 `9c4e7e82` 差异 0；12 判分函数 AST same=True。
- **负控输入**：回写后未升版前 verify rc=1；篡改 SHA 的 runner 路径由行为门覆盖；6 个状态依赖测试先红、状态无关化后 90 绿。
- **门未覆盖/不可证明路径**：`approve` 不绑定 checklist SHA、不验证操作者身份；`verify` 不校验 approved 状态下主集 pending 是否为 0（该责任在 `approve`）；自动化行为门的“恰 3 行”断言本身不是 103 条全量，而由 rehearsal + 本轮 Git 全量对账补足；并发修改/TOCTOU 未在本次范围内测试。

---

## 总判定

CARD-G4-13 的完成条件均已达成：

1. 主集 103/103 非 pending：达成。
2. verdict 与用户勾选清单逐条一致：达成。
3. manifest revision 3、counts/hash 正确、approved + Heishing + checklist_path：达成。
4. 既有内容冻结、12 判分函数 AST 不变、shadow 未动：达成。
5. verify rc=0、行为门 90 passed、点名 47 passed、目录级 2003 passed 红 0：有绑定证据，达成。

**本轮总评：B=0 / H=0 / M=0 / L=0。**


