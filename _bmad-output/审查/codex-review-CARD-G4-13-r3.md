> **存档首部（协议 §2.4.1；字段抄自 `.stderr`，行号在括注里）**
> - 模型：`deepseek-v4.1-flash`（goal 指定「开发/证据整理」裁判；profile `opencode-go`）—— `.stderr:5`
> - reasoning_effort：`max` —— `.stderr:9`
> - codex：`OpenAI Codex v0.153.3` —— `.stderr:2`
> - 附加自证：`provider: opencode-go`（`.stderr:6`）· `sandbox: read-only`（`:8`）·
>   `session id: 01a0c086-d7e2-7950-93a7-0f62ef2192c3`（`:11`）
> - 送审命令：`codex -p opencode-go exec --sandbox read-only "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G4-13-r3.md)"`
>   （rc=0；stdout > `.md`、日志 > `.stderr`（gitignore，不入库）；绑定 `116f83c7`）
> - 结论：**B=0 / H=1 / M=8 / L=8** —— r4 整改见 `UAT-CARD-G4-13-2026-09-19.md` §十

---

# CARD-G4-13 r3 独立复核（只读）

**绑定核验**：HEAD = `116f83c7`，父 = `3d0ad468`；diff 面只有 `gold_set_manifest_tool.py` + 该测试 + UAT/evidence，未碰四份金集与 manifest。只读复算 `verify_all(MANIFEST) = rc 0`，四个 sha 与 manifest 逐字一致。以下均在只读沙箱内用内存 `FakePath` / 只读复算完成，未改任何文件。

---

## ⓪ `_apply_verdict_edits` 是否会写半个条目/破坏文件

**HIGH — `ITEM_ID_LINE_RE` 把 block scalar 内的 `- id:` 当成新条目，且预检只核对三个标注键，能静默改写 query 正文。**
- `backend/scripts/gold_set_manifest_tool.py:553-560, 570-575, 597-611`
- 复现：让 q1 的真实三标注字段已等于目标值（例如同一清单第二次 `apply-verdicts`），并在 `query: |` 块内放 `- id: q1` 后接恰一份 `user_verdict:` / `verdict_by:` / `verdict_at:`；结果 `changed=['q1']`、`problems=[]`、`write_text` 发生，但 query 正文被改成块内值。首次 apply 因真实字段仍是 `pending` 会被预检挡住，所以这是**幂等重跑路径**，不是首次普通路径。

**MEDIUM — 同一 id 重复时 `by_id` / `got` 均 last-wins，只更新最后一个块。**
- `backend/scripts/gold_set_manifest_tool.py:560, 602-605`
- 复现：YAML 有两个 `- id: q1` 块，只勾清单中第一个 q1；第二个块被更新，第一个保持 `pending`，`problems` 为空。

**MEDIUM — CRLF/CR 输入会全文件行尾重写，违反 M-2“其余字节原样”。**
- `backend/scripts/gold_set_manifest_tool.py:550, 551, 612`；测试 `backend/tests/regression/test_gold_set_manifest_g413.py:439, 484-488`
- 复现：CRLF 金集 + 任一有效 update；`Path.read_text` 先做 universal-newline 归一化，`Path.write_text` 再全量写回 LF，所有行尾变化；测试也用 `splitlines()` 读回，`diff=0`，完全看不见。

**LOW — `_yaml_scalar` 的换行守卫实际只查字面 `\n` 转义，不查真实换行。**
- `backend/scripts/gold_set_manifest_tool.py:489-499, 583`
- 复现：`verdict_by="a\nb"`；`safe_dump` 产出跨行 single-quoted scalar，守卫不触发，写入行数超过三行，并可能给后续 span 扫描制造新的 `- id:` 假行。

“字段行重复/缺失”分支本身会 `problem + 跳过该条`；“预检解析失败”会在写之前 return，单条汇总失败不会写该条。这两点按代码检查是 fail-closed，但本文件没有专门测试强制走到这些分支；真正的漏洞是上面的假 span 能让预检误判通过。

