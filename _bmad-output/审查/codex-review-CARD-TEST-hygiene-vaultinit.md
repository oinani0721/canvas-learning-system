> 批次: BATCH-2026-09-05-第十二批 · 车道 Y6 · 卡 CARD-TEST-hygiene-vaultinit round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `Codex v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-TEST-hygiene-vaultinit.md)"`
> 审查绑定: `2091ee678c4463afe70d4c0f46dcb55b5d2c972a`（本卡唯一代码 commit；其后仅 _bmad-output 变更）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

复核对象为 `2091ee678c4463afe70d4c0f46dcb55b5d2c972a`，对比基线 `03ac8bf8`。全程只读，未运行污染测试。

**没有发现 BLOCKER。定位及相对路径修复有直接证据；共享 `/tmp` 判据存在 HIGH 级可靠性问题，“零回归”和“唯一历史真凶”超出了证据范围。**

1. **HIGH — `/tmp` 无条件报错仍会制造并行假红，归属提示没有解决 `(c)` 与 `(e)` 的冲突。**

   [conftest.py:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/tests/unit/conftest.py:114) 对全机目录名称做差集，随后在第 127 行无条件 `pytest.fail`。只要其他车道在两次快照之间创建匹配目录，本车道就会红。

   错误在于把“报错后提示人工核对归属”当成“判据已经排除了其他写者”。`mtime`、进程 cwd 和 `lsof` 都不能单独证明历史写入归属。

   若必须保留 `/tmp` 硬 fail，验收需要**独立 `/tmp` 环境，或全部潜在写者共同遵守独占运行协议**；仅设置 `TMPDIR` 不会重定向硬编码 `/tmp`。否则应把它定义为环境受干扰、需要重跑，不能直接定为本卡新增回归，也不能直接忽略后放行。

2. **MEDIUM — 定向 H2 足以验证这一条污染链，不能由同型超时推出“零回归”。**

   两轮确实执行了目标 operation，均为 `1 failed, 205 deselected`：[改前日志:4420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/h2-directed-20260906T021827.txt:4420)、[改后日志:4384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/h2-directed-AFTER-20260906T023028.txt:4384)。两份日志第 14 行均显示空串输入；改前第 196 行记录写入 `backend/CLAUDE.md`，改后第 192 行记录返回 422，[收尾状态:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/status-after-h2-after.txt:8) 确认四路径 absent。

   因此，`-k setup` 对**定位和验证已知修复**是合理替换；对全量回归而言，覆盖从 206 缩为 1。相同 `DeadlineExceeded` 不能排除被超时遮蔽的其他差异。[“零回归”论证:123](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/定位结论-a-h2.md:123) 应收紧。

   另有一项独立复算结果：最终两轮红 nodeid 集合相同，但与 H1 相比同为 247 条却有一增一减——[H1:11646](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/unit-run-h1-20260905T164916.txt:11646) 的 candidate 用例与[最终轮:3402](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/judge6-final-raw.txt:3402) 的 warning 用例互换，正文均为 W4 哨兵。**这不能归为本卡回归，但证明同数量不能代替身份比较。**原始外部基线不在允许读取面内，其零 diff 本轮只能核到保存的裁判记录。

3. **MEDIUM — `/tmp` 写入归因成立，但“成对排除干扰”和“唯一历史真凶”的推理不成立。**

   [定位结论-a.md:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/定位结论-a.md:69) 假定并行污染必定成对；观察窗口落在两个测试之间、进程中止或只执行子集，都可以只出现一个目录。

   实际更强的证据是 [bisect-node1.txt:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/bisect-node1.txt:13) 和 [bisect-node2.txt:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/bisect-node2.txt:13)：各自测试捕获的 stdout 直接记录了对应绝对路径的创建。[service:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/app/services/vault_init_service.py:96) 在写成功后才记录该事件，因此可以确认两个 nodeid 各自确实写入，不能排除其他共同写者。

   H1 跑完且收尾干净，支持“该配置下未复现”，不足以排除其他测试集合、fixture 覆盖、顺序或期间写入后被清理的情况。正常的绝对 `tmp_path` 不会仅因 cwd 或 xdist 改变就变成 `backend/`，现有材料也没有证明存在这种触发路径。按你的读取边界，我没有读取被归罪测试的源码，因此“八例全经 `vault_dir(tmp_path)`”仍属于作者的源码审查陈述。

   冻结树同形、同 SHA 支持同一种初始化机制；[service:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/app/services/vault_init_service.py:40) 使用固定模板，所以该 SHA 不是历史调用者的唯一指纹。建议结论为：**台账归因缺乏支持；H2 已实证为能产生该现场的写入链。**

