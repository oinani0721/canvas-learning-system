> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-G1-1 round-3（H1 整改链，codex+zai GLM-5.3）
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G1-1-r3.md)"`
> 审查绑定: `8c546e72`（本 commit 之后只动 `_bmad-output`；`git --no-pager diff --stat --no-color 8c546e72 HEAD -- . ':(exclude)_bmad-output'` 为空即仍绑定）
> 会话头自证（抄 .stderr 第 2/5/9 行；stderr 本身不入库，.gitignore:260-264 覆盖）:
> `OpenAI Codex v0.153.3` / `model: glm-5.3` / `reasoning effort: max`

---

## 复审结论：PARTIAL —— H1 未完全闭合

绑定核对通过：`HEAD = 8c546e72569271fdd1e1c2af81f7c7b46e7c9bb8`；`8c546e72..HEAD` 除 `_bmad-output` 外 diff 为空。整改 commit 确为 2 文件 `+131/−3`。两个 ZCode 点名的容器头均已可召回，但独立真数据复扫又找到一个仍漏召回的中文 T1 粗体形态，因此不能判“H1 真闭合”。

---

## HIGH

### HIGH-1R · 中文 T1 仍漏召回未带括注的定位限定词 `L128`，且“真数据 3 处真容器头”的 census 不实

- **位置**：`scripts/annotation_search.py:85`  
  **漏召回真数据**：`_bmad-output/implementation-artifacts/epic-1/1-8-vault-switch-runtime-api.md:174`
- **门未覆盖的路径**：`user_bold_zh` marker 门只允许：
  - 限定词 `原文|触发`；
  - 或括注 `[（(]...30...[）)]`。
  未覆盖“关键词后直接跟未加括号的行号/定位限定词，再闭粗体”的形态。

- **负控输入 / 实际复现**：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/annotation_search.py \
  --root '_bmad-output/implementation-artifacts/epic-1/1-8-vault-switch-runtime-api.md' \
  --a01 '_bmad-output/审查/phase0a-annotation-truth/A01-source-boundary-draft.json' \
  --keyword L128 --json
```

观察到：

```text
marker_hits=0 shown=0
rc=1
```

对应真数据行是：

```markdown
3. **用户批注 L128**: 确认 Claudian 应自动检测 vault 变化
```

该行在 `a07608b8` 与 `8c546e72` 中逐字存在，不是本轮 untracked 证据造成的漂移。它以粗体“用户批注”为标签、冒号在粗体外，且正文记录用户确认事项，符合契约 `_bmad-output/审查/phase0a-annotation-truth/2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md:130/:134` 的中文 T1 面。

- **为什么不是已登记旧问题**：这不是 M1/M2/L1–L8；它是本轮 `user_bold_zh` 正则自身的漏召回面。ZCode r2 H1 的类别就是“中文 T1 粗体容器形态漏召回”，本条仍是同一缺陷类的残留。
- **附带的声明漂移**：`scripts/annotation_search.py:16-17`、`scripts/annotation_search.py:84`、`backend/tests/unit/test_annotation_search.py:1035-1037` 均声称真数据只有 3 处真容器头；加入 `L128` 后该 census 不成立。`scripts/annotation_search.py:7` 的“T1 全部”也仍不能成立。
- **建议修法方向**：不要直接采用 r2 建议里的宽泛 `[^*]{0,30}`——它会重新放进 `**用户原话 3 个 callout...**:` 这条已测负控。较小方向是为真定位符增加有界形态，例如独立的英文 locator/行号限定词分支，并加真锚或最小 fixture：

```markdown
3. **用户批注 L128**: 确认 Claudian 应自动检测 vault 变化
```

同时保留现有 f10/f11/f12 三个负控。

---

## LOW

### LOW-1 · 空行跨行层会把未加粗的 `> Claude：...` 引用行收进“用户批注”块

- **位置**：`scripts/annotation_search.py:625-633`；终止规则仅识别粗体 speaker 或 marker，见 `scripts/annotation_search.py:546-562`。
- **对照输入**：

```text
**用户批注：**

