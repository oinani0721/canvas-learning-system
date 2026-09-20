# 独立复核请求 — CARD-DEBT-1（全量测试超时根因与 timeout 落地）· **round-3（重发）**

> **这是第 3 轮。** round-1（绑 `HEAD`）= BLOCKER 0 / HIGH 1 / MEDIUM 6；
> round-2（绑 `HEAD`）= **BLOCKER 0 / HIGH 0** / MEDIUM 8。
> 你在 round-2 指出我 round-1 整改**新引入**的两处空洞 + 一处事实写错，我全部改了，
> 逐条写在 §②-ter。请重点核：
> (a) 这三处改到位没有，有没有**又**引入新的空洞；
> (b) 收窄后的措辞是否仍有比证据强的地方；
> (c) 你 round-2 说「负控存档未提供源码/还原哈希，不能独立确认还原逐字节一致」——
>     本轮我把还原机制写在下面，请判断它够不够。

---

## ⓪ 绑定口径与「自本 prompt 初稿（2026-09-19 04:22）以来的变更」——**请先读这一节**

**本轮的审查面 = 三份代码文件在当前 HEAD 上的内容**：
`backend/pytest.ini` · `backend/tests/conftest.py` · `backend/tests/unit/test_debt1_default_gate.py`。

⛔ **不要用 `<审SHA>..HEAD` 做全树 diff**：本分支上夹着**另一张卡**的 commit
`d06f7127`（CARD-G4-13，改 `backend/scripts/**` 与 `backend/tests/regression/**`），
按卡批次协议 §1「串行车道按**本卡 diff 面**判」，只看上面这三份文件。

**代码 commit 唯一 = `47c94bab`。** 此后本卡又有四个 commit，**全部只动 `_bmad-output`
与注释/docstring**：

| commit | 性质 |
|---|---|
| `d346e6aa` / `e519924e` / `0ac28596` | 纯 `_bmad-output`（代码面 diff 为空） |
| `9d270cdf` | **D-32 纯注释/docstring 整改**（见下），可执行行零改动 |

`9d270cdf` 的等价已证，**请你独立复核这个证明**：
- `pytest.ini`：非注释行 `diff` 为空；configparser 解出的有效配置 **9 键全同**
  （`timeout=300` / `timeout_method=signal` / `addopts='\n-v\n--tb=short'`）；非注释改动行 = 0。
- 两份 `.py`：去 docstring 后 `ast.dump` 与 `47c94bab` **相同**（验伪锚 `x=1` vs `x=2` → False）。
- 整改后复跑门：**5 passed / 收集 5 / rc=0 / W4 `blocked=0`**
  （`evidence-debt1/gate-after-d32-20260919T061825.txt`）。

**round-3 之前已做过一轮「绑最终 HEAD 的独立对抗审查」**（4 路镜头 + 逐条复算），
裁定书 `_bmad-output/审查/CARD-DEBT-1-人审裁定-20260919.md`。
⛔ 它**不充当 Codex 轮次**，放在这里是为了让你**不必重复**已确认的面，并请你
**对抗性地复核它的结论**。它产出：

- **1 条 HIGH（已实证，声明侧已整改、行为侧登记 → DEBT-3）**：
  `timeout_func_only=False` 的闹钟**只上一次弦**；任一相失败 →
  `check_interactive_exception`（无 pdb 闸门）→ `pytest_exception_interact` →
  pytest-timeout 调 `cancel_timeout()` 拆掉 SIGALRM ⇒ **该 item 的 teardown 完全裸跑**。
  A/B 实测（`--timeout=1` + 20s finalizer）：A 先 `assert False` → 墙钟 **21s**、
  `Timeout` 字样 **0**；B 对照 `assert True` → 墙钟 **2s**、`Failed: Timeout (>1.0s)`。
