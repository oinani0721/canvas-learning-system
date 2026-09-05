# UAT — CARD-TOOL-dredd-decide「Dredd 复活 / 退役裁决卡」

> 批次 `[BATCH-2026-09-05-第十一批 / CARD-TOOL-dredd-decide]` · 车道 `card/z7-tool`
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十一批-goals/Z7-C.md`
> commit：`7b8383d2`（裁决页，只含此页）+ `e6f9aebc`（API 修复 + 版本口径 + 页 §六 补记）
> 基线 `46ed18f1`（Z7-B 末）· 裁决页 `_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md`
> **本卡未改任何 workflow**（`test.yml` / `api-spec-sync.yml` 零字节改动）· 未 push

---

## 4-B 用户可感（先看这段）

**这次做了什么，对你意味着什么：**

1. **一个坏了很久的自动检查，查清楚了它到底怎么坏的。** 那个本该在每次提交时
   替你核对「接口说明书和真实接口对不对得上」的检查，四个月来一次都没通过过。
   本卡把两个候选方案都摸到底了，结论写成了一页可以回头查的裁决页。

2. **原本准备顶上去的那个替代品，其实也是坏的——而且从来没人发现。**
   它写的是上一代工具的用法。**但它并没有像我一开始以为的那样"装哪个版本都跑不起来"**
   ——外部复核推翻了这个说法，实测它在当前环境下那部分是正常的。真正的问题在下面第 3 条。
   本卡顺手把那处写法改成了不依赖隐式前提的形式（属加固，不是修 bug）。

3. **它现在接不上去，有两个各自独立的原因。** 一是**太慢**：本机跑**一个**接口的
   检查就花了三分半，而直接调用同一个接口只要零点几秒。二是**它启动时会去连一个
   本不该连的数据库**，而仓库里已有的安全检查会因此判它不合格——这一条**不是把速度
   修快就能解决的**。所以这次没有把它接进自动流程。

4. **也因此没有把旧的那个删掉。** 你当初同意"删旧的、换新的"，前提是新的能顶上；
   前提不成立，就先不删。（说明一句：旧的那个本来就是停用状态，删了并不会让现在的
   检查变少，删掉的其实是**日后想恢复它的那份现成材料**。）

**你需要做什么**：无变化。

> 📌 **与卡文模板的一处如实偏离**：卡文规定 4-B 写「无变化（决定一个坏了很久的自动
> 检查是修还是换掉，**并把换的那个真接上**）」。括号后半句描述的是原裁决（乙）的
> 预期结果，而实测推翻前提、你重裁为「不退役」之后，**那半句没有发生**。
> 这里按事实写，不按模板写。

---

## 4-A 技术验收

### 一 裁判命令逐条（卡文 §二）

| # | 裁判 | 结果 |
|---|---|---|
| 1 | `python -c "import schemathesis; print(__version__); print(hasattr(...,'openapi'))"` | **4.14.3** / `openapi` = **True** / `openapi.from_asgi` = **True** / 顶层 `from_asgi` = **False** |
| 2 | `pytest tests/contract/test_openapi_contract.py`（env 逐字用 `test.yml:119-121`） | **未能变绿**，见 §三——原因不是环境，是被测文件与运行时长，实测证据在 §三 |
| 3 | 17 文件白名单 + 本文件的可加性验证 | **未执行**（依赖裁判 2 先绿；用户重裁为不落 (b)） |
| 4 | `check-openapi-drift.py --snapshot openapi.json` | **`DRIFT: none (paths=193 schemas=353)`**，快照未手改 |
| 5 | `contract-test` job 数 / `test.yml` 是否提及 / YAML 可解析 | job = **1**（仍在，仍 `if: false` ×2）；`test.yml` 提及 `test_openapi_contract` = **0**；两个 workflow YAML 均可解析 —— **与所选方案（不退役、不动 CI）一致** |

---

### 二 (a) 裁决：抄录 + 前提推翻后的重裁

**原裁决（用户 2026-09-05，裁「3 处都按默认」，主 session 代填）**：

> **Dredd 处置 = 乙**（正式退役 + schemathesis 接进 `test.yml` 白名单并配
> `python -c 'import schemathesis'` 硬前置）。CI/CD 变更仍按纪律：车道落 commit
> 不 push，合并前用户逐项批 diff。
>
> 出处：`…/2026-09-05-第十一批开跑手册-7车道17卡.md:301`（`:326` 记本批 3 处均按默认）

**重裁（同日，前提被实测推翻后）**：

> **本卡只落已完成的、不依赖该前提的部分，不退役。** 即保留 `contract-test` job
> 与 `dredd-hooks.js`，不动 `test.yml`；把「schemathesis 每次调用 20–50s」立新卡。

裁决页（`7b8383d2` 提交，`e6f9aebc` 补 §六）记录了三个选项、各自的实测前提、
以及推翻过程。

---

### 三 为什么 (b) 没有落 —— 实测证据（经两轮外审逐条收窄后）

#### 3.1 「那个替代品坏了」——**这条我说错了两次，最终撤回**

> ### ⛔ 自我更正（我的初版断言被自己的证伪实验推翻）
>
> 我最初写的是「它把 3.x 和 4.x 两套 API 混写在一起，**任何版本都跑不通**，
> **从未被真正执行过**」。**这是错的**，并且已经写进了 `e6f9aebc` 的 commit message
> 与裁决页初稿（两处都已在后续更正）。
>
> 我用一个**一次性 venv**（Python 3.13，绝不碰共享 venv）逐版本实测后推翻了它。
> 之所以做这个实验，是因为我在验收单「本卡未证明什么」里把这条标成了
> 「未验证全版本区间，需要额外证据」——**去把自己标记的洞补上，结果补出了反例**。

逐版本实测（一次性 venv，`pip install schemathesis==<v>` 后直接 `hasattr`）：

| 版本 | `openapi.from_asgi` | 顶层 `from_asgi` | `checks.*_conformance` ×4 | `checks.load_all_checks` |
|---|---|---|---|---|
| 3.19.0 | **无法测**——该版本 import 时 `ModuleNotFoundError: No module named 'cgi'`（`cgi` 在 Python 3.13 已移除） | | | |
| 3.25.0 | ✅ | ✅ | ✅ | ❌ |
| 3.30.0 | ✅ | ✅ | ✅ | ❌ |
| 3.39.0 | ✅ | ✅ | ✅ | ❌ |
| **4.14.3（本机已装）** | ✅ | ❌ | ❌ **四个全无** | ✅ |

> ### ⛔ 第二次自我更正（Codex round-1 #1 又打掉了我一半，源码 + 实测都已核）
>
> 上面那次更正之后，我仍然写着「4.x 上**每个用例都 `AttributeError`**」。
> **这一半也是错的。** Codex 指出 `schemathesis.checks` 有**动态 `__getattr__`**，
> 且**标准 pytest 插件在收集期就会加载检查**。我读了源码确认：
>
> ```
> schemathesis/pytest/plugin.py:129  def _gen_items(self, result):     # @schema.parametrize() 的取件器
> schemathesis/pytest/plugin.py:146      load_all_checks()             # <- 收集期就调用
> ```
>
> 即在**真 pytest 入口**下，四个模块属性在任何测试体执行前就已可用。
> 我之所以看到 `AttributeError`，是因为我用了一个**绕过 pytest 插件的独立探针**
> （`python - <<PY` 里手搓 `@given`）——**我把探针的产物当成了被测物的缺陷**。
>
> **实测坐实（两次，取到了明确拒因）**：把改前的版本（`git show 46ed18f1:…`）原样放回
> `backend/tests/contract/` 用真 pytest 跑一个 operation：
>
> ```
> E   hypothesis.errors.DeadlineExceeded: Test took 20857.69ms, which exceeds
>     the deadline of 10000.00ms.
>     (note: 8 other explicit examples also failed with this error)
> 1 failed, 186 deselected in 218.91s (0:03:38)
> ```
>
> **拒因是 `DeadlineExceeded`，不是 `AttributeError`。** 而且它跑满了 9 个 example
> ——每个都真的发出了调用。属性那一关根本没拦住它。
>
> ⇒ **结论：改前的代码在当前环境下的检查项查找是正常的。**
>
> ⇒ **本卡对 `test_openapi_contract.py` 的改动，不是修一个"会炸"的 bug**，
> 而是一次**防御性加固**：不再依赖"插件恰好已经加载过检查"这个隐式前提。
> 它是好的（Codex 也确认 `get_by_names` 取到的与模块属性**是同一批对象**），
> 但我给它写的理由（"任何版本都跑不通 / 每个用例都 AttributeError"）**两遍都写宽了**。

**经两轮更正后仍然成立的口径**：

- 该文件在 **3.25 / 3.30 / 3.39 上两套 API 并存**；在 4.14.3 上，模块属性经
  动态 `__getattr__` + 插件收集期的 `load_all_checks()` 同样可用。
  ⇒ **它不是"任何版本都跑不通"，也不是"每个用例都 AttributeError"。**
- 本卡改后的写法（`load_all_checks()` + `CHECKS.get_by_names`）在 3.39.0 **不存在**，
  ⇒ 是 **4.x 专用**，所以把 pin 抬到 `>=4.0` 是**必要**的（否则改后的代码在 3.x 上会炸）。
- 「从未被真正执行过」**无法证明**，已撤回。

⇒ **(b) 不落地的理由与 API 无关。** 它有**两个互相独立**的未满足条件：
**耗时**（§3.3）与**启动期的端口/存储隔离**（§3.5）。

#### 3.2 `importorskip` 掩盖了它，假绿机制比"静默 skip"更具体

最小演示（独立小文件，放在 scratchpad，不入仓库）：

| 情形 | 结果 | rc | 阶段 |
|---|---|---|---|
| 模块**不存在** | `1 skipped` | **5**（pytest 的「没收集到测试」） | 收集期 `importorskip` |
| 模块在但**测试体内**属性取不到 | `1 failed` | **1** | 执行期 |

> **口径限定（Codex round-1 #5 指出，采纳）**：
> - 上表第二行是我构造的**测试体内**属性访问，所以是执行期失败、rc=1。
>   若属性访问发生在**模块加载期**，那是**收集错误 → rc=2**，不是 1。两者要分开说。
> - 「**无声吸收**」说得太满：skip 仍然出现在统计与 JUnit 报告里。准确说法是
>   **「它不会阻止这一步成功」**。
> - 「放进 17 文件白名单后整步 rc=0」是**推理不是实测**——我没有真的把它放进白名单跑过。

即：rc=5 单独跑会让 CI 步骤红；但与其它有真实通过用例的文件混跑且无失败时，
整步可以是 rc=0，那条 skip 不会阻止它成功。这说明卡文要求的
`python -c 'import schemathesis'` 硬前置是必要的——**但它只挡"没装"，
挡不住"装了但版本不对"**，后者需要断言 API 存在而不只是 import。

#### 3.3 接入条件之一：耗时

逐层计时（同一 operation `GET /api/v1/health`）：

| 测量 | 耗时 |
|---|---|
| `import app.main` + `from_asgi` 建 schema | 7.1s（一次性） |
| 收集 **206** 个 operation | 35.8s（一次性） |
| **schemathesis `case.call()` 单次** | **20–50s** |
| 其中 checks 部分 | **0.00s**（时间全在 `call`） |
| 对照：`httpx.ASGITransport` 直调同端点 | **0.01s** |
| 对照：`TestClient` 直调同端点 | **0.00s** |
| 对照：`TestClient` 跑一次 lifespan | 7.1s |

> ### ⛔ 自我更正（Codex round-1 #6 证伪，我已读源码复核）
>
> 我原写「慢的**不是应用**，是 schemathesis 4.x 的 ASGI 传输层」——**归因反了**。
> `schemathesis/transport/asgi.py` 的 `ASGITransport.send` 每次都
> `with asgi.get_client(application) as client:`，而 `python/asgi.py::get_client`
> 返回 `starlette_testclient.TestClient(app)` ——
> **进入 `with` 就跑 app 的 lifespan startup、退出跑 shutdown**。
> 而我自己测过：这个 app 的 **lifespan 一次 7.1s**。
>
> 所以 20s 里**大头是应用自身的初始化**。而我那两个"对照"（`httpx.ASGITransport`
> 0.01s / `TestClient` 直调 0.00s）**不公平**——它们复用同一个客户端、只跑一次 lifespan。
>
> **准确说法**：schemathesis 4.x 的 ASGI 传输**每次调用新建客户端**，
> 于是这个 app 的 lifespan 被乘以了调用次数——**这个机制已经确认**。
>
> ⚠️ 但**「主项就是应用初始化 / 根因已定位」仍未证明**（Codex round-2 #4 再次收窄）：
> 单独测得的 7.1s 不能直接解释另一次 20–50s 的构成；`case.call()` 还包含 hooks、
> 请求序列化与响应转换。而且 **`httpx.ASGITransport` 本身根本不触发 lifespan**，
> 所以我说的"对照只跑一次 lifespan"也不准确——它是**一次都不跑**。
> 准确表述：**重复 lifespan 的机制已确认，耗时瓶颈尚未定位。**
> 要定位需要：固定 Case + 同一客户端实现，对同一次调用拆分
> startup / 序列化与 hooks / 请求 / shutdown 的分段 profile。

**最硬的一个数字（真 pytest 入口下的端到端实测，不是外推）**：把改前的版本原样放回
`backend/tests/contract/` 跑**一个** operation（`GET /api/v1/health`，`max_examples=10`）：

```
1 failed, 186 deselected, 613 warnings in 208.70s (0:03:28)
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=19 (blocked=19, advisory=0, unaccounted=0)
```

> **这个数字的口径边界（Codex round-2 #2 指出，采纳）**：
> - `in 208.70s` 是**整个 pytest session** 的耗时，含收集（本身 ~36s）、fixture、
>   执行与报告。**乘以 206 会把一次性成本重复计算 206 遍。**
> - 那次是 `1 failed, 186 deselected`（`-k` 过滤 + `-x` early stop），
>   **分母不是 206**，只跑了 1 个 operation 就停。
> - 「另有 8 个 explicit example 同样失败」= 9 个**显式** example。显式 example
>   **不计入 `max_examples`**，且失败后不会进入随机生成阶段 ⇒
>   **它不能代表一次完整的生成阶段。**
> - 单个 `health` operation、个位数样本、22s/49s 的方差，也不足以给所有端点定耗时下界；
>   本机 Python 3.14 与 CI 的 3.11/3.12 环境差异同样未控制。
>
> **能说的**：本机上，选中一个 operation 的那次 pytest session 耗时 **208.70s 且失败**。
> **不能说的**：「206 个 ≈ 12 小时」「必然跑不完」——那只是**带全部假设的情景算术**。

顺带：那行 `blocked=19` 是 W4 live-port 门的计数——**这一个用例里 app 尝试连 Neo4j 19 次**
（都被门挡住）。它同时是下面 §3.5 那条**独立阻断**的证据。
它也说明我先前「不是在真查库」的排除**下得太早**。

#### 3.5 ⛔ 还有第二个、与"慢"无关的独立阻断（Codex round-2 #3 指出，实测证实）

我原写「(b) 不落地的真正理由**只剩一条：慢**」——**这也是错的**。

`backend/tests/conftest.py` 有两层把「被拦的 live 端口连接」转成失败：

```python
:141 @pytest.hookimpl(wrapper=True)
:142 def pytest_runtest_makereport(item, call):
:143     """结账哨兵：把被 app/main.py 的 try/except 吞掉的拦截转成用例失败。"""
...
:194     elif state.blocked > 0 and status == 0:
:195         status = 3        # 非豁免连接尝试绝不允许以「全绿」收场
```

而我的探针实测 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=19 (blocked=19, advisory=0)`。

