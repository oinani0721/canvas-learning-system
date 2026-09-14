# CARD-G3-9 独立复核请求（BATCH-2026-09-11-第十四批 / 车道 T4-A / round-4）

## 一 背景 与 最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`
审查绑定 SHA：`72b1cabd`（基线 `08100483`；r1 `30b23c4d` / r2 `b2f962d9` / r3 `0596386b`）

**r1 九条、r2 十一条、r3 十一条已全部采纳修复，零驳回。** 本轮请复核 r3 那批修复是否成立、
有没有引入新缺口。⚠️ 本卡 Codex 轮次上限 5，本轮是第 4 轮。

请只读：

- `git diff 08100483 72b1cabd -- . ':(exclude)_bmad-output'`
- `backend/scripts/g39_three_view_reconcile.py`（全文）
- `backend/tests/regression/test_g39_three_view_reconcile.py`（全文）
- `canvas-vault/Dashboard.md` 的 `:52-95`
- `backend/app/api/v1/endpoints/review_overview.py` 的 `:155-340`、`:780-1015`、`:1029-1175`
  （**只读参照，本卡禁改**）

## 二 round-3 十一条的处置

| r3 | 修法 |
|---|---|
| HIGH-1 重定向后的连接失败仍被豁免 | opener 加 `_NoRedirect`，不跟随重定向；302 归「连上了但非 2xx」 |
| MEDIUM-2 errno 混平台数字 | 改按**当前平台** `errno` 常量名取值（ECONNREFUSED/EHOSTUNREACH/ENETUNREACH/EHOSTDOWN/ENETDOWN/EADDRNOTAVAIL） |
| MEDIUM-3 协议/URL 异常逃逸 | open 阶段改捕 `Exception`；非连接失败一律归 `__open_error__` |
| MEDIUM-4 数组传播元素异常 | `_js_interp_throws` 改递归（list 任一元素抛即抛） |
| MEDIUM-5 backlogCnt 插值异常遗漏 | 对 `backlog_cnt` 也做插值检查 |
| MEDIUM-6 `False == 0` | 新增 `_same_count()` 类型严格比较，用于 due_count 与 placeholder_backlog |
| MEDIUM-7 picker 自检依赖 overview 在场 | 自检（node 类型、upcoming 形状）**上移到 `reconcile()`**，与 overview 在不在场无关 |
| MEDIUM-8 损坏 overview 行被过滤后隐形 | 非法板行 / nodes 非数组 / 非法节点行**先报差异**再跳过 |
| MEDIUM-9 零到期板节点列表不查 | 新增「零到期板 nodes 应为空」判据 |
| MEDIUM-10 损坏 next_due 打断排序 | 排序键先把非字符串归一为 None（可排序且可辨认），损坏本身另行报出 |
| MEDIUM-11 重复 upcoming 覆盖 / 非法 next_due 归一 | 两者都报 `picker.upcoming(self)/structure` 差异 |

变异对照：27/27 KILLED（每条修复都有对应的「改回缺陷形态」变异体，要求被点名的那条测试变红），
脚本还原后 shasum 逐字节相同。测试 57 例全绿。

## 三 请按重要性排序回答的问题

1. **r3 那批修复有没有引入新的未被拦下的输入？** 特别是：`_NoRedirect` 是否真的关掉了所有
   重定向路径（含 301/302/303/307/308 与 `Refresh` 头）？`open` 阶段改捕 `Exception` 后，
   有没有把**本该豁免**的连接失败也吞成差异（假红）？
2. **`_js_interp_throws` 的递归是否既不漏也不多？** 还有哪些 JSON 形状会让
   `` `${v}` `` 抛而它判不出来？反过来有没有误判（本不抛却判抛）？
3. **`_same_count` 用在 due_count / placeholder_backlog 上是否恰当？** `not-comparable`
   字符串与数字比较时行为对不对？有没有别的计数比较还在用宽松相等？
4. **picker 自检上移后是否真的与 overview 在不在场无关？** 还有哪些检查仍留在
   `_reconcile_overview` 里而本应属于 picker 自检？
5. **`known_scope_note` 白名单（N1–N5）现在闭合了吗？**

## 四 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句话说明**如何观察到它**。
没有问题的维度请明确写「未发现」。

## 五 边界

- 只读，不要修改任何文件，不要运行会写盘的命令。
- 不要连接任何数据库、不要启动后端进程。
- **不评** `review_overview.py` / `review_app.py` **本体**的设计。
- 不评 mini-UAT 的用户主观项。
- `canvas-vault/**` 是线上 vault，只读。
