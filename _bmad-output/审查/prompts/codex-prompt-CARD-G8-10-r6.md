你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，**纯台账卡、零代码**）——**r6 = 用户 2026-09-20 授权的「微修复核轮」**（不是第 6 轮续审）。来历：r5（B0/H2/M3/L1）两条 HIGH 都出在**核对脚本自身**（「声称可核但实际未核」类微缺口），用户裁定「不接受 H2 登记后合并」，并**显式豁免 G8-10「≤2 commit」限制**、授权第 3 个收尾 commit；限定**只修核对脚本 2 HIGH + 1 LOW，底账内容不动，两处 MEDIUM 仅登记**。

- **本轮绑定**：`9e058c5d`（= 收尾 commit ③ 首对象；其父 = `c35eb6d0`；底账内容仍为 `4120e0b6` 版，sha256 `cbfd619d…` 一字未变）。r6 全部改动只在 `_bmad-output/**`：核对脚本 v4.3 → **v4.4**（sha256 `6841bddf…` → `69d9e281d7f24ec4917cefd7aeba6e3a82df4b2ea229865e007dcdaf0027ff2f`）+ 本单 + evidence；**product code diff = 0**。
- **H1 修法**（`check_g810_refs.py:320-321`）：pass 扫描正则加可选引号 → `outcome[:=]<sp>*["']?pass`（**先去反引号**的口径保留：§5 说明文字里的引用仍不误报）。
- **H2 修法**（`:94-108` 新 helper `_owner_scan_text()` + 两处调用）：owner cell 的白名单扫描不再 `re.sub(r"`[^`]*`","")` **整段剥**——反引号内容**保留**（仅去反引号字符）后交 `_WORD_RE.findall`；唯 `path:line` 引用（v4.3 起按树根边界校验）与 ID token（由允许集精确比对）整段剔除。**卡文最小修法的字面版**会把 owner cell 里 `path:line` 的路径片段与引号内 ID 一起误报 ⇒ 正常底账假红，故取等价但白名单安全的口径（差异已在 UAT §九.16 登记）。
- **LOW 修法**：usage `--expect-digest <16hex>` → `<32hex>`。

**最小读取面**（其余不必读）：

1. 脚本 diff：`git --no-pager diff --no-color c35eb6d0 9e058c5d -- _bmad-output/审查/evidence-g810/check_g810_refs.py`；并读 v4.4 全文（`_owner_scan_text` 与 pass 扫描两处）。
2. 两段负控（**先红后绿**，各 2 相位）：`negctl-A-r6-pre-20260920T102453.txt`（v4.3 假绿 rc=0）→ `negctl-A-r6-post-20260920T103139.txt`（v4.4 rc=1 含 `pass-unsupported`）；`negctl-B-r6-pre-…`（假绿）→ `negctl-B-r6-post-20260920T103139.txt`（rc=1 含 `owner-invalid … '张三'`）；**post2 代绑 `9e058c5d`**：`g810-green-r6-post-20260920T103139.txt`（rc=0，digest `a89b2768…`）。锚群 `anchor-battery-r6-v44-20260920T102657.txt`（8 条旧锚形态 8/8 红 + 对照 rc=0）。
3. UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`：§九.13（r5 处置）/ §九.16-19（r6 微修/收尾结构/作废件/MEDIUM）+ §十一.7-14（台账待登记）；r6 判定字段 = 收尾 amend 回填（本 prompt 随该 amend 入库）。
4. 底账行段：`:160-170`（§2.13 六链表头 + 检索/复习行）、`:244`（§3 observability 行）、`:263-267`（§5 G8-10 append）。
5. 送审前 JEV 分诊：`jev-triage-9e058c5d.json`（jev-1.13.0，calls=1；唯一代码文件 = `check_g810_refs.py`，+25/−6，urgency 2.43 / P(review)=0.64 / risk=logic / VERDICT REVIEW）。⇒ ③ 的排序即取该 urgency。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. r5 两条 HIGH 已按最小修法闭合：引号标量 pass 记录必红（负控 A 改后 rc=1 含 `pass-unsupported`）；反引号内伪 owner 必红（负控 B 改后 rc=1 含 `owner-invalid: row1 (检索链) 非白名单描述词 '张三'`）。
2. **改前**这两段在 v4.3 下 rc=0（**假绿**）——两段 pre 相位存档即「声称可核但未核」的实证。
3. **未放宽旧失败面**：8 条旧锚形态复跑 8/8 红（无引号 `G99` / 平文 `张三` / 混合 owner / `ref-missing` / 文句缩短 / nodeid 空名 / `../` / 绝对路径），对照 rc=0。
4. **未越界**：底账内容一字未动（`cbfd619d…` 恒同，两段负控 `sha_equal=yes`）；只改 `_bmad-output/**`；两处 MEDIUM（nodeid 路径归一化 / 无行号 evidence 与平文 SHA 不绑定）**只登记未修**。
5. **digest 重锚（三值）**：v4.3@`c35eb6d0` = `52ffaaee421ea4c55e013a90f53bdb19` → v4.4@`c35eb6d0` = `b4291854fee3d7c1b5ee74a5e67c6cbf` → v4.4@`9e058c5d` = `a89b276840b99159d19400ffa2ffe365`（脚本自身 sha 进 digest，旧锚不再有效）。

# ③ 请按重要性回答（JEV urgency 降序：唯一代码文件 = checker，urgency 2.43 / risk=logic）

① 两条 HIGH 的修法是否真的闭合？给一条**未被拦下的输入**或确认闭合。重点两处：(a) `_owner_scan_text()` 把 `path:line` 引用与 ID token 整段剔除——是否留下新的穿透面（例如伪 owner 与 `path:line` 形态混写、或反引号跨列不配对）；(b) pass 扫描的引号口径是否仍漏掉其它**有效语法的 pass 记录**写法。
② 在「定位=一致性核对 + 已声明边界」下，脚本 v4.4 是否还有与**其声称**不符的恒绿面？（r5 点名的两处 MEDIUM 仍在且**按卡文只登记不修**——请判定它们是否仍属「已登记」，而非新 HIGH。）
③ r6 证据链是否自洽：负控先红后绿、8/8 锚、digest 三值、`sha_equal=yes`、post2 代绑 `9e058c5d`、UAT 的 PENDING 字段口径（收尾 amend 回填）。
④ r6 收口条件（**B/H = 0**）是否满足；不满足请给最小反例输入。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`** —— 该行会被用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评核对脚本 v4.4 与本次 r6 证据面；不重评底账内容本体（r1-r5 已五轮独立核对且均未发现假归属）；不评各 owner 卡本体；不重裁 §1 判定纪律；两处 MEDIUM 已按用户裁定「只登记不修」，不得仅据此判 HIGH（除非它们与脚本**声称**相矛盾）。
