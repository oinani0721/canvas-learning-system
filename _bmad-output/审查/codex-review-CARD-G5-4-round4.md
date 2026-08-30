终裁：**FAIL。CARD-G5-4 与 CARD-G5-9 均不可验收。**

Round-3 的 19 项仅 **6 PASS / 9 PARTIAL / 4 FAIL**。指定的 187 项测试虽全绿，但存在多条生产入口可复现反例。

## BLOCKER

无。

## HIGH

1. **H1 / R4-1 PARTIAL — fallback 仍不等价于后端 YAML truthiness。**  
   [recap_scan.py:149](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:149)、[recap_scan.py:533](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:533)、[board_manifest_service.py:487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:487)。真实 CLI 与 `_node_role(yaml.safe_load(同文))` 对拍发现：

   - `relationships: false/0/""/{}/[ ]/Null/[] # comment`：fallback=`derived`，后端=`seed`
   - 非空块 mapping：fallback=`seed`，后端=`derived`
   - 引号值后带注释的 `created_from`、块标量、整份 mapping 合法缩进两格仍分叉

   `_fm_scalar` 对 `C#`、`C # comment`、单纯引号值、CRLF、`mastery`/`mastery_score` 精确键均正常；但“引号值 + 尾注释”、块标量、合法顶层缩进会污染 `board_name` 或丢失 mastery。两个对拍测试确实 import 了真实后端，**不是假测试**，但只覆盖 5+4 个精选形态，不能支撑 “exactly”。见 [测试:502](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/test_recap_scan_signals.py:502)、[测试:1107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/test_recap_scan_signals.py:1107)。

2. **H2 PARTIAL — “无据行零数字”仍可绕过。**  
   [recap_scan.py:828](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:828)、[recap_scan.py:904](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:904)。`两/俩` 已修，但 `共有壹条`、Arabic-Indic `共有٩条` 均实测 `VERIFY PASS`。

3. **H3 / R4-2 PARTIAL — 尾部禁数字仍只是 ASCII/全角字符类。**  
   [recap_scan.py:918](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:918)、[recap_scan.py:932](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:932)。ASCII `99/99` 已挡住，但尾加 `九九/九九`、`٩٩/٩٩`、`⁹⁹/⁹⁹` 均 `VERIFY PASS`，仍能附加第二组错误数字。

4. **H4 FAIL — 所谓结构级禁令仍是关键词禁令。**  
   [recap_scan.py:1093](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1093)、[测试:1167](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/test_recap_scan_signals.py:1167)。fallback 种子段写“后代节点数量为零”实测通过；实现只禁“派生”二字，round-3 指出的无限同义改写问题仍在。

5. **H5 FAIL — `--expect-content-sha` 仍可省略。**  
   [recap_exam_build.py:415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:415)、[recap_exam_build.py:669](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:669)、[SKILL.md:363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:363)。真实 CLI 复现：preview 后改成员，省略该参数，create 仍 `created:true`，写入 SHA 与 preview SHA 不同。通用测试 helper 本身也一直省略该参数：[test_g5_9_recap_exam.py:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:106)。

6. **H6 PARTIAL — target no-replace 正确，但发布字节与目录仍未绑定。**  
   [recap_exam_build.py:247](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:247)、[recap_exam_build.py:274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:274)、[recap_exam_build.py:295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:295)。`os.link` 对已存在 target 的 EEXIST/no-overwrite 本身 PASS；但写 FD 关闭后仍按 tmp 路径 link。确定性交错测试在 link 前替换 tmp 后，函数无错误地发布替换内容。祖先目录仍是 check-then-use、无可信 `dir_fd`，处置表也承认未修。

7. **H7 / R4-4 PARTIAL — 两次 inode 复核仍不能绑定最终删除字节。**  
   [recap_exam_build.py:493](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:493)、[recap_exam_build.py:600](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:600)、[recap_exam_build.py:623](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:623)。留痕写出期间对源文件做**同 inode 原地修改**，两次 `(dev,ino)` 都不变，命令仍返回 `undone:true` 并删除新修改；外部只保留旧字节。所谓替换回归锁其实未替换任何 inode：[测试:545](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:545)。

8. **新增 FAIL — preview 首次执行并非零写侧。**  
   [recap_exam_build.py:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:61)、[测试脚本路径:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:34)。在临时完整 vault 中按 SKILL 命令运行 preview，新增 `.claude/skills/board-recap/scripts/__pycache__/recap_scan.cpython-314.pyc`。测试把被测脚本放在 fixture vault 外，证据快照也只覆盖四个数据目录，[README:12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/README.md:12)，因此没有发现该写入。

9. **WF-2 新问题 FAIL — 幽灵数量恒等已修，但幽灵文本可突破 Markdown 隔离。**  
   [recap_scan.py:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:91)、[recap_exam_build.py:90](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:90)、[recap_exam_build.py:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:188)。成员正则允许换行和反引号；构造跨行 ghost id 后，preview 为 `members=0, seeds=0, derived=0, ghosts=1`，但产物出现独立的注入行，反引号隔离失效。普通幽灵测试只覆盖中文单行名：[测试:459](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:459)。

## MEDIUM

1. **M3 PARTIAL — tab 标题已修，但 Markdown 边界仍不严格。**  
   [recap_scan.py:878](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:878)、[recap_scan.py:891](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:891)。信号移到合法空标题 `##` 后、四空格代码块内、或 fenced code 内，均 `VERIFY PASS`。

