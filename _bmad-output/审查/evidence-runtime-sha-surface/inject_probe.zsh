#!/usr/bin/env zsh
# CARD-RUNTIME-SHA-SURFACE 注入 harness（卡文 §二.② 的加固版）
#   用法: zsh inject_probe.zsh <门路径> <unchanged|CHANGED>
#   $2 = 三个扩面目标的期望结论；not_watched 验伪锚**恒**期望 unchanged。
# 加固（相对卡文原版）：
#   1. 断言结论行**恰好 1 条**（不靠 tail -1 的位置锚定，见「⛔ | tail -1 取汇总行 = 位置锚定」）；
#   2. 断言 rc（unchanged ⇒ 0；CHANGED ⇒ 1），不只看文案；
#   3. 每行打印 fake-backend 根，便于复核「工作树零碰」。
set -u
GATE_SRC="$1"; WANT="$2"
typeset -i bad=0
for rel tag in \
  app/data/lancedb_pending_index__probe.jsonl L \
  data/neo4j_memory.json N \
  data/llm_call_logs.db D \
  app/data/not_watched_probe.txt X ; do
  T=$(mktemp -d); trap "rm -rf $T" EXIT
  mkdir -p "$T/backend/app/data" "$T/backend/data" "$T/backend/tests" "$T/backend/scripts"
  print -r -- '# fake' > "$T/backend/app/main.py"
  cp "$GATE_SRC" "$T/backend/scripts/lifespan_isolation_runtime_sha.sh"
  out=$(bash "$T/backend/scripts/lifespan_isolation_runtime_sha.sh" \
        -- /bin/sh -c "printf 'x\n' >> $T/backend/$rel" 2>&1); rc=$?
  # not_watched（tag=X）是验伪锚：无论扩面前后都必须 unchanged
  exp="$WANT"; [[ "$tag" == X ]] && exp=unchanged
  exp_rc=0; [[ "$exp" == CHANGED ]] && exp_rc=1
  hits=$(print -r -- "$out" | grep -cE '^RUNTIME-FILES: (unchanged|CHANGED)$')
  line=$(print -r -- "$out" | grep -E '^RUNTIME-FILES: (unchanged|CHANGED)$')
  print -r -- "tag=$tag rel=$rel exp=$exp exp_rc=$exp_rc got='${line:-<none>}' hits=$hits rc=$rc root=$T"
  [[ "$hits" == 1 ]] || { print -r -- "  !! 结论行条数 != 1"; bad=1; }
  [[ "$line" == "RUNTIME-FILES: $exp" ]] || { print -r -- "  !! 结论文案不符"; bad=1; }
  [[ "$rc" == "$exp_rc" ]] || { print -r -- "  !! rc 不符"; bad=1; }
  trap - EXIT; rm -rf "$T"
done
print -r -- "INJECT-SUMMARY want=$WANT bad=$bad"
exit $bad