---

## ① `_parse_checklist_picks` 是否还有错误归属

**MEDIUM — anchor 搜索优先于标题，且 `current` 不受条目边界约束；标题内嵌 gsid 锚会错误归属，补审段尾部勾选也会记到最后一条。**
- `backend/scripts/gold_set_manifest_tool.py:513-516, 524-539`
- 复现 A：`<!-- gsid:A -->`、`**A** — 「... <!-- gsid:B -->」`、`- [x] ... <!-- verdict:irrelevant -->` → `picks={'B': 'irrelevant'}` 且 `problems=[]`。
- 复现 B：最后一个 item 的标题后接 `## 补审`，再放 `- [x] ... <!-- verdict:irrelevant -->` → 记到最后一条 item，`problems=[]`。新的 `[X]` 识别还扩大了这条写入路径：旧实现不认大写 X，补审段的 `- [X] ... <!-- verdict:... -->` 是新的可写面。

**LOW — `锚在标题后、勾选前` 仍会归属，但标题行已被判为 problems。**
- `backend/scripts/gold_set_manifest_tool.py:517-523`
- 复现：`**A** ...` 在 `<!-- gsid:A -->` 之前；锚随后出现，勾选仍写 A，但标题行先被记为“与隐藏锚 None 对不上”，CLI rc=1。数据没写坏，噪声/语义不干净。

**与旧实现比较**：删除/改坏锚的 M-1 场景确实从“记上一条”变成 fail-closed；但“最近锚 + 无边界 current”的错误归属方向旧实现已有，新标题核对没有关闭它，没有发现其它独立的新 fail-open 方向（`[X]` 扩大可写输入是上述例外）。

---

## ② `verify_gold_set_file` / `verify_all` 是否还有逃逸输入

**MEDIUM — `verify_gold_set_file` 会跳过非目标项的畸形 entries，也能在目标 entry 的 `query_count` 缺失/错误时返回 True。**
- `backend/scripts/gold_set_manifest_tool.py:389-403`
- 复现：manifest `files: [{合法目标 entry}, "garbage"]` → `(True, "OK ...")`；`files: [{合法 sha entry}]`（无 `query_count`）→ `(True, "... queries=None")`。同一 manifest 在 `verify_all` 中会因坏 entry 归 rc=2，两个 runner 走的 bool 边界却不是 manifest-wide fail-closed。

**MEDIUM — `verify_all` 对“已登记文件解析成非预期文档形状”仍会崩溃，未归 rc=2。**
- `backend/scripts/gold_set_manifest_tool.py:265-299`
- 复现：登记一个内容为顶层 list 的 YAML → `doc.get` 抛 `AttributeError`；`queries: 5` → `len(qs)` 抛 `TypeError`；`config: 5` → `(doc.get("config") or {}).get` 抛 `AttributeError`。这是 r2 L-R2a 同族残余，r3 的“同族归 rc=2”表述过宽。

**LOW — 入参类型逃逸。**
- `backend/scripts/gold_set_manifest_tool.py:372-386`
- 复现：`verify_gold_set_file(5)` / `None` / `b"x"` → `Path(...)` 直接 `TypeError`；`manifest_path` 传非 Path → `.exists()` `AttributeError`。两个 runner 实际都传 Path，所以是边界库存项。

**LOW — `files: []` + totals 全 0 + pending 时 `verify_all` 返回 rc=0。**
- `backend/scripts/gold_set_manifest_tool.py:248-250, 312-340`
- 复现：manifest 只有 `files: []`、`totals` 全 0、`adjudication.status: pending` → `(0, [])`。真正的空文件会 rc=2；这个“结构上空 registry”的形态不会。测试层的 `len(entries)==4` 会拦，但 CLI `verify` 本身不拦。

