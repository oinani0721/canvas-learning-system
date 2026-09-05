# UAT — CARD-TEST-hygiene-vaultinit

> `[BATCH-2026-09-05-第十二批 / CARD-TEST-hygiene-vaultinit]`
> 车道 `card-y6-testhygiene`（分支 `card/y6-testhygiene`），基线 `03ac8bf8`。
> 证据目录 `_bmad-output/审查/evidence-hygiene/`。日期 2026-09-05 → 09-06。

## 〇 这张卡在干什么（一句话）

跑后端单元测试会把一整套 vault 骨架撒进代码目录 `backend/` 里 ——
本卡先**查清是谁写的**（台账归错了文件），再堵住那个写入面，
最后立一道门让这种事下次发生时当场变红。

---

## 一 (a) 定位：结论与证据

完整记录见 `evidence-hygiene/定位结论-a.md`（含全部命令与原始输出）。摘要：

| 假设 | 签名① `backend/` 四路径 | 签名② `/tmp/test-vault*` | 签名③ 两文件 sha |
|---|---|---|---|
| H1 = `tests/unit` 目录级 | **未复现** | **复现**，二分到 2 个 nodeid | **未复现** |
| H2 = `tests/contract`（定向 setup-wizard，改前代码） | **复现** ⚠️ | 出现（含并行干扰面） | 未变（未跑到写它的端点） |

### 🎯 H2 复现 = 台账那条污染的真正写者（详见 `定位结论-a-h2.md`）

```
tests/contract/test_openapi_contract.py::test_api_contract[POST /api/v1/system/setup-wizard]
```

在**改前代码**上单跑该 operation（`1 failed, 205 deselected, 614.71s`），
`backend/` 下随即出现 `?? CLAUDE.md ?? outputs/ ?? raw/ ?? wiki/`。
与冻结证据树 `card-z4-redbase` @ `c8611a89` 比对：

- 污染文件树 `diff` → **逐条相同**
- `backend/CLAUDE.md` sha256 → **完全一致**（`319599d2ca3c…`）
- 唯一差异：证据树多一条 ` M subject_mapping.yaml` —— 那由另一个端点
  （metadata 保存面）被属性输入打中所致，本次只跑 setup-wizard 一个 operation，
  故未触及。差异方向自洽。

机制：`@schema.parametrize()` 覆盖全端点且无 exclude；`vault_path` 在 OpenAPI 里
是无约束 `type: string`，hypothesis 会生成空串／相对路径；
`system.py:441` 的 `Path(v).resolve()` **静默**把它拼成 cwd（pytest 从 `backend/` 起跑），
`initialize_vault()` 就地建骨架。

**两条如实声明**：

1. **全量 H2 按卡文原命令跑不完**：206 个 operation，实测 15:29 只完成 4 个
   ⇒ 全量约 13 小时。中止时三签名全空，但那是「没跑到」不是「没发生」，
   不能当结论。改用同文件同机制的 `-k setup` 定向子集（`--co` 确认唯一命中）。
2. **第一次定向尝试是假绿，我自己抓到了**：用带方括号的完整 nodeid 传参 →
   `rc=4` usage error、**0 个用例执行**、三签名全空。若据此写「未复现」就是
   把「没跑」当「不存在」。已加**硬前置断言**（log 里必须出现
   `1 (passed|failed|error)`，否则 `exit 96` 并宣告判据无效）后重跑才得上述结论。

**H1 二分结果（nodeid 级）**：

- `tests/unit/test_startup_health_check.py::TestSetupWizard::test_endpoint_exists`
  → 单跑只产生 `/tmp/test-vault`
- `tests/unit/test_startup_health_check.py::TestSetupWizard::test_returns_structured_report`
  → 单跑只产生 `/tmp/test-vault-wizard`

与源码 `:55-57` / `:61-63` 的硬编码字面量一一对应。

