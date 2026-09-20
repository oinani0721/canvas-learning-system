**round-12 仍不通过：五文件内确认 4 项 HIGH、13 项 MEDIUM、2 项 LOW；BLOCKER 无。** 审查绑定 `8333b1a4ee82311d58fe7b3859836d1f11714ea3`，以本机 Darwin / Python 3.14.4 实测为准。已登记分歧仍照报。

两份时区副本均已复现；以下解析器问题主要定位到 `scripts/local_tz.py`，同样存在于 [backend 副本](backend/app/core/display_tz.py)。

**BLOCKER：无。**

**HIGH**

1. **H1：引用名仍能回溯成裸名，造成误收、误算。**  
   [scripts/local_tz.py:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:96)  
   复现：`TZ='<AAA1><BBB2'`，libc 冬夏均为 UTC，实际 `display_tz()` 冬季 −01:00、夏季 −02:00。引用分支后续失败后，第三支把名字重新拆成 `<AAA` 和 `><BBB`。**“找到 `>` 后禁止裸名回退”尚未落实。**

2. **H2：偏移里的冒号解析失败后，被重新解释成 dst 名。**  
   [scripts/local_tz.py:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:97)  
   复现：`AAA1:`，libc 全年 UTC，实现冬季 −01:00；`AAA1:30:BBB2`，libc UTC，实现冬季 −01:30、夏季 −02:00。小时后分钟、分钟后秒两处都有这个回溯缺口。

3. **H3：灾难性回溯没有消失，202 字符即可阻塞约 3 秒。**  
   [scripts/local_tz.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:95)  
   复现：`parse_posix_tz('A' + '١' * n + '+')`，`n=50/100/200` 耗时约 **0.013/0.197/3.054 秒**，翻倍约增长 16 倍；Unicode 数字同时落入多个重叠量词。ASCII 的 `'A'*n+'+'` 也仍呈平方增长。原来的 `...+'!'` 现在可被名字分支完整匹配，已经不能验证失败路径。**恢复 1024 上限也挡不住上述短串。**

4. **H4：长数字触发未捕获异常，实际入口直接失败。**  
   [scripts/local_tz.py:118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:118)  
   复现：`TZ='AAA'+'0'*4300+'1'`，libc 接受并给 −01:00，两份 `display_tz()` 均抛 `ValueError: Exceeds the limit (4300 digits)`。偏移、切换时刻、M/J 规则的多个数字字段均可触发；仅捕获后拒绝仍会留下误拒。

**MEDIUM**

1. **M1：空裸名在 std、dst 两侧都被误拒。**  
   [scripts/local_tz.py:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:96)  
   复现：`TZ='1'`，libc −01:00，实现 UTC；`AAA1+2`，libc 冬 −01:00、夏 −02:00，实现 UTC。C 库允许的空名不只 `<>`。

2. **M2：Unicode 数字位于 dst 名开头时仍被误拒。**  
   [scripts/local_tz.py:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:97)  
   复现：`A1١`、`A1１`，libc 将 Unicode 数字作为 dst 名，冬 −01:00、夏 UTC；实现退 UTC。`\d+` 已经吞错字段，后置 ASCII 检查无法修正分词。

3. **M3：总览门拒绝解析器与 libc 都能生成的合法偏移格式。**  
   [review_overview.py:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:134)，[test_review_overview.py:398](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/unit/test_review_overview.py:398)  
   复现：把 `AAA15`、`AAA1:00:01` 实际生成的 `…-15:00`、`…-01:00:01` 与对应自报时区送入五空桶门，均被判“generated_at 非生产器形态”。正则仅允许小时 ≤14 且不允许偏移秒；单测还固化了 `+15:00` 的误拒。

4. **M4：`future` 判据错误假设本地日期随 UTC 单调增加。**  
   [review_overview.py:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:620)  
   复现：`AAA0BBB-1,M3.2.0/0,M11.1.0/0:30`，参照 `2026-10-31T23:15Z` 是本地 **11月1日 00:15+01**；未来到期 `23:45Z` 却是 **10月31日 23:45+00**。libc 与实现一致，但合法 `future` 行被 `day <= ref_day` 拒绝。

5. **M5：消费者绕过前导冒号的路径语义。**  
   [review_overview.py:540](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:540)  
   复现：`producer_tz=":AAA-1"`、`generated_at="2026-09-16T13:00:00+01:00"`，五空桶门放行；同串作为 TZ 时，libc 和 `display_tz()` 都为 UTC。这里直接调用解析器，得到 +01。影响是坏投影的接受域不一致；正常生产入口不会自报这个 key。

6. **M6：`UTC0` 例外只写进注释，没有接入判据。**  
   [test_g6_9c_single_tz_source.py:1012](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:1012)  
   复现：`_libc_accepts("UTC0")` 返回 False，解析器接受；补入组合后，阶段一立即判“误收”，**到不了**注释声称能处理行为等价的阶段二。`<UTC>0` 相同。

7. **M7：非零星期和结束切换时刻仍未被探针区分。**  
   [test_g6_9c_single_tz_source.py:969](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:969)  
   两个独立内存变异都让原 **98,532 组合、222,054 换算点、四锚全部 PASS**：
   - 所有星期强制按周日算：现有串 `AAA0BBB,M3.2.3,M11.1.5` 在 `2026-03-09T12:00Z` 应为 UTC，变异后 +01。
   - 忽略显式结束时刻：现有串 `AAA0BBB,M4.1.0,M10.1.0/3` 在 `2026-10-04T01:30Z` 应为 +01，变异后 UTC。

