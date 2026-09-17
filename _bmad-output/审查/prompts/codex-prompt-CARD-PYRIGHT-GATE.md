# 独立审查请求 — CARD-PYRIGHT-GATE（第十四批 / 车道 T8-G，全批最后一道门）

## 一 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`（分支 `card/t8-tools`）。

本卡是第十四批**全批最后一道 GATE**，**零代码**（不改任何 `.py` / `lefthook.yml` / `pyrightconfig.json` / 协议本体），只做四件事：

1. **GATE**：确认本车道树 `pyright app` = **0 errors**（协议 §1 候选树合入门的原文口径）；
2. **协议 §2.3 关闭 ruff-format 过渡条款**：把「462 文件漂移条款保留到 T8-G GATE 合入」翻成「已于 GATE 合入时关闭、`ruff format --check` 恢复硬禁」——**只产出 patch 文件交主 session**，不在任何工作树直改协议；
3. **lefthook `python-typecheck` 块只核不改**；
4. **PYRIGHT-TAIL 清单指向前一卡 T8-F 的 census**（不重抄、不新造）。

审查绑定 SHA：`__BIND_SHA__`（本卡 commit，只含 `_bmad-output/**`；前一卡 T8-F 末 commit = `e45c55c74b1f56db9810a3c75befd29278b6f45d`，`B14_BASE` = `081004834e37b1b0253cf81dc7b44e784646c934`）。

**最小读取面（只读这些，不要扩散到全仓）**：

- `_bmad-output/审查/evidence-pyright-gate/protocol-2.3-close.patch`（**全文**）
- `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md` 的 **§2.3 段（`:62-70`）** 与 **§1 候选树合入门那一条**
- `lefthook.yml` 的 `:205-231`（`python-typecheck` 块）
- `_bmad-output/审查/evidence-pyright-gate/gate-pyright-*.txt`
- `_bmad-output/审查/evidence-pyright-gate/gate-warn-attribution-*.txt`
- `_bmad-output/审查/evidence-pyright-gate/lefthook-typecheck-block-*.txt`
- `_bmad-output/审查/evidence-pyright-gate/protocol-23-close-judges-*.txt`
- `_bmad-output/审查/evidence-pyright-gate/unit-diff-*.txt`（`unit-*.txt` 只看末段汇总行即可，它 5000+ 行）
- `_bmad-output/验收单/UAT-CARD-PYRIGHT-GATE-2026-09-17.md`

## 二 作者自述，请独立核对

① **GATE 不是「缺 pyright 的假绿」**。本批已知一个现成陷阱：主干树 `backend/.venv` 软链指向的 venv **没有** pyright，跑相对路径 `.venv/bin/pyright app` 会 `no such file` 而 shell 仍 rc=0，看起来像通过。本卡的防法是三件事同时成立：绝对路径 `"$P"`（`card-v5-lance/backend/.venv/bin/pyright`，实测 1.1.411）+ 跑前 `test -x "$P"` 自证 + cwd = `backend/`（`pyrightconfig.json` 在仓根）。实测汇总行 `0 errors, 80 warnings, 0 informations`、rc=0。

② **GATE 的负控输入真的能报红**。同一 `"$P"`、同一 cwd 下跑 `/tmp/pyright-probe/x.py`（`x: int = "s"`）取到 error 数 **1**、rc=1；跑对照输入 `/tmp/pyright-probe/ok.py`（`x: int = 1`）取到 error 数 **0**、rc=0 ⇒ 判据两个方向都会翻转。存档里同时记了一条反面实测：若用 `grep -c` 数**匹配行数**，坏文件和零错文件**都给 1**（汇总行不论 0 错还是 N 错都恰 1 行）= 恒真锚，故本卡用 `grep -oE '^[0-9]+'` 取**数字**。

