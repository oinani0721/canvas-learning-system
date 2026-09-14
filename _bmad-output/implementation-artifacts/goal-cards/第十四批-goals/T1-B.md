> ⚠️ 本文件是 CARD-G2-9-F1-canary 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T1-B 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-G2-9-F1-canary]`。车道 `card-t1-lance`（分支 `card/t1-lance`，NEW @ `081004834e37b1b0253cf81dc7b44e784646c934`=B14_BASE；`backend/.venv` symlink 已建、`backend/.env` 已拷），本车道第 2/2 张。前提：**前一卡 T1-A CARD-G2-9-F2 已独立 commit 且 `git status --porcelain` 空**（开工 `git log --oneline -3` 取 T1-A 末 commit SHA 落档，下称 `$PREREQ`）。用户已裁相关：D-17（G2-9-F1 数据丢失面必排，本卡为其收尾的 canary 复跑）/ D-41（现网 LanceDB 备份对账需授权，本卡**不排**）/ D-15（多轮；零代码卡 1 轮）。勘探 2026-09-11 于主干 `286178d8`+波 0（B14_BASE）。协议（绝对路径，⛔ 只读 feature 主干 `--add-dir` 那份）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`。手册（同理只读主干那份）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零/§三 T1-B/§四）。⚠️ **车道树自己那份 `.claude/rules/card-batch-protocol.md` 与手册是 08100483 版、不含本批回写，别读**；本批所有回写只在 `--add-dir` 的 feature 主干那份。

# CARD-G2-9-F1-canary — F2 之后三存储 canary 完整复跑 + (e) side_effect_probe 守卫两态真跑（U5-A 移交的「未真跑」项落地，零生产改动）

## 〇 事实

> 下列 file:line 全部在 **B14_BASE 树**（`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev`）实测；canary 脚本属 T1 车道地盘、**可能已被 T1-A 动过**，所以开工先核 sha、判据一律用符号名/字符串锚（不用行号），行号只作今日语境。

