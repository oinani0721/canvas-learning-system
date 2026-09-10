# 独立审查请求（round-3，收口轮） — CARD-HYGIENE-openapi

## 一 背景与最小读取面

本仓是 Canvas Learning System（FastAPI 后端 + schemathesis 4.14.3 合约测试）。本卡两件事：
把写方法排除出 schemathesis 生成面 + 新增 `tests/contract` 的 autouse 零写门。

**本轮绑定 HEAD `a525d8ad`。代码面自 `11dfe410` 起零变动**
（`git diff --stat 11dfe410 a525d8ad -- . ':(exclude)_bmad-output'` 为空），
本轮之后只会改 `_bmad-output`。

### 前两轮及整改（请据此判断是否已收口）

| 轮 | 绑定 | 结果 | 整改 |
|---|---|---|---|
| r1 | `3c064c9d` | B0 H0 M0 **L1** | 注释覆盖面数字过时（93/113）→ 改为当时实测 92/114（commit `dddfc598`，纯注释） |
| r2 | `dddfc598` | B0 **H1** **M3** | 见下 |

**round-2 的 HIGH-1 与 MEDIUM-2/3（你指出的三条间接写）已全部追加排除**（commit `11dfe410`）：

- `GET /api/v1/review/fsrs-state/{concept_id}`（HIGH）
- `GET /api/v1/health/storage`（MEDIUM）
- `GET /api/v1/multimodal/health`（MEDIUM）

作者已逐条独立核过源码，确认你的调用链成立，并**更正了自己此前的一处归因错误**：
`data/fsrs_card_states.json` 此前被作者归因为「app lifespan 与运行期写入」，
实为该 GET 在请求期写的。

**round-2 的 MEDIUM-4（五项检测面不足以证明代码目录整体零写）登记不改**，
理由：卡文把 `_SKELETON` 写死为这五项，扩大检测面超出本卡授权；缺口已逐字写进验收单的
「本卡未证明什么」与台账。

### 请只读下面这些

- `git diff ce1e085b a525d8ad -- . ':(exclude)_bmad-output'`
- `backend/tests/contract/test_openapi_contract.py`（全文）
- `backend/tests/contract/conftest.py`（全文）
- `_bmad-output/审查/evidence-hyg-openapi/collect-before.txt`
- `_bmad-output/审查/evidence-hyg-openapi/collect-after.txt`
- `_bmad-output/审查/evidence-hyg-openapi/excluded-operations.txt`
- `_bmad-output/审查/evidence-hyg-openapi/collect-verdict-r2-20260909T214525.txt`
- `_bmad-output/审查/evidence-hyg-openapi/zero-write-verdict-20260909T162042.txt`（首轮）
- `_bmad-output/审查/evidence-hyg-openapi/zero-write-verdict-r2-20260909T214642.txt`（终轮）
- `_bmad-output/审查/evidence-hyg-openapi/find-newer-attribution-20260909T211708.txt`（首轮归因）
- `_bmad-output/审查/evidence-hyg-openapi/find-newer-attribution-r2-20260910T025520.txt`（终轮归因）
- `_bmad-output/验收单/UAT-CARD-HYGIENE-openapi-2026-09-09.md`（全文）
- 你为核对上述结论需要跟进的 `backend/app/` 下的 handler 与 service（跟到写盘点为止）

不要读 `.env` 或任何含凭据的文件。

## 二 作者自述（请独立核对，不要采信）

1. **最终收窄面**：`T_BEFORE=206`、`G=93`（GET 93 / HEAD 0）、`EXTRA=4`、`T_AFTER=89`、`N=117`
   （POST 96 / DELETE 9 / PUT 6 / GET 4 / PATCH 2）。
   正控：`89 == 93 − 4`、`206 == 89 + 117`、点名 `test_api_contract[GET /]` 仍在、
   且整改后的 `collect-after` 是整改前（92 条那版）的**真子集**（新增 0 行，恰移除 3 条）。
