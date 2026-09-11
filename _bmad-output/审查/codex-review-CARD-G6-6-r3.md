> 批次: BATCH-2026-09-07-第十三批 · 车道 card-u6-reviewtime · 卡 CARD-G6-6 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-6-r3.md)"`
> 审查绑定: `1ccc971127179c6f589cd0a789afc1190274d4fb`（**末轮，绑最终 HEAD**；送审时工作区仅含本存档文件自身）
> 会话头自证（抄 .stderr 会话头含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `sandbox: read-only`

---

审查对象：`1ccc971127179c6f589cd0a789afc1190274d4fb`，相对指定 BASE。结论：**BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 2**。

全程未修改文件、未连接数据库或网络。验证采用源码对照、Python 纯函数探针及 Node 内存测试，未运行会创建文件的完整 pytest。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM：无。**

**LOW：**

1. **NUL 前缀仍存在跨动作键碰撞，round-3 LOW-1 未完全关闭。**  
   位置：[review_app.py:224](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_app.py:224)。

   具体反例：

   ```js
   snoozeKey("math", "A") === doneKey("snooze", "math\u0000A")
   ```

   两个库名都合法；NUL 在**板名**中。现有 `source_board` 解析、投影校验和端点板名校验均未拒绝该值。内存调用实际 `renderPage` 已复现：`math/A` 推迟请求在飞时，另一库 `snooze` 中该板的完成按钮被错误渲染为 `disabled`。

   新门 [test_review_app.py:3156](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_review_app.py:3156) 的第一、第三条断言分别防住旧冒号前缀、退回裸 `doneKey`；第二条只比较一个现实中不存在的含 NUL 库名，**没有覆盖上述反向碰撞**。源码使用可见转义本身正确；`doneKey` 两入参之间在真实库名约束下也没有该碰撞。

2. **Nuuk 新增说明把 DST 切换的 UTC 时刻写错。**  
   位置：[test_review_overview.py:4001](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_review_overview.py:4001)，同错见 `4015`。

   注释写 UTC 22:00，本机时区数据实测：

   - `2026-03-28 22:00Z` → 当地 `20:00−02:00`，尚未切换。
   - `2026-03-29 01:00Z` → 当地 `00:00−01:00`，此刻才切换。
   - 秋季同样在 `2026-10-25 01:00Z` 切换。

   **失败场景**：依照注释复建 UTC 边界夹具，会提前三小时，测到尚未切换的偏移。现有两组期望 offset `−1 / −2` 和夹具前提断言均正确，生产换算没有这个错误。

其余问题核对如下：

| 问题 | 结论 |
|---|---|
| 1．时钟与 DST | 未发现第三套时钟。已核纽约、Nuuk 四组；次日 offset 正确，UTC 往返后仍为目标当地零点。 |
| 2．损坏 snooze／金样 | 指定错型、naive、坏串、非字符串键、过期值均退化为空活跃集且不抛异常。两条金样保留完整 payload 深等与键序比较，能抓顶层新增键。 |
| 3．升级与缓存 | 空账、缺签名的 v2 state 不因升级白重扫；正常生成的 state 下，due 或 wake 任一越界都独立禁止缓存。**“必然”不覆盖人为损坏的唤醒标记**：例如改成数字 `1`，当前明确按无标记处理，可能继续缓存。 |
| 4．只读与极值 | 未发现 snooze 读链写盘路径；新增 picker 导入有禁写字节码保护。坏串、surrogate、极值换算具有降级处理，未复现 GET／页面 500。 |
| 5．FSRS 门 | 三项允许集保持严格相等，没有放宽。新增负控先确认请求成功及落账正确，再捕捉并检查 `_FSRS_GATE_MSG`，不是任意失败算红。 |
| 6．POST 与今晚布尔 | 两个新 POST 只接点击；timer／visibility 只走 GET。JS 无小时比较。**GET 与 POST 各读一次时钟，并非跨请求共享读数**；跨过 20:00 后 POST 返回 422 是已声明的竞态。 |
| 7．D-8 两项禁令 | 两页面及端点均无节点级、自定义时长入口；非法档位及过时“今晚”返回 422，没有静默夹档。 |
| 8．条件折叠 | 两条既有 `<details>` 精确计数门未改、未被屏蔽；空推迟区不输出，同板完成且推迟只进入完成区。 |
| 9．AST／枚举门 | 两张白名单各仅新增 `_SNOOZE_NOTE`；检查器及探针矩阵未动，文案仍共享注入。四条枚举门是在严格集合和归属检查中登记新端点。 |
| 10．schema 断言 | 替换处均检查升版结果，输入夹具的版本字面量仍保留，另有实值门钉住 3。准确数量为 **6 条断言**，不是自述的 5 条；处置本身正当。 |

round-3 LOW-3 的两条渲染门确实独立承重：分别只变异取回、只变异推迟，两次均为 **6 绿、对应 1 红**。未发现第三处 snooze busy 渲染分支；推迟与取回共用同一键的语义保持不变。


