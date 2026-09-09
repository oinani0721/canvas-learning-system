# UAT — CARD-RED-A2（3 条真负控从「红在配置层」改为「撞到鉴权层 Branch 1」）

> 批次：`[BATCH-2026-09-07-第十三批 / CARD-RED-A2]` · 车道 `card-u10-red-a`（U10 **末卡**）
> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U10-E.md`
> 代码 commit（**5 个**）：`fe3787ce` 初版 → `0b9be419` Codex r1 整改 → `88a15609` r2 整改 → `cc74b130` r3 整改 → `87f75b19` r4 整改（**最终 HEAD**）
> 起点：U10-D 末 commit `052a9289`

---

## 1. 🎯 一句话目标

有三条测试专门守着「上线时忘了填内部密钥，系统必须拒绝请求」这条规矩，但它们一直是坏的 —— 而且坏的原因不是那道门没关，是这三条测试压根没走到门口就摔了。这张卡让它们真正走到门口，并且能认出自己撞的是哪扇门。

---

## 2. 📖 你的视角

作为这套系统的使用者，我想要「密钥没填就一律拒绝」这条保护真的被测试守着，以便将来有人不小心改坏了这道防线时，测试会立刻喊出来，而不是继续绿着骗我。

---

## 3. 🖥️ 交互流程

```
我把「内部密钥」一栏清空并保存
        ↓
我再去做一件需要密钥的事（同步 / 改模型设置 / 测试模型连通）
        ↓
系统明确拒绝我，并告诉我「内部密钥没配置」
        ↓
