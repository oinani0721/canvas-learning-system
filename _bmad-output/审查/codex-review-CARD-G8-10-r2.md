> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p6-skills-w · 卡 CARD-G8-10 round-2
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r2.md)" > _bmad-output/审查/codex-review-CARD-G8-10-r2.md 2> _bmad-output/审查/codex-review-CARD-G8-10-r2.stderr </dev/null`（rc=0；2026-09-20 01:01:26 → 2026-09-20 01:21:03 -0700）
> 审查绑定: `3f32e861`（各轮时点绑定；amend 血缘与终态见验收单 §八/§九.6）
> 会话头自证（行号按 .stderr 原文）: 第 2 行 `OpenAI Codex v0.153.3` / 第 5 行 `model: glm-5.3` / 第 9 行 `reasoning effort: max`

---

只读审查完成：未改动文件、未连接数据库、未访问网络服务。当前 `HEAD = 3f32e861c6aa8a9f7a454adf324cbf57ee236f5e`，底账 sha256 复算为 `1d3fda04aa67d22711e817a1f85dd2778ad3d8bd8c5e6ca9a8c7de9b632221f5`；`cb21f1fe..3f32e861` 仅改底账，`7538275c..3f32e861` 的底账增量确为 1 行。核对脚本当前实跑结果为 `chains=6 obj07=5 failures=0 source_digest=3a37757b6ddabe27`，与 green 存档一致。

## BLOCKER

无。

## HIGH

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:179-182`；底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:11` / `:158` / `:244`** — `yaml-overclaim` 把「缺口处置列为 `—` / `-` / 空」当作唯一闭环信号，仍允许把登记性缺口直接擦掉后双双改成 `pass`，这不满足 §1 的「pass = candidate SHA 上有完整证据」。  
  显形：**未被拦下的输入**——在内存中将第 1、4 链的缺口格改为 `—`，并把 §2.13 summary 与 YAML outcome 均改为 `pass`，脚本返回 `rc=0`（实测 `chains=6 obj07=5 failures=0`）；说明“无未闭环登记”只是同表自证，不是证据闭环。

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:145-150`；底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:160-167`** — `owner-invalid` 只检查 owner cell 中「反引号包裹且完整匹配 ID regex」的 token，未反引号的伪 owner、链接形态 owner 或空 owner 均可绕过，r1 H3 的 owner 失败面没有真正闭环。  
  显形：**未被拦下的输入**——把首行 owner 从 `` `G4-3` `` 改成不带反引号的 `G99`，其余不动，脚本实测仍 `rc=0`；当前台账本身 owner 合格，但门的 claimed coverage 大于实际 coverage。