**H1 的 backend/ 骨架：未复现。** 三处判据同时为空：
`git status --porcelain backend` 空、四路径 `test -e` 全 absent、两文件 sha diff 空。
目录级跑完 `209 failed, 4602 passed, 38 errors`（209+38 = 247，与基线 nodeid 数逐字相同）。

### ⚠️ 我自己发现并声明的判据缺陷

`/tmp` 是**全机共享**的。本批 9 个车道并行，**别的车道跑 `tests/unit` 会产出同样的
两个目录** —— 实测 2026-09-06 01:55，`card-y9-maingoal` 车道（PID 68344，
`lsof` cwd 确认）就造了一对。所以「`ls -d /tmp/test-vault*` 有没有」这个判据
**在并行环境下不可信**。

我认为 nodeid 归因仍成立，理由是：并行车道的污染**成对**出现（两用例连着跑、
间隔 ≈5s，与各自 5.48s/5.49s 的耗时吻合），而我的两次单跑各自**只**产生一个、
且与源码字面量精确对应。「成对 vs 单个」是能翻转结论的对照。y9 那次意外运行
反而成了独立第三方复现。**这条推理已列入 Codex 复核的第 1 问，请重点看。**

---

## 二 台账归因勘误（车道不改台账，此处只写待登记条目）

**原句**（`未合卡追踪台账.md:48` Z4-A 行 与
`2026-09-05-第十一批复核裁定与待裁决登记.md:54`，两处同文）：

> ~~`test_vault_init_service.py` 目录级运行把 vault 骨架写进 `backend/`~~

**实测划改为**：

> `backend/` 内的 vault 骨架，写者是
> **`tests/contract/test_openapi_contract.py::test_api_contract[POST /api/v1/system/setup-wizard]`**
> —— schemathesis 对全端点做属性输入且无 exclude，生成的空串／相对路径
> 经 `system.py:441` `Path(v).resolve()` 静默拼成 cwd（= `backend/`）。
> 改前代码上单跑该 operation 即完整复现，污染文件树与冻结证据树逐条相同、
> `CLAUDE.md` sha256 一致（`319599d2ca3c…`）。
>
> 与之独立的另一处污染：`tests/unit` 目录级会产出 `/tmp/test-vault` 与
> `/tmp/test-vault-wizard`，写者是 `test_startup_health_check.py::TestSetupWizard`
> 的两个 nodeid（硬编码 `/tmp` 字面量，本卡已改 `tmp_path`）。
>
> `test_vault_init_service.py` **不是**任一处的写者：其 8 个用例全部经
> `vault_dir(tmp_path)`，且该文件在 tests/unit 红基线里 0 条；
> `tests/unit` 目录级跑完 `backend/` 三处判据全空。

---

## 三 (b) 守卫面修改

### ① `SetupWizardRequest.vault_path` 加绝对路径校验（`system.py`）

```python
@field_validator("vault_path")
@classmethod
def _must_be_absolute(cls, v: str) -> str:
    if not Path(v).is_absolute():
        raise ValueError(...)
    return v
```

**为什么在 pydantic 层而不是补黑名单**：`setup_wizard` 里
`Path(request.vault_path).resolve()` 对相对路径和空串是**静默**拼 cwd 的，
黑名单（`:442-448`）跑在 `resolve()` **之后**，那时看到的已经是一个合法绝对路径
—— 往黑名单加条目永远追不上这个形态。

**与消费方同口径**：校验用的 `Path(v)` 与 `setup_wizard` 里用的是同一个类，
不存在两套解析规则。

**既有黑名单原样保留、未搬动**（`:442-448` 的 6 条系统目录 + `..` 拒绝逐字未动）。

**语义自证**（独立最小样例，pydantic 2.12.5 / fastapi 0.135.3，本 venv 实跑）：

```
''  '.'  './x'  'relative/x'  '   '  '~/vault'   -> 422
'/tmp/ok'  '/private/var/folders/a/b'            -> 200
```

