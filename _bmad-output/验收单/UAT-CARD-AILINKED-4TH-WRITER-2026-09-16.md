# UAT · CARD-AILINKED-4TH-WRITER — ai-linked-doc 第四写者对齐账本四写规

> 批次 `BATCH-2026-09-11-第十四批` · 车道 `card-t7-skills`（分支 `card/t7-skills`）
> **PREQ**（T7-A tip）= `d5ad6fca` · **终审 HEAD** = `341a88b6` · **未 push**
> Codex **4 轮**（gpt-6-astra · ultra），末轮绑最终 HEAD **B0 / H0 / M0 / L0**
> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T7-B.md`

---

## 1. 🎯 一句话目标

从一篇笔记里派生出新笔记时，这次「派生」要被如实记进学习账本——不会因为别处恰好出现过同样的名字就被当成重复丢掉，也不会在多篇同时派生时记重、记串或记坏。

## 2. 📖 你的视角

作为一个边读边拆概念的学习者，我希望**每一次派生都留下痕迹**，以便后面的复习安排知道我什么时候学过什么；痕迹丢了，复习就会漏掉那个概念。

## 3. 🖥️ 交互流程

你在一篇笔记里选中一段文字 → 触发派生 → 新笔记生成并写入 → **屏幕上多出一条「事件已落日志」的提示**（失败时是一条「写入失败(不阻断派生)」的提示，派生本身照常完成）→ 你继续读下一段。

---

## 4-A. 🤖 Claude 已代验（技术证据）

> 证据目录：`_bmad-output/审查/evidence-ailinked-4th/`（全部 `.txt`，`*.stderr*` 不入库）

### (a) 第 0 分钟自证 + 授权凭据

| 项 | 实测 |
|---|---|
| `pwd` / 分支 | `…/worktrees/card-t7-skills` / `card/t7-skills` ✅ |
| `PREQ=$(git rev-parse HEAD)` | `d5ad6fca21efbf6b02a3f05f7480855534cae760`（= T7-A tip）✅ |
| `git status --porcelain` | 空 ✅ |
| `backend/.venv/bin/pytest` + `backend/.env` | 均在位 ✅ |
| pyright 开工基线（cwd=`backend/`，R-B14-10） | `0 errors, 81 warnings, 0 informations` ✅ |
| 基线 `grep -vc '^#' $BASE` | **64** ✅ |

**(c2) 第 5 文件授权凭据**（手册 §一「只 T7」行，`grep -nF` 实测）：

```
67:- **只 T7**：…、`backend/tests/regression/test_learning_events_schema_contract.py`（T7-B，裁 (c2)）。
```

⚠️ **行号漂移**：卡文记 `:65` → 实测 `:67`（+2）。

### (b)(c) 五门先红后绿

改前那一跑在 **SKILL.md 未改**时做（`git show d5ad6fca:<path>` 临时写入，`try/finally` 无条件还原，前后 `sha256` 逐字相同）。
存档：`ailinked-red-final-20260916T192854.txt`（先红）/ 收工全量绿见 `skills-close-r3-20260916T195156.txt`。

| 门 | 改前（PREQ）红点 | 改后 |
|---|---|---|
| ① 子串误判丢事件 | 「子串误判 duplicate 永久丢失」**实见 0 条** | ✅ 1 条 |
| ② 同 evid 并发（**四条互补判据**） | **红 3/4**：档A `n=2` / `size-at-release=462` / `elapsed=0.00s` | ✅ 全绿 |
| ③ 尾行无 LF 粘连 | 「尾行无 LF 时新事件粘连成坏行」**实见 1 条非空行**且该行解析失败 | ✅ 恰 2 条且都可解析 |
| ④ 形态门三类可达反例 | 三子用例各红（尾随空白 / U+2028 / 超长 607 字符） | ✅ 三例均拒写且不阻断 |
| ⑤ **无法解码的坏行**（round-2 新增） | 红在 `rc=1` —— 写点**直接崩溃**于 `UnicodeDecodeError`（原写点对文件迭代无任何保护） | ✅ 照常落账 1 条 |

先红那一跑：**7 failed / 2 passed**（2 passed = 设计上改前也该绿的伴随判据与验伪锚）。
收工全量：本文件 **9 passed**。

⚠️ 门② 的第 ④ 条判据（账本无空行）是 round-1 整改新增，改前档 B 未触发并发补 LF 故未红；它的价值在负控②⑤ 中体现（两段都红）。

### (e) 五段负控（各红在指定断言）

存档：`ailinked-negctl-final-20260916T192703.txt`。每段 `try/finally` 无条件还原，**两份被监视文件跑前/跑后 `shasum -a 256` 逐段逐字相同**；五段只改 PYEOF 块**正文**，两条界线未动（脚本内有断言）。

| 段 | 变异 | 实测 |
|---|---|---|
| ① | parsed-field 相等 → 子串查重 | **只**门① 红。门⑤ 未红——本段只变异查重方式、未动解码方式，严格解码先抛异常就跳过了，**两门正交** |
| ② | 去掉 `fcntl.lockf` | 门② **4/4 全红**（档A `n=2` / 档B `n=2` / `size=462` / `elapsed=0.01s` / 有空行） |
| ③ | 去掉 LF 守卫 | 门③ 红在承重的两条子断言 |
| ④ | 形态门旁路 | 门④ 三子用例各红 |
| ⑤ | 锁内同 fd 读 → 二次 `open` | 门② **红 ①④，而 ② `size-at-release=0`、③ `elapsed=3.99s` 仍绿** —— 写点**确实等到了锁、确实没抢写**，却照样重复落账。**「恰 1 条」不可被另两条替代，得证** |

### (d)(f)(g)(h)(i)(j) 其余判据

| 判据 | 实测 | 存档 |
|---|---|---|
| pyright（cwd=`backend/`，绝对路径 + `test -x`，无 `\| tail -1`） | `0 errors, 81 warnings, 0 informations` | `static-close-final-20260916T193559.txt` |
| services 仅改注释 | 去 docstring 后 **AST 与 PREQ 相同 = True** | `ast-equivalence-20260916T132004.txt` |
| `tests/skills` 目录级 | **555 passed**（基线 546 + 本卡 9）；`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` | `skills-close-r3-20260916T195156.txt` |
| 四个 regression 文件单跑（含 producer 门 + 门⑪） | **569 passed / 1 skipped**，与开工同数 | `regression-close-final-20260916T192924.txt` |
| `tests/unit` 目录级（带 `--ignore tests/unit/test_deploy_vault_sh.py`，R-B14-3） | base=**64** / close=**64**，`diff` 为空（无 `>` 行） | `unit-close-final-20260916T193632.txt` |
| 门⑪ 普查集合 | 恰 **4** 份（services + 三个 skill） | `static-close-final-*.txt` |
| ruff `check` + `format --check` | 均通过；**验伪锚 F821 → rc=1** | `ruff-anchor-20260916T130903.txt` |
| 地盘门 | 恰 **5** 文件，⊆ 授权集；终审绑定 `341a88b6..HEAD` 代码面为空 | `territory-final-*.txt` |
| lint 指纹 | `f3673ca9529e…` 与 SKILL.md 实测 `sha256` 逐字一致 | `static-close-final-*.txt` |
| PYEOF 外形 | 开界线 `:217` 行尾无空白 / 闭界线 `:354` 顶格 / 块正文行首 `PYEOF` **0** / 两处 `<>` 占位各保留 | `static-close-final-*.txt` |

### (k) Codex 4 轮（gpt-6-astra · ultra · codex-cli 0.153.3）

| 轮 | 绑定 | 结论 | 整改 |
|---|---|---|---|
| r1 | `41629ec3` | B0 H0 **M2 L1** | M1 坏行只捕 `ValueError`；M2 计时起点致正确实现假红；L1 并发补 LF 面无人测 |
| r2 | `65e3f333` | B0 H0 **M1** L0 | M1 有损 UTF-8 解码使无法解码的坏行成为查重证据 |
| r3 | `12f85104` | B0 H0 M0 L0 | 清洁附注：测试源码 2 个裸 U+2028 |
| **r4** | **`341a88b6`（最终 HEAD）** | **B0 H0 M0 L0** | — |

四份存档首部含 `模型 / reasoning_effort / codex` 三字段 + `.stderr` 会话头自证（L2/L5/L9 括注行号），旧模型名计数 **0**。
r4 中 Codex **成功跑起 pyright** 并独立复证 `backend/app` = `0 errors / 81 warnings`。

---

## 4-B. 👤 你来验

> 三步，全在 Obsidian 里完成，约 3 分钟。

- [ ] **我做**：随便打开一篇已有的笔记，选中一小段文字，触发一次派生。
      **我看到**：新笔记生成出来了，同时屏幕上出现一条「事件已落日志」的提示。
      **我感觉**：这一次学习被记下来了，不是做完就没了。

- [ ] **我做**：换一篇笔记，用**同一个名字**再派生一次（比如两处都叫「特征值」）。
      **我看到**：新笔记照常生成；账本里这个名字只留一条，不会重复堆两条。
      **我感觉**：它分得清「同一件事」和「两件事」，不会把我的记录搞乱。

- [ ] **我做**：连着快速派生好几篇不同的新笔记，中间不等它。
      **我看到**：每一篇都生成成功，回头看每一次派生都在账本里，一条不少。
      **我感觉**：**从一篇笔记里再派生出新笔记时，这次派生会被如实记下来，不会因为别处恰好出现过相似的名字就被悄悄当成重复丢掉；多篇同时派生也都记得住——我感觉派生记录终于可靠了。**

---

## 5. 🚦 验收结果

- 三条都勾上 → 说「T7-B 通过」，我继续同车道 T7-C。
- 任一条对不上 → 在下面批注区写你看到的现象（不用写原因），我来查。

## 6. 📝 批注区

> [!question]+ 你的提问
>

> [!error]+ 你发现的问题
>

---

## 7. 🔗 技术引用

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T7-B.md`
- 写点：`canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` **Step 5.5**（`:214-354`）
- 参照实现：`backend/app/services/learning_event_log.py:188-343`
- 五门：`backend/tests/skills/test_ai_linked_doc_writer.py`
- producer 门：`backend/tests/regression/test_learning_events_schema_contract.py::test_real_producer_ai_linked_doc_writer`
- Codex 存档：`_bmad-output/审查/codex-review-CARD-AILINKED-4TH-WRITER{,-r2,-r3,-r4}.md`

