> 批次: BATCH-2026-09-18-第十五批 · 车道 P9（card-p9-testinfra） · 卡 CARD-DEBT-1 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-1-r2.md)"`
> 审查绑定: `bd99c49543b758ad57ca99392886b2c374e69c0a`（该轮 HEAD；本轮结论 BLOCKER 0 / HIGH 0，但对其 MEDIUM 做了整改，HEAD 因此前进 ⇒ 本轮**不绑最终 HEAD**）
> 会话头自证（抄 .stderr，括注行号；stderr 本身不入库）:
> `(2) OpenAI Codex v0.153.3` / `(5) model: gpt-6-astra` / `(9) reasoning effort: ultra`

---

复核绑定 **`bd99c49543b758ad57ca99392886b2c374e69c0a`**。结论：**BLOCKER 0 / HIGH 0 / MEDIUM 8 / LOW 0**；其中 7 项需要修正，1 项可继续登记。

原 HIGH 可以按收窄后的范围降级，**不要求改成 `thread`**。但目前还不能签“逐条整改到位”：新门有两处空洞，部分旧强主张仍留在文件里。本轮只读，未运行 pytest、连接数据库或修改文件。

1. **MEDIUM：AST 判据会漏掉实际扩大 W4 豁免面的映射。**  
   [test_debt1_default_gate.py:218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/unit/test_debt1_default_gate.py:218) 对非 `ast.Constant` 键值直接过滤，结构层检查的可能只是安全子集。  
   **负控输入**：加入 `"regression": "real_" + "neo4j"`；运行时会打 `real_neo4j`，抽取器却漏掉该条，行为样本又不收 regression。四层均接不住。已用内存中的 AST 计算确认漏项，未执行变异测试。应拒绝无法解析的条目，不能静默忽略。

2. **MEDIUM：新增第四层重新引入“收集失败也绿”。**  
   [test_debt1_default_gate.py:303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/unit/test_debt1_default_gate.py:303) 仅检查 nodeid 空列表，漏调 `_assert_deselected_not_broken()`。  
   **未被拦下的输入**：该子进程 rc=4、stdout 为空、stderr 为用法错误；第四层仍通过。前几次子进程成功不能证明这一次成功。另外，辅助函数 `:137` 只排除 rc=3/4，也未排除中断及负信号退出；正常退出状态应采用正面白名单。

3. **MEDIUM：signal 例外③把异常类型写错，剩余保证措辞仍应收紧。**  
   [pytest.ini:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/pytest.ini:69)、[test_debt1_default_gate.py:360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/unit/test_debt1_default_gate.py:360)：`pytest.fail()` 的 `Failed` 属于 `BaseException` 系，普通 `except Exception` 不会吞掉它；`asyncio.Handle._run` 的相关捕获是 `BaseException`。  
   **对照输入**：用 `except Exception` 包住同步 sleep，超时仍向外传播；换成捕获 `BaseException` 才可能吞掉。应写成“同步 sleep 探针已证明按时判红并退出”，避免先概括保证“判红、会话继续”，再靠例外撤回。

4. **MEDIUM：census 仍把瞬时栈、截断输出及 item 超时写成更强的根因结论。**  
   [hang-census.md:340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/_bmad-output/审查/evidence-debt1/hang-census.md:340)、`:346–348`、`:417`、`:450–457` 尚未与已收窄的边界一致。证据只能支持：**本次 openapi 文件未在 20 分钟内完成；某 item 触发 300 秒超时；触发时一个 worker 正在解析 markdown**。不能证明全部 300 秒耗在解析、此前零连接尝试、单次 HTTP 请求超过 300 秒，或 health 的慢只来自连接重试。health 存档还有建图、模型加载及 executor shutdown 等待。  
   **对照输入**：一个 item 内多次请求各不足 300 秒、累计超过 300 秒；或者连接尝试的捕获输出尚未打印，进程便被外层终止。两者都符合现有存档。协议更正文案也必须保留“本次配置下 pact 探针快速结束”，不能反证历史挂起原因。

5. **MEDIUM：新增 npm 红“与本卡无关、已经钉死”的结论仍未经对照证明。**  
   [hang-census.md:192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/_bmad-output/审查/evidence-debt1/hang-census.md:192)、`:208` 与后面的 `:209–212` 相互矛盾。没有触发 timeout、hook 对 unit 不打标，只能排除这两种直接机制。  
   **对照输入**：目录级改前改后都绿，全量改后因顺序、共享状态与插件或新增测试的交互而红，同样符合现有四格记录。应保留“目录级均绿、全量出现新增红，原因未定”；实际问题登记 DEBT-3 可以，确定性免责文字需要改。

