# 修复-CARD-G8-10-r6

> 用户 2026-09-20 裁定：授权 r6 微修（不接受 H2 登记后合并）；显式豁免 G8-10 卡文 ≤2 commit 限制，允许第 3 个收尾 commit。
> 只修核对脚本的 2 个 HIGH + 1 个 LOW；底账内容不动；2 个 MEDIUM 只登记不修。

## 0 位置与基线
- 工作树：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w
- 分支：card/p6-skills-w；基线 HEAD = c35eb6d0（G8-10 存档+UAT；底账 commit = 4120e0b6）
- 开工先核：`pwd` / `git branch --show-current` / `git rev-parse HEAD` = c35eb6d0 / `git status --porcelain` 为空。任一不符：停，交主 session。
- 背景：G8-10 是 batch15 唯一未合入 batch15/integ 的卡；r5 = B0/H2/M3/L1，已达 5 轮上限。两条 HIGH 都在 _bmad-output/审查/evidence-g810/check_g810_refs.py（核对脚本自身），不在底账内容；五轮 ⓪ 项均未发现底账假归属。

## 1 按顺序读取
1. .claude/rules/card-batch-protocol.md §2.4
2. _bmad-output/审查/codex-review-CARD-G8-10-r5.md
3. _bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md §九.13 / §十 / §十一.7
4. _bmad-output/审查/evidence-g810/check_g810_refs.py 全文
5. _bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md
6. evidence-g810 里 r5 的 digest/负控/锚档（expect-digest、anchor、negctl 文件）

## 2 先红（改任何一行之前）
- 负控 A：保持 canonical 底账 YAML/summary 为 not_yet，在 criteria 追加一行 `- {dim: observability-extra, outcome: "pass", coverage: partial}`，按新底账重锚 --expect-digest → 现脚本应 rc=0（HIGH-1：引号 pass 未被拦下）。
- 负控 B：把检索链 owner cell 改成 `` `张三` / `G4-3`（总账 v2 …:500） ``，按新底账重锚 --expect-digest → 现脚本应 rc=0（HIGH-2：反引号内伪 owner 未被拦下）。
- 两段负控后必须 `git show HEAD:<path> > <path>` 还原，shasum 前后逐字同；工作区不得留改动。
- 正常底账基线：`python3 check_g810_refs.py --ledger <底账> --root <树根> --expect-digest <现有digest>` → rc=0。

## 3 最小修（只改 checker + UAT/evidence）
1. check_g810_refs.py:303-305 的 pass 扫描：识别引号标量，最小 = `re.search(r"outcome[:=]\s*[\"']?pass", _scan)`；保留先去反引号，避免 §5 说明文字里的引用误报。
2. check_g810_refs.py:34 / :225-238 的 owner 口径：白名单扫描必须看到反引号内 token；`_ID_RE.findall` 与白名单用同一分词口径。最小 = 对 owner cell 去掉反引号字符但保留其内容后做 `_WORD_RE.findall`，凡不在白名单的 token 报 `owner-invalid`；不要保留先 `re.sub(r"`[^`]*`","")` 的剥法。
3. LOW：usage 的 `--expect-digest <16hex>` 改为 `<32hex>`。
4. 两个 MEDIUM 不修：nodeid 路径 `..` 归一化、无行号 evidence/平文 SHA 不绑定 → 只在 UAT §十/§十一登记为下批卡。
5. 改后复跑：负控 A 必须 rc=1 且含 `pass-unsupported`；负控 B 必须 rc=1 且含 `owner-invalid`；正常底账 rc=0。每段 trap 还原 + shasum 前后同。
6. 重锚 --expect-digest（脚本自身 sha 进 digest），记录 old→new；UAT §九.13/§十一.7 更新 r6 结果、脚本 sha、commit sha、digest、用户第 3 commit 豁免。

## 4 提交边界
- 只允许 _bmad-output/** 改动（checker/UAT/evidence）；product code diff = 0。
- 用户已授权第 3 个收尾 commit（G8-10 ≤2 commit 限制的当次豁免）；commit message 含 `CARD-G8-10` 与 `[BATCH-2026-09-18-第十五批]`，header ≤100 字符。
- *.stderr* / 0 字节文件不入库；不 push；不装包；不写 live vault；不连 7691/7687；禁用 stash 与 checkout-HEAD 式还原（负控只用 git show 还原）。

## 5 JEV + GLM-5.3 max 复核
- 先 JEV：`source ~/.config/jev/env && bash ~/.b15b-drive/jev_triage.sh <最终HEAD> _bmad-output/审查/evidence-g810`。要求 JSON 的 code_files 含 check_g810_refs.py、files 非空、calls>0；按 urgency 写进 GLM prompt ③。若 JEV 0 调用：记 PARTIAL 并说明原因，不得写“已审”。
- 再 GLM：`source ~/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "<r6 prompt>"`。prompt 五分节，最小读取面 = checker diff + 两段负控存档 + UAT §九.13 + 底账 :160-170/:244/:263-267；绑最终 HEAD；该轮 B/H=0 才算过。0 字节或只有 stderr 不计轮次。
- r6 若仍有 HIGH：停，不合并、不改底账，交主 session。

## 6 完成条件
(a) 第 0 分钟核 pwd/分支/HEAD/树净；(b) 改前两 HIGH 可复现且正常底账绿；(c) 只改 checker+UAT/evidence；(d) 负控 A 红于 pass-unsupported；(e) 负控 B 红于 owner-invalid；(f) 正常底账 rc=0 + 新 digest；(g) UAT/存档更新；(h) 第 3 commit（用户豁免）入库、树净；(i) JEV 真审到 checker；(j) GLM r6 绑最终 HEAD 且 B/H=0；(k) product code diff=0、无 stderr/0 字节入库；(l) 跑完说「复核第十五批 P6」并交主 session 做 G8-10 → batch15-integ 合并与集成门。
- 「本卡未证明什么」与「台账待登记条目」各 ≥4（含两 MEDIUM、集成门未跑、JEV 模型身份自证边界、底账五轮独立核对但未做现网故障验证）。

## 7 结构锚（供 15 批同款长度门识别）
- unit 红基线：`evidence-b15/unit-red-baseline-9c4e7e82.txt`；`grep -vc '^#'` = 33。本卡不跑 pytest，只跑 `check_g810_refs.py` 负控；unit 基线只作开工自证。
- D-15：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本卡 r6 上限 1 轮；如审后改脚本，再送一轮并重锚 digest）。
- 「本卡未证明什么」与「台账待登记条目」：见 §6，各 ≥4。
