# 跑完裁判、做**纯注释**补正**之前**的三套字节快照

用途：让 `ast_equal_after_comment_edit.py` 的等价证明**可被独立重算**（Codex round-1 指出
「限定读取面没有原始编辑前快照，未独立重算那两侧内容」）。

复算：
```
PY=backend/.venv/bin/python
EV=_bmad-output/审查/evidence-expect-loc-narrow
for f in g32cb_mutation_gates.py g32ccr1_negative_controls.py g33_mutation_gates.py; do
  $PY $EV/ast_equal_after_comment_edit.py backend/scripts/$f $EV/pre-comment-edit/$f
done            # 三份都应 `AST 相同 : True`
# 验伪锚（证明这把尺子不恒 True）：
printf 'x = 1\n' > /tmp/a.py; printf 'x = 2\n' > /tmp/b.py
$PY $EV/ast_equal_after_comment_edit.py /tmp/a.py /tmp/b.py   # 必须 rc=1
```

⚠️ 这三份是**快照**，不是第二份实现：它们与 `git show <审SHA>:backend/scripts/<f>` 的区别
只有那次纯注释补正。⛔ 别把它们当成可跑的 harness（跑它们不会更新任何表）。
