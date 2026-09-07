# CARD-RV-G3-7 — Y9-B 审后整改 `08fed737` 逐文件复审定性表

> 批次: `[BATCH-2026-09-07-第十三批 / CARD-RV-G3-7]` · 车道 `card-u9-mastery` · 分支 `card/u9-mastery` · HEAD `da690bf8`
> 复审对象: `ecfcc3f1..08fed737` 补丁（7 文件 +242/−42）+ HEAD 六文件逐字节同态
> 复审口径: Codex r2 存档首部无 SHA（审的是工作区），`git diff <审SHA>` 不可算 ⇒ 用补丁 + HEAD 对照
> 零代码卡: 本文件只作结论登记，不改任何 `.py` / `docs`

---

## 一 绑定核验（完成条件 b）

存档 `evidence-rv-g37/binding-20260908T064520.txt`（末行 `rc=0`）。四条命令全部符合：

| # | 命令 | 期望 | 实测 |
|---|---|---|---|
| 1 | `git cat-file -t` × `0f7ffb0d / ecfcc3f1 / 08fed737 / afaceb06` | 均 commit | 均 `commit` ✅（另核 `7c9a6706` / `31e84281` 亦 commit） |
| 2 | `git merge-base --is-ancestor 08fed737 HEAD; echo $?` | 1 | **1** ✅ —— 如实登记：**非 HEAD 祖先（已 squash 进 `afaceb06`），但对象可达** |
| 3 | `git diff --stat --no-color ecfcc3f1 08fed737 -- . ':(exclude)_bmad-output'` | 7 files +242/−42 | **7 files, 242 insertions(+), 42 deletions(-)** ✅ |
| 4 | `git diff --stat --no-color 08fed737 HEAD -- <7 文件>` | 只剩 `backend/openapi.json` | **1 file changed, 74 insertions(+), 2 deletions(-)**，仅 `backend/openapi.json` ✅ |
| 5 | `git diff --stat --no-color afaceb06 HEAD -- <§〇 六文件>` | 空 | 空、`rc=0` ✅ |

parent 链实测：`08fed737^` = `ecfcc3f1`，`afaceb06^` = `31e84281`，与卡文 §〇 一致。

⇒ **复审读 HEAD 即读 08fed737 终态**（除 openapi.json 由后续 squash 再生）这一前提成立。

---

## 二 逐文件定性（完成条件 c）

定性四选一：**整改成立** / **成立但有残留** / **未整改** / **新引入缺陷**。

### 2.1 `backend/app/services/review_service.py`（+114/−42，改动面最大）

| Codex r2 哪条 | 改了什么（补丁 hunk） | HEAD 行号（`sed -n` 实测） | 定性 |
|---|---|---|---|
| **HIGH**：读取失败放行门锁；成因归给 `_read_frontmatter_fsrs` 的 `except OSError` | 新增独立函数 `_node_lookup_is_blinded()`，用**不吞异常**的 `os.stat` 复核「找不到」；并在 `if path is None:` 分支内调用它 | `_node_lookup_is_blinded` **:169-216**；调用点 **:277-287**（在 `if path is None:` **:276** 内）；`governed=True` + `reason="node_lookup_unreadable"` **:278-279** | **整改成立**（见 §三.1 独立实测） |
| **LOW-4**：新 reason 需在消费侧可见 | `node_lookup_unreadable` 加入两处 reason 映射 | PUT 侧 **:1352-1355**（`in ("node_file_unreadable", "node_lookup_unreadable")`）；GET 侧 **:2592** 同形 | **整改成立** + 我做了完整性 census（见下） |
| **MEDIUM-3 基线对照抓到的唯一一条本卡真新增**（`reportOptionalSubscript`） | 收窄条件从 `if _g37_put_reason is not None:` 改为 `if fm_truth is not None and _g37_put_reason is not None:` | **:1367** | **整改成立**（逻辑等价——`_g37_put_reason` 只在 `if fm_truth and fm_truth["governed"]` 内赋值；改动只让类型检查器看见该不变式，运行时行为不变） |

**我独立做的 reason 映射完整性 census**（防「只修了一半」）：
`node_lookup_unreadable` 的**产生点**只有 2 处（`:275` 防御性 OSError 分支、`:282` 定位被蒙蔽分支）；**消费点**只有 2 处（`:1353-1354` PUT、`:2592` GET），两处均已覆盖。全仓 `git grep` 除测试断言（`test_g3_7_truth_source.py:348 / :394`）外**无第三处**。⇒ **无漏映射**。若漏，新 reason 会落进 `else` 分支被谎报成 `truth_source_unparsable`。

**残留 1（新引入 · LOW · 名实一致 DD-13）**：`_read_frontmatter_fsrs` docstring 的 `reason` 枚举 **:234-235** 仍写
`'no_node_file' / 'node_file_unreadable' / 'no_fsrs_due' / 'malformed_fsrs_due' / None`，
**未加** `08fed737` 自己新增的 `node_lookup_unreadable`。契约文档与实际返回值不符。⇒ 归 U9-B 顺手更正。

**残留 2（新引入 · LOW · 死分支未如实标注）**：`08fed737` 把原来的 `except (OSError, ValueError): return out` **拆成两条**：
- `except ValueError:` **:267-270** → `return out`（放行，与拆分前同）
- `except OSError:` **:271-276** → `governed=True` + `reason="node_lookup_unreadable"`（拦，**新行为**）

实测（§三.1 探针 B）：`_node_md_path` 用 `Path.exists()`，而 `Path.exists()` → `os.path.exists()` → `except (OSError, ValueError): return False` ⇒ **它永不抛**，两条 `except` **均不可达**。
`except OSError` 那条 docstring 已自述「防御性: 现行 `_node_md_path` 用 `Path.exists()` 不会抛到这里 (实测)」= 如实；
但 `except ValueError` 那条注释写的是实质语义（「编码上不可能对应文件名 ⇒ "确实没有"是正确结论」），**读起来像活分支**，未声明不可达。
⚠️ 注意区分：`_node_lookup_is_blinded` 里的 `except ValueError` **:257** 是**活分支**（它直接 `os.stat`，不经 `Path.exists`；lone surrogate 会真触发），两者不可混为一谈。

**观察（非缺陷）**：补丁混入约 7 处**纯格式压行**（`:313` / `:1361-1370` / `:1394` / `:2504` / `:2566` / `:2589` / `:2615`），与整改无关，属 UAT §15 所述「顺手 format 后回退」的残留。
我用**内容口径**（不是行号交集）独立归因：

| 版本 | `review_service.py` | `schemas.py` | `review.py` |
|---|---|---|---|
| `ecfcc3f1` | 702 | 585 | 0 |
| `08fed737` | **608** | 585 | 0 |
| `HEAD` | **608** | 585 | 0 |

