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

### 🎯 H2 复现出与冻结证据逐条吻合的污染（详见 `定位结论-a-h2.md`）

> **措辞收窄（Codex round-1 批评「唯一历史真凶超出证据范围」，成立）**：
> 本卡证明的是「**这条链在改前代码上能完整复现该污染形态**，产物与冻结证据树
> 逐条吻合」；**没有**证明「冻结证据那次污染就是它干的」。
> 理由：`CLAUDE.md` 的 sha256 一致只说明**是同一段代码写的** —— 骨架内容由
> `VAULT_DIRECTORIES` + `CLAUDE_MD_SKELETON` 两个常量完全决定，任何调用
> `initialize_vault()` 且路径解析到 `backend/` 的途径都会产出逐字节相同的东西。
> 那是「同一段代码」的证据，不是「同一次运行」的证据；冻结证据是历史快照，
> 本卡没有那次运行的进程级记录。
>
> 可以确定的是：**台账原归因（`test_vault_init_service.py`）被证伪**
> —— 那 8 个用例全走 `tmp_path`，且 `tests/unit` 目录级跑完 `backend/` 三处判据全空。

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

#### 主论证（绑定本进程输出，与并行无关）—— Codex round-1 指出后改用

两次单跑的 pytest **captured stdout 里有被测进程自己写的结构化日志**：

```
node1: "path": "/private/tmp/test-vault/CLAUDE.md",        "event": "claude_md_created"
node2: "path": "/private/tmp/test-vault-wizard/CLAUDE.md", "event": "claude_md_created"
```

这是 `VaultInitService` 在**本进程内**打的日志（`vault_init_service.py:99`），
别的车道的进程写不进我的 pytest 输出。它直接把「谁写的、写到哪」绑死，
不依赖任何关于并行行为的假设。

修后同一判据反向成立（`three-files-after.txt`）：

```
"path": ".../pytest-of-Heishing/pytest-18016/test_endpoint_exists0/test-vault/CLAUDE.md"
grep -c '/private/tmp/test-vault' → 0
```

即改后本进程写的是 `tmp_path`，`/private/tmp` 零命中。

**H2 侧同一判据更强**（日志路径直接含本 worktree 名，并行干扰在逻辑上不可能）：

```
改前 h2-directed:       "path": ".../worktrees/card-y6-testhygiene/backend/CLAUDE.md"
改后 h2-directed-AFTER: grep -c 'claude_md_created' → 0
```

改后**连日志都没有** —— 请求被 `field_validator` 拦在 pydantic 层，
根本没走到 `initialize_vault()`。这同时验证了「污染消失」和「消失的原因是
校验器生效」两件事，而不只是「文件碰巧没出现」。

完整落盘：`evidence-hygiene/写入归因-本进程日志.txt`。

#### 弱论证（保留记录，但不作为依据）

我原本的理由是：并行车道的污染**成对**出现（两用例连着跑、间隔 ≈5s，
与各自 5.48s/5.49s 的耗时吻合），而我的两次单跑各自只产生一个。
**Codex round-1 指出这条不足以排除并行干扰** —— 它只是让并行解释变得不太可能，
并没有排除它（例如另一车道恰好只跑到一半、或恰好只跑了其中一个用例）。
该批评成立，故上面改用本进程日志作主论证。「成对 vs 单个」降级为旁证。

---

## 二 台账归因勘误（车道不改台账，此处只写待登记条目）

**原句**（`未合卡追踪台账.md:48` Z4-A 行 与
`2026-09-05-第十一批复核裁定与待裁决登记.md:54`，两处同文）：

> ~~`test_vault_init_service.py` 目录级运行把 vault 骨架写进 `backend/`~~

**实测划改为**：

> `backend/` 内的 vault 骨架，**台账归给 `test_vault_init_service.py` 缺乏支持**；
> 本卡实证「能产生该现场」的写入链是
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
> `test_vault_init_service.py` 的归因**缺乏支持**：其 8 个用例全部经
> `vault_dir(tmp_path)`（**这是我的源码核对陈述**，Codex 按读取边界未独立验证），
> 且该文件在 tests/unit 红基线里 0 条；`tests/unit` 目录级跑完 `backend/` 三处判据全空
> —— 后者只支持「**该配置下**未复现」，不排除其他测试集合／顺序／写后清理的情况。

---

## 三 (b) 守卫面修改

