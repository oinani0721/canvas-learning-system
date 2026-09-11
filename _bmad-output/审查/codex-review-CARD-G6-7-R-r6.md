> 批次: BATCH-2026-09-07-第十三批 · 车道 U6 · 卡 CARD-G6-7-R round-6
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-7-R-r6.md)"`
> 审查绑定: `756180ec7c4ea08637d3d2964ed5e2579be86d15`（= 最终 HEAD；`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a084db-f8b3-7c41-96de-5fb4431ee36b`
> ⚠ 本轮超出 D-15 的 5 轮上限（第 6 轮）。理由：round-5 已 BLOCKER=0/HIGH=0，收口自查时
>   发现本卡自造的 live backups 越界必须修；本轮生产代码相对 round-5 审查点 `685e5552`
>   **零 diff**，唯一改动是测试文件。Codex 本轮判定「例外理由成立，可以按 BLOCKER／HIGH
>   清零的标准收口」。是否追认这一轮，交主 session 裁定。

---

**本轮可以按 BLOCKER／HIGH 清零的标准收口。** round-6 用于修复本卡造成的 live 写入，例外理由成立；round-5 的 **2 MEDIUM＋1 LOW 登记不修合理，其中没有必须继续留在本卡修复的项**。

审查绑定 `756180ec7c4ea08637d3d2964ed5e2579be86d15`。已重新计算并确认提供的 BASE→HEAD diff 字节一致；相对 `685e5552`，生产代码零差异，唯一代码变更确为测试文件 `+54/−6`。

当前计 **0 BLOCKER、0 HIGH、3 MEDIUM、2 LOW**：保留 round-5 三项，另登记护栏覆盖缺口和一项错误提示措辞。新增项也不构成继续开启修复循环的理由，但护栏不能标为“所有 live 写入均有可靠防护”。

**BLOCKER：无。**

**HIGH：无。**

当前本机、路径身份稳定、生产写者遵守锁协议的调用链中，未找到新的失锁、并发丢账或测试写入 live 业务数据的可达路径。

**MEDIUM**

1. **M3：新增护栏有确定的白名单和扫描范围盲区，只能评为 PARTIAL。**

   位置：[test_daily_review_run.py:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:97)，重点为 `:98、104–111、114–118`。

   白名单完全跳过生产 state、两份日志和 `neo4j`，没有判断写入者。

   **具体失败情形：**测试错误地恢复真实 `BACKUPS` 后调用 `runner.log_line()`，真实 `daily-review.log` 被追加，护栏仍绿。若生产锁文件已经存在，误用生产 vault key 保存 state，也可能只改动被豁免的 state，护栏仍绿。这些反例不需要苛刻的并发时序，但**当前测试中没有找到这样的误配路径**。

   此外，它只检查 backups 顶层；子目录内文件的原地改写、live vault、outputs、learning_events 均不在完整覆盖面内。两次采样间创建后删除、保持大小并恢复 mtime 的改写也可能漏报。它在写入之后报警，不能阻止首次污染。

2. **M1：时间门仍不能证明子进程真正取得了排他锁，保留 round-5 结论。**

   位置：[test_daily_review_run.py:1378](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1378)、`:1420–1425`。

   **具体失败情形：**把生产取锁改成“非阻塞尝试失败→等待约 1.6 秒→不重试直接继续”，仍可能满足父进程约 1.5 秒释放后的时间判据。改成 `LOCK_SH` 也可能通过现有排他探测。

   **当前生产触发前提：必须先改坏现有 `LOCK_EX` 实现。** 普通并发本身不会使当前代码出现这个错误。

3. **M2：隔离门的 ready 握手仍未确定真正取锁与隔离的先后顺序，保留 round-5 结论。**

   位置：[test_daily_review_run.py:1613](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_daily_review_run.py:1613)、`:1788–1792`。

   **具体失败情形：**先撤掉生产 `load_state` 外层锁；子进程写出 ready 后、实际取锁前被抢占；父进程先隔离，子进程随后取得锁并写账，缺锁变体仍可绿。

   **当前生产触发前提：必须先撤掉当前正确的外层锁。** 这是测试判别力债，不能描述为当前生产丢账。

**LOW**

1. **L1：同 inode 拒绝报文仍使用过时的失锁原因，保留 round-5 结论。**

   位置：[daily_review_run.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:307)。

   **具体失败情形：**外部把 state 设置成指向锁文件的软链，触发同 inode 检查；拒绝行为正确，但报文仍声称一次普通 close 会释放锁。当前已使用原生 `flock`，该解释不成立。需要异常文件布局才显露，影响排障，不影响正确拒绝。

2. **L2：保存失败提示容易被理解为整个操作没有动盘。**

   位置：[review_overview.py:2298](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:2298)、`:2395`。

   **具体失败情形：**`load_state` 已成功隔离损坏 state，随后保存因 `ENOSPC` 等错误失败，响应仍称“未写出任何内容”；此时活动 state 已被移走，锁也可能已经创建。其附近“state 逐字节不动”的解释同样过宽。

   这是既有错误路径的措辞问题，可登记后续处理；不表示临时 JSON 被半截发布。

你特别提出的三个问题，结论如下：

