# ⑤ 两分支合并准备 — 冲突面与「可合并」结论

> **主干（trunk）**: `worktree-feature-obsidian-hybrid-dev`
> **待合分支**: `card/s3-events` · `card/s6-recap`
> **口径**: merge-base **必须在 feature worktree 里算**（卡文硬约束）
>
> ## ⚠️ 首要更正：主干在本卡作业期间前进过
>
> | 时点 | trunk HEAD | 说明 |
> |---|---|---|
> | 开工勘探（本文 §一~§三 的只读分析基于此） | `2164b498` | 手册所载基线 `cbb20afb` + 批次文档 |
> | 实际合并时 | **`a9c8b97c`** | 新合入 CARD-D3+D4 `daf97064`、CARD-D2a+D2b `66c0591d`，以及主 session 基于本卡 G5-9 发现更新的目标文档 |
>
> **这直接推翻了 §三 的两条结论**（它们对 `2164b498` 为真，对 `a9c8b97c` 不再为真）：
>
> 1. ~~「锁定 blob 三方完全相同」~~ → `learning_event_log.py` 仍为 `28cdaa18` 四方一致，
>    但 **`fsrs_manager.py` 被主干 D3/D4 改动：`980b3758` → `f9edc906`**。
> 2. ~~「主干未动任何 conftest.py」~~ → `2164b498→a9c8b97c` 动了 `backend/tests/unit/conftest.py`。
>
> 抓住这两条的不是勘探、也不是复核，而是**「合并后必须真跑判据」这条硬要求**。
> 若只凭勘探期的只读分析下「可合并」结论，就会把一个已过期的判断当成事实写进验收单。
> §五 的实跑结果才是「可合并」结论的真正依据。
>
> 补充核实：两个新回归文件**不硬编码 blob SHA**（blob 恒定是 Codex round-22 的核验手段，
> 不是测试断言），所以 `fsrs_manager` 换 blob 不会机械地把测试变红；真实风险由 §五 定论。

---

## 一、merge-base（在 feature worktree 内实算）

```
$ git --version
git version 2.50.1 (Apple Git-155)

$ git merge-base card/s3-events worktree-feature-obsidian-hybrid-dev
37387a8662e9dd646fad5628841679d777cb7eae
$ git merge-base card/s6-recap worktree-feature-obsidian-hybrid-dev
37387a8662e9dd646fad5628841679d777cb7eae

$ git log --oneline -1 37387a86
37387a86 ci: fix readme-claims conftest isolation with --noconftest [BATCH-2026-08-27-第四批 / CARD-G1-5]
```

两分支 merge-base 均为 `37387a86`，**与卡文预期一致 ✅**。

### ⛔ 主仓陷阱已复现（证明卡文的警告是真的，不是传闻）

```
$ git merge-base card/s3-events main
671ae7e786deea774c20c734f33215f13c33b02e     # ← 错误基点

$ git diff --name-only main...card/s3-events | wc -l
    1014                                      # ← 伪造出的巨大文件面

$ git diff --name-only worktree-feature-obsidian-hybrid-dev...card/s3-events | wc -l
      75                                      # ← 正确文件面
```

主仓 `main`（`a55db2ab`）与 trunk 是**两条已分岔的血脉**。拿 `main` 当对照会把基点回退到 `671ae7e7`，
文件面从 75 膨胀到 1014——卡文说的"伪造 14 个文件的假冲突"在本次实测中表现为更大的量级。
**结论：合并队列的所有对照命令都必须显式写 `worktree-feature-obsidian-hybrid-dev`，不得用 `main` 或裸 `HEAD`。**

---

## 二、冲突面试算（`git merge-tree`，纯对象库运算，未触任何工作树）

```
$ git merge-tree --write-tree --name-only card/s3-events worktree-feature-obsidian-hybrid-dev
1e51013810c24fc7c44d6f4f60deefe4e76538f1
CURRENT_TASK.md

Auto-merging CURRENT_TASK.md
CONFLICT (content): Merge conflict in CURRENT_TASK.md
                                                        # exit 1

$ git merge-tree --write-tree --name-only card/s6-recap worktree-feature-obsidian-hybrid-dev
b2ece11606880498d47a309e357f5d91f0a29dd9
                                                        # exit 0 —— 零冲突
```

文件面交集（`comm -12` 于两侧自 `37387a86` 起的改动清单）：

| 分支 | 自 base 改动数 | 与主干（150 文件）的交集 |
|---|---:|---|
| `card/s3-events` | 75 | **仅 `CURRENT_TASK.md` 1 个** |
| `card/s6-recap` | 40 | **空集** |

---

## 三、语义兼容（文件面不重叠 ≠ 合并后测试仍绿，故另查）

主干自 `37387a86` 起改了 **39 个 backend 代码文件**（第五批 G2-2/G2-3/G4-2 等合入），
因此必须确认它们与 S3/S6 的判据面是否有语义耦合：