（判据：`git show <rev>:<path> \| ruff format --diff --stdin-filename <path> \| wc -l`；`--stdin-filename` 必带，否则 ruff 按默认配置判定。仓库 `line-length = 120`。）
⇒ `review_service.py` 的格式偏差**减少 94 行**，方向朝 ruff，**零新增漂移**；`schemas.py` 零变化；`review.py` 本来就干净。与 Y9-B 自证的 `evidence-g37/format-drift-attribution.txt` 末行「✅ 本卡零新增格式漂移」**独立吻合**。存量 608/585 归 U1/U2 阶段 2。
（流程面：把无关格式改动与承重整改混进同一 commit，违反本仓「禁止一次修复混合多个不相关变更」；仅登记，不构成阻断级。）

### 2.2 `backend/app/api/v1/endpoints/review.py`（+18，纯新增）

改动 = 三处显式传 `None`：ebbinghaus-fallback 分支 **:1158-1165**、`found=False` 分支 **:1440-1442**、异常分支 **:1486-1489**。

**定性：整改成立。** 三处均**行为等价**（pydantic `Field` 默认值本来就是 `None`），收益是把「没判过真相源」这件事在调用点显式化，而不是靠默认值默认掉。`found=False` 那处的注释还如实点出了 `fsrs_manager` 未初始化会在读 frontmatter **之前**早退。

**方法论观察（MEDIUM，不是代码缺陷）**：该 hunk 注释自述「顺带消除 pyright 对 pydantic `Field(None)` 默认值的既有误报，**使本卡的诊断增量为 0**」。
「消掉既有误报」与「新增 0」是**两笔账**：净变化 −3 可以由 `+4 / −7` 得到，也可以由 `0 / −3` 得到，光看净值分不开。Y9-B 用的是基线树多重集对照（见 §三.2），方法本身闭合；但**这句措辞**把两笔账并成一句，后人照抄容易退回「净值好看即通过」。⇒ 建议 U9-B/U1/U2 在引用时拆开写。

### 2.3 `backend/app/models/schemas.py`（+24/−2，纯 docstring）

三处 `Field(description=...)` 补充：
- `FSRSStateQueryResponse.truth_source` **:977-1000**：补 fail-closed 情形（文件/目录读不出来 → 仍返回 `frontmatter`、`due` 为 null、`degraded_reason='truth_source_unreadable'`），并**如实声明** `fsrs_not_initialized` 早退发生在真相源查询**之前**，故「节点可能持有一个本响应没反映的权威 `fsrs_due`」；
- `FSRSStateQueryResponse.degraded_reason` **:1001-1017**：补 `truth_source_unreadable` 释义；
- `RecordReviewResponse.truth_source` **:1054-1075**：补「该端点的 `degraded_reason` 也会携带真相源类原因，且**在 `card_state_persisted` 为 true 时同样出现**——写盘成功不说明真相源被更新」。

**定性：整改成立。** 第三条正面对上了 D0 修订 T4「持久化成功与真相源已更新是两个正交信号，禁止互相冒充」。

**我独立核了那句早退声明**（防「诚实声明掩盖真写侧漏洞」）：`get_fsrs_state` **:2437-2444**
```
if self._fsrs_manager is None:
    logger.warning(...)
    return {"found": False, "reason": "fsrs_not_initialized"}
```
`return` 在 `try:` **:2447** **之前** ⇒ 该路径**不写盘、不推进 `_card_states`**。
⇒ 门锁在这条路径上不生效**无写侧危害**，缺的只是读侧信息（响应不反映真相源）。声明与实际一致。

### 2.4 `backend/tests/regression/test_g3_7_truth_source.py`（+101）

| 改动 | 实测 | 定性 |
|---|---|---|
| `test_get_fsrs_state_frontmatter_wins_on_divergence` 加 `isolate_card_states` fixture + 两条副作用断言（`_card_states` 不变、JSON 未生成） | 签名改动（非新增函数） | **整改成立**——原用例只锁 due 与信号，没锁「读一次有没有副作用」 |
| `test_get_fsrs_state_agreement_is_not_reported_as_divergence` 强制投影 due 带微秒（`microsecond=123456`）+ 前提断言 | 新增 8 行 | **整改成立，且是本次整改里最有价值的一条**——投影 due 若恰为整秒，删掉生产侧的 due 覆盖后该用例**仍会通过**（两边字面相同）。这是判据与被测量同源退化，强制微秒后「返回的是 frontmatter 那一份」才真正承重 |
| 新增 `test_unreadable_node_dir_fails_closed` | 含**正控**（chmod 前 `assert governed is True`）+ 可无视 chmod 时 `pytest.skip` 守卫 | **整改成立** |
| 新增 `test_missing_node_is_still_reported_as_absent` | 正控：可读目录下「真没有」必须仍 `governed=False` | **整改成立**（见下承重性判定） |
| 新增 `test_unencodable_concept_id_is_absent_not_blinded` | 直接调 `_node_lookup_is_blinded` 与 `_read_frontmatter_fsrs` 并断言其返回值 | **整改成立**（见 §三.3） |

**正控承重性判定（Codex prompt 问题①）**：`test_missing_node_is_still_reported_as_absent` 断言「目录可读 + 文件不存在 → `governed=False` / `reason='no_node_file'`」。若把 `_node_lookup_is_blinded` 改成恒 `return True`（即「把确实没有一律判成看不见」这个反向缺陷），该用例**必红** ⇒ **承重**。

**覆盖缺口（非缺陷 · LOW）**：`_node_lookup_is_blinded` 的 `except OSError: return True` 只被 **EACCES** 一态覆盖（chmod 000）。其余会走同一分支的 errno（本机实测 `ELOOP`=62 会抛 `OSError`）**无正控**。方向上 fail-closed 是安全侧（拦而非放行），故不升级；登记为覆盖面事实。
另：本机 macOS 实测**超长文件名**（203 字符 / 603 字节）`os.stat` 抛的是 `FileNotFoundError`（ENOENT）而非 `ENAMETOOLONG`，故走 `continue`（判「确实没有」）= 正确。**但这是 macOS 上的结论**；Linux 容器（ext4，NAME_MAX 255 字节）上同一输入预期给 `ENAMETOOLONG`(36) ⇒ 会走 `except OSError: return True` 而被判「看不见」。中文 concept_id 每字 3 字节，**86 字以上即越界**，在本系统是现实输入面。⚠️ **本卡未在 Linux 上实测，仅登记为待验事实**，不作为缺陷主张。

### 2.5 `backend/openapi.json`（08fed737 内 +8/−0）

