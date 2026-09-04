# CARD-G6-2b round-5 复审 — 第一次（绑 9cfcb189）：网络断连，正文未产出

首发命令按卡文 §六 执行（`codex exec --sandbox read-only -m gpt-5.6-sol -c
model_reasoning_effort="ultra" … </dev/null`），运行约 26 分钟后 `codex rc=1`，本文件被写成
**0 字节**。真因在同名 `.stderr`（337KB，未入库）里可证，逐条摘录：

```
ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket:
      IO error: tls handshake eof, url: wss://chatgpt.com/backend-api/codex/responses
ERROR: Reconnecting... 1/5 … 5/5
warning: Falling back from WebSockets to HTTPS transport.
         stream disconnected before completion: tls handshake eof
ERROR: Reconnecting... 1/5 … 5/5
ERROR: stream disconnected before completion: error sending request for url
       (https://chatgpt.com/backend-api/codex/responses)
tokens used 136,441
```

**不是内容拦截，也不是额度**：stderr 里的推理轨迹显示它一路在正常读码、写并执行自己的验证
脚本（`**Confirming test door lacks mutation resistance**`、`**Planning Node payload
extraction and injection**` 等），直到传输层断开。

## 抢救到的东西（报告丢了，证据没丢）

它在断连前已经把自己构造的 **11 条反例集跑完了**，`cases = {...}` 的源码与逐条判定都留在
stderr 里。逐字还原后喂给本卡第一版的门，抓出 **8 条漏网 + 1 条误伤**，其中两条是本卡第一版
自己引入的（`_OWN_DEFINITIONS` 豁免没区分 def/class、没限定至多一个定义点）。

整改与红绿矩阵见：
- `_bmad-output/验收单/UAT-CARD-G6-2b-交互壳残留收口-2026-09-04.md` §四之三
- `_bmad-output/审查/evidence-g62b/probe-matrix.md`（负向 25 + 反向 4 + 验伪锚）

## 重发

按卡文 §六「0 字节 → 重发一次」，重发绑本卡最终 tip；结果覆盖本文件。
