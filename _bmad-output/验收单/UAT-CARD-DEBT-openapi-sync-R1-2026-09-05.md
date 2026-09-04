# UAT — CARD-DEBT-openapi-sync-R1「OpenAPI 漂移门重排」

> 批次 `[BATCH-2026-09-04-第十批 / CARD-DEBT-openapi-sync-R1]`
> 车道 `card/x8-openapi`（从主干 `bce2986a` 切）· 只读取证源 `card-w4-micro @f3333328`
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十批-goals/X8.md`（v2）
> 白名单移植面 = `git diff 2fb779b3^ f3333328` 的 15 文件 减 2 个 `*.stderr-redacted.txt` = **13 文件**
> 本卡 commit（4 个，**0 个 merge commit**）：`6c674467`（裁决页）→ `390a3ae9`（13 文件
> 打包）→ `c99e37ea`（快照重生成）→ **本验收单 commit**（本验收单 + Codex round-4
> 两份产物）。末条刻意不写 hash：它每次 `--amend` 都会变，写死就是个自指的过期数字。
> 前三条已定，不会再变。

---

## 4-B 用户可感（先看这段）

**这次改了什么，对你意味着什么：无变化。**

你在应用里能做的事、能看到的界面、能得到的回答，一件都没有动。这张卡改的全是
「写代码的时候机器帮你检查什么」，不是「你使用的时候程序做什么」。

唯一你可能间接注意到的：以后如果有人改坏了接口说明书而没有同步更新，机器会当场
拦下来，而不是像过去五个月那样一声不吭地放过去。对你而言，这意味着接口说明书和
真实程序**不再会悄悄对不上**——但这属于"本来就该如此"，不是新功能。

---

## 4-A 技术验收

### 一 裁判命令逐条（卡文 §二，7 条）

| # | 裁判 | 期望 | 实测 |
|---|---|---|---|
| 1 | `git diff --name-only bce2986a HEAD \| wc -l` | 13 + 快照 commit 触及数 | **16**（终态实测）= 13 白名单 + 1 本验收单（卡文 (a) 的裁决页）+ 2 份 Codex round-4 产物（卡文 §四 要求的 prompt 与 review）。快照 commit 触及的 `backend/openapi.json` 已在 13 内，额外 0 |
| 1' | 不含前两卡路径 / `*.stderr*` | 全 0 | `bark-autostub` 0、`isolate-lifespan` 0、`evidence-isolate-lifespan` 0、`\.stderr` 0 |
| 2 | `pytest --collect-only tests/contract/test_openapi_snapshot_drift.py` | 23 | **23 tests collected**；全跑 **23 passed**，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` |
| 3a | `check-openapi-drift.py --snapshot openapi.json` | `DRIFT: none` | **`DRIFT: none (paths=193 schemas=353)`** rc=0 |
| 3b | `openapi_drift_negative_control.py` | `NEGATIVE-CONTROL: PASS` | **`NEGATIVE-CONTROL: PASS (3 mutants → exit 1 with named diff; timestamp-only → exit 0)`** rc=0 |
| 4a | `grep -cE '^\s*update-spec:'` | 0 | **0**（裸 `grep -c 'update-spec'` = **2**，v1 写法确会假红——2 处是 `:326`/`:433` 的溯源注释，未删） |
| 4b | `grep -cE '^\s*if: false'` | 1 | **1**（在 `contract-test` job，`api-spec-sync.yml:330`） |
| 4c | `awk '/^pre-commit:/,/^pre-push:/' lefthook.yml \| grep '^  parallel:'` | `parallel: false` | **`  parallel: false`**（裸 `grep -c '^  parallel:'` = **2**，会数到 pre-push 的 `true`，v1 写法确会假红） |
| 5 | `ls-files \| grep -ci 'stderr'` | 只允许历史 `.txt` | 全仓唯一命中 `_bmad-output/审查/G4-9-evidence/census-stderr.txt`（历史文件，非本卡引入） |
| 6 | 不直跑 `lefthook run pre-commit` | — | 遵守：全部用 `--command` + `--file` 定向探针，见 §四；每次探针前后核对 `openapi.json` sha 与工作区变更数 |
| 7 | `grep -c '<user-home 前缀>' <13 文件>`（模式串是 `/Users/` 加用户名；**不把它字面写进本文件**，否则裁判 7 会扫到自己 = 判据自指） | 0 | **0**（复核时扫的是本卡全部 16 个涉及文件，含本验收单与 round-4 两份产物） |