- **7 条 MEDIUM（全部登记不阻断）**：AST 三层只看字面量（原赋值后追加
  `dir_to_marker.update({...})` 可绕过全部四道断言）· `_run_pytest` 未清 `PYTEST_TIMEOUT`
  （插件里 env **优先于 ini**）· 第①层缺「`-m` 表达式有选中能力」的正控 ·
  `pytest-timeout` **不在 `backend/requirements.txt`** ⇒ CI 零超时保护 ·
  `stop-test-runner.js` 的 `-m "not integration"` 选择集被本卡静默改小（62 个无 marker 文件）·
  §2.3 批级通告行没落到共享手册 · 承重存档未落 shasum。
- **8 条文档失实已改**（含：A18 原引的负控存档产于 `f595562e` 时代；「本卡 commit 数 = 1」实为多个；
  A19 写 `PREV HEAD` 在真实 HEAD 上不成立）。

**请你重点打的方向**：上面这些**处置**（尤其「只改声明不改行为」是否可接受、
D-32 等价证明是否严密、7 条 MEDIUM 里有没有实际是 HIGH 的）；以及这三份文件里
**上述审查没覆盖到的面**。

---

## ②-ter round-2 逐条处置

| round-2 条目 | 处置 |
|---|---|
| AST 抽取器对非 `ast.Constant` 键值**静默过滤** | 改成**拒绝**：解析不了的条目当场断言失败。负控 `negctl-6-astconcat-20260919T005706.txt` 实测：注入 `"regression": "real_" + "neo4j"` 后，**旧写法抽取结果仍是三条**（漏项可见），新写法红在「静态解析不了的条目」 |
| 第 ④ 层漏调 `_assert_deselected_not_broken()`；该函数 rc 用黑名单 | 第 ④ 层补上守卫；rc 判据改为**正面白名单** `{0, 5}` |
| signal 例外③ 异常类型写错 | **我写错了**：实测 `Failed.__mro__` = `Failed → OutcomeException → BaseException`，`issubclass(Failed, Exception)` = False ⇒ 普通 `except Exception` 接不住；能吞掉它的是 `except BaseException`，CPython `asyncio/events.py::Handle._run` 捕获的正是它。已改准，并补「这三类本卡都没有实测，是读源码得到的边界声明」 |
| census 瞬时栈/截断输出/item 超时写得过强 | 改成「**超时那一刻**栈在 markdown 解析里」，并明写不能推出「300 秒全耗在解析上」「`grep 7691 = 0` 只说明已打印的输出里没有，进程是被砍断的」 |
| npm 红「与本卡无关、已钉死」未经对照证明 | **撤回免责措辞**，改成「可证的只有：改前/改后目录级都绿，只有全量跑出现新增红；**原因未定**」 |
| ini「缺插件只警告」未同步限定 | 改为「**在本卡实测过的调用方式下**只警告」+ 写明 `-o strict_config=true` / `-W error::…` 可失败 + `--strict-markers` 不管未知 ini 键 |
| **我送审的数字不实**（prompt 写段① = 2 failed / 3 passed，存档是 3 failed / 2 passed） | **认**。整改后第 ③ 条在段① 下也红（红在 AST 的「应恰 1 个」前置断言 = 取证前提没了），验收单与 docstring 都写了，但忘了同步进 prompt。本轮数字为**当前 HEAD 重跑**的实测值：段① `negctl-1-20260919T005822.txt` = **3 failed / 2 passed**，段② `negctl-2-20260919T005942.txt` = **1 failed / 4 passed** |
| 软链收集后改指向 | 继续登记不改（你已同意），并把「语义中性」限定为**路径保持稳定** |

**还原机制（回答你 round-2 最后那句）**：六段负控都由同一个 scratchpad 脚本驱动，
形状是 `( trap "git show HEAD:<abs path> > <abs path>" EXIT; <注入>; <跑门> )`，
跑前跑后各 `shasum -a 256` 一次并要求逐字相同，之后 `git status --porcelain` 必须为空。
脚本全文贴在验收单 §六。脚本首部还有**前置守卫**：工作树非空、或 HEAD 里没有本卡改动时
**拒绝执行**（实测拦过一次）—— 因为 `git show HEAD:` 还原在未 commit 时会吞掉未提交改动。

