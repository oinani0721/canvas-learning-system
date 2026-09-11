# UAT — CARD-RED-R（tests/unit「真实现回归」26+1 条零代码定性）

> 批次 `[BATCH-2026-09-07-第十三批 / CARD-RED-R]` · 车道 `card-u5-lance`（分支 `card/u5-lance`）
> 树 HEAD（开工）`8f5f9efc` = U5-B 末 commit · **零代码卡**（只写 `_bmad-output/`）
> 分派表：`_bmad-output/审查/evidence-red-r/red-r-triage-20260909.md`

## 1. 🎯 一句话目标

把 202 条「测试一直是红的」里，那 26 条**被测功能其实还在、只是没人查过为什么红**的，加上 1 条被临时关掉所以没人看见的，逐条查清：到底是程序哪一次改动弄坏的、是真坏还是当初就说好要改、以及该由哪张卡来修。

## 2. 📖 你的视角

作为一个想知道「这堆红字里到底有没有真问题」的人，我希望有人把每一条红字追到**具体是哪天哪次改动**弄红的，并且明确告诉我「这条是真坏了要修」还是「这条是我们自己改了规矩、测试没跟上」，以便下一批修复卡能照着单子排，而不是继续凭猜测。

## 3. 🖥️ 交互流程

你打开分派表 → 看到一张 27 行的表 → 每行左边是一条红字的名字，右边一路读过去是：它测的功能现在在代码的哪一行、是哪一次改动把它弄红的（带日期）、这条算「真坏了」还是「说好要改」、凭什么这么判、以及该谁来修 → 表格下面是按「哪次改动」分组的解释，和当初三条猜测里哪条被证实、哪条被推翻。

## 4-A. 🤖 Claude 已代验

