#!/bin/bash
# CARD-W4-4b7-TAIL —— W4 三个结构门的「先绿后红」负控跑器（共用实现）。
#
# 三个薄壳 negctl_whitelist.sh / negctl_seam.sh / negctl_order.sh 各自 exec 本脚本并
# 钉死 --gate，其余参数透传。清单只有这一份，避免两份手抄清单各自漂移。
#
# 三个阶段（--phase）：
#   before  把测试文件换成 $PREREQ 那版（未硬化的门）+ 对照源 → 目标门应 PASSED（门盲）
#   after   测试文件保持工作树（已硬化的门）   + 对照源 → 目标门应 FAILED（门看见了）
#   clean   两份文件都不动（干净源）                     → 目标门应 PASSED（不自伤）
#   all     依次跑上面三个
#
# 纪律：
#   * 对照输入写进**工作树**的被守源，临时目录里放的是**原文件备份**；EXIT trap 从备份无条件还原，
#     跑前/跑后全文件 shasum 必须逐字同。⛔ 这证明的是**还原正确**，**不是运行期间隔离** ——
#     变异期间工作树上确实是对照输入，别的进程若同时跑就会看到它（Codex round-1 MEDIUM-3 指出，
#     round-2 LOW-3 复查本条注释是否已同步；墙钟看门只缩小影响面，不改变这个事实）；
#   * 变异锚点必须**恰好命中 1 次**，否则立刻退出 —— 静默落空的变异会让「门真红」变成假话；
#   * 「应通过」那一跑核的是 `<nodeid> PASSED` 这个**身份**，不是进程 rc、不是命中总数
#     （UAT-CARD-W4-7 LOW-3a）；
#   * 未识别参数一律 rc≠0 并打印 `unknown arg: <x>`（同 LOW-3a）。
#
# ⛔ 禁止在本脚本里跑目录级 pytest：whitelist 的对照输入会让 _GuardState.record() 自死锁，
#    只有「不执行 record()」的定向 AST 门跑才是安全的（本脚本只跑指定 nodeid）。

set -u

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TREE="$(cd "$SELF_DIR/../../.." && pwd)"
GUARD_REL="backend/tests/support/live_port_guard.py"
TEST_REL="backend/tests/unit/test_live_port_guard_contract.py"

GATE=""
PHASE="all"
PREREQ="46e7bf77"
WANT_HELP=0
#: pytest 单节点跑的墙钟上限（秒）。对照输入之一是自死锁形态，万一有别的路径走到
#: 变异后的 record()，没有上限就会挂住、EXIT trap 也轮不到执行（Codex round-1 MEDIUM-3）。
TIMEOUT_SECS="${NEGCTL_TIMEOUT_SECS:-180}"

die() { echo "$*" >&2; exit 2; }

# ⛔ 先把**全部**参数解析完、再校验取值、**最后**才处理 --help（Codex round-1 LOW-④ +
#    round-2 LOW-4）：早退会让 `--help --nonsense-arg` / `--help --phase bogus` 静默放过。
#    取值本身也不许以 `-` 开头 —— 否则 `--phase --nonsense-arg` 会把未知开关当成值吞掉。
# ⛔ 缺值检查必须在**调用方**数实参（Codex round-3 LOW-3）：写成 need_value "$1" "${2-}"
#    时被调方永远看得到第二个实参（空串），缺值诊断走不到，最后死在 $2: unbound variable。
need_value() {  # $1=flag  $2=候选值（调用方已保证存在）
  case "$2" in
    "") die "unknown arg: <empty>  ($1 的取值不得为空串 —— 空 PREREQ 会让 git show ':path' 读 index"\
            " 而不是指定的前提提交，Codex round-4 LOW-2)" ;;
    -*) die "unknown arg: $2  (它出现在 $1 的取值位置；取值不得以 - 开头)" ;;
  esac
}

while [ $# -gt 0 ]; do
  case "$1" in
    --gate)   [ $# -ge 2 ] || die "missing value for --gate";   need_value "$1" "$2"; GATE="$2"; shift 2 ;;
    --phase)  [ $# -ge 2 ] || die "missing value for --phase";  need_value "$1" "$2"; PHASE="$2"; shift 2 ;;
    --prereq) [ $# -ge 2 ] || die "missing value for --prereq"; need_value "$1" "$2"; PREREQ="$2"; shift 2 ;;
    -h|--help) WANT_HELP=1; shift ;;
    *) die "unknown arg: $1  (accepted: --gate --phase --prereq -h/--help)" ;;
  esac
done

case "$GATE" in
  whitelist|seam|order) : ;;
  "") die "unknown arg: <missing --gate>  (accepted values: whitelist seam order)" ;;
  *)  die "unknown arg: --gate $GATE  (accepted values: whitelist seam order)" ;;
