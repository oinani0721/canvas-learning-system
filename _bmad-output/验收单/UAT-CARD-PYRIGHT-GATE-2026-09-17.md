# UAT — CARD-PYRIGHT-GATE（第十四批 / 车道 T8-G，全批最后一道门）

> 批次：`[BATCH-2026-09-11-第十四批 / CARD-PYRIGHT-GATE]`　车道：`card-t8-tools`（分支 `card/t8-tools`）
> 本卡 HEAD 起点 = T8-F 末 commit `e45c55c74b1f56db9810a3c75befd29278b6f45d`；`B14_BASE` = `081004834e37b1b0253cf81dc7b44e784646c934`
> **零代码卡**：车道树改动面只有 `_bmad-output/**`；协议 §2.3 的改动**只出 patch 交主 session**，未在任何工作树直改协议。
> 证据目录：`_bmad-output/审查/evidence-pyright-gate/`

---

## 一 本卡做了什么

第十四批的最后一道门。四件事，全部零代码：

1. **GATE**：确认本车道树 `pyright app` = **0 errors**（协议 §1 候选树合入门的原文口径）。
2. **关闭协议 §2.3 的 ruff-format 462 文件漂移过渡条款**——产出 patch 文件交主 session 集成期套用，不在任何树直改。
3. **lefthook `python-typecheck` 块只核不改**。
4. **PYRIGHT-TAIL 清单指向前一卡 T8-F 的 census**（不重抄、不新造）。

---

## 二 与卡文不符的三处（如实记录，均按真实性质改判据，未放宽）

| # | 卡文写的 | 本树实测 | 处置 |
|---|---|---|---|
| 不符-1 | §〇 第 3 行：「本树 `backend/.venv/bin/pyright` **不存在**（`ls` No such file）」 | **存在**，且与 `"$P"` 是**同一 inode**（`33089839`）——本车道树 `backend/.venv` 是软链（`Sep 11 11:12`）指向 `card-v5-lance/backend/.venv` | 卡文该句描述的是**主干树**。判据不变（仍用绝对路径 `"$P"` + `test -x`），但如实声明：「禁相对路径」这条在**本树没有显形点**（相对路径在本树能正常解析到真 binary，不会假绿），属**纵深防御**而非本树可复现的缺陷 → 已进「本卡未证明什么」⑨ |
| 不符-2 | (b)：`pyright app` 必得「`0 errors, **81** warnings」 | `0 errors, **80** warnings, 0 informations` | **80 才是本树的正确预期**：81 是 `B14_BASE` 的值，T8-F（`d1c40998`）删掉 `backend/app/dependencies.py` 一条 `# pyright: ignore[reportArgumentType]` 后该 ignore 自曝的 `reportUnnecessaryTypeIgnoreComment` warning 消失 ⇒ 净 −1。**门只判 errors**（协议 §1 原文），已用三组集合对照把 −1 归因落成数据（见 §三 4-A 第 2 行） |
| 不符-3 | (d)③：`git diff 08100483 HEAD -- lefthook.yml` **为空** | **非空**：212 增 12 删，文件 521 → 721 行 | 与卡文 §〇 自己记的「T8-A 只改 `mutant-residue-scan` 块」**互相矛盾**。T8-A 是 `lefthook.yml` 唯一写者且改动量大 ⇒ 整文件 diff 不可能空。本卡按真实性质判：**块未位移 + 区间 sha256 相同 + T8-A 改动行无一落进区间**（见 §三 4-A 第 4 行）。判据的取名面因此恰好等于它的主张（「这个块没被改」），而不是「整个文件没被改」 |

---

## 三 DoD-3

### 4-A Claude 已代验（全引证据路径与其中的行，不在此处自述数字）

