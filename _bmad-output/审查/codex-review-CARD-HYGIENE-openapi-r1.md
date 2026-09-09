**限定读取面内确认 1 项 LOW；整体为部分验证。** 未修改文件、运行端点或连接数据库及外部服务。

- **LOW — [backend/tests/contract/test_openapi_contract.py:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/contract/test_openapi_contract.py:42)**  
  维护者按此处注释判断覆盖面时，会读到过时的“保留 93／排除 113”；当前实际为 **92／114**，过滤行为不受影响。

五个问题的核对结果：

1. **过滤范围：本节无已确认缺陷。**  
   独立解析三份清单，确认改前 206 条、改后 92 条，114 条排除项严格等于差集；方法分布与自述一致，没有新增 operation，`GET /` 保留，唯一排除的 GET 是 `/api/v1/health/lancedb`。  
   `POST /api/v1/rag/query`、`POST /api/v1/multimodal/search`、`POST /mcp/tools/read_note` 等只是纯查询候选，名称不足以证明没有副作用。其实现不在读取面内，**语义未验证**；即使确属纯查询，排除也符合本卡“全部 POST 排除”的明确目标。

2. **剩余 GET 的间接写：未验证。**  
   扫描证据只有 handler 总数、装饰器分布和一条命中，没有完整的 handler→operation 映射，也没有 service 调用链。因此只能确认两边总数都是 93，不能独立确认“逐一对齐”，更不能确认剩余 92 条无间接写。当前证据不足以提供真实写入路径的 `file:line`。

3. **路径推导：本节无已确认缺陷。**  
   [conftest.py:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/contract/conftest.py:34) 指向 fixture 实体所在的 `backend/`。从仓根、`backend/` 或经整棵仓库／backend 的 symlink 起跑，结果一致。若仅将 `tests/contract` 跨 checkout 链接，则指向链接目标的 backend；现有证据未显示这种布局。

4. **目录排除：问题前提需要纠正。**  
   [conftest.py:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/contract/conftest.py:38) 没有三条排除规则，而是只检查 `CLAUDE.md/raw/wiki/outputs/test_canvas` 五个顶层名称。写进 `.venv/`、`.hypothesis/`、`__pycache__/`、`data/lancedb/` 或其他未列名称，均不会触发断言。  
   这是卡片声明的检测边界，本节无新增缺陷；它只能证明五项在模块开始／结束检查时不存在。`--collect-only` 不执行该 fixture。

5. **历史配置块的实际影响：未验证。**  
   根 `pyproject.toml` 不在允许清单内，也未出现在指定 diff 中；Schemathesis 4.14.3 的配置加载源码同样未获准读取。目前只能确认测试显式设置 `max_examples=10`、`deadline=10000`、两个 Hypothesis phase 和四项检查，无法据此裁定历史配置是否被加载或覆盖。

第 1 项语义复核及第 2、5 项需要的定向补读请求尚待答复；遵照你的“不要扩大读取面”要求，这些项保留为未验证。
