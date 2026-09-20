> 批次: BATCH-2026-09-18-第十五批 · 车道 P4 · 卡 CARD-CARD-STATES-ATOMIC-WRITE round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-CARD-STATES-ATOMIC-WRITE.md)"`
> 审查绑定: `7a5081f197b364c6eb7d1db99e0382e0d4aa7a4f`（当时 HEAD；本轮整改后 HEAD 已前进到 `d7ab47c811230989765cb65568ff6b6b15ea7b7e`，故本份**不绑最终 HEAD**，由 round-2 绑）
> 会话头自证（抄 `.stderr`，括注行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: gpt-6-astra` / `(L9) reasoning effort: ultra`
> 判定: BLOCKER=0 HIGH=1 MEDIUM=3 LOW=1

---

**本卡尚不能认定“零残留与持久顺序已完整封门”。** 核到 HEAD 为 `7a5081f197b364c6eb7d1db99e0382e0d4aa7a4f`，diff 恰为指定 3 个文件，三文件工作区与 HEAD 一致。本次只读；未运行 pytest、pyright。下述测试红绿是源码推演，纯内存检查另行注明。

按你给定的优先级列问题：

1. **MEDIUM｜问题 0：零残留门没有绑定 `finally` 的覆盖范围。**  
   [test_g3_7_truth_source.py:938](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/regression/test_g3_7_truth_source.py:938)、`:975` 都只让 `os.replace` 失败。当前实现确实有外层 `finally`，但测试不能证明它包围了全部步骤。

   **复现思路：**负控输入把 `try/finally` 缩到仅包住 replace 及后续步骤，将 open/write/flush/文件 fsync 放在外面；现有 8 条仍可全绿，而文件 fsync 失败会残留 tmp。

   同属这条门缺口的还有：
   - 删除目录 open/fsync/close，是未被拦下的输入；两个 S6 都在 replace 抛错，到不了目录同步。
   - `:844` 只检查返回后 tmp 不存在，不能证明“从未创建过”。先创建、编码失败后再清理，也能满足该断言。
   
   因此，作者两段负控输入有用，但远非穷尽证明。

2. **MEDIUM｜问题 0/5：spec 的无条件零残留承诺超出实现。**  
   [spec.md:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/openspec/specs/concept-identity/spec.md:20)–22、`:130` 承诺任何失败都无残留；[review_service.py:696](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:696) 只能保证**尝试删除**。

   **复现思路：**负控输入令 replace 失败，再令 unlink 抛 `PermissionError`；外层 `:1032` 返回 `False`，tmp 仍可存在。

   `missing_ok=True` **只忽略 `FileNotFoundError`，不会吞掉其他 unlink 错误**。清理错误会成为向外传播的异常，再被归一成 `False`；当前 warning 显示的是清理错误，原始失败不再是日志中的主异常。这是门未覆盖的路径，不是 `finally` 没执行。

3. **MEDIUM｜问题 1/5：新增目录 fsync 使“replace 成功必清脏”失真。**  
   [spec.md:56](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/openspec/specs/concept-identity/spec.md:56) 仍要求 successful replace 后无条件清空脏标记；实际 [review_service.py:689](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:689) 替换成功后，`:690–694` 仍可能失败，绕过 `:1018` 的 `clear()`。

   **复现思路：**负控输入仅让第二次 `os.fsync` 抛 `OSError`，得到“目标已更新、返回 False、脏标记保留”。

   **不建议统一降级为日志后返回 True。** 在当前契约下，`False` 合理表达“持久性未确认”；应把 spec 的触发条件改为完整持久化序列成功。若某介质或挂载持续拒绝目录同步，这种结果就会反复发生；限定材料没有本地盘／网络盘实测，无法判断本仓发生频率。原文逐字未改，不能证明新增失败点没有改变契约。

4. **HIGH｜问题 2：单 worker 也不能保证固定 tmp 全程串行。**  
   [review_service.py:989](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:989)、`:1015` 的协程被取消后，`asyncio.Lock` 会释放，但已经启动的线程继续执行；新加的 `:696` 可以删除下一次保存的 tmp。

   **复现思路：**负控输入让 A 完成 replace、暂停于目录 fsync；取消 A 协程；B 获取锁并创建同名 tmp；恢复 A，A 的 `finally` 删除 B 的 tmp，随后 B 的 replace 报 `ENOENT`。

   我用纯内存的 `Lock + to_thread + Event` 检查确认了“锁已可重获、线程仍运行”。具体文件互删顺序为源码推演。取消导致线程重叠的基础风险原先已有，**本次新增 finally 带来了交叉删除路径**。

   多进程还可直接互相截断同名 tmp、发布另一进程的内容。uvicorn workers 配置不在允许读取面，数量未证实；即使确认是 1，也不能排除上述路径。

5. **LOW｜问题 5：Scenario 1 仍指定旧 API。**  
   [spec.md:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/openspec/specs/concept-identity/spec.md:74) 写 `Path.replace`，实现 `review_service.py:689` 已直接调用 `os.replace`。

   **复现思路：**对照输入分别记录两个入口，当前实现直接调用后者。原子替换语义并未因此失效，但 Scenario 与 Requirement、实现的具体措辞不一致。

其余问题的核对结果：

| 问题 | 结论 |
|---|---|
| **3：逐字节等价** | 本机 Darwin / Python 3.14.4 的纯内存检查中，`TextIOWrapper(encoding="utf-8", newline=None)` 与 `data.encode("utf-8")` 字节相同，覆盖中文、emoji、字符串换行及缩进。**本机等价，不能推广为跨平台等价**：Windows 默认文本换行转换会把 JSON 缩进中的 LF 写成 CRLF，二进制写保持 LF。对应实现 `review_service.py:1008–1015`。 |
| **4：S1 open 探针** | `test_g3_7_truth_source.py:754–755` 实际同时包装 `builtins.open` 和 `io.open`，能捕获旧 `Path.write_text`。`:784` 正控能让“只包 builtins、换回旧实现”的对照输入变红。但它单独只能证明至少一条绑定活着；当前两条都包装，是源码核对确认的。 |
| **6：pyright ignore** | 指定 diff 中新增、删除的 `pyright: ignore` 均为 **0**，新 helper 也没有 ignore。没有发现本卡新增忽略来掩盖错误的证据；“全文件恰有 6 处”和“实际运行 0 errors”不能在限定材料内独立确认。 |
| **7：最终 HEAD 的目录级测试** | **未证实。** HEAD 相符不等于测试在该 HEAD 上执行。允许材料没有绑定最终 SHA 的命令、退出码及测试结果；移交 `:199–200` 仅记录旧卡 collect-only。此外 fixture `test_g3_7_truth_source.py:117–118` 可跳过测试，验收记录还需区分 passed 与 skipped。 |

Requirement 逐段对照如下；这里区分“代码已有步骤”与“测试已经守住步骤”：

| spec 条款 | 实现对应与结论 |
|---|---|
| `:8–12` 全量快照、JSON 参数 | `review_service.py:1008–1011` 相符。 |
| `:14–19` 先编码、写 tmp、flush、文件 fsync、replace、目录 fsync、一次派发 | `:1014–1015`、`:685–694` 均有对应。一次 `to_thread` 覆盖的是文件 I/O，编码在派发前。 |
| `:20–23` 持久性、零残留、替换前保护目标 | 调用顺序存在；无条件零残留过宽，见问题 2。未做真实介质掉电验证。 |
| `:25–30` 锁内操作 | 常规等待路径相符；取消后的线程生命周期不受锁完整保护，见问题 4。 |
| `:32–37` scope 失败关闭 | `:998–1005` 在 mkdir 前返回，相符。 |
| `:39–47` 异常归一与回滚 | `:1020–1038` 确实未改；新 helper 的 `OSError` 能进入后一个分支。 |
| `:49–54` 脏标记身份 | `:943–958` 返回并查询 `(vault_id, concept_id)`；本卡未改。 |
| `:56–62` 清标记、不恢复回滚值 | 不恢复回滚值的行为保留；“replace 成功即清标记”已失真。 |
| `:64–67` 投影与调度真相源分开 | 方法注释与写入对象相符；外部调用方如何转述信号，不在本次读取面。 |

新增 8 条测试对**旧实现对照输入**的结果，按源码判定如下，未实际运行：

| 测试起始行 | 结果 | 原因 |
|---|---|---|
| `:765` S1 | 仍绿 | 旧实现也不直接写目标，成功后 tmp 被移走。 |
| `:794` S2 | 仍绿 | 失败关闭逻辑未变。 |
| `:824` S3 无旧值 | 红 | 旧编码路径留下 tmp。 |
| `:849` S3 有旧值 | 仍绿 | 恢复旧值逻辑未变，该条不检查残留。 |
| `:868` S4 | 仍绿 | 第二次成功保存会移走旧 tmp，并清脏标记。 |
| `:890` S5 | 仍绿 | vault 脏标记逻辑未变；旧 `Path.replace` 同样经过 `os.replace`。 |
| `:925` S6 清理 | 红 | replace 失败后旧实现残留 tmp。 |
| `:957` S6 顺序 | 红 | 旧实现没有 fsync。 |

所以是 **5 条仍绿、3 条变红**。但“对照输入仍绿 ⇒ 没有绑定任何行为”不成立：那 5 条正在补既有行为的回归门；删除回滚、删除 clear、改成裸 concept_id 等负控输入仍能使相应测试变红。

指定裁定书在工作区与目标提交中均未读到第 149 行，因此未声称核验了 T4-C 原文；也未独立确认作者负控执行及哈希还原记录。

BLOCKER=0 HIGH=1 MEDIUM=3 LOW=1


