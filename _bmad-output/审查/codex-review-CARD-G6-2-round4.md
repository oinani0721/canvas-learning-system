定向复审结论：`7ca194ac` 未闭环 HIGH-1 与 HIGH-4b。当前目标代码/测试 blob 与该提交一致，DD-14 未纳入裁决。

### HIGH-1 — NOT VERIFIED

发现两个生产路径 HIGH：

- [review_app.py:406](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:406)：`pollGen` 只保证“最后启动的 GET”，不保证 GET 启动于 rebuild 之后。旧 GET 在飞 → POST rebuilt → 切后台 → [hidden 分支](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:469) 不启动新 poll → 旧 GET 仍通过代际守卫，并在 [420–428 行附近](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:420) 用重建前投影结算“数字已更新”。`pendingSync.atMs` 从未参与因果校验。无写盘执行当前模板复现 `claimedUpdated=true`；回前台的新 GET 即使失败，pending 已被删除，假成功仍保留。
- [review_app.py:309](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:309)：目标库消失时，[settlePendingSync](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:383) 虽写入“同步失败”，最终帧却只渲染最新 `data.vaults`，随后隐藏横幅并显示已连接。因此目标卡和失败反馈一起消失。门只检查旧 `note` 节点引用（[test_review_app.py:1333](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:1333)），未检查最终 `cards.innerHTML`。

corrupt 与有效投影两场景、渲染探针及一般乱序守卫本身成立，但不足以关闭以上反例。

### HIGH-3 — VERIFIED

[test_review_app.py:381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:381) 已实现：

- 唯一字面 `<script>` 开标签；
- 大小写不敏感统计 `</script` 前缀且要求恰一次；
- 拒绝正文 HTML 注释状态标记；
- 当前真实页面使用规范闭标签，并经真实响应提取链及 Node 门覆盖。

新 MEDIUM：[test_review_app.py:400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:400) 没有验证唯一结束前缀后的 delimiter。若前缀后立即接 ASCII 字母，helper 会接受并截断，但浏览器不会闭合脚本，存在未来回归假绿。当前生产页闭标签规范，故不推翻本条 VERIFIED。

### HIGH-4b — NOT VERIFIED

新 HIGH：AST 门仍检查拼写，不完整检查绑定语义。

- [test_review_app.py:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:273) 只检查直接 `ast.Name` 目标；解构重绑定不会递归检查。
- [test_review_app.py:278](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:278) 漏掉 `posonlyargs`、`vararg`、`kwarg`。
- 接收者白名单中的 `json`、`request` 等没有重绑定保护；任意对象重新绑定为 `json` 后调用白名单 `.items()` 仍通过。
- import 收集忽略 `asname`，允许 import alias 遮蔽白名单调用名。

三个无害内存探针——解构重绑定、允许接收者重绑定、允许 import alias——均被当前等价门判为 `PASS`；同时现有 AST pytest 为 `1 passed`，证明该绿色门确实未覆盖这些绕过。M44/M45 只验证两个指定变异。

### 随行补口

- M1：VERIFIED，[freshNotes](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:372) 返回 null-prototype。
- LOW-2：NOT VERIFIED。hidden 分支自身不新发 GET，但不能保证 pending 留到回前台；上述旧 GET 竞态会提前结算。
- LOW-3：VERIFIED，[own-key 检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:275) 正确。

存档仍记录 89 passed、46/46、external `[]`、pyright 0；`mutation-run-final.log` 的 PASS 标记实际是倒数第二行，物理末行为 `EXIT=0`。未整读受限攻击样本或变异脚本，未修改工作树。

总结论：FAIL（HIGH-1 与 HIGH-4b NOT VERIFIED，存在新 HIGH）