## MEDIUM

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:23` / `:71-82`；底账 `:162-167`** — `_REF_RE` 不识别 `、:108-109` 这类延续行号引用，表中第二及以后的相对 `:line` 显示项没有被解引用校验。  
  显形：**未被拦下的输入**——把检索链的 `、`:108-109`` 改成 `、`:999-999`` 或不存在文件的相对行号，脚本实测仍 `rc=0`；因此“引用核验覆盖两张表全部行”不能理解为覆盖全部显示引用。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:136-138`；底账 `:162-167`** — 机械判据 nodeid、裸 evidence SHA、无行号 archive 目录均不在 `_REF_RE` / owner / quote 检查内，脚本不验证测试存在或 commit 可解。  
  显形：**未被拦下的输入**——把 `G6-9b 4293abb1` 改成不存在的 `4293ffff`，或把任一 pytest nodeid 改名，脚本实测仍 `rc=0`；当前 nodeid/SHA 人工核对为真，但这是收集存档承担的证明，不是脚本九类失败面承担的证明。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:85-109`** — quote 有显式 `（path:line）` 时校验有效，但缺少显式出处时会回退到“该行任一引用区间命中”，没有强制每条 quote 必须携带自己的出处，r1 H2 的错误归属面只被部分收紧。  
  显形：**未被拦下的输入**——删除某条 quote 后紧邻的出处括号，但保留同一文件的露出面行区间，脚本仍可通过另一引用命中而 `rc=0`；当前六链实际出处均正确，但门的出处纪律仍可被结构改写绕开。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:173-184`；底账 `:11` / `:158` / `:244`** — 脚本只比较 summary/YAML outcome 字符串，不验证 outcome 三态枚举、coverage 三态枚举或 summary/YAML coverage 一致性。  
  显形：**未被拦下的输入**——把两处 outcome 同时改成 `banana`，脚本实测 `rc=0`；把 YAML coverage 改成 `complete` 也不会失败，仍与 §1 的枚举纪律不一致。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:64-68` / `:187-188`；底账 `:265-266`** — `source_digest` 只是打印当前引用文件组合摘要，没有 expected digest 参数、没有 git ref/SHA pin，也没有把核对脚本自身纳入绑定；且 `read_text + splitlines + "\n".join` 会规范化换行，不是严格字节级内容绑定。  
  显形：**对照输入**——源文件漂移但引用行与 quote 仍存在时，脚本仍 `rc=0`，只是 digest 变化；若没有人机械比对 `3a37757b6ddabe27`，`@cb21f1fe` 别名仍不能由脚本自身强制锁定。

- **MEDIUM — 底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:163`；`backend/app/api/v1/endpoints/review_app.py:582-592`；`backend/tests/unit/test_review_app.py:2674-2688`** — 若“露出面”按用户可见故障理解，复习链只登记了 `_require_runner()` 后端 503 面，漏掉同一 CARD-G6-7 commit `93d47028` 已合入的用户可见 503 渲染面。  
  显形：**对照输入**——`git blame` 显示 `review_app.py:582-592` 与 `test_review_app.py:2674-2688` 均来自 `93d47028`，测试断言 `标记失败 / 503 / 脚本不可达`；若该表不追求穷尽 UI 面，应在行内显式缩小为“后端契约面”，否则应补记。

## LOW

- **LOW — `_bmad-output/审查/evidence-g810/check_g810_refs.py:125-135`** — 链表只要求行数 `>=6` 且六链名集合存在，不禁止额外第七链或重复链行；OBJ 子表反而是 exact 5。  
  显形：**未被拦下的输入**——追加一行“人工链/重复检索链”，六链名仍全存在，脚本仍可 `rc=0`。

- **LOW — `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:265-266`；`_bmad-output/审查/evidence-g810/check_g810_refs.py:1-13`** — r2 绑定的 `3f32e861` 只包含底账修复；核对脚本 v2、green/negative evidence 与审查文件仍是工作区未跟踪，轮次闭合若依赖脚本，最终还必须绑定后续 commit ② 的脚本内容与 hash。  
  显形：**门未覆盖的路径**——`git status --short` 显示 `_bmad-output/审查/evidence-g810/` 未跟踪；`3f32e861` 本身不能复现脚本版本，除非 commit ② 收口时再登记脚本 SHA。

- **LOW — `_bmad-output/审查/evidence-g810/check_g810_refs.py:173-178`** — summary outcome 取 §2.13 block 中第一处 `outcome=`，若未来在真实汇总行前新增含该 token 的说明行，会比较错对象。  
  显形：**未被拦下的输入**——在 `:158` 前插入一行 `outcome=not_yet`，再把真实 summary/YAML 改成不一致值，当前选择逻辑可能指向插入行。

## 逐项独立核对结论

### ⓪ 六链判据文句是否假归属

**当前内容未发现假归属。** 逐字核对结果：

