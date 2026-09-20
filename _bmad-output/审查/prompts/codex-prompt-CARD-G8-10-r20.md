你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景

CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r20（含 r20 补）= 用户 2026-09-20「追加修复，直到审核说没有问题而通过」授权的第 5 个预算外轮**。闸门：**绑最终 HEAD 的一轮 B/H/M/L = 0/0/0/0** 才说「复核第十五批 P6」并释放合并门。

上一轮 **r19 = B0/H0/M1/L1**（存档 `codex-review-CARD-G8-10-r19.md`，绑 `e8aec46f`）：M-1 `row-file` 仍接受「同目录尾串」（`<basename>-junk`）；L-1 UAT「真实行 rc=0」缺少绑定到当轮生成器 SHA 的复跑件。

- **本轮绑定**：`fd2046f7fcb87b489ae805f26c987e2343cd34c7`（r20 补 commit；父 = `74746264`，后者父 = `e8aec46f`）。
  - **已入库（该 SHA 树内；逐条 `git cat-file -e fd2046f7:<path>` 校核过：24/24 通过）**：`g810-r12-artifact-audit.zsh`（v2.6.3）、`g810-r8-sidecar.py`（v4.9-r20.2）、`g810-r15-audit-ctl.zsh`（C1–C9）、`g810-r15-sidecar-negctl.zsh`（N1–N14+P3+T+P1）、`g810-r20-sidecar-rerun.zsh`；`audit-ctl-r15-20260920T162933-10633.txt`、`sidecar-negctl-r15-20260920T163053-12113.txt`；`sidecar-g810-r20-74746264.json`、`jev-triage-74746264.json`、`jev-triage-74746264-run-20260920T163016.txt`；两代复跑件（`…-v4920`×2 = v4.9-r20 口径、`…-v49202`×2 = v4.9-r20.2 口径）与两个合并件；`codex-review-CARD-G8-10-r19.md`、`prompts/codex-prompt-CARD-G8-10-r19.md`、`jev-triage-e8aec46f.json`、`jev-triage-e8aec46f-run-20260920T162007.txt`、`sidecar-g810-r19-e8aec46f.json`、`g810-green-r11-20260920T162006.txt`、`artifact-audit-r12-20260920T162006-7047.txt`、UAT。
  - **未入库（收尾阶段新增；本 prompt 不据其数字作论断）**：`g810-green-r11-20260920T163127.txt`、`artifact-audit-r12-20260920T163127-12432.txt`、`jev-triage-fd2046f7.json`、`jev-triage-fd2046f7-run-20260920T163128.txt`、`sidecar-g810-r20b-fd2046f7.json`、本 prompt、本审查存档。
- **r20/r20 补 修法**：①（r19-M1）`row-file` **真后缀**（`pos+len(basename)==len(首列去尾引号)` 且界符 `/` 或行首）⇒ `<basename>-junk` 红（**N14** 控制）；②（r19-L1）补两轮真实输入 × 当轮生成器的**干净复跑**（v4.9-r20 = `…-v4920`；v4.9-r20.2 = `…-v49202`）；③（r20 实测量缺陷，**主动登记**）JEV VERDICT 列实测会输出**小写** `pass` ⇒ verdict 白名单改**大小写不敏感**、行末列 `[A-Za-z]+`，且**恒取行末列**（原实现小写时退回取 risk 列、把 `pass` 记成 `logic`）⇒ r20 的 sidecar 用 v4.9-r20.2 重生成（`verdict="pass"`）；④ 控制件加 **P3**（真实 r20 小写 verdict 正控）；⑤ 轮次登记：r20 未形成可审轮（当轮生成器判红 `pass` 行 ⇒ 当轮 sidecar 不可产），r20+r20 补合并送审。
- **product code diff = 0**（`4120e0b6..fd2046f7` 排除 `_bmad-output` 为空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。

# ② 请独立核对

1. r19 的 1 M + 1 L 是否闭合（真后缀是否拦 `-junk`；复跑件是否绑定到当轮生成器 SHA）；r20 实测缺陷的两处修法是否成立（大小写 + 行末列），P3 是否真红/绿正确。
2. 控制件：审计 C1–C9（9/9）；sidecar N1–N14（N12/N13/N14 均 `row-file`）+ P3（rc=0、`verdict="pass"`）+ T（`partial=true`）+ P1（真实 r16）是否可逐条对上。
3. 已入库 24/24 与未入库 7 件是否与 `fd2046f7` 树一致（可 `git cat-file -e` 复算）。
4. 声明边界（§十.36–74）是否仍属「可接受」；若需计 M/L，给最小反例。

# ③ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」）。某级无条目写「无」。

**若四级全无，请在开头写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`**（该行是本 goal 释放合并门的依据）；否则给分级与最小反例。

# ④ 边界

只读；不连任何库；只评生成器 v4.9-r20.2 + 审计 v2.6.3 + r20/r20 补证据面 + 上述闭合项；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r20 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界在**本轮**扩面。