08fed737 内的 8 行是 schemas.py docstring 变更的再生结果。`08fed737..HEAD` 该文件 +74/−2 系后续 squash 统一 `--write` 再生所致（`afaceb06` commit message 自述「集成末尾统一 --write 再生」）。**定性：整改成立**（无独立语义）。

### 2.6 `docs/fsrs-truth-source-d0-revision.md`（+15/−4）

| 改动 | 定性 |
|---|---|
| ② 行从「有 frontmatter 真相源（`.md` 存在且 `fsrs_due` 非空）时**一律**不写盘」改为 `governed` 四态口径 + **明写两处未消除**（(a) 无真相源分支仍写盘；(b) TOCTOU 窗口，登记不修） | **整改成立**——正面兑现 Codex r2 MEDIUM-2「整改成立的是承认并登记窗口，不是关闭窗口」 |
| 新增「解析口径要同时对齐两件事」+「可复用的教训：口径 =（正则 + 输入面）」 | **整改成立** |
| 新增「『找不到』与『看不见』必须分开」段 | **整改成立** |
| `:59` 回归门用例数 `12 用例` → `**20 用例**` | **新引入缺陷（LOW）**，见 §四 |

### 2.7 `docs/known-gotchas.md`（+1/−1，单行表格）

G-TRUTH-001 行：③ 补 fail-closed 判据说明；「未修」清单**新增**「门锁判定跨 `await` 存在 TOCTOU 窗口（登记不修）」；用例数 `11 用例` → `**20 用例**`。
**定性：成立但有残留** —— 前两项整改成立；用例数同 §四 的 LOW。

---

## 三 三句自述的独立核对（完成条件 c 指定）

### 3.1 自述①「成因与 Codex 归因不同：`Path.exists()` 不抛异常、自己吞 OSError 返 False ⇒ 实际走 `if path is None`」

**判定：成立。** 依据 = 本卡独立探针 `evidence-rv-g37/probe-path-exists-20260908T064900.txt`（末行 `rc=0`；全部操作在会话 scratchpad 临时目录，不碰项目树与 live vault）。

- **源码实测**（不凭记忆，卡文明令）：本 venv Python **3.14.4**，`inspect.getsource(pathlib.Path.exists)` 显示它转发给 `os.path.exists`；`inspect.getsource(os.path.exists)` = `try: os.stat(path) / except (OSError, ValueError): return False`。⇒ **吞 `OSError` 与 `ValueError` 两族**。
- **行为实测**：预置一个 `chmod 000` 目录并在其中放 `.md`，`euid=501`（非 root）：`Path.exists()` → **False**（不抛）；同一路径 `os.stat` → **PermissionError errno=13 (EACCES)**。
  ⇒ 「确实没有」与「看不见」在 `_node_md_path` 的返回值里确实不可区分，两者都给 `None`；缺陷确实在**定位层**，走的是 `if path is None`。
- **归因差异也成立**：探针 B 直接对 `_node_md_path` 施压四种输入（normal / NUL / lone surrogate / 超长 CJK），**全部返回 `None`，无一抛异常** ⇒ `_read_frontmatter_fsrs` 的 `except OSError` 分支（Codex r2 归因的那条）**确实不被触发**，照该归因改会修错地方。

⇒ 作者在存档里写明「与外审归因不同」并按实测成因整改，**方向正确**；Codex r2 的归因在这一点上不准确。

### 3.2 自述②「pyright 基线 41 → 最终 38，本卡新增 0」

**判定：成立（方法闭合）；但两笔账需拆开引用。**

- 我独立实测最终态（`evidence-rv-g37/pyright-inventory-20260908T065850.txt`，末行 `rc=0`）：`review.py` **14** / `review_service.py` **18** / `mastery_engine.py` **6** / `mastery_store.py` **1**。14+18+6 = **38** ✅ 与「最终 38」吻合（`mastery_store.py` 不在 Y9-B diff 面）。
- **方法是否闭合「改契约让新错落在没动过的行」这一类？** 闭合。`evidence-g37/pyright-baseline-vs-final.txt` 用的是**基线树多重集对照**（`git archive` 基线树 + 诊断多重集比对），而不是行号交集。行号交集对这一类天然失明：改了契约/签名后，新错误会落在**本次没动过的行**上，与 diff 行号交集为空。该文件末行也自陈「Codex r2 MEDIUM-3 指出『行号零交集证明不了零新增』，此法是其整改」。
- **但两笔账必须拆**：41 → 38 的净 −3 = 「消掉 3 条既有 pydantic `Field(None)` 误报」+「新增 0」。**那条 `reportOptionalSubscript` 真缺陷不属于「消掉 3」**——它是 Y9-B 自己引入后又修掉的 4 条之一，在最终态已不存在，故不进最终计数。原「零交集」判据下曾**漏报这 4 条**。⇒ 结论成立，但引用时不得用净值 −3 代替增量判据。

### 3.3 自述③「r2 整改期自伤真回归已修；`test_unencodable_concept_id_is_absent_not_blinded` 锁的是 reader 行为而非间接症状」

**判定：成立。** 该用例体内直接 `from app.services.review_service import _node_lookup_is_blinded, _read_frontmatter_fsrs`，然后断言：
`_node_lookup_is_blinded(cid) is False` / `fm["found"] is False` / `fm["governed"] is False` / `fm["reason"] == "no_node_file"`。
⇒ 锁的是 **reader 的返回值**（直接调被测函数），**不是**「`record_review_result` 没降级成 ebbinghaus-fallback」这类间接症状。间接症状会被上游任何一处改动干扰，reader 断言不会。

裁判 3 实跑该用例**通过**（21 passed 里含它）。

**本卡自己在此栽过一次，如实登记**：我第一轮探针取的是 `\udcff`（low surrogate，落在 surrogateescape 的 U+DC80–U+DCFF 映射区，**能**编回单字节，`os.stat` 给 ENOENT），而被测用例取的是 `\ud800`（high surrogate，**编不出** UTF-8）。**两者行为不同**，用前者去核后者会得出相反结论。判据取值必须与被测断言里的**同一个字面量**对撞。
第二轮改用 `\ud800` 的探针**跑失败**（`UnicodeEncodeError ... position 25`，stdout 为空、无 traceback）；根因两个假说（stdio 编码 / `__pycache__` 写入）**均已证伪**，未继续追。**如实声明：探针 3 无产出。** §3.3 的结论**不依赖它**，而由「探针 2（`_node_md_path` 对含 `\ud800` 的输入返回 `None` 不抛）+ 裁判 3（该用例在真实 fixture 下通过）」两项独立支撑。附带教训：判据脚本自身的源码里直接写 lone surrogate，会让脚本先于被测对象失败。

---

## 四 三口径计数（完成条件 e）

