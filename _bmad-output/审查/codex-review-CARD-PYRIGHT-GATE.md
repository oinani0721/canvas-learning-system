> 批次: BATCH-2026-09-11-第十四批 · 车道 T8-G · 卡 CARD-PYRIGHT-GATE round-1（本卡零代码 ⇒ 1 轮即末轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-GATE.md)"`
> 审查绑定: `96dc3c496dddfcc603e692e27492a3248f8ab655`（= 本卡最终 HEAD，代码面 diff 为空）。绑定核见验收单 §6.2。
> 会话头自证（抄自 `.stderr`，**括注行号**；`.stderr` 本身不入库，已被 `.gitignore` 覆盖）:
> L2 `OpenAI Codex v0.153.3` / L5 `model: gpt-6-astra` / L9 `reasoning effort: ultra`

---

**计数：BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 1。**

绑定 SHA 已核实：`96dc3c496dddfcc603e692e27492a3248f8ab655`。未发现已证实的假绿，但配置读取的证明仍不完整。

**BLOCKER：无。HIGH：无。**

1. **MEDIUM — [UAT:83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/验收单/UAT-CARD-PYRIGHT-GATE-2026-09-17.md:83)**  
   **问题：**绝对路径、`test -x` 和正负探针不能证明根配置实际加载及有效检查范围，因此还不能排除第三种假绿；这属于证据缺口，不能反推配置实际未读取。  
   **独立确认：**对照 UAT 第 37、83、129 行与 `gate-pyright` 第 1–16 行，只有命令口径、摘要和探针结果，没有配置加载记录；重复得到相同摘要不能替代这项证明。

2. **MEDIUM — [protocol-2.3-close.patch:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-pyright-gate/protocol-2.3-close.patch:14)**  
   **问题：**“恢复硬禁”与仅点名“改动行”的禁令范围不一致，留下了“被检查文件的未改动处仍有既有漂移”这一输入的处置歧义。  
   **独立确认：**比较 patch 第 13–14 行：旧豁免明确针对“不在本卡改动行”的漂移，新句没有明确处理该对象，同时保留 D-40；UAT 第 81 行也承认未验证两者并存的边界。

3. **MEDIUM — [UAT:131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/验收单/UAT-CARD-PYRIGHT-GATE-2026-09-17.md:131)**  
   **问题：**备查探针未保存 Pyright 的退出码，也未显式设置 `pipefail`，默认 zsh 下末尾 `grep` 成功会使坏探针管道返回 0，无法据此复现标注的 `rc=1`。  
   **独立确认：**比较第 129 行的 `$pipestatus[1]` 与第 131–132 行的缺失，再对照 `gate-pyright` 第 11–16 行；这是复验命令不完整，不能据此认定历史日志造假。

4. **LOW — [UAT:55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/验收单/UAT-CARD-PYRIGHT-GATE-2026-09-17.md:55)**  
   **问题：**“往后任何一处对不上，都是这次改动带来的”错误地把取消豁免写成消除了既有漂移。  
   **独立确认：**与同文件第 81、110 行对照，既有漂移仍保留且 format 尚未执行，后续报红不能自动归因为后续提交新增。

其余问题的核对结论：

- **⓪ 工具与目标树有支持证据。**备查命令明确进入本树 `backend/`，warning 明细包含本树路径；我另核实了 `e45…` 与绑定 SHA 的 `backend/app` 树对象、根配置对象均相同。剩余缺口是运行时配置绑定，不能把它说成已经确认的错误配置。
- **① 当前 patch 没有越界。**独立逐字节比较确认：只有一处删除、一处新增，实际修改行均为协议第 67 行；ruff 句之外的 U1/U2 记录、typecheck 句、D-40 和尾句全部相同，上下文也匹配活文件。作者的子串及落点判据确实可能漏掉同行其它文字的修改，但**当前具体 patch 没有这种修改**。
- **② 没有发现追溯历史提交的要求。**“合入时”“自此”以及 UAT 第 80 行已经表达前瞻效力；问题是后续检查范围的歧义。既有漂移若进入检查仍可能报红，但现有读取面不足以断言下一批所有相关卡都会被拦死。
- **③ 没有冒领跨车道通过。**UAT 第 77、112 行及本 prompt 均明确将集成候选树的全量门留给主 session。
- **④ TAIL 处置成立。**UAT 第 78 行明确写了“没去做，不是做不到”；全量扫描绕过本次 staged 子集盲区，但不等于修复日常 hook。本卡“只核不改”的边界不要求另产整目录 patch。
- **⑤ 三处纠偏没有放宽本卡承诺。**绝对路径要求保留；warnings 不属于协议的 errors 门限；lefthook 要求是指定块不变，该块与基线及绑定 SHA 已逐字节核实相同。warning 归因和 unit 更正后的差集存档内部一致，本次未重算范围外的原始基线。

本次未修改文件、执行检查器、连接数据库或应用 patch。
