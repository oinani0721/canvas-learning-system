#!/usr/bin/env python3
"""`llm_call_logs.db`（SQLite 二进制）在「只读不写」下的 sha256 稳定性实测（卡文 (e)）。

为什么必须单独核：门用逐字节 sha 比对判 CHANGED。SQLite 的 header 里有
change counter / freelist / schema cookie 等字段，**某些"只读"操作也会回写 header**
（典型：rollback journal 的建立与删除、WAL 切换）。若「只 SELECT 一次」就让 sha 变了，
那么把它纳入监视面会给本门造出一个新的**假红**面 —— 这属于扩面必须先测的前提，
不是测完再说的附注。

本文件**不**决定是否扩面（卡文已裁定扩面），只如实产出结论；不稳定就登记，
⛔ 不因此放宽监视面。
"""

import hashlib
import os
import sqlite3
import sys
import tempfile

CREATE = """
CREATE TABLE IF NOT EXISTS llm_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    model_name TEXT NOT NULL,
    total_tokens INTEGER NOT NULL DEFAULT 0
);
"""


def sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main() -> int:
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "llm_call_logs.db")

        # 建库 + 写一行，关连接（模拟「生产已经落过盘」的起点）
        con = sqlite3.connect(db)
        con.executescript(CREATE)
        con.execute(
            "INSERT INTO llm_call_logs (request_id, task_type, model_name, total_tokens)"
            " VALUES (?,?,?,?)", ("r1", "chat", "m", 10))
        con.commit()
        con.close()
        s0 = sha(db)
        print(f"[建库后] sha={s0[:16]}… size={os.path.getsize(db)}")

        # ① 默认（读写）连接，只 SELECT 一次
        con = sqlite3.connect(db)
        rows = con.execute("SELECT COUNT(*) FROM llm_call_logs").fetchone()
        con.close()
        s1 = sha(db)
        print(f"[①默认连接·只 SELECT] rows={rows[0]} sha={s1[:16]}… 相同={s1 == s0}")
        if s1 != s0:
            failures.append("默认连接下的一次 SELECT 改变了文件字节")

        # ② 再来一次（证明不是「第一次才变」）
        con = sqlite3.connect(db)
        con.execute("SELECT * FROM llm_call_logs").fetchall()
        con.close()
        s2 = sha(db)
        print(f"[②默认连接·再 SELECT] sha={s2[:16]}… 相同={s2 == s0}")
        if s2 != s0:
            failures.append("第二次 SELECT 改变了文件字节")

        # ③ file:...?mode=ro 只读 URI
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        con.execute("SELECT COUNT(*) FROM llm_call_logs").fetchone()
        con.close()
        s3 = sha(db)
        print(f"[③只读 URI·SELECT] sha={s3[:16]}… 相同={s3 == s0}")
        if s3 != s0:
            failures.append("只读 URI 下的 SELECT 改变了文件字节")

        # ④ 验伪锚：真写一行 ⇒ sha **必须**变（证明本判据不是恒「相同」）
        con = sqlite3.connect(db)
        con.execute(
            "INSERT INTO llm_call_logs (request_id, task_type, model_name, total_tokens)"
            " VALUES (?,?,?,?)", ("r2", "chat", "m", 20))
        con.commit()
        con.close()
        s4 = sha(db)
        print(f"[④验伪锚·真写入] sha={s4[:16]}… 相同={s4 == s0} (期望 False)")
        if s4 == s0:
            failures.append("验伪锚失效：真写入之后 sha 竟未变，本判据不可信")

        # ⑤ 验伪锚之二：门用的 shasum 与本文件用的 hashlib 必须一致
        import subprocess
        out = subprocess.run(["/usr/bin/shasum", "-a", "256", db],
                             capture_output=True, text=True)
        same_tool = out.stdout.split()[0] == s4
        print(f"[⑤验伪锚·shasum==hashlib] {same_tool} (期望 True)")
        if not same_tool:
            failures.append("shasum 与 hashlib 结果不一致，本实测无法代表门的判据")

    if failures:
        for f in failures:
            print(f"!! {f}")
        print("SQLITE-SHA-STABILITY: UNSTABLE（登记进「本卡未证明什么」，⛔ 不放宽监视面）")
        return 1
    print("SQLITE-SHA-STABILITY: STABLE（只读不写 ⇒ 逐字节不变）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