| 口径 | 数值 | 来源（命令实测） | 为什么不同 |
|---|---|---|---|
| 文件实数 | **21** | `grep -cE '^(async )?def test_' backend/tests/regression/test_g3_7_truth_source.py`（HEAD）= 21；`pytest.mark.parametrize` = **0**（无参数化放大） | 当前真值 |
| 两份 docs | **20** | `docs/fsrs-truth-source-d0-revision.md:59`、`docs/known-gotchas.md:139` 均写「**20 用例**」 | **算错 1**，见下 |
| Codex r2 正文 | **18** | `codex-review-CARD-G3-7-r2.md:54`「当前测试源码共有 **18 个测试函数**」 | **准确**——`git show ecfcc3f1:… \| grep -c` = **18**，r2 绑的就是 `ecfcc3f1` |

**逐版实测**：`ecfcc3f1` = **18** → `08fed737` = **21** → `afaceb06` = **21** → `HEAD` = **21**。

**「20」的成因（本卡查清）**：`08fed737` 对测试文件的 `def` 增删为 `+4 / −1`，但那 `−1/+1` 是**同一个函数改签名**（`test_get_fsrs_state_frontmatter_wins_on_divergence` 加 `isolate_card_states` fixture），**净增 3 条**（`test_missing_node_is_still_reported_as_absent` / `test_unencodable_concept_id_is_absent_not_blinded` / `test_unreadable_node_dir_fails_closed`）。18 + 3 = **21**。
两份 docs 的「20」是在**同一个 commit `08fed737`** 里写下的（`git show 08fed737:docs/... \| sed -n '59p'` 即为 `**20 用例**`）⇒ **不是后来漂移，是当场就差 1**。同一 commit 内文档与代码自相矛盾。
⇒ **定性：新引入缺陷（LOW，文档）**。本卡零代码，**不改** docs；修正 20 → 21 归 **U9-B (h)**。

**实跑数（裁判 3，`evidence-rv-g37/g37-gate-20260908T065529.txt`，末行 `rc=0`）**：**21 passed, 0 skipped**，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`。
即 `passed + skipped = 21` ✅。四处 `pytest.skip` **全部未触发**：

| skip 位置 | 触发条件 | 本机是否触发 |
|---|---|---|
| `:118` | FSRS manager 不可用 | 否（manager 可用） |
| `:341` | 当前用户可无视 `chmod 000` 文件 | 否（`euid=501`，非 root，探针同源实测） |
| `:388` | 当前用户可无视目录 `chmod 000` | 否（同上） |
| `:660` | 当前用户可无视 `chmod 000` 文件 | 否（同上） |

⚠️ 交接提示：以 root 身份跑（如某些容器）时这三处会 skip，`passed` 降为 18 而 `passed+skipped` 仍为 21 —— **判据必须写 `passed+skipped`，不能只写 passed**。

---

## 五 两处 TOCTOU 按协议 §1 阻断级五问定级（完成条件 d）

> 协议出处：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md` §1
> 五问 = 数据丢失 / live vault 或 Neo4j 7691 写入 / 安全 / 指定裁判红 / 负控假绿（窄口径：负控本身谎报 PASS）
> ⛔ 以下结论由本卡自己走完五问推出，**不照抄** `decision.md` 的自述。

### 5.1 共同事实基础：写入落点到底碰不碰真相源

我通读 `_save_card_states` **:565-630** 全函数体，逐句核其写面：

- 唯一文件写目标是 `_CARD_STATES_FILE` **:117**（= `backend/data/fsrs_card_states.json`，在 **:110** 被显式标注「非 FSRS 调度真相源 —— 本文件是投影/缓存」）；
- 写法：`mkdir(parents=True, exist_ok=True)` → 写 `.json.tmp` → `replace` 原子换名（**:600-604**）；
- 内存 mutation 在 `async with _card_states_lock` **:597** 内（**:598**）；
- 失败路径两分支：`(TypeError, ValueError)` **:611-621** 回滚 pending 并进 `_unpersisted_concepts`；`OSError` **:622-629** 保留内存 + 标脏；
- **全函数体内没有任何 frontmatter / vault 路径 / Neo4j 驱动的引用**。

⇒ **两处 TOCTOU 的写入对象都是一张默认 FSRS 卡，落点都是已显式降格的投影缓存；节点 `.md` 的 `fsrs_due`（唯一真相源）一个字节不动。**
旁证：`grep -nE 'fsrs_bridge|decay_beta'` 在 U9 面五文件上**全部命中注释**，无 import / 无调用；`mastery_engine.py` / `mastery_store.py` 零引用。

### 5.2 TOCTOU (a) —— 门锁判定跨 `await`

代码位置（HEAD 实测，与卡文 §〇 逐条对上）：注释块 **:2458-2464**（末句「彻底闭合归 G3-5 键化卡」）；`fm_truth = _read_frontmatter_fsrs(concept_id)` **:2465**；`has_truth_source = bool(fm_truth["governed"])` **:2466**；`card_data = await self.load_card_state(concept_id)` **:2473**；`gate_blocked = False` **:2475**；`if has_truth_source:` **:2493** → `gate_blocked = True` **:2498**；`else:` **:2506** → `persisted = await self._save_card_states(...)` **:2507**。