### 二 红门先红（卡文 (d)）——三种红，各自独立取证

红门证据有时序不可逆性：红A 只在打包前可得，红B 只在打包后、快照重生成前可得。
三段都实测到位，判据都绑定到**具体失败项**，不是笼统的 `rc≠0`。

| 段 | 时点 | 命令 | 结果 | 拒因原文 |
|---|---|---|---|---|
| **红A：脚本缺席** | HEAD=`bce2986a`（打包前） | `pytest --collect-only tests/contract/test_openapi_snapshot_drift.py` | **rc=4**，`no tests collected` | `ERROR: file or directory not found: tests/contract/test_openapi_snapshot_drift.py`（该文件与 `check-openapi-drift.py`、`openapi_drift_negative_control.py` 三者在主干均 ABSENT） |
| **红B-1：快照对 live 漂移** | 打包后（`390a3ae9`），快照 = w4 侧 192 paths | 全跑 | **1 failed / 22 passed** | 唯一失败 `test_committed_snapshot_has_no_drift`，点名 `>components>schemas>RefreshChangedResponse>description` 与 `>properties>persist_failed`（CARD-G2-5 引入的字段，w4 快照没有） |
| **红B-2：provenance 不合规** | 定向探针：工作区临时换回主干快照（EXIT trap 保护，跑完 sha 逐字还原） | 全跑 | **2 failed / 21 passed** | 新增失败 `test_snapshot_carries_generator_provenance`：<br>`AssertionError: x-generator='Canvas Learning System OpenAPI Exporter' — 快照应由 check-openapi-drift.py --write 生成; 手改或旧 export-openapi.py 产物不合规` |
| **绿** | `c99e37ea` 之后 | 全跑 | **23 passed**，连接尝试 0 | — |

红B-2 的探针还原经 sha 校验：`c90f6f1e12d775a16c183de7f78d373217d469dc` → 同值，`RESTORED=YES`。

### 三 快照重生成（卡文 (i′)）与 5 个月漂移

主干 `backend/openapi.json` 最后改于 `48f4b82b`（2026-03-31，旧 `export-openapi.py` 产物）。
本车道用 `check-openapi-drift.py --write`（脚本写入，非手改）重生成后：

| 维度 | 主干 `bce2986a` | 本车道 live | 变化 |
|---|---|---|---|
| paths | 163 | **193** | 新增 44、移除 14，净 +30 |
| schemas | 299 | **353** | +54 |
| `x-generator` | `Canvas Learning System OpenAPI Exporter` | `scripts/spec-tools/check-openapi-drift.py --write` | 门认的 provenance |
| `RAGQueryRequest.required` | `['query']` | **`['query', 'vault_id']`** | G4-4a 后 `vault_id` 必填落进契约 |

移除的 14 条以 `/mcp/tools/*` 为主（MCP 工具路由改为 quarantined stub）；新增含
`/api/v1/errors/*`、`/api/v1/boards/manifest`、`/api/v1/chat/enrich-context` 等。

导出过程中 socket lockdown **真实拦截**了一次出网：LiteLLM 尝试拉远程 model cost map，
被拦在 `target=('127.0.0.1', 1082)`（本机系统代理），日志原文
`socket connect blocked during OpenAPI export`。这是 lockdown 在生产路径上生效的实证
——但它证明的是"拦住了 connect"，**不等于**"本次导出没起 lifespan"（见 §七）。

### 四 负控三态（卡文 (e)）——独立演示，不采信脚本自证

三态全部在 tmp 副本上做，正本 `backend/openapi.json` sha 前后逐字相同。

| 态 | 做法 | rc | 输出 |
|---|---|---|---|
| 1 变异 | 改 tmp 副本一处：`components.schemas.RAGQueryRequest.properties.vault_id.description` → `__X8_NEGCTL_MUTANT__` | **1** | `DRIFT: found (paths: +0 -0, schemas: +0 -0, diff lines: 1)`，**点名**该 JSON 指针并回显两侧取值 |
| 2 重生成 | `--write` 到 tmp 后 `--snapshot` 同一文件 | **0** | `DRIFT: none (paths=193 schemas=353)` |
| 3 仅时间戳 | 只改 `info.x-generated-at` → `1999-01-01T00:00:00+00:00` | **0** | `DRIFT: none (paths=193 schemas=353)` |

