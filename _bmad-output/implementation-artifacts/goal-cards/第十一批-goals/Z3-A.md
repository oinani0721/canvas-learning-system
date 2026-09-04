> ⚠️ 本文件是 CARD-W4-3b 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z3-A 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-W4-3b]`。车道：NEW `card-z3-w4`（从 `304f03ca` 切，`.env` / `prompts/` / venv symlink 就位）。同车道串行 **Z3-A（本卡 3b）→ Z3-B（3a）→ Z3-C（3c）**——3a 与 3b 都要改 `guard_probes.py:823-848` 的探针注册清单，所以不并行。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-W4-3b — 门债补门：M15 glob 修复无门保护 / LOW#18·M16 E 失格修复无反例 / M14 过宽 glob / M13 未实测注释

## 〇 事实
| 事实 | 位置 |
|---|---|
| X4 人判合入（`32c8e325`）时按宽口径「拆掉修复后指定负控不翻红」车道自认两条：**M15**（runtime 文件 glob 修复无门保护）、**LOW#18**（E 的失格修复未进常设 `_AST_MUST_FLAG`）——**下一个人把这两处修复删掉，三道裁判仍会全绿** | X4 验收单 §7.9a #15 / §7.7a 其四 |
| M15 成立：`guard_probes.py:823-848` 的 22 条注册探针无一覆盖 runtime 文件 glob 的 absent→present 分支（`probe_shell_can_report_changed:790-818` 写的是固定项 `data/bug_log.jsonl`） | lifespan_isolation_guard_probes.py |
| M14 也在树上：Python 侧 `RUNTIME_FILE_GLOBS`（`negative_control.py:135-137`）与 shell 侧 `WATCHED_GLOBS`（`runtime_sha.sh:243-245`）都是 `vault_index_pending*.jsonl`，会收 `vault_index_pending_backup.jsonl` 这类旁文件；正解 = 拆「旧固定名精确项 + `vault_index_pending__*.jsonl`」 | 两文件 |
| 改 shell 侧 WATCHED_GLOBS 不会打到自证（`SELFTEST_EXPECTED` 是对常量串取 sha，`runtime_sha.sh:184-199`），但 `EXPECTED_FIXED_COUNT=2 / EXPECTED_GLOB_COUNT=1`（`:246-247`）计数自检会跟着变，须同步；`guard_probes.py:775` 断言该常量串仍在脚本里 | runtime_sha.sh |
| LOW#18 成立：E 的修复 = `disqualified_factory_keys`（`negative_control.py:300` 声明 / `:326` 减掉 / `:619` 加入），`_AST_MUST_FLAG`（`:1100-1348`）20+ 条反例里没有「outer→inner 工厂被永久失格 / 失格名单被删就漏检」形态 | negative_control.py |
| M16：失格判定误拒安全前向工厂 `outer() → inner() → FastAPI()`；`_AST_MUST_PASS` 在 `:1349` | negative_control.py |
| M13：`runtime_sha.sh:273` 附近「compgen -G 展开本身已排序、不必外部 sort」为未实测断言 | runtime_sha.sh |
| 文档残留：`backend/tests/conftest.py:184` 与 live_port_guard 标题里的「atexit LIFO 最后执行」措辞已被 round-1 第 2 条撤回 | conftest.py |
| **本卡不碰 `live_port_guard.py`**（留给 Z3-B）；两卡文件不相交 | 地盘 |

## 一 完成条件（AND）
- (a) `guard_probes.py` 新增探针 `runtime-glob-absent-to-present`：tmp 假 backend 里让被包裹命令**新建** `app/data/vault_index_pending__<key>.jsonl`（快照前不存在），断言 `runtime_sha.sh` 判 `RUNTIME-FILES: CHANGED` 且 rc=1；再加对照探针——缓存 glob 展开 / 删 glob 项后必须变绿（证明钉的正是 glob 分支）。
- (b) Python 侧同型门：`negative_control.py` 的 `runtime_files(:141-151)` 增自检——glob 每次调用重新展开，快照后新建的文件必须出现在第二次调用结果里。
- (c) M14 收窄：两侧 glob 拆成「`app/data/vault_index_pending.jsonl` 精确项 + `vault_index_pending__*.jsonl` glob」；`EXPECTED_FIXED_COUNT` / `EXPECTED_GLOB_COUNT` 同步；**改之前先全量扫描列出实际匹配到的文件名**，「哪些被排除、为什么安全」写进验收单（收窄是放松方向，必须有证据）。
- (d) LOW#18：`_AST_MUST_FLAG` 增 E 的原始反例；实测「注释掉 `:326` 的 `-= disqualified_factory_keys` 后负控当场 FAIL」写进验收单。
- (e) M16：`_AST_MUST_PASS` 增正例 `outer() → inner() → FastAPI()`，失格判定改成**固定点收敛之后**再生效；两条一起做。
- (f) M13：补 Bash 3.2（`/bin/bash`）实测证据，或改写成「未验证」并加显式排序。
- (g) 文档残留按撤回结论改正（只动注释/字符串）。
- (h) 新增探针/反例只在 tmp 假 backend 构造，真实工作树一个字节不碰；每条新门配一次**拆门实测**（拆了要红）。
- (i) 一轮 Codex（gpt-6-astra ultra），审查面 = 本卡 diff。

## 二 裁判命令
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 <venv>/python scripts/lifespan_isolation_guard_probes.py` → `GUARD-PROBES: PASS — N/N`，N = 29 + 新增，末行计数与实际一致。
2. `… <venv>/python scripts/lifespan_isolation_negative_control.py` → `NEGATIVE-CONTROL: PASS` 且 `AST-GATE: PASS`（绕过条数 ≥ 基线+1，正例 ≥ 基线+1）。
3. `… bash scripts/lifespan_isolation_runtime_sha.sh -- <venv>/python -m pytest tests/api -q -p no:cacheprovider` → `RUNTIME-FILES: unchanged`。
4. 拆门实测四条各一（M15 glob 缓存 / LOW#18 注释 `:326` / M14 旁文件 / M16 正例）→ 对应门红 → 还原 → sha 同。
5. `git status --porcelain` 只含门文件，无 `data/` 产物。

## 三 禁改与隔离
禁改 `tests/support/live_port_guard.py`（Z3-B 面）；禁扩大 runtime 文件监视面（`lancedb_pending_index__*.jsonl` 等同族仍不在清单，扩面另裁）；禁改 `SELFTEST_EXPECTED` 常量串（`runtime_sha.sh:187`；确需改须同步 `guard_probes.py:775` 并写明）；禁在真实 `backend/app/data/` 或 `backend/data/` 创建/删除文件；禁用「跑了没红」当补门成功证据；不连 7691/7687；不改台账；不 push。

## 四 Codex / 验收单
命令同协议（`codex-prompt-CARD-W4-3b.md` → `codex-review-CARD-W4-3b.md`，1 轮）。验收单 `…/验收单/UAT-CARD-W4-3b-<日期>.md`：DoD-3 双段；4-B「无变化（把上次留的几个『改了但没门证明改对』的口子补上门）」；「本卡未证明什么」必填（同族旁文件扩面未做）；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push。**commit 后同车道继续 Z3-B。**