⇒ **即使把 deadline 放开、把耗时问题彻底解决，这个测试仍然会以 exit 3 收场**，
因为它在 app lifespan 里会尝试连真 Neo4j。而「复用一个已 startup 的客户端」
只能把 lifespan 次数从 N 降到 1，**降不到 0** ⇒ 那条修复方向**不足以**让它变绿。

**正确的口径**：(b) 至少有**两个互相独立的接入条件**尚未满足——
**(一) 耗时**，**(二) 启动期的存储/端口隔离必须符合现有安全门**。
后者是更根本的那个，且它不能靠"调 deadline"或"复用客户端"绕开。

**两个曾想用来解释慢的假设：试验没有支持它们，但也不足以排除**（Codex round-1 #7 指出，采纳）：
- 「其实是在真查库」——本机 7691/7692/11434/12341 全 closed；**但**端口 closed 不排除
  连接尝试与重试退避，且 `backend/app/api/v1/endpoints/health.py:142` 有按运行状态
  ping Neo4j 的分支。
- 「是系统代理超时」——设 `NO_PROXY='*'` 后反而更慢（49s vs 22s）；**但**在已知大方差下，
  单组结果不能排除代理相关开销。

#### 3.4 为什么"先退役再说"不行

乙案的退役是**有条件的**，条件是替代品真能接上。条件不成立时单做退役，等于在
「替代方案尚未满足接入条件」的情况下先把旧的删掉。

