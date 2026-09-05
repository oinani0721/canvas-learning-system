# CARD-TEST-hygiene-vaultinit · (a) 定位结论

> 车道 `card-y6-testhygiene`，代码树 HEAD `03ac8bf8`，实测 2026-09-05。
> 三签名：① `backend/{raw,wiki,outputs,CLAUDE.md}` 出现 ② `/tmp/test-vault*` 出现
> ③ `backend/config/subject_mapping.yaml` / `backend/.gitignore` sha 变化。

## 卡文事实的两处偏差（如实登记，不代改）

1. **基线文件不在本车道树**。卡文 §〇 与裁判 6 写的相对路径
   `_bmad-output/审查/evidence-b12/unit-red-baseline-03ac8bf8.txt` 在本树**不存在**
   （`ls` → No such file）。实存于设计稿树
   `.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b12/`
   （28433 字节，mtime 09-05 13:17）。本卡一律用该绝对路径，口径不变。
2. 基线内容核对**通过**：247 nodeid = 209 FAILED + 38 ERROR；
   `test_startup_health_check.py` 6 条、`test_kg_health.py` 1 条在基线内，
   `test_vault_init_service.py` 0 条（全绿）。与卡文逐字一致。

## H1 = tests/unit 目录级 —— **部分复现**

命令（log `unit-run-h1-20260905T164916.txt`）：

```
cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit \
  -q -p no:cacheprovider -p no:randomly --override-ini='addopts='
```

结果 `209 failed, 4602 passed, 1 skipped, 38 errors in 316.95s`，rc=1
（209+38 = 247，与基线 nodeid 数逐字相同）。

| 签名 | 判据命令 | 结果 |
|---|---|---|
| ① backend 四路径 | `git status --porcelain backend` / `test -e` | **未复现**。status 空；四路径全 absent |
| ③ 两文件 sha | `shasum -a 256 ... \| diff sha-before.txt -` | **未复现**。diff 空 |
| ② `/tmp/test-vault*` | `ls -d /tmp/test-vault /tmp/test-vault-wizard` | **复现**。两目录于 16:51 重新出现 |

`find backend -maxdepth 1 -newer sentinel` 命中 `backend`、`backend/logs`、`backend/data`
—— 是**既有**目录的 mtime 被更新（测试期写日志/数据），不是 vault 骨架；三者均被
`.gitignore` 覆盖，故 git 判据看不见（旁记，见「附带发现」）。

### 二分到 nodeid 级（签名②）

每步跑前把 `/tmp/test-vault*` **改名**重新武装（`initialize_vault` 的
`mkdir(exist_ok=True)` + `if not claude_md.exists()` 会让第二次运行不留痕）。

| nodeid | log | `/tmp/test-vault` | `/tmp/test-vault-wizard` |
|---|---|---|---|
| `tests/unit/test_startup_health_check.py::TestSetupWizard::test_endpoint_exists` | `bisect-node1.txt` | **出现** | 不出现 |
| `tests/unit/test_startup_health_check.py::TestSetupWizard::test_returns_structured_report` | `bisect-node2.txt` | 不出现 | **出现** |

一一对应，与源码 `:55-57` / `:61-63` 的硬编码字面量一致 ⇒ 签名② 的写者**唯一确定**为
这两个 nodeid。(b)② 即修此处。

### ⚠️ 签名② 的判据污染面（实测发现，必须声明）

`/tmp` 是**全机共享**的，本批 9 车道并行 ⇒ **别的车道跑 tests/unit 同样会产出
`/tmp/test-vault*`**，"目录存在"这一判据会被别的进程喂饱。

实测坐实（2026-09-06 01:55~01:57）：本卡 H2 运行期间两目录再次出现，
`stat` 给出 mtime `01:55:04` / `01:55:09`（间隔 5 秒）。同一时刻 `ps -ww -p 68344`：

```
Python ./.venv/bin/pytest -q -p no:cacheprovider tests/unit
lsof cwd → .../worktrees/card-y9-maingoal/backend
```