| 链 | 结论 |
|---|---|
| 检索链 | `ServiceStatus.UNAVAILABLE must carry an empty items payload` 逐字命中 `backend/app/models/service_status.py:108`；两个 nodeid 均存在。 |
| 复习链 | `review_overview.py:1044` 与新增 `:2463` 两句均逐字命中；`test_review_overview.py:3248` 存在，且确实只测 `runner_script_not_found`，底账已如实说明 `runner_module_unavailable` 无专属门。 |
| 部署链 | `每阶段一行 stage=… rc= …` 判据逐字命中 `scripts/deploy-vault.sh:3079`；测试 nodeid 存在。 |
| skill 链 | `inbox_preview.py` 实际 2479 行，`degraded|unavailable` 命中数为 0；该行没有伪造 quote。 |
| 投影 freshness | mapped 字典判据逐字命中 `backend/scripts/vault_lint.py:887`；两个 freshness 测试存在。 |
| DLQ 链 | `traces.py:405-406` 两句逐字命中；`traces_backlog_t6c` 两条与 `vault_lint` 两条 DLQ 测试均存在。 |

owner 方面，当前引用的正式卡均有 `#### <id>` 档案节，且不在总账 v2 §五 DONE 的行首；OBJ-07 五项名称集也正好是 `CI / observability / backup-restore / benchmark / dogfood`。

### ① 复习链补记后，其它五链是否漏计已合入故障露出

按本卡“每链至少一个具体判据文句”的标准，其它五链当前没有发现假归属或明显漏掉标准化 `degraded/unavailable` 主面：

- 检索链的 UI 半边没有冒充已覆盖，而是明确登记为 G4-3 缺口。
- skill 链明确登记“无 standardized 露出”，并挂 G5-7。
- 部署、freshness、DLQ 各有具体后端/脚本面与机械判据。
- 但若把“露出面”理解为穷尽用户可见面，则上面 MEDIUM 中列出的 G6-7 `review_app.py` 503 渲染面仍是一个已合入但未登记的补充面。

### ② 脚本 v2 九类失败面之外的恒绿面

主要恒绿面已列入 HIGH/MEDIUM：gap 擦除后 `pass` 可绿、无反引号 owner 可绕过、相对行号引用不核、evidence SHA/nodeid 不核、quote 缺出处时回退任一引用、outcome/coverage 枚举不核、digest 不强制比对。  
因此我认为 **r1 H2/H3 有实质改善，但不能宣称完全闭环**；尤其 owner-invalid 与 yaml-overclaim 仍各自存在一枚简单输入可绕过。

### ③ DLQ `[车道未合并]` 是否如实

**如实。** 本地 refs 中 `3f32e861` 与 `cb21f1fe` 只被当前 `card/p6-skills-w` 包含，未被本地 integration/main refs 包含；DLQ 相关改动是当前车道态。未访问远端网络，所以这是本地 Git 对象证据下的结论。底账 `:167` 同时在 owner、露出面、evidence 三处标明 P6-C / lane 未合并，没有冒充主干已合证据。

### ④ `yaml-overclaim` 语义是否与 §1 / §3 一致

**只部分一致。** 它能拦住“YAML 改 `pass` 但表内仍留着两行开放缺口”的 r1 场景；但 §1 的 `pass` 要求完整证据，而脚本把 `—` / `-` / 空当作闭环，不验证缺口处置背后的测试、证据或 candidate SHA。因此它是必要的一致性检查，不是充分的 pass 门。当前 `not_yet / partial` 台账本身是如实的。

### ⑤ 其它核对

- H1 的底账修复本身到位：`7538275c..3f32e861` 只有复习链一行增量，新增 `:2462-2490`、`:2463` quote、`:3248` nodeid 与 evidence 口径修正均在。
- green digest 复算一致；三段负控存档内部显示 expected 红项、原底账 sha 前后一致、还原后 rc=0。`negctl-2` 除 `yaml-mismatch` 外同时触发 `yaml-overclaim`，这是一次 mutation 的合理联动，不构成虚假负控。
- `vault-lint` open/close 存档均为 112 passed；全量 `tests/unit` open/close 存档本身是 rc=1（32/33 failed），其差异在验收材料中按既有 flaky 处理。本次没有把该既有失败归因于本零代码卡。
- 当前底账的 `not_yet / partial`、两项缺口、G4-3/G5-7 附加判据提名没有冒充达成。