> **措辞更正（Codex round-1 #9 指出，采纳）**：我原写这是「**单向的覆盖面减法**」——
> **不准确**。Dredd job 已经是 `if: false`，删掉它**不会再减少当前的执行覆盖**
> （当前执行覆盖已经是零），而且删掉的东西也能从 git 历史恢复。
> 它保存的其实是**恢复选项与代码资产**（那 123 行 job 配置 + hooks 文件）。
> 准确的理由是：**替代方案尚未满足接入条件，按重裁保留恢复选项。**

> **Codex 提的第三条路（登记，非本卡执行）**：后续独立卡可以先为**少量关键 operation**
> 建立确定性的 HTTP/schema 检查，再把生成式测试放进独立预算逐步扩面——
> 不必把退役决策绑定在"206 个 operation 一次全部接入"上。已登台账。

---

### 四 (c) 版本口径归一（已落）

| 位置 | 改前 | 改后 |
|---|---|---|
| `pyproject.toml` dev extras | `schemathesis>=3.0` | **`schemathesis>=4.0`** + 写清依据 |
| `tests/contract/requirements.txt:16` | `schemathesis>=3.19.0` | **`schemathesis>=4.0`** + 注明以 pyproject 为准（初版曾改成裸包名靠注释指路，Codex round-1 #3 指出 pip 读不到 pyproject 约束、等于连原下限也取消，已改回自带约束） |

