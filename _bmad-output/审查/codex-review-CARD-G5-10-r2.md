> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-10 round-2
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-10-r2.md)" > _bmad-output/审查/codex-review-CARD-G5-10-r2.md 2> _bmad-output/审查/codex-review-CARD-G5-10-r2.stderr </dev/null`
> 审查绑定: `f3260ed0`（不绑最终 HEAD——其后代码已按本轮意见整改, 移交 round-3）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

# CARD-G5-10 round-2 独立复核（绑 `f3260ed0ce24f65c5e35a7fc03b246605d0121f5`）

## 绑定与读取面

- HEAD 已复核为 `f3260ed0ce24f65c5e35a7fc03b246605d0121f5`。
- tracked 工作树干净；当前只有未跟踪的 `_bmad-output/审查/...` 审查材料。
- `a357194b..f3260ed0` 的 tracked 变更加上 `_bmad-output` 排除后确实只有：
  - `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`
  - `backend/tests/skills/test_g5_10_split_apply.py`
- `split_preview.py`、`board_manifest_service.py` 在本卡 diff 中零改动。
- 静态核对 `split_apply.py` 中删除原语只有 `run_undo_mode` 内一处 `os.remove`。
- 测试函数数为 20。
- 按边界未运行 pytest / apply / undo，未连数据库或网络；本结论是静态独立复核。
- 用户指定的 `第十五批-goals/P7-B.md` 在本 bound checkout 的对应路径下未找到，因此未能核对 §一(c)-(e) 原文。

## r1 九条整改的独立验伪结论

| 命题 | 结论 |
|---|---|
| 1. BLOCKER-1 认领条件 | 字面整改成立。中断补记 done 要求当前 sha == 账上 `sha256_planned`；EEXIST 竞态要求同 id 且 sha == 本次 planned；planned 行缺 `sha256_planned` 时因 `cur != None` 而拒绝。done 已存在但字节被换时，重跑不追加新 done，undo 也因旧 `sha256_after` 不符而拒删。 |
| 2. HIGH-1 四个安全字段对账 | 字面成立：`identity_ambiguous`、`ambiguous_group_size`、`conflict_unresolvable`、`basis` 均对全部旧候选与 fresh 候选逐项比较。但 freshness 没有绑定 anchor/name/fresh fingerprint，见 HIGH-1。 |
| 3. HIGH-2 split_modify 中断还原 | 成立。`sha256_after or sha256_planned` 覆盖“原子写完成、done 未落账”的恢复路径；备份仍先过可信校验。 |
| 4. HIGH-3 字节读取与换行 | 部分成立。LF/CRLF 主路径成立；裸 CR、`splitlines()` 认得的其他行分隔符、混合行尾的局部风格仍未覆盖，见 MEDIUM-1。 |
| 5. HIGH-4 嵌套 callout freshness | 目标场景成立：全文件剔 callout 后按原行号重算，父 span 含子 callout 的同命令重跑可过。但 freshness 的候选绑定仍有更广义缺口，见 HIGH-1。 |
| 6. MEDIUM-1 生成段/fence/comment 屏蔽 | 字面成立。生成段、fence、HTML comment 里的字样不再触发“已存在”。既有 `_DERIVED_CALLOUT` 仍只是短语正则，普通正文提及也会被视为 overlap；这与 `derived_names_in` 同口径，算移交观察，不计本卡缺陷。 |
| 7. MEDIUM-2 undo id shape | shape 门成立；但 symlinked batch directory 仍会使物理账本落到 vault 外，见 HIGH-2。 |
| 8. MEDIUM-3 窗口内 symlink 复查 | 字面成立：callout 每次读源前复查 anchor，create 每次-open 前复查父目录。仍存在用户态 check/read/write 的残余竞态，但没有发现比既有声明更宽的新路径。 |
| 9. LOW-1 `source_board` 原文断言 | 成立，测试已逐字断言 `[[原白板/板A]]`。 |

关于 `conflict_unresolvable` 因池变化翻转：当前实现按“旧 preview 与 fresh 不符”拒绝，是安全侧/保守侧。`basis` 虽然理论上已进入 stable id，但对账仍有价值：它能暴露同 hash 下的字段不一致或 preview 改写，而不是冗余无害。