即 **card-y9-maingoal 车道**跑 tests/unit 造的，与本卡 H2（PID 74013，跑
`tests/contract/test_openapi_contract.py`）无关。

**为什么上表的 nodeid 归因不受此影响**：并行车道的污染是**成对**出现的
（两个用例连着跑，间隔 ≈5s，与用例各 5.48s / 5.49s 的耗时吻合）；而本卡两次
单跑各自**只**产生一个目录，且与源码字面量精确对应（node1 → `test-vault` 且
`test-vault-wizard` 不出现；node2 反之）。"成对 vs 单个"是能翻转结论的对照，
不是同一现象的两种描述。y9 车道的这次意外运行反而构成**独立第三方复现**：
另一个进程跑 tests/unit 也产出同一对目录、同样间隔 5 秒。

**由此收紧收尾判据**：裁判 2 的 `ls -d /tmp/test-vault*` 在并行环境下可能假红。
改用**绑定本进程自身输出**的判据 —— 修后 pytest 的 stdout 里不得再出现
`{"path": "/private/tmp/test-vault*/CLAUDE.md", "event": "claude_md_created"}`
一类日志（那是被测进程自己写的，别的车道进不来），并辅以 `find /tmp -maxdepth 1
-name 'test-vault*' -newer <本次哨兵>` + 进程归属交叉核对。

## 台账归因的实测勘误

台账 `未合卡追踪台账.md:48`（Z4-A 行）与
`2026-09-05-第十一批复核裁定与待裁决登记.md:54` 的原句：

> ~~`test_vault_init_service.py` 目录级运行把 vault 骨架写进 `backend/`~~

**实测不成立**，两处独立证据：

1. `test_vault_init_service.py` 的 8 个用例**全部**经 `:12-14 vault_dir(tmp_path)`
   —— 源码逐行核对，无一例外，且该文件在基线里 0 条红（全绿）。
2. H1 目录级实跑（含该文件全部 8 用例）后，签名① 三处判据**全空**：
   `git status --porcelain backend` 空、四路径 `test -e` 全 absent、
   两文件 sha diff 空。

**划改为**：目录级 `tests/unit` 复现出的写点是 `/tmp/test-vault*`，
写者 = `test_startup_health_check.py::TestSetupWizard` 的两个 nodeid（上表）；
`backend/` 内的 vault 骨架在 `tests/unit` 目录级下**未复现**。

## 附带发现（登记，不在本卡处置面）

- **Y6-C 分诊线索（直接证据，非推测）**：`test_startup_health_check.py` 的
  基线 6 条红，真因是 **W4 端口门哨兵**，不是 auth 503。`bisect-node1.txt` 的失败正文：
  `live Neo4j port connect attempted —— ('::1', 7691, 0, 0)`；同一份 log 里
  middleware 记录 `"path": "/api/v1/system/setup-wizard", "status": 200`
  —— 端点本身返回 200，用例是被哨兵转红的。
- **macOS `/tmp` symlink 使黑名单失效**：日志显示写入路径为
  `/private/tmp/test-vault/CLAUDE.md`，即 `Path("/tmp/...").resolve()` →
  `/private/tmp/...`。`system.py:442` 的 `str(vault) in ("/", ..., "/tmp", ...)`
  字符串比较对 `/tmp` 恒不命中。本卡硬边界要求黑名单原样保留 ⇒ 只登记。
- `backend/logs`、`backend/data` 在 tests/unit 目录级下被写入，但被 `.gitignore`
  覆盖 ⇒ 任何以 `git status` 为唯一判据的卫生门对它们**恒绿**（假绿面）。

## H2 = tests/contract/test_openapi_contract.py

见 `定位结论-a-h2.md`（H2 单独落盘，前提：schemathesis 4.14.3 **已装**，
`importorskip` 不会 skip；该文件对全端点 `@schema.parametrize()`，
grep `exclude` 0 命中）。
