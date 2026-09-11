# CARD-RED-A2 独立复核请求 round-4（第十三批 / 车道 U10 末卡 · 停轮轮次）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
审查绑定：`052a9289..cc74b130`
代码 commit 链：`fe3787ce` 初版 → `0b9be419` r1 整改 → `88a15609` r2 整改 → `cc74b130` r3 整改

## 一 本轮唯一改动（纯注释）

round-3 判定 BLOCKER/HIGH/MEDIUM 全 0，1 条 LOW（注释措辞，非该轮引入）。本轮只改那一条：

**round-3 LOW-1 已接受并改正**：原注释写「任何 `in` 形式的 detail 断言都分辨不了层，
只有 `==` 可以」，概括过宽。本方已独立实证你的反例并落存档
（`evidence-red-a2/detail-substring-analysis-*.txt`）：
`"Set INTERNAL_API_KEY env" in branch1_detail` = False、`in branch2_detail` = True，
即对 Branch 2 **独有后缀**做成员测试可以区分两支。

三处注释（`test_sync_batch_auth.py` 一处、`test_system_endpoint_auth.py` 两处）收窄为：
**对两支共有的那段前缀做正向子串断言分辨不了层；对 Branch 2 独有后缀做 `in` 能分，
但那断的是「不是 Branch 1」、方向相反；正向锁定 Branch 1 仍需精确等值。**

## 二 请核对

1. 收窄后的三处注释是否准确、还有无过宽或把推断当事实之处？
2. 本轮确为纯注释改动、无行为变化？（`git diff 88a15609 cc74b130`）
3. 全卡复读：截至 `cc74b130`，两个测试文件里**还有没有**任何失实、过宽或无依据的表述
   （注释、断言消息、docstring 都算）？
4. 还有没有未被前三轮覆盖的假绿面？

## 三 前三轮各条的最终处置（供核对，不必重验已确认项）

- r1 MEDIUM-1（Branch 1 可达性）：接受，论证已更正为「对精确空串不可达、对空白字符 key 可达」，
  写入验收单 §8① 与台账移交条目①；未改代码。
- r1 LOW-3（裸 token 子串碰撞）：接受，已改代码（`0b9be419`）为
  `caplog.records` + `name`/`levelno`/`funcName`/带括号完整标记。
- r1 LOW-2（`model_construct` 其他偏差）：登记不改，验收单 §8③ 记明「该对象带
  `NEO4J_ENABLED=True` + 空 `NEO4J_PASSWORD`，违反另一条生产不变量，不等同真实生产配置」。
- r1 LOW-4（detail 文案耦合）：登记不改（漂移会显式打红）。
- r1 LOW-5（自述超出证据粒度）：接受，改为「全部既有断言均保留，三条断言数 2→4 / 2→4 / 1→3」；
  本轮五段负控每段均记变异前 sha / 还原后 sha / `git diff --quiet` rc。
- r2 LOW-1（`model_copy` 拒绝理由不成立）：接受，验收单 §8② 改为「保留 `model_construct`
  是取舍而非必然」，并记下「禁 `.env` ≠ 禁进程环境变量」。
- r2 LOW-2（空密码断言证明不了不读 `.env`）：接受，已改注释（`88a15609`）。
- r2 控制流边界（删 `security.py:96` 的 `if` 令 logger 与 raise 无条件执行，三条仍绿）：
  已写入验收单 §8⑥ 与台账条目⑩，并注明该反例为源码推导 + 你的内存实验，本方未实跑生产变异。
- r2/r3 `funcName` 属防御深度而非独立不可省：已写入验收单 §8⑤ 与台账条目。

## 四 其余自述（沿用前轮）

生产代码零改动（`git diff --stat 052a9289 HEAD -- backend/app` 空）；改动面只有那两个测试文件；
只改 `debug=False and key==""` 一档的实例化方式；两文件 17 passed；`tests/unit` 目录级
120 failed → 117 failed，相对本卡开工快照的 nodeid diff 只有 3 条 `<`（恰为目标三条）、
无 `>` 行、29 errors 不变；判据计数 sync=1 / system=2 / 合计 3；裸 `in caplog.text` 残留 0；
五段负控存档见 `evidence-red-a2/negctl-suite-*.txt`。

## 五 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与判断依据。
若某条自述经核对不成立，请直接指出并给出反证。

## 六 边界

不评 U10-A~D 的改动；不评 W4 真连门；不评 pyright 存量；不评 `_archive/`；
不评 `_bmad-output/` 下的文档措辞。

## 最小读取面

- `git diff 88a15609 cc74b130` 全文（本轮唯一改动）
- `backend/tests/unit/test_sync_batch_auth.py` 全文
- `backend/tests/unit/test_system_endpoint_auth.py` 全文
- `backend/app/security.py` 第 60-230 行
- `_bmad-output/审查/evidence-red-a2/detail-substring-analysis-*.txt`
