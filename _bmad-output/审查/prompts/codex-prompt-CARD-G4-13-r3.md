# CARD-G4-13 r3 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`；车道 `card-p9-testinfra`；复核对象 = commit
> `116f83c7`（父 `3d0ad468`）。只读复核，**不改任何文件**。

## ① 背景与最小读取面（⛔ 超出这些文件的证据不能作为结论依据）

背景：CARD-G4-13 的「真人 gold set 用户裁定」窗口未开（103 条全 `pending`）。等待期间做了
准备性加固 commit `116f83c7`：把「用户勾选 → 回写金集 yaml」路径上的已知债（M-1 归错条目 /
M-2 抹注释+全文 churn / L-1 静默漏），以及 r2 复核留下的 M-R2a/M-R2b 与若干 L 项修成
fail-closed + 最小 churn。金集与 manifest **零改动**（sha 逐字同、verify rc=0）。

最小读取面（只读这些）：
- `git --no-pager diff 3d0ad468 116f83c7 -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 71-83 / 154-226 / 228-341 / 358-410 / 489-651 行
- `backend/tests/regression/test_gold_set_manifest_g413.py`（重点 170-217 / 325-570 / 594-750 行）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §九（作者自述 + 证据清单）
- 债务来源：`_bmad-output/审查/zcode-review-CARD-G4-13-r1.md`（M-1/M-2/M-3/L-1~L-6）、
  `_bmad-output/审查/codex-review-CARD-G4-13-r2.md`（M-R2a/M-R2b/L-R2a~c）
- 证据：`_bmad-output/审查/evidence-g413/r3-*.txt`

## ② 作者自述（逐条独立核对，别信自述）

1. M-1：`_parse_checklist_picks` 用「隐藏锚 × 可见标题行」交叉核对；锚被删/被改 ⇒ 不归属 +
   problems + 不写字节（旧实现记为最近锚 = 上一条）。
2. M-2：`_apply_verdict_edits` 只逐行改 3 个标注字段行、其余字节原样；落盘前内存读回预检；
   预检失败 ⇒ 该条放弃/整批放弃，不写半个文件。
3. L-1：大写 `[X]` 可识别；勾选行无 verdict 锚 ⇒ problems（不再静默 continue）。
4. M-R2a/M-R2b：`verify_gold_set_file` 扩 OSError/UnicodeDecodeError 族与 `files` 非列表 →
   `(False, 文案)`；`verify_all` 同族归 rc=2。
5. L-3：`collect_candidates` 拒绝 `--out` 落在 `--vault` 内（CLI rc=2）。
6. L-6：`verify_all` 复核 totals 与 adjudication（approved ⇒ 签名必填）；`build_manifest` 对任何
   已存在 manifest 要求 `--bump-revision`（revision 单调、history 不丢）。
7. M-3：`_pin_env_after_verify` 钉 memory alive→False / vault run_tiers→记录器；变异探针证明 pin
   承重（把校验挪后 ⇒ 测试红）。
8. 测试层：fail-closed 按 case 参数化（L-R2b）；重复键判据按 query 块 + 容忍引号键（L-2）；
   删死代码（L-4）；「在仓外」负断言收窄（L-R2c）。
9. 「金集零改动」= verify rc=0 + 四 sha 与 manifest 逐字同 + 83 条×10 键 diffs=0 + 12 判分函数
   AST same=True。

## ③ 按重要性排序的问题（逐条回答；答不了就答「无可读证据」）

⓪ `_apply_verdict_edits` 在任何输入下是否可能写出「半个条目」或破坏文件？重点：`ITEM_ID_LINE_RE`
   把非条目行当条目（字符串值里出现 `- id:`）、同 id 重复、块跨文件尾、CRLF/无尾换行、字段行
   重复/缺失、预检失败回退是否真的零写。
① `_parse_checklist_picks` 是否还有「错误归属」输入（标题重复、锚在标题后、勾选夹在两锚之间、
   补审段混排）？与旧实现比有没有新的 fail-open 方向？
② `verify_gold_set_file` / `verify_all` 的新分支是否还有逃逸输入（entries 非 dict、path 非 str、
   sha 非 str、files 为 dict、空/只读 manifest）？bool vs rc 的语义差在文案上可区分吗？
③ `build_manifest` 单调 revision：manifest 不存在时带 `--bump-revision` / revision 非法 / history
   非 list 的行为是否 fail-closed？会不会堵死正常「首次生成」路径？
④ 新增/改写测试是否真的测到声称分支（r1 H-2 死补丁教训）？有没有断言可在**不触发目标分支**时
   照样通过？尤其 anchor-loss、两个 env pin、7 个 fail-closed case、roundtrip「恰 3 行变化」。
⑤ 证据面：`r3-gate-red` 的 7 条失败是否都红在指定断言？`r3-m3-mutation-probe-131448` 的变异体 +
   对照是否足以证明 pin 承重？「沙箱内 6 红 = /bin/ps EPERM 伪影」的判定链是否成立？

## ④ 输出格式

- 逐条给 **BLOCKER / HIGH / MEDIUM / LOW**（无则写「未发现」），每条：`file:line` + 一句话复现思路。
- 必须有一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」（没有就写「无」）。
- 结尾「本轮总评：B=x / H=y / M=z / L=w」+ 一句本 commit 是否达成本次自述目标。

## ⑤ 边界

- 只读；⛔ 不改任何文件；不连 7691/7687/8011；不跑两 runner 非 shadow 模式。
- 不评 G4-14 七指标 / R-SLO schema / L-5（Tier-R top10 盲区，已登记，属判分语义面）。
- 不评 103 条 query 的语义本身，只评工具 / 测试 / 证据链。
