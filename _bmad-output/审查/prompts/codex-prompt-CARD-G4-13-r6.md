# CARD-G4-13 r6 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`；车道 `card-p9-testinfra`；复核对象 = commit
> `cb0997ff`（父 `691b1d3e`）。只读复核，**不改任何文件**。

## ① 背景与最小读取面

背景：r5 复核（`codex-review-CARD-G4-13-r5.md`）对 `691b1d3e` 给出 **B=0 / H=1 / M=2 / L=3**：
H = 文本层对账（值序列 + 结构重解析）仍可被「被覆盖的同级 block scalar 放伪条目 + 真条目引号化」
骗过。`cb0997ff` 的应对是**放弃文本启发式**：`apply-verdicts` 的条目与标注字段位置全部改由
**PyYAML 节点树（`yaml.compose`）的行号 marks** 决定（见 UAT §十二）。裁定窗口仍未开（103 条
pending）；金集与 manifest 零改动（verify rc=0、四 sha 逐字同）。

最小读取面（只读这些）：
- `git --no-pager diff 691b1d3e cb0997ff -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 397-545（verify_gold_set_file）/ 617-800（节点树版 _apply_verdict_edits 与 apply_verdicts）/ 其它 r6 触及段
- `backend/tests/regression/test_gold_set_manifest_g413.py`（r6 三个新测试 + 参数化形状 case）
- `_bmad-output/审查/codex-review-CARD-G4-13-r5.md`（上一轮全文 = 问题清单）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §十二（整改对照 + 证据）
- 证据：`_bmad-output/审查/evidence-g413/r6-*`

## ② 作者自述（逐条独立核对）

1. H 类关闭：条目定位 = `queries` 序列节点的映射子节点（`start_mark.line` 定区间）；标注键定位 =
   该映射里名为 `user_verdict`/`verdict_by`/`verdict_at` 的**键节点**行号。字符串/block scalar/
   被覆盖键里的 `- id:` 行**结构上不可能**成为候选；重复键/值跨行/键行非规范 ⇒ 拒绝。
2. 文本启发式零残留：唯一正则 `VERDICT_LINE_RE` 只用于校验键行是规范单行形态（不匹配 ⇒ 拒绝，不猜）。
3. `verify_gold_set_file` 内容守卫加严：`config` 必须映射；每条目必须有 `id` 且 `query` 为字符串；
   `len(qs)` 必须等于 manifest `query_count`。
4. 测试：decoy 受害构造（r5 源码实跑证明会红：`changed=['q2'] bytes_changed=True`，见
   `r6-decoy-red-on-r5-*.txt`）+ 预检分支 + 重复标注键 + 3 个形状 case；gate 46 passed。
5. 证据：`r6-regression-outside-sandbox-*.txt` = 1959 passed / 6 skipped / 1 xfailed 红 0；
   `r6-named`/`r6-immutability`/`r6-dryrun`/`r6-verify`/`r6-shas` 全绿。

## ③ 按重要性排序的问题（逐条回答；答不了就答「无可读证据」）

⓪ 节点树定位是否真关闭 H 类：能否构造「结构上仍让写入落在非目标区域」的输入？请特别考虑：
   同一文件多个 `queries` 键（顶层重复键）、`queries` 为 alias/merge（`<<`）、条目用 merge key
   或 alias 引入标注键、键节点与值节点行号在 flow 形态下的关系、条目里标注键多写（重复）时的
   `end_mark`、以及 `yaml.compose` 与 `yaml.safe_load` 对同一文档的理解差异。
① 内容守卫是否还有「sha 相符但不可跑」的残余（例：query 是空串、id 为 None、`config` 是 dict 但
   runner 仍 KeyError 的其它键路径）？两个 runner 的实际取值行（vault `:217-218`、memory `:148-149`）
   本轮允许列入读取面以核对该面。
② 新代码有无新崩点/误伤：`yaml.compose` 的异常面、`items` 构造对缺 `id` 值节点的处理、
   `_node_key_lines` 在 alias 键下的行为、以及正常四金集/真 103 条清单的兼容性。
③ 测试真实性：decoy 测试是否真在 r5 上红（可对 `git show 691b1d3e:` 复算）；预检/重复键测试是否
   真触发目标分支；有没有断言可在不触发目标分支时照样通过。
④ 证据链：数字自洽（gate 44→46、目录级 1957→1959、+2 与新增测试数一致）；UAT §十二 有无 overclaim；
   `r6-decoy-red-on-r5-*.txt` 是否足以支撑「真先红」。
⑤ r5 清单（H×1 / M×2 / L×3）逐条点名闭合。

## ④ 输出格式

- 逐条给 **BLOCKER / HIGH / MEDIUM / LOW**（无则写「未发现」），每条：`file:line` + 一句话复现思路。
- 必须有一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」（没有就写「无」）。
- 结尾「本轮总评：B=x / H=y / M=z / L=w」+ 一句 `cb0997ff` 是否达成本次自述目标。

## ⑤ 边界

- 只读；⛔ 不改任何文件；不连 7691/7687/8011；不跑两 runner 非 shadow 模式。
- 不评 G4-14 七指标 / R-SLO schema / L-5（Tier-R top10 盲区，已登记，属判分语义面）。
- 不评 103 条 query 的语义本身，只评工具 / 测试 / 证据链。
