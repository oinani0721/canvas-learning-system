# 独立复核 round-4（收口）：CARD-W4-7

## 一 背景与最小读取面

被审对象是 pytest 进程内的隔离门（audit `socket.connect` 事件，阻止测试连 7691/7687）。

轮次：r1 = 0 BLOCKER / 2 HIGH（已闭合）；r2 = **0/0**，余 MEDIUM 2 / LOW 1；
r3 = **0/0**，余 MEDIUM 2 / LOW 2。作者两轮都**没有把 MEDIUM/LOW 留作登记**，逐条整改。
本轮请核对 r3 的四条整改，并判断是否可以收口。

**只读**（工作目录 = 本仓库根）：

1. **r3 之后的增量**：`git diff ad4c853b <审SHA> -- backend/tests/unit/test_live_port_guard_contract.py`
   （本轮**只动了测试文件**，`live_port_guard.py` 与探针脚本未改）；
2. 交叉参数化的两条门：`test_lying_str_subclass_on_uvloop_value_is_still_blocked`
   与 `test_lying_str_subclass_on_other_value_is_not_blocked`，以及类级
   `_Denier` / `_Affirmer`；
3. 证据与跑器（`_bmad-output/审查/evidence-w47/`）：
   `r1-high-negctl.sh`（逐参数绑定版）、`negctl_patch_w47.py`（新增 `r3-med1`）、
   `negctl-r{1-high1,1-high2,2-med1,3-med1}-after4-*.txt`、
   `m4-importlib-probe.py`（新增 `import_succeeded`）+ `m4-importlib-after4-*.txt`、
   `unit-after4-*.txt` 与 `unit-after5-*.txt`（见 §二末条）。

## 二 作者对 r3 四条的整改自述（请独立核对）

- **MEDIUM-1（交叉覆盖）**：改成 `{denier, affirmer} × {uvloop, uvloop.loop}` 必拦、
  `× {json, uvloopx}` 必放。你给的第二个反例做成负控 `r3-med1`。
  ⚠️ **实测更正了作者的推断**：r2 的反例（`... and name.startswith(...)`，走**重载
  startswith**）实际放行的是 `uvloop.loop-denier`，不是作者推的 `-affirmer`；
  r3 的反例（`... and not (name == "uvloop")`，走**重载 __eq__**）才放行 `-affirmer`。
  **两个反例各放行笛卡尔积里不同的一格** —— 这是交叉参数化的实证理由。
- **MEDIUM-2（基线判据）**：加 `import_succeeded` 字段；基线必须**导入成功且看到事件**，
  否则 `INCONCLUSIVE` 返回 2。
- **LOW-3a（逐参数绑定）**：跑器改 `EXPECT_FAIL` / `EXPECT_PASS` 逐参数 id 绑定，
  rc 必须**恰好 1**（拒绝 2/3）。**正是这个改动当场抓出了上面那个推断错误**。
- **LOW-3b（信号退出）**：EXIT 只负责还原；INT/TERM 显式退出 130 / 143。
- **`tests/unit` 的一次 `>` 行**：`unit-after4` 那跑里
  `test_candidate_service.py::test_accept_candidate_already_accepted_returns_422` 新出现、
  `test_mock_degradation_transparency.py::…::test_mock_mode_logs_warning` 消失，
  **总数仍 202**。作者定性为**既有顺序依赖 flaky、非本卡引入**，依据四条：两文件本卡
  diff 为空、两文件 0 命中 guard 符号、candidate 单跑与双文件跑均绿、mock_degradation
  单跑与双文件跑均红。复跑 `unit-after5-*.txt` 与基线 diff 为空。

## 三 请按重要性排序回答

1. **交叉参数化是否闭合**：`{denier,affirmer} × {uvloop,uvloop.loop,json,uvloopx}` 之后，
   还有没有能通过全部八格、却按谎话判定的错误实现？
2. **`import_succeeded` 是否闭合 MEDIUM-2**：基线判据现在还有没有能返回 0 却其实没验到的路径？
3. **逐参数绑定是否闭合 LOW-3a**：`EXPECT_FAIL`/`EXPECT_PASS` 写死参数 id，将来增删参数时
   会变成假红还是假绿？哪种更安全？
4. **作者对 flaky 的定性是否站得住**：四条依据够不够排除「本卡引入」？
   有没有更强的判据（在只读范围内）？
5. **本轮增量有没有引入新问题**；前三轮的 HIGH/MEDIUM 结论是否仍成立。
6. **是否可以收口**：以只读证据看，还有没有必须在本卡处理的项？

## 四 输出格式

每条给：**级别** + **文件:行** + **依据** + **建议**。只读判定不了的写「未验证」。
开头给一行总结：BLOCKER 数 / HIGH 数 + 一句「可否收口」。

## 五 边界

- **只读**；不跑测试/探针/负控；**不连任何端口**。
- CARD-W4-4b 的 HIGH-2 / M4 / M7 / M8 不在本卡；`negative_control.py` 与四套 harness 归 U8；
  `backend/app/**` 不在本卡。
