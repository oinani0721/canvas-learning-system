# Codex 审查存档 — CARD-G5-9（T2 车道首轮）

> **模型**: `gpt-5.6-sol` · `model_reasoning_effort=ultra` · `--sandbox read-only`
> **审阅对象**: commit `4717a2cdbf11485d55bd53b1ff5f5c1e46ae5d0c`（= 审阅时 HEAD）
> **日期**: 2026-08-30 · **产出卡**: BATCH-2026-08-29-第六批 / CARD-收口A ③

---

## ⛔ 碰撞事故说明（必读，涉及本目录两份报告的可信度）

**发生了什么**：本车道在 `card/s6-recap` 跑 G5-9 复核并把结果写入本路径的同时，
另有一个 session（据 trunk 提交 `a9c8b97c docs: update T2 closeout goal with G5-9 review findings`
推断为主 session）**并行**对同一 commit `4717a2cd` 做了独立复核，**写入同一个文件路径**。
两个进程各持一个 fd 写同一文件，字节按各自 offset 交错落盘 ⇒ 产生一个拼接损坏文件：
字节 `0..9890` 是对方报告全文、`9890..16075` 是本报告尾段、拼接点处 UTF-8 解码失败。

**更糟的是**：该损坏文件被本车道的 `git add -A` 连同整改一起提交进 `9e24ef40`，
而那条提交信息却在描述本报告的内容——**提交信息与提交内容不符**。

**如何发现的**：不是靠复核，是靠 round-2 的 Codex 在 transcript 里 `nl -ba` 打印了这个文件，
输出的第 1 行是 `结论：**FAIL，不建议合并 4717a2cd。**`——与本报告的开头对不上。

**恢复**（两份都完整可恢复，无信息丢失）：
- 对方报告：损坏文件字节 `0..9890` 恰为其全文（结尾语完整），逐字节切出 →
  `codex-review-CARD-G5-9-主session独立复核-2026-08-30.md`；
- 本报告：由**已提交**的 transcript 原件 `g5-9-evidence/codex-round1-transcript.txt`
  第 4272–4449 行逐字重建（即本文件下方全文）。

**教训（已写进验收单）**：多 session 并行时，**同一路径不是安全的产出位**。
按车道给产出文件加区分后缀（如 `-T2车道`），或写入前先 `test -e` 并另起文件名。
`git add -A` 会把并发 session 的中间态一并提交——提交前应逐文件核对，而不是只看 `git status` 的文件名列表。

## ⚠️ 本报告自身的存档方式（另一件事，与碰撞无关）

本轮终稿在**输出阶段**被 Codex 平台内容过滤器拦下
（`ERROR: This content was flagged for possible cybersecurity risk`），stdout 得到 0 字节。
过滤器本轮触发**两次**（transcript 第 4120 行推理中途、第 4452 行终稿）。
报告正文已完整生成于 transcript，下方为逐字重建全文，未做任何删改。
与 MEMORY `reference_codex_exec_gotchas` 记录的坑同型（CARD-G5-4 round-5 曾连中三次）。

## 裁决摘要

**需再一轮** · BLOCKER 0 / **HIGH 4** / MEDIUM 8 / LOW 2
4 条 HIGH 已整改，逐条处置与负验证见 `codex-review-CARD-G5-9-round1-处置.md`。

⚠️ 对方那份独立复核给出的是 **BLOCKER 2 / HIGH 4 / MEDIUM 5 / LOW 1**，两份的发现有重叠也有互补，
**其中若干条本车道尚未处置** —— 逐条对照与处置见 `codex-review-CARD-G5-9-两份复核合并处置.md`。

## 复核者自述的一处审计偏差（原文保留，不代为消除）

复核者在「未验证与审计完整性说明」中主动披露：其一名并行代理误用 `importlib` 直接加载工作树脚本 5 次，
改写了一个 **`.gitignore` 已忽略**的 `__pycache__/recap_exam_build.cpython-314.pyc`
（baseline SHA `22071dd5…ec57` → `37f08224…fc9d`）。tracked diff 仍 clean，live vault 未触碰。
因该偏差，当前工作树只能确认 baseline **68/69**。

---

# CARD-G5-9 首轮规范符合性复核

## 结论

**需再一轮。**

