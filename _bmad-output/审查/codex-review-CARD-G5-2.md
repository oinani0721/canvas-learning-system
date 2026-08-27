整体裁决：**不通过**。未发现已确认的 BLOCKER，但有 6 项 HIGH，足以否决 CARD-G5-2 当前验收闭环。

审阅基于 `card/n5-split`、HEAD `b47ebfba351f3eedb496a97961083c5e3b1d5df7`；引擎、裁判和证据目录当前均为 untracked。全程只读，未运行引擎、pytest 或攻击试验。

## 分级发现

### BLOCKER

无。

### HIGH

1. **FAIL — 写边界只有词法约束，没有物理 fail-closed**

   显式写调用仅有目录创建和两个 `write_text`，叶子路径词法上位于 `out_dir`；但仅检查最终目录项是否 symlink，[split_preview.py:608](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:608)、[split_preview.py:615](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:615) 挡不住：

   - 祖先目录 symlink；
   - 既存目标 hardlink；
   - `is_symlink()` 到 `write_text()` 之间的替换竞态；
   - bind mount 等非 symlink 重定向。

   此外 [split_preview.py:612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:612) 的 `parents=True` 会创建缺失祖先并改变父目录元数据，严格说不全在“既存 out-dir 内”。这些是静态可达风险，未实跑利用。

2. **FAIL — 板名校验没有覆盖板内 seed 路径，存在 vault 外读取**

   `_BAD_BOARD` 只校验 CLI 板名，[split_preview.py:117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:117)。成员正则允许 `/`、`\`、`..`，[split_preview.py:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:281)，随后未经 containment 校验直接拼入路径并 hash/read，[split_preview.py:400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:400)、[split_preview.py:414](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:414)。

   静态触发例：`[[节点/../../outside]] — 种子`；绝对 seed 或板/seed 文件 symlink 也会被跟随。虽然是读侧越界，但直接违反“只读指定 vault”的范围契约。

3. **FAIL — Python 与 TS 的严格 slug 等价性不成立**

   除时间戳 fallback 外，至少还有一个未声明偏差和一个被错误描述的偏差：

   - Python `strip()/re \s` 与 ECMAScript `trim()/\s` 的 Unicode 空白集合不同：[split_preview.py:58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:58) 对 [node-derivation.ts:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/frontend/obsidian-plugin/src/node-derivation.ts:21)。例如 U+FEFF 在 TS 中被清理，在 Python 中保留；U+0085 则相反。
   - 两边都先按码点取 40 个字符；真正差异是 TS `lastIndexOf` 返回 UTF-16 code-unit 下标，而 Python `rfind` 返回码点下标：[split_preview.py:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:82) 对 [node-derivation.ts:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/frontend/obsidian-plugin/src/node-derivation.ts:59)。`😀 + 18×a + "-" + 25×b` 会令 TS 回退到 dash，Python 保留完整 40 码点。
   - README 所称“显式偏差只有一处”和“emoji 附近偏移一位”均不准确：[README.md:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/README.md:32)、[README.md:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/README.md:34)。

4. **FAIL — “live vault 0 修改铁证”过度宣称**

   我只读核对了两对文件：before/after 确实分别逐字节相同，284/324 行数量也吻合 README。但它只能证明有限端点投影净相等：

   - SHA 仅覆盖 214 个 `.md`、1 个 `.yaml`、69 个 `.json`；
   - 所谓 stat 实际仅 `path|size|整数秒mtime`，[live-stat-before.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/live-stat-before.txt:1)；
   - 未覆盖其他文件内容 hash、纳秒 mtime、ctime、atime、mode、owner、xattr、ACL、目录元数据、symlink target；
   - 无采集命令、绝对根绑定、采集时间、运行日志或当前引擎 digest；
   - before/after 无法排除窗口中先改后恢复。

   因此 [README.md:17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/README.md:17) 最多支持“所记录投影无最终净差异”，不能支持“不加限定的累计 0 修改”。27/1 候选及 7 处精准重叠的 preview 产物也未封入证据目录或给出 digest，属 **UNVERIFIABLE**。

5. **FAIL — 非法板名拒绝测试可空洞通过**

   [test_split_preview.py:421](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:421) 只断言 `returncode != 0`。即使删除 `validate_board_name`，五个文件名仍会因为目标板不存在而在 [split_preview.py:379](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:379) 非零退出，测试仍绿。它没有钉具体拒绝诊断或零输出。

6. **FAIL — 生成段剥离测试可在剥离逻辑完全失效时继续绿**

   fixture 的 AUTO 段同时会被普通 HTML comment mask 排除；fence 假标题正文不足 60 字；Recent Activity 只有被 `_NON_PLAIN` 排除的列表。[test_split_preview.py:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:68)、[test_split_preview.py:276](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:276)、[test_split_preview.py:331](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:331)。

   静态反事实：把 `strip_generated()` 改成全 `False`，这些剥离测试仍可通过。裁判没有真正锁住核心契约。

### MEDIUM

- **生成段实现仍有语义洞**：普通 HTML 注释中的 `##/###` 没有传给 `sections_of` 的掩码，可截断真实小节或制造注释内假候选；见 [split_preview.py:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:190)、[split_preview.py:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:217)。`derived_names_in` 也不接收 stripped/comment mask，代码 fence 或生成段中的 callout 仍可制造 overlap：[split_preview.py:270](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:270)。

- **“标记对”并不严格配对**：AUTO 闭合只搜索 `/AUTO-GENERATED` 子串；fence 遇到任意 `startswith("```")` 就翻转状态；缺闭合均可吞到 EOF。[split_preview.py:142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:142)。

