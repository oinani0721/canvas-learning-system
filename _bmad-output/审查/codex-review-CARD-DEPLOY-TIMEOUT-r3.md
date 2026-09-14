> 批次: BATCH-2026-09-11-第十四批 · 车道 T2-A · 卡 CARD-DEPLOY-TIMEOUT round-3（末轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEPLOY-TIMEOUT-r3.md)"`
> 审查绑定: `25f56065`（= 本卡**最终代码 HEAD**；此后只有一处**纯注释**头注补充与文档 commit，
> 非注释面逐字节相同，等价核见 `evidence-deploy-timeout/d32-comment-equivalence-20260914T211237.txt`，按 D-32 不重置轮次）
> 会话头自证（抄 `.stderr` 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；`.stderr` 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

审查绑定 **`25f56065df19c732d888d7d5348c413b582fe0b6`**，两份工作区代码均与该 SHA 一致。结论：**BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 3**。全程只读，未运行 pytest、真实构建或数据库操作。

- **BLOCKER：无。**
- **HIGH：无。** r2 HIGH-1 的 locale 绕过已修复。
- **MEDIUM：无。**
- **LOW-1：`_reap` 仍可能误杀复用 PID 的无关进程，r2 LOW-1 仅缓解。**  
  [backend/tests/unit/test_deploy_vault_sh.py:2791](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:2791)、`:2795`。**门未覆盖的路径**：原进程退出后，PID 已被同 UID 的其他进程复用；`kill(pid, 0)` 仍成功，随后 KILL 命中错误对象。披露风险、减少等待窗口均成立，但不能算消除。
- **LOW-2：负控驱动仍可能遗漏失败，且 MISMATCH 不产生失败退出码。**  
  [negctl3-20260914T205017.txt:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-deploy-timeout/negctl3-20260914T205017.txt:66)、`:81`。**门未覆盖的路径**：`mutate` 返回失败时直接跳过，不累计 MISMATCH；出现 MISMATCH 时两支最终都是 `echo`。只读抽取末尾表达式验证：`MISMATCH=1` 仍返回 **rc=0**。本轮七例齐全且全部匹配，因此不推翻本轮结果。
- **LOW-3：头注遗漏新增的“原串最多 20 位”约束。**  
  [scripts/deploy-vault.sh:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:63)、`:77`，对应实现 `:599`。**对照输入**：20 个前导零后接 `1`，数值属于公布的 `1..86400`，仍会被拒。应补明“含前导零总长最多 20 位”；这是说明缺漏，不是超时失效。

对六个问题的核对如下。

**⓪ 未发现绕过新取值校验、取消或显著缩短 alarm 的输入。**  
[scripts/deploy-vault.sh:591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:591) 开始的处理链成立：

- 第一门已限定 ASCII 数字；剥零中的 `[!0]` 没有 locale 排序区间，外层引用使待删除前缀按字面匹配。
- `20` 限制原串处理成本；`5` 限制规范化后的有效位数，随后再比较 `86400`。两者职责不同。
- 数值比较接收的是 1–5 位 ASCII 数字，不再存在本轮原缺陷中的 rc=2 输入。
- `:654` 用 `"$_cap"` 传入 Perl 参数，没有 `eval` 或重新交给 shell 解析。

我只抽取校验代码执行了内存探针：两个 locale 各 34 个边界/异常输入，加非数字单字节检查，均符合预期；十万个零也迅速拒绝。另复现了旧代码在阿拉伯 locale 下放行 `٠٥`、比较报错，以及 Perl 最终得到 alarm 0。空值在缺省赋值处变为 300。

**① 本卡新增 `if/case` 未发现其他可定位的 fail-open。**  
[scripts/deploy-vault.sh:625](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:625) 的 `cd`、Perl 执行失败，以及 fork 失败 125、exec 失败 127，均经 `_build_rc` 非零检查拒绝。marker 的 `case` 不匹配后仍检查退出码；缺省分支省略没有跳过失败门。数字 `case` 的自然落下则代表通过当前拒绝条件。

