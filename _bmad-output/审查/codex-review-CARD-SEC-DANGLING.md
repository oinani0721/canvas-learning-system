> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-D (card-t5-bugs) · 卡 CARD-SEC-DANGLING round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SEC-DANGLING.md)"`
> 审查绑定: `c5e30cfc5e6681076d9bac8cc37c8792545eb1c6`（该轮送审时的 HEAD = 本卡代码 commit）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:261-264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`

---

方案 A 的代码链成立；独立比较指定两份 committed 快照，确认 **31 处悬空全部消失，其中 `/system/*` 16 处**，其他差异仅为生成时间戳。新断言的覆盖和隔离主张仍有以下边界。

本次未运行项目测试、hook、应用或数据库连接，也未写文件；历史运行结果只作为存档证据核对。

**BLOCKER：0 条。HIGH：0 条。**

**MEDIUM：2 条。**

1. **⓪ 枚举遗漏合法的嵌套 Operation。**  
   [test_openapi_contract.py:248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:248)、`:260` 只遍历根节点和直接 `paths`，遗漏：
   - `webhooks.<name>.<method>.security`
   - `components.pathItems.<name>.<method>.security`
   - `paths.<path>.<method>.callbacks.<name>.<expression>.<method>.security`
   - `components.callbacks.<name>.<expression>.<method>.security`
   
   这些结构的递归 callback 和 `$ref` 目标也未处理。它们属于合法 OpenAPI 结构；当前快照没有这些面，因此不否定本次 31 处修复。[规范依据](https://spec.openapis.org/oas/v3.1.0.html#components-object)

   **复核思路：**保留一个正常直接 operation，再分别在上述位置放入未声明方案名，沿当前循环推导可见三个前置条件通过、悬空引用却未被枚举。

2. **④ 完整收集路径没有被 socket 禁闭覆盖。**  
   [test_openapi_contract.py:218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:218) 的主张忽略了模块级 `:18` 导入，以及 `:79` 的 `from_asgi(...)`。二者先于新增门进入 `load_live_schema()`；其中 `from_asgi` 会通过 ASGI 客户端 GET schema。[对应版本实现](https://raw.githubusercontent.com/schemathesis/schemathesis/v4.14.3/src/schemathesis/openapi/loaders.py)

   因而存在**未被该禁闭覆盖的导入、请求及 schema 生成阶段**；`main.py:545` 的缓存还可能让后续受保护调用直接返回此前结果。这不证明实际连过库。脚本也仅替换 `socket.socket.connect`，不能据此保证所有网络入口均被封锁。

   **复核思路：**按模块执行顺序标出首次导入、`from_asgi`、进入禁闭和缓存返回的位置，区分 helper 内保护与完整收集路径保护。

**LOW：2 条。**

1. **⓪② 非 operation 字典会冒充 per-op 引用。**  
   [test_openapi_contract.py:261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:261)、`:289` 没有筛选 HTTP 方法。Path Item 下合法的 `x-*` 扩展若包含 `security` 数据，会造成误红，也能满足 `per_op_refs` 非空条件。直接放置的非标准方法字典同样会被遍历，并非漏检；但它们不是 OpenAPI 3.1 标准 operation。[Path Item 规范](https://spec.openapis.org/oas/v3.1.0.html#path-item-object)

   **复核思路：**令唯一真实 `get.security=[]`，同级加入 `"x-audit-data":{"security":[{"InternalApiKey":[]}]}`，当前算法仍会计出一个 per-op 引用并通过。

2. **④ 新静态门仍依赖 schemathesis 的模块级可用性。**  
   [test_openapi_contract.py:17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:17) 的 `pytest.importorskip("schemathesis")` 会在依赖缺失时连同新增门一起跳过。当前存档确实执行通过，不能报告为当前已跳过。

   **复核思路：**沿模块级 `importorskip` 的提前退出路径，确认新增 nodeid 能否被收集。

其余问题的判断如下：

- **① `scheme_name`：官方 FastAPI 0.135.3 实现下成立。** [security.py:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/security.py:63) 改的是方案标识；header 提取读取 `self.model.name`，缺失值处理读取 `auto_error`，依赖缓存键也不使用方案名。结合精确 diff，未发现改变 header、fail-closed 判定或 `auto_error` 语义的路径。[APIKey 实现](https://raw.githubusercontent.com/fastapi/fastapi/0.135.3/fastapi/security/api_key.py)、[依赖缓存实现](https://raw.githubusercontent.com/fastapi/fastapi/0.135.3/fastapi/dependencies/models.py)  
  **复核思路：**追踪构造参数的赋值及运行时读取点。限于读取面，本次没有独立打开本机安装包，不能把作者的本机属性日志称为本次实测。

- **② 实际已有三条前置断言。** `test_openapi_contract.py:279、285、290` 分别检查声明、引用、per-op 引用；“两条”的注释未同步。没有上述扩展字典干扰时，全部 per-op 缺失或均为 `[]` 会红。保留一个正常 per-op、其他改成 `[]` 则仍绿，但这是鉴权需求覆盖的变化，不是悬空方案名；规范允许 `security: []` 取消全局要求。[规范语义](https://spec.openapis.org/oas/v3.1.0.html#operation-object)  
  **复核思路：**分别推导“全部空”和“部分空”的引用集合，区分缺失要求与未声明方案。

- **③ 快照没有夹带其他漂移。** [openapi.json:15852](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/openapi.json:15852)、`:17166` 起，独立类型敏感结构比较确认：31 对同位置的 `APIKeyHeader: [] → InternalApiKey: []`，另有时间戳变化。保留空容器后的叶子数为 `12435/12435`，与修正版证据相符。修正版统计可以支持本次结果；一般判据还应逐对检查改名位置和值，不能只比较删增数量。  
  **复核思路：**直接比较键集合、容器类型和对应值，让空列表本身参与比较。

- **④ 同源成立，但不等于独立重新生成。** 新门 `:276`、漂移门 `test_openapi_snapshot_drift.py:60`、再生入口 `check-openapi-drift.py:280` 都调用 `load_live_schema()`；缓存与收集阶段的边界见 MEDIUM-2。  
  **复核思路：**沿三个调用点追到 `app.openapi()`，再核对缓存分支。

- **⑤ 不使用全量 schemathesis before/after 证明这项静态性质，取舍成立。** `test_openapi_contract.py:99、213`：直接引用检查、负控和快照比较提供更直接的证据。不过指定存档只能确认 health 契约出现超时，不能独立推出“每个 operation 恒为 16–19 秒并超时”。  
  **复核思路：**区分日志实际覆盖的 operation 与被外推的范围，并判断证据是否直接检查方案声明关系。

- **⑥ 两条格式判据单独并非充分证明，结合本次单点插入可支持归因。** `security.py:54` 起仅增加十行；`ruff-format-preexisting-20260916T195125.txt:3` 起记录多重集相同、格式修改区域不相交。但多重集丢失位置，行号不交集也不能单独排除远处连带变化；存档缺少两份原始格式 diff，本次不能独立重算“零新增”。  
  **复核思路：**在同版本、同配置下，将改前改后格式差异映射到对应位置逐 hunk 比较；本次仅确认存档与提交 diff 相容。

- **⑦ 给出的两个 glob 确实不匹配 `security.py`。** `UAT-CARD-SEC-DANGLING-2026-09-16.md:217` 引述的两个集合均排除该路径，`lefthook-precommit-20260916T200333.txt:45`、`:46` 也记录两门跳过。本次未超出清单读取 `lefthook.yml`，因此结论限定为引述配置与原始日志一致。  
  **复核思路：**展开两个 brace 集合逐项匹配目标路径，再核对原始跳过输出。


