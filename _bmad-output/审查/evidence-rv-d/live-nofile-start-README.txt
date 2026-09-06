⚠️ 文件名 `live-nofile-start-*.txt` 是按卡文 (a) 的措辞命名的
（卡文说「live learning_events.jsonl shasum → NOFILE」）。

但**实测该文件存在**，所以这个 .txt 里记的是 sha 而不是 "No such file"。
文件名保留原样以对应卡文条目，内容以实测为准。

本卡因此把零写判据改成不变量形式：开工/收工两次 shasum 逐字相同，
对应 `live-sha-start-*.txt` / `live-sha-mid-*.txt` / `live-sha-end-*.txt`。
详见验收单 §一。
