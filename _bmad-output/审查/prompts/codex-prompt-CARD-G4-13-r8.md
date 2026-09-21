# CARD-G4-13 r8 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`；车道 `card-p9-testinfra`；复核对象 = commit
> `c773e36b`（父 `22c1603a`）。只读复核，**不改任何文件**。

## ① 背景与最小读取面

背景：r7 复核（`codex-review-CARD-G4-13-r7.md`）对 `22c1603a` 给出 **B=0 / H=0 / M=2 / L=8**；
M1 = vgsf 守卫的类型面残余（memory 期望键缺失 / 非 str 元素 / 非有限数值 / 非 JSON 类型 ⇒ runner
exit 1 或 tolerance fail-open）。`c773e36b` 用 manifest 的 `class_key` 做 **kind-aware 类型化守卫**
关闭它们（并对「expect_empty 缺失被误判」做了自查修正）。裁定窗口仍未开（103 条 pending）；
金集与 manifest 零改动（verify rc=0、四 sha 逐字同）。

最小读取面（只读这些）：
- `git --no-pager diff 22c1603a c773e36b -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 430-620（vgsf 内容守卫全段）
- `backend/tests/regression/test_gold_set_manifest_g413.py`（形状 case 参数化段）
- 两个 runner 的实际取值行（只读核对守卫覆盖）：`run_vault_retrieval_regression.py:190-197,214-220,331-345,497` /
  `run_memory_retrieval_regression.py:134-138,148-149,192-199,374`
- `_bmad-output/审查/codex-review-CARD-G4-13-r7.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §十四
- 证据：`_bmad-output/审查/evidence-g413/r8-*`

## ② 作者自述（逐条独立核对）

1. 守卫按 `class_key` 分流：vault 系查 `expect_hit/expect_not_hit/expect_empty` 的形态；memory 系
   查非 `expect_empty` 条目的 `expect_any`（非空 str 列表）；`class_key` 非法即拒。
2. config 类型化：数值键**有限**（禁 bool/nan/inf）；`group_id`/`vault_id` str|null；`version`
   有限数值；`contamination/forbidden/delivery` 映射；`leak_markers` str 列表。
3. 自查修正：`expect_empty` **缺失**不再被误判（原写法会误拒 41 条真实 vault 条目）。
4. 测试 +3 case；gate 54 passed；目录级 1967 passed/6 skipped/1 xfailed 红 0；四 sha/verify 不变。
5. 登记未改：`contamination/forbidden/delivery` 内部键类型（rc=2 不污染 exit 1）、alias 多条目 span、
   非规范写法 fail-closed 误伤面、L-5（Tier-R top10）。

## ③ 按重要性排序的问题（逐条回答；答不了就答「无可读证据」）

⓪ 守卫是否还有「sha 相符但 runner 会 exit 1 / 门禁 fail-open」的残余？请按上面 runner 取值行逐条
   对照（含 `expect_hit` 内部键/`grade` 类型、`not_hit` 的 `max_in_top_k` 边界、`contamination/
   forbidden/delivery` 内部键、`cfg["version"]` 为 int 的 shadow、`group_id` 为空的语义、vault
   `expect_empty` + `expect_not_hit` 并存、memory `leak_markers` 元素大小写/空串等）。能复现就给输入。
① 守卫是否**误拒**真实四金集或未来合法扩展？（新键被忽略、未知条目键、`source`/`user_verdict`
   等标注键的任意形态、`language`/`query_type`/`category` 类型）
② 三个新 case 是否真在目标分支上判别（对照 r7 源码可复算红）；有无空转。
③ 证据链数字自洽（51→54、1964→1967、+3）；UAT §十四 有无 overclaim。
④ r7 清单（M×2 / L×8）逐条点名；`c773e36b` 是否达成本次自述目标。

## ④ 输出格式

- 逐条给 **BLOCKER / HIGH / MEDIUM / LOW**（无则写「未发现」），每条：`file:line` + 一句话复现思路。
- 必须有一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」（没有就写「无」）。
- 结尾「本轮总评：B=x / H=y / M=z / L=w」+ 一句 `c773e36b` 是否达成本次自述目标。

## ⑤ 边界

- 只读；⛔ 不改任何文件；不连 7691/7687/8011；不跑两 runner 非 shadow 模式。
- 不评 G4-14 七指标 / R-SLO schema / L-5（已登记，属判分语义面）；不评 103 条 query 的语义本身。
