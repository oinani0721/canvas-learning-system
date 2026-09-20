你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r10 = 本 goal 收敛轮的第 3 轮**（卡文 `收敛-CARD-G8-10-checker.md`：连续 loop，直到绑最终 HEAD 的一轮 **B/H/M/L = 0/0/0/0** 才释放合并门）。上一轮 **r9 = B0/H0/M4/L1**（存档 `codex-review-CARD-G8-10-r9.md`，绑 `9a22c33b`）：M-1 = merge 源内**非法枚举标量**（`!!binary Ym9ndXM=` / `!!int 123`）被显式键覆盖后 node/constructed 两层都不红；M-2 = `.//_bmad-output/…` 逃出 evidence 面；M-3 = SHA 槽对 **1–3 位**畸形 token 无判定；M-4 = sidecar 生成器无条件写 `path_decoded=true`（无结构校验）；L-1 = r9 green runner/存档标签仍写「树内 v4.6」。

- **本轮绑定**：`74d58d147cc5a51537fd65cca2f10ab069ea600f`（r10 develop commit；父 = `9a22c33b`）。r10 全部改动只在 `_bmad-output/**`：核对脚本 v4.7 → **v4.8**（`2af0045b…` → `7dcfd39493586ab09555945b8de97ce4180fbe83ba640cc778b1e0afda6a4098`）+ sidecar 生成器 v4.8（`f7bae0dc65be4383de21afb8a7b65701a26e6444e2e89bc7b85276550459ef3a`）+ r10 运行器/证据 + UAT r10 段。**product code diff = 0**（`git --no-pager diff --stat 4120e0b6 74d58d14 -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- **r10 修法（5 项全修，口径见 UAT §九.40）**：
  ①（r9-M1）node 层对 `outcome` 值改**三分类**（pass ⇒ `pass-unsupported`；非标量 ⇒ `outcome-type`；枚举外 ⇒ `outcome-enum`）——被 merge 消费的源值也判定。
  ②（r9-M2）路径归一化用 `posixpath.normpath`（`.//`、`a/./b`、重复斜杠）+ `_bmad-output` 边界（`== "_bmad-output"` 或 `_bmad-output/` 前缀）。
  ③（r9-M3）SHA 形态判定放宽到 **1–40 位纯字母数字 token**（白名单除外）；非 8–40 位小写 hex ⇒ `sha-missing`。
  ④（r9-M4）sidecar 生成器加结构校验（非空 / 非绝对 / 无 `..` / 无 U+FFFD / 无 NUL / **无反斜杠**）⇒ 失败 `path_decoded=false` + `path_validation_failures` + 非 0 退出；新增 `path_exists_in_worktree` 信息字段。
  ⑤（r9-L1）green runner 标题/末行不再写死「树内 v4.6 / `v46@`」；r9 那件已入库的失真标签件**不追改**（作 r9-L1 复现件，§九.42③）。

**最小读取面**（其余不必读）：

