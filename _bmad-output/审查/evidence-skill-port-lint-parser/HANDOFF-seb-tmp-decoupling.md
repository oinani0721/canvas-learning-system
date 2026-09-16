# 交接文档 — start-exam-board 裸 `/tmp/` 残留与 4 处 regression 硬钉点

> 出自 **CARD-SKILL-PORT-LINT-PARSER**（BATCH-2026-09-11-第十四批 · 车道 T7-C）。
> **本卡只登记、未动手**（对 2 个 regression 文件与 SKILL.md 均无写权）。
> ⚠️ **本文件是该议题的权威描述**。新模块 `backend/tests/skills/skill_portability_lint.py`
> 头部 docstring 里有一份**简版**登记，其中「这两处都在模块级」一句**指代有歧义**
> （Codex r1 的 LOW，见文末「为何模块 docstring 保持 r1 审版」）——
> **解耦卡请以本文件为准，不要照抄那句。**

---

## 一 残留事实

`canvas-vault/.claude/skills/start-exam-board/SKILL.md` 中 `/tmp/exam-created-event.json`
尚有 **2 处裸 `/tmp/`**（未进 `/tmp/cls-exam/` 命名空间）：

- 一处是 `Write` 的目标路径
- 一处是 `P = "/tmp/exam-created-event.json"` 赋值

**这不是新债**：第十三批 U4 CARD-SKILL-PORT-LINT 收工时已把裸 `/tmp/` 从 4 降到 2，
这 2 处是当时刻意留下的残留。

**与层 2 基线一致**：`BASELINE["start-exam-board"]` 的 `tmp_all=6 / tmp_ns=4`
⇒ `bare_tmp()` = 2。2026-09-16 实测 SKILL.md 中 `/tmp/` 出现 6 次、`/tmp/cls-exam/` 出现 4 次，
digest = `0f2c085a1bae12446dd74ab89cc1e6aa5c8bc34901dd3be7ac5d8521310d0dce`。

---

## 二 4 处 regression 硬钉点（**两侧作用域不同，失败阶段也不同**）

> 引用一律用「文件名 + 条目名」，**不用行号**（行号会随别的卡漂移；下方括号里的行号是
> 2026-09-16 于 commit `1eab9358` 的实测值，仅供定位，不作判据）。

### 2.1 `backend/tests/regression/test_g3_3_cas.py` —— 2 处，作用域**不同**

**（a）模块级三行**（其上无任何 `def` / `class`，**导入期即执行**）：

| 条目 | 说明 | 实测行 |
|---|---|---|
| `_SEB_BLOCKS = [...]` 列表推导 | 按 `'P = "/tmp/exam-created-event.json"'` 字面量过滤 | `:46`（过滤条件在 `:49`） |
| `assert len(_SEB_BLOCKS) == 1` | 紧随其后 | `:51` |
| `SEB_CODE = _SEB_BLOCKS[0]` | 取出唯一块 | `:52` |

**（b）函数体内一处**（**不在**导入期执行）：

| 条目 | 说明 | 实测行 |
|---|---|---|
| `_exam_board_code()` 里的 `.replace('"/tmp/exam-created-event.json"', …)` | 消费上面那个模块级 `SEB_CODE` | `:144`（`def _exam_board_code` 在 `:134`） |

**⛔ 失败阶段的归因只落在 (a)**：改字面量 ⇒ `assert len(_SEB_BLOCKS) == 1` 在**导入期**
就断言失败 ⇒ **collect-time ERROR、整个文件不可收集**。(b) 那处根本轮不到执行，
**它不是 collect-time 失败的原因**；但解耦时**同样要改**，否则替换不到目标字面量。

### 2.2 `backend/tests/regression/test_learning_events_schema_contract.py` —— 2 处，**都在函数体内**

均位于 `def test_real_producer_start_exam_board_writer(tmp_path)`（实测 `:1012`）**函数体内**（有缩进）：

| 条目 | 说明 | 实测行 |
|---|---|---|
| `matches = [b for b in blocks if 'P = "/tmp/exam-created-event.json"' in b]` + 紧随的 `assert len(matches) == 1` | 同一字面量 | `:1018` |
| 同函数体内的 `.replace('"/tmp/exam-created-event.json"', …)` | | `:1022` |

**⛔ 失败阶段**：改字面量 ⇒ **该条单测运行期断言红**，**不是** collect-time ERROR、
其余测试照常收集运行。

**非钉点（已排除）**：同函数体内 `:1021` 的 `event_json = tmp_path / "exam-created-event.json"`
**不含 `/tmp/` 前缀**，不受命名空间迁移影响。

### 2.3 计数

cas 侧 2 处 + schema 侧 2 处 = **4 处**（口径更正②：原估 2 处不准）。

---

## 三 地盘约束（为何本卡只登记）

| 文件 | 第十四批设计稿 §3 归属 | 本卡写权 |
|---|---|---|
| `backend/tests/regression/test_g3_3_cas.py` | **不属任何车道** | ❌ 无 |
| `backend/tests/regression/test_learning_events_schema_contract.py` | 经裁定 **R-B14-8** 仅把 producer 提取锚一处放行给**同车道前卡 T7-B** | ❌ 无（放行不覆盖 `:430/:435` 钉点解耦） |
| `canvas-vault/.claude/skills/start-exam-board/SKILL.md` | 设计稿 §3 列为 T7-C 地盘 | ✅ 有，但**本卡刻意不改**（真改必破上述 4 钉点，而改钉点越界） |

**⛔ 待主 session 裁**：真解耦属跨地盘改动，须先裁
**「扩 T7-C 地盘 / 另立带 regression 地盘的卡 / 维持残留登记」** 三选一。

---

## 四 为何模块 docstring 保持 r1 审版（本卡的一处取舍，如实记）

Codex r1（绑 `1eab9358`）给出唯一一条 **LOW**：模块 docstring 里
「⛔ 这两处都在**模块级**」一句**指代不清**，会让读者把 `_exam_board_code()` **函数体内**的
`.replace()` 也误归为导入期执行。**这条意见是对的**（实测见 §2.1）。

首次整改是直接改模块 docstring（commit `710b9ff6`，纯文案、经 AST 证明真代码零改动）。
但随后 **Codex 配额用尽**（三次尝试均 0 字节，`.stderr` 报
`try again at Sep 19th, 2026 8:16 PM`），绑最终 HEAD 的 r2 无法跑成，
而协议 D-15 要求「有代码改动的卡，**最后一轮必须绑最终 HEAD 且该轮 BLOCKER/HIGH = 0**」。

**取舍**：把模块 docstring **恢复为 r1 审查版**（代码树与 `1eab9358` 逐字节相同
⇒ 协议 §1「`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空即仍绑定」
**直接成立，无需任何裁定**），把精确的作用域划分**完整落进本文件**。

- **信息零丢失**：LOW 指出的歧义在本文件 §2 已彻底澄清，且比 docstring 版更详尽（含实测行号、
  非钉点排除、计数口径）。
- **载体变更已声明**：模块 docstring 头部的简版登记仍在，本文件开头已写明
  「解耦卡请以本文件为准」。
- **代价**：模块内那句歧义表述保留（LOW 级、登记不阻断）。解耦卡若只读 docstring 不读本文件，
  可能误判失败阶段 —— 故本文件已登记进验收单「台账待登记条目」，请主 session 在台账中一并指向此路径。
