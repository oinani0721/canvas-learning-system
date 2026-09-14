**十份对照在各自输入上因果成立，但不足以支持“十类失败全部封住”。** 确认 1 项 HIGH、2 项 MEDIUM、1 项 LOW。

复核绑定 `cd31cffd`；当前 `lefthook.yml` 与该提交逐字节相同。全程未运行 hook 或对照脚本，未修改文件、暂存区或配置；新增验证仅使用只读命令、内存和管道。

[级别 HIGH] `--text` 后仍会漏掉同一新增行中 NUL 后面的标记。  
文件:行　[lefthook.yml:461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:461)，awk 的 `index($0, M)`。  
依据　用真实 `git diff --no-index --text` 从 stdin 生成 diff，再交给文件中原样抽出的 awk：标记在 NUL 前时有命中；同一行中 NUL 在标记前时，Git 输出仍包含标记，但本机 awk **rc=0、输出零字节**。现有 6-3 将标记放第一行、NUL 放第二行，避开了这个缺口。未运行完整 hook，但解析阶段的漏检已实证。  
建议　改用能完整处理二进制字节的扫描器，或先以显式检查退出状态的步骤处理 NUL；补“同一新增行内 NUL 位于标记之前”的对照。

[级别 MEDIUM] 新增计数管道仍会吞掉上游失败，并受 locale 影响。  
文件:行　[lefthook.yml:416](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:416)，`EXPECTED=$(tr … | wc … | tr …)`。  
依据　没有 `pipefail`，末段成功即可使 `|| EXPECTED=""` 不执行。只读探针中，首段失败仍可得到数字 `0`，空清单因此通过。实际输入字节 `a\0b\xff\0`：`LC_ALL=C` 得到 `2`；`en_US.UTF-8` 下首段报 `Illegal byte sequence`，整链却 **rc=0、得到 `1`**。这既能隐藏工具失败，也可能使完整读取被误判为少读。不能据此单独声称已漏掉真实残留。  
建议　字节处理固定 `LC_ALL=C`，并逐阶段检查退出状态；末字节检查的 `tail | od | tr` 也应采用同样原则。

[级别 MEDIUM] `SEEN=EXPECTED` 尚未封住空清单情况下的读取错误。  
文件:行　[lefthook.yml:471](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:471)，记录数比较。  
依据　8-2 固定暂存一条记录，所以目录注入后 `0≠1` 会阻断。若原清单为空，在相同注入点换成目录，`read` 虽报错，仍有 **循环 rc=0、SEEN=EXPECTED=0**，后续空的正常 `hits` 可走到 OK。该 shell 语义已只读验证；未证明正常运行会自然发生目录替换，也没有声称此空清单场景漏掉真实命中。  
建议　补零记录故障对照；采用必须实际读到的结束哨兵，或能区分 EOF 与读取错误的读取器。仅补 `done … || exit 1` 不足以处理此例。

[级别 LOW] 新注释对实际 shell 的选择依据描述不准确。  
文件:行　[lefthook.yml:429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:429)，`用哪个 sh …`。  
依据　lefthook 2.1.6 执行的是 `sh -c`，由其进程的 PATH 查找 `sh`，并未硬编码 `/bin/sh`。[执行源码](https://github.com/evilmartians/lefthook/blob/v2.1.6/internal/run/controller/exec/exec_unix.go)  
建议　改为“按 lefthook 进程 PATH 查找 sh；本机当前解析为 `/bin/sh`（bash 3.2.57）”。

其余问题的判定：

- **对照因果：成立，限现有输入。** 6-5 明确触发初始化守卫；9 明确触发最终 `hits` 类型检查；8-2 在前置检查之后注入，明确触发计数比较；6-6 新版实际抓到第二个文件。没有发现“被另一条守卫代替判红”。但 `_lib.sh` 使用普通 `bash`：6-5 的旧版 OK 只适用于该解释器；本机 `/bin/sh`／Bash POSIX 模式下，旧版初始化重定向失败原本就会退出。
- **允许名单：匹配语义正确，豁免政策未验证。** `.claude/rules/*.md` 确实放行任意深度、所有现有及未来的 `.md`。五条负例证明那些近邻在范围外，不能证明范围内所有文件都应豁免；另有嵌套路径正例明确验证递归放行。当前独立 `git grep` 只找到五个精确脚本路径，没有规则文命中。需要明确是否授权整个规则文目录递归豁免；若只豁免指定文档，应使用精确名单。
- **Git 标志：断言成立，下游限制见 HIGH。** 本机 Git 2.50.1 只读实测，`-diff` 属性下不加 `--text` 为二进制摘要，加后恢复文本 hunk。外部 diff、textconv 的禁用与官方定义一致；AMT 新增的是类型变化 T，未发现其因此超出“暂存新增内容”的既定扫描口径。[Git 官方文档](https://git-scm.com/docs/git-diff)
- **执行位次：本卡未改变。** 当前命令名和 priority 未变；注释和块体不参与排序。[lefthook 2.1.6 排序源码](https://github.com/evilmartians/lefthook/blob/v2.1.6/internal/config/command.go)
- **dash 与 awk：主体判断正确。** 自证判定段与基线逐字节相同，空暂存面也执行，所以 dash 会阻断。awk 20200816 不认该处 `--` 的说法已实测确认；stdin 重定向正确，应保留。
- **其他绑定：通过。** 五个基线计数确为 `151 / 11 / 11 / 2 / 13`；扫描注释段及块之外的内容与基线相同。两份真 hook 原始输出支持正常正负控结果，不能替代十种故障在真实 runner 下的验证。

BLOCKER=0 HIGH=1 MEDIUM=2 LOW=1