目标 commit 与当前 HEAD 均为 `4717a2cdbf11485d55bd53b1ff5f5c1e46ae5d0c`。首轮发现 **0 BLOCKER、4 HIGH、8 MEDIUM、2 LOW**；依既定停轮口径，HIGH > 0，不能验收。

总体判定：

| 核查面 | 判定 |
|---|---|
| preview CLI 零写侧、无新 pycache | PASS |
| preview→create 字节绑定 | FAIL |
| create 发布与失败原子性 | FAIL |
| undo 三重绑定与耐久留痕 | FAIL |
| 路径/symlink 防御 | PARTIAL |
| 零原板/节点正文复制 | PASS |
| 跨板成员去重 | PARTIAL |
| 消费面兼容 | PARTIAL |
| 测试有效性 | FAIL |
| SKILL 契约一致性 | PARTIAL |
| UAT 数字与边界 | PARTIAL |

## HIGH 发现

### HIGH-1 — 空 SHA 可绕过用户确认字节绑定

参数虽在 [recap_exam_build.py:770](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:770) 声明为 required，实际比较却是：

```python
if args.expect_content_sha and args.expect_content_sha != sha:
```

锚点：[recap_exam_build.py:479-501](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:479)。

`argparse` 只要求 flag 出现；`--expect-content-sha ''` 是合法空参数，并因 falsy 跳过比较。`/tmp` 隔离复现得到 `created: true`、实际写出 1092 bytes。preview 后改变会影响输出的输入，再传空串即可创建用户未确认的新全文。

这直接违反 [SKILL.md:377-381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:377) 的“钉死用户确认字节”，属于用户所见与实际写入不一致。

### HIGH-2 — create 只核 inode、不核发布字节；失败回滚还能删除并发文件

[recap_exam_build.py:300-326](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:300) 在写完后关闭 fd，再按固定 tmp 路径执行 `os.link`；发布后只比较 `(dev, ino)`。另一进程若原地改写同一个 tmp inode，核对仍通过。

隔离故障注入结果：

- 确认字节 SHA：`e51ca99e…bf22`
- 实际目标 SHA：`43cb09e0…4901`
- `_atomic_write` 返回：`err=None, warn=None`

即回执声称的 SHA 与目标实际字节分叉。

另一路径中，并发文件在 `os.link` 后、`lstat` 前替换了 target；inode mismatch 分支的 `target.unlink()` 删除了该并发文件，返回失败时文件已丢失。根因同样是按 pathname 回滚，没有重新绑定即将删除的对象。

### HIGH-3 — undo 三重绑定没有延伸到最终删除与留痕字节

锚点：[recap_exam_build.py:653-726](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:653)。

两个独立反例：

1. 最终重读在 `:689-704` 关闭 fd，之后才在 `:721` 按路径 unlink。隔离注入在 unlink 前换入 `USER-NEW-BYTES`：

   - 返回 `undone: true`
   - 新 inode 被删除
   - 留痕只有旧版本，新字节无处保留

2. 目的留痕写入并 fsync 后从未做目的端 inode+SHA 回读。隔离注入原地修改留痕 inode：

   - 源文件已删除
   - 回执 retained SHA：`765bf07e…d51b`
   - 实际留痕 SHA：`3710644e…45f6`

因此“fd + dev/ino + SHA 三重绑定”和“写留痕后才删源”仍不能保证最终删掉的是已校验源、留下的是已校验备份。

### HIGH-4 — 五类关键变异有四类 survivor

基线实际为 **33 passed**。定向变异结果：

| 安全性质 | 完整套件结果 |
|---|---:|
| 禁用非空 expect-SHA mismatch 拒绝 | 1 failed / 32 passed |
| 移除 tmp `O_EXCL`，把 no-replace 改为覆盖发布 | **33 passed** |
| 禁用 create 父目录 symlink 越界守卫 | **33 passed** |
| 从 wikilink 禁止集中仅移除 `\|` | **33 passed** |
| 移除 undo 前后 dev/inode 比较、保留 SHA | **33 passed** |

即 **1/5 KILLED，4/5 SURVIVED**，满足“失效安全判定让完整套件仍全绿”的 HIGH 口径。

