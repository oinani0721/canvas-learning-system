#!/usr/bin/env zsh
# 收窄正证据：新增的 `lancedb_pending_index__*.jsonl` 是**双下划线**的窄 glob。
#   用法: zsh narrowness_probe.zsh <改后门路径>
# 每一行都是「同一目录、同一前缀，只差分隔符/后缀」的旁文件 —— 若门判它们 CHANGED，
# 说明 glob 写宽了（M14 刚收窄掉的那种假红面被重新造了出来）。
# ⛔ 正锚（G）与它们同跑：真正的命名空间形态必须 CHANGED，否则「全 unchanged」
#    可能只是 glob 整条失效。
set -u
GATE="$1"
typeset -i bad=0
for rel exp note in \
  app/data/lancedb_pending_index_backup.jsonl   unchanged 单下划线人手旁文件 \
  app/data/lancedb_pending_index.jsonl          unchanged 无分隔符的裸名 \
  app/data/lancedb_pending_index__x.jsonl.old   unchanged 后缀不是.jsonl \
  data/neo4j_memory.json.bak                    unchanged 备份后缀 \
  data/llm_call_logs.db-wal                     unchanged SQLite-WAL边车 \
  app/data/lancedb_pending_index__probe.jsonl   CHANGED   正锚-真命名空间形态 ; do
  T=$(mktemp -d); trap "rm -rf $T" EXIT
  mkdir -p "$T/backend/app/data" "$T/backend/data" "$T/backend/tests" "$T/backend/scripts"
  print -r -- '# fake' > "$T/backend/app/main.py"
  cp "$GATE" "$T/backend/scripts/lifespan_isolation_runtime_sha.sh"
  out=$(bash "$T/backend/scripts/lifespan_isolation_runtime_sha.sh" \
        -- /bin/sh -c "printf 'x\n' >> $T/backend/$rel" 2>&1); rc=$?
  exp_rc=0; [[ "$exp" == CHANGED ]] && exp_rc=1
  hits=$(print -r -- "$out" | grep -cE '^RUNTIME-FILES: (unchanged|CHANGED)$')
  line=$(print -r -- "$out" | grep -E '^RUNTIME-FILES: (unchanged|CHANGED)$')
  print -r -- "[$note] rel=$rel exp=$exp got='${line:-<none>}' hits=$hits rc=$rc"
  [[ "$hits" == 1 && "$line" == "RUNTIME-FILES: $exp" && "$rc" == "$exp_rc" ]] || bad=1
  trap - EXIT; rm -rf "$T"
done
print -r -- "NARROWNESS bad=$bad"
exit $bad