| 事实 | 位置 / 实测命令 |
|---|---|
| **本卡身份 = U5-A 移交项**：U5-A（CARD-G2-9-F1）的 (e) 只做了静态核（ast.parse + 区段计数），**未真跑**完整 canary、未验证「关探针不 KeyError / 开探针且 FAIL 时 rc 变 `EXIT_ISOLATION_FAILED`」，显式移交到本卡 | U5-A 卡文 §四「本卡未证明什么 ⑦」「台账待登记 ③/⑫」：`_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U5-A.md` |
| canary 脚本 = `backend/scripts/g29_dual_vault_canary.py`（B14_BASE 1497 行；tracked），B14_BASE sha = `5411cf14da00cabfec8e1f8ddd1f56c8ffeeda745b1eb147536d4927e200ee7a`（**若 T1-A 改过，以开工实测 sha 为准**） | `shasum -a 256 backend/scripts/g29_dual_vault_canary.py` |
| 退出码：`EXIT_OK=0`（`:158`）/ `EXIT_ISOLATION_FAILED=1`（`:159`）/ `EXIT_PRECONDITION_REJECTED=2`（`:160`）/ 端口门最终总账强制退出 `3`（docstring `:45`） | `grep -n '^EXIT_' backend/scripts/g29_dual_vault_canary.py` |
| (e) 探针 `async def probe_schema_drift_side_effect`（B14_BASE `:1244`）用 vault `g29drift_a`/`g29drift_b`（`:1255`）+ B 以 `embedding_dim=16` 建表、A 以 `CANARY_VECTOR_DIM=8`（`:118`）`initialize()`；结果字典含 `B_table`/`B_table_survived_A_init`/`verdict`(`"PASS" if b_table in after else "FAIL"`)/`finding`/`source` | `grep -n 'def probe_schema_drift_side_effect\|verdict\|B_table_survived_A_init' backend/scripts/g29_dual_vault_canary.py` |
| `side_effect_probe` 是**条件顶层键**：`_amain` `if args.probe_schema_drift:`（B14_BASE `:1423`）才写入（`:1424`）；`--no-probe-schema-drift`（`dest=probe_schema_drift, action=store_false`，`:1470-1474`）关得掉；`ap.set_defaults(probe_schema_drift=True)`（`:1485`）默认开。rc 守卫 `probe = report.get("side_effect_probe")`（`:1451`）+ `if probe is not None and probe.get("verdict") != "PASS":`（`:1452`）→ 三行 stderr print 后 `return EXIT_ISOLATION_FAILED`（`:1457`，整块 `:1451-1457`）——**带守卫，关探针不 KeyError** | `grep -n 'args.probe_schema_drift\|report.get("side_effect_probe")\|no-probe-schema-drift\|set_defaults' backend/scripts/g29_dual_vault_canary.py` |
| `run_canary`（`:1024`）用 `VAULT_A="vault:g29canary_a"`（`:101`）/ `VAULT_B="vault:g29canary_b"`（`:102`），三存储端到端，唯一外部依赖 = **7692** 测试容器（用法 docstring `:32-36`）。⚠️ **canary 不碰任何 embedding 服务**：向量是常量 `[0.1]*CANARY_VECTOR_DIM`（`:613`/`:724`）、probe 侧 `[0.2]*16`（`:1262`），脚本自述注释「8 维既不碰 embedding 服务也让写入是确定性的」（`:116-118`），全文 `bge-m3`/`ollama` 命中 **0**——故 (b) 不设嵌入端前置（设了就是恒可 HALT 的假红） | `grep -n 'VAULT_A\s*=\|VAULT_B\s*=\|def run_canary' backend/scripts/g29_dual_vault_canary.py`；`grep -ciE 'bge-m3\|ollama' backend/scripts/g29_dual_vault_canary.py` → `0`；lazy import 清点 `grep -nE '^\s+(from\|import) ' …` → 12 条全是 graphiti_core / app.* / LanceDBClient，**无任何 embedding 客户端** |
| 前置负控（**零 socket、纯前置拒绝 → rc=2**）：①`NEO4J_TEST_URI` 未设 → `_preflight_neo4j_uri` 抛 `PreconditionRejected`（`:344-351`）；②LanceDB 路径命中 `FORBIDDEN_LANCEDB_SUFFIXES`（如 `*/data/lancedb`）→ `_preflight_lancedb_path` 拒（`:393-398`，mkdir **之前**判） | `sed -n '335,407p' backend/scripts/g29_dual_vault_canary.py` |
| `--verify-judges`（`:1481-1484`）= 逐条注入已知破坏隔离的变异、要求指定判据当场翻红；历史报告 `canary-verify-judges-20260906T021613Z.json` 实测 `all_killed=True`、`coverage={covered:14,total:14,complete:True}`——**只覆盖 `report["verdicts"]` 的 14 条**，不覆盖 side_effect_probe 的 verdict | `python3 -c "import json;d=json.load(open('_bmad-output/审查/evidence-g29/canary-verify-judges-20260906T021613Z.json'));print(d['all_killed'],d['coverage'])"` |
| **红参照（历史，U5-A 修复前）**：`_bmad-output/审查/evidence-g29/canary-report-20260906T021427Z.json` 的 `side_effect_probe.B_table_survived_A_init == false` + `finding` 含 `CONFIRMED: vault A 的 LanceDBClient.initialize() 删掉了 vault B 的表`（tracked，车道树里有） | `python3 -c "import json;p=json.load(open('_bmad-output/审查/evidence-g29/canary-report-20260906T021427Z.json'))['side_effect_probe'];print(p['B_table_survived_A_init'],p['finding'])"` |
| 现行（B14_BASE / 波 0）生产侧：`_cache_tables`（`:1020-1056`）的维度检查已由 U5-A 收窄为 `if self._owns_table(t, owner_vault) and not t.endswith(self.FINGERPRINT_TABLE)`（条件行 `:1049`，整段列表推导 `:1046-1050`；`owner_vault = self.active_vault_id` 提到循环外 `:1045`）——非前缀重叠的 `g29drift_b_*` 不归 `g29drift_a`，故 probe 在 B14_BASE 上**已为 PASS** | `sed -n '1044,1053p' backend/lib/agentic_rag/clients/lancedb_client.py` |
| **本批纪律**（协议 §零/§2.2/§2.3）：判据 grep git 输出一律 `--no-color` + 同次验伪锚；evidence 用 `.txt`（仓根 `*.log` 被 `.gitignore` 吞）；承重裁判末行 `echo rc=$pipestatus[1]`（zsh，`tee` 吞退出码）；ruff 判据用 zsh 数组（本卡零 py 改动，不触发）；**批中禁装工具**（不往共享 venv 装/升任何包，Ollama/7692 用现成的）；`fsrs_bridge.py`/`decay_beta.py` ⛔ 零写者；**live vault / 7691 / 7687 / 现网 LanceDB 只读**；pyright 保持 0（本卡零 `backend/app` 改动，不触发 `python-typecheck`，纪律在案）。 | — |

