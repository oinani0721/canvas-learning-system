# BLOCKER

无。

只读绑定复核：`HEAD = 3139cef763ba16097a3578aab7ef887301cb0061`；tracked 工作区干净，本地 `origin/*` 与 `backup/*` tracking refs 均为同一 SHA；35 个 B15 `merged-squash/card/*` tag 对象均在 `59e1f494..HEAD` 祖先链内。r13 三项的“当前事实”闭合：J07 manifest 与 P5 lane `7af5306b` 的结构化差异仅 `notes`，semantic v2.4.1 输出明示 `[EXCEPTION]` 而非伪相等；`docker inspect` 原始 StartedAt 输出在档；台账 J07 行恢复 3 列。

# HIGH

无。

未发现 r13 后新增的阻断级假绿、未入库主声明、越权写库/写 live vault、force reset/rebase 或破坏性 Git 操作痕迹。分支 reflog 显示 B15 末段为连续 commit，仅有此前 r3 已审计登记的 `1e907037` amend。

# MEDIUM

### MEDIUM-1 G8-10 “final failures=0” 的入库 digest 不能在最终 HEAD 复放

- **位置 / SHA**：  
  - `_bmad-output/审查/evidence-b15-closeout/STATUS.md:15` 声称候选/主干树 G8-10 checker `failures=0 rc=0`；  
  - `_bmad-output/审查/evidence-b15-closeout/g810-clean-rerun-L4-20260920T202805.txt:8-9` 明确“digest 含 HEAD”，`:19-22` 的通过档绑 `head=5a2abccc...`、`expect_digest=45b50cb1...`；  
  - checker 实现 `_bmad-output/审查/evidence-g810/check_g810_refs.py:736-743` 把完整 HEAD 字节纳入 digest，不匹配即 `digest-drift`；最终审查 HEAD 是 `3139cef7...`。
- **一句复现思路**：在最终 HEAD 用档案中的 `--expect-digest 45b50cb12084bf368da672ff19999ca4` 复放，得到 `digest-drift`：actual=`6fa6f3ac8b66aad9f59210b1d062982d`、`head=3139cef7...`、`failures=1`、rc=1。
- **未被拦下的输入**：最终 commit 即使只改 docs，也会因 digest 公式中的 HEAD 分量使旧“全绿”档无法复放；STATUS 仍可把它读作最终树门证据。
- **对照输入**：我只读重跑最终 HEAD 并回填新 actual digest，得到 `chains=6 obj07=5 failures=0 head=3139cef7...`，说明内容检查本身当前可通过；缺的是入库的最终 HEAD digest 档。
- **负控输入**：沿用旧 expected digest 在 `3139cef7` 复放，唯一失败就是 digest 绑定失败。
- **门未覆盖的路径**：无机器规则要求“收口宣称所引用的 G8-10 档”的 `head/expect_digest` 必须等于最终 HEAD，也没有最终 digest `6fa6...` 原始档入库。

### MEDIUM-2 J07 manifest 新例外是“路径级、无内容谓词”的白名单，可掩盖声明范围外的后续漂移

- **位置 / SHA**：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:21-29` 把 `docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json` 加入 `EXCEPTIONS`；`:208-216` 对任意不等该路径直接计入 exception；`cross-lane-semantic2-v241-20260920T234445.txt:13-15,21-22` 显示该例外进入 PASS。声明文案在 `_bmad-output/审查/evidence-b15-closeout/D-15-r13-整改说明.md:5` 只授权“r12 notes 补记开窗终态”。
- **一句复现思路**：当前 candidate `3139cef7` 与 P5 lane `7af5306b` 的 manifest 顶层差异确为 `changed_keys=['notes']`；但把 candidate 的 `known_limitations`、`notes` 后续任意文本或其它校验器仍可接受的字段再改一处，semantic 仍会走同一个 `[EXCEPTION]` 并 PASS。
- **未被拦下的输入**：路径下超出“仅 notes 追加”的后续漂移，包括 notes 中追加与开窗无关的结论，或其它 validator 不判红的 manifest 内容变化。
- **对照输入**：当前最终树与 P5 lane 快照经 JSON 结构化逐 key 比较，只有 `notes` 不同；这证明 r13-B1 的当前事实登记如实。
- **负控输入**：在不改 P5 lane 的情况下变异 candidate manifest 的第二个 key，再跑 v2.4.1；预期应红，实际仍会显示 EXCEPTION 并 PASS。
- **门未覆盖的路径**：exception 没有 lane 范围、candidate/lane blob SHA、顶层 key 白名单或“只允许 notes append”的机器谓词；release manifest validator 只证机械自洽，不替代该差异范围检查。

### MEDIUM-3 semantic 的 shell 归一化会剥掉缩进，可放过 shell heredoc 内 Python 语义破坏

- **位置 / SHA**：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:143-160` 对 `.sh` 只做 `bash -n` + 去注释/空行后的行序列比较，且 `_lines()` 对每行 `strip()`；P3 变更面含 `scripts/j01_e2e.sh`，该脚本在 `scripts/j01_e2e.sh:759-767` 有 `py ... << 'PY'` 内嵌 Python。
- **一句复现思路**：把 heredoc 内 `if not base...:` 下的缩进体 `    sys.exit(4)` 去缩进成 `sys.exit(4)`；`bash -n` 仍通过（heredoc 正文对 bash 是数据），但两版经 `strip()` 后行序列相同，semantic 会判 `SH` 等价，运行期 Python 语义/语法已被破坏。
- **未被拦下的输入**：shell heredoc 中 Python/YAML/JSON 正文的前导空格变化、Python 缩进变化、以及依赖缩进的字面量输出变化。
- **对照输入**：当前最终 candidate 与 P3 lane 的 `scripts/j01_e2e.sh` blob hash 均为 `d69c20b2bdcab166bc584ed66fd65b3703518d9df2c6b34126ea87a465290b86`，字节相等，因此当前无实际漂移。
- **负控输入**：只 dedent heredoc 内一条 Python 语句；6 个既有负控均未覆盖 “shell heredoc 正文缩进”。
- **门未覆盖的路径**：shell comparator 不区分 heredoc 边界/quoted heredoc 正文，也没有对应变异负控。

