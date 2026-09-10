**不建议继续按现在的方式逐个补语义角落。建议本卡经过一次结构性收口后结束；当前提交还不能按原有承诺验收。**

复核绑定 `c789ffbfac67e4f3c6bef5bdbfa45bdc72ef1c74`，工作区测试文件与提交一致。只做指定范围读取和内存纯函数验证，未跑 pytest、修改文件、读取禁读正文或连接服务。

**第 0 问：能否收敛，取决于验收目标。**

**(a) 当前开放的语义目标，没有有限轮次收敛的依据；明确限定的保守门可以收敛。**

结构性问题是：当前实现要求“识别出某种风险才登记”，尚未做到“无法证明属于允许范围就登记”。更多负控通过只能证明那些形态，不能证明剩余输入都会被覆盖。换成三个真实解析器，也只解决语法识别，不能自动解决全部别名、执行顺序和运行时语义。

例如：

```python
ROOT = "/t"
P = ROOT + "mp/cls-exam/../x"
```

将 `..` 换成 `a` 是安全对照。实测两者九项计数相同，五项附加判据、URL 判据和块指纹全部为空。第⑩条仍在 [test_skill_portability_lint.py:2977](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2977) 用连续 `/tmp` 筛选输入，因此没有独立封住这个盲区。

**(b) 推荐终止形态：固定覆盖面的源码漂移与债务登记门。**

具体收口为：

- 对既定九份 SKILL.md、七份 scripts，绑定**完整文件原始字节摘要和精确文件集合**，摘要不依赖 `/tmp`、语言标签或 Markdown 分块。
- ①～③保留结构和计数检查；④～⑨保留已覆盖形态的诊断价值，取消“绿色证明所有路径构造安全”的承诺。
- 文件变化必须产生可审查的登记差异；更新摘要表示接受新的审核快照，不能直接等同于债务消除。

这组性质可以有限验收：未改快照通过，受管文件新增、删除或内容变化必须触发漂移。代价是普通文字修改也需要登记，但这个成本明确、可控。

**仅把④～⑨改名为“登记面”不够；“只认字面量、拆分一律登记”也不够**——如果还要先识别所有拆分方式才能登记，就回到了同一个问题。

本卡应完成上述契约与实现的收口；更深的自动语义分析另立卡，先定义受限语法和 `SAFE / VIOLATION / UNKNOWN`，保证未支持输入进入 `UNKNOWN`。当前提交不能因为提出了新终态就追认为已通过。

**(c) 当前可以写进验收单的一句话：**

> 本门能检测既定文件集合、结构、字面指标及已覆盖路径形态的基线漂移，并绑定被识别为含 `/tmp` 的文本块；绿色不证明所有新路径构造均已登记，也不证明运行时落点或宿主可移植性。

**支撑判断的定向回归结果如下。** 不再继续扩张语义反例清单，也不把这次核验当作问题 1～4 的完整复审。

**BLOCKER：未发现。**

**HIGH：2 条，均为 `9c29aacb` 能抓、`c789ffbf` 漏掉。**

1. **[test_skill_portability_lint.py:2677](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2677)：双引号里的字面 `((` 被新掩码当成算术结构，遮住后面的真实 heredoc。**

   放入 `sh` fence：

   ```sh
   echo "(("; python3 - <<'END'
   P = "/t" + "mp/cls-exam/x"
   P = "/etc/passwd"
   END
   ```

   旧版动态判据命中第 4 行，新版返回 `[]`；把 `echo "(("` 换成 `echo "hi"`，新版恢复命中。

2. **[test_skill_portability_lint.py:1738](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1738)：无语言标签时，真实 heredoc 因命令行也能被 Python 解析而被跳过。**

   精确输入：

   ````text
   ```
   python3 <<'END'
   P = "/t" + "mp/cls-exam/x"
   P = "/etc/passwd"
   END
   echo done
   ```
   ````

   同样旧版命中第 4 行、新版 `[]`；只给 fence 补上 `sh`，新版恢复命中。

两条主例的其他文本判据和块指纹均为空，九项计数均为零；把坏赋值目标改成 `Q` 的安全对照均不触发动态判据。

**MEDIUM：1 条。**

- **[test_skill_portability_lint.py:2920](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2920)：删除后备正则后，命令词扫描漏掉复合命令里的真实 `unset`。**

  ```sh
  { unset CLS_BACKEND_URL; }; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
  ```

  旧版 URL 判据命中，新版为空。删除打印字符串误报的方向正确，但替代扫描尚未保住已有覆盖。

**LOW：本次定向核验未发现。**

另两点直接答复：info string 可以作为语言声明来选择解析器，但未知标签、声明不符或解析失败需要登记，不能用“Python 可解析”排除 shell；你问的 `m = globals(); n = m; n["P"] = …`，新版**已经能抓到**，不能将其描述为只支持一层别名。

**本轮定向复核：BLOCKER 0 条，HIGH 2 条。**
