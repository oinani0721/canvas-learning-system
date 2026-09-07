# UAT — CARD-RED-C1（第十三批 · 车道 U11-A）

> 批次 `[BATCH-2026-09-07-第十三批 / CARD-RED-C1]` · 车道 `card-u11-red-c` · 分支 `card/u11-red-c`
> 开工基线 `da690bf8` → 本卡提交 `343fce8e` · 日期 2026-09-08

---

## 1. 🎯 一句话目标

有十盏一直亮着的旧红灯，其实是「规矩早就改了、灯还按老规矩叫」——这次把说得清缘由的逐个改成按新规矩亮或熄，说不清的原样留着交给专门的人查，一盏都不蒙住。

---

## 2. 📖 你的视角

作为这个项目的负责人，我想知道**每一盏红灯到底是"规矩变了"还是"东西真坏了"**，以便我不会因为红灯太多而习惯性忽略它们，也不会因为有人把灯拧灭而错过真问题。

---

## 3. 🖥️ 交互流程（你屏幕上会看到的变化）

```
之前：一张长长的红灯清单，202 盏，其中这十盏年年在里面，没人说得清为什么
  ↓
现在：清单变成 194 盏
  ↓
少掉的 8 盏里 —— 3 盏改成按新规矩亮（现在是绿的）
                5 盏改成"知道它为什么不亮，且写明了谁接手"（不再计入红灯）
  ↓
剩下的 2 盏原样留在清单里，旁边多了一份写清楚"为什么怀疑是真坏了"的说明
  ↓
另外 37 盏被前人用布盖住的灯：布一块没揭，也一块没加
```

---

## 4-A. 🤖 Claude 已代验（技术判据，我已跑完并贴证据路径）

> 证据全部在 `_bmad-output/审查/evidence-red-c1/`，每份末行都是 `rc=<n>`。

