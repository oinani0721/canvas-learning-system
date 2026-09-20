你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r15 = 本 goal 预授权预算内的最后一个 develop commit（r8–r15 = 8/8）**（卡文 `收敛-CARD-G8-10-checker.md`：连续 loop，直到绑最终 HEAD 的一轮 **B/H/M/L = 0/0/0/0** 才释放合并门；预算耗尽 ⇒ 停并交主 session）。上一轮 **r14 = B0/H0/M6/L3**（存档 `codex-review-CARD-G8-10-r14.md`，绑 `b93812ea`）：M-1 prompt 称未入库件为「入库件」；M-2 §十三 非 `名 — 理由` 行被静默丢弃；M-3 `Model:`/标记行取首个匹配（多行可伪装）；M-4 PARTIAL 用 `or []` 把缺字段/`null` 当空；M-5 负控非靶向（无关缺陷也能保红）；M-6 控制件用 `ls -t` 而非本次 invocation 的 `file=`；L-1 锚可被移位截断；L-2 runner provenance 未与被审 REF 绑定。

- **本轮绑定**：`0aa875239de78e5226be4102fc162abc6fac08bb`（r15 develop commit；父 = `b93812ea`）。r15 全部改动只在 `_bmad-output/**`：审计器 → **v2.6.1**、sidecar 生成器 v4.9-r15、两组 r15 控制件（靶向 + 标签断言 + invocation 绑定）、UAT 校正/新段、**r14 顺延存档一并入库**（非 amend）。**product code diff = 0**（`git --no-pager diff --stat 4120e0b6 HEAD -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- **r15 HEAD 的入库审计件（REF 同绑，rc=0）**：`artifact-audit-r12-20260920T151540-70866.txt`（`names=71 excluded=6 (unique=6) tracked=65 missing=0`；`blob_used == blob_in_ref == 0224341a…`）。
- **r15 修法（§九.62，9 项）**：①（M-1）数字来源纪律（只引入库件，预检标注）；②（M-2）`excl-malformed`；③（M-3）`model-line-count` / `marker-line-count`；④（M-4）PARTIAL 要求字段存在且恰 `[]`；⑤（M-5）负控靶向化 + 干净孪生 T；⑥（M-6）按 invocation 的 `file=` 取件；⑦（L-1）锚 = §九 标题唯一 + 章内标记恰一次 + 前项编号 28（`section-anchor` / `marker-count` / `marker-context`）；⑧（L-2）runner provenance 双记（used / in_ref）；⑨ `excl-dead` 面改为整个 §九 + §十三 扩为 6 条。

**最小读取面**（其余不必读）：

1. 脚本：`g810-r12-artifact-audit.zsh`（v2.6.1）、`g810-r8-sidecar.py`（v4.9-r15）、`g810-r15-audit-ctl.zsh`、`g810-r15-sidecar-negctl.zsh`。
2. 证据：**`artifact-audit-r12-20260920T151540-70866.txt`（@`0aa87523`，rc=0）**；`audit-ctl-r15-20260920T151428-69308.txt`（C1–C7 七类红全标签命中，`verdict_bad=0`）；`sidecar-negctl-r15-20260920T151448-69629.txt`（N1–N8 + 孪生 T + 真实 P1，`verdict_bad=0`）；v2.6.1 逐 REF `artifact-audit-r12-20260920T151456/…58/…59/…500/…501/…503*.txt`（`b93812ea` = rc=0；其余各 = 其树内 UAT 的真实缺口）；`g810-green-r11-20260920T151540.txt`（`prev@74d58d14 = 1705ab07…` → `v4.9(docfixed)@0aa87523 = 2291e43027dc6df927e7962a830c8efc`，rc=0）。
3. UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`：§九.62–64 + §十.56–58 + §十一.55–57 + §十三（6 条排除：2 历史/误写、2 车道外、1 作废、1 缩写）。
4. JEV：`jev-triage-0aa87523.json` + 运行 stdout `jev-triage-0aa87523-run-<ts>.txt`（`calls: 1`；唯一 triaged 文件 = `g810-r8-sidecar.py`（+14/−2），urgency **2.46** / P(review)=0.68 / risk=**logic**）+ sidecar `sidecar-g810-r15-0aa87523.json`（**随收尾 commit 入库**）。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. **9 项闭合**：①–⑨ 逐条可在脚本 / 控制件 / 输出件中复核；其中 M-2/M-3/M-4 各带靶向负控（C7 `excl-malformed`、N6 `model-line-count`、N8 缺字段 `partial-inconsistent`），M-5 由孪生 T（rc=0 + `partial=true`）证明红灯来自目标缺陷。
2. **审计 HEAD 件**：`151540-70866` REF 同绑（`# ref=0aa87523…`、`# uat_blob=22e593c1…`）、`blob_used == blob_in_ref`、`missing=0`、rc=0。
3. **未放宽旧失败面**：C1–C7 七类控制全红且标签命中；N1–N8 八例全红且标签命中；v2.6.1 逐 REF 的 rc/missing 逐项可复算。
4. **数字来源纪律**：本 prompt 与 §九.63 表中所有数字均来自**已入库件**；唯一「非入库」项明确标注（HEAD 预检）。
5. **未越界**：r15 commit 只改 `_bmad-output/**`；底账内容一字未动；product code diff = 0；未 amend。
6. **预算状态（如实）**：本 goal 预授权 8 个 develop commit，**r8–r15 已用 8/8**。若本轮仍非 0/0/0/0，按卡文 §5「预算耗尽」停并交主 session（不会再有第 9 个 develop commit）。

# ③ 请按重要性回答（JEV urgency：生成器 2.46 / risk=logic）

① **r14 的 6 M + 3 L 是否真的闭合**？逐项给判；不闭合请给**未被拦下的输入**（尤其：锚三条件的绕过、`excl-*` 四类检查、Model/标记行唯一性、PARTIAL 字段存在性、孪生/靶向控制的判别力）。
② 当前工具集是否仍有与**声称**不符的恒绿面？（§十.36–58 的声明边界请判定「可接受」还是「仍需计」）
③ r15 证据链是否自洽：审计 HEAD 件 rc=0 + 逐 REF + 两组控制 + green 链 + 绑定（`:(exclude)_bmad-output`）+ PENDING-R15 口径 + r14 顺延存档入库事实。
④ **本轮收口条件（B/H/M/L = 0/0/0/0）是否满足**；不满足请给最小反例（**M/L 也要给**）。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`**；若四级全无，写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`——该行会用作轮次闭合的依据（本 goal 的闸门要求四级全 0）。

# ⑤ 边界

只读；不连任何库；只评审计 v2.6.1 + 生成器 + r15 证据面 + 上述闭合项；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r15 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界在**本轮**扩面——若你认为需扩面，记为 MEDIUM/LOW 并指出准确边界即可。
