<!-- 来源: _bmad-output/审查/zcode-review-CARD-G4-13-r1.md（--json 原文的 response 字段逐字拷贝；本拷贝为可读行号版）
sessionId=sess_6207ac52-3bd0-44d4-a796-28ced3310691 traceId=8da348f0-4049-46d2-aa63-fbc0feffc4e9 turnId=turn_c51fa606-ebd3-4381-8659-0c40201e165c -->

复核完成。以下为 CARD-G4-13 补审 round-1（ZCode × GLM-5.3）的完整结论。

# 总裁定：无 BLOCKER，**2 HIGH / 3 MEDIUM / 6 LOW**

生产侧判分逻辑、金集数据面、冻结 manifest 本身**未发现错误**——我对文本层做了独立复核，全部对上（`  - id:` 计数 75/28/2/0、`user_verdict: pending` 与条数逐文件相等、攻击类 17/3、跨两主集 id 无重复、`kind: fixture` 实指 17/3，裁定清单 103 个 gsid 锚齐全）。两条 HIGH 都是「防护面/证据面」缺陷而非判分缺陷，但按协议 §2.4.2 需停下交主 session 裁定。

---

## HIGH

**H-1　`verify_gold_set_file` 在三类「环境/输入错」上崩溃，把 rc=2 语义档污染成 exit 1（=「指标回退」档）**
- `backend/scripts/gold_set_manifest_tool.py:286`（`load_yaml(manifest_path)` 无 try/except）、`:293`（`sha256_of` 前无 exists 检查）、`:290`（`m.get` 假设 manifest 解析出 dict）。
- **未被拦下的输入**：manifest 带合并冲突标记（`<<<<<<<`，生成文件进 git 后的典型冲突形态）→ 未捕获 `yaml.YAMLError`；或已登记金集文件被删 → `FileNotFoundError`。两个 runner 都是 `sys.exit(main())`（两文件末行），未捕获异常 → traceback + **exit 1**，而两 runner 的文档语义里 exit 1 = 「指标回退」。`verify_all`（CLI `verify`）对同样输入有 try/except 返回 rc=2 + 文案（`:217-234`），但 runner 走的是 `verify_gold_set_file`，没有这层。这直接违反 `rel_to_repo` docstring（`:94-97`）自己立下的「fail-closed 边界必须不崩」契约——负控①~④测过 sha 不符/缺文件/删行/重复键，没测过「manifest 解析错」。

**H-2　行为门⑤（`test_runner_rejects_tampered_gold_set`）声称验「篡改 sha → 拒跑」，实际经「仓外」早退分支通过；manifest 的 monkeypatch 落在 runner 不用的模块实例上（死补丁）**
- `backend/tests/regression/test_gold_set_manifest_g413.py:313-321`。
- 机制：`_import_runner`（:314）先 exec runner，其 `from gold_set_manifest_tool import verify_gold_set_file` 绑定**当时缓存**的模块实例的函数；`_import_tool()`（:315）随后新建**另一个**模块实例并替换 `sys.modules`，:320 的 `monkeypatch.setattr(tool, "MANIFEST_PATH", …)` 补在后者上，对 runner 持有的函数不生效；:321 的 `GOLD_SET_MANIFEST` setattr（raising=False）在 runner 里无此属性，纯无效写。于是 `verify_gold_set_file` 读真 manifest + tmp 金集路径 → tmp 在仓外 → `want is None` 早退（`gold_set_manifest_tool.py:287-289`），**根本没走到 sha 比较**。断言 `rc==2` + 「不符」照样绿（文案恰含「不符」）。
- **门未覆盖的路径**：「已登记 + sha 被改」经 runner 真 `main()` 的拒跑从未被有效测试（负控①验的是 CLI `verify_all` + 测试层 sha 对账；负控②验的是调用存在性——且只注掉了 vault 侧）。修法很小：先 `_import_tool` 再 `_import_runner` 复用同一实例，或 patch `runner.verify_gold_set_file.__globals__`，或把 tmp 副本放进仓内。

