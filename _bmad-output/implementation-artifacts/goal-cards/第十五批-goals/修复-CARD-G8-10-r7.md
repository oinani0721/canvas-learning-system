# 修复-CARD-G8-10-r7

> 用户 2026-09-20 主 session 裁定：授权 r7 微修（不接受 H1 登记后合并）；显式豁免 G8-10 卡文 ≤2 commit 限制，允许**第 4 个收尾 commit**。
> r6 已证明“正则扫 pass”路线不闭合；r7 改为对 §3 fenced YAML 做真解析。只修 r6-H1；r6-M1/L1 只登记；r6-M2（UAT/证据漂移）如仍在则一并校正。

## 0 位置与基线
- 工作树：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w
- 分支 card/p6-skills-w；r7 基线 HEAD = 9457ba43（r6 第 3 commit；父 c35eb6d0）；树净。
- r6 评审：codex-review-CARD-G8-10-r6.md，绑定 9e058c5d = B0/H1/M2/L1；r6-H1 = `outcome: "pa\u0073s"` 与 `outcome: &not_yet pass` 经 YAML 解析为 pass，但 v4.4 正则 rc=0。
- 底账 §3 只有一个 fenced YAML 块（当前约 :181-:245；以符号/围栏定位，不写死行号）；PyYAML 6.0.3 已可用，`import yaml` 失败必须红，不许静默跳过。

## 1 按顺序读取
1. .claude/rules/card-batch-protocol.md §2.4
2. _bmad-output/审查/codex-review-CARD-G8-10-r6.md
3. _bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md §八 r6 行 / §九.16-22 / §十 / §十一
4. _bmad-output/审查/evidence-g810/check_g810_refs.py（v4.4，sha 69d9e281…）
5. _bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md §3 fenced YAML 块
6. evidence-g810 的 r6 负控/锚群/green/JEV 档（negctl-{A,B}-r6-*、anchor-battery-r6-v44-*、g810-green-r6-*、jev-triage-9e058c5d.json）

## 2 先红（改任何一行之前）
- 负控 A：在 §3 YAML 块内追加 `- {dim: observability-extra, outcome: "pa\u0073s", coverage: partial}`，按新底账重锚 --expect-digest → v4.4 应 rc=0（r6-H1 复现）。
- 负控 B：在 §3 YAML 块内追加 `- {dim: observability-extra, outcome: &not_yet pass, coverage: partial}`，按新底账重锚 --expect-digest → v4.4 应 rc=0（r6-H1 同类复现）。
- 两段负控后 `git show HEAD:<path> > <path>` 还原，shasum 前后逐字同；工作区不得留改动。
- 正常底账 v4.4 rc=0（现有 digest）；r6 的两段定向负控（引号字面 pass / 反引号伪 owner）仍须在 v4.5 后保持 rc=1。

## 3 最小修（checker v4.4→v4.5；只动 checker + UAT/evidence）
1. 顶部 `import yaml`；若 import 失败：failures 追加 `yaml-missing` 并 rc=1，不静默回退正则。
2. 从底账中提取所有 ```yaml fenced blocks（含 §3 与未来追加块）。0 块 → `yaml-blocks` 红；每块逐一解析。
3. `yaml.safe_load(block)`；解析失败 → `yaml-parse-error` 红。
4. 对每一块递归遍历解析后的对象：凡 dict 键 `outcome` 的值解析后 == 字符串 `"pass"`，追加 `pass-unsupported`。只认 `outcome` 键，不误伤 `meta.outcome_states: [pass, fail, not_yet]` 的枚举值。
5. 保留现有正则扫描作为非-YAML/散文面的次级检查（含去反引号口径）；保留 v4.4 的引号正则与 `_owner_scan_text()`，r6-H2 定向闭合不得回退。
6. 更新 docstring/usage：v4.5；依赖 PyYAML；usage `<32hex>` 保持不变。
7. 保留两 MEDIUM 只登记：r6-M1 owner ID 由 path 文件名子串满足 → 下批卡；r6-L1 JEV JSON 无 calls/verdict 字段 → 不下沉修改 scripts/jev_review_triage.py，登记下批工具卡。
8. r6-M2：复核 UAT §八/§九 的 post digest、文件名（post vs post3）、10:31:39 post2/JEV/prompt 是否已入库；如仍漂移，在 _bmad-output 内校正并登记。
9. 重锚 --expect-digest（脚本自身 sha 进 digest）；记录 v4.4→v4.5 脚本 sha、旧→新 digest。

## 4 后绿（改后必须全满足）
- 负控 A rc=1 且含 `pass-unsupported`；负控 B rc=1 且含 `pass-unsupported`。
- r6 负控（引号字面 pass、反引号伪 owner）仍 rc=1，分别含 `pass-unsupported` / `owner-invalid`。
- 正常底账 rc=0 + 新 digest；锚群 8/8 仍红；旧失败面不得放宽；两段负控 shasum 前后同、底账 sha256 不变。
- UAT §九.22/§十一 更新：r7 修法、r6-M2 校正、v4.5 sha、digest 三值链、第 4 commit。

## 5 JEV + GLM-5.3 max 复核
- 先 JEV：`source ~/.config/jev/env && bash ~/.b15b-drive/jev_triage.sh <r7最终HEAD> _bmad-output/审查/evidence-g810`。要求 code_files 含 check_g810_refs.py、files 非空、usage>0；r6-L1（无 calls/verdict 字段）只登记，不改 JEV 脚本；urgency 进 GLM prompt ③。
- 再 GLM：`source ~/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat <r7 prompt>)"`。prompt 五分节，最小读取面 = v4.5 checker diff + 负控 A/B + r6 负控 + UAT §九.22 + §3 fenced block；绑 r7 最终 HEAD；该轮 B/H=0 才算过。0 字节或只有 stderr 不计轮次。
- r7 若仍有 HIGH：停，不合并、不改底账、不自动 r8；交主 session 再裁。

## 6 提交边界
- 用户已授权**第 4 个收尾 commit**（原 ≤2 commit 限制的当次豁免）；不 amend 9457ba43，保留 r6 历史。
- 只允许 _bmad-output/** 改动（checker/UAT/evidence）；product code diff = 0。
- commit message 含 `CARD-G8-10` 与 `[BATCH-2026-09-18-第十五批]`，header ≤100 字符；*.stderr*/0 字节不入库；不 push；不装包；不写 live vault；不连 7691/7687；禁用 stash 与 checkout-HEAD 式还原。

## 7 完成条件
(a) 第 0 分钟核 pwd/分支/HEAD=9457ba43/树净；(b) 改前 A/B 可复现且正常底账绿；(c) 只改 checker+UAT/evidence；(d) 后绿 A/B 红于 pass-unsupported；(e) r6 两负控仍红；(f) 正常底账 rc=0 + 新 digest；(g) UAT/存档更新含 r6-M2；(h) 第 4 commit 入库、树净、product diff=0；(i) JEV 真审到 checker；(j) GLM r7 绑最终 HEAD 且 B/H=0；(k) 无 stderr/0 字节入库；(l) 跑完说「复核第十五批 P6」，交主 session 做 G8-10 → batch15-integ 合并与集成门。
- unit 红基线：evidence-b15/unit-red-baseline-9c4e7e82.txt；grep -vc '^#' = 33（只作开工自证，本卡不跑 pytest）。
- D-15：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本卡 r7 上限 1 轮；如审后改脚本，再送一轮并重锚）。
- 「本卡未证明什么」与「台账待登记条目」各 ≥4（含 r6-M1、r6-L1、集成门未跑、JEV 字段级边界）。
