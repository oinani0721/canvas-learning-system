# 复核请求：CARD-HOST-PROBE 宿主实测表（零代码卡）

## 一 背景与最小读取面

本卡是一张**零代码探针卡**：在一个无 `.git` 祖先的临时探针 vault 里，实测四个 AI CLI 宿主（Claude Code / Codex / OpenCode / dsh）与后端 `/mcp` 端点的「认哪个根 / 读哪些 skills 目录 / MCP 怎么绑 / 沙箱缺省」，每条探针给出 CONFIRMED / REFUTED / NOT-RUN 三态与证据文件。代码树零变更。

工作目录：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`

**请只读以下四处，不要扩大读取面**：

1. `_bmad-output/研究/2026-09-08-HOST-PROBE-宿主实测表.md` —— 本卡主产出，请通读全文。
2. `_bmad-output/审查/evidence-host-probe/INDEX-evidence-list.txt` —— 证据文件清单与每份末行 `rc=`。**按需**再打开其中个别文件核对具体行号，不要逐份通读 48 份。
3. `backend/app/mcp/server.py` 的 95-150 行 —— 后端 MCP 端点挂载方式。
4. `canvas-vault/.mcp.json` —— 项目级 MCP 配置模板（8 行）。

**不要读取任何 `~/` 下的用户级配置文件**（`~/.codex/config.toml`、`~/.dsh/`、`~/.claude/` 等）。实测表与证据中涉及这些文件的部分，一律只保留了摘要值与计数，原始内容按卡文要求未入库。

## 二 作者自述，请独立核对

我（作者）声称以下几点成立，请你独立判断证据是否支撑结论：

1. **P0 地基**：探针 vault 的 `git rev-parse --show-toplevel` 返回 rc=128，且我用「车道树同命令 rc=0」作为正控，证明该判据不是恒真。
2. **每条探针都有三态与证据文件**，没有留空；NOT-RUN 的都写了具体原因。
3. **P2 的断连对照真的走到了 MCP 连接层**：`failOnStartupError: true` + 死端口时进程 rc=1 退出并报 `ECONNREFUSED`，错误链指向 `dsh-mcp-client/lib/index.js:782`。
4. **P4 做了整目录软链与条目级软链两态**，并用 `project: 3` / `project: 1` 两个计数作为主判据，而非模型自述。
5. **P10 用车道树 vault 替代 live vault**，理由是 live 禁写；我已把这一点登记为偏离。
6. **P6 的四格拒因串逐字相同，但我认为两层仍然分得开**，依据是 2×2 矩阵中唯一的成功格。
7. **禁写面 (i) 有一项未通过**（`~/.codex/config.toml` 的 sha 变化），我没有自判为通过，而是登记并提请裁定。

## 三 请按重要性排序回答的问题

1. **哪一条「CONFIRMED」其实只证明了「进程起来了」，而没有证明「发现了 skill」或「连上了 MCP」？** 具体说：正控是否绑定到了 `probe-skill` 这个字面量与具体工具名字面量上，还是只看了退出码或「没有报错」。
2. **`failOnStartupError: true` 的断连对照，是否真的走到了 MCP 连接这一层**，还是可能被更早的 profile 加载失败所满足？我给出的错误链与「8999+缺省 false 时进程正常启动」的对照，是否足以排除后一种解释？
3. **P10 关于「worktree 的 `.git` 文件被当作项目根」的观测，能否外推到 live vault（其祖先是主仓的 `.git` 目录）？** 我在「本卡未证明什么」里把它列为未证明，这个处理是否恰当，还是说证据其实已经支持外推（或反过来，连我写的结论都过宽）？
4. **「二线转正建议」三行是否有超出证据的地方？** 特别是受信项目下的行为、dsh 的 headless 形态、OpenCode 模型侧可用性这三个未测面，建议里的措辞有没有暗示我其实验过。
5. **有没有哪条探针在 `$HOME` 下留下了文件而我没有登记？** 实测表 §六.6 列了四项副作用，请对照证据判断是否有遗漏，以及 §三.7 对 `~/.codex/config.toml` 的因果归因（正控 r2 / 负控 r1 / 对照 `[mcp_servers.*]` 恒 8）是否成立。

另请留意两处我自己标记过的方法论风险，判断我的处理是否站得住：

- 我一度把「dump 输出行数变了、sha 变了」当作「patch 生效」，后来发现那 1 行差异其实是报错信息本身，于是把判据改为绑定 `id: mcp-cls` 等字面量。
- 我第一次做 codex 写配置的因果实验时选错了条件（用 read-only），得到「什么都没变」，差点据此排除因果；后来靠时间轴回看才补上 workspace-write 的正控。

## 四 输出格式

请按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条写明：

- 级别
- 对应探针编号（P0~P10）或实测表章节号
- 问题一句话
- 一句复核思路（我该怎么验证你说的这条）

若某级别为空请显式写「无」。

## 五 边界

- 只读复核，不要修改任何文件。
- 不要启动 dsh / codex / opencode / claude 任何进程，不要连接任何数据库或后端端口。
- 不要评价 U3-C 的 `--hosts` 实现（不在本卡范围）。
- 不要读取用户级配置文件（见第一节）。