[BATCH-2026-09-18-第十五批 / CARD-DEBT-1] · 车道 `card-p9-testinfra` · 分支 `card/p9-testinfra`

---

## ① 背景与最小读取面（⛔ 只读这些，不要扩大到别的目录）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra`

这张卡要解决的问题：这个后端测试套件的全量跑法一直会挂死，而「挂死」和「跑完了都过」
在存档里看不出区别——于是「跑过了」这三个字不可信。本卡做三件事：

1. 往共享 venv 装 `pytest-timeout==2.4.0`（经批级通告 + 主 session 批准），
   在 `backend/pytest.ini` 加 `timeout` / `timeout_method` 两个键；
2. 在根 conftest `backend/tests/conftest.py` **文件末尾新增一个**
   `pytest_collection_modifyitems`，按一级目录给 `tests/contract` / `tests/integration` /
   `tests/e2e` 自动补同名 marker，使「默认门」
   `-m "not integration and not e2e and not contract"` 真的选得干净；
3. 实测定位挂起点，产出挂起清单 `hang-census.md`。

⛔ 本卡**不改** `backend/app/**`、不改任何测试断言、不删不 skip 任何用例、不改 CI、
不改 `lefthook.yml` / `requirements.txt` / `pyproject.toml` / `setup.cfg` /
`backend/tests/unit/conftest.py` / `backend/tests/support/live_port_guard.py`。

⚠️ 本 prompt **不写死 SHA**，一律用 `HEAD` —— 把 commit 自己的 SHA 写进该 commit 收录的文件里是个自指循环（每次 amend 都会改 SHA）。
本轮的确切绑定 SHA 记在**跑完之后**才写的存档首部里。

**请读的东西，仅此清单：**

- `git --no-pager diff --no-color HEAD HEAD -- . ':(exclude)_bmad-output'`
  （本卡全部代码改动面；`HEAD` 是开工时的 HEAD = 前一张卡 P9-A 的末 commit，
  当前 HEAD 就是本卡唯一 commit。实测该 diff 为 **3 files changed, 496 insertions(+), 0 deletions(-)**）
- `backend/pytest.ini` 全文（41 行以后是本卡新增段）
- `backend/tests/conftest.py` 的 `:1-60`（门的装载顺序与 import 面）与**新增 hook 全段**
- `backend/tests/support/live_port_guard.py` 的 `:150-215`（受拦端口与豁免常量）
  与 `:1564-1587`（`is_exempt` 的相对化口径）—— 这个文件本卡零改动，只作对照
- `backend/tests/unit/test_debt1_default_gate.py` 全文（本卡新增的承重行为门）
- `_bmad-output/审查/evidence-debt1/hang-census.md`（挂起清单）
- `_bmad-output/审查/evidence-debt1/` 下本卡引用的存档（文件名在 hang-census.md 与
  验收单里逐条写死，不用通配）。**round-1 你指出「负控存档名称尚未提供」—— 这里补全**：
  - `negctl-1-20260919T041430.txt`（段①：删掉 hook）
  - `negctl-2-20260919T041529.txt`（段②：删掉 ini 的 `timeout = 300` 一行）
  - ~~`negctl-3-mapping-20260919T003330.txt`~~ —— ⚠️ **已被取代**：它产于
    `set(mapping) == EXPECTED_DIRS` 那条断言**加进去之前**，红点已不成立。
    终态三段见 `negctl-A-20260919T055804.txt`（加第 4 键 → 红在 `set(mapping)`）/
    `negctl-B-20260919T060022.txt`（`contract→real_neo4j`，键集不变 → 红在**第①层**）/
    `negctl-C-20260919T060226.txt`（`e2e→contract`，键集不变 → 红在第③层）。
    ⇒ **第②层在当前顺序下不可达**（125 组合枚举：L1 75 / L3 49 / 全绿 1 / **L2 0**），
    已如实降级为纵深防御并登记（不在本卡改判据顺序）。
  - `negctl-4-mismap-20260919T004504.txt`（段④：映射注入 `{"unit": "contract"}`）
  - `negctl-5-getdefault-r2-20260919T041139.txt`（段⑤：`.get(first, "contract")`，复跑）
  - `negctl-6-astconcat-20260919T005706.txt`（段⑥：`"regression": "real_" + "neo4j"` 拼接）
  - `negctl-7-emptymap-20260919T041026.txt`（段⑦：映射清空 `{}`）
  - `negctl-8-rename-20260919T041026.txt`（段⑧：映射变量改名）
  - `negctl-9-spread-r2-20260919T041330.txt`（段⑨：`{**BASE, ...}` 解包）
  - `gate-after-r5-20260919T040822.txt`（最终门，5 passed）