| # | 完成条件 | 证据路径与引用行 | 判据 / 负控 |
|---|---|---|---|
| 1 | **(b) GATE：`pyright app` = 0 errors** | `evidence-pyright-gate/gate-pyright-20260917T155555.txt` —— `# pyright version:` 行、`pyright ok` / `testx_rc=` 行、汇总行 `0 errors, 80 warnings, 0 informations`、其后 `rc=` 行 | 绝对路径 `"$P"` + `test -x` 自证 + cwd=`backend/`（R-B14-10）；⛔ 未用 `\| tail -1` |
| 1b | **(b) 负控输入：同一 `"$P"` 真能报红，且判据两向可翻转** | 同档 `--- 验伪锚 probe: 坏文件 ---` 段与 `--- 对照输入 probe: 零错文件 ---` 段各自的数字行与 `rc=` 行 | 取 error **数**（`grep -oE '^[0-9]+'`）而非匹配行数；同档末两段记录了**反面实测**：用 `grep -c` 时坏文件与零错文件**都给 1** = 恒真锚 |
| 2 | **(b) warnings 81→80 归因（非漂移）** | `evidence-pyright-gate/gate-warn-attribution-20260917T155740.txt` —— `对照 1` 段 `diff_rc=` 行、`去行号差集` 段的 `'<' 计数` / `'>' 计数` 两行、末段结论 5 行 | 三组集合对照：本次 vs T8-F 收工存档 `pyright-app-final-*` 空差集；vs `pyright-app-before-*` 去行号口径差集恰 1 条（`dependencies.py` 那条 ignore）。同档记录了一处**判据自伤的更正**（见 §五） |
| 3 | **(c) 协议 §2.3 patch：`git apply --check` rc=0，改动只在 §2.3** | `evidence-pyright-gate/protocol-2.3-close.patch`（全文）+ `protocol-23-close-judges-20260917T155925.txt` —— `① 改前红` / `⑥ 新句锚` / `⑥ D-40 句` / `⑦ 子串对照` 各段的计数行与 `rc=` 行；`⑤ 精确化` 段的 `实际删除行号(旧文件) =` 行与 `判据结论:` 行 | 新句独有锚 `不再允许带存档跳过` 原文 0 → scratch 1（**该 0 即验伪锚**，证明「新句在」判据改前确实红）；`python-typecheck 恢复硬禁` 句与 D-40 句用**逐字子串对照**（⛔ 禁整行 `grep -n` diff——三句同在一条物理行，整行必不同 = 恒假红），并配删子串副本的负控使其翻红；落点判据配对照输入（`@@` 挪到 80）翻成 False |
| 4 | **(d) lefthook `python-typecheck` 块只核不改** | `evidence-pyright-gate/lefthook-typecheck-block-20260917T160033.txt` —— `② 块边界现求` 四行、`① 区间 205..231` 段两个 `sha256` 行与 `cmp:` 行、`承重` 段 `落进 [205,231] 的旧侧/新侧改动行` 两行与 `判据结论:` 行、末行 `[status 结束，上方应无输出]` | 两条独立证据合取（内容 sha256 相同 ∧ 改动行不落进区间）；配两个负控：改 1 字符使 sha 翻转、取一个**已知被改**的区间 `[311,313]` 必命中（防行号反算脚本对所有区间恒返回空的假绿） |
| 5 | **(e) TAIL 清单指向 T8-F census** | `evidence-pyright-gate/census-and-territory-20260917T160054.txt` —— `(e)` 段 `文件在否` 行、`确是 TAIL census` 计数行、`验伪锚` 行 | 验伪锚取**独立于被测词**的已知不存在项（期望 0）。⚠️ 卡文原给的 `find -iname '*evidence-b14*'` 锚在本树命中 **0 行**（该目录只在主干树）= 空洞锚，已弃用 |
| 6 | **(f) tests/unit 对 64 条基线新增 = 0** | `evidence-pyright-gate/unit-20260917T160110.txt`（末行汇总）+ `unit-diff-20260917T160613.txt` —— `更正后的集合差集` 段的 `新增(>) 计数` / `消失(<) 计数` / `交集(==) 计数` 三行、`重跑验伪锚` 段三行、末行结论 | 跑法与基线头注**逐字同口径未改**（R-15 `--ignore` 相对路径，R-B14-3）；两侧均为 **nodeid 行集合**（非计数）。配两个负控：注入 1 条新红 → 新增 1；**等长替换**（条数不变、身份变）→ 新增 1 |
| 7 | **(g) 地盘只动 `_bmad-output`** | 同 `census-and-territory-*.txt` —— `(g)` 段 `git status --porcelain` 行、两条带 `':(exclude)_bmad-output'` 的判据后的 `[结束，上方应无输出]` 行、点名面（`lefthook.yml` / `backend` / `pyrightconfig.json` / `.claude`）那条 | ⛔ pathspec 用 `':(exclude)…'`（非 `':!…'`）；git 判据一律 `-c core.quotepath=false --no-pager --no-color`（R-B14-11a）。⚠️ 其中「不加 exclude 的 `git diff` 应 ≥1」这条锚在 commit 前**结构上恒空**（`git diff HEAD` 看不见未跟踪文件），已标注并在 commit 后补跑 —— 见 §六 |
| 8 | **(h) Codex 绑最终 HEAD，BLOCKER/HIGH = 0** | `_bmad-output/审查/codex-review-CARD-PYRIGHT-GATE.md` 首部六行 blockquote + 绑定核见 §六 | 本卡零代码 ⇒ 1 轮即末轮；绑定判据 `git -c core.quotepath=false --no-pager diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空 |

### 4-B 你来验（零技术词）

**1. 那条「历史遗留」的挡箭牌，从今天起不成立了**

我做的事：把一条一直开着的「临时豁免」正式关掉。这条豁免的意思是——「代码排版跟规范对不上？没关系，那是以前就有的老问题，先放你过去」。

我看到的：这条豁免从开出来那天起就写着「用到某一道关卡为止」，而今天这道关卡就是最后一道。我把它的状态改成了「已关闭」，并且把改动做成一张**待批的单子**交上去，没有自己直接动那份规矩文件。

我感觉：像是把一扇一直虚掩着的门推到了该关的位置。但有一点要说清楚（这是审查者帮我纠正的一处措辞）：**关掉的是「随口说一句『那是老问题』就能直接跳过」这条路，不是把那些老问题本身清掉了**。那一批老的排版不一致仍然在，要等后面专门安排的一次统一整理。所以往后再看到不一致，仍然要分辨它是老的还是新的——区别在于，现在**必须分辨、必须拿出证据**，不能一句话带过。那种「反正说不清、干脆放过」的黏糊感没有了，是一种踏实。

**2. 这道关卡本身，我先确认了它真的会拦人**

我做的事：在让这道关卡放行之前，我故意拿一份**明知有毛病**的东西喂给它。

我看到的：它当场拦下来了；我再喂一份明知没毛病的，它就放行了。两次结果不一样，说明它是真在看东西，不是闭着眼睛盖章。

我感觉：踏实。我最怕的不是关卡拦我，而是**关卡其实坏了、却一路给我开绿灯**——那样等问题真冒出来的时候，已经过去很久、谁也找不回是哪一步出的错。先确认它会拦人，再让它放行，心里才有底。

**3. 有三个地方，说明书写的和现场看到的不一样**

我做的事：照着说明书一条条核对时，发现有三处对不上。

我看到的：不是现场出了问题，是**说明书写的时候用的是另一个地方的情况**，后来现场变了，说明书没跟着改。

我感觉：一开始有点心里一紧——说明书对不上，通常意味着要么我搞错了，要么有人动了不该动的东西。查清楚之后松了口气：三处都能解释得通，而且都能拿出证据。我没有「因为说明书这么写就判它不合格」，也没有「为了让它通过就悄悄放宽标准」，而是**把说明书和现场的差别原样记下来，再按现场真实的情况去核**。这一条我希望你重点看看——因为它决定了这份结论是照抄来的，还是真核过的。

---

## 四 本卡未证明什么（≥4）

1. **「候选树上全部语义车道都保持 `pyright app` = 0」本卡未独立证明。** 本卡只在自己车道树（= `B14_BASE` 代码 + T8 车道的注释类改动）验了 0；别的语义车道的改动**不在本树**。全量跨车道 0 是主 session 集成候选树的**合入门**（协议 §1），不是本卡结论。
2. **lefthook 的反向依赖盲区未闭。** 门跑 `{staged_files}`（位置实参），改 `services/x.py` 签名而调用方 `api/y.py` 未 staged 时门会绿。本卡**只核不改**、**未**产出整目录步 patch。判定理由：GATE 跑的是**全量** `pyright app` 而非 staged 子集，全量跑本身绕过该盲区；且 `lefthook.yml` 是 T8-A 的地盘，本卡硬边界禁改。这是「没去做」，不是「做不到」。
3. **未证明 `protocol-2.3-close.patch` 套用后与主 session 集成期对协议的其它 hunk 无冲突。** `git apply --check` 只对**当前** feature 树 HEAD（`8856390d`）成立；若集成期协议又被别的卡改动，需重跑 check。
4. **协议关闭 ruff-format 过渡只对后续提交生效，历史不追溯。** 本卡未核查历史上带存档跳过格式漂移的 commit，也未产出任何追溯清单。
5. **D-40 的 462 文件整仓 format 本卡不做**（归第十五批末位主 session 单独一 commit）。本卡未验证「过渡关闭」与「462 文件漂移仍在」两者并存时，下一批改这些文件的卡会不会被门直接拦死——该风险已写进 Codex prompt 问题②请其独立判断。
6. **(c)⑦ 的逐字子串对照只证明 `python-typecheck 恢复硬禁` 与 D-40 两句未动**，**不**证明 §2.3 内其余文字未被 patch 意外改到。那一面由 ⑤ 的改动行号落点核（实际改动行 = `[67]`）+ `git apply --check` 覆盖，二者都不是逐字节全段对照。
7. ~~**未证明仓根 `pyrightconfig.json` 在 cwd=`backend/` 下被 pyright 实际读取。**~~ → **已于 Codex r1 后补证，不再是缺口**：同一 `"$P"`、同一 cwd 加 `--verbose` 跑，pyright **自报** `Loading configuration file at <本树仓根>/pyrightconfig.json`（路径含 `card-t8-tools` ⇒ 读的是本树那份），且加 `--verbose` 后汇总行仍为 `0 errors, 80 warnings`。验伪锚：换 cwd 到**树根**跑同一命令 → **rc=4**，配置行与汇总行都拿不到 ⇒ 该判据对 cwd 敏感、非恒真，同时实证了 R-B14-10「在树根跑拿不到同一汇总行」。证据 `evidence-pyright-gate/gate-configfile-proof-*.txt`。
   **仍未证明的剩余部分**：`pyrightconfig.json` 里 `include` 覆盖面**是否正确**（本卡只证明该配置被加载，未逐条核 include/exclude 语义）；(b) 的探针文件在 `/tmp`、不在 include 面内，其报红只证明同一 binary 在跑且能报 error。
8. **未证明 lefthook 1.13.6（npx 侧）下 glob / run 行为与 2.1.6 相同**——只在 `/opt/homebrew/bin/lefthook` 2.1.6 上论证。
9. **「禁相对路径 pyright」这条禁令在本树没有显形点。** 本树 `backend/.venv` 是软链、相对路径能解析到与 `"$P"` **同 inode** 的真 binary ⇒ 本树跑相对路径**不会**假绿。该假绿只在主干树发生，本卡**未**在主干树复现它。绝对路径要求在本树属**纵深防御**（防写法漂移到别的树），不得读作「本树已验证防住了假绿」。
10. **tests/unit 的 64 条既有红本卡未逐条复核其根因**——只做 nodeid 集合差集证明「本卡未新增」，未判断这 64 条本身是否应该红。

---

## 五 本卡自己的判据自伤（已更正，如实登记）

| # | 自伤 | 表现 | 更正 |
|---|---|---|---|
| 自伤-1 | 归因段的负控用了 `head -n -1`（去掉最后一行） | macOS BSD `head` **不支持负数**，实测报 `illegal line count -- -1`；但重定向已先把文件建成**空文件** ⇒ `diff 空文件 全集` 给出 80 个 `>`，判据「期望 ≥1」**照样通过** = 假绿（它测的是「空集 vs 全集」，不是「少 1 条会不会被发现」） | 改 `sed '$d'`（BSD/GNU 通用）；更正后负控给 1、控制组给 0。两版都留在 `gate-warn-attribution-*.txt` 内可核 |
| 自伤-2 | tests/unit 提取 nodeid 的口径 `sed -E 's/^(FAILED\|ERROR) //'` | 只剥前缀、**不剥 ` - <msg>` 尾巴**，且本次输出含 ANSI 转义（基线含 ESC 行数 0 / 本次 11）⇒ 同一条 `test_live_vault_enforce_clean` 被当成「1 新增 + 1 消失」 | **跑法不改**（与基线逐字同口径），只更正提取口径：先去 ANSI、再截断 ` - ` 之后。更正后新增 0 / 消失 0 / 交集 64。两版都留在 `unit-diff-*.txt` 内可核 |
| 自伤-3 | (g) 地盘验伪锚「不加 exclude 的 `git diff` 改动文件数应 ≥1」 | commit **之前**结构上恒空（`git diff HEAD` 看不见未跟踪文件），带不带 `:(exclude)` 都是空 ⇒ 证明不了 exclude 生效 | 标注为空洞锚；commit 前改靠 `git ls-files --others --exclude-standard`（6 vs 0）这条有效锚，commit 后已补跑 → `evidence-pyright-gate/territory-postcommit-*.txt`（10 vs 0） |
| 自伤-4 | Codex prompt 合规自检的验伪锚「本 prompt 里确有 `gpt-` 前缀的模型名（期望 ≥1）」 | 实测 **0** —— 因为本 prompt **正确地没有写任何模型名字面量**，这个「已知正例」是我凭空假设的、并不存在 ⇒ 空洞锚：`grep -cF 旧模型名` 给 0 时，分不清是「确实没写」还是「grep 在本文件上根本命中不了东西」 | 验伪锚的正例须同时满足**独立于被测词** ∧ **已知为真**；我只满足了前者。改用确实存在于该文件的串（`CARD-PYRIGHT-GATE` / `BLOCKER` / `最小读取面`，各 ≥1）+ 反例（`ZZZ-NOT-IN-THIS-FILE` = 0）。证据 `evidence-pyright-gate/prompt-compliance-*.txt` |

---

## 六 Codex 与绑定核

### 6.1 轮次与结论

- **round-1（= 末轮，本卡零代码 ⇒ 1 轮即末轮）**：**BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 1**
- 存档：`_bmad-output/审查/codex-review-CARD-PYRIGHT-GATE.md`（4285 字节，非 0）
- prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-GATE.md`
- 合规自检：`evidence-pyright-gate/prompt-compliance-*.txt` —— 协议 §2 点名四措辞各 0；旧模型名字面量 0（用变量核）；**该自检的验伪锚初版空洞，已更正**（见 §五 自伤-4）
- `*.stderr*` **未入库**（`.gitignore` 覆盖），会话头三行已抄进存档首部并**括注行号**

