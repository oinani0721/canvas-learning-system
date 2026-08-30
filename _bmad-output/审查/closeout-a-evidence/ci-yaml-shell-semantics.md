# ② CI 改动的 shell 语义校验（本卡最大的一处「差点翻车」）

> **结论先行**：第一版补丁在**副本上**被抓出会让整条 CI 命令炸掉（exit 127、静默丢 4 个测试文件）。
> 抓到它的不是 YAML 校验器，而是「把 `run:` 脚本真跑一遍数实参」这道校验。全过程零次触碰工作树。

---

## 一、坏在哪

第一版把「出处注释」放进了 `pytest` 的 `\` **续行序列中间**：

```yaml
            tests/regression/test_real_entrypoint_admission.py \
            # BATCH-2026-08-29-第六批 / CARD-收口A: ...        ← ⛔ 就是这里
            tests/regression/test_fsrs_golden_vectors.py \
            tests/regression/test_learning_events_schema_contract.py \
            tests/unit/test_vault_admission.py \
```

**为什么这是错的**：`\<newline>` 在词法阶段就被移除、上下行拼成同一条逻辑行。
于是 `# ...` 变成行内注释，把**该逻辑行剩下的全部内容**吃掉；被吃掉那段里原本的 `\` 也一并消失，
下一行的 `tests/...py` 于是被当成**一条新命令**去执行。

### 最小可复现（不依赖本仓）

```bash
$ cat shelltest.sh
echo ARGS: \
  a.py \
  # 这是一条注释
  b.py \
  c.py \
  --flag "x"

$ bash shelltest.sh
ARGS: a.py
shelltest.sh: line 5: b.py: command not found
$ echo $?
127
```

---

## 二、为什么 YAML 校验抓不到

`yaml.safe_load()` 只把 `run:` 的内容当成一个**字符串标量**——它不解析 shell。
用正则从该字符串里数 `tests/**.py`，坏版本一样数出 17 个，**看起来完全正常**。
这是一个典型的「校验层级错位」：问题在 shell 语义层，校验却停在 YAML 语法层。

---

## 三、真正管用的校验：把 `run:` 脚本原样跑一遍

做法——从 YAML 取出 `Run tests` 步骤的 `run:` 脚本，只替换两处使其无害
（`cd backend` → `cd /tmp`、`python -m pytest` → `printf "%s\n"`），其余**逐字保留**，然后 `bash` 真跑，
数它**实际**传出来多少参数、尾部 flags 有没有幸存。

### 对照结果

| 版本 | exit | 实际到达 pytest 的 `.py` 文件数 | 尾部 flags |
|---|---:|---:|---|
| **坏版本**（注释在续行中间） | **127** | **13** ← 静默丢了 4 个 | 全部丢失 |
| **好版本**（本卡采用） | **0** | **17** ✅ | 全部幸存 |

坏版本丢掉的 4 个文件不只是本卡新增的 2 个，还连带吞掉了**原本就在清单里**的
`tests/unit/test_vault_admission.py` 与 `tests/unit/test_memory_service_contextvar_leak.py`
——即一个"只想加两行"的改动，会顺手废掉两条既有的 CI 覆盖。

好版本实测幸存的尾部 flags：

```
-m / not integration / -v / --tb=short / --junitxml=reports/test-results.xml
/ -q / --no-header / -p / --override-ini=addopts=
```

---

## 四、最终采用的改法（最小 + 合乎本文件既有惯例）

1. **显式清单里只加 2 行**，紧跟在 regression 组末尾（`test_real_entrypoint_admission.py` 之后），
   保持 regression 文件连续，**零注释进入续行序列**。
2. **出处与证据写进步骤上方那个既有注释块**——该文件本来就有这个惯例：
   `#   3. ✅ 已完成 (BATCH-2026-08-25 / CARD-C6) … 文件已加入下方显式清单。`
   本卡按同一格式续写为第 4 条。

---

## 五、复现命令

```bash
SP=<scratchpad>
python3 -c "
import yaml
d=yaml.safe_load(open('.github/workflows/test.yml'))
step=[s for s in d['jobs']['tests']['steps'] if s.get('name')=='Run tests'][0]['run']
step=step.replace('cd backend','cd /tmp').replace('python -m pytest','printf \"%s\n\"')
open('\$SP/run_semantics.sh','w').write(step)
"
bash $SP/run_semantics.sh > $SP/run_args.txt; echo "exit=$?"
grep -c '\.py$' $SP/run_args.txt          # 期望 17
grep -E '^-|junitxml|not integration' $SP/run_args.txt
```