依据：代码用的就是 4.x 形态（`schemathesis.openapi.from_asgi`），而两处 pin 都放行 3.x。
**附带如实登记**：`tests/contract/requirements.txt` 全仓**没有任何安装方**（除它自己第 2 行
的说明文字）；CI 的 `test.yml:72` 是 `pip install hypothesis pytest-bdd schemathesis`，
**完全不带版本**。

> 卡文要求的「CI 加 `python -c 'import schemathesis'` 硬前置」**未落**——它只在
> (b) 成立（测试真进白名单）时才有意义；不接测试却加前置，等于为一个不存在的门做守卫。
> 已登台账。

---

### 五 (d) 负控 —— 一条改形态跑了，一条不成立

| 卡文负控 | 处置 |
|---|---|
| ① 临时把某端点 `response_model` 改坏 → schemathesis 门红 | **未跑**。该负控的前提是「门已接进 CI 且能跑绿」；本卡门未接、测试也跑不完，即使跑红也无法区分"负控生效"与"它本来就红"——那是**假杀**。如实声明不跑，理由见 §三。 |
| ② 卸载/遮蔽 schemathesis → 硬前置红而非 skip | **改形态跑了**：硬前置未落，所以改为直接演示「没有硬前置时会怎样」——即 §3.2 那两行实测（不存在 → skip/rc=5；版本不对 → failed/rc=1）。这恰好**证明了硬前置的必要性**，也暴露了它挡不住版本不对。 |

---

### 六 (e) 覆盖面如实声明

**schemathesis 不等价于 Dredd。** 退役后**确实丢失**的是
「**真实 HTTP 栈按 example 回放 + hooks 流转与鉴权**」这一层：

| | Dredd（**理论上**） | schemathesis（本仓用法） |
|---|---|---|
| 传输 | 真实 HTTP 栈（起服务 + 网络） | `from_asgi`，进程内，不过真实网络栈 |
| 用例来源 | 按 OpenAPI 的 **example 回放** | 按 schema **生成**，`max_examples=10` |

