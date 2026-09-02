BLOCKER/HIGH 清零：否

## 主要发现

- ❌ HIGH（存量）：四空格围栏限制实际失效。[recap_scan.py:1022–1036](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1022) 虽声明 fence 最多缩进三格，但 `bare` 先用 `\s` 吃掉任意前导空白。因此顶层 `    ``` ` 会被错当成 fence，后续用户可见的 `本板共有 987654 个…` 会在 [recap_scan.py:1068–1075](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1068) 被挖空，D2 在 [recap_scan.py:1887](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1887) 看不到它。现有门没有 plain four-space pseudo-fence 用例。

- ❌ HIGH（本轮未闭合）：种子尾巴的覆盖确实扩大了，但也确实放松了接受集。[recap_scan.py:1262–1271](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1262) 新增 `（(【[` 后任意 `.*`。真实括号尾巴现在会进入首个 `tips_count` 绑定，这是正确改进；但 manifest 行  
  `- SeedA — 批注 2 条（理解度未闭环 999 条）`  
  在首个 `2` 对上后会于 [recap_scan.py:2142–2153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2142) 直接 `continue`，尾巴里的 `999` 没有任何绑定。相对于原先整行静默跳过，首数更安全；相对于新增的 fail-closed 形状门，这又是明确放宽。因此“覆盖扩大，不是放松”不准确，应是“两者兼有”。

- ❌ HIGH（存量未改）：tips 两数仍在 raw 文本上匹配，[recap_scan.py:2287–2301](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2287)。保留正确行再追加 `tips 批**注**共 999 条`，用户看见冲突数字，但该行不进入 `all_hits`。

- ❌ HIGH（存量未改）：③信号行虽在 visible 空间选行，但小节本身仍从 raw 标题提取，[recap_scan.py:1113–1115](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1113)。额外的 `### **③**` 在 Obsidian 可显示为同一标题，却不进入绑定；fallback 的段外判断同样使用 raw 小节，[recap_scan.py:2323–2327](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2323)。

- ❌ HIGH（存量未改）：D2 明确丢掉 H2 标题行。分段 body 从 `h.end()` 开始，[recap_scan.py:1891–1896](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1891)，所以 `## 本板共有 987654 个节点` 不进入 [recap_scan.py:1919–2062](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1919) 的取数循环。

- ⚠️ 存量设计边界登记属实：`_visible_text` 不是 Obsidian renderer；尤其无条件剥落单 `*`/`_`，可把用户看到的 `1\*5个` 按 `15` 查池，[recap_scan.py:1447–1460](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1447)。数词定界也是闭表，[recap_scan.py:1334–1341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1334)，Arabic-Indic 等可见数字仍可能完全不被提取。

## 本轮改动逐项

- ✅ 一次切行、同下标配 raw/visible 的修复正确，[recap_scan.py:2090–2128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2090)。HTML 实体解出的 CR/LF 折空格，[recap_scan.py:1766–1772](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1766)，也使目标行的一对一不变式成立。

- ⚠️ “逐个处理全部小节”堵住了首节诱饵，但范围超出意图：它搜全篇所有 `### 种子`，未限定父级 `## 台账`，也未排除代码块，[recap_scan.py:2092–2102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2092)。附录或其他段落中的同名小节会被强制套台账模板，属本轮误伤面。

- ✅/⚠️ `A&B` 对 `A&amp;B` 的 raw 未命中后继续走唯一 visible 候选是正确修复，[recap_scan.py:2154–2178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2154)。但“撞车仍 fail-closed”只覆盖 fallback 分支：raw 精确命中会直接 `continue`，不检查同一 visible key 是否还有其他 raw ID；[recap_scan.py:2116](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2116) 还会静默折叠重复 `node_id`。

- ✅ fallback ⑦ `m7` 改在 `_visible_text(ln)` 上绑定是正确的，[recap_scan.py:2336–2361](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2336)。

- ✅ 分隔表现在有至少 11 个互异字符且禁止重复，[test_recap_scan_signals.py:4566–4578](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4566)。这正确锁住“互异”要求；但成员仍由生产常量自身驱动，不锁“必须恰好是哪 11 个”。

- ⚠️ `_visible_block` 的 `== 3` 比旧 `>=5` 强，但只是源码字面行计数，[test_recap_scan_signals.py:4763–4779](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4763)。删除真实调用并增加死调用仍可维持 3；也未验证三个指定消费者。第 4756 行还残留“四处消费方”的旧措辞，与当前三处相矛盾。

## `preflight()` 与变异证据

- ✅ `preflight()` 已在仓库内，并在基线和任何源码变异前由主流程调用，[recap_domain_negverify.py:763–807](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:763)。当前源码静态可见 52 条、首 token ID 唯一、每个 old 锚点要求恰好一次。

- ⚠️ 能力边界基本诚实，但内部仍有过宽措辞：它只检查 `old != new`，没有检查空 `subs`、按真实顺序模拟整组替换、或最终源码确实变化；docstring 说“不证明替换非空”，成功消息却宣布“替换非空”。`MUTANT_COUNT_EXPECTED` 是同文件手工 tripwire，不是独立外部证据。

- ❌ “52/52 变红即逐条证明命名防线承重”仍不成立。`survivor-51` 仅把 visible 行退回 raw，[recap_domain_negverify.py:605–612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:605)；伪冲突行仍会被“非模板行”拒绝，真正变红的是合法强调行被误拒。`survivor-52` 删 raw 精确分支，[recap_domain_negverify.py:615–622](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:615)，主要制造归一碰撞误拒，错误数字仍 fail-closed。变异归因过宽的判断成立。

## 崩溃识别与行为门

- ❌ HIGH（门证据）：许多拒绝门只断言 `returncode != 0`，例如 [test_recap_scan_signals.py:4748–4750](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4748)。`run_verify()` 遇子进程 traceback 只是打印 marker 后返回，[test_recap_scan_signals.py:109–139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:109)。因此“受控拒绝”和“rc=1 崩溃”仍可同样令行为门 PASS；271 passed 不能单独证明所有负例都走了正常诊断路径。

- ❌ `E   <类名>` 与 `E     <续行>` 不是可靠二分。实现实际按 `^E {1,3}<标识符>` 判断，[recap_domain_negverify.py:678–699](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:678)。当前 pytest formatter 会给 exception-only 的每个物理行应用同一失败前缀，[pytest code.py:967–968](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/.venv/lib/python3.14/site-packages/_pytest/_code/code.py:967)、[code.py:1017–1020](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/.venv/lib/python3.14/site-packages/_pytest/_code/code.py:1017)；无额外缩进的多行 `AssertionError` 续行可能也是 `E   Expected: 3`，会被误判为崩溃。行为门只测试了 4–7 格续行，[test_recap_scan_signals.py:4618–4643](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4618)。反向还会漏掉无 traceback 的子进程退出；docstring 对“启发式、会漏会误报”的总边界是诚实的。

- ⚠️ `[[CHILD-CRASH]]` 在测试文件和 negverify 中各手抄一次，[test_recap_scan_signals.py:104–125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:104)、[recap_domain_negverify.py:675–677](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:675)，现有门没有把真实发射输出直接送入 classifier；单侧漂移可两边各自绿。

- ❌ R21 的“不得错绑到 SeedA”断言不具区分力：账本值为 9 和 2，报告却写 999，[test_recap_scan_signals.py:4811–4817](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4811)。绑对或绑错都会报 999，最终也只查诊断含 999，[test_recap_scan_signals.py:4834–4839](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4834)。

- ✅ 没再看到上一版那种“读自身源码、目标字符串就在断言里”的字面恒真门；R19 的 monkeypatch 哨兵及同一对象断言有效，[test_recap_scan_signals.py:4670–4680](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4670)。

- ⚠️ 仍有死分支/死防线：测试中的 `if False else` [test_recap_scan_signals.py:1468](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:1468)、参数永远非 `None` 的分支 [test_recap_scan_signals.py:1964–1970](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:1964)；生产侧 `_SIG_AGE_RE` 无调用，[recap_scan.py:883–887](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:883)，且 percentile dict 的二次守卫在 schema 成功后不可达，[recap_scan.py:1170–1178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1170)。

## 剩余整改分类

一次改动内可闭合：

- 修复 plain 四空格伪 fence，并补专门 CLI 门。
- D2 纳入 H2 标题行；tips 与③标题统一到 visible 空间。
- 把种子小节限定到 `## 台账` 父级并排除代码块。
- 为种子尾巴定义严格字段语法，逐字段绑定；至少禁止自由 `.*`。
- 校验 ledger raw ID 唯一；限制超长整数或捕获 `int()` 的 `ValueError`。
- 修正 R21 对照值、marker 端到端门、`run_suite()` 五元组注解，以及 preflight 的最终非空变异检查。

需要重做设计：

- 用 Markdown/Obsidian AST 或 fail-closed 的受支持语法子集替代 `_visible_text` 正则收敛器。
- 明确 raw node ID 与用户可见身份的碰撞策略。
- 让每个 mutant 绑定唯一用例和唯一错误方向，不能以宽泛 `-k` 中“任一失败”归因。
- 用结构化崩溃状态替代解析 pytest 展示文本；从原地改生产源码迁移到隔离副本。

实际验证：

- `git rev-parse HEAD`：`cbf5b411d7c6057e1bd96ee7c2e587a860d055d3`
- 指定 pytest：`271 passed, 14 warnings in 50.94s`

首次在只读沙箱内因 pytest 无法创建临时捕获文件而在收集前退出；获准按原命令重跑后得到上述结果。未运行 `recap_domain_negverify.py`，未复核自报的 52/52 或 603 passed，未手工读取 fixtures 正文，未构造探针/临时文件，未运行 `git diff/show/log -p`，也未修改工作树。