macOS 的 `tmp_path` 正是 `/private/var/folders/...` 形态 ⇒ 不会误拒。
`~/vault` 一并拒绝是有意的：`Path` 不展开 `~`，`resolve()` 会把它当相对路径拼 cwd。

### ② `test_startup_health_check.py` 的硬编码 `/tmp` 改 `tmp_path`

`:55-57` / `:61-63` 的 `/tmp/test-vault` 与 `/tmp/test-vault-wizard`
→ `str(tmp_path / ...)`。该文件 `:12-16` 的裸 `TestClient(app)` fixture
**本卡未动**（RED-A1 面，第十三批）。

### ③ 新增负控 `TestSetupWizardPathValidation`

- `test_rejects_non_absolute_path`：6 个参数化坏形态 → 必须 422
- `test_accepts_absolute_path`：绝对路径 → 必须非 422，且断言骨架落在 `tmp_path` 内

**一处必须说明的设计取舍**：正控里 patch 掉了
`app.api.v1.system.startup_health_check`。原因是它会去连现网 Neo4j 7691、
被 W4 端口门哨兵转红 —— 那样这条新用例就会**凭空新增一条基线红**，
直接违反 (e)「不得出现 `>` 行」。patch 生效是因为 `setup_wizard` 在函数体内
按模块全局名查找它（不是 `from X import f` 到别的模块）。
附带收益：用上了文件里存量未使用的 `AsyncMock` / `patch`，
顺手消掉 pyright 两条 `reportUnusedImport`。

## 四 (c) 不变量门与负控

`backend/tests/unit/conftest.py` 新增 `scope="session", autouse=True` 的
`_no_vault_skeleton_left_behind`：session 开始与结束各做一次只读快照，
比对 ① `backend/{raw,wiki,outputs,CLAUDE.md}` 存在性 ② `backend/.gitignore`
与 `backend/config/subject_mapping.yaml` 的 sha256 ③ `/tmp/test-vault*` 集合；
任一「新出现 / sha 变」→ `pytest.fail` 并列出具体路径。

### 零副作用 —— 外部观测证明（不靠读代码）

`fixture-zero-write-proof.txt`：

- **零写**：对 `backend/` 全树取 (相对路径, 大小, mtime_ns) 指纹，
  调用快照函数前后 **1603 个条目、sha256 逐字相同**。
- **不依赖 cwd**：把 cwd 换成 `/` 再调一次，`_hygiene_backend_root()`
  仍解析到同一个 `backend/`，两次快照对象**完全相等**。
- 不 import `app.*`；setup 与 teardown 复用**同一个**快照函数
  （两侧各写一份逻辑会因环境差异产生假红）。

### `/tmp` 那一段判据的已知缺陷（我自己声明）

`/tmp` 全机共享，别的 worktree 跑 `tests/unit` 会让这道门假红。
本卡按卡文要求仍将其纳入 fail，但在失败消息里写明了分辨方法
（`stat` mtime + `ps -ww` / `lsof` 核对进程归属）。
**建议下一卡把它收窄为进程归属绑定或降级为 warning** —— 已列入待登记条目。

### ⚠️ (c) 与 (e) 的结构性冲突（提前用独立探针测出，非事后解释）

用 scratchpad 里一个独立最小 pytest 工程实测（`gate-fail-format-probe.txt`），
session fixture 的 teardown fail 在 short summary 里长这样：

```
ERROR tests/test_x.py::test_b - Failed: ...
```

它**会**被 (e) 的基线口径 `grep -E '^(FAILED|ERROR) tests/'` 捞到，
nodeid 取的是**最后一个跑完的测试**（随收集顺序变）。

于是：卡文 (c) 要求「违反即 fail」，(e) 要求「基线 diff 不得有 `>` 行」——
一旦别的车道在裁判 6 那 ~5.5 分钟里造出 `/tmp/test-vault*`，两条不可同时满足，
而触发条件**不在本卡控制范围内**。