4. **MEDIUM — 校验器正确检查“绝对路径”，但它不是“禁止写入仓库”的守卫。**

   [system.py:448](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/app/api/v1/system.py:448) 与[消费方:466](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/app/api/v1/system.py:466) 使用相同平台的 `Path`，字符串原样返回，解析口径一致。你列出的六种输入均被拒绝，macOS `/private/var/folders/...` 会放行；[新增测试:88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/tests/unit/test_startup_health_check.py:88) 覆盖了这些要求。

   但本 worktree 的 **`backend` 完整绝对路径、该路径加 `/.`、指向仓库的绝对符号链接**，都能通过 `is_absolute()`，最终落在仓库内，且不触发现有黑名单。错误推理是把“语法上绝对”扩大成“解析后的目标安全”。

   另外，本机只读验证显示含 NUL 的绝对字符串也能通过 `is_absolute()`，随后 `resolve()` 抛 `ValueError`；该消费位置没有将其转换为输入错误。这属于校验范围边界，不能把当前实现称为完整路径合法性校验。你记录的 `/tmp → /private/tmp` 黑名单问题也确实存在。

5. **MEDIUM — fixture 是有限的末态增量检查，共用快照函数不能保证无假红、无漏检。**

   [conftest.py:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/tests/unit/conftest.py:54) 至第 97 行确认：新增逻辑不写文件、不导入 `app.*`，通过 `__file__` 定位 backend，前后共用函数。这些主张成立。

   但[第 103 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/tests/unit/conftest.py:103) 只检测顶层路径“不存在→存在”：已有 `raw/` 内新增文件、写后清理、首次 fixture 启动前的污染，均可能漏掉。固定盯 backend 也看不到从仓库根 cwd 写出的根目录骨架。xdist 下各 worker 的 session fixture 没有统一快照边界。

   [第 77 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/tests/unit/conftest.py:77) 将读取失败记为 `None`：`None ↔ hash` 会被报成“文件改写”，两边均 `None` 则通过；`/tmp` 任一侧为 `None` 又直接跳过。**同函数保证检查代码相同，不保证两次可观测性相同。**应区别“内容改变”与“检查无法完成”。

   覆盖注释已经写在[第 34–41 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/backend/tests/unit/conftest.py:34)，不存在漏写问题。只需将“被收集时生效”“立刻变红”收紧为实际 fixture 启动后的观察窗口及 session teardown 报错。

6. **MEDIUM — 负控证明了门独立承重，但保存的证据没有完整覆盖四条判据和恢复链。**

   [negctl-red.txt:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/negctl-red.txt:3) 至第 5 行有专属拒因和 `backend/raw`；第 53 行明确 `1 passed, 1 error`。因此②③④成立，红确实来自这道门的 teardown。正常 pytest 中这种 ERROR 会导致非零退出，不会静默吞掉。

   但允许的证据文本没有 `_probe` 创建记录、变异源码或创建断言，①不能独立核实；红轮也没有保存实际 rc。[negctl-green.txt:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/negctl-green.txt:43) 只有 `1 passed`，没有 nodeid、还原 diff/hash 或 rc，不能完整绑定“同一用例还原后变绿”。

   四条标准足以证明“新建 raw 会触发此门”这个窄结论；补上变异内容、创建断言、两轮确切命令/nodeid/rc 和恢复 hash，才能形成可复算的完整证据链。它们也不自动覆盖 SHA、其他骨架项及 `/tmp` 分支。

7. **MEDIUM — 原地换版加 EXIT trap 降低了风险，但不是无条件恢复保证。**

   换版与 `RESTORE-OK` 只见于[定位结论-a-h2.md:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/定位结论-a-h2.md:48) 至第 56 行；允许的 `.txt` 没有对应原始输出，换版脚本不在本次读取范围。

   `SIGKILL`、机器中断不会执行 EXIT trap；其他进程可能在覆盖窗口导入旧代码，无条件恢复备份也可能覆盖并行编辑。单次恢复 hash 只能证明采样时的内容相同。

   后续取证宜在独立 checkout 固定使用 `03ac8bf8`，保存旧/新文件 hash 与执行记录；可移动的 `HEAD` 不宜作为可重放实验的版本标识。本次没有证据证明已经发生恢复损坏。

8. **LOW — 执行计数断言修掉了本次假绿，但本身不是充分的执行证明。**

   [定位结论-a-h2.md:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-hygiene/定位结论-a-h2.md:43) 的未锚定表达式 `1 (passed|failed|error)` 可以匹配 `11 failed`，且一条 setup error 不代表测试主体执行。

   本次后续有确切 nodeid、实际请求、写入及响应日志，所以重跑有效；第一轮 `rc=4` 被排除也正确。长期应绑定准确 nodeid、执行阶段、数量和退出码。

总评：**定位基本成立**，应去掉唯一历史归因及全面排除 H1 的措辞；**守卫在“拒绝相对路径和空串”这一契约内成立**，已知 H2 污染链的修复有直接证据；**回归门部分成立**，只读、定位和 teardown 承重可信，但共享 `/tmp` 假红、末态检测盲区及负控留证不足，使它目前不能承担“全套件、并行可靠、再次污染必红”的保证。