正本校验：`b861e981d9ad014ba3656644c51e41af2c0ef3fe` → 同值。

### 五 lefthook 双源（卡文 (f)）

| 要求 | 实测 |
|---|---|
| `pre-commit: parallel: false` | ✅ `awk` 限定在 pre-commit 区内取到 `  parallel: false`；pre-push 的 `parallel: true` 未动 |
| 两命令都走 `check-openapi-drift.py --write` | ✅ `lefthook.yml:56` 与 `:67` 各一处，全文已无 `export-openapi.py` |
| `spec-sync-flat` ∩ `spec-sync-root` = 0 | ✅ 见下方探针表 |
| python-typecheck 块（原 `:76-115`）逐字不动 | ✅ 同口径 awk 锚点提取 41 行，主干与本卡 **sha 同为 `b2193117cf61f0a03f00a63e25660a198455441d`**；行号平移到 `:110-150`（本卡 hunk 在其上方，插入 35 行） |
| 禁整文件覆盖 | ✅ 本树 `lefthook.yml` ≠ `f3333328:lefthook.yml`（314 行 vs 287 行；w4 侧 `PYRIGHT_EXIT` 3 处、本树 4 处，即 w4 侧**没有** X5-A 的诚实化改动，整文件覆盖就会静默回滚它） |

**glob 交集探针（生产引擎 lefthook 2.1.6，零副作用方向）**

| 命令 | 喂入文件 | 结果 |
|---|---|---|
| `spec-sync-flat` | `backend/app/main.py` | 未命中 |
| `spec-sync-flat` | `backend/app/config.py` | 未命中 |
| `spec-sync-root` | `backend/app/mcp/server.py` | 未命中 |
| `spec-sync-root` | `backend/app/api/v1/endpoints/rag.py` | 未命中 |
| `spec-sync-root` | `backend/app/models/schemas.py` | 未命中 |
| **验伪锚** `spec-sync-flat` | `backend/app/api/v1/endpoints/rag.py` | **命中并真执行**：`[Spec Sync] API changes detected, regenerating backend/openapi.json (via backend/.venv/bin/python)` → `M  backend/openapi.json` staged |

验伪锚是必须的：没有它，「五个未命中」可能只是 `--command`/`--file` 组合没生效，
证据就是空的。验伪锚同时顺带证明了 (f) 的另外两项在生产引擎下真实工作——
**venv 解析器命中**（用的是 `backend/.venv/bin/python` 而非裸 `python`）、**`--write` 与
`git add` 都执行**。命中产生的 staged 改动已还原，`openapi.json` sha 与工作区变更数
（0 项）前后一致。

> ⚠️ **这个探针第一次跑错了引擎。** `npx lefthook` 解析到主仓 `node_modules` 的
> **1.13.6**，而 git hook 实际调用的是 PATH 上 homebrew 的 **2.1.6**（commit 输出的
> banner 是 v2.1.6）。用 1.13.6 得到的 skip 证据对生产配置不成立，已作废重跑。
> 中途还有两次假证据被自己的判据抓回：2.1.6 不认 `-n` 导致四条命令直接报错而输出为空
> （"输出为空即通过"是假判据）；zsh 的 `set -- $pair` 不分词，导致实际传的是
> `--command "spec-sync-flat backend/app/main.py" --file ""`，命令名不存在所以什么都没跑。
> 最终表格是逐条写死 + 验伪锚之后的结果。

### 六 workflow（卡文 (g)）

| 要求 | 实测 |
|---|---|
| `^\s*update-spec:` 0 次 | **0**（job 名单剩 5 个：`export-openapi` / `validate-spec` / `detect-breaking-changes` / `contract-test` / `summary`） |
| `^\s*if: false` 恰 1 次 | **1**，在 `contract-test`（Dredd）job，`api-spec-sync.yml:330` |
| YAML 可解析 | ✅ `yaml.safe_load` 通过 |
| actionlint | **缺席**（`command -v actionlint` 无），未跑；如实登记 |