> ### ⛔ 自我更正（Codex round-1 #8 证伪，命令已核）
>
> 我原先在这张表里写「中间件 / 鉴权 / hooks 流转：Dredd 覆盖 / schemathesis **不覆盖**」。
> **两半都站不住**：
>
> 1. **Dredd 那半高估了它**。`api-spec-sync.yml:394-399` 的实际命令是
>    `dredd ... --method GET --names || true`。`--names` **只列用例名、不发请求**，
>    `--method GET` 又排除 POST，外加 `|| true` 与 job 级 `continue-on-error: true`
>    ⇒ **这个 job 即使启用，也既不会失败、也测不了任何东西**。
>    所以它并没有在覆盖"hooks 流转与鉴权"，它什么都没在跑。
>    （这也让台账「历史 24/24 全红」与命令形态**对不上**；日志不可考，本卡只登记矛盾。）
> 2. **schemathesis 那半低估了它**。`from_asgi(app)` 的请求**会经过应用的中间件与
>    适用的鉴权依赖**——"不过真实网络栈"不等于"不覆盖中间件/鉴权"。
>
> **保留的结论**：二者**不等价**（传输与用例来源确实不同）。
> **撤回的部分**：把「中间件/鉴权/hooks 流转」整体归给 Dredd 的那一行。

本卡与裁决页**均未**声称二者等价，也未声称「已完全覆盖」。
**且本卡最终没有退役**，所以无论 Dredd 实际覆盖多少，都原样保留着。

---

### 七 (f) README 同步 —— 无可同步项

按 readme-claims-lint 的口径核了一遍 `README.md`（判据绑计数，不靠 `|| echo`）：

| 关键词 | `contract` | `合约` | `契约` | `dredd` | `schemathesis` | `已覆盖` |
|---|---|---|---|---|---|---|
| 命中 | **0** | **0** | **0** | **0** | **0** | **0** |

⇒ README 里没有任何「合约测试已覆盖」类文案，(f) 无可同步项。

---

### 八 已落的代码改动（`e6f9aebc`）

1. **`test_openapi_contract.py`**：四个 conformance check 由**模块属性**改为经**注册表**
   取得（`load_all_checks()` + `CHECKS.get_by_names([...])`）。
   **不削弱任何检查**——取的是同名的那四个，语义不变，修的是访问路径。
   实测 `get_by_names` 返回：`['status_code_conformance','content_type_conformance',
   'response_headers_conformance','response_schema_conformance']`。
   改后该文件 **ruff check / ruff format --check / pyright 全绿**（pyright 0 errors），
   并在 `e6f9aebc` 的真实 commit 路径上被 Z7-A / Z7-B 两道门跑过。
2. **`pyproject.toml`** / **`tests/contract/requirements.txt`**：见 §四。
3. **裁决页 §六**：补记前提推翻与重裁。

---

### 九 副作用对账

> ### ⛔ 自我更正（Codex round-2 #7 证伪）—— **「未污染」这个结论是错的**
>
> 我原写：拍了三次快照、342 行逐行相同、`from_asgi` 与 lifespan **未污染** `data/`。
> **快照本身是真的**（Codex 独立核过三份文件，SHA-256 均为
> `f96c1245…cdd7`），**但我拍错了目录范围**：只拍了**仓库根的 `data/`**，
> 而这个 app 真正写的地方不止那里。
>
> `backend/app/middleware/cost_tracker.py:34-35` 的默认路径是
> `_BACKEND_DIR / "data" / "llm_call_logs.db"` —— 即 **`backend/data/`**，不是根 `data/`。
>
> 重做正确范围的对账后，本卡实验窗口内**确实新建了 3 个文件**：
>
> | 文件 | 出生时间 | 与我的快照 |
> |---|---|---|
> | `backend/data/llm_call_logs.db`（36 KB） | **08:15:47** | 夹在 before(08:15:07) 与 after(08:46:09) **之间** |
> | `backend/data/neo4j_memory.json` | **08:15:47** | 同上 |
> | `backend/app/data/vault_index_pending__canvas_vault.jsonl`（0 字节） | **09:26:12** | **晚于**最后一次快照(08:47:36) |
>
> 三个**全部 untracked 且被 `.gitignore` 覆盖** ⇒ 仓库内容没有被改动，
> `git status` 也确实一直干净——**但那恰恰是这个盲区的形状**：git 判据在这里恒绿。
>
> **我错在哪**：历史教训我记住的是「要对账 `data` 目录」，却把它当成了一个**确定的路径**，
> 没有去问「这个 app 到底往哪些地方写」。正确做法是先从代码里找出**所有**默认写入路径
> （`cost_tracker` / `vault_index_orchestrator` / lancedb …），再决定快照范围。
>
> **准确的结论**：
> - **可以断言**：仓库根 `data/` 在三个时点内容与目录清单逐字相同；仓库 tracked 内容未被改动。
> - **不能断言**：「本卡所有实验都没有产生持久化副作用」——**它产生了，上表三个**。
> - **未证明**：这三个文件是否已存在于更早的时点（我没有它们的基线），
>   也无法单凭时间戳认定是哪个进程创建的。**事后补拍不能冒充对账。**
> - 性质判断：都是开发期产物（LLM 成本日志 DB、索引 pending 队列、Neo4j 内存镜像），
>   不涉及数据丢失或越权写入；但**声明必须收窄**。

---

### 十 Codex 复核（卡文 (g)，两轮）