**② 未发现顺序、端口或残留文件造成整条假绿。**  
新增段实际是 **6 个测试函数，参数展开 11 项**；各项使用独立 `tmp_path`，端口各异。外部端口占用可能造成假红。

`:2710` 的记录写入失败，确实会使 [`:2757`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:2757) 错判“未调用 npm”：正向用例因此假红；负向的单个“未调用”断言可能误过，但整条还要求 **rc=71 且文案点名 `CLS_NPM_BUILD_TIMEOUT`**，普通 build 失败或超时不能满足，故该写入失败本身不足以造成整条假绿。

`[C]` **是对照项，不是独立的 locale 修复回归门**；旧实现本来就拒绝。承重的是阿拉伯 locale 项。测试自身没有验证 locale 可用，换机器时不能仅凭两项皆绿宣称覆盖了旧缺陷。

另一个**门未覆盖的路径**：当前时间断言只有整跑 `<30s`，瞬时成功对照不能杀死“把合法 cap 错传为 1 秒”的变异；这不代表当前代码存在该错误。

**③ 七例支持四种指定变异有杀伤力，但不是所有路径的证明。**

| 负控／对照 | 独立核对结果 | 实际失败或通过条件 |
|---|---:|---|
| n1-locale | 1 failed / 1 passed | 阿拉伯输入整跑超时；C 对照通过 |
| n1-ctrl-legal | 1 passed | `005` 通过 |
| m1-range | 3 failed / 1 passed | `0`、`000`、`4294967296` 超时；`abc` 通过 |
| m1-ctrl-hang | 1 passed | 合法 `5` 仍能打断挂起 |
| m2-rc124 | 1 failed / 1 passed | 明确红于把 npm 自身 rc124 误报为超时 |
| m3-offline | 1 failed | 明确红于 `offline=<unset>` |
| restore-all | 11 passed | 恢复后全部通过 |

`m1` 保留第一道字符集门，因此 `abc` 仍绿与变异源码一致。[范围日志:126](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-deploy-timeout/negctl3-m1-range-205135.txt:126)、[rc124 日志:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-deploy-timeout/negctl3-m2-rc124-205427.txt:15)、[offline 日志:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-deploy-timeout/negctl3-m3-offline-205444.txt:15) 均吻合。

未见本轮红于其他原因的证据。不过 n1/m1 的日志直接证明的是 **45 秒整跑超时**；异常分支没有保存进程启动标记或捕获输出，自定义“假 npm 挂住”文案不能单独排除 build 前卡住。变异位置、对照通过和恢复全绿共同支持归因。

总表中的失败断言摘要实际为空；以上归因采用了七份全量日志。r2 关于汇总判定、预期比对、全量日志的整改成立。

**④ r2 指出的三处过强承诺均已收回。**  
PATH、uint32 截断、build 后文件操作不受 alarm 保护，现已写清。剩余说明问题是上述 LOW-3。

**⑤ 两个集合确实可以独立重算为逐条一致。**  
从 [unit-nodeids:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-deploy-timeout/unit-nodeids-r2fix-20260914T205645.txt:6) 提取 BASE/CLOSE：

- 各 64 条、无重复，均为 **35 FAILED + 29 ERROR**。
- 双向差集为空，列表顺序也一致。
- CLOSE 与本轮原始运行日志重新提取的集合一致。

因此，r2“无法独立重算”的限制在本轮已解除。该结论是失败状态及 nodeid 一致，不扩展为失败原因逐字一致；未越界读取原始基线文件。

同时独立重算确认：`step2_install()` 至 EOF 为 **33,631 bytes**，两端 SHA-256 均为 `96d10556a71e71c3702fd20ae4cb31f4a1c6acab3cc2b3317e8d40abe5789819`，步 5/6 与后续主流程逐字节未动。
