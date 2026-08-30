结论：不能写「BLOCKER/HIGH 清零」。当前 `BLOCKER=0`，但仍有 4 项 HIGH。F2、F5b 已正确修复；F1、F3、F4、F5a 仅部分闭环。

## HIGH

1. F1/F4：fallback 与真实 manifest 的角色口径仍分叉

   [`recap_scan.py:469–476`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:469) 虽读取两种键生成 relation，但角色仍只检查原始文本中的 `derived-from`；后端则按两种键的解析值判断，[`board_manifest_service.py:476–498`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:476)。

   真实 `build_manifest` 临时 fixture 复现：

   - `derived_from: "[[Seed]]"`：fallback `seeds/derived=2/0、unsourced=null/0`；manifest `1/1、unsourced=0/1`。
   - `derived-from: null`：fallback `1/1、unsourced=1/1`；manifest `2/0、unsourced=null/0`。
   - 下划线情形还会出现 `counts.derived=0`、`relation_types.derived_from=1` 的内部矛盾。

   交叉测试仅覆盖有效连字符键；null 测试还把错误的 fallback-only 角色语义锁成预期，[`test_recap_scan_signals.py:390–432`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/test_recap_scan_signals.py:390)。

2. F3：无据行数字防护仍可绕过

   [`recap_scan.py:733–771`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:733) 只拦 ASCII `X/N` 或完整年龄标准式。以下均实测 `VERIFY PASS`：

   - `未答问题年龄：无据（最老 999 天）`
   - `重复堆积：无据（共有 99 条）`
   - `重复堆积：无据（3／7 条）`，使用全角斜线

   新回归仅覆盖 ASCII `3/7`，[`test_recap_scan_signals.py:760–776`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/test_recap_scan_signals.py:760)。

3. 规则 11 的行级绑定可借用同行档位

   [`recap_scan.py:757–802`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:757) 按“含 label 的整行”取值、只取首个数字匹配，并在整行任意位置寻找档位。

   将四条信号合成一行，再把来源覆盖率从应有的 `【文件】` 改成 `【实测】`，同行其他信号保留 `【文件】`，仍然 `VERIFY PASS`。这直接违反“四行一行都不能少、逐行全等”的 [`SKILL.md:267–269, 308–312`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:267)。

4. fallback 派生子女无据红线仍可被同义句绕过

   fallback 明定派生子女恒无据，[`SKILL.md:171–179`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:171)，脚本也将 `derived_children*` 置为 `None`，[`recap_scan.py:1167–1179`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1167)。

   但 Step 4 又建议写“无派生”，且 verifier 词表遗漏该同义句，[`SKILL.md:192–194`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:192)、[`recap_scan.py:709–716`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:709)。加入 `SeedA 无派生。` 后实测仍 PASS。`counts.relation_types.derived_from` 只能证明关系类型聚合，不能支持单个 seed 的子女数断言。

## MEDIUM

1. F4 归一并非幂等。对合法 `[[节点/None]]`，fallback 得到 stem `None`；manifest 先经后端解析为 `None`，再被 `_strip_note_ref()` 当空值清除。manifest 的 `relation_target` 又未走相同归一，[`recap_scan.py:226–242, 385–392`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:226)、[`board_manifest_service.py:132–143`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:132)。普通 null/~/none 的大小写、空白处理本身通过。

2. F5a 顶层非 dict 已修，但子对象 schema 仍 fail-open。[`recap_scan.py:752–802, 875–882`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:752) 不校验必需字段、availability 枚举或“无据 ⇒ value=null、denominator=0”。四个子对象都只保留 `{"availability":"无据"}`，报告写四条无据，实测仍 PASS。

3. 信号没有真正限定在 ③ 段。[`recap_scan.py:748`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:748) 只在下一个 `###` 停止，不在后续 `##` 停止；把四行移到 `## 附录` 后仍 PASS。

## LOW

1. F6 核心缺口已补且有真实 `build_manifest` 兜底，但手工 fixture 仍不是完整真形状：DerivedC relation 缺 `derived_reason/derived_at`，DerivedB 手工写成 `extends`，而实际 frontmatter 会产生 `derived_from`。[`test_recap_scan_signals.py:215–230`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/test_recap_scan_signals.py:215)、[`board_manifest_service.py:478–483`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:478)。

2. 规则 10 文案说闭合与否都不要写 HTML 注释，但脚本会剥除闭合注释并允许 PASS；只有残留 opener 才失败。[`SKILL.md:304–307`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:304)、[`recap_scan.py:903–916`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:903)。F2 的未闭合注释目标修复本身通过。

## 六项修复状态

| 修复点 | 判定 |
|---|---|
| F1 | PARTIAL |
| F2 | PASS |
| F3 | PARTIAL |
| F4 | PARTIAL |
| F5a | 顶层特例 PASS，完整 fail-closed PARTIAL |
| F5b | PASS |
| F6 | 核心 PASS，fixture 忠实度有 LOW |

测试命令按要求执行，结果为 `143 passed, 187 warnings`：29 + 64 + 50，耗时 5.71 秒；`git diff --check` 也通过。这只是指定回归集，不等同于全量 CI。

证据包内部一致性 PASS：before/after 均为 48 行且逐字节相同，两文件 SHA-256 同为 `ec9405aa…`；三份 scan 的板 SHA 均绑定清单，`signals.asof == scan_at_utc`，关键分母/角色/批注恒等式全部通过。[`g5-4-evidence/README.md:3–24`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-4-evidence/README.md:3)

限制：证据目录及目标测试当前未跟踪，且证据未绑定采集脚本 exact SHA/完整执行 transcript，因此这里只确认当前字节内部自洽；未读取 live vault 原文。Graphiti 的 `search_memory_facts` 本会话未提供，未执行该查询。审阅未修改仓库文件。

落款：**BLOCKER 0 / HIGH 4 / MEDIUM 3 / LOW 2**