### 七 未合分支冲突登记（卡文 (j)）

`fix/test-infra-paralysis`（尖端 `66d6a835`）：

| 基准 | `merge-tree` rc | 冲突文件 |
|---|---|---|
| 主干 `bce2986a` | 1 | **仅** `lefthook.yml`（content conflict） |
| 本卡 HEAD `c99e37ea` | 1 | **仍仅** `lefthook.yml` —— 冲突面**未因本卡扩大**（新事实） |

**⛔ 合入该分支会回滚 X5-A 的 python-typecheck 诚实化块。** 量化证据（比 hunk 范围更硬）：

| 标记 | 主干 `bce2986a` | 本卡 HEAD | `fix/test-infra-paralysis` |
|---|---|---|---|
| `HONESTY CONTRACT` | 1 | 1 | **0** |
| `SKIP` | 3 | 3 | **0** |
| `PYRIGHT_EXIT` | 4 | 4 | **3** |

该分支对主干 `lefthook.yml` 的首三个 hunk 是 `-76,13` / `-94,15` / `-115,64`，整块
覆盖主干 76-178 区，而 X5-A 的块正是 `:76-115`。本卡 hunk 全在 `-17..-43`，与之
**零重叠**——即冲突不是本卡造成的，本卡也不消解它。

### 八 边界遵守

| 硬边界 | 状态 |
|---|---|
| 禁改 `backend/app/**` | ✅ 本卡 diff 无该路径 |
| `backend/openapi.json` 禁手改 | ✅ 唯一写入口是 `--write`（`x-generator` 即门认的 provenance） |
| 禁 merge / cherry-pick / rebase `card/w4-micro` | ✅ 全程只用 `git diff … \| git apply`；`git log` 无 merge commit |
| 禁整文件覆盖 `lefthook.yml` | ✅ 见 §五 |
| `lefthook.yml:76-115` 逐字不动 | ✅ sha `b2193117…` |
| 禁改 `requirements*.txt` / 其它 workflow / `test_openapi_contract.py` / `.gitignore` / 台账 | ✅ 本卡 diff 14 文件中均不含 |
| 导入 `app.main` 只 import 不启动 | 脚本内 socket lockdown 全程生效（实测拦到一次真实 connect） |
| 负控 tmp 变异不动正本 | ✅ 正本 sha 前后同值 |
| live 与 7691 只读 | ✅ 全程 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`；`backend/data` 目录三次对账（打包后 / 重生成后 / 绿门后）文件数 6、聚合 sha `8a3f63d4ae1f5b95087d376b82197813a2e6982a` 恒定 |
| 不 push | ✅ |

---

## 待你裁决（4 项，卡文 §一 (a)）—— 已裁（用户 2026-09-05，按默认）

### 裁决记录（**已裁**：用户 2026-09-05 在主 session 裁「4 项都按默认」，取值与下表逐字相同；主干 f128a85e 手册 §三 X8 块上方「用户裁决记录」为权威——本节原写「车道代填·待你确认」是车道在 bce2986a 读到裁决前快照所致，主 session 合入时更正）

```
#0 乙（排第四轮 Codex 确认）/ #1 批（删 update-spec）/ #2 批（Dredd if:false）/ #3 批（lefthook 出声化）
```

| 字段 | 值 |
|---|---|
| 代填时间 | 2026-09-05 |
| 代填人 | 车道 `card/x8-openapi`（**不是用户**） |
| 来源 | 卡文 §四「默认裁决」逐字取值，非用户主动填写 |
| 状态 | **生效中**——本卡的 (b)-(j) 全部按这四个取值执行完毕 |
| 你要做的 | 确认则把上面那一行抄进开跑手册 §三 X8 块上方的「用户裁决记录」（该行注明**由主 session 代填**，故车道不自行改手册）；推翻则见下表「若你推翻」列 |

> ⚠️ **这不是"已获批准"。** 它是一条明确取值、明确来源、可被推翻的裁决记录——
> 存在的意义是让「裁决状态」有据可查，而不是停留在"未裁"这个既不能推进也不能验证
> 的悬空状态。四项里只有 **#0** 的不同取值会改变落地产物（且只有丙会），其余三项
> 推翻都只需 revert 对应 hunk。

### 原始状态与判断依据

**用户未主动裁决。** 开跑手册 §三 X8 块上方「用户裁决记录」实读为空
（`#0 ＿ / #1 ＿ / #2 ＿ / #3 ＿`，2026-09-05）。

