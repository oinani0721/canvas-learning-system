# Codex 审查 · CARD-G5-3（第 2 轮）

## 裁决

**不通过**——多数一轮处置有效，85 条测试全绿，但仍有 3 个 HIGH：机器段误吞真实正文、diff 新增安全字段可缺失并 fail-open、证据包未绑定当前契约字节。

最终审查快照：`HEAD cbb20afb572a7b8ce9ebc205082e4be6de076fb8`；引擎 SHA `3aaa07a1…`，契约 SHA `73cf7881…`。

## 一轮发现逐条复核

1. 重名调序/改名静默换绑 — **PARTIAL**

   实跑交换两个 `## 例题`：ID 留在 occurrence 槽位，指纹互换，diff 为 `changed=2`；两候选均为 `identity_ambiguous=true / group_size=2`，warning 存在，MD 两行均有 `⚠身份歧义`。删除首项得到 `changed=1 + removed=1`；改名进入三重组后新侧三项均标歧义。

   “缩小权威范围”原则上足以处理只读 preview/diff，不必强行更换 v1 语义；但接口还未 fail-closed：删掉 `identity_ambiguous` 和 `ambiguous_group_size` 后，diff 仍 `rc=0`，把缺失值投影成 `false`，`warnings=[]`。[加载守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1028)、[缺失默认 false](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1141)

   撤销 BLOCKER 的最低条件应是：这些字段在 schema/diff/G5-10 全部必填；“缺失”和 `true` 都禁止持久化。若未来要让重复标题也具 provenance，可在来源中持久化显式 UUID/anchor marker；它不依赖正文，固定输入仍可逐字节确定。

2. 创建指纹与 re-baseline — **PARTIAL**

   实跑插入派生 callout：stable ID 不变，指纹从 `cf1-6eea…` 变为 `cf1-4e71…`，diff 为 `changed(content, overlap)`。两个指纹的时序矛盾已消除，`{file, sha256}` 设计也成立。

   但 §7.1 YAML 示例的 `split_source_anchor` 缺少 `basis`，[示例止于 occurrence](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:320)，后文却规定它必填 [basis 要求](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:352)。

3. 空标题 fallback 行号漂移 — **RESOLVED**

   `## .gitignore 的作用` 和 `## 一、` 分别稳定得到 `derived-547968`、`derived-63ab15`；增加 7 行 frontmatter 后名称、ID 均不变，diff 为 `unchanged=2`。

4. whole→section 的 basis 身份维 — **RESOLVED**

   `# 讲义 + 正文` 与 `## 讲义 + 同正文` 的规范路径和指纹相同，basis 分别为 `seed-note-whole/section`，ID 不同，diff 为 `added=1 + removed=1`。未发现 basis 类别自身发生非声明性漂移。

5. 当前证据绑定与 live 硬门 — **PARTIAL**

   - `engine-and-products.sha256`：全部 OK。
   - live 不存在：临时 pytest 插件把常量指向 `/private/tmp/.../definitely-missing-live-vault`，默认结果 `2 failed`。
   - 加 `G53_ALLOW_NO_LIVE=1`：`2 skipped`，理由明确含 `UNVERIFIED`。
   - 但 `judge-and-contract.sha256` 当前失败：manifest 记录契约 `d06b509a…`，实际为 `73cf7881…`。
   - [README](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/README.md:18) 声称 `pytest-green.txt` 是 85 条存证，实际文件仍写 `64 passed`。

6. 拒绝路径零产物 — **PARTIAL**

   指定反例均修复：

   - `board="A"*300`：`rc=1`，out-dir 不存在。
   - `source_anchor={}`：`rc=1`，out-dir 不存在。

   但“候选 schema 入口全校验”和“两产物零半份”不成立，详见 HIGH-2、MEDIUM-1。

7. NFC(file_rel) 与改名声明 — **RESOLVED**

   契约已正确排除 NFC/NFD 等价改名，实际 stable ID 也保持相等。[契约 §4.2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:168)

   不过 diff 的 raw basis 比较会拒绝这种合法等价，列为 MEDIUM-2。

8. 自检措辞与跨 preview basis — **PARTIAL**

   用真实可解析的 U+0000 标题构造两个相同 payload，并设 `--max-units 1`：截断范围外的第二项仍被截断前自检抓到，错误列出两个锚点，out-dir 不存在。跨侧同 ID、不同 basis 也会拒绝。

   但两侧同时缺 `stable_id_basis` 时 `None == None`，守卫被绕过；且 raw basis 比较存在 NFC 假拒绝。

9. 同阈值规模门截断 — **RESOLVED**

   两侧阈值均为 2，前部插入后得到 `added=1 + removed=1`；两条均 `truncation_suspect=true`，两侧 `over_threshold` warning 和 MD 两处 `⚠截断嫌疑` 均存在。

