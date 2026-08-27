整体裁决：**不通过**。当前仍有 **0 BLOCKER，但至少 3 个 HIGH 级闭环缺口**：H1 写越界、H2 读越界、H4 证据未绑定当前引擎 exact bytes。

审阅绑定：`card/n5-split`，HEAD `b47ebfba351f3eedb496a97961083c5e3b1d5df7`。引擎、测试与证据仍为 untracked。本轮严格静态，只做只读摘要复算，未运行 pytest 或引擎。

## H1–H6 复核

| 项目 | 裁定 | 关键证据 |
|---|---|---|
| H1 写边界 | **STILL-OPEN / HIGH** | [split_preview.py:736](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:736) 先 `mkdir`、后 `assert_symlink_free`。已有测试的 `link-dir/out` 会先在 symlink 物理目标创建 `real-dir/out`，然后才拒绝；测试只检查非零退出，没有检查零写，[test_split_preview.py:485](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:485)。此外 `O_NOFOLLOW` 只保护叶子，祖先替换竞态仍在；nlink 检查和 `O_TRUNC` open 不是同一 FD，[split_preview.py:696](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:696)。 |
| H2 seed 越界读 | **STILL-OPEN / HIGH** | `../../` 和叶子 symlink 已挡住，但只检查最终文件。若 `节点/` 或 `原白板/` 本身是目录 symlink，普通外部文件仍会通过 `is_symlink()==False` 被 hash/read/glob，[split_preview.py:437](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:437)、[split_preview.py:461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:461)、[split_preview.py:502](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:502)。检查到读取之间的替换竞态也未关闭。 |
| H3 slug 等价 | **PARTIAL / MEDIUM 残余** | ECMAScript 空白集和 UTF-16 阈值两个原反例已正确修复，[split_preview.py:85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:85)、[split_preview.py:116](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:116)。但 preview 在 slug 前额外调用 `clean_heading()`，[split_preview.py:255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:255)、[split_preview.py:400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:400)，插件则直接传 `args.selected`，[main.ts:1300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/frontend/obsidian-plugin/src/main.ts:1300)。第五条未声明偏差：`1. Topic` → preview `Topic`，TS → `1.-Topic`；`Topic [12:34]()` → preview `Topic`，TS → `Topic-1234()`。 |
| H4 live 声明 | **PARTIAL / HIGH 证据缺口** | 采集面和措辞已明显改进；before/after 均为 324 文件＋175 目录且逐字节相同。但 [engine-and-products.sha256:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/engine-and-products.sha256:1) 记录引擎 `edf520…`，本轮复算当前引擎为 `e011fa…`；`shasum -c` 唯一失败项正是引擎。现有运行、产物与 baseline 因此不能归因到当前 exact bytes。 |
| H5 拒绝测试 | **RESOLVED** | 已钉非零退出、具体“非法字符”诊断、零产物，并与合法但不存在板的诊断区分，[test_split_preview.py:431](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:431)。 |
| H6 剥离测试 | **PARTIAL / MEDIUM 残余** | 富 fence、Recent Activity fixture 与直接 mask 单测已堵住“全部 False 仍全绿”。但 AUTO fixture 外层本身是普通 HTML comment；即使 AUTO stripping 失效，`comment_mask` 仍会吞掉整个块，[test_split_preview.py:539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:539)、[split_preview.py:230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:230)。README 所称“三类 fixture 全部在全 False 时出假候选”不成立。 |

## MEDIUM 批

- **RESOLVED**：注释内标题不切分/不截断；comment mask 已传给 `sections_of`。
- **RESOLVED**：fence/注释内 callout 不计 overlap。
- **RESOLVED**：9+ 冲突不再渲染展示性 diff，[split_preview.py:650](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:650)。
- **RESOLVED**：免责声明已改成“未修改任何既有 vault 文件”并排除两个产物。
- **RESOLVED**：规模门已钉具体前五名单，[test_split_preview.py:388](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:388)。
- **PARTIAL**：零写测试能发现新增目录及 chmod，但不记录 vault 根、目录 mtime/ctime/nlink、symlink target 或 xattr；“任何文件/目录含 mtime”仍过宽，[test_split_preview.py:413](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:413)。
- **STILL-OPEN**：二轮的标记严格配对问题未处理。AUTO 仍由任意包含 `/AUTO-GENERATED` 的行闭合，fence 仍由任意 `startswith("```")` 翻转，[split_preview.py:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:190)。

## 新发现

- **HIGH**：证据 manifest 与当前引擎摘要不符，证据闭环失效。
- **HIGH**：H1 的祖先 symlink 测试实际会在拒绝前创建物理目标目录，是明确的“拒绝但已写”假绿。
- **MEDIUM**：board 被读取三次、seed 被读取两次；候选正文与声明 SHA 可能来自不同版本，[split_preview.py:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:445)、[split_preview.py:496](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:496)。
- **MEDIUM**：[live-run-log.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/live-run-log.txt:1) 只有 stdout，不是 README 宣称的“完整命令回放”，缺采集/diff 命令、exit status 和 live root 绑定。
- **MEDIUM**：baseline collector 会把目录 symlink 当作 `D`，不记录 target；当前样本恰好没有 `L` 行，[collect_live_baseline.py:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/collect_live_baseline.py:28)。
- **LOW**：slug 测试只调用 Python，没有以 TS 实现作 oracle，也未锁 U+0085、U+001C–U+001F 负例。

静态确认测试函数数量确为 **31**；“31/31 全绿”因本轮未运行且证据包没有 pytest transcript，维持 **UNVERIFIABLE**。

最终裁决：**CARD-G5-2 第三轮不通过**。H1/H2 仍能违反核心范围边界，且 H4 证据没有绑定当前引擎，不能进入验收闭环。