- `_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md` 的 `:56`（DEBT-1 行）
- `.claude/rules/card-batch-protocol.md` 的 `§2.2`（其中 `tests/contract` 目录级挂起那一条，本卡对它提出措辞更正）

---

## ② 作者自述 —— 以下每一条请独立核对，不要采信我的结论

1. **自动打标恰三条，且对 W4 语义中性**：映射是
   `{"contract": "contract", "integration": "integration", "e2e": "e2e"}`，
   不含 `real_neo4j`。`live_port_guard.EXEMPT_MARKERS` = {integration, e2e, real_neo4j}
   是「只记不拦」名单，`EXEMPT_PATH_PREFIXES` = ("integration", "e2e") 是同一件事的
   路径侧；本卡打的 integration/e2e 只落在路径上**早已豁免**的那两个目录里，
   打的 contract 不在豁免名单里。我据此声称 advisory 面没有变宽。
2. **`addopts` 未动**：`backend/pytest.ini:19-21` 逐字不变，`-m` 默认门**没有**写进 addopts。
3. **timeout 值有 durations 存档支撑**：N=300 取自开工那次 `tests/unit --durations=25`
   （存档 `unit-open-20260918T192142.txt`）。最慢的**通过**项是
   `test_study_question_deep_mode.py::test_mode_answer_keeps_top_k_20_and_hard_cap_15`，
   teardown 217.38s + call 5.02s，item 总墙钟约 222.4s。因为 `timeout_func_only` 保持
   默认 false，计时罩住 setup+call+teardown 整个 item ——
   ⚠️ **更正：这只对「每一相都通过」的 item 成立**（见 ⓪ 的 HIGH，A/B 已实证；
   ini 注释已收窄并补为「第四类例外」）。标定口径不受影响：我按 item 总墙钟标定而不是
   按 call 行。卡文的「≥3 倍」= 667s 超出卡文自己给的上限 300，我取了上限 300，
   余量只有约 1.35 倍——这一点我写进了 ini 注释与验收单的未证明清单。
4. **census 每条结论都来自存档**，尤其「contract 目录级挂起**不是** pact provider 等真服务」
   这一条：`tests/contract/test_pact_provider.py:35-40` 的 `PACT_DIR` 指向一个**不存在**的
   目录（`canvas-progress-tracker/`），`:43` 的 `PACT_BROKER_URL` 默认空串，于是 `:298` 的
   `skipif` 把整个验证类跳过，永远走不到 `:283` 的 provider URL。我另外单跑了两个探针
   （`census-contract-schemathesis-*.txt` / `census-contract-pact-*.txt`）来给这条结论落证据。
5. **根 conftest 零删改既有行**：只在文件末尾追加，
   `git --no-pager diff --no-color a7341ca4 bd99c495 -- backend/tests/conftest.py | grep -c '^-[^-]'` = 0。
6. **两段负控各红在我指定的那条断言上**：段①（删 hook）→ **3 failed / 2 passed**
   （⚠️ 本行初稿写「2 failed / 3 passed」，与本文件 §②-ter 首行自述矛盾，已更正；
   终态存档 `negctl-1-20260919T041430.txt`，绑 `47c94bab` 之后的代码），
   红的是 `test_contract_dir_autotagged`（红在 `deselected` 断言）与 `test_integration_e2e_dir_autotagged`；
   段②（删 ini 的 `timeout = 300` 一行）→ 1 failed / 4 passed，红的是 `test_ini_timeout_header`。
   被我标成**控制组**的是第 3 条（段①下仍绿）与第 5 条（段②下仍绿）。
   还原用 `git show HEAD:<path> > <path>`，跑后 sha256 与 HEAD 逐字节相同。