esac
case "$PHASE" in
  before|after|clean|all) : ;;
  *) die "unknown arg: --phase $PHASE  (accepted values: before after clean all)" ;;
esac

if [ "$WANT_HELP" = 1 ]; then
  echo "usage: $(basename "$0") [--phase before|after|clean|all] [--prereq <sha>]"
  exit 0
fi

N_PREFIX="tests/unit/test_live_port_guard_contract.py"
case "$GATE" in
  whitelist)
    BEFORE_NODES=("$N_PREFIX::TestSettlementAtomicity::test_settlement_path_never_nests_the_lock")
    AFTER_NODES=("${BEFORE_NODES[@]}")
    EXPECT_TEXTS=("未经确认的持锁调用")
    ;;
  seam)
    BEFORE_NODES=("$N_PREFIX::TestFinalizeRaceSeam::test_seam_is_called_unconditionally_not_inside_a_condition")
    AFTER_NODES=("$N_PREFIX::TestFinalizeRaceSeam::test_seam_runs_exactly_once_on_a_blocked_attempt")
    EXPECT_TEXTS=("受拦路径上注入点被执行了 0 次")
    ;;
  order)
    BEFORE_NODES=(
      "$N_PREFIX::TestInstallOrder::test_audit_hook_is_installed_before_the_target_precheck"
      "$N_PREFIX::TestInstallOrder::test_final_accounting_is_registered_before_the_precheck"
    )
    AFTER_NODES=("${BEFORE_NODES[@]}")
    EXPECT_TEXTS=("承重 hook 装在预检之后" "结算器排到了 hook 前面")
    ;;
esac

PYTEST="$TREE/backend/.venv/bin/pytest"
[ -x "$PYTEST" ] || die "pytest 缺席：$PYTEST"

TMPD="$(mktemp -d "${TMPDIR:-/tmp}/negctl-w4-XXXXXX")"
cp "$TREE/$GUARD_REL" "$TMPD/guard.orig"
cp "$TREE/$TEST_REL"  "$TMPD/test.orig"
SHA_GUARD_BEFORE="$(shasum -a 256 "$TREE/$GUARD_REL")"
SHA_TEST_BEFORE="$(shasum -a 256 "$TREE/$TEST_REL")"

restore() {
  cp "$TMPD/guard.orig" "$TREE/$GUARD_REL"
  cp "$TMPD/test.orig"  "$TREE/$TEST_REL"
}
trap restore EXIT

apply_mutant() {
  GATE="$GATE" SRC="$TMPD/guard.orig" DST="$TREE/$GUARD_REL" python3 - <<'PY' || exit 3
import os, sys
gate, src, dst = os.environ["GATE"], os.environ["SRC"], os.environ["DST"]
text = open(src, encoding="utf-8").read()
PATCHES = {
    # ① 别名赋值后调用：ledger() 自己会取 self._lock ⇒ 不可重入锁的自死锁形态。
    #    旧门只认字面 self.<name>(...)，这两行它一条都数不到。
    "whitelist": (
        '        addr_text = _safe_repr(address)\n'
        '        with self._lock:\n'
        '            stale = gen != self.current_gen\n',
        '        addr_text = _safe_repr(address)\n'
        '        with self._lock:\n'
        '            _f = self.ledger\n'
        '            _f()\n'
        '            stale = gen != self.current_gen\n',
    ),
    # ② 注入点变成 break 之后的死语句：四条结构子规则条条仍然满足（独立 Expr /
    #    在受拦分支 body 里 / 祖先链无恒假分支 / 不进任何判据），运行时永不执行。
    "seam": (
        '            try:\n'
        '                _finalize_race_seam_hook()\n'
        '            except BaseException:  # noqa: BLE001 —— 见上：注入点不得影响控制流\n'
        '                pass\n',
        '            try:\n'
        '                while True:\n'
        '                    break\n'
        '                    _finalize_race_seam_hook()\n'
        '            except BaseException:  # noqa: BLE001 —— 见上：注入点不得影响控制流\n'
        '                pass\n',
    ),
    # ③ 诱饵 _install_audit_hook() 放进 `if True: pass` 的死 else 并摆在预检之前，
    #    真调用挪到预检之后。只认字面恒假的旧剪枝会把诱饵当可达，顺序读成「对的」。
    "order": (
        '    _install_audit_hook()\n'
        '    register_final_accounting()\n'
        '    if os.environ.get(ENV_REQUIRE_BLOCKED_TARGET) == "1":\n'
        '        assert_neo4j_target_blocked()\n',
        '    if True:\n'
        '        pass\n'
        '    else:\n'
        '        _install_audit_hook()\n'
        '    register_final_accounting()\n'
        '    if os.environ.get(ENV_REQUIRE_BLOCKED_TARGET) == "1":\n'
        '        assert_neo4j_target_blocked()\n'
        '    _install_audit_hook()\n',
    ),
}
old, new = PATCHES[gate]
hits = text.count(old)
if hits != 1:
    sys.exit(f"[FATAL] 对照输入锚点命中 {hits} 次（须恰好 1）—— 变异静默落空会让『门真红』变成假话")
open(dst, "w", encoding="utf-8").write(text.replace(old, new, 1))
print(f"[mutant] {gate}: 锚点命中 1 次，已写入 {dst}")
PY
}