③ **warnings 从 81 变 80 已归因到数据、不是漂移**。卡文写的期望值是 81（`B14_BASE` 的值），实测 80。归因：前一卡 T8-F（`d1c40998`）删掉了 `backend/app/dependencies.py` 的一条 `# pyright: ignore[reportArgumentType]`，该 ignore 原本自曝为 `reportUnnecessaryTypeIgnoreComment` warning。证据是三组集合对照：本次明细 vs T8-F 收工存档 `pyright-app-final-*.txt` **空差集**；vs T8-F 改前存档 `pyright-app-before-*.txt` 在**去行号口径**下差集恰 1 条（就是那条 ignore），`>` 侧 0 条。GATE 判据本身只判 **errors = 0**（协议 §1 原文），warnings 数不是门。

④ **协议 patch 只改 §2.3 的 ruff-format 一句，另两句逐字未动**。`git apply --check` 对 feature 树活文件 rc=0（只 check 不 apply）。改前/改后锚：`保留到第十四批 T8-G GATE 合入` 原文 1 → scratch 0；新句独有锚 `不再允许带存档跳过` 原文 **0**（这条是验伪锚，证明「新句在」判据改前确实红）→ scratch 1。`python-typecheck 恢复硬禁` 句与 D-40 句各用**逐字子串对照**（`diff <(grep -oF …) <(grep -oF …)`）验为空差集——这里**不能**用整行 `grep -n` 做 diff，因为这三句同在**一条物理行**上（该行 456 字符 / 763 字节），改了同行任一片段整行必不同 = 恒假红。该子串对照配了负控：删掉子串的副本上 `grep -cF` 归 0、`diff` 非空。

⑤ **patch 的改动行严格落在 §2.3 内部**。从 patch 反算实际改动行号 = `[67]`，§2.3 区间 = `62..70`，`62 < 67 < 70` 成立。hunk 范围 `@@ -64,7 +64,7 @@` 覆盖 64..70 含边界行 70（§3 标题）**作为只读上下文**，那是 `diff -u` 默认 3 行上下文，不是改动。该落点判据配了对照输入（把 `@@` 挪到 80）→ 判定翻成 False。

⑥ **lefthook `python-typecheck` 块未被动过**。⚠️ 卡文 (d)③ 原写「`git diff 08100483 HEAD -- lefthook.yml` 为空」——**实测非空**（212 增 12 删，文件 521→721 行），因为同车道前序卡 T8-A 是该文件的唯一写者且改动量大；卡文这条期望与它自己 §〇 记的「T8-A 只改 `mutant-residue-scan` 块」互相矛盾。本卡按**真实性质**判：(i) 块未位移（`python-typecheck:` 两版都在 `:205`、glob 都在 `:206`）；(ii) 区间 `205..231` 两版 **sha256 完全相同**；(iii) T8-A 的 212 行改动**无一落进 `[205,231]`**（最早改动行在 `:311`）。(ii) 配了改 1 字符的对照输入使 sha 翻转，(iii) 配了「取一个已知被改的区间 `[311,313]` 必命中」的锚，防止行号反算脚本对所有区间恒返回空。

⑦ **tests/unit 对 64 条基线无新增**。首轮差集曾出现 1 新增 + 1 消失，经查是**同一条测试的排版差异**：基线在无色环境取（含 ANSI 行数 0），本次输出带色（11 行含 ANSI），且 pytest 的 `FAILED` 汇总行格式是 `FAILED <nodeid> - <msg>`，原提取口径只剥前缀不剥 ` - ` 尾巴。**跑法与基线逐字同口径未改**，只更正了提取 nodeid 的口径（先去 ANSI、再截断 ` - ` 之后）；更正后新增 0 / 消失 0 / 交集 64。该差集判据配了两个负控：注入 1 条新红 → 新增 1；**等长替换**（条数仍 64、身份变）→ 新增 1（证明集合判据挡得住计数判据挡不住的情况）。

⑧ **地盘只动 `_bmad-output`**。⚠️ 其中一条验伪锚（「不加 exclude 的 `git diff` 改动文件数应 ≥1」）在 commit **之前**是结构上恒空的——`git diff HEAD` 看不见未跟踪文件，带不带 `:(exclude)` 都是空，证明不了 exclude 生效。该条已标注为空洞并在 commit 后补跑；commit 前靠 `git ls-files --others --exclude-standard`（6 vs 0）这条有效锚支撑。