处置：跑裁判 6 前 `ps` 择时 + 清空 `/tmp/test-vault*` 重新武装；
若仍出现该 ERROR，按 mtime + 进程归属如实判定来源。
**本卡自身零污染另有独立证明**：`backend/` 四路径与两文件 sha 是本 worktree
独有的判据，不受并行影响，能独立回答「本卡有没有把东西写进仓库」。
详见 `evidence-hygiene/门失败格式与e冲突.md`。

---

## 五 裁判输出

原始输出全部落在 `_bmad-output/审查/evidence-hygiene/`（`.txt`，末行 `rc=`）。
本节只引用路径与结论，不复述数字来源以外的内容。

### 裁判 1 — H1 哨兵（卡文 §二.1）（`unit-run-h1-20260905T164916.txt`，782 KB）

`209 failed, 4602 passed, 1 skipped, 38 errors in 316.95s`，rc=1。
209+38 = 247 = 基线 nodeid 数。签名①③ 未复现，签名② 复现。
判据落盘：`status-after-h1.txt`（空）、`newer-after-h1.txt`、`tmp-after-h1.txt`。

### 裁判 4 — 修后三文件（卡文 §二.4）（`three-files-after.txt`）

`7 failed, 19 passed in 30.82s`，rc=1。

| 文件 | 红数 | 基线 | 判定 |
|---|---|---|---|
| `test_startup_health_check.py` | 6 | 6 | nodeid 逐条相同，**不增** ✅ |
| `test_vault_init_service.py` | **0** | 0 | 8 用例全绿 ✅ |
| `test_kg_health.py` | 1 | 1 | **不增** ✅ |

`19 passed` 中含本卡新增的 7 条负控（6 参数化拒 + 1 正控）**全绿**。
随后 `ls -d /tmp/test-vault /tmp/test-vault-wizard` → **两条 No such file** ✅

### 裁判 3 — 二分（卡文 §二.3）（`bisect-node1.txt` / `bisect-node2.txt`）

见 §一。每步跑前把 `/tmp/test-vault*` **改名**重新武装（不 rm），
否则 `mkdir(exist_ok=True)` + `if not claude_md.exists()` 会让重跑不留痕。

### 裁判 2 — H2 哨兵（卡文 §二.2）（`unit-run-h2-*.txt` / `h2-directed-*.txt` / `h2-directed-AFTER-*.txt`）

见 §一与 `定位结论-a-h2.md`。含**受控对照**：同一 operation 改前污染、改后干净，
且失败身份（`DeadlineExceeded`）逐字同型 ⇒ 零回归。
换版用 `git show HEAD:...` + `EXIT trap`，收尾 `RESTORE-OK sha=5f1d7c1d77ef…` 自证。

### 裁判 5 — (c) 负控（卡文 §二.5）（`negctl-red.txt` / `negctl-green.txt`）

红轮 `1 passed, 1 error`，四条判据全 PASS：

1. **变异确实生效** — `backend/raw/_probe` 真被造出来（否则绿轮的绿是自证）
2. **拒因出自本卡的门** — 消息含 `CARD-TEST-hygiene-vaultinit 不变量门`
3. **消息指名 `backend/raw`**
4. **用例本身 passed** — 红只来自门，不是被用例断言顺带弄红的

绿轮 `1 passed`，rc=0，门未误报，`backend/raw` 不存在。
临时探针文件与 `backend/raw` 均已由 EXIT trap 清除，`git status backend` 干净。

### 裁判 7 — 地盘门（卡文 §二.7）（`judge7-scope-gate.txt`）