## MEDIUM

**M-1　`apply-verdicts` 的 gsid 归属取「最近一个锚」：锚行丢失时，该条勾选会记到上一条头上——错误条目被改、`problems` 空、rc=0**
- `backend/scripts/gold_set_manifest_tool.py:393-409`（`current` 只在遇到下一个 gsid 时前进）。
- **未被拦下的输入**：清单中某行 `<!-- gsid:xxx -->` 被误删（Obsidian 渲染态隐藏 HTML 注释，源码模式误选即删），该条三个勾选全部归给上一条 → 上一条的 `user_verdict/verdict_by/verdict_at` 被写坏且无任何 SKIP。其余 fail-closed 分支（多选 ：403-405 / 非法值 ：421-422 / 未知 id ：431-432）我逐一核过，确实不动该条且 rc=1。

**M-2　`_rewrite_queries_in_place` 会把 queries 段内所有注释抹掉并归一化全文件格式——用户裁定回写（本卡明确的下一步）必然触发**
- `backend/scripts/gold_set_manifest_tool.py:436-442`。safe_dump 重写整个 `queries:` 段：`# ═══ example_recall (6) ═══` 这类分节注释、cross_vault_attack 出处注释块全丢；flow→block、引号重排产生大面积文本 churn。解析层语义不变（门⑥只断言这个），sha 冻结让变更**可见**但没有任何东西**恢复**注释。docstring（:437）只承诺保留文件头注释——如实，但易误读成「注释不受影响」。

**M-3　门⑤对 memory runner「校验先于 `check_backend_alive`」的钉法环境依赖：仅当 8011 恰好 down 时才真正检验顺序；`alive_marker` 是从未使用的死参数**
- `backend/tests/regression/test_gold_set_manifest_g413.py:298-306`。**对照输入**：backend up 的机器上，即便把校验挪到 alive 之后，门仍绿（alive 过 → 校验拒 → 同样 rc=2+「不符」）。UAT A12 的人工离线探针确证过顺序，但自动门未钉死；`alive_marker` 留了控制组的位置没做控制组。修法：monkeypatch `runner.check_backend_alive → lambda: False` 后再断言「不符」仍在。

## LOW

- **L-1**（A1 边界）勾了但读不懂的勾选**静默**跳过：`- [X]` 大写不识别（`gold_set_manifest_tool.py:399`），`verdict:` 锚不匹配 `[a-z_]+` 时 `continue` 无 problem（`:400-402`）。数据面 fail-closed、告警面 fail-silent，rc=0，仅 `changed=N` 计数可察觉。
- **L-2**（A4 边界）文本层重复键判据只认**未加引号**拼写（引号键 `"user_verdict":` 不计数 → 该形态重复键是假绿方向），判分键（query/expect_*）完全不在文本层防护内。现风险低：所有在库生成路径均 safe_dump（结构性不可能产重复键），原缺陷出自不入库的 scratchpad 迁移脚本；`build` 只写 manifest 不会引入，`apply-verdicts` 重写反而结构性消灭之——代价是 M-2。
- **L-3**（A3 边界）`collect` 代码内确无写 vault 路径（只 `read_text`/`glob`，写仅 `out_json`，`:463-511`）；唯一破口是 `--out` 无「不得落在 `--vault` 内」守卫（`:508-509`）。
- **L-4** 门⑥死代码：`marked` 循环整体 no-op（`test_gold_set_manifest_g413.py:358-362`），`text.replace(x, x, 1)`（:363）自替换 no-op。不影响断言，纯混淆。
- **L-5**（B1 残余）per-query `expect_not_hit` 只查 Tier-R top10（`run_vault_retrieval_regression.py:301-315`）：若泄漏行 `source_path` 不在 `双vault验证/` 下（canvas_file 为空、或将来 fixture 改写到别处），Tier-R 配额对此盲，Tier-D 由 `expect_empty`→fp 兜底。
- **L-6**（A2 补注）CLI `verify` 不复核 `totals`/`adjudication` 与文件重算一致（仅测试层兜）；`build_manifest` 在 manifest 被手改 `frozen: false` 后 rebuild 会重置 revision=1 并丢 `revision_history`（`:144-162`）——需先手改生成文件才触发，纯理论。

