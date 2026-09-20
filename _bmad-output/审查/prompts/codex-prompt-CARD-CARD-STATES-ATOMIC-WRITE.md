# 独立复核：CARD-CARD-STATES-ATOMIC-WRITE（BATCH-2026-09-18-第十五批 / 车道 P4）

## ① 背景与最小读取面（只读这些，不要扩大搜索面）

本卡把 FSRS 投影快照的**唯一写入口** `ReviewService._save_card_states` 从
`Path.write_text → Path.replace`（无 fsync、无 finally、无临时文件清理）改成
「先编码成 bytes → 写 `.json.tmp` → fsync → `os.replace` → 目录 fsync →
finally 清理」，并把 `openspec/specs/concept-identity/spec.md` 的 6 个 Scenario
逐条落成 regression 断言（第 6 条是本卡新增）。

请只读下面这些：

1. 本卡 diff：`git --no-pager diff --no-color 9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680 7a5081f197b364c6eb7d1db99e0382e0d4aa7a4f -- . ':(exclude)_bmad-output'`（恰 3 个文件）
2. `backend/app/services/review_service.py`：`:60-70`（stdlib import 段）、
   `:655-700`（形态分派 helper 段 + 本卡新增的 `_persist_card_states_bytes`）、
   `:916-1040`（`_load_card_states` 与 `_save_card_states` 全貌，含 `:1020`/`:1032`
   两个异常分支）
3. `openspec/specs/concept-identity/spec.md` 改后全文（134 行）
4. `backend/tests/regression/test_g3_7_truth_source.py`：`:74-135`（既有 fixtures，
   其中 `isolate_card_states` 把 `_CARD_STATES_FILE` 重定向到 `tmp_path`）与
   `:685` 到文件末尾（至 `:992`）（本卡新增的整段「concept-identity Scenario 回归门」）
5. 范式对照：`canvas-vault/.claude/scripts/sync_board_concepts.py:582-611`
   （`atomic_write`，本卡实现照抄其结构）
6. 不复用理由对照：`backend/app/utils/atomic_io.py:47-91`
   （`atomic_write_text`：写入阶段异常不清 tmp，同型残留面；本卡**不改它**，
   它不在本车道地盘，已登记建议另立卡）
7. 移交原文：`_bmad-output/验收单/UAT-CARD-U9B-OPENSPEC-2026-09-16.md:188-208`（§六 #3/#4/#6）
8. 裁定书 `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md:149`（T4-C 行）

## ② 作者自述（请独立核对，不要采信）

1. **先编码再开文件**：`data.encode("utf-8")` 发生在任何 `to_thread` 之前，
   所以 lone surrogate 的 `UnicodeEncodeError` 抛出时临时文件根本没被建出来。
2. **零残留**：helper 的 `finally: tmp.unlink(missing_ok=True)` 覆盖 open /
   write / fsync / replace / 目录 fsync 全部失败路径；成功路径上 tmp 已被
   `os.replace` 移走，unlink 是 no-op。
3. **持久顺序**：临时文件的 `os.fsync` 发生在 `os.replace` 之前；`os.replace`
   之后再对父目录 fsync。整段只经**一次** `asyncio.to_thread`。
4. **异常归一口径未变**：`:1020` 的 `except (TypeError, ValueError)`（回滚 pending
   + 记脏）与 `:1032` 的 `except OSError`（保留内存 + 记脏）两个分支一字未动，
   helper 内任何 `OSError`（含目录 fsync 失败）冒到后者 → 返回 `False`。
5. **spec 未越写**：`spec.md` 只改了 Requirement 的临时文件段、Scenario 1/3 各追加
   一条 `AND`、并新增 Scenario 6；原 `:34-57`（异常归一 / 脏标记身份 / 清标记不是
   治愈数据）三段逐字未动（已用整段字符串包含比对自证）。
6. **6 组断言各绑一个 Scenario**：每个 test 的 docstring 第一行写 spec 路径 +
   Scenario 标题原文。S5（跨 vault 脏标记）**刻意不在 vault b 下做成功保存**——
   成功快照会 `clear()` 掉 vault a 的脏标记，那会把两条断言变成恒绿。
7. **负控输入两段，各只拆一层**：拆掉 `finally` 的清理动作 → S6 零残留断言变红；
   拆掉 `os.fsync(fh.fileno())` → S6「fsync 早于 replace」断言变红。两段都以
   `git show HEAD:<path> > <path>` 还原并用 `shasum -a 256` 前后逐字比对。
8. **一处刻意保留**：`_save_card_states` 里紧邻替换段上方的注释
   `# Atomic write: write to temp file then rename` 未改——本卡地盘约束把
   `review_service.py` 的增删行限定在四处（import 段 / 新 helper / docstring /
   替换段），改这行会越界。该注释现在描述不全（未提 fsync 与清理）。

## ③ 请按重要性回答（排序即优先级）

0. 零残留门是否**真的**绑在 `finally` 上？上面那段负控输入是不是唯一能让它变红
   的改法——有没有**门未覆盖的路径**能让临时文件残留而 6 条断言全绿？另外
   `missing_ok=True` 是否吞掉了「unlink 本身失败」这一层真实错误？
1. 目录 fsync 失败被归一成 `False`，意味着「文件其实已经落位却报未持久」。在真实
   介质（本地盘 / 网络盘）上这会不会反复出现？是否该降级为日志而不是失败？
2. 固定的 `.json.tmp` 名在多进程 / 多 worker 下的互踩面有多大？
   `_card_states_lock` 是进程内 `asyncio.Lock`——本仓的进程模型（uvicorn workers 数）
   是否足以让这个假设成立？
3. `open(tmp, "wb")` 取代 `Path.write_text` 之后，newline / encoding 语义是否与旧实现
   **逐字节**等价？请核 `json.dumps(..., ensure_ascii=False, indent=2)` 的输出在两种
   写法下落盘字节有无差异。
4. S1 的 open 探针是否真能抓到旧实现那次 `Path.write_text`（它走 `io.open` 绑定）？
   只包 `builtins.open` 会不会让那条断言绿在一个瞎掉的探针上？本卡加了一条「临时
   文件必须被以写模式打开」的正控锚，它够不够？
5. spec 的 Requirement 改写有没有引入实现里**没有**的承诺？（T4-C 教训：措辞过宽
   即被推翻。）请逐句对照实现。
6. pyright 报 0 errors 是不是靠 `# pyright: ignore` 掩盖的？（自述：本文件 6 处
   ignore 全部是既有的，本卡新增 0 处。）
7. `tests/regression` 目录级 0 新红是否真的在**最终 HEAD** 上跑的？

另外：本卡新增的 8 个 test，有没有哪一条在**对照输入**（把实现换回改前形态）下
仍然是绿的？若有，那条断言没有绑住任何行为。

## ④ 输出格式

逐条列 `BLOCKER / HIGH / MEDIUM / LOW`，每条给 `file:line` + 一句复现思路。
措辞请统一用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
最后给一行总计：`BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## ⑤ 边界

只读，不要写任何文件；不连任何数据库；不评 `next_review` 迁移（那是下一张卡
P4-B）；不评 `backend/app/utils/atomic_io.py` 该怎么修（不在本卡地盘）；不评
`tests/unit` 用例的 `_CARD_STATES_FILE` 隔离问题（属别的车道）；不评
`backend/app/models/**`（本批零写者）。
