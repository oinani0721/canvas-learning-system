# UAT · CARD-G3-6b-R2（rank_manifest 指纹覆盖 decay_beta 函数体）

> 批次：[BATCH-2026-09-04-第十批 / CARD-G3-6b-R2] · 车道 `card/x5-micro`（从 `1f249b33` 切）
> 改动面：`scripts/daily_review_pick.py` + `scripts/review_rank_manifest.json` + 回归测试 + W6 验收单三处登记
> 提交：本卡单 commit，未 push、未合并。**合并序：必须早于 X2（G6-2b）的最终裁判**

---

## 1. 🎯 一句话目标

补上 W6 卡自己登记的那个洞：**改 `decay_beta.py` 的函数体能让推荐板序翻转，而"系数指纹"纹丝不动**。现在这份文件的整份字节也进指纹了。

## 2. 📖 你的视角

作为每天看复习推送的人，我想相信「排序规则变了，投影里的指纹就会变」这句话，**以便**哪天推荐的板忽然不一样了，我能查出是配置动了还是数据动了——而不是面对一个「一切照旧」的指纹去猜。

## 3. 🖥️ 交互流程（你的屏幕变化）

**无变化（内部指纹更严）。** 今日复习的板序、句子、分钟数一个字都没动；`payload.rank_manifest` 里 `version` 从 `1` 变成 `2`、`sha256` 换了一个值（因为指纹口径变了，不是因为排序变了）。

## 4-A. 🤖 Claude 已代验

### 主判据：先红 / 后绿（B1 / B2）

用独立探针（`scratchpad/b1_probe.py`）在**两个进程**里分别跑 HEAD 版与本卡版的 `daily_review_pick.py`，同一份变异：把 `decay_beta.py` 的 `pick_score` 函数体从 `μ − β·σ` 改成 `μ + β·σ`（**六个常量逐字不动**）。

| 版本 | `build_rank_manifest` 签名 | 原始 decay 的 sha | 改了函数体的 sha | 判据 |
|---|---|---|---|---|
| **HEAD**（v1） | `(decay, version, minutes, recorded)` | `bc3aa142…` | `bc3aa142…` | ❌ **先红成立**：指纹纹丝不动 |
| **本卡**（v2） | `(decay, version, minutes, recorded, decay_path)` | `95210f05…` | `397ada23…` | ✅ **后绿成立** |

探针的两条**自证前置**（缺一门就是空的）：① 两份文件字节确实不同；② 六个常量的定义行**逐字相同**——否则本门就退化成「改常量指纹会变」，而那条旧门 HEAD 起就绿着。

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| B1 | 先红（HEAD 分不出改过函数体的 decay） | ✅ | 上表 HEAD 行，`HEAD_RC=1` |
| B2 | 新键 `decay_beta_sha256`，路径从 **vault 根**显式传参、`Path.read_bytes` | ✅ | `decay_source_path(vault)` → `build_payload` → `build_rank_manifest` → `effective_rank_config`；实现里**零 import、零 `decay.__file__`** |
| B3 | 69 条基线 + 5 条新增全绿 | ✅ **74 passed, 0 failed, 0 skipped** | `PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/regression/test_daily_review_pick.py` |
| B3' | `_fake_decay` 破面已处理 | ✅ | 新 helper `_decay_copy(tmp_path, name, mutate)` 把生产 `decay_beta.py` 复制进 tmp；**8 处** `build_rank_manifest` / **3 处** `effective_rank_config` 调用点逐个显式传路径 |
| B4 | W6 验收单 #9 **保留原文**另加一行 | ✅ | 原文「改函数体可让板序翻转而 sha 纹丝不动」一字未删（grep 计数 1），下方加 `⤷ CARD-G3-6b-R2 追加登记`；#8 / #10 同样加了登记行 |
| B5 | 全程只读 `decay_beta.py` 字节，不 import、不改本体 | ✅ | 禁改门 `git log … -- decay_beta.py sync_board_concepts.py daily_review_run.py` → **空**；`git status` 三文件 → **空**；变异一律在 tmp 副本上做 |
| B6 | `version` 升 2 + 登记旧 sha 快照失效 | ✅ | `review_rank_manifest.json` 新增 `_版本历史` 节，`"2"` 条目点名 `503fd4b6…` 失效并写明升版原因；门 `test_g36b_r2_manifest_version_bumped_and_old_snapshot_registered` 锁住 |
| B7 | #8 runner 门继续不跑 | ✅ 如实 | 见下「本卡未证明什么」第 1 条；runner 侧**实测**只调 `build_payload`（`daily_review_run.py:159-160`，四位置参数形态未变），全仓 grep 确认生产侧无第三处调用方 |
| B8 | live 只读探针 | ✅ | `ok {'version': 2, 'sha256': '95210f05…'}`；`top_boards: ['CS 61B', '特征值与特征向量', 'CS188 lecture 2']` |
| B9 | live vault 零写 | ✅ | 324 个文件的整体 digest 前后**逐字相同**（`795f2e76…`）；`PYTHONDONTWRITEBYTECODE=1` 全程在，未新增 `.pyc` |
| B10 | 不引入新的格式漂移 | ✅ | `ruff check` 全过；`ruff format --diff` 漂移 hunk **HEAD=33 / WORK=33**，且 `+/-` 行里**不含**本卡任何新增标识符（存量漂移，非本卡引入） |

