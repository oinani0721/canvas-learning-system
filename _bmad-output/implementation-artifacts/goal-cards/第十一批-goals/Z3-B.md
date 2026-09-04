> ⚠️ 本文件是 CARD-W4-3a 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z3-B 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-W4-3a]`。车道：`card-z3-w4`，**前提 Z3-A 已独立 commit 且工作树干净**。本卡 2 轮 Codex：round-1 = 白名单修复本体；round-2 = **X4 门下复审**（第十批 X4 是人判合入，两轮终审 BLOCKER 相同，这里以修复后的门为对象补一次独立外审，结论供用户对 D-1 二次确认）。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-W4-3a — NEO4J_TEST_URI 端口判据改正面白名单（只允许 7692）+ driver canonical address 契约测试 + X4 门下复审

## 〇 事实
| 事实 | 位置 |
|---|---|
| 端口判据当前是**黑名单**：`REQUIRED_BLOCKED_PORTS = frozenset({7691, 7687})`，`BLOCKED_PORTS` 等于它，7692 不在其中 | `live_port_guard.py:118-119` |
| BLOCKER 链路仍在树上：`assert_test_uri_not_blocked`（`:623`）只要求「端口能解析且不在 BLOCKED_PORTS」——`:639 if port is None: raise`、`:644 if port in BLOCKED_PORTS: raise`，端口 `0` 两条都不命中 → 放行 | live_port_guard.py |
| driver 侧把 `:0` 归一成 7687：`neo4j/_addressing.py:175 / :183` `port = port or default_port or 0`，`_sync/driver.py:435 _default_port = 7687`、`:450 Address.parse(target, default_port=…)`；`int("0")` 是 falsy | venv 内 neo4j |
| 第二段：`is_exempt()`（`:779`；`:120 EXEMPT_MARKERS`、`:128 EXEMPT_PATH_PREFIXES`）对 `tests/integration` / `tests/e2e` 只记 advisory 不抛 → 误配 `:0` 时那些用例会真连开发库 | live_port_guard.py |
| ⛔ **白名单不能落在 socket audit hook（`:386`）**：那里改「只放行 7692」会把测试进程里所有其它 loopback/出站一并拦掉——仓内至少 Ollama `localhost:11434`（`config.py:531`）、`tests/contract/test_pact_provider.py`、`tests/unit/test_embedder_factory.py` 会连非 7692 本地端口；guard 自身文档（`:115`）也说探针会临时加本地端口 | 最大风险 |
| 自证锚点连带：`audit_hook_alive(:547)` 用 `next(iter(sorted(REQUIRED_BLOCKED_PORTS)))` 合成自证地址，`assert_guard_live(:572-576)` 断言「受拦集不得缩小」——黑名单常量**不能改**，否则门从 fail-closed 变恒真 | live_port_guard.py |
| `extract_port`（`:305-322`）对非 tuple / 长度 <2 地址返回 None；白名单语义下 None 既不在白名单也不该被拦——判据必须显式三分（受拦 / 白名单 / 射程外） | live_port_guard.py |
| 契约测试落点：`tests/unit/test_live_port_guard_contract.py::TestBlockedPortsContract`（`:89`，含同型 `test_test_uri_without_explicit_port_is_rejected :106-113`，全文件 216 行） | 现成 |
| live_port_guard 刻意不 import `app.*`（装门早于业务 import，`conftest.py:28`），但 `assert_test_uri_not_blocked` 在 session fixture 才被调（`conftest.py:106`）→ **函数体内延迟 import `neo4j.Address` 合法**；模块层新增 import **禁止** | 时序 |
| A 类另 3 HIGH：`:318` tuple 子类可重载 `len`/`[1]`（本卡顺带修）；`:392` `os._exit(3)` 前 IO 可抛 / `_FINALIZING`·`record()`·ledger 未同锁（**另立 W4-④**，不在本卡） | X4 验收单 §7.10 |

## 一 完成条件（AND）
- (a) `live_port_guard.py` 新增 `ALLOWED_TEST_PORTS = frozenset({7692})`，`assert_test_uri_not_blocked(:623)` 判据由「端口不在 BLOCKED_PORTS」改为「**canonical port ∈ ALLOWED_TEST_PORTS**」；`BLOCKED_PORTS` / `REQUIRED_BLOCKED_PORTS`（`:118-119`）与 `_audit_hook(:386)` 的黑名单语义**保持不变**，理由写进注释（防误拦 11434 等 + 自证锚点）。
- (b) canonical port 不再由自写 `_port_of_uri(:679)` 推断，改为函数体内**延迟 import** `neo4j.Address` 复算 `Address.parse(target, default_host='localhost', default_port=7687)`（与 `_sync/driver.py:450` 同参）；解析失败 / 拿不到 int 端口一律 fail-closed 拒绝装门；延迟 import 的合法性写明依据。
- (c) `TestBlockedPortsContract(:89)` 增契约用例 ≥5：`bolt://127.0.0.1:0`、`bolt://127.0.0.1:00`、`bolt://[::1]:0`、`bolt://127.0.0.1`（无端口）、`neo4j://host`，断言均 raises 且错误文案含 canonical 端口 7687；保留既有 7692 放行用例。
- (d) **验伪锚**：monkeypatch `ALLOWED_TEST_PORTS` 为空集 → 7692 也被拒（证明白名单承重而非恒真）。
- (e) 顺带修 A 类 HIGH #2（`:318`）：`extract_port` / `port_is_trustworthy` 对 tuple **子类**一律按不可信处理（fail-closed），`TestPortTrustworthiness(:119)` 加覆写 `__getitem__` 的反例。
- (f) `guard_probes.py` 增 1 条探针：把 `ALLOWED_TEST_PORTS` 改成含 7687 后预检必须仍拒（白名单不能被「往里加现网端口」拆门）；注册进 `:823-848`（Z3-A 之后的最新清单），末行计数同步。
- (g) 全程零 live 写：不连 7691/7687、不起真 Neo4j；新测试只用 monkeypatch.setenv + 纯函数调用。
- (h) **两轮 Codex（gpt-6-astra ultra）**：round-1 只审 (a)-(f) 的 diff；round-2 = X4 门下复审，最小读取面**写死**在 prompt：`live_port_guard.py`（全）、`tests/support/lifespan.py`、`tests/support/guard_plugin.py`、`tests/regression/conftest.py`、`tests/conftest.py` 的装门 hunk、`test_live_port_guard_contract.py`——**显式排除 4 个 `scripts/lifespan_isolation_*` 负控（3744 行）**，问题聚焦：门能不能被绕过 / `is_exempt` advisory 路径 / 解析完备性 / 装门时机早于业务 import；§四 已裁决写入「端口 0 BLOCKER 已由本卡修」「B 类 AST 门 5H / C 类 BASH_ENV / W4-④ 原子性另立卡」。
- (i) 验收单出「人判复核结论」一节：认可 / 附条件认可 / 建议 revert `32c8e325`，三选一并给依据（供用户对 D-1 二次确认）。