本车道**按卡文 §四 的默认裁决执行**。卡文 (a) 字面写「用户批前不动 (b)」，但完成
条件 (a)-(j) 是 AND 且 (b)-(j) 全部以 (b) 落地为前提——若字面停在裁决页，这张卡
永远无法完成。默认裁决存在的意义就是让车道不空转。**默认裁决不等于已获批准**；
每项的回退成本见下表最后一列，你事后推翻任何一项都不需要重跑这张卡。

| # | 决策 | 现状（为什么要裁） | 选项 | 默认 | 若你推翻 |
|---|---|---|---|---|---|
| **0** | 停轮状态下怎么合并 | round-3 终裁是 **FAIL**：2 BLOCKER + 1 HIGH + 1 MEDIUM。整改压在 `66017721`（把 `_normalize` 里的 required 排序**整个删掉**，-73 行），**没经过第四轮确认**。 | **甲** 接受现状认账「移除 required 排序」<br>**乙** 排第四轮 Codex 确认 2B+1H 清零<br>**丙** 降级只收路径修正 | **乙**（已跑，见 §九） | 选**甲**：删掉 round-4 的两个文件即可，代码零改动（甲乙的落地产物**完全相同**）。<br>选**丙**：需 revert `390a3ae9` 重挑子集——唯一需要重做的选项。 |
| **1** | 删 `api-spec-sync.yml` 的 `update-spec` job | 该 job 在 `push && main` 时自动 `git push \|\| true` 回写 spec。`\|\| true` 让它失败也不出声；且本仓从不直接 push main。**可证从未生效**。 | 删 / 留 | **批（删）** | revert 该 hunk。 |
| **2** | Dredd 契约测试改 `if: false` | Dredd job 长期红（需 `npm install -g dredd` + 起服务）。停用后 **CI 侧契约覆盖归零**——schemathesis 的 `test_openapi_contract.py` 没进 `test.yml` 白名单，只在本机 `importorskip` 跑。 | 停用 / 留着红 | **批（停用）**<br>+ 登记独立候选卡 | 把 `if: false` 改回原样。⚠️ 无论怎么裁，**契约覆盖归零需要一张独立的卡**，本卡只负责登记。 |
| **3** | lefthook `spec-sync` 出声化 | 这个 hook **死了 4 个月没人发现**：解析器是裸 `python`（不是本仓 venv）、`2>/dev/null` 吞掉全部失败、检查的 `openapi.json` 在**仓库根**（该文件在本仓全部历史里都不存在）。三处任一都足以让它静默空转。 | 修 / 留 | **批（修）** | revert 本卡的 `lefthook.yml` hunk。 |

**#3 的已知代价（批了就会遇到）：** ① 改 `backend/app/{api,models,schemas,mcp}/*.py`
或 `main.py`/`config.py` 的 commit 多花约 20 秒重生成快照；② 快照含恒变时间戳，
所以 `backend/openapi.json` **必然出现在这类 commit 的 diff 里**；③ 导出失败会
**阻断本地 commit**（这正是「出声」的含义）。§五的验伪锚已实地跑过一次这条链路。

---

## 九 本卡独立发现（未修，已登记）

### 9.1 门打印的 FIX 命令在两种 cwd 下都不可用

`check-openapi-drift.py:258` 在报漂移时向 stderr 打印：

```
FIX: python scripts/spec-tools/check-openapi-drift.py --write backend/openapi.json  (禁手改快照)
```

实测两个 cwd，**没有一个能照抄执行**：

| cwd | 结果 |
|---|---|
| `backend/` —— 裁判 2 的 pytest、裁判 3 的 `--snapshot` 实际都在这里跑 | `can't open file '<repo>/backend/scripts/spec-tools/check-openapi-drift.py': [Errno 2] No such file or directory`（路径是相对仓库根写的） |
| 仓库根 —— 路径成立 | 裸 `python` 解析到 `/opt/homebrew/bin/python`（3.14.4，**非本仓 venv**）→ `ModuleNotFoundError: No module named 'structlog'`，rc=1 |

