# 独立复核请求 — CARD-DEBT-1（全量测试超时根因与 timeout 落地）· **round-2**

> **这是第 2 轮。** 第 1 轮（绑 `f595562e`）你给了 BLOCKER 0 / HIGH 1 / MEDIUM 6。
> 我对**每一条**都做了处置，逐条写在下面 §②-bis。请重点核：
> (a) 那条 HIGH 的整改是否到位（我没有改 `timeout_method`，而是收窄了主张与覆盖面声明）；
> (b) 新加的判据层有没有引入**新的**空洞或过强主张；
> (c) 我对 MEDIUM 的「登记不改」处置是否有哪一条其实应该改。

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

**请读的东西，仅此清单：**

- `git --no-pager diff --no-color a7341ca4ebb6d7f2a12ed35ffe643df4f62d7bad bd99c49543b758ad57ca99392886b2c374e69c0a -- . ':(exclude)_bmad-output'`
  （本卡全部代码改动面；`a7341ca4` 是开工时的 HEAD = 前一张卡 P9-A 的末 commit，
  `bd99c495` 是本卡唯一 commit = 当前 HEAD。实测该 diff 为 **3 files changed, 496 insertions(+), 0 deletions(-)**）
- `backend/pytest.ini` 全文（41 行以后是本卡新增段）
- `backend/tests/conftest.py` 的 `:1-60`（门的装载顺序与 import 面）与**新增 hook 全段**
- `backend/tests/support/live_port_guard.py` 的 `:150-215`（受拦端口与豁免常量）
  与 `:1564-1587`（`is_exempt` 的相对化口径）—— 这个文件本卡零改动，只作对照
- `backend/tests/unit/test_debt1_default_gate.py` 全文（本卡新增的承重行为门）
- `_bmad-output/审查/evidence-debt1/hang-census.md`（挂起清单）
- `_bmad-output/审查/evidence-debt1/` 下本卡引用的存档（文件名在 hang-census.md 与
  验收单里逐条写死，不用通配）。**round-1 你指出「负控存档名称尚未提供」—— 这里补全**：
  - `negctl-1-20260919T003755.txt`（段①：删掉 hook）
  - `negctl-2-20260919T004000.txt`（段②：删掉 ini 的 `timeout = 300` 一行）
  - `negctl-3-mapping-20260919T003330.txt`（段③：映射注入 `{"regression": "real_neo4j"}`）
  - `negctl-4-mismap-20260919T004504.txt`（段④：映射注入 `{"unit": "contract"}`）
  - `negctl-5-getdefault-20260919T004604.txt`（段⑤：`.get(first, "contract")`）
  - `gate-after-r3-20260919T004239.txt`（整改后的门，5 passed）
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
   默认 false，计时罩住 setup+call+teardown 整个 item，所以我按 item 总墙钟标定而不是
   按 call 行。卡文的「≥3 倍」= 667s 超出卡文自己给的上限 300，我取了上限 300，
   余量只有约 1.35 倍——这一点我写进了 ini 注释与验收单的未证明清单。
4. **census 每条结论都来自存档**，尤其「contract 目录级挂起**不是** pact provider 等真服务」
   这一条：`tests/contract/test_pact_provider.py:35-40` 的 `PACT_DIR` 指向一个**不存在**的
   目录（`canvas-progress-tracker/`），`:43` 的 `PACT_BROKER_URL` 默认空串，于是 `:298` 的
   `skipif` 把整个验证类跳过，永远走不到 `:283` 的 provider URL。我另外单跑了两个探针
   （`census-contract-schemathesis-*.txt` / `census-contract-pact-*.txt`）来给这条结论落证据。
5. **根 conftest 零删改既有行**：只在文件末尾追加，
   `git --no-pager diff --no-color a7341ca4 bd99c495 -- backend/tests/conftest.py | grep -c '^-[^-]'` = 0。
6. **两段负控各红在我指定的那条断言上**：段①（删 hook）→ 2 failed / 3 passed，
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
