> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p6-skills-w · 卡 CARD-G8-10 round-3
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r3.md)" > _bmad-output/审查/codex-review-CARD-G8-10-r3.md 2> _bmad-output/审查/codex-review-CARD-G8-10-r3.stderr </dev/null`（rc=0；2026-09-20 01:35:05 → 2026-09-20 01:50:29 -0700）
> 审查绑定: `6624a1b4`（各轮时点绑定；amend 血缘与终态见验收单 §八/§九.6）
> 会话头自证（行号按 .stderr 原文）: 第 2 行 `OpenAI Codex v0.153.3` / 第 5 行 `model: glm-5.3` / 第 9 行 `reasoning effort: max`

---

只读审查完成：未改动文件、未连接数据库、未访问网络服务。当前 `HEAD = 6624a1b4`；`cb21f1fe..6624a1b4` 仅改底账一个被跟踪文件；核对脚本与证据仍在工作区未跟踪。

## BLOCKER

无。

## HIGH

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:237-248`；底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:11` / `:158` / `:187` / `:244`** — r2-H1 的 candidate-SHA 收紧仍只证明 summary 里 8–40 位 hex 能被本地 Git 解析，不证明它是 commit、不证明它是本表 candidate、也不把任何引用、文句、nodeid 或测试绑定到该 SHA。  
  显形：**未被拦下的输入**——把两处 outcome 改 `pass`、擦掉两格缺口，并在 summary 写 `candidate SHA: 0ab10703`；本地 `git cat-file -t 0ab10703` 返回 `blob` 而非 `commit`，但脚本只看 returncode，且所有源文件检查仍读工作区而非 candidate 树，应仍可绿。

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:31` / `:189-196`；底账 `:160-167`** — r2-H2 的 owner 整改仍没有“非空 owner”约束、没有链名→owner 允许集，任何非 ID grammar 的伪 owner、空 owner、或有效但归属错误的正式卡都可绕过。  
  显形：**未被拦下的输入**——把检索链 owner 从 `G4-3` 改成同样存在档案节的 `G8-2`，或改成 `张三` / 空 cell；`G8-2` 会通过档案节检查，`张三` / 空 cell 则不进入 `_ID_RE.findall`，均无 `owner-invalid`。

## MEDIUM

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:122-141`** — nodeid 只做全文件静态 `def/class name` 子串搜索，不限制测试路径、不校验唯一性/可运行性/断言内容，也不要求每条非 skill 链必须存在 nodeid。  
  显形：**未被拦下的输入**——把机械判据 cell 改成纯文本“人工复核”使 `.py::` token 消失，或让 token 指向任一含有注释 `# def test_x` / 同名非测试函数的文件；`nodeid-missing` 不会触发。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:32` / `:176-185` / `:241-248`** — SHA 覆盖边界是“§2.13 块内、反引号包裹、恰好 8 位小写 hex、任一 Git object 可解”，不验证 commit 类型、完整 SHA、candidate 祖先关系、主干包含关系或与证据内容的绑定。  
  显形：**未被拦下的输入**——把任一 evidence SHA 改成本地 blob 短 SHA `0ab10703` 可通过，改成 9 位或 40 位伪造 hex 则根本不进入 `_SHA_RE` 扫描。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:100` / `:251-254`；`g810-green-v31-20260920T013134.txt:1`** — `source_digest` 只绑定 `_check_refs` 收集的引用源文件字节与脚本自身，不绑定底账、nodeid 测试文件、证据存档、Git HEAD / candidate / clean tree，且 `--expect-digest` 是可选参数、green 输出也不记录调用参数。  
  显形：**对照输入**——把 `backend/tests/unit/test_review_app.py:2674-2688` 改成同名空测试或删除关键断言，或省略 `--expect-digest` 重跑；nodeid 静态检查仍命中同名函数，测试文件不进 `used`，digest 仍可保持 `ee045b4872d4bb0f`。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:28-29` / `:103-119`** — quote 校验是“引用串是出处行区间任一行的子串”，不是整句/整行等值比对，也不限制出处必须是对应生产源文件而非底账自身。  
  显形：**未被拦下的输入**——把判据文句缩短为 `ServiceStatus`，或把出处改为包含同一句的底账 `file:line`；二者仍满足 `q in ln`，假归属不会被拦下。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:197-218`** — `expose.startswith("**无**")` 的免 quote 分支不校验链名是否为 `skill 链`，且 `:0-0` 这类非正行号可过 `_check_refs`。  
  显形：**未被拦下的输入**——把部署链 expose 改成 `**无**`，在行内保留 `_PREVIEW_REL:0-0` 与总账 v2 引用并删除 quote；控制流会按“无露出”分支跳过 quote 必需检查。

## LOW

