> ⚠️ 本文件是 CARD-TOOL-lint-glob 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z7-A 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-TOOL-lint-glob]`。车道：NEW `card-z7-tool`（从 `304f03ca` 切；X8 已合入，`lefthook.yml` 现为 314 行版）。**所有碰 `lefthook.yml` 的卡都在本车道串行：Z7-A（本卡）→ Z7-B（pyright）→ Z7-C（Dredd 裁决）**。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-TOOL-lint-glob — lint glob 补 `scripts/` + `mutant-residue-scan` 门 + 存量格式债一次性定性（不混提）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 主干 `lefthook.yml` python-lint 块（X8 后行号漂移，开工 `grep -n 'python-lint:'` 重取）glob 为 `{backend,src}/**/*.py`；`src/` 下 tracked .py = **0**（该支恒空集）；`scripts/` 下 tracked .py = **90**（49 个在一级） | lefthook.yml / `git ls-files` |
| lefthook 2.1.6 glob 引擎实测矩阵（X8 卡钉死，`card-x8-openapi/lefthook.yml:40-47` 注释）：单 `*` 跨目录层级，`**` 反而要求至少跨一级；`{..}/**/*.py` 是 `{..}/*.py` 的真子集 → **天真改成 `{backend,src,scripts}/**/*.py` 会漏 scripts/ 一级 49 个 + backend/ 一级 2 个（`mutmut_config.py` / `start_server.py`）** | X8 |
| 配置口径疑点（**静态推断，须实机证伪**）：根 `ruff.toml` 只有 `[lint] select = []`（无 line-length），根 `pyproject.toml:71-88 [tool.ruff]` 写 line-length=120 / select=[E,W,F,I,B,C4]；按 ruff 同目录优先级，`scripts/` 解析到根 ruff.toml → lint 规则集空、formatter 行宽退回 88；`backend/ruff.toml` 自己 line-length=120 | ruff.toml / pyproject.toml |
| 存量债代理度量（**不是 ruff 结果**）：90 文件里 80 个含 >88 列行，合计 1450 行；台账硬数 `daily_review_pick.py` 33 处 | 勘探 |
| X7-A 登记的跨卡流程缺陷：变异体残留 `if False:  # MUTANT` 曾躺在 card-w7-ledger（主 session 已于波 0 还原，diff 存证 `evidence-w7-abandon/`）；下批三张变异卡都会再次原地改生产文件——`mutant-residue-scan` 门性价比最高 | 台账 |
| 真实案例：`fsrs_bridge.py` 被追加 `_s.exit(9)`，三裁判全绿 + `grep MUTANT`=0 全没抓到 → 本门是**廉价补充**不是证据锚点，唯一可靠锚点是全文件 sha 基线（g32b:1832-1838） | 诚实契约 |

## 一 完成条件（AND）
- (a) 按实测矩阵改 python-lint 的 glob：不得用 `{backend,src,scripts}/**/*.py`；改用单星形态或补一条 flat 命令；附本机 lefthook 逐文件探针矩阵（≥ `scripts/send_bark.py`（一级）、`scripts/lib/planning_utils.py`（二级）、`scripts/spec-tools/check-openapi-drift.py`、`backend/start_server.py`、`backend/app/main.py`）。
- (b) 先做配置口径定性：`backend/.venv/bin/ruff check --show-settings scripts/send_bark.py` 实机取回生效配置，「scripts/ 实际按哪套规则、哪个行宽」写进验收单；若推断错则以实测覆盖。
- (c) 存量债与门**分两个 commit**：commit-1 只改 glob + 必要的 ruff 配置口径 + (e) 的 mutant 门；commit-2 才是 `ruff format` 落盘。禁止同一 commit 既扩门又批量重排。
- (d) 扩面前的存量基线数字用 `ruff check` / `ruff format --check` 的**文件数与 diff 行数**（不是 1450/80 代理值），并与台账 `daily_review_pick.py`「33 处」对齐或显式更正。
- (e) `mutant-residue-scan` 门：在 pre-commit.commands 段末新增块，**不设 glob**（残留可落在 .md），只扫 `git diff --cached -U0 --diff-filter=AM` 的新增行，命中 `MUTANT` 即 echo 违规文件+行并 exit 1；排除名单显式写死并注释：`backend/scripts/g32b_mutation_gates.py`、`backend/scripts/g32cb_mutation_gates.py`、`_bmad-output/**`（这些文件里 MUTANT 是数据不是残留）；块内注释写明诚实契约（本门不检测不带 MUTANT 字样的残留；唯一可靠锚点是 sha 基线）。
- (f) 负控三条：① scripts/ 下临时构造必错文件（未定义名 + 格式漂移），`git add` 后跑 python-lint 命令 → rc≠0；② 暂存一份含 `if False:  # MUTANT` 的改动 → mutant 门 exit 1 且输出含文件名与行；③ 把 harness 自身重新暂存 → 放行 rc=0。负控产物同次还原，不入 commit。
- (g) 不动 python-typecheck / cypher-vault-filter-lint / readme-claims-lint / spec-sync-* 等同级块任何字节（Z7-B 与 X8 面）。
- (h) 一轮 Codex（gpt-6-astra ultra），审查面 = 两个 commit 的 diff。

## 二 裁判命令
1. `backend/.venv/bin/ruff --version`；`backend/.venv/bin/ruff check --show-settings scripts/send_bark.py | head -40`。
2. `backend/.venv/bin/ruff check $(git ls-files 'scripts/*.py' 'scripts/**/*.py') --statistics`；`backend/.venv/bin/ruff format --check $(…) 2>&1 | tail -20` → 基线数字进验收单。
3. `/opt/homebrew/bin/lefthook run pre-commit --command python-lint --force`（先 `git add` 一个 scripts/ 下空白改动，跑完还原干净；⚠️ 用 homebrew 2.1.6，**不用 `npx lefthook`**（1.13.6，flag 不兼容，且会隐式重装主仓 hooks——加 `--no-auto-install`））→ scripts/ 文件进入命中集。
4. `grep -n 'mutant-residue-scan' lefthook.yml` 落在 pre-commit 段内；该块下无 `glob` 键；负控 ② ③ 输出贴验收单。
5. `git diff 304f03ca HEAD -- lefthook.yml | grep -E '^[-+]' | grep -E 'python-typecheck|spec-sync|cypher-vault|readme-claims'` → 空（同级块零字节改动）。

## 三 禁改与隔离
禁整文件覆盖 `lefthook.yml`；禁用 `{backend,src,scripts}/**/*.py` 写法；禁把 `ruff format` 落盘与 glob 扩面写进同一 commit；禁顺手打开根 `ruff.toml` 的 lint 规则集（2000+ 存量违规，本卡只定性）；禁给 mutant 门加 glob 限定到 *.py；禁把扫描门做成仅 warning；禁在本卡内跑任何变异 harness；不改台账；不 push。

## 四 Codex / 验收单
命令同协议（`codex-prompt-CARD-TOOL-lint-glob.md` → `codex-review-CARD-TOOL-lint-glob.md`，1 轮）。验收单 `…/验收单/UAT-CARD-TOOL-lint-glob-<日期>.md`：DoD-3 双段；4-B「无变化（提交代码前多检查两件事：脚本目录也过格式检查；不小心留下的测试残片会被拦下）」；「本卡未证明什么」必填：未跑 CI、未证明 scripts/ 运行时行为、格式重排大文件未逐行人审、mutant 门不检测不带字样的残留；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push。**commit 后同车道继续 Z7-B。**
