# 一 背景与最小读取面

你在只读审查一个 Python 后端仓库的一张卡：`CARD-PYRIGHT-DEBT-rest`（批次 BATCH-2026-09-07-第十三批）。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u2-pyright-rest`

这张卡的范围是**把 `backend/app` 里非 `services/` 的 pyright 报错清到 0**，纪律是**只做类型层改动，不改运行期行为**。
它分三阶段；本轮审的是**阶段 0 + 阶段 1**（阶段 2 还要合并候选树、再清两个共享文件，所以本轮**不绑最终 HEAD**）。

**请只读下面这些**（不要全仓漫游）：

1. `pyrightconfig.json`
2. 本卡代码 diff：
   `git diff da690bf8 HEAD -- pyrightconfig.json backend/app ':(exclude)backend/app/services'`
3. 新增测试：`backend/tests/unit/test_exam_models_rubric_required_u2a.py`
4. ignore 清单与结构性修复说明：`_bmad-output/审查/evidence-pyright-rest/ignore-table-p1.md`
5. AST 位置默认扫描前后：`_bmad-output/审查/evidence-pyright-rest/field-positional-base-*.txt` 与 `field-positional-p1-*.txt`
6. 多重集对照两份的末行：`_bmad-output/审查/evidence-pyright-rest/multiset-p0-state1-*.txt`、`multiset-p1-state2-*.txt`
7. openapi required 差集输出：`_bmad-output/审查/evidence-pyright-rest/openapi-required-diff-p0-*.txt`
8. 验收单：`_bmad-output/验收单/UAT-CARD-PYRIGHT-DEBT-rest-2026-09-08.md`

# 二 作者自述（请独立核对，别默认为真）

1. **`extraPaths: ["backend/lib"]` 是解析器搜索路径配置，不是关闭规则**。依据：`backend/lib` 在运行期由 7 个真实 `sys.path.insert` 调用点挂载。它只影响 import 解析、不影响"检查哪些文件"。
2. **`models/**` 与 14 个其他文件的位置默认改写语义零变化**：只在第一个位置实参前插入 `default=`，默认值表达式逐字不动，其余关键字实参原样。做法是按 AST 取该实参的**字节偏移**后插入。
3. **真 bug ①（`AutoScoreResult` 四个 rubric 维度必填化）不改成功路径**：两个实例化点 `services/autoscore.py:141` 与 `:197` 都显式传四维；`RubricDimension.score` **没有**加默认 0。
4. **勘探稿的"真 bug ② `metadata.py:467`"经复核不成立**，它是位置默认假阳，阶段 0 机械改写顺带清掉。
5. **`claude_client.py` 的 `hasattr(block,"text")` → `isinstance(block, TextBlock)` 不改分支顺序、不改语义**：依据是 anthropic 0.88.0 的 `ContentBlock` 联合 12 个成员里只有 `TextBlock` 声明 `text` 字段。
6. **`app/config.py` 零改动**：`provider_factory.py:256/:261` 走行级 ignore（TAIL T14），没有给 `Settings` 加 `OPENAI_API_KEY` 字段。
7. **发现 4 处真缺陷但一处没修**，全部只让类型过门 + 登记：`edges.py:106`（`Neo4jClient` 无 `execute_query`）、`infra_tools.py:56/57`（`switch_vault` 恒返回 `JSONResponse`）、`boards.py:86` 与 `board_manifest_tools.py:67`（`except pydantic.ValidationError` 是死分支）。作者刻意**不用 `cast`** 覆盖后两类，理由是 cast 会把真缺陷永久盖住。

# 三 请按重要性排序回答的问题

1. 25 条 `# pyright: ignore` 里，有没有哪一条**盖住了真错误**而作者把它写成了假阳？特别看 `edges.py`、`infra_tools.py`、`metadata.py`、`health.py`。
2. 4 处 `assert x is not None`（`metadata.py` ×2、`intelligent_parallel.py` ×1，以及 `neo4j_client.py` 的 `driver` 绑定）是否都落在"原本遇 None 也会崩"的位置？有没有哪处 assert 实际改变了控制流或掩盖了可达的 None？
3. `AutoScoreResult` 四维必填化有没有遗漏的实例化点（含测试、含 MCP 工具、含任何 `model_validate` / `**dict` 形式的实例化路径）？
4. openapi 除 `required` 之外有没有形状变化被漏掉？作者只证了 `--snapshot` 无漂移 + `required` 差集为 0 + schemas 无增删，没有逐键比 `description`/`examples`。这个证明强度够不够支撑"位置默认改写不动 schema"这个结论？
5. `intelligent_parallel.py` 改成 `if TYPE_CHECKING:` 导入 + `get_service()` 返回注解 + `assert`，有没有引入循环 import 风险或改变单例语义？
6. `middleware/llm_call_logger.py` 的条件基类改成 `TYPE_CHECKING` 分叉后，litellm 缺席时的降级路径是否真的还在？
7. 位置默认机械改写有没有漏改或误改（例如 `Field(..., )` 必填形态被误动、`default_factory` 被动过、多行形态改坏）？
8. `claude_client.py` 把 `content_blocks` 从 `List[Dict[str, Any]]` 收紧为 `List[ContentBlockParam]`——这个收紧会不会在某些输入形态下把原本合法的实参形态判成不合法（注意 `img.get("media_type", "image/png")`）？
9. 阶段 1 末 `api` 包不是 `0 errors`（剩 `exam.py` 10 + 两个共享文件 11）。作者把这写成"按卡文延后"，请判断这是不是在放宽判据。

# 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 四级，每条给出 `file:line` + 一句问题陈述 + 一句"为什么它会真的出问题"（具体的输入或状态 → 具体的错误结果）。没有就写"无"。

# 五 边界

- 只读。不要修改任何文件。
- 不要连接任何数据库（Neo4j 7691/7687、LanceDB）。
- 不要跑 `tests/integration` 或 `tests/e2e`。
- `backend/app/services/**` 的 pyright 残余**不在本卡范围**（那是并行的另一张卡 U1-A）。
- `review.py:1543` 族（对 dict 取属性）是已知的 api 侧真 bug，**不在本卡范围**，阶段 2 也只登记不修。