| 五问 | 答案 | 依据 |
|---|---|---|
| **数据丢失？** | **否** | 见 §5.1：写入对象 = 一张默认卡；落点 = `_card_states` + 投影 JSON；真相源 frontmatter 不动。且被写的 concept 在窗口内本就无投影卡（走的是 `if not card_data:` **:2477** 分支），**不覆盖任何既有数据** |
| **live vault / Neo4j 7691 写入？** | **否** | §5.1 写面证明；三条裁判（2/3/4）均输出 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` |
| **安全？** | **否** | 无凭据、无权限判定、无外发面；仅本地 JSON 投影缓存 |
| **指定裁判红？** | **否** | 裁判 3 = **21 passed / 0 skipped / rc=0** |
| **负控假绿？**（窄口径：负控本身谎报 PASS） | **否** | `test_g3_7` 的正控一对仍能区分「门锁生效」与「普遍写不动」：`test_missing_node_is_still_reported_as_absent`（真没有 → 必须放行）与 `test_unreadable_node_dir_fails_closed` 里 chmod **前**的 `assert _read_frontmatter_fsrs(cid)["governed"] is True`（可读时必须拦）。把 `_node_lookup_is_blinded` 改成恒 True 或恒 False，各有一条会红 |

**⇒ 阻断级 = 0。归属：U9-C（`:2464` 已指派 G3-5 键化卡）。**

**「后果有界」论证——我独立走完下游（Codex prompt 问题③）**：
设窗口内发生：t0 读 frontmatter 无 `fsrs_due` → 放行；t1 vault 写出 `fsrs_due`；t2 默认卡落进 `_card_states` + JSON。
**下一次 GET**：`card_data = self._card_states.get(concept_id)` **:2469** 命中 → `if not card_data:` 不成立 → 走 `else:` **:2570** 分支 → `auto_created = False` **:2577**、`persisted = concept_id not in self._unpersisted_concepts` **:2579**，**该分支不调用 `_save_card_states`** ⇒ **不重复写盘**；随后 `if has_truth_source:` **:2582** 为真 → `result["truth_source"] = "frontmatter"`、`due` 以 frontmatter 为准、两侧不一致时 `degraded_reason` 追加 `truth_source_divergence`。
⇒ **「下一次 GET 就会正确拦截并报分歧」成立。**

**但措辞需收紧（交 U9-C）**：那张被写进去的默认卡**留在** `_card_states` 与 `fsrs_card_states.json` 里，没有任何路径会删除它。「不会**静默**固化」重心在「静默」，是成立的；若被读成「不会固化」则**不成立**。
另核 `_unpersisted_concepts`：它只在**写失败**时被 `add`（**:618 / :626**）、在**写成功**时整体 `clear`（**:606**）。TOCTOU 场景下写是**成功**的，故不会进该集合，也不会因此固化成「永久未持久化」。⇒ Codex prompt 问题③ 中「`_unpersisted_concepts` 与 dirty 标记会不会让它固化」的答案是**不会**（固化的是卡本身，不是脏标记）。

### 5.3 TOCTOU (b) —— 无真相源分支仍写盘

代码位置：`else:` **:2506** → `persisted = await self._save_card_states(pending=(concept_id, card_data))` **:2507**。
文档登记：`docs/fsrs-truth-source-d0-revision.md:66` ②「(a) 无真相源分支仍写盘（HTTP safe-method 违规被收窄未根治）」；`:83`「T5 未完全落实」；`decision.md:69`。

| 五问 | 答案 | 依据 |
|---|---|---|
| **数据丢失？** | **否** | 同 §5.1。且此分支的前提是 `governed=False`（无 `.md`，或 `.md` 可读但无 `fsrs_due` = 新卡语义）—— 此时**真相源本就没有话可说**，写投影不覆盖任何权威值 |
| **live vault / Neo4j 7691 写入？** | **否** | 同 §5.2 |
| **安全？** | **否** | HTTP safe-method 语义违规是**契约/语义**问题（GET 产生副作用），不是安全边界；无越权、无外发 |
| **指定裁判红？** | **否** | 裁判 3 = 21 passed；裁判 4（API 面）= **14 passed** |
| **负控假绿？** | **否** | `test_node_without_fsrs_due_is_treated_as_no_truth_source` 锁的正是这一态必须放行；若改成一律拦，它会红 |

**⇒ 阻断级 = 0。归属：退役卡（`decision.md:69`；`docs/…d0-revision.md:83` 亦记「根治归退役卡」）。**

**如实登记的边界**：本卡只做**定级**，**未闭合**任一窗口，也未证明这两处在高并发真实负载下的发生率。

---

## 六 证据 rc 缺失登记（完成条件 f）

存档 `evidence-rv-g37/g37-evidence-rc-audit-20260908T065823.txt`（末行 `rc=0`）。

| 项 | 实测 | 台账/卡文 |
|---|---|---|
| `evidence-g37/` 文件总数 | **29**（27 `.txt` + `decision.md` + `pyright.json`） | 台账 Y9-B 行写「**30** 份证据」⇒ **更正为 29** |
| 末行含**有效** `rc=<数字>` | **0** | 与卡文一致 |
| 末行是**空值** `rc=` | **2**：`g37-test-red-20260906T133240.txt` / `six-suites-BEFORE.txt` | 与卡文一致（zsh 下 `${PIPESTATUS[0]}` 取空，手册 §零.6 同款） |

**效力判定（协议 §2.2）**：`.txt` 末行为 pytest 汇总行 / sha / 文本的那 25 份，**只能作「这条命令跑过」的旁证**，不能作「通过」的依据 —— 缺 `rc` 就无法区分「命令成功」与「命令中途失败但仍产出了看似正常的尾部」（`tee` 吞退出码是本仓已登记的反复陷阱）。两份**空值 `rc=`** 更弱：它看起来像有 rc，实际什么也没说，**禁止**按有效 rc 计。

**本卡自证**：本卡落进 `evidence-rv-g37/` 的每一份**裁判**存档末行都带 `rc=$pipestatus[1]`，唯一例外是按设计无 rc 的 `data-before.txt` / `data-after.txt`（(i) 的 `ls backend/data` 快照）。验伪锚见验收单。

---

## 七 pyright 存量声明核对（完成条件 g，只读）

存档 `evidence-rv-g37/pyright-inventory-20260908T065850.txt`（末行 `rc=0`；`pyright` 自身有错时 rc=1 属预期，此处 rc 记的是管道首命令）。

| 文件 | 本卡实测 | UAT §14.3（`:50` 前口径） | UAT §4-A A14 / §15 r2-3（改口后） | 台账 #7 |
|---|---|---|---|---|
| `app/api/v1/endpoints/review.py` | **14** | 17 | — | — |
| `app/services/review_service.py` | **18**（+2 warnings） | 18 | — | — |
| `app/services/mastery_engine.py` | **6** | 6 | — | — |
| `app/services/mastery_store.py` | **1** | 不在 Y9-B diff 面 | — | — |
| **三文件合计** | **38** | 41（= 17+18+6） | 基线 **41** → 最终 **38**，本卡新增 **0** | 「LEFTHOOK 待裁 D 项」 |

⇒ 三处口径**可对上**：UAT §14.3 的 41 是**基线**（`review.py` 当时 17），最终态 38（`review.py` 降到 14，即「消掉 3 条既有 pydantic `Field(None)` 误报」）。本卡实测最终态 = **38** ✅。

**结论**：全部为**存量**，归 **U1（services 三文件）/ U2（`review.py`）阶段 2**（用户 D-16 甲）。
本批 U9-B / U9-C 改这些文件时，按协议 §2.3：带存档跳过 hook + **基线树多重集对照 = 0 新增**（⛔ 不得用行号交集——它对「改契约让新错落在没动过的行」失明），**禁顺手修存量**。
本条是交接事实，**不是本卡动作**；本卡未改任何 `.py`。

---

## 八 本卡另行实测、与卡文不符或需更正的事实

1. **裁判 8（OpenAPI drift）与卡文预期不符 —— 主干既有红，非本卡引入。**
   卡文期望 `DRIFT: none`；实测 **`DRIFT: found (paths: +0 -0, schemas: +0 -0, diff lines: 1)`，rc=1**。
   漂移内容：`/api/v1/review/overview/board-done` 的 `post.description` 里，快照写 `learning_events.jsonl 不追加`，live 代码写 `learning_events 账本不追加`。
   **来源已定位**：`d209622d`「第十二批集成修复 — Y2-B 注释字面量撞写点普查门」改了 `backend/app/api/v1/endpoints/review_overview.py` 的 docstring（为让字面量不撞写点普查门），**未重新生成 `openapi.json` 快照**。
   与 G3-7 面（`fsrs-state` / `review/record`）**零交集**；本卡零代码、工作区与 HEAD 一致（`git status --porcelain -- backend/ docs/ …` 空）⇒ 三类归因中属**主干既有**。
   本卡**不修**（零代码卡禁改 `openapi.json`，且 `--write` 会改快照）。⇒ 交主 session / 相关车道。
   （附带模式：为躲开门 A 改了措辞，结果打红门 B —— 与本仓已登记的「依据被自己后一步消灭」同族。）

2. **`mastery_engine.py:288-290` docstring 的「5 处在线读方」行号：部分过期。**
   逐条实测：
   - `mastery_tools.py:187-190` ✅ 准确（真实路径 `backend/app/mcp/tools/mastery_tools.py`，docstring 未写目录前缀）
   - `mastery_tools.py:274-277` ✅ 准确
   - `signal_registry.py:148` ✅ 准确（`if concept.fsrs_card_data or concept.last_interaction_ts:`）
   - `event_handlers.py:102-103` / `:332-333` ✅ 准确（读 `fsrs_stability` / `fsrs_difficulty`）
   - `mastery_engine.py:326` ❌ 是**写点**（`concept.fsrs_card_data = self.fsrs_manager.serialize_card(card)`），不是读方
   - `mastery_engine.py:651` ❌ 是**空行**
   本文件内 `fsrs_card_data` 的真实读方：**`:298` / `:299` / `:342` / `:352` / `:667` / `:669`**（`:310` 是注释，`:326` 是写点）。
   ⚠️ 卡文 (j) 写「读方实际在 `:342/:349/:352/:667/:669`」—— 实测 **`:349`** 是 `stability = max(concept.fsrs_stability, 1.0)`，**不含 `fsrs_card_data`**；应为 `:298/:299`。⇒ 归 U9-B (e) 一并更正。

3. **`save_card_state` 裁定 ④ 的事实基础成立。**
   `git grep -n 'save_card_state(' -- backend/app` 只命中 **`:2364`**（`async def`）与 **`:2398`**（注释引文），无调用方 ✅。
   函数体 `:2364-2405`（`return persisted` 在 **:2405**，`:2406` 空行，`:2407` `def get_cached_card_states`）；内部 `_save_card_states` 在 **:2403**；隔离注释 **:2397-2402**（**:2396** 是另一条 `# CARD-D3 Codex HIGH-2` 注释，不属该引文）。
   ⚠️ 名字相近的 **`load_card_state`（`:2337`，体止 `:2362`）有真调用方 `:2473`** —— 退役面必须逐字区分，别连坐。
   本卡只核事实基础，**退役处置归 U9-B**。

