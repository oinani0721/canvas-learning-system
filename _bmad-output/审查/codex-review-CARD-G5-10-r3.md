> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-10 round-3
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-10-r3.md)" > _bmad-output/审查/codex-review-CARD-G5-10-r3.md 2> _bmad-output/审查/codex-review-CARD-G5-10-r3.stderr </dev/null`
> 审查绑定: `d5a06d33`（不绑最终 HEAD——其后代码已按本轮意见整改, 移交 round-4）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

# CARD-G5-10 round-3 独立复核（绑 `d5a06d33578ff682034493afd15c2078486eb80b`）

## 绑定与读取面核对

- 当前 HEAD确认为 `d5a06d33578ff682034493afd15c2078486eb80b`，提交主题与送审描述一致。
- tracked 工作树干净；只有 `_bmad-output/审查/...` 等未跟踪审查材料。
- `a357194b..d5a06d33` 排除 `_bmad-output` 后确实只有两份新增文件：
  - `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`
  - `backend/tests/skills/test_g5_10_split_apply.py`
- `f3260ed0..d5a06d33` 的整改面也只改这两份文件；`split_preview.py`、`board_manifest_service.py`、`SKILL.md` 均未进入本卡 diff。
- 静态核对测试函数为 24 个；未重新运行 pytest / apply / undo，因此“24/24 绿、ruff rc=0、AST 门、地盘检查”仍按作者声明处理，本轮是静态独立验伪。
- 用户指定的 `第十五批-goals/P7-B.md` 在本 bound checkout 下未找到，未能核对 §一(c)-(e) 原文；这是本轮契约核对的限制。

## r2 五条整改的独立验伪结论

| 命题 | 结论 |
|---|---|
| r2-HIGH-1 候选绑定与行号映射 | **部分成立，但不足以保证执行内容正确。** 互换/改名负控确实能被 `source_anchor`、`suggested_name`、`resolved_name` 兼容规则和行号映射拦住；但映射结果没有用于后续正文切片或 callout 插入，见 HIGH-1。`resolved_name` 同基任意后缀的宽松面见 MEDIUM-1。 |
| r2-HIGH-2 undo 批次目录链 | **journal 链本身成立。** `vault → outputs → outputs/board-split → batch → journal` 的内容读账、身份判定和追加都发生在链校验之后；前面只有 `is_file()` 的 stat 跟随，未读内容也未写盘。但 undo 的业务目标父链未验 symlink，见 HIGH-2。 |
| r2-MEDIUM-1 切行契约与局部行尾 | **主命题成立。** 裸 CR 与 Python `splitlines()` 认识的 `\v \f \x1c-\x1e \x85 \u2028 \u2029` 会被精确拒绝；CRLF/LF 混合文件按插入点上一行的实际结尾选择。对合法 `\f`/`\u2028` 正文的一刀切拒绝是明确保守契约，不是漏拦。测试覆盖面见 LOW-2。 |
| r2-MEDIUM-2 `--confirm-insert` 前置 | **零产物命题成立。** 未知 insert id 在 `run_create()` 之前拒绝；虽然校验发生在 gates 之后，但 gates 是读路径，批次目录仍未创建。重复 id 没有在列表阶段去重，但后续转成 `set`，行为不重复。 |
| r2-LOW-1 测试补臂 | **四条新增测试存在且大体钉住对应修复。** ⑮/⑲/⑳ 的点名程度比 r2 提高；㉑能区分行号映射与内容指纹，㉔能证明未知 insert id 零批次。㉒/㉓仍有覆盖缺口，见 LOW-1/LOW-2。 |

其余静态命题：真 `scan_vault` 承接面、callout 默认关、undo 的 sha 所有权方向、0 物理删除的静态调用位置、零改动和不加 `SKILL.md` 均未发现反向证据。

---

# BLOCKER

无。

---

# HIGH

## HIGH-1：fresh 行号映射只用于验旧，创建正文和 callout 插入仍使用未映射的账上行号，接受 callout 漂移后会生成错位内容

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:237-246`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:344-349`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:471-477`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:635-643`

缺陷：门①能把 fresh 行号在“剔除 callout”坐标系下映射回账上行号，但 `run_create()` 随后仍直接用旧 `line_start/line_end` 切当前文件，`run_callout_insert()` 也直接用旧 `line_start` 插入；一旦前面已有 callout，当前坐标已后移，节点正文会含错行/缺末行，callout 可能插到目标标题之前。

