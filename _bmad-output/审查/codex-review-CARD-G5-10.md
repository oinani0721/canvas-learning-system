> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-10 round-1
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-10.md)" > _bmad-output/审查/codex-review-CARD-G5-10.md 2> _bmad-output/审查/codex-review-CARD-G5-10.stderr </dev/null`
> 审查绑定: `db9fc54f`（= 送审时 HEAD；其后代码已按本轮意见整改, 故**不绑最终 HEAD**——移交 round-2 复核）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

## 绑定与读取面核对

- 当前 HEAD 确认为 `db9fc54fe801e2ef61c6ffe557ee578d4c534e8c`。
- `a357194b..db9fc54f` 的 tracked diff 确认只有两份新增文件：`split_apply.py` 766 行、测试 480 行；`split_preview.py`、`board_manifest_service.py`、`models/board_manifest.py`、board-split `SKILL.md` 均零改动。
- tracked 工作树干净；但当前目录下有未跟踪的 `_bmad-output/审查/...` 审查材料。我未读取这些材料。
- 静态统计测试函数为 13 个；测试确实先通过 `split_preview.py` CLI 生成 preview，再用 subprocess 跑 `split_apply.py`，未手造 preview JSON，也未动态加载被测脚本。
- AST 静态核对：删除类调用只有 `run_undo_mode` 内 `os.remove` 1 处，非 undo 函数为 0。
- `outputs/board-split/` 不会被下一轮 preview 当作语料：`build_preview` 只读指定 `原白板/<board>.md` 及 Concepts 列出的 `节点/<seed>.md`，不递归 `outputs/`。
- 按边界未运行 pytest / apply / undo，因此“13/13 绿”仍是作者声明；本轮是静态独立复核。

## BLOCKER

### BLOCKER-1：中断恢复会把外来文件认作自建产物，后续 undo 会物理删除它

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:207-215`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:348-356`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:395-401`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:570-606`

缺陷：目标归属判定只看可见的 `split_stable_id`，缺失 done 的重跑也不把当前文件 sha 与既有 `sha256_planned` 对账；undo 还进一步放宽到 planned 行可用 `sha256_planned` 删除，违反了 `undo_journal.py:1027-1035` “planned 一律不认领”的所有权规则。

复现思路：未被拦下的输入——先让账本留下某候选的 planned 行并中断，然后在该目标路径放一份 frontmatter 中同 `split_stable_id`、但非本进程创建的文件；重跑 apply 会在 `348-356` 补记 done，之后 `--undo` 在 sha 相符时执行 `os.remove`。planned 分支甚至不需要同 stable id，只要文件字节等于 `sha256_planned` 就会删除。

## HIGH

### HIGH-1：freshness 复算没有比对安全标志，手工改 preview 可放行歧义候选

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:188-205`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:244-264`

缺陷：`_check_fresh()` 已重算 fresh preview，却只比对 stable_id 集合和旧 preview 的内容指纹；`identity_ambiguous`、`ambiguous_group_size`、`conflict_unresolvable` 仍只信旧 JSON。

复现思路：未被拦下的输入——对真实 preview 里同标题路径重复的候选，把 JSON 中 `identity_ambiguous` 改为 `false`、`ambiguous_group_size` 改为 `1`；stable_id 集与内容指纹仍相符，门③放行并持久化 `split_stable_id`。`conflict_unresolvable` 也可同理改为 `false` 而未与 fresh 结果对账。

### HIGH-2：callout 已写入但 done 未落账时，undo 永远拒绝还原

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:512-535`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:610-633`

缺陷：`OP_SPLIT_MODIFY` 的 planned 行虽然有 `sha256_planned`，undo 分支只认 `sha256_before` 或 `sha256_after`；写后、done 前中断时没有 `sha256_after`，当前内容又不是 `sha256_before`，只能拒绝。

复现思路：对照输入——callout 原子写完成后、done 行追加前终止进程，再执行同批 `--undo`；备份和 planned sha 都在，但当前内容不等于 `sha256_before` 且无 `sha256_after`，路径落在 `627-633` 拒绝，重试也相同。

### HIGH-3：callout 插入会把 CRLF / CR 行尾整体重写为 LF

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:493-505`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:531`

缺陷：`Path.read_text()` 默认做 universal newline 转换，随后 `split("\n")` / `join("\n")` 再按字节写回，导致源文件所有 CRLF 或裸 CR 行尾被改为 LF，而不是只插入一行。

