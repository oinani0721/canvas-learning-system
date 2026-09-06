> 批次: BATCH-2026-09-05-第十二批 · 车道 Y1 · 卡 CARD-DEBT-mutation-kill-identity round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-mutation-kill-identity.md)"`
> 审查绑定: `52f1ccd2`（**送审后按本轮意见做了 5 条整改 ⇒ 与 HEAD 已失绑**，整改清单与「整改未复审」登记见验收单 §六-B）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**结论：FAIL。发现 3 项 HIGH、4 项 MEDIUM；击杀身份尚未闭合。**  
复核绑定 `52f1ccd2767dd74ac31559753ad0d5af6e866fb5`。未修改文件、未连接数据库；未重跑变异批次。以下区分源码核对、既有日志证据与内存复现。

**BLOCKER**

未发现。

**HIGH**

1. **该 nodeid 自己的 reason 仍能被子进程输出喂饱。**  
   位置：[mutation_kill_identity.py:174](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/mutation_kill_identity.py:174)。

   已复现：真实子进程运行时拼接输出 `"不得再推进" + "水位线"` 到 stderr，并返回 1。执行门源码中的 `test_g3_2_review_ledger.py:4754`，pytest 实际摘要为：

   ```text
   FAILED …::test_round16_fsrs_applied_across_all_branches - AssertionError: 降级遗留必须能恢复: 不得再推进水位线
   ```

   M142 的目标断言在 **4805 行，尚未执行**，但 `kill_identity_ok()` 返回 **True**。原因是前提断言把 `r2.stderr[:250]` 插在首行，而判据只做子串匹配。生产源码里片段出现零次，也挡不住运行时拼接。

   **建议：**绑定 pytest 失败报告中的断言位置／稳定断言标识；不能把任意 reason 子串当作断言身份。此复现证明输入通道可达，不表示当前 M142 变异已经这样输出。

2. **解析器没有限定摘要区域，captured stdout/stderr 中的伪 `FAILED` 行也会被收录。**  
   位置：[mutation_kill_identity.py:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/mutation_kill_identity.py:82)、同文件 129 行。

   本机 pytest 9.0.2 的内存用例先打印：

   ```text
   FAILED <目标nodeid> - AssertionError: <EXPECT_MSG>
   ```

   随后抛出另一条前提错误。pytest 在 captured output 区原样展示伪行，真正摘要则报告前提错误；解析器收录两行，最终 **KILLED=True**。`learning_event_log.py` 被门直接在 pytest 进程内调用，生产侧打印可进入这一通道。

   **建议：**通过 pytest report hook 输出独立结构化结果，至少包含 `nodeid / when / outcome / 失败位置`。只截取摘要区域仍不足以解决上一项首行插值问题。旧 g33 也存在此解析形态，本卡共用件继续保留。

3. **40 条豁免仍计作断言级 KILLED，且本卡日志已有明确错位实例。**  
   位置：[g32b_mutation_gates.py:2057](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g32b_mutation_gates.py:2057)、[mutation_kill_identity.py:172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/mutation_kill_identity.py:172)。

   M102 声称移除 attempt 值比较，使 `attempt=999` 被放行。但门的这个场景仍被生产完整性检查拒绝；实际红在**下一个“ts 带空白”场景的拒因断言**。本卡[全量日志第 96 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/_bmad-output/审查/evidence-mutkill/g32b-run-20260906T112329.txt:96)明确记录：

   ```text
   M102 … KILLED (AssertionError: [ts 带空白] … receipt 事实清单不完整 …)
   ```

   **建议：**无身份绑定的结果单列 `KILLED-UNBOUND`／`UNVERIFIED`，不得并入“指定断言击杀”。这里登记的是新增豁免与裁决口径的问题，不要求修改门或生产代码。

**MEDIUM**

4. **`judge_surface_missing()` 不足以区分判据损坏和变异存活，g32b 连已识别的损坏也归入 SURVIVED。**  
   位置：[mutation_kill_identity.py:150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/mutation_kill_identity.py:150)、[g32b_mutation_gates.py:2336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g32b_mutation_gates.py:2336)。

   内存输入验证以下情况均返回 `surface=None、kill=False`：

   - `FAILED <目标nodeid>`，reason 缺失；
   - reason 被截断，目标片段落在截断部分；
   - pytest 返回 4，输出用法错误；
   - 参数 ID 含空格而无法匹配 `\S+`，同时另有一条可解析的失败行。

   此外，即便完全没有摘要、检查已返回“判据面不成立”，g32b 的调用路径仍打印 **`SURVIVED ⇒ 假门`**。

   **建议：**独立返回 `HARNESS-ERROR`，检查合法退出状态及目标报告完整性；缺失、截断、不可解析不能解释为门不承重。普通无空格参数化 nodeid 的前缀匹配本身正确，但语义是“任一参数实例命中”。