**bool vs rc 文案**：可以区分。sha 不符走 `sha256 期望…实测…`；环境错走 `解析失败` / `不可读` / `files 字段非法`。r3 把 docstring 改成“bool 压缩、不承诺 rc 一一对应”是准确的；但上面的非目标坏 entry 说明 bool 也不是完整的 manifest 判决。

---

## ③ `build_manifest` 单调 revision 是否 fail-closed

**MEDIUM — revision 缺失/None/float 会被当成 0/截断，history 非 list 会被 `list(...)` 吞掉或写坏。**
- `backend/scripts/gold_set_manifest_tool.py:176-183`
- 复现：`revision: null` + `--bump-revision --reason x` → 成功写 revision=1（重置）；`revision: 1.9` → prev=1，写 revision=2；`revision_history: {"a":1}` → 写成 `['a', {新记录}]`；`revision_history: 5` → 未捕获 `TypeError`。正常 list/history、合法 revision 路径可工作（dry-run revision=3），但“任何已存在 manifest 都单调、history 不丢”未达成。

**LOW — manifest 本身畸形时 build 以异常收场；不存在时 `--bump-revision` 被静默忽略。**
- `backend/scripts/gold_set_manifest_tool.py:163-164, 191-196`
- 复现：旧 manifest 为顶层 list → `old.get` `AttributeError`；YAML 冲突标记/目录 → `YAMLError`/`IsADirectoryError`；这些发生在写之前，不会写坏旧文件，但不是干净 rc。manifest 不存在时 `--bump-revision` 不报错、直接 revision=1，首生成路径**没有**被堵死。

---

## ④ 新增/改写测试是否真的覆盖声称分支

**MEDIUM — `test_no_duplicate_annotation_keys` 可以空转通过。**
- `backend/tests/regression/test_gold_set_manifest_g413.py:190-210`
- 复现：测试目标文件若没有 `  - id:` 行（或未来 id 行缩进/格式变化），`blocks=[]`，循环零次，`problems=[]`，`assert` 通过；没有 `blocks` 非空或 `len(blocks)==_queries` 的反空转锚。整体套件另有 `total>=100`，但这个 L-2 门自身可假绿。

**MEDIUM — 未覆盖 `UnicodeDecodeError`，也未直接覆盖 `verify_all` 的新 rc=2 分支。**
- `backend/tests/regression/test_gold_set_manifest_g413.py:619-687`
- 现有 7 个 case 中 `manifest-is-dir` / `registered-is-dir` 只证明 `IsADirectoryError`（OSError 族）；没有非 UTF-8 字节 case。`verify_all` 的 entries 非 dict、path 非 str、sha 非 str、totals 错、adjudication 非法等新增分支在该文件里没有独立单元测试，只有 green path 与代码检视。

**LOW — roundtrip 的“恰 3 行变化”对行尾/预检失败分支是弱断言。**
- `backend/tests/regression/test_gold_set_manifest_g413.py:439, 484-488`
- 复现：CRLF 文件走 roundtrip，前后 `read_text().splitlines()` 都归一化，`len(diff)==3` 照样成立；没有 CRLF、无尾换行、重复/缺失字段行、precheck 解析失败或读回不一致的测试。该 roundtrip 对旧 `safe_dump` 全量 churn 的 red（941→1176 行）是有效的，但不能支撑“其余字节原样”。

**已核实有效的部分**：`test_apply_verdicts_anchor_loss_is_fail_closed` 确实走标题-锚不匹配分支；`checkbox_edge_cases` 同时覆盖 `[X]` 与缺 verdict；7 个 fail-closed case 都进入各自目标分支；M-3 的 vault recorder 有实际调用记录。  
**仍缺的**：memory 侧 pin 没有记录 `check_backend_alive` 是否真被调用，`test_memory_runner_verify_passes_then_alive_gate` 在 backend 恰好 down 时与“死补丁”输出不可区分。

---

## ⑤ 证据面

