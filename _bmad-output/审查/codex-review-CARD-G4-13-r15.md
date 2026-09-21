# CARD-G4-13 r15 独立复核（只读 · 绑 `f277fdad`，父 `12d61f9a`）

**绑定/方法**：HEAD=`f277fdad05f990847cfe7ab1caac6c68d67e97f9`，工作树仅两条任务前已存在的未跟踪文件（`codex-review-CARD-G4-13-r15.md` 空占位、`prompts/codex-prompt-…r15.md`），我未改任何文件（沙箱外跑完行为门后 `git status --porcelain` 复核仍只有这两条）。r14（`git show 12d61f9a:` 载入）与 r15（盘上）**同进程**载入为两个模块对象，同一批 fixture 直调 `_contains_ok`/`_grade_ok` 与 `verify_gold_set_file()`（IO 打桩，不落盘）；runner 侧只以 AST 取仓库**真函数体**（`norm_text/material_text/grade_of`）→ 无 HTTP/无库/无落盘；四真金集走真 `verify_gold_set_file`（只读）；四 sha 独立 `hashlib` 重算；ruff `--no-cache` 独立复跑；行为门沙箱外实跑一次（`-B -p no:cacheprovider`，82 passed / 2.33s）。未连 7691/7687/8011，未跑任何 runner（含 shadow）；目录级 1995 未重跑（artifact + 算术核对，同 r13 先例）。

## ① r14 三条 LOW 逐条复算（r14 源码 vs r15 源码，同 fixture）

| 项 | 同 fixture 实测 | 判定 |
|---|---|---|
| LOW-1 falsy `contains` | 谓词表：仅 `0`/`0.0`/`-0.0` 由 T→F；`"0"`/`"0.0"`/`"5"`/`5`/`-3`/`2.5`/`10**400`/`.nan`/`.inf` 两版 T；`""`/`" "`/`"\t"`/`"\xa0"`/`"\u3000"`/`False`/`True`/`None`/`[]`/`{}`/`[0]` 两版 F。**端到端**：`contains: 0`、`contains: 0.0` 的 fixture r14=`True`→r15=`False`（detail 点名 expect_hit 形态）。runner 分叉用仓库真 `grade_of` 实证：`contains: 0` → 声明 grade 5（静默跳过），`"0"` → min(grade,2)=2 | **真关闭**（`tool:411-412`，`:552` 使用点） |
| LOW-2 文案名实 | `tool:559` 已改「contains 须真值标量」；`contains: 5`/`"0"` 仍 T、`""` 仍 F —— 与 r14 的真实接受面相符 | **真关闭**；子句级残留见 **LOW-1** |
| LOW-3 证据注记 | `r14-gate-green-…162952` 尾注记已在（"r14 中间态…以同 glob 最新 81 passed 为准"，同 glob `163010` 确为 81 绿）；r15 glob 只有 1 个 gate-green（82），未复发 | **真关闭** |

## ② 放宽/收紧后是否引入新 fail-open / 误拒

- **纯收紧**：r15 只删接受面、不增；`contains` 全形态表见上，无新 fail-open。
- **`grade` 全形态表（30 形）两版逐行相同**（本轮未动）：`0/10/2.0/"2"/"２"/"+5"/" 5 "/"1_0"/"٣"/"-0"/"+10"/"\u30005\u3000"/"\xa05 "` T；`-1/11/2.5/nan/inf/True/False/None/[]/""/"＋5"/"²"/"1e2"/"0x1"` F。与 runner `int()` 接受面一致（我另测 `int(" 5 ")`/`int("\u30005\u3000")`/`int("\xa05 ")`/`int("1_0")`/`int("٣")` 均可解析；`"＋5"/"²"` ValueError 且守卫已拒）。
- **四真金集 8 处 `contains` 全 T**：逐条取类型 = 8/8 `str` 且 truthy（`vq-e01/e06/f04/a01/a02/a03/a05/m02`）；r14/r15 两版 `verify_gold_set_file` 均 True；四份真文件 sha256 独立重算 == manifest == `r15-shas` 逐字（650c5d46…/d88d3a0a…/c7b25fcc…/582df3af…）。**零误拒**。

## ③ 是否还有「守卫 T 但 runner 落 rc=1 或 fail-open」的新路径

**未发现新的**（改动方向只会把输入从 T 移到 F，即落入 rc=2 语义）。承袭面复核：两 runner 的 `verify_gold_set_file` 都先于一切读取（vault `:490` / memory `:359`），最外层 `main()` 把任何 `Exception` 兜成 rc=2（vault `:578-590` / memory `:437-448`），故守卫 T 之后的坏值最多 rc=2、不会冒 rc=1；非-str 真值标量 runner 走 `norm_text→str()`（`run_vault…:115`）⇒ 确定性字面匹配，不崩。

