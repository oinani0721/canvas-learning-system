> ⚠️ 本文件是 CARD-G2-9 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十二批手册 §三 Y3-A 块。
> 批次标记 `[BATCH-2026-09-05-第十二批 / CARD-G2-9]`。车道：`card-z5-canary`（分支 `card/z5-canary`，HEAD `03ac8bf8` = 主干 ff，零卡 commit，dirty=0；`backend/.env` 在位，`backend/.venv` 目录级 symlink → `card-v5-lance/backend/.venv` 已建），**无前提**（本车道首卡；独立 commit 后同车道继续 Y3-B）。无用户裁决项。勘探 2026-09-05 于主干 03ac8bf8。协议：`.claude/rules/card-batch-protocol.md`（§2.1 存档首部 / §2.2 裁判落盘 / §2.3 环境通告 / §3 无 W4 门禁目录级）。

# CARD-G2-9 — 双 vault 数据隔离 canary（跨 vault 那一半的发布必需门；裸脚本自行装门 + 负控，blocked=0 不再单独作证）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 车道 HEAD = 03ac8bf8 = 主干（ff，零卡 commit，`git status --porcelain` 空）；`backend/.env` 5 字节在位；`backend/.venv` → `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv`。**勘误**：上一批 Z5 卡文写「NEW 从 304f03ca 切 + 波 B 等 Z3 合入」——Z3 已在第十一批合入主干，本卡是波 A 直接开跑 | `git` / `ls -la`（2026-09-05 实测） |
| `backend/scripts/g29_dual_vault_canary.py` **不存在**；同目录 `graphiti_schema_canary.py` 是风格参照（模块 docstring 写用法 / 退出码 / fail-closed 契约） | `ls backend/scripts/` |
| 端口门常量：`REQUIRED_BLOCKED_PORTS = frozenset({7691, 7687})` :118；`ALLOWED_TEST_PORTS = frozenset({7692})` :145 | `backend/tests/support/live_port_guard.py` |
| 门的公开 API：`install()` :581（uvloop 已在 `sys.modules` 时 raise RuntimeError :594-600，拒绝装一道已知失效的门）；`register_final_accounting()` :986（atexit，进入即置 `_FINALIZING`；docstring 明写**不能**声称「在所有 atexit 之后执行」）；`write_ledger(path)` :1005（写失败直接抛）；`STATE.summary_line()` :296-303 产出 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=<n> (blocked=…, advisory=…, unaccounted=…)`（前缀常量 `_SUMMARY_PREFIX` :169）；`assert_test_uri_not_blocked()` :865；`assert_neo4j_target_blocked()` :921；`canonical_target_ports(uri)` :730；`assert_guard_live()` :664 | 同上 |
| 最终总账 :1036-1046：脚本直跑（reported_status 为 None）按 0 处理——`unaccounted>0` 或 `blocked>0 且退出码 0` → 强制以 `FINAL_EXIT_CODE` 结束 | 同上 |
| pytest 侧门由 `conftest.py:83 pytest_configure → live_port_guard.install()` 装（:83-89）；裸脚本不经 pytest → **不装门则 blocked 恒 0 = 假绿**（第十一批「负控假绿」同型） | `backend/tests/conftest.py` |
| 测试库 fixture 口径：`neo4j_available` :783-807 读 `NEO4J_TEST_URI`（未设即 skip「refusing to guess」）、`NEO4J_TEST_USER` 默认 `neo4j`、`NEO4J_TEST_PASSWORD` 默认 `testpassword`、`Neo4jClient(uri=, user=, password=, database="neo4j")`（`from app.clients.neo4j_client import Neo4jClient`）；docstring :786 / :816 / :885「dedicated test Neo4j container (port 7692), NOT the product DB (7691)」。**勘误**：上一批卡文 :779/:809/:878 已 +7 漂移 | `backend/tests/conftest.py` |
| docker 实测（2026-09-05）：`canvas-learning-system-neo4j-test  127.0.0.1:7479->7474/tcp, 127.0.0.1:7692->7687/tcp  Up 7 hours (healthy)`；`canvas-learning-system-neo4j  …127.0.0.1:7691->7687/tcp  healthy`。**勘误**：台账「7691 Errno 61」已过期 | `docker ps --format '{{.Names}}\t{{.Ports}}\t{{.Status}}'` |
| LanceDB：`LanceDBClient(db_path=None → env LANCEDB_DATA_PATH → "data/lancedb", …, vault_id=None)` :627-650；`resolve_table_name(self, table_name)` :762 返回 `{vault_id}_{table_name}`（G2-4 已删 legacy 裸表回退） | `backend/lib/agentic_rag/clients/lancedb_client.py` |
| group_id 物理格式：`to_physical_group_id` :140（`vault__x`）、`sanitize_group_id_for_graphiti` :64 | `backend/app/graphiti/group_id_compat.py` |
| 读侧：`require_read_group()` :388 / `VaultScopeUnresolved` :359 | `backend/app/core/vault_scope.py` |
| 写契约 W1-W5 / 读契约 R1-R5（G2-3 写身份复合键已修；R4 存量清零） | `.claude/rules/cypher-write-contract.md` / `cypher-read-contract.md` |
| 契约测试 `tests/unit/test_live_port_guard_contract.py`：`grep -c 'def test_'` = 51，另含 7 处 `parametrize`（收集数可 > 51；勘探两处分别记 51 / 84）——**开工先实测并抄进验收单，卡文不写死**；Z3-B 白名单钉子 :315-318（`ALLOWED_TEST_PORTS & BLOCKED_PORTS` 为空 + `7692 in ALLOWED_TEST_PORTS`） | 实测 |
| `tests/unit/test_lancedb_vault_isolation.py` 15 def（`LanceDBClient(vault_id=…)` 前缀契约，无 parametrize）；`tests/regression/test_write_side_group_guard.py` 5 def（写侧不回落 `DEFAULT_GROUP_ID`） | 实测 |
| C1a 双 vault 用例 `test_two_vaults_same_day_push_and_state_isolated` :386（同进程两 tmp vault，docstring 自述只证 state 隔离、不证「一库一进程」） | `backend/tests/regression/test_daily_review_run.py` |
| tests/unit 既有红基线 247 nodeid（本卡不跑 tests/unit 目录级；tests/api 主干应 0 红） | `_bmad-output/审查/evidence-b12/unit-red-baseline-03ac8bf8.txt` |

## 一 完成条件（AND）
- (a) **canary 脚本落 `backend/scripts/g29_dual_vault_canary.py`，可重复执行**：准备两个 vault（A / B）同路径 / 同 node ID / 同 concept 名 / 同 user ID 的资产，写 → 读 → 删全程留证；A / B **顺序切换 scope**（一进程内先 A 全程再 B 全程，或双进程），禁同一时刻混跑两套 scope；连跑 2 次 rc=0 且报告（剥掉时间戳后）diff 为空；接受 `--evidence-dir` 参数。
- (b) **三存储各自 A/B 计数对账**：LanceDB（`LanceDBClient(db_path=<tmp>, vault_id=A/B)`，表名经 `resolve_table_name` :762）；Neo4j 业务节点按 `group_id`（物理格式 `to_physical_group_id` :140）；Graphiti 写入面（同一 7692 库内 graphiti_core 落的节点，group_id 经 `sanitize_group_id_for_graphiti` :64）。判据：A 计数 == B 计数 > 0；以 A 的 scope 查 B 的键 = 0 命中（反向同）；删 A 全部后 B 计数不变、A 计数 = 0。三存储各贴计数表进报告。
- (c) **FSRS frontmatter 与通知链互不影响**：沿 test_daily_review_run.py:386 C1a 形态扩一条（两 tmp vault 各生成投影：A 的节点 frontmatter / state 文件 / 今日复习.json 与 B 逐字节无交叉），复习投影 A/B 各自独立。
- (d) **全程只用 7692 与 tmp LanceDB 目录**（`LANCEDB_DATA_PATH` 或 `db_path` 显式指 tmp，**默认 `data/lancedb` 也不许**）。证据必含：① 跑前 `docker ps --format '{{.Names}}\t{{.Ports}}\t{{.Status}}'` 文本，须见 `canvas-learning-system-neo4j-test … 127.0.0.1:7692->7687/tcp … healthy`；② 脚本末尾打印 `STATE.summary_line()`，形如 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=<n> (blocked=0, advisory=0, unaccounted=0)`；③ `write_ledger` 落的 JSON（`installed: true`）。
- (e) **裸脚本自行装门**（上一批卡文原缺）：脚本第一段可执行代码——在 `from __future__` 与 stdlib import 之后、**任何 `app.` / `agentic_rag` / `neo4j` / `lancedb` / `graphiti_core` import 之前**：`sys.path.insert(0, <backend>/tests/support)`；`import live_port_guard`；`live_port_guard.install()`（:581）；`live_port_guard.register_final_accounting()`（:986）；跑完 `live_port_guard.write_ledger(<evidence-g29>/ledger-<ts>.json)`（:1005）。若 install() 因 uvloop 已被提前 import 而 raise（:594-600），那是门在说话——**不得**把装门挪到 import 之后换取跑通；用 `python -X importtime` 找出提前拉进 uvloop 的链路并登记。
- (f) **负控（判据 4）**：同一脚本 `NEO4J_TEST_URI=bolt://localhost:7691` 再跑一次 → 必须被拒（`assert_test_uri_not_blocked()` :865 抛，或 connect 被 audit 拦）：rc ≠ 0、stderr 含拒绝原因字样、账本 blocked ≥ 1 或进程被 :1036-1046 强制退出。判据绑定「被哪一层拒的」（贴拒因字符串出自哪一行），不是只看 rc ≠ 0。**blocked=0 单独不构成隔离成立证据**——必须与 (b) 交叉 0 命中 + (f) 负控同贴。
- (g) **主干既有红**：tests/api 目录级 blocked=0；若有红，在主干 03ac8bf8 树复现的 = 既有，逐条登记不算本卡（tests/unit 基线文件只对 tests/unit，本卡不跑 tests/unit 目录级）。
- (h) **报告与脚本落 `_bmad-output/审查/evidence-g29/`**（docker ps / 两次 canary stdout / 负控 stdout+stderr / ledger JSON / pytest 汇总，每份带时间戳 + 末行 `rc=`）；备份恢复半边显式声明不在本卡。
- (i) **一轮 Codex**（gpt-6-astra ultra），审查面 = 本卡 diff（脚本 + 新测试）；已裁决：不做备份恢复 / 规模化 / 仓外调用方；不改生产代码（发现隔离缺陷 → 登记移交，不修）。存档首部按协议 §2.1。
- (j) **「本卡未证明什么」必填**：未证明生产 7691 上存量数据的隔离（只在 7692 + tmp）；未做备份恢复半边；未做规模化 / 并发；未验证仓外调用方（MCP / Obsidian 插件）；(c) 沿 C1a 形态同进程跑两库，不证「一库一进程」。**「台账待登记条目」必填**：G2-9 交付 + 契约测试实测收集数；「7691 Errno 61」登记过期勘误；conftest 行锚 +7 勘误；若发现隔离缺陷的移交卡号；Codex 结论原文与模型名。