4. **交 U9-C 的实测（勘探稿 §7 风险栏据此作废）**：`GET /review/fsrs-state/{concept_id}` **端点早已有 vault 维度** ——
   `@review_router.get(` **:1382** / 路径 **:1383** / `vault_id: Optional[str] = Query(default=None, min_length=1, …)` **:1395-1399** / `_resolve_vault_group_id(vault_id, subject_id=subject_id, legacy_group_id=group_id)` **:1424**（其末行 `set_current_subject_id(derived)` 在 `:60`）/ 随后 `result = await review_service.get_fsrs_state(concept_id)` **:1430** —— **ContextVar 注入了，但 service 侧没人读**。
   ⇒ G3-5 键化可在 service 侧读 `app.core.vault_scope.current_vault_id()`（`vault_scope.py:294`）完成，**HTTP 契约与 `openapi.json` 不必变**。
   同时交 U9-C：真相源 reader 的 base 是**进程级**（`frontmatter_signals.py:35` `canvas_base = getattr(settings, "CANVAS_BASE_PATH", None) or "/vaults/canvas-vault"`；`_node_md_path` `:33`，`p.exists()` `:38`，`:36` 是 `for prefix in _NODE_DIR_PREFIXES:`）⇒「vault 由目录天然隔离」**只在一进程一 vault 时成立**。
   ⚠️ 另注：`_node_lookup_is_blinded` **:194** 把同一段 base 解析与默认值字面量 `"/vaults/canvas-vault"` **复制了一份**（docstring 自陈「默认值字面量在此重复一次是已知代价」）。当前两处一致，但这是一个会随 `frontmatter_signals` 改动而静默漂移的面 —— 键化卡若改 base 解析，**必须同改两处**。

5. **卡文 §〇 其余 file:line 全部实测一致**，无第二处偏差：`codex-review-CARD-G3-7-r2.md` 首部 `:1-13` 与 `:28-34` 与 `:54`；`d0-revision.md:66` / `:83`；`schemas.py:938/:977/:989/:1001/:1009/:1018/:1054/:1070/:1076`；`review.py:1125-1134/:1469-1474`；`decision.md:32/:63-65/:68-71`；UAT 章节 `§12 :141 / §13 :164 / §14 :179 / §15 :234`；grep 计数 3 / 1 / 6（锚点 `110 524 549 570 1306 2401`）。
   `tests/unit` 红基线（feature 树绝对路径）去 `#` 行 = **202** ✅；与 U9 面同名的红只有 `test_mastery_fusion.py::TestPearsonCorrelation::test_no_correlation`（U11-C 面，本卡不动）。

---

## 九 本卡未证明什么（表内部分，验收单 §12 为准）

- 未闭合任一 TOCTOU，只做定级；未证明两窗口在真实并发负载下的发生率。
- 未证明 mastery 侧（裁定 ③ 隔离）无害 —— 只核注释与读方行号，未跑该域行为。
- 未证明仓外 / 运行时动态拼出的 URL / 未纳入本仓的客户端为零消费方（`decision.md:32` 同款边界）。
- 未复跑 Y9-B 的承重性变异 M1 / M2（UAT §11）—— 不在本卡读取面。
- 未跑 `tests/unit` 目录级（见验收单：U10-A 车道 `/tmp` 负控窗口通告期内，目录级会出环境噪音 ERROR；该项本就是卡文 (h) 的**可选**项、非完成条件）。
- 未在 Linux 上实测 `ENAMETOOLONG` 路径（§2.4 覆盖缺口那条只在本机 macOS 实测）。
- 未证明 `Path.exists()` 在**所有** Python 版本吞 OSError —— 只核了本 venv 的 **3.14.4**。
- 探针 3（`\ud800` 对撞）**无产出**，其目标结论改由探针 2 + 裁判 3 支撑。

