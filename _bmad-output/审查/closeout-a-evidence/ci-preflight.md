# ② CI 接入前置核对（防「readme-claims 首跑翻车」重演）

> 本卡的硬约束是「本地等价验证先行」。但本地绿 ≠ CI 绿——CI 与本地至少有四处环境差。
> 下表逐条把差异点查实，写明**已消解**还是**如实遗留**。

| # | 差异点 | 核对方法 | 结论 |
|---|---|---|---|
| 1 | **依赖是否装得到** | `grep -in fsrs backend/requirements.txt` | ✅ 已消解。`fsrs==6.3.1`（:131），且该行注释本就点名 `test_fsrs_golden_vectors.py` 为绑定消费方。本地实测同为 6.3.1 ⇒ golden vectors 绑定的 `fsrs_library_version` / `fsrs_params_hash` 在 CI 与本地同源。 |
| 2 | **CI checkout 是否看得到测试引用的路径** | 对每条路径跑 `git ls-files` | ✅ 已消解。`canvas-vault/.claude/scripts/fsrs_bridge.py` **TRACKED**；`canvas-vault/.claude/skills` **TRACKED**。⚠️ `canvas-vault/learning_events.jsonl` **UNTRACKED**，但引用它的用例自带 skip 守卫（contract:1078「仓内 vault 根无 learning_events.jsonl (worktree 环境)」）——本地那 1 skipped 正是它，CI 上会同样 skip，**不会红**。 |
| 3 | **Python 版本** | CI matrix `['3.11','3.12']` vs 本地 `.venv` = 3.14.4 | ⚠️ **如实遗留**。未建 3.11/3.12 全量 venv（依赖树含 lancedb 等重包，历史重建耗时 ~35min 且 guard-hook 拦包卸载类命令，代价与收益不成比例）。**降级校验已做**：用 uv 的 cpython-3.11 / 3.12 对两个新文件跑 `py_compile` 双双通过；并扫描版本敏感构造（`datetime.UTC` / `itertools.batched` / `type` 语句 / `Self` / `ExceptionGroup` / `tomllib`）**命中 0**。<br>⚠️ 同时如实说明：**这条差异对现有 15 个文件完全同等存在**（它们也只在本地 3.14 被验证过），本卡的 2 个新增**没有加宽**这个缺口。 |
| 4 | **paths / branches trigger** | 人工读 `on:` 块（:9-31） | ✅ 已消解。`pull_request.paths` 与 `push.paths` 均含 `backend/**` ⇒ 两个新回归文件及其 `backend/tests/fixtures/learning_events/*.jsonl` 都在触发面内；`push.branches` 含 trunk 分支 `worktree-feature-obsidian-hybrid-dev` ⇒ 合并后即生效。<br>📌 **但 `push.branches` 不含 `card/*`** ⇒ feature 分支上 push 也不会触发 CI。这正是「本地等价验证先行」不可省的原因：**CI 上的第一次真跑，就是合并进 trunk 之后**。 |

## 逐条判定命令（可复现）

```bash
# 1 依赖
grep -in "fsrs" backend/requirements.txt          # → 131:fsrs==6.3.1
backend/.venv/bin/python -c "import importlib.metadata as m; print(m.version('fsrs'))"

# 2 CI 可见性
git ls-files canvas-vault/.claude/scripts/fsrs_bridge.py   # 非空 = TRACKED
git ls-files canvas-vault/.claude/skills | head -1
git ls-files canvas-vault/learning_events.jsonl            # 空 = UNTRACKED（有 skip 守卫）

# 3 版本降级校验
uv python find 3.11 | xargs -I{} {} -m py_compile \
  backend/tests/regression/test_fsrs_golden_vectors.py \
  backend/tests/regression/test_learning_events_schema_contract.py
uv python find 3.12 | xargs -I{} {} -m py_compile \
  backend/tests/regression/test_fsrs_golden_vectors.py \
  backend/tests/regression/test_learning_events_schema_contract.py

# 4 trigger
sed -n '9,31p' .github/workflows/test.yml
```

## 未做的事（如实）

- **未跑 `act`**。理由：`act` 需拉 ubuntu runner 镜像并在容器内重装全量 `requirements.txt`，
  与差异点 #3 的成本问题同源；且它仍无法覆盖 GitHub 托管 runner 的真实 Python 构建。
  改为按上表**逐差异点人工核对**，每条给出可复现的判定命令——覆盖面比 `act` 跑一次更明确。
- 未在远端触发一次真实 CI（本卡硬边界：不 push）。
