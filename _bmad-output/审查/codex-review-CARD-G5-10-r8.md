> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-10 round-8（H 整改补轮）
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-10-r8.md)" > _bmad-output/审查/codex-review-CARD-G5-10-r8.md 2> _bmad-output/审查/codex-review-CARD-G5-10-r8.stderr </dev/null`
> 审查绑定: `e2abb8ef`（= 送审时 HEAD & 该轮代码 SHA；**第 8 轮 B0/H1/M0/L0 —— 已按整改 → 补轮 r9**）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

## 绑定与读取面核对

- 实测 HEAD：`e2abb8efc4c459974fd8c11d398afa008c540211`，与送审绑定一致。
- tracked 工作树干净；仅存在未跟踪的 r8 审查/evidence/prompt 文件。
- `e2abb8ef^..e2abb8ef` 实际只改两份文件：
  - `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`
  - `backend/tests/skills/test_g5_10_split_apply.py`
- `split_preview.py` blob 仍为 `0438b6618502a5aad569444c44b0c158fac87dfa`；`undo_journal.py` 仍为 `c093c6a8e8aa5dbe9dee4245c54afd7f34d32445`，零改动成立。
- 测试函数静态计数为 36；未新增 `SKILL.md`。
- 未运行 `apply` / `undo` / `pytest`，未修改文件。

---

# BLOCKER

无。

---

# HIGH

## HIGH-1：canonical 顶层判据只覆盖「能被 `rglob` 枚举出来」的命中；不可列举目录中的同名同 `stable_id` 残留仍会静默漏网并重建双产物

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:307-348`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:349-363`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:203-220`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:637-650`
- 负控缺口：`backend/tests/skills/test_g5_10_split_apply.py:1233-1252`

### 未被拦下的输入 / 复现思路（未执行）

1. 对候选 `甲小节` 生成 preview 并 apply，得到：
   - `节点/甲小节.md`
   - frontmatter 含 `split_stable_id=<sid>`
2. 创建普通目录 `节点/archive/`。
3. 执行等价移动：
   - `节点/甲小节.md` → `节点/archive/甲小节.md`
   - 保持文件名不变。
4. 将 `节点/archive/` 设为不可列举，例如 `chmod 000`，或用 ACL 拒绝 list/read/traverse。
5. 用同一旧 preview 再执行 `--confirm <sid> --apply`。

### 为什么会漏

当前修复依赖：

```python
for p in node_dir.rglob("*.md"):
    ...
    if sid in by_id and p != node_dir / f"{by_id[sid]}.md":
        return ...
```

但本卡运行时对应的 Python `3.14.4` 中，`Path.rglob()` 的 recursive selector 在递归 `scandir()` 遇到 `OSError` 时是静默 `pass` 的语义；不可列举目录的子项不会进入迭代结果。第二个兜底扫描：

```python
for d in node_dir.rglob("*"):
    if _UJ.is_symlink(d) and d.is_dir():
        return ...
```

也只拒绝 **symlink 目录**，不拒绝不可列举/不可搜索的普通目录。于是：

1. `node_dir.rglob("*.md")` 看不见 `archive/甲小节.md`，新的 canonical 路径判据没有输入可比较；
2. 顶层 `pool` 本来只由 `node_dir.glob("*.md")` 构成，嵌套残留不占名；
3. `ours` 只检查顶层 canonical 路径，也不会扣除该残留；
4. 批前池重放仍解析出原候选名；
5. 顶层目标不存在，冲突门不视为已应用；
6. `run_create()` 最终用 `O_CREAT | O_EXCL | O_NOFOLLOW` 创建新的 `节点/甲小节.md`。

结果仍然是：`节点/archive/甲小节.md` 与新的 `节点/甲小节.md` 同时携带同一 `<sid>`，即 r7-HIGH-1 的同影响路径，只是把残留藏进 `rglob` 无法枚举的目录。

### 修复方向

不要依赖会吞掉遍历错误的 `Path.rglob()` 作为安全枚举。至少应改为显式递归 `os.scandir()`：任何目录级 `OSError` / `PermissionError` 都视为归属不可判定并整批拒绝；对每一个将要下钻的目录，枚举失败必须 fail-closed，而不是跳过。并补一个权限负控（测试 finally 中恢复权限），覆盖「移入不可列举子目录 + 保持原名」。

---

# MEDIUM

无。

---

# LOW

无。

---

## 重点命题独立核验记录