---

## 十 Codex 复核后的更正（2026-09-08，本节为审后追加）

> 存档：`_bmad-output/审查/codex-review-CARD-RV-G3-7.md`（`gpt-6-astra` / `ultra` / `codex-cli 0.153.3`），结论 **PARTIAL，BLOCKER = 0、HIGH = 0**（4 MEDIUM + 4 LOW）。
> ⚠️ **§一～§九 原文一字未改**，更正全部集中在本节——否则 Codex 存档里引用的行号会失效、复核链断掉。
> **本卡零代码**，以下更正只改本文档与验收单；代码/文档修复一律移交。

### 10.1 行号更正表（Codex LOW-3 与其余我自查出的）

**根因（如实登记）**：我在多处按 `sed -n 'A,Bp'` 输出的**相对位置推算**行号，没有逐个 `grep -n` 实测。本仓已登记过「行号必须实测不能推算」这条教训，本卡**又犯了一次**。以下全部为 `grep -n` / `awk NR` 实测值。

| # | §几 原文写的 | **实测正确值** | 谁抓到 |
|---|---|---|---|
| 1 | 文首「Codex r2 存档**首部无 SHA**（审的是工作区）」 | **首部有 SHA** —— `codex-review-CARD-G3-7-r2.md:4` = `审查绑定: \`ecfcc3f1\`（正文首行自证；审后 08fed737 整改 5 条未复审）`。准确表述应是：**首部有绑定 SHA（主 session 补记，标注不计配额）；正文 `:10` 亦自证 `ecfcc3f1`；但正文自陈「工作树另有未跟踪文件，所以『工作树干净』并不完全属实」** —— 所以「审的是工作树」成立，「首部无 SHA」不成立。该说法我照搬卡文而未独立核，虽然 §〇 核验时已读到 `:4` 原文却没发现矛盾 | Codex |
| 2 | §2.1「调用点 `:277-287`」「`if path is None:` **:276**」 | `if path is None:` = **`:277`**；`_node_lookup_is_blinded(...)` 调用 = **`:279`**；`governed/reason` 赋值 = **`:280-281`** | 自查 |
| 3 | §2.1 残留 2「`_node_lookup_is_blinded` 里的 `except ValueError` **:257**」 | **`:200`**（`:257` 根本不在该函数体内；helper 体是 `:169-214`） | Codex |
| 4 | §5.1「锁 `:597`」 | **`:595`**（`prev` `:597`、mutation `:598`） | Codex |
| 5 | §5.1「`mkdir`→写→`replace` `:600-604`」 | **`:600` / `:604` / `:605`** | 自查 |
| 6 | §5.1「失败分支 `:611-621` / `:622-629`」 | **`:612-623`**（`TypeError, ValueError`）/ **`:624-630`**（`OSError`） | 自查 |
| 7 | §5.1 / §5.2「`clear()` **:606**」「`add` **:618 / :626**」 | **`clear()` :610**；**`add` :621 / :628** | Codex |
| 8 | §5.2「`if not card_data:` **:2477**」 | **`:2476`**（另有第一处 `:2471`） | 自查 |
| 9 | §5.2「缓存命中 `else:` **:2570**、`auto_created=False` **:2577**、`persisted=` **:2579**」 | **`:2513` / `:2520` / `:2522`**（`async with _card_states_lock` = `:2521`） | Codex |
| 10 | §2.3「早退 `:2437-2444`」「`try:` **:2447**」 | 早退 **`:2439-2446`**（`if` `:2439`，`return` `:2446`）；`try:` **`:2448`** | 自查 |
| 11 | §2.2「`found=False` 分支 `:1440-1442`」 | 新增的三个 `None` 在 **`:1443-1445`**（`:1442` 是既有的 `reason=`） | 自查 |

**未受影响的锚点**（复核后仍准确）：`_node_lookup_is_blinded :169`、`_read_frontmatter_fsrs :217`、其 `except ValueError :267` / `except OSError :271`、`reason` 产生点 `:275 / :282`、`_save_card_states :565`、`_CARD_STATES_FILE :117`、`非 FSRS 调度真相源` 六锚点、门锁区 `:2458-2464 / :2465 / :2466 / :2473 / :2475 / :2493 / :2498 / :2506-2507`、`if has_truth_source :2582`、`result["truth_source"] :2583`、`save_card_state :2364 / :2398 / :2403 / :2405`、`load_card_state :2337 / :2473`、schemas 与 review.py 的其余引用。

### 10.2 定级修订（逐条采信）

