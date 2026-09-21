# 修复-CARD-G8-10-r8

> 用户 2026-09-20 主 session 裁定：授权 r8 微修（不接受 r7-H1 登记后合并）；r8 是**最后一个自动微修轮**，若仍有 HIGH：停、不自动 r9、不合并，交主 session 在「登记/退卡/重构验证器」中再裁。
> 显式豁免 G8-10 卡文 ≤2 commit 限制，允许**第 5 个收尾 commit**；不 amend dce85102，保留 r7 历史。

## 0 位置与基线
- 工作树：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w
- 分支 card/p6-skills-w；r8 基线 HEAD = dce85102（r7 第 4 commit；父 9457ba43）；树净。
- r7 评审：codex-review-CARD-G8-10-r7.md，绑定 6816ff71 = B0/H1/M0/L1；r7-H1 = PyYAML `safe_load()` 对同一 mapping 重复 key 执行 last-write-wins：`outcome: "pa\u0073s", outcome: not_yet` 解析后只剩 not_yet，v4.5 rc=0（已独立复现）。
- 已验证原型：strict SafeLoader 能对重复 key 抛 `duplicate key: 'outcome'`；merge/anchor 隐藏 pass 虽被 safe_load 覆盖为 not_yet，但 `yaml.compose_all` node 树扫描能命中 anchor 与 merge 源。r8 必须同时做 duplicate-key 拒绝 + node 级 pass 扫描 + constructed-data 扫描。

## 1 按顺序读取
1. .claude/rules/card-batch-protocol.md §2.4
2. _bmad-output/审查/codex-review-CARD-G8-10-r7.md
3. _bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md §九.22-.28 / §十 / §十一.18-25
4. _bmad-output/审查/evidence-g810/check_g810_refs.py（v4.5，sha 6e44e143…）
5. _bmad-output/审查/evidence-g810/review-high-duplicate-key-repro-20260920T113255.txt
6. _bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md §3 fenced YAML 块（当前约 :181-:245）

## 2 先红（改任何一行之前）
- 负控 A（r7-H1 复现）：在 §3 YAML 块内 canonical observability 行后追加 `- {dim: observability-extra, outcome: "pa\u0073s", outcome: not_yet, coverage: partial}`，重锚 digest → v4.5 应 rc=0（重复 key 折叠）。
- 负控 B（merge/anchor 隐藏 pass）：在 §3 YAML 块内加 `defs: &passmap {dim: observability-extra, outcome: pass, coverage: partial}`，并加一条 criteria `- {<<: *passmap, outcome: not_yet}`，重锚 digest → v4.5 应 rc=0（safe_load 后只剩 not_yet）。
- 负控 C（scalar alias）：`meta: {pass_anchor: &p pass}` + criteria `outcome: *p`，重锚 digest → v4.5 应 rc=0 或只在 constructed-data 面可见 pass；r8 必须红。
- 三段负控后 `git show HEAD:<path> > <path>` 还原，shasum 前后逐字同；正常底账 v4.5 rc=0 基线。

## 3 最小修（checker v4.5→v4.6；只动 checker + UAT/evidence）
1. 新增 `StrictSafeLoader(yaml.SafeLoader)`：`construct_mapping` 先扫原始 `node.value`，对非 `<<` 的 scalar key 检重；同一 mapping 两个相同显式 key ⇒ `yaml-duplicate-key` 红。保留 `<<` merge key 语义：单个 `<<` 允许，多个 `<<` 或非 scalar key ⇒ `yaml-key-invalid` 红。
2. 用 `yaml.compose_all()` 取每块 YAML 的 node tree；递归遍历 MappingNode：键 ScalarNode 值 == `outcome` 且值节点 ScalarNode `strip()` 后 == `pass` ⇒ `pass-unsupported`（node 级；覆盖 duplicate 前原始值和 anchor/merge 源）。
3. 用 `StrictSafeLoader` 构造数据；再保留 v4.5 的 constructed-data `_iter_key_values()` 扫描（覆盖 scalar alias / merge 结果 / block scalar / `!!str` 等解析后 pass）。
4. 同块多文档（`---` 第二文档）⇒ `yaml-multiple-docs` 红；0 块/import 失败/解析失败继续 yaml-blocks/yaml-missing/yaml-parse-error 红。
5. 保留 v4.5 的全部既有门：`_yaml_blocks` 全 yaml/yml 块、v4.4 引号正则次级检查、`_owner_scan_text()`、锚群、digest 重锚；不得放宽旧失败面。
6. 更新 docstring/usage：v4.6；记录 strict loader 与 node 级扫描；usage `<32hex>` 不变。
7. r7-M1/L1、r5 两 MEDIUM 只登记不修；r7-L1「树净 vs dirty=1」在 UAT 注明 tracked 净，不修改 r7 已入库证据文件。