## 一 完成条件（AND）

- **(a) 第 0 分钟自证（全部落档到 evidence 目录，缺任一停下报主 session）**：`cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance` → `pwd` 在该车道树；`git branch --show-current` = `card/t1-lance`；`git log --oneline -3`（取 T1-A 末 commit SHA = `$PREREQ` 落档）；`git status --porcelain` **为空**（前提：T1-A 已独立 commit、工作树干净）；`test -x $(pwd)/backend/.venv/bin/python && $(pwd)/backend/.venv/bin/python -c "import sys;print(sys.executable)"`；`test -f $(pwd)/backend/.env`；**canary 开工 sha 落档** `shasum -a 256 backend/scripts/g29_dual_vault_canary.py`（记为 `$SHA0`）；**红参照落档**：抄出历史 `evidence-g29/canary-report-20260906T021427Z.json` 的 `side_effect_probe.B_table_survived_A_init`(=false) 与 `finding`(=CONFIRMED…删掉了) 进 evidence（这是 U5-A 修复前的红态，本卡零生产改动**不重建红**）。
- **(b) 前置可用性核（不满足即 HALT + 登记，不伪造 PASS）**：唯一前置 = 7692 测试容器 `nc -z 127.0.0.1 7692`（rc=0）。不可达 → 在验收单写「前置不满足，canary 真跑未执行」并停下交主 session，**不得**声称本卡通过。⛔ 全程禁触 7691/7687。⚠️ **不设嵌入端前置**：canary 用常量向量、零 embedding 调用（§〇 第 6 行实测，`grep -ciE 'bge-m3\|ollama' …` = 0），把 bge-m3 写成 HALT 门等于给本卡挂一个与判据无关、却随时能让全卡停摆的假红；开工用该 grep = 0 落档作依据。
- **(c) 两态真跑 + rc 对照（核心判据）**：同一树、各用一个**全新** `mktemp -d` 的 tmp LanceDB 路径，`NEO4J_TEST_URI=bolt://localhost:7692`：
  - **ON 态**（默认，不带 `--no-probe-schema-drift`）→ rc = `0`（`EXIT_OK`）；报告 JSON 里 `side_effect_probe.verdict == "PASS"` **且** `side_effect_probe.B_table_survived_A_init == true` **且** `B_table in tables_after_A_init`（即「B 表在 A init 后仍在」）。
  - **OFF 态**（带 `--no-probe-schema-drift`）→ rc = `0`；报告 JSON **无** `side_effect_probe` 键（证明条件键 opt-out 生效、关探针不 KeyError——这正是 U5-A 移交要真跑验证的点）。
  - 两态报告/账本均落 `$EV`；ON 态 tee 输出里 `live_port_guard` 的 `summary_line()` 含 `blocked=0`（只打到 7692 白名单、没碰 live port）。
