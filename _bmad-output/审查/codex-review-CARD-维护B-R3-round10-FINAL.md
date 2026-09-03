BLOCKER/HIGH 清零：否

## 实跑锚点

- WT HEAD：`e3ee51d7882b8ef18bc9452f7b183f2687ce9510`
- 指定 pytest：`281 passed, 14 warnings in 46.97s`
- 首次在只读沙箱中因无可用临时目录而未进入收集；随后仅以同一指定命令完成运行。没有运行其他测试命令。

## 上轮处置逐项复核

- ✅/⚠️ `%%` 硬断点：安全处置成立。[recap_scan.py:2813](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2813) 先在 `text_raw` 上判死，[recap_scan.py:2820](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2820) 后剥闭合注释，错误最终在 2960–2964 保留并返回 1；未发现 fail-open。但它拒绝全文任何相邻字面 `%%`，包括 frontmatter、围栏和 inline code。若契约是“全文禁 token”，这是有意保守；若只禁真正的 Obsidian 注释，则是误伤。r30 确为 5 报1放，[test:5475](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5475)，但只测了一个正文位置；单 `%` 对照不能防止未来实现误写成“全文累计两个 `%` 即拒绝”。此外 r30 声称证明“校验前剥掉”，实际所有样例先被 raw gate 判死，strip 删除后门仍会全绿。

- ✅ 第八形态的四个具体修复和“不带 closer”独立条目成立。[recap_scan.py:2335](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2335) 已拒绝双空格、tab、inline-code、highlight；不带 closer 的两案位于 [test:5303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5303)。

- ❌ H3 没有闭合，存在第九形态。`_h3_wellformed` 只判形状、不判段名；`### 其他`、`### 种子 (说明)`、`### 种子 ^id` 可被判“wellformed”，却不是受绑定的种子小节，于是 `_cur_bad=False` 并跳过其下台账行。源码自己已承认该缺口，[recap_scan.py:2268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2268)，实际状态路径在 [recap_scan.py:2349](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2349)。另有 1–3 空格缩进的 Obsidian/CommonMark H3 不会更新状态，可继承前一合规 H3 的安全状态。属 HIGH。

- ⚠️ 首个 H3 前的裸模板缺口已修：`_cur_bad=True` 确实在 [recap_scan.py:2345](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2345)，r27 也有独立承重案。但漏网门仅识别 `_SEED_LEDGER_LINE_RE`；首个 H3 前的 ``批注 `999` 条``、`批注 ==999== 条` 两种 raw/visible 正则均不命中，仍无人检查。故只能判“裸形态已修”，不能判区间闭合。

- ⚠️ `tips_open` / `derived_children_count` 确已逐节点接线：字段产生于 [recap_scan.py:483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:483)、[recap_scan.py:3154](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:3154)，验证按 `row_by_node` 在 [recap_scan.py:2169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2169) 比较。裸十进制篡改会红；但绑定只认 `\d+`，inline code、highlight、分组数、小数等可让标签可见而绑定零命中。因此“篡改必红”仍过宽。r31 又只直调 helper、只用一个节点，未证明跨节点身份或单字段独立 presence。[test:5414](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5414)

- ❌ “假声明已删”只对主实现成立；测试源码仍写着“没有逐节点对应字段，不绑定”，与 r31 自己矛盾。[test:4858](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4858)

- ✅/⚠️ “定界宽、赋值窄”的核心链成立：分隔符进入 token，[recap_scan.py:1675](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1675)；含分隔符 token 在 [recap_scan.py:1888](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1888) 得到 `None`；D2 区间、普通计数及 fallback 三个调用点均会上报 `None`。但有两项旁效应：

  - 本轮引入误伤：`_NUM_RUN_PAT` 允许分隔符单独成 token，fallback 的 `#### 派生，说明` 会把普通 `，` 报成“无法验证的数字”。[recap_scan.py:2752](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2752)
  - “赋值窄”没有覆盖预归一化。合法分组正则允许分隔符旁出现整个 `_D2_JOIN_ONE`，其中含空白和可见词“约”等；`1, 002`、`1,约002` 会先被归成 `1002` 再赋值。[recap_scan.py:1841](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1841)、[recap_scan.py:1457](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1457)

- ❌ A1 软换行仍是 BLOCKER。D2 在 [recap_scan.py:1988](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1988) 按源码行遍历；`本板共有\n987654 个子节点` 的第一行有句式无数字、第二行有数字无句式，第二行在 [recap_scan.py:2067](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2067) 被跳过。

## 变异证据与行为门