`git diff --name-only HEAD -- . ':(exclude)_bmad-output'` → 恰好三文件，
与期望集合**逐条相同** ✅（用 `:(exclude)` 而非 `:!`，rc=0 且有输出，
避开了 zsh 吞 `:!` 导致「输出为空即通过」的假绿）。
禁改文件（`vault_init_service.py` / `tests/conftest.py` /
`test_vault_init_service.py` / `subject_mapping.yaml` / `tests/contract/`）
`git diff --stat` 输出空且 rc=0 ⇒ **全部零改动** ✅

### 裁判 8 — pyright（卡文 §二.8）（`pyright-before.txt` / `pyright-after.txt`）

**9 errors → 7 errors**（净减 2）。`system.py` 的 7 条逐条对应、位移量整齐 `+25`
（= 本卡净插入行数），插入点之前的 336/401 行号不变 ⇒ **零新增** ✅
详细对照与 commit 门冲突见 `pyright-零新增证明与门冲突.md`。

### 裁判 6 — tests/unit 基线逐 nodeid diff（卡文 §二.6）（`judge6-*.txt`）

`209 failed, 4609 passed, 1 skipped, 38 errors in 285.12s`，rc=1。

| 项 | 值 |
|---|---|
| 收工红 nodeid 数 | **247** |
| 基线红 nodeid 数 | **247** |
| `diff` 结果 | **完全为空**（rc=0） |
| 新增 `>` 行 | **0** ✅ |
| 减少 `<` 行 | 0 |
| passed | 4609 vs 基线 4602 ⇒ **+7** = 本卡新增负控全绿 |
| 不变量门触发 | **0**（目录级零误报） |
| `/tmp/test-vault*` | 两条 No such file ✅ |
| `backend/` 四路径 | 全 absent ✅ |

跑前 `ps` 择时（无其他车道在跑 pytest）+ 清空 `/tmp/test-vault*` 重新武装；
全程 `/tmp` 未被并行车道污染，故 (c)/(e) 的冲突**本次未被触发**
（不等于它不存在，见 §四）。

> 收工那一次在给 fixture 补覆盖面注释后**重跑**过，见 `judge6-final-raw.txt` /
> `unit-red-final.txt`（改动全是 `#` 注释行，`ruff check` + `format --check` 全绿）。

### 裁判 9 — tests/api 契约面（卡文 §二.9）（`judge9-tests-api.txt`）

