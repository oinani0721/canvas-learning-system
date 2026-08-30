# Codex 审查 · CARD-G5-3（第 1 轮）

## 裁决

**不通过** — `occurrence` 会在重名调序/改名时静默转移 ID 所属，G5-10 的持久化指纹契约也存在创建后立即误报漂移的时序矛盾；当前证据包又未绑定当前实现字节。

审查锚：引擎 SHA-256 `1b5e2310bc7ac5ec240eac5d063f5b3ffc68df784eb6c2d0d5ff10babfe79190`。

## BLOCKER

- **重名调序/改名会静默“换绑” stable_id** — [split_preview.py:462](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:462)、[split-stable-id-contract.md:129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:129)、[split-stable-id-contract.md:157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:157) — ID 实际绑定“同路径第 N 个槽位”，不是内容单元。现有文档虽披露删除首个重名项的风险，却仍无条件声明“改标题=removed+added”和“整体调序不换 ID”。— **复现**：`old=[例题(A),例题(B)]`、`new=[例题(B),例题(A)]`，实际两个 ID 留在原序号、两份指纹对调，diff 为 `changed=2,moved=0`；把中间“讨论”改名为“例题”时，新小节直接继承旧 `例题#2` 的 ID，真正的旧 `例题#2` 被挤成新 ID。预期是语义单元保 ID 并报 moved，或改名项独立 removed+added；实际发生 provenance 静默错配。— 建议处置：v1 要么对归一化同路径重复项 fail-closed，要么引入不依赖文档序的持久锚；在此之前不能把 `split_stable_id` 定义为权威身份。补上“重名交叉调序、改名进入/退出重名集合”裁判。

- **G5-10 的创建指纹与 re-baseline 自相矛盾** — [split-stable-id-contract.md:257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:257)、[split-stable-id-contract.md:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:268)、[split-stable-id-contract.md:275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:275) — 契约要求节点保存创建前 preview 的指纹且“不随来源更新”，同时承认插入派生 callout 会改变指纹，只要求重跑 preview；这不能修正节点 frontmatter 中已持久化的旧指纹。— **复现**：在 `/private/tmp/codex-g53-audit.ok5KPN/latest-extra/` 对候选创建前运行 preview，再只插入一行派生 callout；stable ID 保持不变，但指纹从 `cf1-6eea325e0f0aa5ca` 变成 `cf1-e4f76718f60e99d7`。预期创建完成后尚无用户漂移；实际按 §7.1 比较会立即报“来源已漂移”。— 建议处置：明确原子时序，并保存 post-write re-baseline 指纹；或者分别持久化 `confirmed_fingerprint` 与 `post_write_baseline_fingerprint`。同时给基线增加不可变文件名/批次和 SHA，不能只存会被下一次 preview 覆盖的 basename。

## HIGH

- **归一化后空标题使纯行漂移被误报 changed** — [split_preview.py:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:190)、[split_preview.py:534](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:534)、[split-stable-id-contract.md:155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:155) — `## 一、` 经 `clean_heading` 变为空串，名称回退却用含行号的 `file:line`。— **复现**：同一小节只在 frontmatter 增加 5 行；ID 和指纹均相同，但名称从 `derived-62bb6c` 变为 `derived-406a22`，diff 为 `changed=1, reason=["name"]`。预期按卡片 (d) 为无变化；实际误报。— 建议处置：拒绝空归一标题，或由 stable basis/stable_id 生成 fallback 名，禁止使用行号。

- **§4.1 #7 的 whole→section 声明存在直接反例** — [split_preview.py:571](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:571)、[split-stable-id-contract.md:135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:135)、[test_split_stable_id.py:622](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/backend/tests/skills/test_split_stable_id.py:622) — 标题层级和 `basis` 不参与 ID；裁判只测了路径不同的典型形态。— **复现**：种子从 `# 讲义 + 正文` 改成无 H1 祖先的 `## 讲义 + 同正文`。前后路径均为 `["讲义"]`，ID、指纹、名称全同，只有 `basis` 从 `seed-note-whole` 变成 `seed-note-section`；diff 实际 `unchanged=1`，不是文档声称的 removed+added。— 建议处置：把 whole/section 类型判别量加入身份载荷，或收窄 #7 声明并让 diff 显式检测 `basis` 变化。

- **当前 live/绿证没有绑定当前字节，且 live 缺失仍可整套绿** — [test_split_stable_id.py:745](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/backend/tests/skills/test_split_stable_id.py:745)、[README.md:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/README.md:6)、[engine-and-products.sha256:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/engine-and-products.sha256:1) — 当前裁判有 37 个测试函数，README/绿证仍是 30 新 + 34 存量；证据绑定的引擎为 `5081846c…`，当前为 `1b5e2310…`。— **复现**：将裁判副本的 `LIVE_VAULT` 指向不存在的 `/tmp` 路径后，全文件退出码仍为 0：`35 passed, 2 skipped`。预期卡片 (d) 的“≥2 块真实板”缺失时硬门失败；实际可静默跳过。— 建议处置：重新生成绑定当前引擎、裁判、契约 SHA 的红绿/live 证据；live 不可用时卡片验收任务必须失败或明确标记 `UNVERIFIED`，不能计作绿。

## MEDIUM

