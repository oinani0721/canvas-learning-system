结论：**FAIL，不能判定 round-2 已闭环，也不能批准 CARD-G5-9 当前写侧契约。**  
审阅对象为分支 `card/s6-recap`、`HEAD 37387a8662e…`；未修改仓库。

## HIGH

1. **G5-4 H1 仍为 PARTIAL：fallback 角色口径继续与真实 manifest 分叉。**  
   [recap_scan.py:149](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:149)、[recap_scan.py:484](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:484)、[board_manifest_service.py:476](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:476)、[board_manifest_service.py:487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:487)。  
   `derived-from: null` 实测 fallback=`derived`、无来源 `1/1`，真实 manifest=`seed`、无来源 `null/0`。合法顶层缩进键和 `created_from: ai_linked_doc # comment` 同样分叉。原因是 fallback 按“键存在”，后端仍按 YAML 解析后的 truthiness。

2. **G5-4 H2 仍为 PARTIAL：“无据行零数字”仍可绕过。**  
   [recap_scan.py:778](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:778)、[recap_scan.py:846](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:846)。  
   `_ANY_DIGIT_RE` 漏掉常用表量字“两”；`重复堆积：无据（共有两条）` 实测 `VERIFY PASS`。

3. **G5-4 H3 仍为 PARTIAL：独占 label 已修，但整行没有全等绑定。**  
   [recap_scan.py:833](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:833)。  
   正确 `2/3【文件】` 后追加错误 `99/99【实测】` 仍 `VERIFY PASS`；代码只检查首个匹配和正确档位是否“出现过”。

4. **G5-4 H4 仍为 PARTIAL：同义断言黑名单可继续改写绕过。**  
   [recap_scan.py:735](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:735)、[recap_scan.py:1032](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1032)、[SKILL.md:301](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:301)。  
   fallback 写“派生数量为零”实测仍 PASS，继续构成无据派生子女断言。

5. **G5-9 preview 没有绑定 create，用户确认的不是最终写入字节。**  
   [recap_exam_build.py:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:244)、[recap_exam_build.py:276](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:276)、[SKILL.md:360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:360)。  
   preview 后新增成员，create 仍成功，复算 hash 从 `9b82…` 变为 `83ee…`。相同 `--ts` 不能保证所见即所写；CLI 缺强制 `--expect-content-sha`。

6. **G5-9 create 的“原子且不覆盖、目录内落盘”承诺未成立。**  
   [recap_exam_build.py:169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:169)、[recap_exam_build.py:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:184)、[recap_exam_build.py:218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:218)、[recap_exam_build.py:295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:295)。  
   `O_EXCL|O_NOFOLLOW` 只保护固定 tmp；最终 `os.replace(tmp, target)` 可覆盖预检后出现的 target。父目录也只做 check-then-use，`O_NOFOLLOW` 不保护中间目录分量，未用可信 `dir_fd` 绑定 containment。

7. **G5-9 undo 校验的字节与最终移走的字节未绑定。**  
   [recap_exam_build.py:337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:337)、[recap_exam_build.py:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:357)、[recap_exam_build.py:403](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:403)。  
   hash/指纹检查后仍按路径 `shutil.move`；期间编辑器或同步程序替换文件时，undo 会移走未经校验的新版本，而不是拒绝用户改动。

8. **G5-9 `undo_hint` 存在 shell 边界错误。**  
   [recap_exam_build.py:323](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:323)、[SKILL.md:363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:363)、[g2-create.json:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/g2-create.json:4)。  
   路径未经 shell quoting。证据中的合法板名含空格、括号和 `&`，其 hint 经 `zsh -n` 已报 `parse error near ')'`；当前允许的其他 shell 控制字符还可能改变命令边界。

## MEDIUM

1. **G5-4 M1 FAIL：`_strip_note_ref` 不幂等。**  
   [recap_scan.py:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:233)、[recap_scan.py:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:399)、[test_recap_scan_signals.py:487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/test_recap_scan_signals.py:487)。  
   `_strip_note_ref("[[节点/null]]") == "null"`，再次调用却得到 `None`。现有回归只重复跑 fallback，没有覆盖真实 manifest 的二次归一。

2. **G5-4 M2 PARTIAL：JSON boolean 被当作整数。**  
   [recap_scan.py:784](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:784)。  
   `isinstance(True, int)` 为真；`value:true` 配报告 `1/N` 实测通过。

3. **G5-4 M3 PARTIAL：合法 tab 标题仍突破③段边界。**  
   [recap_scan.py:822](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:822)。  
   把四行移到 `##\t附录` 后仍通过，因为终止正则只识别标题后的普通空格。