- **mtime：本机够用于发现普通重复写回归，没有整秒粒度问题。** 已只读核实所在卷为 APFS，代码使用整数 `st_mtime_ns`；现存 metadata 也有亚秒部分。APFS 支持纳秒时间戳，但这不意味着每次写入都必然得到唯一时间戳，更不能替代内容或写操作审计。[Apple 格式说明](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/APFS_Guide/VolumeFormatComparison/VolumeFormatComparison.html)、[Python stat 说明](https://docs.python.org/3/library/os.html#os.stat_result.st_mtime_ns)
- **两处 `undo()` 污染链已切断。** `:1581–1583` 和 `:1797–1799` 的独立 `MonkeyPatch.context()` 只恢复自己的 `Path.read_text` 补丁，保留 `_patch_runner` 的 `VAULT/BACKUPS`。父进程写路径进入 tmp；相关子进程均传 `CANVAS_REPO=tmp_path`；Web 写侧通过 `board_done_env`。未找到第三条现存的 live state／vault 业务数据逃逸路径。
- **不能扩大成“四文件测试绝不写真实仓库”。** 普通 pytest 的字节码、缓存取决于启动参数；另有既有公共导入路径：[bug_tracker.py:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/bug_tracker.py:98) 会在默认 `data/` 不存在时创建它，发生在 fixture 之前。当前该目录已存在，用例期异常日志则已重定向到 session tmp。这些不属于本卡新增的 live 业务数据污染。

十项独立复核：

| 问题 | 结论 |
|---|---|
| **1．tmp 四项保证** | **保留。** 唯一名、`O_EXCL\|O_NOFOLLOW`、异常尝试 unlink、同目录 `os.replace` 均在；独立 tmp 的 open/close 不释放当前原生 `flock`。unlink 自身失败或强杀仍可能留残渣；原子发布不等于断电持久性。 |
| **2．合并与 base** | **当前生产调用链成立。** 题面自述过期：base 实际在归一化**之后**深拷贝；缺文件、隔离重建记录默认 base；版本单调取大。base 缺席或磁盘缺失／无法解析时整写 mine。按路径存最近 load 的快照确有通用 API 局限，但 Web 同库 load→save 全程持锁、GET 不更新 base、runner 独立进程，阻断了题述覆盖时序。合并仍按顶层键处理，不是通用事务。 |
| **3．时间门和对照组** | **PARTIAL。** 对照的返回码、取锁耗时和落盘内容确实承重，排除子进程根本没完成；但不能证明持锁组实际取得排他锁，见 M1。 |
| **4．refresh 是否写 state** | **不写。** `_refresh_state_file` 只派生路径；pick 对 `--state` 只读取、解析一次，取两个账本，不调用 runner 隔离／保存。持久输出仍是两份投影，另有目录与临时件操作。 |
| **5．撤销三门及幂等** | **真实复用。** 三个 helper 均唯一定义并复用。`already_undone` 区分“删了一条／原本缺键”，不能区分拼错、从未完成、重复撤销，符合明确选择的幂等语义。“不落盘”须限定为正常 state 缺键时不保存；首次建锁和损坏隔离仍可能发生。 |
| **6．自动 POST** | **未发现。** 三处 POST 均在点击处理器；轮询与 `visibilitychange` 只进入 GET。 |
| **7．升版行为门** | **有效。** `:1944` 直接 `save_state(load_state())`，测试没有中途补键；后续检查版本、原值及准确键集。另两门分别证明字节幂等、隔离保留原字节，单独不证明升版。 |
| **8．三项写面允许集** | **有意增加一个空锁对象，没有放开其他路径。** `:2931` 仍是全树差集严格相等，`:2934` 抓非零锁内容，锁移入 vault 会被路径差集及 `:2935` 抓住。`_tree`、另外三个既有调用用例经 BASE→HEAD 原文比对均未改变。证明范围仍是终态，不能检测写后恢复。 |
| **9．重入登记与探测** | **稳定路径、正常异常下成立。** 同线程只加深度；save 复用 fd；其他线程串行；多层嵌套正常回收。探测两半分别证明持锁时冲突、退出后释放，但不能单独区分共享锁／排他锁，见 M1。 |
| **10．自调用及异常** | **稳定路径下最多额外一层。** 成功登记后第二次持锁判断为真，普通读写异常会退出上下文。极端边界是外部强关专用 fd，使 `LOCK_UN/close` 自身抛错，可能跳过末尾 `tlock.release()`；当前调用链没有这种 fd 所有权破坏路径。 |

另需保留证据限制：[负控日志:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/_bmad-output/审查/evidence-g67r/neg-live-guard-20260909T142543.txt:6)确实显示同名 live 测试 state 改动后护栏报错，日志中的测试文件 hash 与当前文件一致；**这证明事后检测有效，也意味着该负控再次发生了 live 写入。** [收工记录:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/_bmad-output/审查/evidence-g67r/live-readonly-final-20260909T141943.txt:5)明确说开工 hash 没有独立存档，因此“生产内容全程未被动过”不能独立评为 PASS。污染物继续留待人工处置合理。

本轮未修改文件、未连接数据库、未运行会落盘的 pytest。实际完成六组合并输入验证、只读 fd 的原生锁实验，以及撤销相关 **6 个 Node 子用例，全部通过**；存档中的 `324 passed` 是既有运行证据，不是本轮重跑结果。


