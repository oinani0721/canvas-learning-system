> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t7-skills · 卡 CARD-AILINKED-4TH-WRITER round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-AILINKED-4TH-WRITER-r2.md)"`
> 审查绑定: `65e3f333`（该轮送审时的 HEAD；round-4 绑最终 HEAD）
> 会话头自证（抄 .stderr 对应行，stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

审查绑定 **`65e3f33324cb2f3b8b7c048640a48d99d49789d5`**。round-1 三项修改已落实；全面复核另发现 **1 个 MEDIUM**，该问题已存在于 round-1 版本。

| 分级 | 结果 |
|---|---|
| BLOCKER | 无 |
| HIGH | 无 |
| MEDIUM | 1 条：有损 UTF-8 解码使坏行成为查重证据 |
| LOW | 无 |

**MEDIUM — 坏行仍可能吞掉本次事件。**  
定位：[SKILL.md:305](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/ai-linked-doc/SKILL.md:305)。沿 `decode('utf-8', 'replace') → json.loads → :326 event_id 相等` 检查：非法字节被替换成 U+FFFD，原本无法解码的历史行因此被当作有效查重证据。

独立复现使用普通节点名 `测试节点`：预置完整历史事件，其 `event_id` 为 `derive:测试节点`，仅将 `payload.note` 内容换成原始字节 `0xff`。逐字提取写点执行后：

- Python **3.9.6、3.14.4** 均返回 `0`，stdout 为空，账本原样不变，**有效目标事件仍为 0 条**。
- 校验器明确报告该历史行为非法 UTF-8。
- 相同节点名在空账本正控中正常追加，校验器 PASS。

这违反了“无法解析的坏行不构成 duplicate 证据”。建议按物理 LF 切分 **bytes**，在逐行 `try` 内严格 UTF-8 解码，再解析 JSON；不能改成整本严格解码，否则又会让一条坏行中止整次追加。

其余复核结果：

| 项目 | 判断 |
|---|---|
| round-1 MEDIUM-1 | **异常捕获整改到位**。深层嵌套、超长整数、普通坏 JSON 均未阻止新事件追加；未发现其他由普通输入触发的解析异常漏捕。上面的有损解码问题属于另一条路径。 |
| round-1 MEDIUM-2 | **对所述准备耗时问题有效**。`prep ≥ 1s` 直接判夹具不健康，两方向的不可比样本都不进入写规裁决；健康样本约剩至少 `3s`，高于③的 `2.4s`。 |
| 计时限制 | [测试:274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/skills/test_ai_linked_doc_writer.py:274) 的 `t_held` 实际是父进程收到信号的时刻，`t0` 又在 gate 放行后记录。因此 `.25` 留出的 `0.6s` 余量不能覆盖任意调度停顿；不能称为无条件时序保证。 |
| round-1 LOW-1 | **整改到位**。档 B 确实预置无末尾 LF 的账本并启动双写者，④检查原文；门③注释也已准确。 |
| 移至 Step 5.5 | **理由充分**。Step 3 负责生成文档，Step 5 才实际写文件，成功后落日志的位置正确。剩余 bullets 均约束生成内容或元数据，自洽。 |
| ⓪ parsed-field | **PASS**。历史非 `event_id` 字段恰等于新 evid 不再造成误判。 |
| ①② fd / LF | **PASS**。锁内始终同一个 fd，无隐式重开；close 结束持锁期。LF 守卫在锁内，空文件不补 LF 正确。 |
| ③形态门 | **PASS**。首尾空白拒写、不 strip；禁止集与校验器精确相等，共 2181 个码点。门④三类反例在 `derive:` 前缀下均可达。 |
| ④外形与提取 | **PASS**。写点普查仍恰四份；唯一 PYEOF 块正文无行首终止符；两个占位各保留一次；producer 文件仅改指定函数。 |
| ⑤backend | **PASS**。去掉 docstring 后，完整 AST 与 `d5ad6fca` 相同，仅注释变化。 |

本轮也在内存中制作并执行了两个负控，未修改仓库模板：

| 负控 | 档 A 条数 | 档 B 条数 | 释放前大小 | elapsed | 红判据 |
|---|---:|---:|---:|---:|---|
| 去掉锁 | 2 | 2 | 462 | 0.006s | ①②③④ |
| 锁内二次 `open` | 1 | 2 | 0 | 3.991s | ①④ |

因此，**“①不能由②③替代”成立，并已独立复现**。固定 backlog 和屏障放大了竞态窗口，但“必红”仍不宜理解为跨机器、跨调度保证。

验证结果：隔离运行四门、ai-linked-doc producer 门和摘要门，**10 passed**；禁用了项目 conftest、自动插件和缓存。`pyright app` **未复证**：仍因缺少 `libllhttp.9.3.dylib` 以 250 退出。未连接数据库；仅使用自动清理的临时夹具，仓库五文件哈希及最终 HEAD 均未变化。


