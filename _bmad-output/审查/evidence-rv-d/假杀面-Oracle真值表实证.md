# `:277` 判据的假杀面 —— 从推演升级为实证

## 判据本体

`g32ccr1_negative_controls.py`（审面内为 `:276`，主干 HEAD 为 `:277`）：

```python
killed = rc == 1 and gate in out and "failed" in out
```

g32cb `:383` 同型。它只回答「**哪道门红了**」，不回答「**哪条断言红了**」。

## Codex p1 的 Oracle 真值表（合成字符串，不跑 pytest）

Codex 直接把判据喂给构造出来的 pytest 输出串，得到：

| 输入形态 | 判据结果 | 含义 |
|---|---|---|
| `wrong assertion`（门红在**无关**断言上） | **True** | ⚠️ 假杀：击杀归给了错误的原因 |
| `runtime compile error`（变异体运行期编译错） | **True** | ⚠️ 假杀：门根本没执行到靶断言 |
| `name only in collected item, other failure`（门名只出现在收集行，实际失败是别的） | **True** | ⚠️ 假杀：`gate in out` 这一项被收集行喂饱 |
| `collection syntax error` | False | 收集期语法错不会被误判 |
| `error-only output`（只有 error 没有 failed） | False | 纯 error 不会被误判 |

⇒ **五种形态里三种会产生假杀。** 这不是推演，是把判据表达式直接求值出来的。

Codex 同时自证了证据面的可信度：
`Evidence equals exact-commit diff: True`，
`Evidence SHA256: b6e49093b74deec298d3d0a69b4e5c0435101adea6f9c745af41b7ef14ceaeb0`
—— 它独立确认了我提供的 diff 文件确实等于 `514cff3c..e22ad10a` 的 diff。

## 与本卡其它发现的咬合

同一根因（判据不绑失败断言身份）在本卡产生了**四个独立实例**：

1. **E3 归因错** —— 自称验证「死条目检测」，实际击杀必然来自该门第一条断言
   （严格表等值），目标断言从未执行。（三个独立 agent 收敛到此结论）
2. **E8 多拆一层** —— 描述只说拆词法判据，`old` 串里 `isinstance` 类型检查
   被一并废掉；击杀可能来自类型层。
3. **E10 多拆一层** —— 描述只说海象重绑，实际同时把 `record` 换成 `bytes`；
   击杀可能来自「不是 dict」这个更早的形态判断。
4. **一致性门 ①②③ 三条断言零覆盖** —— 打这道门的 E3/E9 都停在第一条断言 ⓪。

⇒ 「11/11 KILLED」这个数字的**指向性**比字面弱：它证明的是
「11 次变异各自让某道门变红」，不是「11 道防线各自被验证承重」。

## 处置（本卡零代码改动，登记给 Y1-B）

最小修法：把判据从「门名 + 有 failed 字样」改成**绑定失败断言身份** ——
解析 pytest 输出里的失败行，确认失败的断言就是该负控声称要打的那一条
（例如按断言消息里的稳定标识串匹配），并对「变异体编译失败」单独给第三态
（不是 KILLED 也不是 SURVIVED，而是 `BROKEN`，需人工看）。

配套：收窄 E8 / E10 的替换文本让每条只拆一层，或把描述改成与实际相符。
