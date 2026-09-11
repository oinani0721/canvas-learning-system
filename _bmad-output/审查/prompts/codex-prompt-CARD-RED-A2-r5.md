# CARD-RED-A2 独立复核请求 round-5（第十三批 / 车道 U10 末卡 · 轮次上限轮）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
审查绑定：`052a9289..87f75b19`
代码 commit 链：`fe3787ce` 初版 → `0b9be419` r1 整改 → `88a15609` r2 整改 → `cc74b130` r3 整改 → `87f75b19` r4 整改

## 一 本轮唯一改动（纯注释，两条均为本卡自引入的失实表述）

round-4 判定 BLOCKER/HIGH/MEDIUM 全 0、3 条 LOW。本轮处置：

- **r4 LOW-3 已改（本卡自引入）**：docstring 说 `is_local` 要求「`DEBUG=True` 且 CORS 含
  `localhost`」，漏了 `config.py:286` 的 `or` 分支。已改为「含 `localhost` **或**
  `127.0.0.1`」。两文件各一处。
- **r4 LOW-1 已改（本卡自引入）**：三处仍写「正向锁定 Branch 1 要用精确等值」，仍过宽。
  已接受你的实证（`detail.endswith("not configured")` 对 Branch 1 为 True、对 Branch 2 与
  两条 403 文案均为 False，同样是正向区分），改为「此处采用精确等值，锁定 Branch 1 的完整
  detail 文案（不是唯一可行的正向判据，是本卡选定的那一个）」。
- **r4 LOW-2 未改，登记移交**：两文件头部矩阵仍写 `DEBUG=True + 空 key → 200`（与 P0-2
  加固后的 503 实际行为不符）。经核对该处**不在本卡改动面内**
  （`git diff 052a9289 HEAD` 对这两行计数 = 0），属基线既有债；卡文硬边界写明
  「⛔ 禁顺手修存量」，故本卡不改，已写入验收单台账移交条目⑬。
- **r4 附注（鉴权先于 handler 未被独立锁定）**：已写入验收单台账移交条目⑯，注明其为源码推导、
  未执行变异。

## 二 请核对

1. 本轮两处改动是否准确、有无新的过宽或失实？
2. 本轮确为纯注释改动、无行为变化？（`git diff cc74b130 87f75b19`）
3. 「r4 LOW-2 属基线既有债、不在本卡改动面内、按禁顺手修存量登记移交」这一判断是否成立？
4. 截至 `87f75b19`，两个测试文件里**本卡引入或修改过的**文字，还有没有失实、过宽或无依据之处？
   （基线既有的失实请单独标注为「非本卡引入」，便于分流。）
5. 还有没有未被前四轮覆盖的假绿面？

## 三 前四轮处置总表（不必重验已确认项）

| 轮 | 条目 | 处置 |
|---|---|---|
| r1 | MEDIUM-1 Branch 1 可达性 | 接受，论证更正为「对精确空串不可达、对空白字符 key 可达」，写入验收单 §8① 与台账① |
| r1 | LOW-3 裸 token 子串碰撞 | 改代码 `0b9be419`（`caplog.records` + name/levelno/funcName/带括号完整标记） |
| r1 | LOW-2 `model_construct` 其他偏差 | 登记，验收单 §8③ |
| r1 | LOW-4 detail 文案耦合 | 登记（漂移会显式打红） |
| r1 | LOW-5 自述超出证据粒度 | 接受，改为「断言数 2→4 / 2→4 / 1→3」；五段负控每段记前后 sha 与还原 rc |
| r2 | LOW-1 `model_copy` 拒绝理由不成立 | 接受，验收单 §8② 改为「取舍而非必然」，并记「禁 `.env` ≠ 禁进程环境变量」 |
| r2 | LOW-2 空密码断言证明不了不读 `.env` | 改注释 `88a15609` |
| r2 | 控制流边界（删 `if` 令 logger+raise 无条件执行仍全绿） | 验收单 §8⑥ + 台账⑩，注明未实跑生产变异 |
| r3 | LOW-1 「任何 `in` 都分不开」过宽 | 改注释 `cc74b130` |
| r4 | LOW-1 / LOW-3 | 改注释 `87f75b19`（本轮） |
| r4 | LOW-2 | 登记移交（基线既有债） |

## 四 其余自述（沿用前轮）

生产代码零改动；改动面只有那两个测试文件；只改 `debug=False and key==""` 一档的实例化方式；
两文件 17 passed；`tests/unit` 目录级 120 failed → 117 failed，相对本卡开工快照的 nodeid diff
只有 3 条 `<`（恰为目标三条）、无 `>` 行、29 errors 不变；判据计数 sync=1 / system=2 / 合计 3；
裸 `in caplog.text` 残留 0；五段负控存档见 `evidence-red-a2/negctl-suite-*.txt`。

## 五 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与判断依据。
若某条自述经核对不成立，请直接指出并给出反证。**请对每条 LOW 标注「本卡引入」或「基线既有」。**

## 六 边界

不评 U10-A~D 的改动；不评 W4 真连门；不评 pyright 存量；不评 `_archive/`；
不评 `_bmad-output/` 下的文档措辞。

## 最小读取面

- `git diff cc74b130 87f75b19` 全文（本轮唯一改动）
- `backend/tests/unit/test_sync_batch_auth.py` 全文
- `backend/tests/unit/test_system_endpoint_auth.py` 全文
- `backend/app/config.py` 第 274-300 行
- `backend/app/security.py` 第 60-230 行
