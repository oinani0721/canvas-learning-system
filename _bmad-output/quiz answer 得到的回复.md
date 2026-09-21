 走查侧备注（UAT 通道，非 skill 回执）

 1. ⚠️ HARD-ISO 上下文洁净被前三步污染（如实登记）
 本轮 ④ 出题前的同一会话中，我在诊断 ③ 时 cat 过 节点/csm-tutoring-unit-credit.md —— 该输出包含 ## 核心概念 正文。虽然题目本身只引用了你 scheduler.csmentors.org 那句批注原文、未复述任何定义字句，但按 HARD-ISO-4「
 出题时上下文不得含节点正文」的前提，这条严格意义上不成立。建议走查单在 ④ 记一条：走查者的 ③ 诊断动作污染了 ④ 的隔离前提。

 2. 🔴 发现算法级单调性缺陷：decay_beta.update() 在低证据量下「答错反升」
 update() 里 a ← max(γ·a + grade, FLOOR=0.05)、b ← max(γ·b + (1-grade), FLOOR)。当节点 a·γ·γ_d^d < 0.05（低证据量 + 久闲置）时，a 被 FLOOR 抬回 0.05，而 b 照常打折下降 → μ = a/(a+b) 反而上升。即：答对答错都可能让
 掌握度上升，单调性不成立。
 - 复现条件：a ≈ FLOOR 且 days_idle 较大（本轮的节点就落在这个区间）。
 - 后果：UAT ⑤ 的「数字变了」成立，但方向与作答质量相反 → 若车道用「变化方向」做语义判据会误判；FSRS/pick 排序也会被轻微带偏。
 - 修复方向（供参考）：FLOOR 只夹 b 或改为「同比例夹」，或 update 后强制 μ' ≤ μ（当 grade < μ 时）加断言。

 3. 🟡 存在第二个写者：节点 frontmatter 被外部重序列化
 本轮 qa 的 python 用 json.dumps 写入，落到盘上却是 YAML 规范化后的形态，我方代码不可能产出：
 - ts: "2026-09-20T22:38:36Z" → ts: 2026-09-20T22:38:36Z（引号被去掉）
 - grade_norm: 0.0 → grade_norm: 0（f"{0.0}" 只会是 "0.0"）
 - self_confidence_norm: null → 值为空
   语义无损（YAML 等价），但字节不同：Obsidian 插件（或后端元数据镜像）在 skill 写入后重新序列化了该文件。→ 直接影响你方的「零静默改写门」和 before/after 字节哈希比对：会多出一次无法归因 skill 的 diff，请把它算作
   已知第二写者而非静默改写。

 4. 🟡 本轮写入面 = 4 条路径（全部是 skill 声明内，但超出发单的「四目录 + state 文件」描述）：
 节点/csm-tutoring-unit-credit.md、检验白板/CS 61B-2026-09-20-2235.md、原白板/CS 61B.md（Step 4c-bis 目录同步）、learning_events.jsonl（vault 根，Step 4c 事件）。→ 若快照面不含 vault 根的 learning_events.jsonl，会
 报 outside ≠ 0，请在判据里预登记。

 5. 🟡 UAT ⑤ 判据建议：mastery_score 是 2 位小数展示值，单次演化变化可能不足一个刻度；before/after 请纳入 mastery_a / mastery_b / attempt_count / last_examined / calibration_log，否则可能把「已更新」判成「没更新」
 。

 6. 状态：③ 的 marker （G8-7 走查批注） 到此刻仍未补（节点/csm-tutoring-unit-credit.md mtime 未变，grep 0 命中）→ UAT ③ 依旧空手，等你手动补。