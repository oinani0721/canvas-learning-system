> 批次: BATCH-2026-09-18-第十五批 · 车道 P6 · 卡 CARD-SEB-WRITER-SUBSTRING-TMP round-2 prompt-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SEB-WRITER-SUBSTRING-TMP-r2.md)"`
> 审查绑定: `13ab1b37bd7840a26e568a71a5c77bd3e6d30b13`（与 r1 同一 HEAD；r1 之后零代码改动，只改 `_bmad-output/` 文档）
> 本轮目的: r1 明确写「④⑤⑥ 需超出限定读取面、未能独立核实」⇒ 本轮**只补读取面**（判据函数本体 + SKILL.md 全文 + quiz-answer :3070-3100），请其独立重算。
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(L2) / `model: gpt-6-astra`(L5) / `reasoning effort: ultra`(L9)

---

**④⑤⑥ 独立重算相符。新增：BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 0。**

绑定 HEAD：`13ab1b37bd7840a26e568a71a5c77bd3e6d30b13`。复核结束时，相关代码文件与该 HEAD 无差异。

**④ 四张表、计数和整文件摘要全部对上。**

以下均为 `start-exam-board` 项的独立实算结果：

| 判据 | 实测值 | 对账 |
|---|---|---|
| `_body_counts` | `tmp_all=8`、`tmp_ns=8`、`bare_tmp=0` | 相符 |
| `escaping_tmp_paths` 多重集 | `prose:/tmp` ×1；`prose:Bash: mkdir -p /tmp/cls-exam` ×2 | 相符 |
| `suspicious_tmp_lines` | `[603]` | 相符 |
| `opaque_tmp_lines` | 下列 4 项 | 相符 |
| `tmp_block_fingerprints` | 下列 7 项 | 相符 |
| 整文件 SHA-256 | 下列摘要 | 相符 |

```text
OPAQUE:
188:65b99234f2075b8f
430:d55b9d2e64fff5a7
603:249fe6bc3d886700
604:3380562d248d9528

TMP_BLOCK:
B195:49bbb79cdd7750a1
B433:1fe4ec494f0e8996
S128:3d332975e351d095
S188:35c02f61a9f9604b
S430:d55b9d2e64fff5a7
S603:249fe6bc3d886700
S604:3380562d248d9528

SHA-256:
c3c0434d385c66f33c097c051d4aac2d05f908a881bc1471785beeaf52493473
```

定位：`backend/tests/skills/skill_portability_lint.py:2003、2061、2087、2126、2182、3245`。上述结果也与作者的 `lint-table-close-20260918T171623.txt`、`lint-table-head-20260918T175932.txt` 逐项一致。

复现思路：通过 `python3 -B` 调用仓库原判据，以完整 604 行 SKILL 为输入；原始字节 SHA-256 另用 `shasum -a 256` 交叉核对。

**行号漂移没有漏改：**

- 原 `577 → 603`，suspicious、opaque、tmp-block 均已同步；后两者对应内容指纹保持不变。
- `430`、`B433` 起点在增行之前，应保持行号，仅更新内容指纹；现状正确。
- `604` 是新增变更记录，opaque、tmp-block 均已登记。
- escaping 是路径**多重集**，本身不按行号钉。

**负控输入**：只在内存把 `603`／`S603` 基线退回 `577`／`S577`，opaque、tmp-block 检查均报不符，suspicious 集合也不等。未发现本次漂移遗漏；整文件摘要另有 `test_skill_portability_lint.py:1313` 的测试调用覆盖。本轮未重跑 pytest，不将判据实跑表述为整套测试通过。

**⑤ 全文件五项计数确为 `0 / 2 / 1 / 0 / 0`。**

| 字面量 | 次数 | 命中行 |
|---|---:|---|
| `/tmp/exam-created-event.json` | 0 | — |
| `/tmp/cls-exam/exam-created-event.json` | 2 | 430、435 |
| `CARD-SEB-WRITER-SUBSTRING-TMP` | 1 | 604 |
| `in ln for ln in _lines` | 0 | — |
| `decode("utf-8", "replace")` | 0 | — |

定位：[start-exam-board/SKILL.md:430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/canvas-vault/.claude/skills/start-exam-board/SKILL.md:430)。复现思路：对全文逐项执行精确字面量 `str.count()`，包含注释与变更记录。

**⑥ 同族登记准确；等值判断的准确行号是 3096。**

[quiz-answer/SKILL.md:3087](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/canvas-vault/.claude/skills/quiz-answer/SKILL.md:3087) 使用有损解码；3091–3095 逐行 `json.loads` 并跳过 `ValueError`；3096 明确执行：

```python
isinstance(_o_lock, dict) and _o_lock.get("event_id") == evid
```

复现思路：在内存执行原片段。**对照输入**中，其他字段等于 `evid`、或 `event_id=evid+"-suffix"`，均不触发重复拦截；精确相同 ID 才触发。含非法 UTF-8 字节且携带相同 ID 的历史坏行，经 `replace` 后仍会被当作重复证据。

因此，限定于这处查重的「子串误判／有损解码」两面，**“无子串面，剩有损解码半个”描述准确**；引用范围应延伸至 3096，不构成新增缺陷。

未修改文件，未连接数据库。


