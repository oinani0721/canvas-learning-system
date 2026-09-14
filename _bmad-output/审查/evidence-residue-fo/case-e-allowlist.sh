#!/bin/bash
# CASE e — 允许名单补的 4 条分支确实生效(方向与其余十条相反, 故单列)
# 自述: (e) 补的是 fail-closed **误伤**面, 不是 fail-open。所以这里的期望是反过来的:
#       同一输入在**旧版块**上被拦下(BLOCKED rc=1), 在**新版块**上放行(OK rc=0)。
#       四条分支各跑一份, 外加一条**验伪锚**: 一个不在名单里的同名近邻路径必须**仍被拦下**
#       —— 否则只能说明 case 里的模式写宽了, 不能说明名单补对了。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE e: 允许名单 4 条新分支 + 验伪锚 ==="
prepare_blocks || exit 1
echo "⚠️ 本条**只跑 bash**(下面 run_one/run_two 直接调 bash, 不走 run_both) —— 上面那行"
echo "   「解释器: bash sh」是 prepare_blocks 的统一抬头, 对本条不成立。允许名单的"
echo "   匹配是 case 语句的语义, 与解释器无关, 故未跑双解释器; 如实声明, 不当双解释器证据。"

run_one() {   # $1 = 仓内路径, $2 = 期望(ALLOW|BLOCK)
  local p=$1 want=$2 repo
  repo="$WORK/repo-$(echo "$p" | tr '/.' '__')"
  mkrepo "$repo" || return 1
  mkdir -p "$repo/$(dirname "$p")"
  printf 'x = 1  # %s\n' "$MARK" > "$repo/$p"
  ( cd "$repo" && "$REAL_GIT" add "$p" )
  ( cd "$repo" && bash "$WORK/old.sh" ) > "$WORK/o.out" 2>&1; local orc=$?
  ( cd "$repo" && bash "$WORK/new.sh" ) > "$WORK/n.out" 2>&1; local nrc=$?
  local oldv newv
  if /usr/bin/grep -qF '[Mutant-Scan] OK (staged additions' "$WORK/o.out"; then oldv=OK; else oldv=BLOCKED; fi
  if /usr/bin/grep -qF '[Mutant-Scan] OK (staged additions' "$WORK/n.out"; then newv=OK; else newv=BLOCKED; fi
  local verdict=FAIL
  if [ "$want" = ALLOW ] && [ "$oldv" = BLOCKED ] && [ "$orc" = 1 ] && [ "$newv" = OK ] && [ "$nrc" = 0 ]; then verdict=PASS; fi
  if [ "$want" = BLOCK ] && [ "$oldv" = BLOCKED ] && [ "$orc" = 1 ] && [ "$newv" = BLOCKED ] && [ "$nrc" = 1 ]; then verdict=PASS; fi
  printf '  %-52s want=%-5s old=%-7s(rc=%s) new=%-7s(rc=%s)  %s\n' \
         "$p" "$want" "$oldv" "$orc" "$newv" "$nrc" "$verdict"
  [ "$verdict" = PASS ]
}

ALL=0
run_one backend/scripts/g32ccr1_negative_controls.py        ALLOW || ALL=1
run_one backend/scripts/openapi_drift_negative_control.py   ALLOW || ALL=1
run_one backend/tests/regression/recap_domain_negverify.py  ALLOW || ALL=1
run_one .claude/rules/card-batch-protocol.md                ALLOW || ALL=1
echo "  --- 匹配面实测: case 的 * 会匹配 '/', 故 .claude/rules/*.md 覆盖任意深度 ---"
echo "  (这是 shell case 的语义, 不是笔误; 与既有的 _bmad-output/* 同口径。"
echo "   下面这条按 ALLOW 判, 因为「规则文」本来就包括子目录里的规则文。)"
run_one .claude/rules/nested/deep.md                        ALLOW || ALL=1
echo "  --- 验伪锚(必须仍被两版都拦下, 证明模式没宽到名单之外) ---"
run_one backend/scripts/g32ccr1_negative_controls_copy.py   BLOCK || ALL=1
run_one .claude/rules/card-batch-protocol.md.bak            BLOCK || ALL=1
run_one .claude/rules/notes.txt                             BLOCK || ALL=1
run_one .claude/rulesX/a.md                                 BLOCK || ALL=1
run_one docs/.claude/rules/a.md                             BLOCK || ALL=1

echo "--- 名单原有的 2 条应不受影响(两版都放行) ---"
run_two() {   # 旧新都应 OK
  local p=$1 repo
  repo="$WORK/repo2-$(echo "$p" | tr '/.' '__')"
  mkrepo "$repo" || return 1
  mkdir -p "$repo/$(dirname "$p")"
  printf 'x = 1  # %s\n' "$MARK" > "$repo/$p"
  ( cd "$repo" && "$REAL_GIT" add "$p" )
  ( cd "$repo" && bash "$WORK/old.sh" ) > "$WORK/o.out" 2>&1; local orc=$?
  ( cd "$repo" && bash "$WORK/new.sh" ) > "$WORK/n.out" 2>&1; local nrc=$?
  printf '  %-52s old_rc=%s new_rc=%s\n' "$p" "$orc" "$nrc"
  [ "$orc" = 0 ] && [ "$nrc" = 0 ]
}
run_two backend/scripts/g32b_mutation_gates.py  || ALL=1
run_two backend/scripts/g32cb_mutation_gates.py || ALL=1

if [ "$ALL" = 0 ]; then echo "CASE e: PASS"; else echo "CASE e: FAIL"; fi
exit $ALL
