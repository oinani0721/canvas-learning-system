# UAT — CARD-HYGIENE-openapi（schemathesis 合约测试排除写端点）

> 批次: `BATCH-2026-09-07-第十三批` · 车道 `card-u5-lance`（分支 `card/u5-lance`）· U5 末卡
> 起点 HEAD（U5-C 末 commit）: `ce1e085b`
> 卡文: `_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U5-D.md`（feature 主干树）
> 证据目录: `_bmad-output/审查/evidence-hyg-openapi/`
> 落地日期: 2026-09-09

---

## 〇 第 0 分钟（完成条件 (a)）

| 项 | 实测 |
|---|---|
| `pwd` | `…/.claude/worktrees/card-u5-lance` ✅ |
| 分支 | `card/u5-lance` ✅ |
| HEAD | `ce1e085b`（U5-C 末 commit `docs(red-r): 27 条零代码定性分派表`）✅ |
| `git status --porcelain` | 空 ✅ |
| `test -e backend/.venv/bin/pytest` / `backend/.env` | 两项均在 ✅ |
| 开工污染（五项 `ls \| grep`） | `rc=1`（`CLAUDE.md` / `outputs` / `raw` / `wiki` / `test_canvas` 全不在）✅ |

**schemathesis 版本与两签名实测**（存档 `api-signature-20260909T160120.txt`）：

- `schemathesis.__version__` → **`4.14.3`** ✅（与卡文 §〇 第 2 行一致）
- `BaseSchema.include(self, func=None, *, name, name_regex, method, method_regex, path, path_regex, tag, tag_regex, operation_id, operation_id_regex) -> BaseSchema` ✅
- `BaseSchema.exclude(…同 kwargs…, deprecated: bool = False) -> BaseSchema` ✅

**卡文 §〇 file:line 逐条核对**（全部一致，无勘误）：
`test_openapi_contract.py` 的 `:17 importorskip` / `:18 from app.main import app` / `:19 from hypothesis` /
`:27 from_asgi` / `:36`（注释行）/ `:37 @schema.parametrize()` / `:38-42 @settings` / `:43 def test_api_contract(case)` /
`:91 class TestCanvasWorkflow`；`vault_init_service.py:18-23 VAULT_DIRECTORIES` / `:93-95 .gitkeep` /
`:96-98 CLAUDE.md` / `:103`（注释行）/ `:104 self._ensure_gitignore(root)` / `:106 return`。

---

## 一 改前证据（完成条件 (b)）

### ⓪ 先红实证 —— 裁定 **(乙)**（手册 §四.5 D-25），一次性 scratch worktree

| 步 | 实测 |
|---|---|
| scratch | session scratchpad 下 `hyg-openapi-prered`，`worktree add … da690bf8`，HEAD 实测 `da690bf8` ✅ |
| venv | symlink → `card-v5-lance/backend/.venv` ✅ |
| `.env` | 见下方「⚠️ 卡文前提不成立」 |
| 哨兵 | `$EV/prered-sentinel` mtime `2026-09-09T16:02:36`（落在车道树，scratch 删掉也还在）✅ |
| 选择器自证 | `--collect-only … -k setup-wizard` → **1/207 collected（206 deselected）**，证明 `-k` 不是空筛选 ✅ |
| 真跑 | `pytest -q -p no:cacheprovider tests/contract/test_openapi_contract.py -k setup-wizard --hypothesis-seed=0` → **rc=1**，`1 failed, 206 deselected`，用时 272.91s |
| 失败模式 | `hypothesis.errors.DeadlineExceeded: Test took 10851.06ms, which exceeds the deadline of 10000.00ms`（另 11 个 explicit examples 同因失败）—— **不是** 500 / PermissionError |
| 跑完立刻 `ls <scratch>/backend \| grep` 五项 | `rc=1`，**五项均未出现**；`git status --porcelain backend/` 亦为空 |
| 拆除 | `worktree remove --force` → `remove_rc=0`，worktree list 命中 0，目录 `GONE` ✅（不留隔夜） |