| # | 判据 | 结果 | 证据文件（末行 / 关键行） |
|---|---|---|---|
| A1 | 第 0 分钟：目录 / 分支 / HEAD / 工作树干净 | ✅ | `pwd` = `…/worktrees/card-u11-red-c`；`git branch --show-current` = `card/u11-red-c`；`git rev-parse --short=8 HEAD` = `da690bf8`；`git status --porcelain` 空 |
| A2 | 开工目录级与 202 基线一致（基线在本树可复现） | ✅ | `red-diff-open-20260908T064547.txt` = **0 字节（空）**；`unit-open-20260908T064547.txt` 汇总 `= 173 failed, 4749 passed, 48 skipped, 122 warnings, 29 errors in 255.38s =`，末行 `rc=1` |
| A3 | 「取错节」三道交叉锚（防 nodeid 取到别卡那一节） | ✅ | `diff c1-nodeids.txt c1-nodeids.expected.txt` rc=0；`diff c1-files.txt files-a.txt` rc=0（恰 5 文件）；10 条逐条 `grep -cF` 于 `red-baseline-202.bare.txt` 均 = 1 |
| A4 | 外来红 9 条与卡文 §〇 预声明逐条相同 | ✅ | `foreign-9.txt`（9 行 = C2/U11-B 7 + R/U5-C 2） |
| A5 | 10 条失败身份原文已取（依据表第一列来源） | ✅ | `identity-open-20260908T065447.txt` 汇总 `19 failed, 39 passed, 6 skipped`（19 = C1 10 ∪ 外来红 9） |
| A6 | **10 条依据表，依据 sha 分两支不是抄十遍** | ✅ | `c1-verdicts.md` §1 / §3：`59586af1` 7 条 + **`daa9fd37` 3 条**（`git show 59586af1 --stat` 的文件列表里没有 `config.py`，故 DEPRECATED 默认族另取依据） |
| A7 | **终审绑定轮：`>` 行为零，`<` 行恰 8 条** | ✅ | `red-diff-20260908T071724.txt`：`grep -c '^>'` = **0**，`grep -c '^<'` = **8**，逐条 `grep -cF` = 1 且恰为本卡处置的 8 条；移交 2 条各 `grep -cF` = **0**（确实不在 `<` 行） |
| A8 | 终审轮汇总行与末行 | ✅ | `unit-after-20260908T071724.txt`：`= 165 failed, 4752 passed, 48 skipped, 5 xfailed, 121 warnings, 29 errors in 236.43s =`；末行 `rc=1`。errors 回到基线 **29**（被弃的两轮是 30） |
| A9 | 文件级：failed 集合 == 预声明外来红 9 ∪ 移交 2 | ✅ | `diff files-failed-20260908T065833.txt expected-failed.txt` **无输出**；汇总 `11 failed, 42 passed, 6 skipped, 5 xfailed`；`grep -c XPASS` = **0** |
| A10 | xfail 严格性：5 条全 `strict=True`，无 `strict=False`、无裸 `xfail(reason=` | ✅ | 5 文件开工**均无既有 xfail**（`xfail-baseline-open.txt`）⇒ 收工的 5 处全为本卡新增；`grep -rn 'xfail(strict=False\|xfail(reason'` 于 5 文件 → 无输出（rc=1）；每条 reason 含归属卡名 |
| A11 | **五处 Y4-D skip 标记一处未动** | ✅ | 硬判据：`git diff --no-color -- backend/tests/unit/ \| grep -E '^[+-][^+-]' \| grep -i 'skip'` → **无输出（rc=1）**；`y4d-skip-marks-open/close.txt` 留档 |
| A12 | 地盘门：非 `_bmad-output` 改动只 4 个测试文件 | ✅ | `git diff --name-only --no-color da690bf8 HEAD -- . ':(exclude)_bmad-output'` → 4 个测试文件；**验伪锚**：换成不存在的排除目录后 `_bmad-output` 条目重新出现，证明排除语法真的在起作用（不是命令没跑成） |
| A13 | `backend/app` 零改动 | ✅ | `git diff --stat --no-color da690bf8 HEAD -- backend/app` → 无输出 |
| A14 | 移交路线确实一行未碰 | ✅ | `test_qa_38_6_scoring_reliability_extra.py` 收工 sha256 与开工**逐字节相同**：`b87a39a4fbcc0adbffadcef3eff5421fdd581467646152ba42155de92997a1ba`（`files5-sha-open.txt`） |
| A15 | **格式：本卡零新增漂移**（不靠「两边都红」这种弱判据） | ✅ | 内容口径：HEAD 版与本卡版 `ruff format --diff` 的 ± 内容行**多重集逐条相同**（`diff` rc=0，`ruff-diff-head.txt` vs `ruff-diff-after.txt`）；本卡新增行在重排面里 `grep -cE 'CARD-RED-C1\|xfail\|daa9fd37\|canvas_service\.py'` = **0** |
| A16 | commit 规格 | ✅ | header **78** 字符（≤100，`wc -m`）含批次标记；body 逐行 `wc -m` 均 ≤100；本卡 diff 内 `stderr` 文件 = 0；`board_manifest_last_run.json` 未随卡提交 = 0；**未 push** |
| A18 | **改断言 3 条是承重的，不是恒真自证** | ✅ | `loadbearing-3assertions.txt`：把生产 `config.py` 的字段默认在**内存里**改回 `True`（= `daa9fd37` 之前的契约）后，3 条**全部翻红，KILLED 3/3**，且每条都是被**它自己那条断言的拒因**打红（不是被别的失败喂饱）。三阶段设计：①未变异时 3 条须全 PASS（前提门，防判据本身就坏）②打印变异后 `model_fields default` 与 `Settings(_env_file=None)` 实测值自证变异真的生效 ③逐条记 KILLED/SURVIVED 并贴拒因首行。末行 `rc=0` |
| A19 | A18 的变异**零磁盘改动**（未违反禁改 `backend/app`） | ✅ | 脚本在 scratchpad、非项目内；跑后 `backend/app/config.py` 的 sha256 与 `git show HEAD:` 版**逐字节相同**（`e5a8ce3e…5605`）；`git diff --stat -- backend/app` 无输出 |
| A17 | Codex 多轮至 BLOCKER/HIGH = 0 | ⏳ 见 §7 轮次记录 | `codex-review-CARD-RED-C1[-rN].md` |

