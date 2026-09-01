# 复核请求：一个本地笔记工具的「先记日志、后改文件」一致性实现

你是独立代码复核者。请复核一个**单机离线学习笔记工具**的一致性实现，并按末尾格式给出结论。

## 背景（三句话）

用户在 Obsidian 里给自己的笔记做自测评分。评分结果要写两处：一份追加式的 JSON Lines 日志（`learning_events.jsonl`），和笔记文件头部的 YAML 字段（记录下次复习时间等）。实现采用「先把事件追加进日志、再改笔记」的顺序，这样程序中途退出时，下次运行可以从日志把没做完的那一步补上。

**要复核的问题只有一个**：在「程序中途退出 / 用户重跑同一次评分 / 日志文件被别的程序写坏」这三种情况下，会不会**漏算一次评分**，或者**把同一次评分算两遍**。

这是个人学习工具，没有网络接口、没有多用户、不处理任何凭据。

## 请读这些文件

```
WT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger
```

1. `WT/canvas-vault/.claude/skills/quiz-answer/SKILL.md` — 主实现。它是一份 Markdown 说明文档，其中**恰有一个** `python3 - <<'PYEOF' … PYEOF` 代码块包含 `P = "/tmp/quiz-answer-payload.json"`，那个块就是被复核的程序。
2. `WT/canvas-vault/.claude/scripts/fsrs_bridge.py` — 间隔重复算法的调用封装。
3. `WT/docs/learning-events-schema-v1.md` 的 §6.1–§6.3 — **规格说明，判定对错以它为准**。
4. `WT/backend/tests/regression/test_g3_2_review_ledger.py` — 现有 36 个行为测试。
5. `WT/backend/app/services/learning_event_log.py` — 另一个日志追加入口（本次改动**没动**它；请判断是否该动）。

（其余文档不必读。）

## 请怎么验

规格里的判定点已经落成测试，但**测试通过不等于实现正确**——请自己构造输入验证。最省事的方式：把上面第 1 项里的那个代码块原样抽出来（`re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", text, re.DOTALL)` 后按 `P = "/tmp/quiz-answer-payload.json"` 筛），把其中的 `P` 常量重定向到你自己的临时目录，然后在临时目录里搭一个最小笔记库跑它：

```
<tmpdir>/repo/canvas-vault/节点/测试节点.md          # 笔记，YAML 头 + 正文
<tmpdir>/repo/canvas-vault/.canvas-config.yaml       # 只需一行 vault_id: "xxx"
<tmpdir>/repo/canvas-vault/.claude/scripts/          # symlink 到 WT 的同名文件
<tmpdir>/repo/backend/scripts/validate_learning_events.py   # symlink
<tmpdir>/repo/backend/.venv                          # 目录级 symlink 到 WT/backend/.venv
```

`WT/backend/scripts/g32b_r1r7_counterexamples.py` 里有现成的搭建函数（`new_vault` / `run` / `write_rows`），可以 import 复用，改掉它的 `CE_ROOT` 指向你自己的目录即可。

跑测试时请这样设环境变量，避免配置校验失败刷屏：

```bash
env PYTHONDONTWRITEBYTECODE=1 INTERNAL_API_KEY=review-placeholder NEO4J_ENABLED=false \
    TMPDIR=<你的可写目录> .venv/bin/pytest <目标> -q -p no:cacheprovider --tb=short
```

不要设 `DEBUG=true`。**不要**运行 `WT/backend/scripts/g32b_mutation_gates.py`（它会临时改被复核的文件）。

## 本次改动做了什么

这一轮修了 13 个问题。为免先入为主，只列改后的规则，请你判断它们是否**正确且完整**：