### 6.2 D-15 绑定核（末轮必绑最终 HEAD）

审查绑定 SHA = **`96dc3c496dddfcc603e692e27492a3248f8ab655`**，与本卡最终 HEAD **相同**；Codex 在存档正文里**独立核实**了该 SHA。

```zsh
git -c core.quotepath=false --no-pager diff --stat --no-color \
  96dc3c496dddfcc603e692e27492a3248f8ab655 HEAD -- . ':(exclude)_bmad-output'
# => 空（审后新增的 commit 只含 _bmad-output，代码面零改动）
```

⇒ **D-15 闭合**：末轮绑最终 HEAD ∧ BLOCKER = 0 ∧ HIGH = 0 ∧ 轮次 1 ≤ 5。

### 6.3 四条意见逐条处置

| 级别 | Codex 意见 | 处置 | 依据 |
|---|---|---|---|
| **MEDIUM-1** | 绝对路径 + `test -x` + 正负探针**不能证明根配置实际加载及有效检查范围**，第三种假绿未排除（属证据缺口，不能反推配置未读取） | ✅ **已补证，缺口消除** | 同一 `"$P"`、同一 cwd 加 `--verbose`，pyright **自报** `Loading configuration file at <本树仓根>/pyrightconfig.json`（路径含 `card-t8-tools`）；加 `--verbose` 后汇总行仍 `0 errors, 80 warnings`。验伪锚：换 cwd 到树根跑 → **rc=4**，配置行与汇总行都拿不到 ⇒ 判据对 cwd 敏感、非恒真。证据 `evidence-pyright-gate/gate-configfile-proof-*.txt`。**剩余未证**：`include` 覆盖面本身是否正确（只证明配置被加载，未核 include/exclude 语义）→ 已写回 §四 第 7 条 |
| **MEDIUM-2** | 新句「恢复硬禁」与旧句仅点名「改动行」的**范围不一致**，留下「被检查文件的未改动处仍有既有漂移」的处置歧义 | ⚠️ **登记不改，移交主 session 裁定** | 卡文 (c)② **逐字规定了**替换句，并明确「末尾『不再允许带存档跳过』= 唯一新锚 `$NEW`，**逐字保留不得改写**，改一个字判据就失锚」。改写它会同时越出卡文授权、打破 ⑥ 的锚。该范围歧义与 D-40（462 文件整仓 format 归第十五批）的交互，应由主 session 在**集成期套用 patch 时**一并裁定 → 已进 §七 台账第 9 条 |
| **MEDIUM-3** | §八 备查段的探针命令**未保存 pyright 退出码**、未设 `pipefail`，默认 zsh 下末尾 `grep` 成功会让管道返回 0 ⇒ 照抄复现不出标注的 `rc=1`（属复验命令不完整，非历史日志造假） | ✅ **已修** | §八 两条探针命令补 `; echo rc=$pipestatus[1]` 并加注说明；另补入配置加载自证命令与其验伪锚。**承重存档本身的取法一直是对的**（`gate-pyright-*.txt` 内每段末行即 `rc=$pipestatus[1]`），错的只是备查段的转写 |
| **LOW-1** | 4-B 第 1 段「往后任何一处对不上，都是这次改动带来的」**错误地把取消豁免写成消除了既有漂移** | ✅ **已修** | 该句确为事实错误：462 文件既有漂移仍在（D-40 归第十五批），后续碰到它们报红不能归因为新引入。已改写为「关掉的是『随口说一句那是老问题就能跳过』这条路，**不是**把老问题本身清掉」。⚠️ 说明：协议对 LOW 是**登记不阻断**，此处选择修，是因为 (i) 4-B 是给用户读的、错误表述会直接误导，(ii) 改动落在 `_bmad-output` 内，而绑定判据带 `':(exclude)_bmad-output'` ⇒ **不破坏 6.2 的绑定**，且按 D-32 纯文档尾巴不占轮次 |

