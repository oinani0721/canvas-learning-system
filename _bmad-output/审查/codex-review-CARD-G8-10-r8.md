BLOCKER: 无 / HIGH: 1 —— 本轮不满足 B/H/M/L = 0/0/0/0，合并门不应释放。

**Now / prohibited / unlock when**

- **Now**：r8 develop commit 的 7 项定向修法大多真实落地，指定负控 / 回归 / 锚群 / YAML 门 / digest 链也内部一致；但 v4.6 仍有一个 fenced YAML 内的 `pass` 穿透面，另有两个 r5-M2 同类恒绿面。
- **Prohibited**：不得宣告「复核第十五批 P6」、不得回填 PENDING-R8 为通过、不得合并。
- **Unlock when**：修复下述 HIGH/M/L 并补两相位负控；重跑 canonical digest；按 §九.34 做收尾 commit；绑定最终 HEAD 后由下一轮独立复核达到 0/0/0/0，且最终树净、product diff = 0、底账 SHA 不变。

---

## BLOCKER

无。

## HIGH

### H-1：`!!binary` 形态的 `outcome: b"pass"` 两层 YAML 扫描都不拦

- `file:line`：`_bmad-output/审查/evidence-g810/check_g810_refs.py:150-155`、`_bmad-output/审查/evidence-g810/check_g810_refs.py:635-637`
- **问题**：node 层只比较 ScalarNode 的原始字符串 `.value == "pass"`，constructed 层只接受 `isinstance(_val, str)`；PyYAML SafeLoader 会把 `outcome: !!binary cGFzcw==` 构造成 `bytes b"pass"`，两层都返回未命中。
- **未被拦下的输入**：在 canonical observability criteria 行后追加  
  `  - {dim: observability-extra, outcome: !!binary cGFzcw==, coverage: partial}`  
  并重锚 digest。node value 是 `cGFzcw==`，constructed value 是 `b'pass'`，因此既无 `pass-unsupported`，也无 outcome 类型/枚举红；本 session 只读验证结果为 `node_found []` / `constructed {'outcome': b'pass'}`。这仍在 UAT 声称覆盖的 fenced ```yaml / ```yml 与“有效标量写法”面内，不是已声明的非 fence 边界。

## MEDIUM

### M-1：平文 SHA gate 接受 `HEAD` / `main` 这类可变 symbolic ref

- `file:line`：`_bmad-output/审查/evidence-g810/check_g810_refs.py:261-268`、`_bmad-output/审查/evidence-g810/check_g810_refs.py:300-311`
- **问题**：`_ALNUM_TOKEN_RE` 只要求 4–40 位 ASCII 字母数字，随后任何能被 `git rev-parse <t>^{commit}` 解析的 token 都通过；`HEAD` 和 `main` 都满足，但不是 immutable SHA provenance。
- **未被拦下的输入**：把 §2.13 中的 `6337e320` 替换为 `HEAD`（或现存分支名 `main`）并重锚 digest；本 session 对实际 §2.13 做只读等价变换后 `_check_provenance_tokens()` 返回 `failures=[]`，并把当前 HEAD 的 commit/tree 放进 used set。UAT §十.28 只声明“有效 commit 替换由人工裁”，不足以覆盖可变 symbolic ref 被称作 SHA 的情况。

### M-2：无行号 evidence 路径检查是字面 prefix，未先做同根归一化

- `file:line`：`_bmad-output/审查/evidence-g810/check_g810_refs.py:283-299`
- **问题**：只有 `t.startswith("_bmad-output/")` 才进入 `_resolve_under_root()`；语义相同的 `./_bmad-output/...` 或绝对路径不会进入存在性 / 内容绑定检查。
- **门未覆盖的路径**：把 evidence 引用改成不存在的 `` `./_bmad-output/审查/evidence-g2-8-nope-r8/` `` 并重锚 digest；本 session 只读验证 `_check_provenance_tokens()` 对该 token `failures=[]` 且 used set 无该目录文件。它仍在 §2.13 与 `_bmad-output` 证据面内，不属于 §十.26 已声明的产品树散文路径边界。

## LOW

### L-1：develop commit 里的 green runner 在 post-commit 复跑时会取错“旧 checker”

