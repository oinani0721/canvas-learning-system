> 批次: BATCH-2026-09-05-第十二批 · 车道 Y1 · 卡 CARD-G3-3-R1 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-3-R1.md)"`
> 审查绑定: `a795741f`（送审时 HEAD = a795741f；之后只改 `_bmad-output`，代码树保持绑定）
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: …/.claude/worktrees/card-z2-cas` / `model: gpt-6-astra` / `reasoning effort: ultra` / `sandbox: read-only`

---

## 结论

**有阻断级问题：负控仍可能将“目标坏事根本没发生”的运行期故障判为 `KILLED`，本 diff 尚不能完成假杀修复收口。** 这属于[仓内协议第 8 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/.claude/rules/card-batch-protocol.md:8)规定的“负控本身谎报 PASS”；以下为静态核对，没有运行作者的脚本或测试。

审查绑定 `7105e84c → a795741fc048a5e907e2c3b457738faef02861fe`。下文简称：

- **G**：[负控脚本](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/scripts/g33_mutation_gates.py)
- **T**：[测试文件](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/tests/regression/test_g3_3_cas.py)
- **S**：[quiz-answer 生产写点](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/canvas-vault/.claude/skills/quiz-answer/SKILL.md)
- **E**：[learning_event_log.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas/backend/app/services/learning_event_log.py)

## 发现

| 级别 | 编号 | 位置 | 事实 | 影响 | 建议处置 |
|---|---|---|---|---|---|
| HIGH | R1-01 | T:1125、204–206；G:176–179、436–440 | M15 的断言是 `ids.count(...) == 1`。**零行同样失败**，消息为“同 event_id 被写了两遍: []”，恰好满足 `expect_msg`。写点若在 bridge 注入之前发生运行期异常，仍可被判 KILLED。M1 的 `… == 2` 在全部零值时也抛出 lost-update 消息。 | 编译通过、指定断言失败，仍不能证明发生了重复写入或覆盖。G:171–175 所称“零行反而通过”直接不成立。 | 将“注入未发生／事件未写入”和“实际重复／实际覆盖”分成不同断言身份；KILLED 必须同时要求目标坏状态的具体证据。 |
| HIGH | R1-02 | T:579–589、1233、1263；G:188、197 | 两条新门首先把“最终正文没有 `RACE_MARK`”判成 CAS 未挡住；但没有独立确认追加编辑已经发生。race 副本若在追加前运行期退出，目标消息照样出现。对照运行的是另一份未注入副本。 | “编辑从未成功注入”仍可冒充“编辑被恢复发布覆盖”。 | 增加独立于节点正文的注入完成凭据，先确认竞态前提成立，再判断覆盖。 |
| MEDIUM | R1-03 | G:276、336–346、435–440 | `_error_lines()` 对**整份输出**抽取任意 `^E\s+` 行，再做子串匹配；没有绑定回溯段、异常类型或断言位置。捕获输出中的 `E <expect_msg>`、多行异常载荷、断言解释里的值均可能被纳入。参数化失败身份与消息也分别汇总。 | 尚未建立作者声称的“那一条断言”身份绑定。 | 使用结构化 pytest 失败报告，将完整参数 nodeid、失败阶段、断言位置及唯一失败标识绑定在同一报告内。 |
| MEDIUM | R1-04 | T:693、708–712 | 加性比较改用调用前快照，但调用方检查仍只要求没有 `out_of_order`。若正确落盘后另外修改调用方已有字段，新测试会通过；旧比较会抓住这一特定情况。 | 落盘加性判据更可靠，但对调用方原有字段的部分污染检测被移除了。 | 保留快照比较，并另断言 `caller_payload == caller_snapshot`。 |
| LOW | R1-05 | G:470–487、521 | 残留判据实际是 `actual - baseline` 为空，**不是集合相等**；基线文件缺失不会报错。扫描还忽略了 grep 返回码，扫描失败可能被解释为空结果。 | 作者关于“仍与基线集合相同”的说明不准确，残留检查存在漏报边界。目标文件 SHA 检查仍是另一层保护。 | 明确采用“无新增”还是“集合相等”；检查扫描返回码，失败不得当作无残留。 |

R1-01、R1-02 是从现有条件可以直接推出的假杀输入，**不代表我实测了当前 M15/M16/M17 已发生假杀**。

对问题 1 的前缀与参数化细节：目前 18 个 `expect_msg` 片段在 T 中各出现一次，未发现现存断言消息前缀碰撞。但匹配器没有防止这种碰撞。M1 确有 `[1]`、`[2]` 参数实例（T:178）；当前每次只运行指定函数，因此不能把汇总实现直接描述成“已经串了其他测试的结果”，只能确认它不保留完整参数实例与异常文本的对应关系。

**两条对照段确实有经过前置门的证据：**

- 初始节点没有水位线、attempt 或校准记录（T:54–58、81）；唯一 seed 的三个时刻均为 `TS1`，attempt 为 `1`（T:662–674、1191–1200）。
- 因无 receipt，S:2493 会进入采用时刻检查；`W=None` 时采用值就是整秒 `TS1`，S:2501 可以通过。
- S:2587 得 `_already_=False`；S:2643–2651 计算期望序数为 `0+1=1`。foreign 后来补入的 receipt 不会改变此前算好的 `_already_`。
- foreign 对照的专用消息来自 **replace 和目录 fsync 之后**的 S:2691，再结合实盘水位线及 S:2704 的专用续跑退出，足以证明恢复发布完成。
- dup 的“崩溃窗口①”消息位于 **发布之前**的 S:2744，单独不够；结合 T:1250 的 `rc=0` 与 T:1252 的实盘水位线，才构成发布完成证据。
- 账本仍一行、validator 成功、整文件包含 event_id 都只是辅助证据，单独不能证明经过两道门。

**M4b 当前形态没有发现旁路致红：** E:277 在替换前已算好 `is_review`；本次 `out_of_order=True`，所以 E:302 的后续读取分支被跳过。E:317–345 直接序列化、写入并返回，没有完整 schema 校验提前拒绝。测试先要求 append 成功、标记存在，之后才在 T:708 因其余键丢失而红。针对 M4a/M4b，deepcopy 改动改善了归因；R1-04 指的是其他调用方污染形态的覆盖变化。

## 对作者自述的逐条裁定

1. **核对通过：单行短路及消息绑定；无法核对：实测输出。**  
   G:176 保留原缩进及下一行块体，消除了旧替换串的缺块体问题；G:179 对应 T:1125。没有运行测试，不能确认作者给出的两行账本异常输出。该断言仍接受零行假杀，见 R1-01。

2. **核对通过：源码实现；无法核对：运行结果。**  
   G:247 与 T:37 的 PYEOF 正则一致；G:250–266 做编译检查，G:420–426 在写盘前判 `SYNTAX-INVALID`，G:518–521 确保它导致非零退出。自检包含旧串、新串、原文三个检查，且仅在内存替换。未运行自检，不能确认实际 SHA 输出。编译检查不覆盖运行期可达性。

3. **核对通过：四条变异及声明的门、消息均存在；不成立：据此已经充分绑定目标坏事。**  
   M4a/M4b 当前归因成立；M16/M17 对照路径成立，但竞态注入前提未被独立证明。文本匹配限制见 R1-02、R1-03。

4. **核对通过：补入第五项的依据；不成立：“集合相同”这一描述。**  
   Git 核对确认 `03ac8bf8` 是目标提交祖先，且该提交中的 `g32ccr1_negative_controls.py` 已包含标记字面量。G:240 已加入它。但 G:487 实际只检查集合差，见 R1-05；没有扫描全仓来确认完整标记集合。

5. **核对通过：生产逻辑零 diff；无法核对：“无条件还原”的实际保证。**  
   指定的生产目录 diff 为空。源码有逐条 finally、外层 finally，以及 SIGTERM/SIGINT/SIGHUP 处理；正常返回后还比较 SHA。它仍依赖恢复写入成功、独占运行及可处理的退出方式：没有并发互斥，信号路径不完成最终 SHA 验证，也没有协调所有后代进程退出。不能把这些机制描述为任何中断下都已验证还原。

## 我没有核对到的面

- 未运行负控、`--selfcheck-syntax`、pytest、validator 或 bridge；作者的 KILLED 数量、具体回溯、运行后 SHA 与残留结果均未复现。
- 未连接数据库或任何网络服务，未修改文件，未读取作者审查报告或通读全仓。
- 两条恢复门仅核对了无 receipt、单 pending、初始水位线为空的场景；没有验证多 pending、既有水位线或 degraded receipt 恢复。
- 未验证 CAS 检查之后到 replace 之间的竞态；S:358–362 已将其声明为现存能力边界。
- 未核对线上 bridge 或部署；部署不计入本 diff 缺陷。
- 所给路径下的 `development-discipline.md`、`plan-traceability.md` 不存在；本次依据可读的 `card-batch-protocol.md` 与 schema 相关条款作判断。