| Codex 条目 | 我原来的判定 | **修订后** | 处置 |
|---|---|---|---|
| **MEDIUM-1** `ENAMETOOLONG` 误锁（`:210`） | §2.4「覆盖缺口 · LOW · 仅登记为待验事实」 | **条件性 MEDIUM** —— 在返回该 errno 的文件系统上这是**功能缺陷**（同一输入会被门锁持续拦截），不只是覆盖缺口。**边界照旧**：本机 macOS 实测给 `ENOENT`（走 continue = 正确），Linux 路径**双方均未实测**，不得把预期当实测 | 移交 U9-C（键化卡同面）；建议按 errno 白名单收窄 fail-closed 分支 |
| **MEDIUM-2** helper 已 `stat` 到文件却仍返回「没有文件」（`:213` → reader `:283`） | **我完全漏了** | **采信，MEDIUM** —— `_node_lookup_is_blinded` 的 `else: return False`（`:212-213`，注释「竟然 stat 到了 (定位后被创建), 不算被蒙蔽」）之后，reader 在 `:283` `return out`，带着初始化的 `found=False / governed=False / reason='no_node_file'` —— **已经看见那个文件了，却不去读它**。若该文件含 `fsrs_due`，门锁会放行并推进投影。这是**定位层内部的 TOCTOU**，外部写者即可触发，**不需要跨 `await`**。Codex 同时指出旧逻辑也有相近窗口，故不判全新 HIGH | 移交 U9-C，并入 TOCTOU (a) 的闭合范围 |
| **MEDIUM-3** 「不覆盖任何既有数据」不足以支撑零阻断 | §5.2 第一问依据含「不覆盖任何既有数据」 | **撤回该半句。** 缓存 miss（`:2469` / `:2471` / `:2476`）是**锁外**观察，写锁在 `_save_card_states` 内部（`:595`）才取；等锁期间同 concept 的另一写者可先写入，本次取锁后仍无条件写默认卡 ⇒ **「检查时不存在」不等于「写入时不存在」**。<br>**第一问答案修订为**：真相源 frontmatter 未被改动（**成立**，写面证明见 §5.1）；投影缓存内的并发覆盖**未排除**（**未证**）。<br>**阻断级仍为 0** —— 协议 §1「数据丢失」指真相源 / live vault / Neo4j 侧的数据，投影缓存内的竞态是正确性问题；Codex 亦明言「不能据此升级为已证实的 BLOCKER」 | 移交 U9-C |
| **MEDIUM-4** pyright / 格式「零新增」证明未闭合 | §3.2「成立（方法闭合）」；§2.1「零新增格式漂移」 | **降为 PARTIAL。** ①「基线树多重集」**方法方向成立**，但 `evidence-g37/pyright-baseline-vs-final.txt` 只有结果与方法摘要，**没有两侧诊断集合、归一化过程、同环境命令与最终树绑定**；本卡 inventory 只有**文件级计数**，无法重算增量。② 同签名旧错消失 + 新位置出现仍可能相互抵消。③ **格式 `702→608` 只证明净减少，不证明零新增** —— 这与我在 §3.2 自己批评过的「净值不能代替增量判据」是同一个错，我在格式面上犯了它。<br>④ Codex 的一致性批评成立：**不能一边拒绝无 rc 的旧证据承担「通过」，一边用同类汇总认证本项闭合** | 移交 U1 / U2 阶段 2：补两侧诊断集合存档后才可称闭合 |
| **LOW-1** r2 LOW-4 字段说明仍有残留 | §2.3「整改成立」 | **改判「成立但有残留」。** `schemas.py:1076-1081` 的 `RecordReviewResponse.degraded_reason` 描述仍写 `"Set when card_state_persisted=false: 'card_state_write_failed' or 'empty_concept_id_not_persisted'"` —— **错误限定**（它也在 `persisted=true` 时携带真相源类原因）且**只列两个原因**。`:1067-1071` 在**另一个字段**（`truth_source`）里补了反例，**消除不了本字段自身的错误限定** | 移交 U9-B |
| **LOW-2** 「下一次 GET 必然报分歧」过宽 | §5.2「下一次 GET 就会正确拦截并报分歧」 | **收窄为**：在 `fsrs_manager` 可用、节点仍存在且读取解析成功的前提下，外层 `due` 采用 frontmatter；**只有两侧确实不一致才报 `truth_source_divergence`**（一致时本就不该报警——`test_get_fsrs_state_agreement_is_not_reported_as_divergence` 正是锁这个）。行号更正见 10.1 #9 | 已在本节收窄 |
| **LOW-3** 三处锚点/解释有误 | — | **全采信**：①②见 10.1 #1、#3；③ §5.2 第五问引的是 **reader 正控**（只证明分类正确），**真正的写盘正控**是 `test_gate_allows_write_when_no_truth_source`（`test_g3_7_truth_source.py:252-266`）——它断言无真相源时 auto-create **必须照常写内存 + 落盘 + `persisted is True`**，其 docstring 自陈「没有这条，上一条的『跑前跑后没变』可能只是因为这条路径本来就写不动，判据会恒真」。**第五问的正控引用以它为准** | 已更正 |
| **LOW-4** `except ValueError` 判「新引入 LOW」依据不足 | §2.1 残留 2「新引入缺陷 · LOW」 | **降为「观察」。** 防御性捕获及其既有放行语义**本身没有因此出错**，仅是注释未注明「当前不可达」。同节的 `reason` 枚举漏 `node_lookup_unreadable`（`:234-235`）**维持 LOW**（那是契约文档与实际返回值不符） | 枚举 LOW 仍移交 U9-B；不可达注释降为观察 |

**驳回：无。** Codex 8 条全部采信（MEDIUM-1 / MEDIUM-3 为「采信论证、调整表述或保留边界」，非驳回）。

### 10.3 Codex 单列的「已核实成立」（可承重的部分）

1. **r2 五条整改逐项裁定**：HIGH（权限失败路径）整改成立；MEDIUM-2 文档整改成立、窗口仍在；MEDIUM-3 条件收窄与显式 `None` 成立（零新增证明未闭合）；LOW-4 信息已补但本字段仍有残留；LOW-5 计数漂移**未全部闭合**（20 仍错）。
2. **作者对 r2 成因归属的纠正成立** —— Codex 独立复核了 Python 3.14.4 的 `Path.exists()` → `os.path.exists()` → `except (OSError, ValueError)` 链路，确认目录权限失败实际走 `path is None`，只改外层 `except OSError` 不够。**与本卡探针结论一致（第二源独立复核）**。
3. **两个重点测试确实承重**：helper 恒 `True` 会打红 `test_g3_7_truth_source.py:441`；恒 `False` 会打红 `:393`。强制非零微秒的补强也成立。**但不能证明所有 errno 与并发时序正确。**
4. **未发现外层 `except ValueError` 导致合法 concept_id 永久放行**（Codex prompt 问题②的答案 = 否）。
5. **缓存与 dirty 链路的核心判断成立**：缓存命中不再次保存；成功保存在 `:610` 清空 `_unpersisted_concepts`；磁盘失败保留内存并标脏。**卡本身会留下** ⇒ 区分「不会固化」与「不会**静默**固化」**必要**。
6. **18 / 20 / 21 版本归因成立**（`18 → 21 → 21 → 21`，无参数化放大，改签名不算新增；两份 docs 在 `08fed737` 当场写成 20 = 同提交引入的 LOW 文档错误）。
7. **rc 核数与 OpenAPI 来源归因成立**。Codex 建议表述收紧为「不能**单独**承担整条命令通过的正式证明」（日志内容仍有旁证价值），并提醒「有 rc 也不自动证明绑定和增量正确」——**采纳**。

### 10.4 本节新增的移交项（并入 §十 后的交接清单）

| 项 | 定级 | 归属 |
|---|---|---|
| `ENAMETOOLONG` 条件性误锁（`review_service.py:210`） | 条件性 MEDIUM（Linux 面未实测） | U9-C |
| helper 内部 TOCTOU：`stat` 成功却返回 `no_node_file`（`:212-213` → `:283`） | MEDIUM | U9-C（并入 TOCTOU (a) 闭合面） |
| 锁外 miss 判定导致的投影并发覆盖未排除（`:2469/:2471/:2476` vs 锁 `:595`） | 论证收窄，阻断级仍 0 | U9-C |
| pyright / 格式「零新增」缺两侧诊断集合存档 | PARTIAL | U1 / U2 阶段 2 |
| `schemas.py:1076-1081` `degraded_reason` 描述错误限定 | LOW | U9-B |
| `review_service.py:234-235` reason 枚举漏 `node_lookup_unreadable` | LOW | U9-B |
| 两份 docs 用例数 20 → 21 | LOW | U9-B |
