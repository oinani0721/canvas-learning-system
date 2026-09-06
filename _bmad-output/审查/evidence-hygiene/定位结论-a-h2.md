# (a) 定位结论 · H2 = tests/contract 属性输入

> 车道 `card-y6-testhygiene`，代码树 `03ac8bf8`，实测 2026-09-06。

## 一 全量 H2 按卡文原命令不可行（如实记录，非借口）

命令（卡文裁判 2）：

```
cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/contract/test_openapi_contract.py -q -p no:cacheprovider -p no:randomly --override-ini='addopts='
```

实跑 `unit-run-h2-20260906T015411.txt`：**15 分 29 秒只完成 4 个 operation**
（log 内容 `FFFF` = 4 个 FAILED）。该文件收集数 **206 tests**
（`--co -q` 实测，`206 tests collected in 57.02s`）⇒ 全量约需 **13 小时**。
`schemathesis` 的 `deadline=10000` + `max_examples=10` 让每个 operation 约 3.9 分钟。

中止时（`status-after-h2-partial.txt`）三签名全空 —— 但这**不能**当作
「H2 未复现」，因为 setup-wizard 那个 operation 根本还没轮到。
按卡文口径这属于「未跑到」，不是「不存在」。

**处置**：改用**同文件、同机制**的定向子集 —— `-k setup`，
精确选中唯一相关 operation：

```
tests/contract/test_openapi_contract.py::test_api_contract[POST /api/v1/system/setup-wizard]
```

（`--co -q | grep -c '::'` = 1，无歧义。）

### 第一次定向尝试是**假绿**，已识别并修正

第一版用完整 nodeid 带方括号传参：

```
pytest "tests/contract/test_openapi_contract.py::test_api_contract[POST /api/v1/system/setup-wizard]"
```

→ `rc=4`（pytest usage error），`10 warnings in 0.71s`，**0 个用例执行**。
此时三签名全空。若据此写「H2 未复现」，就是把「没跑」当成「没发生」。

修正：改 `-k setup`，并在脚本里加**硬前置断言** —— log 里必须出现
`1 (passed|failed|error)`，否则直接 `exit 96` 并声明「判据无效」。

## 二 定向 H2（改前代码）—— **复现，且与冻结证据树逐条吻合**

为证明是**改前**行为，用 `git show HEAD:backend/app/api/v1/system.py` 换回
HEAD 版本再跑，`EXIT trap` 无条件还原并 sha 自证（脚本 `h2-directed.sh`）：

```
HEAD sha   = bbad6c2f5163177d1dea7d1364090f02ea886e39c1916f991119519239846b05
现文件 sha = bbad6c2f5163177d1dea7d1364090f02ea886e39c1916f991119519239846b05
改前代码是否含 field_validator（应为 0）: 0
...
RESTORE-OK sha=5f1d7c1d77ef694525fbdd4e220c7a90938b869f7d9ab7c3ed7de549ecaef9c4
```

跑完（`1 failed, 205 deselected, 1358 warnings in 614.71s`）后的三签名
（`status-after-h2-directed.txt`）：

| 签名 | 结果 |
|---|---|
| ① `backend/` 四路径 | **全部出现** ⚠️ |
| ① `git status --porcelain backend` | `?? backend/CLAUDE.md` `?? backend/outputs/` `?? backend/raw/` `?? backend/wiki/` |
| ① `find backend -maxdepth 1 -newer sentinel` | 命中 `backend/{wiki,outputs,raw,CLAUDE.md}` |
| ③ 两文件 sha | 未变（本次只跑 setup-wizard 一个 operation） |
| ② `/tmp/test-vault*` | 出现（并行车道干扰面，见 `定位结论-a.md`，非本条结论所依赖） |

### 与冻结证据树 `card-z4-redbase` @ `c8611a89` 的比对

文件树 `diff` → **逐条相同**：

```
backend/outputs  backend/outputs/exam_boards  backend/outputs/exam_boards/.gitkeep
backend/raw      backend/raw/.gitkeep
backend/wiki     backend/wiki/canvases  backend/wiki/canvases/.gitkeep
                 backend/wiki/concepts  backend/wiki/concepts/.gitkeep
```

`backend/CLAUDE.md` 的 sha256 **完全相同**：