- ✅ 当前静态为 71 个 mutant key、78 条 designation edge；`DESIGNATED_COUNT_EXPECTED=78` 是独立 literal。[negverify:1080](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1080)
- ✅ collect-only rc、列表内去重、pytest `rc==1`、失败数及 `failed_ids == set(designated)` 均已实现。[negverify:1145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1145)、[negverify:1160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1160)、[negverify:1265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1265)
- ✅ `survivor-67~70` 指名正确。
- ❌ `survivor-71` 不成立。它把三位分组改成一位分组，[negverify:818](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:818)，会先破坏合法 `1,005`；指名测试在 [test:5552](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5552) 立即红，后面的 `1, 2` 安全断言根本未执行。因此是目标无关先红。
- ⚠️ 精确失败身份比较以同一份可修改的 `DESIGNATED` 同时充当执行目标和期望，只冻结了总数，没有独立冻结映射身份；把 nodeid 换成另一个真实且同样会死的门仍可自洽。dict literal 的重复 key 也会在 preflight 前被 Python 覆盖。
- ⚠️ `survivor-14` 仍只有宽泛性质关联；`survivor-29` 虽同样指名宽函数，但该函数开头存在直接 `_visible_text` 断言，关联相对实。锁窄窗仍在 [negverify:1211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1211)；改副本能解决原件残留，但不能解决 stale lock。还原 hash 又使用可被 `python -O` 移除的 `assert`。[negverify:1262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:1262)
- ⚠️ r27 宣称“15 形态、9 报6放”，实数是 10 报5放。[test:5238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5238)
- ⚠️ r29 文案仍说“分隔符一律删除”，与其后“仅合法分组归一、含糊分隔不赋值”的断言相反。[test:5511](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5511)
- ⚠️ r29/r30 仍以 `returncode != 0` 加宽泛关键词判断；没有要求 `rc==1`、无 traceback/`CHILD_CRASH_MARK`。因此生产崩溃且 traceback 恰含关键词时仍可能假绿。[test:5483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5483)、[test:5541](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:5541)

## 另外仍可达的分叉

以下均为本轮审查新发现；按源码注释判断多为存量，但因遵守禁令未用历史 diff 确认引入提交。

- ❌ BLOCKER：H2 标题本身不进 D2。标题用于切段，body 从 `h.end()` 开始；可见的 `## 本板共有 987654 个子节点` 不会进入数字循环。[recap_scan.py:1960](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1960)
- ❌ BLOCKER：`数据来源与新鲜度` 整段无条件豁免，可直接在合法段内放置虚假全板计数；其后缀匹配还与 `_SECTION_RE` 分叉，空格或 ASCII 括号后缀同样出域。[recap_scan.py:1973](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1973)
- ❌ BLOCKER：inline-code 豁免不是字段值白名单。`` `本板共有987654个子节点` `` 因含非 countish 字符会被整段挖空，Obsidian 却完整显示它。[recap_scan.py:1559](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1559)、[recap_scan.py:1983](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1983)
- ❌ HIGH：`_visible_text` 和数字字符集仍是封闭枚举；highlight、math、Arabic-Indic 数字等可形成“有 claim、无 token”。源码也已承认 `1\*5` 按 15、`5多个` 按 5 的存量 fail-open。[recap_scan.py:1742](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1742)、[recap_scan.py:1478](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1478)

## 闭合分类

一次局部改动可闭合：

- H2 标题纳入 D2；豁免标题真正共用 `_SECTION_RE`。
- H3 不再以“任意 wellformed 标题”作为安全状态；补缩进 H3 和格式化漏网行。
- 尾字段出现标签却无法解析数值时 fail-closed，并补双节点、单字段、CLI 门。
- num-run 要求至少含一个数字字符；合法分组不得吞空白或“约”等可见文字。
- 修正 r27/r29/旧假声明，拆分 survivor-71，门统一要求预期 rc 且拒绝 crash。
- hash 检查不用 `assert`；锁改为进程退出自动释放的 OS 锁。

需要重做设计：

- A1：从源码行改成 Obsidian 渲染段。
- inline code、highlight、math、block-id、Unicode 数字及 `_join_free` 的统一渲染语义。
- 整段豁免改成字段级正向允许；台账按角色定义允许内容并覆盖 seed/derived。
- 变异器改在隔离副本运行，彻底避免修改生产源文件。

验证限制：未运行 `recap_domain_negverify.py`，未核验自报的 `71/71` 和 `613 passed`；未读 fixtures 的 `.md/.json` 正文，未创建探针或临时文件，未执行 `git diff`、`git show` 或 `git log -p`。新增绕过为两路独立静态路径复核，未按你的限制做运行时复现。