这条击穿 `_normalize` docstring 的原话「**误红的代价 = 开发者跑一次门输出里打印的
FIX 命令**」——实际代价是开发者得先自己搞清楚该在哪个目录、用哪个解释器。属于
「声明比证据宽」。

更值得记的是：**裸 `python` 正是本卡在 `lefthook.yml` 里修掉的那个缺陷**（现在两条
spec-sync 命令都先探 `backend/.venv/bin/python`），但同一个脚本自己打印的 FIX 提示
仍在教用户用裸 `python`。这是同一缺陷的**未封堵站点**，不是新缺陷。

**未修，理由**：卡文 (h) 把 round-4 的审查面限定在 `_normalize`，本卡完成条件
(a)-(j) 中没有「修 FIX 提示」这一项；擅自扩范围违反防蔓延。已登记为候选卡（见台账
第 6 条）。修法本身很小——把 FIX 行改成与 lefthook 同款的 venv 探测 + 注明 cwd。

## 十 Codex 冻结审查（卡文 (h)，(乙) 一轮为限）

### 10.1 结果

一轮（(乙) 默认裁决，本族累计第 4 轮）。命令同形态、冻结、只读：
`codex exec --sandbox read-only --cd <lane> -m gpt-5.6-sol -c model_reasoning_effort="ultra"`，
提示词 `_bmad-output/审查/prompts/codex-prompt-CARD-DEBT-openapi-sync-R1.md`，
全文 `_bmad-output/审查/codex-review-CARD-DEBT-openapi-sync-R1.md`（已脱敏 16 处 / 11 行）。

**BLOCKER 0 · HIGH 0 · MEDIUM 0 · LOW 4**，末行 `BLOCKER/HIGH 清零: 是`，
绑定 `card/x8-openapi@c99e37ea`。审查面按卡文 (h) 收窄到 `_normalize` /
`_tag_leaf` / `canonicalize` 及其对应门。

### 10.2 逐条

| 项 | 结论 | 关键证据（Codex 独立复现） |
|---|---|---|
| 1 · round-3 B1（语境切分误排序）| **PASS** | `VALUE_CONTEXT_KEYS` / `value_context` / required sort 全仓零命中；x-extension 与 Link `requestBody` 内的字面 `required` 反序后 `compare=False` 并逐下标报差异——即**不再被吸收**，假绿路径随机制一并消失 |
| 2 · round-3 HIGH（属性名 enum/const/… 被误判）| **PASS** | dict key 只参与排序、不参与策略选择；五种属性名的子树处理完全相同 |
| 3a · 只严不松方向性 | **PASS** | 保序相对旧排序只能扩大「不相等」集合 ⇒ 只增误红、不新增漏报（该结论只针对 required，不涵盖 number 等价策略） |
| 3b · required 顺序是否稳定 | **PASS** | 5 个独立 `--write` 进程 + 5 个新 `--snapshot` 进程：654 个 required 成员 / 281 个数组，顺序签名五次同为 `b2309581…`，canonical SHA-256 五次同为 `389b8b67…`，5 次均 `DRIFT: none`。**不外推到 CI Python 3.11 或跨机器** |
| 3c · FIX 命令说法 | **PASS + LOW-2** | 受控反序确实产生 exit 1 + 4 条逐位差异 + 打印 FIX；但该命令本身不可照抄（见 §9.1，我方独立发现同一处） |
| 4a · bool 先于 int | **PASS** | `True → ("boolean", True)` vs `1 → ("number", 1)` 比较为漂移 |
| 4b · int/float 同归 number | **PASS（有意策略）** | `1` vs `1.0` clean，由测试 `:306-315` 钉死；**不会**吞 `1 → 1.5`，也不会吞 `"type": "integer" → "number"` |
| 4c · `raw` 分支 | **生产 PASS，helper 域 LOW-1** | 生产 CLI 两端都经 JSON round-trip，`raw` 不可达；但直接调 helper 传 `bytes` vs 同内容 `bytearray` 会 `compare=(True, [])`（假相等） |
| 4d · deepcopy / volatile keys | **PASS** | 先 deepcopy 再只删顶层 `info` 的两个生成器扩展；全树扫描未发现其他易变字段 |
| 5 · 回归面 | **全 PASS** | 23 passed / `NEGATIVE-CONTROL: PASS` / `DRIFT: none` / 连接尝试 0；未构造 TestClient，未连 7691/7687 |

