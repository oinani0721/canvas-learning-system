你是独立审查者，审 CARD-G5-6c 的最终态 `edf737ac`（BATCH-2026-09-01-第九批）。用中文。

# ⛔ 先读这一段：本轮的裁决面边界

前七轮中有两条**产品行为**被反复按 BLOCKER 记，但它们是**用户在看到量化数据后
明确拍板保留的决策**，不是实现缺陷：

1. **C4「精确重复」不看标题**（`dup_body()` 丢弃标题行）。用户 2026-09-02 裁决
   **不改**。量化依据：让标题参与比对后，5 件取样只剩 1 件仍被识别为重复 ——
   「同一段正文粘两份、标题不同」「一份有标题一份没有」都不再算重复，而那正是
   清收件箱最常见的场景。用户选择保住重复识别能力，接受「标题里的独有信息可能
   随重复件被删」。已登记为生产文件头**偏差 18**。
2. **C3 可确定删除面只剩五种**（0 字节 / 纯空行 / 纯分隔线 / 空标题模板 /
   只有引用符）。这是用户同日第一次裁决「标题里写了字算实质正文」的**代价**。

⛔ **请把这两条视为已定的产品规格，不要据此判 BLOCKER/HIGH。**
你可以也应该验证「实现是否忠实于这两条规格」、指出它们**未被记录的**连带后果、
或指出文档对它们的描述是否过宽 —— 但「应该改变这两条产品决策」本身不在本轮
裁决面内。审查的职责是验证实现质量与声明诚实度，不是推翻用户的产品选择。

其余照常：任何**未被上述两条决策覆盖**的「有内容或有来源的材料被
`建议删 + confident=true`」，仍请按 BLOCKER/HIGH 报。

# 限定读取范围（只读，不扫全仓，不联网）

1. 全卡 diff：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/CARD-G5-6c-diff-969844ef-to-edf737ac.txt`
2. 被测物：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py`
3. 裁判：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py`
4. 你前九轮的报告：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/` 下 `codex-review-CARD-G5-6c*.md`
5. 取证包：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/`（README 十节记录全过程）
6. 验收单：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md`

复现在 **/private/tmp** 自建 vault：
`python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault <tmp> --now 2026-09-01T00:00:00+08:00 --out-dir <tmp-out>`
（--batch-size 上限 10）。⛔ 不写 worktree、不碰 live vault、不跑会原地改源码的脚本。

# 上一轮（第九轮）你抓的三条已修，请复核

1. **R9-H3 `# # #` / `#######`** → 新增 `_atx_heading_text()` 按 ATX 真实结构
   （opening 1-6 个 # + 空白 + content + 可选 closing）分离，不再字符集剥离。
2. **R9-H1 C4 抹掉有语义空白** → `dup_body()` 现在：围栏内逐字保真、空行保留为
   段落边界、行尾 ≥2 空格保留硬换行。NFD/NFC 与标题差异仍被吸收。
   ⚠️ 我先把它归为「判据形状不修」，重看后判错了 —— 判据名叫「精确重复」而比较
   形态是有损投影，这是**名实不符的实现缺陷**，与「C4 不看标题」（已裁决保留）
   是两回事。
3. **R9-H2 护栏不看文件名** → 来源信号扫描面加上文件名（URL / DOI / **ISBN 的
   正面形态**；文件名分隔符常被换成 `_`，故还原成 `:` 与 `/` 各试一遍）。

⚠️ C4 的**证据域**本身没变（"投影相等 ⟹ 整件可删"），只是投影更保真、
扫描面加了文件名。若你认为证据域仍需重定义，请在第六节说明，不必再列同族样本。

# 你要判什么

1. **历史反例是否仍闭合**（排除上述两条决策覆盖的）：把前七轮抓过的反例重跑。
2. **新构造**：尽力构造新反例。⚠️ 本卡已跑八轮、修 70+ 条；若你认为剩余问题
   已属**判据形状**层面（而非可补的实现缺陷），请在第六节明说，那比再列一条
   同族反例更有价值。⚠️ 若根因落在上述两条决策上，请登记为
   「已裁决项的连带」而非 BLOCKER/HIGH。
3. **实现是否忠实于两条决策**：偏差 18 说 C4 不看标题 —— 实现是否正好如此，
   有没有多丢或少丢？C3 那五种可达面是否都在、有没有第六种被误伤？
4. **门强度**：92 门是否真承重；12 条变异的判据（失败集合相等 + rc==1 +
   FAILED/ERROR 并计）有无绕过面。
5. **措辞**：生产文件头、MD §七、验收单、取证 README 里还有没有比证据更宽的
   声明 —— 特别是对那两条决策的描述是否准确、代价是否写全。

# 报告格式

按 `一、历史反例 / 二、新构造 / 三、决策忠实度 / 四、门强度 / 五、措辞 / 六、登记`
分节，每条带可复现命令与逐字输出。
⛔ 最后一行必须恰好是：`BLOCKER/HIGH 清零: 是` 或 `BLOCKER/HIGH 清零: 否`