| 判据 | 结果 | 证据 |
|---|---|---|
| 第 0 分钟：pwd / 分支 / HEAD / 工作树干净 | ✅ `card-u5-lance` / `card/u5-lance` / `8f5f9efc` / `git status --porcelain` 0 行 | 本单 §7 |
| 外部输入自证：`test -f $BASE && test -f $ALIGN` | ✅ rc=0（两者均在 feature 主干树，本车道树无） | — |
| 基线口径 `grep -vc '^#' $BASE` | ✅ **202** | `evidence-b13/unit-red-baseline-da690bf8.txt` |
| 分母验伪锚：`align-r.nodeids` 抽取行数 | ✅ **26** 行（抽取式先自证，非 0） | `evidence-red-r/align-r.nodeids` |
| 分母 diff：`sort -u nodeids-26.txt` vs `align-r.nodeids` | ✅ 空（rc=0） | `evidence-red-r/nodeids-26.txt` |
| 开工目录级 `tests/unit` | ✅ `173 failed, 4759 passed, 48 skipped, 6 xfailed, 29 errors`（173+29=202），`rc=1` | `evidence-red-r/unit-open-20260909T113441.txt` |
| 开工带前缀集 vs 基线 `diff` | ✅ 空 | `evidence-red-r/open.nodeids` / `base.nodeids` |
| 开工 `comm -23 nodeids-26 open.bare.nodeids` | ✅ 空（26 条全在红集内；右侧用剥前缀的 bare 套） | `evidence-red-r/open.bare.nodeids` |
| 逐条 bisect 存档（每条独立 scratch worktree） | ✅ **27** 份 `<slug>-bisect.txt`（26 + 第 27 条） | `evidence-red-r/*-bisect.txt` |
| 被推翻轮次如实留档 | ✅ **8** 份（实测 `ls \| grep -cE 'candidate-refuted\|refuted-836d0986\|checkout-failed'`） | `evidence-red-r/*-r1-candidate-refuted.txt` 等 |
| first-bad 上的失败身份探针 | ✅ **28** 份（24 条批量 + epic30 单点 + p25/p26/p27 对 59586af1 的 collect-error 实证） | `evidence-red-r/probe-*.txt` |
| 26 条当前失败身份（两法交叉一致） | ✅ `--tb=line` 与 `--tb=short` 按分隔行归属结果一致，26 failed | `failure-identities-20260909T121755.txt` / `failure-identities-tbshort-*.txt` |
| 第 27 条捞回（scratch 删 :326-329，未动 :330 class 行） | ✅ 删后 `sed -n 326,328p` 直接见 `class TestFullCycleIntegration:`，`ast.parse` 通过；两条失败身份各一行 | `qa386-fullcycle-identity-20260909T115052.txt` |
| 车道树 `backend/tests` 零改动 | ✅ `git status --porcelain -- backend/tests` 全程 0 行 | — |
| 分派表闭合 ①：表体行数 | ✅ **27** | `red-r-triage-20260909.md` |
| 分派表闭合 ②：nodeid 双向 `comm` | ✅ 两向皆空（见 §7 命令） | 同上 |
| 收工目录级 `tests/unit` | ✅ `173 failed, 4759 passed, 48 skipped, 6 xfailed, 29 errors`（173+29=202），`rc=1` | `evidence-red-r/unit-after-20260909T124417.txt` |
| 收工带前缀集 vs 基线 `diff` | ✅ **空**（零代码卡预期；无 `>` 亦无 `<`） | `evidence-red-r/after.nodeids` |
| 收工 `comm -23 nodeids-26 after.bare.nodeids` | ✅ 空（26 条全部仍红，本卡不修） | `evidence-red-r/after.bare.nodeids` |
| 分派表定性分布（第 6 列精确计数） | ✅ 回归 19 / 契约演进 8 / 测试写错 0 = 27 | `red-r-triage-20260909.md` |
| 零代码门（**判据已修正**：原 `8f5f9efc HEAD` 两端同一 commit 恒真，属假绿，Codex round-2 MEDIUM 指出） | ✅ `git diff --stat 8f5f9efc -- . ':(exclude)_bmad-output'` 空 rc=0；`git status --porcelain=v1 -uall -- . ':(exclude)_bmad-output'` 空 rc=0；验伪锚（去 exclude）输出 `_bmad-output` | `evidence-red-r/zero-code-gate-r2-20260909T133119.txt`（原轮次留档 `zero-code-gate-20260909T125457.txt` 不删，记为判据不成立） |
| scratch 全清 `git worktree list --porcelain \| grep -c 'bisect-\|diag-\|probe-'` | ✅ **0** | `evidence-red-r/zero-code-gate-r2-20260909T133119.txt` |
| 车道树 `git bisect log`（不接管道取真实 rc） | ✅ `error: We are not bisecting.`，**rc=1** | `evidence-red-r/zero-code-gate-r2-20260909T133119.txt` |
| 禁连现网 | ✅ 全程 `NEO4J_URI=bolt://127.0.0.1:1` / `NEO4J_ENABLED=false`，`VAULTS_ROOT` 指临时目录；scratch 树不落 `.env` | `evidence-red-r/*-bisect.txt` 首部 |
| Codex round-1（gpt-6-astra ultra，绑 `8f5f9efc`） | BLOCKER **0** · HIGH **3** · MEDIUM **4** · LOW **3**；三条 HIGH 逐条实测复核后**全部成立**，已整改 | `_bmad-output/审查/codex-review-CARD-RED-R-r1.md` |
| Codex round-2（整改后复核，绑 `8f5f9efc`） | 见文末「Codex 轮次登记」 | `_bmad-output/审查/codex-review-CARD-RED-R-r2.md` |

**定性分布**：回归 **19** / 契约演进 **8** / 测试写错 **0**。

## 4-B. 👤 你来验

- [ ] 我打开那份 27 行的清单 → 我看到每一行都写着「哪一天的哪次改动把它弄红的」，而不是「疑似」「可能」 → 我感觉这份单子终于可信，不再是一堆猜测。
- [ ] 我随便挑一行看「凭什么这么判」那一栏 → 我看到的是能自己去核对的东西（哪个文件第几行、当时那次改动写了什么），而不是「内部审核认为」 → 我感觉这是能被追究的结论。
- [ ] 我看清单最后那几段分组说明 → 我能看懂「这一大批红字其实是同一件事造成的」，并且看到当初三条猜测里哪条被证实、哪条被推翻 → 我感觉排下一批修复卡时心里有数了。
- [ ] 我注意到有两条被单独标出来说「这个不只是测试红，是这个功能在真机上一直不能用」 → 我感觉这次翻查不是白做的，它顺手挖出了真问题。
- [ ] 我确认这次没有动任何程序本身 → 我看到的只是一份清单和证据 → 我感觉可以放心，它没有顺手改坏什么。