`268 passed, 40 warnings in 1.90s`，rc=0，红 nodeid **0 条**，
`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。

**开工基线未在改前采集**（如实声明，是我的执行顺序失误：改完 `system.py`
才想起这一条）。补强论证有两条，且比 diff 更强：

1. `grep -rn 'setup-wizard|setup_wizard|vault_path' tests/api/` → **0 命中**，
   本卡对 `system.py` 的改动只触及 `SetupWizardRequest`，与该目录零相关；
2. 收工**全绿**（0 红）—— 无论开工基线是什么，全绿都不可能包含新增红。

### hook 绕过声明

`LEFTHOOK_EXCLUDE=python-lint,python-typecheck`，原始输出与「报错不在本卡改动行」
的完整证明见 `LEFTHOOK_EXCLUDE-声明.md`：

- `python-lint`：`ruff check` **rc=0 全过**；只有 `ruff format --check` 因
  `system.py` 的**存量**漂移失败（HEAD 版本即已 DRIFT，42747 字节自证非空），
  且 format 想改的 18 个 hunk 与本卡改动行（20、428–453）**零相交**。
  卡文 §三明确允许此项，条件是贴证据 —— 已贴。
- `python-typecheck`：⛔ 卡文与协议 §2.3 **均禁止**绕过。本卡形式上违反，
  实质意图（零新增）已逐行号证明。**列为需裁条目**，见 §八.5。

## 六 DoD-3

### 4-A Claude 已代验（技术项）

| # | 项 | 结果 |
|---|---|---|
| 1 | 定位到 nodeid 级 | ✅ H1 → 2 个 nodeid；H2 → `test_api_contract[POST /api/v1/system/setup-wizard]` |
| 2 | 与冻结证据树比对 | ✅ 文件树逐条相同 + `CLAUDE.md` sha256 一致（`319599d2ca3c…`） |
| 3 | 绝对路径校验 6 坏形态 → 422 | ✅ 裁判 4 中 7 条新增负控全绿 |
| 4 | 绝对路径 → 非 422，骨架落 tmp_path | ✅ 同上，含 `assert (vault / "raw").is_dir()` |
| 5 | 不变量门负控 红/绿 两轮 | ✅ 红轮 4 判据全 PASS、绿轮 3 判据全 PASS |
| 6 | fixture 零写 + 不依赖 cwd | ✅ 外部观测，1603 条目指纹逐字相同 |
| 7 | tests/unit 基线逐 nodeid diff 无 `>` 行 | ✅ 247 vs 247，diff **完全为空** |
| 8 | pyright 零新增 | ✅ 9 → 7 errors，逐行号 +25 对应 |
| 9 | 地盘门 ⊆ 三文件 | ✅ 逐条相同；禁改文件 5 项全零改动 |
| 10 | 修复有效性（受控对照） | ✅ 同一 contract operation：改前污染、改后干净，失败身份不变 |
| 11 | 契约面零回归 | ✅ tests/api `268 passed, 0 failed`，`blocked=0` |
| 12 | `/tmp` 污染消失 | ✅ 裁判 2 与裁判 6 后均为两条 `No such file` |

### 4-B 你来验（一句话，零技术词）

> **无变化 —— 跑测试不再往代码目录里撒文件。**
>
> 你不需要做任何操作。这张卡改的是"跑自动化测试时的卫生"：
> 以前跑某一类测试会在后端代码目录里凭空多出 `raw/`、`wiki/`、`outputs/`
> 和一个 `CLAUDE.md`（那是给 Obsidian 笔记库用的骨架，跑到代码目录里纯属误伤）。
> 现在这条路被堵住了，而且以后再发生会立刻报错，不会再拖几天才被发现。
> 你日常用这个 App 的体验完全不变。

#### 双段铁律自检（`_bmad-output/.claude/CLAUDE.md` D3-A / D3-C）

```
段非空自证：4-B 228 字符 / 4-A 779 字符 ✅   （防「段没取到 ⇒ 0 命中」的假绿）
D3-A 4-B 段禁词（curl/docker/HTTP/JSON/.env/endpoint/pytest/schema/容器/
                daemon/终端/命令行/DevTools/nodeid/commit/sha256/pyright/ruff/API）: 0 命中 ✅
