BLOCKER: 无 / HIGH: 无 / MEDIUM: 1 / LOW: 2

**结论：`B/H/M/L = 0/0/1/2`，不满足 `0/0/0/0`；合并门继续锁定。**

## BLOCKER

无。

## HIGH

无。

## MEDIUM

1. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:115-140` — r16-M2 未完全闭合：互核仍不校验首行 `file` 与 `verdict`，只校验行数、churn、三个数值和 risk，因此“克隆 JSON 数值的伪行”仍可恒绿；这不属于 §十.62 已声明的“第 2..N 行未逐行比对”边界。  
   **未被拦下的输入**：把 `jev-triage-884af91a-run-20260920T155052.txt:7` 的真实行仅将 `REVIEW` 改为 `PASS`（也可同时改文件名），保留 `+19/-8 2.41 0.61 0.63 logic`；静态复算同一 regex 得行数 `1 == len(files)` 且全部现行 `row-*` 检查相等，随后 `g810-r8-sidecar.py:149-151` 会写入 `verdict="PASS"`，不会产生 `row-file` / `row-verdict` 红。

## LOW

1. `_bmad-output/审查/evidence-g810/g810-r15-audit-ctl.zsh:48` — r16-L4 复发：脚本注释已称 v2.6.3，但控制件实际输出标题仍写“审计 v2.6.1 控制组”。  
   **对照输入**：读 `_bmad-output/审查/evidence-g810/audit-ctl-r15-20260920T160235-94574.txt:1`，再读同件 C4–C9 内嵌的 `runner_sha256=e7b1ce…` / `blob_used=20ee1d…`，可见标题版本与实际 v2.6.3 runner 不一致。

2. `_bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r17.md:10` — “已入库 20/20”计数不准：该行枚举 20 个反引号文件后又追加 `UAT`；若 UAT 按清单语义计入，实际是 21 件。  
   **对照输入**：逐项计数 4 个脚本 + 2 个控制存档 + 7 个逐 REF 审计件 + 7 个 r16 证据/文书 = 20，再加 `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`；后者在 `4569aef4` 树内可解，故清单口径应写 21/21，或明确 UAT 不计入清单。

## 只读复核摘要

- 绑定对象核实：`HEAD = 4569aef4d30c65c279f65ebe39d01b06cf6d784b`，父提交为 `884af91a66163f63ad6be5a137a28b3b2c63d5e6`。
- `4120e0b6..4569aef4` 排除 `_bmad-output` 后 product diff 为空；底账 SHA-256 复算仍为 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- 未入库集合与声明一致：仅有 r17 prompt、green、HEAD audit、JEV JSON/stdout、sidecar、审查存档 7 类；本轮未据其收尾数字作判定。
- C1–C9 存档 9/9 `rc=1 assert=yes`；N1–N11 11/11 `rc=1 assert=yes`，T `rc=0/partial=true`，P1 真实 r16 `rc=0`。
- 七个 REF 独立复算结果与存档一致：  
  `74d58d14 31/0/28/3`、`2e52f551 62/0/58/4`、`4c5777d0 64/2/60/2`、`c84a0cc4 67/4/62/1` 均有真实 missing；`b93812ea 71/4/67/0`、`0aa87523 74/6/68/0`、`884af91a 80/6/74/0` 均 rc=0。
- r16 的 L-1/L-2/L-3/L-5/L-6 修法本身可从代码与存档核对；L-4 如上未闭合。
