BLOCKER: 无 / HIGH: 无

## MEDIUM

1. `_bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r14.md:9`、`:24` — r14 prompt 把 `artifact-audit-r12-20260920T150310-64176.txt` 称为“入库审计件”并称 §九.59 数字来自已入库件，但该文件在 `b93812ea` 树中不存在，当前仅为 untracked 工作区件。  
   **对照输入**：`git rev-parse --verify 'b93812ea:_bmad-output/审查/evidence-g810/artifact-audit-r12-20260920T150310-64176.txt'` 失败；同时 `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:370-372` 明确写“HEAD 预检（非入库）”且该件“随收尾 commit”。

2. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:71-77`、`:105-114` — §十三 的“逐条”解析仍会静默丢弃以 `` - ` `` 开头但不匹配 `名 — 理由` 格式的条目，malformed duplicate 可绕过 `excl-duplicate` / `excl-empty-reason`。  
   **未被拦下的输入**：在 §十三 连续写入 `` - `real-missing.txt` — 历史误写 `` 与 `` - `real-missing.txt` ``，并让正文引用 `real-missing.txt`；第二条被丢弃，第一条有效理由即可 SKIP 且 rc=0。

3. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:98-104`、`:115-120` — `calls` 与 `标记人工审查` 都取第一个匹配行；多个 `Model:` 机器行或多个 marker 行时，前部 stale `0/0` 可掩盖后部真实 `calls:5` / `1/1`。  
   **未被拦下的输入**：构造 stdout 前部 `Model: jev-1.13.0 | calls: 0` + `标记人工审查: 0/0`，后部再放真实 `Model: … | calls: 5` + `标记人工审查: 1/1`；JSON `files=[]`、`code_files=[]` 并带 `--allow-empty` 时仍得 `partial=true`、rc=0。

4. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:105-118` — PARTIAL 声称要求 `files=[] ∧ code_files=[]`，实现用 `payload.get(...) or []` 把字段缺失/`null` 也当作空数组，未强制字段存在且值确为 `[]`。  
   **未被拦下的输入**：提交缺少 `files` 与 `code_files` 字段的 JSON，stdout 为 `Model: … | calls: 0` 且 marker `0/0`，带 `--allow-empty` 时生成 `partial=true`、rc=0。

5. `_bmad-output/审查/evidence-g810/g810-r14-sidecar-negctl.zsh:19-44`、`:52` — N1–N7 全部带 `--allow-empty`，且 N4–N7 的 `code_files` 均为 `[""]`，N1–N3 又同时有非空 `files`/`code_files`；目标分支即使回归，也会被无关的 `path_decoded=False` 或 `partial-inconsistent` 保红。  
   **负控输入**：删除 `calls` 锚定逻辑或 marker 约束，再重跑 N6/N7；二者仍因 `code_files=1` + 空路径校验 rc=1 并命中泛化标签 `partial-inconsistent`，`verdict_bad` 仍为 0。

6. `_bmad-output/审查/evidence-g810/g810-r14-audit-ctl.zsh:46-49`、`:53-54` — audit 控制件用 `ls -t` 选择最新临时输出，而不是绑定当前 invocation 在 stdout 中返回的 `file=...`；C1b 早退时可复用 C1 的同标签旧件。  
   **负控输入**：先让 C1 正常产出 `marker-count`，再让 C1b 在创建输出件前 rc=1（例如 REF/runner 早失败）；`ls -t` 仍找到 C1 旧件，C1b 记录 `assert=yes`。

## LOW

1. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:44-62`、`:82-89` — marker 只校验“行首且恰一次”，并只检查 §十三 不在其之前；未证明该 marker 确实位于 §九 的真实第 29 条，后移 marker 可截断审计名面。  
   **未被拦下的输入**：把唯一 marker 移到 §九尾部/§十之前，并把需要保留的引用名一同放到新 marker 之后；§十三 仍在后，工具会以缩小后的名面运行。

2. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:29-30` — `runner_sha256/blob` 来自当前工作区 runner，不由 `REF:path` 反解，也未断言该 blob 在被审 REF 树内。  
   **门未覆盖的路径**：用脏工作区 runner 对旧 REF 运行；输出可记录一个不在 REF 树中的 runner blob 并仍按树内 UAT/tree 计算 rc。

3. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:2`、`:45`、`:95` — 脚本头部仍自称 v2.3，而实际逻辑/输出为 v2.5.1/v2.5，版本标签残留歧义。  
   **对照输入**：并排读脚本头部、`:45` 的 v2.5.1 注释与任意 r14 输出件 `:1` 的 v2.5 头。

---

# ① r13 10 项闭合判定

| r13 项 | 判定 | 依据 |
|---|---|---|
| M-1 数字来源/prompt | **不闭合** | r14 prompt 再次把未入库的 `150310-64176` 称为入库件；见 MEDIUM-1。 |
| M-2 runner 登记 | **主值闭合，残余 LOW** | `b93812ea` 实际 blob/sha256 与 UAT 及输出件一致；但 runner provenance 不强制来自 REF。 |
| M-3 §十三 duplicate | **部分闭合** | well-formed duplicate 会红，C4 也命中；malformed duplicate 仍可静默丢弃。 |
| M-4 `calls` 锚定 | **单行场景闭合，多机器行不闭合** | `^Model:` 锚定有效，N6 场景不再取 `Commit:` 行；但 first-match 可被 stale Model 行掩盖。 |
| M-5 控制件标签断言 | **部分闭合** | 存档确有目标标签；但 sidecar fixture 混入独立失败源，audit 控制未绑定当前输出件。 |
| L-1 marker 唯一/位置 | **唯一性行首闭合；位置弱** | 恰 1 次已实现；未绑定 §九真实位置。 |
| L-2 输出撞名 | **闭合** | 输出名含 PID，`150310-64176` 等件名可见。 |
| L-3 短名排除 | **闭合** | `len<5` 已移除；`a.py` 会进入名面。 |
| L-4 PARTIAL marker | **单 marker 场景闭合；可伪装** | `1/1` 会红，N7 存档命中；但 first-match marker 与缺失数组问题仍在。UAT 允许 marker 缺席。 |
| L-5 注释/实现 | **声明边界闭合；版本注释残留** | “含空白不进面”已一致；但顶部 v2.3 标签滞后。 |

# ② 声明边界判定

- **可接受**：basename-only、不证路径归属/内容哈希、含空白/通配/占位符/反斜杠/绝对路径/`..` 起步不进面、§十三 理由语义需人工复核、JEV 模型身份不能自证、不合并/不集成/不触发真实故障、同进程内输出撞名不构成路径。这些在 §十.46–55 有明确声明。
- **仍需计**：malformed §十三 条目、marker 章节/位置、多 `Model:`/多 marker、缺失数组与 `[]` 等价、控制件失败源混杂、控制输出未按 invocation 绑定、runner blob 不 REF 反解；见上方 M/L。

# ③ r14 证据链核对

- **自洽部分**：HEAD=`b93812ea…`，父=`c84a0cc4…`；`c84a0cc4..b93812ea` 只改 `_bmad-output/**`；`4120e0b6..b93812ea` 排除 `_bmad-output` 后 product diff 为空；底账在 HEAD 与工作区 sha256 均为 `cbfd619d…`。r13 存档/证据确为新增入库，非 amend。
- **逐 REF 数字相符**：`150151=39/3`、`150153=53/2`、`150154=69/4`、`150155=71(excl2)/2`、`150157=74(excl4)/1`、r13-era `145007=74/4/69/1`。我用 `b93812ea` 的树内 UAT/tree 独立重算得 `markers=1 names=78 excluded=4 unique=4 tracked=74 missing=0`，与 `150310-64176:83-88` 一致。
- **控制/JEV/green 内容相符**：C1/C1b/C2/C3/C4 标签与 `verdict_bad=0` 存在；N1–N7/P1/P2 输出与登记值一致；JEV JSON/stdout/sidecar 的 `calls=1`、`+6/-3`、urgency `2.36`、review `0.60`、risk `logic` 一致；green 件内部为 `d0683276… → 7866c708…` 且 rc=0。
- **不自洽部分**：`150310-64176`、`g810-green-r11-20260920T150310.txt`、r14 JEV、sidecar、prompt/review 当前均未入库；UAT §九.61 仍为 PENDING-R14。只有 sidecar 被 prompt 明确标注“随收尾 commit”，审计件却被误称已入库。

# ④ 收口判定

**不满足 B/H/M/L = 0/0/0/0。本轮为 B/H/M/L = 0/0/6/3。**  
最小反例已逐条列在 MEDIUM/LOW；其中 MEDIUM-1 已足以阻止本轮以“最终 HEAD 绑定且全零”释放合并门。
