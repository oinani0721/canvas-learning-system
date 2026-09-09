**结构性方向成立，可以有限验收；当前还差两项门禁收尾，暂不建议按原句直接签收。** 不需要继续扩张语义反例清单。

复核绑定 `869081f8001a6820ee8726ed019b5ed371d5f563`；收尾时被审代码仍与提交一致。

**BLOCKER：未发现。HIGH：未发现。**

**MEDIUM：2 条。**

1. **[test_skill_portability_lint.py:4362](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:4362)：目前没有精确锁住实际路径及文件类型。**  
   普通文件替换成指向相同内容的符号链接，摘要与键均不变；目录分量也能通过符号链接把读取引到受管根之外。在大小写不敏感文件系统上，`SKILL.md → skill.md` 后，字面量 glob 仍可能找到它，`:4363` 又硬编码键名为 `SKILL.md`，因此改名静默。  
   若保留“精确文件集合”的验收承诺，本卡应按实际目录项核对大小写，并拒绝受管路径及相关目录分量的符号链接，或显式登记这些对象属性。上述判断来自静态分析，未创建文件系统样本。

2. **[test_skill_portability_lint.py:4428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:4428)：新增负控没有验证正式门禁承重。**  
   它只比较两次 `hashlib.sha256`，不调用 `managed_file_digests()`／`check_managed_files()`；正式检查若退化成 `return []`，两条新增测试仍通过。应使用小型受管样本，让未改、新增、删除、字节修改实际经过正式门禁，无须复制现有大文件。拆分常量这个样本本身选对了：内存实测九项正文计数全零，七个附加检查均为 `[]`；计数前提也应补进断言。

**LOW：以下三项。**

- **[test_skill_portability_lint.py:2003](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2003)、[`:2979`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2979)：诊断降级尚未贯穿旧说明。**  
  “不受任何解析能力所限，是最后一道”“不管什么形态，块变了就红”仍然过强，后一句已被本轮自己的拆分常量负控否定。`:1709`、`:1735` 也仍描述旧的 heredoc 排除逻辑。应统一限定为候选提取范围内的诊断能力。新增总契约 `:4394–4396` 明确不证明路径安全，**方向未发现问题**；具体样本中的“安全对照”无需一概删除。

- **[test_skill_portability_lint.py:4363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:4363)：sha256 前 16 个十六进制字符只有 64 bit，不能严格推出“任何字节变化必红”。**  
  对固定基线的普通回归检测，随机不同内容误同概率约为 `2⁻⁶⁴`，工程上足够低；但它不是完整 SHA-256，也不是绝对保证。建议保留全部 64 个十六进制字符，并写成“路径集合及原始字节摘要一致”。两份内容都可自由选择时的生日碰撞约需 `2³²` 次工作，不能将其混同于攻击已固定基线。

- **[test_skill_portability_lint.py:1739](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1739)、[`:2930`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2930)：三处修复带来两种保守误报。**  
  无标签 fence 中，若 Python 三引号字符串内部包含 `python3 <<'END'` 及两次路径赋值，新版会将字符串内容额外解释为执行候选；旧版动态判据为空，新版命中。另将 `"{" unset CLS_BACKEND_URL`、`"(" unset CLS_BACKEND_URL` 中被引用的命令名去引号后当作语法前缀，会由旧版 `False` 变为新版 `True`。这些可以随诊断降级明确登记，**不要求继续修解析器才能收尾**。

其他维度逐项结论：

| 维度 | 结果 |
|---|---|
| 普通受管文件新增、删除、字节修改 | **未发现比较逻辑错误**；前提是枚举正确、读取成功且摘要不碰撞。 |
| 未改快照必绿 | 基线原本匹配、枚举路径和读取字节均未变时成立；不等于“同一 Git 提交跨平台必绿”。 |
| 文件模式变化 | `chmod` 后仍可读取时会静默；模式不属于字节，应明确排除，不必扩成本卡代码义务。 |
| LF／CRLF、BOM、尾随空白 | **未发现字节归一化导致的静默**；`read_bytes()` 会保留差异。 |
| `.gitattributes` | 转换后的工作树字节改变会红；同提交不同检出配置可能因此不同。配置自身变化但受管字节未变时不会红。 |
| 三条 glob 的深度与扩展名 | 相对 `:116` 明示范围，**未发现遗漏**；更深子目录、`.sh`、模板本来在范围外。当前 16 个摘要键与既有 skill／script 基线集合一致。 |
| 三个原定回归 | 均验证恢复命中；**未发现有合法执行语义的 `c789ffbf` 能抓、`869081f8` 漏掉的新回归**。 |

本卡必须完成的只剩：**落实精确路径／链接边界、补正式门禁负控、同步上述契约说明**。完成后可采用验收结论：

> 本卡按明确受管范围的文件集合与原始字节摘要验收；前十条仅提供诊断，摘要更新代表人工接受此次快照，不代表路径安全或债务消除。

本次未跑 pytest、未修改文件、未连接服务，也未独立重算实际 16 份文件摘要；因此没有把真实正控标为已验证通过。

**本轮 BLOCKER 0 条，HIGH 0 条。**
