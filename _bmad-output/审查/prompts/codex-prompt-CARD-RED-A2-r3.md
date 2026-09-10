# CARD-RED-A2 独立复核请求 round-3（第十三批 / 车道 U10 末卡）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
审查绑定：`052a9289..88a15609`（代码 commit：`fe3787ce` 初版 → `0b9be419` r1 整改 → `88a15609` r2 整改）

## 一 本轮唯一改动

round-2 判定 BLOCKER/HIGH/MEDIUM 全 0，仅 2 条 LOW（均为我方**表述**问题）。本轮只针对
其中写在**代码注释里**的那一条做了更正，**无行为改动**：

**round-2 LOW-2 已接受并改正**：原注释写「`NEO4J_PASSWORD` 断言 Field 默认 `""` ——
同时证明该档没从真 `.env` 取值」。经核对：结论对、理由错。你的反例成立 —— `.env` 里
不设这个键、只设别的键时该字段同样是 `""`，单字段断言与「不读 `.env`」之间没有蕴含关系。
注释已改为如实说明：依据是 `model_construct` 本身不走 `BaseSettings` 的取值链，四条自检
断言只确认字段值符合预期、不承担那个证明。

**round-2 LOW-1 已接受，登记不改代码**：我方拒绝 `model_copy` 的理由（「合法基底必然合并
`.env`」）**不成立** —— `Settings(_env_file=None, ...)` 可禁用 `.env`。已在验收单改为：
保留 `model_construct` 是取舍而非必然，两条路径都不是正常启动路径；并记下你补充的区分
「禁 `.env` 不等于禁进程环境变量」。

## 二 请核对的点

1. 更正后的注释（`test_sync_batch_auth.py` 与 `test_system_endpoint_auth.py` 的
   `_settings_factory` 内）是否仍有把推断当事实的地方？
2. 本轮确为纯注释改动、无行为变化？（`git diff 0b9be419 88a15609`）
3. round-2 里你给出的两点边界，我方拟按下列表述写入验收单与台账移交条目，请判断是否准确：
   - 「`L2-funcname` 证明的是『改错函数名会红』；由于完整标记已排除 WebSocket 侧，
     `funcName` 条件属**防御深度**而非独立不可省的必要条件。」
   - 「本卡判据锁的是『那条日志记录与那个响应出现了』，锁不住『`security.py` 那个分支
     条件被求值为真』—— 若把该 `if` 删除、令 logger 与 raise 无条件执行，三条仍会全绿
     （同文件其余 403/200 用例会捕获这种改动）。这是负控的覆盖边界，如实登记。」
4. 还有没有别的未被前两轮覆盖的假绿面或失实表述？

## 三 其余自述（沿用 round-2，已独立复核过的不必重验）

生产代码零改动；改动面只有那两个测试文件；只改 `debug=False and key==""` 一档的实例化方式；
两文件 17 passed；`tests/unit` 目录级 120 failed → 117 failed，相对本卡开工快照的 nodeid diff
只有 3 条 `<`（恰为目标三条）、无 `>` 行、29 errors 不变；判据计数 sync=1 / system=2 / 合计 3；
裸 `in caplog.text` 判据残留 0；五段负控存档见 `evidence-red-a2/negctl-suite-*.txt`。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与判断依据。
若某条自述经核对不成立，请直接指出并给出反证。

## 五 边界

不评 U10-A~D 的改动；不评 W4 真连门；不评 pyright 存量；不评 `_archive/`；
不评 `_bmad-output/` 下的文档措辞。

## 最小读取面

- `git diff 0b9be419 88a15609` 全文（本轮唯一改动）
- `backend/tests/unit/test_sync_batch_auth.py` 全文
- `backend/tests/unit/test_system_endpoint_auth.py` 全文
- `backend/app/config.py` 第 270-300 行、第 960-970 行
- `backend/app/security.py` 第 60-230 行
- `_bmad-output/审查/evidence-red-a2/final-gates-*.txt`