10. Concepts 重复/NFC-NFD 孪生种子 — **RESOLVED**

   三行引用只生成 1 个候选，另外两行均在 `sources` 留下 NFC 去重说明，`rc=0`。

11. 机器尾段与 fence/HTML 注释 — **PARTIAL**

   普通 Recent Activity 刷新保持 unchanged；代码 fence 和普通 HTML 注释修改均得到 `changed(content)`。但存在 HIGH-1 反例。

12. 跨 vault 指纹 — **PARTIAL**

   两份当前引擎产物来自不同 vault 时 `rc=0`，JSON/MD 均告警。但两边同时缺 `vault_fingerprint` 时无告警通过。

13. `derived_overlap` reason — **RESOLVED**

   `overlapping false→true` 后 reason 为 `["content","overlap"]`。

14. Markdown `|` 转义 — **RESOLVED**

   `P(A|B)` 渲染为 `P(A\|B)`，实际表格分隔符仍为 8 个，列数未破坏。

## 本轮新发现

### BLOCKER

无。

### HIGH

1. **普通 HTML 注释可触发 Recent Activity 掩码，静默吞掉后续用户正文**

   输入：

   ```md
   <!--
   ## Recent Activity
   -->
   用户正文版本 A/B
   ```

   预期：HTML 注释和其后的用户正文进入指纹，A→B 应为 changed。实际：两侧指纹相同，diff `unchanged=1`。原因是 Recent Activity 分类在普通注释掩码之外独立运行。[机器分类](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:296)、[注释掩码](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:322)

2. **schema v2 新安全字段可缺失，三道处置同时 fail-open**

   生产 CLI 复现：

   - 删除歧义字段：`rc=0`、`warnings=[]`、输出把歧义投影为 `false`。
   - 两份跨 vault 输入同时删除 `vault_fingerprint`、候选同时删除 `stable_id_basis`：`rc=0`、`warnings=[]`、`unchanged=1`。
   - `index=[]`、`suggested_name=null`、`resolved_name=null`、`basis={}`、anchor 值全为 null/空数组：仍 `rc=0`。

   预期是坏 schema 拒绝；实际入口只验字段存在，不验新增字段及类型。[入口校验](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1049)、[basis 比较](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1181)

3. **证据包当前不是自洽的当前字节证明**

   `sha256sum -c .../judge-and-contract.sha256` 实际退出 1，契约 FAILED；README 指向的 85 条绿证实际仍为 64 条。预期 manifest 和绿证绑定最终交付，实际只绑定了部分旧快照。

### MEDIUM

1. **第二产物拒写时留下第一份 JSON**

   预置 `split-diff-板A.md` 为 symlink，再跑合法 diff：`rc=1` 且 symlink 目标未改，但 `split-diff-板A.json` 已留下。预期零产物/成对发布，实际顺序写入造成半份。[顺序发布](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1595)

2. **NFC/NFD 等价来源名得到同 ID，却被 basis 守卫假拒绝**

   `节点/café.md` → `节点/café.md`，正文、标题路径、ID 均相同；实际 diff `rc=1`，因为产物保存 raw `file`，守卫比较整个 raw dict。[ID 使用 NFC](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:516)、[basis 保存 raw file](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:610)

3. **`--max-units` 接受负数**

   `--max-units -1` 实际 `rc=0`，三候选保留两条，并输出自相矛盾的 `threshold=-1, kept=2, over_threshold=true`。预期拒绝非正整数。[参数无范围校验](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1632)

### LOW

1. §7.1 YAML 示例漏掉后文声明必填的 `basis`。
2. “标题正文不可能含 U+0000”不成立；UTF-8 文件可包含它并制造分隔载荷碰撞。不过当前截断前自检能 fail-closed，因此未升级严重度。[错误假设](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:513)

## 我实际跑了什么

- 指定全套测试，加 `-p no:cacheprovider` 避免审查本身写仓库：**85 passed, 10 warnings**。
- live 缺失两态：默认 **2 failed**；显式允许后 **2 skipped / UNVERIFIED**。
- 两份 manifest 的 `sha256sum -c`：engine/products 全绿；judge/contract 当前红。
- 生产 CLI 对抗夹具脚本：[audit_round2.py](/private/tmp/codex-g53-r2.bJ9PPX/audit_round2.py)，完整机器结果：[results.json](/private/tmp/codex-g53-r2.bJ9PPX/results.json)。
- 同一 preview 连跑两次并 `cmp` JSON/MD：两份均逐字节相等。
- 所有实验写入仅在 `/private/tmp/codex-g53-r2.bJ9PPX`；未编辑仓库，未写真实 vault。
- 审查期间工作树曾被外部继续修改；上述结论绑定本文开头的最终 SHA。仓库要求的 `graphiti-canvas` 本会话不可调用，因此未伪造 Graphiti 结果。


