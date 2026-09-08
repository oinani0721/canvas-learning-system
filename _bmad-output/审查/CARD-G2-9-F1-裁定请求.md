# CARD-G2-9-F1 — 交主 session 的裁定请求（一页版）

> 车道 `card-u5-lance` · 分支 `card/u5-lance` · HEAD `0ec1f0c3`（da690bf8 起 3 个 commit）
> 完整依据见 `_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md` §三.6 与 §五 #1。
> ⚠️ 本车道**不自判可合**（协议 §1 + D-15）。以下是裁定所需的全部事实。

## 一 卡本身：做完了

原缺陷（canary CONFIRMED，D-17 必排）：`_cache_tables` 对**全库**表跑维度/缺 doc_type 检查并 drop
⇒ 打开 vault A 会删掉 vault B 的表。**已修**：新增 `_owns_table` 单点归属过滤 + 分页收口。

| 判据 | 结果 |
|---|---|
| 新行为门（先红后绿） | 改前 3 failed / 改后 **6 passed + 2 xfailed** rc=0 |
| 负控（卡文要求 3 段） | **6 段**全 KILLED，各含变异 diff + sha 前后逐字相同 |
| 邻近六套件 | **118 passed** rc=0（含 g24 `:624/:625` 正向对照、`test_e3` 承重契约） |
| `tests/unit` 目录级 | nodeid diff 对 202 基线 **空**；本卡门不在红集；4749 → **4755 passed** |
| 现网只读 | 三个 LanceDB 目录 `find -newer` 全 **0**；10 处 `connect` 经 AST 溯源全在 tmp_path |
| 地盘门 | 恒为三文件；未碰 `backend/app/**` |

## 二 ⛔ 需要裁定的一件事

**本卡的分页收口新增了一个条件性跨 vault 数据丢失可达面。**

归属口径 `startswith(f"{vid}_")` 让**短 id 的 vault 单向认领长 id vault 的表**
（`cs` 认领 `cs_61b_*`；需下划线边界，`ab_x` 不碰撞）。这个**口径本身是既有的**
（`resolve_table_name:790` 起），本卡一字未改。

**但可达性变了** —— 实测（`evidence-g29f1/high1-r2-pagination-widens-overlap-*.txt`，
同一夹具跑两版源码）：

| 版本 | 排在默认分页外的 `a_b_canvas_nodes`（属 vault `a_b`） |
|---|---|
| `da690bf8` | **仍在**（默认分页只看前 10 张，碰不到它） |
| 本卡 | **被删**（全量枚举后碰得到了） |

门内证据 = **负控 6**：拆掉分页收口，该门立刻从 xfail 翻成 XPASS 报红。

> ⚠️ 我在 Codex round-1 时写的「这是既有口径、本卡未引入」**不完整**，round-2 由外审指出后更正。
> 那些新变可达的行**不在 diff 里** —— 这正是「可达性会被上游修复打开」。

⚠️ **有两条路径，不是一条**（round-3 由外审指出后补测，原登记不完整）：

| 路径 | 入口 | 触发条件 | 实测存档 |
|---|---|---|---|
| **cache** 启动自愈 | 进程启动 → `_cache_tables` | (i) id 互为前缀 + (ii) 表数 >10 + (iii) 重叠表在页外 + **(iv) 该表 schema 漂移** | `high1-r2-pagination-widens-overlap-*.txt` |
| **drop** 显式删索引 | `DELETE /index/{vault_id}` → `drop_vault_tables` → `list_vault_tables` | (i) + (ii) + (iii)，**不需要 (iv)** | `a2-dropvault-path-*.txt`（用**健康**表：改前删 10 张不含它，改后删 11 张含它） |

⇒ **drop 路径门槛更低**（少一个条件），且入口是**用户显式操作**而非后台启动。
(i) 在本仓可达：`sanitize_vault_id('cs 61b')` = `'cs_61b'`。

### 请裁定：这是否构成协议 §1 的阻断级（「数据丢失」）？

两个选项，代价如下（本卡**未实施**任何一个，等裁定）：

| 选项 | 做法 | 代价 |
|---|---|---|
| **A**（当前状态） | 保留完整分页收口，靠 `CARD-G2-9-F2` 尽快闭合 | 合入后到 F2 之前，主干多一个**条件性**数据丢失面 |
| **B**（保守） | 分页收口只对「去掉本 vault 前缀后**不含**下划线」的页外表生效，**且必须同时覆盖 `list_vault_tables`**（否则挡不住 drop 路径） | 不引入新可达面；但页外的 `canvas_nodes` 这类**正常**表既修不到、**也删不掉**（显式删索引会漏删），(d) 价值大打折扣；且把「默认分页」这个 SDK 细节写进业务逻辑 |

> B 的判据依据：表名 `{vid}_{rest}` 若 `rest` 无下划线，则不可能是「vault `{vid}_{X}` 的表」
> （那样至少要两个下划线）⇒「`rest` 无下划线」⟺「归属无歧义」。
> 而 `a_canvas_nodes` 既可能是 vault `a` 的 `canvas_nodes`、也可能是 vault `a_canvas` 的 `nodes`，
> **不知道 vault 列表就无法消歧** —— 这也是根治（最长前缀优先）必须由 F2 做的原因。

## 三 已加的锁与移交

- 门⑤ 族 **4 条** `xfail(strict=True)`：两条路径（cache / drop）× 两种形态（page-inner 既有面 / page-outer 本卡新打开）
- 前提另立 **4 条不带 xfail** 的门，与缺陷锁共用 **module-scope fixture**
  —— 否则 xfail 会吞掉前提失败（含 fixture setup），且 F2 修好后停在 XFAIL 而非 XPASS
- **负控 7** 在真实源码上模拟 F2 修好，实测 `8 failed, 4 passed`（4 前提门红 + 4 缺陷锁 XPASS）
  ⇒ 交接机制**已实测可用**，不是推理
- 移交 `CARD-G2-9-F2`：需拿到全部 vault 列表做最长前缀优先，涉及
  `resolve_table_name` / `_fingerprint_table_name` / `_owns_table` 三处同口径，**整体一张卡**

## 四 三处对卡文的其他偏离（均已登记，见验收单 §三）

| # | 偏离 | 理由 |
|---|---|---|
| A1 | 改了卡文说「不动」的 `:3650` 存在性判断 | 不改则 (d) 对启动自愈**完全无效**（内层把每张越界表挡回去），门③ 恒红。负控 5 证其必要 |
| A2 | 门②/④ 表名按 `:845` 实测口径改写 | 卡文举例假定「无 vault 前缀 = 归 default」，实测口径是「表名**不含任何下划线**」。逐字同语义是硬要求 |
| A3 | §二.7 判据 ⑤ 收紧为 ≥2 | 卡文写的 ≥1 在**开工就已满足**（脚本别处已有 `report.get`）= 死判据 |

另：卡文称 canary 的 rc 汇总点在 `_amain`，实测在 `_run_canary_cli`（行号对、函数归属错）；
原判据 `awk '/^async def _amain/,0'` 把两个函数一起罩住，已换 AST 精确判据。
