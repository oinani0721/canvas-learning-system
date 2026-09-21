只读复核完成：未改文件、未连数据库/网络服务。网络对齐只核了本地 `origin/backup` tracking refs（均为 `a6303136866d2e0dc764dc0e15e8a6a8e0727ccf`），活态 `ls-remote` 结论采用你提供的 transcript。当前 tracked dirty = 0。

## BLOCKER

无。

我不把 P3 lane 在终审期间推进到 `1726b695` 本身计作 B15 未闭合：只读复算 `34c29691..1726b695` 全部改动均在 `_bmad-output/**`，且 `32a405a4..1726b695` 排除 `_bmad-output` 后 diff 为空；主干 G8-7 仍是 signoff pending / 非 pass。该面已被 `b15-freeze-exclusions.json:5-16` 显式切到第十六批，B-1 的“当前冻结事实”成立。另在最终 HEAD 只读复跑 G8-10 checker：actual digest `aa2428f6db8bd60cd2e1692a3522fd27`，回填后 `chains=6 obj07=5 failures=0 rc=0`，且 `dirty_tracked=0`。

## HIGH

### H-1 semantic v2.2 仍未完全 fail-closed：`empty_n > 0` 可以 PASS，r5-H1 的明确验伪输入未被拦下

- 位置：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:127-140,149-152`；对照要求见 `_bmad-output/审查/codex-review-B15-CLOSEOUT-r5.md:38-42`。
- 复现思路：
  1. `blob_checked()` 只证明路径存在；随后 `:132-135` 对空 blob 仅递增 `empty_n` 并打印 `[EMPTY]`，不 append `failures`。
  2. 若两侧同为一个零字节 blob，`equiv()` 在 `:68-70` 先因 `a == b` 返回 `BYTES`，最终仍可 PASS。
  3. 更严重的是任一声明例外路径（`:21-28`）一侧为空、另一侧非空时，`equiv=None` 会落入 `:138-140` 的 exception 分支，只计入 `exc_n`；最终 `clean` (`:149-152`) 不检查 `empty_n`，仍可 `failures=0 / verdict=PASS / rc=0`。
- 未被拦下的输入：同一比较文件两侧同为零字节；或 `neo4j_client.py` 等六个 exception 路径一侧零字节、另一侧非空。
- 对照输入：当前档 `_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2-v22-20260920T211104.txt:19-20` 实际 `empty=0`，所以本次结果本身不是空 blob 假绿。
- 负控输入：把一个 enumeration 内文件替换为零字节 blob；当前负控档只覆盖坏 BASE 与 code drift，没有 empty-blob 负控。
- 门未覆盖的路径：`empty_n` 未进入 failures/clean；exception 优先级可吞掉 empty mismatch；r5 复核明确要求 `empty_n` 非零时 `sys.exit(1)`，v2.2 未实现。

## MEDIUM

### M-1 “仅 P3 docs-only 可容忍”的冻结口径没有机器化限定，semantic guard 实际容忍所有 lane 的 docs-only 漂移

- 位置：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:30-38,113-125`；声称口径见 `_bmad-output/审查/evidence-b15-closeout/b15-freeze-exclusions.json:15` 与 `_bmad-output/审查/evidence-b15-closeout/STATUS.md:18`。
- 复现思路：脚本只在注释里提到 P3 排除，运行时从不解析 `b15-freeze-exclusions.json`；每 lane 仅计算 `pin..HEAD` 排除 `_bmad-output` 后的 code drift，不要求 tip 等于 pin，也不区分 P3 与其他 lane。给 p1 增加一个 docs-only commit 后，`tip` 变化但 `code_drift=0`、非 `_bmad-output` 文件清单不变，仍可 PASS。
- 未被拦下的输入：p1/p2/p4–p10 任一未登记排除 lane 在冻结后推进 `_bmad-output/**` 证据面。
- 对照输入：本轮只读实测 p1/p2/p4–p10 tip 均等于 `CODE_TIPS` pin，只有 P3 从 `32a405a4` docs-only 前进到 `1726b695`，因此当前没有实际漂移。
- 负控输入：人为给 p1 增加 `_bmad-output` commit，或删掉/漏配某 lane 的 `CODE_TIPS` 键；当前 v2.2 不会因 tip漂移红，`pin=""` 时还会直接跳过 drift 检查。
- 门未覆盖的路径：P3-only allowlist 解析、未排除 lane 的 exact-tip pin、`CODE_TIPS` 缺键 fail-closed。

## LOW

### L-1 两个负控 helper 只留下摘录 transcript，声称执行的脚本本体/全文输出未入库

- 位置：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2-v22-negcontrols-20260920T211104.txt:3-16,18-24`；最终树 `a6303136866d2e0dc764dc0e15e8a6a8e0727ccf` 中没有 `v22-neg-badbase.py` 或 `v22-neg-drift.py`。
- 复现思路：负控档命令行引用上述两个脚本名，但 `git ls-tree -r a6303136` 只能找到主脚本与结果档；坏 BASE 段还在 `:11` 用 `...` 省略中间失败输出，只保留 `failures=21` 汇总。
- 未被拦下的输入：负控脚本与正式 v2.2 的实际差异、执行时脚本 hash、被省略的 21 条 failure 全文均无法从最终树逐字节复算。
- 对照输入：主脚本 `cross-lane-semantic2.py` 已入库，坏 BASE 与 code drift 的失败机理可静态推导；当前 transcript 的 `rc=1` 汇总与代码路径相符。
- 负控输入：归档两个 one-line mutation 脚本或完整 stdout+脚本 SHA，再验证不可复现。
- 门未覆盖的路径：负控 artifact 的 source provenance / 完整 stdout 绑定。

### L-2 `b15-freeze-exclusions.json:3` 对最终代码面注释delta的归属写漏 r4-L1

- 位置：`_bmad-output/审查/evidence-b15-closeout/b15-freeze-exclusions.json:3`；准确口径已在 `_bmad-output/审查/evidence-b15-closeout/STATUS.md:19`。
- 复现思路：JSON 写“自 `1e907037` 起……除 r5-L1 注释勘误外零变更”，但 `1e907037..a6303136` 的最终注释 delta 实际包含两级：r4 的 `89→90 / 93→94 GET` 与 r5 的 `206/117→211/121`。我重算该文件父子 AST 完全相等，行为确为零变更，但登记归属不完整。
- 未被拦下的输入：读者按 freeze JSON 认为 `89→90 / 93→94` 不属于最终代码面 delta。
- 对照输入：`STATUS.md:19` 明确写“r4/r5 两轮整改累计”，与 git diff/AST 复算一致。
- 负控输入：把 freeze JSON 的说明改成“r4-L1 + r5-L1 注释-only累计”，再与 `git diff 1e907037..a6303136 -- backend/tests/contract/test_openapi_contract.py` 对账。
- 门未覆盖的路径：freeze JSON 与 STATUS/git 累计 delta 的机器一致性检查。

其他关键复算均与声称相符：openapi 为 `211 ops = GET94/POST100/DELETE9/PUT6/PATCH2`，选中 90、未选 121；`1e907037..a6303136` 非 `_bmad-output` 仅 contract 注释且 AST 相等；unit 33→32 且 canonical nodeid 差集仅 `test_digest_is_injective_over_adversarial_leaves`；contract 三个档红 nodeid 集合相同；7692 四文件 107 passed；D40 为 480 `.py` + OpenAPI timestamp；G8-10/协议/R-SLO/集成修复/P9/G4-13/P3 冻结登记与 git 对象核对一致；35 tag 分解与本地对象一致。

清零：否；B/H/M/L = 0/1/1/2