# pytest 单节点跑 + 墙钟上限（macOS 无 coreutils `timeout`，自己看门）。
# stdout 通过临时文件回收，避免 $(...) 在被杀时丢输出。
# ⛔ 用 `set -m` 起独立进程组，超时时杀**整组**（Codex round-2 LOW-3）：pytest 可能派生
#    子进程，只 `kill -9 $pid` 不保证整棵进程树结束，会留孤儿。本卡未观察到真实孤儿，
#    这是防御性收紧，不是已复现缺陷。
run_pytest() {
  local outfile="$TMPD/pytest-out.$$"
  set -m
  ( cd "$TREE/backend" && PYTHONDONTWRITEBYTECODE=1 "$PYTEST" -v -p no:cacheprovider "$@" ) \
    > "$outfile" 2>&1 &
  local pid=$! waited=0
  set +m
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$waited" -ge "$TIMEOUT_SECS" ]; then
      echo "[FAIL] pytest 超过 ${TIMEOUT_SECS}s 未退出（自死锁形态的对照输入被真执行？）——强制终止整个进程组" >> "$outfile"
      kill -9 -- "-$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
      wait "$pid" 2>/dev/null
      PYTEST_RC=124
      PYTEST_OUT="$(cat "$outfile")"
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  wait "$pid"
  PYTEST_RC=$?
  PYTEST_OUT="$(cat "$outfile")"
}

# ⛔ nodeid 判定必须绑**结果行本身**（Codex round-1 LOW-④）：裸
#    `grep -F "$node PASSED"` 没有左边界，`other/<完整nodeid> PASSED` 或正文里转述的
#    `expected <nodeid> PASSED` 都能冒充。pytest -v 的结果行形如
#    `<nodeid> PASSED  [ 50%]`，所以按**字段精确相等**判（不用正则，免去 nodeid 里
#    `/` `.` `::` `[]` 的转义问题 —— 转义写错本身就是一类静默假阴性）。
#
# ⛔⛔ 但 **awk 未匹配时退出码仍是 0**（Codex round-2 MEDIUM-1 实测：
#     `printf 'a b\n' | awk '$1=="zzz"'; echo $?` → 0）。上一版直接拿它当条件用，
#     整个 nodeid 身份检查因此**恒真** —— 修 LOW-④ 时换的工具带进来一个比原问题更大的
#     假绿。所以这里显式判**输出是否非空**，并把 awk 的 `exit 1` 也补上作双保险。
node_result_line() {
  local node="$1" want="$2" line
  line="$(printf '%s\n' "$PYTEST_OUT" | awk -v n="$node" -v w="$want" '$1 == n && $2 == w { print; found = 1 } END { exit(found ? 0 : 1) }')" || return 1
  [ -n "$line" ] || return 1
  printf '%s\n' "$line"
}

run_nodes() {
  local want="$1"; shift
  local -a nodes=("$@")
  local node ok=0
  run_pytest "${nodes[@]}"
  echo "$PYTEST_OUT"
  echo "[pytest rc=$PYTEST_RC]"
  for node in "${nodes[@]}"; do
    if node_result_line "$node" "$want" > /dev/null; then
      echo "[OK] nodeid 级判定命中（行首锚）：$(node_result_line "$node" "$want" | head -1)"
    else
      echo "[FAIL] 正文里没有以 \`$node\` 开头、紧跟 $want 的结果行（这才是判据，不是进程 rc）"
      ok=1
    fi
  done
  if [ "$want" = "PASSED" ] && [ "$PYTEST_RC" -ne 0 ]; then
    echo "[FAIL] 期望全 PASSED 但 pytest rc=$PYTEST_RC"; ok=1
  fi
  return $ok
}

phase_before() {
  echo "=== phase before（$PREREQ 版未硬化门 + 对照输入 ⇒ 期望 PASSED，门盲）==="
  git -C "$TREE" show "$PREREQ:$TEST_REL" > "$TREE/$TEST_REL" || return 3
  apply_mutant || return 3
  run_nodes PASSED "${BEFORE_NODES[@]}"
}

