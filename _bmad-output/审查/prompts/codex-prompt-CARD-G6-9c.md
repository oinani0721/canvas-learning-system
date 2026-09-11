# 代码审查请求 — CARD-G6-9c（两套时钟统一到单一时区来源）

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime`
审查基线：`da690bf8`（BASE）→ `0e8dc06e`（HEAD，本卡唯一 commit）

**这张卡要解决的问题**：系统里原本有四套互不相认的「今天」——
`backend/app/api/v1/endpoints/review_overview.py`（显示侧）、`scripts/daily_review_pick.py`（生产器桶位）、
`backend/scripts/vault_lint.py`（lint 的 freshness 判定）三处把时区写死成 `Asia/Shanghai`，
而 `scripts/daily_review_run.py`（launchd 早间 runner）用机器本地。宿主时区一变，这几处算出的「今天」就不是同一天。
用户裁定 D-18（2026-09-07）：「今天」= 用户当前所在地 = 机器本地；允许一个显式配置项覆盖。

**请读这些（最小读取面）**：

1. `git diff da690bf8 0e8dc06e -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动
2. `scripts/local_tz.py` 与 `backend/app/core/display_tz.py` 全文（两份同源副本）
3. `backend/tests/regression/test_g6_9c_single_tz_source.py` 全文（本卡新增的对照门，9 用例）
4. `backend/tests/regression/test_g6_9_boundary_matrix.py` 全文（上一张卡留下的边界矩阵，本卡把它的 8 条 xfail 翻转去标）
5. `backend/scripts/vault_lint.py` 的 `:55-115`（取模块机制：零写兜底那一行与 `sys.path` 拼装）与 `:120-145`
6. `backend/tests/unit/test_vault_lint.py` 的 `:55-80`（活 oracle 直载生产模块）、`:100-135`（新增的 autouse 夹具）、`:620-660`（隔离副本）、`:660-740`（FRESHNESS_MATRIX 与主断言）

## 二 作者自述（请独立核对，不要采信）

我声称做到了下面这些，请你自己去代码里查证：

1. **五处同源**：显示侧、生产器桶位、refresh 子进程、JS、`vault_lint` 全部走同一个 `display_tz()`；缺省三档 = 配置项 → `TZ` 环境变量 → `/etc/localtime` 软链解析，末档固定偏移。
2. **显示侧每次调用求值**：`review_overview.py` 里没有任何模块级时区常量，也没有 `lru_cache` / 默认参数把它固化在 import 时刻。
3. **refresh 子进程的强制赋值已删除**：此前 `_child_env()` 会把子进程的 `TZ` 钉成一个固定名，现在改为透传。
4. **8 条 `xfail(strict=True)` 已翻转去标**，登记表清空，`test_launchd_path_does_not_force_display_tz` 从"记录非对称"改成"锁住对称"。
5. **两态跑**：`TZ=Asia/Shanghai` 与 `TZ=America/Los_Angeles` 下各跑七个测试文件（含 `test_vault_lint.py`），都是 415 passed。
6. **无效配置值抛错**，不静默退化成别的时区。

## 三 请回答的问题（按重要性排序）

1. `_child_env` 改成透传之后，父进程 `TZ` 为空的容器形态下，子进程算出的日期是否与后端 GET 返回的 `display_tz` 是同一个时区视图？有没有第二套时钟残留？
2. 那个显式配置项是否在 backend / 生产器 / runner 三处都由**同一个函数**读取？有没有任何一处仍走无参的 `astimezone()`，从而在覆盖生效时分叉？
3. 源码对照门（`test_two_copies_share_identical_function_body`）是否只比函数体？它能否被"语义等价但写法不同"的副本骗过？它的判据是否比它声称的范围更宽？
4. 登记表清空成 `{}` 之后，`test_known_divergent_table_is_current` 是否退化成恒真？我把 `display` 的求值位置从内层循环外挪进了循环内并写了理由，这个改动本身是否让门变弱了？
5. JS 退回浏览器本地的那条分支有没有门覆盖？服务端下发 `null` 时，页面显示的日期与服务端算的是否可能不是同一天？
6. 改名（`_sh_day`/`_sh_today`/`_today_sh`/`shDay` 等）是否漏掉任何调用点？我的 grep 判据是否覆盖了测试目录？
7. 显示侧是否**真的每次调用**求值？变异 M2（把它改回模块级常量）是否真能被门 ⑤ 照出来，还是那条门有别的方式恒绿？
8. `vault_lint` 与 `review_overview` 收敛后是否仍可能给出不同的「今天」？`FRESHNESS_MATRIX` 的改写（加了一个 autouse 夹具钉住配置项）有没有把期望值改成与被测量同源，从而两边一起退化？
9. `display_tz()` 缺省三档的解析在哪些宿主形态下会取不到 IANA 名而静默落到固定偏移？我在门 ⑥ 里断言"必须有名"，这个断言在什么环境下会误报？
10. `vault_lint.py` 新增的 `sys.path` 拼装与模块 import 是否可能破坏它自称的"零写"声明？（三种形态：隔离副本、被当库 import、CLI 直跑。）它在那个模块缺席时是如实报错还是静默退回硬编码？
11. 矩阵文件里我把三条**非时区**用例改成钉一个字面量常量 `_FIXED_HOST_TZ`，并给它们各加了一行 `monkeypatch.setattr(picker, "_DISPLAY_TZ", ...)`。这样是否避开了门自指（若改成用显示时区的名字函数去设宿主时区，本卡收敛做没做这三条都恒绿）？那三行 patch 是否足以覆盖"生产器用模块级常量、夹具不 reload 模块"带来的全部失明面？
12. `test_vault_lint.py` 的判别锚从 `setattr(vl, "_TZ_SHANGHAI", ny)` 换成 `setattr(vl, "_display_tz", lambda: ny)` 之后，是否仍能杀掉该用例 docstring 里列的三条变异（按宿主本地换算 / 直接取 UTC 日 / 用 `date.today()`）？新加的 autouse 夹具会不会反过来把某些机制层的用例变成恒真？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 四级，每条给出 `file:line` 与一句话说明为什么它是那个级别。
没有问题的级别写「无」。请不要复述我的自述，只写你独立查证后的结论。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接数据库或任何网络服务。
- `canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py` 与 `clear-inbox/scripts/inbox_preview.py` 本卡零改动（后者固定 +8 是已裁定的例外，它有跨宿主逐字节相等的产物契约）；`scripts/launchd/*` 本批不改。这三处不在审查范围。
