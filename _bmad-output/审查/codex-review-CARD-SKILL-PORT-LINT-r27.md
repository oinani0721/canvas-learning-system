**heredoc 的「引号判别」不成立；本轮仍有旧版能抓、新版漏掉的回归。**

复核绑定 **`9c29aacb3a1d2307da4fdc302bc6a27f65c58cb0`**，测试文件 blob 为 `7cae776f7fdb9eba32439905901dd80032dffe12`；收尾确认工作区测试文件与提交一致。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

下面漏检主例均以 Markdown fence 包裹验证：与安全对照相比，**九项计数相同，新版七项附加判据全部为空，包括块指纹**。路径故意写成 `"/t" + "mp/..."`，因此第十条不能兜底。

**BLOCKER：未发现。**

**HIGH：5 条，按根因合并。**

**HIGH-1（新回归）— [test_skill_portability_lint.py:1679](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1679)：引号不能决定 `<<` 是否处于 heredoc 语法位置，两种误判都会丢失真实执行区。**

带引号仍可能是合法算术：

```sh
(( 1 << "2" ))
python3 - <<'END'
P = "/t" + "mp/cls-exam/x"
P = "/etc/passwd"
END
```

新版把第一行误认成 heredoc，找不到 `2` 结束行便吞到块尾，后面的 Python 执行区消失。

反方向，真 heredoc 开启行可以被 Python 解析：

```sh
python3 -B <<EOF
P = "/t" + "mp/cls-exam/x"
P = "/etc/passwd"
EOF
echo done
```

`python3 -B <<EOF` 可以解析为 Python 的减法／左移表达式，新版因而跳过它。保留 `echo done` 很关键：它排除了“整块碰巧能解析为 Python”带来的补救。

**两个例子都是 `6540e409` 动态判据报红，`9c29aacb` 返回空。** 完整样本通过本地 Bash 语法检查，算术行单独执行成功；未完成整个 heredoc 的运行验收。

此外，Python 的 `x << "A"` 可以通过 `__lshift__` 合法执行，不能以“毫无意义”排除。你举的 `[[ … << … ]]` 和未经转义的 `case` 模式样本在本地语法检查失败，未作为有效反例；**`$((…))` 已受掩码保护，该形态未发现缺口。**

**HIGH-2（新回归，含既存关联缺口）— [test_skill_portability_lint.py:1136](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1136)：排除所有带参数 `vars()`，把直接可确定的模块字典写入一起排除了。**

```python
P = "/t" + "mp/cls-exam/x"
import sys
vars(sys.modules[__name__])["P"] = "/etc/passwd"
```

这里无需别名分析：参数就是当前模块，`vars(module)` 返回模块字典。旧版报红，新版全漏；隔离内存执行确认 `P` 被覆盖。

同根回归还包括：

- `import sys as s; s.modules[__name__].__dict__["P"] = ...`
- `d = dict; d.update(globals(), P=...)`
- `import importlib as imp; imp.reload(sys.modules[__name__])`

你的三种指名形态，结果分别是：

| 形态 | 当前结果与方向 |
|---|---|
| `s.modules[__name__].__dict__["P"] = ...` | **漏检，新回归** |
| `s.modules[__name__].P = ...` | **漏检，两版都漏**；旧版尚未检查 Attribute 目标 |
| `from importlib import reload; reload(sys.modules[__name__])` | **能抓**，`:1167` 有裸 `reload` 分支 |
| `reload(s.modules[__name__])`／`reload(m)` | **漏检**，实参来源未识别 |
| `m = globals(); m["P"] = ...` | **漏检，两版都漏** |

**HIGH-3（既存）— [test_skill_portability_lint.py:1313](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1313)：解包赋值把整个 RHS 错当成每个目标的值，导致“合规写入”证明失真。**

```python
P = "/etc/passwd"
P, *_ = "/t" + "mp/cls-exam/x"
```

实测 `_provably_last()` 返回 **True**，最终 `P` 却是 **`"/"`**。

这例确实满足直线执行、源码在后、非延迟、非搬运等控制条件；错误在于 **`P` 实际没有接收整串合规路径**。四个控制条件之外，还必须证明目标实际绑定的值。

