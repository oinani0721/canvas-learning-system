结论先行：B3 / H1 / H2 / H3 / H4 的指定缺陷均为 `CONFIRMED-CLOSED`；但当前字节仍存在 3 条真实 CLI 可达的破坏性删除路径，因此不能判定 BLOCKER/HIGH 清零。

隔离副本与原件 `cmp=0`，被测脚本 SHA-256 均为 `7ffe3532f6a592000e96233b4c2b2bcbb5f1e4549bbc8579afcbb8bf3bb4b3de`；裁判均为 `8da71e92b093ff672a709f248efcf47d47984a28f5298f6bd7a41e7cb41fae92`。完整裁判独立运行结果为 `73 passed in 4.17s`，但未覆盖下述 3 条新反例。

## 一、五条逐条判定

### B3 围栏关闭长度与字符规则 — CONFIRMED-CLOSED

- 位置：[inbox_preview.py:496](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:496)、[inbox_preview.py:536](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:536)

- 输入：

~~~text
````
```
# keep
````
~~~

- 复现命令：

```bash
python3 -B /private/tmp/card-g56b-final-audit.ZC4lfi/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault /private/tmp/card-g56b-final-audit.ZC4lfi/cases/B3/vault --now 2026-09-01T00:00:00+08:00 --out-dir /private/tmp/card-g56b-final-audit.ZC4lfi/cases/B3/out
```

- 实际输出：

```text
本批 1 件 · 拿不准 1 件 · 建议删 0 件
{"name":"四反引号.md","criterion":"C6_undecided","verdict":"拿不准","nomination_type":null,"target_hint":null,"basis":"无机械判据可施加","confident":false}
```

- 结论：三反引号不再关闭四反引号围栏，`# keep` 保留为代码正文。指定 B3 已闭合。

### H1 URL host 非空 — CONFIRMED-CLOSED

- 位置：[inbox_preview.py:360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:360)、[inbox_preview.py:363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:363)、[inbox_preview.py:941](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:941)

- 反例：`source: https://:443/x`、`source: https://user@/x`。

- 复现命令：

```bash
python3 -B /private/tmp/card-g56b-final-audit.ZC4lfi/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault /private/tmp/card-g56b-final-audit.ZC4lfi/cases/H1/vault --now 2026-09-01T00:00:00+08:00 --out-dir /private/tmp/card-g56b-final-audit.ZC4lfi/cases/H1/out
```

- 实际输出：

```text
本批 2 件 · 拿不准 2 件 · 建议删 0 件
空host用户.md: C6_undecided / 拿不准 / type=null / target=null / confident=false
空host端口.md: C6_undecided / 拿不准 / type=null / target=null / confident=false
```

- 结论：两种空 host 均不再产出 C1、确定去向或 `confident=true`。

### H2 裸词与右边界 — CONFIRMED-CLOSED

- 位置：[inbox_preview.py:246](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:246)、[inbox_preview.py:662](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:662)、[inbox_preview.py:685](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:685)

- 复现命令：

```bash
python3 -B /private/tmp/card-g56b-final-audit.ZC4lfi/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault /private/tmp/card-g56b-final-audit.ZC4lfi/cases/H2/vault --now 2026-09-01T00:00:00+08:00 --out-dir /private/tmp/card-g56b-final-audit.ZC4lfi/cases/H2/out
```

- 实际输出：

```text
本批 3 件 · 拿不准 3 件 · 建议删 0 件
版权话题.md:     C6_undecided / 拿不准 / confident=false
由字版权话题.md: C6_undecided / 拿不准 / confident=false
评测话题.md:     C6_undecided / 拿不准 / confident=false
```

三件的 `nomination_type`、`target_hint` 均为 `null`。

- 结论：指定三个话题提及均不再命中 C2。裸词已删除，右边界生效。

### H3 正文 URL 不得冒充 frontmatter 键 — CONFIRMED-CLOSED

- 位置：[inbox_preview.py:350](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:350)、[inbox_preview.py:352](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:352)、[inbox_preview.py:443](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:443)

- 输入：`"---\nhttp://example.com/path\n---\n"`。

- 复现命令：

```bash
python3 -B /private/tmp/card-g56b-final-audit.ZC4lfi/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault /private/tmp/card-g56b-final-audit.ZC4lfi/cases/H3/vault --now 2026-09-01T00:00:00+08:00 --out-dir /private/tmp/card-g56b-final-audit.ZC4lfi/cases/H3/out
```

- 实际输出：

```text
本批 1 件 · 拿不准 1 件 · 建议删 0 件
{"name":"裸URL行.md","criterion":"C6_undecided","verdict":"拿不准","basis":"无机械判据可施加","confident":false}
```

- 结论：URL 行保留为正文，没有再产出 C3 或“其余皆空行”的假依据。