> 卡文原定 round-2 = 「只审负控与 `test.yml` / `api-spec-sync.yml` diff」。
> 本卡**没有改任何 workflow**（自 `46ed18f1` 起 workflow diff = **0 行**），该审查面为空，
> 因此 round-2 如实改为**审「不落 (b) 的证据链是否成立」**——即 §三 那些测量与由它们
> 推出的处置。这处偏离是事实驱动的，不是为了少做一轮：**如果证据链不成立，
> "不接进 CI" 这个结论就是错的，本卡等于用一份不可靠的测量说服用户放弃了一件该做的事。**

#### round-1（`gpt-6-astra` ultra / codex-cli 0.153.3 / read-only，审查面 `46ed18f1..e6f9aebc`）

**终裁**：**BLOCKER 0 / HIGH 2 / MEDIUM 5 / LOW 2** ⇒ 按 `card-batch-protocol.md` §1
**阻断级 = 0**。原文末句：「这次指定 diff 中未发现数据丢失、安全漏洞或越权写入级别的新问题。」

**9 条全部本机复核后采信 9、驳回 0**，其中**四条推翻了我自己写下的断言**（已在
`4cf0a3ba` 撤回，逐条更正写在 §三 与裁决页 §六）：

| # | 级别 | Codex 指出 | 我的复核 | 处置 |
|---|---|---|---|---|
| 1 | HIGH | 「任何版本都跑不通」不成立；且 4.x 的 `checks` 有动态 `__getattr__`，pytest 插件**收集期**就 `load_all_checks()`，裸 `dir()` 证明不了"每例必 AttributeError" | **完全成立**。源码 `pytest/plugin.py:146` 在 `_gen_items` 里调用；端到端实测改前版本拒因是 `DeadlineExceeded: 20857.69ms`，**不是** AttributeError | ✅ 撤回，代码改动**降级为防御性加固** |
| 2 | LOW | 修法本身可接受，未发现检查削弱；`get_by_names` 与模块属性**逐一同一对象** | 成立 | ✅ 保留代码，改正解释 |
| 3 | MEDIUM | 裸包名没有实现依赖归一：pip 读不到 pyproject 约束，反而把 `>=3.19.0` 下限也取消了；「没有安装方」应收窄 | **完全成立** | ✅ 改回自带 `>=4.0`；措辞收窄 |
| 4 | MEDIUM | `pyproject.toml` 注释**虚称 CI 已配硬前置** | **成立，是我写错** | ✅ 改为如实说明未实施 |
| 5 | LOW | rc 语义要分阶段：模块加载期的 AttributeError 是**收集错误 rc=2**；「无声吸收」应为「未阻止步骤成功」 | 成立 | ✅ 分阶段重写 |
| 6 | HIGH | 不能把慢归因为传输层：`with asgi.get_client(app)` → `starlette_testclient.TestClient(app)`，**每次调用含完整 lifespan** | **完全成立，我归因反了** | ✅ 撤回。当时改成了「主项是应用初始化」，**round-2 #4 又把这句也收窄了** → 最终口径是「重复 lifespan 机制已确认，**瓶颈尚未定位**」 |
| 7 | MEDIUM | 两个"排除"都超出证据 | 成立 | ✅ 改为「试验未支持该解释，尚不能排除」 |
| 8 | MEDIUM | Dredd 实际命令带 `--method GET --names`，**不发请求** ⇒ 推不出必然 422；且 `from_asgi` 会经过中间件与鉴权，覆盖表两半都不准 | **完全成立** | ✅ 撤回覆盖表那一行；payload 问题降级为「潜在恢复障碍」 |
| 9 | MEDIUM | 「单向覆盖面减法」不准确（job 已 `if: false`，删它减的是恢复选项）；另给出第三条路 | 成立 | ✅ 改措辞；第三条路登台账 |

#### round-2（同模型 / 同口径，审查面 = 「不落 (b) 的证据链」，绑定 `46ed18f1..4cf0a3ba`）

**终裁**：**BLOCKER 0 / HIGH 3 / MEDIUM 4 / LOW 1** ⇒ 阻断级 = 0。它对结论的两句回答：

> (1) 这次指定代码 diff 中，**未发现数据丢失／安全漏洞／越权写入级别的新问题**，
>     但现有对账不能证明此前所有实验均未产生持久化副作用。
> (2) 「不把合约测试接进 CI」的结论，判为 **证据不足但方向对**，
>     限定为「本卡暂不将现有整份测试原样接入」，不能扩大为「合约测试无法进入 CI」。

**8 条全部复核后采信 8、驳回 0**，其中**四条又推翻了我更正后的说法**：

