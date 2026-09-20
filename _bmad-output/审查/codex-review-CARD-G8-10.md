> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p6-skills-w · 卡 CARD-G8-10 round-1
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-10.md)" > _bmad-output/审查/codex-review-CARD-G8-10.md 2> _bmad-output/审查/codex-review-CARD-G8-10.stderr </dev/null`（rc=0；2026-09-20 00:43:01 → 2026-09-20 00:52:25 -0700）
> 审查绑定: `7538275c`（各轮时点绑定；amend 血缘与终态见验收单 §八/§九.6）
> 会话头自证（行号按 .stderr 原文）: 第 2 行 `OpenAI Codex v0.153.3` / 第 5 行 `model: glm-5.3` / 第 9 行 `reasoning effort: max`

---

只读核对完成；未改文件、未连接数据库/网络服务。

## BLOCKER

无。

## HIGH

- **HIGH — `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:163`；总账 v2 `_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:556-561`；`backend/app/api/v1/endpoints/review_overview.py:2462-2490`** — 复习链把 G6-7 仅作旁证，但 G6-7 已合入的写路径故障面 `_require_runner()` 会在 runner script 缺失/加载失败时返回 503，且含显式 `"error": "runner_module_unavailable"`，并由 `review_overview.py:2719/2825/2870/2906` 的完成/撤销/推迟端点消费。  
  显形：**对照输入** `git show 93d47028` 可见该面由 CARD-G6-7 引入，当前树 `grep -F runner_module_unavailable` 命中 `review_overview.py:2490`；只查 G6-7 验收单 `degraded` 0 命中不能证明无 `unavailable` 露出。

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:92-99`** — quote 校验只取前 12 个字符，并在“该行任一 `path:line` 引用文件”中全文查找，不解析判据格括号内的出处、不要求全文逐字相等、不要求命中 cited line。  
  显形：**未被拦下的输入** 把文句改成另一条引用文件/底账自述中存在的前缀，或把真实文句标注到同文件错误行，脚本仍可 `failures=0`；现有 `negctl-3` 只把文句改成全仓不存在的“假文句”，没有覆盖“错误归属但别处存在”。

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:64-70,101-106`** — 门只检查“第一表行数 ≥6、第二表行数 ==5、两处 outcome 互相相等”，不检查六链名称、OBJ-07 五项名称、owner 档案节/DONE 规则，也不强制 `not_yet`。  
  显形：**未被拦下的输入** 六行全写“部署链”、五行全写 `CI`、owner 改成不存在的 `G99`，或把汇总行与 YAML 同时改成 `pass`，仍可 rc=0。

## MEDIUM

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:73-86`** — 行号解引用用 `split("\n")` 计数，会在末尾换行文件上把不存在的 `N+1` 空行当成有效行，且只检查 range 末端，不检查 `start <= end`。  
  显形：**负控输入** 对一个物理 N 行且以换行结尾的文件引用 `:N+1`，或把 `:39-45` 改成 `:45-39`，当前门不红。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:71`** — 引用核验循环只遍历 chain rows，不遍历 OBJ-07 子表；chain evidence 中未加反引号的 UAT/archive 路径、以及无 `:line` 形态的机械 nodeid 也不在 `_REF_RE` 覆盖内。  
  显形：**门未覆盖的路径** 把 backup-restore/benchmark/dogfood 的总账 `:line` 改成坏路径，或把 G6-9b/G2-8 UAT 引用改成不存在文件，脚本仍绿。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:87-91`** — skill “无露出”行的跳过条件是 expose 前缀任意位置含“无”，且只要求存在任一总账 v2 引用，不重算 `grep -c -e degraded -e unavailable = 0`。  
  显形：**未被拦下的输入** expose 写成“`foo.py:1-2`、无历史命中（…）”或伪造“全文 0 命中”但保留一个总账 `:line`，该行可绕过文句与零命中核验。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:75-79`** — 脚本直接读取当前 `--root` 工作区，不接受/校验 git ref/SHA，也没有记录被引用源文件 hash；green 结果不能机械绑定到 evidence alias 所称的 `@cb21f1fe` 基线。  
  显形：**门未覆盖的路径** 在源文件后续漂移后原样重跑，只要行数与文句仍在文件任意位置，旧 alias 仍可获得新 green。

## LOW

无。

## 其余独立核对结论

- **⓪ 实际假归属：未发现。** 五个非空判据文句均在受审树引用文件逐字命中：`service_status.py:108`、`review_overview.py:1044`、`deploy-vault.sh:3079`、`vault_lint.py:887`、`traces.py:405-406`；skill 行未伪造成有文句。
- **① 检索链 owner G4-3：无冲突。** G4-3 在总账 v2 `:500` 有档案节且未入 §五 DONE；它同时出现在底账 `:52` 的“故障诚实”owners 中，是跨维度重复担责，不是同一原子判据重复登记。
- **③ DLQ / P6-C 标注：合规。** 底账 `:167` 的 owner、`vault_lint.py:1143` 露出面和 evidence 均显式写明“本车道 P6-C，未合主干 / [车道未合并]”，未把它冒充主干已合证据。
- **④ backup-restore：如实。** 底账 `:175` 写“无机械判据，只指认”与当前无已合入机械产物一致；G8-5 总账 `:710-715` 已是未来备份恢复验收 owner，不需要为满足本纯台账卡而伪造一条附加判据。
- **outcome / YAML / 预留行：实际内容一致。** `:158` 与 `:244` 均为 `not_yet`，coverage 为 partial，known gaps 未写成达成；“预留行”仅 `:19`、`:154`、`:263` 三处历史/标题提法。