phase_after() {
  echo "=== phase after（工作树已硬化门 + 对照输入 ⇒ 期望 FAILED）==="
  cp "$TMPD/test.orig" "$TREE/$TEST_REL"
  apply_mutant || return 3
  local node text ok=0 summary matched
  run_pytest "${AFTER_NODES[@]}"
  echo "$PYTEST_OUT"
  echo "[pytest rc=$PYTEST_RC]"
  if [ "$PYTEST_RC" -ne 1 ]; then
    echo "[FAIL] 期望 pytest rc=1（有用例真红），实测 rc=$PYTEST_RC —— 收集错误 / 超时 / 其它都不算门红"; ok=1
  fi
  for node in "${AFTER_NODES[@]}"; do
    if node_result_line "$node" "FAILED" > /dev/null; then
      echo "[OK] nodeid 级判定命中（行首锚）：$(node_result_line "$node" FAILED | head -1)"
    else
      echo "[FAIL] 正文里没有以 \`$node\` 开头、紧跟 FAILED 的结果行 —— 门没看见这条对照输入"; ok=1
    fi
  done
  # ⛔ 关键词必须绑到**同一个节点的失败原因**上（Codex round-1 LOW-④ / round-2 LOW-2）：
  #    整份输出里搜关键词会被「红在别的断言、而关键词来自回溯里的源码或捕获输出」蒙混过关。
  #    pytest 的 `short test summary info` 行形如 `FAILED <nodeid> - <异常与首行消息>`。
  #    三处收紧：① 只在 `short test summary info` 之后的区段里筛（不是整份输出）；
  #    ② nodeid 要求紧跟在 `FAILED ` 之后（awk 字段比较，有左边界）；
  #    ③ 关键词与节点**按下标一一配对**，不做交叉搜索 —— 否则 order 的两个关键词
  #       可以都由同一个节点提供，另一个节点红在别处也能过。
  # ⛔ 只取**最后一个** summary 区段（Codex round-3 LOW-2）：捕获输出里可以出现一整段
  #    伪造的 `=== short test summary info ===`，旧写法把多个匹配区段合并，伪造段就能供词。
  #    pytest 真正的 summary 永远在输出末尾，所以遇到新标题就把已收的清空、从头再收。
  summary="$(printf '%s\n' "$PYTEST_OUT" \
    | awk '/^=+ short test summary info =+$/ { inseg = 1; n = 0; next }
           inseg && /^=+ / { inseg = 0 }
           inseg { buf[n++] = $0 }
           END { for (i = 0; i < n; i++) print buf[i] }')"
  echo "--- short test summary info 区段（节点 ↔ 失败原因同一行）---"
  printf '%s\n' "$summary"
  if [ "${#EXPECT_TEXTS[@]}" -ne "${#AFTER_NODES[@]}" ]; then
    echo "[FAIL] 关键词条数 ${#EXPECT_TEXTS[@]} ≠ 目标节点条数 ${#AFTER_NODES[@]} —— 无法一一配对"; ok=1
  else
    local i
    for i in "${!AFTER_NODES[@]}"; do
      node="${AFTER_NODES[$i]}"; text="${EXPECT_TEXTS[$i]}"
      if printf '%s\n' "$summary" \
           | awk -v n="$node" '$1 == "FAILED" && $2 == n' \
           | grep -qF "$text"; then
        echo "[OK] 断言消息绑在该节点自己的 summary 行上：$node ← 「${text}」"
      else
        echo "[FAIL] 「${text}」没出现在 $node 自己的 summary 行上 —— 红在别处不算数"; ok=1
      fi
    done
  fi
  return $ok
}

phase_clean() {
  echo "=== phase clean（干净源 + 已硬化门 ⇒ 期望 PASSED，不自伤）==="
  restore
  run_nodes PASSED "${AFTER_NODES[@]}"
}

overall=0
case "$PHASE" in
  before) phase_before || overall=1 ;;
  after)  phase_after  || overall=1 ;;
  clean)  phase_clean  || overall=1 ;;
  all)
    phase_before || overall=1
    phase_after  || overall=1
    phase_clean  || overall=1
    ;;
esac

restore
SHA_GUARD_AFTER="$(shasum -a 256 "$TREE/$GUARD_REL")"
SHA_TEST_AFTER="$(shasum -a 256 "$TREE/$TEST_REL")"
echo "--- 全文件 shasum 跑前/跑后 ---"
echo "guard before: $SHA_GUARD_BEFORE"
echo "guard after : $SHA_GUARD_AFTER"
echo "test  before: $SHA_TEST_BEFORE"
echo "test  after : $SHA_TEST_AFTER"
if [ "$SHA_GUARD_BEFORE" != "$SHA_GUARD_AFTER" ] || [ "$SHA_TEST_BEFORE" != "$SHA_TEST_AFTER" ]; then
  echo "[FAIL] 还原不逐字节 —— 对照输入留在了树上"; overall=1
else
  echo "[OK] 两份文件跑前跑后逐字节相同"
fi

echo "negctl gate=$GATE phase=$PHASE overall_rc=$overall"
exit $overall
