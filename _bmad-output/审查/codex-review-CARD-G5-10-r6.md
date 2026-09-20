> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-10 round-6（H 整改补轮）
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-10-r6.md)" > _bmad-output/审查/codex-review-CARD-G5-10-r6.md 2> _bmad-output/审查/codex-review-CARD-G5-10-r6.stderr </dev/null`
> 审查绑定: `b8b8357a`（= 送审时 HEAD & 该轮代码 SHA；**第 6 轮 B0/H1/M1/L2 —— 已按整改 → 补轮 r7**）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

# CARD-G5-10 round-6 独立复核（绑定 `b8b8357ab2f731e913b63f37540648b068e81359`）

**绑定/范围核对**：HEAD 与送审 SHA 一致；tracked 工作树干净，但存在未跟踪的 r6 审查/evidence 文件。排除 `_bmad-output` 后本 commit 只改 `split_apply.py` 与 `test_g5_10_split_apply.py`；`split_preview.py`、`undo_journal.py` 未改。测试函数静态计数为 33。未运行 pytest/apply/undo，未改文件。

**三条 r5 HIGH 核验**：  
- r5-HIGH-2 的两条点名路径（symlink 残留、id 超过 200 行）静态闭合：`existing_split_stable_id()` 不再设 200 行上限，池内 symlink/非普通文件/读不回均拒绝。  
- r5-HIGH-3 的 exact/tolerance 分层成立；作者判定“(7,11)≠(7,12) 先拦”也成立：preview-era callout 形态行进入候选 span 时，`_callout_mapped_span()` 会先因剔除该行导致 span 映射不符而拒绝，当前 revision 到不了 `run_create()` 的剔行分支。  
- r5-HIGH-1 的“只改正文 + 只抄 fingerprint”被字节锚拦下；r5 原处方（旧 JSON fingerprint 对 fresh fingerprint）确实对“同步抄指纹”无效。残余判断成立：所有绑定证据仍在同一 JSON 内，协同重写不可与合法新 preview 区分。细化一点：board 候选需同步改 fingerprint + `board_sha256` + board source sha；seed-only 候选只需同步改 fingerprint + seed source sha，不必动 board 字段，但仍属同一“带内协同重写”边界。  
- 去掉 200 行上限未引入二次复杂度；池扫描最坏为线性读取第一层 `节点/*.md` 总字节数。非算法 DoS。

---

## BLOCKER

无。

---

## HIGH

### HIGH-1：`同 stable_id 双产物` 保证仍只覆盖 `节点/` 第一层池，移动到子目录的残留可绕过

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:307-312`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:332-337`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:203-220`

缺陷：`_resolution_replay_reason()` 用 `node_dir.glob("*.md")` 只扫描 `节点/` 直接子项。把本 preview 已创建的产物移动到 `节点/archive/改名.md` 后，该文件不再进入池扫描；旧顶层名 `节点/甲小节.md` 变为空闲，同一 preview 可再创建一份携带相同 `split_stable_id` 的顶层节点。

复现思路（**未执行**，负控输入）：

1. 对候选 `甲小节` 生成 preview 并 apply，得到顶层 `节点/甲小节.md`，frontmatter 含 `split_stable_id=<sid>`。
2. 创建普通目录 `节点/archive/`，把 `节点/甲小节.md` 移动为 `节点/archive/改名.md`。
3. 用同一旧 preview 再执行 `--confirm <sid> --apply`。
4. `glob("*.md")` 看不到子目录残留；`:332-337` 不检查其 stable_id；目标顶层路径不存在，`:211-220` 不判 applied；板字节锚未变，最终 created=1。
5. 结果是 `节点/archive/改名.md` 与新的 `节点/甲小节.md` 同时携带同一 `<sid>`。

这不是 r5 点名的 symlink/200 行路径，但仍是“同 stable_id 双产物”安全性质的未覆盖输入；若产品定义明确只保证第一层命名池，则需要在契约中显式收窄，否则应递归/带外登记处理残留。

---

## MEDIUM

### MEDIUM-1：字节锚容忍面按整行集合剔除，不保留 machine fence 语义；preview 时已有“本轮候选名”的精确 callout 行会导致插入后重跑误拒

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:370-371`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:391-398`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:757-766`
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py:436-448`
- 测试缺口：`backend/tests/skills/test_g5_10_split_apply.py:1129-1153`（㉜只测“非本轮候选名”的 fence 行）

缺陷：`forms` 只按候选名的精确字符串建集合，`:395` 会把全文所有同形行全部剔掉，不区分该行当前是否在 code fence/HTML 注释里。可是 preview 的 `derived_names_in()` 和 callout “已存在”判断都把 machine fence 中的行排除。因此 preview 时代已存在的“本轮候选名”精确形态示例行会被字节锚误认为可剔除的本轮插入。

复现思路（**未执行**）：

1. 板上 `甲小节` 候选正文外/尾部 code fence 中预置逐字行：  
   `> [!relation/related_to]+ 已派生为 [[节点/甲小节]] · 相关`
2. 生成 preview。`derived_names_in()` 因 fence 跳过该行，候选仍解析为 `甲小节`；`forms` 包含这行的精确形态。
3. 第一次 `--apply --insert-callout --confirm-insert <sid>`：原始字节锚精确匹配；插入判据也因 fence 忽略该行，因此真实 callout 插入成功。
4. 第二次同命令重跑：当前文件同时有 fence 中的 preview-era 行和真实插入行；`:395` 两行都被剔除，重建文本比 preview 原字节少了原来的 fence 行，`:396-398` 误判字节锚不符并拒绝。

影响是保守拒绝/重跑 livelock，不会静默产错文；但破坏了该输入形态下的插入幂等/中断续跑，且 ㉜没有覆盖“候选名本身出现在 fence”的分支。

---

## LOW

### LOW-1：沿承 r5-LOW-1，普通改名残留提示中的“重跑 preview”仍无效

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:333-336`
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py:786-840`

复现思路：创建 `节点/甲小节.md` 后改名为顶层 `节点/新名.md`，再重新生成 preview。新 preview 仍会给候选账上名 `甲小节`，但 `_resolution_replay_reason()` 会继续发现 `新名.md` 携带同 stable_id 的改名残留并拒绝；用户只能恢复旧文件名，重跑 preview 不能解除。行为安全，但提示误导。

### LOW-2：沿承 r5-LOW-2，㉒仍没有单独钉住 `outputs/` 这一层 symlink 检查

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:841-849`
- `backend/tests/skills/test_g5_10_split_apply.py:758-793`

复现/负控思路：从 `_assert_batch_chain_symlink_free()` 的直接检查元组中移除 `vault / outputs`，保留更内层 `assert_symlink_free(workroot/batch)`；`outputs` symlink 变体仍会因祖先链检查拒绝并输出泛化 `"symlink"`，现有测试不会变红，因此无法证明该层被逐层点名。

---

# 结论计数

`BLOCKER 0 / HIGH 1 / MEDIUM 1 / LOW 2`