我看到的是一句能看懂的说明，不是一个报错页
```

---

## 4-A. 🤖 Claude 已代验（技术断言全在这段）

| # | 断言 | 结果 | 证据 |
|---|---|---|---|
| A1 | 三条目标 nodeid 从红名单消失 | ✅ | `FINAL-GATES-r5-*.txt` / `red-diff-final5-B-*.txt` / `unit-final5-*.txt`，逐条 `grep -c` 各 = 1 |
| A2 | 目录级：开工 120 failed → 收工 117 failed，29 errors 不变 | ✅ | `unit-open-*.txt` / `unit-final5-*.txt` 汇总行 + 末行 `rc=1` |
| A3 | nodeid diff（vs **本卡开工快照**）只有 3 条 `<`、**无任何 `>` 行** | ✅ | `red-diff-final5-B-*.txt`，`grep '^>'` 无输出 |
| A4 | nodeid diff（vs 202 基线）同样**无 `>` 行**（`<` 56 条 = 前四卡 53 + 本卡 3） | ✅ | `red-diff-final5-A-*.txt` + `open-baseline-attribution-*.txt` |
| A5 | **配置层直证**：直接实例化 `Settings(DEBUG=False, INTERNAL_API_KEY='')` 必抛，正文含 `INTERNAL_API_KEY required outside local dev` | ✅ rc=1 | `settings-raise-*.txt` |
| A6 | **归因第二证据**：开工时 bug_tracker 记录的 `error_type` 为 `ValidationError` ×3（不是 HTTPException） | ✅ | `two-open-*.txt` |
| A7 | 两文件级：开工 3 failed（`assert 500 == 503` ×3）→ 收工 **17 passed / 0 failed** | ✅ | `two-open-*.txt` / `two-r5fix-*.txt` |
| A8 | 同族 12 条逐条 PASSED（含 `:158` / `:122` / `:128` / `:137` 与 system 侧 8 条） | ✅ | `two-after-*.txt` 逐条 `grep -c` 全 = 1 |
| A9 | **负控 L1**（override 换 Branch 2 档）⇒ 3 条红在 detail 精确等值上 | ✅ | `negctl-L1-layer-red-*.txt` |
| A10 | **负控 L2**（`funcName` 换 WebSocket 侧函数名）⇒ 3 条红在日志判据上 | ✅ | `negctl-L2-funcname-red-*.txt` |
| A11 | **负控 L3**（完整标记换成不存在 token）⇒ 3 条红在日志判据上（不恒真） | ✅ | `negctl-L3-token-red-*.txt` |
| A12 | **负控 L4**（移除 detail 等值 + 换 Branch 2 档）⇒ 日志判据**独立**变红 | ✅ | `negctl-L4-caplog-solo-red-*.txt` |
| A13 | **负控 L5**（实例化改法退回原样）⇒ 3 条回到 `assert 500 == 503` | ✅ | `negctl-L5-revert-red-*.txt` |
| A14 | 五段负控每段均记录变异前 sha / 还原后 sha / `git diff --quiet` rc=0 | ✅ | `negctl-suite-*.txt` |
| A15 | 地盘门：`git diff --name-only 052a9289 HEAD -- . ':(exclude)_bmad-output'` **只含两个测试文件** | ✅ rc=0 | `FINAL-GATES-r5-*.txt` |
| A16 | `git diff --stat -- backend/app` 为空；`config.py` / `security.py` / `main.py` 逐一为空 | ✅ rc=0 | 同上 |
| A17 | 其余禁改面（conftest / support / system.py / lefthook / pyrightconfig / .claude/agents）为空 | ✅ rc=0 | 同上 |
| A18 | 判据存在性：`auth_fail_closed` 逐文件 sync=**1** / system=**2** / 合计 **3** | ✅ | `FINAL-GATES-r5-*.txt` |
| A19 | detail 精确等值断言 sync=1 / system=2；原 `status_code == 503` 断言保留（2 / 4 处，未删未弱化） | ✅ | 同上 |
| A20 | 无 skip / xfail（两文件各 0） | ✅ | 同上 |
| A21 | 裸 `in caplog.text` 判据残留 = 0（r1 整改后全改为 `caplog.records` 结构化判据） | ✅ | `FINAL-GATES-r5-*.txt` |
| A22 | ruff check + format 全绿 | ✅ rc=0 / 0 | `FINAL-GATES-r5-*.txt` |
| A23 | W4 真连门：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` | ✅ | `two-after-*.txt`（Codex r5 独立实跑亦确认为 0） |
| A24 | Codex **五轮**：r1 (B0/H0, 1 MEDIUM+4 LOW) → r2 (B0/H0/M0, 2 LOW) → r3 (B0/H0/M0, 1 LOW) → r4 (B0/H0/M0, 3 LOW) → **r5 (B0/H0/M0, 1 LOW 且标注「本卡引入 = 0」)，绑最终 HEAD `87f75b19`** | 见 §7 | `codex-review-CARD-RED-A2-r*.md` |

### 4-A 附：修法与「为什么这不算放宽校验」

选 **方案 A（`Settings.model_construct`）**，只作用于 `debug=False and key==""` 这一档，其余档位仍走原 `Settings(**fields)`。

- **为什么不算放宽 `validate_security_defaults`**：生产代码一字未改（A16 佐证）。该校验拦的是**进程启动装配**；本卡改的是「测试如何造出『运维忘了配 key』的那个非法配置对象」。三条测试要验的规则（生产档空 key 必须被拒）一条没动，反而第一次真正跑到了执行它的那段代码。
- **为什么选 A 不选 B（先建合法再改属性）**：卡文 (c) 担心选 B 会隐性依赖真 `.env`（`config.py:288-292` 对空 `NEO4J_PASSWORD` 另有一条 raise）。`model_construct` 不走 `BaseSettings` 的取值链，该档不读 `.env`，确定性更高。⚠️ 这个取舍的**理由在 Codex r2 后已收窄**，见 §8 未证明项 ②。
- **自检**：`model_construct` 后紧跟四条断言（`DEBUG is False` / `INTERNAL_API_KEY == ""` / `CORS_ORIGINS` / `NEO4J_PASSWORD`），确认关键字段没被跳成别的值。

---

## 4-B. 👤 你来验（3 分钟，全程在设置界面里完成）