## §③ 逐问回答（摘要）

- **A1**：未勾条目数据面不会被改（`picks` 只含勾选）；破口 = M-1（归错条目）与 L-1（静默跳过）；多选/非法值/未知 id 三条确实 fail-closed + rc=1。
- **A2**：`verify_all` 三态确实各异（缺失/解析错 rc=2 `:215-234`；sha/计数/版本/字段 rc=1 `:237-257`）；runner 不消费 rc 而消费 bool，统一映射 exit 2 + 文案区分——例外是 H-1 的崩溃输入落成 exit 1。
- **A3**：无写路径可达 `--vault`（见 L-3 的唯一例外）。
- **A4**：修复本身到位（17+3 条 ref 实指 `g29_dual_vault_canary.py:101-111`，我独立 grep 复核 17/3）；判据覆盖边界 = L-2；`build` 不会引入重复键。
- **B1**：**能命中，给对照输入**——canary LanceDB 行 `canvas_file="双vault验证/同名白板.canvas"`（`g29_dual_vault_canary.py:105,:725`）→ `_normalize_material` 原样透传为 `source_path`（`supplementary_search_service.py:989`；`_resolve_chunks_to_source_file` 仅改写 `*/chunks/merged.md` 形态，对此 no-op）→ runner `:307-308` `fnmatch("双vault验证/同名白板.canvas","双vault验证/*")` 命中（fnmatch 的 `*` 跨 `/`），`startswith("双vault验证/")` 双保险；另有 `expect_empty` 在 Tier-D 兜底。残余盲区 = L-5。
- **C1**：12 条门无「注释骗关键词」型结构判据（⑤是行为门）；主要问题 = H-2（行为门走未预期分支）+ M-3 + L-4。未发现恒真断言（①有 `total>=100` 验伪锚、④ git 不可用 skip 不假绿、③明确独立 hashlib 双读）。
- **D1**：顺序属实（memory `:358-363` 先于 `:365`），文案可区分（「金集与 gold_set_manifest.yaml 不符」vs「backend 不可达」），UAT A12 离线实证在档；例外 = H-1（manifest 解析错时既无文案也无 rc=2）。自动门的钉法环境依赖 = M-3。
- **E1**：vault 侧 17 条对 G4-15/R-J04 **可直接消费**（G2-9 实名标识 + glob 与落盘形状吻合 + `expect_empty` 双保险）；memory 侧 3 条仅有 `expect_empty`，无 group/path 级禁止语义（`is_leaked` 的 group_id 分支还依赖 API 回传 group_id，现不回传）。真双 vault 跑还缺四样：① query 侧无 `target_vault`/`forbidden_vault` 字段（`vault_id` 硬编码于 config）；② manifest 不登记 fixture 版本/资产清单，fixture 漂移无锚；③ Neo4j/graphiti 面资产（Concept/User/Entity）不在两个 runner 检索面内，只能经 LanceDB/fact 泄漏间接覆盖；④ `user_verdict` 全 pending，若下游要以裁定后标签为真值需先开裁定 session。

复核过程说明：Bash 的 python/shasum 执行被本车道权限系统拦截，独立复核退化为 grep 文本层（计数/pending/配额/id 唯一性/fixture ref 全对上）；parse 层与 sha 层结论依据 = 门③独立 hashlib 断言 + UAT 存档 + 绑定自证（`d06f7127`→HEAD diff 空）。未修改任何文件，未连接任何端口。