# LOW

### LOW-1 v2.4.1 的主 PASS、自测与 6 负控没有形成同一脚本版本的证据闭环

- **位置 / SHA**：`cross-lane-semantic2-v241-20260920T234445.txt:1` 绑 `head=0d712dd4`，不是最终 `3139cef7`；`cross-lane-semantic2-v24-negcontrols-20260920T215132.txt:1-2` 自称 v2.4 且主脚本 sha256=`81a34da2...`，负控输出绑 `9b96e5a6`；最终脚本实际 sha256=`e8a715009f2682549197de2a16c6dafb352a160df1767ed57f5c6f4b19cc7a6b`，且 `cross-lane-semantic2.py:2` 与 `b15-freeze-exclusions.json:15` 仍标 v2.4；`D-15-r13-整改说明.md:5` 却宣称 v2.4.1 final rerun `rc=0`。
- **一句复现思路**：比较 `0d712dd4..3139cef7` 可见脚本只新增 J07 exception 一行，且 9 个最终 commit 文件全在 `_bmad-output/**`；但树内没有任何 v2.4.1 `--self-test` / 6 负控重跑档或当前脚本 hash 绑定档。
- **未被拦下的输入**：把 exception 字典改动命名为 v2.4.1 后，不重跑自测/负控、不更新版本标识，仍可复用 v2.4 控制证据。
- **对照输入**：`0d..3139` 非 `_bmad-output` diff=0，且新增 exception 不影响空 blob self-test 与 pin 类负控的核心逻辑，所以当前实质风险较低。
- **负控输入**：在同一“v2.4.1”标签下修改 guard 代码而不重跑 6 负控；现有证据无法用脚本 hash 自动判失配。
- **门未覆盖的路径**：semantic 证据没有强制记录“主输出 + self-test + 负控”的同一脚本 hash / version tuple。

### LOW-2 状态账 B15 行仍保留已被总账勘误推翻的 contract “逐字同”表述

- **位置 / SHA**：`_bmad-output/审查/2026-08-30-主goal全量状态账.md:171` 写“contract 3 文件与基线逐字同”；正确口径在 `_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:1096` 已改为“红 nodeid 集合/计数等价；warnings 577→579”。
- **一句复现思路**：对比 `contract-3files-20260920T151657.txt:3,2031-2033`（batch15-integ rootdir、577 warnings）与 `contract-3files-FINALPOSTP9-20260920T192431.txt:4,2038-2040`（feature rootdir、579 warnings），完整输出不是逐字相同。
- **未被拦下的输入**：warning 数、rootdir 或非红输出变化后，状态账旧句仍可让读者误判完整 contract 日志全等。
- **对照输入**：两档的 FAILED nodeid 均为同两条，计数均为 `2 failed, 75 passed`，该部分声称成立。
- **负控输入**：只修改 warning 数或路径，不新增红 nodeid；现有 semantic/G8-10/OpenAPI/unit 门均不会检查状态账措辞。
- **门未覆盖的路径**：状态账与总账/STATUS 的 contract 口径无机器交叉校验。

清零：否；B/H/M/L = 0/0/3/2
