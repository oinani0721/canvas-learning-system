> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-10 round-9（H 整改补轮 · 收口轮）
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-10-r9.md)" > _bmad-output/审查/codex-review-CARD-G5-10-r9.md 2> _bmad-output/审查/codex-review-CARD-G5-10-r9.stderr </dev/null`
> 审查绑定: `9943b59d`（= 送审时 HEAD & 最终代码 SHA；**第 9 轮 B0/H0/M0/L0 —— ✅ 绑最终 HEAD 的 PASS 轮，H 整改收口**）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

# 独立复核记录（round-9 / `9943b59d`）

## 绑定与读取面核对

- 实测 HEAD：`9943b59dd0c803ba088745f75ecfbc7c1d27108d`，与送审绑定一致。
- tracked 工作树干净；仅有未跟踪的 `_bmad-output/审查/` r8/r9 审查、prompt、evidence 文件。未读取 r9 文件。
- `9943b59d^..9943b59d` 实际只改两份文件：
  - `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`
  - `backend/tests/skills/test_g5_10_split_apply.py`
- `split_preview.py` blob 在 `e2abb8ef` 与 `9943b59d` 均为 `0438b6618502a5aad569444c44b0c158fac87dfa`。
- `undo_journal.py` blob 在 `e2abb8ef` 与 `9943b59d` 均为 `c093c6a8e8aa5dbe9dee4245c54afd7f34d32445`。
- 测试函数静态计数为 37；本轮 diff 未新增或修改 `SKILL.md`。
- 按送审要求未运行 `apply` / `undo` / `pytest`，未修改文件。

---

# BLOCKER

无。

---

# HIGH

无。

---

# MEDIUM

无。

---

# LOW

无。

---

## 重点命题核验

### 1. r8-HIGH-1 是否闭合：结论为闭合

本轮修复将残留扫描从 `Path.rglob()` 换成显式栈式 `os.scandir()`：

- `_enumerate_node_pool()`：`canvas-vault/.claude/skills/board-split/scripts/split_apply.py:300-335`
- 调用与 fail-closed：`canvas-vault/.claude/skills/board-split/scripts/split_apply.py:345-355`
- symlink / 非普通文件 / 读不回 / canonical 判据：`canvas-vault/.claude/skills/board-split/scripts/split_apply.py:356-385`
- 新负控：`backend/tests/skills/test_g5_10_split_apply.py:1259-1284`
- r8 原漏点与修复方向：`_bmad-output/审查/codex-review-CARD-G5-10-r8.md:22-28`, `:42-74`

我按下列类别核对：

| 条目 / 目录类别 | 结论 |
|---|---|
| `节点/` 本身 `chmod 000` | 普通 POSIX 权限下 `Path.is_dir()` 仍可 stat 成目录；随后 `os.scandir(node_dir)` 抛 `OSError`，被捕获并返回拒绝原因 |
| 任一子目录 `chmod 000` | 父层 `scandir` 能看到该普通目录并压栈；下一轮 `scandir` 抛 `OSError`，fail-closed |
| 多层普通目录中的 `.md` | 普通目录持续压栈，不依赖 Python 递归；路径过长 / IO 失败会作为 `OSError` 拒绝 |
| 普通 `.md` 文件 | 输出为 `md`，后续沿用普通文件、UTF-8、stable_id、canonical 路径门 |
| symlink 的 `.md` | 输出为 `symlink-md`，后续拒绝 |
| 可判定目标的 symlink 目录，无论目录名是否 `.md` | 输出为 `symlink-dir`，后续拒绝 |
| 目录名以 `.md` 结尾 | 输出为 `dir-md`，后续 `not p.is_file()` 拒绝 |
| FIFO / socket / 设备等非普通文件且名字 `.md` | 输出后由 `not p.is_file()` 拒绝 |
| 读不回或非 UTF-8 的 `.md` | 沿旧门拒绝：`split_apply.py:373-379` |
| 枚举失败发生前已得到部分 entries | 调用方只看 `enum_reason`，不消费部分结果，整批拒绝 |
| 非常深嵌套 | 无 Python 递归深度问题；栈式遍历，遇到 OS 路径 / IO 错误 fail-closed |
| mount point | 可访问挂载内容会继续枚举；枚举失败则拒绝。若挂载层主动遮蔽底层 namespace，那是带外 mount 状态，用户态路径枚举无法证明底层内容 |
| bind mount cycle | 可能造成预写扫描不终止或巨大代价，但不是静默放行；且旧 `rglob` 同样递归遍历，不是本轮回退 |
| 枚举中途权限变化 | 已观测到的 `OSError` 会拒绝；完全并发替换 / 移动 / 重挂载属于 TOCTOU 边界，静态单趟扫描无法闭合 |
| 非 `OSError` | `scandir` / DirEntry 分类的操作性失败面是 `OSError`；`KeyboardInterrupt` / `SystemExit` / `MemoryError` 等应中止进程，且发生在任何批次写入前。未发现会变成静默放行的常规非 OSError 路径 |
| `sorted(it)` 资源语义 | `sorted` 在 `with os.scandir(...) as it` 内耗尽迭代器；异常时 context manager 也会关闭句柄，不依赖生成器 finalizer。排序只影响错误出现顺序，不影响覆盖集 |

