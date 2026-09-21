# CARD-G4-13 r5 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`；车道 `card-p9-testinfra`；复核对象 = commit
> `691b1d3e`（父 `581a8d0a`）。只读复核，**不改任何文件**。

## ① 背景与最小读取面（⛔ 超出这些文件的证据不能作为结论依据）

背景：r4 复核（`codex-review-CARD-G4-13-r4.md`）对 `581a8d0a` 给出 **B=0 / H=1 / M=2 / L=4**：
残余 HIGH = 文本层「值序列对账」缺**结构对齐**维度（隐藏真条目 + 丢弃区块内假行可把写入落进
block scalar 正文）；MEDIUM = `verify_all` 条目级崩溃 / 关键机制无测试；LOW ×4。
`691b1d3e` 逐条整改（对照表见 UAT §十一）。**用户裁定窗口仍未开**（103 条全 pending）；
金集与 manifest 零改动（verify rc=0、四 sha 逐字同）。

最小读取面（只读这些）：
- `git --no-pager diff 581a8d0a 691b1d3e -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 155-242 / 244-395 / 397-545 / 547-620 / 617-758 / 746-790 行
- `backend/tests/regression/test_gold_set_manifest_g413.py`（重点：r5 新增 3 测试 + 2 个 verify_all case）
- `_bmad-output/审查/codex-review-CARD-G4-13-r4.md`（上一轮全文 = 问题清单）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §十一（整改对照 + 证据）
- 证据：`_bmad-output/审查/evidence-g413/r5-*`

## ② 作者自述（逐条独立核对）

1. H 关闭：`_apply_verdict_edits` 现对每个候选段落做**结构对账** —— 段落单独按 ``queries:`` 解析
   必须与整文档**同序条目逐键相同**，否则整文件拒绝（另有值序列对账 + 全文档不变量 + 重复 id 拒绝）。
2. `verify_all` 增条目级守卫（`queries` 含非映射 ⇒ rc=2）；`verify_gold_set_file` 增**内容形状守卫**
   （顶层映射 / ``queries`` 映射列表 ⇒ 否则 `(False, 文案)`）。
3. `apply_verdicts` 走 `_load_queries_strict`（读不动/非映射/坏形状 ⇒ problem，不崩）；parser 标题
   边界收窄为 `^#{1,6}\s`；`verify_all` 入参类型守卫。
4. `build_manifest`：`revision_history` 为 nil/falsy 非 list 都不再绕过（is None 判空 + isinstance 拒绝）。
5. 测试：受害构造（`test_apply_verdicts_structural_alignment_blocks_hidden_fake_item`，先红后绿）、
   无尾换行、内容形状、2 个 verify_all case ⇒ 先红 3 failed / 后绿 44 passed。
6. 证据：`r5-regression-outside-sandbox-*.txt` = 1957 passed / 6 skipped / 1 xfailed 红 0；
   `r5-immutability`/`r5-named`/`r5-dryrun` 全绿。

## ③ 按重要性排序的问题（逐条回答；答不了就答「无可读证据」）

⓪ 残余 H 是否真关闭：能否构造「结构对账通过但写入仍落在非条目区域」的输入？请特别考虑：
   段落单独解析与整文档解析在别名/锚（`&a`/`*a`）、行内 flow 条目、`queries:` 后仍属列表但
   含多文档标记、条目中含重复键（同键两写）等情形下的**等价性**；以及整文档条目数与候选数相等
   但**顺序错位**时结构对账会不会漏（例：交换两个条目的位置）。
① 内容形状守卫是否完整：还有哪些「sha 相符但内容不可跑」的输入能让 runner 走 exit 1？
   （例：``queries`` 是 dict、条目是空 dict、`id` 非字符串、顶层键缺 `config`…）
② 新代码有无新崩点或误伤：`_load_queries_strict` 的 except 面；结构对账对**合法但非规范**写法的
   拒绝面是否会误伤用户裁定当日（清单一侧不受影响？金集一侧是当前四份固定文件）；
   标题边界收窄后正常清单是否仍逐条归属。
③ 测试真实性：受害构造是否真的会红在旧代码（可对 `git show 581a8d0a:` 源码内存复算）；有没有
   断言可在不触发目标分支时照样通过；反空转锚是否仍有效。
④ 证据链：`r5-gate-red` 的 3 条失败是否各红在指定断言；1957/6/1 与 r4 的 1952 差 +5 是否自洽；
   UAT §十一 对照表有无 overclaim。
⑤ r4 清单（H×1 / M×2 / L×4）逐条点名：是否真关闭；未关闭的列残余面。

## ④ 输出格式

- 逐条给 **BLOCKER / HIGH / MEDIUM / LOW**（无则写「未发现」），每条：`file:line` + 一句话复现思路。
- 必须有一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」（没有就写「无」）。
- 结尾「本轮总评：B=x / H=y / M=z / L=w」+ 一句 `691b1d3e` 是否达成本次自述目标。

## ⑤ 边界

- 只读；⛔ 不改任何文件；不连 7691/7687/8011；不跑两 runner 非 shadow 模式。
- 不评 G4-14 七指标 / R-SLO schema / L-5（Tier-R top10 盲区，已登记，属判分语义面）。
- 不评 103 条 query 的语义本身，只评工具 / 测试 / 证据链。
