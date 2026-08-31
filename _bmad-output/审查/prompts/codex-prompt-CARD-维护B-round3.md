# Codex 独立复核 · CARD-维护B round-3（round-2 缩小范围重发）

你是独立对抗复核者。round-1 你判 FAIL（BLOCKER 3 / HIGH 5 / MEDIUM 3）；round-2 你在
复核中途被你侧 cyber 过滤器拦截，stdout 0 字节、无终裁（你拦截前留下一条线索：
引用内「列表项+围栏」形态可能不被 `_strip_code_blocks` 识别——**车道已复现确认为真洞
并修复**，见下）。本轮是按停轮规则的**缩小读取范围重发**。

工作树: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix
分支: card/v2-recapfix · 审对象 = `git diff 0c4afeb7..HEAD`（4 个 commit）。

## ⛔ 读取范围硬限（round-2 截断教训，请严格遵守）

1. **不要读**任何 `fixtures/` 目录下的 `.md`/`.json` 文件内容
   （`recap_live_reports/`、`recap_synthetic_signals/` 都不要读——被审内容触发过滤是
   round-1/round-2 两次截断的共因）。需要存在性/大小用 `ls`/`shasum` 即可。
2. **不要读** `_bmad-output/审查/codex-review-CARD-维护B-round1.md` 之外的历史审查存档正文
   （对抗性语料多）。
3. **优先写报告正文**：先把逐条 finding 与裁决句写出来，再补验证过程。
   **裁决句「BLOCKER/HIGH 清零：是/否」请在报告第一行就给出**（防截断吞掉裁决）。

## round-2 你中断前后的关键事实（车道自述，逐条验证）

1. 你中途亲跑目标套件 **239 passed**（当时时点）。
2. 你的线索「列表项+围栏不被识别」：车道复现确认（`> - ``` … > - ``` ` 藏信号行
   两形态 VERIFY PASS 漏拦，先红证据 `_bmad-output/审查/evidence-maintb-r2/codex-hint-repro.txt`），
   修复 = `_strip_code_blocks` 的 `bare` 剥引用前缀后再剥列表标记
   `bare = re.sub(r"^[>\s]*(?:[-*+][^\S\n]+)?", "", ln)`（recap_scan.py ≈:1010），
   配新门 `test_domain_block_list_item_fence_hides_signals` + c2 单元契约扩展
   （含 `---` thematic break 反向锁）+ negverify survivor-7 锚点更新。commit `fd7e1acc`。
3. 修复后裁判复跑：目标套件 **240 passed**（`evidence-maintb-r2/judge1-final2.txt`）、
   扩大回归 **572 passed**（`judge3-final.txt`）、负验证脚本 **10/10** rc=0
   （`negverify-final.txt`）、隔离副本 8 条变异全量重放全承重（`replay-after-result2.txt`）、
   live 8 份原件开工前 vs 收尾 shasum+mtime 逐字相同（`f-collect-{before,final2}.txt`）。

## 你的复核动作（缩水版——只做这三件）

1. **读代码**（这是本轮重心）：
   - `canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py` 的
     `_strip_code_blocks`（含列表符剥离的新 `bare` 正则）、`_SIGNAL_TAIL_NOTES` 注记槽、
     `_FALLBACK_DERIVE_ALLOW`（⑦/⑧ 收紧）、死代码删除后的残留一致性；
   - `backend/tests/regression/test_recap_scan_signals.py` 的「CARD-维护B-R2」节新门
     （行为门+篡改门+反向锁是否成对、docstring 是否夸大）；
   - `backend/tests/regression/recap_domain_negverify.py` 的 10 条 MUTANTS
     （锚点是否精确命中、keyword 是否指向指定门）；
   - `_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md`（v2）
     ——**每句声明是否比门/证据证明的宽**（重点：「全部承重」「本卡未证明什么」
     「round-2 截断的处置是否如实」「D1-D7 是否如实标注待裁决」）。
2. **可选重放**（若你判断某条变异必须在临时副本亲验才敢确认，只做这四条、
   且在 `/tmp` 副本上做）：
   a. S1 `_NODATA_REASONS` 增「任意原因」→ b1/b2 门变红；
   b. S3 `bare` 退回 `^>?[^\S\n]*` → c1/c2/列表项围栏门变红；
   c. `_FALLBACK_DERIVE_ALLOW` 表尾增备注允许式 → d1/d2 门变红；
   d. 注记槽三行替换 `note_slot = r"(?:[^【】]*)"` → e2 门变红。
   （车道侧全量重放输出已在 `evidence-maintb-r2/replay-after-result2.txt`，
   审它 + 抽查即可，不必全量重跑。）
3. **跑一遍目标套件**核对 240：`cd backend && .venv/bin/pytest
   tests/regression/test_recap_scan_signals.py -q -p no:cacheprovider`。

## 输出格式

- **第一行**：裁决句「BLOCKER/HIGH 清零：是/否」。
- 逐条 finding：severity（BLOCKER/HIGH/MEDIUM/LOW）+ 标题 + `file:line` 实证 + 判词。
- 车道自述 3 条（上面「关键事实」）逐条 ✅/⚠️/❌。
- 完整报告一次给出；不要分多次输出。