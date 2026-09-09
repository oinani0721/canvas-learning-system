> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7a round-5（轮次上限）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7a-r5.md)"`
> 审查绑定: `7cb2d93e`（审查者自证四文件与该提交逐字一致；本机 `git diff --stat 7cb2d93e HEAD -- . ':(exclude)_bmad-output'` 为空）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

> ✅ **D-15 终止条件满足**：绑最终 HEAD 的一轮 **BLOCKER = 0 / HIGH = 0**（r3/r4/r5 连续三轮）。
> 本轮 3 MEDIUM / 8 LOW 按协议 §1 登记不阻断；轮次已用满 5，**不再送审**，全部转下一卡。

---

绑定 **`7cb2d93e`：0 BLOCKER / 0 HIGH / 3 MEDIUM / 8 LOW**。四个文件的工作区内容均与该提交逐字一致。

仅做只读分析、内存 AST 执行及断言重放；下文“存活”只指注明的门，**不代表整套测试存活**。

**BLOCKER / HIGH**

核对结果：无问题。限定于本轮读取面及上述验证程度。

**MEDIUM**

1. **树自洽门与 `follow_root` 的非对称语义冲突，会误拦合法模板根链。** [test_vault_install_manifest.py:2574](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2574) 将同树作为两侧，而校验器仅解引用源侧。复现：模板的 dataview 根项链接到空目录，执行同树自比，源侧目录摘要与目标侧链接摘要不同，报 drift；已核对分支及内存摘要，**未证明当前模板树存在这种形态**。

2. **hotkeys 读取前移后，缺少 `main.js` 也可能因特殊文件形态挂起。** [verify_vault_install.py:1277](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1277) 未检查普通文件形态便调用 `read_text()`。复现：hotkeys.json 为无写端 FIFO、main.js 缺失，会阻塞在打开阶段，不能返回 unreadable/rc=2；这是静态确认，未创建或打开 FIFO。

3. **`main.js` 已存在但为目录时，形态错误仍被豁免退出码。** [verify_vault_install.py:1306](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1306)。复现：合法 hotkeys 对象绑定不存在的命令、main.js 为目录，原函数内存执行得到 `unreadable=[] / orphan=[] / rc=0`，只有“不是普通文件”的提示；这是既有缺口，并非 r5 新增。

**LOW**

1. **零写门仍漏掉写调用，行为快照也看不见权限修改。** [test_vault_install_manifest.py:744](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:744)。变异：`os.open(path=path, flags=os.O_WRONLY | os.O_TRUNC)`、`open(path, **{"mode":"wb"})` 均通过 AST 门；在 `fh.read(1)` 后加入 `os.fchmod(fh.fileno(), 0o600)` 也通过，而 `_tree_digest` 不记录权限——未实际执行这些写操作。

2. **数组唯一定义门仍漏掉缩进的重复赋值。** [test_vault_install_manifest.py:2940](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2940)。变异：将安装器第 84 行空行改为 `    CLAUDE_ITEMS=(skills)`，实际数组被缩减，但七个结构/归属门全部 PASS。

3. **清理集合门仍把后续命令的参数当作 rm 操作数。** [test_vault_install_manifest.py:2778](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2778)。变异：第 142 行只保留续行反斜杠，第 143 行追加 `; : "$TARGET/.obsidian/plugins/templater-obsidian/data.json"`，templater 已不被 rm 清理，七门仍全部 PASS。

4. **cp 结构门只检查每行第一个 cp。** [test_vault_install_manifest.py:2827](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2827)。变异：安装器第 89 行追加 `; cp -R "$SOURCE/.claude/$item" "$TARGET/extra-copy"`，第二个复制点缺少 `-H`，七门仍全部 PASS。

5. **`_sh_line(kind="code")` 仍只能证明文本出现，不能证明对应操作存在。** [test_vault_install_manifest.py:2611](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2611)。变异：将安装器第 96 行改为 `: '<原 rm 整行>'`，清理变成无操作，锚仍返回 96，七门全部 PASS。

6. **树自洽门没有验证已检查项目的完整覆盖或 hotkeys 检查状态。** [test_vault_install_manifest.py:2575](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2575)。复现：原断言重放中，`match=[]`、hotkeys 保持“未检查”，只要阻断桶为空且 optional-missing 集合相等仍 PASS；但全局删除 hotkeys 调用或清空 match，会被其他现有门拦住。

7. **源码 hotkeys 门仍不能独立验证顶层对象形态。** [test_vault_install_manifest.py:1485](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1485)。变异：提供十个内存命令 ID，把 hotkeys 改成包含有效 CLS 键的 JSON 字符串数组，原测试函数 PASS；当前生产类型检查会拒绝，因此已不再是“两层同时放行”。

8. **报告没有传达源码已经收窄的两项证据边界。** [verify_vault_install.py:1367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1367)。复现思路：源根链指向树外且复制内容一致，或生成件首读成功但后续读取失败，报告无法显示解引用来源或“只做首读探测”；建议把这两条边界带进报告。

针对你的其余问题：

- **Q1：`follow_root` 的复制等价判断，核对结果：无问题。** 源根链指向树外或另一 vault 时，会读取解引用位置，按原 item 路径比较过滤后的内容；相同可以 match，现有源链夹具已经明确支持树外 `shared`。它**不证明来源归属、Git 追踪身份或跨 vault 隔离**。新增问题是上面的同树自比误伤与报告披露不足。
- **Q2：按已收窄契约，核对结果：无问题。** 第 724–727 行已经准确声明首个 `read(1)` 不抛、允许空文件、不保证后续可读及祖先无链；无需为这个契约强制整件哈希。
- **Q3：当前 owner 分类，核对结果：无问题。** 实际覆盖 **30/30**，被 `None` 跳过的 copy/skeleton 集合为空；`checked == 30` 需与集合等价门的总数 30 联合成立。另外，深层 `.obsidian/plugins/...` 实际回退到 `OBSIDIAN_FILES`，并非 `None`。
- **Q5：旧“优先/回退”问题，核对结果：无问题。** 当前版本确已取消回退；剩余歧义见 LOW-5。
- **r4 hotkeys 顶层非对象整改，核对结果：无问题。** 生产自校验确在 main.js 缺失分支之前；`path.open("wb+")` 对照变异也已被正确杀死。

W4 的 12/173 哨兵归属说明不在限定读取面内，本轮未独立验证。