1. 日志行与本次评分是否「同一件事」，比较的是一个固定 8 键的信封（`event_version` / `event_type` / `node_id` / `effective_at` / `payload` 的 8 个键），candidate 侧**独立构造**，不从日志行复制任何键。两个记录环境快照的键（`fsrs_library_version` / `fsrs_params_hash`）明确排除在比较之外，它们的完整性交给校验器。
2. 日志行里的时刻必须是 canonical 整秒 UTC（复用校验器本体的正则 `_WHOLE_SECOND_RE`，再叠加 UTC 偏移为 0），不合规就停下报错，**不做归一化**。
3. 「这是第几次评分」的序数从日志边界回推，不取笔记文件的当前值。
4. 正常写入和崩溃恢复两条路径的产物必须逐字节相同（业务时刻统一取日志行里的 `review_time`）。
5. 日志行里的 rating 必须等于 `rating_from_grade(grade_norm, abandoned)`，不等就在应用前停下。
6. 上述第 1、2 条的裁决已回写规格 §6.2。
7. 判断「日志最后一行是被腰斩的半行」的依据是：**最后一个非空行**后面有没有换行符（不是文件末尾有没有）。
8. 标了 `payload.out_of_order` 的行，其 `review_time` 必须不晚于水位线；该键只接受布尔 `true`。
9. 日志文件按二进制读再显式 decode；非 UTF-8 字节报错停下。
10. 一行 JSON 里出现重复键就停下（`json.loads` 默认取最后一个，歧义无法证明）。
11. 同时存在多个「已入日志但未应用」的事件时停下报错（正常路径下不可能出现）。
12. 六种状态（日志有无该事件 × 笔记是否已记录 × 时刻是否已过水位线）逐一有测试覆盖。
13. 校验器负责拦下写入端管不着的行（`node_id` 缺失/写错、`schema_ext` 非法）。

## 请重点判断

1. 第 1 条的 8 键信封，有没有**两侧文本相等但语义不同**的日志行形态？（数值类型、字符串与数字、Unicode 归一化、`effective_at` 与 `payload.review_time` 不一致等。）
2. 第 2、8 条只作用于「本笔记 + `schema_ext == "review/1"` + 未标 `out_of_order`」的行。这个范围划得对吗？划窄了会漏，划宽了会让一条坏数据卡死整个笔记库。
3. 第 3 条的序数回推：同一时刻的两个事件、笔记里没有计数字段、合法乱序行夹在中间、旧格式行夹在中间——这些组合算得对吗？会不会把**合法的重跑**误判成冲突（那会让用户重跑旧评分时报错）？
4. 第 4 条的逐字节相同，换别的参数还成立吗？（不同的上次复习时间、不同的时刻推进幅度、算法降级路径。）
5. 第 5 条会不会误伤**旧版本已经合法写入**的日志行，让它们永远无法被恢复？
6. 第 7、9、10 条的边界：`\r\n` 结尾、末行是空白行、只有一行且是坏行、重复键出现在顶层而非 payload、非 UTF-8 字节出现在首行。
7. 第 12 条的六种状态，每个测试构造出来的前置条件真是它声称的那一种吗？（尤其那个删除笔记里校准记录的辅助函数，有没有顺手改到别的判定依据？）
8. 第 5 项文件（`learning_event_log.py`）这次没改，对吗？

## 输出格式

中文，严格按这个结构：

```
结论：<通过 | 需整改>

### 13 条规则逐条判断
| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |

### 六种状态
（逐个给 PASS/FAIL 与依据）

### 问题清单
[BLOCKER|HIGH|MEDIUM|LOW] <file:line> — <一句话>
依据: <最小复现步骤与你实际观测到的退出码/文件内容>
建议: <具体怎么改>

### 测试复核
（`pytest` 实跑结果；自报数字是 266 collected / 265 passed / 1 skipped，不符请点名）

### 验证限制
（沙箱可写性、没跑的东西、无法证明的东西）

VERDICT: <通过 | 需整改>
```

判定一律以 `docs/learning-events-schema-v1.md` §6.1–§6.3 为准；实现与规格不一致时，请指出该改哪一侧。

**不要**把「没有实现并发锁」当作问题——这个工具设计上就是单进程串行运行，加锁是另一张卡的范围，规格里已写明。但如果你发现**单进程串行的前提下**仍然会漏算或重复计算一次评分，那就是 BLOCKER。