**LOW — “沙箱内 6 红 = `/bin/ps` EPERM 伪影”只对 5/6 条成立。**
- `_bmad-output/审查/evidence-g413/r3-regression-20260920T131532.txt:119-141, 236-242`
- 5 条 daily review 失败明确含 `[Errno 1] Operation not permitted: '/bin/ps'`；第 6 条见 `r3-iso-ragchunk-20260920T132239.txt:17-18`，失败是 `assert len(out) >= 2 / assert 1 >= 2`，没有 EPERM。`r3-regression-outside-sandbox...:190` 的 6/6 绿只能证明环境依赖，不能证明第 6 条与 `/bin/ps` 同族。

**LOW — M-3 变异探针的最终存档不足以独立复算，尤其 memory 侧。**
- `_bmad-output/审查/evidence-g413/r3-m3-mutation-probe-20260920T131448.txt`（全文仅 11 行）
- 前两个探针文件被明确标注“作废”；最终文件只有结果，没有 mutant diff/脚本。vault 侧“`run_tiers 被调用=True`、无 sha 签名”与 recorder 测试能形成因果链；memory 侧缺少“no-pin + alive=True”对照，无法排除沙箱内 backend down 的等价解释。

**成立的部分**：`r3-gate-red-20260920T131228.txt` 的 7 条失败分别落在指定断言/异常路径（roundtrip 941→1176、anchor loss `changed=['vq-d01']`、大写 X `changed=[]`、collect `DID NOT RAISE`、三条 fail-closed 的 `read_text`/iterate/`sha256_of`）；`r3-gate-green-20260920T131354/131456/133053/133147` 为 25 passed；`r3-named...` 37 passed；沙箱外 regression `1938 passed / 6 skipped / 1 xfailed / 0 failed`；`r3-immutability...131528` 显示 58/25 条 diffs=0、12 个 AST same=True；`r3-dryrun...133141` 显示副本上每文件恰 3 行变化、shadow 0 行、`build revision=3` 后 `verify rc=0`。这些支撑普通 LF/当前四集路径，不支撑“任何输入不写坏”。

---

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

- **未被拦下的输入**：query 块内假 `- id:` + 幂等重跑；同 id 重复；CRLF/CR 文件；manifest 非目标坏 entry / 缺 `query_count`；已登记文件解析成 list/int/标量 config；`verify_gold_set_file(path=非 str)`；`files: []` + totals 0；`revision: null` / `revision_history: dict|str|int`。
- **对照输入**：干净 manifest + `check_backend_alive=False` 的 memory 对照（rc=2/backend 不可达）；未篡改 manifest 的直接 `verify_gold_set_file` OK 对照；roundtrip 的 LF 正常路径；`collect` vault 外 out 的正常写入路径。
- **负控输入**：`r3-gate-red` 的 7 条旧代码失败；删除 gsid 锚的 M-1 负控；`[X]` 与缺 verdict 的 L-1 负控；`--out` 在 vault 内的 L-3 负控；三个 fail-closed 异常负控。
- **门未覆盖的路径**：`verify_all` 的 entries 非 dict/path 非 str/sha 非 str/totals/adjudication 新分支；`UnicodeDecodeError`；CRLF/无尾换行/预检失败/重复字段行/多文件部分成功；`build_manifest` 的 revision 缺失/None/float 与 history 非 list；memory pin 的“无 pin + alive=True”对照；M-3 mutant diff 本体。

---

**本轮总评：B=0 / H=1 / M=8 / L=8**

本 commit 对普通 LF、当前四金集、M-1 删除锚场景、L-1 大小写/缺 verdict、L-3 与具体 OSError fail-closed case 达成了自述目标；但 `_apply_verdict_edits` 存在可静默改写 query 正文的 HIGH 假 span 路径，CRLF 会全文件行尾重写，且 `verify_all` / `build_manifest` 在若干畸形输入上仍非完整 fail-closed——因此“M-2 其余字节原样”和“任何输入不写坏”只能判为部分达成，不宜按全绿收口。