**HIGH-4（既存）— [test_skill_portability_lint.py:1298](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1298)：`_assignments()` 遗漏直接 `del P`，删除合规绑定后可以重新读到外层坏值。**

```python
P = "/etc/passwd"
class C:
    P = "/t" + "mp/cls-exam/x"
    del P
    result = P
```

实际 `C.result == "/etc/passwd"`，两版全部静默。类作用域中的 `P` 被删除后，读取回退到模块绑定。

这不是 `_provably_last()` 成功证明了安全，而是**写入／删除记录不完整，检查提前沉默**。本轮补了 `del globals()[...]`，直接删除名字仍未覆盖。

**HIGH-5（既存）— [test_skill_portability_lint.py:1117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1117)：暂停执行没有进入必经性检查，生成器后方的合规赋值被当成必然执行。**

```python
def f():
    P = "/etc/passwd"
    yield P
    P = "/t" + "mp/cls-exam/x"

result = next(f())
```

实际 `result == "/etc/passwd"`，两版全部静默。`next()` 停在 `yield`，后面的合规赋值尚未执行。

这里是**实现误判必经**，并非真实满足“必经、非延迟”后仍发生覆盖。坏赋值与好赋值之间插入 `assert False` 也会静默，但暂停并交付坏值的上述例子更直接。

**MEDIUM：2 条。**

**MEDIUM-1（新回归）— [test_skill_portability_lint.py:2844](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2844)：只允许赋值前缀，会漏掉经 `command`／`builtin` 等合法前缀执行的 `unset`。**

```sh
command unset C'LS'_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
```

旧版 URL 判据报红，新版为空；`builtin unset`、`! unset`、前置重定向也复现。仅用本地 `unset` 和 `printf` 验证，变量确实被删除，随后展开使用 localhost 缺省值；未执行 curl。

**MEDIUM-2（既存误报未修净）— [test_skill_portability_lint.py:2852](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2852)：后备正则再次无位置约束地搜索 `unset`，绕过新增命令词检查。**

```sh
printf '%s %s' unset CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
```

这只是打印参数，新旧版却都报红。新增负控用了 `C'LS'_BACKEND_URL`，恰好避开后备正则，**没有证明普通拼写下误报已消除**。

**LOW：未发现独立问题。** 测试语料缺项已归入对应缺陷，不重复计数。

其余维度的明确结论：

| 维度 | 结果 |
|---|---|
| 短选项按序消费 `W/X/Q` 参数 | **未发现本轮新增回归** |
| `AnnAssign.simple` 与所测 nonlocal 层级 | **未发现本轮新增回归** |
| 直接 Attribute、`__ior__`、`__delitem__`、`del globals()[...]` | **所测形态能抓，未发现对应整改残留** |
| `config.update(globals())`、读取 namespace 作为下标键 | **所测负控不误报，未发现问题** |
| 交接常量 | `check_handoff_constants()` 返回 `[]`，**未发现问题** |

自检语料应补**组合和明确的正确结果**：

| 语料组 | 必须同时覆盖 |
|---|---|
| heredoc | quoted 算术后接真 heredoc；可被 Python 解析的 opener × 有／无后续 shell 命令；重载字符串左移 |
| namespace | 直达模块／简单别名 × 读取／写入；`vars(module)` 与 `vars(普通对象)` |
| 赋值证明 | 普通赋值／解包；直接删除／反射删除；普通函数／生成器暂停 |
| URL | `unset` × 命令前缀 × 普通／整体引用／拆引号变量名；打印负控采用同一矩阵 |

逐 commit 差分能发现**行为变化**，却发现不了 HIGH-3～5 这种“两版共同漏检”。每组还需固定安全／坏形态的预期判据，避免把历史输出本身当成正确答案。

分界目前**尚未完全划对**：上述回归，以及同一执行区内直接可见的解包、删除、暂停和模块来源，应在本卡修复或明确触发登记；无需因此扩展成完整程序分析器。任意跨函数／跨模块传播、运行期反射及宿主运行验证可以另卡，但不能用它们解释掉这些已证实的直接形态。

**本轮 BLOCKER 0 条，HIGH 5 条。**