### 6.4 Codex 明确背书的项（原文摘要）

- **① patch 没有越界**：Codex 独立逐字节比较确认「只有一处删除、一处新增，实际修改行均为协议第 67 行；ruff 句之外的 U1/U2 记录、typecheck 句、D-40 和尾句全部相同，上下文也匹配活文件」。同时指出作者的子串+落点判据**理论上**可能漏掉同行其它文字的修改，但**当前具体 patch 没有这种修改** —— 该理论缺口已在 §四 第 6 条如实登记。
- **③ 没有冒领跨车道通过**：确认验收单与 prompt 均把全量门留给主 session。
- **④ TAIL 处置成立**：确认「没去做，不是做不到」的表述，且本卡「只核不改」的边界不要求另产整目录 patch。
- **⑤ 三处纠偏没有放宽本卡承诺**：绝对路径要求保留、warnings 不属协议 errors 门限、lefthook 指定块已逐字节核实相同。

---

## 七 台账待登记条目（≥4，台账只主 session 改）

1. **协议 §2.3 ruff-format 462 漂移过渡条款关闭**：patch = `_bmad-output/审查/evidence-pyright-gate/protocol-2.3-close.patch`；`git apply --check` 对 feature 树活文件 rc=0；改动行 = 协议 `:67` 单行，§2.3 区间 `62..70` 内。**待主 session 集成期套用到 feature 树协议**（本卡未在任何树直改）。替换前后逐字原文见 patch 的 `-`/`+` 两行。
2. **PYRIGHT-TAIL 全清单指向 T8-F census** `_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md`（含 §四「第十五批立卡（行为变化项，D-35：本卡只登记不改）」整节，各自第十五批立卡）。⚠️ 卡文 (e) 表述为「D-35 三条」，实测该文件中**显式带 `D-35` 字样的表行为 2 条**（`T-new-2` / `T14`），§四整节立卡项多于此数 —— **以 census 原文为准，本卡不重抄、不新造数字**。
3. **D-40**：462 文件整仓 format 归第十五批末位主 session 单独一 commit。本卡关闭的是**过渡条款**，不是做 format。
4. **Codex 存档路径 + 绑定 SHA**：`_bmad-output/审查/codex-review-CARD-PYRIGHT-GATE.md`（round-1 = 末轮，**BLOCKER 0 / HIGH 0** / MEDIUM 3 / LOW 1），绑定 `96dc3c496dddfcc603e692e27492a3248f8ab655` = 本卡最终 HEAD，代码面 diff 空 ⇒ **D-15 闭合**。首部六行齐（模型 / reasoning_effort / codex 版本三字段实测命中，会话头三行括注行号 L2/L5/L9）。详见 §六。
5. **本卡 GATE 只在车道树验 0**；**全量跨车道 `pyright app` = 0 由主 session 集成候选树合入门复核**（协议 §1）。
6. **lefthook 反向依赖盲区（门只查 `{staged_files}`）本批未闭**，本卡只核不改、未出整目录步 patch（理由见 §四 第 2 条）。若主 session 判定需闭，插入点必须在 `PYRIGHT_EXIT=$?`（`:225`）**之后**，不是 `{staged_files}` 行（`:224`）之后 —— 插在 `:224`/`:225` 之间会在 `$PYRIGHT_EXIT` 未赋值时做比较并吞掉 staged 步的 rc = 假绿。
7. **卡文 T8-G.md 三处与实测不符**（见 §二）：(b) 期望 warnings 81 → 实测 80；(d)③ 期望 `lefthook.yml` 整文件 diff 空 → 实测 212 增 12 删；§〇 称本树无 `backend/.venv/bin/pyright` → 实测存在且与 `"$P"` 同 inode。建议主 session 回填卡文或在复核报告登记。
8. **卡文 (e) 给的 `find -iname '*evidence-b14*'` 验伪锚在车道树命中 0 行**（该目录只在主干树）= 空洞锚，本卡已换用独立于被测词的已知不存在项。建议后续卡文勿再沿用。
9. **⚠️ 移交主 session 裁定 —— Codex r1 MEDIUM-2（措辞范围歧义）**：新句「`ruff format --check` 自此**恢复硬禁**」与旧句仅点名「**改动行**的格式漂移」范围不一致，留下「被检查文件的**未改动处**仍有既有漂移」该如何处置的歧义；与 D-40（462 文件整仓 format 归第十五批末位）并存时，下一批改这批文件的卡是否会被门直接拦死，本卡**未验证**。本卡**登记不改**，因为卡文 (c)② 逐字规定了替换句且明确「末尾『不再允许带存档跳过』逐字保留不得改写，改一个字判据就失锚」—— 改写它会同时越出卡文授权并打破 ⑥ 的锚。**请主 session 在集成期套用 patch 时一并裁定**（可选：套用时顺手把范围限定语写明，或在第十五批 D-40 卡里同步收口）。
10. **Codex 存档正文含 1 处协议 §2 点名措辞**（`codex-review-CARD-PYRIGHT-GATE.md` 正文 ④ 段：「全量扫描**绕过**本次 staged 子集盲区」）。分诊：**我方可控面干净** —— prompt 四措辞 0、存档首部 0（证据 `evidence-pyright-gate/prompt-compliance-*.txt` 与 `archive-compliance-*.txt`）；该命中是 **Codex 自己描述事实的用语**，按协议 §2.1「首部之后接 Codex 正文、正文一字不改」**不得篡改**。登记供主 session 裁定该禁令对「审查者输出」是否适用。
11. **本卡四处判据自伤已更正并留档**（见 §五）：`head -n -1` 在 BSD 下不支持却因重定向先建空文件而假绿；nodeid 提取口径未剥 ANSI 与消息尾巴；地盘验伪锚 commit 前结构上恒空洞；prompt 合规自检的验伪锚正例凭空假设（不满足「已知为真」）。四条均属**判据侧**问题，无一改变被测对象的结论。