- [ ] 我打开设置，把「内部密钥」那一栏清空并保存 → 我看到它保存成功，没有弹出看不懂的东西 → 我感觉这一步很平常。
- [ ] 我接着去做一件需要这个密钥的事（比如让它同步一次，或者去改一下模型设置）→ 我看到它**明确拒绝**了我，并且写着「内部密钥没有配置」 → 我感觉这道门是真的关着的，而不是嘴上说关着（**安心**）。
- [ ] 我读那句拒绝的话 → 我看到的是一句**人能看懂的说明**，告诉我问题出在密钥没配，而不是一个红色报错页或者一串看不懂的字 → 我感觉它在帮我，而不是在甩锅（**被照顾到**）。
- [ ] 我把密钥填回去再保存，然后重做刚才那件事 → 我看到它正常做完了 → 我感觉这道门该开的时候会开，不会一直挡着我（**顺畅**）。
- [ ] 我回想整个过程 → 我看到「没填密钥」和「填了但填错」这两种情况给我的提示是不一样的 → 我感觉它分得清我到底哪里做错了（**被理解**）。

---

## 5. 🚦 验收结果

- 全部勾上 → 回一句「CARD-RED-A2 通过」。
- 有勾不上的 → 在 §6 用 `Cmd+Shift+A` 写 `[!error]+`，说清「我做了什么 / 我看到什么 / 我期待看到什么」。

---

## 6. 📝 批注区

> [!question]+ 你的提问
>

> [!error]+ 你发现的问题
>

---

## 7. 🔗 技术 spec 引用（给 Claude 读）

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U10-E.md`
- 改动文件：`backend/tests/unit/test_sync_batch_auth.py`、`backend/tests/unit/test_system_endpoint_auth.py`
- 相关生产代码（**本卡零改动**）：`backend/app/config.py::validate_security_defaults`、`backend/app/security.py::require_internal_api_key`、`backend/app/main.py::CORSExceptionMiddleware`
- 裁判存档：`_bmad-output/审查/evidence-red-a2/`
- Codex 存档：`_bmad-output/审查/codex-review-CARD-RED-A2-r{1,2,3,4,5}.md`；prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-RED-A2{,-r2,-r3,-r4,-r5}.md`

### Codex 轮次与绑定 SHA

| 轮 | 绑定 | 结论 | 处置 |
|---|---|---|---|
| r1 | `052a9289..fe3787ce` | B0 / H0 / 1 MEDIUM / 4 LOW | MEDIUM-1 与 LOW-3 独立复核后**成立**；LOW-3 改代码（`0b9be419`），其余登记 |
| r2 | `052a9289..0b9be419` | B0 / H0 / **M0** / 2 LOW | LOW-2 改代码注释（`88a15609`）；LOW-1 登记并更正取舍理由 |
| r3 | `052a9289..88a15609` | B0 / H0 / **M0** / 1 LOW | LOW-1 改代码注释（`cc74b130`） |
| r4 | `052a9289..cc74b130` | B0 / H0 / **M0** / 3 LOW | LOW-1 + LOW-3（均本卡自引入的失实表述）改注释（`87f75b19`）；LOW-2 属基线既有债，登记移交（见 §9⑬） |
| r5 | `052a9289..87f75b19` | B0 / H0 / **M0** / 1 LOW（**标注「基线既有」，本卡引入 = 0**） | 无需整改；LOW-1 的 4 处位置并入台账⑬ |

> **D-15 停轮达成**：末轮 `r5` 绑最终 HEAD `87f75b19`，`git diff --stat 87f75b19 HEAD -- . ':(exclude)_bmad-output'` **为空**（rc=0），BLOCKER = 0 / HIGH = 0，且 r5 明确判定「**本卡引入为 0**」。轮次 5 / 上限 5。
> `r4` 其实已在绑最终 HEAD 时达成 B0/H0；因其 LOW-1、LOW-3 是本卡自己写进注释的失实表述（与本批「把推断当事实必须改正」同口径），仍做了一轮整改并按「审后再改代码必再送一轮」补送 `r5`。

