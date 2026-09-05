> ⚠️ 本文件是 CARD-TOOL-pyright 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z7-B 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-TOOL-pyright]`。车道：`card-z7-tool`，**前提 Z7-A 两个 commit 已落**。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-TOOL-pyright — 装 pyright + 依赖声明归口 + 存量类型债一次性口径（X5-A 的后半段）

## 〇 事实
| 事实 | 位置 |
|---|---|
| X5-A（`e3ead62e`）只把 python-typecheck 从「说谎」改成「诚实 SKIP」：`lefthook.yml` 块（X8 后行号漂移，开工重取）先查 `backend/.venv/bin/pyright` 再查 PATH，都没有则两行 SKIP + `exit 0`；装上后自动走真跑 + `exit $PYRIGHT_EXIT`——**装 pyright 本身不需要再改 lefthook.yml** | lefthook.yml |
| 实机：`backend/.venv/bin` 有 ruff，无 pyright、无 mypy；PATH 无 pyright → SKIP 分支 100% 命中，门名义存在实际零覆盖 | `ls backend/.venv/bin` |
| 口径矛盾：根 `requirements.txt:189 / :268` 声明 `mypy>=1.5.0`（注释「类型检查」），而 `pyrightconfig.json` + lefthook 用 pyright；两者都没装 | requirements.txt / pyrightconfig.json |
| pyright 未在任何依赖声明出现（backend/requirements.txt、根 requirements.txt、pyproject.toml、tests/contract/requirements.txt、setup.cfg 全无） | grep |
| `pyrightconfig.json`：include = [backend/app, src, tests]（:2-6）、typeCheckingMode=basic、pythonVersion=3.14（:13）、venvPath=backend / venv=.venv（:15-16）；backend/app 258 个 .py、src 0、根 tests 35（backend/tests 461 不在 include）；backend/app 现存 `type: ignore` 22 处 | pyrightconfig.json |
| 版本口径不一：pyrightconfig 3.14 vs 根 `pyproject.toml:6 requires-python>=3.9` vs `backend/ruff.toml:7 target-version=py39` | 三处 |

## 一 完成条件（AND）
- (a) 先解决口径矛盾：pyright vs mypy 二选一并写明理由；选 pyright 则同批把 `requirements.txt` 里的 mypy 声明改注释或删除，不留两套。
- (b) 依赖落点：pyright 写进 `backend/requirements*.txt`（或新建 `backend/requirements-dev.txt` 并在 lefthook/CI 侧显式引用），装进 `backend/.venv`（本车道的 venv 是 symlink 到 card-v5-lance——**装进真实 venv 目录会影响所有 symlink 车道，验收单写明**）；禁止只在本机 pip install 而不落声明。
- (c) pythonVersion 对齐：给出一句结论性口径并改到一致，或明确记为「刻意不一致」并写清后果。
- (d) 存量类型债基线：在现有 include 上跑一次全量 pyright，error/warning 数按规则码 top-10 落表进验收单；src 为空集这一事实写进表。
- (e) 债不阻断新代码：pre-commit 只对 staged 文件跑（`{staged_files}` 已是）；不得为让存量变绿调低 typeCheckingMode 或大面积加 `# type: ignore`（22 处，本卡后增量 ≤ 0 并报出）。
- (f) 负控两条：① 临时把 pyright 从 PATH/venv 遮蔽，重跑 python-typecheck → 仍走 SKIP 且 rc=0（X5-A 承诺不被破坏）；② 构造必然类型错误的 staged 文件 → hook rc≠0 阻断。产物不入 commit。
- (g) 一轮 Codex（gpt-6-astra ultra），审查面 = 本卡 diff（依赖声明 + 配置 + 验收单债表）。

## 二 裁判命令
1. `backend/.venv/bin/pyright --version`。
2. `backend/.venv/bin/pyright --outputjson backend/app 2>&1 | tail -5`（取 summary 的 errorCount/warningCount）。
3. `grep -n -i 'pyright\|mypy' backend/requirements*.txt requirements.txt pyproject.toml` → 单一口径。
4. `git ls-files 'backend/app/**/*.py' | wc -l` → 258（债表分母）；`grep -rn 'type: ignore' backend/app | wc -l` → ≤ 22。
5. `/opt/homebrew/bin/lefthook run pre-commit --command python-typecheck --force --no-auto-install`（先 `git add` 一个 backend/app 空白改动，跑完还原）→ 真跑并按 rc 传递；负控 ① ② 输出贴验收单。

## 三 禁改与隔离
禁删改或弱化 lefthook.yml 的 HONESTY CONTRACT 注释块与 SKIP 分支语义；禁为求绿下调 `typeCheckingMode` 或关 `reportMissingImports`；禁批量新增 `# type: ignore`；禁只在本机装不落声明；禁改 python-lint / mutant-residue-scan 块（Z7-A 面）；不改台账；不 push。

## 四 Codex / 验收单
命令同协议（`codex-prompt-CARD-TOOL-pyright.md` → `codex-review-CARD-TOOL-pyright.md`，1 轮）。验收单 `…/验收单/UAT-CARD-TOOL-pyright-<日期>.md`：DoD-3 双段；4-B「无变化（提交代码前多了一道类型检查，以前那道其实一直没开）」；「本卡未证明什么」必填：未证明 258 文件类型正确、未跑 CI、未把 pyright 接入 workflow；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push。**commit 后同车道继续 Z7-C。**