2. **新增 FAIL — signal schema 仍非 fail-closed。**  
   [recap_scan.py:835](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:835)、[recap_scan.py:923](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:923)。`percentile_ref=null`，报告写 `None/None/None`，仍通过。M2 的 bool 修复本身 PASS。

3. **R4-5 PARTIAL — 双向控制字符集合不完整。**  
   [recap_scan.py:1058](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1058)、[测试:1086](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/test_recap_scan_signals.py:1086)。U+200B 会拒收，但 U+061C、U+2066–U+2069 未覆盖；U+061C/U+2066 实测通过。

4. **M4 PARTIAL — undo 目的端 O_EXCL 正确，耐久承诺不成立。**  
   [recap_exam_build.py:232](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:232)、[recap_exam_build.py:574](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:574)、[recap_exam_build.py:623](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:623)。缺目的端 readback hash；目录 fsync 失败被吞掉后仍删除源。

5. **M5 FAIL — 固定 tmp 的崩溃恢复未实现。**  
   [recap_exam_build.py:247](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:247)、[测试:382](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:382)。进程中断留下 `.g59-tmp` 后，后续 create 长期拒绝；现有测试锁的是“残留即拒绝”，不是恢复。

6. **M6 PARTIAL — `# / | / ^` 已拒绝，但 `]` 同样破坏 wikilink。**  
   [recap_exam_build.py:320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:320)、[recap_exam_build.py:141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:141)、[board_manifest_service.py:132](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:132)。板名 `A]B` 被 preview 接受，但生成的 source wikilink 被消费方解析成错误 ID。

7. **H8 新操作缺口 PARTIAL — shell 语法已修，但 hint 不能直接执行。**  
   [recap_exam_build.py:460](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:460)、[SKILL.md:368](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:368)、[测试:523](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:523)。quote 与无尖括号均 PASS；但 hint 以裸 `undo` 开头，当前 zsh 为 `undo: none`。测试只做 `shlex.split`，与“可直接复制执行”不符。

8. **证据包声明绑定 PARTIAL。**  
   [g5-9 README:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/README.md:3)、[g1-create.json:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/g1-create.json:1)、[g5-9 README:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/README.md:28)。create 回执没有记录 `--expect-content-sha` 是否实际校验；consumer 日志早于最终全链且不含产物 SHA。独立用最终 retained exact bytes 重放 `scan_vault` 后，兼容性本身 PASS，但原证据包无法独立证明其声明绑定的是最终字节。

## LOW

1. **L3 PARTIAL — I/O 异常仍可能 traceback + exit 1。**  
   [recap_exam_build.py:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:87)、[recap_exam_build.py:503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:503)。无效 UTF-8 原白板实测 `returncode=1`、stdout 空、stderr 为 `UnicodeDecodeError`，没有 JSON+exit 2。

2. **L4 FAIL — UAT/README/代码说明仍有实况漂移。**  
   [G5-4 UAT:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/验收单/UAT-CARD-G5-4-偏航lint一梯队信号-2026-08-28.md:15) 写 p25/p50/p75=`78/78/78`，实际是 [77/77/77，max=78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-4-evidence/scan-CS188-lecture-2.json:27)；[G5-9 UAT:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/验收单/UAT-CARD-G5-9-阶段回顾检验白板-2026-08-28.md:31) 写 26 条，[同文件:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/验收单/UAT-CARD-G5-9-阶段回顾检验白板-2026-08-28.md:61) 仍写 16 条；[recap_exam_build.py:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:13) 仍称 `os.replace/move`；[返回标注:247](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:247) 与实际二元 tuple 不符；round-4 报告文件当前为 0 字节。

## Round-3 19 项终态

| 项目 | 终态 |
|---|---|
| H1 | PARTIAL |
| H2 | PARTIAL |
| H3 | PARTIAL |
| H4 | FAIL |
| H5 | FAIL |
| H6 | PARTIAL |
| H7 | PARTIAL |
| H8 | PASS；另有 hint 不可执行的新缺口 |
| M1 | PASS |
| M2 | PASS；另有 percentile schema 新缺口 |
| M3 | PARTIAL |
| M4 | PARTIAL |
| M5 | FAIL |
| M6 | PARTIAL |
| M7 | PASS |
| L1 | PASS |
| L2 | PASS；UAT 仍有措辞漂移 |
| L3 | PARTIAL |
| L4 | FAIL |

新增重点：R4-1 PARTIAL、R4-2 PARTIAL、R4-3 PASS、R4-4 PARTIAL、R4-5 PARTIAL；WF-2 的 `members == seeds + derived` 算术恒等 **PASS**，但幽灵输出隔离 **FAIL**。

## 验证结果与限制

- 指定命令：**187 passed, 187 warnings**
- `--collect-only`：G5-4 **63**；G5-9 **26**
- ROUTING：**66/66**
- `ruff check`、`ruff format --check`、`git diff --check`：PASS
- G5-4 证据 before/after 各 48 行且逐字节相同；G5-9 happy path 的 preview/undo 回基线、create 恰增一文件均成立
- 这是 `HEAD 37387a8662e… + 当前 dirty/untracked worktree` 的定向审计，不等同提交对象或全量 CI
- Graphiti MCP 本会话未暴露，无法执行规定的 `search_memory_facts`
- 本轮只读，未修改仓库、未读取 raw/private vault 正文

**落款：BLOCKER 0 / HIGH 9 / MEDIUM 8 / LOW 2。**

**最终裁决：CARD-G5-4 = FAIL；CARD-G5-9 = FAIL；当前版本不可验收。**


