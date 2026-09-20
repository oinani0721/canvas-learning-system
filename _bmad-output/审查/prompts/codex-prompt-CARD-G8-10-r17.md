你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r17 = 用户 2026-09-20「追加修复，直到审核说没有问题而通过」授权的第 2 个预算外轮**。闸门不变：**绑最终 HEAD 的一轮 B/H/M/L = 0/0/0/0** 才说「复核第十五批 P6」并释放合并门。

上一轮 **r16 = B0/H0/M2/L6**（存档 `codex-review-CARD-G8-10-r16.md`，绑 `884af91a`）：M-1 prompt 把收尾件 `g810-green-r11-20260920T155050.txt` 列入「已入库证据」；M-2 verdict「数据行」只约束列形/白名单，可被伪造行恒绿；L-1 伪 `28.` 编号可把名字面起点后移；L-2 行首空白只认 ASCII space/tab；L-3 `blob_in_ref` 未验 object type；L-4 控制件标题版本残留；L-5 UAT 把 P1 标「真实 r15」（实为 r14）；L-6 §十一.59 把 PENDING 链当已闭合。

- **本轮绑定**：`4569aef4d30c65c279f65ebe39d01b06cf6d784b`（r17 develop commit；父 = `884af91a`）。
  - **已入库（该 SHA 树内，本 prompt 逐条 `git cat-file -e 4569aef4:<path>` 校核过：**21/21 通过**（20 个文件 + 本 UAT））**：`g810-r12-artifact-audit.zsh`（v2.6.3）、`g810-r8-sidecar.py`（v4.9-r17）、`g810-r15-audit-ctl.zsh`（C1–C9）、`g810-r15-sidecar-negctl.zsh`（N1–N11+T+P1）；`audit-ctl-r15-20260920T160235-94574.txt`、`sidecar-negctl-r15-20260920T160236-94522.txt`；v2.6.3 逐 REF 七件 `artifact-audit-r12-20260920T160243-94973.txt` / `…160244-95000.txt` / `…160246-95027.txt` / `…160247-95055.txt` / `…160248-95086.txt` / `…160250-95114.txt` / `…160251-95142.txt`；`codex-review-CARD-G8-10-r16.md`、`prompts/codex-prompt-CARD-G8-10-r16.md`、`jev-triage-884af91a.json`、`jev-triage-884af91a-run-20260920T155052.txt`、`sidecar-g810-r16-884af91a.json`、`g810-green-r11-20260920T155050.txt`、`artifact-audit-r12-20260920T155050-89409.txt`、UAT。
  - **未入库（收尾阶段新增；本 prompt 不据其数字作论断，仅供你收尾后复核方向）**：`g810-green-r11-20260920T160348.txt`、`artifact-audit-r12-20260920T160348-95809.txt`、`jev-triage-4569aef4.json`、`jev-triage-4569aef4-run-20260920T160350.txt`、`sidecar-g810-r17-4569aef4.json`、本 prompt、本审查存档。
- **r17 修法（§九.70，8 项）**：①（M-1 制度化）prompt/UAT 分「已入库（审SHA 内可解）」/「收尾阶段新增（未入库）」两栏且不混用；②（M-2）verdict 数据行与 JSON `files` **互核**（行数 == len(files)；首行 churn/urgency/review/test/risk 相等，伪行 ⇒ `row-*` 红）；③（L-1）锚要求标记前尾两项 = 27,28 且 `28.` 唯一；④（L-2）行筛/解析用 `str.lstrip()`（Unicode 空白）；⑤（L-3）`blob_in_ref` 另验 `cat-file -t == blob`；⑥（L-4）控制件标题版本同步；⑦（L-5）sidecar 控制件 P1 改用当轮真实 JEV（r16）；⑧（L-6）§十一.59 改「待收尾回填」。
- **product code diff = 0**（`git --no-pager diff --stat 4120e0b6 4569aef4 -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。

# ② 请独立核对（不要采信）

1. r16 的 2 M + 6 L 是否闭合（尤其：互核只做首行/行数——多行表的第 2..N 行对齐未做，已声明边界 §十.62；编号连续性只约束尾两项，已声明 §十.63）。
2. 「已入库」清单 20/20 是否真在该 SHA 树内（可用 `git cat-file -e` 逐条复算）；「未入库」栏是否恰好只含收尾件。
3. 控制件：审计 C1–C9（含 C9 伪 28 → `marker-context`）、sidecar N1–N11（含 N11 伪行 → `row-churn`）+ 孪生 T + 真实正控 P1 是否都能在存档件里逐条对上标签与 rc。
4. 逐 REF 审计：`74d58d14`/`2e52f551`/`4c5777d0`/`c84a0cc4` rc=1（各自真实缺口）、`b93812ea`/`0aa87523`/`884af91a` rc=0 是否可复算。
5. 声明的边界（§十.36–64）是否仍属「可接受」或应计 M/L。

# ③ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若四级全无，请在开头写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`**（该行是本 goal 释放合并门的依据）；否则写 `BLOCKER: … / HIGH: …` 并给最小反例。

# ④ 边界

只读；不连任何库；只评审计 v2.6.3 + 生成器 v4.9-r17 + r17 证据面 + 上述闭合项；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r17 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界在**本轮**扩面——若你认为需扩面，记为 MEDIUM/LOW 并指出准确边界即可。
