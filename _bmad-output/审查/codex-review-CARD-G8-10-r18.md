BLOCKER: 无 / HIGH: 无 / MEDIUM: 1 / LOW: 2

**结论：`B/H/M/L = 0/0/1/2`，不满足 `0/0/0/0`；合并门继续锁定。**

## BLOCKER

无。

## HIGH

无。

## MEDIUM

1. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:152` — `row-file` 只做 basename **子串包含**判断，而不是文件列身份/后缀等价判断，因此 r17-M1 的“克隆数值 + 改名”仍未完全闭合。  
   **未被拦下的输入**：把真实 r17 行改成 `evil-g810-r8-sidecar.py +37/-11 2.79 0.73 0.65 logic PASS`，JSON 保持不变；行数仍为 `1 == len(files)`，数值/risk 全等，且期望 basename `g810-r8-sidecar.py` 仍作为子串出现在 `evil-g810-r8-sidecar.py` 中，所以不会产生 `row-file`，sidecar 会以 `verdict="PASS"` 退出 0。

## LOW

1. `_bmad-output/审查/evidence-g810/g810-r15-sidecar-negctl.zsh:2` — 控制件标题仍写 `N1–N11 + 孪生 T + 真实正控 P1`，但本提交已扩到 N12。  
   **对照输入**：同文件第 12、68、101 行和存档 `sidecar-negctl-r15-20260920T161236-99894.txt:37-39` 均存在 N12 / `row-file`，标题矩阵少计一项。

2. `_bmad-output/审查/evidence-g810/g810-r15-sidecar-negctl.zsh:14` — 注释仍称 P1 为“真实 r14”，实际 invocation 已改用 r16。  
   **对照输入**：同文件第 104 行使用 `jev-triage-884af91a.json` / `--round r16`，存档 `sidecar-negctl-r15-20260920T161236-99894.txt:43-45` 也标明“真实 r16”且 `sha=884af91a…`。

## 只读复核摘要

- 绑定核实：`HEAD = 5b581b0c6da2d57c491b2cb72c5d86885bf4ab37`，父提交为 `4569aef4d30c65c279f65ebe39d01b06cf6d784b`。
- 已入库清单独立复算：prompt 所列 14/14 均可从 `5b581b0c` 树内解析；未入库集合恰好为当前 7 个 r18 收尾件，未据其数字作结论。
- `4120e0b6..5b581b0c` 排除 `_bmad-output` 的 product diff 为 0；底账 SHA-256 仍为 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- 控制件复算：审计存档 C1–C9 为 9/9 `rc=1 assert=yes`，`verdict_bad=0`；sidecar 存档含 N1–N12、T、P1，N12 命中 `row-file`，T/P1 均 `rc=0`，`verdict_bad=0`。
- r17-L1 与 r17-L2 已闭合：审计控制件输出标题已是 v2.6.3 / C1–C9；r17 prompt 计数已写 21/21。
- §十.65 的 verdict 词级边界可接受：JSON 无独立 verdict 来源，本工具只能转录 stdout。§十.62/66 的第 2..N 行未逐行互核也已明确声明，本轮未将其扩面计缺陷；但“basename 子串包含”不足以支撑“改名不再恒绿”的闭合宣称。