### ① `SetupWizardRequest.vault_path` 加绝对路径校验（`system.py`）

> **契约边界（Codex round-1 #4 指出后收窄）**：这道校验的契约是
> **「拒绝相对路径与空串」**，**不是**「保证 `resolve()` 后的目标不在仓库内」。
> 明确不在契约内的形态：仓库的完整绝对路径、该路径加 `/.`、指向仓库的绝对符号链接
> —— 它们都能通过 `is_absolute()`；另有含 NUL 的绝对字符串会通过校验、
> 随后在 `resolve()` 抛 `ValueError`（既有行为，改前同样如此，本卡未改善也未恶化）。
> 已登记为独立卡，见 §八。**把「语法上绝对」当成「解析后的目标安全」是错误推理**，
> 本单其余处的措辞已按此收窄。

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

> **能力边界（Codex round-1 #5 指出后收窄）**：它是**末态增量检查**，
> 变红发生在「fixture 启动后的观察窗口内」并以 session teardown 报错的形式出现
> —— 不是「任何时刻立刻变红」。已知盲区：`raw/` 内新增文件（只测顶层存在性）、
> 写后自行清理、fixture 启动**前**已存在的污染、从仓库根 cwd 写出的骨架
> （fixture 固定盯 `backend/`）、xdist 下各 worker 无统一快照边界。
>
> 另：我原先说「setup 与 teardown 共用同一快照函数 ⇒ 不会假红」**说宽了**。
> 共用函数只消除「两侧逻辑不同」这一种假红源，消除不了「两次可观测性不同」——
> `conftest.py:77` 把读取失败记 `None`，于是 `None ↔ hash` 会被报成「文件改写」，
> 两边都 `None` 则静默通过。**「内容改变」与「检查无法完成」当前没有区分。**

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

#### ⚠️ commit 后地盘门变成**四**个文件（`backend/openapi.json`，非本卡主动改）

```
backend/app/api/v1/system.py
backend/openapi.json          ← 多出来的
backend/tests/unit/conftest.py
backend/tests/unit/test_startup_health_check.py
```

**来源已查清，是仓库强制机制、不是越界**：`lefthook.yml` 的 `spec-sync` hook
（CARD-DEBT-openapi-sync，第八批立）在 pre-commit 时检测到 `backend/app/api/**`
变更，自动跑 `check-openapi-drift.py --write` 重生成快照并 `git add`；
该 hook 注释明写「禁手改快照」，重生成失败即 `exit 1` 阻断 commit。
也就是说：改了 `backend/app/api/**` 就**必然**带上这个文件，别无选择。

实际 diff 只有两处：

```
- "description": "Path to the Obsidian vault directory"
+ "description": "Absolute path to the Obsidian vault directory"      ← 本卡改 Field 的必然衍生
- "x-generated-at": "2026-09-05T01:36:01..."
+ "x-generated-at": "2026-09-05T18:58:07..."                          ← hook 注释说明它恒变
```

**一个值得记的事实**：`field_validator` 的约束**没有**进 JSON Schema ——
它是运行时校验，不像 `min_length` 那样会写成 schema 约束。快照里
`vault_path` 仍是无约束的 `{"type": "string"}`。

推论（与实测吻合）：schemathesis **仍会**生成非绝对路径输入，只是现在拿到 422
而不是把目录建进仓库；422 是 FastAPI 为带 body 的端点自动声明的响应码，
`status_code_conformance` 照样通过 —— 这正好解释了为什么改后那条 contract 测试
的失败原因（`DeadlineExceeded`）与改前逐字同型。
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

#### ⚠️ (e) 判据本身带 flaky 面（Codex round-1 发现，我已独立核实）

Codex 指出：**H1（改前那轮）**的红集合与基线相比虽同为 247 条，却有**一增一减**。
我实测确认：

| 用例 | H1（改前） | 裁判 6（改后） | 失败正文 |
|---|---|---|---|
| `test_candidate_service.py::test_accept_candidate_already_accepted_returns_422` | FAILED | 通过 | `live Neo4j port connect attempted` |
| `test_mock_degradation_transparency.py::...::test_mock_mode_logs_warning` | 通过 | FAILED | `live Neo4j port connect attempted` |

