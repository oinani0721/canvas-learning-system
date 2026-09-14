# CARD-G2-8 负控存档序列（哪一份是定论，前面几份为什么留着）

**定论 = `negctl-final-15seg-*.txt`（15 段全 `VERDICT=KILLED`）。**
前面几份留着不删，是因为它们记录的是**我自己的变异写错了**，而不是门不承重 ——
删掉等于把「判据曾经报错」这件事从账上抹掉。逐份如实交代：

| 存档 | 段数 | 结果 | 原因 |
|---|---|---|---|
| `negctl-4seg-*.txt` | 4 | 全 KILLED | 卡文 (h) 要求的四段（含禁写面 sha）。 |
| `negctl-assert-anchored-*.txt` | 4 | 全 KILLED | 同上，另加「红在**声称的那条断言**上」的核对。 |
| `negctl-r1fix-7seg-*.txt` | 7 | 全 KILLED | r1 整改后扩段。 |
| `negctl-r2fix-11seg-*.txt` | 11 | **2 段 NOT-KILLED** | ⛔ 两处**变异本身写错**：① readiness 段我把新 `case` 插在旧 `case` 之前，旧分支随后把结果覆盖回去，等于没变异；② lance 段断言锚选错（不剥前导零时 `$((08-0))` 的算术错误会让步 5 **后半段整段跳过**，所以红在「缺 Lance 阶段行」而不是 elapsed 上）。**不是门不承重。** |
| `negctl-r2fix-12seg-*.txt` | 12 | 全 KILLED | 上面两处改对后的重跑；并按 Codex r2 LOW-2 补落**变异 diff + 失败断言原文**。 |
| `negctl-r3fix-15seg-*.txt` | 15 | **1 NOT-KILLED + 2 MUTATE-FAILED** | ⛔ 仍是变异侧问题：① r3 把 `down` 输出改走 fd 9 之后，`rollback-unscoped` 的锚点串过期 ⇒ `MUTATE-FAILED`；② `ACTIVE_VAULT` 负控打在 `lines` 上，而 r3 之后「缺键」路径**不再经过 `lines`** ⇒ 变异无效果；③ 末行无行尾那段的反斜杠在 shell 单引号里多转义了一层 ⇒ `MUTATE-FAILED`。 |
| `negctl-final-15seg-*.txt` | 15 | **全 KILLED** | 三处改对后的重跑 = **定论**。 |

## 另一条如实记录：Codex r3 LOW-1 判为「口径澄清 + 补覆盖」，不是行为缺陷

r3 LOW-1 说「缺 `DAILY_REVIEW_VAULTS` 键且末行无行尾时会给该行补 LF，不满足逐字节不变」。
**实测两版输出逐字节相同**（旧：`lines[-1] += b"\n"` 后 join；新：`raw + sep + …`），
五种输入形态（`A=1\nB=2` / `…\n` / CRLF / 空 / CR 结尾）全部 `same`。
所以本卡对这条的处置是：**改写法让意图显式 + 补上这一类输入的门**，
而**不宣称修了一个缺陷**。对应的负控段 `alsopush-pads-last-line` 因此打的是
「去掉分隔符条件 ⇒ 末行与新键粘连」这个**真会坏**的变异，而不是还原旧写法
（还原旧写法的输出与新写法相同，杀不掉任何门 —— 那才是假负控）。
