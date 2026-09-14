> 批次: BATCH-2026-09-11-第十四批 · 车道 T3（`card-t3-review`）· 卡 CARD-G6-9c-R2 round-6（⚠️ 超协议上限 5，理由见 prompt §〇）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`--version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R2-r6.md)"`
> 审查绑定: `08100483 → 0e456454`（送审时 HEAD = `0e456454`，代码面 = `a7e11469`；本轮审后又改代码至 `cb1d6e9f` ⇒ **不绑最终 HEAD**，另送 round-7）
> 会话头自证（抄 `.stderr` 中含版本 / model / reasoning 的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（L2） / `model: gpt-6-astra`（L5） / `reasoning effort: ultra`（L9）

---

结论：**1 HIGH + 1 LOW，均为「本卡新增」**。r5 的启动异常已修复，但同一输入现在会导致总览响应序列化失败，因此本轮不能判定“无新增 HIGH”。

审查绑定 `08100483 → 0e456454`；结束时 HEAD 和审查文件均未变化。

- **BLOCKER：无。**

- **HIGH／本卡新增：非 UTF-8 `TZ` 的代理字符进入响应，导致总览响应失败。**

  引入点：[display_tz.py:192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:192)、[local_tz.py:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:193)。`surrogateescape` 让解析成功，但 `_PosixTZ.key` 保留了代理字符；[review_overview.py:1164](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:1164) 将其原样放入响应。

  **复现：**清除 `CANVAS_TZ`，设置 `os.environb[b"TZ"]=b"<\xff>0BBB"` 并 `tzset()`，将真实 `_display_tz_name()` 返回值送入该路由的响应序列化器。

  | 版本 | 返回名字 | 响应序列化 |
  |---|---|---|
  | BASE | `"UTC"` | 成功 |
  | HEAD | `"<\udcff>0BBB"` | 失败 |

  真实 `JSONResponse` 抛 `UnicodeEncodeError`；FastAPI 的 `dump_json=True` 路径抛包含同一编码错误的 `PydanticSerializationError`。`b"AAA0<\xff>"` 同样复现。**启动校验通过了，响应出口仍然失败。**本次验证了真实解析函数及路由序列化边界，未发送 HTTP 请求。

- **MEDIUM：无。**

- **LOW／本卡新增：新增测试注释对收集失败的解释不准确。**

  [test_g6_9c_single_tz_source.py:643](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:643) 声称这些 bytes 不能直接参数化，否则生成 pytest ID 会抛异常。**复现：**直接参数化两个非 UTF-8 bytes，当前 Python 3.14.4／pytest 9.0.2 成功收集 **2 项，退出码 0**，ID 自动转义。

  同文件 [第 656 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:656) 描述的代理字符 docstring 编译失败现象成立，但无需 pytest rewrite：直接 `compile(bytes_source, ..., "exec")` 就能触发异常。

r5 五条整改的核验结果：

| 条目 | 判定 |
|---|---|
| H1 | **原启动异常已解决**；真实环境字节下未再发现 `display_tz()` 本身的新异常，但存在上述响应失败 |
| M1 | **已解决**：NUL 拒收；删除检查后原门失败 |
| L1 | **已解决**：南半球新增用例确实击中 `year + 1` 上界 |
| L2 | **已解决**：`e(Y+1)` 可滚入 `Y+2` 的解释与实测一致 |
| L3 | **已解决**：两处总括现在符合测试与 libc 对照结果 |

新增门的独立验证使用原测试函数和内存变异：

- 非 UTF-8、极值年份、十九拒例：**44/44 PASS**。
- 改回严格编码：**4/4 被门拦住**。
- 南支 `elif year < 9999` 改为 `else`：**2/2 被门拦住**。
- 删除 NUL 检查：**2/2 被门拦住**。

因此两个门能守住所声明的函数级防线；**非 UTF-8 门没有检查返回名字能否序列化，无法拦住本轮 HIGH。**

补充边界：直接向解析器传入包含 `U+D800` 的字符串，HEAD 仍会抛编码异常，BASE 返回 `None`；这是**本卡新增的内部异常差异**。但真实环境字节不会解码成该码位，JSON 生产入口也已有严格 UTF-8 校验提前拒收，故不另计为生产 HIGH。

第三节六项仍按**「既有」**处理，不计新增 HIGH；其中南半球极值年份已从 BASE 抛错变成 HEAD 不抛，但完整范围支持仍未得到保证。其余采样未发现新增错误接受或候选年回归。

全程只读，未连接网络或数据库；未执行完整归日链路，也未运行会改文件的二十段负控脚本。第六轮超出原协议上限的事实保留，交主 session 裁定。