- **“拒绝路径零产物”存在空目录和半份产物反例** — [split_preview.py:911](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:911)、[split_preview.py:1402](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1402)、[split-stable-id-contract.md:328](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:328) — 输入形状和输出文件名长度没有完整前置校验。— **复现**：① `board="A"*300` 时先创建 out-dir，随后 `ENAMETOOLONG`，留下空目录；② 候选 `source_anchor={}` 且制造一次 content change，先写出 `split-diff-板A.json`，渲染 MD 时 `KeyError: 'file'`，留下半份产物。预期零产物；实际分别留下目录和 JSON。— 建议处置：在 `prepare_out_dir` 前验证完整候选 schema、board 的 UTF-8 文件名字节长度；先完成 JSON/MD 双渲染，再采用成对原子发布或失败清理。

- **NFC(file_rel) 与“文件改名必换 ID”声明冲突** — [split_preview.py:473](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:473)、[split-stable-id-contract.md:131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:131)、[split-stable-id-contract.md:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:134) — 文件路径确实做了 NFC，因而 canonical-equivalent 的路径字节变化不会换 ID。— **复现**：板名从 NFC `café` 改成 NFD `café`；`stable_id_basis.file` 原始字符串不同，但 stable ID 完全相同。预期按 #6“全板换 ID”；实际不换。— 建议处置：在 #3/#6 明确排除 NFC/NFD 等价改名，并把“文件路径字节形态归一”补入 §4.2。

## LOW / 观察

- **64-bit 截断自检的能力被说得过满** — [split_preview.py:719](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:719)、[split-stable-id-contract.md:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:203) — 同 preview 重复检查无法判断“身份键缺维”与真实截断碰撞，也不覆盖跨 preview 同 ID、不同 basis。— **复现**：给旧、新各放一个相同 stable ID，但把新侧 `stable_id_basis.heading_path_normalized` 改成完全不同值；diff 实际报 `unchanged=1`。预期若要声称碰撞自检覆盖，应拒绝 basis 不一致。— 建议处置：共同 ID 比对时核对 namespace+basis；至少把“而不是哈希碰巧碰撞”改为概率性声明，必要时持久化完整摘要。

- **R2/R3/R4 的正向门有效** — [test_split_stable_id.py:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/backend/tests/skills/test_split_stable_id.py:208)、[split_preview.py:971](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:971)、[split_preview.py:1069](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1069) — v1 字段投影及旧键相对顺序完全一致；当前全仓未找到其他 split-preview 消费方或 MD 表解析方；576 组排列验证记账、确定性和相邻交换只标 `{C}`。`change_reasons` 是硬编码 `conflict/content/name`，当前恰为字典序，并非实际 `sorted()`。— **复现**：legacy projection 输出 `legacy_projection_equal=True`；7 个建议变异分别产生 1–6 条失败，没有全绿变异。— 建议处置：保留这些门，新增上述四个边界反例；如 reason 集合未来扩展，直接排序并加全组合断言。

## 我实际跑了什么

- `git diff HEAD --stat`、`git status --short --untracked-files=all`、`git diff HEAD --check`：最终 tracked 改动为引擎和存量裁判；新裁判、契约、证据包仍是 untracked；`diff --check` 通过。
- 完整读取四个被审文件及证据包脚本、日志、JSON、SHA 清单；核对 `board_manifest_service.py:57` 的常量。
- `backend/.venv/bin/pytest backend/tests/skills/test_split_preview.py -q`：`34 passed`。
- 将当前裁判复制到 `/tmp/codex-g53-audit.ok5KPN/latest-judge.py`，只把 `SCRIPT` 指向当前引擎副本、把 live 路径改成不存在的 `/tmp` 路径：
  - 排除 live：`35 passed, 2 deselected`。
  - 不排除 live：`35 passed, 2 skipped`，退出码 0。
- 在 `/private/tmp/codex-g53-audit.ok5KPN/latest-cases/` 运行真实 CLI preview/diff，复现重名调序、改名进入重名集合、空标题行漂移、whole→H2 路径碰撞。
- 在 `/private/tmp/codex-g53-audit.ok5KPN/latest-guards/` 逐项验证 schema v1、跨板、缺 ID、缺指纹、重复 ID、非法 JSON、路径逃逸均零产物；另复现超长 board 留空目录、坏 `source_anchor` 留单份 JSON。
- 穷举 4 个共同候选的 `24×24=576` 对排列：summary 恒等、状态互斥、二跑确定；`[A,B,C,D]→[A,C,B,D]` 只报 `C moved`。
- 变异副本全部位于 `/tmp/codex-g53-audit.ok5KPN/`：去 occurrence、加入行号、去 NFC、去 clean_heading、去 rstrip、LCS 返回空集、删除 schema 守卫；七项全部使裁判变红。
- 以 HEAD 版引擎和当前引擎跑同一小 vault，移除 v2 新键并归一 schema/generator 后旧 JSON 投影完全相等，旧键相对顺序不变。
- 全仓定向 `rg` 未找到当前生产消费方读取 split-preview JSON，也未找到解析新增 MD 表格列的代码。
- **未运行原始 live 测试，未 stat/read/write `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault`；所有新增动态输入均在 `/tmp` 的物理路径 `/private/tmp` 下。**


