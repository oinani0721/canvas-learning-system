#!/usr/bin/env zsh
# 正锚（positive control）：证明 fake-backend harness 的「检出 CHANGED」这条路径本身是通的。
#   若没有本锚，(c) 先红那四行「全 unchanged」也可能是 harness 坏了（fake 树搭错 /
#   门根本没跑 / 结论行 grep 恒不命中）造成的假绿。
#   用法: zsh posctl_probe.zsh <门路径>
#   注入面一律是**改前门就已监视**的四个形态 ⇒ 期望恒 CHANGED rc=1。
set -u
GATE_SRC="$1"
typeset -i bad=0
for rel tag in \
  data/bug_log.jsonl                      F1 \
  data/outbox/events.jsonl                F2 \
  app/data/vault_index_pending.jsonl      F3 \
  app/data/vault_index_pending__probe.jsonl G1 ; do
  T=$(mktemp -d); trap "rm -rf $T" EXIT
  mkdir -p "$T/backend/app/data" "$T/backend/data/outbox" "$T/backend/tests" "$T/backend/scripts"
  print -r -- '# fake' > "$T/backend/app/main.py"
  cp "$GATE_SRC" "$T/backend/scripts/lifespan_isolation_runtime_sha.sh"
  out=$(bash "$T/backend/scripts/lifespan_isolation_runtime_sha.sh" \
        -- /bin/sh -c "printf 'x\n' >> $T/backend/$rel" 2>&1); rc=$?
  hits=$(print -r -- "$out" | grep -cE '^RUNTIME-FILES: (unchanged|CHANGED)$')
  line=$(print -r -- "$out" | grep -E '^RUNTIME-FILES: (unchanged|CHANGED)$')
  print -r -- "tag=$tag rel=$rel exp=CHANGED exp_rc=1 got='${line:-<none>}' hits=$hits rc=$rc"
  [[ "$hits" == 1 ]] || { print -r -- "  !! 结论行条数 != 1"; bad=1; }
  [[ "$line" == "RUNTIME-FILES: CHANGED" ]] || { print -r -- "  !! 结论文案不符"; bad=1; }
  [[ "$rc" == 1 ]] || { print -r -- "  !! rc 不符"; bad=1; }
  trap - EXIT; rm -rf "$T"
done
print -r -- "POSCTL-SUMMARY bad=$bad"
exit $bad