### H4 人读 MD 不得钦定正本 — CONFIRMED-CLOSED

- 位置：[inbox_preview.py:1079](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1079)、[inbox_preview.py:1538](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1538)

- 复现命令：

```bash
python3 -B /private/tmp/card-g56b-final-audit.ZC4lfi/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault /private/tmp/card-g56b-final-audit.ZC4lfi/cases/H4/vault --now 2026-09-01T00:00:00+08:00 --out-dir /private/tmp/card-g56b-final-audit.ZC4lfi/cases/H4/out
```

- 实际 JSON：

```text
criterion=C4_exact_duplicate
exact_duplicate_of=归档/乙本.md
exact_duplicate_others=["节点/甲本.md"]
basis=库内已有 2 份正文逐字相同的文件……哪一份算「正本」不可判……
```

- 实际 MD §四：

```text
- **第三份.md** · 与库内 2 份文件逐字相同：归档/乙本.md、节点/甲本.md —— 哪一份是正本不可判（exact_duplicate_of 仅为字典序代表）
```

- 结论：JSON 与 MD 语义一致，两个候选均完整呈现，原 H4 已闭合。

## 二、新回归

### BLOCKER-1：自然英文肯定式 AI 声明穿透 C2 与护栏，落 C3 确定删除

- 位置：[inbox_preview.py:246](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:246)、[inbox_preview.py:703](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:703)、[inbox_preview.py:1012](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1012)、[inbox_preview.py:1019](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1019)

- 输入 SHA-256：`ee52afe3d0a1918d73efb520b0f6c6509424bd86681ac97bc2ea01dcbc28567b`

```yaml
---
generator: This report was generated by an AI system
---
```

- 真实 CLI：

```bash
python3 -B /private/tmp/card-g56b-final-audit.ZC4lfi/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault /private/tmp/card-g56b-final-audit.ZC4lfi/clean-blockers/natural/vault --now 2026-09-01T00:00:00+08:00 --out-dir /private/tmp/card-g56b-final-audit.ZC4lfi/clean-blockers/natural/out
```

- 逐字 stdout 尾行：

```text
本批 1 件 · 拿不准 0 件 · 建议删 1 件
```

- JSON：

```text
{"name":"自然英文AI.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","nomination_type":null,"target_hint":null,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（61 字节文件：标题 0 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）","confident":true,"uncertain_reason":null}
```

`find_ai_marker()` 与 `raw_ai_marker()` 共用有限表；不含表中字面量的肯定式声明，两层同时失明。它不是语义否定或话题提及，且确实产生破坏性提名，因此不属于题目豁免的原理上限。

### BLOCKER-2：Markdown autolink 形态的 URL 别名未进入来源护栏

- 位置：[inbox_preview.py:968](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:968)、[inbox_preview.py:974](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:974)、[inbox_preview.py:981](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:981)

- 输入 SHA-256：`d07b4da9b96f0c011b5e5746cbc16bee525e84ff134a0c50304e681e6e218c77`

```yaml
---
URL: <https://example.test/x>
---
```

- 真实 CLI：

```bash
python3 -B /private/tmp/card-g56b-final-audit.ZC4lfi/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault /private/tmp/card-g56b-final-audit.ZC4lfi/clean-blockers/url/vault --now 2026-09-01T00:00:00+08:00 --out-dir /private/tmp/card-g56b-final-audit.ZC4lfi/clean-blockers/url/out
```

- 实际输出：

```text
本批 1 件 · 拿不准 0 件 · 建议删 1 件
{"name":"URL别名角括号.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"uncertain_reason":null}
```

`_looks_like_source_value()` 只接受剥空白后直接以 `http://` 或 `https://` 开头，角括号包裹的来源完全绕过护栏。我还重放了相同元数据加重复正文的形态：它进入 C4、同样 `建议删/confident=true`；即两个删除出口均可达。

### BLOCKER-3：含反引号的 backtick info string 被误认成合法开启围栏

- 位置：[inbox_preview.py:343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:343)、[inbox_preview.py:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:521)、[inbox_preview.py:524](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:524)

- 输入 SHA-256：`558ee8d723e3e5ec358386f7ba8712459c9fb0a2c0b8a0da44cc7c370f65dfa3`

