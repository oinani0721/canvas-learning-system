你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r9 = 本 goal 收敛轮的第 2 轮**（卡文 `收敛-CARD-G8-10-checker.md`：连续 loop，直到绑最终 HEAD 的一轮 **B/H/M/L = 0/0/0/0** 才释放合并门）。上一轮 **r8 = B0/H1/M2/L2**（存档 `codex-review-CARD-G8-10-r8.md`，绑 `3457f70b`）：H-1 = `!!binary` 形态 `outcome: b"pass"` 两层扫描都不拦；M-1 = 平文 SHA 槽接受 `HEAD`/`main` 可变 symbolic ref；M-2 = evidence 路径检查用字面 `startswith("_bmad-output/")`，`./_bmad-output/…` 逃逸；L-1 = green 运行器 post-commit 取错 prev（**已在 r8 收尾 commit `ca597bbf` 入库绑定**）；L-2 = sidecar `code_files` 保留 git quoted/octal 转义。

- **本轮绑定**：`9a22c33b87b87e3ded707ac3be712c0e7fe1632a`（r9 develop commit；父 = `ca597bbf` = r8 收尾）。r9 全部改动只在 `_bmad-output/**`：核对脚本 v4.6 → **v4.7**（`3fd00174…` → `2af0045b19141d21c615a1ae8744ae099e28316f5fd803d2871f10283dd14a9d`）+ sidecar 生成器（`g810-r8-sidecar.py` 加 `_decode_git_path`）+ r8/r7 sidecar 重生成 + r9 运行器/证据 + UAT r9 段。**product code diff = 0**（`git --no-pager diff --stat 4120e0b6 9a22c33b -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- **r9 修法（4 项 open 全修，口径见 UAT §九.37）**：
  ①（r8-H1）新增 `_scalar_text()` / `_node_scalar_text()`：node 层对 `tag:yaml.org,2002:binary` 标量**先 base64 解码**再比对；constructed 层归一化 str / bytes / bytearray；**非字符串标量的 `outcome` 值 ⇒ `outcome-type` fail-closed 红**（两层）；`outcome` 值不在 {pass,fail,not_yet} ⇒ `outcome-enum` 红。
  ②（r8-M1）平文 SHA 槽只接受 **immutable 8–40 位小写 hex OID**；`HEAD`/`main`/畸形值一律 `sha-missing` 红（不再「能 rev-parse 就算数」）。
  ③（r8-M2）引用路径**先归一化**（剥前导 `./`）；绝对路径 / 含 `..` 段直接 `ref-missing` 红；归一化后以 `_bmad-output/` 开头者做存在性 + 内容进 digest。
  ④（r8-L2）sidecar `code_files` 现为**可直接 `Path(...)` 解析**的 UTF-8 路径（原样存 `code_files_raw`；`path_decoded: true`）；r8/r7 sidecar 就地重生成（审后改件，随本轮重送）。

**最小读取面**（其余不必读）：

1. 脚本 diff：`git --no-pager diff --no-color ca597bbf 9a22c33b -- _bmad-output/审查/evidence-g810/check_g810_refs.py _bmad-output/审查/evidence-g810/g810-r8-sidecar.py`；并读 v4.7 全文（重点 `_scalar_text` / `_node_scalar_text` / node 层 `outcome-type` 分支 / constructed 层三分支 / `_check_provenance_tokens` 的路径归一化与 hex 收紧）。
2. 负控（**先红后绿**，两相位）：`negctl-r9-pre-20260920T134140.txt`（**v4.6** 提取自 `3457f70b`：8 条新用例全穿透 rc=0；A–G/r6/r7 回归按 r8 口径）→ `negctl-r9-post-20260920T134226.txt`（**v4.7**：8 条新用例全红——`R9-B1-bin`/`R9-B2-binalias` `pass-unsupported`、`R9-B3-seq` `outcome-type`×2、`R9-M1-head`/`R9-M1-main` `sha-missing`、`R9-M2-{dotpath,dotdot,abs}` `ref-missing`；A–G 红、`F2` rc=0 且 digest `aa604ecf… → 15ebec57…`、r6/r7 红）；锚群 = `anchor-battery-r9-v47-20260920T134307.txt`（8/8 红 + 对照 rc=0）；YAML 门 = `yamlgate-branches-r9-v47-20260920T134314.txt`（5/5 红 + 对照 rc=0）；正常底账 = `g810-green-r9-20260920T134329.txt`（`v4.6@ca597bbf = cbf2f7b7…` → `v4.7@ca597bbf = aa604ecf…`，rc=0）与 **post-commit** `g810-green-r9-20260920T134413.txt`（`prev@ca597bbf = df553078…` → `v4.7@9a22c33b = c70a6184…`，rc=0）。
3. UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`：§九.37–39（r9 修法/负控表/作废件）+ §十.36–39 + §十一.35–38；r9 判定 = 收尾回填（PENDING-R9）。
4. 底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md` §3 fenced YAML 块（**不要写死行号**）+ §2.13 六链表（r9 未改底账内容）。
5. JEV 分诊：`jev-triage-9a22c33b.json` + 运行 stdout `jev-triage-9a22c33b-run-20260920T134414.txt`（jev-1.13.0，`calls: 2`；两文件 = `check_g810_refs.py`（+79/−12，urgency **2.87** / P(review)=0.76）+ `g810-r8-sidecar.py`（+45/−4，urgency 2.37 / P(review)=0.63），risk=logic，VERDICT REVIEW）+ **机器可读 sidecar** `sidecar-g810-r9-9a22c33b.json`（calls/verdict/urgency/risk/review/test/code_files/sha/bound_head + provenance；`code_files` 两条均可 `Path(...)` 解析——L-2 闭环证据；另附重生成的 `sidecar-g810-r8-3457f70b.json` / `sidecar-g810-r7-retro-6816ff71.json`）。
6. r8 收尾（L-1 绑定）：`git show ca597bbf:_bmad-output/审查/evidence-g810/g810-r8-green.zsh` 含 `PREV_REF` 参数（`PREV=${1:-dce85102}`）；证据 `g810-green-r8-20260920T132049.txt` 即由该版生成。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. **r8-H1 闭合**：B1（复核原形 `outcome: !!binary cGFzcw==`）pre v4.6 rc=0 → post v4.7 rc=1（`pass-unsupported` node 层 + 解析值）；B2（binary + anchor + merge 源 alias）同型；B3（非标量 `[pass]`）→ `outcome-type`×2。
2. **r8-M1 闭合**：`HEAD` / `main` 两例 pre 穿透 → post `sha-missing`；合法 hex OID 仍绿（canonical rc=0）。
3. **r8-M2 闭合**：`./_bmad-output/…`（不存在）/`../_bmad-output/…`/`/tmp/_bmad-output/…` 三变体 pre 穿透 → post `ref-missing`。
4. **r8-L2 闭合**：sidecar 生成器解码 git quoted/octal；r9 sidecar 的 `code_files` 两条路径 `Path(...).exists()` 为 True；r8/r7 sidecar 已同法重生成。
5. **未放宽旧失败面**：A–G（r8 用例）在 v4.7 下仍全红（F2 rc=0 且 digest 变 = 绑定）；r6-A/r6-B/r7-A/r7-B 仍红；锚群 8/8；YAML 门 5/5；canonical rc=0（`v4.7@ca597bbf = aa604ecf…`、`v4.7@9a22c33b = c70a6184…`）。
6. **L-1 已绑定**：`ca597bbf` 内的 green 运行器 = `PREV_REF` 版；`g810-green-r8-20260920T132049.txt` 的 `prev@dce85102` 与该版一致。
7. **未越界**：r9 只改 `_bmad-output/**`；底账内容一字未动；product code diff = 0；未 amend 已入库 commit（r9 = develop commit + 计划中的收尾 commit）。

# ③ 请按重要性回答（JEV urgency 降序：`check_g810_refs.py` 2.87 / `g810-r8-sidecar.py` 2.37，均 risk=logic）

① **4 项 open（H-1 / M-1 / M-2 / L-2）是否真的闭合**？逐项给判；不闭合请给**未被拦下的输入**（尤其：`!!binary` 的其它形态〔block scalar / anchor / merge 组合 / 非 UTF-8 解码〕、`outcome` 其它构造类型、路径归一化的其它变体、sidecar 其它字段的机器可用性）。
② v4.7 是否仍有与**其声称**不符的恒绿面？（`outcome-type` / `outcome-enum` / hex 收紧 / 路径归一化 / `_decode_git_path` / 白名单死项；UAT §十.36–39 的声明边界请判定「可接受」还是「仍需计」）
③ r9 证据链是否自洽：先红后绿、21/21 回归、锚群/YAML 门、digest 两代链、`sha_equal=yes`、绑定（`:(exclude)_bmad-output`）、PENDING-R9 口径。
④ **本轮收口条件（B/H/M/L = 0/0/0/0）是否满足**；不满足请给最小反例（**M/L 也要给**——本 goal 的闸门含 M/L）。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`**；若四级全无，写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`——该行会用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评核对脚本 v4.7 + sidecar 生成器 + r9 证据面 + 上述 4 项闭合；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r9 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界（非 fence YAML 面 / 产品树散文路径）在**本轮**扩面——若你认为需扩面，记为 MEDIUM/LOW 并指出准确边界即可。