## 5. 🚦 验收结果

- 通过 → 说「复核第十三批 U5」，主 session 按分派表排第十四批修复卡。
- 不通过 → 在 §6 批注区写下哪一行不服，Claude 按该行重跑对应证据。

## 6. 📝 批注区

> [!question]+ 你的疑问
>

## 7. 🔗 技术 spec 引用

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U5-C.md`（feature 主干树）
- 分派表：`_bmad-output/审查/evidence-red-r/red-r-triage-20260909.md`
- 证据目录：`_bmad-output/审查/evidence-red-r/`
- 基线与分派来源（feature 主干树，untracked）：`evidence-b13/unit-red-baseline-da690bf8.txt` / `evidence-b13/red-align-da690bf8.md` §二

## 8. 本卡未证明什么

1. **「契约演进」≠「无需处置」**。本卡不修、不删任何测试。8 条判为契约演进的条目，其测试该删、该改还是该恢复生产行为，由接收卡定；本卡只给出「该次改动是有意的」这一事实与原文出处。
2. **27 条中只有 11 条是宽区间二分搜出来的**，另 16 条的 first-bad 是「good 端（候选的父 commit）实测通过 + bad 端实测失败 + 两者相邻」的**逻辑推论** —— `git bisect run` 在相邻区间上会**再跑一次 BAD revision** 确认（存档实测），但不搜索中间点。承重证据是两端各自的实测，不是 bisect 本身；分派表 §五之二 已把两类摊开。这 18 条的隐含前提是「候选区间选对了」，而本卡已实测到 3 组候选区间是错的（epic30、difficulty ×2 与 qa/story 族），故该前提在其余条目上**未被穷尽验证**。
3. **老 commit 上的环境等价性未逐 commit 证明**。全部 bisect 都用**当前** venv（`card-v5-lance/backend/.venv`，Python 3.14）跑历史代码，依赖版本与当年不同。缓解手段只有「单 nodeid + collect error 一律判 SKIP 而非 BAD」与端点双向验证，未对区间内每个 commit 证明环境等价。个别 SKIP 有可能本应是 BAD/GOOD。
4. **first-bad 不等于「当前失败成因」**，本卡对 **8** 条（epic30 ×1 + story_2_3 ×4 + qa_38_6 merged_view / story_38_6 / 第 27 条 ×3）实测到 first-bad 上的失败身份与 HEAD 不同，已逐条标注并补充当前成因的实测出处；但**未**对「当前身份」再做一次独立 bisect（那需要把判据从「是否失败」换成「失败身份是否为某串」），故当前成因的定位强度低于 first-bad。其中 `test_search_memories_node_id_filter_post_merge` 的当前成因经 Codex round-1 HIGH 指出后**已更正**（不是 node_id 形参缺失，而是 4236b12e 的相关度地板）。
5. **`test_full_cycle_fail_record_recover_merge`（同 class 另一条）只记失败身份，未定性**，它归 C1 的 33 skip，不在本卡分母。
6. **第 27 条解 skip 后的失败身份与 #134/#209 是否同根，只做了形态对照**（三条都指向 `get_learning_history` 合并视图，身份分别为 `assert 0 == 1` / `assert 1 == 3` / `assert 1 == 2`），未做修复验证。
7. **a9304c69 的机制是否为该族 8 条的唯一原因未逐处排除**：该 commit 一次改了 251 处 / 65 文件，本卡只验证了每条各自被测路径上的那一处 hunk 与桩异常类型对得上。
8. **草案假设 3 的机制（读侧按 `user_id` 等值过滤 / 写侧不写 `user_id`）虽被实测证实，但未验证修复方案**；也未排查除 `_record_failed_write` 外是否还有别的写入点会写 `user_id`。
9. **不在本卡范围**：26 条以外被 Y4-D skip 掩盖的 C1 33 条、MOCKFIX 9 条、以及修复工作量估算。
10. **sparse-checkout 的取舍未做完备性证明**。为绕开非法字节序列文件名与 `_bmad` 的切换阻断，scratch 树只检出白名单路径；已确认 `/src/` 必须保留（否则 conftest ImportError 会被误读成「测试那时不存在」），但未穷举证明白名单对区间内每个 commit 都充分。

## 9. 台账待登记条目

1. **RED-R 27 行分派表结论**：回归 19 / 契约演进 8 / 测试写错 0；分派表 `evidence-red-r/red-r-triage-20260909.md`。
2. **第十四批修复卡候选（按被测文件分族，台账实测无重名）**：`CARD-RED-R-FIX-agent-service`（2 条，first-bad a9304c69）、`CARD-RED-R-FIX-review-endpoint`（3 条，836d0986 ×2 + a9304c69 ×1）、`CARD-RED-R-FIX-memory-service`（**9** 条 = 3d10a02b ×5 + 59586af1 ×4）、`CARD-RED-R-FIX-neo4j-edge-client`（1 条，a9304c69）、`CARD-RED-R-FIX-intelligent-parallel`（3 条，a9304c69）、`CARD-RED-R-FIX-websocket`（1 条，a9304c69）；六族合计 **19** 条（= 回归数）。契约演进 **8** 条（1768c19d ×2 + 4236b12e ×1 + 43294c38 ×4 + 89d51dc9 ×1）移交 **U11-B RED-C2**（第十三批同批并行，未合）或第十四批。各族条数为分派表第 8 列实测计数，六族 + U11-B = 27。
3. **⛔ 超出「测试红」的生产问题（经 Codex round-1 MEDIUM + round-2 MEDIUM 两次纠正后的最终口径）**：
   - `review.py:239 / :448`（**已降级，不再计为生产缺陷**）：836d0986 把 `AgentType` 的 import 下移到 `from app.core.config import get_settings` 之后。① AI 出题走 template 降级是**既有状态**（`836d0986^` 上 `app/core/config.py` 同样不存在）；② 「配置补齐即 NameError」也**不成立** —— 配置补齐后 `AgentType` 会在同一个 try 里一并 import 成功；③ 生产正常路径 `:396` 提前返回，走不到 `:448`。实际触发只在测试那种「强置 `_ai_question_available=True` 却不补 `AgentType`」的部分替换状态下发生 ⇒ **本条目前只证明是测试侧回归，未证明存在生产触发路径**。
   - `memory_service.py:802-803` 读侧按 `user_id` 等值过滤 fallback，而写侧 `agent_service.py:99` 的 `_record_failed_write` 落盘 entry **无 `user_id` 字段** ⇒ 任何带 user_id 的调用都会把失败评分滤净，Story 38.6 AC-4 恒失效。
4. **第 27 条从 skip 名单捞回的失败身份与归属**：`test_full_cycle_recovery_fails_then_merge`（归 R）`assert history["total"] == 1` → `assert 0 == 1`；同 class 的 `test_full_cycle_fail_record_recover_merge`（归 C1）`assert result["recovered"] == 1` → `assert 0 == 1`。类级 skip 由 `1de96584`（2026-09-06 Y4-D）引入。
5. **两族「—」候选的裁定**：`43294c38`（group_filter ×4）与 `89d51dc9`（strip_whiteboard ×1）**均被 bisect 证实，候选未被推翻**（实测 6 步 / 8 步二分，good 端实测绿）。
6. **候选被推翻的 6 条**：epic30（a9304c69 → 实测 59586af1）、difficulty ×2（4867dd09 → 实测 836d0986，且 4867dd09 早于测试文件引入点）、qa_38_6 merged_view / story_38_6 / 第 27 条（e6fbd337 → 实测 59586af1；e6fbd337 落在该文件的 import-error 窗口内，两端均不可判）。
7. **草案 `:400-422` 三条机制假设的裁定**：假设 1（a9304c69 收窄 except）**证实**；假设 2（形参字段删后重写未恢复）**证实**，恢复点实测确为草案原写的 `d4823ef9`（`git log --reverse -S 'async def search_error_memories('` 只给出 3d10a02b 删 + d4823ef9 加，且 `f6a55d3a^` 已有该方法）—— 本卡此前误认成 `f6a55d3a`，经 Codex round-1 HIGH 纠正；假设 3（`user_id` 等值过滤 vs 写侧不写）**机制证实、first-bad 资格被推翻**。
8. **RED 族各卡通用的口径修正（建议主 session 收进协议 §5）**：`comm` 两侧必须同格式 —— `nodeids-26.txt` / red-align §二 是**裸 nodeid**，pytest 红集行带 `FAILED `/`ERROR ` 前缀，直接 `comm` 会输出全集 = 假阻断；本卡起统一「`diff` 用带前缀套 / `comm` 用 `.bare` 套」。
9. **基线与 RED 分派文件在 feature 主干树且 untracked** ⇒ 本批所有 NEW @ `da690bf8` 的车道引用 `evidence-b13/**` 必须用主干树绝对路径，并在开工做 `test -f` + `grep -vc '^#'` = 202 自证。
10. **Codex 复核轮次与裁定**：round-1（`codex-review-CARD-RED-R-r1.md`，绑 `8f5f9efc`）BLOCKER 0 / HIGH 3 / MEDIUM 4 / LOW 3 —— 三条 HIGH 与 MEDIUM-1 经逐条实测**全部成立**并已整改（HIGH-1 当前成因由「node_id 形参缺失」更正为「4236b12e 相关度地板」；HIGH-2 恢复点由 `f6a55d3a` 更正为 `d4823ef9`；HIGH-3 注入类型由「裸 Exception」更正为 `SessionNotFoundError(Exception)` 并登记异常链未闭合；MEDIUM-1 把「既有降级」与「本次埋下的 NameError」分开）；round-2（`codex-review-CARD-RED-R-r2.md`，同绑 `8f5f9efc`）**BLOCKER 0 / HIGH 0** / MEDIUM 3 / LOW 5 —— 达到 D-15 门槛。round-2 的 MEDIUM/LOW 亦逐条实测复核后全部成立并已整改：MEDIUM-1「配置补齐即 NameError」不成立（该条降级为纯测试侧回归）；MEDIUM-2 零代码门原命令 `8f5f9efc HEAD` 两端同一 commit 属**恒真假绿**，已换成「工作区 vs commit + `-uall` status + 验伪锚」重做并落档；MEDIUM-3「U11-B 未合入」降级为「未发现合入记录」（`is-ancestor` 排除不了 squash）；LOW 五条（§三 摘要未同步、返回类型表述、group_filter 实为 6 步、相邻区间仍会跑一次 BAD revision、1768c19d 删的是 17 个测试而非 12）均已改。整改只动 `_bmad-output/`，按协议 §1 不触发新轮次。
11. **⛔ bisect 方法学（建议收进协议，RED 族与任何跨历史二分通用）**，逐条均在本卡实测触发过：
    - 判据**不得用 pytest 退出码** —— 老 commit 的 `pytest.ini` addopts 含 `--cov-fail-under=85`，实测覆盖率 23%，「1 passed」也返回 rc=1，`git bisect run` 会把 GOOD 端判成 bad 并收敛到错误的 first-bad，全程无异常表现。
    - macOS **无 `timeout`** —— 卡文模板里的 `timeout 300` 实测 rc=127，而 bisect 把 127 当 bad ⇒ 每步都判 bad。改用 `perl -e 'alarm N; exec @ARGV'`，并把超时映射为 125(skip)。
    - GOOD 端 checkout 失败必须**显式比对 HEAD** —— 否则树停在 BAD 端，BAD 端结果会被当成 GOOD 端，产出「候选被推翻」的假结论。
    - `git bisect run` 是否收敛必须**显式校验** —— 端点验证通过（INTERVAL_OK）不代表二分跑成了；中途 checkout 被 local change 阻断时 git 直接 `Aborting`，存档里只是少了一行 first-bad。
    - **不得往 scratch 树写 `backend/.env`** —— 该文件在部分老 commit 是 tracked（且含 `bolt://localhost:7691` 现网 URI），放消毒副本 = local change ⇒ 下一次 checkout 中止。改由环境变量注入（env 优先级高于 dotenv），同时消除现网连接与 live vault 写入风险。
    - 测试写 tracked 文件（`backend/data/review_data.db`）同样阻断二分 ⇒ runner 每步跑完 `git checkout -- .`。
    - sparse-checkout 收窄会造成**伪 SKIP** —— 漏掉仓库根 `/src/` 会让老 commit 的 conftest ImportError，被判 SKIP 后**看起来像「测试那时还不存在」**。
    - `git log -S ... -- <file>` 的**搜索面是当前分支** —— 在主仓 `main` 下查车道分支才有的文件会静默返回空，误读为「函数从未出现」。
    - `grep ... | head; echo $?` 取的是 `head` 的码（恒 0）；`time (cmd | tail)` 会让 `$pipestatus[1]` 失真。
