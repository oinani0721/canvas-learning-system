BLOCKER: 无 / HIGH: 无

## MEDIUM

1. `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:317`、`_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:324-327` — r12 审计证据链仍把最终相位写成 `rc=0`，且两处 `names=36` 与实存审计件不符；`@1db667ba` 实际是 `names=48 tracked=48 missing=0`，`@4c5777d0` 的现存复跑件实际是 `names=66 excluded=2 tracked=63 missing=1`。  
   **对照输入**：并排读 `artifact-audit-r12-20260920T143207.txt:2,52-55` 与 `artifact-audit-r12-20260920T143334.txt:2,70-74`，再对照 UAT §九.49/§九.53 的 `36/rc=0` 声明；当前“收尾后 rc=0”并未由绑定对象证明。

2. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:29-41`、`_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:53-64` — §十三 排除名单实现没有强制“非死项”和“理由非空”，会把所有可解析排除项都从 `tracked` 公式里扣掉。  
   **未被拦下的输入**：加入 `- `real-missing.txt` —` 这类空理由项，或加入一个从未出现在 §九 r8 起名字面的死排除项；脚本仍输出 `SKIP/excluded` 并可 `rc=0`，不会像 checker 的 SHA 白名单那样报 dead-entry。

3. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:88-89`、`_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:104`、`_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:113-120` — `--allow-empty` 的 PARTIAL 判定只看 `files=[]`，没有同时约束 `calls=0`、`code_files=[]` 与“标记人工审查 0/0”，因此 PARTIAL 字段语义可被不一致输入伪装。  
   **未被拦下的输入**：构造 JSON `files=[]` 但 `code_files=["x.py"]`，或 stdout 为 `calls: 5`，再带 `--allow-empty`；脚本仍写 `partial=true`、`partial_reason="0 code files"` 并返回 0。

## LOW

1. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:27-28` — 找不到 `29. **r8 开工自证` 边界标记时会静默退化为扫描整份 UAT，而不是 fail-closed。  
   **负控输入**：从 REF 的 UAT 中改掉或删除该标记后运行；脚本不会报 `marker-missing`，仍按整份文本生成审计面。

2. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:21-22` — UAT 与 tree 分别写入固定 `/tmp/g810r12-*.txt`，并发运行时会发生跨 REF 竞态，削弱 `REF/UAT/tree` 同绑。  
   **对照输入**：对两个不同 REF 同时运行两份脚本；一方可在 Python 读取阶段读到另一方覆盖的 `/tmp` 文件，输出头部的 `ref/uat_blob` 与实际名字面/树面来源分离。

3. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:42` — “全部反引号产物名”的抽取语法只接受字母数字、下划线、点、连字符和中文，不匹配含 `/`、空格、`+`、括号等合法文件名字符的引用名。  
   **门未覆盖的路径**：在 UAT 中引用 ``foo+bar.txt`` 或 ``report (v2).json``；该名字不会进入 `names`，缺件也不会导致 MISS。

4. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:47-49`、`_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:64-65` — 审计输出记录了 REF 与 UAT blob，但不记录 audit runner 自身 blob/sha 或版本号，v2/v2.1/v2.2 的输出头不可区分。  
   **对照输入**：用被改成恒绿的 runner 生成同样格式的输出；仅凭输出文件无法绑定它来自入库的 `g810-r12-artifact-audit.zsh`，需外部复跑或补记 runner blob。

---

# ① r11 六项 + §九.52 闭合判定

| 项 | 判定 | 独立核对结果 |
|---|---|---|
| r11-M1：前缀白名单 | **机制闭合，有残余 M/L** | v2.2 `:42` 确实无前缀过滤；我按各 REF 的 `REF:<UAT>` 复算：`74d58d14=36`、`1db667ba=48`、`2e52f551=64`、`4c5777d0=66`。`check_g810_refs.py`、`g810-r8-sidecar.py`、`card-batch-protocol.md`、`inbox_preview.py` 均进入面内。残余问题见 M-2 与 LOW-3。 |
| r11-M2：名字面与 REF 未同绑 | **顺序运行语义闭合；并发语义有 LOW** | `:20-22` 从 `REF:<UAT>` 与 `REF` tree 取输入，`:48/:65` 输出 `uat_blob`；四个 REF 的 blob 分别复算为 `f2bd35db…`、`5c3a9d1c…`、`a57c13e1…`、`2441b2ec…`。`@74d58d14` 独立复算确为唯一 missing `sidecar-g810-r9-9a22c33b.json`。固定 `/tmp` 并发竞态见 LOW-2。 |
| r11-L1：green 注释默认值 | **闭合** | `g810-r11-green.zsh:3-5` 注释与 `:16` 实际 `PREV=${1:-74d58d14}` 一致。 |
| r11-L2：checker 说明仍写 4–40 | **闭合** | `check_g810_refs.py:317` 是 `^[0-9A-Za-z]+$`，`:328-339` 说明已改为不限长；`2e52f551` 中 checker diff 仅注释/docstring。工作区 sha256 精确等于 `f7c63b3c…f887f`。 |
| r11-L3：r11 prompt stdout 名误写 | **闭合** | `codex-prompt-CARD-G8-10-r11.md:20` 现在引用 `…141639.txt`；实存件与 r11 sidecar `source_stdout` 一致。 |
| r11-L4：不完整负控件 141449 | **闭合** | `git ls-files` 与 worktree 查找均 0 命中；UAT §九.50/§十三 显式说明其为未入库存废件。 |
| §九.52：首跑 3 个不可解名 | **在 `4c5777d0` 绑定点未闭合；仅在未提交工作区疑似修好** | `2e52f551` 的 `143247` 确复现 3 missing。`4c5777d0` 已排除作废件/误写名，但其树内 UAT 仍保留反引号省略名 `...141639.txt`，所以现存复跑 `143334` 仍 `rc=1`。当前 dirty UAT 已把该处全名化；我按当前文本独立复算是 65 个名字、2 个显式排除、0 个非排除 missing，但这还不是 `REF:<UAT>` 的入库复跑证据。 |