| # | 级别 | Codex 指出 | 我的复核 | 处置 |
|---|---|---|---|---|
| 1 | HIGH | 自我更正**没有覆盖仍在生效的表述**（裁决页 / UAT / pyproject 多处仍写着已撤回的断言）；另指出 UAT 说 requirements「不写版本」已过期，且 `backend/scripts/contract-test.sh:18` 是真实调用入口，「未被任何自动流程执行过」过宽 | **全部成立**，逐处核对无误 | ✅ 本轮把裁决页 5 处 + UAT 6 处 + pyproject 1 处全部改正；台账条目 2 改写 |
| 2 | HIGH | 「209s ⇒ 206 个约 12 小时」不是可靠预测：`in 208.70s` 是**整个 session**（含 36s 收集），乘 206 会重复计一次性成本；那次是 `1 failed, 186 deselected`，分母不是 206；9 个 **explicit** example 不计入 `max_examples` 且失败后不进生成阶段 | **成立** | ✅ 降级为「带全部假设的情景算术」，并写明分母与 example 类型 |
| 3 | HIGH | **「只剩慢」漏掉了一个已经触发的独立失败门**：`conftest.py:142 pytest_runtest_makereport` 把被拦连接转成用例失败，`:194` 又保证非豁免 `blocked>0` 不能返回 0 ⇒ **即使消除 DeadlineExceeded，测试仍会红** | **完全成立**，源码已核（`elif state.blocked > 0 and status == 0: status = 3`），而我的探针实测 `blocked=19` | ✅ **新增 §3.5**：接入条件从「一条」改为**两条互相独立**的 |
| 4 | MEDIUM | 「应用初始化是主要耗时／根因已定位」仍未证明；且 **`httpx.ASGITransport` 本身不触发 lifespan**，我说的"对照只跑一次 lifespan"也不对 | 成立 | ✅ 改为「重复 lifespan 机制已确认，**瓶颈尚未定位**」 |
| 5 | MEDIUM | `continue-on-error` 在**步骤级**不是 job 级 ⇒ 「整个 job 不会失败」与据此推出的「历史 24/24 全红对不上」都要撤回 | **成立**（`:390-392` 在 step 下）。而且这**解释了**历史：Dredd 那步不会让 job 红，job 是因**别的步骤**红的，两者不矛盾 | ✅ 撤回「矛盾」之说 |
| 6 | MEDIUM | 仍残留「白白少一层保护」与「中间件/鉴权覆盖独占归 Dredd」 | 成立 | ✅ 4-B 第 4 条与裁决页 §三 表格均已改 |
| 7 | MEDIUM | **`data/` 对账遗漏真实写入目录**，且末次快照没覆盖后续实验窗口 | **完全成立**，见 §九 的更正 | ✅ §九 重写；结论收窄 |
| 8 | LOW | `importorskip` 的假绿是**条件性**的；负控只是「机制演示」，不是 CI 负控验收 | 成立 | ✅ §3.2 与 §五 已按条件性表述改写 |

> **这轮最有价值的一条是 #3**：它不是措辞问题，而是**我把接入条件少数了一个**。
> 少数的那个（启动期端口/存储隔离）比"慢"更根本——它不能靠调 deadline 或复用客户端绕开。
> 如果没有这轮复核，本卡会把一个**两条件**问题写成**一条件**问题交出去，
> 下一张卡就会照着错误的方向去优化性能，然后发现测试还是红的。

---

## 本卡未证明什么

1. **没有在 GitHub 上实跑任何 workflow**，所有结论都来自本机。
2. **没有证明 schemathesis 与 Dredd 等价**——恰恰相反，§六 写清了不等价与丢失面。
3. **没有证明那 206 个用例能通过**。实测到的失败形态是 `DeadlineExceeded`
   （改前改后都是——见 §3.1 的更正），我**没有**在放开 deadline 后跑完整套
   （单个 operation 209s，全套按线性外推需小时级）。
   **也就是说：本卡不知道这些契约检查放开时间限制后会不会发现真实的契约不符。**
4. **20–50s 的方差没有做统计**：同一 operation 两次测得 22s 与 49s，样本量个位数。
5. **没有定位 schemathesis 内部把时间花在哪一步**——只证明了「在 `call()` 里，不在
   checks 里」。**「主要耗时是应用初始化」同样未证明**（Codex round-2 #4）：
   已确认的只有"每次调用都会重复跑 lifespan"这个机制；单独测得的 7.1s 不能直接解释
   另一次 20–50s 的构成，而 `case.call()` 还包含 hooks、请求序列化与响应转换。
   准确说法是**「机制已确认，瓶颈尚未定位」**。
6. ~~没有验证「任何 3.x 版本都跑不通」的全版本区间~~ —— **这条已经补上，并且推翻了
   我原来的断言**（见 §3.1 的自我更正）。现在仍未证明的是**更窄**的一段：
   3.19.0–3.24.x 区间没测（3.19.0 在 Python 3.13 上因 `cgi` 被移除而无法 import），
   以及 4.0–4.13.x 没测（只测了 4.14.3）。**`openapi.from_asgi` 与
   `checks.*_conformance` 的确切交叠区间因此仍是未知的**，我只证明了 3.25/3.30/3.39
   在交叠区内。**注意 4.14.3 并不在交叠区外**——它的 `checks` 有动态 `__getattr__`，
   pytest 插件收集期加载后四个属性同样可用（见 §3.1 第二次更正）。
7. **没有跑负控 ①**（`response_model` 改坏），理由见 §五。
8. **没有落 CI 硬前置**，理由见 §四末尾。
9. **没有动 `dredd-hooks.js` 的 payload 缺 `vault_id`**——只证明了它与
   `RAGQueryRequest.required = ['query','vault_id']` 不符（证据取自 `backend/openapi.json`
   快照），没有修，因为甲案未被选中。**且已更正：这在当前命令下不会触发**（见 §六）。
10. **没有核实台账「Dredd 历史 24/24 全红」是否属实**。它与当前命令形态
    （`--method GET --names || true` + `continue-on-error`，即空跑且不会失败）**对不上**，
    日志不可考。本卡只登记矛盾，不下结论。