## 三 请按重要性排序回答的问题

⓪ **GATE 的「0 errors」有没有可能仍是假绿？** 请独立判断：`test -x` + 绝对路径 + 负控探针这三件事合起来，是否足以排除「pyright 没真跑」「跑的不是本树代码」「跑的不是 `pyrightconfig.json` 那套配置」三种情形。特别是第三种——本卡**未**验证仓根 `pyrightconfig.json` 在 cwd=`backend/` 下被实际读取，只是复现了波 0 证据的同一跑法得到同一汇总行。这个缺口有多大？

① **协议 patch 有没有越出 §2.3 改到别的条款？** 请逐字比对 patch 的 `-`/`+` 两行，确认除 ruff-format 那一句外，同一物理行内的其余文字（`python-typecheck 恢复硬禁` 句、D-40 句、前半段 U1/U2 合入记录）**逐字未变**。作者用的是子串对照而非全段逐字节对照，这中间有没有**门未覆盖的路径**（例如 §2.3 内 patch 没触及的其它行被意外改动）？

② **关闭 ruff-format 过渡的措辞是否恰当？** 新句写的是「改动行的格式漂移不再允许带存档跳过」。请判断：这句话是否可能被读成「历史上带存档跳过的 commit 也要追溯」（作者的本意是只对**后续**提交生效），以及 D-40（462 文件整仓 format 归第十五批）与它是否存在字面冲突——如果 462 个文件的漂移还在，而 `ruff format --check` 已恢复硬禁，下一批改这些文件的卡会不会被门直接拦死？这是本卡最可能的**未被拦下的输入**。

③ **「全量跨车道 `pyright app` = 0」有没有被写成本卡已证明？** 本卡只在自己车道树（= `B14_BASE` 代码 + T8 车道的注释类改动）验了 0，**别的语义车道的改动不在本树**。请检查验收单与本 prompt 里有没有任何一处把它说成本卡已证明的事实（它应当是主 session 集成候选树的合入门）。

④ **TAIL 清单有没有把「没去做」写成「做不到」？** 本卡对 lefthook 的反向依赖盲区（门只查 `{staged_files}`，改 `services/x.py` 而调用方 `api/y.py` 未 staged 时门绿）选择了**只核不改、如实登记未闭**，理由是 GATE 跑的是全量而非 staged 子集、且 `lefthook.yml` 是 T8-A 的地盘。请判断这个理由是否成立，还是本卡其实应当产出那份整目录步 patch。

⑤ **卡文与实测不符的三处，作者的处置是否正确？** 分别是：(a) 卡文说本树 `backend/.venv/bin/pyright` 不存在——实测存在且与 `"$P"` 同 inode（车道树 venv 是软链），作者据此声明「禁相对路径」这条在本树**没有显形点**、属纵深防御；(b) 卡文期望 warnings = 81——实测 80；(c) 卡文期望 `lefthook.yml` 整文件 diff 为空——实测非空。作者对三处都选择了「如实记录 + 按真实性质改判据」而非「照卡文判失败」或「悄悄放宽」。请指出其中有没有哪一处的处置实际上放宽了本该守住的性质。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：

- 级别
- `file:line`
- 一句话说明问题
- 一句话说明如何独立确认（读哪一段、比对什么）

没有问题的级别请明写「无」。请在开头给出四级各自的计数。

## 五 边界

- **只读**。不要修改任何文件；不要连数据库（7691 / 7687）；不要运行 pyright / pytest / ruff / lefthook；**不要套用任何 patch**；不要改协议。
- D-40 的 462 文件整仓 format **不在本卡范围**（归第十五批末位主 session 单独一 commit），不要评价它该怎么做，只评价本卡关闭过渡条款这个动作本身。
- 不要评价 census 里被判「第十五批立卡」的行为变化项**本身该怎么修**——那是前一卡 T8-F 的面。
- 不要扩散到最小读取面之外的文件。