## 二 裁判命令
0. 第 0 分钟：`cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary && git rev-parse --short=8 HEAD`（= 03ac8bf8）`; git status --porcelain | wc -l`（= 0）`; test -e backend/.env && readlink backend/.venv`；`PYTEST=$(pwd)/backend/.venv/bin/pytest`；`mkdir -p _bmad-output/审查/evidence-g29`；`docker ps --format '{{.Names}}\t{{.Ports}}\t{{.Status}}' | tee _bmad-output/审查/evidence-g29/docker-ps-$(date +%Y%m%dT%H%M%S).txt`（须见 neo4j-test 7692 healthy）。
1. `cd backend && grep -c 'def test_' tests/unit/test_live_port_guard_contract.py`（抄验收单）`; set -o pipefail; PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_live_port_guard_contract.py 2>&1 | tee ../_bmad-output/审查/evidence-g29/contract-$(date +%Y%m%dT%H%M%S).txt; echo rc=$?` → 全绿，收集数如实记（含 :315-318 白名单用例）。
2. `… $PYTEST -q -p no:cacheprovider tests/unit/test_lancedb_vault_isolation.py tests/regression/test_write_side_group_guard.py` → 15 + 5 绿。
3. `set -o pipefail; NEO4J_TEST_URI=bolt://localhost:7692 LANCEDB_DATA_PATH=<tmp 目录> backend/.venv/bin/python backend/scripts/g29_dual_vault_canary.py --evidence-dir _bmad-output/审查/evidence-g29 2>&1 | tee _bmad-output/审查/evidence-g29/canary-run1-$(date +%Y%m%dT%H%M%S).txt; echo rc=$?` → rc=0；再跑 run2；两份报告剥时间戳后 diff 为空；末行含 `(blocked=0, advisory=0, unaccounted=0)`；ledger JSON `installed: true`。
4. 负控：`NEO4J_TEST_URI=bolt://localhost:7691 … 2>&1 | tee …/canary-negctl-$(date +%Y%m%dT%H%M%S).txt; echo rc=$?` → rc ≠ 0 且日志含拒绝原因（贴出自 live_port_guard.py 哪一行）。
5. `… $PYTEST -q -p no:cacheprovider tests/api 2>&1 | tail -3 | tee …/api-$(date +%Y%m%dT%H%M%S).txt` → 摘要 `blocked=0`。
6. `git diff --stat 03ac8bf8 HEAD -- backend/app backend/lib | wc -l` → 0（不改生产代码）。