模型 `gpt-6-astra` · reasoning_effort `ultra` · codex-cli `0.153.3`（`codex --version` 实测）。五份存档均已补协议 §2.1 六行首部（模型 / reasoning_effort / codex 版本 / 绑定 SHA / 会话头自证三行，字段齐备性已跑门）。

---

## 8. 本卡未证明什么（如实登记）

1. **未证明 Branch 1 在真实生产进程里「完全不可达」，也未证明它「可达」是常态** —— 卡文 §〇 与本卡初版论证都写过「Branch 1 是死分支 / 在任何经 pydantic 校验的 Settings 上不可达」，**这条已被推翻**。Codex r1 给出反例并经本方独立复现：`INTERNAL_API_KEY="   "`（空白字符）能通过 `config.py:295` 的真假值检查，而 `security.py:91` 先 `.strip()`，于是命中 Branch 1。正确表述是：**对精确空串 `""` 不可达**（校验先拒，且 `config.py:966` 在模块导入期就 `settings = get_settings()`），**对空白字符 key 可达**。本卡三条测的是「非法配置一旦抵达鉴权依赖，最后一道防线仍拒绝请求」，**不是**「漏配 key 的部署能起来并返回 503」。
2. **未证明「不采用 `model_copy`」的原始理由成立** —— 本方原理由「合法基底必然合并 `.env`」被 Codex r2 反证：`Settings(_env_file=None, ...)` 可禁用 `.env`。保留 `model_construct` 现在只是**一个取舍**（两条路径都不是正常启动路径），不是必然。另需区分：**禁 `.env` ≠ 禁进程环境变量**，后者需另行控制，本卡未处理。
3. **未证明 `model_construct` 建出的对象在其余字段上等同真实生产配置** —— 只自检了 4 个字段。Codex r1 独立遍历 77 字段确认「与同参数 `DEBUG=True` 的合法 Settings 相比只有 `DEBUG` 不同」，但该对象同时带 `NEO4J_ENABLED=True` + 空 `NEO4J_PASSWORD`，**违反 `config.py:288` 的另一条生产不变量**；也没有保留真实环境对其他字段的覆盖值。
4. **未证明 `NEO4J_PASSWORD == ""` 能佐证「该档不读 `.env`」** —— 反例：`.env` 不设该键、只设别的键时它同样为 `""`。结论（不读 `.env`）成立，但依据是 `model_construct` 的调用链，不是这条单字段断言。代码注释已于 `88a15609` 更正。
5. **未证明 `funcName` 条件是独立不可省的** —— `L2-funcname` 只证明「改错期望函数名会红」。由于带括号的完整标记已排除 WebSocket 侧，`funcName` 属**防御深度**而非必要条件。
6. **⛔ 未证明判据能锁住「那个分支条件被求值为真」** —— 本卡判据锁的是「那条日志记录 + 那个响应出现了」。Codex r2 给出控制流反例：把 `security.py:96` 的 `if` 删除、令 logger 与 `raise` 无条件执行，目标三条**仍会全绿**（同文件其余 11 条 403/200 用例会捕获该变异）。这是负控的覆盖边界。该反例为源码推导 + Codex 的内存实验，**本方未实际运行该生产变异**（本卡零 `backend/app` 写面）。
7. **未证明日志判据不会因日志重构而假红** —— 若将来把 `logger.error` 抽取进 helper，`funcName` 会变；显式 `stacklevel` 也能改变归因，故函数名不是不可伪造的代码身份。
8. **未证明 `caplog.clear()` 能排除清空后其他线程新增的日志** —— 当前单请求、禁 lifespan 场景未发现混入路径，但这是场景结论不是不变量。
9. **未证明本卡的绿完全不依赖真 `backend/.env`** —— 卡文 (k)⑤ 的担忧对**选 B** 成立；选 A 后该档不读 `.env`，但**其余档位**（`debug=True` / 已配 key）仍走真 `Settings(...)` 会合并 `.env`。本批禁改 `.env`、禁另起树，故**未在一棵没配 `.env` 的树上实跑验证过**。
10. **未证明 WebSocket 侧同型分支的行为**（`security.py:184-259`，其 Branch 2 仍 dev 放行）—— 本卡只在判据上把它排除掉，没有测它。
11. **未证明 `CORSExceptionMiddleware` 把 `ValidationError` 兜成 500 这一行为本身是否合理** —— 登记，不改。
12. **未跑 `tests/integration` / `tests/e2e`**。
13. **⚠️ 卡文 (b)① 的「开工 diff 为空」与实际不符** —— 本卡 HEAD 在 U10-A~D 四卡之后，开工 diff（vs 202 基线）有 **53 条 `<`**（前四卡的净修复，逐文件与车道 `git diff --name-only` 名单完全对上），`>` 为 0。卡文那句只在 U10-A 开工时成立。本卡因此把承重口径改绑「收工 vs **本卡开工快照**」，该口径下恰 3 条 `<`、0 条 `>`；同时保留 202 基线口径作双重对照（同样 0 条 `>`）。
14. **未重跑 `tests/unit` 全量做「Codex 独立复现」** —— Codex 各轮的目录级数字均来自对本方存档的重算，非其独立执行。

