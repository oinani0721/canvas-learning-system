BLOCKER/HIGH 清零：否（就计数取值口径而言）

终判：**FAIL，0 BLOCKER / 3 HIGH**。round-3 所列整改在代表形态上成立，但端到端仍有以下取值通道。

### 仍存 HIGH

- ❌ **HIGH（存量）：D2 区间只可能终核右端。** `_range_ok` 发现任一端无出处时保留原串，注释声称随后“逐个判”，但普通循环只提取紧邻量词的右端。[recap_scan.py:1661](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1661) [recap_scan.py:1664](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1664) [recap_scan.py:1712](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1712)  
  静态反例：`本板共有987654-0个…`。左端不在池时区间不被挖空，随后只按右端 `0` 查池；任一非空基础池都会由 `abs(a-a)` 生成 0。[recap_scan.py:1478](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1478) 现门只测了相反方向 `1-987654`，没有覆盖“大数在左”。[test_recap_scan_signals.py:2165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2165)

- ❌ **HIGH：fallback 没有整串小数/逗号防线。** D2 的逗号归一化和两道小数检查仅存在于 D2 路径；fallback 直接对原行执行 `_NUM_RUN_RE.findall()` 并逐片入池。[recap_scan.py:1650](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1650) [recap_scan.py:1687](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1687) [recap_scan.py:1972](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1972)  
  因此 fallback 标题中的 `0.0个`、`零点零个` 会按 `[0,0]` 查池；`1,005个` 会按 `[1,5]` 查池。读者所见值与进池值不同。新门的小数案例只走 `d2()`；fallback 部分只测空格/标记、`廿五`，没有小数或逗号。[test_recap_scan_signals.py:3483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3483) [test_recap_scan_signals.py:3491](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3491)

- ❌ **HIGH：D2 小数/分隔符仍非渲染语义定界。** `_CJK_DECIMAL_RE` 要求数串与 `[.点]` 直接相邻，连接字符不能包住小数点。[recap_scan.py:1539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1539)  
  `本板共有987654<b>.</b>0个…` 渲染为 `987654.0`，但两道 decimal guard 均不命中，普通循环只按尾部 `0` 查池。类似地，逗号归一化只认 ASCII `,`；`987654，000个` 的全角逗号会让循环只取 `000`。[recap_scan.py:1406](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1406) [recap_scan.py:1650](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1650)

### 四问结论

1. ✅ **还有其它“进池值 ≠ 渲染数”路径。** 上述区间左端、fallback 小数/逗号、标签包裹小数点及全角分隔符均成立。`_join_free` 的可见字符过拼接本身也仍是字面不等，但我不单独把它升为 HIGH；真正的 HIGH 是上述可静态推出的欠拼接/尾片重锚。

2. ⚠️ **三张表登记仅 PARTIAL。**
   - `_CJK_NUM`：✅ 12 个赋值字符与独立写死期望一致，登记诚实。[test_recap_scan_signals.py:3135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3135)
   - `_NUMERAL_LIKE_CHARS`：⚠️ 代码明确是封闭枚举，UAT 也承认；但测试只做子集包含，连声明中的 `卌` 和多种异体都未精确锁定。[test_recap_scan_signals.py:3168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3168)
   - `_D2_QUANT`：⚠️ 表外量词会让整条计数零命中，并非“无法解析”式 fail-closed；且区间正则仍手抄旧 11 字量词表，与 `_D2_QUANT` 分叉。[recap_scan.py:1393](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1393) [recap_scan.py:1434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1434)
   - UAT §五之三还残留已删除的 `_D2_COUNT_RE`、旧的空白切断行为和“12 条变体”等过期陈述，且未登记上述三条 HIGH，因此不能判“登记完整诚实”。[UAT:447](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:447) [UAT:452](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/_bmad-output/验收单/UAT-CARD-维护B-R3-中文数词终态-2026-09-02.md:452)

3. ⚠️ **“定界宽、赋值窄”局部成立、端到端不成立。** 对已经被完整捕获的 token，D2 与 fallback 都调用 `_join_free → _count_token_value`，`None` 均报错，赋值确实窄。[recap_scan.py:1712](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1712) [recap_scan.py:1972](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1972)  
   但范围端点是第三条直接 `int()` 入池路径；fallback 又缺少 D2 的复合数前处理，所以“两个消费点全程同一口径”不成立。

4. ⚠️ **新门总体非空，但有证据空洞/宽措辞。**
   - ✅ `_one_problem_has` 的双 needle 调用确实要求类别与 token 在同一输出行。[test_recap_scan_signals.py:3425](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3425)
   - ❌ `980,005` 门只要求拒绝且某行出现 `980005`，没有同时绑定“找不到同值来源”；改成“无法解析 980005”仍会绿，不能证明“按 980005 查池”。[test_recap_scan_signals.py:3520](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3520)
   - ⚠️ “D2 与 fallback、CJK 与 ASCII 走同一条取数规则”比矩阵实际覆盖宽；fallback 小数就是反例。[test_recap_scan_signals.py:3445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3445)
   - ✅ survivor-15、16 的替换分别绕过共享判值器和共享定界集，确实禁掉两消费点的对应防线。[negverify.py:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:197) [negverify.py:207](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:207)
   - ⚠️ survivor-17 确实摘掉 D2 的唯一 `点` 小数防线，但不能证明 fallback 小数性质；fallback 原本就没有该防线。[negverify.py:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:217)

### 实际运行

- 指定 pytest：有效执行收集 **256**，结果 **256 passed, 15 warnings in 34.71s**。首次在只读沙箱中因无可用临时目录于收集前退出；随后以相同命令获临时目录权限重跑成功。
- `git rev-parse HEAD`：`c5612ee22f71c0e78df5838babf29e78128bdf95`
- 因计数正好为 256，未运行 `git status`。
- 未运行 negverify、任何探针或变异，也未读取 fixtures 正文；车道提供的 17/17、588 passed、35/35 仅作为车道证据，不冒充本轮亲跑结果。