> Claude：这不是用户原话 kw
```

直接调用当前 `extract_block()` 观察到：

```python
(
  ["**用户批注：**", "> Claude：这不是用户原话 kw"],
  "**",
  True
)
```

也就是说，该未加粗 Claude 行会进入 excerpt，且关键词 `kw` 会把该块召回为 `user_bold_zh`。

- **降级理由**：我在当前 `_bmad-output` 中未找到“`>` 后直接 `Claude:` 且无粗体”的真实实例；项目真实 speaker 形态看起来是粗体标签。因此这是可复现但未见真数据命中的新边界，不足以升 MEDIUM。
- **已有防线确认**：以下对照输入不会误收：
  - `> **Claude（2026）：** ...` 会停；
  - `> [!note]+ ...` 会停；
  - 后续真空行会停；
  - 第二个 quote block 之间隔空行会停。

---

## 问题逐答

### 0. H1 是否真闭合？

**两个被点名点已闭合，但整体 H1 未闭合。**

- `2026-08-02...给ChatGPT.md:23`
  - 实跑：`files_scanned=1 marker_hits=1 shown=1 empty=0`，rc=0；
  - excerpt 包含空行后的用户原话，且含 `"真正担心的问题"`。
- `Story-2.1...md:429`
  - 实跑：`shown=1`；
  - excerpt 为 `:429-430` 两行，包含用户原话。
- 另一个作者声称的真锚 `research/round-23...md:13` 也可召回，excerpt 含 `:14` 用户原话。
- 三个 fixture 负控均未命中：
  - Claude 自述语；
  - 无冒号 topic；
  - 裸中文转述。

但 HIGH-1R 的 `L128` 真数据仍为 `marker_hits=0 shown=0`，所以 H1 只能判 PARTIAL。

### 1. 正则面

- 已确认不命中：f10/f11/f12 三个负控。
- 已确认命中：嵌套括注、半/全角混用括号；这不是当前真数据中的误归因证据，未单独报错。
- 已确认不命中：超过 30 字符括注、`**用户批注** ：` 这种闭粗体后带空格再冒号的形态；当前未见真数据依据，未作为整改要求。
- **必须扩**：至少要覆盖 ` L128` 这种未括注定位符；这是真数据，不是推测。
- 不建议直接放宽为任意 `[^*]{0,30}`，因为 f10 会重新进入。

### 2. 空行跨行层

- 对目标布局有效：仅紧邻空行、下一块必须是 `>`、再按 quote block 收。
- `--context 0` 不会把该块判空：内部 `limit=max(context,1)` 保底扫描一行。
- quote 中若出现粗体 speaker 或 marker，会被 `stops_block()` 截住。
- 未加粗 `> Claude：...` 是当前未被拦下的对照输入，见 LOW-1。
- 默认 `--context` 仍限制关键词检索面；这是已登记 M1，按本轮边界不重复处理。

### 3. 门是否锁得住

- 存档核对：
  - 点名套件 `85 passed / 0 skipped`；
  - 摘除 `user_bold_zh` → 8 条指定测试红；
  - 停用空行跨行层 → 4 条指定测试红；
  - 当前 `scripts/annotation_search.py` SHA256 与负控存档 pre/post SHA 一致：
    `f553e223...ffa`；
  - `tests/unit` 基线 diff 仅少一条既有 flaky failure。
- 但当前 85 绿没有覆盖 `L128` 形态；也就是说，“只收 `原文|触发` / 括注”的收窄正则本身就是存活 mutant。需要为 HIGH-1R 增加真数据锚或最小 fixture。
- `:23` 行号脆性：现有真锚会在行号漂移时红，符合 L7 的 loudly-fail 口径；本轮未见需要额外登记的新问题。

### 4. 声明漂移

- `len(MARKERS)==11` 的注释、实现、测试三处一致；callout 数也为 9。
- 但“真数据 3 处真容器头”与“T1 全部”在 `L128` 证据下不成立，见 HIGH-1R。
- 旧 UAT 里的“中文 T1 未覆盖”是历史审查记录，不要求本轮改写；当前活文档以脚本 docstring 和新测试注释为准。

### 5. 回归面

- diff 只触及 marker 表和 `extract_block()` 的中文空行分支；未改私人 root、A01 fail-closed、日期、排序、输出格式。
- 实跑仍显示默认排除 `ROOT-ACTIVE-VAULT` / `ROOT-ANCHORED-PRD`。
- 同参数两次子进程、不同 `PYTHONHASHSEED`：stdout/stderr 均逐字相同。
- `ruff check` 与 `ruff format --check` 均通过。
- 只读沙箱无法完整执行 pytest（全局 conftest 需要 temp dir）；我核对到 85 条可收集，并以存档 + 直接 CLI/函数复现代替完整重跑。
