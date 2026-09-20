> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-G1-1 round-4（H1 整改链，codex+zai GLM-5.3）
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G1-1-r4.md)"`
> 审查绑定: `bf3a765c`（本 commit 之后只动 `_bmad-output`；`git --no-pager diff --stat --no-color bf3a765c HEAD -- . ':(exclude)_bmad-output'` 为空即仍绑定）
> 会话头自证（抄 .stderr 第 2/5/9 行；stderr 本身不入库，.gitignore:260-264 覆盖）:
> `OpenAI Codex v0.153.3` / `model: glm-5.3` / `reasoning effort: max`

---

## 复审结论：PASS —— HIGH-1R 已闭合；LOW-1 接受「登记不改」

**Now**：`bf3a765c` 可按本卡闭合 HIGH-1R；未发现本轮引入的 BLOCKER / HIGH / MEDIUM 新问题。  
**Prohibited**：不要为 LOW-1 在无真数据实例时加宽 speaker 终止启发式；也不要把定位符分支放宽成任意 `[^*]{0,30}`。  
**Unlock when**：LOW-1 继续留在整改档；只有出现真实 `> Claude：…` 被并入用户批注摘录的数据实例时，才应另开小修。

---

## 绑定与地盘

- `HEAD = bf3a765cebf86081d74232f9b6f14e629eaeb786`
- `bf3a765c..HEAD` 除 `_bmad-output` 外 diff 为空。
- H1+H1R 全整改面 `a07608b8 → bf3a765c` 恰好：
  - `backend/tests/unit/test_annotation_search.py`：+118/−2
  - `scripts/annotation_search.py`：+38/−1
  - 合计 2 文件，+156/−3。
- 当前 `scripts/annotation_search.py` SHA256：
  - `ed6b8e8111c5b104b84144eba36e5013eb929242c1e3b904a9004dd128b724df`
  - 与 `h1r-negctl-3H` 存档的 pre/post SHA 逐字一致。

---

## 分级结果

### BLOCKER

无。

### HIGH

无。HIGH-1R 已闭合。

### MEDIUM

无。

### LOW

#### LOW-1 · 未加粗 `> Claude：…` 可进入中文空行跨行摘录 —— 接受登记不改

- **位置**：`scripts/annotation_search.py:624-639`；相关终止规则在 `scripts/annotation_search.py:552-568`。
- **对照输入**：

```text
**用户批注：**

> Claude：这不是用户原话 kw
```

我直接调用当前 `extract_block()` 复现，输出仍为：

```python
(
  ["**用户批注：**", "> Claude：这不是用户原话 kw"],
  "**",
  True
)
```

- **门未覆盖的路径**：`stops_block()` 只拦粗体 speaker、marker、空行；未加粗 quote speaker 是续行收集器既有未覆盖输入，不是本轮定位符分支引入。
- **处置判断**：接受登记不改。当前全仓检索只找到 r3 存档里的合成样例 `_bmad-output/审查/codex-review-CARD-G1-1-r3.md:64`，未找到真实数据实例。并且普通紧邻续行收集同样有该性质；现在加入宽泛 `Claude：` 启发式，容易误截断 `> Note：` 等正常引用内容。
- **后续解锁条件**：出现真实用户批注块误收未加粗 Claude 回复的 `file:line`，再做只针对 quote speaker 的窄修。

---

## 问题逐答

### 0. HIGH-1R 是否闭合？

**闭合。**

我用 r3 原输入独立实跑：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/annotation_search.py \
  --root '_bmad-output/implementation-artifacts/epic-1/1-8-vault-switch-runtime-api.md' \
  --a01 '_bmad-output/审查/phase0a-annotation-truth/A01-source-boundary-draft.json' \
  --keyword L128 --json