按“必须触达声称的生产/消费分支，且断言能区分正确与失效”的判据，**26/33 是承重门，7/33 是非承重或假门**。主要假门：

- [test:342-357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:342)：bad-ts/anchor 未传 SHA，只撞 argparse。
- [test:360-389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:360)：两个 tmp 防御测试同样未传 SHA。
- [test:602-612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:602)：名为 replaced inode，实际没有替换 inode。
- `start-exam-board`、`quiz-answer` 用例只检查生产者前提；消费方排除测试只搜静态字符串。

## MEDIUM 发现

1. **SHA 绑定的是拟写入全文，不是 vault 输入状态。**  
   `board_sha256` 只进入 preview JSON，不进入 `_render_content` 或 create 校验。preview 后修改节点正文但保持角色/计数不变，content SHA 不变，旧 SHA 仍可创建。故“输出字节未变时所见即所写”成立；[SKILL.md:379-381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:379) 所称“vault 若有任何变化均拒绝”不成立。

2. **create/undo 不是完整失败原子事务。**  
   [recap_exam_build.py:271-349](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:271) 中，link/write 失败后的 tmp 清理异常被吞；inode mismatch 时 target/tmp 清理均可能失败；tmp unlink 失败会留下 target+tmp 两个硬链接。`_fsync_dir` 对 open/fsync 失败全部静默，仍返回成功。undo 出现“留痕已写、源未删”时两份都在、可恢复，但没有 journal/restart reconciliation；目的目录 fsync 失败后仍可删源，崩溃耐久保证不足。

3. **symlink 防御只覆盖瞬时、直接路径。**  
   静态 `检验白板/`、target、tmp 会被检查，tmp 最后一段受 `O_NOFOLLOW` 保护；但 vault 根/祖先和中段没有 dirfd 锚定。probe 后把父目录换成外部 symlink，可在 vault 外成功创建文件。undo 又在 [recap_exam_build.py:556](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:556) 先 `resolve()`，使后面的 `O_NOFOLLOW` 看不到原 final symlink；`alias.md -> real.md` 会移走 real 并留下 dangling alias。该路径有留痕可恢复，故定 MEDIUM。

4. **跨板只对汇总数字去重，链接清单没有全局去重。**  
   [recap_exam_build.py:168-173](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:168) 对 totals 去重；[recap_exam_build.py:212-216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:212) 仍按每板逐项输出。两板共享 `Shared` 时，总成员为 1，但 `[[节点/Shared]]` 出现 2 次。测试也只锁 totals。

5. **`recap_kind` 没有被所有消费方读取。**  
   后端 [board_manifest_service.py:681-700](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:681) 完全不看 `recap_kind`，并在 `:843-845` 把阶段回顾板计入 `exam_board_count`；API/Snapshot 模型也没有该字段。隔离实测创建前后：

   - `parse_errors: 0 → 0`
   - `digests: 1 → 1`
   - `exam_history: 1 → 2`
   - 锚板 `exam_board_count: 0 → 1`

   所以 manifest 的窄兼容判据确实通过，但 `/board-recap` 的“检验历史 N 板”、`ai-linked-doc` 的板统计及 start-exam-board 的板级历史仍会把阶段板视作普通检验历史。Dashboard 的过滤当前正确。

6. **消费面证据多为必要前提/静态文本，不是端到端执行证据。**  
   `board_manifest_service.scan_vault`：PASS，已独立实跑。  
   start-exam-board：PARTIAL，仅检查产物的 type/path；未执行消费者拒绝分支。  
   quiz-answer：PARTIAL，仅检查 status/无答题区和 SKILL 字符串；未驱动 done 或无参定位流程。  
   Dashboard：静态 PASS，[Dashboard.md:440-442](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/Dashboard.md:440) 确实读取该键，但未在 Obsidian/Dataview 运行时执行。

7. **`undo_hint` 不能原样执行。**  
   [SKILL.md:382-386](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:382) 称其“可直接复制执行”；实现 [recap_exam_build.py:526-529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:526) 只输出 `undo --vault ...`，缺少 `python3 <script>` 前缀。参数 quoting 正确，但普通 zsh 中 `undo` 不存在。