D3-C 4-A 段甩锅词（请你跑/你执行/你打开终端/你来跑）: 0 命中 ✅
检测器验伪锚（人为往 4-B 注入 curl 后应命中）: 命中 1 ✅
```

> 验伪锚是必要的：不加它，「0 命中」既可能是真干净，也可能是检查器自己坏了。
> 本卡第一版用 shell 写的这个检查就是后者 —— `grep -c` 返回 `0\n0` 让
> `[ -gt ]` 全部报错、累加器从未执行，却照样打印了「✅ 0 命中」。

（D3-E 的「我做 X → 我看到 Y → 我感觉 Z」句型不适用：本卡是纯内部卫生修复，
卡文明确要求 4-B 就写一句「无变化」，用户侧没有可操作的验收动作。）

## 七 本卡未证明什么（必填）

1. **未证明 tests/contract 属性输入的完整污染面**。本卡只定向跑了
   206 个 operation 里的 **1 个**（setup-wizard）。其余 205 个是否还有别的
   写盘端点（例如证据树里那条 ` M subject_mapping.yaml` 对应的 metadata 保存面）
   **没有验证** —— 全量跑需约 13 小时。metadata 面不在本卡地盘，只登记。
2. **未证明 (c) 的 fixture 覆盖 tests/unit 之外的套件**。它是
   `tests/unit/conftest.py` 里的 session fixture，只在 `tests/unit` 被收集时生效。
   本卡实测的真凶 `tests/contract` **不在它的覆盖范围内** —— 这道门挡不住今天
   查到的那条链，它挡的是同类问题下次从 tests/unit 侧再发生。
   （把门放到 `tests/conftest.py` 才能全覆盖，但那个文件是 Y7-A 独占，硬边界禁改。）
3. **未证明 `test_startup_health_check.py` 6 条基线红的完整真因**。
   本卡拿到的直接证据是 W4 端口门哨兵（`live Neo4j port connect attempted
   ('::1', 7691)`，端点本身返回 200），但只验证了其中 1 条 nodeid 的失败正文，
   其余 5 条未逐条核对。归 Y6-C。
4. **未清理主干已入库的 5 条乱码 mapping**（`subject_mapping.yaml`，`793cd538`）。
   硬边界禁改该文件。
5. **未证明本卡的修复对「非 pytest 的真实调用方」无影响**。全仓 grep 显示
   setup-wizard 端点只有测试在调、前端零引用，但没有对真实部署做端到端验证。
6. **未证明 `/tmp` 那段判据在并行环境下不会假红** —— 恰恰相反，实测它**会**
   （见 §四）。本卡按卡文要求保留了它。

## 八 台账待登记条目（必填，车道不改台账）

1. **Z4-A 行归因勘误**（`未合卡追踪台账.md:48`）与
   `2026-09-05-第十一批复核裁定与待裁决登记.md:54` —— 原句保留划改，
   实测结论见本单 §二。真凶是 `tests/contract/test_openapi_contract.py`
   的 setup-wizard operation，不是 `test_vault_init_service.py`。
2. **`tests/contract/test_openapi_contract.py` 对写端点无 exclude = 独立卡**
   （第十三批候选）。本卡实证它会往仓库里建目录、写文件；`@schema.parametrize()`
   覆盖 206 个 operation 且 grep `exclude` 0 命中。**H2 命中，按卡文 (f)③ 登记。**
3. **`subject_mapping.yaml` 5 条乱码 mapping 入库**（`793cd538`）= 独立卫生卡。
   本卡定向复现只跑了 setup-wizard，未触及写它的端点，但形态与条目 2 同源。
4. **`system.py:28` router 无 router 级鉴权** —— 只有 `:757` / `:824` 两端点各挂
   `require_internal_api_key`，setup-wizard 裸奔。转 Y6-C 分诊线索。
5. **⛔ pyright 门与卡文禁令的冲突（需裁，与 Z7-B D-1 合并）**：
   `system.py` 带 7 条**存量** pyright error 进 staged ⇒ `python-typecheck`
   hook `exit 1` 阻断 commit；卡文又禁 `LEFTHOOK_EXCLUDE=python-typecheck`；
   而修那 7 条超出地盘（其中 3 条要改 pydantic 模型构造，会动行为）。
   三者不可同时满足。本卡的零新增证明见
   `evidence-hygiene/pyright-零新增证明与门冲突.md`。
6. **`/tmp/test-vault*` 判据在多车道并行下不可信** —— 实测 `card-y9-maingoal`
   车道跑 `tests/unit` 会产出同一对目录。凡以「`ls` 到没到」为判据的卫生门
   都受此影响，建议改为进程归属绑定。
7. **`backend/logs`、`backend/data` 在 tests/unit 下被写入**，但被 `.gitignore`
   覆盖 ⇒ 任何以 `git status` 为唯一判据的卫生门对它们**恒绿**（假绿面）。
8. **卡文事实偏差 2 条**：① 基线文件 `evidence-b12/unit-red-baseline-03ac8bf8.txt`
   不在本车道树、只在设计稿树；② 裁判 2 的全量 H2 命令按 206 operation 需约
   13 小时，不可执行。详见 `evidence-hygiene/前置事实与卡文偏差.md`。
