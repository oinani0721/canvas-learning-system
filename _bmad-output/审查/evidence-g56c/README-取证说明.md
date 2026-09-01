# CARD-G5-6c 取证说明（BATCH-2026-09-01-第九批）

本目录是 CARD-G5-6c 的**可复现**取证包。它证明什么、不证明什么，逐条如实写在下面。

## 1. 三条新反例的先红 / 后绿（核心裁判 2）

`make_repro_g56c.py <目标目录>` 落三份 tmp vault，字节与 round-8 审查存档逐字节对齐：

| 反例 | 文件 | 字节数 | 十六进制（前缀） |
|---|---|---|---|
| round-8 BLOCKER-1 | `hash-NBSP.md` | 8 | `23c2a06b6565700a`（`#` + U+00A0 + `keep` + LF） |
| round-8 BLOCKER-2 | `GPT4声明.md` | 36 | `2d2d2d0a67656e657261746f723a20…` |
| round-8 HIGH | `DOI来源.md` | 32 | `2d2d2d0a536f757263653a20444f493a…` |

⛔ 脚本对 NBSP 反例带**字节断言**（`EXPECTED_HEX`）：不可见字符若被编辑器/格式化器
静默换成普通空格，脚本当场 `SystemExit`，不会产出一份「看着对但测错东西」的 fixture。
同理，源码里这些字符一律写成 `\uXXXX` ASCII 转义，不直接敲 —— 本卡实测 `ruff format`
重排该文件后字节自证仍通过，正是这个写法的回报。

复现（`--vault` 与 `--out-dir` 都用 tmp，零写 live）：

```sh
python3 -B canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault <tmp>/NEW_HEADING/vault --now 2026-09-01T00:00:00+08:00 \
  --out-dir <tmp>/NEW_HEADING/out
```

- **修复前**（HEAD `969844ef`）：三份均 `C3_empty_or_skeleton / 建议删 / confident=true`，
  与 round-8 §二贴出的 JSON 逐字符一致。
- **修复后**：三份均 `C6_undecided / 拿不准 / confident=false`。
- 三份输入文件的 sha256 在跑前跑后相同（零写侧对账）。

## 2. 回退变异负控（核心裁判 3）

`g56c_mutations.py <仓库根>`，输出存 `g56c_mutations_output.txt`。

判据比「N/N killed」严：**指定的那一道门必须变红**。`rc=5`（没收集到用例）不算红。
每条变异回退该缺陷的**全部**防线层（M-AI 退两层、M-DOI 退两层）—— 只退一层会被
另一层兜住，门看起来「没抓到」，从而被误判为不承重。

实测：三条各 `1 failed, 81 passed`，**连带红恰好 1 门**（说明每道新门恰好覆盖它
声称覆盖的那条防线，既非假红也非靠交叉保护蒙混）；跑完源码 sha256 与基线逐字节相同。

⛔ 本脚本**原地修改 checkout 源码**，必须串行、独占运行。

## 3. 本取证包不证明什么

- 不证明「没有第四条」。round-3..8 每一轮都在「已全部声明」之后又抓出新构造；
  本卡只证明 round-8 点名的那三条已被拦住。
- 不证明真实库存上的判据准确率（I-4 仍未解锁：两个 vault 都还没有 `_待处理/`）。
- 不证明非法端口、Markdown 特殊路径等已登记的 M/L 边界被修 —— 它们按卡文 §3
  默认裁决**保留不修**，见生产文件头偏差 16 / 17。