### 4-A 附：三处需要主 session 知晓的「判据本身的问题」

| # | 事项 | 实情 | 本卡处置 |
|---|---|---|---|
| B1 | 卡文 §二.2 要求 SKIPPED 集 `diff` **为空** | 实测**非空**：4 行差异全来自 `test_story_38_6_scoring_reliability.py`，且**只是行号标签位移**（154/165/190/236 → 181/192/217/263，逐条 **+27**，恰等于 `git diff --numstat` 的 27 净增行；三个 hunk 全在 skip 标记之前） | **不拿归一化结果冒充「原始 diff 为空」**。如实登记：归一化行号后 rc=0（集合逐条相同）；不依赖归一化的硬判据是 A11 的 `git diff` 零 skip 改动。建议后续 RED 卡改为双条件判据 |
| B2 | 卡文 §一.(l) 要求 `git ls-tree -r HEAD --name-only \| grep -c stderr` = 0 | 实测 = **1**，命中 `_bmad-output/审查/G4-9-evidence/census-stderr.txt`，该文件在 `da690bf8` 里**就已存在** | 全树口径会算上存量。按「本卡 diff 内 stderr = **0**」如实登记 |
| B3 | 提交被 `python-lint` 格式门阻断 | 3 个测试文件在 `da690bf8` 上**就已** `Would reformat`（存量漂移）。按 D-16 甲禁顺手修存量（顺手 format 会改掉大量与本卡无关的存量行） | 按协议 §2.3 带存档跳过 `python-lint` 提交，存档 `lefthook-exclude-evidence-20260908T072435.txt` 含 hook 原始输出 + 三重「非本卡引入」证明。本卡零 `backend/app` 改动，`python-typecheck` 自报 `no files for inspection`，**未跳过**它 |

### 4-A 附：一条被跨车道环境噪音污染的轮次（已定位、已重跑）

前两轮收工目录级各出现 **1 条 `>` 行**（一条 teardown ERROR）。归属已钉死（`tmp-window-attribution.txt`）：

1. 错误正文是工作树污染不变量门报「新出现 `/tmp/test-vault*` 目录: `/tmp/test-vault-treeB-49484`（第二轮为 `-88464`）」；
2. `stat` 实测两目录创建于 07:01:42 / 07:14:21，**落在各自那一轮的运行窗口内**；写者 pid 已退出，非本 session；
3. U10-A 车道跨 session 通告其负控窗口为 06:59:14–07:18:58，期间建过且仅建过 4 个目录，**其中两个正是我抓到的这两个** —— 归属由第二来源独立印证；
4. 第三轮（07:17:24 起跑）errors 回到基线 **29**、污染特征串计数 **0**、`>` 行零 ⇒ **终审绑定轮**；
5. 三轮的 `<` 行集合**逐轮相同**，差别只在那一条噪音。被弃的两轮存档保留供审计，未删。

### 4-A 附：一处当场自查发现并纠正的错误

我一度想从 `-q -rs` 那一轮存档派生 nodeid 差集，得到「202 条全部消失」的结果。原因是 **pytest 的 `-r` 是替换而非追加**短摘要类别：默认 `-q` 给 `fE`，显式传 `-rs` 后短摘要**只剩 SKIPPED**，FAILED/ERROR 行消失。同一 HEAD 两轮实测：`rs-close` 的 `^FAILED ` = **0** / `^SKIPPED` = 48；`unit-after`(-q) 的 `^FAILED ` = **165** / `^SKIPPED` = 0。本卡的 nodeid 判据自始至终只用 `-q` 轮、SKIPPED 判据只用 `-rs` 轮，未受影响；两个错误派生文件已移出证据目录，未入库。

---

## 4-B. 👤 你来验（3 分钟，不用打开任何工具，读完对照着想一遍就行）