- **(d) 验伪锚（可运行，证判据有牙齿）**：`--verify-judges` 真跑 → rc = `0`（`EXIT_OK`）且报告 `all_killed == true`、`coverage.complete == true`（`covered==total`，当前 14/14）——证明 run_canary 的每条 verdict 都被变异点名过、能翻红。⚠️ 如实声明：`--verify-judges` **不覆盖** side_effect_probe 的 verdict（它是条件顶层键、不在 `report["verdicts"]` 里），probe 的翻红能力只有 (a) 的历史红参照，本卡不重建（见「本卡未证明什么」）。
- **(e) 前置负控两条（纯前置拒绝，零 socket，不碰 7691）**：①`env -u NEO4J_TEST_URI` 跑 canary → rc = `2`（`EXIT_PRECONDITION_REJECTED`，`NEO4J_TEST_URI 未设置` 被拒，根本不连库）；②`NEO4J_TEST_URI=bolt://localhost:7692` 但 `--lancedb-path` 指向命中禁用后缀的路径（`<tmp>/data/lancedb`）→ rc = `2`（`LanceDB 路径…指向现网默认库` 被拒，mkdir 前拒、无 Neo4j 连接）。两条各自 tee 落档 + 末行 rc。
- **(f) 脚本 sha 跑前=跑后（零生产改动的铁证）**：收工 `shasum -a 256 backend/scripts/g29_dual_vault_canary.py` = `$SHA0`（逐字节相同）；`grep -cF 'side_effect_probe' backend/scripts/g29_dual_vault_canary.py` 与开工相同。若任一不同 = 本卡误改了生产脚本，停下。
- **(g) 地盘核（只允许 `_bmad-output/**` 面）**：`git --no-pager diff --stat --no-color $PREREQ HEAD -- . ':(exclude)_bmad-output'` **输出为空**（本卡零代码/测试改动；⚠️ 必须写 `':(exclude)…'` 不是 `':!…'`，后者在 zsh/本机 git 2.50 报 `Unimplemented pathspec magic`、rc=128、stdout 空，会把没跑成读成绿）；验伪锚：同次先 `git --no-pager diff --stat --no-color $PREREQ HEAD | head` 证命令本身能出非空行（至少列出 `_bmad-output` 下的新增 evidence/验收单）。
- **(h) tests/unit 目录级 diff 只许 `<`**：本卡零代码改动 ⇒ tests/unit 红集不可能被本卡改变，(g) 即主证。为满足批级口径仍做：开工/收工各跑一次**与基线逐字同跑法**（R-B14-3：先 `cd backend`，`--ignore` 写相对路径）`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider` 取 nodeid 集并 `diff`（期望**完全相同**，0 新增 `>` 0 消失 `<`；跑前先落开工快照）。⛔ `--ignore` 必须是**相对** `tests/unit/…`：`cd backend` 之后写 `backend/tests/unit/…` 匹配不到任何被收集文件 = 空操作，R-15 点名的挂起源 `test_deploy_vault_sh.py` 会被真跑（R-B14-3）。批级基线参照（主 session 集成用）= `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`，自证口径 `grep -vc '^#' <基线>` = **64**（⛔ 禁 `grep -c '::'`——注释里逐字引了一条 flaky nodeid，那个数是 65，R-B14-2）。⚠️ F2（T1-A）已去掉 6 条 xfail 锁，车道 tip 的红集与 08100483 基线本就不同；本卡的对照基准是**车道 T1-B 开工快照**，不是原始 08100483。
- **(i) 收尾（Codex + 验收单 + commit，见 §四）**：Codex **1 轮**（零代码卡）绑最终 HEAD BLOCKER/HIGH = 0；验收单 DoD-3 双段；「本卡未证明什么」「台账待登记条目」各 ≥4 条；commit header ≤100 含批次标记且含 `CARD-G2-9-F1-canary`；`*.stderr*` 不入库；不改台账；不 push；独立 commit 后本车道收工（T1 仅 2 卡）。

## 二 裁判命令

> zsh；承重裁判 `2>&1 | tee "$EV/<name>-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]`；grep git 输出一律 `--no-color`。evidence 用 `.txt`。