5. **M13b 的豁免理由错误；另有多条把当前接口限制说成门无法提供身份。**  
   位置：[g32b_mutation_gates.py:2027](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g32b_mutation_gates.py:2027)。

   门 `test_g3_2_review_ledger.py:1405` 已有稳定片段：

   ```text
   结尾在字节上无 LF ⇒ 应按截断隔离:
   ```

   全门文件恰好出现一次，实际全量摘要也包含它。**无需改门即可绑定 M13b。**

   40 条逐项核对结果如下：

   | 条目 | 核对结果 |
   |---|---|
   | M2b、M5、M10、M12、M14、M15b、M16、M20、M29、M30、M31、M32、M38b、M45、M61、M65、M79、M91、M117、M129 | 实际失败断言确实仅以子进程输出作消息 |
   | M102 | 消息还有动态场景描述；且存在上述实际错位击杀 |
   | M9、M26 | 消息实际为空，理由成立 |
   | M89、M90 | 实际首先红在无消息的前提运行断言，后续 receipt 断言未执行 |
   | M97 | 实际为 `yaml.parser.ParserError`；可考虑异常类型＋位置身份，当前接口不支持 |
   | M76 | 消息确实重复生产文案 |
   | M13b | **可直接绑定，豁免不成立** |
   | M23、M24、M25、M47、M49、M50、M51、M58、M75、M77、M81、M140 | 全文件确有重复，但不少重复位于不同 nodeid |

   **建议：**移除 M13b 豁免；其余重复项按目标 nodeid 的断言范围核唯一性，或绑定源位置。例如 M75、M140 的重复消息分别位于不同测试，不能因此断言“必须改门才能绑”。

6. **信号能中断正在执行的 `finally`，跳过剩余还原。**  
   位置：[g32b_mutation_gates.py:2151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g32b_mutation_gates.py:2151)、同文件 2307、2320 行。

   单次 SIGTERM 若恰在进入还原后、原快照写回前到达，`_Terminated` 会直接退出该 `finally`，没有外层恢复兜底。已用实际 handler 在独立审计子进程的内存 `finally` 中验证。

   **建议：**恢复期间延迟处理退出请求，全部恢复完成后退出。**没有发现 `except Exception` 吞掉该异常**；信号落在正常 `run_gate()` 路径时，现有 `finally` 能展开。

7. **`--list` 的消息自检失败仍可能返回 0。**  
   位置：[g32b_mutation_gates.py:2176](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g32b_mutation_gates.py:2176)。

   场景：门消息漂移，但生产锚仍全部唯一。脚本打印 EXPECT_MSG 自检错误，返回码却只取决于锚检查。

   **建议：**退出码同时取决于锚点与消息自检结果。

**LOW**

8. **裸 `--only` 缺值时被静默忽略，转成全量执行。**  
   位置：[g32b_mutation_gates.py:2185](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g32b_mutation_gates.py:2185)。

   `_only` 保持 `None`，随后启动自愈和全部变异。建议参数解析阶段拒绝缺值、空前缀及未知参数。正常完成的 `--probe`、有效 `--only` 确实返回 4，不进入全量 PASS；“恒 4”不包括初始化失败或中断。

9. **PYEOF 提取存在继承的边界漏洞；当前变异未命中。**  
   位置：[mutation_kill_identity.py:79](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/mutation_kill_identity.py:79)。

   具体输入：

   ```text
   python3 - <<'PYEOF'
   x = 1
   PYEOF_label = 2
   if True print(1)
   PYEOF
   ```

   正则在 `PYEOF_label` 前提前结束，只编译 `x = 1`，返回通过。缺闭合标记也会零块通过；反过来，合法的 `cat <<'PYEOF'` YAML 文本会被误当 Python 编译。

   **建议：**结束符匹配完整行，允许 Python 引导行带参数，并对两个 SKILL 校验必要执行块存在。上述为构造输入可复现的边界，**不是本轮已有语法假杀，也不是放宽新引入的全部问题**。

**核对通过及证据边界**

- 在内存逐条施加 **138＋9＋11＋18＝176** 条变异，含同层替换：锚均唯一、编译均通过。干净树两个 SKILL 的 **2＋3 块**也均通过。因此“当前干净树不会因放宽而误判”成立。
- 三个目标 `.py` 全文件 `compile()` 足以检查其当前文本的编译语法；不证明导入、运行成功或变异实际生效。
- 四处更锚均保持意图：

  | 变异 | quiz-answer/SKILL.md 位置 | 结论 |
  |---|---:|---|
  | M142 | 2213 | 确实改为全局 W 判断 |
  | M143 | 2183 | 确实拆掉整道凭据拒绝 |
  | M145 | 2726 | 确为 dup 恢复后的凭据提升 |
  | M157 | 主 1973、层 1997 | 分别对应时刻、序数方向检查 |

  M143 与 g32cb M1 **不重复**：凭据缺失为 `None` 时，M1 仍拒绝，M143 放过。
- 未发现运行时把本次观察值自动写成期待值的代码；期待表是固定的。但先观察再回填只能形成历史行为基准，不能独立证明原始因果意图。豁免分支则明确跳过断言身份检查。
- g32b 阶段二的层／主体单独对照仍使用旧粗判据、未接编译自检；当前分体均可编译，作为继承范围登记。

**作者自述中比证据宽的说法**

- 日志中的 N/N 数量及 g33 两份 JSON 的 `(id, verdict)` 序列一致，均核对成立；但 **g32b 总 rc=1**，因 M100/M151 既有层债，不能称整套验收全绿。
- “138 条全部被指定断言杀死”不成立：实际 **98 条绑定＋40 条豁免**，且 M102 已有错位证据。
- “今后击杀漂到别处就立即 SURVIVED”仍说宽：豁免、首行插值和伪摘要都能绕过。
- “豁免根源全在门本体、只能补门消息”不成立，至少 M13b 可直接修正；跨 nodeid 重复也属于当前自检范围过宽。
- “先推导”的名单不一致：脚本列 M142/M143/M145/M157，验收单说四格四条，实际包含 M144、不含 M157；“其余 91 条”也与当前数量不符。现有日志不能证明逐条人工判断的先后顺序。