- `file:line`：develop commit `3457f70b` 中 `_bmad-output/审查/evidence-g810/g810-r8-green.zsh:13-19`；当前未入库修复在同文件 `:15-19`
- **问题**：已入库版本用 `git show HEAD:checker` 提取 “v4.5”；当 HEAD 已变成 `3457f70b` 后，取到的是 v4.6，会把 v4.6 标成 prev 并退化成同源对比。
- **对照输入**：`git show 3457f70b:_bmad-output/审查/evidence-g810/g810-r8-green.zsh` 后查看第 13 行；而 `g810-green-r8-20260920T132049.txt:4` 明确写着 checker prev 来自 `dce85102`，说明该 post-commit 证据由当前未入库的 `PREV_REF` 修复版生成。该修复必须随 §九.34 收尾 commit 真正绑定，否则证据生成器与证据不一致。

### L-2：sidecar 的 `code_files` 保留 git quoted/octal escape，不是可直接解析的文件路径

- `file:line`：`_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:47-74`、`_bmad-output/审查/evidence-g810/sidecar-g810-r8-3457f70b.json:23-29`
- **问题**：生成器只 `.strip('"')`，没有解码 `\\345\\256\\...`，所以 manifest 虽有字段和 provenance，但机器消费者不能直接把 `code_files[0]` 当 POSIX path 使用。
- **对照输入**：`Path(sidecar["code_files"][0]).exists()` 为 `False`，而实际 UTF-8 路径 `_bmad-output/审查/evidence-g810/check_g810_refs.py` 存在。数字字段与 bound SHA 本身一致；这是机器可用性残留，不是 JEV 分诊值伪造。

---

# ① 7 项 open finding 的闭合核对

| 原 finding | 判定 | 依据 / 残留 |
|---|---|---|
| ① r7-H1：duplicate key / merge hidden / scalar alias | **指定三形态闭合** | A/B/C pre v4.5 全 rc=0，post v4.6 全 rc=1；A 另有 `yaml-duplicate-key`。PyYAML composer 确会把 alias 解析为同一节点对象，`_scan_node_outcome_pass()` 能看到 merge 源。已知三形态未再穿透；但相邻 `!!binary` 形态为 H-1。 |
| ② r5-M1：nodeid path 归一化 | **闭合** | D 输入 `backend/tests/../app/...::ServiceStatus` post 红 `路径越界（含 .. 段）`；`_resolve_under_root()` 同时拒绝绝对路径、`..`、resolve 后越根。 |
| ③ r5-M2：evidence 目录 / 平文 SHA | **定向闭合，整体声称不闭合** | E1/E2/F1/F2 的指定输入均按日志成立；但 M-1 symbolic ref、M-2 `./_bmad-output` prefix 是同类恒绿面。 |
| ④ r6-M1：owner 独立 token | **闭合** | G 输入中 `G4-3` 只出现在 `CARD-G4-3-验收单.md:1` 文件名内，post `owner-missing` + 实见 `[]`；`_owner_ids()` 对完整 ID / path ref / nodeid 的 token 语义与负控一致。 |
| ⑤ r7-L1：dirty 拆分 | **闭合** | v4.6 输出 `dirty / dirty_tracked / dirty_untracked`；r8 diff 未触碰 r7 evidence 历史文件。 |
| ⑥ r6-L1：sidecar | **字段级基本闭合，机器路径残留 L-2** | calls/verdict/urgency/risk/review/test/code_files/sha/bound_head 与上游 JSON/stdout 对齐；缺字段会非 0 退出；未改上游分诊脚本。但 `code_files` 不是可直接解析路径。 |
| ⑦ 幽灵引用 | **闭合** | two-copy 证据显示权威 feature 副本含 §2.4/§2.4.1–§2.4.3，车道副本停在第十四批；UAT §九.31/§十一.30 的“权威副本 vs 陈旧本地副本”口径自洽。 |

`StrictSafeLoader` 对既存底账未引入假红：canonical v4.6 证据 rc=0，且本 session 在当前 `3457f70b` 只读复跑仍为 `source_digest=e0e912385666e90578b24624a53fdefa / rc=0`。重复显式 key 本身是 invalid YAML，merge key 被有意豁免。

---

# ② 已声明边界判定

