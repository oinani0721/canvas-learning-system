你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r14 = 本 goal 收敛轮的第 7 轮**（卡文 `收敛-CARD-G8-10-checker.md`：连续 loop，直到绑最终 HEAD 的一轮 **B/H/M/L = 0/0/0/0** 才释放合并门）。上一轮 **r13 = B0/H0/M5/L5**（存档 `codex-review-CARD-G8-10-r13.md`，绑 `c84a0cc4`）：M-1 prompt 引了非入库的预检数字 + 误引 JEV stdout 名；M-2 UAT 登记 runner blob 与实际不符 + 输出头版本号旧；M-3 §十三 同名条目按 dict 覆盖可掩盖空理由；M-4 `calls` 解析未锚定 `Model:` 行可被散文行伪装；M-5 两组控制件只断言 rc 不断言目标标签、fixture 锚点不稳；L-1 marker 不校验唯一/位置；L-2 输出名秒级可撞；L-3 `len<5` 静默排除短名；L-4 PARTIAL 不约束「标记人工审查 0/0」；L-5 注释与实现矛盾。

- **本轮绑定**：`b93812eac6685d36bd45c9ea34cc4eab3e2986bd`（r14 develop commit；父 = `c84a0cc4`）。r14 全部改动只在 `_bmad-output/**`：审计器 → **v2.5.1**、sidecar 生成器（calls 锚定 + PARTIAL 四项一致）、两组 r14 控制件（带标签断言）、UAT 校正/新段、**r13 顺延存档一并入库**（非 amend）。**product code diff = 0**（`git --no-pager diff --stat 4120e0b6 HEAD -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- **r14 修法（§九.58，10 项）**：①（M-1）prompt 只引入库件、预检标 `(pre-check)`；②（M-2）runner 逐版登记（v2.5.1 blob `df8a35b7…` / sha256 `aff96a43…`），输出头 → v2.5；③（M-3）§十三 逐条检查 + `excl-duplicate`；④（M-4）`calls` 只认 `^Model:\s*\S+\s*\|\s*calls:\s*(\d+)`；⑤（M-5）控制件加标签断言 + 结构锚 fixture；⑥（L-1）marker 行首锚定 + 恰 1 次（`marker-count` 红）；⑦（L-2）输出名加 `-$$`；⑧（L-3）去掉长度过滤；⑨（L-4）PARTIAL 另要求 `标记人工审查 0/0`；⑩（L-5）注释与实现一致。
- **r14 HEAD 的入库审计件（REF 同绑，rc=0）**：`artifact-audit-r12-20260920T150310-64176.txt`（`names=78 excluded=4 (unique=4) tracked=74 missing=0`；`runner_blob=df8a35b7…`）。

**最小读取面**（其余不必读）：

1. 脚本：`g810-r12-artifact-audit.zsh`（v2.5.1）、`g810-r8-sidecar.py`、`g810-r14-audit-ctl.zsh`、`g810-r14-sidecar-negctl.zsh`。
2. 审计/控制证据：**`artifact-audit-r12-20260920T150310-64176.txt`（@`b93812ea`，rc=0）**；r13-era 件 `artifact-audit-r12-20260920T145007.txt`（@`c84a0cc4`，74/4/69/1）；v2.5.1 逐 REF `artifact-audit-r12-20260920T150151/…53/…54/…55/…57*.txt`；`audit-ctl-r14-20260920T150133-62888.txt`（C1 mark-count-0 / C1b count-2 / C2 dead / C3 empty-reason / C4 duplicate，全含标签断言，`verdict_bad=0`）；`sidecar-negctl-r14-20260920T150145-63083.txt`（N1–N7 全断言命中，P1/P2 正控，`verdict_bad=0`）。
3. 其它：`g810-green-r11-20260920T150310.txt`（`prev@74d58d14 = d0683276…` → `v4.9(docfixed)@b93812ea = 7866c708c5b52c9020031fb21dddddaf`，rc=0）。
4. UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`：§九.58–61（r14 修法/证据/边界/收尾结构）+ §十.53–55 + §十一.52–54 + §十三（4 条排除）。
5. JEV：`jev-triage-b93812ea.json` + 运行 stdout `jev-triage-b93812ea-run-20260920T150311.txt`（`calls: 1`；唯一 triaged 文件 = `g810-r8-sidecar.py`（+6/−3），urgency **2.36** / P(review)=0.60 / risk=**logic**）+ sidecar `sidecar-g810-r14-b93812ea.json`（**随收尾 commit 入库**，本 prompt 不预称其已入库）。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. **10 项闭合**：①–⑩ 逐条在脚本/控制件/输出件中可 `sed`/`grep` 复核（尤其 M-3 的 duplicate 控制、M-4 的 N6 spoof 控制、M-5 的标签断言）。
2. **审计 HEAD 件**：`150310-64176` 是 REF 同绑（`# ref=b93812ea…`、`# uat_blob=5f951941…`）、含 runner provenance、`missing=0`、rc=0；其新写法的输出名带 `-$$`。
3. **未放宽旧失败面**：N1–N3 路径负控、N4/N5/N6/N7 PARTIAL 负控全 rc=1 且标签命中；C1–C4 全 rc=1 且标签命中；v2.5.1 逐 REF 的 missing 逐项可复算（39/3、53/2、69/4、71(excl 2)/2、74(excl 4)/1、@`b93812ea` 78(excl 4)/0）。
4. **数字来源纪律**：UAT §九.59 表中所有数字均来自**已入库件**（`150310-64176` 等）；唯一「非入库」项明确标注 = HEAD 预检（工作区覆盖）。
5. **未越界**：r14 commit 只改 `_bmad-output/**`；底账内容一字未动；product code diff = 0；未 amend。

# ③ 请按重要性回答（JEV urgency：生成器 2.36 / risk=logic）

① **r13 的 5 M + 5 L 是否真的闭合**？逐项给判；不闭合请给**未被拦下的输入**（尤其：`excl-*` 与 marker 唯一性、`calls` 锚定的旁路、PARTIAL 四项一致的可伪装面、控制件标签断言是否真的会失败）。
② 当前工具集是否仍有与**声称**不符的恒绿面？（§十.36–55 的声明边界请判定「可接受」还是「仍需计」）
③ r14 证据链是否自洽：审计 HEAD 件 rc=0 + 逐 REF + 控制组 + sidecar 负控 + green 链 + 绑定（`:(exclude)_bmad-output`）、PENDING-R14 口径、r13 顺延存档入库事实。
④ **本轮收口条件（B/H/M/L = 0/0/0/0）是否满足**；不满足请给最小反例（**M/L 也要给**）。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`**；若四级全无，写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`——该行会用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评审计 v2.5.1 + 生成器 + r14 证据面 + 上述闭合项；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r14 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界在**本轮**扩面——若你认为需扩面，记为 MEDIUM/LOW 并指出准确边界即可。
