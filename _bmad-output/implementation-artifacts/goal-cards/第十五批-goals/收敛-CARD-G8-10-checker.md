# 收敛-CARD-G8-10-checker（loop goal）

> 用户 2026-09-20 裁定：按前 14 批方式，一个 goal 连续 develop + GLM-5.3 max + JEV 连续审，直到绑定最终 HEAD 的一轮 **B/H/M/L = 0/0/0/0** 才释放合并门；**不逐轮交主 session**。
> 预授权本 goal 最多 **8 个 develop commit**（从 round 8 起算）；不 amend 已入库历史 commit；连续 2 轮无进展或达到预算 ⇒ 停并交主 session。
> 本 goal 取代之前的 `修复-CARD-G8-10-r8` 单轮块。

## 0 位置与基线
- 工作树：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w
- 分支 card/p6-skills-w；起点 HEAD = dce85102（r7 第 4 commit）；树净。
- r7 评审：codex-review-CARD-G8-10-r7.md，绑定 6816ff71 = B0/H1/M0/L1；r7-H1 = PyYAML `safe_load()` 重复 key last-write-wins（`outcome: "pa\u0073s", outcome: not_yet` ⇒ 只剩 not_yet，v4.5 rc=0）。
- 独立复现：review-high-duplicate-key-repro-20260920T113255.txt；底账 cbfd619d… 未动；checker v4.5 = 6e44e143…；product code diff = 0。
- r1-r7 存档全部冻结；新轮只追加。

## 1 收敛 DoD（只有全满足才放行）
- 绑最终 HEAD 的 GLM-5.3 max 一轮 **B0 / H0 / M0 / L0**。
- 所有已登记 in-scope B/H/M/L 闭合：
  1. r7-H1：重复 mapping key + merge/anchor/scalar alias 隐藏 pass。
  2. r5-M1：nodeid 路径 `..` 归一化/越根。
  3. r5-M2：无行号 evidence 目录与平文 SHA provenance 不绑定。
  4. r6-M1：owner ID 可由 `path:line` 文件名内 ID 子串满足。
  5. r7-L1：`g810-green-*` 标题「树净」与 `dirty=1` 口径冲突。
  6. r6-L1：JEV JSON 缺机器可读 `calls`/`verdict`/`urgency`。
  7. 幽灵引用：UAT/卡文「协议 §2.4」实际不存在（协议只有 §2.1-§2.3）；UAT 更正/登记。
  8. 每轮新发现且属本 scope 的 B/H/M/L。
- 只允许 `_bmad-output/**` 改动；底账内容一字不动；product code diff = 0。
- 任何 finding 需要改 product code / 底账内容 / 用户授权 / live 服务 ⇒ 立即停，登记交主 session；不得扩 scope。

## 2 Loop 协议
- 轮次从 **r8** 起；每轮按同一流程，不再逐轮回主 session：
  1. 读上一轮 GLM 存档 + JEV sidecar + UAT open 项；列出本轮要闭合的全部 B/H/M/L。
  2. 全部修完：新增/更新负控；先红后绿；重锚 digest；正常底账 rc=0；锚群 8/8 仍红；旧失败面不得放宽；底账 shasum 前后同。
  3. 单 commit：message 含 `CARD-G8-10 rN` + `[BATCH-2026-09-18-第十五批]`；不 amend 历史；product diff=0。
  4. JEV 分诊新 commit；输出 JSON + **机器可读 sidecar manifest**（calls / verdict / urgency / risk / review / test / code_files / sha / bound HEAD），sidecar 放 evidence-g810 并进 commit。
  5. GLM-5.3 max 复核新 commit；存档 `codex-review-CARD-G8-10-rN.md`，绑 commit 首对象 + `:(exclude)_bmad-output` 判据。
  6. 解析该轮 B/H/M/L：全 0 且树净、product diff=0、所有已知 M/L 闭合 ⇒ 说「复核第十五批 P6」，释放合并门；否则自动进入 rN+1。
- 上下文检查点：session context > 85% 或需要重启时，写 `evidence-g810/loop-state-rN.md`（HEAD、digest、open findings、下一轮动作、commit 预算余量），新 session 用同一 goal block 续跑。
- 无进展检测：连续 2 轮 open B/H/M/L 总数不降，或同类失败重复出现且无新增证据 ⇒ 停并交主 session，不盲目循环。
- commit 预算：最多 8 个 develop commit；超预算 ⇒ 停并交主 session。
- 允许的停点只有：scope 外、需用户授权、无进展 2 轮、commit 预算耗尽、工具/环境硬失败。其余一律继续 loop。

## 3 已知 finding 的闭合口径
- r7-H1：`StrictSafeLoader` 拒绝重复显式 key；`yaml.compose_all` node 级扫描 `outcome == pass`（覆盖 anchor/merge 源）；constructed-data 扫描覆盖 scalar alias/merge 结果；负控 A/B/C 必须 red，正常底账 rc=0。
- r5-M1：nodeid 路径走与 refs 相同的 root 边界/归一化；`backend/tests/../app/...` 负控必须 red。
- r5-M2：无行号 evidence 目录与平文 SHA 必须可解引用并进 digest；移走 evidence 目录/无效平文 SHA 负控必须 red。
- r6-M1：owner ID 必须是独立 token；owner cell 仅有 `path:line` 文件名含 `G4-3` 不满足；负控必须 red。
- r7-L1：checker 输出区分 tracked/untracked dirty；UAT 措辞更正；不修改 r7 已入库证据文件本身。
- r6-L1：sidecar manifest 由本 goal 在 evidence-g810 生成；不改 `scripts/jev_review_triage.py`；sidecar 字段不全 ⇒ L 仍 open，loop 不得退出。
- 幽灵引用：UAT/卡文记录 actual protocol §2.1-§2.3；标准 block 可保留 §2.4 作为批次格式锚，但正文注明历史引用。

## 4 硬边界
- 只改 `_bmad-output/**`（checker/UAT/evidence/loop-state/sidecar）；底账内容不动；product code 不动。
- 不 push、不装包、不写 live vault、不连 7691/7687、禁用 stash/checkout-HEAD 式还原；不 amend 已入库 commit。
- 只允许 JEV + GLM-5.3 max 两个外部审；不引入第三个模型。
- r1-r7 存档保持字节稳定；新轮只新增 `codex-review-CARD-G8-10-rN.md` / evidence 新件。

## 5 完成与停止
- 完成：B0/H0/M0/L0 绑最终 HEAD；全部已知 M/L 闭合；JEV sidecar 机器可读；UAT/台账更新；树净；product diff=0；commit 数在预算内；底账 cbfd619d… 不变。此时才说「复核第十五批 P6」，交主 session 做 G8-10 → batch15-integ 合并与集成门。
- 停止：报告当前 round、HEAD、open B/H/M/L、停止原因（scope/授权/无进展/预算/硬失败）、已尝试修法与下一步选项；不得合并、不得改底账、不得自动换 scope。
- 结构锚：unit 红基线 `evidence-b15/unit-red-baseline-9c4e7e82.txt`，`grep -vc '^#'` = 33（只作开工自证，本 goal 不跑 pytest）；D-15 = 「Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0」（本 goal 扩为 M/L 也 0）。
- 「本卡未证明什么」与「台账待登记条目」：每轮 UAT 各 ≥4；未闭合 M/L 不得从清单消失。