两条变化的失败正文**都是 W4 端口门哨兵**。该哨兵报的是「**本用例期间**有 N 次到
现网 Neo4j 的连接尝试」，而越界连接常来自异步任务/后台线程，**归到哪个用例
取决于时序** —— 同一次越界连接会在不同轮次被记到不同 nodeid 上。

**对本卡结论的影响：无。** 差异出现在我改代码**之前**那轮（H1）上；
而改后的裁判 6 与基线 `diff` 完全为空，两轮收工彼此逐字相同。

**对方法的影响：有，须登记。** tests/unit 的红集合在 **nodeid 层面并不稳定**，
即使总数稳定在 247。(e) 的「逐 nodeid diff 必须为空」判据带 flaky 面 ——
本卡这次为空，有一部分是归属恰好一致。**下一张卡可能因同样的时序漂移被误判为
引入回归**，见 §八.10。

（附注：Codex 在只读面里拿不到那份外部基线文件——我的 prompt 只给了 evidence
目录——所以它用 H1 log 当基线。它的视角与我的判据不冲突，两个发现都成立。）

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
| 9 | 地盘门 | ✅ 三文件 + `openapi.json`（spec-sync hook 强制同步，见 §五）；禁改文件 5 项全零改动 |
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
7. **未证明这道门在 `pytest-xdist`（`-n`）下的行为**。本卡全程顺序跑
   （卡文要求二分需固定顺序）。venv 里装着 xdist 3.8.0，而 session 级 fixture
   在 xdist 下**每个 worker 各执行一次** setup/teardown ——
   多个 worker 的快照窗口互相重叠时会不会互相误报，本卡没测。
8. **未证明本卡引入的假红不会阻断别的车道**。这道门只在本 worktree 的
   `tests/unit` 生效，理论上不影响别人；但合并到主干后，**所有**车道跑
   `tests/unit` 都会带上它，届时 `/tmp` 那段判据的假红面就会扩散到全批。
   这是合并前应当裁掉或收窄的（见 §八.6）。
9. **未证明 `field_validator` 对非 pytest 的真实调用方无副作用**。全仓 grep 显示
   setup-wizard 只有测试在调、前端零引用（与 §七.5 同源），但未做真实部署验证；
   若将来有客户端传相对路径（过去会「成功」地在 cwd 建 vault），现在会收到 422
   —— 这是**有意的行为变更**，不是回归，但使用方需要知道。

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
8. **`backend/openapi.json` 使地盘门必然多一个文件**：`spec-sync` hook 对
   `backend/app/api/**` 的任何改动都会重生成并 stage 该快照，且失败即阻断 commit。
   凡「地盘门 ⊆ N 个文件」类卡文，只要 N 里含 `backend/app/api/**`，就应预先把
   `backend/openapi.json` 计入，否则每张这类卡都会在收尾时撞一次。
9. **⛔ (e) 的逐 nodeid diff 判据带 flaky 面（Codex round-1 发现，已独立核实）**：
   W4 端口门哨兵按「本用例期间的连接尝试」归属，而越界连接来自异步任务/后台线程，
   归到哪个 nodeid 取决于时序。实测同一批红在 H1 与裁判 6 两轮之间发生「一增一减」
   （`test_accept_candidate_already_accepted_returns_422` ↔ `test_mock_mode_logs_warning`），
   两条正文都是该哨兵。**总数稳定 ≠ nodeid 集合稳定**。
   建议：(e) 类判据改为「新增项的失败正文必须不是 W4 哨兵」，或对哨兵归属做去抖，
   否则下一张卡可能被这个时序漂移误判成引入回归。
10. **路径守卫只做到语法层 = 独立卡**（Codex round-1 #4）：`is_absolute()` 通过、
    但 `resolve()` 后仍落在仓库内的形态 —— 仓库完整绝对路径、该路径加 `/.`、
    指向仓库的绝对符号链接 —— 本卡不拦；含 NUL 的绝对字符串通过校验后
    `resolve()` 抛 `ValueError` 且未转成 422（**改前即如此**，本卡未改善未恶化）。
    若要「保证目标不在仓库内」，需要 `resolve()` 之后的目标域校验，那是另一张卡。
11. **卡文事实偏差 2 条**：① 基线文件 `evidence-b12/unit-red-baseline-03ac8bf8.txt`
   不在本车道树、只在设计稿树；② 裁判 2 的全量 H2 命令按 206 operation 需约
   13 小时，不可执行。详见 `evidence-hygiene/前置事实与卡文偏差.md`。
