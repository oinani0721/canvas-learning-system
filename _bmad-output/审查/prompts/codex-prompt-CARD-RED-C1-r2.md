# 独立复核请求（第 2 轮）— CARD-RED-C1

## 一 背景与最小读取面（只读这些，不要扩大扫描面）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c`，分支 `card/u11-red-c`，开工基线 `da690bf8`。

**这是第 2 轮。** 第 1 轮（绑定 `343fce8e`）结论是 **BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 4**。作者对四条 LOW **全部采纳、无一驳回**并整改；其中一条涉及**代码改动**，因此按本项目规矩必须再送一轮。本轮的重点是：**整改本身对不对、有没有把别的东西改坏、有没有产生新的「声明比证据宽」**。

第 1 轮的四条 LOW 与作者的整改：

| # | 第 1 轮发现 | 作者整改 |
|---|---|---|
| LOW-1 | `test_cache_configuration.py` 那条 xfail 的 reason 只写「配置清理卡（登记）」，没有可定位的接收卡标识 | **代码改动**：reason 里具名 `CARD-CONFIG-CLEANUP` |
| LOW-2 | 收工 skip 快照按开工行号抽取，`test_story_38_6_scoring_reliability.py` 那段抽空，使「五处标记原文均已留存」这句比证据宽 | 内容锚定重采，新增 `evidence-red-c1/y4d-skip-marks-close-v2.txt`（旧文件保留不删） |
| LOW-3 | 「11 处生产调用方」没说明统计口径 | 改为三口径写明，统一采「直接调用 `AgentService._trigger_memory_write`」= 10 |
| LOW-4 | 「`59586af1 --stat` 只有两个文件」有误 | 措辞改为绑定「限定三条路径的那条命令」，并列出不限路径的真实文件列表 |

**最小读取面（请只读下列，逐项）**：

1. 第 1 轮之后的**增量**代码改动：`git diff 343fce8e <本轮审 SHA> -- . ':(exclude)_bmad-output'`
2. 本卡代码改动全貌（供上下文）：`git diff da690bf8 <本轮审 SHA> -- . ':(exclude)_bmad-output'`
3. `_bmad-output/审查/evidence-red-c1/c1-verdicts.md`（作者依据表，**§6 事实更正**与 **§7 轮次与裁定**是本轮新增/改写的部分）
4. `_bmad-output/审查/evidence-red-c1/y4d-skip-marks-close-v2.txt` 与同目录 `y4d-skip-marks-open.txt`（LOW-2 整改物与其对照基线）
5. `_bmad-output/审查/evidence-red-c1/red-diff-r2-<本轮 ts>.txt`（整改后重跑的 nodeid 差集）与 `unit-after-r2-<本轮 ts>.txt`
6. `_bmad-output/审查/evidence-red-c1/loadbearing-3assertions.txt`（作者对三条翻绿断言做的承重验证）

## 二 作者自述，请独立核对（不要采信下列任何一句，请自己去证）

1. **LOW-1 的整改没有改变行为**：只改了 xfail 的 `reason` 文案，装饰器仍是 `strict=True`，断言与函数体一字未动，该用例仍计 `xfailed` 而非 `XPASS`。
2. **LOW-2 的重采是完整的**：`y4d-skip-marks-close-v2.txt` 五块 skip 正文与 `y4d-skip-marks-open.txt` 归一化后逐条相同（作者称 `diff` rc=0）；实测行号 `37 / 33 / 263 / 162 / 326`，只有 `test_story_38_6_scoring_reliability.py` 由 135 位移到 162（+27）。作者还称最初用 `-A4` 抽取会截断两个模块级块的末行，故改用 `-A7`。请核对「归一化」有没有把真实差异一起抹掉，以及 `-A7` 是否真的够。
3. **LOW-3 的三个数字都对**：直接调用 `AgentService._trigger_memory_write` = 10；含 `batch_orchestrator` 同名包装方法的全部调用点 = 12；作者承认原写的 11 与其自身枚举（8+1+1）自相矛盾。
4. **LOW-4 的更正是准确的**：`git show 59586af1 --stat` 不限路径是 3 个文件（含整文件删除的 `graphiti_bridge_service.py`），`config.py` 在限定与不限定两种口径下都不在列，故 `daa9fd37` 分叉仍成立。
5. **整改后重跑的判据仍全绿**：nodeid 差集只有 `<` 行、恰 8 条且与第 1 轮同一集合，`>` 行为零；文件级 failed 集合仍等于「预声明外来红 9 条 ∪ 移交 2 条」，`XPASS` = 0；SKIPPED 集与开工相比只有那 4 处行号位移。
6. **承重验证成立且零磁盘改动**：作者把生产 `config.py` 的 `FieldInfo.default` 在**内存里**改回 `True` 后，三条翻绿断言全部翻红，且各自被自己的断言消息打红；脚本在临时目录、跑后 `backend/app/config.py` 的 sha256 与 `git show HEAD:` 版逐字节相同。

## 三 请按重要性排序回答下列问题

1. **LOW-1 的整改有没有引入行为变化？** 特别是：reason 文案变长后，装饰器结构、`strict=True`、以及该用例的收集与判定结果是否与整改前一致。
2. **LOW-2 的重采能不能真的支撑「五处标记未被改动」这句？** 请自己判断：内容锚定 + 归一化对照这套做法，对「reason 文本被改了一个字」这种真实变化是否仍然敏感；如果不敏感，请指出更可靠的判据（作者另有一条不依赖归一化的判据：本卡 `git diff` 里零 skip 相关增删行）。
3. **承重验证（第 6 项）的设计有没有假杀 / 假存活的面？** 作者声称设计了三段防护：未变异时先要求三条全 PASS、打印变异后的实测值自证变异生效、只把 `AssertionError` 记击杀。这三段是否足够？内存态改 `FieldInfo.default` + `model_rebuild(force=True)` 是否真能让三条断言各自走到它们声称的那条路径上？
4. **第 1 轮我提出的「无法独立确认终审轮输入绑定」，作者补了一条时间线 + 内容 sha 的证明**（见 `c1-verdicts.md` §7 末尾）。这条证明链是否成立？有没有它覆盖不到的情形？
5. **整改过程中有没有顺手改到不属于本卡的东西？** 本卡禁改 `backend/app/**`、禁改五处 `pytest.mark.skip` 标记、禁碰另两张卡的用例与任何类名。

## 四 输出格式

每条发现写成：

```
[BLOCKER|HIGH|MEDIUM|LOW] <一句话结论>
file:line
一句说明：该问题在什么输入或什么时序下会显现
```

没有发现就明说「该项未发现问题」，不要为凑数编造。请在开头给出四个等级各自的计数。

## 五 边界

- **只读**。不要修改任何文件，不要运行会写盘的命令。
- **不要连数据库**；`tests/integration` / `tests/e2e` 不在范围。
- **不要重新评价第 1 轮已经结论为「该项未发现问题」的面**，除非整改动作把它弄坏了。
- **不要评价 U5-C 的回归定性结论本身** —— 本卡只提供证据并移交。
- **不要评价第十四批的去 skip 方案**。
- 不要给出修复补丁，只指出问题与位置。
