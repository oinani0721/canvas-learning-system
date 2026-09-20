> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G8-7 round-2
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r2.md)"`
> 审查绑定: 审工作区 @ HEAD=9d4f7bf0（未提交；本卡零代码, 改动面全在 `_bmad-output/`）
> 会话头自证（抄 .stderr 三行, 行号括注）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: glm-5.3` / `L9: reasoning effort: max`
---

## 结论

**BLOCKER = 0 · HIGH = 1 · MEDIUM = 2 · LOW = 0**

范围核对：`git diff --stat 9d4f7bf0 HEAD -- . ':(exclude)_bmad-output'` 为空；`git status --porcelain` 非空，但 5 条未跟踪项全在 `_bmad-output/`（r1/r2 prompt、review、evidence 目录），未见 `_bmad-output` 外改动。

---

## BLOCKER

无。

---

## HIGH

### H-1 · r2 新增的 manifest 孤立对照没有绑定最终 J06 manifest 对象

- 证据：`_bmad-output/审查/evidence-g87-journey/manifest-isolation-20260919T211402.txt:1-3,31-36`
- 最终对象：`_bmad-output/审查/evidence-g87-journey/b15-g8-7/journeys/J06/manifest.json:34-38,156-283`
- 复现思路：对当前 J06 manifest 计算 SHA-256，结果是 `92126050fd0cc0d97987e1d04d727e0efb049c628ba66ed92c2ecdbff01d2938`；但 isolation 记录的副本 SHA 是 `e0d395562ed16782e60e207c8934286e0ecb0eb5da042df571b0062a36794d11`。且 isolation 时间为 21:14:02，J06/root manifest 的 `finished_at` 与内容更新时间为 21:15:09。
- 影响：[1] 绿、[2] 仅 `result=pass` ⇒ 仅红 S3、[4] 仅 `signoff=approved` ⇒ 仅红 signoff、[5] 还原绿，这些对照证明的是 **21:14 的旧 J06 对象**，不是当前含 9 条 commands / 18 件 artifacts 的最终对象。HIGH4 因此不能算完全闭合。
- 修复方向：冻结最终 J06 后重跑 isolation 序列，并记录新的最终 SHA；若 isolation 输出本身会造成自引用循环，应用非循环的 sidecar/index 说明绑定与排除规则。

---

## MEDIUM

### M-1 · 强化负控的结果可读，但精确命令、白名单实现与 rc 未落档，复现弱

- 证据：`_bmad-output/审查/evidence-g87-journey/negctl-strengthen-20260919T211354.txt:2-20`
- 对照要求：`第十五批-goals/P3-C.md:35`
- 复现思路：检查 strengthen 产物，只见“精确白名单”的摘要与 `changed/outside` 结果，没有可复跑的 exact `sed`、路径提取、whitelist matcher、scratch 输入 SHA、每段 rc；因此能确认“这些负控输入被指定文件捕获”，但不能从产物本身重建同一门实现。
- 影响面：HIGH1/2/3 的 **行为结果** 已有证据，但 **可复现审计** 仍不完备。尤其 D 段只登记 `before vs bm_d 差异 = 0` 与原文 hash 前 16 位，未完整落出卡文 sed 命令与完整原文行，不能独立验证“最后一位原本就是 `f` ⇒ no-op”的身份链。

### M-2 · r2 isolation 证据不在 manifest artifact/execution 账本中，缺少非循环绑定说明

- 证据：`_bmad-output/审查/evidence-g87-journey/manifest.json:38-95,156-283`
- 副本：`_bmad-output/审查/evidence-g87-journey/b15-g8-7/journeys/J06/manifest.json:38-95,156-283`
- 新证据：`_bmad-output/审查/evidence-g87-journey/manifest-isolation-20260919T211402.txt:1-36`
- 复现思路：解析两份 manifest，`commands=9`、`artifacts=18`，但 artifact path 列表不含 `manifest-isolation-20260919T211402.txt`；manifest 内也没有说明“validator/isolation 输出因自引用不入 artifacts”的裁定。
- 影响：这不是简单漏列，因为直接自引用会改变被测对象 SHA；但当前包缺少一个非循环的登记层，使 reviewer 无法只靠 manifest 账本知道该 isolation 证据的存在、排除原因与最终对象绑定。

---

## 重点项逐项裁定

- **⓪ 零静默改写门：行为闭合，复现性 PARTIAL。**  
  `negctl-strengthen:4-10` 证明非白名单 `原白板/CS.md` 与无关节点 `节点/lecture 2.md` 均 `outside=1` 且红在指定文件；`:12-16` 证明含空格路径在卡文字面 `awk $3` 下截断，而修正提取得到完整路径并 `outside=1`。因此“非 diff 非空”和“`节点/` 整目录过宽”两点已被负控输入覆盖。剩余问题见 M-1。

- **① `search_notes` 身份绑定：PASS。**  
  `00-README.md:14` 要求完整 vault 相对路径 + 内容 SHA 前 16 位，不接受仅同名/同标题；`manifest.json:123-127` 同步。足以排除同名旧材料顶替。

- **② `fsrs_*` vs `mastery_*`：PASS。**  
  `00-README.md:16` 与 `manifest.json:137-141` 明确同时 grep `mastery_`/`fsrs_`，且仅 `mastery_*` 变化时只登记本地掌握度更新，不证明 `fsrs_bridge`。这与 `quiz-answer/SKILL.md:74` 的“不碰后端熟练度链”一致。

- **③ manifest 混合解析：口径诚实，最终绑定 FAIL。**  
  根件自称非正式 RC 证据：`manifest.json:13`；J06 副本自称仅为 schema 一致性副本、不是 RC J06：`J06/manifest.json:13`；卡文字面冲突有实测：`manifest-validator-conflict-20260919T170857.txt:4-24`。但最终对象未绑定到 isolation 序列，见 H-1。

- **④ 断点归属：PASS。**  
  `03-breakpoints.md:10-13` 将 8 处 skill 差异归为“部署冻结、非缺陷”，与总账 `2026-08-28-主goal全量分goal总账-v2.md:1007` 一致；读取面外主张也已在 `03-breakpoints.md:13` 明示，不纳入本包复核。

- **⑤ 未授权路径的独立价值：PASS。**  
  六环节全部按未授权登记为 `not_run`：`03-breakpoints.md:22-33`、`manifest.json:107-149`；同时保留 README 判据、skill 版本表、before/after 快照、manifest、断点表、零改写门与负控产物，见 `00-README.md:27-39`、`manifest.json:156-283`。不是空壳，但旅程本身未证明。

---

## r1 项闭合汇总

| r1 项 | r2 裁定 |
|---|---|
| HIGH1 sed no-op / 证据不自洽 | **PARTIAL**：no-op 与修正对照有结果，但 exact 命令与完整身份链未落档 |
| HIGH2 含空格路径 | **CLOSED** |
| HIGH3 白名单过宽 | **行为面 CLOSED；复现面 PARTIAL** |
| HIGH4 红/绿孤立对照 | **NOT CLOSED**：isolation 未绑定最终 J06 SHA |
| HIGH5 同名旧材料冒充 | **CLOSED** |
| MEDIUM1 `fsrs_*` 区分 | **CLOSED** |
| MEDIUM2 commands/artifacts 扩展 | **PARTIAL**：9/18 数量正确，但 isolation 证据缺非循环登记 |
| LOW1 after vs journey-log 索引 | **CLOSED** |
| LOW2 读取面外主张 | **CLOSED** |