### 5 条新增测试各自锁什么

| 测试 | 锁定的性质 |
|---|---|
| `test_g36b_r2_decay_body_change_moves_sha` | **主门**：改函数体 ⇒ sha 变；且差异**必须落在新键上**（`decay_beta_constants` 与 `implementation_sha256` 两个旧键逐字不变） |
| `test_g36b_r2_decay_path_is_required_no_silent_fallback` | **防新门自身假绿**：不给路径 ⇒ `TypeError`（两个函数都验）。没有默认值可回落，所以"静默兜 None 让指纹恒定"这条路被堵死；并断言 `_fake_decay` 确实没有 `__file__`（本门的前提） |
| `test_g36b_r2_decay_sha_digests_bytes_not_identity` | **单向性**：同字节不同路径 ⇒ 同 sha；只改一行**注释** ⇒ sha 照样变。这条**故意**证伪「sha 变 ⟺ 排序变」；两个 sha 键不得指向同一文件（DD-13 接线检查） |
| `test_g36b_r2_payload_sha_follows_vault_decay_file` | **端到端**：路径确实由 `build_payload` 从 vault 根派生。同时**如实锁住模块缓存边界**——两次 build 的 `top_boards` 完全相同（`import decay_beta` 取缓存），证明本门是字节层不是运行时层 |
| `test_g36b_r2_manifest_version_bumped_and_old_snapshot_registered` | **B6**：version=2、`_版本历史` 两版都在、`503fd4b6…` 被点名失效、登记节不参与计算 |

## 4-B. 👤 你来验

**无变化（内部指纹更严）。** 今日复习推送的内容、板序、句子、分钟数完全一样。

## 5. 🚦 验收结果

- 技术侧（4-A）：**B1-B10 全绿**，74 passed。
- 完成条件 B1-B7：全部满足（B7 是「如实写没跑」，已写）。
- Codex 审查：按卡文「三张微卡默认不送」——**未送审**。

## 6. 📝 批注区

[!question]+ 你的批注写在这里（Cmd+Shift+A）

[!note]+ 为什么 `decay_path` 做成**必填**而不是可选
> 可选参数必然要有一个「没传时怎么办」的分支。那个分支只有两种写法：抛错（那就等于必填）或兜一个常数（那么在所有没传路径的地方，新键恒定 = 新键等于没加，门自己变假绿）。卡文点名的 `_fake_decay` 破面正是这个形状：它是 `SimpleNamespace`，连 `__file__` 都没有。必填让第三种可能（悄悄退化）根本不存在。

[!note]+ 为什么新开一个键而不是并进 `implementation_sha256`
> 两个键指向两个不同的文件（pick.py / decay_beta.py），并进去以后「sha 变了」就再也分不清是哪份变的。测试里有一条专门断言两键不相等。

## 7. 🔗 技术 spec 引用

- 卡文：`goal-cards/第十批-goals/X5.md` § B（完成条件 B1-B7 + 默认裁决）
- 实现：`scripts/daily_review_pick.py`（`decay_source_path` / `_file_sha` / `_decay_sha` / `effective_rank_config` / `build_rank_manifest` / `build_payload` / `load_decay`）
- 配置：`scripts/review_rank_manifest.json`（`version: 2` + `_版本历史`）
- 测试：`backend/tests/regression/test_daily_review_pick.py`（helper `_decay_copy` + 5 条 `test_g36b_r2_*`）
- 上游登记：`_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md` #8 / #9 / #10

---

## 待你裁决（本卡默认值先行，均可改）

| # | 事项 | 本卡采取的默认 | 备选 |
|---|---|---|---|
| ① | 新键还是并键 | 新键 `decay_beta_sha256`（卡文默认裁决） | 并进 `implementation_sha256`（会失去「哪份文件变了」的区分度） |
| ② | 版本号 | 升 2 + `_版本历史` 登记旧快照失效 | 不升版（则归档里两套口径的 sha 混在一起，无法判读） |
| ③ | `recorded` 要不要也登记一份 decay 文件 sha | **不登记**。登记了就得在每次改 `decay_beta.py` 时同步手改 manifest，否则天天刷漂移告警；而 sha 变化本身已经是信号 | 登记（换来「忘了同步会说话」，代价是维护负担） |
| ④ | 归档探针脚本会坏 | 不修。`evidence-g36b-r1/g36b_r1_recheck.py` 等 R1 归档探针按旧 4 参签名写，重跑会 `TypeError` | 一并改签名（但它们是**当时那一轮的证据快照**，改了就不再是快照） |
| ⑤ | #8 runner 门 | **继续不跑**（三前置未满足，卡文默认裁决） | 等 W4① 合入后补跑 |