关于手动删除 done 后 undo：`state != done` 一律拒删，收口符合 r1 的所有权方向。确实会失去一条自动撤销路径，但这是为了不把无法证明归属的文件当作自建产物；备份仍在批次目录中，用户可人工处置。

---

# BLOCKER

无。

---

# HIGH

## HIGH-1：freshness 只对账 ID 集合与四个标志，没有把旧候选绑定到 fresh 候选的 anchor/name/fingerprint，可把确认项落到错误来源或目标

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:261-280`
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py:646-650`

缺陷：`_check_fresh()` 先比较 stable id 的集合，再只比较四个标志；随后 `_span_drift_reason()` 仍拿“旧候选的旧 anchor 行号”去重算旧指纹，没有比较 `fresh_by_id[old_id]` 的 `source_anchor`、`resolved_name`、fresh `content_fingerprint`。因此候选集合相同但映射已变时，旧候选会被绑到错误槽位。

复现思路：未被拦下的输入——preview 中 `## 甲` 与 `## 乙` 两节正文逐字相同；preview 生成后把两节整体互换。两个 stable id 集合不变，四个标志不变，旧“甲”的账上行号现在指向“乙”的相同正文，内容指纹也相同，门①通过。此时确认“甲”并启用 callout，会把“已派生为节点/甲”插到现在的“乙”小节下。对照输入——两节正文不同时，旧行号处 fingerprint 不符，会被拒绝。另一个更直接的手改 preview 输入是只改某候选的 `resolved_name` 为另一个安全未占用名： flags 与内容指纹不变，当前门也会照建该目标名。

期望修复方向：对每个旧候选与同 id fresh 候选至少对账 `source_anchor.file/heading_path/line_start/line_end`、`resolved_name/suggested_name`、fresh `content_fingerprint`；callout 已插入时的行号差异需要用明确的、只剔本批插入行的映射来解释，不能只看旧窗口内容恰好等价。

## HIGH-2：`--undo` 只验 batch id 字符串，不验 batch/work 目录物理路径，symlinked batch directory 会让 journal 追加写到 vault 外

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:619-631`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:681`
- `canvas-vault/.claude/scripts/undo_journal.py:177-190`
- `canvas-vault/.claude/scripts/undo_journal.py:901-909`

缺陷：`run_undo_mode()` 直接 `work / batch_id`，只要 `journal.jsonl` 经路径解析后是文件就开始读账；没有像 apply 的 `ensure_dirs()/mkdir_chain()` 那样确认 `outputs/board-split/` 和 batch 目录本身不是 symlink。后续 `_append_entry()` 经 `append_bytes()` 追加 journal；`O_NOFOLLOW` 只保护 journal 末段，不保护祖先里的 batch/work symlink。

复现思路：门未覆盖的路径——把一个真实批次的目录内容放到 vault 外，并把 vault 内 `outputs/board-split/bs-<16hex>` 做成指向它的目录 symlink，journal 中 fingerprint/batch_id 均与当前 vault 一致。执行同 id `--undo` 时，`.is_file()` 跟随 symlink 返回真，后续 `undone` 行会追加到物理位于 vault 外的 journal。对照输入——apply 路径在 `ensure_dirs()/mkdir_chain()` 遇到 symlink 目录会拒绝；undo 缺同一层物理 containment 检查。

期望修复方向：在任何 journal 封口/追加之前，对 `vault`、`outputs`、`outputs/board-split`、batch directory、journal path 做无 symlink 组件校验；保持“纯读判绑定，通过后才可写”的顺序。

---

# MEDIUM

## MEDIUM-1：换行处理只真正支持 LF/CRLF；preview 用 `splitlines()`，apply 用 `split("\n")`，裸 CR 或 Unicode 行分隔符会产出“可 preview 但不可 apply”的候选

- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py:598-604`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:229-235`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:548-570`
- `canvas-vault/.claude/scripts/undo_journal.py:463-469`

缺陷：preview 的候选行号来自 `text.splitlines()`，它识别裸 `\r`、NEL、LS、PS 等行分隔；apply 的 freshness、正文抽取、callout 插入都用 `raw.split("\n")`。二者行号口径不同。`detect_newline()` 也只区分 CRLF 与 LF，并且以文件第一个 `\n` 前一字节决定所有插入行的 terminator。

复现思路：对照输入——同一 Markdown 内容分别使用 LF、CRLF、裸 CR。LF/CRLF 可正常 apply；裸 CR 文件可被 preview 识别出多节，但 apply 把整份文本当成一个 `\n` 行，账上行号指纹对不上，最终以 stale preview 拒绝（安全但不可用）。混合行尾输入中，若第一个 `\n` 是 CRLF，后续即使插在 LF 区，新 callout 也统一用 CRLF；既有字节不被重写，但“沿用插入点本地行尾”的说法不成立。

期望修复方向：preview 与 apply 统一 line-splitting 契约，或在 preview 侧明确只接受 LF/CRLF；若支持混合行尾，插入 terminator 应按插入点邻近行或原始字节位置决定。

## MEDIUM-2：`--confirm-insert` 子集校验发生在 `run_create()` 之后，未知 id 也会先创建节点和批次账本再报错

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:823-830`

缺陷：`run_create()` 先执行，随后才解析 `--confirm-insert` 并检查是否属于本批 `--confirm`。因此一个确定性 CLI 输入错误会先落盘，再以 `die()` 结束。

复现思路：未被拦下的输入——`--apply --confirm <valid_id> --insert-callout --confirm-insert <unknown_id>`。节点创建、journal planned/done、batch 目录都会发生，然后才报“不在本批”。对照输入——`--confirm <unknown_id>` 在准入前被拦，零产物。负控输入——把 unknown insert id 校验移到 `run_create()` 前，应保持批次目录不存在。

期望修复方向：在加载 preview/运行 gates 后、计算 batch 与调用 `run_create()` 前，先完成 insert id 的解析、去重与子集校验。

---

# LOW

## LOW-1：⑮/⑲/⑳ 新增测试没有完全钉住对应修复，存在“绿在更早判据”的突变空间

- `backend/tests/skills/test_g5_10_split_apply.py:517-535`
- `backend/tests/skills/test_g5_10_split_apply.py:643-665`
- `backend/tests/skills/test_g5_10_split_apply.py:671-678`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:267-277`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:774-779`

缺陷一：⑮ 只手改 `identity_ambiguous` 与 `ambiguous_group_size`；如果把实现中的对账元组删到只剩这两个字段，`conflict_unresolvable` 与 `basis` 的改写仍无负控。  
缺陷二：⑲ 只覆盖代码 fence，未覆盖 HTML comment；只中和 `comment_mask` 相关逻辑时该测试仍可绿。  
缺陷三：⑳ 的四个坏形状 id 都指向不存在的路径，只断言 rc≠0；删掉 shape 正则后，这些输入仍会因“找不到批次账本”而 rc≠0，测试不会红。

复现思路：负控输入——分别在实现中删除 `conflict_unresolvable/basis` 对账、只破坏 comment 屏蔽、删除 undo shape 正则；对应现有测试仍可能保持绿。对照输入——⑭/⑯/⑰/⑱ 的核心断言能分别在 sha 认领、planned restore、CRLF 字节、嵌套 freshness 上点名红，钉住程度较好。

期望修复方向：⑮ 分别改写四个字段并断言“与重算不符”；⑲ 增加 HTML comment 用例；⑳ 至少断言坏 id 报文含“形状不对”，或使用能区分 shape 门与后续 existence 门的负控。

---

# 移交观察（不计本卡计数）

- `split_preview.py:433-448` 的 `_DERIVED_CALLOUT` 是“已派生为 [[节点/...]]”短语正则，不要求完整 callout 语法。`split_apply.py:553-558` 采用同口径后，普通正文里的该短语也会触发“已存在同形”跳过。若这是 `derived_overlap` 的有意证据口径，建议改名/文案避免“同形 callout”名实不一致；若要求 exact callout，应移交 preview 契约统一修改。
- `compute_content_fingerprint()` 丢弃空行并 clamp 到当前行数；apply 未直接对账 fresh 行号时，这个既有归一化会让纯空白边界移动更难被发现。HIGH-1 的 anchor/fresh fingerprint 对账应一并覆盖此面。

# 结论计数

`BLOCKER 0 / HIGH 2 / MEDIUM 2 / LOW 1`
