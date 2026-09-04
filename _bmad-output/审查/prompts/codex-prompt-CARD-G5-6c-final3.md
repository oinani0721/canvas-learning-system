你是独立审查者，对 CARD-G5-6c 做**最终态全面审查（第七轮）**（BATCH-2026-09-01-第九批）。用中文。

⛔ 背景与本轮定位（请先读懂再动手）
本卡卡文规定最多 3 轮冻结审查。三轮已用尽，末行均为 `BLOCKER/HIGH 清零: 否`。
此后又发生三次改动，其中最后一次是**用户在看到量化数据后的产品裁决**：
「Markdown 标题里写了字就算实质正文」。这三次改动此前都**没有独立审查看过**。
第六轮只抓出一条 HIGH（行尾 YAML 注释里的来源被静默丢弃），已修 —— 至此
「来源被引擎剥掉」这个根因的三种写法（跨行 HTML 注释 / frontmatter 整行 YAML
注释 / frontmatter 行尾 YAML 注释）已同口径。每轮新 HIGH 数 5→3→2→3→1。
本轮请审**当前最终态 `57712c59`**，给出可据以归档的裁定。

# 限定读取范围（只读，不扫全仓，不联网）

1. 全卡 diff（`969844ef` → final `6ac7e891`）：
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/CARD-G5-6c-diff-969844ef-to-6ac7e891.txt`
2. 被测物：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py`
3. 裁判：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py`
4. **你前四轮的报告**（历史反例与判定的权威来源）：
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/codex-review-CARD-G5-6c.md`、`…-round2.md`、
   `…-round3.md`、`…-round4-verify.md`
5. 取证包：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/`（README 第 1-9 节记录了全过程）
6. 验收单：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md`

复现在 **/private/tmp** 自建 vault：
`python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault <tmp> --now 2026-09-01T00:00:00+08:00 --out-dir <tmp-out>`
（--batch-size 上限 10）。⛔ 不写 worktree、不碰 live vault、不跑会原地改源码的脚本。

# 最终态的判据面（三次未复核改动的净效果）

- **不可见字符**按 Unicode 类别（Cf/Mn/Cc）+ 非 ASCII 空白判定，不枚举；
  护栏归一走 `_guard_variants` 双变体（换空格还原词间、直接删还原词内，
  删版保留 ASCII 空格）。
- **信号⑩**：被**闭合** HTML 注释剥掉的**内容**（非整行）算未消化。
- **用户裁决**：`has_substantive_content` 中，标题行 `lstrip(" \t#").strip()`
  非空即算实质正文。C3 的可确定删除面因此只剩五种：0 字节 / 纯空行 /
  纯分隔线 / 空标题模板（`# ` 后无字）/ 只有引用符。

# 你要判什么

1. **历史反例是否全部仍闭合**：把你前四轮抓过的**每一条**反例重跑（含 NBSP、
   模型声明、DOI、长模型名、`by:`、`by_`、零宽各形态、重复属性名、ISBN、
   白名单键、闭合注释、U+2063 族、U+3164/U+2800）。有任何一条重新出现
   `建议删 + confident=true`，按 BLOCKER/HIGH 报。
2. **新构造**：请尽力构造**你没用过的**新反例。重点面：正文侧未消化结构、
   围栏内外的注释、frontmatter 解析边界、标题判定的新绕过。
3. **C3 会不会已经判死**：那五种可达面是否都还在、是否还有合理的空骨架形态
   被误伤。这是「少删」与「判据失效」的平衡，请给实测。
4. **C1/C2 命中面**必须与本卡开工前（`969844ef`）完全一致 —— 护栏四轮加宽
   都不得扩大任何确定提名面。请对比验证。
5. **门强度**：91 门是否真承重；信号归属断言是否锁得住；变异 runner 的判据
   （失败集合相等 + rc==1 + FAILED/ERROR 并计）有无绕过面；期望集合是否自抄。
6. **措辞**：生产文件头（含偏差 15/16/17）、MD §七、验收单、取证 README 里
   还有没有比证据更宽的声明。逐条给位置与判定。

# 报告格式

按 `一、历史反例复核 / 二、新构造 / 三、C3 可达面 / 四、门强度 / 五、措辞 / 六、登记`
分节，每条带可复现命令与逐字输出，不接受「看代码觉得」。
⛔ 最后一行必须恰好是：`BLOCKER/HIGH 清零: 是` 或 `BLOCKER/HIGH 清零: 否`