~~~text
```foo`bar
```
# keep
~~~

- 真实 CLI：

```bash
python3 -B /private/tmp/card-g56b-final-audit.ZC4lfi/tree/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py --vault /private/tmp/card-g56b-final-audit.ZC4lfi/regressions/B3BADOPEN/vault --now 2026-09-01T00:00:00+08:00 --out-dir /private/tmp/card-g56b-final-audit.ZC4lfi/regressions/B3BADOPEN/out
```

- 实际输出：

```text
本批 1 件 · 拿不准 0 件 · 建议删 1 件
{"name":"反引号info含反引号.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（22 字节文件：标题 1 行、纯结构行 0 行、代码围栏 2 行、其余皆空行或注释）","confident":true,"uncertain_reason":null}
```

反引号围栏的 info string 含反引号时不能作为该围栏的合法开启行；当前 `_FENCE_RE` 未检查 rest，导致第一行开启、第二行关闭、`# keep` 又被剥成标题。这是同一区域的残余破坏性缺口；本轮 diff 是否新引入无法从当前证据证明，但终态确实可达。

### 其余重点交叉面

- H2 存量正例通过：
  - `> 本文由 Deep Research 生成` → C2，target=`deep research 报告/`；
  - `R99_深度调研.md` 内 `由 AI 生成` → C2，target=`R99/`；
  - `本文由 AI 生成` 仍由 `由 AI 生成` 覆盖。
- 题目所称仍留在表中的 `本文由 AI`、`本报告由 AI` 实际已删除；当前以 ASCII `AI` 收尾的核心标记是 `Generated by AI`。行尾/标点命中，后接空格单词不命中。
- `Generated by AI Lab researchers` 与 `Generated by AI on 2026…` 均落 C6；后者有召回损失但方向安全。
- 已知原理上限实测仍在：`这不是由 AI 生成`、`由 AI 生成，这个话题很热` 均命中 C2。按题目要求只登记，不计新缺陷。
- H3 两条键正则现在均允许冒号前空白，不存在题目所疑的当前口径不一致。`tags:`、时间戳、引号值、tab 分隔、`title : x` 均解析正常；引号 source、tab source 进入 C1，纯空骨架仍 C3。
- B3 合法关闭对照通过：等长/更长、0–3 空格缩进、ASCII 空格或 tab 尾随、tilde 围栏均能正常关闭；短关闭、异字符、NBSP 尾随及关闭行带 info string 不会提前关闭。
- H1 合法 IPv6、大写 scheme、Unicode IDN、punycode、localhost 均进入 C1。
- H4 三候选实测 JSON 与 MD 均完整列出 A/B/C 三条路径并声明不可判。
- 既有护栏对照通过：坏 source、未解析 frontmatter、未闭合注释、现表 AI 嫌疑、损坏裸 URL 别名、`slept_at` 均为 C6；无信号纯骨架与闭合注释骨架仍为 C3。例外即上述 BLOCKER-1/2。

## 三、门强度

### 字节码门确实承重

- 实现：[inbox_preview.py:169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:169)、[inbox_preview.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:186)
- 裁判：[test_g5_6_clear_inbox.py:692](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:692)

基线副本门：

```text
1 passed in 0.18s
```

仅删除副本内 `sys.dont_write_bytecode = True` 后：

```text
AssertionError: 运行/导入在副本树落下了字节码缓存: [PosixPath('board-split/scripts/__pycache__')]
FAILED ...::test_no_bytecode_cache_written_into_vault_skills
1 failed in 0.20s
```

结论：tmp 隔离没有削弱该门，且不再删除 checkout 内既有缓存。

### 八道门与 M1–M6

| 门 | 裁判位置 | 指定变异 |
|---|---:|---|
| B3 close | 1130–1177 | M1 |
| H1 hostname | 1180–1215 | M2 |
| H2 boundary | 1218–1297 | M4 |
| H2 table | 1300–1308 | M3 |
| H3 bare URL | 1311–1330 | M5 |
| H3 span | 1333–1340 | 无 |
| H3 no-space | 1343–1355 | 无 |
| H4 MD | 1358–1381 | M6 |

变异输出的前六行只证明前六个指定节点被杀；`24/24 killed` 不能替代后两门的指定变异证据。

我对两个遗漏门另做独立变异：

- 放宽 `_FM_LOOKS_LIKE_KEY_RE` 后，span 门精确失败：`assert 3 == 0`；
- 同时放宽 LOOKS/KEY 后，no-space 门精确失败：`'C1_source_url' == 'C6_undecided'`。

因此两门不是空转，但变异矩阵记载不完整，登记 LOW。

### 否定断言与假绿面

- H2 表锁门 [test_g5_6_clear_inbox.py:1300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:1300) 全是 `not in`。把 `AI_MARKERS=()` 后，该单门仍 `1 passed`；正例交叉门会失败。单门不自足，LOW/PARTIAL。
- no-space 门只锁 `criterion/verdict`；临时让 C6 同时输出 `confident=true`、强制 type/target，该门仍通过。B3 与裸 URL 的路径门也有同类字段缺口；通用 C6 门有交叉保护，但路径特异性不足，MEDIUM。
- 三道既有循环门在条目集合为空时会恒真通过：
  - [test_g5_6_clear_inbox.py:414](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:414)
  - [test_g5_6_clear_inbox.py:545](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:545)
  - [test_g5_6_clear_inbox.py:632](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:632)

  临时令 `batch_raw=[]` 后三门结果为 `3 passed in 0.18s`。完整套件另有条目数量门交叉发现，故属门级 MEDIUM/PARTIAL，不是当前生产逻辑缺陷。