关键顺序也正确：`run_gates()` 在 `_check_fresh()` 中触发枚举拒绝，且整个准入发生在 `run_create()` 建批次账本之前：

- gate 顺序：`split_apply.py:513-525`
- 批次账本创建发生在后续 `run_create()`：`split_apply.py:567-590`

因此“枚举失败 ⇒ 整批拒绝且连批次目录都不建”成立。

### 2. 旧 / 新判据：只收紧，不放宽

顶层命名池仍只来自 `node_dir.glob("*.md")`，未扩大、未缩小：`split_apply.py:345-346`。这保持合法重跑 / 分段确认的批前池重放语义。

对可枚举域逐项比较：

| 形态 | `e2abb8ef` 旧行为 | `9943b59d` 新行为 | 结论 |
|---|---|---|---|
| 目录枚举失败 | `rglob` 静默漏段，可能放行 | 返回原因，整批拒绝 | 收紧 |
| canonical 顶层 `.md` 且同 id | 放行为自家产物 | 放行 | 不变 |
| 非 canonical `.md` 且同 id | `p != canonical` 拒绝 | 同判据保留并拒绝 | 不变 |
| symlink `.md` | 旧第一轮 `is_symlink` 拒绝 | `symlink-md` 拒绝 | 不变 |
| 目录名 `.md` | `not is_file()` 拒绝 | `dir-md` 后 `not is_file()` 拒绝 | 不变 |
| 非 `.md` 后缀的普通特殊文件 | 旧设计不视为 node-pool 成员 | 仍不视为 node-pool 成员 | 不变 |
| 可访问 symlink 目录 | 旧 `rglob("*") + is_dir()` 兜底拒绝 | `symlink-dir` 拒绝 | 不变 |
| 读不回 / 非 UTF-8 `.md` | 拒绝 | 同段保留 | 不变 |
| 条目分类期间 `OSError` | 可能被 `rglob` 吞掉或变成漏扫 | 一律按枚举失败拒绝 | 收紧 |

未找到任何“旧拒绝 / 新放行”反例。排序和单趟合并只改变错误优先级，不改变接受集。

### 3. fail-closed 是否过宽

一个不可读目录导致整批拒绝是可接受的：

- 命名池是全局的，一个隐藏残留可能释放任意候选名，无法安全做到“只拒相关候选”；
- 若继续放行，就重新打开 r8-HIGH-1；
- `节点/` 契约本是扁平池，嵌套目录本身已偏向异常状态；
- 若要改善 UX，可另做 preflight 汇总多个错误，但安全决策仍应整批 fail-closed。

大树代价方面，新实现一趟显式遍历；旧实现实际有 `rglob("*.md")` 加 `rglob("*")` 两趟。新增 `sorted()` 只按单个目录的 entry 名排序，内存为当前目录 entry 数量级别；没有引入旧版没有的渐进复杂度。

### 4. 其余命题未回退

- r5 改名残留 fail-closed：canonical 路径与同 id 判据仍在 `split_apply.py:380-385`；既有负控在 `test_g5_10_split_apply.py:971-1013`, `:1180-1253`。
- 剔行分层：`split_apply.py:223-253`, `:639-657`；测试 `:1017-1064`。
- 字节锚：`split_apply.py:404-451`；板与种子反例 `:1070-1091`, `:1097-1124`。
- r6 机器段 / HTML 注释口径：`split_apply.py:443-449`, `:810-819`；测试 `:1204-1228`。
- r7 canonical 顶层规则：`split_apply.py:347-355`, `:380-385`。
- 真 `scan_vault` derived / 非孤儿：`test_g5_10_split_apply.py:179-198`。
- 歧义零持久化：`split_apply.py:192-200`；负控 `:204-218`。
- 过期 preview 零产物：`split_apply.py:454-510`；测试 `:224-238`。
- undo 全树逐字节还原：`test_g5_10_split_apply.py:307-341`；用户改过的自建文件拒删在 `:347-370`。
- 默认 apply / callout 路径无物理删除：`os.remove` 静态仅出现在 undo 分支 `split_apply.py:975`，且前有 sha 所有权检查 `:958-974`。
- callout 默认关：`--insert-callout` 是 opt-in `split_apply.py:1063-1066`，仅在显式传入后执行 `:1131-1133`。
- 完整协同重写 preview JSON 的带外生成时间锚残余风险仍成立；本轮没有也不会解决该边界。

---

# 结论计数

`BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 0`
