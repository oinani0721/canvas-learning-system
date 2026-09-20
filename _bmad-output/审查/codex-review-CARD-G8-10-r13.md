BLOCKER: 无 / HIGH: 无

## MEDIUM

1. `_bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r13.md:10`、`:18` — r13 prompt 把“c84a0cc4 HEAD 预检”写成 `77/4/73/0 rc=0`，并引用不存在的 `jev-triage-c84a0cc4-run-20260920T145008.txt`；现存 c84 绑定审计件实际是 `74/4/69/1 rc=1`，JEV stdout 实存件名是 `…145009.txt`。  
   **对照输入**：读 `_bmad-output/审查/evidence-g810/artifact-audit-r12-20260920T145007.txt:79-85` 与 `_bmad-output/审查/evidence-g810/jev-triage-c84a0cc4-run-20260920T145009.txt:1`；当前 dirty UAT 可复算出 `77/4/73/0`，但那还不是 REF-bound 入库证据，PENDING-R13 不能覆盖 prompt 里已写死的结果。

2. `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:335`、`:486` — UAT 登记的审计 runner blob `f83241eb…` 与实际入库 runner `91e432d3…` 不符，且输出头仍写 `v2.3` 而非 v2.4.2。  
   **对照输入**：并排读 `g810-r12-artifact-audit.zsh:1-2`、四个 `1449xx` 审计件如 `artifact-audit-r12-20260920T144926.txt:1-2`，再对 UAT 登记值；`git ls-tree HEAD` 实际 blob 是 `91e432d36109a8c8bc46fb91ef1a0427a1aafa5f`。

3. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:56-66`、`:93-98` — 排除名单按名字写入 dict，后一条会覆盖前一条 reason，因此“同名两条：第一条空理由、第二条非空理由”会让空理由项消失并可 `rc=0`。  
   **未被拦下的输入**：在 §十三 连续加入 `- \`real-missing.txt\` —` 与 `- \`real-missing.txt\` — 历史误写`，且正文引用 `real-missing.txt`；`excluded` 只剩非空 reason，不会报 `excl-empty-reason`。

4. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:98`、`:113-118` — PARTIAL 的 `calls=0` 来自未锚定的第一个 `calls:` 字符串，不保证来自 `Model:` 机器行；较早的 Commit/散文 `calls: 0` 可掩盖真正 `Model … calls: 5`。  
   **未被拦下的输入**：构造 stdout 前部含 `calls: 0`、机器行含 `Model: … | calls: 5`，JSON `files=[]` / `code_files=[]`，带 `--allow-empty`；生成器会误判三方一致并输出 `partial=true`、rc=0。

5. `_bmad-output/审查/evidence-g810/g810-r13-audit-ctl.zsh:19-23`、`:33-41` 与 `_bmad-output/审查/evidence-g810/g810-r13-sidecar-negctl.zsh:37-50` — 两组控制件只断言 rc=1，不断言目标标签；audit C3 的固定 anchor 在当前入库 UAT 已不存在，重跑会先失败生成 fixture，随后“缺 override 文件导致 rc=1”仍可被当成控制通过。  
   **负控输入**：按当前 HEAD 直接重跑 `g810-r13-audit-ctl.zsh`，或删除 sidecar 的 PARTIAL 分支但保留空路径校验；二者仍可能出现 `verdict_bad=0`，却没有对应 `excl-*` / `partial-inconsistent` 证据。

## LOW

1. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:44-53` — marker 只要求存在，不校验唯一、行首或章节位置；把真实 r8 标记删除并在 §十三 前放置一次字符串，可把审计面缩到尾部。  
   **未被拦下的输入**：UAT 尾部保留 `29. **r8 开工自证` 字符串但删除真实第 29 条；脚本不报 `marker-missing`，只审计尾部片段。

2. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:24-25` — 输入临时文件已用私有 `$TMPD`，但输出文件名仍是秒级时间戳；两个并发运行写到同一 OUTDIR 且同一秒会互相覆盖最终证据。  
   **对照输入**：并发审计两个 REF 到同一 OUTDIR 并强制同秒；输入面隔离，但最终 artifact 只剩后写/交错结果。

3. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:69`、`:75-77` — `len(_t)<5` 会静默排除 `a.py` 这类合法 4 字符产物名，而 §十.50 未声明“短名不进面”。  
   **未被拦下的输入**：正文引用缺失的 `` `a.py` ``；正则命中但长度过滤丢弃，缺件不产生 MISS。

4. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:103`、`:115-122`、`:151` — PARTIAL 三方一致不约束 `标记人工审查: 0/0`；`calls=0 ∧ files=[] ∧ code_files=[]` 但标记为 `1/1` 时仍 `partial=true`、rc=0。  
   **未被拦下的输入**：stdout 机器行 `calls: 0`，尾部写 `标记人工审查: 1/1`；sidecar 同时记录 `flagged="1/1"` 与 `partial=true`。

5. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:13`、`:69` — 脚本注释声称含空白名字支持，但 `[^\s…]+` 实际排除空白；UAT §十.50 才是正确边界。  
   **对照输入**：引用 `` `foo bar.txt` ``；脚本注释说支持，实际 names 面不含它。

---

# ① r12 项与自发现项逐项判定

| 项 | 判定 | 核对结果 |
|---|---|---|
| r12-M1 数值勘误 | **既有四件已闭合；新增 r13 prompt 预检不自洽** | §九.55 与 `143035/143207/143247/143334` 及四个 `1449xx` 件逐项相符；但 prompt 的 c84 `77/4/73/0 rc=0` 无绑定件，现存 c84 件为 `74/4/69/1 rc=1`。 |
| r12-M2 死项/空理由 | **主路径闭合，残余 MEDIUM** | C2/C3 存档件确有 `excl-dead` / `excl-empty-reason` 且 rc=1；当前 4 条排除均 live、reason 非空；但重复同名可覆盖空理由。 |
| r12-M3 三方一致 | **指定三字段主路径闭合，calls 解析可伪装** | N4/N5 存档输出确有 `partial-inconsistent` 且 rc=1，`4c5777d0` 真实空 commit 为 `partial=true` rc=0；但未锚定 `calls:` 可取错来源。 |
| r12-L1 marker-missing | **缺失场景闭合；位置/唯一性仍弱** | C1 在 `dce85102` 上真实红；但 marker 可被移位。 |
| r12-L2 私有 temp | **输入面闭合；输出名仍可撞** | `$TMPD/uat.txt` / `$TMPD/tree.txt` 已与 REF 同次运行绑定；输出仍秒级命名。 |
| r12-L3 `/ + ( )` | **这些字符闭合；短名未声明** | `NAME_RE` 已接受 `/ + ( )`，`scripts/jev_review_triage.py` 与 goal 卡均入面；`a.py` 仍被长度过滤。 |
| r12-L4 runner provenance | **输出面闭合；UAT 登记错 blob** | 输出记 `runner_sha256=ce412a…` / `runner_blob=91e432…` 且非空；UAT 写 `f83241…`。 |
| 自发现 tree 同绑缺陷 | **闭合** | 脚本 `:38` 生成 `$TMPD/tree.txt`、`:79` 读取；`144926` 对 `74d58d14` 正确报 `sidecar-g810-r9-9a22c33b.json` MISS。 |

# ② 声明边界与恒绿面

- **可接受**：basename-only、不证路径归属/内容哈希、不合并/不集成/不触发真实故障、排除理由的语义正确性需人工复核、空白/通配/占位符/绝对路径/`..` 起步/反斜杠不进面，这些在 §十.46–52 已明确声明。
- **仍需计**：重复空理由、非机器行 `calls:`、短文件名、marker 移位、输出碰撞、`标记人工审查` 不参与 PARTIAL 一致性，以及控制件只看 rc 的问题，见上方 M/L。

# ③ r13 证据链

已独立核实：HEAD=`c84a0cc4…`，父=`4c5777d0…`；r13 diff 全部在 `_bmad-output/**`；`4120e0b6..HEAD` 排除 `_bmad-output` 后 product diff 为空；底账 sha256 仍为 `cbfd619d…`。四个 `1449xx` REF 数字与 missing list 均与文件原文一致；C1/C2/C3 与 sidecar N1–N5/P1/P2 的存档标签存在；green 链 `prev=1be00749… → here=dbb6040b…` 与 c84 绑定；JEV JSON/stdout 的 calls=1、urgency=2.69、review=0.73、risk=logic 一致。

不自洽处主要是：prompt 声称的 c84 rc=0 预检没有绑定证据、JEV stdout 文件名差 1 秒、UAT runner blob 错登，以及控制件对当前 HEAD 不具备稳定复跑性。

# ④ 收口判定

**不满足 B/H/M/L = 0/0/0/0。本轮为 B/H/M/L = 0/0/5/5。**

最小反例已在上列 M/L 给出；其中 M-2 与 M-3 直接是 r12-M2/M3 的残余穿透，M-1/M-2 是证据登记错绑，M-5 是控制件假通过面。

# ⑤ 其它

未发现越界：当前 tracked/untracked 变更均在 `_bmad-output/**`，未改底账或产品代码；`sidecar-g810-r13-c84a0cc4.json` 与最终 rc=0 审计件仍处 PENDING-R13，按口径不能提前当作已入库证据。