```zsh
# —— (a) 第 0 分钟 ——
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance
PY=$(pwd)/backend/.venv/bin/python
EV=$(pwd)/_bmad-output/审查/evidence-g29f1-canary
mkdir -p "$EV"
git branch --show-current                                            # card/t1-lance
git log --oneline -3 | tee "$EV/prereq-$(date +%Y%m%dT%H%M%S).txt"   # 取 T1-A 末 commit = $PREREQ，手抄进下一行
PREREQ=<把上面 T1-A 末 commit SHA 填这里>
git status --porcelain | tee "$EV/status-start.txt"                  # 必须为空
test -x "$PY" && "$PY" -c "import sys;print(sys.executable)"
test -f "$(pwd)/backend/.env" && echo ".env ok"
shasum -a 256 backend/scripts/g29_dual_vault_canary.py | tee "$EV/canary-sha-start.txt"   # = $SHA0
SHA0=$(shasum -a 256 backend/scripts/g29_dual_vault_canary.py | awk '{print $1}')
grep -cF 'side_effect_probe' backend/scripts/g29_dual_vault_canary.py | tee "$EV/probe-key-count-start.txt"
# 红参照（历史，不重建）
"$PY" -c "import json;p=json.load(open('_bmad-output/审查/evidence-g29/canary-report-20260906T021427Z.json'))['side_effect_probe'];print('RED-REF B_survived=',p['B_table_survived_A_init'],'|',p['finding'])" \
  2>&1 | tee "$EV/red-ref-$(date +%Y%m%dT%H%M%S).txt"
# 基线自证（R-B14-2 唯一口径；禁 grep -c '::'）
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt
test -f "$BASE" && grep -vc '^#' "$BASE" | tee "$EV/unit-base-selfcheck.txt"   # 期望 64
# tests/unit 开工快照（与 (h) 收工快照 unit-end-* 同口径、同命令，作 diff 对照基准）
# ⛔ R-B14-3：先 cd backend，--ignore 用相对路径（写 backend/tests/… 是空操作，R-15 挂起源会被真跑）
ROOT=$(pwd)
cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit \
  --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider \
  2>&1 | tee "$EV/unit-start-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
cd "$ROOT"

# —— (b) 前置可用性 ——
nc -z 127.0.0.1 7692 && echo "7692 up" | tee "$EV/precheck-7692.txt"   # rc=0 必须；不可达→HALT 登记
# 不设嵌入端前置的依据（落档）：canary 全文零 bge-m3/ollama 引用，向量是常量
grep -ciE 'bge-m3|ollama' backend/scripts/g29_dual_vault_canary.py | tee "$EV/no-embed-dep.txt"   # 期望 0
grep -nE 'CANARY_VECTOR_DIM = |\[0\.1\] \* CANARY_VECTOR_DIM' backend/scripts/g29_dual_vault_canary.py | tee -a "$EV/no-embed-dep.txt"   # 同次验伪锚：grep 能命中已知正例（:118/:613/:724）

# —— (c) 两态真跑 ——
export NEO4J_TEST_URI=bolt://localhost:7692
T_ON=$(mktemp -d)
"$PY" backend/scripts/g29_dual_vault_canary.py --evidence-dir "$EV" --lancedb-path "$T_ON" \
  2>&1 | tee "$EV/run-on-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 期望 rc=0
T_OFF=$(mktemp -d)
"$PY" backend/scripts/g29_dual_vault_canary.py --evidence-dir "$EV" --lancedb-path "$T_OFF" --no-probe-schema-drift \
  2>&1 | tee "$EV/run-off-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 期望 rc=0
# 解析最新两份报告：ON 有 side_effect_probe.verdict==PASS & B_table_survived_A_init==true & B_table in tables_after_A_init；OFF 无该键
"$PY" - <<'PYEOF' 2>&1 | tee "$EV/two-state-assert-$(date +%Y%m%dT%H%M%S).txt"
import json,glob,os
ev=os.path.join(os.getcwd(),"_bmad-output/审查/evidence-g29f1-canary")
reps=sorted(glob.glob(ev+"/canary-report-*.json"))
print("latest reports:",reps[-2:])
# 人工按时间戳区分 ON/OFF；逐份打印关键字段
for r in reps[-2:]:
    d=json.load(open(r)); p=d.get("side_effect_probe")
    print(os.path.basename(r),"| has_probe=",p is not None,
          "| verdict=",(p or {}).get("verdict"),
          "| B_survived=",(p or {}).get("B_table_survived_A_init"),
          "| B_in_after=",((p or {}).get("B_table") in (p or {}).get("tables_after_A_init",[])) if p else "n/a")
PYEOF
grep -oh 'blocked=[0-9][0-9]*' "$EV"/run-on-*.txt | sort -u | tee "$EV/blocked-tokens.txt"   # 期望仅一行 blocked=0
[ "$(grep -oh 'blocked=[0-9][0-9]*' "$EV"/run-on-*.txt | sort -u)" = "blocked=0" ] && echo "blocked=0 OK" || echo "⛔ blocked 非0或缺失"   # 等值断言：不取尾行、缺失或任何非 0 都判红
printf 'summary: blocked=7 allowed=1\n' | grep -oh 'blocked=[0-9][0-9]*'   # 同次验伪锚：必打出 blocked=7，证这条 grep 真能命中非 0 值（不是「恒抓不到 ⇒ 恒空 ⇒ 恒红/恒绿」）

# —— (d) 验伪锚 ——
T_VJ=$(mktemp -d)
"$PY" backend/scripts/g29_dual_vault_canary.py --evidence-dir "$EV" --lancedb-path "$T_VJ" --verify-judges \
  2>&1 | tee "$EV/verify-judges-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 期望 rc=0
"$PY" -c "import json,glob,os;ev=os.path.join(os.getcwd(),'_bmad-output/审查/evidence-g29f1-canary');f=sorted(glob.glob(ev+'/canary-verify-judges-*.json'))[-1];d=json.load(open(f));print('all_killed=',d['all_killed'],'coverage=',d['coverage'])" \
  2>&1 | tee "$EV/verify-judges-assert-$(date +%Y%m%dT%H%M%S).txt"   # all_killed True / complete True

# —— (e) 前置负控两条（rc=2，零 socket） ——
T_N1=$(mktemp -d)
env -u NEO4J_TEST_URI "$PY" backend/scripts/g29_dual_vault_canary.py --evidence-dir "$EV" --lancedb-path "$T_N1" \
  2>&1 | tee "$EV/negctl-no-uri-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 期望 rc=2
T_N2=$(mktemp -d)
"$PY" backend/scripts/g29_dual_vault_canary.py --evidence-dir "$EV" --lancedb-path "$T_N2/data/lancedb" \
  2>&1 | tee "$EV/negctl-forbidden-path-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 期望 rc=2

# —— (f) sha 跑前=跑后 ——
shasum -a 256 backend/scripts/g29_dual_vault_canary.py | tee "$EV/canary-sha-end.txt"
[ "$(shasum -a 256 backend/scripts/g29_dual_vault_canary.py | awk '{print $1}')" = "$SHA0" ] && echo "SHA UNCHANGED" || echo "⛔ SHA CHANGED"
grep -cF 'side_effect_probe' backend/scripts/g29_dual_vault_canary.py | tee "$EV/probe-key-count-end.txt"

# —— (g) 地盘核 ——
git --no-pager diff --stat --no-color "$PREREQ" HEAD -- . ':(exclude)_bmad-output' \
  2>&1 | tee "$EV/turf-outside-bmad-$(date +%Y%m%dT%H%M%S).txt"    # 期望为空
git --no-pager diff --stat --no-color "$PREREQ" HEAD | head          # 验伪锚：证命令能出非空行（_bmad-output 下有增量）

# —— (h) tests/unit 目录级 diff（开工/收工各一次；与 (a) 开工快照逐字同跑法） ——
ROOT=$(pwd)
cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit \
  --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider \
  2>&1 | tee "$EV/unit-end-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
cd "$ROOT"
# 取 unit-end-* 与 (a) 的 unit-start-* 两份 tee 的 nodeid 集 diff（期望完全相同：0 新增 > / 0 消失 <）
diff <(grep -oE '^(FAILED|ERROR) [^ ]+' "$EV"/unit-start-*.txt | sort -u) \
     <(grep -oE '^(FAILED|ERROR) [^ ]+' "$EV"/unit-end-*.txt   | sort -u) \
  2>&1 | tee "$EV/unit-diff-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 期望空
# 同次验伪锚（三行都必须打出非 0；空集对空集的 diff 也是「空」= 假绿）
grep -oE '^(FAILED|ERROR) [^ ]+' "$EV"/unit-start-*.txt | sort -u | wc -l   # 必 >0
grep -oE '^(FAILED|ERROR) [^ ]+' "$EV"/unit-end-*.txt   | sort -u | wc -l   # 必 >0 且与上一行相等
grep -cE '^(FAILED|ERROR) ' "$BASE"                                         # 已知正例 = 64，证这条提取式真能命中同形行
```

