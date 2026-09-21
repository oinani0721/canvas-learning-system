# CARD-G4-13 r11 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 复核对象 = commit `191de457`（父 `0b0fc8ac`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

r10 复核对 `0b0fc8ac` 报 **B=0/H=0/M=5/L=6**：M1 守卫自身对大整数抛 OverflowError、M2
`delivery.hard_cap` 显式 null、M3 空串恒真 fail-open、M4 空 `leak_markers`、M5 `expect_hit.grade`
类型；根因是两 runner 的 `main()` 无最外层兜底（漏网异常冒充 exit 1）。`191de457` ①逐条修 M1–M5；
②把两 runner 的 `main` 改名 `_main` 并加**最外层 try/except ⇒ rc=2**（判分函数零改动）。

最小读取面：
- `git --no-pager diff 0b0fc8ac 191de457 -- backend/scripts/gold_set_manifest_tool.py backend/scripts/run_vault_retrieval_regression.py backend/scripts/run_memory_retrieval_regression.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 430-660（vgsf 内容守卫 + `_is_finite_number`）
- 两 runner 的 `_main`/`main` 外壳段（vault 尾部 / memory 尾部）
- `_bmad-output/审查/codex-review-CARD-G4-13-r10.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §十八
- 证据：`_bmad-output/审查/evidence-g413/r11-*`

## ② 核对点

1. M1–M5 逐条复算（r10 源码 vs r11 源码同 fixture），给每条的「r10 结果 → r11 结果」；
2. **rc 契约兜底是否真关掉 exit-1 类**：对 r8/r9/r10 点过的 exit-1 输入（含未修的
   `contamination/forbidden` 内部键、alias 误伤面之外的任何构造）逐一说明现在的落档（应 ≤2，
   不得是未捕获 traceback/exit 1）；同时检查兜底**是否吞掉不该吞的**（例如真正的指标回退 1 档、
   KeyboardInterrupt/SystemExit 行为、以及 `--update-baseline` 写坏一半时 rc=2 的语义是否可接受）；
3. 判分函数/`_main` 主体是否真的零语义改动（除 rename）；
4. 新增 8 个门（6 guard case + 2 兜底测试）是否真在目标分支上判别、无空转；gate 70 / 目录级 1983 自洽；
5. UAT §十八 有无 overclaim；§十六.2 登记项是否仍诚实（逐条点名剩余项）。

## ③ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ④ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
