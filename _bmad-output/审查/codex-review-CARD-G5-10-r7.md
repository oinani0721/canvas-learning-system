> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-10 round-7（H 整改补轮上限）
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-10-r7.md)" > _bmad-output/审查/codex-review-CARD-G5-10-r7.md 2> _bmad-output/审查/codex-review-CARD-G5-10-r7.stderr </dev/null`
> 审查绑定: `8ce16fbb`（= 送审时 HEAD & 该轮代码 SHA；**第 7 轮（补轮上限）B0/H1/M0/L1 —— ⛔ D-15 上限已到，代码在 r7 后零改动，交主 session**）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

## 绁戝畾与读取面核对

- 实测 HEAD 为 `8ce16fbba5efea274f2f376a27533111b16f4dd6`，父提交为 `b8b8357ab2f731e913b63f37540648b068e81359`，与送审绑定一致。
- tracked 工作树干净；只存在未跟踪的 r6/r7 审查与 evidence 材料。
- `b8b8357a..8ce16fbb` 排除 `_bmad-output` 后只改两份文件：
  - `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`
  - `backend/tests/skills/test_g5_10_split_apply.py`
- `split_preview.py` 在父/本提交的 Git blob 均为 `0438b6618502a5aad569444c44b0c158fac87dfa`；`undo_journal.py` 均为 `c093c6a8e8aa5dbe9dee4245c54afd7f34d32445`，零改动成立。
- 测试函数静态计数为 35；未新增 board-split `SKILL.md`。
- 遵守只读要求：未运行 `pytest`、`apply`、`undo`，未改文件。作者 evidence 仅作静态核对。

## r6 整改核验摘要

- **r6-MEDIUM-1 静态闭合**：`_anchor_sha_reconciliation()` 现在用同一 `_SP.strip_generated()` / `_SP.comment_mask()` 先保留 machine fence、AUTO-GENERATED、Recent Activity 与 HTML 注释中的同形行，再只剔非 machine/非注释的精确 callout 行。该口径与 `derived_names_in()` 和 `run_callout_insert()` 的机器段判定同源到同一组函数。攻击者新增 fence/comment 边界行时，这些边界行会保留在重建字节中，SHA 不匹配，未看到新绕过。
- **`rglob` 语义成立**：本环境 Python `3.14.4` 的 `Path.glob` 默认参数实测为 `recurse_symlinks=False`。因此 `node_dir.rglob()` 默认不跟随 symlink 目录；单独检查 symlink 目录是必要的。
- **递归面**：普通更深层 `.md` 会被扫描；symlink 文件会被 `is_symlink()` 拒绝；非 UTF-8 `.md` 会在 decode 门拒绝；目录名以 `.md` 结尾会因 `not p.is_file()` 拒绝。
- **symlink 目录代价**：任何 `节点/` 下有效 symlink 目录都会让 board-split apply fail-closed，即使该目录看似与候选无关。这是保守但明确的安全取向；不跟随就无法证明里面没有残留。会卡住使用 symlink 目录的合法 vault，但不是静默失败，提示要求移出。
- **复杂度**：当前实现做两次递归枚举（`rglob("*.md")` 与 `rglob("*")`），且每个 `.md` 先完整 read/decode 一次，再由 `existing_split_stable_id()` 完整读第二次。最坏约为 descendant entry 数与 `.md` 总字节的线性两遍 I/O；不是 symlink 图循环，但大树 vault 会付出明显代价。此处未单独计缺陷。
- **r6-LOW-1 已修**：改名残留消息已改为“只能恢复原文件名（重跑 preview 不解除本门）”，不再误导。
- **带内协同重写残余风险仍成立**：完整同步重写 preview JSON 中的指纹、`board_sha256`、`sources[]` 等证据在带内仍不可判，需要带外生成时间锚；仍超出本卡边界。

---

# BLOCKER

无。

---

# HIGH

## HIGH-1：r6-HIGH-1 未完全闭合——产物移入子目录但**不改名**时，仍会创建同 `stable_id` 双产物

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:312-338`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:347-356`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:203-220`
- 测试缺口：`backend/tests/skills/test_g5_10_split_apply.py:1179-1197`

缺陷：递归扫描虽然能看见 `节点/archive/甲小节.md`，但拒绝条件只比较最终文件名 stem：

```python
if sid in by_id and p.stem != by_id[sid]:
```

因此只捕获“移动且改名”的残留。若本 preview 产物移动到子目录时保留原名，`p.stem == by_id[sid]`，该残留不会被拒绝。随后：

1. `pool` 仍只由顶层 `node_dir.glob("*.md")` 构成，子目录文件不占名；
2. `ours` 也只检查顶层 canonical 路径 `节点/{resolved_name}.md`，不会把嵌套同名同 id 文件计入；
3. 批前池重放仍解析出原候选名；
4. 顶层目标不存在，冲突门不视为已应用；
5. 同一 preview 重跑会创建新的顶层节点。

复现思路（**未执行**，这是未被拦下的输入）：

1. 对候选 `甲小节` 生成 preview 并 apply，得到：
   - `节点/甲小节.md`
   - frontmatter 含 `split_stable_id=<sid>`
2. 创建 `节点/archive/`。
3. 执行等价于：
   - `节点/甲小节.md` → `节点/archive/甲小节.md`
   - **保持文件名不变**，不像 ㉟ 的现有测试那样改成 `改名.md`
4. 用同一旧 preview 再执行 `--confirm <sid> --apply`。
5. 预期当前实现：递归扫描看到该文件但 stem 相等，不拒绝；`ours` 只查顶层路径也不认领；最终 `created=1`。
6. 结果：`节点/archive/甲小节.md` 与新的 `节点/甲小节.md` 同时携带同一 `<sid>`。

这不是“扁平池中子目录不占名”的合法结果：扁平契约可以支持顶层 `pool` 不把子目录名算作命名冲突，但递归残留扫描的目的就是发现非 canonical 位置上的本 preview 产物。当前代码既不把该嵌套文件从批前池中扣除，也不 fail-closed，等同于把它当成无害文件消失。

修复方向应是：对任何携带当前候选 `stable_id` 的递归命中，只有当路径 exactly 等于 canonical 顶层路径 `node_dir / f"{resolved_name}.md"` 时才可作为 `ours`；否则无论 stem 是否相同都拒绝。现有 ㉞ 只覆盖“移动 + 改名”，应补“移动 + 保持原名”的负控。

---

# MEDIUM

无。

---

# LOW

## LOW-1：沿承 r6-LOW-2——㉒ 仍未逐层钉住 `outputs/` symlink 检查；作者“测试钉法弱点、无行为缺陷”的判定成立

- 实现：`canvas-vault/.claude/skills/board-split/scripts/split_apply.py:855-866`
- 测试：`backend/tests/skills/test_g5_10_split_apply.py:758-793`

实现行为本身存在：`_assert_batch_chain_symlink_free()` 直接点名检查 `vault → outputs → board-split → batch → journal`，并在 journal 末段单独拒绝 symlink。

但 ㉒ 的 `outputs` 变体仍只断言泛化 `"symlink"` 与外部 journal 未追加。负控思路：从直接检查元组中移除 `vault / DEFAULT_WORK_PARENT`，保留更内层 `_SP.assert_symlink_free(work_root/batch)`；该变体仍会因祖先链检查拒绝并保持测试绿，因此无法证明 `outputs` 这一层被单独点名。

这是测试精度/变异覆盖弱点，不是当前行为缺陷；留观判定成立。

---

# 结论计数

`BLOCKER 0 / HIGH 1 / MEDIUM 0 / LOW 1`
