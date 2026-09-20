BLOCKER: 无 / HIGH: 无

## BLOCKER

无

## HIGH

无

## MEDIUM

1. `_bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r15.md:8`、`_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:390-392` — r15 prompt 再次把当前 untracked 的 `artifact-audit-r12-20260920T151540-70866.txt` 称为「r15 HEAD 的入库审计件」，且 :23 声称数字来源均为已入库件。  
   **对照输入**：`git rev-parse --verify '0aa87523:_bmad-output/审查/evidence-g810/artifact-audit-r12-20260920T151540-70866.txt'` 失败；UAT :390 明确标为「非入库」、:392 明确归入收尾 commit / PENDING-R15。

2. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:100-107`、`:112`、`:123-130` — r14-M3 未完全闭合：唯一性检查只统计行首无缩进的 `Model:` / `标记人工审查:`，真实坏行只要缩进即可不被计数，而 calls/marker 仍取前部 clean 值。  
   **未被拦下的输入**：JSON `files=[]`、`code_files=[]`，stdout 为 `Model: jev | calls: 0` + `标记人工审查: 0/0`，再另起缩进行的 `  Model: jev | calls: 5` 与 `  标记人工审查: 1/1`；生成器仍可判 `partial=true` 且 rc=0。

3. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:109-118`、`:131-139`、`:195` — verdict fallback 会把输出表头本身当作 verdict 数据行，缺真实分诊行时仍可恒绿。  
   **未被拦下的输入**：给足 JSON 的 urgency/risk/review/test/sha/code_files，stdout 只含 `FILE … RISK             VERDICT` 表头和一条 `Model: … | calls: 1`、无数据行；fallback 匹配 `('RISK','VERDICT')`，写出 `verdict="VERDICT"` 且 rc=0。

## LOW

1. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:71-74` — r14-L1 的「移到 §九尾部」已被 `marker-context` 拦下，但锚只看标记前最近编号项为 28，不限制 28 与 29 之间的正文内容。  
   **未被拦下的输入**：在真实 28 项和 29 项之间插入 `` `missing.txt` `` 引用，并让该文件不在树内；最近编号仍是 28、marker 仍唯一，名字面却从 29 项之后才开始，`missing=0`。

2. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:35`、`_bmad-output/审查/evidence-g810/artifact-audit-r12-20260920T151456-69743.txt:37-40` — runner 在被审 REF 中不存在时，`git rev-parse` 的失败输出与 fallback `absent` 同时进入 `runner_blob_in_ref`，形成两行 malformed provenance，而不是单一 `absent`。  
   **对照输入**：并排看 `151456-69743:39-40` 或 `151458-69761:53-54`，字段先是 `74d58d14:_bmad-output/...`，下一行才是 `absent`；同类 `151503-69969:79-81` 的 HEAD 情况则是正常 blob。

3. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:2`、`:59`、`:116`、`_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:374`、`:546` — r14 存档中的第三条 LOW（版本标签残留）未修：脚本头仍是 v2.3，注释/输出混合 v2.6/v2.6.1，而 UAT 声称 6M+3L 全修。  
   **对照输入**：并排读脚本 :2、:59、:116 与 UAT :374/:546，再对照 `_bmad-output/审查/codex-review-CARD-G8-10-r14.md:31-32` 的 r14-L3。

---

# ① r14 6M + 3L 闭合判定

| r14 项 | 判定 | 依据 |
|---|---|---|
| M-1 数字来源 / 入库表述 | **不闭合** | r15 prompt :8/:23 再次把 untracked 件称为入库来源；见 MEDIUM-1。 |
| M-2 §十三 malformed 静默丢弃 | **闭合** | `g810-r12-artifact-audit.zsh:84-92` 对所有 `- ` 行逐一解析，不匹配即 `excl-malformed`；`:127-138` 入 failures；C7 输出 `:47-56` 命中。 |
| M-3 Model/marker 多行伪装 | **不闭合** | 未缩出的多行会红，但缩进的真实坏行仍可隐藏；见 MEDIUM-2。 |
| M-4 PARTIAL 字段存在且恰 `[]` | **闭合** | `g810-r8-sidecar.py:126-128` 分别要求 `"files" in payload == []`、`"code_files" in payload == []`；N8 输出 `sidecar-negctl-r15...:25-27` 红。 |
| M-5 负控靶向性 | **闭合** | N4/N5/N7/N8 均只保留目标缺陷，N6 只保留双 Model 缺陷，T 孪生 `:28-30` rc=0 且 `partial=true`；audit C5/C7 虽额外触发 duplicate，但目标标签断言使 detector 回归时 `verdict_bad` 不能靠无关红保绿。 |
| M-6 控制件 `ls -t` | **闭合** | `g810-r15-audit-ctl.zsh:47-52` 从本次 invocation stdout 的 `file=` 回解 `$TMP` 输出；存档各段均有实际 `# file=...`。 |
| L-1 marker 移位截断 | **主反例闭合，残余 LOW** | 移到 §九尾部会被 `marker-context` 拦；但 28/29 间插入名字仍可置于名面外；见 LOW-1。 |
| L-2 runner provenance | **HEAD 主值闭合，残余 LOW** | HEAD 件 `151540-70866:79-81` 确实 `blob_used == blob_in_ref == 0224341a…`；但 absent REF 的字段格式 malformed；见 LOW-2。 |
| r14-L3 版本标签残留 | **不闭合** | r15 UAT 称 6M+3L 全修，但脚本头/输出仍混用 v2.3/v2.6/v2.6.1；见 LOW-3。 |

