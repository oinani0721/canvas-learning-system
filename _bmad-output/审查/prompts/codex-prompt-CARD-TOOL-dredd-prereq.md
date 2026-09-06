你是独立复核者。任务：核对一份**性能分段测量报告**的归类是否正确、措辞是否比证据宽。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review`
代码树：`67ee147c`。本卡（`CARD-TOOL-dredd-prereq`）**没有改动任何代码**，只新增了 `_bmad-output/` 下的文档与测量存档。

---

## §一 最小读取面（只读这些，不要扩大）

1. `_bmad-output/审查/2026-09-06-Dredd-schemathesis-接CI可行性判据与成本.md` —— 被复核的判据页（全文）
2. `_bmad-output/审查/evidence-dredd-prereq/profile_harness.py` —— 产出下面两份数字的测量脚本（全文，约 320 行）
3. `_bmad-output/审查/evidence-dredd-prereq/profile-20260906T103504.txt` —— run-1 原始输出，**报告块在 `:516-569`，末行 rc 在 `:1218`**（其余是应用日志，可略读）
4. `_bmad-output/审查/evidence-dredd-prereq/profile-both-20260906T104054.txt` —— run-2 原始输出，**主用例报告块 `:516-570`，对照组报告块 `:580-613`，末行 rc 在 `:1262`**
5. `backend/tests/conftest.py:120-206` —— pytest 侧的连接记账与退出码收口
6. `backend/tests/support/live_port_guard.py:157-175` 与 `:1061-1083` —— 豁免面常量与 `is_exempt()`
7. `backend/tests/contract/test_openapi_contract.py:17-43` —— 被对照的生产用例

第三方库源码（`backend/.venv/.../schemathesis/transport/asgi.py`、`transport/requests.py`、`generation/case.py`、`python/asgi.py`）如需核对分段边界可以读，但不必通读。

---

## §二 作者自述（**请独立核对，不要采信**）

判据页的主要结论是：

1. **段级归属已闭合**：单次 `case.call()` 的 30–37s 全部落在 app lifespan 的 startup（中位 19.1s）与 shutdown（中位 12.3s）两段；schemathesis 自身的 hooks + 序列化 + ASGI 请求合计中位 9ms；四段之和与整次墙钟的差额在 0.000193s–0.001099s 之间。
2. **前作 Z7-C 的 7.1s 解释不成立的两个理由**：(a) 本机实测 startup 本来就不是 7.1s；(b) shutdown 段从来没被量过，它占单次调用约四成。
3. **段内归因只是采样证据**，强度低于对账：startup 的应用帧几乎全在 wikilink 图 eager-build；shutdown 指向一个启动期派发的后台任务。作者明确写了「仍未定位的部分」。
4. **门下跑的退出码是 1，不是前作说的 3**，并给了机制解释（哨兵已把拦截结账 ⇒ `unaccounted=0`；兜底分支要求 `status == 0` 而此时已是 1）。
5. **对照组实测**：把 lifespan 换成 no-op 后，单次调用降到中位 0.008s、被拦连接数降到 0、该用例通过。
6. 判据页给了 4 条接 CI 的达标判据（A 耗时 / B 门总账 / C 被测对象等价性 / D 环境可移植），其中 C、D 标为未测。

---

## §三 请按这个重要性顺序核对

### ① 四段计时的归类是否正确 —— 哪一段可能吞了别段？（最重要）

- 读 `profile_harness.py` 的 `_TimedClientCM`、`_install_probes`、`_Timed`，对照 schemathesis 的调用链，判断四段边界是否与源码一一对应。
- 特别检查：是否存在**重叠**（同一段墙钟被计进两段）或**遗漏**（某段耗时掉进未归类却被报成 0）。
- 「四段之和 ≈ 整次墙钟」这个对账，在什么情况下会**同时**掩盖漏计与重复计？如果存在这种情况，请说明。
- 采样线程（`_StackSampler`）用一个模块级变量记录「当前段落」。这个变量在什么条件下会与采样时刻的真实段落不一致？由此产生的归因误差有多大？
- `no_lifespan` 对照组的分段边界是否仍然成立（它的 startup 段量到的是什么）？

### ② 「仍未定位 / 已定位」的措辞是否比证据宽？

- 判据页 §〇 与 §二 用了「段级归属：已定位，且对账闭合」。这个说法被上面的数据支持到什么程度？有没有哪一句把**采样证据**的强度说成了对账证据的强度？
- §二 关于 shutdown 的那段（TLS 读、模型装载、后台任务）里，哪些是观测、哪些是推断？作者是否把推断标成了推断？
- §六 的「本卡未证明什么」7 条是否覆盖了正文里所有超出证据的表述？有遗漏请列出。

### ③ 三问答案（§四）的 `file:line` 是否成立？

逐条核对 §四 引用的每一个行号：`live_port_guard.py:157/159-163/164/253-256/513/1061-1083`、`conftest.py:132-133/141-158/175-204/179/180-182/197-204`、`main.py:163/173/216/276/303/320-334/343/363/392`、`tests/support/lifespan.py:10-17/29-31/63-83`、`.github/workflows/api-spec-sync.yml:330`、`test_openapi_contract.py:27/74-75/76-83`。行号错、或该行不支持作者那句话的，请指出。

### ④ 有没有任何倍数外推或「已定位」滑坡？

- 判据页明确禁止把前作那个 208.70s 的整 session 数字做倍数外推，也禁止把本卡的单次调用数字做倍数外推。全文有没有任何地方实际上做了（包括换成文字叙述的形式，例如「按这个速度全部跑完要多久」）？
- 有没有任何地方把「机制已确认」写成了比证据更强的因果结论？

---

## §四 输出格式

按严重度分节（BLOCKER / HIGH / MEDIUM / LOW），每条：

```
[严重度-序号] 一句话结论
  位置: <文件>:<行号>
  依据: <你读到的原文 / 数据，逐字引用>
  为什么这是问题: <一句话>
  建议: <改成什么>
```

无问题的分节写「无」。最后**必须**单独起一行：

```
BLOCKER/HIGH 清零：是/否
```

---

## §五 边界

- **只读复核，不要运行任何命令、不要修改任何文件。**
- 本卡不涉及 CI 变更：`.github/workflows/api-spec-sync.yml` 的 `contract-test` job 仍是 `if: false`，本卡没有改它。
- 不需要评价「该不该把这个测试接进 CI」这个产品决策本身——那是别的卡的事。你的任务是核对本页的**测量与措辞**是否站得住。
- 如果你认为某条结论需要额外证据才能成立，请直接说「证据不足」并写清缺什么，不要替作者补论证。