| 检查项 | 方法 | 结果 |
|---|---|---|
| G3-1/G3-4 **锁定 blob** 是否被主干改动 | 三方 `git rev-parse <ref>:<path>` | ⚠️ **此结论已被推翻，见文首「首要更正」**。对 `2164b498` 为真；对实际合并的 `a9c8b97c`，`fsrs_manager.py` 已由 D3/D4 改为 `f9edc906`。`learning_event_log.py` 仍 `28cdaa18` 四方一致 |
| 主干是否动过任何 `conftest.py` | `git diff --name-only 37387a86 trunk -- '*conftest.py'` | ⚠️ **此结论已被推翻，见文首「首要更正」**。对 `2164b498` 为空；`2164b498→a9c8b97c` 动了 `backend/tests/unit/conftest.py` |
| 主干是否动过 `canvas-vault/`（S6 消费面） | `git diff --name-only 37387a86 trunk -- canvas-vault` | ✅ **空** |
| S6 判据的依赖面 | 读 `backend/tests/skills/test_g5_9_recap_exam.py` 的 import | ✅ 只有 `hashlib/json/subprocess/sys/pathlib/pytest` —— 纯 stdlib + pytest，与主干 39 处后端改动**完全绝缘** |
| S3 判据的依赖面 | 读两个回归文件的 import | ⚠️ 经 `tests/conftest.py` 间接 `from app.main import app`，而主干改了 15 个 endpoints ⇒ **存在理论耦合，必须靠合并后真跑判据来定**（见 §五） |

---

## 四、`CURRENT_TASK.md` 冲突的处置口径

**冲突实质**：不是代码冲突，是**设计性 churn 点**。该文件前 15 行是「Clear Context 后的恢复锚点」，
每条车道都会把它整块改写成自己的状态。三方对比：

| 版本 | 「本车道状态」写的是谁 |
|---|---|
| base `37387a86` | 第四批车道 5（`card/n5-split`，G5-1+G5-2） |
| trunk `2164b498` | 第五批车道 S2（`card/s2-neo4j`，G2-3） |
| `card/s3-events` `9014f313` | 第五批车道 S3（G3-1 二十二轮状态） |

**处置**：保留分支侧（ours）的车道状态。理由——该分支尚未合入，它自己的恢复锚点仍是活的工作上下文；
主干侧那段属于已合并完成的 S2 车道，其信息已固化在 git 历史与 S2 验收单里，不会因此丢失。
⛔ **逐处人工解，不使用 `-X ours` / `-X theirs` 批量策略**（本批对 `docker-compose.yml` 的同类警告同源：
批量策略会把未预期的 hunk 一并吞掉）。本次冲突只有 1 个文件、1 个语义块，人工解成本极低。

---

## 五、合并后判据（实跑，这才是「可合并」结论的依据）

### S3 — `card/s3-events` ← trunk `a9c8b97c`，合并提交 `4748bad2`

实际冲突面与 §二 的 `merge-tree` 只读试算**完全一致**：173 个变更文件里只有
`CURRENT_TASK.md` 一处 `UU`，其余全部自动合并。逐处人工解，未用 `-X ours/theirs`。

| 判据 | 合并前 | 合并后 | 判定 |
|---|---:|---:|---|
| 三文件合跑（contract + golden + learning_event_log） | 219 passed + 1 skipped | **219 passed + 1 skipped** | ✅ 零变化 |
| ② 接入 CI 的完整 17 文件清单（按 workflow 同一 env/flags） | 516 passed + 1 skipped | **517 passed + 1 skipped** | ✅ +1 来自主干给清单内某文件新增的用例 |

⇒ **S3 可合并**。主干对 `fsrs_manager.py`（D3/D4）与 `tests/unit/conftest.py` 的改动
未对 S3 判据造成任何回归。

### S6 — `card/s6-recap` ← trunk `a9c8b97c`，合并提交 `c0912962`

⚠️ **冲突面与勘探期不同，如实说明**：勘探期 `merge-tree` 试算 **零冲突**（文件面交集为空集）。
实际合并有 **1 处** `CURRENT_TASK.md` 冲突 —— 原因是**本卡自己**在 ③ 的整改里更新了该文件
（对方复核 B2 点出它仍声明陈旧分支 `card/n5-split`）。即冲突是本卡引入的，不是勘探漏判。

| 判据 | 合并前 | 合并后 | 判定 |
|---|---:|---:|---|
| S6 完整裁判（`test_recap_scan_signals.py` + `test_g5_9_recap_exam.py`） | 160 passed | **160 passed** | ✅ 零变化 |
| 负验证 10 变体 | 10/10 变红 | **10/10 变红**，还原后字节逐字相同 | ✅ |

⇒ **S6 可合并**。主干 39 处后端改动对 S6 判据零影响——`test_g5_9_recap_exam.py`
只 import stdlib + pytest，与后端服务面天然绝缘（这条在勘探期就查实，且合并后仍成立）。

---

## 六、格式门的处置（如实记录，非绕过纪律）

S3 的合并提交被 lefthook `python-lint` 的**格式**子门拦下（`ruff check` 本身 All checks passed）。

核查：暂存的 72 个 py 文件里 38 个 `ruff format --check` 报漂移。
**逐个核对 38/38 与主干 blob 逐字节相同、0 例外**：

```bash
while read f; do
  a=$(git rev-parse ":$f"); b=$(git rev-parse "worktree-feature-obsidian-hybrid-dev:$f")
  [ "$a" = "$b" ] || echo "不同: $f"
done < drift.txt          # → 无输出；相同 38 / 不同 0
```

即漂移**全部是主干既有**，本次合并一个字节都没碰（我手改的只有 `CURRENT_TASK.md`，非 py）。

处置：`LEFTHOOK_EXCLUDE=python-lint` 外科绕过，理由写进提交信息。
**为什么不直接跑 `ruff format`**——那会在一个**合并提交**里塞进 38 个无关文件的重排：
违反最小改动、淹没后续 diff review、并与主干产生无谓分叉。存量格式债的收敛应另立卡。
（该处置与 MEMORY `reference_ruff_format_drift_lefthook` 记录的既定做法一致。）
