> 批次: BATCH-2026-09-07-第十三批 · 车道 U5 · 卡 CARD-G3-3-R2-writer-boundary round-5（末轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-3-R2-writer-boundary-r5.md)"`
> 审查绑定: `61590b3b`（**最终 HEAD**，本轮 BLOCKER=0 且 HIGH=0 ⇒ D-15 通过条件满足；轮次上限 5 已用尽）
> 会话头自证（抄 .stderr 前三行 + model 行，stderr 本身不入库）:
> `Reading additional input from stdin...` / `OpenAI Codex v0.153.3` / `--------`（续 `model: gpt-6-astra`）
---
绑定 **`61590b3bf0ac9954dfbab48b0b2569e91643bba1`**，指定两文件与该提交一致。仅静态复核，未运行测试、写操作或连接网络、数据库。

**round-4 的四处空白收窄已闭合，但仍有 3 项 MEDIUM 必须闭合，不能判定解析已无静默换树／回退路径。** 以下反例均为静态推导，未执行复现。

**BLOCKER：无。**

**HIGH：无新增发现。** 此结论限于指定差分、片段及前四轮存档，不构成完整写入链重新认证。

**MEDIUM：3 项，均必须闭合。**

1. **[SKILL.md:437](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/canvas-vault/.claude/skills/quiz-answer/SKILL.md:437)**：`normpath` 在检查目录前按字符串消去 `..`，可能改变含符号链接路径实际指向的树。  
   **观察：** 对 `/A/link/../repo`，若 `/A/link → /B/child`，操作系统逐段解析指向 `/B/repo`，代码却得到 `/A/repo`；后者具有 `backend/scripts` 就会被采用。

2. **[SKILL.md:425](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/canvas-vault/.claude/skills/quiz-answer/SKILL.md:425)**：引号正则不识别转义引号，仍可能把引号内部的 ` #...` 当成注释并截短路径。  
   **观察：** 有效配置 `harness_tree: '/A/repo'' #alt'` 的 YAML 值是 `/A/repo' #alt`，正则却捕获 `/A/repo'`；截短后的树具有 `backend/scripts` 即放行，双引号中的 `\"` 后接 ` #` 也有同类问题。

3. **[SKILL.md:397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/canvas-vault/.claude/skills/quiz-answer/SKILL.md:397)**：只识别列首精确拼写 `harness_tree:`，会把有效 YAML 中明确提供的同名键当成没有配置。  
   **观察：** `harness_tree : /B` 或 `"harness_tree": /B` 均不会赋值给 `_raw`，随后 `:432–433` 静默回退父目录；父树可用且不同于 `/B` 时即选错树。允许读取面及前轮存档没有明确豁免这种回退。

**LOW：登记即可。**

- **[test_g3_2_review_ledger.py:6967](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/regression/test_g3_2_review_ledger.py:6967)**：TAB 的 docstring 已纠正，但参数旁注释仍保留“真 YAML plain scalar 禁 TAB”的泛化表述，文字整改尚未完全一致。  
  **观察：** 直接对照该注释与 `:6991–6992` 明确反对这一泛化的正文即可。

- **既有 L7，见 [round-2 存档:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/_bmad-output/审查/codex-review-CARD-G3-3-R2-writer-boundary-r2.md:39)**：科学计数法的 YAML 类型往返问题继续登记，本轮没有重新验证。  
  **观察：** 前轮记录的 `1e-6 → 1e-06 → 字符串` 问题，不能由已采样评分流程成功推导为消失。

逐段检查结果如下：

| 阶段 | 改动哪些字符／值 | 对树指向的判断 |
|---|---|---|
| 读取、键值正则 `:389–399` | 去掉行尾 CR/LF；值两侧仅剥 SP/TAB | Unicode 空白遗漏已修；未识别键仍有上述 M3 |
| 引号分支 `:425–427` | 去掉匹配的外层引号及尾注释，保留捕获内容 | 普通引号内空白、`#` 保留；转义引号存在 M2 |
| 值首 `#` `:428–429` | 真正以 `#` 开头的裸值变为空值 | 注释回退合理；`U+3000#alt`、`NBSP#alt` 不再误入 |
| 注释剥除 `:431` | 删除首个 SP/TAB 分隔的 `#` 及后文 | `/repo<U+3000><SP>#alt` 现在保留 U+3000 |
| `strip(" \t")` `:431` | 仅删除裸值两端 SP/TAB | 不再删除 U+3000、NBSP 等路径字符 |
| 空值回退 `:432–433` | 空值返回父目录 | 空引号、仅注释属于既定行为；`:400–401` 还将读取 `OSError` 当空配置，下游是否阻断未核验 |
| `expanduser`、相对路径拼接 `:434–436` | 展开开头的 `~`；相对路径加上 VAULT 前缀 | 不删除 Unicode 空白或 `#`；展开失败的语义见下文 |
| `normpath` `:437` | 合并分隔符、去掉 `.`、归约 `..` 等 | 无符号链接且中间目录有效时通常保持指向；不能一般化，见 M1 |

**`expanduser` 与 `normpath` 不能一概视为保持树身份。** POSIX 下缺少 `HOME` 时，`expanduser` 通常查询当前 UID 的账户主目录，并非直接回退 VAULT 父目录。未知 `~user`、或无法获得账户主目录时，可以保留原串，随后被当成 VAULT 内相对路径；对应字面目录存在便可能通过。空 `HOME` 还可能令 `~/repo` 展开为 `/repo`。这些需要明确展开契约，可登记；现有证据不足以把所有此类结果独立判为缺陷。`normpath` 则已有上面的确定反例，也会消掉 `/A/missing/../repo` 中不存在的中间目录，使原本不可达的路径变得可用。

**新增的 Unicode 子串断言有承重，但不能唯一绑定拒绝层。** [测试文件:7046](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/regression/test_g3_2_review_ledger.py:7046) 能排除“吞掉 Unicode 字符后，只报告截短路径”的假绿；当前 `:439` 的预期拒因确实输出计算后的 `_tree`。

不过，断言搜索的是整个 stderr。**如果旧门错误回退后，其他层回显原配置并拒绝**，`harness_tree`、`<lead>#alt`、非零退出、零账本和快照不变仍可能同时成立。指定读取面不包含全部 stderr 来源，因此这个条件性假绿尚未排除，不能声称已经实际发生。两个新增参数也不覆盖上述引号、键识别及 `normpath` 问题。

三件产物中，`self_confidence_norm` 与 `event_id` 门本轮未改，前轮可见范围的结论没有被此次差分推翻；完整数据流及测试辅助函数没有重新审计。**本轮必须闭合的是上述 3 项解析 MEDIUM；TAB 残留措辞及既有 L7 可继续登记。**