## 三 禁改与隔离

- **本卡地盘（只允许新增这些，全在 `_bmad-output/**`）**：`_bmad-output/审查/evidence-g29f1-canary/**`（报告/账本/裁判 tee）、`_bmad-output/验收单/UAT-CARD-G2-9-F1-canary-<日期>.md`、`_bmad-output/审查/codex-review-CARD-G2-9-F1-canary-r1.md`（+ prompt `_bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F1-canary.md`）、本卡文自身。
- **零代码/零测试改动**：`backend/scripts/g29_dual_vault_canary.py` **只读/执行、不改**（sha 跑前=跑后，(f)）；`backend/lib/agentic_rag/clients/lancedb_client.py` 与 `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`（T1-A 地盘）**只读不碰**；不碰 `backend/app/**`（零文件，不触发 typecheck）。
- **若 canary 复跑暴露新缺陷**（verdict FAIL / 隔离判据红 / blocked>0 / 跨 vault 连带删表复现）：**停下**，在验收单与「台账待登记条目」如实登记（含报告路径、复现命令、rc），**不在本卡修**——本卡严格零生产改动，修复另立卡由主 session 排。
- **硬边界**：禁写 live vault；禁连 7691 / 7687（负控只用「未设 URI」与「禁用后缀路径」两条纯前置拒绝，zero socket）；7692 为测试容器、可连但只写本卡自己的 canary vault；**本卡不连任何嵌入端**（canary 用常量向量，§〇 第 6 行实测）；禁碰 `fsrs_bridge.py` / `decay_beta.py`；禁 `git stash`（共享栈，用临时 WIP commit 代替）；**不改台账**（只在验收单写「台账待登记条目」）；**批中禁装/升任何包**；不 push。

