**原 H1 和空清单 M2 的修复逻辑成立；仍发现 2 项 MEDIUM、1 项 LOW。**

复核绑定 `f9e31034dfa83a0e343b8625b02be94830a17358`，当前 `lefthook.yml` 与该提交逐字节一致。全程未运行 hook、对照脚本，未修改或暂存文件。下面两个故障反例均为**静态推导，本轮未实测**。

[级别 MEDIUM] 新增 `dn` 未检查文件类型，沿用 case-9 的故障模型即可成功丢弃全部 diff。  
文件:行　[lefthook.yml:508](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:508)，写入 `dn`；519 行交给 awk。  
依据　[case-9-s-hits.sh:18](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/case-9-s-hits.sh:18) 已采用 mktemp 包装层预置 `hits → /dev/null`。将同一故障的目标换成 `dn`：Git 正常写出 `d`，`tr` 向设备写入成功，awk 从设备读到 EOF 并成功退出，`hits` 保持正常空文件；计数、哨兵及最终 `hits` 检查全部通过，走到 OK。无需伪造 Git 输出或工具退出码。旧有 `d` 也存在同型缺口。  
建议　写入前拒绝已有的链接及非普通对象，写入后、交给下一阶段前核验 `d/dn` 为可读普通文件；补 case-9 的 `dn` 变体。这仍不保证抵御同用户持续并发替换。

[级别 MEDIUM] Git 仍共享记录流的 stdin，哨兵和计数无法发现只被吞掉的路径字节。  
文件:行　[lefthook.yml:498](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:498)，循环内 Git 未隔离 stdin；486、488 行计数后跳过空记录。  
依据　设清单为 `a_clean.py\0b_dirty.py\0哨兵\0`。处理第一条时，Git 包装层若只消费下一路径的全部非 NUL 字节，再正常透传 Git，下一次 `read` 会取得空记录：它仍计入 `SEEN`，随后被跳过。最终哨兵可达、两数均为 3，而 `b_dirty.py` 未扫描。只吞部分前缀也可使后续查询变成不存在的路径。现有 6-6 覆盖的是吞整条／整流。**此项依赖消费 stdin 的包装层或故障注入；未证明正常本机 Git 会这样做，且属于存量缺口。**  
建议　给循环内 Git 加 `</dev/null`。这能隔离意外消费，不能防御任意伪造输出的恶意 Git。

[级别 LOW] “字节处理一律 C、逐段核 rc、不用管道”的声明仍超出实现。  
文件:行　[lefthook.yml:434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:434)、450、511 行。  
依据　仍有两条管道：
- 434：`od | tr`，两段都有 C locale，但上游 rc 被吞，赋值整体 rc 也未检查。
- 450：`wc -c | tr`，同样未检查各段及赋值 rc；只有 `tr` 固定 C。`wc -c` 本身计字节，不能仅因未固定 locale 就认定计数错误。
- 511：awk 未固定 C，仍继承外部 locale。

空值／非法数字校验和最终计数比较能阻断常见失败，因此不能据此声称已经实证另一条残留漏检；round-1 M1 应判 **PARTIAL**。  
建议　分别捕获并检查 `od`、`wc` 和输出规范化步骤的 rc；awk 也固定 C。非法 UTF-8 对本机 awk 的剩余影响**未验证**，需要实际版本的专项输入对照。

其余问题的判定如下：

- **NUL 替换本身：通过。** 一个 NUL 换成一个 `?`，不会删除分隔字节；标记全为 ASCII 字母，使用字面 `index()`，所以相邻 `?` 不会制造或破坏完整标记。LF 和 `+`、`@@`、`diff --git ` 锚点保持不变。普通文本逐字节不变；含 NUL 的命中正文显示为 `?`，不再是原始字节。
- **哨兵构造与计数：通过。** 正常 Git 仓内路径不能等于以前导 `/` 开始的哨兵。追加失败有显式退出；追加先于计数，`SEEN` 又先于哨兵分支递增，两边均为 `N+1`。空清单读取错误因此被封住。它不证明路径字节完整，限制见第二条发现。
- **其他未显式检查的 rc：** 468、471 行两次 probe `printf`；470、520 行两个 `while` 的终止状态；412 行 trap 注册和其中的 `rm`；538 行 `cat`。probe 内容比较、主循环哨兵／计数提供部分语义兜底；`cat` 失败后仍会 `exit 1`，只影响诊断完整性。
- **行为回归：未发现。** 允许名单与 round-1 逐字节相同，自证判定段与基线相同；扫描注释和块之外的内容与 `08100483` 相同。正常情况下 `d/dn` 每轮均以 `>` 截断，Git／tr 失败会置 `FAILED` 并跳过消费，不会串读上轮 `dn`。命中格式和行号推进未改。新增副本增加磁盘占用；极大文件、极长行及资源耗尽行为**未验证**，需相应规模和失败对照。
- **6-5 降级：准确，限所述本机解释器。** 裸 `: > 文件; echo …` 在本机 sh 下会退出；带 `||` 的形式可进入处理器。[存档第 21–30 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-residue-fo/r2-out-case-6-5-hits-init-20260914T202736.txt:21) 确实记录旧版只有权限错误、新版增加自定义诊断。Apple Bash 3.2 对 OR 左项设置忽略立即退出的标志，与该结果一致。[对应源码](https://raw.githubusercontent.com/apple-oss-distributions/bash/main/bash-3.2/execute_cmd.c)
- **清理及只读文件系统：存在残留边界，未见由此放行。** `mktemp` 成功至 trap 注册之间被强杀可能留下目录；`rm` 失败也没有独立验收。创建前文件系统只读会触发 mktemp 守卫，创建后转只读会由首次 `> names` 或后续写入守卫阻断。完整清理需要故障证据，不能由 `trap` 存在推定。任意替换 Git 后直接返回空输出和 rc=0，则超出这些检查能够证明的工具可信边界。

证据方面，12 条失败对照确为 **11 条双解释器 SEALED，6-5 为 bash SEALED／sh NOT-SEALED**；H1、M2 的旧版均明确绑定 `cd31cffd`。额外的允许名单 `case-e` 仍硬编码 bash。三控日志记录 `0/1/1`，但未保存完整输入、命中正文及配置摘要；新版对照也只记录“工作树抽出、145 行”。因此，**历史运行与最终提交字节的严格绑定未验证**，需要当时抽出块的摘要及完整三控材料。

BLOCKER=0 HIGH=0 MEDIUM=2 LOW=1