# ② 声明边界判定

**可接受、不计新问题**：basename-only、不证路径归属/内容哈希/是否由本卡提交（§十.46）；含空白/通配/占位符等不进名面（§十.53）；§十三 理由语义仍需人工复核（§十.49/51）；sidecar 不证明 JEV 过程真实语义（§十.57）；未合并、未集成、未触发真实故障（§十.58）。

**仍需计**：untracked 件被称入库、缩进机器行伪装、表头伪 verdict、28/29 间名面截断、absent runner provenance malformed、版本标签/闭合账目不一致；即上方 M/L。

# ③ r15 证据链核对

**自洽部分**：

- HEAD = `0aa875239de78e5226be4102fc162abc6fac08bb`，父 = `b93812eac6685d36bd45c9ea34cc4eab3e2986bd`，非 amend。
- `b93812ea..0aa87523` 只改 `_bmad-output/**`；`4120e0b6..HEAD -- . ':(exclude)_bmad-output'` 为空。
- 底账在 HEAD 与工作区 sha256 均为 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- r14 顺延存档确已进入 r15 commit：r14 review/prompt、JEV JSON/stdout、sidecar、`150310-64176` audit、`150310` green 均在 `0aa87523` 树内。
- C1–C7 目标标签与 `verdict_bad=0` 相符；N1–N8、T、P1 与 `verdict_bad=0` 相符；生成器 sha `b86487db…` 与当前树内脚本一致。
- `151540-70866` 的内容本身与 `0aa87523` 绑定：ref/full SHA、UAT blob `22e593c1…`、runner sha/blob 均相符；我独立重算名面为 `names=71`，6 个 missing 全部对应 §十三 6 条排除，因此 `tracked=65 missing=0` 成立。
- 逐 REF 输出与登记一致：`74d58d14=3缺`、`1db667ba=2缺`、`2e52f551=4缺`、`4c5777d0=2缺`、`c84a0cc4=1缺`、`b93812ea=0缺`。
- JEV 链数值相符：calls 1、唯一 code file `g810-r8-sidecar.py`、+14/−2、urgency 2.46、review 0.68、risk logic；sidecar 字段与 JSON/stdout一致。

**不自洽 / 未最终闭合部分**：

- `151540-70866`、`g810-green-r11-20260920T151540.txt`、r15 JEV JSON/stdout、sidecar、prompt/review 当前全部是 untracked；这符合 UAT PENDING-R15 的收尾结构，但不符合 prompt「入库审计件」和「数字均来自已入库件」的表述。
- `g810-green-r11-20260920T151540.txt:11,15` 自记 `dirty_untracked=1`，且其自身当前未入库；收尾 commit 后 HEAD/tree OID 变化，仍需按 PENDING-R15 重新绑定最终 digest。
- 两组控制件是在 r15 commit 前以当时 HEAD=`b93812ea` 运行；runner/generator sha 与后来入库内容一致，可作为 precommit 控制，但不能当成 r15 HEAD postcommit 复跑。

# ④ 收口判定

**不满足 `B/H/M/L = 0/0/0/0`。本轮为：**

`B/H/M/L = 0/0/3/3`

最小阻断反例即 MEDIUM-1：prompt 把不在 `0aa87523` 树内的 `151540-70866` 称为入库审计件。即使忽略该文书问题，MEDIUM-2 / MEDIUM-3 也仍是生成器恒绿输入。

预算状态与卡文一致：r8–r15 已用 **8/8** develop commit。因此不应再开 r16 / 第 9 个 develop commit；应停止本轮收敛并交主 session 裁定。

# ⑤ 其它

无 BLOCKER/HIGH 级新增问题；product code 与底账未发现 r15 越界改动。本次审查仅执行只读 git/grep/sed/shasum 类核对，未修改文件、未连接数据库或网络服务。