复现思路：对照输入——同一板文件分别使用 LF 与 CRLF，二者都执行 `--apply --insert-callout --confirm-insert <id>`；LF 文件只多一行，CRLF 文件整份行尾字节变化。`undo_journal.detect_newline()` 已有字节级行尾探测，但此处未使用。

### HIGH-4：嵌套候选插入 callout 后，同命令重跑会被父候选 freshness 拒绝

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:219-240`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:483-506`

缺陷：freshness 容忍只删除当前候选自己的 exact callout 行；父候选 span 还会包含子候选 callout，重跑时父候选指纹必然对不上。

复现思路：对照输入——同一文件内父小节与嵌套子小节都确认并插入 callout；第一次执行成功，第二次同参数执行时父候选 span 中残留子候选 callout，门①报“过期”。若第一次在子 callout 后、父 callout 前中断，续跑同样被挡住。

## MEDIUM

### MEDIUM-1：“已存在同形 callout”的判定过宽，代码块或注释里的文本会导致跳过

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:493-497`

缺陷：重复检测对整份文本跑 `_DERIVED_CALLOUT.finditer()`，不限制为真实 callout 行，也不排除代码 fence / HTML 注释；这与 docstring 的“同形”不一致。

复现思路：未被拦下的输入——来源文件代码块中含 `已派生为 [[节点/<name>]]` 字样，真实 callout 并不存在；执行 callout 插入时被误报“已存在同形”并跳过。

### MEDIUM-2：`--undo <batch_id>` 未限制为单个批次目录名，可指向 outputs 之外

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:554-563`

缺陷：`batch_id` 直接进入 `work / batch_id`，未校验 `bs-` 形状、禁 `..`、禁绝对路径；与“批次 id 在 `<vault>/outputs/board-split/` 下”的界面契约不一致。

复现思路：门未覆盖的路径——传入含 `../` 的相对值或绝对路径时，账本查找路径已离开 `outputs/board-split/`；只要该处存在 batch/fingerprint 自洽的 journal，后续撤销仍按 vault 内 dst 继续处理。

### MEDIUM-3：callout 分支没有在写入前重查来源锚点 symlink

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:158-183`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:491-507`

缺陷：symlink 门只在 `run_gates()` 时检查；创建节点之后再进入 `run_callout_insert()`，读取、备份、写入前均未重查 anchor，来源锚点在窗口内换成 symlink 时会被跟随读取并复制进备份。

复现思路：门未覆盖的路径——准入通过后、callout 分支执行前把来源锚点替换为指向 vault 外普通文件的 symlink；`491-507` 仍直接 `read_text()` / `journal.backup()`，没有再次 `assert_symlink_free()`。

## LOW

### LOW-1：scan_vault 测试没有逐字段断言 `source_board`

- `backend/tests/skills/test_g5_10_split_apply.py:189-195`

缺陷：测试断言了 member、role、非 orphan 和 parse_errors，但没有直接断言 member/frontmatter 的 `source_board` 原始值，弱于作者“按 node_id / source_board 逐字段断言”的自述。

复现思路：对照输入——若生成的 `source_board` 是另一个经 `resolve_node_id()` 后仍落到 `板A` 的 wikilink 写法，membership/role 断言仍可能绿，测试不会发现 provenance 原文偏差。

## 作者自述结论

- 命题 1：正常路径静态成立；测试有上述 LOW 断言缺口。
- 命题 2：仅对未修改的真实 preview 成立；HIGH-1 可放行被改写的歧义候选。
- 命题 3：基本改动会被拦截；但嵌套 callout 重跑 HIGH-4，安全标志未复算 HIGH-1。
- 命题 4：happy path 成立；planned/missing-done 归属和 callout 中断恢复不成立，见 BLOCKER-1 / HIGH-2。
- 命题 5：静态 AST 核对通过。
- 命题 6：默认关、非 TTY 未确认全跳过、普通幂等测试成立；CRLF、嵌套、误判重复问题见 HIGH-3 / HIGH-4 / MEDIUM-1。
- 命题 7：零改动核对通过。
- 命题 8：scripts-only、无 SKILL.md 核对通过。

`BLOCKER 1 / HIGH 4 / MEDIUM 3 / LOW 1`