4. **G5-9 undo 目的端仍非 no-replace、非耐久回退。**  
   [recap_exam_build.py:384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:384)。  
   `exists()` 后再 `shutil.move` 有目的端竞态；跨文件系统会变成 copy+unlink，未做目的端独占创建、readback hash 或 fsync 后便删除源。

5. **G5-9 create 缺崩溃恢复，可能留下固定 tmp。**  
   [recap_exam_build.py:198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:198)、[recap_exam_build.py:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:203)。  
   只 fsync 文件、不 fsync 父目录；进程中断可留下 `.g59-tmp`，且清理失败被吞掉，后续 create 会长期拒绝。

6. **G5-9 合法文件名中的 `#`/`|` 会破坏 wikilink 归属。**  
   [recap_scan.py:119](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:119)、[recap_exam_build.py:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:124)、[board_manifest_service.py:132](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:132)。  
   `A#B` 可成功创建，但消费方按 heading/alias 语义截断，`scan_vault` 得到 `board_id=null` 且无 parse error。空格、括号和 `&` 的 YAML/wikilink 本身通过；`&` 的问题发生在 undo hint。

7. **G5-9 时间戳只验形状，且本地时间被冒充 UTC。**  
   [recap_exam_build.py:56](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:56)、[recap_exam_build.py:263](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:263)、[recap_exam_build.py:424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:424)、[snapshot_v3.py:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/models/snapshot_v3.py:217)。  
   `2026-99-99-9999` 可通过；默认 `datetime.now()` 是 Asia/Shanghai 本地时间，却追加 `Z`。非法值还会阻止 SnapshotV3 刷新。

## LOW

1. **preview 的既有目标返回契约与 SKILL 不一致。**  
   [recap_exam_build.py:251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:251)、[SKILL.md:355](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:355)。  
   只返回 `target_exists:true`，没有所承诺的 `refusal_reason`。

2. **“节点正文根本不进内存”的声明不实。**  
   [recap_exam_build.py:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:28)、[recap_exam_build.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:95)、[recap_scan.py:457](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:457)。  
   `_ledger_from_local` 会读取完整节点文件和 body；“未复制进产物”通过，但数据最小化声明不成立。

3. **部分 I/O 错误不符合 JSON + exit 2 契约。**  
   [recap_exam_build.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:307)、[recap_exam_build.py:391](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:391)、[recap_exam_build.py:403](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:403)。  
   `mkdir`/`shutil.move` 等异常未归一，可能 traceback + exit 1。

4. **证据与验收文案过度声明。**  
   [g5-4 README.md:26](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-4-evidence/README.md:26)、[G5-9 UAT:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/验收单/UAT-CARD-G5-9-阶段回顾检验白板-2026-08-28.md:31)、[G5-9 UAT:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/验收单/UAT-CARD-G5-9-阶段回顾检验白板-2026-08-28.md:32)。  
   G5-4 README 声称 null 幂等已修；G5-9 UAT 同时写 23 条和 16 条，而实际收集 19 条，并称已“封 TOCTOU”。

## Round-2 九项状态

| 项目 | 三轮结果 |
|---|---|
| H1 / H2 / H3 / H4 | PARTIAL |
| M1 | FAIL |
| M2 / M3 | PARTIAL |
| L1 | PASS |
| L2 | PASS |

额外 `_fm_scalar` 修复：**跨行吞下一键的问题 PASS，整体 YAML 等价性 PARTIAL**。单双引号、行尾空白、CRLF、值含冒号未见回归；但顶层缩进、行尾注释、块标量、重复键仍与后端 YAML 解析分叉。受影响调用点包括 mastery、derived 两拼写、created_from、attempt_count、last_examined、source_note 与 board_name：[recap_scan.py:473](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:473)、[recap_scan.py:509](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:509)、[recap_scan.py:1169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1169)。

## 验证与限制

- 指定测试：**162 passed, 187 warnings**；这是定向测试，不等同全量 CI。
- G5-9 文件实际为 **19 tests**，不是 23。
- `git diff --check`：PASS。
- G5-4 证据 before/after 各 48 行且逐字节相同，三份 scan 数字自洽。
- G5-9 happy path：preview 零写、create 恰加 1 文件、undo 回基线、当前外部留痕 SHA 正确；但未覆盖数据变化或并发窗口。
- `scan_vault` 的普通名称消费面、`question_count=0`、digest 零新增、start-exam-board 防嵌套及未修改产物的 quiz-answer 安全停均通过。
- Graphiti MCP 本会话不可用，未执行 `search_memory_facts`；未读取 live vault 原文。

落款：**BLOCKER 0 / HIGH 8 / MEDIUM 7 / LOW 4**