## ④ 新 case 判别力 / 数字自洽

- `contains-zero`（test `:1285-1291`）**真判别**：同 fixture 在 r14 源码下 `ok=True` ⇒ `assert ok is False`（`:1320`）必红；r15 下 `ok=False` 且 detail 真含 `contains`。反向由正控 `:1494-1530`（`contains: 5`）+ 真集 verify（8 处 str contains）共同钉住。
- **gate 独立复跑 82 passed**（2.33s），与 `r15-gate-green…164336` 同；目录级 1995 = r14 1994 + 1，且本 commit 仅动这一个测试文件（`--stat` 逐文件核）⇒ 自洽；named 47 内部自洽（2+35+10）。
- ruff `check` + `format --check` 独立复跑 rc=0（与 `r15-ruff` 同）。

## ⑤ UAT §二十二 / §22.3 诚实性

- §22.1 三行与代码/证据一一对应（上文①逐条实测）。
- §22.2 六行：gate/named/dryrun/shas/ruff 我独立复算一致；目录级 1995 未重跑（artifact 内部自洽 + 算术 + 改动面无第二个测试文件）。
- §22.3：三条内容本身准确、可溯源，但**标题「维持，见 §21.3」名实不符** —— 与 §21.3（`UAT:727-731`）列表不等：丢 `:731`「LOW-5 类证据确定性重放」、增 `:770`「`vault_id:null`」，均无移出/移入注记；且未登记本轮仍活的两条（LOW-1/2）。
- §22.4 三条如实：我独立计数 103 主集（75+28）全 pending；总 105 = 103 主 + 2 shadow，与 dryrun `main=103` 一致。

## 逐条判定

**BLOCKER**：未发现
**HIGH**：未发现
**MEDIUM**：未发现
**LOW-1**：`backend/scripts/gold_set_manifest_tool.py:559` 文案仍省略「且 `str()` 后非空白」子句（`:403-413` 的 docstring 才是全条件）—— `contains: "\u00a0"` 是真值标量却被拒，detail 却说「contains 须真值标量」。复现：同 fixture 直调 verify → `ok=False`，文案与 `:404-408` 自相矛盾；对刚被拒的 `contains: 0`，文案也无「需加引号」的可操作提示。
**LOW-2**：`contains: .nan`（及 `.inf`、超大 int）仍被接受（`tool:411` 只挡 falsy），runner 端按 `str()` 字面匹配 `"nan"`/`"inf"`（`run_vault…:115`、`:132`）⇒ 作者意图大概率落空，但方向为**更严、确定性，非 fail-open**；r14 正文已点名「意图可疑」，r15 未处置也未登记。复现：`_contains_ok(float('nan'))=True`；真 `grade_of` 对无 `"nan"` snippet 返回 min(grade,2)。
**LOW-3**：`_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md:766` 标称「维持，见 §21.3」，实际与 `:727-731` 列表不等（丢 `:731`、增 `:770`）且无注记。复现：diff 两节列表即见。

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

**未被拦下**：`contains: .nan/.inf/10**400`（T，字面匹配，更严）；`contains: "\u200b"`（T，可用）；`vault_id: null`（登记在册，runner `str(None)→"none"`）；`file` 非 str（守卫比 runner 严——runner 会 `str()`，属 r5 起既有契约，非本轮新增）。
**对照输入**：四真金集 r14/r15 双 True + sha 逐字；8 处 `contains` 全 T；`contains: "0"`（真集形态）两版 T 且 runner 维持 `min(grade,2)` 封顶；`contains: 5` 正控 T。
**负控输入**：同 fixture 在 r14 源码下 `contains: 0` → True（新 case 必红，判别力成立）；`contains: ""` 两版 False（旧 case 未失效）；`contains: 0` 的 runner 语义分叉（grade 5 vs 2）用仓库真函数实证，非纸面推断。
**门未覆盖的路径**：`_contains_ok` 无专属单测（只走 case 表）⇒ `0.0`/`-0.0`/`.nan`/`"\xa0"` 无 case；`contains: !!binary`（bytes 在 `:516-519` JSON 门先被拒，contains 分支不可达）无 case；目录级 1995 未重跑；本轮无 immutability artifact（改动面不含 12 个冻结判分函数与四金集，四 sha 我独立重算未变 ⇒ 性质由构造保持）。

**本轮总评：B=0 / H=0 / M=0 / L=3** —— r14 三条 LOW 全部真关闭（falsy `contains` 端到端 r14=True→r15=False 且 runner 分叉实证；文案与接受面名实；证据注记在且未复发）；收尾为纯收紧、四真金集零误拒、gate 82 与目录 1995 自洽、ruff 与四 sha 独立复算一致；新残三低：文案子句省略、`.nan` 类真值标量的语义自由度未处置未登记、「维持」列表名实。
