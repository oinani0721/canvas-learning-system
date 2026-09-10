> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7a round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7a-r3.md)"`
> 审查绑定: `725bbd19`（送审 HEAD；审查者自证「结束时四个受审文件仍与该提交一致」）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

> **D-15 达标点**：本轮 **BLOCKER = 0 / HIGH = 0** 且绑最终 HEAD ⇒ 协议 §1 的多轮终止条件满足。
> 3 MEDIUM / 5 LOW 按协议登记不阻断；其中 MEDIUM-1 是 round-2 修法引入的**新误报**、
> LOW-1/2/3 是本卡新门被审查者变异实测**存活**（门的证明能力不足）—— 见 round-4 处置。

---

本轮结果：**0 BLOCKER / 0 HIGH / 3 MEDIUM / 5 LOW**。绑定 `725bbd19e0fc15a349fe60e884cd08a1e6b64e40`，结束时四个受审文件仍与该提交一致。

未执行安装脚本、安装片段或整套测试文件；动态证据来自自动清理的临时夹具，门的变异仅在内存运行纯文本检查。

- **MEDIUM-1：`-H` 新修法与摘要语义不一致，正确复制也会报 content-drift。**  
  位置：[install-vault.sh:108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/install-vault.sh:108)、[verify_vault_install.py:740](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:740)。源操作数软链按链接文本摘要，目标实体目录按内容摘要。  
  **复现已完成：**源插件目录指向共享目录，独立执行 `cp -R -H` 后目标字节完全一致，但校验器仍报插件目录 drift、`rc=2`；`.claude` 操作数软链同理。这是 round-2 修法新增的误报。

- **MEDIUM-2：generate 指向不可读普通文件的软链，仍会进入 match。**  
  位置：[verify_vault_install.py:1035](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1035)、[verify_vault_install.py:696](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:696)。`_leaf_digest` 只读取链接原文，返回 `probe_bad=False`；`is_file()` 只确认目标类型。  
  **复现已完成：**生成件链接到 `chmod 000` 的普通文件，真实读取抛 `PermissionError`，校验器却输出 `match`、`unreadable=[]`、`rc=0`。当前最终记 match 的行是 **1103**，1097 已是 drift 分支的 `continue`。

- **MEDIUM-3：key 自检仍把 `cmp` 的运行时读取错误当成通过。**  
  位置：[install-vault.sh:194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/install-vault.sh:194)。`-f && -r` 预检不能保证随后打开、读取成功，而 `! cmp` 仍合并了返回码 1 与 2。  
  **复现已完成：**两份普通且可读的文件，仅将独立 `cmp` 子进程的 `RLIMIT_NOFILE` 限为 4，真实 `cmp` 返回 2；现有取反表达式会将其视为成功。另 [test_vault_install_manifest.py:2458](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2458) 还强制要求 `! cmp -s` 字面量，会妨碍改为准确区分返回码。

- **LOW-1：清理联动门不能证明每个 generate 位都被清理。**  
  位置：[test_vault_install_manifest.py:2703](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2703)。它比较的是“删除路径 ∪ 变量赋值路径”。  
  **变异实测存活：**只删除 templater 的 `rm` 操作数，保留 `TEMPLATER_DATA=`，该门仍通过；随后存在性守卫会保留旧配置。当前清理项齐全，缺陷在门的证明能力。

- **LOW-2：递归复制结构门没有真正区分可执行参数与行尾注释。**  
  位置：[test_vault_install_manifest.py:2740](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2740)。它只跳过整行注释，仍检查整行子串。  
  **变异实测存活：**移除 `.claude` 复制命令的 `-H`，在行尾保留 `# cp -R -H required`，结构门仍通过；现有行为门只检查核心插件。`cp -PR` 等参数重排也能避开该文本检查。

- **LOW-3：origin 门仍能放过错数组与错误区间，唯一锚也会被注释触发假红。**  
  位置：[test_vault_install_manifest.py:227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:227)、[test_vault_install_manifest.py:2557](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2557)。  
  **变异实测：**把 `.claude/skills` origin 从 72 改为其他数组的 73，或把生成区间缩成 `134-135`，门仍通过；仅增加 `# pending_archives documentation` 则因双命中报红。前两例漏检，后一例是假红。

- **LOW-4：generate 可读性探测新增与文件大小成正比的整文件内存、读取及哈希开销。**  
  位置：[verify_vault_install.py:704](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:704)、[verify_vault_install.py:1035](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1035)。摘要计算后没有使用。  
  **复现已完成：**16 MiB 稀疏生成文件触发约 16 MiB Python 分配峰值；未做 OOM 压测。后面的 match 不会再读取一次。

- **LOW-5：校验器文案仍把 optional 的内容保证写得过宽。**  
  位置：[verify_vault_install.py:50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:50)、[verify_vault_install.py:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:134)。仍笼统声称“不放松内容对不对”，没有像 manifest 一样限定 copy。  
  **复现思路：**放置任意内容的可读 generate 文件，它仍可 match。此外，“缺省 harness 源”应明确属于安装器；校验器未给 `--source` 时实际不评 drift。

其余问题的核对结论：

- **当前生成路径的内部软链写穿：核对结果：无问题。** 操作数目录由 `-H` 实体化；两个 `data.json` 都是其直接子项，叶软链由 `rm -f` 删除。临时夹具分别链接外部文件、外部目录，两种目标字节均未改变。内部子目录链不是当前生成路径的祖先；`find` 未带 `-L`。结论限当前路径集合及无并发替换。
- **内部软链摘要：只证明链接原文相同。** 已实证相同的 `../payload` 在目标侧悬空、或解析到不同字节，父目录仍 match。这是 `_leaf_digest` 已声明的既有语义，不能据此宣称链接可用或实际读取内容一致。
- **稳定 FIFO：核对结果：无问题。** `lstat` 先识别类型，不会进入 `read_bytes()`；真实 FIFO 夹具立即归入 unreadable、`rc=2`，没有阻塞。
- **47 条重写 origin：核对结果：无问题。** 已逐项／逐组核对脚本对应关系；当前门的不足见 LOW-3。另三条引用卡文的 origin 不在本轮可核实范围。说明性文字仍有旧行号，例如 manifest 的数组区 `73-77`、key 自检 `187`。
- **`wiki/**` 还会扩大 unreadable 桶。** 同一个不可列举的 `wiki/concepts`，仅有 skeleton 时 `rc=0`；加入 exclude 后新增 unreadable、`rc=2`，原 skeleton match 仍保留。正常可读 wiki 内容不会改变 extra、allowed-extra 或 content-drift，因为 wiki 不在对应扫描／copy 面。
- **树自洽门还未断言 match、allowed-extra、hotkeys_note。** intentionally-excluded 之外还有这些覆盖边界；hotkey-orphan 已由 `exit_code == 0` 间接约束。未断言不等于已经发生错误变化。


