本轮结论：**BLOCKER 0 / HIGH 1 / MEDIUM 0 / LOW 3**。审查绑定 `71a85acf`；**round 1 HIGH-1 尚未关闭**。

**BLOCKER：无。**

**HIGH-1 新校验仍能放行非 ASCII 数字，导致闹钟取消。**  
位置：[scripts/deploy-vault.sh:581](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:581)，以及同文件 `:587、:621`。

未被拦下的输入：`LC_ALL=ar_EG.UTF-8`、`CLS_NPM_BUILD_TIMEOUT='٠٥'`。本机原校验片段的独立重放结果为：

```text
数字门：通过
两次数值比较：报 integer expression expected，rc=2
整个校验：仍通过
Perl alarm 剩余时间：0
```

该 locale 下 `[0-9]` 接受了阿拉伯数字；随后两个比较错误被当作条件不成立，最终执行 `alarm 0`。对照输入 `005` 正确归一为 `5`，闹钟剩余 `5` 秒。现有四个非法值用例及 `negctl2` 均未覆盖这条路径。

**MEDIUM：无新增问题。** round 1 MEDIUM-2 的退出码碰撞已修复；MEDIUM-1 的脱组后代仍是能力边界，不能解释为已经清空进程树。

**LOW-1 `_reap` 在 PID 复用时可能误杀无关进程。**  
位置：[backend/tests/unit/test_deploy_vault_sh.py:2775](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:2775)，以及 `:2801–2802`。

门未覆盖的路径：原进程退出后，PID 在存活检查、清理调用或 TERM→KILL 的间隔内被同 UID 进程复用；代码只核裸 PID，甚至已经判定 `gone=True` 后仍再次发送信号。这是低概率的实际误杀风险，本轮未修。

**LOW-2 负控驱动没有执行预期红绿判定，也未保存具体失败断言。**  
位置：[negctl2-20260914T202240.txt:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-deploy-timeout/negctl2-20260914T202240.txt:16)，至 `:22`。

负控输入：预期 RED 实际 GREEN，或还原后实际 FAIL；`rc` 与预期参数 `$3` 均未使用，函数仍随 `printf` 成功返回。这里已有 `pipefail`，**本次不是 tail 吃掉 rc，而是取得后弃用**。此外，`tail -3` 只留下失败 nodeid，不能排除该测试因端口、fixture 等其他原因变红。

**LOW-3 头注仍有超出实现的承诺。**  
位置：[scripts/deploy-vault.sh:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:74)，以及 `:76、:79`。

门未覆盖的路径：build 成功后，`:641–645` 的目录创建或复制因文件系统卡住，alarm 已取消，因此不能保证“本步骤按时返回”。另有两处事实不符：不是所有超 uint32 值都取消闹钟，`4294967297` 会截成 `1`；实际 `:603` 使用 PATH 中的 `perl`，并未固定 `/usr/bin/perl`。

其余问题的复核结果如下：

- **⓪ 取值组合：**在已测 C、en_US locale 下，`+5`、空白、全角数字、零值和越界值均被拒；空环境值按 `:99` 回退为 `300`。极长零串最终也拒绝，但十万零的剥零操作实测约需 14 秒，发生在 alarm 安装前。合法 ASCII 输入的 `_cap` 同时用于 alarm 与文案，二者一致。
- **① 带外标记：**正常 npm stdout/stderr 已与捕获管道断开，`exit 124` 不再伪装成超时。`$$` 在命令替换中仍是外层 Bash PID；即使两次标记相同，也没有共享捕获通道。固定前缀保证非空，`*"$_mark"*` 将变量中的 `*`、`[` 按字面匹配。这不构成抵御同 UID 子进程主动操纵 Perl 控制器的隔离保证。
- **② kill 短路：**返回值是发送操作成功计数，此处为 0/1，不是实际终止人数。组不存在时返回 0，继而尝试单 PID；仅剩 zombie 时，成功也不能证明有活进程处理信号，但不存在因此漏杀活成员的问题。本工具沙箱拒绝了组信号实验，故未把正常 macOS zombie 情形写成实测结论。
- **③ 测试隔离：**参数化实例各有独立 `tmp_path`，`bin`、`npm-pids` 都新建；上一例文件不会使非法值断言假绿，残留记录反而会使其变红。8251–8259 没有被这些假 npm 监听；外部占用会造成前置失败。`005` 快构建对照只证明接受该值，并未测出实际等待五秒。
- **⑤ 三段变异：**m1 的 `3 failed / 1 passed`、137 秒耗时及挂起对照通过，m2 仅 rc124 对照失败，m3 删除 offline 后 fast 用例失败，均支持作者解释；**未发现已证实的其他致红原因**。但具体归因属于源码与对照支持的推断，日志本身没有保存失败断言。不能因此宣称所有输入路径都有覆盖。

round 1 LOW-3 的记录已订正为 `probe_diff_rc=1 / real_diff_rc=0`；但该文件仅三行，未提供比较集合或驱动，无法独立重算“失败逐条与基线一致”。

最后，两个代码文件的 SHA256 与负控跑前、还原后完全一致；步 2 至 EOF 的 **33,631 字节**与基线逐字节相同，摘要为 `96d10556a71e71c3702fd20ae4cb31f4a1c6acab3cc2b3317e8d40abe5789819`。证据中的定向测试为 **9 passed**，文件级为 **145 passed / 9 skipped**；全量 unit 则是 **35 failed / 29 errors，rc=1**，并非全绿。

本轮未修改文件，未运行 pytest、真实构建、部署或数据库连接。