- [ ] 我读完上面那句「一句话目标」→ 我看到少掉的 8 盏灯里，3 盏是**改成按新规矩亮**、5 盏是**写清楚了为什么不亮并且写了谁接手** → 我感觉这两种都不是"把灯拧灭"，心里踏实。

- [ ] 我特意找"有没有哪盏灯是被蒙住的" → 我看到剩下的 2 盏**原样留在清单里没动**，旁边附了一份写清楚"为什么怀疑它是真坏了"的说明 → 我感觉说不清的没有被硬掰成说得清，这一点让我信任这份清单。

- [ ] 我问"那 37 盏前人用布盖住的灯呢" → 我看到布**一块没揭、也一块没加**，并且有一条直接的证明说这次改动里一处都没碰到布 → 我感觉没有人顺手动了不属于这次的东西。

- [ ] 我问"这十盏灯的缘由，会不会是同一个理由抄了十遍" → 我看到缘由分成**两个不同的来源**，其中三盏的来源和另外七盏根本不是同一件事，而且是核对时发现原本的猜测不成立才改的 → 我感觉这是真去查了，不是走过场。

- [ ] 我追问"那 3 盏改成按新规矩亮的灯，会不会以后不管出什么事都一直绿着" → 我看到他专门做了一次试验：把规矩**临时改回旧的**，那 3 盏**立刻全部报警**，而且每盏报的都是它自己该报的那句话 → 我感觉这 3 盏是真在看着东西，不是摆设。

- [ ] 我问"过程里有没有出岔子、出了会不会告诉我" → 我看到有一轮结果被**别的并行工作**干扰了，说明里写清楚是怎么认出来的、重跑后干净了；还有一处是他自己中途算错、当场发现并写进说明 → 我感觉出问题时会被如实告诉，而不是等我自己发现。

**一句话总结（用你的话）**：一直亮着的十盏旧红灯里，这次把「规则早就改了、灯还按老规则叫」的那些逐个改成按新规则亮或熄；说不清为什么红的那几盏不硬掰，交给专门查「是不是真坏了」的人——我看到红灯变少但没有一盏是被蒙住的，心里更踏实。

---

## 5. 🚦 验收结果

- **通过** → 说一句「复核第十三批 U11」，我把这张卡交主 session 复核，同车道继续 U11-B。
- **不通过** → 在下面批注区写下你觉得不对的那一条，我按批注调整后重跑全部判据并重新送独立复核。

---

## 6. 📝 批注区

> [!question]+ 你的提问
>
>

> [!error]+ 你发现的问题
>
>

---

## 7. 🔗 技术引用

| 项 | 路径 |
|---|---|
| 卡文 | `…/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U11-A.md` |
| 依据表（核心交付物） | `_bmad-output/审查/evidence-red-c1/c1-verdicts.md` |
| 证据目录 | `_bmad-output/审查/evidence-red-c1/` |
| 本卡 commit | `343fce8e`（未 push） |
| 改动文件 | `backend/tests/unit/{test_cache_configuration, test_qa_38_4_dual_write_extra, test_story_38_4_dual_write_default, test_story_38_6_scoring_reliability}.py` |
| Codex prompt | `_bmad-output/审查/prompts/codex-prompt-CARD-RED-C1.md` |
| Codex 存档 | `_bmad-output/审查/codex-review-CARD-RED-C1[-rN].md` |

### Codex 轮次记录

| 轮 | 模型 / effort | 绑定 SHA | BLOCKER | HIGH | MEDIUM | LOW | 存档 |
|---|---|---|---|---|---|---|---|
| r1 | `gpt-6-astra` / `ultra` | `343fce8e` | **0** | **0** | **0** | **4** | `codex-review-CARD-RED-C1.md` |
| r2 | `gpt-6-astra` / `ultra` | 见下（r1 四条 LOW 全整改，含一处代码改动 ⇒ D-15 必再送一轮） | 待填 | 待填 | 待填 | 待填 | `codex-review-CARD-RED-C1-r2.md` |

#### r1 四条 LOW 的处置（**全部经本车道独立复验成立，一条未驳回**）