```
319599d2ca3c6f1f9839bb2a17e96e438bcd82d339f46e745a754d36b5449fa8   （本次复现）
319599d2ca3c6f1f9839bb2a17e96e438bcd82d339f46e745a754d36b5449fa8   （证据树）
```

**唯一差异**：证据树还有一条 ` M backend/config/subject_mapping.yaml`。
本次只跑了 setup-wizard 一个 operation，没跑到写 subject_mapping 的那个端点
（metadata 保存面），故 sha 未变 —— 差异方向自洽，不是矛盾。

## 三 结论

> **措辞收窄（Codex round-1 #3，按其建议改写）**：本卡证明的是
> 「**该链能产生该现场**」+「台账原归因缺乏支持」，**不是**「历史那次就是它干的」。
> `CLAUDE.md` 的 sha 一致只说明是同一段代码写的（`vault_init_service.py:40`
> 是固定模板），**该 SHA 不是历史调用者的唯一指纹**。

**`backend/` 里的 vault 骨架，本卡实证「能产生该现场」的写入链是**

```
tests/contract/test_openapi_contract.py::test_api_contract[POST /api/v1/system/setup-wizard]
```

机制：`@schema.parametrize()` 对全端点做属性输入且 **无 exclude**
（grep 0 命中）；`SetupWizardRequest.vault_path` 在 OpenAPI 里只是
无约束的 `type: string`，于是 hypothesis 会生成空串 / 相对路径一类的值；
`system.py:441` 的 `Path(v).resolve()` 把它们**静默**拼成 cwd（pytest 从
`backend/` 起跑 ⇒ cwd = `backend/`）；`initialize_vault()` 随即在那里建骨架。

**这条链与 `tests/unit` 无关。** H1（`tests/unit` 目录级）在同样三签名下
`backend/` 三处判据全空 ⇒ 台账归给 `test_vault_init_service.py` **缺乏支持**。

> **两处限定（Codex round-1 #3）**：① H1 收尾干净只支持「**该配置下**未复现」，
> 不足以排除其他测试集合／fixture 覆盖／执行顺序／期间写入后又被清理的情况；
> ② 「那 8 个用例全经 `vault_dir(tmp_path)`」是**我的源码核对陈述**，
> Codex 按读取边界未独立验证该文件源码 —— 如实标注，不冒充双方确认。

## 四 修后验证 —— 受控对照实验

同一条定向命令、同一个 operation，唯一变量是 `system.py` 的 `field_validator`
（`h2-directed-AFTER-20260906T023028.txt` / `status-after-h2-after.txt`）：

| 判据 | 改前（`621.55s` 前那轮 `614.71s`） | 改后（`621.55s`） |
|---|---|---|
| `backend/raw` `wiki` `outputs` `CLAUDE.md` | **全部出现** | **全部 absent** |
| `git status --porcelain backend` | `?? CLAUDE.md` `?? outputs/` `?? raw/` `?? wiki/` | 只剩本卡改的 3 个文件 |
| `find backend -maxdepth 1 -newer sentinel` | 命中 4 条 | **空** |
| 两文件 sha | 未变 | 未变 |
| `/tmp/test-vault*` | 出现 | **两条 No such file** |

### 失败身份未被改变（**不等于**零回归）

两轮 pytest 都是 `1 failed`，但**失败原因逐字同型**：

```
改前: hypothesis.errors.DeadlineExceeded: Test took 23885.92ms, ... deadline of 10000.00ms
改后: hypothesis.errors.DeadlineExceeded: Test took 31706.09ms, ... deadline of 10000.00ms
```

即：这个 contract operation 在改前就是红的（超时，根因是端点内
`startup_health_check` 去连 7691 与 Ollama 各自超时，远超 10s deadline
—— 与第十一批 Z7-C 裁定的「合约测试慢」是同一件事），改后仍红且原因相同。
本卡**没有**改变它的失败身份，只消除了它的写盘副作用。

> **措辞收窄（Codex round-1 #2）**：这条只支持「**该 operation 的失败身份未变**」，
> **不支持**更广义的「零回归」—— `-k setup` 把覆盖从 206 个 operation 缩为 1，
> 且相同的 `DeadlineExceeded` 不能排除被超时遮蔽的其他差异。
> 全量回归面本卡未验证（约需 13 小时），已登记。

（判据绑定失败身份而非 rc：只看「都是 1 failed」不足以证明零回归，
必须比对拒因文本。）
