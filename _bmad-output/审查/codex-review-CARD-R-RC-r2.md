> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p10-docs · 卡 CARD-R-RC round-2 prompt-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-R-RC-r2.md)"`
> 审查绑定: `ef8ace4a73b346790672a61e5308458fbfbcec4f..920ae5b7b12c02691ccaed3c6897149795553e76`
> ⛔ 该绑定**不是**最终 HEAD: 本轮结论促成了进一步整改, 最终代码 SHA 为 `5abcff162de43153d71c2dde84a0226a040918e2`。绑最终 HEAD 的 round-3 因 codex 配额耗尽（`usage limit`，提示 2026-09-23 恢复）无法完成, 两次调用存档均 0 字节且未入库。按协议 §四交主 session 人审替代。
> 会话头自证（抄 `.stderr`, 括注行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: gpt-6-astra` / `(L9) reasoning effort: ultra`

---

**结论：BLOCKER 0；HIGH 1。当前不宜认定本轮全部整改完成。** 新的同 SHA 扫描引入了畸形旧件导致冻结崩溃的路径；新增 J02 使一条旧断言发生假绿；包含性检查仍存在可越界写入的竞态。

本轮只读指定范围，未运行会落盘的 pytest 或负控重放。以下区分源码推演与已有运行记录；畸形 `candidate` 的异常另用原始 AST 语句在内存中确认。现场 HEAD 是 `920ae5b7…`，三个文件与该提交一致；指定九件证据存在，但尚未被 Git 跟踪，未见所述后续证据提交。

**HIGH**

1. **包含性检查通过后，仍可借软链把产物写到 out-root 外，甚至覆盖已有回执。**  
   定位：[freeze_release_candidate.py:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:399)，以及 `:419/:445/:503`。

   包含性、落点不存在和判重检查，都在校验器 subprocess **之前**；写入时没有绑定已检查的目录。

   **复现思路／未被拦下的输入：** out-root 位于代码树外；检查时 `rc_dir` 不存在；校验器运行期间，另一进程创建 `rc_dir → 外部目录 X`，且 `X/journeys` 不存在。代码树保持干净，写前复核通过；随后 `mkdir` 跟随父目录软链，在 X 创建骨架，`write_text` 写入或截断 X 中已有的 `rc-manifest.json`。这是静态明确可达的路径，本轮未执行落盘复现。

**MEDIUM**

2. **写前复核仍不能保证 SHA 与锁摘要属于同一快照；N4 没有验证复核行为。**  
   定位：[freeze_release_candidate.py:377](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:377)，以及 `:240/:432/:438/:440/:479`；[test_freeze_release_candidate.py:878](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_freeze_release_candidate.py:878)。

   **复现思路／负控输入：** 首次 status 干净后临时修改锁文件，让采集读到修改后的字节，再在末次 status 前恢复。两次 HEAD/status 均通过，回执却保存不属于候选 SHA 的锁摘要。

   剩余窗口没有可由源码保证的毫秒上限；进程调度、文件读取和 subprocess 都可能延长它。最后一次 HEAD 与 status 也不是原子操作。`rechecked_before_write=true` 只能自陈执行到该位置。

   更直接的测试负控是：删除 `:432–439`，保留 `:440`。32 条测试没有中途变更输入，恒真字段仍可满足 N4 对应裁判。

3. **同 SHA 判重对不可读旧件放行，也没有并发排他。**  
   定位：[freeze_release_candidate.py:311](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:311)，尤其 `:318–320/:411`；[README.md:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/README.md:68)。

   **复现思路／对照输入：** 正常同 SHA 旧件会拒绝；将旧件设为不可读或截断 JSON，再换 rc 名，扫描直接 `continue`。注释所说“由 check 报”没有后续调用保证，真实校验器 `--all` 又不扫描 `rc-manifest.json`。

   另一个**门未覆盖的路径**是两个进程同时扫描同一 out-root、同一 SHA、不同 rc 名：均可在任何回执落盘前通过判重。因此 README 的机械保证目前只适用于可读旧件及串行执行。

4. **合法点开头 rc 名仍会让 cwd 压过显式 out-root。**  
   定位：[freeze_release_candidate.py:560](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:560)，以及 `:389/:571–573`。

   `freeze --rc-name .rc` 合法，但 `check .rc --out-root …` 把 `.rc` 当 cwd 路径。

   **复现思路／未被拦下的输入：** cwd 与 out-root 各放不同 SHA 的 `.rc`，执行上述 check，会检查 cwd 那份；成功行仅显示名字。**对照输入** `rc-a` 则正确选择 out-root。名字与路径的取值域仍未统一。

5. **非 dict 修复遗漏两个入口；非法编码也会让 check 崩溃。**  
   定位：[freeze_release_candidate.py:320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:320)、[:598](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:598)，以及 `:585–587/:616–619`。

   **复现思路／未被拦下的输入：** 将 RC 回执的 `candidate` 设为 `"x"`、`[1]` 或 `true`，分别触发同 SHA 扫描和 check 的未捕获 `AttributeError`。其中扫描入口是本轮新增的失败面。

   RC 或 journey JSON 含非法 UTF-8 字节时，`UnicodeDecodeError` 也不在现有捕获范围内，后续 journey 比对会中断。

6. **`--ignore-submodules=none` 解决了子模块忽略配置，不能排除其他 Git 配置漏报。**  
   定位：[freeze_release_candidate.py:146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:146)。

   **复现思路／负控输入：** 在临时真仓中提交普通文件，仅改变其可执行位，并配置 `core.fileMode=false`；当前 status 参数不会报告这项 mode 改动，仍可冻结。**对照输入**为 `core.fileMode=true`。

   这是已跟踪文件元数据的变化，不属于当前列出的忽略文件、索引标记或仓外状态 caveat。该 flag 足以覆盖所述子模块配置，不能支撑更广的配置无关保证。

7. **环境错误的分档整改仍不完整。**  
   定位：[freeze_release_candidate.py:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/freeze_release_candidate.py:240)，以及 `:118–126/:291–297/:520–522`。

   **复现思路／未被拦下的输入：** 锁文件存在但不可读，使 `read_bytes()` 抛 `PermissionError`；它不会转成 `_Env`，仍是 traceback、rc=1。启动 Git/校验器的其他 `OSError`、读取 schema 摘要的错误也有同类遗漏。浅层路径如 `/tmp/v.py` 还会使 `validator.resolve().parents[2]` 抛 `IndexError`。

8. **新增 validator 替身确实是 stub，“零打桩”声明不成立。**  
   定位：[test_freeze_release_candidate.py:757](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_freeze_release_candidate.py:757)，以及 `:14–16/:764–767`。

   **对照输入：** 任意参数、任意证据内容，替身都只打印固定文字并返回预设退出码。真实文件、真实 subprocess、正式 `--validator` 接口，都不改变它是进程级测试替身的性质。

   **按本轮给出的“禁 mock／禁止假 API”约束，我判为不符合。** 它能测试包装脚本的分档和拒绝行为，但不能称为真实校验器验证。既有校验器测试使用合成输入后运行真实实现，和替换实现不同。

**LOW：裁判仍存在“取名面小于主张”**

| 定位 | 问题与复现思路 |
|---|---|
| [test_freeze_release_candidate.py:515](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_freeze_release_candidate.py:515) | **这是本轮新增的第四处假绿。** `:505` 已加入在场 J02，后面仍把 J02…J10 当“缺失”搜索整个 stdout；J02 的成功行满足了断言。**负控输入：** 缺失清单错误加入 J02，测试仍可通过。 |
| [test_freeze_release_candidate.py:849](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_freeze_release_candidate.py:849) | 自陈测试只找“未验”和“schema”。**负控输入：** 删除 symlink、完整性两项说明，测试仍绿。 |
| [test_freeze_release_candidate.py:881](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_freeze_release_candidate.py:881) | N5 只测普通主仓及普通 linked worktree。**负控输入：** 恢复 `git_common_dir.parent`，同时保留来源字符串 `"worktree-list"`，两种输入仍通过。没有覆盖其声称修复的特殊拓扑。 |
| [test_freeze_release_candidate.py:405](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_freeze_release_candidate.py:405) | vault 字节对比排除 `.git/`；普通 `git status` 又未抑制 optional locks，可能刷新 index。**门未覆盖的路径：** Git 元数据变化。因此只能证明所比较的普通文件不变。 |
| [test_freeze_release_candidate.py:626](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_freeze_release_candidate.py:626) | 选项全集只约束新增选项名。**负控输入：** 用新环境变量，或既有选项的特殊值，同时跳过两道 dirty 门，集合不变。当前代码未发现这种旁路，但测试不能证明其不存在。另 `:438` 的缺锁测试只删除第二份锁，第一份缺失也是未覆盖输入。 |

**12 段负控的核对结果**

以下行号来自指定的 `negctl-battery-8fe7f228-20260919T002007.txt`：

| 段／行号 | 独立判断 |
|---|---|
| N1／6 | 失败节点吻合；没有断言栈，不能确定红在空白门、XOR 还是输出断言。 |
| N2／12 | 节点吻合；当前测试能识别所述 `.`／`..` 逃逸。 |
| N3／18 | 节点吻合；包含异 SHA 对照输入，能区分“同 SHA 禁止”与“一律禁止第二次”。 |
| N4／24 | **不能证明复核行为**；恒真字段就是可单独满足的判据。 |
| N5／30 | **不能证明修复了特殊拓扑**；可能仅来源字符串变化导致红。 |
| N6／36 | 普通名字的 cwd 诱饵对照有效，但没有 `.rc`。 |
| N7／42 | journey 类型保护判据有效，包含无 traceback 和继续报告 J02；没有 RC 自身入口。 |
| N8／48 | 只锁住部分自陈文字。 |
| N9／54 | 对预设返回 1 的替身，拒绝标记、输出和零骨架都有断言；受上述 stub 判断限制。 |
| N10／60 | 初测一红、复测两红能相互解释，见下文。 |
| N11／66 | 一致 J02＋不一致 J01 能识别“至少一份一致即可”；同时引入上述缺失清单假绿。 |
| N12／72 | 测试确实逐份重算锁摘要和长度；日志未留下具体失败断言。 |

**所有段落均缺少具体变异 diff 和失败断言栈。** `n=1` 与一个失败节点不足以独立认证“只拆一层，且红在目标断言”。

N10 两份记录可以合并使用：最终脚本摘要与记录一致，相关测试改动是 dirty 断言加固。若负控是主门恒判干净，旧 tracked 用例可被 caveat 中的裸 `dirty` 和末尾拒绝满足；旧 untracked 还有文件名断言，所以只红一条。最终两条都要求主门专有的 `dirty tree` 和文件名，后置复核无法满足；复测也列出了正确的两个失败节点。**主门现在不会再被后置复核掩盖。**

其余问题的结论如下：

- **拒绝路径零写入：** 所有显式内容拒绝门都在首次 `mkdir` 前；新增包含性和同 SHA 门位置正确。读取旧回执不是产物写入。但这只能支持“拒绝前不创建 RC 产物”，不能扩大成任何 Git 元数据都不写；HIGH 项则是未被拒绝的越界成功路径。
- **包含性：** 静态的 `.`、`..`、指向外部的既有软链会被拒绝。大小写不敏感文件系统上的既有同名别名通常由 `exists()` 拒绝，未发现额外静态逃逸；竞态仍成立。
- **索引参数：** 空串、纯空白与双方同时提供的整改有效。`index_sha` 的指定 schema 只要求非空字符串，不要求 hex；不能把非 hex 值另判非法。
- **check 职责：** 当前成功自陈与实际边界基本一致：没有验 journey schema、symlink 或完整性。它只做有限回执检查，不能将“自洽”理解成所有回执元数据均已验证。
- **main_root：** fallback 在 worktree-list 非零或未找到 `worktree ` 行时执行，并吞掉该失败继续推算。非 `-z` 输出再 `splitlines()` 也留下特殊字符路径边界；现有测试和指定证据不足以认证 separate-git-dir、submodule、bare 全部正确。
- **README：** 证据提交不改回执 SHA、执行树须 checkout 候选 SHA，以及 `candidate.worktree` 填实际旅程树，这三项说明中的后两类关系是正确的；“按 SHA 机械判”须受第 3 项限制。部署数量和挂载来源不在允许核验面内，未替它们背书。
- **真 Git 依赖：** 仓夹具确实运行 `git init/add/commit`，普通冻结路径确实运行真实脚本和默认校验器；不能说每条测试都真调校验器。指定成功证据只证明树外冻结、`--all=0` 和零 journey 的 check，不证明同树完整性路径或真实旅程绑定验收。
