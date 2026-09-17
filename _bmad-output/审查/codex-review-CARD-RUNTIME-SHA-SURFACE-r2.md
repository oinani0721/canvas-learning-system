> 批次: BATCH-2026-09-11-第十四批 · 车道 T9-D（`card-t9-w4`） · 卡 CARD-RUNTIME-SHA-SURFACE round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RUNTIME-SHA-SURFACE-r2.md)"`
> 审查绑定: `5fa2d401..1f63d216`（**最终 HEAD = `1f63d216`**；本轮 BLOCKER=0 / HIGH=0 / MEDIUM=0，
> 4 条 LOW 全在证据与措辞面，整改只动 `_bmad-output/`，门文件一字未改 ⇒ 不触发新一轮）
> 会话头自证（抄 `.stderr` 的 codex 版本行 / model 行 / reasoning 行，括注行号；`.stderr` 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

## 结论

**源码复核 PASS；补充证据 PARTIAL。原 MEDIUM-1、门内 LOW-2 均已修好，未发现新的 BLOCKER / HIGH / MEDIUM。**

结束时 HEAD 仍为 `1f63d216f95f76ffa1ff54c960d32d1004f58fea`，工作树门文件与该提交逐字节一致。本轮未修改、暂存文件，未运行门、探针、测试套件或 hook。辅助证据按当前磁盘版本核对。

## 尚存问题

### LOW-1 — final 探针存档不具备声称的完整记录和首尾 SHA

**文件：** [gate-probes-final-20260915T183936.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/gate-probes-final-20260915T183936.txt:1)

**依据：** 文件实际只有 **6 行**：开头门 SHA、最后三个探针结果、`total=27 failed=0`、`rc=0`。没有结束 SHA，也没有其余逐项结果。与请求及验收单“首末各记一次且相同”的描述不符。

完整的 **33 行**记录是 [gate-probes-after-20260915T183715.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/gate-probes-after-20260915T183715.txt:1)，首尾 SHA 均正确绑定 `b191a085`。

**建议：** 将 final 明确标为摘要，引用完整 after 记录，并说明通过纯注释差异衔接最终 HEAD。若要求最终态独立执行证据，需要重新生成完整记录；不能事后补写历史结束 SHA。

### LOW-2 — rc=7 记录仅验证人工结果对象，未验证端到端执行

**文件：** [noexec_contract.py:75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/noexec_contract.py:75)

**依据：** 三项传播检查使用手工构造的 `CompletedProcess(returncode=1/0/7, ...)`，调用 `caller_exit_code()`。它证明调用方函数返回对应数值，但没有实际运行返回 7 的被包裹命令，也没有观测外层 Python 进程退出 7。

**建议：** 标为“调用方函数的人工结果对象检查”。**端到端 rc=7 传播未验证**；若主张已实跑，需要实际命令、门 SHA 和外层退出码记录。源码静态判断仍支持传播逻辑正确。

### LOW-3 — 补证说明误指原探针驱动入口

**文件：** [run_gate_probes.py:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/run_gate_probes.py:6)

**依据：** 注释称真正驱动方是 `lifespan_isolation_negative_control.py`，实际聚合调用位于 [guard_probes.py:2161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_guard_probes.py:2161) 及第 2179 行，由其自身 `main()` 驱动。新增 runner 的实际调用正确。

**建议：** 更正 runner 和验收单中的入口说明，避免后续再次跑错脚本；无需修改范围外文件。

### LOW-4 — 验收单仍把端点观测扩大为过程结论

**文件：** [验收单:267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/验收单/UAT-CARD-RUNTIME-SHA-SURFACE-2026-09-15.md:267)，同类措辞见第 296–297 行；第 27 行还保留“门 SHA 相同＝工作树零碰”。

**依据：** 两份 realtree 文件确实完全相同，但两项 `absent→absent` 只能证明两个采样时刻不存在，不能排除期间创建后删除；单个门文件 SHA 相同也不能证明全树未变。