---

## 8. ⚠️ 口径更正（本卡实测，与卡文/排批稿不同之处）

1. **写点原位于 Step 3 的 System Prompt 模板 fence 内**（`:128-191`，卡文 §〇 未记）。三反引号 fence 不能套三反引号 fence，且那条 bullet 本就是给 Skill 执行者的 Bash 动作（原文「新节点写入成功后」）却被放进了给**生成器**的 prompt 里 ⇒ 移出为 **Step 5.5** 独立 ```bash 块（Step 5 正是「写新节点文件」）。Codex r2 判「理由充分」，并指出「fence 绝不能嵌套」这个措辞不准确（外层用四反引号可容纳内层三反引号）——措辞已收敛为「三反引号 fence 不能套三反引号 fence」。
2. **门② 的先红确定性取决于屏障精度**：无屏障 **0/3** 复现（两个 `Popen` 启动差 ~30ms ≫ 写点读写窗口 ~1ms，第二个写者读到第一个写完的账本）；屏障 + `sleep(0.001)` 轮询 **3/5**（macOS 实测抖动 1~2ms，与窗口同量级）；屏障 + **busy-spin** **6/6**。卡文口径更正④ 的「两进程同屏障」四个字，实现精度决定它是真门还是假门。
3. **门② 需要两档账本**（卡文只写「空账本」）：第一轮负控**推翻**了单档形态——改后的写点把 import 全提到开头并用 `os.read` 一次性快照，「读→写」窗口缩到几十微秒，于是去掉 `fcntl.lockf` 只红 2/3、锁内换二次 `open` **全绿**（本该证明「①不可替代」的那一段什么都没证到）。加档 B（20000 行，解析 ~36ms > 取锁轮询间隔 20ms）后两段负控才成立。
4. **lint 指纹行号**：卡文 `:4354` → 实测 `:4383`（T7-A 改动致 +29）。
5. **(c2) 凭据行号**：卡文 `:65` → 实测 `:67`（+2）。
6. **ruff 验伪锚不能用 F401**：`backend/**` 未启用该规则，F401 锚 rc=**0**（恒不触发 = 假锚）；改用 **F821**，rc=1。
7. **本卡自己引入过两处问题并自查修掉**：SKILL.md 注释里 2 个裸 U+2028/U+2029（全仓其余 8 个 `SKILL.md` 该计数均为 0）；测试源码里 2 个裸 U+2028，恰好落在「⛔ 源码里用转义写，不敲裸码点」那条注释和它下面的反例里。
8. **`test_learning_events_schema_contract.py:369` 的 2 个裸 U+001C 非本卡引入**（`d5ad6fca` 逐字节相同，属 `test_control_char_wrapped_line_rejected`，在本卡可改的 producer 函数之外），不动。

9. **两条收工判据自身有假阴性，已修正并留档**（`territory-corrected-*.txt`）:
   - **中文路径被 git quoting**：`git diff --name-only` 对非 ASCII 路径输出 `"_bmad-output/\345…"`（**行首是双引号**），于是地盘门的验伪锚 `grep -c '^_bmad-output/'` 恒 **0** —— 看起来像「pathspec 没起作用」，实际是判据自己匹配不到。必须 `git -c core.quotepath=false`；修正后 = **43**。
   - **`grep 'stderr'` 取名面过宽**：它命中了历史批次里**名字含 stderr 的 `.txt`**（`census-stderr.txt` / `stderr-not-tracked-*.txt` / `stderr-gate-*.txt`），那不是 `*.stderr` 后缀文件。判据应取 `'\.stderr'` 且只看本卡新增面；修正后本卡新增 = **0**，另贴四份 `.stderr` 各自的 `git check-ignore -v` 命中 `.gitignore:264`。

10. **第三条判据也有同型假阴性**（`not-pushed-*.txt`）：`git log origin/<br>..HEAD | wc -l` 在 **remote 分支根本不存在**时命令出错，stderr 被吞掉后 `wc -l` 同样得 **0** —— 与「已同步」无法区分。改用正面证据：`git rev-parse --verify origin/card/t7-skills` 报 `fatal: Needed a single revision`、`branch -r | grep -c 't7-skills'` = 0、本分支**无上游配置**；验伪锚 = remote 分支总数 **23**（证明 `branch -r` 确实列得出东西）。⇒ 两个 commit 均未 push。

---

## 9. 🚫 本卡未证明什么

1. **未证明现网 `learning_events.jsonl` 里是否已有因旧缺陷被误丢的 node_derived 事件** —— 只能从账本历史对账，本卡不碰现网。
2. **未在真实 vault 端到端跑 ai-linked-doc skill** —— 只逐字提取写点模板用子进程跑，不起 Obsidian、不连后端。
3. **未修 `start-exam-board/SKILL.md:477` 的同类子串残留**（登记移交）。
4. **形态门只覆盖可达的三类形态**（尾随空白 / 禁止码点 / 超长），未覆盖校验器其它语义校验（`event_version` / 双时间戳等）；**且未覆盖「空 evid」「前导空格」——在 `derive:` 前缀下实测不可达**，若将来写点改成拿裸节点名当 evid，这两类会重新可达。
5. **门② 的「必红」不是跨机器 / 跨调度保证**（Codex r2/r3 指出并经采纳）：它依赖「档 B 的解析耗时 > 写点取锁轮询间隔」这个时间常数关系，固定 backlog 与 busy-spin 屏障只是把竞态窗口放大。应作为**本机压力回归证据**，结合静态的锁生命周期复核一起读。
6. **门② 的计时不是无条件时序保证**：`t_held` 是父进程收到 `held` 的时刻、`t0` 在放行后记录，`HOLD_S * 0.25` 的准备耗时上限挡住了本机常见抖动（实测 `prep ≈ 0.03s`，余量约 30 倍），但不能覆盖任意调度停顿。未采纳 Codex 建议的 `sys.settrace` + 管道握手形态——需要在逐字模板外再套一层执行控制，复杂度与本卡收益不成比例且会引入「trace 改变被测行为」的新风险；Codex r3 确认「本卡无需强制改」。
7. **并发只验两进程同机 `fcntl.lockf`**，未验网络盘 / NFS 的记录锁语义。
8. **未证明写点外形改为 PYEOF 块对其它逐字提取 ai-linked-doc SKILL.md 的测试/工具（非 learning_events 面）无副作用** —— 本卡只跑 `tests/skills` 目录级 + 四个 regression 文件单跑。
9. **超时路径未被触发**：`HOLD_S = 4.0` 远小于写点侧取锁超时 30s，「写点内部锁等待超时」的行为不在本卡承诺范围。
10. **坏行隔离不含资源耗尽场景**：Codex r3 明确「整本读入仍不能提供资源耗尽情况下的无条件隔离保证」。
11. **`pyright` 的 `0 errors` 只是 `backend/app` 面**：Codex r4 实测根配置范围为 `165 errors / 82 warnings`，额外诊断均在本卡未改的根 `tests/`，**不能表述为全仓结果**。

---

## 10. 📒 台账待登记条目

1. **第四写者子串查重数据丢失面已修** → 本卡 `341a88b6`；五门 nodeid 见 `backend/tests/skills/test_ai_linked_doc_writer.py`（`test_substring_dedup_false_positive_loses_event` / `test_undecodable_line_is_not_dedup_evidence` / `test_concurrent_same_evid_under_held_lock_writes_once` / `test_lf_guard_isolates_truncated_tail` / `test_shape_gate_rejects_malformed_event_id[3 参数]`）。
2. **裁定 R-B14-8 (c2) 落地** → `backend/tests/regression/test_learning_events_schema_contract.py` 并入 T7-B 地盘（手册 §一「只 T7」实测 `:67`），本卡把 `test_real_producer_ai_linked_doc_writer` 的提取段改为 PYEOF 形态。**同文件 `:1007` 起行号因此漂移**（T7-C 卡文引 `:1013/:1014/:1017` 钉点，按其卡文以符号名引用；T7-C 只读该文件，无写写冲突）。另登记 `test_skill_portability_lint.py` 的 ai-linked-doc 指纹更新为 `f3673ca9529eaeff1358b50e11b4a9455a12f137cd676a4d1568f5f29b2ae176`（行号 `:4354` → 实测 `:4383`）。
3. **`start-exam-board/SKILL.md:477` 同类子串残留移交**（`seen = any(json.dumps(evid, ensure_ascii=False) in ln for ln in _lines)`），建议下批立卡；**且它同样有「有损解码」面待查**（本卡 round-2 发现的第二条路径，该写点用的是 `decode('utf-8','replace')`）。
4. **backend `services/learning_event_log.py` docstring `:14/:57` 已更新**（第四写者已入锁协议），代码零改动（去 docstring 后 AST 与 PREQ 相同）。
5. **路径更正留痕**：勘探/排批稿写 `backend/app/core/learning_event_log.py` → 实测 `backend/app/services/learning_event_log.py`（手册已按 R-B14-8 更正；T7-C 卡文 §三 禁改行仍写 `core/`，只登记不改他卡）。
6. **口径更正（建议回写协议/设计稿）**：并发门不得用「不同 evid 双写」当判据（`O_APPEND` 使其恒绿）；锁内二次 `open()` 会隐式释放 POSIX 记录锁；`derive:` 前缀使「空 evid」「前导空格」两类形态反例不可达；**新增三条**见本单 §8.2/§8.3/§8.6（屏障精度决定真假门 / 修复后缺陷的可观测性会改变故先红场景未必适合做负控 / `backend/**` 的 ruff 验伪锚须用 F821 不能用 F401）。
7. **写点位置修正**：ai-linked-doc 的账本写点此前嵌在 Step 3 给生成器的 System Prompt 模板 fence 内，已移出为 Step 5.5 独立 bash 块。**建议普查其余 Skill 是否也有「执行动作混进 prompt 模板」的同型问题**。
8. **Codex 四轮存档路径、绑定 SHA、B/H/M/L 计数**：见本单 §4-A(k) 表；存档 `_bmad-output/审查/codex-review-CARD-AILINKED-4TH-WRITER{,-r2,-r3,-r4}.md`（首部三字段齐）。
9. **`tests/unit` 目录级 diff 结果**：base=64 / close=64，无 `>` 行。
10. **本卡引入又自查修掉的两处裸码点**（SKILL.md 2 个 / 测试源码 2 个）——成因是写文件时 JSON 解码把 `\uXXXX` 转义序列变成了真实码点。**建议把「写完含转义序列的文件后必须复查裸码点计数」写进协议**。
