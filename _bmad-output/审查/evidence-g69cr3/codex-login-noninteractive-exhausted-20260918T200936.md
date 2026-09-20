# Codex 登录：非交互路径穷举（证明必须用户操作）@ 2026-09-18T20:09:36

## 当前状态

    $ codex login status
    

    $ ls ~/.codex/auth.json
    不存在

## `codex login` 支持的非交互方式（`codex login --help` 实录）

    --with-api-key        Read the API key from stdin
                          (e.g. `printenv OPENAI_API_KEY | codex login --with-api-key`)
    --with-access-token   Read the access token from stdin
                          (e.g. `printenv CODEX_ACCESS_TOKEN | codex login --with-access-token`)

## 逐条查证：这两条路都没有可喂的凭据

| 来源 | OPENAI_API_KEY | CODEX_ACCESS_TOKEN | OPENAI_TOKEN |
|---|---|---|---|
| 进程环境变量 | 未设置 | 未设置 | 未设置 |

    $ grep -o '^[A-Z_]*OPENAI[A-Z_]*' backend/.env   → 无输出
    $ grep -o '^[A-Z_]*CODEX[A-Z_]*'  backend/.env   → 无输出

⇒ `--with-api-key` / `--with-access-token` 都没有可喂的值。

## 我没有做、也不该做的事

**没有去别处翻用户的凭据**（keychain / 其它项目的 .env / shell 历史）。
凭据的取用范围是用户的决定，不是我可以自行扩大的搜索面。

## 结论

`codex login`（不带子命令）走的是**交互式浏览器登录**，Claude 代做不了。
这是一个真实的外部阻塞，不是判据问题、也不是可以绕过的步骤。

**需要用户在 Claude 之外执行一次**：

    codex login

（在本会话输入框里可写成 `! codex login`，输出会直接进对话。）

## 登录后本卡可立刻继续，一切已就绪

| 项 | 值 |
|---|---|
| 代码定稿 commit | `c6a7f446` |
| 送审 SHA（prompt 里已填） | `967cf4cf` |
| 末轮绑定判据 | `git diff --stat c6a7f446 HEAD -- . ':(exclude)_bmad-output'` = **空**（恒成立，此后只改 `_bmad-output`） |
| prompt | `_bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R3-r1.md`（五分节齐全，含三跤自述与 8 个问题） |
| 存档命名 | `codex-review-CARD-G6-9c-R3-r1.md`（带 `-rN`，撞名核已过：裸名会覆盖 U6-A 的 `-r3`） |
| 首部生成器 | 已写好，从 stderr 抄会话头三行并括注行号（协议 §2.1） |

其余 12 条完成条件 (a)–(m)、(o)、(p) 全部达标，详见验收单。