## 二 裁判命令
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_live_port_guard_contract.py` → 全绿且用例数 > 合并前（≥ +6）。
2. `… <venv>/python scripts/lifespan_isolation_guard_probes.py` → `GUARD-PROBES: PASS — N/N`（N = Z3-A 之后 + 1）。
3. `… <venv>/python scripts/lifespan_isolation_negative_control.py` → `NEGATIVE-CONTROL: PASS` + `AST-GATE: PASS`。
4. `… bash scripts/lifespan_isolation_runtime_sha.sh -- <venv>/python -m pytest tests/api -q -p no:cacheprovider` → `RUNTIME-FILES: unchanged`，且 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`。
5. 验伪：`NEO4J_TEST_URI=bolt://127.0.0.1:0 $PYTEST -q tests/unit/test_live_port_guard_contract.py -k test_uri` → 被拒（文案含 7687）；`NEO4J_TEST_URI=bolt://localhost:7692 …` → 放行。
6. `grep -n '^import\|^from' backend/tests/support/live_port_guard.py | grep -c neo4j` → 0（模块层无 neo4j import）。

## 三 禁改与隔离
禁改 `REQUIRED_BLOCKED_PORTS / BLOCKED_PORTS` 取值；禁把 `_audit_hook:386` 改成白名单语义；禁在 `live_port_guard.py` 模块层新增任何 import；禁改 `negative_control.py` / `runtime_sha.sh`（Z3-A 面，已合在本车道前一 commit，不再动）；禁改 `EXEMPT_MARKERS / EXEMPT_PATH_PREFIXES` 覆盖面（放宽/收紧豁免另裁）；禁改 `tests/conftest.py` 装门时机；不连 7691/7687；不改 `backend/.env`；不改台账；不 push。

## 四 Codex / 验收单
命令同协议，两轮文件名 `codex-prompt-CARD-W4-3a-r1.md` / `-r2.md` → `codex-review-CARD-W4-3a-r1.md` / `-r2.md`（0 字节重发一次后主 session 人审）。验收单 `…/验收单/UAT-CARD-W4-3a-<日期>.md`：DoD-3 双段；4-B「测试再也连不到真数据库，哪怕配置写错端口」；「人判复核结论」一节必填；「本卡未证明什么」必填（W4-④ 原子性、B 类 AST 5H、C 类 BASH_ENV 未修）；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push。**commit 后同车道继续 Z3-C。**