- **LOW — 底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:167`** — DLQ 两句 `traces.py:405-406` 的主干引入者是 `b8c6e4922`（CARD-NEO4J-REPLAY-BOUND），而 evidence 列只显式列出当前 G8-3 lane 的 `evidence-g83/`，历史 provenance 低引。  
  显形：**对照输入**——`git blame cb21f1fe -L 405,407 -- backend/app/api/v1/endpoints/traces.py` 指向 `b8c6e4922`，而 G8-3 当前 lane 的 `vault_lint.py:1143` 指向 `2b298383`；读者易把前者的主干文句误读为后者交付。

- **LOW — `_bmad-output/审查/evidence-g810/check_g810_refs.py:1`；commit `6624a1b4`** — r3 受审 commit 本身不包含核对脚本，当前轮次闭合只能依赖后续 commit ② 的承诺登记脚本 SHA。  
  显形：**门未覆盖的路径**——`git ls-tree -r --name-only 6624a1b4` 中没有 `evidence-g810/check_g810_refs.py`；在 commit ② 入库前，`6624a1b4` 不能独立复现 v3.1 检查器字节。

## 逐项独立核对

### ⓪ 六链「判据文句」有无假归属

**当前台账内容未发现假归属；但这是人工 Git/文本核对结论，不是脚本可靠性结论。**

| 链 | 独立核对 |
|---|---|
| 检索链 | `ServiceStatus.UNAVAILABLE must carry an empty items payload` 在当前与本地主干 ref 的 `service_status.py:108` 逐字命中；引入 commit 为 `9960b146`（G4-2），行内同时列 G4-2 证据并把 UI 缺口挂 G4-3，未把 G4-2 文句冒充 G4-3 交付。 |
| 复习链 | `review_overview.py:1044` 与 `:2463` 两句均逐字命中；`review_app.py:582-592` 确为用户可见失败渲染，`test_review_app.py:2674-2688` 确断言 `标记失败`、`503`、`脚本不可达` 且禁止成功文案。 |
| 部署链 | `每阶段一行 stage=… rc=…` 判据在 `deploy-vault.sh:3079` 逐字命中，引入 commit `db20ca7b` 与行内 G2-8 一致。 |
| skill 链 | `inbox_preview.py` 全文 `degraded|unavailable` 计数为 0；台账没有伪造文句，而是显式登记无露出并挂 G5-7 缺口。 |
| 投影 freshness | 当前 lane 为 `vault_lint.py:887`，本地主干 ref 为 `:882`；台账已显式登记 +5 漂移，mapped 判据逐字存在，归属 G8-2/G8-2b 合理。 |
| DLQ 链 | 两句英文判据在当前与本地主干 ref 的 `traces.py:405-406` 逐字命中；当前 lane 的 `vault_lint.py:1143` 也确实存在。仅有上方 LOW 的历史 provenance 低引问题。 |

“主干”结论基于本地 `worktree-feature-obsidian-hybrid-dev` / remote-tracking ref，不访问远端；未验证远端现势。

### ① r2 两条 HIGH 是否闭环

- **r2-H1：未闭环。** 新增检查只拦“完全没有 candidate SHA”，没有拦“任意 blob / 无关 commit / 非 candidate 树”。它也没有把 `_check_refs`、quote、nodeid、测试收集或 digest 绑定到 candidate。
- **r2-H2：未闭环。** `G99` 这类符合 ID grammar 的伪 owner 已被拦，但空 owner、自然语言伪 owner、有效但错误归属的正式卡仍绿。当前六行 owner 本身合格，但门的 claimed coverage 仍大于实际。

旧失败面代码检查上确实“只增不减”：`ref-missing`、`quote-miss`、`yaml-mismatch`、`chain-missing`、`obj-set`、`owner-invalid`、`yaml-overclaim`、`expose-overclaim` 路径仍在。

### ② v3.1 失败面之外的恒绿面

重点是：

1. **nodeid 可同名伪造 / 直接缺失**：静态 regex 不区分测试函数、生产函数、注释或字符串；测试文件也不进 digest。
2. **SHA 覆盖窄且弱**：只认块内反引号 8 位 hex；可解 object 即过，不验 commit / ancestry / candidate。
3. **digest 绑定强度不足**：引用源文件与脚本有字节 hash，但底账、测试文件、证据包、HEAD、candidate、clean status 均不在锚内；expected 参数也不体现在 green 输出中。
4. **quote 可自证**：任意路径 + 子串命中即可，包括引用底账自身。
5. **`expose=无` 分支可被非 skill 行复用**，且 `:0-0` 可绕过正行号语义。

### ③ 底账新增内容是否如实

**如实。**

- `review_app.py:582-592` 的 `renderBoardDoneResult` 对非 200 返回 `❌ 标记失败（HTTP …）`，并拼接后端 `detail.message`。
- `test_review_app.py:2674-2688` 明确注入 503 / `runner_script_not_found` / `脚本不可达`，断言失败渲染且禁止 `已标记` 成功文案。
- 复习链同时保留 `runner_module_unavailable` 无专属门的如实声明。
- 当前 quote 出处、skill 0 命中、检索 UI 半边缺口、skill 缺口均未冒充达成；`outcome=not_yet / coverage=partial` 与两处开放缺口一致。

### ④ `yaml-overclaim` 与 §1 语义

**只与 §1 的一个必要条件弱一致，不满足“pass = candidate SHA 上有完整证据”的完整语义。**

残余自证面：

- candidate 可为 blob / 无关 object；
- meta `candidate_sha` 可仍为 null；
- 源文句与 refs 从工作区读，不从 candidate `git show`；
- nodeid 可缺失、可同名伪造、测试可空体且不影响 digest；
- 缺口仍只是以 `—` / `-` / 空 cell 表示闭环；
- skill / 伪造 `expose=无` 行可在无判据文句情况下进入 pass 路径；
- `pass + coverage=partial` 不触发失败。

### ⑤ 其它核对

- **amend 血缘如实**：`7538275c`、`3f32e861`、`6624a1b4` 的 parent 均为 `cb21f1fe`，作者时间相同、committer 时间递增，符合三轮 amend 描述；三对象均在本地库。
- **改动面如实**：`cb21f1fe..6624a1b4` 仅底账一个文件；当前 tracked 代码无改动。
- **负控与 green 存档**：指定红项、`source_digest=ee045b4872d4bb0f`、脚本 sha 前后一致的文字均在档；但输出不含 HEAD / ledger blob / clean-tree 状态，所以“终态 HEAD 重跑”只能由时间顺序与本地状态强支持，不能由存档自身强绑定。
- **后续收口条件**：commit ② 必须实际入库脚本并登记字节 SHA；若修复上述 HIGH，`--expect-digest` 也应随脚本与规则变化重新锚定。