## 4 后绿（改后必须全满足）
- 负控 A rc=1 含 `yaml-duplicate-key`（且含 `pass-unsupported`，若原始重复对里有 pass）。
- 负控 B rc=1 含 `pass-unsupported`（node 级 anchor/merge 源命中）。
- 负控 C rc=1 含 `pass-unsupported`（constructed-data alias 命中）。
- r7 两负控（`"pa\u0073s"`、`&not_yet pass`）仍 rc=1；r6 两负控（引号字面 pass、反引号伪 owner）仍 rc=1。
- YAML 门分支控制：0 块 / import 失败 / 解析失败 / 多文档 / block scalar pass / `!!str pass` 全红；正常底账 rc=0 + 新 digest。
- 两段/三段负控 shasum 前后同；底账 cbfd619d… 不变；锚群 8/8 仍红；normal 对照 rc=0。

## 5 JEV + GLM-5.3 max 复核
- 先 JEV：`source ~/.config/jev/env && bash ~/.b15b-drive/jev_triage.sh <r8最终HEAD> _bmad-output/审查/evidence-g810`；要求 code_files 含 check_g810_refs.py、files 非空、usage>0；r6-L1 字段缺口继续登记。
- 再 GLM：`source ~/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat <r8 prompt>)"`；prompt 五分节，最小读取面 = v4.6 checker diff + 负控 A/B/C + r7/r6 回归 + UAT §九.29+ + §3 YAML node 结构；绑 r8 最终 HEAD；B/H=0 才算过。0 字节/只有 stderr 不计轮次。
- **r8 若仍有 HIGH：停，不合并、不改底账、不自动 r9；交主 session 在「接受登记 / 退卡 / 重构验证器」中再裁。**

## 6 提交边界
- 用户已授权**第 5 个收尾 commit**（原 ≤2 commit 限制的当次豁免）；不 amend dce85102，保留 r7 历史。
- 只允许 _bmad-output/** 改动（checker/UAT/evidence）；product code diff = 0。
- commit message 含 `CARD-G8-10` 与 `[BATCH-2026-09-18-第十五批]`，header ≤100 字符；*.stderr*/0 字节不入库；不 push；不装包；不写 live vault；不连 7691/7687；禁用 stash 与 checkout-HEAD 式还原。

## 7 完成条件
(a) 第 0 分钟核 pwd/分支/HEAD=dce85102/树净；(b) 改前 A/B/C 可复现且正常底账绿；(c) 只改 checker+UAT/evidence；(d) 后绿 A/B/C 红于指定条目；(e) r7/r6 负控仍红；(f) 正常底账 rc=0 + 新 digest；(g) UAT/存档更新（含 r7-L1 tracked 净口径）；(h) 第 5 commit 入库、树净、product diff=0；(i) JEV 真审到 checker；(j) GLM r8 绑最终 HEAD 且 B/H=0；(k) 无 stderr/0 字节入库；(l) B/H=0 才说「复核第十五批 P6」，交主 session 做 G8-10 → batch15-integ 合并与集成门；否则按 §5 停。
- unit 红基线：evidence-b15/unit-red-baseline-9c4e7e82.txt；grep -vc '^#' = 33（只作开工自证，本卡不跑 pytest）。
- D-15：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本卡 r8 上限 1 轮；如审后改脚本，再送一轮并重锚）。
- 「本卡未证明什么」与「台账待登记条目」各 ≥4（含 r7-M1/L1、r5 两 MEDIUM、集成门未跑、非 yaml fence / 记录语义边界）。