| # | 发现 | 我的复验 | 整改 |
|---|---|---|---|
| LOW-1 | 配置项那条 xfail 的 reason 只写「配置清理卡（登记）」，无可定位接收卡标识 | 成立（卡文硬约束要求 reason 写明归哪张卡，泛称不满足） | **代码改动**：reason 具名 `CARD-CONFIG-CLEANUP` |
| LOW-2 | 收工 skip 快照按旧行号抓，`test_story_38_6` 那段抓空 ⇒「五处原文均留存」比证据宽 | 成立（实测该段确为空标题） | 内容锚定重采 `y4d-skip-marks-close-v2.txt`，与开工归一化 `diff` **rc=0**，实测行号 `37/33/263/162/326` |
| LOW-3 | 「11 处生产调用方」未说明统计口径 | 成立，**且比它指出的更糟**：我那一行的枚举是 8+1+1=**10**，写出来的数字却是 **11**，内部自相矛盾 | 三口径写明，统一采「直接调用 `AgentService._trigger_memory_write`」= **10**（另 2 处为 `batch_orchestrator` 同名包装转发，全口径 12） |
| LOW-4 | 「`59586af1 --stat` 只有两个文件」有误 | 成立（不限路径实测 **3** 个，多一个 −409 整文件删除的 `graphiti_bridge_service.py`） | 措辞改为绑定「限定三条路径的那条命令」，并贴出不限路径的真实列表 |

#### Codex 独立确认的判据（第二来源，非我自述）

- 从**原始日志重算** `202 → 194，移除恰好 8 条、新增 0 条`，两条移交测试仍红 —— 与 A7 的算术独立吻合。
- 三条翻绿断言「均能捕捉生产默认值变回 True」—— 与 A18 的内存变异实测（KILLED 3/3）结论一致。
- `canvas_service.py` 六处 getattr「真实存在，第三参数全部为 True」—— 印证我收窄 reason 措辞是必要的。
- 「最终提交仅在 AC1 三个方法前各新增 9 行，类级 skip 与被遮蔽用例均未改」「其他用例、所有类名和类级装饰器保持不变，移交文件也完全未改」。

#### Codex 的两条实质性观察（采纳，不改结论）

1. 选 B 的依据可以更准：旧符号零命中只证明**旧符号消失**；现存 worker 仍有 `can_retry` / `backoff_seconds`，但用**随机退避**，不实现原来固定的 2 秒 / 1·2·4 秒契约 ⇒「无可重锚生产符号」**成立且更强**。
2. `test_episode_worker_retry.py` 5 个用例的实际覆盖面（对 `CARD-EPW-COVERAGE` 直接有用）：入队成功 / 三次失败后第四次成功与退避范围 / 耗尽重试写死信 / 指标 / 显式 `request_id` 进死信；**未覆盖**旧单次超时、固定退避、`MemoryService` 配置读取、getattr 防御、旧失败文件恢复，且退避范围断言「甚至允许恒零延迟通过」⇒ 不足以证明完整等价覆盖 —— 与本卡「只登记缺口、不宣称等价」一致。

#### Codex 明确未能独立确认的面（如实转录，不代为背书）

- (e) 的调用关系它只确认 `backend/app` 范围，未扩面背书「全仓只有测试」，未验证现网 pending 数据 —— 与 §8 第 4 条一致。
- `/tmp` 归属的 `stat`/`ps`/跨 session 通告**只有我的转述**，它无法独立确认写者身份。
- 它指出「不能单凭『终审绑定轮』这个名称证明其输入精确绑定 `343fce8e`」→ **已补证**：4 个测试文件最后修改 `06:57:40 / 06:57:26 / 06:57:07 / 06:56:21` < 终审轮起跑 `07:17:24` < 结束 `07:21:34` < commit `07:24:48`，且工作树内容与 `343fce8e` 内容逐文件 sha256 **4/4 相同** ⇒ 终审轮跑的正是该 commit 的代码内容。

---

## 8. ⛔ 本卡未证明什么（必填）