11. **⛔ 方法论层面的自我登记：本卡连续三次用"受控条件与真实路径不同的探针"代表真实路径**
    ——(a) 一个版本 → 所有版本；(b) 裸 `import` → 真 pytest 入口；
    (c) 复用客户端的直调 → schemathesis 每次新建客户端。三次都被外部审查或我自己的
    证伪实验推翻。**这说明本卡里凡是没有"跑在消费方真正走的那条路上"的判据，
    都应视为未证明**，而不是"暂时没测但大概率对"。

---

## 台账待登记条目

> 台账只由主 session 写入，本卡不改。以下为建议登记内容。

| # | 条目 | 建议归属 |
|---|---|---|
| 1 | **合约测试单个 operation 209s（真 pytest 实测），206 个 ≈ 12 小时。根因已定位**：`schemathesis/transport/asgi.py::ASGITransport.send` 每次 `with asgi.get_client(app)`，而它返回 `starlette_testclient.TestClient(app)` ⇒ **每次调用跑一遍 app lifespan**（本 app lifespan 单次 7.1s，且单个用例里触发 19 次 Neo4j 连接尝试）。**修复方向：复用一个已 startup 的客户端**，而不是每次新建 | **新卡（中）**，本卡直接产出 |
| 2 | **合约测试在 CI 白名单外**；本机存在调用入口 `backend/scripts/contract-test.sh:18`（`pytest tests/contract/`），但**是否被真正跑过无从证明**（Codex round-2 #1 指出，我原写"未被任何自动流程执行过"过宽）。当前失败形态是 `DeadlineExceeded` + W4 端口门 exit 3 | 与第 1 条同卡 |
| 3 | **CI 硬前置 `python -c 'import schemathesis'` 未落**（本卡不接测试，加前置无意义）。且实测表明它**挡不住"装了但版本不对"**——真正需要的是断言 API 存在 | 与第 1 条同卡 |
| 4 | **`tests/contract/requirements.txt` 全仓没有任何安装方**，属文档级清单。与 Z7-B 查出的根 `requirements.txt` 情况不同（后者有 `scripts/deploy_epic12.py`） | backlog |
| 5 | **`dredd-hooks.js` 的 payload 缺 `vault_id`**（`:38-41` 与 `:152-158` 两处），与 `RAGQueryRequest.required` 不符。是**潜在的恢复障碍**（当前命令带 `--method GET --names` 不会触发它），若将来复活 Dredd 必须先修 | backlog |
| 6 | **`contract-test` job（123 行）仍在树上且仍 `if: false`** —— 本卡刻意不删，理由见 §3.4 | 环境记录 |
| 8 | ⛔ **该 Dredd job 即使启用也是空跑**：命令是 `dredd … --method GET --names \|\| true`，job 级还有 `continue-on-error: true`。`--names` **只列用例名不发请求**，`--method GET` 又排除 POST ⇒ **既不会失败、也测不了任何东西**。这与台账「历史 24/24 全红」**对不上**，日志不可考，本卡只能登记这个矛盾——**若将来复活，第一件事是搞清楚它当年到底跑的是什么** | **新卡（小）**，与第 1 条同批 |
| 10 | ⛔ **接入条件不止"慢"这一条**：`backend/tests/conftest.py:142/:194` 会把非豁免的 live 端口拦截转成失败并强制 exit 3，而该测试的 app lifespan 实测触发 **19 次** Neo4j 连接尝试 ⇒ **启动期的端口/存储隔离必须先符合现有安全门**，这条不能靠调 deadline 或复用客户端解决 | **与第 1 条同卡，且应排在性能之前** |
| 11 | **本卡实验产生了 3 个未被对账覆盖的持久化产物**（`backend/data/llm_call_logs.db`、`backend/data/neo4j_memory.json`、`backend/app/data/vault_index_pending__canvas_vault.jsonl`，全部 gitignored）。根因是对账只拍了**根 `data/`**。**建议把"起 app 前后要对账哪些目录"写成一份从代码里推导出来的清单**（`cost_tracker` / `vault_index_orchestrator` / lancedb …），而不是每次凭记忆拍一个路径 | **新卡（小）**，跨车道通用 |
| 9 | **Codex 提的第三条路**：不必把退役绑定在「206 个 operation 一次全接入」上——可以先为少量关键 operation 建确定性 HTTP/schema 检查，再把生成式测试放进独立预算逐步扩面 | 与第 1 条同卡 |
| 7 | **`test.yml:72` 装 schemathesis 不带版本**，与 `pyproject.toml` 的 `>=4.0` 不同步。若将来接入需一并处理 | 与第 1 条同卡 |

---

## 待你裁决

**本卡的两个裁决点都已裁，无新增待裁项。**

1. **Dredd 处置**：原裁 **乙**（手册 `:301`）→ 前提被实测推翻 → 同日重裁
   **「只落已完成的、不退役」**。两次记录都在裁决页。
2. 无其它待裁项。

> 后续动作的建议顺序（供主 session 排期，非待裁）：先做台账第 1 条（定位
> schemathesis 传输层耗时），它是「契约测试能不能回到 CI」的唯一卡点；
> 第 3、7 条随它一并处理。

---

*生成时间 2026-09-05 · 车道 `card/z7-tool` · commit `7b8383d2` + `e6f9aebc` · 未 push*
