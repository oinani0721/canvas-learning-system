> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-12 round-1
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-12.md)" > _bmad-output/审查/codex-review-CARD-G5-12.md 2> _bmad-output/审查/codex-review-CARD-G5-12.stderr </dev/null`
> 审查绑定: `371c21ae`（不绑最终 HEAD——其后代码已按本轮意见整改（r1-M1/L1/L3），移交 round-2）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

# 复核结论：PARTIAL（可收口，但有覆盖边界）

绑定核验：当前 HEAD 确为 `371c21aed0e35b04d97aa0fb2ef1c1d652b4ad23`；`1191dc1f..371c21ae` 排除 `_bmad-output` 后恰为 `backend/tests/regression/test_sync_board_concepts.py`，+132/-0。tracked 文件干净；现存 untracked 均为本轮审查/evidence 文件。脚本 sha256 实测为 `282b7a968033f622cba03fae57e4330424c2465ad08d73f5abdc8f3162f6d123`，与 `backend/tests/skills/skill_portability_lint.py:3217` 一致。遵照只读边界，本轮未运行 pytest/写盘测试；测试结论来自源码推理加存档交叉核对。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

### MEDIUM-1：`_user_region` 的 `_CONCEPT_LINE` 排除面宽于脚本真实收编集合

- `file:line`：`backend/tests/regression/test_sync_board_concepts.py:59-75`；对照 `canvas-vault/.claude/scripts/sync_board_concepts.py:48`、`:383-412`、`:434-445`
- 缺陷：测试 helper 对**全文**所有匹配 `^\s*-\s*\[\[([^\]]+)\]\]` 的行都排除，而脚本只在 `## Concepts` 段内处理这类行，并且围栏行豁免、稳态成员行带自定义文字时保留；因此“用户文字区 sha256”并非覆盖所有用户文字形态。
- 复现思路：未被拦下的输入包括带批注的成员行、围栏内的成员清单行、以及其他段落里的清单形用户文字；这些行即被脚本改写或被未来回归误删，h1/h1b 的新 hash 也不变。既有 a1/a2/b1 只对部分子串形态兜底，不是字节级覆盖。

## LOW

### LOW-1：h1b“第二遍写盘”实际是写模式 no-op，不是第二次落盘证明

- `file:line`：`backend/tests/regression/test_sync_board_concepts.py:248-254`；对照 `canvas-vault/.claude/scripts/sync_board_concepts.py:557-559`、`:687-689`
- 缺陷：测试内第二次 `_sync` 确实未带 `--check`，但第一次同步已把尾巴拆行收敛，第二遍会因 `_strip_stamp` 等价而返回 `old == new`，`main()` 直接打印已同步，不会走 `atomic_write`。
- 复现思路：门未覆盖的路径是“已收敛文件再次写模式运行”；第三串 hash 证明的是写模式 no-op 不改变用户区，不能证明第二次实际覆盖写仍保留用户区。

### LOW-2：sentinel 尾巴的前导空白会被脚本和 hash 门同时归一

- `file:line`：`backend/tests/regression/test_sync_board_concepts.py:65-70`；对照 `canvas-vault/.claude/scripts/sync_board_concepts.py:341-345`
- 缺陷：脚本对 `-->` 后尾巴执行 `lstrip()`，helper 也同样 lstrip，因此 Markdown 缩进等前导字节的丢失不会让 hash 变红；“逐字节”承诺对这一子集实际是“非空文字逐字节”。
- 复现思路：未被拦下的输入是 `-->    - [[节点/甲]] — 我的批注` 这类带前导空白尾巴；同步后缩进消失但 hash 不变。若验收口径包含 Markdown 结构字节，应另立缺陷卡；仅按文字内容防丢失，则本卡登记不改可接受。

### LOW-3：helper 敏感性自测没有真正覆盖 `_EMPTY_HINT` 排除分支

- `file:line`：`backend/tests/regression/test_sync_board_concepts.py:267-289`
- 缺陷：自测覆盖用户行删除、END 机器头、成员行收编、尾巴粘行/独立行映射，但样板板始终有成员行，没有任何 `_EMPTY_HINT` 对照。
- 复现思路：未被拦下的输入是 helper 回归为不再排除 `_EMPTY_HINT`；此时 `test_g512_user_region_hash_is_sensitive` 仍会通过，无法证明该排除分支非空转。

## 关键命题核对

- **脚本零改动**：PASS。diff 恰 1 个测试文件；脚本 digest 与 lint 锚一致。
- **新增断言当前绿、红来自负控**：PASS（存档口径）。开工 `40 passed / collected 40`，收工 `41 passed / collected 41`；负控 1b/2 的 traceback 均落在新增 `hexdigest` 断言。负控 2 同变异态下 h1 仍绿，也符合“红只针对拆尾层”的表述。
- **负控 1a 判定**：PASS。对会进入 `doomed` 的拆尾，前序 sentinel mark 已把 `insert_at` 放在尾巴之前，`:533-539` 的 `head_idx` 会回插；若 sentinel mark 因围栏被跳过，该行及尾部也不会进入删除循环。因此未找到 `:456` 减法是唯一保命线的路径，登记为纵深保护而非缺陷是合理的。
- **测试保留与新增**：PASS。既有 25 个 test 函数未删改，现为 26 个；新增仅 `test_g512_user_region_hash_is_sensitive`，既有断言仍在 hash 后保留。
- **写入方清单**：PASS（限 tracked 静态读取面）。`appendBoardLines` 四个调用点都读取白板后走同一实现；该实现插入在 `## Concepts` 后第一个 `\n## `、`\n---` 或 `\n```dataviewjs` 前。模板方面，TS 源文本因 `\`` 转义不是原始字节相同，但 template literal 求值后的 sentinel 四行 Markdown 语义相同；census 若表述为“源文件逐字同”则不严谨，表述为“发射块文本逐字同”则成立。
- **`--all` / `--backup`**：未发现独立缺陷路径；两者复用同一 `sync_board` 产物，backup 只是写盘前额外保留最早 `.bak`。但 h1/h1b 的字节门确未直接参数化这些 CLI 模式，当前只能靠核心函数等价性推断。

计数：`BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3`