2. **(e) 跑了两轮全跑**：
   - 首轮（`EXTRA=1`，92 operation）：`92 failed, 1 skipped`，4:55:14，`rc=1`；
     `find -newer` 命中 **6 条**（判据未通过）。
   - 终轮（`EXTRA=4`，89 operation）：`89 failed, 1 skipped`，5:06:32，`rc=1`；
     `find -newer` 命中 **2 条**（判据仍未通过）。
   - `git status` 排除本卡两文件后两轮均为 0 行；五项骨架两轮均不存在。
3. **作者声称的因果**：排除那三条 GET 后，`fsrs_card_states.json` 的 mtime 停在首轮的
   `18:26:21`、`llm_call_logs.db` 停在 `16:21:24`、`qa_metrics.db` 停在 `17:20:56`，
   均早于终轮哨兵 `21:46:42`，故终轮全程未被写。
   作者称这是「两轮对照实测确认了 round-2 HIGH-1」。
4. **剩余 2 条的归因与处置**：
   - `logs/memory-system-2026-09-09.log`（mtime `22:06:45`，跑中）= health 系 GET 请求期写的日志
     → 登记不排除（可观测性输出、gitignore 覆盖、非 vault 骨架、排除整个 health 面代价过大）。
   - `app/data/vault_index_pending__canvas_vault.jsonl`（mtime `2026-09-10T02:53:30`，
     ≈ `21:46:42 + 5:06:32` 即跑结束时刻）= app 关闭时持久化，非单个 GET 触发
     → 登记不排除。
5. **(g) 目录级**：块 A（`test_openapi_contract.py`，即 (e) 终轮）+ 块 B（其余 5 文件，
   `3 failed, 99 passed, 2 skipped`）。块 B 的 3 红经「临时移走本卡 conftest」对照基线
   证明是存量（三数与三条 nodeid 逐条相同）。

## 三 请按重要性排序回答的问题

1. **自述 3 的因果论证是否成立？** 「文件 mtime 早于哨兵 ⇒ 该轮未被写」这个推断，
   在什么情况下会不成立？（例如：写入内容相同导致 mtime 不更新？原子替换的语义？
   文件被别的进程持有？）如果不成立，作者「两轮对照实测确认 HIGH-1」的说法就站不住。
2. **自述 4 的两条归因是否成立？** 特别是
   `vault_index_pending__canvas_vault.jsonl` 的 mtime 恰等于跑结束时刻，
   作者据此判为「app 关闭时持久化」。这个推断可靠吗？有没有别的写者也会在那个时刻写它？
   `memory-system-*.log` 判为「health 系 GET 请求期写的日志」是否准确？
3. **排除面是否仍有遗漏**：在你已获授权的读取面内，剩余 **89** 条 GET 里，
   还有没有会在请求期写盘（含写完即删的探针）的？给出 `file:line` 调用链。
4. **`.exclude()` 的链式语义**：文件里连着写了 4 个 `.exclude(path_regex=...)`。
   schemathesis 4.14.3 的这几个 filter 是**累积**的，还是后一个覆盖前一个？
   `collect-after` 显示 4 条都被排掉了 —— 这与你读到的实现一致吗？
5. **验收单的诚实性**：`_bmad-output/验收单/UAT-CARD-HYGIENE-openapi-2026-09-09.md` 里，
   有没有把「未通过的判据」写成通过、把「未证明」写成已证明、
   或把推理包装成实测的地方？请直接指出段落。

## 四 输出格式

对每个发现给出：

- 等级：BLOCKER / HIGH / MEDIUM / LOW
- 位置：`file:line`
- 一句话说明：在什么条件下这个问题会真的发生

按等级从高到低排列。没有发现就明确写「本节无」。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接任何数据库或外部服务，也不要真的发起 HTTP 请求。
- 不评价 `system.py` 的 `vault_path` 校验设计本身，也不评价是否应把合约测试接入 CI。
- 不要求作者再跑一次 5 小时的全量测试（如认为必需，请说明理由与更省的替代做法）。