## 四 Codex / 验收单

**Codex 命令**（协议 §2 固定）：
```zsh
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F1-canary.md)" \
  > _bmad-output/审查/codex-review-CARD-G2-9-F1-canary-r1.md \
  2> _bmad-output/审查/codex-review-CARD-G2-9-F1-canary-r1.stderr </dev/null
```
**轮次**：**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（上限 5 轮；**本卡零生产/测试代码改动 ⇒ 零代码卡 ⇒ 1 轮**；审后若改动任何 `_bmad-output` 以外的代码即转有代码卡、必再送一轮；车道对 HIGH 的驳回写理由但不能自判通过，交主 session 复核；0 字节存档重发一次，再 0 字节 → 主 session 人审替代）。

**存档首部**（协议 §2.1，六行 blockquote + `---`，缺 `模型`/`reasoning_effort`/`codex` 任一 = 该轮不计配额）：批次/车道/卡/round-1；`模型 gpt-6-astra · reasoning_effort ultra · codex 实测版本`（`codex --version`）；命令行；审查绑定（最终 HEAD SHA，与 HEAD 不同须如实写）；会话头自证抄 `.stderr` 中含 **codex 版本行 + `model:` 行 + `reasoning effort` 行** 的三行并括注行号（codex 0.153.x 把 `model:` 排在会话头靠后，字面抄前三行会漏字段——按行号抄实际那三行；`.stderr` 本身不入库）。

**Prompt 五分节要点**（prompt 里 ⛔ 不得出现会触发 cyber 拦截的攻击类措辞；一律改说「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」）：
- **一 背景**：本卡是 CARD-G2-9-F1（U5-A）移交的 canary 完整复跑 + (e) side_effect_probe 守卫两态真跑；零生产改动。
- **二 最小读取面（写死）**：`backend/scripts/g29_dual_vault_canary.py` 的 `_amain` / `_run_canary_cli` / `probe_schema_drift_side_effect` / `_preflight_neo4j_uri` / `_preflight_lancedb_path` 五个函数全文 + argparse 段；本卡 evidence 目录 `_bmad-output/审查/evidence-g29f1-canary/` 全部报告与 tee；`git diff $PREREQ HEAD -- . ':(exclude)_bmad-output'`（应为空）。
- **三 作者自述请独立核对**：①两态 rc 与报告字段（ON：verdict PASS + B_table_survived_A_init true + B_table∈tables_after_A_init；OFF：无 side_effect_probe 键、rc 仍 0、无 KeyError）是否与 tee 一致；②前置负控两条是否都在 preflight 拒绝（未开 socket、未连任何库）、rc 确为 2、而非在运行期才失败；③`--verify-judges` 的 all_killed/coverage 是否真来自本卡新跑的报告而非历史文件；④脚本 sha 跑前=跑后是否逐字节；⑤地盘 diff（排除 `_bmad-output`）是否为空。
- **四 按重要性排序的问题**：⓪ canary 的 vault id（run_canary 的 `g29canary_a`/`g29canary_b`、probe 的 `g29drift_a`/`g29drift_b`）都**非前缀重叠**，本卡是否**错误声称**验证了 F2 的最长前缀归属（它没有——该面由 T1-A 单测证）；① OFF 态「无 side_effect_probe 键」是否被误当成「探针通过」（应是「探针未跑」）；② 历史红参照是否被当成本卡重建的红（应如实标注为历史、不可重建）；③ blocked=0 是否被单独当作隔离成立证据（不应）；④ 前置负控是否真零 socket（有无走到驱动连接）。
- **五 边界**：只读、不连任何库、不评 `_check_and_fix_dimension_mismatch` 的 drop 条件设计、不评完整 canary 的嵌入/图存储实现。

