你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r13 = 本 goal 收敛轮的第 6 轮**（卡文 `收敛-CARD-G8-10-checker.md`：连续 loop，直到绑最终 HEAD 的一轮 **B/H/M/L = 0/0/0/0** 才释放合并门）。上一轮 **r12 = B0/H0/M3/L4**（存档 `codex-review-CARD-G8-10-r12.md`，绑 `2e52f551`/`4c5777d0`）：M-1 = UAT 的审计数字与实存件不符（`names=36` vs 实为 48 等）；M-2 = §十三 排除名单无死项/空理由检查；M-3 = `--allow-empty` PARTIAL 无三方一致性约束；L-1 = 审计边界标记缺失时静默退化；L-2 = 固定 `/tmp` 路径并发竞态；L-3 = 名字抽取不接受 `/ + ( )`；L-4 = 输出不记 runner 自身 provenance。

- **本轮绑定**：`c84a0cc489eafb087cc107342bde12a86222a7b8`（r13 develop commit；父 = `4c5777d0`）。r13 全部改动只在 `_bmad-output/**`：审计器 → **v2.3/v2.4.2** + sidecar 生成器 PARTIAL 约束 + UAT 数值校正 + r13 运行器/证据 + **r12 顺延存档一并入库**（非 amend）。**product code diff = 0**（`git --no-pager diff --stat 4120e0b6 HEAD -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- **r13 修法（§九.54）**：①（M-1）UAT 逐项按实存件校正（§九.49/§九.55）；②（M-2）§十三 强制 `excl-dead` + `excl-empty-reason`；③（L-1）`marker-missing` fail-closed；④（L-2）`mktemp -d` 私有临时目录；⑤（L-3）名字抽取支持 `/ + ( )`（含空白/通配/占位符/绝对/`..`/反斜杠 = 声明边界，§十.50）；⑥（L-4）输出记 runner `sha256`/`blob`；⑦（M-3）PARTIAL 三方一致（`files=[] ∧ calls=0 ∧ code_files=[]`）否则 `partial-inconsistent`；⑧（§十三）+2 条**车道外引用**（`scripts/jev_review_triage.py`、goal 卡）。
- **本轮自发现缺陷（已修 + 已登记，§九.55 表末行）**：v2.3 起审计器把 tree 面从**旧硬编码** `/tmp/g810r12-tree.txt` 读（非 REF 同绑）⇒ 1446xx/1447xx 一组假绿件**已删除**；v2.4.2 改为读 `$TMPD/tree.txt`，1449xx 组为修正后运行（@`74d58d14` 重新正确报出 r9 sidecar MISS）。
- **r13 HEAD 的审计（预检，本次复核后随收尾入库）**：`names=77 excluded=4 tracked=73 missing=0` / rc=0（UAT 内占位/历史名已全部处置）。

**最小读取面**（其余不必读）：

1. 脚本：`g810-r12-artifact-audit.zsh`（v2.4.2 全文：`_seg_body`、`NAME_RE`、`excl-*` 检查、`$TMPD/tree.txt`、`RUNNER_ABS`）、`g810-r8-sidecar.py`（PARTIAL 三方一致）、`g810-r13-audit-ctl.zsh`、`g810-r13-sidecar-negctl.zsh`。
2. 审计证据：`artifact-audit-r12-20260920T143035.txt`（v2 @74d58d14）/`…143207.txt`（v2 @1db667ba）/`…143247.txt`（v2 @2e52f551）/`…143334.txt`（v2.1 @4c5777d0）/ **`…144926/…27/…28/…30.txt`（v2.4.2 四个 REF）** / `audit-ctl-r13-20260920T144925.txt`（C1 marker-missing / C2 excl-dead / C3 excl-empty-reason 全 rc=1）/ `sidecar-negctl-r13-20260920T144553.txt`（N1–N5 全 rc=1；P1/P2 正控 rc=0 且 P2 `partial=true`）。
3. 其它证据：`g810-green-r11-20260920T145007.txt`（`prev@74d58d14 = 1be00749…` → `v4.9(docfixed)@c84a0cc4 = dbb6040b7bfdf40421a47d05e6b8d910`，rc=0）。
4. UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`：§九.54–57（r13 修法/证据表/控制件/收尾结构）+ §十.50–52 + §十一.49–51 + §十三（4 条排除：2 历史/误写 + 2 车道外）。
5. JEV：`jev-triage-c84a0cc4.json` + 运行 stdout `jev-triage-c84a0cc4-run-20260920T145008.txt`（`calls: 1`；唯一 triaged 文件 = `g810-r8-sidecar.py`（+20/−1），urgency **2.69** / P(review)=0.73 / risk=**logic**）+ sidecar `sidecar-g810-r13-c84a0cc4.json`（随收尾入库）。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. **r12-M1 闭合**：§九.49/§九.55 的数字逐项等于实存件原文（v2 三件 + v2.1 一件 + v2.4.2 四件 + 控制件）。
2. **r12-M2 闭合**：`excl-dead` / `excl-empty-reason` 在 C2/C3 控制下真红（§九.56 件）；正常运行时 4 条排除全部有理由且在正文名字面内。
3. **r12-M3 闭合**：N4（`files=[]` + `calls=5`）/ N5（`files=[]` + `code_files` 非空）在 `--allow-empty` 下 rc=1；真实 0 文件 commit（`4c5777d0`）仍 rc=0 且 `partial=true`。
4. **r12-L1/L2/L3/L4 闭合**：marker-missing 红（C1）；`$TMPD` 私有临时目录；抽取面含 `/ + ( )`；输出来自 `$RUNNER_ABS` 的 sha256/blob（非空）。
5. **自发现缺陷**：v2.4.2 的 tree 面 = `$TMPD/tree.txt`（可 `sed` 复核）；@`74d58d14` 现正确报 `sidecar-g810-r9-9a22c33b.json` MISS。
6. **未放宽旧失败面**：Sidecar 负控 N1–N3 仍红；审计四 REF 的 rc=1 与 missing 逐项可复算（`74d58d14`: 39/3；`1db667ba`: 53/2；`2e52f551`: 69/4；`4c5777d0`: 71(excl=2)/2）；canonical rc=0（`dbb6040b…`）。
7. **未越界**：r13 commit 只改 `_bmad-output/**`；底账内容一字未动；product code diff = 0；未 amend。

# ③ 请按重要性回答（JEV urgency：生成器 2.69 / risk=logic）

① **r12 的 3 M + 4 L + 自发现项是否真的闭合**？逐项给判；不闭合请给**未被拦下的输入**（尤其：`excl-*` 检查的绕过、`--allow-empty` 的一致性面、抽取面的声明边界、tree/uat 同绑是否仍有旁路）。
② 当前工具集是否仍有与**声称**不符的恒绿面？（§十.36–52 的声明边界请判定「可接受」还是「仍需计」）
③ r13 证据链是否自洽：审计四 REF + 控制三例 + HEAD 预检 rc=0（77/4/73/0）、sidecar 五反例两正控、green 链、`sha_equal`/绑定（`:(exclude)_bmad-output`）、PENDING-R13 口径。
④ **本轮收口条件（B/H/M/L = 0/0/0/0）是否满足**；不满足请给最小反例（**M/L 也要给**）。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`**；若四级全无，写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`——该行会用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评审计 v2.4.2 + 生成器 + r13 证据面 + 上述闭合项；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r13 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界在**本轮**扩面——若你认为需扩面，记为 MEDIUM/LOW 并指出准确边界即可。