当前两条实际 §十三 排除项本身理由成立：`141449` 是已删除且未入库的作废件；`141638` 是明确误写名，实存 `141639`。问题不是这两条当前理由，而是 M-2 所述机制缺少最小性与非空理由硬门。

# ② 恒绿面与声明边界

- **checker v4.9(docfixed)：未发现新的未声明恒绿面。**  
  非 fence YAML、产品树散文路径、其它键名枚举、sidecar 路径存在性等信息面在 UAT §十.36–48 已显式声明；本轮不要求扩面，判定“可接受”。

- **产物审计 basename 判定面：可接受。**  
  “不证路径归属、不证内容哈希、同名任意树内位置可命中”已在 UAT §十.46 声明；`inbox_preview.py` 命中产品树、`card-batch-protocol.md` 命中协议文件都符合该边界，本轮不计。

- **仍需计的未声明面：**
  1. 排除项可为空理由/死项 → M-2；
  2. PARTIAL 只看 `files=[]` → M-3；
  3. 边界标记缺失静默退化 → LOW-1；
  4. 固定 `/tmp` 并发竞态 → LOW-2；
  5. 文件名抽取字符集窄于“全部名字” → LOW-3；
  6. runner 自身不进输出绑定 → LOW-4。

# ③ r12 证据链自洽性

**已独立核实：**

- HEAD 为 `4c5777d065bc947814497f5a96fc7a53113c93c6`；`2e52f551` 父为 `1db667ba`，`4c5777d0` 父为 `2e52f551`，未 amend。
- 两个 commit 的 path 列表全部在 `_bmad-output/` 下。
- `git diff 4120e0b6 HEAD -- . ':(exclude)_bmad-output'` 为空，product code diff = 0。
- 底账在 `4120e0b6`、`1db667ba`、`2e52f551`、`4c5777d0`、HEAD 的 blob sha256 均为 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- doc-only 后负控 27/27 同型，末尾 `verdict_bad=0 f2_binding_bad=0`；锚群 8/8 红 + 对照 `9ff7fa06…` rc=0；YAML 门 5/5 红 + 对照 rc=0。
- digest 两代链成立：`v4.9@1db667ba = 9ff7fa06…`，以及 `prev@74d58d14 = cf06119f… → v4.9@2e52f551 = c2c7bf9e…`，两者 rc=0。
- JEV 主件：`2e52f551` 唯一 code file 为 checker，+3/−2，urgency 2.32 / review 0.64 / risk `test_or_docs` / VERDICT REVIEW；sidecar 与 JSON/stdout 字段一致。
- JEV 补件：`4c5777d0` `calls:0`、`files=[]`、`code_files=[]`；当前 `sidecar-g810-r12b-4c5777d0.json` 记录 `partial:true`、`verdict:null`，没有写“已审”。当前这一件语义正确，但生成器存在 M-3 的伪装输入。

**不自洽处：**

- 审计四相位目前只有前三相已被绑定证据证明：`@74d=rc1/missing r9 sidecar`、`@1db=rc0`、`@2e=rc1/3 missing`。  
- 第四相“收尾后 rc=0”没有绑定证据；现存 `@4c5777d0` 复跑件是 `rc=1`，missing 仍是省略名。
- UAT 对 `@1db` 和补后审计的 `names=36` 声明与实存件不符。
- 当前 dirty 修改包括 audit v2.2 `OUTDIR` 与 sidecar `--allow-empty` 行为变化，但 UAT 的 r12 登记仍主要停在 v2/v2.1，PENDING-R12 尚未回填；这些不能当作已闭合证据。

# ④ 收口判定

**不满足 B/H/M/L = 0/0/0/0。本轮为 B/H/M/L = 0/0/3/4。**

最小反例已经落在上表：

- **M 反例 1**：`4c5777d0` 绑定树内审计仍 `rc=1`，而 UAT §九.53 写 `rc=0`。
- **M 反例 2**：空理由或死排除项仍可进入 §十三 并被 SKIP。
- **M 反例 3**：`files=[] + calls:5` 或 `files=[] + code_files=["x.py"]` 仍可生成 `partial=true` 且 rc=0。
- **L 反例**：边界标记缺失、并发 `/tmp` 覆盖、`foo+bar.txt` 不入抽取面、runner 版本不可从输出自证。

因此本轮不应释放合并门。最小收口路径不是改底账或产品代码，而是：先修正/登记上述工具与 UAT 数值，完成 `_bmad-output`-only 收尾 commit，再在该最终对象上重跑 checker digest 与产物审计，并由下一轮把最终 HEAD、runner/UAT blob、audit rc=0 和 sidecar PARTIAL 口径同绑复核。

# ⑤ 其它

无 BLOCKER/HIGH 级问题；也未发现 r12 越出 `_bmad-output`、触碰底账或产品代码。当前工作区的 tracked/untracked 变更均在 `_bmad-output/**`，符合“收尾件待做”的状态。