7. **默认门实跑 47 分 33 秒，未达 ≤20 分钟目标**，我没有把它写成达标；
   `deselected = 196` 与 `tests/contract` 收集数 196 相等。

---

## ②-bis round-1 逐条处置（请独立核对我改没改到点子上）

| 你 round-1 的条目 | 我的处置 |
|---|---|
| **HIGH** `signal` 只抛异常、不保证 item/进程按时结束，asyncio 输入下甚至可能被吞掉 | **接受，不改 `timeout_method`**（换 `thread` 会 `os._exit` 截断存档，与本卡「产出一份读得出根因的清单」直接冲突）。改的是**主张范围**：`backend/pytest.ini` 新增「signal 保证的到底是什么」一段 + 你点名的三类例外；第 5 条门的 docstring 明写「证明什么 / 不证明什么」；模块 docstring 去掉「杀掉」；验收单「本卡未证明什么」第 5 条重写为三类例外 |
| **MEDIUM** 「映射加第四目录就会红」不成立 | **接受，加结构不变量**：凡映到 `EXEMPT_MARKERS` 的目录必须已在 `EXEMPT_PATH_PREFIXES`。负控 `negctl-3-mapping-…:18` 实测红 |
| **MEDIUM** 收集出错且无 nodeid 会被读成「成功排除所有用例」 | **接受，加 `_assert_deselected_not_broken()`**：同一次输出里要求 `deselected` 正面痕迹 + 排除 `INTERNALERROR` / 收集错误 + rc ∉ {3,4} |
| **MEDIUM** census 结论强于存档 | **接受，其中一条是我的事实错误**：我把 contract 的慢笼统归给「W4 连接重试」；实测 schemathesis 探针的超时栈是 **obsidiantools 建 vault 图 + BeautifulSoup/lxml**，该存档 `grep -c '7691'` = **0**。已改写 C-2b/C-4/§一.2②/§五，`blocked=19` 明确归给 `test_health_contract` |
| **MEDIUM** `196 = 196` 是数量不是身份 | **接受**，改写为数量判据并写明「没有导出同次 deselected nodeid 清单逐条比对」 |
| **MEDIUM** 「只警告不失败」应限定默认配置 | **接受**，写明 `-o strict_config=true` / `-W error::…` 下可失败，且 `--strict-markers` 不管未知 ini 键 |
| **MEDIUM** 软链收集后改指向 | **登记不改**（MEDIUM 按协议登记不阻断；你自陈未发现实例、未复现；修它要动 W4 运行期判定 = 别的卡的面）|

**另外，round-1 之后我自己又补了两层判据**（一轮内部复核发现，⛔ 那轮无存档、不作依据）：
`" or ".join(sorted(EXEMPT_MARKERS))` 恰好**不含 `contract`**，所以「`contract` 被打到
`tests/contract` 之外」这条路径原先零覆盖 —— 而它的后果比扩大 advisory 面更重：
默认门会把那个目录**静默** deselect（本门文件自己就在 `tests/unit` 里，会一起消失）。
于是第 3 条用例扩成**四层**，各配负控（见上面补全的存档名）。请核这四层有没有新的空洞。

## ②-quater round-2 之后我又自己找出并修掉的三处（请重点核有没有改坏）

round-3 第一次调用因你方配额限流返回 0 字节，这段时间我自己跑了一轮对抗复核，
抓出**三条都是我 round-2 整改自己引入的**缺陷，已修 + 各配负控：

1. **`ast.dump(None)` 的 TypeError**：`{**other}` 解包时 `d.keys` 里是 `None`，
   而我那条声称「管解包」的断言会先崩在 dump 上。已加 `_show()` 渲染。负控⑨。
