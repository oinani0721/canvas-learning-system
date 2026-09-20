你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r11 = 本 goal 收敛轮的第 4 轮**（卡文 `收敛-CARD-G8-10-checker.md`：连续 loop，直到绑最终 HEAD 的一轮 **B/H/M/L = 0/0/0/0** 才释放合并门）。上一轮 **r10 = B0/H0/M2/L2**（存档 `codex-review-CARD-G8-10-r10.md`，绑 `74d58d14`）：M-1 = 41+ 位纯字母数字畸形 SHA token 掉出判定面（`_ALNUM_TOKEN_RE {1,40}`）；M-2 = UAT 声称 `sidecar-g810-r9-9a22c33b.json` 已入库而 `74d58d14` 树内不存在（r9 轮未发生收尾 commit）；L-1 = `!!binary b3V0Y29tZQ==` 作为**键名**（= `outcome`）在 node/constructed 两层都漏；L-2 = green runner 注释默认值 / checker docstring 文案旧。

- **本轮绑定**：`1db667bac7bf32f0c473fdb78a647f0224620bcf`（r11 develop commit；父 = `74d58d14`）。r11 全部改动只在 `_bmad-output/**`：核对脚本 v4.8 → **v4.9**（`7dcfd394…` → `59935c2cac462ff1fbd3e486171dfd2bb23f4a740beca6b51a1e8d4b08f7d6c4`）+ r11 运行器/证据 + **r9/r10 顺延存档一并入库**（§九.46，非 amend）+ UAT r11 段。**product code diff = 0**（`git --no-pager diff --stat 4120e0b6 1db667ba -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- **r11 修法（§九.44）**：
  ①（r10-M1）`_ALNUM_TOKEN_RE` 由 `{1,40}` → `+`（**不限长**）：任何 `^[0-9A-Za-z]+$` token 要么是 8–40 位小写 hex OID（可解引用），要么 `sha-missing` 红。
  ②（r10-L1）`outcome` **键**标量归一化：node 层 `_node_scalar_text(k)`、constructed 层 `_iter_key_values` 内对非 str 键用 `_scalar_text()` ⇒ `{ !!binary b3V0Y29tZQ==: pass }` 命中 `pass-unsupported`。
  ③（r10-M2）登记勘误 + **补入库** `sidecar-g810-r9-9a22c33b.json`；**新增 `g810-r11-artifact-audit.zsh`**（UAT 引用的 evidence-g810 产物名逐条 `git cat-file -e <REF>:<path>`）——预修审计对 `74d58d14` = rc=1 / missing=1（恰为该件），post-commit 审计对 `1db667ba` = **rc=0 / tracked=42 / missing=0**。
  ④（r10-L2）green 注释默认值与 checker 内「4–40 位」文案校正。

**最小读取面**（其余不必读）：

1. 脚本 diff：`git --no-pager diff --no-color 74d58d14 1db667ba -- _bmad-output/审查/evidence-g810/check_g810_refs.py _bmad-output/审查/evidence-g810/g810-r9-green.zsh`；v4.9 重点 = `_ALNUM_TOKEN_RE` / `_check_provenance_tokens` 形态分支 / `_scan_node_outcome_pass` 键归一化 / `_iter_key_values` 键归一化。
2. 负控（**先红后绿**，两相位）：`negctl-r11-pre-20260920T141402.txt`（**v4.8** 提取自 `74d58d14`：R11 两条穿透 rc=0；其余 25 条按既定口径）→ `negctl-r11-post-20260920T141457.txt`（**v4.9**：`R11-M1-longsha` `sha-missing`、`R11-L1-binkey` `pass-unsupported` ×2；25 条旧用例同红；F2 rc=0 且 digest 变）；锚群 = `anchor-battery-r11-v49-20260920T141543.txt`（8/8 红 + 对照 rc=0）；YAML 门 = `yamlgate-branches-r11-v49-20260920T141549.txt`（5/5 红 + 对照 rc=0）；**产物审计** = `artifact-audit-r11-20260920T141152.txt`（预修，对 `74d58d14` rc=1 / missing 恰为 `sidecar-g810-r9-9a22c33b.json`）与 **post-commit** `artifact-audit-r11-20260920T141637.txt`（对 `1db667ba` rc=0 / tracked=42 / missing=0）；正常底账 = `g810-green-r11-20260920T141554.txt`（`v4.8@74d58d14 = eb60d83e…` → `v4.9@74d58d14 = 7ec785d3…`）与 **post-commit** `g810-green-r11-20260920T141637.txt`（`prev@74d58d14 = b33cd1bf…` → `v4.9@1db667ba = 43c417e7…`，rc=0）。
3. UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`：§九.44–47（r11 修法/负控表/顺延入库/收尾结构）+ §十.43–45 + §十一.42–44；§九.42④ 已就地勘误（M-2）。
4. 底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md` §3 fenced YAML 块（**不要写死行号**）+ §2.13 六链表（r11 未改底账内容）。
5. JEV 分诊：`jev-triage-1db667ba.json` + 运行 stdout `jev-triage-1db667ba-run-20260920T141639.txt`（jev-1.13.0，`calls: 1`；唯一代码文件 = `check_g810_refs.py`（+16/−7，urgency **2.65** / P(review)=0.67 / risk=logic），VERDICT REVIEW）+ **机器可读 sidecar** `sidecar-g810-r11-1db667ba.json`（`path_decoded=true` / `path_validation_failures={}`）。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. **r10-M1 闭合**：`6337e320` → 41×`a` pre rc=0 → post rc=1×2 `sha-missing`；合法 hex OID 仍绿（canonical rc=0）；1–3 位 `abc`（r10-M3）在 v4.9 下仍红。
2. **r10-L1 闭合**：`- {!!binary b3V0Y29tZQ==: pass}` pre rc=0 → post rc=1（`pass-unsupported` node 层 + 解析值，路径 `$.criteria[50].outcome@182`）。
3. **r10-M2 闭合**：`sidecar-g810-r9-9a22c33b.json` 已在 `1db667ba` 树内（`git cat-file -e` 通过）；产物审计 post-commit rc=0（tracked=42 / missing=0）；预修审计（对 `74d58d14`）rc=1 且 missing_list 恰为该件。
4. **r10-L2 闭合**：`g810-r11-green.zsh` 注释与默认值一致（`PREV=${1:-74d58d14}`）；checker 文案与实现一致（不限长）。
5. **未放宽旧失败面**：25 条旧用例（r10/r9/r8/r6/r7 全量）在 v4.9 下同型；锚群 8/8；YAML 门 5/5；canonical rc=0（两代 digest 链）。
6. **未越界**：r11 只改 `_bmad-output/**`；底账内容一字未动；product code diff = 0；未 amend 已入库 commit（r9/r10 顺延存档随本轮入库属新增，非 amend）。
7. **存档完备**：r9/r10 两轮的 prompt / 审查存档 / JEV JSON + 运行 stdout / sidecar / post-commit green 均已随 r11 develop commit 入库；`*.stderr` 一律未入库。

# ③ 请按重要性回答（JEV urgency：`check_g810_refs.py` 2.65 / risk=logic）

① **4 项 open（M-1/M-2/L-1/L-2）是否真的闭合**？逐项给判；不闭合请给**未被拦下的输入**（尤其：不限长判定是否引入新的假红面、键归一化是否覆盖 alias/merge 源里的 binary 键、产物审计的口径面是否会被绕过）。
② v4.9 是否仍有与**其声称**不符的恒绿面？（UAT §十.36–45 的声明边界请判定「可接受」还是「仍需计」）
③ r11 证据链是否自洽：先红后绿、25/25 回归、锚群/YAML 门、产物审计两相位、digest 两代链、`sha_equal=yes`、绑定（`:(exclude)_bmad-output`）、PENDING-R11 口径、r9/r10 顺延存档入库事实。
④ **本轮收口条件（B/H/M/L = 0/0/0/0）是否满足**；不满足请给最小反例（**M/L 也要给**）。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`**；若四级全无，写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`——该行会用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评核对脚本 v4.9 + 产物审计 + r11 证据面 + 上述 4 项闭合；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r11 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界（非 fence YAML 面 / 产品树散文路径 / 其它键名枚举）在**本轮**扩面——若你认为需扩面，记为 MEDIUM/LOW 并指出准确边界即可。
