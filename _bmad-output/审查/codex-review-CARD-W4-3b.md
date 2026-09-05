> 批次: BATCH-2026-09-05-第十一批 · Z3-A · CARD-W4-3b round-1（首部由主 session 2026-09-05 按协议 §2.1 补记，正文一字未改）
> 模型: `gpt-6-astra`（stderr 实测） · reasoning_effort: `ultra`（stderr 实测） · codex: `codex-cli 0.147.0`（stderr 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt>)"`（第十一批手册规定形态；实参见车道 stderr）
> 审查绑定: `304f03ca → 2c53a881`（正文首段自证）；（审后 004e08cc +204 行零外审 → 第十二批 Y5-B 复审）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4` / `model: gpt-6-astra`

---

审查绑定 `304f03ca → 2c53a881`。发现 **0 BLOCKER、1 HIGH、1 MEDIUM、2 LOW**。其中 HIGH 已用两个 commit 的纯 AST 实现在内存中交叉复现；未运行应用、写盘测试或数据库连接。

1. **HIGH — M16 引入错误不动点：失格工厂的调用方仍被判安全。**

   位置：[lifespan_isolation_negative_control.py:700](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/scripts/lifespan_isolation_negative_control.py:700)，关联第 422、693–696、744 行。

   以下输入可以绕过本卡的 AST 门：

   ```python
   from fastapi import FastAPI
   from fastapi.testclient import TestClient
   from app.main import app as real_app

   def outer():
       return make()

   def make():
       a = FastAPI()
       return a

   def make():
       return real_app

   def test_case():
       app = outer()
       with TestClient(app):
           pass
   ```

   本次独立验证结果：

   | 版本 | 最终安全工厂集 | 违规数 |
   |---|---|---:|
   | `304f03ca` | 空 | 1 |
   | `2c53a881` | `{'<module>.outer'}` | **0** |

   **依据：** 第一遍扫描把安全定义的 `make` 加入可信集；第二遍在第 700 行清空失格集，`outer` 利用尚未剔除的 `make` 获得安全资格。不安全定义随后只让 `make` 失格，第 422 行差集留下了 `outer`。下一轮得到相同状态，遂认定收敛。实际最后绑定的 `make()` 返回生产 `real_app`。

   将内外循环上限在内存中增至 **20/40**，仍然漏检。因此新注释“知识收敛之后才作数”“E 的语义一字不损”不成立。

   **建议：** 按工厂 key 聚合同名全部定义，使用冻结的上一轮可信集求值，整组通过后才发布安全资格；避免暂态资格传播，并加入上述组合反例。单纯增加循环次数不能修复。

2. **MEDIUM — Python 顺序自证不能证明排序修复承重。**

   位置：[lifespan_isolation_negative_control.py:224](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/scripts/lifespan_isolation_negative_control.py:224)。

   **依据：** 判据只有：

   ```python
   if runtime_files(fake) != runtime_files(fake):
   ```

   两次调用之间没有改变目录，也没有改变枚举顺序。把第 169 行的 `sorted(globbed)` 改成 `globbed`，只要目录枚举稳定，即使每次都是错误的 `b, a, selftest` 顺序，仍然通过。

   它**不是数学上的恒真式**——两次枚举确实变化时可以失败；但它无法识别本应保护的“去掉排序”错误。“四条全过”不能据此证明排序正确。

   **建议：** 比较完整结果与独立构造的预期有序清单，并提供确定性的乱序输入；增加删除排序后必须失败的对照。

3. **LOW — AST 捷径被加入写盘前置，注释给出的依赖理由不成立。**

   位置：[lifespan_isolation_negative_control.py:1890](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/scripts/lifespan_isolation_negative_control.py:1890)。

   **依据：** 注释称两个 AST 捷径“也依赖 `runtime_snapshot` 的语义”，但 `--ast-negative-control` 在第 1899 行返回，`--ast-only` 在第 1920 行返回；运行时快照到第 1951 行才开始。两条 AST 路径原本不需要运行时文件比较，现在都必须先执行 `mkdtemp`、`mkdir`、`write_text`。

   这会让纯静态检查额外依赖可写临时目录。若意图是强制所有入口运行综合自检，应如实写明，不能描述成现有调用依赖。

   **建议：** 将运行时自证放在 AST 短路之后、首次运行时快照之前；或者明确区分纯 AST 检查与综合检查入口。

4. **LOW — shell 排序探针的“删除 sort 必翻红”依赖未验证的目录枚举前提。**

   位置：[lifespan_isolation_guard_probes.py:1047](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/scripts/lifespan_isolation_guard_probes.py:1047)。

   **依据：** 探针打乱六个文件的创建顺序，再断言 `seen == sorted(names)`；它没有证明当前环境的原始 `compgen` 输出确实乱序。若枚举碰巧已经有序，删除 `sort` 仍能通过。因此“这组名字会让 readdir 乱序”超过了代码保证。

   **建议：** 增加去排序对照并验证乱序前提；前提不成立时应报告承重验证无效，或使用确定性乱序输入。当前绑定环境下的拆门结果本次**未复跑**。

对新增门的逐项裁定如下。代码实际新增的是 **6 条 shell 探针**，注册数由 29 增至 35：

| 探针 | 裁定 |
|---|---|
| `runtime-glob-absent-to-present` | 承重：缓存展开或中和匹配模式后，新文件无法进入 after，指定探针失败。`GATE-BROKEN` 被明确排除，不会把普通崩溃当作成功检出。 |
| `runtime-glob-cached-expansion` | 对指定变异承重：展开位置改变，写命令执行及退出码透传保留；变异未生效则得到 CHANGED，探针失败。 |
| `runtime-glob-pattern-neutralized` | 承重：保留数组项数、只换模式，避免计数门提前失败冒充 glob 行为证据。 |
| `runtime-glob-sidecar-excluded` | 承重：恢复宽 glob 后旁文件被纳入，得到 CHANGED。需与 absent→present 正探针共同解释，单独通过不能证明 glob 工作。 |
| `runtime-glob-expansion-sorted` | 能验证当前输出有序；删除排序必失败受 LOW-4 所述前提限制。 |
| `runtime-legacy-journal-watched` | 能验证旧名被监视。拆门应中和路径并保持项数；直接删项触发计数门，只证明计数自检承重。 |

三个绿色判据**对本提交的具体变异足以排除普通崩溃或写命令失败**：写命令只做重定向写入，门执行它并透传退出码，变异没有改动这条执行链。创建后检查文件内容、要求唯一且互斥的裁定行可以增强独立性，但本次没有找到当前代码中“未执行写入却满足三条件”的具体分支，不将其列成已确认漏洞。

Python 自证的前三条分别能针对缓存展开、删除旧名、放宽 glob；第四条存在 MEDIUM-2。新增两条同名 AST 反例在删除失格差集后均漏检，确实承重；前向转调正例在恢复累积失格后误拒，反向正例仍通过，也符合其注释。**现有 24 条反例、13 条正例本次全部通过，却没有覆盖 HIGH-1 的组合输入。**

另外三项核对结论：

- **M14 收窄成立。** [生产构造点:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/app/services/vault_index_orchestrator.py:127) 固定 journal stem；[namespaced_state_path:105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/app/core/vault_state_paths.py:105) 始终插入 `__`。部署 key 经 sanitize，压缩后仍不含路径分隔符；旧名由精确项承接。未发现生产正式 journal 名逃出新清单。写入中间件 `.jsonl.tmp`、隔离备份 `.bak` 原先也不匹配旧 glob，不能算本卡新增遗漏。
- **M13 错误传播正确。** [runtime_sha.sh:348](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:348) 的排序管道独立于 `compgen || true`，已有 `pipefail`，失败经两侧 snapshot 返回码检查传播为 GATE-BROKEN；缺少可执行 sort 也明确拒绝。`LC_ALL=C` 足以固定该排序的字节序。不过，新增探针没有专门覆盖 sort 缺席和执行失败；这些动态故障路径**未验证**，需要隔离临时目录中的故障注入才能确认。
- **其余声明边界：** conftest 的 atexit LIFO 更正与现有实现相符。合法前向转调链达到 8 层时，当前循环上限仍会误拒；父版已经拒绝这些输入，故不另计本卡回归，但“迭代到不动点”不能作为无条件保证。

拆门存档已读；其 9 条 KILLED 记录没有完整变异源码，本次未独立认证九次执行。上述结论以代码和明确标出的内存验证为依据。

**整体裁定：本卡阻断级问题共 1 项（0 BLOCKER、1 HIGH），当前不能判通过。**


