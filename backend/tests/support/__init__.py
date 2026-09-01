"""测试侧的共享基元。

这里放的是**测试自己用的工具**，不是被测代码。刻意不叫 conftest：conftest 会被
pytest 自动加载并把里面的 fixture 撒给整棵子树，而这些基元需要被显式 import，
调用点一眼可查（``grep no_lifespan`` 就能列全射程）。
"""