---

## 9. 台账待登记条目

1. **`security.py` Branch 1 的可达性结论更正** —— 旧说法「在经校验的 Settings 上不可达 / 死分支」**作废**。新口径：对精确空串不可达（`config.py:966` 模块导入期即装配），对空白字符 key 可达（`config.py:295` 查真假值 vs `security.py:91` 先 `.strip()`）。两层防御各有价值，**没有依据删除 Branch 1 或放宽 `validate_security_defaults`**（Codex r1 与本方独立复现一致）。
2. **既有 `"not configured" in detail.lower()` 断言分辨不了 Branch 1/2** —— 且比卡文所述更强：**Branch 2 的 detail 以 Branch 1 的整句为前缀**（实测 `startswith` = True），故 `test_sync_batch_auth.py` 那条 Branch 2 用例里既有的 `"Internal API key not configured" in detail` 同样两层都命中。本卡对三条目标用例改用精确等值 + 结构化日志判据；**其余用例的宽判据未动**（非本卡地盘），移交登记。
3. **嫌疑 commit 更正**：`f718d040`（2026-05-08，Round-23 Story 7.1 Patch 1 引入 `validate_security_defaults`），非 `c9bb6c9a`。
4. **(c) 选了方案 A（`model_construct`）** —— 理由与「为什么不算放宽校验」见 §4-A 附；取舍理由的收窄见 §8 ②。
5. **五段负控存档与还原 sha**：`evidence-red-a2/negctl-suite-<TS>.txt`（L1-layer / L2-funcname / L3-token / L4-caplog-solo / L5-revert），每段变异前 sha、还原后 sha、`git diff --quiet` rc=0 均在档。
6. **Codex 轮次与绑定 SHA**：见 §7 表。模型 `gpt-6-astra` + `ultra`，codex-cli `0.153.3`。
7. **测试对真 `.env` 的隐性依赖**（移交第十四批 RED-ENVDEP 候选卡）—— `_settings_factory` 不传 `NEO4J_PASSWORD`，`debug=True` 等其余档位仍走真 `Settings(...)` 会合并 `.env`。本卡只让 `debug=False + key=""` 那一档脱离 `.env`。另附 Codex 补充：**禁 `.env` ≠ 禁进程环境变量**，收口时两者都要算。
8. **地盘归属待补登手册** —— `test_sync_batch_auth.py` / `test_system_endpoint_auth.py` 归 U10-E 独占目前只是**车道内约定**（U10-C / U10-D / 本卡三份卡文互认），手册 §一 未列（`grep` = 0 命中）。请主 session 在手册 §一 地盘互斥段补一行。
9. **§〇 同族用例指位更正**：初稿的 `test_system_endpoint_auth.py:150` 不是 `def` 行（它是 `:139` 那条用例体内的 override 行），已按 def 行枚举 `:115/:124/:129/:139/:163/:172/:177/:188`。
10. **⛔ 判据覆盖边界（新增，源自 Codex r2）** —— 本卡判据锁「日志记录 + 响应出现」，锁不住「`security.py:96` 的分支条件被求值为真」。删掉该 `if` 令 logger 与 `raise` 无条件执行，目标三条仍全绿（其余 11 条 403/200 用例会捕获）。**这是本类判据的通用边界，建议写进工程坑索引**。
11. **⛔ 日志判据不得用裸 token 子串（新增）** —— `security.py` 的 WebSocket 侧标记以 `ws_` 打头因而**包含**鉴权侧的裸 token，两者同 logger 同 ERROR 级别。裸 `in caplog.text` 会被误判成命中。本卡改为遍历 `caplog.records` + 限定 `name` / `levelno` / `funcName` / 带括号的完整标记。**建议写进工程坑索引**。
12. **开工基线口径说明** —— 见 §8 ⑬。合并期核对本卡时，请用「vs 本卡开工快照」口径认净增量；202 基线口径下本卡收工的 `<` 应为 56 条（前四卡 53 + 本卡 3）。
13. **⛔ 两个测试文件头部的 fail-closed 矩阵已失实（基线既有债，本卡未改）** —— `test_sync_batch_auth.py` 文件头矩阵与 `TestDevelopmentConvenience` 的介绍性文字、`test_system_endpoint_auth.py` 文件头矩阵，都仍写着 `DEBUG=True + 空 key → 200 (dev convenience / dev bypass)`。实际行为在 P0-2 加固后是：`security.py` 要求**显式 bypass 且 loopback**，否则 **503**；两文件里三条 dev 档用例本身也断言 503。**这些位置都不在本卡改动面内**（`git diff 052a9289 HEAD` 对该处计数 = 0），按卡文「⛔ 禁顺手修存量」不在本卡改，移交登记。Codex r4 LOW-2 + r5 LOW-1 补出的额外两处：`test_sync_batch_auth.py` 的 `TestDevelopmentConvenience` 分区标题（当前 :218）与其类 docstring（当前 :223）——r5 已核实这四处原文均存在于 `052a9289`（sync 当前 :218/:223 对应基线 :151/:156）。反证为 `security.py:110`：开发模式空 key 还须**同时**满足显式 bypass 与 loopback，否则 503。**r5 明确认可本卡的归因与移交判断成立。**
14. **`is_local` 条件的完整口径**（本卡已于 `87f75b19` 修正自身 docstring）—— `config.py:286` 是 `DEBUG and ("localhost" in CORS_ORIGINS **or** "127.0.0.1" in CORS_ORIGINS)`。本卡初版 docstring 漏了 `or 127.0.0.1` 分支。Codex r4 LOW-3。
15. **「正向锁定 Branch 1 只能用精确等值」是过宽表述**（本卡已于 `87f75b19` 收窄）—— Codex r4 实证 `detail.endswith("not configured")` 对 Branch 1 为 True、对 Branch 2 与两条 403 文案均为 False，同样是正向区分。精确等值是**本卡选定的**判据，不是唯一可行的。
16. **r5 提出但未计 LOW 的措辞建议（登记，不改）** —— `test_system_endpoint_auth.py` 两处注释里的「才能证明」可改为「用于验证」以统一措辞；r5 判定「紧邻前句已明确『非唯一』，按完整上下文不另计 LOW」。本卡轮次已达上限 5，且该处不影响任何判据，登记不改。
17. **未被独立锁定的目标：「鉴权先于 handler」** —— `test_system_endpoint_auth.py` 文件头声称「the point is to prove the dependency runs BEFORE the body handler」，但没有一条断言去检查「拒绝时业务替身未被调用」。当前路由确实前置注册鉴权，「先产生副作用再拒绝仍可能通过」为源码推导、未执行变异。Codex r4 附注，登记移交。