**建议：** 改为“跑前跑后均不存在；期间是否创建后删除未验证”，并将“工作树零碰”收窄为实际采样文件的端点结论。

## 对五个问题的逐项回答

### 1. round-2 是否纯注释：PASS

[门:133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:133)、第 530 行起的修改均处于真正的 shell 注释上下文。

独立比较后：

- `b191a085..1f63d216`：去除注释和空行后的内容完全相同。
- `5fa2d401..1f63d216`：可执行变化恰为三个新增监视项、两个计数常量更新。
- 文件模式未变，提交范围只有这个文件。

**建议：** 可确认“纯注释改动”。

### 2. MEDIUM-1 两点是否修好：已闭合

**原级别 MEDIUM；文件：** [门:135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:135)

**依据：**

- `re.M` 允许完整结论行出现在多行日志中，符合门先打印快照的协议；不会接受所列 `GATE-BROKEN`、碎片、非行首或表头负例。
- 当前合法结论均在 stdout 输出完整行并带换行，因此直接拼接 stdout、stderr 不会破坏当前正常路径的匹配。
- 存在合法结论后传播 `p.returncode`：文件变化返回 1；文件未变则透出被包裹命令退出码，与 [门:708](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:708) 起的实现一致。
- 无结论的用法错误可能由原 rc=2 转为调用方 rc=1，这是“缺结论即判红”的明确语义，不能称为所有分支都原样传播。
- 此判据仍是输出存在性检查，不是输出来源认证；主动伪造仍属于已声明边界。

**建议：** 关闭原 MEDIUM-1；补证强度按上述 LOW-2 表述。

### 3. WAL 新措辞是否越界：门内已闭合

**原级别 LOW；文件：** [门:530](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:530)

明确限定主 `.db`、排除 WAL/SHM、限定默认连接实验及无并发条件，并将其他条件登记为待验证，未再直接定性未来结果。

**建议：** 保留。验收单第 297–298 行仍有“可能成为新的假红面”的旧措辞，宜同步引用完整边界。**实际 WAL、并发和生产完整生命周期表现仍未验证**，需对应条件实验才能判断。

### 4. 其余五项是否仍成立：PASS

| 核对项 | 当前依据 |
|---|---|
| 扩面只加不放宽 | [门:536](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:536)：原固定项和 glob 全保留，未修改拒绝分支 |
| 计数同步 | 第 576 行起：实际 **5 fixed / 2 glob**，常量一致，自检仍先于命令执行 |
| noexec 诚实 | 第 126、156 行：明确内部不可防，未增加声称内部防御的执行分支 |
| 未出地盘、探针锚未破 | 唯一受控改动文件为门；AST 名册和注释集合均为 **19**，原名册区逐字未变，三个文本锚各命中一次 |
| 开头边界注释 | 第 48 行起：具名默认路径、首尾采样、配置覆盖盲区、Neo4j 库内与磁盘 JSON 的区别均保留 |

**建议：** 无需调整这些实现。

### 5. 执行存档是否支持限定回归主张：支持，但 final 独立补证未闭合

[runner:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/run_gate_probes.py:35) 和第 53 行起确实调用 **19＋8＝27** 条检查，未调用 socket/端口族。

**完整 `b191a085` 记录＋round-2 执行内容、名册和文本锚均未变化**，足以支持“本卡扩面没有破坏这些既有 shell 与 M15 glob 探针”的限定主张。原 M15 族针对 `vault_index_pending`，不能单凭这 27 条外推新增 LanceDB 监视面的全部行为。

两条原证据限制的状态是：

- **realtree 缺 after：已闭合。** 一项存在文件摘要相同、两项端点 absent；过程零写入未验证。
- **152 passed 不能证明探针执行：已补上独立执行依据。** 但“final 存档完整且首尾 SHA 相同”未闭合，见 LOW-1。


