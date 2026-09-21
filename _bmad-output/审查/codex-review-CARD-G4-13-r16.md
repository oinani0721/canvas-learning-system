# CARD-G4-13 r16 独立复核（只读 · 绑 `f989d0fe`，父 `f277fdad` ✓）

**绑定/方法**：HEAD=`f989d0fe`（父实签 `f277fdad` ✓），工作树前后仅两条 r16 复习占位未跟踪文件（r16 复核单 + prompt），我未改任何文件。未连 7691/7687/8011，未跑任何 runner（含 shadow）。独立复跑/重算：行为门沙箱外实跑一次（**82 passed / 2.26s**，与 `r16-gate-green-…165606` 同）；`verify` CLI rc=0；四 sha 全 64 位独立重算 == manifest 逐字；同 fixture 下 **f277fdad 源码模块 vs 工作树源码模块同进程对跑** `_contains_ok`/`verify_gold_set_file`（在内存、不落盘、IO 打桩）；`ruff --no-cache check/format --check` rc=0（0.15.9）；`vault_id:null` 链在真实 app 模块内实测。目录级 1995 未重跑（artifact + 算术 + 改动面核，同 r15 先例）。

## ① r15 三条 LOW 逐条复算

| r15 项 | 同 fixture 实测 | 判定 |
|---|---|---|
| LOW-1 文案子句/提示 | `tool:561-563` 现含「str() 后非空白、非 nan/inf（数字请加引号）」；fixture `contains: .nan`/`0`/`" "` 端到端 detail 逐字为补全后文案 | **真关闭**（bool 残角另报见 LOW-2） |
| LOW-2 `nan/inf` 未处置未登记 | `tool:411-412` 拒非有限浮点；双源码对跑：`.nan`/`.inf`/`-.inf` r15=`True`→r16=`False`；`§22.3 UAT:772` 已登记 | **真关闭**（超大 int 仍 T，见下文段落） |
| LOW-3 §22.3 名实 | 标题已改「完整列表」、列表已扩（`UAT:770-772` 增 vault_id:null / max_in_top_k / nan/inf），但 **:731「LOW-5 类证据确定性重放」仍未纳入且无移出注记**，§21.3 仍标「维持」 | **部分关闭 → LOW-1（本轮）** |

## ② 是否还有 M 级及以上新路径

**未发现**。diff 仅两处 hunk 且方向为纯收紧（只从接受面删项，不加项）：剩余被收形状 = 真值标量经 `str()` 非空白且非 nan/inf，runner 端一律 `norm_text→str()` 字面匹配（`run_vault…:115-118`、`:132`）⇒ 确定性、不崩；`math` 已在 `:31` 导入；最外层 `main()` rc=2 兜底未变。`contains: true` 被拒（`:409`）属 fail-closed，仅文字面问题（LOW-2），非 rc=1/fail-open 路径。

**2b. 四真金集**：`verify_gold_set_file` 直调四份全 `True`、`verify` rc=0；8 处 `contains` 全在 vault 主集（vq-e01/e06/f04/a01/a02/a03/a05/m02），逐条 `str` 且 `_contains_ok=True`；memory 两集无 `contains` 键。**零误拒**。四 sha 全 64 位 == manifest（`:15/:38/:59/:73`，650c5d46…/d88d3a0a…/c7b25fcc…/582df3af…），自 r15 未动。

## ③ gate 82 / 目录级 / 四 sha / verify

gate **82 passed** 独立复跑与 artifact 一致（无新 case 属实：commit 未动测试文件）；目录级 artifact 尾行 `1995 passed, 6 skipped, 1 xfailed` 与算术自洽（r14 1994 + r15 case 1；仓库内唯一 import 该工具的测试模块即 gate 文件）；verify rc=0、四 sha 如上。唯 §23.1「verify / 四 sha」行无独立 r16 artifact（evidence 目录仅 gate-green/regression 两件），但该不变量由 gate 内 `test_manifest_sha_matches_independently_computed` + `test_tool_verify_returns_zero_on_repo_files` 承载，我已独立重算 → 记入覆盖段，不单列 LOW。

## ④ §22.3 残余登记诚实性

四要件均在 `UAT:768-771`：LOW-4（维持登记）；**L-5**：runner `:303-311` 确只数 `top10`，登记属实；**`vault_id:null`**：tool `:614-616` 放行 null，实测 `build_vault_group_id(sanitize_vault_id(str(None)))` == `"vault:none"`，登记属实；**`max_in_top_k` 注解自由度**：tool `:572-576` 收 [0,10⁶]，runner `:303` `int()` + top10 计数 ⇒ [10,10⁶] 行为等价，属实。**完整性不达标**：见 LOW-1。

## 逐条判定

**BLOCKER**：未发现
**HIGH**：未发现
**MEDIUM**：未发现
**LOW-1**：`_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md:766` 自述「完整列表」，但相对 `:727-731`（§21.3「维持」）仍丢 `:731`「LOW-5 类证据确定性重放」且无移出/移入注记 —— r15 LOW-3 收尾只换标题未对账。复现：diff 两节列表即见（:766-772 无该项）。
**LOW-2**：`backend/scripts/gold_set_manifest_tool.py` 文字面与接受面残角两处 —— ①`:404-406` docstring「可接受形态=真值标量且 str() 后非空白」未含 nan/inf 拒收（只落在 `:412` 行内注释；r15 曾以 docstring 为「全条件」参照）；②`contains: true` 被 `:409` 拒，而 `:562` 文案与 `:404` docstring 均写「须真值标量」（true 即真值标量）⇒ 文案对该输入反暗示可收。复现：同 fixture `contains: true` → `(False, 文案含「真值标量」)`。

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

**未被拦下**：`contains: 10**400`（有限 int→T，字面匹配、确定性；r15 点名的「超大 int」既未拒也未单列登记）；`contains: "\u200b"`（T）；`contains: 1e400` 裸写实为 YAML 字符串（按字面接受）；`vault_id: null`（登记在册，实测落 `vault:none`）；memory 集内若出现 `contains` 既无消费者也不过新守卫（无影响）。
**对照输入**：四真金集 True×4 + 8 处 contains 全 T + sha 逐字；`contains: 5`/`"0"` 两版 T（无误拒）；`contains: "nan"`（字符串）T —— 合法字面用法保留。
**负控输入**：同 fixture 在 `f277fdad` 源码模块下 `.nan/.inf/-.inf` → True，工作树 → False（新行判别力实证）；`contains: 0`/`" "` 两版 F（r15 修复未回退）。
**门未覆盖的路径**：新守卫无 case 钉住 —— 删除 `tool:411-412` 后 gate 仍 82 绿（nan/inf 无 case，`0.0`/`-0.0`/`"\xa0"` 沿用 r15 注记）；目录级 1995 未重跑；§23.1「verify/四 sha」行无独立 artifact（由 gate 内两测试 + 本轮独立重算承载）。

**本轮总评：B=0 / H=0 / M=0 / L=2** —— r15 LOW-1/2 真关闭（文案补全逐字复现、nan/inf 双源码 True→False 实证且已登记）、四真金集零误拒、gate 82 与目录级 1995 自洽、四 sha 与 verify 独立复算一致、ruff 绿；新残两条皆文档级：§22.3「完整列表」仍缺 §21.3:731 项（r15 LOW-3 部分关闭），以及 `_contains_ok` 文字面（docstring 未同步 nan/inf；bool 拒收在文案反暗示可收）。**无 M 及以上；按 §22.3 登记路径可收口，建议两条 LOW 一句话级补注后关闭。**