2. **守卫插在不变量之前**：`.get(first,"contract")` 变异下是**全被选中**，
   而守卫文案说「不能排除收集塌了」—— 与事实相反。三处统一改成
   **先断言不变量、后上守卫**。负控⑤复跑。
3. **`SUBPROCESS_TIMEOUT_S` 120 × 4 = 480 > ini 的 300**，负载下这道门会撞上
   它自己装的超时。改成 60（4 × 60 = 240 < 300）。

另两处换了修法：`_hook_dir_marker_map()` 改为**按变量名 `dir_to_marker` 锚定赋值**
（不再是「函数体内恰好一个 dict」），并加 `set(mapping) == {"contract","integration","e2e"}`
作为第 2、3 层「期望空集」判据的**非空前提**。负控⑦⑧。

⚠️ 这一轮我的负控自己也犯过一次错，如实说：负控⑨ 首版用文本锚注入，
`str.replace(...,1)` 换掉的是 **docstring 里那处**示例（`conftest.py:1060`），
真正的赋值行 `:1079` 没被碰 —— 门「没红」看起来像判据漏了，其实是注入打歪了。
改用赋值行作锚后如期红。

## ③ 请优先回答的问题（按重要性排序）

⓪ **自动打标有没有让 `tests/integration` / `tests/e2e` 之外的任何用例拿到
   `integration` / `e2e` / `real_neo4j` 中的任何一个 marker？** 也就是 W4 的 advisory 面
   有没有被这次改动扩大。如果有**门未覆盖的路径**能做到这一点（例如符号链接、
   `rootdir` 之外的用例、`conftest` 加载顺序导致 hook 不执行、或别处还有一个
   `pytest_collection_modifyitems` 与它叠加），请指出那条路径。

① `timeout_method = signal` 在 `asyncio_mode = auto` + anyio portal 线程的组合下，
   会不会把「超时」显示成**别的失败**（= 假归因），或者对 C 级阻塞根本杀不掉
   （= 门绿了但东西还挂着）？请说明在什么**对照输入**下这两种情况会发生。

② `hang-census.md` 里每一条的根因，是从存档读出来的还是推断出来的？
   特别是「不是 pact」那一条，以及「contract 目录慢在 lifespan 对受拦端口的连接重试上」
   这一条——如果证据只支持更弱的说法，请指出该弱到什么程度。

③ 默认门的 `-m "not integration and not e2e and not contract"` 有没有让**本来在跑的用例
   静默消失**？`deselected` 数与 `tests/contract` 的收集数是否对得上？
   如果有用例既不在 contract 目录、又被这条表达式排除掉了，请指出是哪一条以及为什么。

④ 新加的两个 ini 键，在**没装这个插件**的 venv（主仓 venv、CI）里是警告还是失败？
   验收单里那句「只警告不致错」有没有如实写、依据够不够（我给的依据是全仓没有
   `--strict-config` / `--strict-markers`）。

⑤ 两段**负控输入**（段① 删掉 hook、段② 删掉 ini 的 `timeout` 行）是不是各自红在了
   我指定的那条断言上？被我标成**控制组**（删了也不该红）的那两条，标注是否属实？
   有没有哪一条断言其实在**未被拦下的输入**上也会绿？

---

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- 一句话结论
- `file:line`（精确到行）
- 一句复现思路，措辞请用「**负控输入** / **对照输入** / **未被拦下的输入** / **门未覆盖的路径**」

如果某条只是风格或偏好，请标 LOW 并说明它不影响正确性。

---

## ⑤ 边界

- **只读**，不要修改任何文件。
- 不要连接任何数据库、不要起容器、不要跑需要网络的东西。
- 不要评审 DEBT-2（xdist 收集不确定性）、DEBT-3（挂起用例本身怎么修）、
  DEBT-4（CI 与依赖声明）的面——本卡对它们只登记不改。
- 不要评审 `backend/tests/support/live_port_guard.py` 的**改动**：那是上一张卡 P9-A 的面，
  本卡对它零改动，只把它当对照常量读。
- 不要评审 `backend/app/**`：本卡不触它。
