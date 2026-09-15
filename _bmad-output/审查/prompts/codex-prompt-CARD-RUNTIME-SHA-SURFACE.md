# 独立复核请求 — CARD-RUNTIME-SHA-SURFACE（BATCH-2026-09-11-第十四批 / 车道 T9-D）

## 一 背景与最小读取面

仓库根（本次审查的工作树）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`

审查绑定：`5fa2d401..b191a085`（`b191a085` 是本卡唯一的代码 commit，也是当前 HEAD）。

**被改文件（本卡地盘，唯一一个）**
- `backend/scripts/lifespan_isolation_runtime_sha.sh`（改后 706 行）

这是一道 shell 写的「运行时文件门」：它对一份**具名清单**里的文件在被包裹命令执行
前后各取一次 sha256 快照，逐字节相同则打印 `RUNTIME-FILES: unchanged`，不同则打印
`RUNTIME-FILES: CHANGED` 并 exit 1。清单 = `WATCHED_FIXED`（固定路径）+
`WATCHED_GLOBS`（每次快照重新展开的 glob）。两个常量 `EXPECTED_FIXED_COUNT` /
`EXPECTED_GLOB_COUNT` 是防「清单被悄悄改短 ⇒ 门零比较恒绿」的计数自检。

**本卡做了什么**：把三个原先漏列的运行时文件补进监视面，并同步两个计数常量；另外
把文件开头两处边界注释与 `SHELLOPTS=noexec` 那一段的调用方硬要求注释写细。

**生产写点（请核对新增三项确实是这三处产出的默认路径）**
- `backend/app/services/lancedb_index_service.py`：`_journal_stem: str = "lancedb_pending_index"`
  （经 `backend/app/core/vault_state_paths.py::namespaced_state_path()` 落成
  `app/data/lancedb_pending_index__<vault_key>.jsonl`）
- `backend/app/clients/neo4j_client.py`：`DEFAULT_STORAGE_PATH`（`backend/data/neo4j_memory.json`）
- `backend/app/middleware/cost_tracker.py`：`_DEFAULT_DB_PATH`（`backend/data/llm_call_logs.db`）

**耦合的只读面（这几个文件本卡**不**改，请只读它们来判断本卡有没有把它们弄坏）**
- `backend/scripts/lifespan_isolation_guard_probes.py`：门头注释里「由 **19 条** shell
  探针承重」那句被一条花名册探针钉住（它按文本找那句声明与「数字与清单不一致」那段
  之间的区间）；另有一族 glob 探针按字符串 `vault_index_pending__*.jsonl` 锚定门体。
- `backend/scripts/lifespan_isolation_negative_control.py`：`RUNTIME_FILE_RELPATHS`(3) 与
  `RUNTIME_FILE_GLOBS`(1) 是门清单的**镜像**，注释写着「与 runtime_sha.sh 监视清单保持一致」。
- `backend/tests/unit/test_live_port_guard_contract.py`：驱动上面那些探针的契约测试。

**证据目录**：`_bmad-output/审查/evidence-runtime-sha-surface/`（判据脚本与各次输出）。

## 二 作者自述（请独立核对，不要采信）

1. **三面各有「扩面前 / 扩面后」对照**（`inject_probe.zsh`，在 `$TMPDIR` 里搭 fake
   backend，真实工作树一字节不碰、跑前跑后 sha 已比对）：
   - 扩面前门：三面注入 → 全 `unchanged` rc=0（`inject-before-*.txt`）
   - 扩面后门：三面注入 → 全 `CHANGED` rc=1（`inject-after-*.txt`）
   - **未被拦下的输入（验伪锚）**：同目录写一个不在清单里的 `not_watched_probe.txt`
     → 改前改后都 `unchanged` rc=0（证明没有被放宽成「整目录监视」）。
2. **harness 正锚**（`posctl_probe.zsh`）：用**扩面前**的门对**改前就已在清单里**的四个
   形态注入 → 全 `CHANGED` rc=1。作者用它排除「(1) 里那些 unchanged 是 harness 本身
   坏掉」的可能。
3. **收窄正证据**（`narrowness_probe.zsh`）：单下划线旁文件
   `lancedb_pending_index_backup.jsonl`、裸名 `lancedb_pending_index.jsonl`、
   `…__x.jsonl.old`、`neo4j_memory.json.bak`、`llm_call_logs.db-wal` 五种 → 全 `unchanged`；
   真命名空间形态 `…__probe.jsonl` → `CHANGED`。
4. **计数自检同步**（`count_selfcheck.zsh`）：改后门正常跑不出现两条计数 GATE-BROKEN
   文案；**负控输入**是把两个 `EXPECTED_*_COUNT` 各改错一次，同一判据当场变红。
5. **`SHELLOPTS=noexec`**（`noexec_contract.py`）：作者主张这一条**在脚本内部无法防御**
   （bash 只解析不执行，连门自己的 exec 那句都不跑），所以本卡**没有**在脚本里加任何
   声称能防它的分支，只把给调用方的硬要求注释写成可粘贴的断言配方。实测：noexec 下
   真门 rc=0、输出长度 0、无结论行；断言对该输出判 1，对正常 run 判 0；shell 版断言
   在同一 noexec 环境里自己也 rc=0 零输出（故常驻强制必须落在非 bash 进程）。
6. **`llm_call_logs.db` 是 SQLite 二进制**，门按字节比对。作者实测「只读不写」三种形态
   （默认连接 SELECT / 再 SELECT / 只读 URI SELECT）sha 均不变，真写入才变
   （`sqlite_sha_stability.py`）。
7. **探针契约测试** `tests/unit/test_live_port_guard_contract.py` file-level 改前改后
   同为 152 passed。
8. **两项移交、本卡不做**：`negative_control.py` 的镜像清单现仍 3+1、与扩面后的 5+2
   不一致（该文件属别的车道地盘，本卡只登记）；勘探里与本卡并称的 `*_with_status`
   四个兼容壳是**源码扫描面**、与「运行时文件字节快照」不同类，另立卡。

## 三 请按重要性排序回答的问题

1. **扩面是否只加不放宽**：新增三项是否都能由上面的生产写点证明？新增的 glob 是否
   确实是双下划线的窄形态？有没有顺手改宽或摘掉任何既有监视项？有没有任何
   fail-closed 分支（门自证 / 计数自检 / compgen 自检 / glob 排序 / before-after 判定）
   被改成放行？
2. **计数常量是否与数组真的同步**（5 / 2）？若不同步会怎样？
3. **noexec 这一段是否诚实**：脚本里有没有出现任何看起来能防 `SHELLOPTS=noexec`、
   实则不会执行的分支？注释里的断言配方是否「无结论行即判红、有结论行即放行」？
   有没有把「只能靠调用方」这件事写清楚，而不是暗示脚本自己解决了？
4. **对照输入与未被拦下的输入是否都落盘**：三面的 before/after 对照、验伪锚、正锚、
   收窄正证据，是否都有可核的存档？`llm_call_logs.db` 的二进制 sha 稳定性是否真的
   被核过，还是只是声称？
5. **有没有碰到门未覆盖的路径或出地盘的文件**：`guard_probes.py` /
   `negative_control.py` / `test_live_port_guard_contract.py` / `backend/app/**` /
   `backend/tests/**` 是否一字未改？门头「19 条」那句声明是否被误动（它被花名册探针钉着）？
6. **两处边界注释（文件开头「这道门不比什么」一节）是否与新的监视面一致**：还有没有
   残留「lancedb 不在清单里」「不看 Neo4j」这类现在已经不准确的说法？新写的说法有没有
   反过来把话说得比实现更宽（例如让人以为覆盖了非默认路径）？

## 四 输出格式

逐条给：**级别**（BLOCKER / HIGH / MEDIUM / LOW）+ **文件:行** + **依据**（引到具体代码
或存档）+ **建议**。只读环境下判不了的，请写「未验证」并说明需要什么才能判。

## 五 边界

- 只读审查：不要修改任何文件、不要暂存文件、不要跑 git hook、不要跑测试套件。
- `guard_probes.py` / `negative_control.py` / `test_live_port_guard_contract.py` /
  `backend/app/**` / 其余 `backend/tests/**` **不在本卡改面**——发现它们有问题请写成
  移交建议，不要判成本卡缺陷。
- 本卡不改台账、不改设计稿、不 push。
