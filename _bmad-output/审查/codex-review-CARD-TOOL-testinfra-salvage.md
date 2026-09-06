> 批次: BATCH-2026-09-05-第十二批 · 车道 Y4 · 卡 CARD-TOOL-testinfra-salvage round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-TOOL-testinfra-salvage.md)"`
> 审查绑定: `16b9e337..aae845f8`（审后按本轮意见整改，HEAD 已前进到 `556ecc3d` —— 失绑，见验收单 (h)「整改未复审」）
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `sandbox: read-only` / `session id: 01a07549-4316-7161-a19b-266a3c13d0e7`

---

复核锚定 `16b9e337 → aae845f8`，全程未修改文件。**抽取范围和基线对账基本准确，但前端 pre-push 仍会吞掉失败码。**

下文 UAT 指[验收单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-testinfra-salvage-2026-09-06.md)，transcript 均位于 [evidence-testinfra](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/审查/evidence-testinfra)。

**BLOCKER：无。**

**HIGH**

1. **前端检查仍然返回成功；验收单漏检了 wrapper 后面的 `echo`。（问题 1、6）**

   [lefthook.yml:474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/lefthook.yml:474) 调用 wrapper，475 行随即无条件执行成功 `echo`，其退出码成为整个分支的退出码。本机 lefthook 2.1.6 使用 `sh -c`，没有启用 `-e`。[对应版本执行器源码](https://github.com/evilmartians/lefthook/blob/v2.1.6/internal/run/controller/exec/exec_unix.go#L75-L122)

   我只读抽取了 **473–475 行完整分支命令体**，通过 `TMPDIR=/dev/null` 让日志创建失败，确保不创建文件，结果：

   ```text
   wrapper 报告 exit code: 1
   随后打印 Plugin tests done.
   整个命令体退出码：0
   ```

   `control-group-pipe-20260906T134627.txt:8–10` 只测了第 474 行，漏掉第 475 行。因此 UAT:27 的“6 处补上”和 :244 的传播结论超出了证据。

   **建议：**wrapper 调用后接 `|| exit $?`，或立即保存退出码并最终退出；验收必须覆盖完整 `run` 块。

   **手工冲突解法本身没有配置回退：**差异只有 461–468 行注释和 474 行替换；470 行 glob 保留插件路径，runner 保留 `npm test`。`backend-smoke` 497–513 行与基底**逐字节相同，均为 626 字节**，A11 两文件、`.venv/bin/python`、`TEST_EXIT=$?` 均保留。没有恢复全目录执行或 `command -v python`；482 行出现的 `backend/tests/unit/` 是原有历史注释。

**MEDIUM**

2. **wrapper 存在未登记的第四条瑕疵：日志创建失败后，命令未执行，却被标成测试失败。（问题 2）**

   [run_cmd_capture.sh:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/scripts/run_cmd_capture.sh:68) 没有检查 `mktemp` 结果。失败后 `LOGFILE=""`，81 行重定向失败，82 行取得的是**重定向失败码**。

   只读实测：设置 `TMPDIR=/dev/null`，包裹 `sh -c 'exit 7'`，最终返回 **1**、日志路径为空。这里不能说“子命令的 7 被改成 1”：**子命令根本没有启动。**

   脚本没有 `return`；所有退出路径如下：

   | 路径 | 返回值及证据 |
   |---|---|
   | 未知 flag；缺少 `--` 而遇到命令名 | 64，53–56 行 |
   | 无参数、只有选项或 `--` 后没有命令 | 64，61–64 行 |
   | `--cwd` / `--tail` 位于最后，缺少 `$2` | 本机 Bash 隐式退出 1，33、42、46 行；确与测试失败码碰撞 |
   | 参数齐全的 `--cwd` / `--tail` | 继续执行，解析本身不退出 |
   | 非空 cwd 无法进入 | 65，71–74 行 |
   | 正常执行外部命令 | 81 行后**立即** `RC=$?`，没有中间语句污染；96 行原样退出 |
   | 命令找不到／不能执行 | shell 状态通常为 127／126，同样经 82、96 行传出 |
   | 日志创建或打开失败 | 本机重定向失败为 1，命令未启动，随后仍输出测试失败头 |
   | 失败摘要中的 `tail` 再失败 | 在当前无 `errexit` 的调用方式下，不覆盖已保存的 `RC` |

   因此，**正常命令路径保留退出码成立，“所有路径都等于被包裹命令退出码”不成立。**

   **建议：**检查日志创建结果，明确报告 wrapper 初始化错误并使用约定的设施错误码。

3. **死信断言是字段契约修正，但不能证明“默认不落正文”。（问题 5）**

   [test_episode_worker_retry.py:239](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/backend/tests/unit/test_episode_worker_retry.py:239) 只检查不存在 `episode_body_full` 键。生产 [episode_worker.py:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/backend/app/services/episode_worker.py:244) 展开 `task.to_dict()`，而 **108 行仍写入 `episode_body[:200]`**。本测试的 17 字符正文会完整保存在 `record["episode_body"]`。

   所以测试注释 237–239 行、UAT:319 的“默认只留 hash + length／不落全文”不准确。**生产行为是存量，本卡新增的是过宽的验证声明。**

   两条修正的其余部分成立：

   - 分组期望是固定字面量 `"canvas-test__semantic"`，符合生产 583–601 行的边界转换，没有调用生产 helper 求期望。
   - `task.group_id == "canvas-test"` 是独立不变量，能检测“调用参数正确、原始 task 却被改写”的回归。
   - SHA 和长度从固定正文独立计算，没有从生产结果反取，也不会随生产 helper 一起漂移。

   **建议：**将本卡声明收窄为“默认省略 `episode_body_full` 键，hash/length 正确”；正文摘要字段的存量问题另行处理。

4. **47 条 skip 中确有 4 条原本为绿的测试，属于已登记的覆盖损失；三列账没有造假。（问题 3）**

   独立比较 nodeid 集合，并将 skip 明细通过源码行号映射回测试，结果：

   | 文件 | 实际新增 skip | 其中原本为红 |
   |---|---:|---:|
   | `test_memory_service_write_retry.py` | 18 | 18 |
   | `test_graphiti_json_dual_write.py` | 11 | 8 |
   | `test_story_30_10_idempotency.py` | 9 | 9 |
   | `test_failure_observability.py` | 3 | 3 |
   | `test_qa_38_6_scoring_reliability_extra.py` | 2 | 2 |
   | `test_story_38_6_scoring_reliability.py` | 4 | 3 |
   | **合计** | **47** | **43** |

   证据：`skip-detail-20260906T133844.txt:15–61`。其中 memory 的 18 条在 15–32 行，**全部是跳过，没有任何一条算作修复**。

   集合复算为：红基线与开工均 **247**，完全相同；收工 **202**；减少 **45＝43 跳过＋2 修正**，新增红 **0**。总体也能对齐：

   ```text
   通过数：4602 + 2 修正 + 5 新测试 - 4 被关闭 = 4605
   跳过数：1 + 47 = 48
   ```

   证据：`unit-pre-20260906T132440.txt:3531`、`unit-post2-20260906T134314.txt:3039`；两条 hash 断言的独立通过记录在 `reconcile-e-fixed-20260906T135119.txt:18–20`。

   额外四条确实原本通过：

   - `TestGraphitiJsonDualWrite::test_fire_and_forget_doesnt_block_return`
   - `TestGraphitiJsonDualWrite::test_timeout_protection`
   - `TestGraphitiJsonDualWrite::test_config_flag_disables_dual_write`
   - `TestAC3StartupRecovery::test_recover_no_file`

   将基底源码收集顺序与开工进度串对照，前三条对应 `unit-pre:112` 的第 2、4、5 个 `.`，第四条对应 `unit-pre:241` 的第 9 个 `.`。因此不是仅靠“不在红名单”推断为绿。

   **建议：**恢复仍有效的四条检查，并逐项核对旧测试与新五条测试的覆盖关系。UAT:327–342、424–427 已如实登记这些限制。

**LOW**

5. **验收单列出的三条 wrapper 瑕疵均不足以上调到 HIGH，但登记还不完整。（问题 2）**

   - **成功路径静默：LOW。**没有摘要，也不公布成功日志路径，影响可观测性；不改变退出码。证据：脚本 84–94 行仅在失败时输出，UAT:216。
   - **缺参返回 1：LOW。**确有用法错误与测试失败混淆，但当前六处调用都提供参数。路径有些来自带引号的变量，并非 UAT:223 所说全部是字面量；“不会缺少参数位置”的结论仍成立。
   - **BSD 文件名保留 `XXXXXX`：LOW，接近纯外观问题。**随机后缀仍保证唯一性；证据：`canary-d-extra-20260906T133746.txt:19–24`。

   另有一项未登记的参数校验不足：46 行不验证 `--tail` 是否为有效数字；非法值会使 91 行摘要失败，成功命令则完全不会暴露该错误。它不覆盖已保存的退出码。建议与缺参校验一起整理。

6. **默认模式测试未隔离环境，合法配置可能产生假红。（问题 5、6）**

   测试 fixture 49–58 行没有清除 `DEAD_LETTER_STORE_FULL_BODY`。生产 230–232、253–254 行允许 `true/1/yes/on` 开启全文字段，此时新增的 239 行断言必然失败。

   **建议：**该用例显式清除环境变量，确保测试的确运行在其声称的默认模式。

7. **Stop 的真实非零测试结果仍映射到 exit 2，但“阻断→放行：无”不准确。（问题 4）**

   减掉的是旧版 **47–49 行外层 catch 中的 `e.status === 2` 分支**。新版 [stop-test-runner.js:50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/.claude/hooks/stop-test-runner.js:50) 至 63 行统一捕获测试阶段异常，非零退出、启动失败和超时均走 `exit(2)`，协议保住。

   实际存在两类放宽：

   - 前置 `execSync` **最终抛出 status=2**，旧版阻断，新版外层 67–69 行放行。普通 git 返回非零已被 35 行 `|| echo ""` 吞掉，两版都如此。
   - 测试返回 0，但旧截断输出包含 `FAILED`／`ERROR`，旧正则可能误拦；新版取消这种误报。

   UAT:367 写“无”，368–369 又承认第一项，措辞自相矛盾。**建议改成“真实非零测试退出未改为放行”，再列出上述边界。**

8. **两处文案需校正。（问题 6）**

   UAT:6 写“10 个测试文件”，实际为 **9 个测试文件＋4 个配置／脚本文件＝13**。UAT:312、424 所说“每条 skip reason 都直指新文件”也过宽，`skip-detail:56–61` 的恢复测试理由只写需要另行设计。建议修正文案；不影响三列账。

范围复核没有发现额外越界：九个 Python 文件从原始 `f19dcff6` 到格式化后的 `33fd106d` **AST 全等**，格式差异确为 `+108/-334`；最终 13 路径集合与原始抽取面一致。`66d6a835` 不是 HEAD 祖先，区间没有 merge commit。三份禁改文件的基底与 HEAD blob 全部相同；相关存档为 `judge-78-20260906T134325.txt:4–5、24–40`。

总体判断：**定点抽取没有回退主干，43／2／0 对账可信；但前端退出码传播尚未修完整，wrapper 初始化失败和死信保证的表述也需补正。** 本次没有重跑会写产物的 pytest 或触发真实 push，运行结论限于已有 transcript、独立集合／AST 对照及上述无文件写入探测。