1. 脚本 diff：`git --no-pager diff --no-color 9a22c33b 74d58d14 -- _bmad-output/审查/evidence-g810/check_g810_refs.py _bmad-output/审查/evidence-g810/g810-r8-sidecar.py _bmad-output/审查/evidence-g810/g810-r10-green.zsh`；并读 v4.8 相关段（`_scan_node_outcome_pass` 三分类 / node 层 dispatch / `_check_provenance_tokens` 的 normpath 分支 / `_ALNUM_TOKEN_RE` / `_validate_relative_path`）。
2. 负控（**先红后绿**，两相位）：`negctl-r10-pre-20260920T135716.txt`（**v4.7** 提取自 `9a22c33b`：4 条新用例全穿透 rc=0；其余 21 条按既定口径）→ `negctl-r10-post-20260920T135804.txt`（**v4.8**：`R10-M1a-enumbin`/`R10-M1b-enumint` `outcome-enum` node 层、`R10-M2-dblslash` `ref-missing`、`R10-M3-abc` `sha-missing`；21 条旧用例同红、`F2` rc=0 且 digest `2b89c64a… → 24b509a5…`）；锚群 = `anchor-battery-r10-v48-20260920T135852.txt`（8/8 红 + 对照 rc=0）；YAML 门 = `yamlgate-branches-r10-v48-20260920T135900.txt`（5/5 红 + 对照 rc=0）；sidecar 生成器负控 = `sidecar-negctl-r10-20260920T135940.txt`（绝对 / `..` / 非 UTF-8 三反例 rc=1 且 `path_decoded=false` + 正控 rc=0）；正常底账 = `g810-green-r10-20260920T135904.txt`（`v4.7@9a22c33b = c70a6184…` → `v4.8@9a22c33b = 2b89c64a…`，rc=0）与 **post-commit** `g810-green-r10-20260920T140018.txt`（`prev@9a22c33b = 25d0ba6b…` → `v4.8@74d58d14 = eb60d83e…`，rc=0）。
3. UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`：§九.40–43（r10 修法/负控表/作废件/收尾结构）+ §十.40–42 + §十一.39–41；r10 判定 = 收尾回填（PENDING-R10）。
4. 底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md` §3 fenced YAML 块（**不要写死行号**）+ §2.13 六链表（r10 未改底账内容）。
5. JEV 分诊：`jev-triage-74d58d14.json` + 运行 stdout `jev-triage-74d58d14-run-20260920T140019.txt`（jev-1.13.0，`calls: 2`；`check_g810_refs.py`（+27/−14，urgency **2.82** / P(review)=0.78 / risk=logic）+ `g810-r8-sidecar.py`（+36/−6，urgency 2.52 / P(review)=0.63 / risk=error_handling），VERDICT REVIEW）+ **机器可读 sidecar** `sidecar-g810-r10-74d58d14.json`（含 `path_decoded=true` / `path_validation_failures={}` / `path_exists_in_worktree` 两条 true）。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. **r9-M1 闭合**：`<<: {outcome: !!binary Ym9ndXM=}` 与 `<<: {outcome: !!int 123}` pre v4.7 rc=0 → post v4.8 rc=1（`outcome-enum` node 层，路径 = `$.criteria[50].<<.outcome@182`）。
2. **r9-M2 闭合**：`.//_bmad-output/审查/evidence-g2-8-nope-r10/` pre rc=0 → post rc=1 `ref-missing`；`./`、`../`、绝对路径三类 r9 用例在 v4.8 下仍红。
3. **r9-M3 闭合**：`abc` pre rc=0 → post rc=1×2 `sha-missing`；合法 hex OID 仍绿（canonical rc=0）。
4. **r9-M4 闭合**：3 反例 rc=1 + `path_decoded=false`（原因 = 绝对路径 / 含 `..` 段 / 含 U+FFFD）；正控 rc=0 + `path_decoded=true`；r10 sidecar 两路径 `path_exists_in_worktree=true`。
5. **r9-L1 闭合**：`g810-r10-green.zsh` 标题 = 「canonical 底账；树内 checker 见 checker_here_sha256」，末行 = `here@74d58d14=…`；r9 失真标签件保留为复现件（§九.42③）。
6. **未放宽旧失败面**：21 条旧用例（r9 B1/B2/B3、M1 head/main、M2 dotpath/dotdot/abs、r8 A–G、r6-A/B、r7-A/B）在 v4.8 下同型（F2 仍 rc=0 且 digest 变 = 绑定）；锚群 8/8；YAML 门 5/5；canonical rc=0（两代 digest 链）。
7. **未越界**：r10 只改 `_bmad-output/**`；底账内容一字未动；product code diff = 0；未 amend 已入库 commit。

# ③ 请按重要性回答（JEV urgency 降序：`check_g810_refs.py` 2.82 / `g810-r8-sidecar.py` 2.52）

① **5 项 open（M-1/M-2/M-3/M-4/L-1）是否真的闭合**？逐项给判；不闭合请给**未被拦下的输入**（尤其：node 三分类的其它构造〔`!!float`/`!!timestamp`/空值/anchor 组合〕、`.//` 之外的路径变体、1–40 位之外的形态、生成器校验的绕过）。
② v4.8 / 生成器 v4.8 是否仍有与**声称**不符的恒绿面？（UAT §十.36–42 的声明边界请判定「可接受」还是「仍需计」）
③ r10 证据链是否自洽：先红后绿、21/21 回归、锚群/YAML 门、sidecar 三反例、digest 两代链、`sha_equal=yes`、绑定（`:(exclude)_bmad-output`）、PENDING-R10 口径。
④ **本轮收口条件（B/H/M/L = 0/0/0/0）是否满足**；不满足请给最小反例（**M/L 也要给**）。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`**；若四级全无，写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`——该行会用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评核对脚本 v4.8 + sidecar 生成器 v4.8 + r10 证据面 + 上述 5 项闭合；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r10 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界（非 fence YAML 面 / 产品树散文路径 / 其它键名枚举）在**本轮**扩面——若你认为需扩面，记为 MEDIUM/LOW 并指出准确边界即可。
