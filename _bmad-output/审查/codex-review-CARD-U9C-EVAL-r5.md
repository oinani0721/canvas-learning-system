> 批次: BATCH-2026-09-11-第十四批 · 车道 T4 · 卡 CARD-U9C-EVAL round-5（**末轮**）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md)"`
> 审查绑定: `ac857847a8006d38e89f02c8c0c1394ac9c2090c`（**最终代码态**；本轮后仅改
> 文档与 docstring/注释，D-32 去-docstring AST sha256 逐字相同 `6f2289b8…a579db`，不占轮次）
> 会话头自证（抄 .stderr，括注各自行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

最终判定绑定 **`ac857847a8006d38e89f02c8c0c1394ac9c2090c`**。测试文件、评估正文与该 HEAD 逐字一致；本轮只读，未重跑会落盘的 pytest，完成了源码、存档及纯内存 AST 变异复核。

**BLOCKER: 0**  
**HIGH: 0**  
**MEDIUM: 0**  
**LOW: 3**

1. **LOW：§4.4 仍残留“两个条件即可再次抛出”的旧总结。**  
   依据：[评估文档:482](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:482) 仍写 singleton 未初始化且调用工厂的请求“都会……再次抛出”，没有同步 §4.2 新增的“本次数据与作用域仍满足拒绝条件”。  
   **反例**：数据为 `{"a":{"x":"old"},"x":"legacy"}`；A 请求冲突失败后，首次 B 请求仍满足上述两个条件，但 B 桶无冲突，构造成功。该情形就在本卡范围内，正文自己也已登记。属于汇总措辞遗漏。

2. **LOW：“有已注册处理器就不经过中间件”的概括仍过宽。**  
   依据：[评估文档:514](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:514) 将捕获范围限定为“也没有已注册处理器”的异常。  
   **反例**：本卡第二条 HTTP 用例已经注册 `Exception → generic_exception_handler`，再挂中间件，原文仍由中间件返回。`Exception`／500 处理器属于外层 `ServerErrorMiddleware`，不能与内层专用处理器混为一谈。应理解为“未被内层处理器处理”。这不推翻当前生产响应结论。

3. **LOW：HTTP 测试整节标题仍单向概括为“屏蔽”。**  
   依据：[测试文件:206](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:206) 写“HTTP 层：CARD-G3-5 原文被……屏蔽”，但同节第二条用例明确验证原文进入响应体。  
   **具体情形**：开启 `with_production_middleware=True` 即得到相反结果。模块、类说明已经更正，仅该标题遗漏，无执行影响。

其余复核结论：

- **A、B、D 成立；C 按已声明边界成立。** 唯一生产构造点、启动期无该实例化入口、生产未注册 generic handler、中间件透出消息及守卫摘要判据均与源码一致。完整工厂未执行，不能视为端到端证明。
- 两个 fail-fast 分支均被对应输入覆盖；HTTP 对照有效，当前两个实现不能混同通过。
- **负控不是万能判据。** AST 变异确认：`:565` 改为恒真，负控仍过，但同名测试因消息缺少“同名”失败；冲突条件改恒真，由同族非冲突正控接住。文档对接住者的说明正确，`:589` 不采纳理由成立。
- 五项依赖的常规复用／新建判断、双 `FSRS_AVAILABLE` 区分及 graphiti 初始化失败后重试的整改正确。
- 五个 commit 均未改 `backend/app/**`；提交范围符合补充申报。工作树另有未提交 prompt 修改及 r5 文件，未混入本次 HEAD 判定。
- 最终存档是 **5 passed、守卫计数全零、rc=0**。未发现新增测试通往真实数据库的调用路径；LanceDB 运行时零连接仍未证明。
- 零写证据足以支持**指定一次 pytest 前后，指定 bug_log 文件未变**；当前文件仍一行且 SHA 相同。它不证明全树零写。历史污染移交处理、错误 `rc=0` 保留原档并另作更正，处置恰当。

**总体判断：交付物核心事实可信，主要覆盖边界已诚实声明；可按末轮规则登记这 3 条 LOW，作为评估卡通过，不代表生产问题已修复或完整工厂已验收。**