1. **不证明 `test_episode_worker_retry.py` 等价覆盖了被 skip 的 33 条语义** —— 只登记缺口为 `CARD-EPW-COVERAGE`。该文件 `grep -c 'def test_'` = 5，5 个用例对 18+8+3+3+1 条的语义覆盖度**本卡未做逐条映射**。
2. **不证明 `59586af1` 之前这 10 条是绿的** —— 依据只证明「被断言的符号是在那个 commit 被删的」，未回溯当时的运行结果。
3. **不证明 Story 38.x 的契约当前"应该"取何值** —— 2.0/1.0 只是删前的生产值，不是产品裁定；本卡对子类②走的是退役交接，不是替它选值。
4. **不证明启动期 fallback JSON 回写被删是否真的造成了数据面丢失** —— 只提供了 8 条源码层证据（写侧 11 处生产调用仍活 / 两条回收路径零生产调用方 / 替代者未接管 / 启动期恢复的是另一机制），**没有**查现网是否有 pending 条目在丢：`backend/data/failed_writes.jsonl` 今日 06:46 的改动是**本车道自己的测试跑**造成的（该路径被 `backend/data/.gitignore:5 *.jsonl` 覆盖 ⇒ 工作树状态恒绿看不见这类污染），不能当生产证据；本卡未碰 live vault、未跑服务、未连 7691/7687。定性归 U5-C。
5. **不去 skip、不恢复 Y4-D 关掉的 4 条原本绿** —— 归第十四批 Y4-D 尾巴微卡。
6. **不证明 `config.py:644/:650` 的 `MEMORY_RETRY_*` 被任何路径消费** —— 只做了 census（`backend/app` 内零消费方），未排除运行期动态读取等非静态可见路径。
7. **只在 `tests/unit` 目录级验证** —— 未跑 `tests/integration` / `tests/e2e`（卡文明令禁止）。
8. ~~不证明本卡改后的 3 条断言在"生产默认被改回 True"时一定会红~~ → **已补证，见 A18**。仍未证明的边界：该验证是**内存态**变异（改 `FieldInfo.default` + `model_rebuild`），未覆盖「有人改的是 `.env` 或环境变量而非字段默认」这一路径（那条路径下 `test_settings_field_default_is_false` 按设计本就不该红，它锁的是字段默认而非运行值）。
9. **不评价那 2 条移交用例本身的门强度** —— `"sync_all_fallbacks" in source` 是子串断言，对复制/位移/末尾追加失明，即便回归属实也不是好门；但「无替代覆盖不许删」，移交分支下本卡本就不改它们。

---

## 9. 📋 台账待登记条目（必填，主 session 登记）