**验收单** `_bmad-output/验收单/UAT-CARD-G2-9-F1-canary-<日期>.md`（DoD-3 双段，覆盖原 `_bmad-output/templates/uat-sheet-template.md` 7 段结构）：
- **4-A Claude 已代验**（技术 assert 贴证据）：两态 rc + 报告字段、验伪锚 all_killed/coverage、两条前置负控 rc=2、sha 跑前=跑后、地盘 diff 空、tests/unit diff 空——每条贴 evidence 路径与末行 rc。
- **4-B 你来验**（零技术词，「我做 X → 我看到 Y → 我感觉 Z」+ felt-sense）：例「我把两门课的资料库各建一份、再重开其中一门 → 我看到另一门的资料一张都没少、自己那门过期的旧索引还会自动重建 → 我感觉两门课的东西终于互不打扰，切换时很安心」。

**本卡未证明什么**（≥4）：①未证明 canary 覆盖 F2 的**前缀重叠**修复面——run_canary 与 probe 的 vault id 均非前缀重叠（末字符不同、互不为前缀），F2 的 `a`/`a_b` 最长前缀归属只由 T1-A 单测 `test_lancedb_cross_vault_drop_g29f1.py`（xfail→XPASS 翻转）证明，本卡 canary 不碰这条面；②未证明 side_effect_probe 的 verdict 判据**自身**可翻红——`--verify-judges` 只覆盖 run_canary 的 14 条 `report["verdicts"]`，probe 的 verdict 是条件顶层键、不在覆盖集，其翻红能力只有历史红参照（U5-A 修复前报告），本卡零生产改动**不重建红**；③未做现网 LanceDB 备份对账（是否已有被误删的 B 表只能从备份查，D-41 需授权，本卡不做）；④未真跑 7691 端口门负控（禁连 7691）——端口门拦 7691 的牙齿由历史 `evidence-g29/canary-negctl-*.txt` 证据引用，本卡负控只用「未设 URI」「禁用后缀路径」两条零 socket 的前置拒绝；⑤未证明 7692 不可用时的降级——前置不满足即 HALT 上报，不伪造 PASS；也未证明「canary 未来接入真实嵌入端后仍隔离」——B14_BASE 的 canary 全程用常量向量、零 embedding 调用（`grep -ciE 'bge-m3\|ollama' …` = 0），本卡的隔离结论只在这个「确定性向量」前提下成立。

**台账待登记条目**（≥4）：①T1-B = U5-A 移交项（台账 ③ 完整 canary 复跑 + ⑫ (e) 守卫两模式真跑）落地：本卡 commit sha + 两态报告路径 + 验伪锚报告路径；②canary 脚本 sha 跑前=跑后（零改动），开工 `$SHA0`（B14_BASE `5411cf14…`，T1-A 若改过记 T1-A tip 值）；③两态 rc（ON/OFF 各 0）+ probe verdict=PASS + B_table 存活 + guard `blocked=0` 落档路径；④`--verify-judges` all_killed + coverage 14/14 complete；⑤口径更正三条（排批期主 session 实测，已写进本卡文）：(1) U5-A/勘探的 (e) 守卫行 `:1415-1416` → 实测 B14_BASE `:1423-1424`（canary 合入 F1 实现后增长）；(2) 原卡文把「Ollama bge-m3 嵌入端可达」列为 (b) HALT 前置 = **假前置**，实测 canary 零 embedding 调用（脚本自述 `:116-118` + 全文 `bge-m3`/`ollama` 命中 0），已删该门并改为落档 grep=0 作依据；(3) (h) 的 tests/unit 跑法原为车道树根 `pytest backend/tests/unit` 无 `--ignore`，会真跑 R-15 点名的挂起源 `test_deploy_vault_sh.py`，已按 R-B14-3 改为 `cd backend` + 相对 `--ignore tests/unit/test_deploy_vault_sh.py`、并按 R-B14-2 把基线自证定为 `grep -vc '^#'` = 64；⑥Codex 1 轮存档路径、绑定最终 HEAD SHA、B/H/M/L 计数；⑦地盘核结果（`:(exclude)_bmad-output` diff 为空）+ tests/unit diff 结果；⑧若 canary 复跑暴露新缺陷则停下登记（本卡不修）的条目占位 + D-41 现网备份对账移交。

commit header ≤100 含批次标记 `[BATCH-2026-09-11-第十四批 / CARD-G2-9-F1-canary]` 且含卡号；body 行 ≤100；`*.stderr*` 不入库（`.gitignore` 已覆盖）；不 push；独立 commit 后本车道（T1 共 2 卡）收工；跑完说「**复核第十四批 T1**」。