## 三 禁改与隔离
- ⛔ 禁连 Neo4j 7691 / 7687（阻断级）：`NEO4J_TEST_URI` 必须显式 `bolt://localhost:7692`（端口 0 / 省略端口 Z3-B 后一律 fail-closed）。
- 禁改 `backend/tests/support/live_port_guard.py` 与 `backend/tests/conftest.py`（Y7-A 独占；本卡只 import 公开函数）。
- 禁写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/` 与现网 LanceDB（`data/lancedb` 默认路径亦禁；所有数据落 tmp 与 7692）。
- 禁改 `lancedb_client.py` / `vault_scope.py` / `memory_service.py` / `rag_service.py` / `neo4j_client.py` / `group_id_compat.py`（发现缺陷登记移交）。
- 禁改 `review_app.py` / `review_overview.py` / `daily_review_pick.py` / `daily_review_run.py`（Y2）；禁改 `lifespan_isolation_*`（Y7 / Y8）；禁改 `lefthook.yml`（Y4）。
- 禁跑 `tests/integration` / `tests/e2e` 目录级（advisory 仍真连，协议 §3）。
- 禁把 blocked=0 当隔离成立的唯一证据；禁把脚本改成 pytest 承载而不声明（判据 3 字面仍可过但 (e) 语义落空）。
- 台账只有主 session 改；不 push；`*.stderr*` 不入库。D-14：本卡不改 `backend/app/**`；新脚本在 `backend/scripts/`（pyright glob 覆盖）——新文件自身的 pyright 报错须修，若拦在**非本卡文件**允许带存档的 `LEFTHOOK_EXCLUDE=python-typecheck` 并贴原始输出。

## 四 Codex / 验收单
命令同协议 §2；prompt `_bmad-output/审查/prompts/codex-prompt-CARD-G2-9.md`（五分节：一 背景 + 最小读取面写死 = 新脚本 / `live_port_guard.py` :118、:145、:581-600、:865、:986-1046 / `group_id_compat.py` :64、:140 / `lancedb_client.py` :627-650、:762 / 新测试；二 作者自述请独立核对；三 按重要性排序的问题：① 装门是否早于全部业务 import、uvloop 链路有没有提前进来 ② 负控是否真被拒且判据绑定拒因来源行 ③ 三存储交叉查询是否覆盖 Graphiti 面而非只查业务 Concept ④ 两次运行等价判据剥掉时间戳后是否仍有实质内容 ⑤ 删 A 后 B 不变的断言是否在删之前先记了 B 的计数；四 输出格式；五 边界 + 已裁决）。存档 `_bmad-output/审查/codex-review-CARD-G2-9.md` 首部按协议 §2.1；顺序固定「代码与门全部定稿 → 跑全部裁判 → 送 Codex → 之后只改 _bmad-output」，审后再改代码 = 失绑须登记。验收单 `_bmad-output/验收单/UAT-CARD-G2-9-<日期>.md`：DoD-3 双段（4-B 零技术词）；4-B「两个知识库各写各的，互相看不见对方的东西，删一个不影响另一个」+ felt-sense；「本卡未证明什么」「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100（`wc -m`）；不 push；**独立 commit 后同车道继续 Y3-B**；跑完说「复核第十二批 Y3」。