**⚠️ 卡文 (b)⓪ 第 1 步的前提不成立 —— 如实登记处置**：
卡文写「`cp` 车道树 `backend/.env` 过去（先 `grep -n 7691` 确认无现网 URI）」。
实测车道树 `backend/.env:67 NEO4J_URI=bolt://localhost:7691` —— **就是现网**，
且 `:31 VAULTS_ROOT` / `:33 CANVAS_BASE_PATH` 指向 live vault `canvas-vault`。
按 §三 硬边界（禁连 7691/7687、禁写 live vault），**未原样 cp**：scratch 副本里把
`NEO4J_URI` 改指不可达的 `bolt://127.0.0.1:7699`、把 `VAULTS_ROOT`/`CANVAS_BASE_PATH`
改指 scratch 内的 `_scratch_vaults`（`grep -c '7691\|7687'` 改后为 0）。
`setup-wizard` 的写面来自请求体 `vault_path`、与这三个配置无关，故该处置不影响实证保真度。
（另：`tests/conftest.py:26-28 live_port_guard.install()` 是第一道门，本次全程
`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。）

**三处扫描面结果**（存档 `prered-scan-full-{tmpdir,home,scratch}-20260909T160236.txt`、
判定 `prered-scan-verdict-20260909T160236.txt`）：

| 扫描面 | `find -newer prered-sentinel -maxdepth 3` 行数 |
|---|---|
| `$TMPDIR` = `/var/folders/vq/…/T/` | 1918 |
| `$HOME` = `/Users/Heishing` | 90 |
| `<scratch>` | 10 |
| **合计** | **2018** |

对这 2018 行做骨架名过滤（basename ∈ `{CLAUDE.md, raw, wiki, outputs, test_canvas, .gitkeep}`）
→ **命中 0 行**。

> ⚠️ 首轮扫描的 tee 存档被 `head -60` 截断，已重跑**不截断**版本并单独落档；结论以不截断版为准。
> ⚠️ 噪音声明：本机同时有多条并行车道 session 在跑，`$TMPDIR`/`$HOME` 的命中绝大多数
> 与本卡无关（其它 pytest 的 `pytest-of-Heishing/`、codex 的 sqlite、macOS 系统文件）。

**⓪ 结论（按卡文第 5 步逐字回填，⛔ 不保留「未实测」旧措辞）**：
**已实测** —— 改前在一次性 scratch 里跑过一次（`-k setup-wizard`、`--hypothesis-seed=0`），
**本次未复现**写盘，且只在上述三处扫描面内为真。失败模式是 `DeadlineExceeded`，
即 hypothesis 在 explicit 阶段就因超时抛出，未走到大量随机 `vault_path` 的生成阶段。

### ① collect-before（车道树只读）

`collect-before.txt` 共 **207** 行 = `test_api_contract[...]` **206** 条
+ `TestCanvasWorkflow::test_canvas_crud_workflow` 1 条。
含 `tests/contract/test_openapi_contract.py::test_api_contract[POST /api/v1/system/setup-wizard]`（命中 1）✅

**⚠️ 卡文 §二.2 抽取式勘误（实测，已按卡文「先查抽取式再下结论」执行）**：
卡文写 `pytest --collect-only -q … | grep '^tests/'`，本机实测抽到 **0 行**。
根因：`backend/pytest.ini:19-21 addopts = -v --tb=short`，pytest 的 verbosity 是**代数和**，
`-v`(+1) 与命令行 `-q`(−1) 抵消为 0 ⇒ 输出落回树形（`<SchemathesisFunction test_api_contract[…]>`），
不是 nodeid 行。改用 **`-q -q`**（verbosity −1）后抽取式成立。
未改 `pytest.ini`（非本卡地盘）。

### ② 源码链原文

- `app/api/v1/system.py:456 @router.post("/setup-wizard")` → `:466 vault = Path(request.vault_path).resolve()`
  → `:467-470` 黑名单仅 `("/", "/etc", "/usr", "/var", "/tmp", "/System")` → `:471 if ".." in request.vault_path`
  → `:474 svc = VaultInitService()` → `svc.initialize_vault(str(vault))`
- `app/services/vault_init_service.py:18-23 VAULT_DIRECTORIES = ["raw", "wiki/concepts", "wiki/canvases", "outputs/exam_boards"]`；
  `:88 dir_path.mkdir(parents=True, exist_ok=True)`；`:92-94 gitkeep.touch()`；
  `:96-98 claude_md.write_text(CLAUDE_MD_SKELETON)`；`:104 self._ensure_gitignore(root)`；`:106 return`
- `system.py:430-455 _must_be_absolute`（Y6-A）只拒**相对路径/空串**；`field_validator` 不进 JSON Schema
  ⇒ 生成面仍覆盖任意**绝对**路径，写面是挪走了不是消失。

### ③ 冻结污染现场（只读实物核对）

`card-z4-redbase @ c8611a89` **仍在** worktree list。该树 `backend/` 下四项俱在
（存档 `frozen-scene-20260909T160156.txt`）：

```
CLAUDE.md  type=Regular File  mtime=2026-09-05T10:13:14
outputs    type=Directory     mtime=2026-09-05T10:13:14
raw        type=Directory     mtime=2026-09-05T10:13:14
wiki       type=Directory     mtime=2026-09-05T10:13:14
```

---

## 二 契约覆盖面收窄（完成条件 (c)）

### 改动

`test_openapi_contract.py` 的 `from_asgi` 改为链式过滤（最终态，含 Codex round-2 整改）：

```python
schema = (
    schemathesis.openapi.from_asgi("/api/v1/openapi.json", app)
    .include(method_regex=r"^(GET|HEAD)$")
    .exclude(path_regex=r"^/api/v1/health/lancedb$")
    .exclude(path_regex=r"^/api/v1/review/fsrs-state/\{concept_id\}$")
    .exclude(path_regex=r"^/api/v1/health/storage$")
    .exclude(path_regex=r"^/api/v1/multimodal/health$")
)
```

`@schema.parametrize()` 与 `@settings(max_examples=10, …)` **未动**（`max_examples` 未改大也未改小）。

### 数字对账（最终态）

| 量 | 值 | 出处 |
|---|---|---|
| `T_BEFORE`（改前 `test_api_contract[` 条数） | **206** | `collect-before.txt` |
| `G`（改前 GET/HEAD 条数） | **93**（GET 93 / HEAD 0） | `collect-before.txt` |
| `EXTRA`（会写盘、故追加排除的只读条数） | **4** | 见下「剩余 GET 面写原语复核」 |
| `T_AFTER`（改后 `test_api_contract[` 条数） | **89** | `collect-after.txt` |
| `N`（`comm -23` 差集行数） | **117** | `excluded-operations.txt` |

**改前 method 分布**：POST 96 / GET 93 / DELETE 9 / PUT 6 / PATCH 2 = 206 ✅
**被排除 method 分布**：POST 96 / DELETE 9 / PUT 6 / GET 4 / PATCH 2 = 117 ✅

> 中间态（Codex round-2 整改前）为 `EXTRA=1 / T_AFTER=92 / N=114`，正控当时同样全 PASS，
> 存档 `collect-verdict-20260909T161913.txt`。整改后的 `collect-after` 是中间态的**真子集**
> （新增 0 行，恰移除那 3 条），存档 `collect-verdict-r2-20260909T214525.txt`。

### ⛔ 正控（口径修订如实登记）

卡文写死 `T_AFTER == G`，但 (c) 同时要求「剩余 GET 面写原语命中即追加排除」。
本卡**确有命中**（最终 4 条），两条要求在此互斥 ⇒ 正控参数化为 `T_AFTER == G − EXTRA`，
并补一条独立对账 `T_BEFORE == T_AFTER + N`。两条合起来仍堵死「全被排掉」
（那时 `T_AFTER = 0`，正控-2 失败）。

| 正控 | 判据 | 实测 | 结论 |
|---|---|---|---|
| 正控-1 | `T_AFTER == G − EXTRA` | `89 == 93 − 4` | **PASS** |
| 正控-2 | `T_AFTER > 0` | `89 > 0` | **PASS** |
| 正控-3 | `T_BEFORE == T_AFTER + N` | `206 == 89 + 117` | **PASS** |
| 正控-4 | 点名 GET nodeid 仍在 `collect-after` | `test_api_contract[GET /]` 命中 **1** | **PASS** |
| 正控-5 | 整改后 `collect-after` ⊆ 整改前 | 新增 **0** 行，恰移除 3 条 | **PASS** |

其余既有判据：`collect-after` 的 `setup-wizard` 计数 **0** ✅；
`grep -vE '\[(GET\|HEAD) ' collect-after \| grep 'test_api_contract\['` **空** ✅；
四条会写盘的 GET（`health/lancedb`、`review/fsrs-state/{concept_id}`、`health/storage`、
`multimodal/health`）均已不在 `collect-after`（各命中 0）✅。

### 剩余 GET 面写原语复核

扫描面 = `backend/app` **全树**所有 `<任意名>.get(...)` 装饰的 handler，
正则 `mkdir|write_text|write_bytes|os.replace|save_state|add_documents|drop_table|append_event|subprocess`。

> ⚠️ **扫描面修正如实登记**：初版把装饰器基名限死为 `router`/`app`，只扫到 **28** 个 handler，
> 与收集到的 93 条 GET 对不上 —— 划窄的搜索面会把「没扫到」伪装成「没有」。
> 修正后扫到 **93** 个（装饰器基名 27 种别名 + `app.get` 的 `GET /`），
> **93 == 93**，这个相等本身就是扫描面完整性的证据。

**(1) 直接命中 1 条**（作者的 AST 扫描）：

| 位置 | handler | 原语 | 实际写面 |
|---|---|---|---|
| `app/api/v1/endpoints/health.py:1139` | `check_lancedb_health` | `mkdir` | `lancedb_path = getattr(settings, "lancedb_path", "./data/lancedb")` 是**相对路径**，随后 `db_path.mkdir(parents=True, exist_ok=True)` ⇒ 从 `backend/` 起跑会造出 `backend/data/lancedb/` |

**(2) 间接命中 3 条**（Codex round-2 补出，作者已逐条独立核过源码）：

> ⚠️ 这三条正是上面那句「只覆盖一层直接文本」的**已声明局限**所漏掉的。
> 声明局限不等于免除责任 —— 独立审查把局限变成了实际缺陷，本卡按同一条规则（(c)
> 「命中即追加排除」）处置。

| 等级 | GET operation | 写链（作者复核确认） |
|---|---|---|
| **HIGH** | `GET /api/v1/review/fsrs-state/{concept_id}` | `endpoints/review.py:1430` → `review_service.get_fsrs_state()` → 该 concept 无卡且不受 frontmatter 管辖时 auto-create 默认卡 → `_save_card_states()`(`review_service.py:2507`) → `:600 mkdir` + `:604 write_text` + `:605 replace`，目标 `_CARD_STATES_FILE`(`:116-118` = `backend/data/fsrs_card_states.json`) |
| MEDIUM | `GET /api/v1/health/storage` | `endpoints/health.py:1671` → `_check_json_health()` → `:1444` 默认 `./data` → `:1448 mkdir` → `:1452-1453` `.health_check` `touch()`/`unlink()` |
| MEDIUM | `GET /api/v1/multimodal/health` | `endpoints/multimodal.py:251` → `multimodal_service.get_health_status()` → `:1034-1036` `.health_check` `write_text()`/`unlink()` |

⇒ 四条已全部追加 `.exclude(path_regex=...)`，逐条理由单列于文件头注释。

**其中 HIGH 那条同时更正了作者的一处归因错误**：首轮 `find -newer` 命中的
`data/fsrs_card_states.json`（mtime `2026-09-09T18:26`，落在全跑**中途**）被作者归因为
「app lifespan 与运行期写入」，实为该 GET 在**请求期**写的。

**该扫描的边界（如实，修正后仍然存在）**：作者的 AST 扫描只覆盖 handler 函数体**一层
直接文本**；`health/storage` 与 `multimodal/health` 这类「探针写完即删」的写入，
连跑完后的 `find -newer` 也看不见 —— 只能靠读调用链发现。
本卡**未**对剩余 89 条 GET 做逐条调用链审计，Codex 也只在授权读取面内查到这三条。

---

## 三 零写门（完成条件 (d)）

新文件 `backend/tests/contract/conftest.py`：

- `_BACKEND_ROOT = Path(__file__).resolve().parents[2]` —— 与进程 cwd 无关。
  实测：从**车道树根**（不是 `backend/`）加载该模块，`_BACKEND_ROOT` 仍解析为
  `…/card-u5-lance/backend` ✅
- `_SKELETON = ("CLAUDE.md", "raw", "wiki", "outputs", "test_canvas")`
- `@pytest.fixture(scope="module", autouse=True)`，跑前命中 → `pytest.fail("污染现场已存在: …")`；
  跑后命中 → `pytest.fail("本次合约测试把 vault 骨架写进了 backend/: […]")` 并列 `mtime`
- fixture 自身**零写**：只 `Path.exists()` 与 `os.stat()`，不 touch、不 mkdir
- 断言**未**降级为 warning

---

## 四 裁判结果

### (e) 改后全跑 + 零写判据 —— 跑了**两轮**（Codex round-2 整改后重跑）

| | 首轮（`EXTRA=1`，92 operation） | **终轮**（`EXTRA=4`，89 operation） |
|---|---|---|
| 存档 | `contract-after-20260909T162042.txt.gz` + `.summary.txt` | `contract-after-r2-20260909T214642.txt` |
| 哨兵 | `sentinel`（16:20:42） | `sentinel-r2`（21:46:42） |
| 结果 | `92 failed, 1 skipped`，**4:55:14** | `89 failed, 1 skipped`，**5:06:32** |
| `rc` | **1**（如实） | **1**（如实） |
| 判据 3-a（`git status` 排除本卡两文件） | 0 行 ✅ | 0 行 ✅ |
| 判据 3-b（五项骨架 `test -e`） | 无 POLLUTED ✅ | 无 POLLUTED ✅ |
| 判据 3-c（`find -newer`） | **6 条，未通过** ❌ | **2 条，仍未通过** ❌ |

> `rc=1` 的含义：92 / 89 条全部 `DeadlineExceeded` —— `@settings(deadline=10000)` 对本机
> app 响应过紧。这是**存量契约红**，卡文明示「本卡判据是零写，不是契约全绿」，登记不修。
>
> 判据 3-a′（未排除版原始输出）首轮是 2 行（` M test_openapi_contract.py` + `?? conftest.py`），
> 恰好只有本卡自己那两个文件；终轮是 0 行（两文件此时已 commit）。

#### ⛔ 判据 3-c 两轮均未通过 —— 逐条归因，不放宽判据

**首轮 6 条**（存档 `find-newer-attribution-20260909T211708.txt`）：全部被 gitignore 覆盖、
全部不在五项骨架内。其中 `.ruff_cache/...` 是作者自己跑 ruff 造成的（裁判自身副作用）。
作者当时把其余 5 条归因为「app lifespan 与运行期写入」——**这个归因不够精确**，
被 Codex round-2 纠正（见下）。

**终轮 2 条**（存档 `find-newer-attribution-r2-20260909T....txt`）：

| 文件 | mtime | 归因 | 处置 |
|---|---|---|---|
| `logs/memory-system-2026-09-09.log` | `22:06:45`（开跑后约 20 分钟，**跑中**） | 被保留的 health 系 GET 在请求处理中经 `memory_logger` 写的**日志**（`endpoints/health.py:849/853/865/883/909`） | **登记不排除**：可观测性输出，`.gitignore:192 logs/` 覆盖，非 vault 骨架；为它排除整个 health GET 面，覆盖损失远大于收益 |
| `app/data/vault_index_pending__canvas_vault.jsonl` | `2026-09-10T02:53:30`（= `21:46:42 + 5:06:32`，**跑结束时刻**） | app **关闭时**持久化，非任何单个 GET 触发 | **登记不排除**：排除任何 GET 都消不掉它；`.gitignore:253` 覆盖；非 vault 骨架 |

#### ✅ 两轮对照实测确认了 Codex round-2 HIGH-1

排除 `GET /api/v1/review/fsrs-state/{concept_id}` 后，`data/fsrs_card_states.json` 的 mtime
**停在 18:26:21**（首轮时间），终轮全程未被写。`llm_call_logs.db`（16:21:24）与
`qa_metrics.db`（17:20:56）同理停在首轮时间。

**这不是推理，是两轮全跑的对照实测** —— 命中从 6 条降到 2 条，降掉的正是 Codex 指认的那条
及两个只在首次创建时写的文件。

### (f) 负控二 —— fixture 面对预置骨架必红

存档 `negctl2-fixture-20260909T162541.txt`，`rc=0`（3 条断言用例全通过）。
⛔ 探针**只落在 pytest `tmp_path` 镜像目录**，真 `backend/` 全程未被碰
（跑后五项 `test -e` 仍全不在）。

| 用例 | 断言 | 结果 |
|---|---|---|
| `test_reddens_when_skeleton_appears_after_run` | 跑后出现 `raw` → 红，正文逐字含「本次合约测试把 vault 骨架写进了 backend/」+ `raw` + `mtime=` | ✅ |
| `test_reddens_when_dirty_before_run` | 跑前已有 `outputs` → 红，正文含「污染现场已存在」+ `outputs` | ✅ |
| `test_control_group_clean_mirror_stays_green` | 干净镜像全程绿（`StopIteration`，无 `Failed`）—— 证明上面两条**不是恒红** | ✅ |

控制组的前置条件**被断言**（`mod._present(mirror) == []`），不靠假设。

实测失败正文（节录）：

```
本次合约测试把 vault 骨架写进了 backend/: ['raw']
(root=…/pytest-22548/test_reddens_when_skeleton_app0/backend_mirror; 跑前这些项都不存在)
  - …/backend_mirror/raw (mtime=2026-09-09T16:25:41.660293)
```

`shasum -a 256 backend/tests/contract/conftest.py` 跑前/跑后：
`ba8734acf9221c1be7caf9a46742c34fe92b6fff72964121317ef653da82f071` —— **逐字节同** ✅

### (f) 负控一 —— 去掉过滤后 collect-only 应重现 setup-wizard

存档 `collect-negctl-20260909T211728.txt`。**只用 `--collect-only`，不真跑**；
EXIT trap 无条件还原；禁 `git stash` / `git checkout`。

| 步 | 实测 |
|---|---|
| 跑前 `shasum -a 256 test_openapi_contract.py` | `e2206057c7a770153ba9a32f93914cdfc68d43e5c87560ed859614f4536caeb2` |
| 去掉 `.include`/`.exclude`（脚本断言待替换片段恰出现 1 次，否则中止） | 替换 1 处 ✅ |
| 去过滤态 collect-only | **207** 行 / `test_api_contract[` **206** 条；`setup-wizard` 命中 **1**（`POST /api/v1/system/setup-wizard`）；`health/lancedb` 命中 **1** |
| 显式还原 | ✅（trap 亦兜底） |
| 还原后 `shasum` | 与跑前**逐字节同** ✅ |
| 还原后 collect-only | **93** 行 / `test_api_contract[` **92** 条；`setup-wizard` 命中 **0**；与 `collect-after.txt` **逐行相同** ✅ |

> 该负控跑在 Codex round-2 整改**之前**（当时 `T_AFTER=92`），故对照的是 92 条那一版。
> 整改后的 collect 面已由 `collect-verdict-r2-*.txt` 单独落档，且证明是 92 条那版的真子集。

### (g) 目录级三数对比

**⚠️ 开工基线未取得，如实说明**：卡文要「与开工对比」，但改前跑 `test_openapi_contract.py`
全跑 = 在长期树真跑写端点 = §三 硬禁，**开工基线拿不到**。
且该文件单跑实测约 5 小时，目录级若把它再跑一遍就是重复的 5 小时。
故 (g) 拆成两块，合并方式写明如下：

| 块 | 命令 | 结果 |
|---|---|---|
| 块 A：`test_openapi_contract.py` | (e) 终轮已单独跑过 | `89 failed, 1 skipped`（5:06:32） |
| 块 B：目录内其余 5 文件 | `pytest -q tests/contract --ignore=tests/contract/test_openapi_contract.py` | **`3 failed, 99 passed, 2 skipped`**（2:22），`rc=1` |
| **合并（目录级等价三数）** | 块 A + 块 B | **`92 failed, 99 passed, 3 skipped`** |

存档：`contract-dir-others-20260909T211904.txt` + `contract-dir-others-zerowrite-20260909T211904.txt`。
块 B 跑完的零写复核：五项无 POLLUTED、`git status` 排除本卡两文件后 0 行 ✅。

#### 块 B 的 3 红是**存量**，不是本卡 conftest 引入 —— 有对照基线

存档 `contract-dir-baseline-noconftest-20260909T212214.txt`。
手法：临时把本卡新增的 `conftest.py` 移出 `tests/contract/`（EXIT trap 还原，
禁 `git stash`/`git checkout`），重跑同一组文件。

| | 有本卡 conftest | 移走 conftest（基线） |
|---|---|---|
| 三数 | `3 failed, 99 passed, 2 skipped`（142.90s） | `3 failed, 99 passed, 2 skipped`（142.07s） |
| FAILED nodeid | `test_health_contract.py::test_health_contract[GET /api/v1/health]`、`test_node_id_patterns.py::TestNodeIdPatternConsistency::test_pattern_matches_json_schema`、`test_openapi_snapshot_drift.py::test_committed_snapshot_has_no_drift` | **三条完全一致** |
| W4 门计数 | `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=19 (blocked=19)` | 同 |

⇒ **逐条相同**，这 3 红是存量。`conftest.py` 的 `shasum` 移走前/还原后
`ba8734acf9221c1be7caf9a46742c34fe92b6fff72964121317ef653da82f071` **逐字节同** ✅

> 本卡不跑 `tests/unit` 目录级：协议 §3「改了什么面就跑那个面」，
> 本卡零 `backend/app` 改动，只须 `tests/contract` 本目录级。

### (g) lint

`ruff 0.15.9`（`pyproject.toml:101 line-length = 120`）：

- `ruff check` 两文件 → `All checks passed!`，`rc=0` ✅
- `ruff format --check` 两文件 → `2 files already formatted`，`rc=0` ✅

### 地盘门（§二.7）与入库卫生（(i)）

存档 `domain-gate-20260909T212721.txt` + `gate-anomaly-attribution-20260909T212805.txt`。

```
git diff --name-only --no-color ce1e085b HEAD -- . ':(exclude)_bmad-output'
→ backend/tests/contract/conftest.py
  backend/tests/contract/test_openapi_contract.py      （恰 2 行，⊆ 两文件 ✅）
```

**⚠️ 验伪锚一度显示 0，实为 `core.quotepath` 陷阱（如实登记）**：
「去掉 exclude 应多出 `_bmad-output/`」这条验伪锚初测为 **0**。
根因是 git 默认 `core.quotepath=on`，把中文路径转义成 `"_bmad-output/\345\256\241..."`（**带引号**），
`grep '^_bmad-output/'` 因此匹配不到。加 `-c core.quotepath=false` 后计数 **42**，
验伪锚成立 ✅。—— 若不查这一步，会得出「地盘门没有反证支撑」的错误结论。

| (i) 项 | 判据 | 实测 | 结论 |
|---|---|---|---|
| 单独 commit | 本卡自己的 commit | `3c064c9d` → `dddfc598` → `11dfe410` | ✅ |
| commit header ≤100 | `wc -m` | 94 / 86 / 86 | ✅ |
| body 行 ≤100 | `wc -m` 逐行 | 无超限 | ✅ |
| `*.stderr*` 不入库 | `git ls-files \| grep -E '\.stderr($\|\.)'` | **0** | ✅ |
| `.hypothesis/` 不入库 | `git ls-files backend/.hypothesis \| wc -l` | **202** | ❌ 见下 |

**⚠️ `.hypothesis` 判据未通过 —— 历史遗留，本卡未新增（如实登记）**：
卡文 (i) 要求该计数为 0，实测 **202**。查证：本卡 commit `3c064c9d` **未碰**任何
`.hypothesis` 文件（`git show --name-only` 命中 0）；`ce1e085b` 时已是 **202**，HEAD 仍 **202**
（`git ls-tree` 对照，数量未变）；最早入库于 `992a2d5a 2025-12-15 chore: backup before Epic
optimization`。`.gitignore:107` 对**已跟踪**文件不生效，这是历史债，不在本卡地盘。

**⚠️ `stderr` 计数一度显示 2**：那是 `_bmad-output/审查/` 下**别的卡**的证据档
文件名里含 "stderr"（`G4-9-evidence/census-stderr.txt`、`evidence-g29f1/stderr-not-tracked-*.txt`），
不是 `*.stderr` 后缀。收窄口径为 `grep -E '\.stderr($|\.)'` 后计数 **0** ✅。

**大存档处置**：首轮全跑原档 59,477,945 字节 / 106,172 warnings（绝大多数是同一条
`DeprecationWarning` 的重复），逐字全文入库不现实 ⇒ gzip 后入库（2,195,473 字节），
并另出 `contract-after-20260909T162042.summary.txt`（会话头 + 进度行 + 全部 92 条 FAILED
+ 结尾摘要 + `rc`，逐字抄自原档，未改写）。终轮存档 331KB 以内，原样入库。

### (h) Codex 独立审查（gpt-6-astra · ultra · 多轮直到绑最终 HEAD 且 BLOCKER/HIGH = 0）

| 轮 | 绑定 SHA | B | H | M | L | 存档 |
|---|---|---|---|---|---|---|
| round-1 | `3c064c9d` | 0 | 0 | 0 | **1** | `codex-review-CARD-HYGIENE-openapi-r1.md` |
| round-2 | `dddfc598` | 0 | **1** | **3** | 0 | `codex-review-CARD-HYGIENE-openapi-r2.md` |
| round-3 | `<R3_SHA>` | <R3_B> | <R3_H> | <R3_M> | <R3_L> | `codex-review-CARD-HYGIENE-openapi-r3.md` |

#### round-1 LOW-1 → 已整改（commit `dddfc598`）

注释里的覆盖面数字写成「保留 93 / 排除 113」，那是**追加排除 `health/lancedb` 之前**的值。
已改为当时实测的 92 / 114。纯注释修改，`collect-only` 结果与整改前**逐行相同**（行为未变）。

#### round-2 HIGH-1 + MEDIUM-2/3 → 已整改（commit `11dfe410`）

Codex 补出了作者扫描面的**已声明局限**（只扫 handler 函数体一层直接文本）漏掉的
**间接写**。作者已逐条独立核过源码，三条**全部成立**：

| 等级 | GET operation | 写链（作者复核确认） |
|---|---|---|
| **HIGH** | `GET /api/v1/review/fsrs-state/{concept_id}` | `endpoints/review.py:1430` → `review_service.get_fsrs_state()` → 无卡且不受 frontmatter 管辖时 auto-create → `_save_card_states()`(`review_service.py:2507`) → `:600 mkdir` + `:604 write_text` + `:605 replace` 写 `_CARD_STATES_FILE`(`:116-118` = `backend/data/fsrs_card_states.json`) |
| MEDIUM | `GET /api/v1/health/storage` | `endpoints/health.py:1671` → `_check_json_health()` → `:1444` 默认 `./data` → `:1448 mkdir` → `:1452-1453` `.health_check` touch/unlink |
| MEDIUM | `GET /api/v1/multimodal/health` | `endpoints/multimodal.py:251` → `multimodal_service.get_health_status()` → `:1034-1036` `.health_check` write_text/unlink |

**这条 HIGH 同时解释了首轮 `find -newer` 的一条命中**：`data/fsrs_card_states.json`
的 mtime 是 `2026-09-09T18:26`，落在全跑**中途**而非启动期 —— 作者首轮把它归因为
「app lifespan 与运行期写入」是**不够精确的**，它是被保留的那条 GET 在请求期写的。

⇒ 三条已全部追加 `.exclude(path_regex=...)`，逐条理由写进文件头注释。
整改后 `T_AFTER` 92 → **89**，`N` 114 → **117**（GET 被排除 4 条）。
正控重跑全 PASS：`89 == G(93) − EXTRA(4)`、`206 == 89 + 117`、点名 `GET /` 仍在。
且 `collect-after` 是整改前版本的**真子集**（新增 0 行，恰移除那 3 条）。

#### round-2 MEDIUM-4（检测边界）→ 登记不改，理由如下

Codex 指出零写门只查 `backend/` 顶层五个名称，若 vault 根是 `backend/<非五项名>/`
则骨架仍写进代码目录而门看不见。**这一条属实**，但：

- 卡文 (d) 把 `_SKELETON` 写死为这五项，扩大检测面超出本卡授权；
- Codex 自己也确认：对「vault 根恰好是 `backend/`」的完整初始化，
  `VaultInitService:18-23` 的目录被 `raw/wiki/outputs` 覆盖、`:96-98` 的文件被 `CLAUDE.md` 覆盖，
  **检测充分**；
- 该缺口已逐字写进 §六「本卡未证明什么」第 13 条与 §七 台账。

#### round-2 未完成归因项（Codex 明确标注，如实转录）

`llm_call_logs.db` 与 `qa_metrics.db` 的写者 **未完成归因**（Codex 说需要 `app/main.py`
的 lifespan 段与 `system.py` 两个统计 GET，超出本轮授权读取面）；
`vault_index_pending__canvas_vault.jsonl` 与 `memory-system-*.log` 只确认了
「存在请求期/后台写入机制」，**未闭合到本次全跑的具体写者**。
⇒ 登记为本卡未证明项，不写成「已确认是启动期写入」。

---

## 五 DoD-3 双段

### 4-A 技术段（贴证据）

| 完成条件 | 证据 | 结论 |
|---|---|---|
| (a) 第 0 分钟 + 版本/两签名 + 开工无污染 | `api-signature-20260909T160120.txt`；开工五项 `rc=1` | ✅ |
| (b)⓪ 裁定 (乙) scratch 修前实证 | `prered-20260909T160236.txt`（rc=1）、`prered-ls-*.txt`（五项 rc=1）、`prered-scan-full-*.txt`（骨架命中 0）、`prered-teardown-*.txt`（GONE） | ✅ 已执行，**未复现** |
| (b)① collect-before 含 setup-wizard | `collect-before.txt` 命中 1 | ✅ |
| (b)② 源码链原文 | 本单 §一.② | ✅ |
| (b)③ 冻结现场只读核 | `frozen-scene-20260909T160156.txt`，四项俱在 | ✅ |
| (c) 排除面 = 全部非 GET/HEAD + 追加 1 条 | `excluded-operations.txt` 114 行 | ✅ |
| (c) **正控** | 正控-1/2/3/3′/4 全 PASS（本单 §二） | ✅ |
| (c) 剩余 GET 写原语复核 | `get-handler-write-primitive-scan-20260909T161754.txt`，93 handler / 1 命中 / 已追加排除 | ✅ |
| (d) 零写 fixture | `backend/tests/contract/conftest.py`；跑前/跑后双断言 + mtime；自身零写 | ✅ |
| (e) 改后全跑 + 零写判据 | 见 §四 (e) 段 | <!-- E-VERDICT --> |
| (f) 两负控 | 负控一 `collect-negctl-*.txt`；负控二 `negctl2-fixture-20260909T162541.txt`（3/3） | <!-- F-VERDICT --> |
| (g) 目录级三数 + ruff | ruff check/format 两文件 `rc=0`；目录级见 §四 (g) 段 | <!-- G-VERDICT --> |
| (h) Codex 多轮绑 HEAD | 见 §四 Codex 段 | <!-- H-VERDICT --> |
| (i) 单独 commit、`.hypothesis` 不入库 | 见 §四 地盘门段 | <!-- I-VERDICT --> |
| (j) 两个必填锚 | §六（13 条）+ §七（16 条） | ✅ |

### 4-B 用户段（零技术词）

跑一遍接口体检后，代码目录里不会再莫名多出几个课程文件夹和说明文件；
体检只查「读」的那部分接口，会写东西的接口这次先不体检，并且列了清单
——我感觉工作目录干净了，也知道少查了什么。

**felt-sense**：以前跑完体检要先扫一眼目录、心里犯嘀咕「这几个文件夹是刚才冒出来的吗」，
现在不用犯这个嘀咕了：真冒出来，体检自己会红着脸停下来告诉我是哪几个、什么时候出现的。
代价我也看得见——清单上那 114 项这次没查，不是「查过了没问题」，是「没查」。
这两件事分得清，比假装都查过了让人踏实。

---

## 六 本卡未证明什么

**①′（最重要，按裁定 (乙) 的实测结果逐字回填）**：
先红实证**已按手册 §四.5 D-25 裁定 (乙)** 在一次性 scratch worktree（`da690bf8` 检出，
跑完即 `worktree remove --force`）里跑过一次（`-k setup-wizard`、`--hypothesis-seed=0`）。
结论：**本次未复现** —— scratch 的 `backend/` 五项均未出现，三处扫描面骨架命中 0 行。
失败模式是 `DeadlineExceeded`（10851ms > 10000ms），hypothesis 在 explicit 阶段就抛出。

**仍未证明的部分**：

1. **扫描面只覆盖 `$TMPDIR` / `$HOME` / `<scratch>` 三处、`maxdepth 3`**。`vault_path` 落在这三处
   之外的写面本卡**看不见**（全盘 `find /` 不可行，不做）。
2. 未在车道树 / 任何长期树复现（§三 硬禁，也不打算证）。
3. **单次固定 seed** 只覆盖 hypothesis 在 `--hypothesis-seed=0` 下生成的那些 `vault_path`，
   不代表其它 seed 的写面；且本次因 deadline 在 explicit 阶段即中止，
   **随机生成阶段的写面根本没被触达** —— 「未复现」尤其不等于「不会写」。
4. (d) fixture 的「跑后必红」只在 **tmp 镜像 + monkeypatch `_BACKEND_ROOT`** 下证明过，
   未在真 `backend/` 上制造过一次真实污染来验证（§三 硬禁在真目录放探针）。
5. `card-z4-redbase @ c8611a89` 冻结现场四项俱在，是**历史**污染的实物证据，
   不是本次实证的产物。

因此本卡证明的是「写端点不再进入合约测试的生成面 + 一旦写进来 fixture 会报警
+ 改前在受控 scratch 下的一次实测结果」，**不是**「改前一定在污染」，
也**不是**「改后一定不写盘」。

**另外未证明的**：

6. 未证明其它写端点（canvas / index / sync）在 `CANVAS_BASE_PATH="./test_canvas"` 相对路径下的
   写面**被修** —— 它们只是被**排除出合约测试**，端点本身未动。
7. 未证明 `setup-wizard` 对**任意绝对路径**的写面被修（归 U10-D / 后续卡：
   `system.py:467-470` 黑名单只 6 个目录）。
8. `max_examples=10` 下 GET 面未命中的分支不代表安全。
9. 未把合约测试接入 CI（Dredd 裁决页口径维持，登记）。
10. 未证明 4.14.3 与 `pyproject.toml:71-` `[tool.schemathesis]` 历史块的交互
    （本卡不改 `pyproject.toml`，列入 Codex 问题 ⑤）。
11. 收窄后 GET 面的契约红是**存量**，本卡不修（判据是零写，不是契约全绿）。
12. **GET handler 写原语扫描只覆盖 handler 函数体一层直接文本**；
    handler → service → 写盘的**间接路径未覆盖**（列入 Codex 问题 ②）。
13. 零写门只看 `backend/` **顶层**五项，不做全树扫描；端点写到 `backend/data/` 之类
    **不在五项内**的位置，本门看不见（`backend/data/` 实测早已存在，mtime `2026-09-08 06:46`，
    非本卡产生）。

---

## 七 台账待登记条目

1. **Y6-A 勘误「真写者 = 合约测试对写端点无 exclude」→ 本卡修复**：
   修复 sha `3c064c9d` → `dddfc598` → `11dfe410`；排除面 **117 条**（POST 96 / DELETE 9 / PUT 6 / GET 4 / PATCH 2），
   清单 `_bmad-output/审查/evidence-hyg-openapi/excluded-operations.txt`
   （分组版 `excluded-operations-grouped.md`）。契约覆盖面从 206 → **89**。
2. **`setup-wizard` 任意绝对路径写面**：Y6-A 的 `_must_be_absolute`（`system.py:430-455`）
   只拒相对路径/空串，`system.py:467-470` 黑名单只 6 个目录，`Path(...).resolve()` 对其余
   任意绝对路径照建 ⇒ **写面挪走了不是消失** → U10-D / 第十四批候选。
3. **`CANVAS_BASE_PATH="./test_canvas"` 相对路径写面**（`backend/tests/conftest.py:487`）
   → U7 地盘，本卡只登记不改。
4. **合约测试不在 CI 白名单**（`.github/workflows/test.yml`），维持现状
   —— 出处 `_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md:12-14`。
5. **`pyproject.toml:71-` `[tool.schemathesis]` 历史块与 4.x 口径可能不一致**，本卡未改、未证
   → 登记（Codex 问题 ⑤）。
6. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数** → `<见 §四 Codex 段>`。
7. **`card-z4-redbase @ c8611a89` 冻结现场仍在**（worktree list 命中 1，
   `backend/` 下 `CLAUDE.md`/`outputs`/`raw`/`wiki` 四项俱在，mtime `2026-09-05T10:13:14`）
   → 是否退役由主 session 裁定。
8. **「先红」的实现方式**：车道树 / 长期树硬禁真跑写端点 + 由裁定 **(乙)** 的一次性
   scratch worktree 补一次修前实证（手册 §四.5 D-25）+ 三条替代证据链降级为并列佐证。
   遗留缺口：扫描面只三处、单 seed、且本次因 deadline 未触达随机生成阶段。
   本条**不是「偏离」**；第十四批候选只保留「更完整扫描面（隔离容器）复跑一次」这一项。
9. **卡文行号勘误链**：本次实测 `test_openapi_contract.py` 的
   `:17/:18/:19/:37/:38-42/:43/:91-136` 与 `vault_init_service.py:104 _ensure_gitignore`
   **与卡文 §〇 完全一致，无新增勘误**（卡文已把前稿的 `:16/:17/:18/:36/:37-41/:42/:95-136`
   与 `:103` 更正过来，本次逐条复核确认更正正确）。
10. **「先红后绿」裁定 = (乙)**（手册 §四.5 D-25，主 session 2026-09-07 排批期裁定）
    + 实际结果：`rc=1`、失败模式 `DeadlineExceeded`、`ls <scratch>/backend` 五项 **rc=1（未出现）**、
    `--hypothesis-seed=0`、三处扫描输出
    `prered-scan-full-{tmpdir,home,scratch}-20260909T160236.txt`（合计 2018 行，骨架命中 **0**）
    + **扫描面缺口**（只 `$TMPDIR` / `$HOME` / scratch 三处，maxdepth 3）。
    ⛔ 本次实证**未复现写盘**，登记为「未复现 + 扫描面不完整」，**不得写成「已证明不写盘」**。
11. **正控口径（建议收进协议，本批 exclude / filter 类卡通用）**：
    `collect-after` 的 `test_api_contract[` 条数 `== G − EXTRA` 且 `> 0`，
    外加独立对账 `T_BEFORE == T_AFTER + N`。
    ——「排除面判据在**全被排掉**时同时假通过」这类**空集恒真**面，
    建议主 session 收进 `card-batch-protocol.md`。
    本卡实测中该正控**确实起了作用的变体**：卡文写死的 `T_AFTER == G` 与 (c) 的
    「GET 面写原语命中即追加排除」在真有命中时**互斥**，须参数化为 `G − EXTRA`。
12. **卡文 §二.2 抽取式在本机不成立（新增勘误）**：`pytest --collect-only -q | grep '^tests/'`
    抽到 **0 行**。根因 `backend/pytest.ini:19-21 addopts = -v --tb=short`，
    pytest verbosity 是**代数和**，`-v`(+1) 与 `-q`(−1) 抵消为 0 ⇒ 落回树形输出。
    修正为 **`-q -q`**。⛔ 若不查抽取式直接下结论，会得出「collect-before 里没有 setup-wizard」
    这个方向相反的错误结论 → 建议收进协议。
13. **GET handler 扫描面划窄的自查判据（新增）**：初版把装饰器基名限死 `router`/`app`
    只扫到 28 个 handler，与收集到的 93 条 GET 对不上。
    修正后 **93 == 93**，该相等即扫描面完整性证据 → 建议作为同类扫描的通用自证手法。
14. **卡文 (b)⓪ 第 1 步前提不成立**：车道树 `backend/.env:67 NEO4J_URI=bolt://localhost:7691`
    就是现网，`:31/:33` 指向 live vault。已按 §三 硬边界在 scratch 副本中改指
    不可达端口与 scratch 内目录后再用（改后 `grep -c '7691\|7687'` = 0）→ 登记。
15. **4 条「只读」GET 实际会写盘，本卡只排除、端点本身未修** → 后续卡候选：
    - `GET /api/v1/health/lancedb`（`health.py:1139`）：`lancedb_path` 默认相对路径
      `./data/lancedb` + `mkdir`（直接写原语）。
    - **`GET /api/v1/review/fsrs-state/{concept_id}`**（`review.py:1430` →
      `review_service.py:2507` → `:600/:604/:605`）：查询无卡的 concept 会 **auto-create
      默认卡并持久化**到 `backend/data/fsrs_card_states.json`。**一个 GET 改变了持久化状态**，
      这不只是测试卫生问题，是端点语义问题 → 建议单独立卡评估。
    - `GET /api/v1/health/storage`（`health.py:1671` → `_check_json_health` `:1448/:1452-1453`）：
      默认 `./data` + `mkdir` + `.health_check` 探针 touch/unlink。
    - `GET /api/v1/multimodal/health`（`multimodal.py:251` → `multimodal_service.py:1034-1036`）：
      `.health_check` 探针 write_text/unlink；构造器还会创建媒体目录。
16. **合约测试全跑耗时是存量问题**：首轮 92 个 GET operation 实测 **4:55:14**（约 3.2 分钟/个，
    92 failed / 1 skipped，全部 `DeadlineExceeded` —— `@settings(deadline=10000)` 对本机
    app 响应过紧）；改前 206 个 operation 按同速率约需 11 小时。本卡的过滤把它减半，
    但**未修** deadline 本身（卡文禁改 `max_examples`，deadline 同理不动）→ 登记。
17. **「探针写完即删」的写入，跑后 `find -newer` 看不见**（`health/storage` 与
    `multimodal/health` 的 `.health_check`）。⇒ 单靠「跑完扫一遍文件系统」这类事后判据
    **系统性地漏掉一整类写入**，必须配合读调用链。建议主 session 收进协议 —— 与
    条目 11 的「空集恒真」同属「判据本身看不见某类事实」的坑。
18. **零写门的检测边界缺口**（Codex round-2 MEDIUM-4）：`conftest.py` 只查 `backend/`
    顶层五项名称；若 vault 根是 `backend/<非五项名>/`，骨架仍写进代码目录而门看不见。
    卡文 (d) 写死这五项，扩大检测面超出本卡授权 → 登记，后续卡候选。
