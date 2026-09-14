> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE-r4.md)"`
> 审查绑定: `7bcbfc1aded2ca3ea5aa44b7711163b9a8c77af4`（该轮报 HIGH 1，整改为 ccb1d101 后送 r5）
> 会话头自证（抄 .stderr 第 2/5/9 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**本轮发现新增 HIGH 1：旧 checkpoint 与新分行口径不兼容，可能漏回灌正常记录。当前 SHA 不满足所述 D-15 的 B/H 归零条件。**

审查绑定 `7bcbfc1aded2ca3ea5aa44b7711163b9a8c77af4`，结束时 HEAD 未变，四个受审文件无未提交修改。仅做限定源码复核和 Python 3.14.4 纯内存实验；未修改文件、未连接数据库。

1. **HIGH — 分行切换直接沿用旧 checkpoint，跳过未处理记录。**  
   [fallback_sync_service.py:227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:227)，跳过判断在 `:233`，保存下标在 `:256`。  
   **负控输入／复现思路：**首条合法 JSON 含 U+2028，后接普通记录 1–50；旧版切成 52 片，在完成普通记录 48 后保存 checkpoint=50 并中断。新版切成 51 行，载入旧值 50 后只处理记录 50，**尚未处理的记录 49 被跳过，也不进入 `still_pending`**。纯内存结果：旧版续跑 `[49,50]`，新版 `[50]`。  
   这是 r4 新回归。需兼容转换旧游标并标记分行格式版本；不能未经核对直接清零重放。限定读取面未包含 checkpoint loader，本结论以它按题述契约返回历史下标为前提。

2. **MEDIUM — r3 清理身份问题仅部分关闭，前四条仍跨 vault／运行匹配。**  
   [test_neo4j_replay_wire_t6b.py:163](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:163)，另见 `:167、:171、:174`。  
   **对照输入／复现思路：**另一 vault 的 `Canvas {path:'t6bgate_canvas', group_id:'vault__other__t6bgate_canvas'}` 仍被 `:174` 删除；并行另一轮生成的 `t6bgate_concept_<另一UUID>`、`t6bgate_cid_<另一UUID>` 也仍命中。  
   精确 group 只约束第五条孤立 Episode 查询。最小方向是为每次运行分配独立身份，让 Canvas、Concept、Node 的清理与计数共同使用它。

3. **MEDIUM — 启动回灌仍依赖回填先成功，登记不能视为关闭。**  
   [main.py:416](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:416)，测试入口见 [test_neo4j_replay_wire_t6b.py:296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:296)。  
   **负控输入／复现思路：**`:392` 的 `backfill_vault()` 抛异常，控制流直接进入 `:462`，回灌不执行；删除 `:416` 的调用，当前不运行 lifespan 的管理端点门也检不出。  
   保留 r3 MEDIUM-2。“不能跑现网 lifespan”解释了验收限制，但不能消除生产控制流问题。最小改法是将回灌置于回填 `try/except` 之外独立处理，仅触碰本卡启动接线；隔离测试可以验证共享启动回灌函数，整套 lifespan 仍明确列为未验。

4. **LOW — 清理与计数的标签、属性条件并未逐字对齐。**  
   [test_neo4j_replay_wire_t6b.py:314](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:314)。  
   **负控输入／复现思路：**留下 `(:Node {name:'t6bgate_concept_foreign', id:'othergate_cid'})`，无标签的计数查询因 `name` 命中而计入 Node；清理要求 Concept 标签匹配该名字，或 Node 的 `id` 匹配，因此清不掉，首次绝对值断言可持续假红。  
   最小改法是计数也明确绑定相同的“标签＋属性”组合。

5. **LOW — `exists()` 仍绕过读取失败 warning。**  
   [fallback_sync_service.py:152](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:152)，另见 `:177`。  
   **对照输入／复现思路：**Python 3.14 下，不可访问路径使 `exists()` 返回 `False`，函数直接返回零，无法通过 warning 区分不可读与真空。此项为静态复核，未制造权限故障。  
   保留 r3 LOW-3；作为明确未关闭的 LOW 登记可以接受。最小修法是直接读取，分别处理 `FileNotFoundError` 与其余读取异常，只触碰本卡计数，不涉及 T6-C。

其余问题的核对结论：

- **⓪ 清理整改部分有效。** `t6bgate2_*` 和不同 group 的 `other_t6bgate_canvas` 孤立 Episode 已排除，参数化成立。`gid=None` 时跳过兜底的取舍合理：普通孤立 Episode 不进入当前关联计数，不能断言它必然污染幂等；以后同 group 能解析时仍可清理，也不能无条件称其永久滞留。另需区分返回 `None` 与抛异常：`:160` 的调用若抛异常，整套查询都无法构造；解析实现未在读取面中，未证明具体触发输入。

- **① 两种切法不对所有输入等价。** U+0085/U+2028/U+2029 在合法字符串中由多片变一行，正是修复目的；用这些字符代替记录间 LF 的非标准历史输入，则可能由旧版可读变成新版 pending。**CRLF、裸 CR 没有本轮兼容回归**：`read_text()` 默认将其转换为 LF；即使尾部残留 `\r`，`json.loads` 也接受这个 JSON 空白。无需依赖“生产只写 LF”的前提。其他生产写侧和历史文件不在允许读取面内，未核实该前提。

- **② 初读与 finalize 的新切法一致。** 完整记录追加的 LF／CRLF／裸 CR 对照均正确识别并保留新增尾行；不能据此扩大为所有并发写入保证。历史 checkpoint 的问题独立存在，见 HIGH。

- **③ 全量 diff 另有门未覆盖的路径：并发双 POST。** 两请求可能都读到同条记录并进入回放，现门只有顺序调用。实际写图主体在读取面外，因此本轮不把“重复 Episode”作为已证缺陷计数。

**计数汇总：BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 2。**


