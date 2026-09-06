# CARD-RV-C 只读探针（可复跑）

全部探针**只读**：不修改任何被审文件，不连接 7691 / 7687，目标端口一律用 65000 等无害值，
且各自安装的审计钩子在 `socket.connect` 事件触发时立即抛异常——「抛 = 连接没发生」。

## 复跑

```
cd <树根>
git show e06009bc:backend/tests/support/live_port_guard.py > /tmp/lpg.py   # probe_codex_high / probe_mutation_contract 需要
backend/.venv/bin/python _bmad-output/审查/evidence-rv-c/probes/<probe>.py
```

> `probe_codex_high.py` 与 `probe_mutation_contract.py` 从**同目录**的 `lpg.py` 加载被审模块
> （即 `git show e06009bc:backend/tests/support/live_port_guard.py` 的落盘副本），
> 刻意不 import 工作区版本——并行卡 Y7-A 正在改那个文件。复跑时请把该副本放到脚本同目录。

## 对应关系

| 脚本 | 回答的问题 | 结论 |
|---|---|---|
| `probe_addr_types.py` | AF_INET 是否接受非 tuple 序列？底层槽位能否被重载欺骗？ | list 在**审计事件之前**即 `TypeError`；`tuple.__getitem__` 读到真值 |
| `probe_neo4j_import_window.py` | `install()` :604 的延迟 import 窗口内有无网络动作？ | neo4j 6.1.0 下 0 个 socket/getaddrinfo/subprocess 事件 |
| `probe_af_families.py` | AF_INET6 / AF_UNIX 上哨兵地址的行为？ | INET6 同 INET；AF_UNIX 触发事件但非 tuple，被 D1 挡下 |
| `probe_sentinel_v2.py` | 自证闭合性依赖哨兵的什么属性？ | 依赖「不可被解析」；可解析的哨兵会让真实连接被判为自证 |
| `probe_codex_high.py` | Codex p1 的 HIGH（记账前异常逃逸）成立吗？ | 成立：三条路径 Δ账本 = (0,0,0)，对照 TypeError 路径 = (1,1,1) |
| `probe_mutation_contract.py` | 契约 6 条在 M1/M2 变异下是否仍全绿？ | 双双 SURVIVED；M0 对照 6/6 背书复刻忠实性 |

`probe_sentinel_dependency.py`（v1）未归档：它的脚本内预写了 verdict 文本，而实测数据推翻了那段文本
（真正的判据是「能否被解析」，不是「含不含 NUL」）。v2 改为由数据表直接得出解释，归档 v2。

## 收官审查后追加（P8-P11）

| 脚本 | 回答的问题 | 结论 |
|---|---|---|
| `probe_which_layer.py` (P8) | AF_UNIX 的哨兵地址究竟被哪一层挡住？ | 被 `:493` 分支守卫短路，`_is_selftest_address` 一次都没被调用——报告初稿「由 D1 挡下」是错误归因 |
| `probe_import_branch_v2.py` (P9) | `:514` 的 import 分支看得见哪些 import 入口？ | `import` 语句可见；`importlib.import_module` 与 `spec+exec_module` **不可见** |
| `probe_uvloop_two_layers.py` (P10) | 两层 uvloop 防御能否被同一动作同时穿过？ | 能：`poison` + `del` + `importlib.import_module`（场景 D） |
| `probe_nul_host.py` (P11) | AF_INET 上含 NUL 的主机名，事件在失败之前还是之后触发？ | 之前（`fired first = False`）——此结论初稿被错标为 P1 的产出 |

> **P7 没有对应脚本**：它是一组 `git show … | sed -n` 的只读引用，直接落在 `P7-negctl-not-fake-green-*.txt` 里。
> 该文件末尾附有一段 CORRECTION：初稿把负控的判定锚点标成 `:2203-2210`，实为 `:2267`（`:2203-2210` 是那个场景下唯一放行的一段）。
>
> `probe_codex_high.py` 的首跑（`P5-…-025117.txt`）以 rc=1 结束——脚本末段用了错误类名 `LivePortGuardState`（真实为 `_GuardState`）。
> 现已修正并重跑（`P5-…-RERUN-*.txt`, rc=0），归档的是修正后的版本；五行数据与 final ledger 在两次运行中一致。