### 1. canonical 顶层路径判据本身，对**可枚举**路径是闭合的

在文件确实被 `rglob("*.md")` 返回的前提下：

| 位置 / 形态 | 结论 |
|---|---|
| canonical 顶层 `节点/<账上名>.md` | 放行；apply 写入路径与比较路径逐字同构 |
| 顶层改名 | `p != canonical`，拒绝 |
| 一层或多层子目录，保持原名 | `p != canonical`，拒绝；㊱ 已覆盖一层 |
| 一层或多层子目录，改名 | `p != canonical`，拒绝；㉞ 已覆盖 |
| 深层 more layers | 同样多出路径组件，`p != canonical`，拒绝 |
| symlink `.md` 文件，包括 canonical 路径本身是 symlink | 先在 `_UJ.is_symlink(p)` 拒绝；canonical target 也有前置 symlink gate |
| 非普通文件、目录名以 `.md` 结尾 | `not p.is_file()` 拒绝 |
| 读不回 / 非 UTF-8 `.md` | decode/read 门拒绝 |
| valid symlink 目录 | `rglob("*")` 兜底拒绝 |
| hardlink 位于非 canonical 路径 | 词法路径不等，拒绝；不会因同一 inode 被认成 canonical |
| `.` / `..` 路径段 | `rglob` 结果不产生这种目录项；confirmed `resolved_name` 又经 `member_name_ok()` / `safe_join()` 拒绝路径逃逸，未确认候选取会被批前池重放对账拒绝 |
| 大小写异写 | POSIX `Path` 词法比较不等，拒绝；即使底层 FS case-insensitive，也不会把异写路径误等成 canonical |
| NFD/NFC 异写 | 词法路径不等，拒绝；这是保守 fail-closed，不是漏网 |
| 不可列举目录 | **漏网，见 HIGH-1** |

`resolve()` / `os.path.samefile()` / NFC 归一不应引入：它们分别会把 symlink 物理别名、hardlink / case / Unicode 别名合并成“同一文件”，反而可能把非 canonical 残留判成 canonical。当前 raw lexical equality 是更严格的位置判定。

合法自建文件不被误伤：`targets[sid]` 由 `_UJ.safe_join(vault, f"节点/{name}.md")` 构造，实际创建也写这个 exact target；残留门比较的也是同一 resolved `vault / "节点" / f"{name}.md"`，二者对有效 `resolved_name` 逐字一致。

### 2. 旧 / 新判据真值表：在可枚举且有效命选名的域内，是单向收紧

设 `sid in by_id`，`n = by_id[sid]`，`C = node_dir / f"{n}.md"`：

| `p` | 旧判据 `p.stem != n` | 新判据 `p != C` | 结论 |
|---|---:|---:|---|
| `p == C` | false，因为文件名为 `n + ".md"` | false | 旧放行 / 新放行 |
| `p != C` 且 `p.stem != n` | true | true | 旧拒绝 / 新拒绝 |
| `p != C` 且 `p.stem == n` | false | true | 旧放行 / 新拒绝（r7 缺口） |
| `sid not in by_id` | false（该分支不触发） | false | 其他门处置 |

因此对有效 CLI 输入，没有找到“旧拒绝 / 新放行”的安全反例；新增拒绝面正是“同名异路径”。带 `/`、`..` 等恶意 `resolved_name` 会被 confirmed 名字门或批前池重放拒绝，不能成为实际放行反例。

### 3. 其余面未被本轮回退

- r5 的 symlink / 非普通文件 / 读不回 / symlink 目录 fail-closed 面仍在，未见放宽；唯不可列举目录是原有递归枚举盲区，在 HIGH-1 中列报。
- r5-HIGH-3 剔行分层逻辑未改。
- r6-MEDIUM-1 机器段 / HTML 注释口径未改。
- r6-LOW-1 文案方向未被回退。
- `split_preview.py` 与 `undo_journal.py` blob 均不变。
- `os.remove` 静态仅出现在 undo 分支 `split_apply.py:938`，默认路径仍无物理删除。
- `--insert-callout` 仍默认关，只有 `--apply` 下显式执行。
- 完整协同重写 preview JSON（指纹 + `board_sha256` + `sources[]`）的带内不可判残余风险仍成立，仍需带外生成时间锚，超出本卡边界。

---

# 结论计数

`BLOCKER 0 / HIGH 1 / MEDIUM 0 / LOW 0`