1. **C1 分母勘误 43 → 10**（202 口径）；另 33 条被 Y4-D `f19dcff6` 模块级/类级 skip 掩盖，清单指针 = `red-align-da690bf8.md` §三。
2. **10 条处置结果计数**：改断言 **3** / xfail(strict=True) 交接 **5** / 移交 U5-C **2**；依据表 `_bmad-output/审查/evidence-red-c1/c1-verdicts.md`。
3. **GraphitiEpisodeWorker 等价覆盖缺口 → 独立卡候选 `CARD-EPW-COVERAGE`**（33 + 4 条 nodeid，第十四批）；本卡 5 条 xfail 的 reason 已全部指向它或配置清理卡。
4. **`test_story_30_24_boundary.py:468` 归属勘误**：规划稿写 U11-A，实为 C2/U11-B，本卡未碰。
5. **`FallbackSyncService.sync_all_fallbacks` 零生产调用方 = G-PIPE 候选**（`docs/known-gotchas.md` G-PIPE 族）；连带 `MemoryService.recover_failed_writes` 亦零生产调用方。**移交 U5-C RED-R 的 2 条 nodeid 见 `handover-u5c.txt`**。
6. **`MEMORY_RETRY_BASE_DELAY/MAX_DELAY` 消费方 census 结果**：`backend/app` 内**零消费方**（只有 `config.py:644/:650` 定义），属死配置项 → **接收卡命名 `CARD-CONFIG-CLEANUP`**（第十四批候选）。该 ID 已写进 `test_cache_configuration.py` 那条 xfail 的 reason，解除 xfail 时可从代码直接定位（Codex r1 LOW-1 整改）。
7. **Codex 各轮存档路径 / 绑定 SHA / B·H·M·L 计数** —— 见 §7 轮次表。
8. **开工/收工 nodeid diff 与 SKIPPED 集 diff 结果路径** —— `red-diff-open-20260908T064547.txt`（空）/ `red-diff-20260908T071724.txt`（8 `<`、0 `>`）/ `skips-open-20260908T065015.txt` vs `skips-close-20260908T070403.txt`（见 §4-A B1）。
9. **卡文两处事实更正（写卡期已记）复核确认**：`MEMORY_WRITE_TIMEOUT` 在 `agent_service.py:93` = 15.0（`memory_service.py` 0 命中）✅ 实测确认；C2 文件数 23 ✅ 未复算（本卡不需要）。
10. **文件级判据勘误（写卡期第 2 轮已记）复核确认**：5 文件在 202 里 19 条红、本卡只占 10，另 9 条外来红 ✅ 实测确认（`foreign-9.txt` 与卡文 §〇 逐条相同）。
11. **(c)-A 自证面（写卡期第 2 轮已记）复核确认**：两常量在 `backend/app` 双 0 命中 ✅ 实测确认 ⇒ 本卡走默认 B。
12. **⭐ 本卡新增事实更正 3 处**（写卡期未预见）：
    - **(d) 3 条的依据 sha 是 `daa9fd37` 不是 `59586af1`** —— `git show 59586af1 --stat` 的文件列表里没有 `config.py`。卡文 §二.4 预留的分支被实际命中。
    - **(d) ③-b 的 reason 措辞须收窄** —— 卡文原稿「本用例的被测防御模式已无实现」过宽：同形 `getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True)` 在 `canvas_service.py:267/:360/:440/:457/:986/:995` **仍有 6 处**且 fallback 默认值是 **True**（与用例名所称 False 相反）。已改为「memory_service 侧的该防御点已删」并把 6 处写进 reason。
    - **模块 docstring 未改并登记** —— `test_story_38_4_dual_write_default.py:8/:10` 仍称默认为 True，与翻转后的断言不一致。卡文只授权改 10 个用例的函数名/函数体/装饰器/docstring 与 `TestAC1SafeDefault` 类 docstring，未授权改模块级文件头（该文件头同时描述 U11-B 地盘的 AC-2）。本卡不改，登记为残留名实不一致项。
13. **⭐ 本卡新增判据盲区 2 处**（建议写进协议或后续 RED 卡文）：
    - **SKIPPED 集「diff 为空」判据对行号位移失明** —— 同文件插入行会让 pytest 的 SKIPPED 行号标签整体位移，原始 diff 必然非空。建议改双条件：「归一化行号后 diff 为空 **且** `git diff` 内零 skip 改动」。
    - **`-rs` 替换默认 `fE` 短摘要** —— `-q -rs` 那一轮存档里没有 FAILED 行，从它派生 nodeid 差集会得到「全部消失」的假差集。要一轮同时取两者须传 `-rfEs`。
14. **⭐ 跨车道 `/tmp` 共享导致的目录级假红** —— U10-A 负控窗口 06:59:14–07:18:58 期间，本车道两轮收工目录级各多一条 teardown ERROR。归属证据 `tmp-window-attribution.txt`。U10-A 自报其卡合入后该干扰不再打红别的树。
15. **⭐ `python-lint` 带存档跳过一次** —— 存量格式漂移（3 个测试文件在 `da690bf8` 上就已 `Would reformat`）。存档 `lefthook-exclude-evidence-20260908T072435.txt`；本卡零新增漂移已由内容口径多重集对照证明（rc=0）。存量归 lint/format 专项清理卡。
16. **⭐ `stderr` 全树判据会算上存量** —— `_bmad-output/审查/G4-9-evidence/census-stderr.txt` 在 `da690bf8` 里就已存在；本卡 diff 内为 0。建议判据改「本卡 diff 内」口径。
