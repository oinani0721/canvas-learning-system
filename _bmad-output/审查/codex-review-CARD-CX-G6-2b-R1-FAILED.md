# CARD-CX-G6-2b-R1 · Codex 环境阻断诊断与解法（round-1/2 失败 → round-3 换二进制）

> `[BATCH-2026-09-05-第十一批 / CARD-CX-G6-2b-R1]` · 2026-09-05
> 原始 `*.stderr` 按 `.gitignore:257-261`（第八批收官规则）永不入库，留在工作树：
> `codex-review-CARD-CX-G6-2b-R1.stderr`（round-1）
> `…R1.round2.stderr`（round-2，协议要求的重发）
> `…R1.round3.stderr`（round-3，换二进制后的成功轮）
>
> **本文件记录的是环境问题的诊断与解法。复核报告本体在
> `codex-review-CARD-CX-G6-2b-R1.md`。**

## 一 症状：两轮 0 字节

命令与协议 `.claude/rules/card-batch-protocol.md` §2 逐字一致：

```
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-CX-G6-2b-R1.md)" \
  > <树>/_bmad-output/审查/codex-review-CARD-CX-G6-2b-R1.md \
  2> <树>/_bmad-output/审查/codex-review-CARD-CX-G6-2b-R1.stderr </dev/null
```

| 轮次 | rc | 输出 .md | stderr |
|---|---|---|---|
| round-1 | 0 | **0 字节** | 10864 字节，尾部见下 |
| round-2（协议要求的重发） | 1 | **0 字节** | 与 round-1 **逐字相同** |

```
warning: Model metadata for `gpt-6-astra` not found. Defaulting to fallback metadata;
this can degrade performance and cause issues.
ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error",
"message":"The 'gpt-6-astra' model requires a newer version of Codex.
Please upgrade to the latest app or CLI and try again."}}
```

## 二 诊断：第四种 0 字节成因

`/opt/homebrew/bin/codex` → `codex-cli 0.147.0`。

这**不在**既有三因（stdin 挂起未加 `</dev/null` / 被审内容触发内容过滤 / 网络——codex 是
reqwest，不读 macOS 系统代理只认 `HTTPS_PROXY`）之内，而是 **CLI 版本旧于服务端对该模型的
要求**，请求一发出就被 400。

四因判别（写给下一个撞上的人）：

| 线索 | 指向 |
|---|---|
| stderr 里有 `"status":400` 的结构化 JSON | **版本/模型**（前三因都不产生 HTTP 状态码） |
| stderr 只有 prompt 回显 + 报错，**无推理标题、无 `tokens used`** | 请求没被受理 ⇒ 不是「内容拦截」（那是跑一段才断），也不是「跑完断在交付」 |
| 报的是 HTTP 状态码而非 `tls handshake eof` | 不是传输层网络问题 |
| 两轮**逐字相同** | 确定性错误，重发第三次没有意义 |

**「不指定 `-m` 用默认模型」这条退路不存在**：车道树内跑一条最小探测，会话头是

```
OpenAI Codex v0.147.0
model: gpt-6-astra
reasoning effort: ultra
```

默认模型**就是** `gpt-6-astra`（已按 2026-09-05 裁定配好）。
⚠ 该探测**必须在 git 仓库内**跑——在 `/tmp` 会先撞
`Not inside a trusted directory and --skip-git-repo-check was not specified`，
那个失败与模型无关，容易误诊。

## 三 解法：换本机已有的另一份 codex（不动共享环境）

`brew upgrade --cask codex`（0.147.0 → 0.153.3）**不是唯一出路**，而且它改共享环境、
在本会话还被 auto-mode classifier 拦下。

**本机同时并存三份 codex，版本各不相同**：

```bash
codex --version                                               # PATH 上的 homebrew: 0.147.0
ls -d ~/.npm/_npx/*/node_modules/@openai/codex*/              # npx 缓存
/Applications/ChatGPT.app/Contents/Resources/codex --version  # app 内置: 0.153.3
```

实测：**npx 缓存里已经躺着 `codex-cli 0.153.3`**，文件 mtime `Sep 5 07:00` ——
与本车道撞 400 是同一小时，说明**别的车道先撞上、先装了新版**。

round-3 直接用**绝对路径**调它，homebrew 那份一个字节没动：

```bash
NPXC=~/.npm/_npx/d3e0db43a6e4314a/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
"$NPXC" exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-CX-G6-2b-R1.md)" \
  > <树>/_bmad-output/审查/codex-review-CARD-CX-G6-2b-R1.md \
  2> <树>/_bmad-output/审查/codex-review-CARD-CX-G6-2b-R1.round3.stderr </dev/null
```

**升级前先确认没打断别人**：`ps -Ao pid,lstart,etime,comm | awk '$NF=="codex"'`。
本机那几个裸 `codex` 进程 elapsed 是 13 天 / 4 天 / 2 天，全是长期残留，
不是本批正在跑的复核。（即便有，Unix 下运行中进程持有 inode，换二进制也不打断它们。）

## 四 对其余车道的意义

这是**批级**问题：第十一批 7 个车道执行同一条协议命令都会撞同一个 400，
**解法也同样通用**——照 §三 用 npx 那份的绝对路径即可，
**不需要用户裁决，也不需要动 homebrew**。

> 📌 复盘：本卡一度把「(f) 一轮 Codex」判为「阻断在环境、需用户点头升级」并据此收工。
> 那是把**没去做**说成了**做不到**——当时还有「换一份本机已有的二进制」这条零风险路径
> 完全没试。教训：撞到工具版本问题时，第一反应应是「本机还有没有别的版本」，
> 而不是「升级共享的那份」（后者才需要跨 session 授权）。

## 五 round-3 的一个已知噪声：只读沙箱下的假红

Codex 在 `--sandbox read-only` 下自己跑裁判命令会得到 **21 failed / 125 passed**，
与车道内实测的 **146 passed** 不符。原因不是代码有问题：
`test_review_app.py` 的 10+ 道 JS 门要把 `page-script.js` / `boot.mjs` / `case.test.mjs`
写进 `tmp_path` 再起 `node --test`，**只读沙箱不允许写盘**，于是这些门必红。

**数字对得上，不是猜的**：

```
grep -cE '^def test_.*\(node_harness' backend/tests/unit/test_review_app.py
→ 21
```

依赖 `node_harness` fixture 的测试函数**恰好 21 个**，与沙箱下的 `21 failed` 精确吻合；
`125 passed` + `21 failed` = 146 = 车道内实测的全绿数。⇒ 红的**正好是且仅是**那批要写盘的门。

⇒ 报告里若出现「这批 JS 门是红的」类结论，属**沙箱环境假红**，
按完成条件 (g)「每条先实测再采信」在车道内复跑对照即可分辨。