---

## 八 命令与口径备查

```zsh
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools
P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright
PROTO=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt

# (b) GATE —— 绝对路径 + test -x + cwd=backend（R-B14-10），⛔ 禁 | tail -1
( test -x "$P" && echo "pyright ok" || { echo "pyright 缺席"; exit 1; } ); echo rc=$?   # R-B14-11b 子 shell
( cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' ; echo rc=$pipestatus[1] )
# 负控 / 对照输入（⛔ 取数字 grep -oE '^[0-9]+'，不是 grep -c）
# ⛔ rc 必须取 $pipestatus[1]（zsh，= pyright 自身退出码）：末尾 grep 成功会让整条管道返回 0，
#    直接看 $? 复现不出标注的 rc（Codex r1 MEDIUM-3 指出本节初版漏了这一句，已补）
( cd backend && "$P" /tmp/pyright-probe/x.py  2>&1 | grep -E '^[0-9]+ errors?, ' | grep -oE '^[0-9]+' ; echo rc=$pipestatus[1] )   # 数字 1，rc=1 为预期
( cd backend && "$P" /tmp/pyright-probe/ok.py 2>&1 | grep -E '^[0-9]+ errors?, ' | grep -oE '^[0-9]+' ; echo rc=$pipestatus[1] )   # 数字 0，rc=0

# 配置加载自证（补证 Codex r1 MEDIUM-1：证明仓根 pyrightconfig.json 真被读取）
( cd backend && "$P" --verbose app 2>&1 | grep -iE 'configuration file|pyrightconfig' ; echo rc=$pipestatus[1] )
#   => Loading configuration file at <本树仓根>/pyrightconfig.json
# 验伪锚：换 cwd 到树根跑同一命令 -> rc=4、配置行与汇总行都拿不到（实证 R-B14-10 的 cwd 要求）
( "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' ; echo rc=$pipestatus[1] )

# (c) 协议 patch —— 只 check 不 apply
git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev \
  apply --check "$(pwd)/_bmad-output/审查/evidence-pyright-gate/protocol-2.3-close.patch"; echo rc=$?
# ⑦ 逐字子串对照（⛔ 禁整行 grep -n diff：三句同一物理行 = 恒假红）
TC='自第十四批起 `python-typecheck` **恢复硬禁**（见 §1 合入门）'
diff <(grep -oF "$TC" "$PROTO") <(grep -oF "$TC" /tmp/proto-gate/card-batch-protocol.md); echo rc=$?

# (d) lefthook 块 —— 区间对照（⛔ 不是整文件 diff，T8-A 是该文件唯一写者）
git show 081004834e37b1b0253cf81dc7b44e784646c934:lefthook.yml > /tmp/lefthook-base.yml
shasum -a 256 <(sed -n '205,231p' lefthook.yml) <(sed -n '205,231p' /tmp/lefthook-base.yml)

# (f) tests/unit —— 跑法与基线头注逐字同口径；提取口径去 ANSI + 截断 ' - ' 尾巴
( cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit \
    --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider )
grep -E '^(FAILED|ERROR) ' "$UT" | sed $'s/\033\\[[0-9;]*m//g' | sed -E 's/^(FAILED|ERROR) //; s/ - .*$//' | sort -u

# (g) 地盘（⛔ ':(exclude)…' 不用 ':!…'；R-B14-11a 三个 flag 是 git 的）
git -c core.quotepath=false --no-pager diff --stat --no-color HEAD -- . ':(exclude)_bmad-output'
git ls-files --others --exclude-standard -- . ':(exclude)_bmad-output'
```

**探针留存**：`/tmp/pyright-probe/`（`x.py` / `ok.py`）与 `/tmp/proto-gate/`（`card-batch-protocol.md` 改后副本 / `neg.md` / `neg-range.patch`）**留着不删** —— 均不在任何工作树、不 stage、不入库。用户级 guard-hook 拦一切删除形态，要清理请用户确认后由用户删。
