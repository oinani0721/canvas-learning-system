> 批次: BATCH-2026-09-05-第十二批 · 车道 Y4 · 卡 CARD-TOOL-typecheck-glob round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-TOOL-typecheck-glob.md)"`
> 审查绑定: `4cc4824c..64498c26`（审后按其第 2/3 问**只改了注释文本**，HEAD 已前进；
> 等价性判据见 `evidence-typecheck-glob/judge9-equivalence-*.txt` 与验收单 §Codex 复核）
> 会话头自证（抄 .stderr 会话头块，stderr 本身不入库；⚠️ 字面前三行是
> `Reading additional input from stdin...` / `OpenAI Codex v0.153.3` / `--------`，
> model 行在第 5 行，故此处抄含 model 的三行）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`
> `session id: 01a070f4-d5f9-7b13-af4c-5fecbca7b17d` · `sandbox: read-only`

---

**结论：第 1 问成立；第 2、3、4 问部分成立。** 收窄行为有实测支持，但存在数字范围误用、环境条件表述过强，以及提交文件数不符。

以下探针、计数文件均位于[证据目录](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/审查/evidence-typecheck-glob)。

**1. glob 语义：成立（限本机 2.1.6 的所列实测）。**

三份 HIT 的第 3–4 行均记录新 glob 和版本，深度均相对 `backend/app/`：

| 证据文件 | 深度 | 真正运行的依据 |
|---|---:|---|
| `probe-HIT-backend_app_main.py.txt` | 根级 | 第 14–22 行：Running 字面输出、1 error、exit 1 |
| `probe-HIT-backend_app_mcp_server.py.txt` | 1 级 | 第 14–23 行：Running 字面输出、6 warnings、exit 0 |
| `probe-HIT-backend_app_api_v1_endpoints_health.py.txt` | 3 级 | 第 14–27 行：Running 字面输出、4 errors、exit 1 |

三份均出现 `[Python] Running pyright type check (backend/.venv/bin/pyright)...`，随后有实际诊断，证据不止启动提示。它们支持单星跨目录匹配；“任意层级”是对此的规则归纳，并非穷举所有深度。

两份 `probe-NEG-*` 的第 **12 行**均为 `python-typecheck (skip) no files for inspection`，确实未进入检查。

新旧对照有效：`probe-OLDGLOB-flip.txt:2–4,7–25` 记录同一 scratch、base、版本下，旧 glob 对 `backend/tests/conftest.py` 真跑并输出 `exit status 1`；新 glob 对同一路径的跳过见对应 NEG 第 12 行。

勘误也正确：OLD 第 **29 行的 `rc=0` 不能解释为 lefthook 成功**；第 **44–51 行**已说明管道返回码采集问题，并以第 23、25 行的失败字面输出纠正结论。旧错误行保留，但已明确标错。

历史矩阵 `lefthook.yml:40–47` 与上述跨层级行为相容；新探针直接补足了新模式对根级文件的证明。

**2. 注释实数：部分成立。数字都有对应记录，但 846 用错了范围。**

原始依据均在 `judge1-counts-20260905T173653.txt`：

| 数字 | 原始行号 | 记录的口径 |
|---:|---|---|
| 263 | 6–7 | `backend/app` 的 tracked `.py` |
| 0 | 8–9 | `src` 的全部 tracked 文件 |
| 41 | 10–11 | 仓库根 `tests` 的 tracked `.py` |
| 304 | 25–26 | `263 + 0 + 41` |
| 846 | 12–13 | **整个 `backend`** 的 tracked `.py` |
| 493 | 14–15 | `backend/tests` 的 tracked `.py` |

明确冲突在 [lefthook.yml:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/lefthook.yml:151)：

> “旧 glob 的可达面是 backend 全部 846 个 .py”

同文件第 **172–173 行**却说明旧 glob 漏掉一级两个 `.py`；计数记录第 **16–18 行**列出了它们，OLD 第 **32–37 行**还直接证明 `backend/mutmut_config.py` 在旧 glob 下跳过。因此 **846 是目录总量，不能称为旧 glob 命中量**。按注释自身的匹配规则扣除两个一级文件，应为 **844**；这是推算，原始记录没有直接计数旧 glob 命中集。提交说明重复了同一错误。

592 的归属正确：[pyrightconfig.json:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/pyrightconfig.json:2) 的 include 列出三个路径，第 **16 行**注明“同一 include”，第 **20 行**记载 592 errors。它不是 `backend/app` 单独的错误数。**304 来自本次 tracked 文件计数，并非原配置直接记载的检查文件数。**

另外，`lefthook.yml:153,158` 的历史 **18/19、258/35** 在限定材料中没有原始佐证；且 `18/19` 约为 **94.74%**，并非精确的 `94%`。

**3. 措辞：部分成立。没有冒充类型通过，但环境条件写得过强。**

[lefthook.yml:176](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/lefthook.yml:176) 明言“不声称任何文件的类型是对的”；提交说明明确写“未证明”；第 **197 行**也写明 `did NOT run -- this is NOT a pass`。未发现把本卡包装成整体类型检查通过的表述。

第 **179–181 行**确实分开陈述主仓跳过与共享 venv 工作树运行，但有两处边界问题：

- **“主仓 venv 无 pyright ⇒ SKIP”条件不足。** 第 **190–191 行**还会从 `PATH` 查找；必须两个入口均不可用，才进入第 **195–198 行**的 SKIP。提交说明也省略了这个条件。
- **“只有 symlink……才真跑”按字面不成立。** 第 **188–191 行**同样接受普通 venv 中的可执行文件及 `PATH` 中的 pyright，没有检查软链。

限定材料没有主仓环境实测记录，故只能确认这些话被分开写出，**不能独立确认主仓当时必然跳过**；这也不等于认定其环境描述必假。

**4. 改动面：部分成立。配置改动受限，但整个 commit 不止一个文件。**

绑定区间 `4cc4824c..64498c26` 的变更清单是：

- `M lefthook.yml`
- **9 份新增证据文件**：三份 `judge*`、五份 HIT/NEG、一个 OLDGLOB 对照。

因此准确说法是“**只修改一个既有配置文件，并新增九份证据文件**”，不是“整个 commit 只涉及 `lefthook.yml`”。

该文件的绑定 diff 只有一个 hunk：新增 36 行注释，并替换 glob。由此可确认：**命令名集合及出现顺序不变，没有新增 `priority`，run 脚本未改。** `pyrightconfig.json` 不在绑定区间变更清单中，确实未改。

“有意不收”的登记基本属实：

- `src/` 零 tracked 文件：计数记录第 **8–9 行**；配置第 **4 行**确有 `"src"`。
- backend 一级两个文件：计数记录第 **16–18 行**，均不在 `backend/app`。`mutmut_config.py` 被旧 glob 漏掉有 OLD 第 **32–37 行**直接证明；`start_server.py` 没有独立探针，其被漏属于同层级匹配规则的推论。

总评：**最需要修正的是 `lefthook.yml:151` 及提交说明中“旧 glob 可达全部 846 个文件”的说法。** 它把目录总量当成匹配量，且与本卡自己的排除项、旧 glob 探针直接冲突。收窄行为本身的证据成立。