```

观察到：

```text
files_scanned=1 marker_hits=1 shown=1 empty=0
line=174
marker="**用户批注 L128**:"
excerpt="3. **用户批注 L128**: 确认 Claudian 应自动检测 vault 变化"
rc=0
```

r2 输入也回归通过：`2026-08-02…:23` 仍为 `shown=1 empty=0`，摘录包含空行后的 `> 「我这里引用 Graphiti 的真正原因…」` 用户原话。

**census「4 处」证实**。我用比实现更宽的粗体容器形态复扫 `_bmad-output/**/*.md`：

```regex
\*\*\s*用户(?:批注|反馈|原话|修正)[^*\n]{0,100}?\*{0,2}\s*[：:]
```

排除本轮 review/prompt/evidence 的自引用样例与已知 Claude 自述负控后，真实用户容器头正是四类：

1. `_bmad-output/审查/2026-08-02-规模化结构检索-审查请求-给ChatGPT.md:23`
2. `_bmad-output/验收单/Story-2.1-Phase1-成熟度升级-2026-05-03.md:429`
3. `_bmad-output/research/round-23-phase-a-retrieval-quality-2026-05-09.md:13`
4. `_bmad-output/implementation-artifacts/epic-1/1-8-vault-switch-runtime-api.md:174`

已知非容器负控 `_bmad-output/research/obsidian-qa-round3-claude-answers-2026-04-14.md:1031` 仍不命中。

三处声明同步一致：

- `scripts/annotation_search.py:17-19`
- `scripts/annotation_search.py:87-88`
- `backend/tests/unit/test_annotation_search.py:189-193` 与 `:1054-1056`

`MARKERS` 实测 11 项，与 `scripts/annotation_search.py:73-74`、`backend/tests/unit/test_annotation_search.py:1029-1033` 一致。

### 1. `(?:\s?L\d+)?` 正则面是否过宽或过窄？

**未发现真数据误纳。**

我直接调用 `find_markers()` 测了以下输入：

| 输入 | 结果 | 判断 |
|---|---|---|
| `**用户原话 3 个 callout 名字对应 Canvas 真实机制**: …` | 不命中 | f10 负控仍拦住 |
| `核心决策：**用户批注（Obsidian callout）是否应该…**，…` | 不命中 | 无冒号 topic 负控仍拦住 |
| `采纳用户原话：Claude 转述…` | 不命中 | 裸中文 T3 负控仍拦住 |
| `**用户原话 L128 是一条长描述**：…` | 不命中 | `L128` 后还有正文，不会误当标签 |
| `| **用户原话 L128** | 无冒号表格单元 |` | 不命中 | 无冒号不构成容器 |
| `| **用户原话 L128**：表格容器 |` | 命中 | 表格嵌套 + 明确标签 + 冒号，符合契约 `:131` 的 table/blockquote/list 变体面；未见真数据误实例 |

定位符变体方面，`L 128`、`l128`、`line 128`、括注后再跟 `L128` 等当前不收；全仓真数据复扫未发现这些同族变体，因此不报漏。

### 2. LOW-1 处置是否可接受？

**接受「登记不改」。**

理由：

1. 复现仍存在，但当前只有 r3 合成样例，无真实数据实例。
2. 这是续行收集器的既有性质，不是 H1R 本次引入。
3. `stops_block()` 的现 vocabulary 只认粗体 speaker / marker / 空行；为未加粗 `Claude：` 加宽规则会牵连其他 quote 行，有截断真实用户内容的反向风险。
4. 登记后续观察比现在猜规则更符合本卡“无证据不猜”的边界。

### 3. 是否还有残余中文 T1 真数据漏召回？

**在本次审查的粗体 T1 容器族内，未发现第五处真实漏召回。**

一个容易混淆的例子：

- `_bmad-output/research/round-14-graphiti-retrieval-deep-explore-2026-05-05.md:28`
- 形态：`## 用户批注原文（line 295）`

这是未加粗标题，不在本轮“中文粗体容器头族”census 内；且紧随其后的 `:30` 是 `> **User：…**`，实际用户原话已由 ASCII `user_bold` marker 召回。因此它不构成新的未召回用户批注，也不使“4 处粗体真容器头”census 变假。

### 4. 声明与测试门

- `MARKERS == 11`：实现、注释、测试一致。
- census 4 处：脚本 docstring、marker 注释、测试 fixture docstring、contract variant docstring 一致。
- H1R 真锚：`backend/tests/unit/test_annotation_search.py:602-608` 精确断言 `:174` 与 marker 文本。
- 负控③存档：摘除 `(?:\s?L\d+)?` 后 4 条指定测试红，且 pre/post SHA 均等于当前源码 SHA。
- 行为门存档：87 passed。
- 目录级失败面：`close-h1r.nodeids` 与上一轮 `close-h1.nodeids` 32 条失败清单 diff 为空；通过数 5848→5850，只对应新增两条 H1R 测试。
- `ruff check --no-cache` 通过；`ruff format --check --no-cache` 通过。

### 5. 回归面

- 本轮 H1R commit 只改 regex、注释与测试；未改私人 root、A01 fail-closed、日期、排序、输出格式。
- 独立 CLI 汇总仍显示默认排除：
  - `ROOT-ACTIVE-VAULT`
  - `ROOT-ANCHORED-PRD`
- 并如实报告 4 个无落地路径的私人 root。
- 同参数 L128 JSON 输出两次 SHA256 均为：
  - `646b1eae22b13642aa1086f10913bc218845a80fb92ce0bc2de10b9b7c14b22b`

**验证限度**：我只读沙箱无法让 pytest 创建 temporary capture file，尝试 collect 时因 “No usable temporary directory” 失败；因此 87 passed / 目录级 32 failed 不是我本地完整重跑的结论，而是基于存档、当前源码 SHA 绑定、失败 node-ID diff、直接 CLI/函数复现与 ruff 独立复核作出的闭合判断。
