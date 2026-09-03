## 逐条判决

- **HIGH-4 e③：CONFIRMED-CLOSED（原缺短语/零次循环问题）**
  - 独立存在性断言位于句级循环之前：`backend/tests/unit/test_g25_journal_namespace.py:930-937`。
  - 反方向样本位于 `backend/tests/unit/test_g25_journal_namespace.py:1008-1014`。它满足“只覆盖当前部署”，删除存在性断言后目标短语循环为零次；“旧文案”与“不成立”也满足 `:951-965` 的引用—否定窗口。因此当前 helper 中确实只能由 `:934` 拒绝，专测性成立。
  - **残余 MEDIUM**：`:934` 只检查精确子串存在，`:936-942` 只排疑问标记；若目标短语被外层否定或作为被驳斥引文，仍可能误放。这属于 §9.8 已承认的正则闭集限制，但现在有了更具体的极性绕过形态：`验收单:468-469`。不重开原 HIGH。

- **HIGH-3 锁内重读残余：CONFIRMED-CLOSED**
  - 重读发生于锁内：`backend/app/services/lancedb_index_service.py:270-282`。
  - 异常分支只更新诊断、返回 `persist_failed=1`：`:283-295`；不会进入 merge、rewrite 或 unlink：`:296-310`。
  - `return` 离开 `with` 时会释放锁；异常分支没有调用再次获取 `self._file_lock` 的 helper，因此无自死锁，也没有“不明内容被旧快照覆盖”的语义回退。

- **fresh pending 计数：STILL-OPEN（实现已修，回归门未落实）**
  - 实现确为 `len(still_pending) + len(fresh)`：`backend/app/services/lancedb_index_service.py:313-319`。
  - 但并发 append 用例只断言 `persist_failed` 和 journal 内容，未断言 `result["pending"] == 2`；退化回旧计数仍可绿：`backend/tests/unit/test_g25_journal_namespace.py:776-784`。

- **d③ 混合场景：STILL-OPEN（部分落实）**
  - 绝对路径＋持久化失败、503、`persist_failed=1`、`durable=False` 已落实：`backend/tests/unit/test_g25_journal_namespace.py:618-628`。
  - `:629` 仅排序比较状态集合，没有绑定具体 path→status，也未断言 `excluded == 1`；不满足声明的“逐路径状态断言”。

- **d⑥ 逐键：CONFIRMED-CLOSED**
  - 解析后的完整列表与完整 dict 相等，字段缺失、改变或多出都会失败：`backend/tests/unit/test_g25_journal_namespace.py:736-742`。

- **LOW docstring ×10：CONFIRMED-CLOSED**
  - docstring 已写“十条”：`backend/tests/unit/test_g25_journal_namespace.py:970`；实际十个独立篡改门位于 `:1002-1035`。

## MEDIUM 登记处置

- **multiplicity：不接受。** `orig_lines` 集合化会吞掉相同字节的新 append：`验收单:463-465`。相同载荷不等于同一时序事件；旧意图恢复成功后发生的新失败仍需保留，因此“幂等无害、零损失”论证不成立。维持低概率 **MEDIUM**。
- **e① 源码级绑定：不接受。** 验收单明确承认行为探针没有证明运行期采用配置周期：`验收单:466-467`。成本理由不能替代绑定证据，维持 **MEDIUM**。

## 验证

当前 HEAD 为 `e86982b4`。指定命令实跑结果：**27 passed, 10 warnings**。

## 新问题分级

- **BLOCKER：无**
- **HIGH：无**
- **MEDIUM：**
  - e③ 必需事实短语未验证肯定极性。
  - fresh 返回计数缺直接回归断言。
  - d③ 未锁定逐路径状态映射及 `excluded` 聚合值。
- **LOW：无**

BLOCKER/HIGH 清零：是