复现思路：未被拦下的输入——preview 含 A、B 两节；先对 A 执行 `--apply --insert-callout --confirm-insert A`，再用同一 preview 只确认 B。A 的 callout 使 B 的 fresh 行号整体后移，映射门通过；但 `run_create()` 按旧 B 区间切片，当前索引已指到 B 标题附近，正文错位并缺尾部行；若同时插入 B callout，则按旧行号会插到 B 标题前。另一个对照路径是：A 节点生成并插入 callout 后手工删除 A 节点，再用旧 preview 重建 A；门①接受 callout 漂移，但新 A 节点正文会包含 callout 行并截掉原 span 末行。

## HIGH-2：undo 只验 journal 目录链，不验账上业务目标的父链 symlink，create 分支可删到 vault 外、modify 分支可覆盖 vault 外

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:692-703`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:737-749`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:760-769`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:773-802`

缺陷：`_assert_batch_chain_symlink_free()` 只覆盖 journal 所在链；撤销 `dst/src` 时只检查末段不是 symlink，没有对 `节点/`、`原白板/` 或更深层父目录执行无 symlink 组件校验，`safe_join()` 也只做词法 containment。

复现思路：门未覆盖的路径——先正常 apply 产生节点或 callout 修改；随后把整个 `节点/`（或 `原白板/`）移动到 vault 外并用目录 symlink 替换。journal 链仍全在 vault 内，`dst/src` 末段是普通文件，sha 也匹配；create 分支的 `os.remove()` 会删除物理位于 vault 外的节点，modify 分支会用批次备份覆盖 vault 外的板文件。

---

# MEDIUM

## MEDIUM-1：`resolved_name` 的“同基后缀重排”过宽，手改 preview 可把确定性的 `_3` 目标改成任意未占用 `_9`

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:294-301`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:337-343`
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py:474-495`

缺陷：fresh 解析器按 `_2.._9` 的第一个空闲后缀确定性选名，但 apply 的兼容规则接受同基任意后缀；因此旧 JSON 的 `resolved_name` 可以被改成另一个未占用后缀而不触发 freshness 拒绝。

复现思路：未被拦下的输入——preview 时 `节点/甲.md` 与 `节点/甲_2.md` 已存在，fresh/旧候选本应解析为 `甲_3`；手工把旧 JSON 的 `resolved_name` 改成 `甲_9`。`suggested_name`、anchor、stable_id、内容指纹均不变，`甲_9` 空闲，`_resolved_name_fits("甲_9", "甲_3")` 为真，最终创建 `节点/甲_9.md`。锚点、内容与 stable_id 仍被绑住，也没有覆盖既有文件，所以低于 HIGH，但目标命名不再等于 fresh 解析结果。

---

# LOW

## LOW-1：㉒只钉住 batch 末段 symlink，没有覆盖 outputs / work root / 更深祖先 / journal 末段

- `backend/tests/skills/test_g5_10_split_apply.py:758-775`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:692-703`

缺陷：测试只把批次目录本身替换成 symlink；若实现只检查 batch 末段而漏掉 `outputs`、`outputs/board-split` 或 journal 本身，该测试仍可能保持绿。

复现思路：负控输入——把链检查缩窄为只检查 batch 目录，保留现有㉒输入；测试仍会因“symlink”变红转绿路径不充分。对照输入应分别替换 `outputs`、`outputs/board-split`、batch 与 `journal.jsonl`，并断言各自点名 symlink 且外部 journal 字节数不变。

## LOW-2：㉓只覆盖裸 CR，未钉住 splitlines-only 分隔符和 CRLF/LF 混合文件的局部行尾选择

- `backend/tests/skills/test_g5_10_split_apply.py:781-793`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:250-270`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:640-643`

缺陷：现有测试能证明裸 CR 有精确拒绝理由，但不能证明 `\f`、`\u2028` 等也被同一契约拒绝，也不能证明混合行尾时插入行真的沿用插入点上一行的局部风格。

复现思路：负控输入——把 `_SPLITLINES_ONLY_RE` 从检查中移除但保留裸 CR 条件，㉓仍绿；再分别在 LF 区与 CRLF 区插入 callout，当前测试没有断言新增行 terminator 随局部上一行变化。

---

# 移交观察（不计本卡计数）

- `split_preview.py:433-448` 的 `_DERIVED_CALLOUT` 仍是短语级匹配，不要求完整 callout 语法；`split_apply.py` 复用该口径做 drift 剔除和“已存在”判断。该正则本身属于 preview 既有面，按边界计移交；但本卡 HIGH-1 已说明即使限定为真实工具插入的 exact callout，行号映射结果也必须传导到后续读写，否则仍会错位。
- `undo_journal.append_bytes()` 只用 `O_NOFOLLOW` 防末段 symlink，未检查打开后 inode 的 `nlink`；普通 hardlink alias 不在本轮“symlink 组件”命题内，暂不计缺陷。若后续把物理 containment 扩展到 alias 面，应与 P7-A 一并处理。

# 结论计数

`BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 2`
