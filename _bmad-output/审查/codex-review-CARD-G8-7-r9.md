# CARD-G8-7 r9 复审报告（判据覆盖自审补后复审）

**绑定核对**：`git rev-parse --short=8 HEAD` = `49247d54` ✓（= FINAL）；PREV=`1464de1f` ✓。`d9d64ea1..49247d54` 排除 `_bmad-output` **为空** ✓（零代码成立）。

## 独立核验结果（对应 ③ 各点）

| 核验点 | 结果 |
|---|---|
| ⓪ 59/59 sha256+bytes | **证实**：逐条循环比对 0 MISMATCH；J06 副本（`evidence-g87-journey/b15-g8-7/journeys/J06/manifest.json`）validator 独立复跑 **PASS rc=0**，同为 59 条（repo:// 前缀差属预期格式差） |
| ① 形态计数 | **证实（按当前树）**：允许面 00/01 = 5、03/04/05 = **7**（03:1+04:4+05:2）、第三方 = 15，合计 27；与 T-3.7 及送审自述一致。但存档冻结值写 6（见 L1） |
| ① 意图两段 | **部分**：(1) `cp\|mv\|install` 重跑 rc=1、0 命中 ✓；(2) `tee\|cat\|shutil.copy` **今日重跑 rc=0、2 命中**（见 M1，命中为登记文本非命令） |
| ② 判定方向 | **证实未写反**：存档 D 节明写「A=红 / B=绿」并「交主 session 裁定是否收窄」，未自裁收窄、未混为全绿 |
| ③ 重建非冒充 | **证实**：`minute0…txt:2` 明示「非当时落档/不冒充当场存档」；不可重建项（3 当时 status、6 sed 深核）如实列「未落档」；但第 4 条存档自身有缺陷（见 H1） |
| ④ 索引计数 | **证实**：manifest 实测 59（35+13+9+2）；journey `04-journey-log.md:28` = 59 件；UAT `:11`（77/59）、`:82`、`:162` 均为 59，`find $EV -type f | wc -l` = **77**；无残留 57/75（journey `:193` 的「57→59」为变更说明非残留） |
| ⑤ 零代码/零 live 写 | **证实**：排除 diff 为空；`d9d64ea1..49247d54` 不触碰 `fsrs_bridge.py`/`decay_beta.py`；`01-skill-versions.md:34-35` dev==live 2/2 SAME（a766fbcc…/3bf4ed94…） |
| ⑥ 双真相源/翻面 | **无**：manifest 仍为声明权威（journey `:28`「权威 = manifest」）；六环节 ①pass②pass③fail④fail⑤pass⑥fail、result=partial、E2、signoff=pending、outside=2 开放项均未变；**r8 收口结论实质不受影响** |

## 分级清单

### BLOCKER：无

### HIGH：1

- **H1** `minute0-reconstruct-20260920T193730.txt:7-9` ↔ `04-journey-log.md:192` / `UAT-CARD-G8-7-2026-09-20.md:135` / `manifest.json:593`：存档内第 4 条的复核命令**实际失败**（grep/shasum 双双 `No such file or directory`，计数值空白、sha256 为「…」占位），但存档结论 `:18` 将其列入「可重建且值符合预期」，且三处下游登记均写「BASE=33 现复核 / BASE sha256 在案」——「sha256 在案」按存档字面为**不实**。复现思路：按卡文钉死路径重跑 `grep -vc '^#' $BASE; shasum -a 256 $BASE`，与存档 7–9 行对照。**独立复核旁证**：该文件现存在于 feature 树原路径、`grep -vc '^#'`=**33**、sha256=`726e998a7254871838cef77782830e6a719dcc26aefa93abe28fe3e945042cb4`、mtime 09-17——数值为真、存档为败录。属「未被存档拦下的空值登记」，不翻判定；建议补一条 errata/重跑存档后交付。

### MEDIUM：1

- **M1** `fsrs-decay-scope-20260920T193722.txt:23-25`（B(2) 段）↔ `manifest.json:593` + J06 副本 `:593`：意图段 (2)「0 命中=绿」在登记落盘后**不可原样复现**——今日重跑 rc=0、命中 2 行，均为 manifest description 字符串（同时含 `tee|cat|shutil.copy` 字样与 `fsrs_bridge/decay_beta`），存档的排除面只排了本存档自身（`fsrs-decay-scope-`）而**门未覆盖的路径** = 登记文本自引用。命中为描述散文非写入命令，实质绿不变，但「可独立重跑」的字面承诺失效；建议在档内补一句排除说明（排除 manifest description 行）。

### LOW：3

- **L1** `fsrs-decay-scope-20260920T193722.txt:19`：存档写「03/04/05 = 6 行」（含 04 计 3 行），登记后现状为 **7**（T-3.7 自身 `04-journey-log.md:190` 成为第 4 命中）；T-3.7/送审自述写 7。自引用时点差造成的 6↔7 内部不一致，红判定不受影响。复现：现跑分文件 `grep -c` 对比存档清单。
- **L2** `fsrs-decay-scope-20260920T193722.txt:18` ↔ `01-skill-versions.md:37`：「允许面 5 行」中含 01 的结论段（:37，非 sha 表行 :34-35）；按卡文字面「只允许 sha 表行」，该行严格说也在形态过宽面内。方向不变（本就判红、交主 session），仅为分类宽贷一处。
- **L3** `evidence-g87/jev-triage-1464de1f.json`（本次 delta 第 8 个文件，+18 行）：r8 PREV 的 Jev triage 空记录（files=[]、0 token、19:33:49 生成），**未出现在本轮「两件新存档」叙述、journey manifest 59、UAT/journey 任何引用中**（在 `evidence-g87/` 而非 `-journey/`）。零代码约束不破，属叙述面少报一件伴随文件；建议主 session 知悉或在 UAT 台账补一行。

## 结论

两条判据覆盖缺口（(m) 补跑、§二.1 重建）**均已登记且方向处理正确**，r8 收口结论**不受影响**；但因新增 H1（minute0 第 4 条败录被登记为「现复核/sha256 在案」）与 M1（意图段 (2) 登记后不可原样复现），本轮**不满足「无新发现」条件**，不能无条件写「判据覆盖自查闭合，本卡可交主 session」。

**建议**：补 minute0 第 4 条的重跑/errata（一行命令 + 实测 sha256）并在 fsrs-decay-scope 补 M1 排除说明后即可交主 session；或主 session 明确带 H1/M1/L1-L3 限制接收。用户侧开放项（③ 带锚点复跑 / ⑥ 成功页截图 / 思维导图触发者确认 / 签字）维持原状，本轮未评。