### 10.3 LOW 4 条的处置（全部登记，本卡不修）

| # | 内容 | 处置理由 |
|---|---|---|
| LOW-1 | `raw` 分支对非 JSON 输入不 fail-closed，`bytes` vs `bytearray` 假相等 | **生产不可达**（CLI 两端都经 JSON round-trip）。属 helper 健壮性缺口，登记候选卡 |
| LOW-2 | FIX 命令裸 `python` + 依赖仓库根 cwd | 与我方 §9.1 **同一处**，两方独立发现。修法明确但超出卡文 (h) 审查面，登记候选卡（台账第 6 条） |
| LOW-3 | 23 个门里**没有**直接钉住 round-3 那三种原形（x-extension / Link `requestBody` / 特殊属性名）的 fixture | 当前全局保序实现足以通过，但**将来若有人重新引入选择性分支，现有测试拦不住**。这是本轮最值得排卡的一条——它是「机制删掉了，但防止它被重新引入的门没建」 |
| LOW-4 | 陈旧文字：测试 `:175-179` 称「sorted 而非 set」、`:212-228` 仍称「语境切分」；负控 `:11-12` 仍写 required 按集合排序；模块 docstring 列四条规则却在 `:103`/`:137` 写「规则 5 / 五条」 | 文档与实现不符（说的比做的多）。改动面横跨 3 个文件、可能触及 23 个门的注释，超出本卡范围，登记候选卡 |

### 10.4 Codex 自己声明的边界（照录，不代其收窄）

- 3b 的稳定性结论「不外推到 CI Python 3.11 或跨机器」；
- 回归面「是定向门，不代表 whole-suite / CI」；
- 审查期间发现本验收单文件并发变为 `M`（那是我在同时写它），Codex 未触碰、未还原，
  并声明「来源未判定，不影响目标文件绑定」——四个被审文件与 `backend/openapi.json`
  的 working-tree blob 均与 HEAD 逐字一致。

---

## ⛔ 本卡未证明什么（必填）

1. **未经 GitHub 实跑。** `api-spec-sync.yml` 的改动（删 `update-spec`、Dredd
   `if: false`）与新加的 Snapshot drift gate，**CI 翻红/翻绿只有 push 后可见**。
   本卡不 push，所以「workflow 改完还能跑」这件事只有 YAML 可解析这一层证据。
   卡文另记：该 workflow `PYTHON_VERSION='3.11'` 而本机 venv 是 3.14.4，
   `requirements` 只锁下限 → **首推大概率红**；那是门在工作，不是本卡改坏。
2. **「import-only 自证」在 pytest 进程内空转。** `backend/tests/conftest.py:32`
   在收集期已 `from app.main import app`，`load_live_schema()` 的延迟 import 命中
   模块缓存。`test_lockdown_actually_blocks` 只证明 socket lockdown 会拦 connect，
   **不能证明「本次导出没有起 lifespan」**。§三里那次真实拦截（LiteLLM → 127.0.0.1:1082）
   发生在独立的 `--write` 进程里，比 pytest 内的自证强，但它证明的仍然只是
   「拦住了 connect」这一件事。
3. **lefthook 探针只覆盖被喂入的 6 个文件。** §五的交集结论是这 6 个样本 + 两条
   glob 的 brace 集合互斥（`{api,models,schemas,mcp}` vs `{main.py,config.py}`）
   共同支撑的，**不是对 `backend/app` 下全部 263 个 `.py` 的穷举**。
4. **actionlint 未跑**（本机缺席）。workflow 只过了 `yaml.safe_load` 这一层。
5. **快照终态未定。** 本卡的 `c99e37ea` 是**车道本地态**（基于 `bce2986a` 的 live
   schema）。卡文 (i) 要求终态快照由主 session 在**最终主干**再 `--write` 一次——
   在那之前，这份快照对最终主干可能仍有漂移。
6. **两条 `.stderr-redacted.txt` 的内容未被审阅。** 它们按 (b) 直接排除（匹配
   `.gitignore` 的 `*.stderr*`），本卡没有读过其中是否有需要抢救的线索。