---

## 本卡未证明什么（必填段，如实）

1. **runner 门一次都没跑**：`test_daily_review_run.py` 会真发 Bark（W4 门未合），本卡按卡文明令不跑。runner 零影响只由「diff 不含 `daily_review_run.py`」+「全仓 grep 确认生产侧无第三处调用方」+「`build_payload` 四位置参数签名未变」三条**静态**证据推出，**不是**由 runner 自身测试回归证明的。
2. **不证明「排序真正用的就是被摘字节的那份文件」**：`load_decay` 走 `import decay_beta`，同一进程内第二次导入取模块缓存。`test_g36b_r2_payload_sha_follows_vault_decay_file` 里两次 build 的 `top_boards` **完全相同**就是这个边界的现场——指纹摘的是「vault 根派生出的那条路径上的字节」，不是「运行时那个模块对象」。生产是单 vault 单进程，两者同一；本卡**没有**为多 vault 同进程加任何一致性检查。
3. **仍不覆盖运行时字节码**：篡改 `__pycache__/*.pyc` 并伪造 mtime 可让排序变而两个 sha 都不变（W6 round-3 已实测复现）。本卡**未评估**该面，与 W6 同口径按威胁模型排除。
4. **不证明「改函数体会改排序」**：本卡全程**不 import** 被改的副本（B5 只读约束），主门断言的只是「文件字节变 ⇒ sha 变」。「板序 `[B板,A板]`→`[A板,B板]` 翻转」这句话来自 W6 R1 轮的实测记录，**本卡没有复跑它**。
5. **单向性没变**：摘全文件 ⇒ 对注释、空行同样敏感（有专门的正例门锁住）。**不可**拿「sha 变了」反推「排序逻辑变了」。
6. **live 只是单时刻只读快照**：2026-09-04 某一刻的 `top_boards` 与 sha 会随节点增删/复习推进而变；验的是「不写盘 + 能算出 v2 指纹」，不是这三块板本身。
7. **没跑目录级 pytest**：只跑了 `tests/regression/test_daily_review_pick.py` 一个文件（卡文禁目录级）。本卡改的是 `scripts/` 下的独立脚本，但**没有**验证 backend 其它测试是否间接依赖 `daily_review_pick`。
8. **`_版本历史` 节是纯文本登记**：有门断言它不参与计算、内容含关键串，但**没有**任何机制强制「以后升版必须写这一节」。

## 移交登记

**台账待登记条目**（本卡按纪律**不动** `未合卡追踪台账.md`）：

1. **CARD-G3-6b-R2 完成，未 push 未合并**，车道 `card/x5-micro`。**合并序硬要求：必须早于 X2（G6-2b）的最终裁判**——X2 若在本卡之前定裁，它验收单里记的 rank sha 会是 v1 口径的值。
2. **W6（CARD-G3-6b）验收单已被本卡追加三处登记**（#8/#9/#10，原文全部保留）。W6 那张卡若还未合并，合并时要连这三行一起带上。
3. **R1 归档探针脚本按旧签名写、重跑会 `TypeError`**：`_bmad-output/审查/evidence-g36b-r1/g36b_r1_recheck.py`（:56/:103/:105/:246/:342/:367/:368）与 `g36b_r1_verify_high_decay.py:62`。本卡**不修**（它们是当时那一轮的证据快照，改了就不再是快照）——见待裁决 ④。
4. **所有 v1 口径下归档的 rank sha 失效**（`503fd4b6…` 等）。已写进 `review_rank_manifest.json` 的 `_版本历史`，但**散落在各验收单正文里的 sha 字面量本卡没有逐一去标注**。
5. **`daily_review_pick.py` 的 `ruff format` 存量漂移 33 处**（HEAD 起就有，非本卡引入）。本卡已确保新增代码零漂移，但这道格式门在本文件上**依然是红的**——独立卡处置。
6. **新发现（本卡提交时实测）：`scripts/` 下的 Python 完全不进 lefthook 的 lint 门**。`python-lint` / `python-typecheck` 两块的 glob 都是 `{backend,src}/**/*.py`，`scripts/daily_review_pick.py` 不匹配——所以上一条那 33 处漂移**根本不是"门红了"，是这道门压根看不见这个文件**。本卡提交时该块只 lint 了 1 个文件（backend 下的测试文件）。这解释了漂移为何能长期存量：不是被绕过，是不在覆盖面内。⚠ 修 glob 会让 `scripts/` 下所有存量漂移一次性变红，属独立卡。
7. **本车道无 `backend/.venv`**：`python-lint` 在裸 PATH 下报 `ruff: command not found` 并 `exit 1`（真红，但原因是工具缺失而非代码有问题——与 A 卡治的 `python-typecheck` 同病灶、不同结局）。本卡提交时把 `card-v5-lance/backend/.venv/bin` 挂上 PATH 供给工具，**未使用 `LEFTHOOK_EXCLUDE` 绕过任何一块**。
