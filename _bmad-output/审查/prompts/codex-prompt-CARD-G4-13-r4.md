# CARD-G4-13 r4 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`；车道 `card-p9-testinfra`；复核对象 = commit
> `581a8d0a`（父 `116f83c7`）。只读复核，**不改任何文件**。

## ① 背景与最小读取面（⛔ 超出这些文件的证据不能作为结论依据）

背景：上一轮（r3，`codex-review-CARD-G4-13-r3.md`）对 `116f83c7` 给出 **B=0 / H=1 / M=8 / L=8**：
HIGH = block scalar 里的假 `- id:` 可让预检误判通过并静默改写 query 正文；MEDIUM 含 CRLF 全文件行尾重写、
parser 归属边界、`verify_gold_set_file` 跳坏条目、`verify_all` 形状崩、`build` revision 重置、重复键判据空转、
测试缺口等。`581a8d0a` 逐条整改（对照表见 UAT §十），**未开用户裁定窗口**（103 条全 pending）。
金集与 manifest 仍零改动（verify rc=0、四 sha 逐字同）。

最小读取面（只读这些）：
- `git --no-pager diff 116f83c7 581a8d0a -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 155-240 / 242-386 / 388-525 / 527-600 / 597-765 行
- `backend/tests/regression/test_gold_set_manifest_g413.py`（重点：fail-closed 参数化段、r4 新增 5 测试、
  `_pin_env_after_verify` 与对照测试）
- `_bmad-output/审查/codex-review-CARD-G4-13-r3.md`（上一轮全文，作为问题清单）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §十（整改对照 + 证据）
- 证据：`_bmad-output/审查/evidence-g413/r4-*`（含 `r4-m3-probe-assets/`）

## ② 作者自述（逐条独立核对）

1. H-1 关闭：文本层 `- id:` 候选序列必须与解析层 id 序列逐个相符（数量/顺序/值），否则整文件拒绝；
   另有全文档预检不变量（回写后除被点条目三字段外，解析结果逐键一致）；同一 id 出现多次该条不动。
2. 回写改字节级 `read_bytes/decode` + `write_bytes`，CRLF/无尾换行不被重写（`eol` 逐行保留）；
   `_yaml_scalar` 拒绝含真实换行的值。
3. parser：锚必须独占一行才算锚（内嵌不夺权）；勾选必须在「已见匹配标题」的当前条目内；
   `#`/`---` 结束当前条目（补审段勾选不归属）。
4. `verify_gold_set_file`：全部 entries 必须为映射；目标条目 `query_count` 必须为非负 int；
   入参非路径 → `(False, 文案)`；`files: []` → fail-closed。
5. `verify_all`：顶层/`queries`/`config` 形状守卫 → rc=2；`build_manifest`：revision 必须正整数、
   history 必须 list、旧 manifest 读不动/非映射即拒绝（不再把 null 当 0）。
6. 测试：重复键判据加反空转锚；+14（5 fail-closed case / 4 verify_all case / 5 新测试）→ 39 passed；
   M-3 pin 记录 alive 调用，对照断言 `calls == ["alive"]`。
7. 证据：`r4-regression-outside-sandbox-*.txt` = 1952 passed / 6 skipped / 1 xfailed 红 0；
   `r4-m3-mutation-probe-*.txt` + 自包含 `r4-m3-probe-assets/`（变异体 + diff + probe.py）。

## ③ 按重要性排序的问题（逐条回答；答不了就答「无可读证据」）

⓪ H-1 是否真关闭：构造（或说明为什么构造不出）在新的「序列对账 + 全文档不变量 + 重复 id 拒绝」
   之下仍能**静默改写非标注字段**的输入。特别注意：假行恰好复刻 id 序列的极端构造、`splitlines` 与
   `safe_load` 对行尾/换行的处理差异、以及 `ids_in_yaml` 里非字符串 id 的归一化。
① 新 parser 是否引入新的 fail-open 或**误伤**：正常清单（如 `UAT-CARD-G4-13-2026-09-19-裁定清单.md`）
   会不会出现「勾选被忽略/多报 problem」；`##` 标题、`---`、内嵌锚、标题重复等边界还有没有漏洞。
② `verify_gold_set_file` / `verify_all` / `build_manifest` 的 r4 守卫是否完整：还有哪些输入能让
   它们崩、返回 rc=0、或让 runner 走 exit 1（而非 rc=2）？两函数的 bool/rc 语义是否仍可区分。
③ 新测试是否真的覆盖声称分支、且不会误绿（含反空转锚只在有 query 的文件上生效这一收缩是否可接受）？
④ 证据链：r4 探针资产是否足以让第三方复算「pin 承重」的两条结论；目录级 1952 passed 的口径是否
   与 r3 的 1938 可比（+14 是否等于新增收集数）；UAT §十 的对照表有无 overclaim。
⑤ 是否还有 r3 清单里**未真正关闭**的项（逐条点名：H-1 / M×8 / L×8）。

## ④ 输出格式

- 逐条给 **BLOCKER / HIGH / MEDIUM / LOW**（无则写「未发现」），每条：`file:line` + 一句话复现思路。
- 必须有一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」（没有就写「无」）。
- 结尾「本轮总评：B=x / H=y / M=z / L=w」+ 一句 `581a8d0a` 是否达成本次自述目标。

## ⑤ 边界

- 只读；⛔ 不改任何文件；不连 7691/7687/8011；不跑两 runner 非 shadow 模式。
- 不评 G4-14 七指标 / R-SLO schema / L-5（Tier-R top10 盲区，已登记，属判分语义面）。
- 不评 103 条 query 的语义本身，只评工具 / 测试 / 证据链。