| UAT 边界 | 判定 |
|---|---|
| §十.25：非 ```yaml/yml fence、裸 ```/json/缩进块/散文 YAML 不做真解析 | **可接受，不计**；这正是用户本轮明确不要求扩面的边界。 |
| §十.26：provenance 只扫 §2.13 反引号 token，不查其它小节 / UAT / 产品树散文路径 | **原则上可接受**；但 M-2 是 §2.13 内语义相同的 `_bmad-output` 路径，仍需计。 |
| §十.27：`_ALNUM_NON_SHA_ALLOW` 是人工白名单 | **可接受，不计**；死项红、token 封闭，边界清楚。 |
| §十.28：有效 commit 之间的替换由人工裁定 | **对 immutable OID 可接受**；但 M-1 的 `HEAD/main` 是可变 symbolic ref，与“平文 SHA provenance”名实不符，仍需计。 |
| §十.29：r7 历史证据文件不追改，只按 tracked 净读 | **可接受，不计**。 |
| §十.30：nodeid 仍是静态 `def/class` 文法检查 | **可接受，不计**。 |
| §十.31：未合并、未跑集成门、未验证现网 | **可接受且是硬边界**；本轮更不能因 PENDING-R8 宣告合并。 |

---

# ③ r8 证据链自洽性

已独立核对：

- 当前 HEAD = `3457f70bc7b407a2c2e63a86c85c54cee89ac516`，父 = `dce85102d15c37b7bd07b544986f1e4c8e2c13c4`；`dce..3457` 恰 1 个 develop commit，未超出 8 个预授权。
- v4.6 当前文件 SHA = `3fd001741b7c80106684e36c8244ed2bbd9a8c7daf9802062c11419738793faf`，与 commit 内对象一致。
- 底账 SHA = `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`；`4120e0b6..3457` 对底账 diff 为空。
- `4120e0b6..3457 -- . ':(exclude)_bmad-output'` 为空；r8 commit path list 全部在 `_bmad-output/**`。
- negctl：pre 9 例 rc=0；post A/B/C/D/E1/E2/F1/G 红，F2 rc=0 且 digest `a0269b1d… → 67e41faa…`，绑定证明成立。
- regress：r6-A/r6-B/r7-A/r7-B 两相位均红；r7-H1 pre rc=0 → post rc=1。
- anchor battery 8/8 红 + 对照 rc=0；YAML gate 5/5 红 + 对照 rc=0；各 mutation 后 `sha_equal=yes`。
- digest 两段链不矛盾：  
  `v4.5@dce / HEAD=dce = 767bc1af… → v4.6@dce / HEAD=dce = a0269b1d…`；  
  post-commit 则是 “checker 版本取 dce，但 HEAD 已到 3457”：`401019c2… → e0e91238…`。本 session 在当前 HEAD 复跑 v4.6 仍得 `e0e91238… / rc=0`。
- JEV 与 sidecar 的 calls/verdict/urgency/risk/review/test/SHA 相互一致；JEV churn `+262/-17` 与 git numstat 一致。
- UAT 的 PENDING-R8 不是矛盾：当前确实还有未入库收尾面，且本审查已有 HIGH/M/L，不能回填为最终通过。

证据链的惟一复现性残留是 L-1：postcommit green 证据依赖当前未入库的 runner 修复；§九.34 收尾 commit 必须把该修复与证据同绑。

---

# ④ 本轮 0/0/0/0 收口条件

**不满足。**

当前最小反例已给出：

1. HIGH：`outcome: !!binary cGFzcw==` + 重锚 digest → v4.6 绿。
2. MEDIUM：`6337e320` → `HEAD` 或 `main` + 重锚 digest → provenance 绿。
3. MEDIUM：evidence token → `./_bmad-output/审查/evidence-g2-8-nope-r8/` + 重锚 digest → 不做存在性检查。
4. LOW：develop commit 中的 green runner post-commit 取错 prev checker；当前修复尚未入库绑定。
5. LOW：sidecar `code_files[0]` 不是可直接解析路径。

此外，当前工作树仍有收尾 dirty/untracked 文件，最终 closure HEAD、终态 SHA、UAT PENDING 字段均未绑定；即使上述代码问题修复，也仍需按 §九.34 收尾并重跑最终 HEAD 口径后才能进入下一轮 0/0/0/0 判定。