- **resolve 只有部分等价**：后缀 `_2.._9` 起止完全一致；但 Python 额外做 NFC 和 preview-local `claimed`，[split_preview.py:302](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:302)，TS 仅依赖精确 `existsCheck`，[node-derivation.ts:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/frontend/obsidian-plugin/src/node-derivation.ts:76)。`claimed` 已声明，NFC 未被 README 当作 TS 偏差登记。

- **9+ 差异已声明，但未 fail-closed**：TS throw；preview 确实设置 `conflict_unresolvable` 并在表格标 ⛔，此项披露 **PASS**。[split_preview.py:319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:319)。但它仍把冲突 base 放进 `resolved_name`，继续渲染可执行外观的 wikilink diff：[split_preview.py:565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:565)。测试只断言 boolean flag。

- **默认免责声明字面不实**：默认 out-dir 就是 `<vault>/outputs`，[split_preview.py:592](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:592)、[split_preview.py:607](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:607)，但输出无条件写“未修改任何 vault 文件”：[split_preview.py:49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:49)。准确表述应排除 preview 产物。

- **零写侧测试不是“全树”**：快照只记录 `p.is_file()` 的 bytes 和 mtime；在 vault 内新增空目录、chmod 或 xattr 变化仍可绿。[test_split_preview.py:407](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:407)。

### LOW

- `_BAD_BOARD` 对当前 macOS/POSIX 的直接目录逃逸基本有效：`/`、`\`、`..`、首点、NUL/C0 均拒绝。理论盲区包括长度、DEL/C1、双向/不可见字符、NFC/大小写碰撞；Windows 另有 `:` ADS、尾点/空格等。Unicode 斜线和 `%2f` 不会被 `pathlib` 自动解释为分隔符，不能算实际逃逸。

- 规模门测试只证明保留 5 个且行号递增，没有钉住“恰为最前 5 个”；`candidates[1:6]` 之类的实现仍可能通过。[test_split_preview.py:369](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:369)。

- README 复跑代码先 `cd backend`，下一条仍使用仓库根相对路径；同一 shell 粘贴执行会找不到脚本。[README.md:49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-2-evidence/README.md:49)。

## 指定逐项核对

### 写侧穷举

| 语句 | 结果 |
|---|---|
| [split_preview.py:612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:612) `mkdir(parents=True)` | 创建 out-dir/缺失祖先并改变父目录元数据 |
| [split_preview.py:618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:618) JSON `write_text` | 词法叶子在 out-dir；创建/截断并更新 size/mtime/ctime |
| [split_preview.py:621](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:621) MD `write_text` | 同上 |

未发现其他显式 `open/write/rename/replace/chmod/utime/unlink`。但 `read_text/read_bytes/glob` 在启用 atime/relatime 的文件系统上可能更新访问时间；现有基线不记录 atime。

### slug 逐行等价

| Python ↔ TS | 裁定 |
|---|---|
| 首句 split、`[0]`、`?? selected` | **PASS**；JS `split` 对字符串始终至少返回一个元素，`?? selected` 实际不可达 |
| 分句字符集 | **PASS**：`\n】【。！!？?；;` 相同 |
| 非法字符集 | **PASS**：`\ / : * ? " < > \| # ^ [ ]` 相同 |
| 普通空白折叠、首尾 `-` | 普通输入 PASS；完整 Unicode 字符集 **FAIL** |
| `_hard_cut` 与 `Array.from(...).slice(0,40)` | 合法 Unicode 文本按码点等价 |
| `lastIndexOf`/`rfind` 阈值 | astral 前缀时 **FAIL** |
| fallback | SHA1-anchor 对 timestamp，已明确声明 |
| `_2.._9` | **PASS** |
| NFC、preview `claimed` | Python 扩展语义，不是 TS 函数本体等价 |
| 9+ | TS throw；preview 标记并继续，差异已声明 |

金样本确实双向钉住：

- 历史硬砍值 `Eigenvalues-are-special-vectors-that-sat`：[test_split_preview.py:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:163)；
- 现行值 `Eigenvalues-are-special-vectors-that`：[test_split_preview.py:169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/skills/test_split_preview.py:169)。

所以“双值断言存在”是 **PASS**；但测试没有调用 TS，也没有把 live 文件或其 digest 纳入 oracle，跨语言/历史事实证明力仅 **PARTIAL**。

### 确定性

固定 Python/runtime、冻结输入文件树时，静态结论为 **PASS**：

- 候选和 seed 保持文档序；
- glob 结果进入 set 后，在冲突映射前显式 `sorted`；
- set 只用于 membership/数量；
- dict 均按固定字面插入，`json.dumps` 不接收无序结构；
- 无 locale、time、random；fallback 是 anchor SHA1。

限制：板内容与 SHA、seed 内容与 SHA 分开读取，没有快照/锁；并发修改可形成内部不一致。跨 Python Unicode 数据版本、文件系统规范化和 Windows 文本换行也不保证逐字节一致。

### 裁判与证据状态

- 源码中确有 16 个测试函数：**PASS**。
- “16/16 全绿”：本轮按要求未运行，**UNVERIFIABLE**。
- “先红后绿”：证据包无红态 commit/log，且对象未跟踪，**UNVERIFIABLE**。
- 大多数正向用例走真实 CLI，无 mock：**PASS**。
- 非法板名、生成段剥离：存在明确假绿结构，**FAIL**。
- live 快照有限字段前后相同：**PASS**。
- “live vault 累计窗口 0 修改铁证”：**FAIL**。

因此，当前代码可视为“有用的 preview 原型”，但不能验收为已经证明安全、严格 TS 等价且证据闭环的 CARD-G5-2。


