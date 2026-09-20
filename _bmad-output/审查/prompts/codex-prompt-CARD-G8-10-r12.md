你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r12 = 本 goal 收敛轮的第 5 轮**（卡文 `收敛-CARD-G8-10-checker.md`：连续 loop，直到绑最终 HEAD 的一轮 **B/H/M/L = 0/0/0/0** 才释放合并门）。上一轮 **r11 = B0/H0/M2/L4**（存档 `codex-review-CARD-G8-10-r11.md`，绑 `1db667ba`）：M-1 = 产物审计 v1 有**未声明的前缀白名单**（`check_g810_refs.py` 这类无前缀名不在面内）；M-2 = 审计的**名字面（工作区 UAT）与被审 REF 未同绑**；L-1 = r11 green 注释默认值仍未改到位；L-2 = checker 函数说明仍写「4–40 位」；L-3 = r11 prompt 的 JEV stdout 文件名误写 `141638`（实存 `141639`）；L-4 = 未引用的 5/27 不完整负控件 `negctl-r11-post-20260920T141449.txt`。

- **本轮绑定**：`2e52f551e2c417dbf4a9a40a587bcb8b1a593853`（r12 develop commit；父 = `1db667ba`）**+ `4c5777d065bc947814497f5a96fc7a53113c93c6`（r12 补：audit v2.1 排除名单 + UAT 全名化；只含 `_bmad-output/**`）**；两 commit 均只改 `_bmad-output/**`，**product code diff = 0**（`git --no-pager diff --stat 4120e0b6 HEAD -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。尚有 **r12 收尾 commit**（本 prompt + 本审查存档 + JEV/sidecar + post-commit green + 最终审计件 + 本单回填）待做，同属 `_bmad-output`-only。
- **r12 修法（§九.48 / §九.52）**：
  ①（r11-M1+M2）**产物审计 v2 → v2.2**（`g810-r12-artifact-audit.zsh`）：**无前缀白名单**（审计面 = UAT §九 r8 起引用的全部 `*.py|*.txt|*.json|*.zsh|*.md` 反引号名）；**REF 同绑**（UAT 从 `REF:<UAT>` 读出 + 记 `uat_blob`）；判定 = basename 在 REF 树内至少一处；**§十三 审计排除名单**（显式理由、随 REF 同绑、输出 `excluded=n` 与逐条理由；非静默白名单）+ `OUTDIR` 第二参数（用于最终 HEAD 复跑不留工作树残留）。
  ②（r11-L1/L2）r11 green 注释默认值 → `74d58d14`/r10；checker `_check_provenance_tokens()` 说明 → 不限长（doc-only ⇒ 行为不变、digest 重锚）。
  ③（r11-L3/L4）r11 prompt 的 JEV stdout 名 → `jev-triage-1db667ba-run-20260920T141639.txt`；`negctl-r11-post-20260920T141449.txt` **删除**（未入库）。
  ④（自发现，§九.52）post-commit 审计 v2 对 `2e52f551` 首跑 **rc=1**（3 个不可解名：作废件 / 误写名 / 我自己的省略号缩写）⇒ UAT 全名化 + §十三 排除名单（v2.1）+ 复跑（见 ④ 证据）。

**最小读取面**（其余不必读）：

1. 脚本：`g810-r12-artifact-audit.zsh`（v2.2 全文）、`g810-r11-artifact-audit.zsh`（v1，被审件）、checker v4.9（doc-fixed，sha256 `f7c63b3c7be635bca7909a5be9e771f8d19fff6dfb76ace79634a827fc0f887f`）、`g810-r8-sidecar.py`（含 `--allow-empty` PARTIAL 模式）。
2. 审计证据：`artifact-audit-r12-20260920T143035.txt`（@`74d58d14`：`names=36 tracked=35 missing=1`，missing 恰为 `sidecar-g810-r9-9a22c33b.json`）/ `artifact-audit-r12-20260920T143207.txt`（@`1db667ba`：rc=0）/ **`artifact-audit-r12-20260920T143247.txt`（@`2e52f551`：rc=1，复现 3 个不可解名）** / 最终复跑件 = 收尾 commit 内（见该 commit）。
3. 负控/回归（doc-only 之后）：`negctl-r11-post-20260920T143114.txt`（27/27 同型）/ `anchor-battery-r11-v49-20260920T143154.txt`（8/8 + 对照 rc=0）/ `yamlgate-branches-r11-v49-20260920T143201.txt`（5/5 + 对照 rc=0）/ `g810-green-r11-20260920T143206.txt`（`v4.9(docfixed)@1db667ba = 9ff7fa069a09c2e76ec2d09137b5c205`，rc=0）/ `g810-green-r11-20260920T143247.txt`（`prev@74d58d14 = cf06119f…` → `v4.9(docfixed)@2e52f551 = c2c7bf9e…`，rc=0）。
4. UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`：§九.48–53（r12 修法/证据/作废件/补/**§十三 审计排除名单**）；§十.46–49；§十一.45–48；PENDING-R12 字段由收尾回填。
5. JEV：`jev-triage-2e52f551.json` + 运行 stdout `jev-triage-2e52f551-run-20260920T143248.txt`（`calls: 1`；唯一代码文件 = checker（+3/−2），urgency **2.32** / P(review)=0.64 / risk=**test_or_docs**；VERDICT REVIEW）+ sidecar `sidecar-g810-r12-2e52f551.json`；**补 commit** = `jev-triage-4c5777d0.json`（`calls: 0`，0 个 triaged 文件）+ `sidecar-g810-r12b-4c5777d0.json`（`partial: true` / `verdict: null` / PARTIAL，按卡文口径不得写「已审」）。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. **r11-M1 闭合**：审计 v2 面 = UAT §九 r8 起引用名（36 条；含 `check_g810_refs.py`、`g810-r8-sidecar.py` 等无前缀名）——请自行从 `REF:<UAT>` 复算名字集合与判定。
2. **r11-M2 闭合**：`zsh g810-r12-artifact-audit.zsh <REF>` 的 UAT 文本来自 `REF:<UAT>`（非工作区），输出记 `uat_blob`；对 `74d58d14`（其树内 UAT）复算 = rc=1 / missing 恰为 r9 sidecar。
3. **r11-L1/L2 闭合**：`g810-r11-green.zsh` 注释默认值 = 实际默认值（`PREV=${1:-74d58d14}`）；checker 说明与 `_ALNUM_TOKEN_RE = ^[0-9A-Za-z]+$` 一致（doc-only ⇒ 行为不变，digest 重锚 `43c417e7… → 9ff7fa06…`）。
4. **r11-L3/L4 闭合**：prompt 内 stdout 名 = 实存件；`negctl-r11-post-20260920T141449.txt` 已删且未入库（`git ls-files` 0 命中）。
5. **自发现项处置（§九.52）**：「真实缺失 vs 历史/缩写提及」的界线 = **§十三 排除名单**（显式理由 + 随 REF 同绑 + 输出回显）；首跑 rc=1 的 3 个名已分别处置（2 个进名单、1 个全名化）。
6. **未放宽旧失败面**：27 用例 / 锚群 8/8 / YAML 门 5/5 在 doc-only 后同型；canonical rc=0（`9ff7fa06…`）。
7. **未越界**：r12 两个 commit 只改 `_bmad-output/**`；底账内容一字未动；product code diff = 0；未 amend。

# ③ 请按重要性回答（JEV urgency：checker 2.32 / risk=test_or_docs）

① **r11 的 6 项（M-1/M-2/L-1/L-2/L-3/L-4）+ 自发现的 §九.52 项是否真的闭合**？逐项给判；不闭合请给**未被拦下的输入**（尤其：审计 v2.2 的排除名单能否被滥用/误用、basename 判定面、REF 同绑是否真的有界、PARTIAL sidecar 的字段语义）。
② 当前工具集是否仍有与**声称**不符的恒绿面？（UAT §十.36–49 的声明边界请判定「可接受」还是「仍需计」）
③ r12 证据链是否自洽：审计四相态（@74d58d14 rc=1 / @1db667ba rc=0 / @2e52f551 rc=1 复现 / 收尾后 rc=0）、doc-only 后全量复跑、digest 两代链、`sha_equal=yes`、绑定（`:(exclude)_bmad-output`，含补 commit）、PARTIAL 记录、PENDING-R12 口径。
④ **本轮收口条件（B/H/M/L = 0/0/0/0）是否满足**；不满足请给最小反例（**M/L 也要给**）。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`**；若四级全无，写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`——该行会用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评审计 v2.2 + checker v4.9(docfixed) + r12 证据面 + 上述闭合项；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r12 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界（非 fence YAML 面 / 产品树散文路径 / 其它键名枚举 / basename 判定面）在**本轮**扩面——若你认为需扩面，记为 MEDIUM/LOW 并指出准确边界即可。