6. **MEDIUM：ini 的“缺插件只警告、不失败”没有同步整改。**  
   [pytest.ini:88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/pytest.ini:88) 仍保留绝对说法及 `--strict-markers` 依据。census `:126–130` 的限定已经正确。  
   **对照输入**：禁用插件并启用 `-o strict_config=true`，或将 `PytestConfigWarning` 升级为错误，可以失败；`--strict-markers` 不负责未知 ini 键。应统一限定为“本次存档的调用配置下只警告”。

7. **MEDIUM：负控①的送审数字及控制组标签不属实。**  
   [negctl-1-20260919T003755.txt:227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/_bmad-output/审查/evidence-debt1/negctl-1-20260919T003755.txt:227) 实际为 **3 failed / 2 passed**；`:173–180` 明确第三条也红在“hook 应恰有一个”。源码 `:246–248` 已正确说明这一点。  
   **负控输入**：删掉整个 hook，第一、第二条确实红在指定位置，第三条也红，因此不能称第三条为该输入下的控制组。负控②确为 **1 failed / 4 passed**，第五条控制组成立。

8. **MEDIUM，原有登记风险：收集后软链改指向仍可保留豁免 marker。**  
   [conftest.py:1083](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/conftest.py:1083) 在收集时解析路径；[live_port_guard.py:1575](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/support/live_port_guard.py:1575) 随后优先接受已存在的 marker。  
   **门未覆盖的路径**：收集时软链指向 integration，获得 marker 后改指向非豁免目录。该时序风险成立，但本轮未发现实际实例；**可以继续登记，不要求本卡改 W4**，同时把“语义中性”限定为路径保持稳定。

其余重点核对结果如下：

| 问题 | 结论 |
|---|---|
| 当前自动打标是否扩大 advisory | **路径稳定时没有。** 三条常量映射与 W4 使用相同的真实路径口径。词法路径在 unit 的软链可能获得 integration marker，但若真实目标在 integration，W4 原本已经豁免。 |
| 其他 hook／加载顺序 | 本次允许读取面不足以证明全仓没有叠加 hook；不能签无条件的全仓结论。 |
| 默认门是否额外静默排除 | 存档确为 **196 deselected / 9257 selected**，contract 独立收集确为 **196**。没有可从允许证据中点名的额外排除项；接受你收窄为数量判据，身份集合仍未证明。 |
| 默认门耗时 | **2853.11 秒＝47:33，rc=1，有总结行**；未达 20 分钟，表述属实。 |
| C-1 teardown 等待链 | 有直接 worker 栈支持 executor shutdown 等待 SentenceTransformer/Hugging Face 加载，不能归为纯推断。 |
| pact | 本次档案确为 **25 passed / 2 skipped**，provider 文件显示 `ss`。具体 skip 条件及历史配置未在允许读取面内独立验证。 |
| 其余负控 | ③映射扩面、④错映 contract、⑤`.get` 默认值，均红在所述断言；正控为 **5 passed / rc=0**。 |
| 改动范围 | 三文件 **496 行新增、零删除**；`addopts` 未动，根 conftest 只追加。 |

针对 timeout 的两个具体风险，以下是**本轮未执行的对照输入**：

- **异常变形或吞掉**：异步测试通过 `loop.call_soon(time.sleep, 6)` 安排阻塞回调，自身等待另一个可完成的异步操作；1 秒信号可能在回调里变成被事件循环记录的异常，测试自身仍可能通过。清理代码再抛其他异常，也可能让最终报告以其他异常或异常组呈现。现有 contract 收工档已经出现包含 timeout 的 `BaseExceptionGroup`。
- **挂起未结束**：portal/executor worker 永久阻塞，主线程超时后清理仍等待 worker；或者主线程进入不检查 Python 信号的长 C 调用。同步 sleep 门通过不能覆盖这两类输入。

因此，“登记不改”适合保留给软链时序风险和挂起用例本身；**本卡新增判据的空洞及本卡文档的错误主张，应在本卡修正**。另，六份负控存档未提供源码/还原哈希，不能据此独立确认历史还原逐字节一致；验收单未给具名路径，本轮没有扩读其全文。