8. **C1/C2/C3 触发与范围解析未闭合。**  
   第二刀称覆盖 C1/C2/C3，但 [SKILL.md:97-100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:97) 的 CRITICAL TRIGGER 仍只有 `/board-recap`；[skill_trigger_matrix.yaml:128-151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/skill_trigger_matrix.yaml:128) 三条仍是 `planned-extension / trigger_today:false`。C1/C2 没给板名，而脚本 [recap_exam_build.py:752-757](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:752) 强制 `--boards`，SKILL 没有章节/阶段到板集合的解析步骤。当前完整的是“已进入 skill 且显式列板”的 C3-like 路径。

## LOW 发现

1. **UAT 测试数陈旧。**  
   [UAT:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/验收单/UAT-CARD-G5-9-阶段回顾检验白板-2026-08-28.md:31) 和 `:61` 写 31；目标 commit 实际收集 **33 tests，33 passed**。这是低估，不是假绿。

2. **拒绝文档枚举/返回形态不完整。**  
   实现拒绝 `# | ^ [ ]`，SKILL `:374/:415` 只列 `# | ^`；这些字符实际返回 `{"error": ...}` + exit 2，不是文档所说的 `refusal_reason`。安全行为更强，属于文档漂移。

## 其余逐项判定

### preview 与零正文复制

- 正式 CLI preview 的 `sys.dont_write_bytecode` 保护有效；在无既有 pycache 的 `/tmp` vault 中，文件数 `65 → 65`、SHA diff 为 0、新 pyc 为 0。
- 当前 `_render_content` 没接收原板/节点正文、标题、callout 或题干字段；只接收板 stem、节点 ID、计数、ghost 标识及固定模板。未找到原节点/原板 prose 正文字节进入输出的反例。
- ghost ID 是明确要求展示的链接标识，anchor 是 CLI stem；二者不构成原板标题或节点定义正文复制。
- 现有测试只用节点正文哨兵，覆盖面偏窄；此处 PASS 主要来自静态数据流核对。

### 时间戳、幽灵链接

- `datetime.strptime` 真校验日历时刻，默认使用 `datetime.now(timezone.utc)`：PASS。
- 静态传入的显式 `--ts` 是否真来自 UTC 只能靠 SKILL 的 `date -u` 约定，脚本无法从无时区字符串自行证明。
- 幽灵链接不计入 members、不输出死 wikilink、单列待修段：PASS。

### UAT 与证据包

- 证据包内部：baseline、两组 preview、两组 undo 均为 69 行且逐字节相同；两份 after-create 均恰多 1 行；preview content 的独立 SHA 与 create/undo 回执一致。
- `/tmp` 隔离链复现了 `69 → 70 → 69` 和留痕 SHA 全等。
- `g2-manifest-compat.txt` 的 `0 parse_errors / question_count=0 / digests 零新增` 属实，但只是窄判据。
- [UAT:71-76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/验收单/UAT-CARD-G5-9-阶段回顾检验白板-2026-08-28.md:71) 清楚声明 D5 用户 UAT 未发生、live 验证顺延 G5-11；该边界诚实。

## 未验证与审计完整性说明

- 未访问或写入主仓 live vault。
- 未运行 Obsidian/Dataview UI，也未真实驱动 LLM 执行 start-exam-board/quiz-answer；这些面按 PARTIAL 报告。
- 未做真实断电测试；fsync/崩溃结论来自静态路径和 `/tmp` 故障注入。
- 只运行目标 33 项测试，不宣称全仓 CI 通过。
- Graphiti 工具本会话不可用，未执行记忆写入。
- 审计过程中一名并行代理误用 `importlib` 直接加载了工作树脚本 5 次，改写了一个既有、被 `.gitignore` 忽略的 `canvas-vault/.claude/skills/board-recap/scripts/__pycache__/recap_exam_build.cpython-314.pyc`。baseline SHA 为 `22071dd5…ec57`，当前为 `37f08224…fc9d`。我没有恢复或删除它；tracked diff 仍为 clean，live vault 未触碰。因该审计自身偏差，当前工作树只能确认 baseline **68/69**，不能再宣称当前 69 文件逐字节等于原证据。

## 残留清单

- **BLOCKER：0**
- **HIGH：4**
- **MEDIUM：8**
- **LOW：2**

最终裁决：**CARD-G5-9 需再一轮。**