- 八道本轮新门本身不存在“item 不在报告仍通过”：它们会因 `item_by_name`、`items[0]`、`next()` 或直接纯函数断言而失败。
- 当前三条新 BLOCKER 分别说明仍缺：现表外肯定式 AI 声明、角括号 URL 值、非法 backtick info string 的门。

## 四、措辞

1. **文件头总括语过宽 — FAIL。**  
   [inbox_preview.py:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:39) 的“全部声明／无未声明项”不能由有限的 73 门、24 个定点变异证明；本轮三条新破坏路径已经直接反证。

2. **显式偏差 4 — PARTIAL/FAIL。**  
   [inbox_preview.py:50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:50)
   - 有限边界、语义否定上限写得诚实；
   - “漏判无正文由 AI 嫌疑护栏落 C6”被 BLOCKER-1 反证，只对仍含现表裸 marker 的漏判成立；
   - “护栏④”实际已经是偏差 15 的信号⑤；
   - “basis 带逐字片段”过宽：实现回显的是 `AI_MARKERS` 原表文本，不是输入行逐字文本；大小写/NBSP 会被规范成表内拼写。

3. **显式偏差 11 — 核心 PASS，证据边界 PARTIAL。**  
   [inbox_preview.py:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:74) 的“不可判＋全部候选”已由两候选门和本轮三候选 CLI 支撑；任意 N 主要依赖静态列表展开。`*`/`_` 未转义已在文件头如实登记 LOW，JSON 保真，不重开 H4。

4. **显式偏差 12 — 结果部分成立，因果与全称过宽。**  
   [inbox_preview.py:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:82)
   - 首行 `source:https://x` 的 `frontmatter_span=0`，该行作为正文走普通 C6，并非偏差 15 护栏；
   - 只有排在合法键后的形态走 `unparsed_fm` 护栏；
   - “文件名带 R 仍按 C5”缺少“有实质正文且未先命中 C4”条件；无正文时护栏在 C5 之前返回 C6。

5. **MD §七 — PARTIAL/STALE。**  
   [inbox_preview.py:1605](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1605)
   - “只有正文逐字相等才建议删”应限定为“重复判据中”，否则与 C3 出口冲突；
   - 护栏列举漏掉实现已有的 URL 别名与 `slept_at`；
   - “AI 依据逐字片段”仍不是输入原文；
   - “漏判方向落拿不准”不能扩读成全称安全保证，BLOCKER-1 已反证。

6. **验收单 — MEDIUM/STALE，不能代表当前字节终态。**  
   [UAT:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:3)、[UAT:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:97)、[UAT:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:124)、[UAT:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:184)
   - 仍称 round-4 两条未修、不做 round-5、`67` 门/`16` 变异；当前实际为 `73`/`24`；
   - 仍写“三道护栏”，未同步后续 AI、URL 别名、`slept_at`；
   - “分得清谈 AI 与 AI 写的”“AI 给原文”“按 Markdown 通行规范”“必须有域名”均比现有证据或实际判据宽；
   - UAT 对“变异不构成全称证明”“CommonMark 仅子集”的限制说明本身是诚实的。

## 五、MEDIUM / LOW 登记（不续轮，仅记录）

- **MEDIUM — 非法端口仍被当合法 C1。** `source: https://example.test:notaport/x` 实际输出 `C1_source_url / 留原地 / primary-record / confident=true`。`urlsplit().hostname` 不会验证端口，代码没有读取 `parts.port`。方向非破坏性，故不升 BLOCKER/HIGH。
- **MEDIUM — 批内重复 conflict 与最终 C4 自相矛盾。** [inbox_preview.py:901](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:901) 可写“故不产出建议删”，但同件随后仍可由 C4 建议删。属既有信息一致性问题。
- **MEDIUM — 路径门字段锁定不足、三个循环门可空集合假绿。** 详见 §三。
- **LOW — H4 人读 Markdown 未转义路径中的 `*`/`_`。** JSON 路径仍逐字保真。
- **LOW — ASCII 收尾分档会漏掉 `Generated by AI on …`。** 当前落 C6，不产生确定去向，方向安全。
- **LOW — 变异矩阵未列 H3 span/no-space 两门。** 两门经独立补杀确认承重，只是现有输出不能声称由 24 条指定变异覆盖。

BLOCKER/HIGH 清零: 否