7. **`required` 顺序的稳定性只在本机 Python 3.14.4 上成立。** 移除 required 排序后，
   顺序变化会被判漂移，所以「同一份代码重复导出是否给出相同顺序」直接决定这个门
   会不会无故变红。Codex round-4 的 3b 做了 5 个独立进程 × 双向（write + snapshot）
   的实测：654 个 required 成员 / 281 个数组，顺序签名五次相同，未复现随机顺序。
   **但这条证据不外推到 CI 的 Python 3.11，也不外推到别的机器**——而 CI 跑的正是
   3.11，且 `requirements` 只锁下限。首推若在此处变红，先查是不是这个原因。
8. **round-3 那三种原形没有专门的门钉住**（Codex LOW-3）。B1/HIGH 是靠**删掉机制**
   消失的，不是靠新增断言拦住的。现在没有任何 fixture 直接覆盖 x-extension 内字面
   `required`、Link Object 的 `requestBody`、属性名恰为 `enum`/`value` 的 Schema 子树。
   将来若有人重新引入"聪明的"选择性排序，这 23 个门**拦不住**。
9. **LOW-1 的 helper 缺口未在生产路径上验伪。** Codex 说 `raw` 分支生产不可达（两端
   都经 JSON round-trip），本卡采信其证据，**没有独立复核这个不可达性**。

---

## 台账待登记条目

1. **「Dredd 复活 / 退役」独立候选卡**（卡文 (a) #2 要求同批登记）。停用 Dredd 后
   CI 侧契约覆盖归零：schemathesis 的 `backend/tests/contract/test_openapi_contract.py`
   **没有进 `test.yml` 的白名单**，只在本机 `importorskip` 跑。该卡要裁的是：把
   schemathesis 接进 CI，还是修复 Dredd，还是明确接受"契约测试只在本机跑"。
2. **`fix/test-infra-paralysis` 冲突登记 + 新事实**（卡文 (j)）：对主干与对本卡 HEAD，
   唯一冲突文件都是 `lefthook.yml`，冲突面**未因本卡扩大**；该分支 lefthook.yml 的
   `HONESTY CONTRACT`=0 / `SKIP`=0 / `PYRIGHT_EXIT`=3（主干为 1/3/4），
   **合入会回滚 X5-A 的 python-typecheck 诚实化块**。本卡不消解。
3. **lefthook 存在两个版本，行为不同。** `npx lefthook` → 主仓 `node_modules` 的
   **1.13.6**；git hook 实际调用 → PATH 上 homebrew 的 **2.1.6**（`package.json`
   声明的是 1.13.6）。两者 flag 集不兼容（2.1.6 用 `--command` 单数、无 `-n`）。
   任何"用 npx 验证 hook 行为"的证据都不对生产成立。建议登记：统一版本，或在
   文档里写死"验证 hook 必须用 `/opt/homebrew/bin/lefthook`"。
4. **主仓 `.git/hooks` 被 `npx lefthook run` 隐式重装过一次**（本卡 2026-09-05
   05:04，`pre-commit`/`commit-msg`/`pre-push`/`prepare-commit-msg` 四个文件 mtime 变化）。
   已核验**内容无实质变化**（与未被触碰的 `post-commit` 逐字同结构，仅 hook 名不同，
   即两次都是同版本 dispatcher）。后续用 `--no-auto-install` 可避免。主仓 `.git` 为
   全部 worktree 共享，此类隐式重装应登记为跨车道风险。
5. **`backend/.venv` 在本车道缺席**，本卡建了指向 `card-v5-lance` venv 的目录级
   symlink（`.gitignore` 已覆盖 `.venv`，未入库）才让 `python-lint` 与
   `spec-sync-*` 的 venv 解析器可跑。若不建，`ruff check` 会 rc=127 直接阻断 commit。
   建议登记：新车道开跑手册加一步 venv symlink。
6. **候选卡：修 `check-openapi-drift.py:258` 的 FIX 提示**（见 §9.1）。该命令在
   `backend/`（门的实际 cwd）下路径不成立，在仓库根下裸 `python` 缺依赖——两种
   cwd 都不可照抄。同一缺陷（裸 `python`）本卡已在 `lefthook.yml` 侧封堵，此处是
   未封堵站点。修法：与 lefthook 同款 venv 探测 + 注明 cwd。