8. **M8：已取消的控制字符收紧仍被测试静默豁免。**  
   [test_g6_9c_single_tz_source.py:1030](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:1030)  
   复现：内存把名字字符类改回排除 `\x00-\x1f`，`AAA\t1`、`<A\tAA>1` 等从接受变拒绝，`_declared_narrowing()` 却全部认作“已声明收紧”。补样本也不能让这类退化正确变红。

9. **M9：分号误拒仍存在，不修理由不成立。**  
   [scripts/local_tz.py:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:100)  
   复现：`AAA1BBB2;M4.1.0,M10.1.0`，2026 年夏季 libc −02，实现 UTC。把分号换成逗号，`time.tzname` **同样**为 `('BBB','AAA')`；逐时刻 `tm_zone/tm_isdst` 仍正确。不能把这个元数据表现归因于分号。

10. **M10：年份分歧仍存在，“整体颠倒／64 位溢出”的归因证据不足。**  
    [scripts/local_tz.py:432](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:432)，[回归注释:439](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:439)  
    复现：2570 年北半球串在冬夏均为 UTC，南半球串在冬夏均为 +01；实现继续季节切换。观测更符合**固定在最后一个季节状态**，并非季节判断整体反转。省略规则族也仍有 `AAA1BBB` 在 2038 年夏季 libc −01、实现 UTC，以及 2006 年春季分歧。

11. **M11：24 小时相关收紧仍违反全域等价。**  
    [scripts/local_tz.py:349](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:349)  
    复现：`AAA24`，libc −24 小时、实现 UTC；`AAA12BBB-12,M3.2.0,M11.1.0`，两侧偏移可表示，但实现因差值 24 小时全年退 UTC。Python 表示限制是真实理由，但登记不能将它变成等价 PASS。

12. **M12：真实可用的系统 tzfile 路径仍被误拒。**  
    [scripts/local_tz.py:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:217)  
    复现：本机确实存在的 `/usr/share/zoneinfo.default/Asia/Shanghai`，libc +08，实现 UTC，因为路径没有独立的 `zoneinfo` 段。这是可直接复现的已声明路径分歧。

13. **M13：非 UTF-8 环境名字仍与 libc 不等价。**  
    [scripts/local_tz.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:291)  
    复现：`os.environb[b"TZ"]=b"\xff1"`，libc −01，实现 UTC。避免响应编码异常的动机成立，但当前方案仍改变机器时区结果。

**LOW**

1. **L1：显示名仍与 libc 不同。**  
   [scripts/local_tz.py:538](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:538)  
   复现：`TZ='<中>1'`，libc 名字为 `___`，实现为 `中`。这是已登记的显示差异，不影响本例偏移。

2. **L2：关键注释仍保留互相矛盾或错误的事实。**  
   复核对应代码／样本即可复现：
   - [scripts/local_tz.py:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:87)：仍称引用内容含 `<` 非法；`:72/:84` 仍称③单独守 NUL；`:128` 仍称未闭合名字进不到 `_strip_name`。
   - [scripts/local_tz.py:450](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:450)：裸 `n=365` 在闰年是 **12月31日**，不是次年元旦。
   - [回归文件:587](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:587)：仍引用旧的 `406.70/42/448.70`；`:1480` 仍描述已删除的独立 NUL 防线。
   - [回归文件:944](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:944)：`M11.1.5` 是**第一个星期五**，不是第五周。
   - [回归文件:1182](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:1182)：原来两条全角探针并非都被两道检查拦截；分别删除检查实测，它们本来就各自独占一道。
   - [回归文件:1080](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:1080)：声称三类收紧全部命中，断言却只要求两类；`:1212` 仍保留已过时的“只能末尾追加”约束。

**地盘外·移交 — MEDIUM**

[negctl.py:354](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g69cr2/scripts/negctl.py:354)：`rc != 0` 就可认作 RED，没有核验每个绑定 nodeid 都 FAILED。

复现：对原判定逻辑注入“collection ImportError、rc=2、没有 FAILED”或“一个绑定项失败、另一个通过”，均可得到合格结果。最新日志确实绑定本轮 HEAD、38 段均为 rc=1 且有断言摘录；**没有证据说本次实际发生了 collection ERROR**，但现有 runner 不能证明其声明的逐项失败条件。

对六个问题的直接回答：

1. **还有问题**，见上述分级。
2. 实测支持 `<` 名字的非对称词法模型，未发现需要另立第三种模型；但实现仍有 H1 的非法回溯。
3. **还有误收**，H1、H2 均在现有组合之外。
4. 非零星期、结束切换时刻是已证明的盲区。实际表里结束月份已不只 11 月；路径正例只有上海、start/end 绑整串、dst 偏移秒及独立越界仍是覆盖缺口，不能靠总向量数证明充分。
5. **删除③未发现新的 NUL 放行缺口**，字符类与完整串尾约束仍有效；删除长度上限则暴露 H4，而 H3 表明旧性能论证也不成立。
6. **按本轮“完全等价”判据，两条登记都不能销项。** 分号的不修理由被对照推翻；年份可以作为产品支持范围的取舍，但当前既继续接受又返回不同结果，仍是分歧。

全程未写文件、未连接网络或数据库；未运行会改源码的负控入口或完整归日链路。原组合门及两个存活变异均在内存隔离执行，最终五文件仍与审查 HEAD 一致。


