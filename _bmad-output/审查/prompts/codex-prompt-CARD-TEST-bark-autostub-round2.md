# 独立对抗审查 round-2 — CARD-TEST-bark-autostub（复核 round-1 整改 + 回归面）

你是独立代码审查员，这是同一张卡的**第二轮**。round-1 你判 FAIL（3 HIGH + 2 MEDIUM + 3 LOW）。本轮任务：逐条复核整改是否真实落地、有没有引入**新的**回归，再给最终裁定。

只读以下文件（绝对路径）：

1. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/scripts/send_bark.py
2. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/conftest.py
3. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/test_daily_review_run.py
4. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/bark_egress_probe.py
5. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/bark_autostub_negative_control.py
6. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/_bmad-output/审查/CARD-TEST-bark-autostub-验收单.md

上下文（零改动）：scripts/daily_review_run.py（:250 调 send；:267-272 osascript 兜底）。

## round-1 发现 → 声称的整改（逐条核）

- **H1** (:232) KEY_FILE→不存在路径使忘打桩的 main() 静默 skip-nokey 返 0，「响亮失败」不成立 → **整改**：KEY_FILE 改指 tmp 下**格式合法且真实存在**的假 key，load_key 成功 → 必然走到 `_urlopen` 拒绝器 → 响亮失败。env BARK_KEY_FILE 同步重定向。
- **H2** (:205) 守卫与测试共用 monkeypatch，测试 undo() 一次拆三层 → **整改**：守卫改用**独立** `pytest.MonkeyPatch()` 实例（fixture 不再取 monkeypatch 形参），finally 里独立 undo。
- **H3** (:229) importlib.reload(send_bark/runnner) 恢复生产值 → **整改**：守卫 patch `importlib.reload`（属性式调用），对 `("send_bark","daily_review_run")` 的 reload 完成后自动重打三层。**如实交代**：整改初版把判断条件错写成测试模块名元组，条件恒假、重打永不触发——本卡新增的 E/E' 篡改门（见下）当场抓住，已改为生产模块名。`from importlib import reload` 预绑定形态拦不住，已声明为如实边界。
- **M1** (negctl :42) B 判据仅子串匹配、可假绿 → **整改**：判据收紧为 rc + pytest 摘要行（恰 `1 failed(, N warnings)`，出现 error 即拒收）+ **整行锚定正则** `^E\s+AssertionError: Bark egress attempted in tests\s*$`；TimeoutExpired 捕获记 FAIL。负控扩为八跑 A/B/C'/C/D/D'/E/E'（C/D/E = 守卫三层各自 + reload 自愈的放行门；C'/D'/E' = --noconftest 篡改门，证明放行门真的依赖守卫）。
- **M2** (:201) endswith 模块门误伤/漏防 → **整改**：按模块名末段**精确枚举**匹配 `_BARK_GUARDED_MODULES = ("test_daily_review_run", "bark_egress_probe")`；「目录内新增文件默认不设防」在 conftest 注释与验收单均声明为边界 + 裁决点。
- **L1** (:205) 零副作用过宽（tmp_path/monkeypatch 形参改变 1028 条测试的 fixture 图）→ **整改**：fixture 只取 `request`；布防模块的 tmp 目录用 `tempfile.mkdtemp` + finally rmtree；非布防模块零 fixture 图变化。验收单措辞收窄。
- **L2** (send_bark:40) 「零行为变化」过宽（import 时冻结别名不观察后续 rebind）→ **整改**：注释如实改为「生产路径绑定同一函数对象」；验收单收窄措辞。
- **L3** (probe:60) 代理清理不重建已缓存 opener → **整改**：注释改「尽力消除 + 双墙兜底」，探针加第二道墙 `socket.create_connection` 拦截器（两墙都记录 host）。
- **L4** (conftest:213) docstring 行号 :134/:136 漂移 → **整改**：已改 :138/:140。

## 本轮审查重点

- R1: 逐条核上表 9 项整改是否真实落地（file:line 证据），有没有「改了措辞没改行为」的假整改。
- R2: 整改引入的**新**回归：独立 MonkeyPatch 的 teardown 顺序/泄漏；importlib.reload 全进程 patch 在布防测试期间的意外后果；假 key（真实存在）相对不存在 key 的新暴露面（例如 reload 自愈失效 + 假 key = 真出网尝试假 key？评估这条链的可达性）；negctl 八跑的子进程面。
- R3: 负控八跑判据还有没有假绿形态（重点：`re.fullmatch(r"1 failed(, \d+ warnings?)?", body)` 的绕过、`"error" not in body` 的绕过、E 门 E' 门的判据）。
- R4: 新的声明-证据差：conftest/probe/negctl 三文件 docstring 与实际行为逐字对照；验收单 v2 的 4-A 表与「未证明什么」「不比什么」是否与代码一致（验收单本轮已重写为 v2）。
- R5: 模块门精确枚举后，有没有新的漏防或误伤形态。

可运行只读验证命令（cd backend 后 `.venv/bin/pytest` / `.venv/bin/python scripts/bark_autostub_negative_control.py`，全部加 `-p no:cacheprovider`；**⛔ 禁止运行 scripts/daily_review_run.py、scripts/daily-review-push.sh 或任何会真实外发的入口**；负控八跑是安全的——探针双墙保证不出网、C/D/E 结构性断言零副作用，可亲自复跑核对）。

## 输出格式

每条发现：`[BLOCKER|HIGH|MEDIUM|LOW] file:line — 一句话缺陷 + 复现思路`。
对 round-1 九项逐条给 `已整改/未整改/部分整改` 判定。
无发现的审查面明确写「R# 无发现」。
末行 `VERDICT: PASS` 或 `VERDICT: FAIL`（存在 BLOCKER/HIGH 即 FAIL）。
